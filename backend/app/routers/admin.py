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
    cursor = db.users.find({}, projection={"password": 0}).sort("createdAt", -1)
    users = [serialize_doc(u) async for u in cursor]
    for u in users:
        if u.get("role") != "seller":
            continue
        raw_id = u.get("_id") or u.get("id")
        if not raw_id:
            continue
        try:
            seller_oid = ObjectId(str(raw_id))
            score = await get_supplier_score_for_response(seller_oid)
            if score:
                u["trustScore"] = score.get("total_score", 0)
                u["trustLevel"] = score.get("trust_level", "Low Trust")
        except Exception:
            pass
    return success_response(data={"users": users})


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
    await admin_log(ObjectId(user["id"]), "VERIFY_SUPPLIER", id, {"verified": verified, "email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_VERIFIED" if verified else "SUPPLIER_UNVERIFIED", "Supplier verified" if verified else "Supplier unverified", {"verified": verified})
    if verified:
        await create_notification(oid, "Supplier verified", "Your account has been verified as a supplier.", "supplier_verified", "user", id)
    return success_response(data={"user": serialize_doc(target)})


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
    await admin_log(ObjectId(user["id"]), "VERIFY_SUPPLIER", seller_id, {"email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_VERIFIED", "Supplier verified", {})
    await create_notification(oid, "Supplier verified", "Your account has been verified as a supplier.", "supplier_verified", "user", seller_id)
    return success_response(data={"user": serialize_doc(target)})


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
                profile = await db.companyprofiles.find_one({"user": ObjectId(str(raw_id))}, projection={"companyName": 1, "city": 1})
                if profile:
                    doc["companyName"] = profile.get("companyName")
                    doc["city"] = profile.get("city")
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
    await admin_log(ObjectId(user["id"]), "UNVERIFY_SUPPLIER", seller_id, {"email": target.get("email")})
    await emit_event("user", oid, ObjectId(user["id"]), "admin", "SUPPLIER_UNVERIFIED", "Supplier unverified", {})
    return success_response(data={"user": serialize_doc(target)})


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
