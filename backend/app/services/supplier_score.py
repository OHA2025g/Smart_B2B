"""
Supplier Trust Score and Quote Ranking.

Trust score formula (each component 0-100, weights sum to 1.0):
  0.30 * profile_completeness
  + 0.20 * response_rate
  + 0.20 * product_strength
  + 0.15 * buyer_rating
  + 0.15 * verified_status

verified_status: 100 if admin-verified supplier, else 0.

Trust levels: 85-100 Highly Trusted, 70-84 Trusted, 50-69 Moderate, <50 Low Trust

Defaults when data is thin:
- response_rate: 50
- product_strength: 50 if no active products, else min(100, 10 * active_count)
- buyer_rating: 70 (until real reviews exist)

Quote score (for buyer comparison):
  50% price competitiveness + 25% delivery speed + 25% supplier trust score
"""
from __future__ import annotations

import datetime
from typing import Any

from bson import ObjectId

from app.database import get_db

TRUST_WEIGHTS: dict[str, float] = {
    "profile_completeness": 0.30,
    "response_rate": 0.20,
    "product_strength": 0.20,
    "buyer_rating": 0.15,
    "verified_status": 0.15,
}

DEFAULT_RESPONSE_RATE = 50.0
DEFAULT_PRODUCT_STRENGTH = 50.0
DEFAULT_BUYER_RATING = 70.0


def _trust_level_from_score(score: float) -> str:
    s = float(score)
    if s >= 85:
        return "Highly Trusted"
    if s >= 70:
        return "Trusted"
    if s >= 50:
        return "Moderate"
    return "Low Trust"


def _compute_weighted_total(
    profile_completeness: float,
    response_rate: float,
    product_strength: float,
    buyer_rating: float,
    verified_status: float,
) -> float:
    """Return 0-100. Weights must sum to 1.0."""
    return float(
        TRUST_WEIGHTS["profile_completeness"] * profile_completeness
        + TRUST_WEIGHTS["response_rate"] * response_rate
        + TRUST_WEIGHTS["product_strength"] * product_strength
        + TRUST_WEIGHTS["buyer_rating"] * buyer_rating
        + TRUST_WEIGHTS["verified_status"] * verified_status
    )


async def get_or_create_supplier_score(seller_id: ObjectId) -> dict:
    db = get_db()
    doc = await db.supplier_scores.find_one({"seller_id": seller_id})
    if doc:
        return doc
    new_doc: dict[str, Any] = {
        "seller_id": seller_id,
        "profile_completeness": 0,
        "response_rate": 0,
        "product_strength": 0,
        "buyer_rating": 0,
        "verified_status": 0,
        "total_score": 0,
        "trust_level": "Low Trust",
    }
    await db.supplier_scores.insert_one(new_doc)
    return new_doc


async def recalculate_supplier_score(seller_id: ObjectId) -> dict | None:
    db = get_db()
    seller = await db.users.find_one({"_id": seller_id})
    if not seller:
        return None

    profile = await db.companyprofiles.find_one({"user": seller_id})
    profile_score = 0.0
    if profile:
        fields = ["companyName", "description", "city", "state", "country", "phone", "website", "gstNumber"]
        filled = sum(1 for f in fields if profile.get(f))
        profile_score = min(100.0, (filled / len(fields)) * 100.0) if fields else 0.0

    my_products = await db.products.find({"seller": seller_id, "isActive": True}, {"_id": 1}).to_list(10000)
    my_pids = [p["_id"] for p in my_products]
    quotes_count = await db.quotes.count_documents({"sellerId": seller_id})
    if not my_pids:
        response_rate = DEFAULT_RESPONSE_RATE
    else:
        rfqs_with_my_products = await db.rfqs.count_documents({"items.productId": {"$in": my_pids}})
        if rfqs_with_my_products <= 0:
            response_rate = DEFAULT_RESPONSE_RATE
        else:
            response_rate = min(100.0, (quotes_count / rfqs_with_my_products) * 100.0)

    products_count = await db.products.count_documents({"seller": seller_id, "isActive": True})
    if products_count == 0:
        product_strength = DEFAULT_PRODUCT_STRENGTH
    else:
        product_strength = min(100.0, products_count * 10.0)

    buyer_rating = DEFAULT_BUYER_RATING
    verified_status = 100.0 if seller.get("isVerifiedSupplier") else 0.0

    total = _compute_weighted_total(
        profile_completeness=profile_score,
        response_rate=response_rate,
        product_strength=product_strength,
        buyer_rating=buyer_rating,
        verified_status=verified_status,
    )
    total = round(min(100.0, max(0.0, total)), 1)
    trust_level = _trust_level_from_score(total)

    await get_or_create_supplier_score(seller_id)
    update: dict[str, Any] = {
        "profile_completeness": round(profile_score, 1),
        "response_rate": round(response_rate, 1),
        "product_strength": round(product_strength, 1),
        "buyer_rating": round(buyer_rating, 1),
        "verified_status": round(verified_status, 1),
        "total_score": total,
        "trust_level": trust_level,
        "updated_at": datetime.datetime.utcnow(),
    }
    await db.supplier_scores.update_one({"seller_id": seller_id}, {"$set": update})
    return await db.supplier_scores.find_one({"seller_id": seller_id})


def score_doc_to_api(doc: dict | None) -> dict | None:
    if not doc:
        return None
    sid = doc.get("seller_id")
    ua = doc.get("updated_at")
    if hasattr(ua, "isoformat"):
        ua = ua.isoformat() + "Z"
    return {
        "seller_id": str(sid) if sid else None,
        "profile_completeness": doc.get("profile_completeness", 0),
        "response_rate": doc.get("response_rate", 0),
        "product_strength": doc.get("product_strength", 0),
        "buyer_rating": doc.get("buyer_rating", 0),
        "verified_status": doc.get("verified_status", 0),
        "total_score": doc.get("total_score", 0),
        "trust_level": doc.get("trust_level", "Low Trust"),
        "updated_at": ua,
        "weights": TRUST_WEIGHTS,
    }


async def get_supplier_score_for_response(seller_id: ObjectId) -> dict | None:
    """Return stored score; ensure at least one calculation has run (updated_at set)."""
    doc = await get_or_create_supplier_score(seller_id)
    if doc and doc.get("updated_at") is None:
        await recalculate_supplier_score(seller_id)
        doc = await get_db().supplier_scores.find_one({"seller_id": seller_id})
    if not doc:
        return None
    return score_doc_to_api(doc)


def compute_quote_score(quote_items: list, rfq_items: list, supplier_total_score: float, all_quotes_total: list) -> float:
    """
    quote_score = 50% price competitiveness + 25% delivery speed + 25% supplier trust (0-100).
    Price competitiveness: lower is better; normalize against other quotes.
    Delivery: lower days is better; normalize to 0-100.
    """
    if not quote_items:
        return round((supplier_total_score or 0) * 0.25, 1)
    total_price = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in quote_items)
    avg_delivery = sum(it.get("deliveryDays") or 7 for it in quote_items) / len(quote_items)
    if not all_quotes_total:
        price_score = 80.0
    else:
        max_total = max(all_quotes_total)
        if max_total <= 0:
            price_score = 80.0
        else:
            price_score = max(0, 100 - (total_price / max_total) * 100)
    delivery_score = max(0, min(100, 100 - (avg_delivery / 14) * 100))
    score = 0.5 * price_score + 0.25 * delivery_score + 0.25 * (supplier_total_score or 0)
    return round(min(100, max(0, score)), 1)
