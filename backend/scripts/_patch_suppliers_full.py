from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "suppliers.py"
t = p.read_text("utf-8")
t = t.replace(
    "from app.services.supplier_score import TRUST_WEIGHTS, get_supplier_score_for_response",
    "from app.services.supplier_score import TRUST_WEIGHTS, get_supplier_score_for_response\nfrom app.services.seller_plan import get_supplier_plan, plan_badge_and_flags, search_sort_key",
    1,
)
# replace block
old = """    sort: str = Query("trust", description="trust, orders, products, name"),
    limit: int = Query(50, le=200, ge=1),
    skip: int = Query(0, ge=0),
):
    \"\"\"Public + auth: discover suppliers (sellers) with trust metadata.\"\"\"
    db = get_db()
    q = {"role": "seller"}
    if verified_only is True:
        q["isVerifiedSupplier"] = True
    cursor = db.users.find(q, {"password": 0}).sort("name", 1)
    rows = []
    async for seller in cursor:
        oid = seller["_id"]
        prof = await db.companyprofiles.find_one({"user": oid})
        cname = (prof or {}).get("companyName") or seller.get("name") or ""
        em = (seller.get("email") or "").lower()
        c = ((prof or {}).get("city") or "").lower()
        if search:
            s = search.lower()
            if s not in cname.lower() and s not in em and s not in (seller.get("name") or "").lower():
                continue
        if city and city.lower() not in c:
            continue
        if category:
            has = await db.products.find_one(
                {"seller": oid, "isActive": True, "category": re.compile(re.escape(category), re.I)}
            )
            if not has:
                continue
        score_data = await get_supplier_score_for_response(oid) or {}
        ts = int(score_data.get("total_score", 0) or 0)
        tl = str(score_data.get("trust_level", "Low Trust") or "")
        if trust_level and trust_level.lower() not in tl.lower():
            continue
        n_products = await db.products.count_documents({"seller": oid, "isActive": True})
        n_orders = await db.orders.count_documents({"seller": oid})
        rows.append(
            {
                "sellerId": str(oid),
                "name": seller.get("name"),
                "email": seller.get("email"),
                "companyName": cname,
                "city": (prof or {}).get("city") or "",
                "verified": bool(seller.get("isVerifiedSupplier")),
                "trustScore": ts,
                "trustLevel": tl,
                "productCount": n_products,
                "orderCount": n_orders,
            }
        )
    key_map = {
        "trust": lambda r: -r["trustScore"],
        "orders": lambda r: -r["orderCount"],
        "products": lambda r: -r["productCount"],
        "name": lambda r: (r.get("companyName") or r.get("name") or "").lower(),
    }
    sk = key_map.get(sort, key_map["trust"])
    rows.sort(key=sk)
    page = rows[skip : skip + limit]"""
# build new
new = """    sort: str = Query("trust", description="trust, orders, products, name, recommended, pro_first"),
    plan: str | None = Query(None, description="free, go, pro"),
    limit: int = Query(50, le=200, ge=1),
    skip: int = Query(0, ge=0),
):
    \"\"\"Public + auth: discover suppliers (sellers) with trust metadata.\"\"\"
    db = get_db()
    q = {"role": "seller"}
    if verified_only is True:
        q["isVerifiedSupplier"] = True
    cursor = db.users.find(q, {"password": 0}).sort("name", 1)
    rows = []
    async for seller in cursor:
        oid = seller["_id"]
        prof = await db.companyprofiles.find_one({"user": oid})
        cname = (prof or {}).get("companyName") or seller.get("name") or ""
        em = (seller.get("email") or "").lower()
        c = ((prof or {}).get("city") or "").lower()
        if search:
            s = search.lower()
            if s not in cname.lower() and s not in em and s not in (seller.get("name") or "").lower():
                continue
        if city and city.lower() not in c:
            continue
        if category:
            has = await db.products.find_one(
                {"seller": oid, "isActive": True, "category": re.compile(re.escape(category), re.I)}
            )
            if not has:
                continue
        score_data = await get_supplier_score_for_response(oid) or {}
        ts = int(score_data.get("total_score", 0) or 0)
        tl = str(score_data.get("trust_level", "Low Trust") or "")
        if trust_level and trust_level.lower() not in tl.lower():
            continue
        n_products = await db.products.count_documents({"seller": oid, "isActive": True})
        n_orders = await db.orders.count_documents({"seller": oid})
        s_plan = await get_supplier_plan(db, oid)
        pflags = plan_badge_and_flags(s_plan, bool(seller.get("isVerifiedSupplier")))
        if plan and plan.lower() not in ("all", "") and (pflags.get("subscriptionPlan") or "free").lower() != plan.lower():
            continue
        rows.append(
            {
                "sellerId": str(oid),
                "name": seller.get("name"),
                "email": seller.get("email"),
                "companyName": cname,
                "city": (prof or {}).get("city") or "",
                "verified": bool(seller.get("isVerifiedSupplier")),
                "trustScore": ts,
                "trustLevel": tl,
                "productCount": n_products,
                "orderCount": n_orders,
                "subscriptionPlan": pflags.get("subscriptionPlan", "free"),
                "planBadge": pflags.get("planBadge"),
                "isFeaturedSupplier": pflags.get("isFeaturedSupplier"),
                "searchBoostLabel": pflags.get("searchBoostLabel"),
            }
        )
    srt = (sort or "trust").lower()
    if srt in ("pro_first", "recommended"):
        def _k(r: dict) -> tuple:
            return search_sort_key(
                r.get("subscriptionPlan", "free") or "free",
                float(r.get("trustScore") or 0),
                bool(r.get("verified")),
                mode="pro_first" if srt == "pro_first" else "recommended",
            )
        rows.sort(key=_k)
    else:
        key_map = {
            "trust": lambda r: -r["trustScore"],
            "orders": lambda r: -r["orderCount"],
            "products": lambda r: -r["productCount"],
            "name": lambda r: (r.get("companyName") or r.get("name") or "").lower(),
        }
        sk = key_map.get(srt, key_map["trust"])
        rows.sort(key=sk)
    page = rows[skip : skip + limit]"""
if old not in t:
    raise SystemExit("block not in suppliers - already patched?")
p.write_text(t.replace(old, new, 1), "utf-8")
print("ok")
