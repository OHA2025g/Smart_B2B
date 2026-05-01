from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "main.py"
t = p.read_text("utf-8")
t = t.replace(
    'app.include_router(buyer_dashboard.router, prefix="/api/buyer", tags=["buyer"])\n    app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])\n    app.include_router(order_payments.router, prefix="/api/orders", tags=["orders"])',
    'app.include_router(buyer_dashboard.router, prefix="/api/buyer", tags=["buyer"])\napp.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])\napp.include_router(order_payments.router, prefix="/api/orders", tags=["orders"])',
    1,
)
p.write_text(t, "utf-8")
print("ok")
