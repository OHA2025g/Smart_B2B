from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "suppliers.py"
t = p.read_text("utf-8")
if '"subscriptionPlan"' in t and "get_supplier_profile" in t:
    # check if inside profile
    if 'planBadge' in t[4000:9000]:
        print("skip")
        raise SystemExit(0)
if "get_supplier_plan" not in t.split("get_supplier_profile", 1)[0]:
    pass
anchor = "    score_data = await get_supplier_score_for_response(oid)\n    total_products_active"
if anchor not in t:
    raise SystemExit("anchor missing")
t = t.replace(
    anchor,
    """    score_data = await get_supplier_score_for_response(oid)
    s_plan = await get_supplier_plan(db, oid)
    plan_flags = plan_badge_and_flags(s_plan, bool(seller.get("isVerifiedSupplier")))
    total_products_active""",
    1,
)
# add keys in profile return - find "verified_supplier" line
t = t.replace(
    '"verified_supplier": bool(seller.get("isVerifiedSupplier")),',
    '"verified_supplier": bool(seller.get("isVerifiedSupplier")),\n            "subscriptionPlan": plan_flags.get("subscriptionPlan", "free"),\n            "planBadge": plan_flags.get("planBadge"),\n            "isFeaturedSupplier": plan_flags.get("isFeaturedSupplier"),\n            "searchBoostLabel": plan_flags.get("searchBoostLabel"),\n            "verifiedSupplier": plan_flags.get("verifiedSupplier"),',
    1,
)
p.write_text(t, "utf-8")
print("ok")
