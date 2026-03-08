"""
Supplier Trust Score and Quote Ranking.

Trust score formula:
  30% profile_completeness + 20% response_rate + 20% product_strength
  + 15% buyer_rating + 15% verified_status

Trust levels: 85-100 Highly Trusted, 70-84 Trusted, 50-69 Moderate, <50 Low Trust

Quote score (for buyer comparison):
  50% price competitiveness + 25% delivery speed + 25% supplier trust score
"""
from bson import ObjectId
from app.database import get_db

TRUST_WEIGHTS = {
    "profile_completeness": 0.30,
    "response_rate": 0.20,
    "product_strength": 0.20,
    "buyer_rating": 0.15,
    "verified_status": 0.15,
}

TRUST_LEVELS = [
    (85, 100, "Highly Trusted"),
    (70, 85, "Trusted"),
    (50, 70, "Moderate"),
    (0, 50, "Low Trust"),
]


def _trust_level_from_score(score: float) -> str:
    for low, high, label in TRUST_LEVELS:
        if low <= score < high or (high == 100 and score == 100):
            return label
    return "Low Trust"


async def get_or_create_supplier_score(seller_id: ObjectId) -> dict:
    db = get_db()
    doc = await db.supplier_scores.find_one({"seller_id": seller_id})
    if doc:
        return doc
    # Create with defaults; recalculate will fill in
    new_doc = {
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


async def recalculate_supplier_score(seller_id: ObjectId) -> dict:
    db = get_db()
    seller = await db.users.find_one({"_id": seller_id})
    if not seller:
        return None

    # Profile completeness: company profile fields filled
    profile = await db.companyprofiles.find_one({"user": seller_id})
    profile_score = 0.0
    if profile:
        fields = ["companyName", "description", "city", "state", "country", "phone", "website", "gstNumber"]
        filled = sum(1 for f in fields if profile.get(f))
        profile_score = min(100, (filled / len(fields)) * 100) if fields else 0

    # Response rate: quotes submitted / RFQs where seller could quote (simplified: use 80% default if has quotes)
    quotes_count = await db.quotes.count_documents({"sellerId": seller_id})
    rfqs_with_my_products = await db.rfqs.count_documents({"items.productId": {"$in": [p["_id"] for p in await db.products.find({"seller": seller_id}, {"_id": 1}).to_list(None)]}})
    response_rate = 80.0
    if rfqs_with_my_products > 0:
        response_rate = min(100, (quotes_count / rfqs_with_my_products) * 100)

    # Product strength: active products count, capped at 100 (e.g. 10+ products = 100)
    products_count = await db.products.count_documents({"seller": seller_id, "isActive": True})
    product_strength = min(100, products_count * 10)

    # Buyer rating: placeholder (no reviews yet) - use 70 default
    buyer_rating = 70.0

    # Verified status: 100 if verified, 0 otherwise
    verified_status = 100.0 if seller.get("isVerifiedSupplier") else 0.0

    total = (
        TRUST_WEIGHTS["profile_completeness"] * profile_score
        + TRUST_WEIGHTS["response_rate"] * response_rate
        + TRUST_WEIGHTS["product_strength"] * product_strength
        + TRUST_WEIGHTS["buyer_rating"] * buyer_rating
        + TRUST_WEIGHTS["verified_status"] * verified_status
    ) * 100 / (sum(TRUST_WEIGHTS.values()))  # normalize to 0-100
    total = round(min(100, max(0, total)), 1)
    trust_level = _trust_level_from_score(total)

    doc = await get_or_create_supplier_score(seller_id)
    import datetime
    update = {
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


async def get_supplier_score_for_response(seller_id: ObjectId) -> dict | None:
    doc = await get_or_create_supplier_score(seller_id)
    if not doc or doc.get("total_score") is None:
        await recalculate_supplier_score(seller_id)
        doc = await get_db().supplier_scores.find_one({"seller_id": seller_id})
    if not doc:
        return None
    sid = doc.get("seller_id") or doc.get("sellerId")
    return {
        "seller_id": str(sid) if sid else None,
        "profile_completeness": doc.get("profile_completeness", 0),
        "response_rate": doc.get("response_rate", 0),
        "product_strength": doc.get("product_strength", 0),
        "buyer_rating": doc.get("buyer_rating", 0),
        "verified_status": doc.get("verified_status", 0),
        "total_score": doc.get("total_score", 0),
        "trust_level": doc.get("trust_level", "Low Trust"),
    }


def compute_quote_score(quote_items: list, rfq_items: list, supplier_total_score: float, all_quotes_total: list) -> float:
    """
    quote_score = 50% price competitiveness + 25% delivery speed + 25% supplier trust (0-100).
    Price competitiveness: lower is better; normalize against other quotes.
    Delivery: lower days is better; normalize to 0-100.
    """
    if not quote_items:
        return round(supplier_total_score * 0.25, 1)
    total_price = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in quote_items)
    avg_delivery = sum(it.get("deliveryDays") or 7 for it in quote_items) / len(quote_items)
    # Price: invert so lower price = higher score. Use 100 - (pct of max). If single quote use 80.
    if not all_quotes_total:
        price_score = 80.0
    else:
        max_total = max(all_quotes_total)
        if max_total <= 0:
            price_score = 80.0
        else:
            price_score = max(0, 100 - (total_price / max_total) * 100)
    # Delivery: 0 days = 100, 14+ days = 0 linear
    delivery_score = max(0, min(100, 100 - (avg_delivery / 14) * 100))
    score = 0.5 * price_score + 0.25 * delivery_score + 0.25 * (supplier_total_score or 0)
    return round(min(100, max(0, score)), 1)
