from pathlib import Path
p = Path(__file__).resolve().parent.parent / "app" / "routers" / "rfq.py"
t = p.read_text("utf-8")
if "get_supplier_plan" not in t:
    t = t.replace(
        "from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score",
        "from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score\nfrom app.services.seller_plan import get_supplier_plan, rfq_list_limit_for_plan",
        1,
    )
old1 = """        "paymentStatus": "payment_pending",
    }"""
new1 = """        "paymentStatus": "payment_pending",
        "escrowStatus": "not_started",
        "lastPaymentId": None,
    }"""
if old1 in t and "escrowStatus" not in t.split("order_doc", 1)[1][:500]:
    t = t.replace(old1, new1, 1)

old2 = """    my_ids = [p["_id"] for p in my_products]
    cursor = db.rfqs.find({"items.productId": {"$in": my_ids}, "status": {"$in": ["sent", "quoted"]}}).sort("createdAt", -1)
    rfqs = []
    async for rfq in cursor:
        items = await _populate_rfq_items(db, rfq.get("items", []))
        buyer = await db.users.find_one({"_id": rfq["buyerId"]}, projection={"name": 1, "email": 1}) if rfq.get("buyerId") else None
        doc = _serialize_rfq_enriched(rfq)
        if doc:
            doc["items"] = items
            doc["buyerId"] = serialize_doc(buyer) if buyer else None
        rfqs.append(doc)
    return success_response(data={"rfqs": rfqs})"""
new2 = """    my_ids = [p["_id"] for p in my_products]
    sp = await get_supplier_plan(db, ObjectId(user["id"]))
    cap = rfq_list_limit_for_plan(sp)
    cursor = db.rfqs.find({"items.productId": {"$in": my_ids}, "status": {"$in": ["sent", "quoted"]}}).sort("createdAt", -1)
    all_rows = [r async for r in cursor]
    if cap is not None:
        all_rows = all_rows[: int(cap)]
    rfqs = []
    for rfq in all_rows:
        items = await _populate_rfq_items(db, rfq.get("items", []))
        buyer = await db.users.find_one({"_id": rfq["buyerId"]}, projection={"name": 1, "email": 1}) if rfq.get("buyerId") else None
        doc = _serialize_rfq_enriched(rfq)
        if doc:
            doc["items"] = items
            doc["buyerId"] = serialize_doc(buyer) if buyer else None
        rfqs.append(doc)
    return success_response(
        data={"rfqs": rfqs, "rfqAccess": {"limited": cap is not None, "dailyCap": cap, "plan": (sp or {}).get("id", "free")}}
    )"""
if "rfqAccess" not in t:
    if old2 not in t:
        raise SystemExit("assigned block not found")
    t = t.replace(old2, new2, 1)
p.write_text(t, "utf-8")
print("ok")
