"""Demo subscription checkout (no real PSP)."""
from __future__ import annotations

import datetime
import secrets
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.subscription import SubscriptionCheckoutBody, PaymentSimulateBody
from app.services.seller_plan import PLAN_CATALOG, get_supplier_plan
from app.services.admin_audit import admin_action_log
from app.services.notifications import create_notification

router = APIRouter()


@router.get("/plans")
async def get_plans(_request: Request, _user: dict = Depends(get_current_user)):
    """Plan catalog; requires login."""
    plans = [PLAN_CATALOG["free"], PLAN_CATALOG["go"], PLAN_CATALOG["pro"]]
    return success_response(data={"plans": plans})


@router.get("/me", dependencies=[Depends(require_roles("seller"))])
async def get_my_subscription(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    current = await get_supplier_plan(db, uid)
    sub = await db.seller_subscriptions.find_one({"sellerId": uid}, sort=[("createdAt", -1)])
    return success_response(
        data={
            "currentPlan": current,
            "subscription": serialize_doc(sub) if sub else None,
        }
    )


@router.post("/checkout")
async def checkout(request: Request, body: SubscriptionCheckoutBody, user: dict = Depends(require_roles("seller"))):
    if body.plan not in ("go", "pro"):
        raise HTTPException(status_code=400, detail=error_response("Invalid plan", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    uid = ObjectId(user["id"])
    price = int(PLAN_CATALOG[body.plan]["price_inr"])
    now = datetime.datetime.utcnow()
    sub_doc = {
        "sellerId": uid,
        "plan": body.plan,
        "status": "inactive",
        "startedAt": None,
        "expiresAt": None,
        "billingCycle": "monthly",
        "amount": price,
        "currency": "INR",
        "paymentId": None,
        "createdAt": now,
        "updatedAt": now,
    }
    sr = await db.seller_subscriptions.insert_one(sub_doc)
    sub_id = sr.inserted_id
    pay_doc = {
        "userId": uid,
        "payerRole": "seller",
        "paymentType": "subscription",
        "relatedEntityType": "subscription",
        "relatedEntityId": sub_id,
        "amount": price,
        "currency": "INR",
        "status": "initiated",
        "method": None,
        "demoReference": f"DMO-SUB-{secrets.token_hex(4).upper()}",
        "createdAt": now,
        "updatedAt": now,
    }
    pr = await db.payments.insert_one(pay_doc)
    pay_id = pr.inserted_id
    await db.seller_subscriptions.update_one({"_id": sub_id}, {"$set": {"paymentId": pay_id, "updatedAt": now}})
    payment = await db.payments.find_one({"_id": pay_id})
    return success_response(
        data={
            "payment": serialize_doc(payment),
            "subscriptionId": str(sub_id),
            "checkoutPath": f"/seller/subscription/checkout/{str(pay_id)}",
        }
    )


@router.post("/payment/{payment_id}/simulate")
async def simulate_payment(
    request: Request,
    payment_id: str,
    body: PaymentSimulateBody,
    user: dict = Depends(require_roles("seller")),
):
    try:
        pid = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid payment id", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    uid = ObjectId(user["id"])
    pay = await db.payments.find_one({"_id": pid})
    if not pay or pay.get("paymentType") != "subscription":
        raise HTTPException(status_code=404, detail=error_response("Payment not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(pay.get("userId")) != str(uid):
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    now = datetime.datetime.utcnow()
    method = body.method
    if body.result == "success":
        rel = pay.get("relatedEntityId")
        if not rel:
            raise HTTPException(status_code=400, detail=error_response("Orphan payment", "VALIDATION_ERROR", path=str(request.url.path)))
        sub = await db.seller_subscriptions.find_one({"_id": rel})
        if not sub:
            raise HTTPException(status_code=404, detail=error_response("Subscription not found", "NOT_FOUND", path=str(request.url.path)))
        plan = sub.get("plan") or "go"
        expires = now + datetime.timedelta(days=30)
        await db.payments.update_one(
            {"_id": pid},
            {"$set": {"status": "success", "method": method, "updatedAt": now}},
        )
        await db.seller_subscriptions.update_one(
            {"_id": rel},
            {
                "$set": {
                    "status": "active",
                    "startedAt": now,
                    "expiresAt": expires,
                    "updatedAt": now,
                }
            },
        )
        await db.users.update_one(
            {"_id": uid},
            {
                "$set": {
                    "subscriptionPlan": plan,
                    "sellerPlanExpiresAt": expires,
                    "isFeaturedSupplier": plan == "pro",
                    "isProSearchBoost": plan == "pro",
                }
            },
        )
        await create_notification(
            uid,
            "Subscription active",
            f"Your {plan.upper()} plan is now active (demo).",
            "subscription_active",
            "subscription",
            str(rel),
        )
        try:
            adm = await db.users.find_one({"role": "admin"}, projection={"_id": 1})
            if adm:
                await admin_action_log(
                    adm["_id"],
                    "SUBSCRIPTION_ACTIVATED",
                    str(uid),
                    {"plan": plan, "paymentId": str(pid), "demo": True},
                )
        except Exception:
            pass
    else:
        await db.payments.update_one(
            {"_id": pid},
            {"$set": {"status": "failed", "method": method, "updatedAt": now}},
        )
        if pay.get("relatedEntityId"):
            await db.seller_subscriptions.update_one(
                {"_id": pay["relatedEntityId"]},
                {"$set": {"status": "cancelled", "updatedAt": now}},
            )
        await create_notification(
            uid,
            "Subscription payment failed (demo)",
            "You can start checkout again from the subscription page.",
            "subscription_failed",
            "payment",
            str(pid),
        )
    updated = await db.payments.find_one({"_id": pid})
    return success_response(data={"payment": serialize_doc(updated), "ok": body.result == "success"})
