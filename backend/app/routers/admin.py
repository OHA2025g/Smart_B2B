from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.admin import BanBody, VerifySupplierBody
from app.services.supplier_score import recalculate_supplier_score, get_supplier_score_for_response

router = APIRouter(dependencies=[Depends(require_roles("admin"))])


async def admin_log(admin_id, action_type, target_id, details):
    db = get_db()
    try:
        await db.adminactionlogs.insert_one({"adminId": admin_id, "actionType": action_type, "targetId": target_id, "details": details})
    except Exception as e:
        print("AdminActionLog error:", e)


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
    verified = await db.users.count_documents({"role": "seller", "isVerifiedSupplier": True})
    pending_sellers = await db.users.count_documents({"role": "seller", "isVerifiedSupplier": {"$ne": True}})
    rfqs_c = await db.rfqs.count_documents({})
    quotes_c = await db.quotes.count_documents({})
    orders_c = await db.orders.count_documents({})
    return success_response(data={
        "dashboard": {
            "totalUsers": users_c,
            "verifiedSuppliers": verified,
            "pendingSuppliers": pending_sellers,
            "totalRfqs": rfqs_c,
            "totalQuotes": quotes_c,
            "totalOrders": orders_c,
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
        orders.append(doc)
    return success_response(data={"orders": orders})


@router.get("/logs")
async def get_logs(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.adminactionlogs.find({}).sort("createdAt", -1).limit(100)
    logs = []
    async for log in cursor:
        admin_user = await db.users.find_one({"_id": log["adminId"]}, projection={"name": 1, "email": 1}) if log.get("adminId") else None
        doc = serialize_doc(log)
        if doc:
            doc["adminId"] = serialize_doc(admin_user) if admin_user else None
        logs.append(doc)
    return success_response(data={"logs": logs})
