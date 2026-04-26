from pathlib import Path

p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text(encoding="utf-8")
if '"deliveryLocation"' in t:
    print("demo data already has delivery fields")
    raise SystemExit(0)
needle = """        doc = {
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "createdAt": created_at,
            "validUntil": created_at + timedelta(days=7),
            "updated_at": now,
        }"""
repl = """        req_by = created_at + timedelta(days=random.randint(10, 50))
        doc = {
            "buyerId": buyer_id,
            "items": items,
            "status": status,
            "createdAt": created_at,
            "validUntil": created_at + timedelta(days=7),
            "deliveryLocation": random.choice(
                [
                    "Distribution Center North, Chicago, IL",
                    "Plant 2, Houston, TX",
                    "Warehouse B, Newark, NJ",
                    "Site 7, Phoenix, AZ",
                ]
            ),
            "requiredByDate": req_by,
            "buyerNotes": "Please confirm lead time and packaging."
            if random.random() > 0.5
            else None,
            "priority": random.choice(["normal", "urgent"]),
            "updated_at": now,
        }"""
if needle not in t:
    raise SystemExit("needle not found in generate_demo_data")
p.write_text(t.replace(needle, repl, 1), encoding="utf-8")
print("generate_demo_data RFQ fields ok")
