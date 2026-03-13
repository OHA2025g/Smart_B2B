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
    total_products = await db.products.count_documents({"seller": oid, "isActive": True})
    my_product_ids = await db.products.find({"seller": oid}, {"_id": 1}).distinct("_id")
    rfqs_received = await db.rfqs.count_documents({"items.productId": {"$in": my_product_ids}}) if my_product_ids else 0
    quotes_submitted = await db.quotes.count_documents({"sellerId": oid})
    orders_fulfilled = await db.orders.count_documents({"sellerId": oid})
    response_rate = (min(100, (quotes_submitted / rfqs_received) * 100)) if rfqs_received else 0
    categories_served = await db.products.distinct("category", {"seller": oid, "isActive": True})
    city = (profile or {}).get("city") or ""
    average_rating = (score_data or {}).get("buyer_rating", 70)
    return success_response(data={
        "profile": {
            "seller": serialize_doc(seller),
            "company": serialize_doc(profile) if profile else None,
            "verified": bool(seller.get("isVerifiedSupplier")),
            "trust_score": (score_data or {}).get("total_score", 0),
            "trust_level": (score_data or {}).get("trust_level", "Low Trust"),
            "response_rate": round(response_rate, 1),
            "total_products": total_products,
            "rfqs_received": rfqs_received,
            "quotes_submitted": quotes_submitted,
            "orders_fulfilled": orders_fulfilled,
            "average_rating": average_rating,
            "city": city,
            "categories_served": categories_served,
        }
    })
