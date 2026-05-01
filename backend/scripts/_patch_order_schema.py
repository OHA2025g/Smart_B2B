from pathlib import Path

p = Path(__file__).resolve().parent.parent / "app" / "schemas" / "order.py"
t = p.read_text(encoding="utf-8")
old = '''class OrderPaymentUpdate(BaseModel):
    paymentStatus: Literal["payment_pending", "escrow_held", "released", "refunded"]'''
new = '''class OrderPaymentUpdate(BaseModel):
    paymentStatus: Literal[
        "payment_pending",
        "initiated",
        "payment_failed",
        "escrow_held",
        "released",
        "refunded",
    ]'''
if old not in t:
    raise SystemExit("order schema not found")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("ok")
