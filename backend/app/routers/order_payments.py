"""Order escrow demo payment routes; mounted at /api/orders."""
from __future__ import annotations

import datetime
import secrets
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.subscription import PaymentSimulateBody
from app.services.workflow_events import emit_event
from app.services.notifications import create_notification
from app.services.admin_audit import admin_action_log
from app.routers import orders as orders_mod

router = APIRouter()


def _get_populate():
    return orders_mod._populate_order  # type: ignore


@router.get("/{order_id}/payments")
async def list_order_payments(
    order_id: str, request: Request, user: dict = Depends(get_current_user)
):
    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(
            status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path))
        )
    db = get_db()
    o = await db.orders.find_one({"_id": oid})
    if not o:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(o.get("buyerId")) != user.get("id") and str(o.get("sellerId")) != user.get("id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    cur = db.payments.find({"relatedEntityId": oid, "paymentType": "order_escrow"}).sort("createdAt", -1)
    return success_response(data={"payments": [serialize_doc(p) async for p in cur]})


@router.post("/{order_id}/payments/initiate")
async def initiate_order_payment(
    order_id: str, request: Request, user: dict = Depends(require_roles("buyer"))
):
    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(
            status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path))
        )
    db = get_db()
    o = await db.orders.find_one({"_id": oid})
    if not o or str(o.get("buyerId")) != str(user.get("id")):
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    st = o.get("paymentStatus") or "payment_pending"
    if st in ("escrow_held", "released", "refunded", "initiated", "processing"):
        raise HTTPException(
            status_code=409, detail=error_response("Payment already in progress or completed for this order.", "CONFLICT", path=str(request.url.path))
        )
    amt = float(o.get("totalAmount") or 0)
    now = datetime.datetime.utcnow()
    pay = {
        "userId": ObjectId(user["id"]),
        "payerRole": "buyer",
        "paymentType": "order_escrow",
        "relatedEntityType": "order",
        "relatedEntityId": oid,
        "amount": amt,
        "currency": "INR",
        "status": "initiated",
        "method": None,
        "demoReference": f"DMO-ORD-{secrets.token_hex(4).upper()}",
        "createdAt": now,
        "updatedAt": now,
    }
    r = await db.payments.insert_one(pay)
    pid = r.inserted_id
    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {
                "paymentStatus": "initiated",
                "paymentId": pid,
                "escrowStatus": o.get("escrowStatus") or "not_started",
                "updatedAt": now,
            }
        },
    )
    pdoc = await db.payments.find_one({"_id": pid})
    o2 = await db.orders.find_one({"_id": oid})
    return success_response(
        data={
            "payment": serialize_doc(pdoc),
            "order": await _get_populate()(db, o2),
        }
    )


@router.post("/{order_id}/payments/{payment_id}/simulate")
async def simulate_order_payment(
    order_id: str, payment_id: str, request: Request, body: PaymentSimulateBody, user: dict = Depends(get_current_user)
):
    try:
        oid = ObjectId(order_id)
        pid = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid id", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    o = await db.orders.find_one({"_id": oid})
    if not o:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(o.get("buyerId")) != user.get("id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Only the buyer or admin can simulate order payment.", "FORBIDDEN", path=str(request.url.path)))
    pay = await db.payments.find_one({"_id": pid, "relatedEntityId": oid})
    if not pay or pay.get("paymentType") != "order_escrow":
        raise HTTPException(status_code=404, detail=error_response("Payment not found for this order.", "NOT_FOUND", path=str(request.url.path)))
    now = datetime.datetime.utcnow()
    method = body.method
    if body.result == "success":
        await db.payments.update_one(
            {"_id": pid},
            {"$set": {"status": "escrow_held", "method": method, "updatedAt": now, "holder": "platform"}},
        )
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "paymentStatus": "escrow_held",
                    "escrowStatus": "held",
                    "escrowPaymentId": pid,
                    "updatedAt": now,
                }
            },
        )
        await create_notification(
            o["sellerId"],
            "Order payment in escrow (demo)",
            f"Order {str(oid)[:8]}: buyer's demo payment is held in SmartB2B escrow.",
            "order_escrow",
            "order",
            str(oid),
        )
        await create_notification(
            o["buyerId"],
            "Payment held in escrow (demo)",
            f"Order {str(oid)[:8]}: your demo payment is in escrow until release.",
            "order_escrow_buyer",
            "order",
            str(oid),
        )
        try:
            adm = await db.users.find_one({"role": "admin"}, projection={"_id": 1})
            if adm:
                await create_notification(adm["_id"], "Order escrow (demo)", f"Order {oid} escrow_held", "order_escrow_admin", "order", str(oid))
        except Exception:
            pass
        await emit_event(
            "order",
            oid,
            ObjectId(user["id"]),
            user.get("role") or "user",
            "PAYMENT_ESCROW_HELD",
            "Payment held in escrow (demo)",
            {"paymentId": str(pid)},
        )
        try:
            adm2 = await db.users.find_one({"role": "admin"}, projection={"_id": 1})
            if adm2:
                await admin_action_log(adm2["_id"], "ORDER_ESCROW_HELD", str(oid), {"paymentId": str(pid), "demo": True})
        except Exception:
            pass
    else:
        await db.payments.update_one(
            {"_id": pid},
            {"$set": {"status": "failed", "method": method, "updatedAt": now}},
        )
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "paymentStatus": "payment_failed",
                    "updatedAt": now,
                }
            },
        )
        await create_notification(
            o["buyerId"],
            "Order payment failed (demo)",
            "You can retry the demo payment from the order page.",
            "order_pay_failed",
            "order",
            str(oid),
        )
    o2 = await db.orders.find_one({"_id": oid})
    p2 = await db.payments.find_one({"_id": pid})
    return success_response(
        data={
            "payment": serialize_doc(p2),
            "order": await _get_populate()(db, o2),
        }
    )


@router.post("/{order_id}/payments/release")
async def release_order_escrow(
    order_id: str, request: Request, user: dict = Depends(get_current_user)
):
    is_admin = user.get("role") == "admin"
    is_buyer = user.get("role") == "buyer"
    if not is_admin and not is_buyer:
        raise HTTPException(status_code=403, detail=error_response("Only buyer or admin can release", "FORBIDDEN", path=str(request.url.path)))
    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid order ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    o = await db.orders.find_one({"_id": oid})
    if not o:
        raise HTTPException(status_code=404, detail=error_response("Order not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(o.get("buyerId")) != str(user.get("id")) and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    if (o.get("status") or "") not in ("delivered",) and not is_admin:
        raise HTTPException(
            status_code=409, detail=error_response("Order must be delivered before the buyer can release payment (admin may override in demo).", "CONFLICT", path=str(request.url.path))
        )
    if o.get("paymentStatus") not in ("escrow_held",) and o.get("escrowStatus") != "held" and not is_admin:
        raise HTTPException(
            status_code=409, detail=error_response("No escrow to release (demo).", "CONFLICT", path=str(request.url.path))
        )
    eid = o.get("escrowPaymentId") or o.get("paymentId")
    if not eid:
        raise HTTPException(status_code=400, detail=error_response("No escrow payment on order", "VALIDATION_ERROR", path=str(request.url.path)))
    eid = eid if isinstance(eid, ObjectId) else ObjectId(str(eid))
    now = datetime.datetime.utcnow()
    await db.payments.update_one({"_id": eid}, {"$set": {"status": "released", "updatedAt": now}})
    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {
                "paymentStatus": "released",
                "escrowStatus": "released",
                "updatedAt": now,
            }
        },
    )
    await create_notification(
        o["sellerId"],
        "Payment released (demo)",
        f"Escrow for order {str(oid)[:8]} was released to your notional account.",
        "order_payment_released",
        "order",
        str(oid),
    )
    await emit_event("order", oid, ObjectId(user["id"]), user.get("role") or "user", "PAYMENT_RELEASED", "Payment released to seller (demo)", {})
    o2 = await db.orders.find_one({"_id": oid})
    return success_response(data={"order": await _get_populate()(db, o2)})
