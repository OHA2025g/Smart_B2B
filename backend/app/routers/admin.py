import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.admin import BanBody, VerifySupplierBody
from app.services.supplier_score import recalculate_supplier_score, get_supplier_score_for_response
from app.services.workflow_events import emit_event
from app.services.notifications import create_notification
from app.services.admin_audit import admin_action_log
from app.routers.orders import _company_display_name

router = APIRouter(dependencies=[Depends(require_roles("admin"))])


async def admin_log(admin_id, action_type, target_id, details):
    await admin_action_log(admin_id, action_type, target_id, details)


def _target_type_from_action(action_type: str) -> str:
    if not action_type:
        return "unknown"
    if "USER" in action_type or "BAN" in action_type:
        return "user"
    if "SUPPLIER" in action_type or "VERIFY" in action_type or "SCORE" in action_type:
        return "supplier"
    if "CATEGORY" in action_type:
        return "category"
    return "misc"


async def _enrich_admin_log(db, log: dict) -> dict:
    admin_user = await db.users.find_one({"_id": log["adminId"]}, projection={"name": 1, "email": 1, "role": 1}) if log.get("adminId") else None
    doc = serialize_doc(log) or {}
    doc["actor"] = (admin_user or {}).get("name") or (admin_user or {}).get("email") or "Admin"
    doc["actorRole"] = (admin_user or {}).get("role") or "admin"
    doc["action"] = log.get("actionType")
    doc["targetType"] = _target_type_from_action(log.get("actionType") or "")
    # Do not re-assign targetId/details from raw BSON — breaks JSON (ObjectId) and caused admin 500s.
    if admin_user:
        doc["adminId"] = serialize_doc(admin_user)
    return doc


@router.get("/summary")
async def summary(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    users_c = await db.users.count_documents({})
    products_c = await db.products.count_documents({})
    inquiries_c = await db.inquiries.count_documents({})
    return success_response(data={"summary": {"users": users_c, "products": products_c, "inquiries": inquiries_c}})


@router.get("/dashboard")
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    users_c = await db.users.count_documents({})
    buyers_c = await db.users.count_documents({"role": "buyer"})
    sellers_c = await db.users.count_documents({"role": "seller"})
    verified = await db.users.count_documents({"role": "seller", "isVerifiedSupplier": True})
    pending_sellers = await db.users.count_documents({"role": "seller", "isVerifiedSupplier": {"$ne": True}})
    products_c = await db.products.count_documents({})
    rfqs_c = await db.rfqs.count_documents({})
    quotes_c = await db.quotes.count_documents({})
    orders_c = await db.orders.count_documents({})
    rfq_status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    rfq_status_dist = {}
    async for d in db.rfqs.aggregate(rfq_status_pipeline):
        rfq_status_dist[d["_id"] or "unknown"] = d["count"]
    order_status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    order_status_dist = {}
    async for d in db.orders.aggregate(order_status_pipeline):
        order_status_dist[d["_id"] or "unknown"] = d["count"]
    top_categories_pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    top_categories = [{"name": d["_id"], "count": d["count"]} async for d in db.products.aggregate(top_categories_pipeline) if d.get("_id")]
    seller_order_counts = {}
    async for o in db.orders.aggregate([{"$group": {"_id": "$sellerId", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]):
        seller_order_counts[str(o["_id"])] = o["count"]
    top_suppliers = []
    for sid, count in list(seller_order_counts.items())[:10]:
        u = await db.users.find_one({"_id": ObjectId(sid)}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if sid else None
        score = await get_supplier_score_for_response(ObjectId(sid)) if sid else None
        top_suppliers.append({"sellerId": sid, "name": (u or {}).get("name"), "email": (u or {}).get("email"), "verified": bool((u or {}).get("isVerifiedSupplier")), "orderCount": count, "trustScore": (score or {}).get("total_score", 0)})
    recent_logs = []
    async for log in db.adminactionlogs.find({}).sort("createdAt", -1).limit(20):
        recent_logs.append(await _enrich_admin_log(db, log))
    return success_response(data={
        "dashboard": {
            "totalUsers": users_c,
            "totalBuyers": buyers_c,
            "totalSellers": sellers_c,
            "verifiedSuppliers": verified,
            "pendingSuppliers": pending_sellers,
            "totalProducts": products_c,
            "totalRfqs": rfqs_c,
            "totalQuotes": quotes_c,
            "totalOrders": orders_c,
            "rfqStatusDistribution": rfq_status_dist,
            "orderStatusDistribution": order_status_dist,
            "topCategories": top_categories,
            "topSuppliers": top_suppliers,
            "recentLogs": recent_logs,
        }
    })


@router.get("/users")
async def get_users(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.users.find({"role": "buyer"}, projection={"password": 0}).sort("createdAt", -1)
    users = [serialize_doc(u) async for u in cursor]
    return success_response(data={"users": users})


@router.get("/user-profile/{user_id}")
async def admin_user_profile(user_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Full user + company profile for admin (buyer or seller)."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid user ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    company = await db.companyprofiles.find_one({"user": oid})
    out: dict = {"user": serialize_doc(target), "company": serialize_doc(company) if company else None}
    if target.get("role") == "seller":
        sc = await get_supplier_score_for_response(oid)
        out["score"] = sc
    return success_response(data=out)


@router.put("/users/{id}/ban")
async def ban_user(id: str, request: Request, body: BanBody, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    banned = body.banned if body.banned is not None else True
    await db.users.update_one({"_id": oid}, {"$set": {"isBanned": banned}})
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    await admin_log(ObjectId(user["id"]), "USER_BAN", id, {"banned": banned, "email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "USER_BANNED" if banned else "USER_UNBANNED", "User banned" if banned else "User unbanned", {"banned": banned})
    if banned:
        await create_notification(oid, "Account suspended", "Your account has been suspended.", "user_banned", "user", id)
    return success_response(data={"user": serialize_doc(target)})


@router.put("/users/{id}/unban")
async def unban_user(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    await db.users.update_one({"_id": oid}, {"$set": {"isBanned": False}})
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    await admin_log(ObjectId(user["id"]), "USER_UNBAN", id, {"email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "USER_UNBANNED", "User unbanned", {})
    await create_notification(oid, "Account reinstated", "Your account has been reinstated.", "user_unbanned", "user", id)
    return success_response(data={"user": serialize_doc(target)})


@router.put("/users/{id}/verify-supplier")
async def verify_supplier(id: str, request: Request, body: VerifySupplierBody, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    verified = body.verified if body.verified is not None else True
    await db.users.update_one({"_id": oid}, {"$set": {"isVerifiedSupplier": verified}})
    await recalculate_supplier_score(oid)
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    score = await get_supplier_score_for_response(oid)
    await admin_log(ObjectId(user["id"]), "VERIFY_SUPPLIER", id, {"verified": verified, "email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_VERIFIED" if verified else "SUPPLIER_UNVERIFIED", "Supplier verified" if verified else "Supplier unverified", {"verified": verified})
    if verified:
        await create_notification(oid, "Supplier verified", "Your account has been verified as a supplier.", "supplier_verified", "user", id)
    else:
        await create_notification(
            oid, "Supplier verification removed", "Your supplier verification has been updated by an administrator.", "supplier_unverified", "user", id
        )
    return success_response(data={"user": serialize_doc(target), "score": score})


@router.post("/suppliers/{seller_id}/verify")
async def admin_verify_supplier(seller_id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    await db.users.update_one({"_id": oid}, {"$set": {"isVerifiedSupplier": True}})
    await recalculate_supplier_score(oid)
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    score = await get_supplier_score_for_response(oid)
    await admin_log(ObjectId(user["id"]), "VERIFY_SUPPLIER", seller_id, {"email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_VERIFIED", "Supplier verified", {})
    await create_notification(oid, "Supplier verified", "Your account has been verified as a supplier.", "supplier_verified", "user", seller_id)
    return success_response(data={"user": serialize_doc(target), "score": score})


@router.get("/suppliers")
async def get_suppliers(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.users.find({"role": "seller"}, projection={"password": 0}).sort("createdAt", -1)
    suppliers = []
    async for u in cursor:
        doc = serialize_doc(u)
        if doc:
            raw_id = doc.get("_id") or doc.get("id")
            if raw_id:
                try:
                    score = await get_supplier_score_for_response(ObjectId(str(raw_id)))
                    if score:
                        doc["trustScore"] = score.get("total_score", 0)
                        doc["trustLevel"] = score.get("trust_level", "Low Trust")
                except Exception:
                    pass
                profile = await db.companyprofiles.find_one(
                    {"user": ObjectId(str(raw_id))},
                    projection={"companyName": 1, "city": 1, "state": 1, "country": 1, "phone": 1, "gstNumber": 1, "description": 1, "website": 1},
                )
                if profile:
                    doc["companyName"] = profile.get("companyName")
                    doc["city"] = profile.get("city")
                    doc["state"] = profile.get("state")
                    doc["country"] = profile.get("country")
                    doc["phone"] = profile.get("phone")
                    doc["gstNumber"] = profile.get("gstNumber")
                    doc["description"] = profile.get("description")
                    doc["website"] = profile.get("website")
        suppliers.append(doc)
    return success_response(data={"suppliers": suppliers})


@router.put("/suppliers/{seller_id}/unverify")
async def admin_unverify_supplier(seller_id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail=error_response("User not found.", "NOT_FOUND", path=str(request.url.path)))
    await db.users.update_one({"_id": oid}, {"$set": {"isVerifiedSupplier": False}})
    await recalculate_supplier_score(oid)
    target = await db.users.find_one({"_id": oid}, projection={"password": 0})
    score = await get_supplier_score_for_response(oid)
    await admin_log(ObjectId(user["id"]), "UNVERIFY_SUPPLIER", seller_id, {"email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_UNVERIFIED", "Supplier unverified", {})
    await create_notification(
        oid, "Supplier verification removed", "Your supplier verification has been removed. Your trust score was recalculated.", "supplier_unverified", "user", seller_id
    )
    return success_response(data={"user": serialize_doc(target), "score": score})


@router.post("/suppliers/{seller_id}/recalculate-score")
async def admin_recalculate_score(seller_id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    target = await db.users.find_one({"_id": oid}, projection={"role": 1})
    if not target or target.get("role") != "seller":
        raise HTTPException(status_code=404, detail=error_response("Supplier not found.", "NOT_FOUND", path=str(request.url.path)))
    updated = await recalculate_supplier_score(oid)
    score_doc = serialize_doc(updated) if updated else None
    await admin_log(ObjectId(user["id"]), "RECALCULATE_SCORE", seller_id, {})
    return success_response(data={"score": score_doc})


@router.get("/rfqs")
async def get_rfqs(request: Request, status: str | None = None, user: dict = Depends(get_current_user)):
    db = get_db()
    filter_q = {}
    if status:
        filter_q["status"] = status
    cursor = db.rfqs.find(filter_q).sort("createdAt", -1)
    rfqs = []
    async for rfq in cursor:
        buyer = await db.users.find_one({"_id": rfq["buyerId"]}, projection={"name": 1, "email": 1}) if rfq.get("buyerId") else None
        doc = serialize_doc(rfq)
        if doc:
            doc["buyerId"] = serialize_doc(buyer) if buyer else None
        rfqs.append(doc)
    return success_response(data={"rfqs": rfqs})


@router.get("/orders")
async def get_orders(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.orders.find({}).sort("createdAt", -1)
    orders = []
    async for o in cursor:
        items = []
        for it in o.get("items", []):
            prod = await db.products.find_one({"_id": it.get("productId")}) if it.get("productId") else None
            items.append({**it, "productId": serialize_doc(prod) if prod else None})
        buyer = await db.users.find_one({"_id": o["buyerId"]}, projection={"name": 1, "email": 1}) if o.get("buyerId") else None
        seller = await db.users.find_one({"_id": o["sellerId"]}, projection={"name": 1, "email": 1}) if o.get("sellerId") else None
        doc = serialize_doc(o)
        if doc:
            doc["items"] = items
            doc["buyerId"] = serialize_doc(buyer) if buyer else None
            doc["sellerId"] = serialize_doc(seller) if seller else None
            doc["buyerCompany"] = await _company_display_name(db, o.get("buyerId"))
            doc["sellerCompany"] = await _company_display_name(db, o.get("sellerId"))
        orders.append(doc)
    return success_response(data={"orders": orders})


@router.get("/categories")
async def admin_list_categories(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.categories.find({}).sort("name", 1)
    categories = [serialize_doc(c) async for c in cursor]
    return success_response(data={"categories": categories})


@router.get("/logs")
async def get_logs(
    request: Request,
    user: dict = Depends(get_current_user),
    action: str | None = None,
    role: str | None = None,
):
    db = get_db()
    q = {}
    cursor = db.adminactionlogs.find(q).sort("createdAt", -1).limit(200)
    logs = []
    async for log in cursor:
        if action and action.lower() not in (log.get("actionType") or "").lower():
            continue
        enriched = await _enrich_admin_log(db, log)
        if role and (enriched.get("actorRole") or "").lower() != role.lower():
            continue
        logs.append(enriched)
    return success_response(data={"logs": logs[:150]})


@router.get("/analytics/overview")
async def analytics_overview(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    users_c = await db.users.count_documents({})
    products_c = await db.products.count_documents({})
    rfqs_c = await db.rfqs.count_documents({})
    orders_c = await db.orders.count_documents({})
    verified = await db.users.count_documents({"role": "seller", "isVerifiedSupplier": True})
    return success_response(data={"overview": {"totalUsers": users_c, "totalProducts": products_c, "totalRfqs": rfqs_c, "totalOrders": orders_c, "verifiedSuppliers": verified}})


@router.get("/analytics/top-suppliers")
async def analytics_top_suppliers(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    pipeline = [{"$group": {"_id": "$sellerId", "orderCount": {"$sum": 1}}}, {"$sort": {"orderCount": -1}}, {"$limit": 20}]
    top = []
    async for o in db.orders.aggregate(pipeline):
        sid = o["_id"]
        if not sid:
            continue
        u = await db.users.find_one({"_id": sid}, projection={"name": 1, "isVerifiedSupplier": 1})
        score = await get_supplier_score_for_response(sid)
        top.append({"sellerId": str(sid), "name": (u or {}).get("name"), "verified": bool((u or {}).get("isVerifiedSupplier")), "orderCount": o["orderCount"], "trustScore": (score or {}).get("total_score", 0)})
    return success_response(data={"topSuppliers": top})


@router.get("/analytics/category-performance")
async def analytics_category_performance(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    pipeline = [{"$group": {"_id": "$category", "productCount": {"$sum": 1}}}, {"$sort": {"productCount": -1}}, {"$limit": 20}]
    cats = [{"name": d["_id"], "productCount": d["productCount"]} async for d in db.products.aggregate(pipeline) if d.get("_id")]
    return success_response(data={"categoryPerformance": cats})


@router.get("/analytics/top-products")
async def analytics_top_products(request: Request, user: dict = Depends(get_current_user)):
    """Most-requested products via RFQ line items (demo metric)."""
    db = get_db()
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.productId", "rfqCount": {"$sum": 1}}},
        {"$sort": {"rfqCount": -1}},
        {"$limit": 20},
    ]
    out = []
    async for row in db.rfqs.aggregate(pipeline):
        pid = row.get("_id")
        if not pid:
            continue
        prod = await db.products.find_one({"_id": pid}, projection={"title": 1, "category": 1, "seller": 1})
        out.append({
            "productId": str(pid),
            "title": (prod or {}).get("title"),
            "category": (prod or {}).get("category"),
            "rfqLineCount": row.get("rfqCount", 0),
        })
    return success_response(data={"topProducts": out})


@router.get("/analytics/rfq-trends")
async def analytics_rfq_trends(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    pipeline = [
        {"$project": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}}}},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    series = [{"month": d["_id"], "count": d["count"]} async for d in db.rfqs.aggregate(pipeline) if d.get("_id")]
    return success_response(data={"rfqTrends": series})


@router.get("/analytics/order-trends")
async def analytics_order_trends(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    pipeline = [
        {"$project": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}}}},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    series = [{"month": d["_id"], "count": d["count"]} async for d in db.orders.aggregate(pipeline) if d.get("_id")]
    return success_response(data={"orderTrends": series})




@router.get("/moderation/messages")
async def admin_moderation_messages(request: Request, user: dict = Depends(get_current_user)):
    """Flagged / moderated RFQ chat messages with raw + display text for review."""
    db = get_db()
    out = []
    async for th in db.messagethreads.find({}):
        rfq_id = str(th.get("rfqId", ""))
        for m in th.get("messages", []) or []:
            if not (m.get("moderationFlag") or m.get("containsContactAttempt") or m.get("moderationScore", 0) >= 45):
                continue
            mid = str(m.get("_id", ""))
            sid = m.get("senderId")
            sender = None
            if isinstance(sid, ObjectId):
                sender = await db.users.find_one({"_id": sid}, projection={"name": 1, "email": 1, "role": 1})
            row = {
                "messageId": mid,
                "rfqId": rfq_id,
                "sender": serialize_doc(sender) if sender else None,
                "senderRole": m.get("senderRole"),
                "rawMessage": m.get("rawMessage") or m.get("text"),
                "displayMessage": m.get("displayMessage") or m.get("text"),
                "moderationScore": m.get("moderationScore", 0),
                "moderationReasons": m.get("moderationReasons") or ([m.get("moderationReason")] if m.get("moderationReason") else []),
                "moderationStatus": m.get("moderationStatus"),
                "detectedTypes": m.get("detectedTypes", []),
                "createdAt": m.get("createdAt"),
            }
            out.append(row)
    out.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return success_response(data={"messages": out[:500], "count": len(out[:500])})


@router.get("/flagged-messages")
async def admin_flagged_messages(request: Request, user: dict = Depends(get_current_user)):
    """Messages with moderation flag (off-platform / contact attempt)."""
    db = get_db()
    out = []
    async for t in db.messagethreads.find({}):
        rfq_id = t.get("rfqId")
        for m in t.get("messages", []):
            if m.get("moderationFlag") or m.get("containsContactAttempt"):
                out.append(
                    {
                        "threadId": str(t.get("_id")),
                        "rfqId": str(rfq_id) if rfq_id else None,
                        "messageId": str(m.get("_id") or m.get("id", "")),
                        "senderId": str(m.get("senderId", "")) if m.get("senderId") is not None else None,
                        "senderRole": m.get("senderRole"),
                        "text": m.get("text"),
                        "createdAt": m.get("createdAt").isoformat() if getattr(m.get("createdAt"), "isoformat", None) else None,
                        "moderationFlag": bool(m.get("moderationFlag")),
                        "moderationReason": m.get("moderationReason"),
                    }
                )
    out.sort(key=lambda x: x.get("createdAt") or "", reverse=True)
    return success_response(data={"flagged": out[:500], "count": len(out[:500])})

@router.get("/subscriptions")
async def list_subscriptions(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cur = db.seller_subscriptions.find({}).sort("createdAt", -1).limit(500)
    out = []
    async for s in cur:
        doc = serialize_doc(s) or {}
        sid = s.get("sellerId")
        u = await db.users.find_one({"_id": sid}, projection={"name": 1, "email": 1}) if sid else None
        if u:
            doc["sellerName"] = u.get("name")
            doc["sellerEmail"] = u.get("email")
        out.append(doc)
    return success_response(data={"subscriptions": out})


@router.get("/payments")
async def list_payments(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cur = db.payments.find({}).sort("createdAt", -1).limit(500)
    out = []
    async for p in cur:
        doc = serialize_doc(p) or {}
        uid = p.get("userId")
        u = await db.users.find_one({"_id": uid}, projection={"name": 1, "email": 1, "role": 1}) if uid else None
        if u:
            doc["userName"] = u.get("name")
            doc["userEmail"] = u.get("email")
            doc["payerRoleResolved"] = u.get("role")
        out.append(doc)
    return success_response(data={"payments": out})


@router.get("/revenue-summary")
async def revenue_summary(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    sub_rev = 0.0
    async for p in db.payments.find(
        {"paymentType": "subscription", "status": "success"},
        {"amount": 1},
    ):
        sub_rev += float(p.get("amount") or 0)
    escrow_vol = 0.0
    async for p in db.payments.find(
        {"paymentType": "order_escrow", "status": {"$in": ["escrow_held", "released"]}},
        {"amount": 1},
    ):
        escrow_vol += float(p.get("amount") or 0)
    ok = await db.payments.count_documents({"status": {"$in": ["success", "escrow_held", "released"]}})
    fail = await db.payments.count_documents({"status": "failed"})
    go = await db.users.count_documents({"role": "seller", "subscriptionPlan": "go"})
    pro = await db.users.count_documents({"role": "seller", "subscriptionPlan": "pro"})
    free = await db.users.count_documents(
        {
            "role": "seller",
            "$or": [
                {"subscriptionPlan": {"$exists": False}},
                {"subscriptionPlan": "free"},
            ],
        }
    )
    pro_active = await db.seller_subscriptions.count_documents({"plan": "pro", "status": "active"})
    go_active = await db.seller_subscriptions.count_documents({"plan": "go", "status": "active"})
    return success_response(
        data={
            "revenue": {
                "subscription_revenue_inr": round(sub_rev, 2),
                "escrow_payment_volume_inr": round(escrow_vol, 2),
                "successful_payments": ok,
                "failed_payments": fail,
                "active_go_sellers": go_active,
                "active_pro_sellers": pro_active,
                "sellers_by_plan_go": go,
                "sellers_by_plan_pro": pro,
                "sellers_by_plan_free": free,
            }
        }
    )
