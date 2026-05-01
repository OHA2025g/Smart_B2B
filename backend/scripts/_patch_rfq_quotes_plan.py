from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "rfq.py"
t = p.read_text("utf-8")
if "plan_badge_and_flags" in t and "enrich_quote_dict" in t and 'doc["sellerId"]["planBadge"]' in t:
    print("skip")
    raise SystemExit(0)
if "from app.services.seller_plan import" not in t:
    t = t.replace(
        "from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score",
        "from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score\nfrom app.services.seller_plan import get_supplier_plan, plan_badge_and_flags",
        1,
    )
old = """        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None
        supplier_score = score_data.get("total_score", 0) if score_data else 0
        quote_score_val = compute_quote_score(q.get("items", []), rfq_items, supplier_score, all_totals)
        doc = serialize_doc(q)
        if doc:
            doc["items"] = items
            doc["sellerId"] = serialize_doc(seller) if seller else None
            if doc["sellerId"]:
                doc["sellerId"]["trustScore"] = supplier_score
                doc["sellerId"]["trustLevel"] = (score_data or {}).get("trust_level", "Low Trust")
            doc["quoteScore"] = quote_score_val
            enrich_quote_dict(doc)"""
new = """        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None
        supplier_score = score_data.get("total_score", 0) if score_data else 0
        s_plan = await get_supplier_plan(db, q["sellerId"]) if q.get("sellerId") else None
        p_badge = plan_badge_and_flags(s_plan, bool((seller or {}).get("isVerifiedSupplier"))) if s_plan else {}
        quote_score_val = compute_quote_score(q.get("items", []), rfq_items, supplier_score, all_totals)
        doc = serialize_doc(q)
        if doc:
            doc["items"] = items
            doc["sellerId"] = serialize_doc(seller) if seller else None
            if doc["sellerId"]:
                doc["sellerId"]["trustScore"] = supplier_score
                doc["sellerId"]["trustLevel"] = (score_data or {}).get("trust_level", "Low Trust")
                for k, v in p_badge.items():
                    doc["sellerId"][k] = v
            doc["quoteScore"] = quote_score_val
            enrich_quote_dict(doc)"""
if old not in t:
    raise SystemExit("quotes block not found")
t = t.replace(old, new, 1)
# comparison rows
old2 = """        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        company = await db.companyprofiles.find_one({"user": q["sellerId"]}, projection={"companyName": 1, "city": 1}) if q.get("sellerId") else None
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None"""
new2 = """        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        company = await db.companyprofiles.find_one({"user": q["sellerId"]}, projection={"companyName": 1, "city": 1}) if q.get("sellerId") else None
        s_plan2 = await get_supplier_plan(db, q["sellerId"]) if q.get("sellerId") else None
        p2 = plan_badge_and_flags(s_plan2, bool((seller or {}).get("isVerifiedSupplier"))) if s_plan2 else {}
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None"""
t = t.replace(old2, new2, 1)
# add p2 fields in rows.append dict
t = t.replace(
    '"verified_supplier": bool((seller or {}).get("isVerifiedSupplier")),',
    '"verified_supplier": bool((seller or {}).get("isVerifiedSupplier")),\n            "subscriptionPlan": p2.get("subscriptionPlan", "free") if p2 else "free",\n            "plan_badge": p2.get("planBadge") if p2 else "Free Supplier",\n            "is_featured_supplier": p2.get("isFeaturedSupplier") if p2 else False,',
    1,
)
p.write_text(t, "utf-8")
print("ok")
