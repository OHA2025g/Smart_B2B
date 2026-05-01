from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "orders.py"
t = p.read_text("utf-8")
old = """        if out.get("paymentStatus") is None:
            out["paymentStatus"] = "payment_pending"
    return out"""
new = """        if out.get("paymentStatus") is None:
            out["paymentStatus"] = "payment_pending"
        if out.get("escrowStatus") is None:
            out["escrowStatus"] = "not_started"
    return out"""
if old not in t:
    raise SystemExit("populate not found")
p.write_text(t.replace(old, new, 1), "utf-8")
print("ok")
