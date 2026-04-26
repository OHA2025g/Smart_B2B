from pathlib import Path

p = Path(__file__).resolve().parent.parent / "app/routers/products.py"
t = p.read_text(encoding="utf-8")
old_sig = """    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
):"""
new_sig = """    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    sort: str = Query(
        "newest",
        description="newest, relevance, price_asc, price_desc, trust",
    ),
):"""
if old_sig not in t:
    raise SystemExit("sig not found")
t = t.replace(old_sig, new_sig, 1)
old_ret = "        products.append(doc)\n    return success_response(data={\"products\": products})"
new_ret = """        products.append(doc)
    s = (sort or "newest").lower()
    if s == "price_asc":
        products.sort(key=lambda d: float(d.get("price") or 0))
    elif s == "price_desc":
        products.sort(key=lambda d: float(d.get("price") or 0), reverse=True)
    elif s in ("trust", "trust_desc", "trust_score"):
        products.sort(
            key=lambda d: (d.get("seller") or {}).get("trustScore", 0) or 0,
            reverse=True,
        )
    elif s == "relevance":
        pass
    return success_response(data={"products": products})"""
if old_ret not in t:
    raise SystemExit("return block not found")
t = t.replace(old_ret, new_ret, 1)
p.write_text(t, encoding="utf-8")
print("products sort patched")
