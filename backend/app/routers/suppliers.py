import re
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Query
from app.database import get_db
from app.schemas.common import success_response, error_response, serialize_doc
from app.services.supplier_score import TRUST_WEIGHTS, get_supplier_score_for_response
from app.services.seller_plan import get_supplier_plan, plan_badge_and_flags, search_sort_key

router = APIRouter()


@router.get("")
async def list_suppliers(
    request: Request,
    search: str | None = Query(None, description="Company or seller name / email"),
    city: str | None = Query(None),
    category: str | None = Query(None, description="Match if supplier has a product in this category"),
    verified_only: bool | None = Query(None),
    trust_level: str | None = Query(None),
    sort: str = Query("trust", description="trust, orders, products, name, recommended, pro_first"),
    plan: str | None = Query(None, description="free, go, pro"),
    limit: int = Query(50, le=200, ge=1),
    skip: int = Query(0, ge=0),
):
    """Public + auth: discover suppliers (sellers) with trust metadata."""
    db = get_db()
    q = {"role": "seller"}
    if verified_only is True:
        q["isVerifiedSupplier"] = True
    cursor = db.users.find(q, {"password": 0}).sort("name", 1)
    rows = []
    async for seller in cursor:
        oid = seller["_id"]
        prof = await db.companyprofiles.find_one({"user": oid})
        cname = (prof or {}).get("companyName") or seller.get("name") or ""
        em = (seller.get("email") or "").lower()
        c = ((prof or {}).get("city") or "").lower()
        if search:
            s = search.lower()
            if s not in cname.lower() and s not in em and s not in (seller.get("name") or "").lower():
                continue
        if city and city.lower() not in c:
            continue
        if category:
            has = await db.products.find_one(
                {"seller": oid, "isActive": True, "category": re.compile(re.escape(category), re.I)}
            )
            if not has:
                continue
        score_data = await get_supplier_score_for_response(oid) or {}
        ts = int(score_data.get("total_score", 0) or 0)
        tl = str(score_data.get("trust_level", "Low Trust") or "")
        if trust_level and trust_level.lower() not in tl.lower():
            continue
        n_products = await db.products.count_documents({"seller": oid, "isActive": True})
        n_orders = await db.orders.count_documents({"seller": oid})
        s_plan = await get_supplier_plan(db, oid)
        pflags = plan_badge_and_flags(s_plan, bool(seller.get("isVerifiedSupplier")))
        if plan and plan.lower() not in ("all", "") and (pflags.get("subscriptionPlan") or "free").lower() != plan.lower():
            continue
        rows.append(
            {
                "sellerId": str(oid),
                "name": seller.get("name"),
                "email": seller.get("email"),
                "companyName": cname,
                "city": (prof or {}).get("city") or "",
                "verified": bool(seller.get("isVerifiedSupplier")),
                "trustScore": ts,
                "trustLevel": tl,
                "productCount": n_products,
                "orderCount": n_orders,
                "subscriptionPlan": pflags.get("subscriptionPlan", "free"),
                "planBadge": pflags.get("planBadge"),
                "isFeaturedSupplier": pflags.get("isFeaturedSupplier"),
                "searchBoostLabel": pflags.get("searchBoostLabel"),
            }
        )
    srt = (sort or "trust").lower()
    if srt in ("pro_first", "recommended"):
        def _k(r: dict) -> tuple:
            return search_sort_key(
                r.get("subscriptionPlan", "free") or "free",
                float(r.get("trustScore") or 0),
                bool(r.get("verified")),
                mode="pro_first" if srt == "pro_first" else "recommended",
            )
        rows.sort(key=_k)
    else:
        key_map = {
            "trust": lambda r: -r["trustScore"],
            "orders": lambda r: -r["orderCount"],
            "products": lambda r: -r["productCount"],
            "name": lambda r: (r.get("companyName") or r.get("name") or "").lower(),
        }
        sk = key_map.get(srt, key_map["trust"])
        rows.sort(key=sk)
    page = rows[skip : skip + limit]
    return success_response(
        data={"suppliers": page, "total": len(rows), "returned": len(page)}
    )


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
    s_plan = await get_supplier_plan(db, oid)
    plan_flags = plan_badge_and_flags(s_plan, bool(seller.get("isVerifiedSupplier")))
    total_products_active = await db.products.count_documents({"seller": oid, "isActive": True})
    total_products_all = await db.products.count_documents({"seller": oid})
    my_product_ids = await db.products.find({"seller": oid}, {"_id": 1}).distinct("_id")
    rfqs_received = await db.rfqs.count_documents({"items.productId": {"$in": my_product_ids}}) if my_product_ids else 0
    quotes_submitted = await db.quotes.count_documents({"sellerId": oid})
    quotes_accepted = await db.quotes.count_documents({"sellerId": oid, "status": "accepted"})
    orders_fulfilled = await db.orders.count_documents({"sellerId": oid})
    operational_response_rate = (min(100, (quotes_submitted / rfqs_received) * 100)) if rfqs_received else 0.0
    quote_acceptance_rate = round((quotes_accepted / quotes_submitted) * 100, 1) if quotes_submitted else 0.0
    categories_served = await db.products.distinct("category", {"seller": oid, "isActive": True})
    city = (profile or {}).get("city") or ""
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
    # Delivery: average of quoted delivery days
    deliv_samples = []
    async for qu in db.quotes.find({"sellerId": oid}, {"items": 1}).limit(200):
        for it in qu.get("items") or []:
            if it.get("deliveryDays"):
                deliv_samples.append(float(it["deliveryDays"]))
    avg_delivery_days = round(sum(deliv_samples) / len(deliv_samples), 1) if deliv_samples else None
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
            "subscriptionPlan": plan_flags.get("subscriptionPlan", "free"),
            "planBadge": plan_flags.get("planBadge"),
            "isFeaturedSupplier": plan_flags.get("isFeaturedSupplier"),
            "searchBoostLabel": plan_flags.get("searchBoostLabel"),
            "verifiedSupplier": plan_flags.get("verifiedSupplier"),
            "trust_score": (score_data or {}).get("total_score", 0),
            "trust_level": (score_data or {}).get("trust_level", "Low Trust"),
            "score_breakdown": {
                "profile_completeness": (score_data or {}).get("profile_completeness", 0),
                "response_rate": (score_data or {}).get("response_rate", 0),
                "product_strength": (score_data or {}).get("product_strength", 0),
                "buyer_rating": (score_data or {}).get("buyer_rating", 0),
                "verified_status": (score_data or {}).get("verified_status", 0),
                "weights": (score_data or {}).get("weights") or TRUST_WEIGHTS,
            },
            "trust_score_updated_at": (score_data or {}).get("updated_at"),
            "response_rate": round(operational_response_rate, 1),
            "operational_response_rate": round(operational_response_rate, 1),
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
            "average_delivery_days": avg_delivery_days,
            "city": city,
            "categories_served": categories_served,
            "recent_products": recent_products,
            "recent_activity": recent_activity,
        }
    })
