from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "main.py"
t = p.read_text("utf-8")
if "order_payments" in t:
    print("skip")
    raise SystemExit(0)
old = """    buyer_dashboard,
)"""
new = """    buyer_dashboard,
    subscriptions,
    order_payments,
)"""
if old not in t:
    raise SystemExit("import block not found")
t = t.replace(old, new, 1)
t = t.replace(
    'app.include_router(buyer_dashboard.router, prefix="/api/buyer", tags=["buyer"])\n',
    'app.include_router(buyer_dashboard.router, prefix="/api/buyer", tags=["buyer"])\n    app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])\n    app.include_router(order_payments.router, prefix="/api/orders", tags=["orders"])\n',
    1,
)
p.write_text(t, "utf-8")
print("ok")
