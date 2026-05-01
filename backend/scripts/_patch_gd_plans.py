from pathlib import Path
p = Path(__file__).resolve().parent.parent / "scripts" / "generate_demo_data.py"
t = p.read_text("utf-8")
if "apply_demo_plans_payments" in t:
    print("skip")
    raise SystemExit(0)
needle = '    print("13. Boosting preserved'
insert = '    from scripts.demo_plans_payments import apply_demo_plans_payments\n\n' + '    ' + 'print("13. Boosting preserved'  # wrong

idx = t.find("await create_supplier_scores(db, [seller_id])")
if idx < 0:
    raise SystemExit("anchor not found")
# insert after the line "await create_supplier_scores..." following boost
anchor = "    await create_supplier_scores(db, [seller_id])"
pos = t.find(anchor) + len(anchor)
if "apply_demo_plans_payments" not in t:
    t = t[:pos] + "\n\n    await apply_demo_plans_payments(db, all_sellers, seller_id, buyer_id)\n" + t[pos:]

# add import at top
if "demo_plans_payments" not in t[:200]:
    t = t.replace("import asyncio", "import asyncio", 1)
    t = t.replace("import os\n", "import os\nfrom scripts.demo_plans_payments import apply_demo_plans_payments\n", 1)

# Remove duplicate if we used inline import
t = t.replace("from scripts.demo_plans_payments import apply_demo_plans_payments\nimport asyncio", "import asyncio", 1)
# ensure single import
if t.count("apply_demo_plans_payments") < 2:
    # need import + call only once import
    pass
p.write_text(t, "utf-8")
print("ok")
