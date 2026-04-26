import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.order import OrderStatusUpdate, OrderPaymentUpdate
from app.services.workflow_events import emit_event
from app.services.notifications import create_notification

router = APIRouter()

_ORDER_STATUS_EVENTS = {
    "confirmed": ("ORDER_CONFIRMED", "Order confirmed"),
    "processing": ("ORDER_PROCESSING", "Order is being processed"),
    "shipped": ("ORDER_SHIPPED", "Order shipped"),
    "delivered": ("ORDER_DELIVERED", "Order delivered"),
    "cancelled": ("ORDER_CANCELLED", "Order cancelled"),
}

_PAYMENT_LABELS = {
    "payment_pending": "PAYMENT_PENDING",
    "escrow_held": "ESCROW_HELD",
    "released": "PAYMENT_RELEASED",
    "refunded": "PAYMENT_REFUNDED",
}


async def _company_display_name(db, user_oid):
    if not user_oid:
        return None
    prof = await db.companyprofiles.find_one({"user": user_oid}, projection={"companyName": 1})
    if prof and prof.get("companyName"):
        return prof["companyName"]
    u = await db.users.find_one({"_id": user_oid}, projection={"name": 1})
    return (u or {}).get("name")


async def _populate_order(db, order):
    items = []
    for it in order.get("items", []):
        prod = await db.products.find_one({"_id": it.get("productId")}) if it.get("productId") else None
        doc = dict(it)
        doc["productId"] = serialize_doc(prod) if prod else None
        items.append(doc)
    buyer = await db.users.find_one({"_id": order["buyerId"]}, projection={"name": 1, "email": 1}) if order.get("buyerId") else None
    seller = await db.users.find_one({"_id": order["sellerId"]}, projection={"name": 1, "email": 1}) if order.get("sellerId") else None
    buyer_company = await _company_display_name(db, order.get("buyerId"))
    seller_company = await _company_display_name(db, order.get("sellerId"))
    out = serialize_doc(order)
    if out:
        out["items"] = items
        out["buyerId"] = serialize_doc(buyer) if buyer else None
        out["sellerId"] = serialize_doc(seller) if seller else None
        out["buyerCompany"] = buyer_company
        out["sellerCompany"] = seller_company
        if out.get("paymentStatus") is None:
            out["paymentStatus"] = "payment_pending"
    return out


@router.get("/me")
async def get_my(request: Request, status: str | None = Query(None), user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    if user.get("role") == "admin":
        filter_q: dict = {}
    else:
        filter_q = {"sellerId": uid} if user.get("role") == "seller" else {"buyerId": uid}
    if status:
        filter_q["status"] = status
    cursor = db.orders.find(filter_q).sort("createdAt", -1)
    orders = [await _populate_order(db, o) async for o in cursor]
    return success_response(data={"orders": orders})


@router.get("/{id}")
async def get_by_id(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(order["buyerId"]) != user["id"] and str(order["sellerId"]) != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    doc = await _populate_order(db, order)
    return success_response(data={"order": doc})


@router.get("/{id}/timeline")
async def get_order_timeline(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(order["buyerId"]) != user["id"] and str(order["sellerId"]) != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    cursor = db.workflow_events.find({"entity_type": "order", "entity_id": oid}).sort("created_at", 1)
    events = [serialize_doc(e) async for e in cursor]
    return success_response(data={"timeline": events})


@router.put("/{id}/status")
async def update_status(id: str, request: Request, body: OrderStatusUpdate, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    is_seller = str(order["sellerId"]) == user["id"]
    is_admin = user.get("role") == "admin"
    if not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Only seller or admin can update order status.", "FORBIDDEN", path=str(request.url.path)))
    prev = order.get("status")
    await db.orders.update_one({"_id": oid}, {"$set": {"status": body.status}})
    etype, elabel = _ORDER_STATUS_EVENTS.get(body.status, ("ORDER_STATUS_CHANGED", f"Status: {body.status}"))
    await emit_event(
        "order",
        oid,
        ObjectId(user["id"]),
        user.get("role") or "user",
        etype,
        elabel,
        {"from": prev, "to": body.status},
    )
    buyer_id = order.get("buyerId")
    seller_id = order.get("sellerId")
    if buyer_id:
        await create_notification(
            buyer_id,
            "Order update",
            f"Your order status is now: {body.status}.",
            "order_status",
            "order",
            str(oid),
        )
    if is_admin and seller_id:
        await create_notification(
            seller_id,
            "Order update (admin)",
            f"Order {oid} status set to: {body.status}.",
            "order_status",
            "order",
            str(oid),
        )
    updated = await db.orders.find_one({"_id": oid})
    return success_response(data={"order": await _populate_order(db, updated)})


@router.put("/{id}/payment")
async def update_payment(id: str, request: Request, body: OrderPaymentUpdate, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    is_buyer = str(order["buyerId"]) == user["id"]
    is_seller = str(order["sellerId"]) == user["id"]
    is_admin = user.get("role") == "admin"
    if not (is_buyer or is_seller or is_admin):
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    prev = order.get("paymentStatus") or "payment_pending"
    await db.orders.update_one({"_id": oid}, {"$set": {"paymentStatus": body.paymentStatus}})
    ev_type = _PAYMENT_LABELS.get(body.paymentStatus, "PAYMENT_STATUS_CHANGED")
    elabel = f"Payment: {body.paymentStatus}"
    await emit_event(
        "order",
        oid,
        ObjectId(user["id"]),
        user.get("role") or "user",
        ev_type,
        elabel,
        {"from": prev, "to": body.paymentStatus},
    )
    for uid in (order.get("buyerId"), order.get("sellerId")):
        if not uid or str(uid) == str(user.get("id")):
            continue
        await create_notification(
            uid,
            "Payment status update",
            f"Order payment is now: {body.paymentStatus}.",
            "payment_status",
            "order",
            str(oid),
        )
    updated = await db.orders.find_one({"_id": oid})
    return success_response(data={"order": await _populate_order(db, updated)})
