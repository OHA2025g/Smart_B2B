from pathlib import Path
p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text("utf-8")
if "apply_demo_plans_payments" in t:
    print("skip")
    raise SystemExit(0)
if "from scripts.demo_plans_payments import apply_demo_plans_payments" not in t:
    t = t.replace("import os\n", "import os\nfrom scripts.demo_plans_payments import apply_demo_plans_payments\n", 1)
old = """    await create_supplier_scores(db, [seller_id])

    # Summary"""
new = """    await create_supplier_scores(db, [seller_id])

    await apply_demo_plans_payments(db, all_sellers, seller_id, buyer_id)

    # Summary"""
if old not in t:
    raise SystemExit("block not found")
p.write_text(t.replace(old, new, 1), "utf-8")
# add collections to summary
t = p.read_text("utf-8")
t = t.replace(
    '("workflow_events", db.workflow_events),',
    '("workflow_events", db.workflow_events),\n        ("payments", db.payments),\n        ("seller_subscriptions", db.seller_subscriptions),',
    1,
)
p.write_text(t, "utf-8")
print("ok")
