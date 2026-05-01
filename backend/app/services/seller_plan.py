"""Denormalized seller subscription plan (demo) and listing boosts."""
from __future__ import annotations

import datetime
from typing import Any

from bson import ObjectId

PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_inr": 0,
        "billing": "monthly",
        "features": [
            "Basic supplier profile & product listing",
            "View up to 3 active RFQs per day (rolling)",
            "No search ranking boost",
        ],
        "rfq_daily_cap": 3,
        "unlimited_rfq": False,
        "searchBoostWeight": 0.0,
        "featured": False,
        "analytics": "none",
    },
    "go": {
        "id": "go",
        "name": "GO",
        "price_inr": 2499,
        "billing": "monthly",
        "features": [
            "Unlimited RFQ viewing and quote replies",
            "Basic listing analytics",
            "Standard supplier listing (no ranking boost)",
        ],
        "rfq_daily_cap": None,
        "unlimited_rfq": True,
        "searchBoostWeight": 0.0,
        "featured": False,
        "analytics": "basic",
    },
    "pro": {
        "id": "pro",
        "name": "PRO",
        "price_inr": 5999,
        "billing": "monthly",
        "features": [
            "Everything in GO",
            "PRO Supplier & Featured badges",
            "Search & discovery boost",
            "Priority visibility in product & supplier results",
            "Advanced analytics (demo metrics)",
        ],
        "rfq_daily_cap": None,
        "unlimited_rfq": True,
        "searchBoostWeight": 0.35,
        "featured": True,
        "analytics": "advanced",
    },
}


def _norm_plan(p: str | None) -> str:
    s = (p or "free").lower().strip()
    if s in PLAN_CATALOG:
        return s
    return "free"


async def get_supplier_plan(db: Any, seller_id: ObjectId) -> dict[str, Any]:
    u = await db.users.find_one({"_id": seller_id}, projection={"subscriptionPlan": 1, "sellerPlanExpiresAt": 1, "isFeaturedSupplier": 1, "isProSearchBoost": 1})
    if not u:
        return {**PLAN_CATALOG["free"], "isActive": True, "source": "default"}
    plan = _norm_plan(u.get("subscriptionPlan"))
    exp = u.get("sellerPlanExpiresAt")
    if exp and isinstance(exp, datetime.datetime) and exp < datetime.datetime.utcnow() and plan != "free":
        plan = "free"
    cat = {**PLAN_CATALOG[plan], "isActive": True, "source": "user", "expiresAt": exp, "isFeatured": bool(u.get("isFeaturedSupplier") or (plan == "pro")), "isProSearchBoost": bool(u.get("isProSearchBoost") is not False and plan == "pro")}
    return cat


def plan_badge_and_flags(plan: dict[str, Any], verified: bool) -> dict[str, Any]:
    pid = plan.get("id", "free")
    label = f"{(plan.get('name') or 'Free')} Supplier" if pid != "pro" else "PRO Supplier"
    return {
        "subscriptionPlan": pid,
        "subscriptionLabel": plan.get("name", "Free"),
        "isFeaturedSupplier": bool(plan.get("featured")),
        "searchBoostLabel": "Priority visibility" if pid == "pro" else None,
        "verifiedSupplier": bool(verified),
        "planBadge": label,
        "featuredBadge": bool(plan.get("featured") and pid == "pro"),
    }


def search_sort_key(
    plan_id: str,
    trust: float,
    is_verified: bool,
    *,
    mode: str = "recommended",
) -> tuple:
    p = _norm_plan(plan_id)
    boost = PLAN_CATALOG[p].get("searchBoostWeight", 0.0)
    if mode == "pro_first":
        return (0.0 if p == "pro" else 1.0, -float(trust or 0), not is_verified)
    if mode == "trust":
        return (-float(trust or 0), 0.0 if p == "pro" else 1.0, not is_verified)
    # recommended: blend PRO, trust, verification
    score = (5.0 if p == "pro" else 0.0) + float(trust or 0) * 0.01 + (1.0 if is_verified else 0.0) + boost * 3.0
    return (-score, str(plan_id), -float(trust or 0))


def rfq_list_limit_for_plan(plan: dict) -> int | None:
    if plan.get("unlimited_rfq"):
        return None
    return int(plan.get("rfq_daily_cap") or 3)
