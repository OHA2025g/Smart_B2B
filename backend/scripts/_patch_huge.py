# Patch rfq.py — run: python backend/scripts/_patch_huge.py
from pathlib import Path


def main():
    base = Path(__file__).resolve().parent.parent
    p = base / "app/routers/rfq.py"
    rfq = p.read_text(encoding="utf-8")

    rfq = rfq.replace(
        '''@router.post("/create-from-cart", status_code=201)
async def create_from_cart(request: Request, user: dict = Depends(require_roles("buyer"))):
    """Create RFQ from current cart. Same as POST / with body { fromCart: true }."""
    return await create(request, RfqCreate(fromCart=True), user)''',
        '''@router.post("/create-from-cart", status_code=201)
async def create_from_cart(request: Request, body: RfqCreate, user: dict = Depends(require_roles("buyer"))):
    """Create RFQ from current cart. Body is merged with fromCart=true; include delivery, dates, etc."""
    merged = body.model_copy(update={"fromCart": True})
    return await create(request, merged, user)''',
    )

    rfq = rfq.replace(
        "async def _seller_quote_line_items(db, rfq: dict, seller_oid: ObjectId, body_items: list):",
        "async def _seller_quote_line_items(db, rfq: dict, seller_oid: ObjectId, body_items: list, request_path: str = \"\"):",
    )
    rfq = rfq.replace(
        'detail=error_response("No items in this RFQ are from you.", "FORBIDDEN", path=str(request.url.path)),',
        'detail=error_response("No items in this RFQ are from you.", "FORBIDDEN", path=request_path or ""),',
    )
    rfq = rfq.replace(
        '''                "Quote items must include exactly one line per product you supply on this RFQ.",
                "VALIDATION_ERROR",
                path=str(request.url.path),''',
        '''                "Quote items must include exactly one line per product you supply on this RFQ.",
                "VALIDATION_ERROR",
                path=request_path or "",''',
    )
    rfq = rfq.replace(
        "quote_items = await _seller_quote_line_items(db, rfq, seller_oid, body.items)",
        "quote_items = await _seller_quote_line_items(db, rfq, seller_oid, body.items, str(request.url.path))",
    )

    old_block = """    now = datetime.datetime.utcnow()
    valid_until = now + datetime.timedelta(days=7)
    doc = {\"buyerId\": uid, \"items\": items_doc, \"status\": \"sent\", \"createdAt\": now, \"validUntil\": valid_until}"""
    new_block = """    now = datetime.datetime.utcnow()

    dloc = (body.deliveryLocation or \"\").strip()
    if not dloc:
        raise HTTPException(
            status_code=400,
            detail=error_response(\"deliveryLocation is required.\", \"VALIDATION_ERROR\", path=str(request.url.path)),
        )
    rbd = _naive_utc(body.requiredByDate) if body.requiredByDate else None
    if not rbd:
        raise HTTPException(
            status_code=400,
            detail=error_response(\"requiredByDate is required.\", \"VALIDATION_ERROR\", path=str(request.url.path)),
        )
    if rbd <= now:
        raise HTTPException(
            status_code=400,
            detail=error_response(\"requiredByDate cannot be in the past.\", \"VALIDATION_ERROR\", path=str(request.url.path)),
        )
    if body.validUntil is not None:
        vu = _naive_utc(body.validUntil)
        if vu <= now:
            raise HTTPException(
                status_code=400,
                detail=error_response(\"validUntil must be in the future if provided.\", \"VALIDATION_ERROR\", path=str(request.url.path)),
            )
        valid_until = vu
    else:
        valid_until = now + datetime.timedelta(days=7)
    buy_notes = (body.buyerNotes or \"\").strip() or None
    pri = body.priority or \"normal\"
    doc = {
        \"buyerId\": uid,
        \"items\": items_doc,
        \"status\": \"sent\",
        \"createdAt\": now,
        \"validUntil\": valid_until,
        \"deliveryLocation\": dloc,
        \"requiredByDate\": rbd,
        \"buyerNotes\": buy_notes,
        \"priority\": pri,
    }"""
    if old_block not in rfq:
        raise SystemExit("old create block not found")
    rfq = rfq.replace(old_block, new_block, 1)

    part = """        if isinstance(x, dict):
            pid = x[\"productId\"]
            if isinstance(pid, str):
                pid = ObjectId(pid)
            items_doc.append({\"productId\": pid, \"quantity\": x.get(\"quantity\", 1), \"notes\": x.get(\"notes\") or \"\"})"""
    new_part = """        if isinstance(x, dict):
            pid = x[\"productId\"]
            if isinstance(pid, str):
                pid = ObjectId(pid)
            qn = int(x.get(\"quantity\", 1) or 0)
            if qn < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response(\"Each line item quantity must be at least 1.\", \"VALIDATION_ERROR\", path=str(request.url.path)),
                )
            items_doc.append({\"productId\": pid, \"quantity\": qn, \"notes\": x.get(\"notes\") or \"\"})"""
    if part not in rfq:
        raise SystemExit("items dict block not found")
    rfq = rfq.replace(part, new_part, 1)

    # else branch for RfqItem
    else_part = "else:\n            items_doc.append({\"productId\": ObjectId(x.productId), \"quantity\": x.quantity, \"notes\": x.notes or \"\"})"
    # validate pydantic RfqItem quantity
    new_else = """else:
            if int(x.quantity) < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each line item quantity must be at least 1.", "VALIDATION_ERROR", path=str(request.url.path)),
                )
            items_doc.append({"productId": ObjectId(x.productId), "quantity": x.quantity, "notes": x.notes or ""})"""
    if else_part in rfq:
        rfq = rfq.replace(else_part, new_else, 1)
    else:
        print("warn: else RfqItem branch not matched exactly, skip if needed")

    old_q = """    quote_doc = {
        "rfqId": oid,
        "sellerId": seller_oid,
        "items": quote_items,
        "message": (body.message or "").strip(),
        "termsAndConditions": (body.termsAndConditions or "").strip() or None,
        "status": "submitted",
        "createdAt": now_q,
        "quoteValidUntil": qvu,
    }"""
    new_q = """    q_msg = (body.message or "").strip()
    q_tnc = (body.termsAndConditions or "").strip() or None
    q_del = (body.deliveryCommitment or "").strip() or None
    q_war = (body.warrantyOrSupportNote or "").strip() or None
    quote_doc = {
        "rfqId": oid,
        "sellerId": seller_oid,
        "items": quote_items,
        "message": q_msg,
        "termsAndConditions": q_tnc,
        "deliveryCommitment": q_del,
        "warrantyOrSupportNote": q_war,
        "status": "submitted",
        "createdAt": now_q,
        "quoteValidUntil": qvu,
    }"""
    if old_q not in rfq:
        raise SystemExit("quote doc block not found")
    rfq = rfq.replace(old_q, new_q, 1)

    old_o = 'order_doc = {"rfqId": rfq_oid, "quoteId": quote_oid, "buyerId": ObjectId(user["id"]), "sellerId": quote["sellerId"], "items": order_items, "totalAmount": total, "status": "created", "createdAt": now}'
    new_o = """order_doc = {
        "rfqId": rfq_oid,
        "quoteId": quote_oid,
        "buyerId": ObjectId(user["id"]),
        "sellerId": quote["sellerId"],
        "items": order_items,
        "totalAmount": total,
        "status": "created",
        "createdAt": now,
        "paymentStatus": "payment_pending",
    }"""
    if old_o not in rfq:
        raise SystemExit("order doc not found")
    rfq = rfq.replace(old_o, new_o, 1)

    p.write_text(rfq, encoding="utf-8")
    print("rfq.py patched ok")


if __name__ == "__main__":
    main()
