from bson import ObjectId
from fastapi import APIRouter, Depends, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, serialize_doc
from app.services.seller_plan import get_supplier_plan, PLAN_CATALOG

router = APIRouter(dependencies=[Depends(require_roles("seller"))])


@router.get("/dashboard")
async def seller_dashboard(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    my_product_ids = await db.products.find({"seller": uid}, {"_id": 1}).distinct("_id")
    total_products = len(my_product_ids)
    active_rfqs = await db.rfqs.count_documents({"items.productId": {"$in": my_product_ids}, "status": {"$in": ["sent", "quoted"]}}) if my_product_ids else 0
    total_quotes = await db.quotes.count_documents({"sellerId": uid})
    accepted_quotes = await db.quotes.count_documents({"sellerId": uid, "status": "accepted"})
    orders_received = await db.orders.count_documents({"sellerId": uid})
    rfqs_by_month = {}
    if my_product_ids:
        async for r in db.rfqs.aggregate([
            {"$match": {"items.productId": {"$in": my_product_ids}}},
            {"$project": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}}}},
            {"$group": {"_id": "$month", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]):
            rfqs_by_month[r["_id"]] = r["count"]
    orders_by_status = {}
    async for o in db.orders.aggregate([{"$match": {"sellerId": uid}}, {"$group": {"_id": "$status", "count": {"$sum": 1}}}]):
        orders_by_status[o["_id"] or "unknown"] = o["count"]
    product_request_counts = {}
    if my_product_ids:
        async for it in db.rfqs.aggregate([{"$unwind": "$items"}, {"$match": {"items.productId": {"$in": my_product_ids}}}, {"$group": {"_id": "$items.productId", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]):
            product_request_counts[str(it["_id"])] = it["count"]
    top_requested_products = []
    for pid, count in list(product_request_counts.items())[:10]:
        prod = await db.products.find_one({"_id": ObjectId(pid)}, projection={"title": 1, "category": 1}) if pid else None
        top_requested_products.append({"productId": pid, "title": (prod or {}).get("title"), "category": (prod or {}).get("category"), "requestCount": count})
    quotes_with_dates = await db.quotes.find({"sellerId": uid}, projection={"rfqId": 1, "createdAt": 1}).to_list(100)
    response_times = []
    for q in quotes_with_dates:
        rfq = await db.rfqs.find_one({"_id": q["rfqId"]}, projection={"createdAt": 1}) if q.get("rfqId") else None
        if rfq and rfq.get("createdAt") and q.get("createdAt"):
            delta = (q["createdAt"] - rfq["createdAt"]).total_seconds() / 3600
            response_times.append(delta)
    avg_response_hours = sum(response_times) / len(response_times) if response_times else None
    pl = await get_supplier_plan(db, uid)
    return success_response(data={
        "dashboard": {
            "currentPlan": {
                "id": pl.get("id", "free"),
                "name": pl.get("name", "Free"),
                "expiresAt": pl.get("expiresAt"),
            },
            "availablePlans": [PLAN_CATALOG["go"], PLAN_CATALOG["pro"]],

            "totalProducts": total_products,
            "activeRfqs": active_rfqs,
            "totalQuotesSubmitted": total_quotes,
            "acceptedQuotes": accepted_quotes,
            "ordersReceived": orders_received,
            "averageResponseTimeHours": round(avg_response_hours, 1) if avg_response_hours is not None else None,
            "topRequestedProducts": top_requested_products,
            "rfqsByMonth": rfqs_by_month,
            "ordersByStatus": orders_by_status,
        }
    })
