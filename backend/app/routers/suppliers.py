from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.schemas.common import success_response, error_response, serialize_doc
from app.services.supplier_score import get_supplier_score_for_response, recalculate_supplier_score

router = APIRouter()


@router.get("/{seller_id}/score")
async def get_supplier_score(seller_id: str, request: Request):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    user = await db.users.find_one({"_id": oid}, projection={"role": 1})
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=404, detail=error_response("Supplier not found.", "NOT_FOUND", path=str(request.url.path)))
    score = await get_supplier_score_for_response(oid)
    if not score:
        raise HTTPException(status_code=404, detail=error_response("Score not found.", "NOT_FOUND", path=str(request.url.path)))
    return success_response(data={"score": score})


@router.get("/{seller_id}/profile")
async def get_supplier_profile(seller_id: str, request: Request):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    seller = await db.users.find_one({"_id": oid}, projection={"password": 0})
    if not seller or seller.get("role") != "seller":
        raise HTTPException(status_code=404, detail=error_response("Supplier not found.", "NOT_FOUND", path=str(request.url.path)))
    profile = await db.companyprofiles.find_one({"user": oid})
    score_data = await get_supplier_score_for_response(oid)
    total_products_active = await db.products.count_documents({"seller": oid, "isActive": True})
    total_products_all = await db.products.count_documents({"seller": oid})
    my_product_ids = await db.products.find({"seller": oid}, {"_id": 1}).distinct("_id")
    rfqs_received = await db.rfqs.count_documents({"items.productId": {"$in": my_product_ids}}) if my_product_ids else 0
    quotes_submitted = await db.quotes.count_documents({"sellerId": oid})
    quotes_accepted = await db.quotes.count_documents({"sellerId": oid, "status": "accepted"})
    orders_fulfilled = await db.orders.count_documents({"sellerId": oid})
    response_rate = (min(100, (quotes_submitted / rfqs_received) * 100)) if rfqs_received else 0
    quote_acceptance_rate = round((quotes_accepted / quotes_submitted) * 100, 1) if quotes_submitted else 0.0
    categories_served = await db.products.distinct("category", {"seller": oid, "isActive": True})
    city = (profile or {}).get("city") or ""
    # average_rating: derived from supplier score buyer_rating component (0–100) → 1–5 for display (no separate review collection).
    br = float((score_data or {}).get("buyer_rating", 70) or 70)
    average_rating = round(min(5.0, max(1.0, br / 20.0)), 2)
    quotes_with_dates = await db.quotes.find({"sellerId": oid}, projection={"rfqId": 1, "createdAt": 1}).to_list(100)
    response_times = []
    for q in quotes_with_dates:
        rfq_row = await db.rfqs.find_one({"_id": q["rfqId"]}, projection={"createdAt": 1}) if q.get("rfqId") else None
        if rfq_row and rfq_row.get("createdAt") and q.get("createdAt"):
            delta = (q["createdAt"] - rfq_row["createdAt"]).total_seconds() / 3600
            response_times.append(delta)
    avg_response_hours = round(sum(response_times) / len(response_times), 1) if response_times else None
    recent_products = []
    async for p in db.products.find({"seller": oid, "isActive": True}).sort("createdAt", -1).limit(8):
        recent_products.append(serialize_doc(p))
    recent_activity = []
    async for ev in db.workflow_events.find({"actor_id": oid}).sort("created_at", -1).limit(12):
        recent_activity.append(serialize_doc(ev))
    return success_response(data={
        "profile": {
            "seller_id": str(oid),
            "seller_name": seller.get("name"),
            "email": seller.get("email"),
            "seller": serialize_doc(seller),
            "company": serialize_doc(profile) if profile else None,
            "company_name": (profile or {}).get("companyName") or seller.get("name"),
            "verified": bool(seller.get("isVerifiedSupplier")),
            "verified_supplier": bool(seller.get("isVerifiedSupplier")),
            "trust_score": (score_data or {}).get("total_score", 0),
            "trust_level": (score_data or {}).get("trust_level", "Low Trust"),
            "response_rate": round(response_rate, 1),
            "average_response_time_hours": avg_response_hours,
            "total_products": total_products_active,
            "active_products": total_products_active,
            "total_products_all": total_products_all,
            "rfqs_received": rfqs_received,
            "total_rfqs_received": rfqs_received,
            "quotes_submitted": quotes_submitted,
            "total_quotes_submitted": quotes_submitted,
            "quote_acceptance_rate": quote_acceptance_rate,
            "orders_fulfilled": orders_fulfilled,
            "total_orders_fulfilled": orders_fulfilled,
            "average_rating": average_rating,
            "city": city,
            "categories_served": categories_served,
            "recent_products": recent_products,
            "recent_activity": recent_activity,
        }
    })
