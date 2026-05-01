from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "admin.py"
t = p.read_text("utf-8")
if "def list_subscriptions" in t:
    print("skip")
    raise SystemExit(0)
block = '''

@router.get("/subscriptions")
async def list_subscriptions(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cur = db.seller_subscriptions.find({}).sort("createdAt", -1).limit(500)
    out = []
    async for s in cur:
        doc = serialize_doc(s) or {}
        sid = s.get("sellerId")
        u = await db.users.find_one({"_id": sid}, projection={"name": 1, "email": 1}) if sid else None
        if u:
            doc["sellerName"] = u.get("name")
            doc["sellerEmail"] = u.get("email")
        out.append(doc)
    return success_response(data={"subscriptions": out})


@router.get("/payments")
async def list_payments(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    cur = db.payments.find({}).sort("createdAt", -1).limit(500)
    out = []
    async for p in cur:
        doc = serialize_doc(p) or {}
        uid = p.get("userId")
        u = await db.users.find_one({"_id": uid}, projection={"name": 1, "email": 1, "role": 1}) if uid else None
        if u:
            doc["userName"] = u.get("name")
            doc["userEmail"] = u.get("email")
            doc["payerRoleResolved"] = u.get("role")
        out.append(doc)
    return success_response(data={"payments": out})


@router.get("/revenue-summary")
async def revenue_summary(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    sub_rev = 0.0
    async for p in db.payments.find(
        {"paymentType": "subscription", "status": "success"},
        {"amount": 1},
    ):
        sub_rev += float(p.get("amount") or 0)
    escrow_vol = 0.0
    async for p in db.payments.find(
        {"paymentType": "order_escrow", "status": {"$in": ["escrow_held", "released"]}},
        {"amount": 1},
    ):
        escrow_vol += float(p.get("amount") or 0)
    ok = await db.payments.count_documents({"status": {"$in": ["success", "escrow_held", "released"]}})
    fail = await db.payments.count_documents({"status": "failed"})
    go = await db.users.count_documents({"role": "seller", "subscriptionPlan": "go"})
    pro = await db.users.count_documents({"role": "seller", "subscriptionPlan": "pro"})
    free = await db.users.count_documents(
        {
            "role": "seller",
            "$or": [
                {"subscriptionPlan": {"$exists": False}},
                {"subscriptionPlan": "free"},
            ],
        }
    )
    pro_active = await db.seller_subscriptions.count_documents({"plan": "pro", "status": "active"})
    go_active = await db.seller_subscriptions.count_documents({"plan": "go", "status": "active"})
    return success_response(
        data={
            "revenue": {
                "subscription_revenue_inr": round(sub_rev, 2),
                "escrow_payment_volume_inr": round(escrow_vol, 2),
                "successful_payments": ok,
                "failed_payments": fail,
                "active_go_sellers": go_active,
                "active_pro_sellers": pro_active,
                "sellers_by_plan_go": go,
                "sellers_by_plan_pro": pro,
                "sellers_by_plan_free": free,
            }
        }
    )
'''
if not t.rstrip().endswith(")"):
    pass
p.write_text(t.rstrip() + block, "utf-8")
print("ok")
