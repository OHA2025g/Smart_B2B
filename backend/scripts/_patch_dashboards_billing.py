from pathlib import Path

# seller
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "seller_dashboard.py"
t = p.read_text("utf-8")
if "subscriptionPlan" in t and "currentPlan" in t:
    pass
else:
    t = t.replace(
        "from app.schemas.common import success_response, serialize_doc",
        "from app.schemas.common import success_response, serialize_doc\nfrom app.services.seller_plan import get_supplier_plan, PLAN_CATALOG",
        1,
    )
    t = t.replace(
        '    return success_response(data={\n        "dashboard": {',
        """    pl = await get_supplier_plan(db, uid)
    return success_response(data={
        "dashboard": {
            "currentPlan": {
                "id": pl.get("id", "free"),
                "name": pl.get("name", "Free"),
                "expiresAt": pl.get("expiresAt"),
            },
            "availablePlans": [PLAN_CATALOG["go"], PLAN_CATALOG["pro"]],
""",
        1,
    )
p.write_text(t, "utf-8")

# buyer
p2 = Path(__file__).resolve().parent.parent / "app" / "routers" / "buyer_dashboard.py"
t2 = p2.read_text("utf-8")
if "escrowOrderCount" in t2:
    print("buyer skip")
else:
    t2 = t2.replace(
        '    orders_placed = await db.orders.count_documents({"buyerId": uid})',
        """    orders_placed = await db.orders.count_documents({"buyerId": uid})
    pending_payments = await db.orders.count_documents(
        {"buyerId": uid, "paymentStatus": {"$in": ["payment_pending", "payment_failed"]}}
    )
    escrow_held = await db.orders.count_documents(
        {"buyerId": uid, "paymentStatus": "escrow_held", "escrowStatus": "held"}
    )""",
        1,
    )
    t2 = t2.replace(
        '"ordersPlaced": orders_placed,',
        '"ordersPlaced": orders_placed,\n            "pendingPayments": pending_payments,\n            "escrowHeldOrders": escrow_held,',
        1,
    )
p2.write_text(t2, "utf-8")
print("ok")
