from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "orders.py"
t = p.read_text("utf-8")
old = """_PAYMENT_LABELS = {
    "payment_pending": "PAYMENT_PENDING",
    "escrow_held": "ESCROW_HELD",
    "released": "PAYMENT_RELEASED",
    "refunded": "PAYMENT_REFUNDED",
}"""
new = """_PAYMENT_LABELS = {
    "payment_pending": "PAYMENT_PENDING",
    "initiated": "PAYMENT_INITIATED",
    "payment_failed": "PAYMENT_FAILED",
    "escrow_held": "ESCROW_HELD",
    "released": "PAYMENT_RELEASED",
    "refunded": "PAYMENT_REFUNDED",
}"""
if old not in t:
    raise SystemExit("not found _PAYMENT_LABELS")
t = t.replace(old, new, 1)
p.write_text(t, "utf-8")
print("ok")
