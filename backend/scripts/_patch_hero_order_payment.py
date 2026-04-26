from pathlib import Path

p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text(encoding="utf-8")
old = """            await db.orders.insert_one({
                "rfqId": qd["rfqId"],
                "quoteId": qd["_id"],
                "buyerId": rfq_doc["buyerId"],
                "sellerId": seller_id,
                "items": o_items,
                "totalAmount": round(total, 2),
                "status": next_demo_order_status_for_seller(seller_id),
                "createdAt": now - timedelta(days=random.randint(0, 22)),
            })"""
new = """            await db.orders.insert_one({
                "rfqId": qd["rfqId"],
                "quoteId": qd["_id"],
                "buyerId": rfq_doc["buyerId"],
                "sellerId": seller_id,
                "items": o_items,
                "totalAmount": round(total, 2),
                "status": next_demo_order_status_for_seller(seller_id),
                "createdAt": now - timedelta(days=random.randint(0, 22)),
                "paymentStatus": random.choice(
                    ["payment_pending", "escrow_held", "released", "payment_pending", "escrow_held", "refunded"]
                ),
            })"""
if old not in t:
    raise SystemExit("hero order block not found")
if '"paymentStatus"' in old:
    pass
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("hero order ok")
