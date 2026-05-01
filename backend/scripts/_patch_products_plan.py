from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "products.py"
t = p.read_text("utf-8")
if "get_supplier_plan" in t:
    print("skip")
    raise SystemExit(0)
t = t.replace(
    "from app.services.supplier_score import get_supplier_score_for_response",
    "from app.services.supplier_score import get_supplier_score_for_response\nfrom app.services.seller_plan import get_supplier_plan, plan_badge_and_flags, search_sort_key",
    1,
)
old = """async def _enrich_seller_with_score(seller_doc: dict, seller_oid) -> dict:
    if not seller_doc:
        return None
    out = serialize_doc(seller_doc)
    if not out:
        return None
    score = await get_supplier_score_for_response(seller_oid)
    if score:
        out["trustScore"] = score.get("total_score", 0)
        out["trustLevel"] = score.get("trust_level", "Low Trust")
    out["isVerifiedSupplier"] = bool(seller_doc.get("isVerifiedSupplier"))
    return out"""
new = """async def _enrich_seller_with_score(seller_doc: dict, seller_oid) -> dict:
    if not seller_doc:
        return None
    out = serialize_doc(seller_doc)
    if not out:
        return None
    db = get_db()
    plan = await get_supplier_plan(db, seller_oid)
    flags = plan_badge_and_flags(plan, bool(seller_doc.get("isVerifiedSupplier")))
    out |= flags
    score = await get_supplier_score_for_response(seller_oid)
    if score:
        out["trustScore"] = score.get("total_score", 0)
        out["trustLevel"] = score.get("trust_level", "Low Trust")
    out["isVerifiedSupplier"] = bool(seller_doc.get("isVerifiedSupplier"))
    return out"""
if old not in t:
    raise SystemExit("enrich not found")
t = t.replace(old, new, 1)
# projection add subscription
t = t.replace(
    'seller = await db.users.find_one({"_id": p["seller"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if p.get("seller") else None',
    'seller = await db.users.find_one(\n        {"_id": p["seller"]},\n        projection={"name": 1, "email": 1, "isVerifiedSupplier": 1, "subscriptionPlan": 1, "sellerPlanExpiresAt": 1, "isFeaturedSupplier": 1, "isProSearchBoost": 1},\n    ) if p.get("seller") else None',
    1,
)
# sort options in query description
t = t.replace(
    "description=\"newest, relevance, price_asc, price_desc, trust\"",
    'description="newest, relevance, price_asc, price_desc, trust, pro_first, recommended"',
    1,
)
# after building products, add sort for pro_first
insert_after = "    s = (sort or \"newest\").lower()\n    if s == \"price_asc\":"
if insert_after in t and "if s == \"pro_first\":" not in t:
    block = """    s = (sort or "newest").lower()
    if s in ("pro_first", "recommended"):
        products.sort(
            key=lambda d: search_sort_key(
                (d.get("seller") or {}).get("subscriptionPlan", "free") or "free",
                (d.get("seller") or {}).get("trustScore", 0) or 0,
                (d.get("seller") or {}).get("isVerifiedSupplier", False),
                mode="pro_first" if s == "pro_first" else "recommended",
            )
        )
    if s == "price_asc":"""
    t = t.replace(insert_after, block, 1)
# plan filter
if "plan=" not in t or "query plan" in t:
    t = t.replace(
        "    verified_only: bool | None = Query(None, description=",
        "    plan: str | None = Query(None, description=",
        1,
    )  # wrong
p.write_text(t, "utf-8")
print("ok first part")
