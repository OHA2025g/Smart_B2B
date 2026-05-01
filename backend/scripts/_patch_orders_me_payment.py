from pathlib import Path

p = Path(__file__).resolve().parent.parent / "app" / "routers" / "orders.py"
t = p.read_text("utf-8")
old = """@router.get("/me")
async def get_my(request: Request, status: str | None = Query(None), user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    if user.get("role") == "admin":
        filter_q: dict = {}
    else:
        filter_q = {"sellerId": uid} if user.get("role") == "seller" else {"buyerId": uid}
    if status:
        filter_q["status"] = status"""
new = """@router.get("/me")
async def get_my(
    request: Request,
    status: str | None = Query(None),
    payment_status: str | None = Query(None, description="Filter by order paymentStatus"),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    uid = ObjectId(user["id"])
    if user.get("role") == "admin":
        filter_q: dict = {}
    else:
        filter_q = {"sellerId": uid} if user.get("role") == "seller" else {"buyerId": uid}
    if status:
        filter_q["status"] = status
    if payment_status:
        filter_q["paymentStatus"] = payment_status"""
if old not in t:
    raise SystemExit("orders get_my pattern not found")
p.write_text(t.replace(old, new, 1), "utf-8")
print("ok")
