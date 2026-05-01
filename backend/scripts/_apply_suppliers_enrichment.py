from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "suppliers.py"
t = p.read_text("utf-8")
if "get_supplier_plan" in t:
    print("skip")
    raise SystemExit(0)
t = t.replace(
    "from app.services.supplier_score import TRUST_WEIGHTS, get_supplier_score_for_response",
    "from app.services.supplier_score import TRUST_WEIGHTS, get_supplier_score_for_response\nfrom app.services.seller_plan import get_supplier_plan, plan_badge_and_flags, search_sort_key",
    1,
)
t = t.replace(
    '    sort: str = Query("trust", description="trust, orders, products, name"),\n    limit: int = Query(50, le=200, ge=1),',
    '    sort: str = Query("trust", description="trust, orders, products, name, recommended, pro_first"),\n    plan: str | None = Query(None, description="Filter free, go, pro"),\n    limit: int = Query(50, le=200, ge=1),',
    1,
)
# in loop after score, before rows.append - inject plan
old = """        n_products = await db.products.count_documents({"seller": oid, "isActive": True})
        n_orders = await db.orders.count_documents({"seller": oid})
        rows.append(
            {
                "sellerId": str(oid),"""
if old in t and "subscriptionPlan" not in t[500:2000]:
    t = t.replace(
        "        n_orders = await db.orders.count_documents({\"seller\": oid})\n        rows.append(",
        """        n_orders = await db.orders.count_documents({"seller": oid})
        s_plan = await get_supplier_plan(db, oid)
        pflags = plan_badge_and_flags(s_plan, bool(seller.get("isVerifiedSupplier")))
        if plan and plan.lower() not in ("all", "") and (pflags.get("subscriptionPlan") or "free").lower() != plan.lower():
            continue
        rows.append(
        """,
        1,
    )
    t = t.replace(
        """                "orderCount": n_orders,
            }
        )""",
        """                "orderCount": n_orders,
            }
        )""",
        1,
    )
# That didn't add fields - do second replace
old_row = """                "orderCount": n_orders,
            }
        )"""
# find and extend dict
t = t.replace(
    '"orderCount": n_orders,\n            }',
    '"orderCount": n_orders,\n                "subscriptionPlan": pflags.get("subscriptionPlan", "free"),\n                "planBadge": pflags.get("planBadge"),\n                "isFeaturedSupplier": pflags.get("isFeaturedSupplier"),\n                "searchBoostLabel": pflags.get("searchBoostLabel"),\n            }',
    1,
)
# fix if pflags not defined in loop - the first replace may have failed
t = t.replace("        s_plan = await get_supplier_plan", "    s_plan = await get_supplier_plan", 0)  # no-op
p.write_text(t, "utf-8")
# manual: read file and fix if broken
print("check manually")
