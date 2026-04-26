from pathlib import Path

p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text(encoding="utf-8")
if '"paymentStatus"' in t and "order" in t:
    print("already patched")
    raise SystemExit(0)
b1 = """        await db.orders.insert_one({
            "rfqId": o["rfqId"],
            "quoteId": o["quoteId"],
            "buyerId": o["buyerId"],
            "sellerId": o["sellerId"],
            "items": o["items"],
            "totalAmount": o["totalAmount"],
            "status": next_demo_order_status_for_seller(o["sellerId"]),
            "createdAt": now - timedelta(days=random.randint(0, 25)),
        })"""
a1 = """        await db.orders.insert_one({
            "rfqId": o["rfqId"],
            "quoteId": o["quoteId"],
            "buyerId": o["buyerId"],
            "sellerId": o["sellerId"],
            "items": o["items"],
            "totalAmount": o["totalAmount"],
            "status": next_demo_order_status_for_seller(o["sellerId"]),
            "createdAt": now - timedelta(days=random.randint(0, 25)),
            "paymentStatus": random.choice(
                ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
            ),
        })"""
b2 = """                await db.orders.insert_one({
                    "rfqId": qd["rfqId"],
                    "quoteId": qid,
                    "buyerId": rfq_doc["buyerId"],
                    "sellerId": qd["sellerId"],
                    "items": order_items,
                    "totalAmount": round(total, 2),
                    "status": next_demo_order_status_for_seller(qd["sellerId"]),
                    "createdAt": now - timedelta(days=random.randint(0, 25)),
                })"""
a2 = """                await db.orders.insert_one({
                    "rfqId": qd["rfqId"],
                    "quoteId": qid,
                    "buyerId": rfq_doc["buyerId"],
                    "sellerId": qd["sellerId"],
                    "items": order_items,
                    "totalAmount": round(total, 2),
                    "status": next_demo_order_status_for_seller(qd["sellerId"]),
                    "createdAt": now - timedelta(days=random.randint(0, 25)),
                    "paymentStatus": random.choice(
                        ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
                    ),
                })"""
c = 0
if b1 in t:
    t = t.replace(b1, a1, 1)
    c += 1
if b2 in t:
    t = t.replace(b2, a2, 1)
    c += 1
if c < 1:
    raise SystemExit("order insert blocks not found")
p.write_text(t, encoding="utf-8")
print("order paymentStatus in demo", c, "blocks")
