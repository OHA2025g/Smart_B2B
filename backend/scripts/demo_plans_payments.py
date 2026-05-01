"""Apply subscription tiers and demo order payments after bulk generate_demo_data."""
from __future__ import annotations

import datetime
import secrets
from bson import ObjectId

GO_INR = 2499
PRO_INR = 5999


def _sub_payment_doc(user_id: ObjectId, amount: int, method: str, ref: str, now) -> dict:
    return {
        "userId": user_id,
        "payerRole": "seller",
        "paymentType": "subscription",
        "relatedEntityType": "subscription",
        "relatedEntityId": None,
        "amount": amount,
        "currency": "INR",
        "status": "success",
        "method": method,
        "demoReference": ref,
        "createdAt": now,
        "updatedAt": now,
    }


async def _insert_active_subscription(
    db, seller_id: ObjectId, plan: str, amount: int, ex, now, method: str, ref: str
) -> None:
    pr = await db.payments.insert_one(_sub_payment_doc(seller_id, amount, method, ref, now))
    subr = await db.seller_subscriptions.insert_one(
        {
            "sellerId": seller_id,
            "plan": plan,
            "status": "active",
            "startedAt": now,
            "expiresAt": ex,
            "billingCycle": "monthly",
            "amount": amount,
            "currency": "INR",
            "paymentId": pr.inserted_id,
            "createdAt": now,
            "updatedAt": now,
        }
    )
    await db.payments.update_one(
        {"_id": pr.inserted_id},
        {"$set": {"relatedEntityId": subr.inserted_id}},
    )


async def apply_demo_plans_payments(
    db,
    all_sellers: list[ObjectId],
    seller_id: ObjectId,
    _buyer_id: ObjectId,
    free_tier_id: ObjectId,
    go_tier_id: ObjectId,
    pro_tier_id: ObjectId,
) -> None:
    """
    - seller@example.com and freesupplier@: Free (normal suppliers)
    - gosupplier@: active GO
    - prosupplier@: active PRO (featured)
    - Remaining bulk sellers: 8/8/8 free/go/pro sample (excluding tier demo ids)
    """
    now = datetime.datetime.utcnow()
    ex = now + datetime.timedelta(days=30)

    # Default "main" demo seller + dedicated free account: no paid plan
    for uid, label in [(seller_id, "main"), (free_tier_id, "free_tier")]:
        await db.users.update_one(
            {"_id": uid},
            {
                "$set": {
                    "subscriptionPlan": "free",
                    "sellerPlanExpiresAt": None,
                    "isFeaturedSupplier": False,
                    "isProSearchBoost": False,
                }
            },
        )

    # GO classroom account
    ex_go = now + datetime.timedelta(days=30)
    await db.users.update_one(
        {"_id": go_tier_id},
        {
            "$set": {
                "subscriptionPlan": "go",
                "sellerPlanExpiresAt": ex_go,
                "isFeaturedSupplier": False,
                "isProSearchBoost": False,
            }
        },
    )
    await _insert_active_subscription(
        db, go_tier_id, "go", GO_INR, ex_go, now, "demo_upi", f"SEED-GO-CLASSROOM-{secrets.token_hex(2).upper()}"
    )

    # PRO classroom account
    ex_pro = now + datetime.timedelta(days=30)
    await db.users.update_one(
        {"_id": pro_tier_id},
        {
            "$set": {
                "subscriptionPlan": "pro",
                "sellerPlanExpiresAt": ex_pro,
                "isFeaturedSupplier": True,
                "isProSearchBoost": True,
            }
        },
    )
    await _insert_active_subscription(
        db, pro_tier_id, "pro", PRO_INR, ex_pro, now, "demo_card", f"SEED-PRO-CLASSROOM-{secrets.token_hex(2).upper()}"
    )

    # Next 24 demo sellers (skip preserved tier accounts and main seller)
    skip = {seller_id, free_tier_id, go_tier_id, pro_tier_id}
    others = sorted([s for s in all_sellers if s not in skip], key=str)
    chunk = (others * 2)[:24] if len(others) < 24 else others[:24]
    for i, sid in enumerate(chunk):
        if i < 8:
            plan, feat, amt = "free", False, 0
        elif i < 16:
            plan, feat, amt = "go", False, GO_INR
        else:
            plan, feat, amt = "pro", True, PRO_INR
        ex2 = now + datetime.timedelta(days=20 + (i % 7))
        await db.users.update_one(
            {"_id": sid},
            {
                "$set": {
                    "subscriptionPlan": plan,
                    "sellerPlanExpiresAt": ex2 if plan != "free" else None,
                    "isFeaturedSupplier": bool(feat),
                    "isProSearchBoost": bool(feat),
                }
            },
        )
        if plan == "free":
            continue
        pdoc = {
            "userId": sid,
            "payerRole": "seller",
            "paymentType": "subscription",
            "relatedEntityType": "subscription",
            "relatedEntityId": None,
            "amount": amt,
            "currency": "INR",
            "status": "success",
            "method": "demo_card" if i % 2 == 0 else "demo_upi",
            "demoReference": f"SEED-PLAN-{i}-{plan}",
            "createdAt": now,
            "updatedAt": now,
        }
        pr = await db.payments.insert_one(pdoc)
        subr = await db.seller_subscriptions.insert_one(
            {
                "sellerId": sid,
                "plan": plan,
                "status": "active",
                "startedAt": now,
                "expiresAt": ex2,
                "billingCycle": "monthly",
                "amount": amt,
                "currency": "INR",
                "paymentId": pr.inserted_id,
                "createdAt": now,
                "updatedAt": now,
            }
        )
        await db.payments.update_one(
            {"_id": pr.inserted_id},
            {"$set": {"relatedEntityId": subr.inserted_id}},
        )
    # Vary some orders' payment/escrow (first 50)
    olist = [o async for o in db.orders.find({})]
    for idx, o in enumerate(olist[:50]):
        r, b = o["_id"], o.get("buyerId")
        tot = float(o.get("totalAmount") or 0)
        if not b or tot <= 0:
            continue
        st = o.get("status", "created")
        if idx % 5 == 0:
            await db.orders.update_one(
                {"_id": r},
                {"$set": {"paymentStatus": "payment_pending", "escrowStatus": "not_started", "status": st}},
            )
        elif idx % 5 == 1:
            pay = await db.payments.insert_one(
                {
                    "userId": b,
                    "payerRole": "buyer",
                    "paymentType": "order_escrow",
                    "relatedEntityType": "order",
                    "relatedEntityId": r,
                    "amount": tot,
                    "currency": "INR",
                    "status": "escrow_held",
                    "method": "demo_card",
                    "demoReference": f"SEED-ESCROW-{r}",
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
            await db.orders.update_one(
                {"_id": r},
                {
                    "$set": {
                        "paymentStatus": "escrow_held",
                        "escrowStatus": "held",
                        "escrowPaymentId": pay.inserted_id,
                        "paymentId": pay.inserted_id,
                        "status": st,
                    }
                },
            )
        elif idx % 5 == 2:
            pf = await db.payments.insert_one(
                {
                    "userId": b,
                    "payerRole": "buyer",
                    "paymentType": "order_escrow",
                    "relatedEntityType": "order",
                    "relatedEntityId": r,
                    "amount": tot,
                    "currency": "INR",
                    "status": "failed",
                    "method": "demo_upi",
                    "demoReference": f"SEED-FAIL-{r}",
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
            await db.orders.update_one(
                {"_id": r},
                {
                    "$set": {
                        "paymentStatus": "payment_failed",
                        "escrowStatus": "not_started",
                        "lastPaymentId": pf.inserted_id,
                        "status": st,
                    }
                },
            )
        elif idx % 5 == 3:
            pr2 = await db.payments.insert_one(
                {
                    "userId": b,
                    "payerRole": "buyer",
                    "paymentType": "order_escrow",
                    "relatedEntityType": "order",
                    "relatedEntityId": r,
                    "amount": tot,
                    "currency": "INR",
                    "status": "released",
                    "method": "demo_upi",
                    "demoReference": f"SEED-REL-{r}",
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
            await db.orders.update_one(
                {"_id": r},
                {
                    "$set": {
                        "paymentStatus": "released",
                        "escrowStatus": "released",
                        "escrowPaymentId": pr2.inserted_id,
                        "status": st,
                    }
                },
            )
    print("14. Applied demo subscription tiers + order payment status samples...")
