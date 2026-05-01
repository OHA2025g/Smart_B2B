from bson import ObjectId
from fastapi import APIRouter, Depends, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, serialize_doc

router = APIRouter(dependencies=[Depends(require_roles("buyer"))])


@router.get("/dashboard")
async def buyer_dashboard(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    wishlist_count = await db.wishlistitems.count_documents({"buyerId": uid})
    cart_count = await db.cartitems.count_documents({"buyerId": uid})
    rfqs_created = await db.rfqs.count_documents({"buyerId": uid})
    my_rfq_ids = await db.rfqs.find({"buyerId": uid}, {"_id": 1}).distinct("_id")
    quotes_received = await db.quotes.count_documents({"rfqId": {"$in": my_rfq_ids}}) if my_rfq_ids else 0
    accepted_quotes = await db.quotes.count_documents({"rfqId": {"$in": my_rfq_ids}, "status": "accepted"}) if my_rfq_ids else 0
    orders_placed = await db.orders.count_documents({"buyerId": uid})
    pending_payments = await db.orders.count_documents(
        {"buyerId": uid, "paymentStatus": {"$in": ["payment_pending", "payment_failed"]}}
    )
    escrow_held = await db.orders.count_documents(
        {"buyerId": uid, "paymentStatus": "escrow_held", "escrowStatus": "held"}
    )
    recent_rfqs_cursor = db.rfqs.find({"buyerId": uid}).sort("createdAt", -1).limit(5)
    recent_rfqs = []
    async for r in recent_rfqs_cursor:
        doc = serialize_doc(r)
        if doc:
            recent_rfqs.append(doc)
    recent_orders_cursor = db.orders.find({"buyerId": uid}).sort("createdAt", -1).limit(5)
    recent_orders = []
    async for o in recent_orders_cursor:
        doc = serialize_doc(o)
        if doc:
            recent_orders.append(doc)
    rfq_status_distribution = {}
    async for d in db.rfqs.aggregate([{"$match": {"buyerId": uid}}, {"$group": {"_id": "$status", "count": {"$sum": 1}}}]):
        rfq_status_distribution[d["_id"] or "unknown"] = d["count"]
    return success_response(data={
        "dashboard": {
            "wishlistCount": wishlist_count,
            "cartCount": cart_count,
            "rfqsCreated": rfqs_created,
            "quotesReceived": quotes_received,
            "acceptedQuotes": accepted_quotes,
            "ordersPlaced": orders_placed,
            "pendingPayments": pending_payments,
            "escrowHeldOrders": escrow_held,
            "recentRfqs": recent_rfqs,
            "recentOrders": recent_orders,
            "rfqStatusDistribution": rfq_status_distribution,
        }
    })
