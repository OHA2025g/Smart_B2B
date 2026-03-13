import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.order import OrderStatusUpdate
from app.services.workflow_events import emit_event

router = APIRouter()


async def _populate_order(db, order):
    items = []
    for it in order.get("items", []):
        prod = await db.products.find_one({"_id": it.get("productId")}) if it.get("productId") else None
        doc = dict(it)
        doc["productId"] = serialize_doc(prod) if prod else None
        items.append(doc)
    buyer = await db.users.find_one({"_id": order["buyerId"]}, projection={"name": 1, "email": 1}) if order.get("buyerId") else None
    seller = await db.users.find_one({"_id": order["sellerId"]}, projection={"name": 1, "email": 1}) if order.get("sellerId") else None
    out = serialize_doc(order)
    if out:
        out["items"] = items
        out["buyerId"] = serialize_doc(buyer) if buyer else None
        out["sellerId"] = serialize_doc(seller) if seller else None
    return out


@router.get("/me")
async def get_my(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    filter_q = {"sellerId": uid} if user.get("role") == "seller" else {"buyerId": uid}
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
    if str(order["sellerId"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Only seller can update order status.", "FORBIDDEN", path=str(request.url.path)))
    await db.orders.update_one({"_id": oid}, {"$set": {"status": body.status}})
    await emit_event("order", oid, ObjectId(user["id"]), "seller", "ORDER_STATUS_CHANGED", "Order status changed", {"from": order.get("status"), "to": body.status})
    updated = await db.orders.find_one({"_id": oid})
    return success_response(data={"order": await _populate_order(db, updated)})
