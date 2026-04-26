"""Patch rfq.py: OID coercion, linkedOrderId on GET rfq, reject-quote endpoint."""
from pathlib import Path

RFQ = Path(__file__).resolve().parent.parent / "app/routers/rfq.py"


def main():
    t = RFQ.read_text(encoding="utf-8")
    t = t.replace(
        "from app.schemas.common import success_response, error_response, serialize_doc",
        "from app.schemas.common import success_response, error_response, serialize_doc, coerce_object_id, coerce_object_id_list",
    )

    old_get = (
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products})\n"
        "    is_buyer = str(rfq[\"buyerId\"]) == user[\"id\"]\n"
        "    is_seller = user[\"id\"] in seller_ids\n"
        "    is_admin = user.get(\"role\") == \"admin\"\n"
        "    if not is_buyer and not is_seller and not is_admin:\n"
        "        raise HTTPException(status_code=403, detail=error_response(\"Access denied.\", \"FORBIDDEN\", path=str(request.url.path)))\n"
        "    await _maybe_emit_rfq_expired(db, rfq, oid)\n"
        "    doc = _serialize_rfq_enriched(rfq)\n"
        "    if doc:\n"
        "        doc[\"items\"] = items\n"
        "        doc[\"buyerId\"] = serialize_doc(buyer) if buyer else None\n"
        "    return success_response(data={\"rfq\": doc})\n"
    )
    new_get = (
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products})\n"
        "    buyer_oid = coerce_object_id(rfq.get(\"buyerId\"))\n"
        "    is_buyer = buyer_oid is not None and str(buyer_oid) == user[\"id\"]\n"
        "    is_seller = user[\"id\"] in seller_ids\n"
        "    is_admin = user.get(\"role\") == \"admin\"\n"
        "    if not is_buyer and not is_seller and not is_admin:\n"
        "        raise HTTPException(status_code=403, detail=error_response(\"Access denied.\", \"FORBIDDEN\", path=str(request.url.path)))\n"
        "    await _maybe_emit_rfq_expired(db, rfq, oid)\n"
        "    doc = _serialize_rfq_enriched(rfq)\n"
        "    if doc:\n"
        "        doc[\"items\"] = items\n"
        "        doc[\"buyerId\"] = serialize_doc(buyer) if buyer else None\n"
        "        linked = await db.orders.find_one({\"rfqId\": oid}, sort=[(\"createdAt\", -1)], projection={\"_id\": 1})\n"
        "        if linked:\n"
        "            doc[\"linkedOrderId\"] = str(linked[\"_id\"])\n"
        "    return success_response(data={\"rfq\": doc})\n"
    )
    if old_get not in t:
        raise SystemExit("get_by_id block not found")
    t = t.replace(old_get, new_get, 1)

    old_quotes = (
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products if p.get(\"seller\")})\n"
        "    is_buyer = str(rfq[\"buyerId\"]) == user[\"id\"]\n"
    )
    new_quotes = (
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products if p.get(\"seller\")})\n"
        "    buyer_oid = coerce_object_id(rfq.get(\"buyerId\"))\n"
        "    is_buyer = buyer_oid is not None and str(buyer_oid) == user[\"id\"]\n"
    )
    if old_quotes not in t:
        raise SystemExit("get_quotes block not found")
    t = t.replace(old_quotes, new_quotes, 1)

    old_tl = (
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products})\n"
        "    is_buyer = str(rfq[\"buyerId\"]) == user[\"id\"]\n"
    )
    new_tl = (
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}, projection={\"seller\": 1}).to_list(None)\n"
        "    seller_ids = list({str(p[\"seller\"]) for p in products})\n"
        "    buyer_oid = coerce_object_id(rfq.get(\"buyerId\"))\n"
        "    is_buyer = buyer_oid is not None and str(buyer_oid) == user[\"id\"]\n"
    )
    if old_tl not in t:
        raise SystemExit("timeline block not found")
    t = t.replace(old_tl, new_tl, 1)

    old_seller_lines = (
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    my_products = await db.products.find({\"seller\": seller_oid, \"_id\": {\"$in\": product_ids}}).to_list(None)\n"
        "    my_pid_set = {p[\"_id\"] for p in my_products}\n"
        "    seller_rfq_lines = [it for it in rfq.get(\"items\", []) if it.get(\"productId\") in my_pid_set]\n"
    )
    new_seller_lines = (
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    my_products = await db.products.find({\"seller\": seller_oid, \"_id\": {\"$in\": product_ids}}).to_list(None)\n"
        "    my_pid_set = {p[\"_id\"] for p in my_products}\n"
        "    seller_rfq_lines = [it for it in rfq.get(\"items\", []) if coerce_object_id(it.get(\"productId\")) in my_pid_set]\n"
    )
    if old_seller_lines not in t:
        raise SystemExit("_seller_quote_line_items block not found")
    t = t.replace(old_seller_lines, new_seller_lines, 1)

    marker = '@router.get("/{id}/messages")'
    if "reject_quote" in t:
        print("reject_quote already present")
    else:
        reject_fn = '''

@router.post("/{id}/reject-quote/{quoteId}")
async def reject_quote(id: str, quoteId: str, request: Request, user: dict = Depends(require_roles("buyer"))):
    try:
        rfq_oid = ObjectId(id)
        quote_oid = ObjectId(quoteId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": rfq_oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    if buyer_oid is None or str(buyer_oid) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Only buyer can reject a quote.", "FORBIDDEN", path=str(request.url.path)))
    if rfq.get("status") == "accepted":
        raise HTTPException(status_code=400, detail=error_response("RFQ already has an accepted quote.", "VALIDATION_ERROR", path=str(request.url.path)))
    quote = await db.quotes.find_one({"_id": quote_oid})
    if not quote or str(quote.get("rfqId")) != id:
        raise HTTPException(status_code=404, detail=error_response("Quote not found.", "NOT_FOUND", path=str(request.url.path)))
    if quote.get("status") in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail=error_response("Quote is already final.", "VALIDATION_ERROR", path=str(request.url.path)))
    await db.quotes.update_one({"_id": quote_oid}, {"$set": {"status": "rejected"}})
    await emit_event("rfq", rfq_oid, ObjectId(user["id"]), "buyer", "QUOTE_REJECTED", "Quote rejected", {"quoteId": str(quote_oid)})
    return success_response(data={"ok": True, "quoteId": str(quote_oid), "status": "rejected"})


'''
        idx = t.find(marker)
        if idx < 0:
            raise SystemExit("messages marker not found")
        t = t[:idx] + reject_fn + t[idx:]

    RFQ.write_text(t, encoding="utf-8")
    print("rfq.py patched")


if __name__ == "__main__":
    main()
