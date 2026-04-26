import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc, coerce_object_id, coerce_object_id_list
from app.schemas.rfq import BuyerCounterOfferCreate, RfqCreate, RfqStatusUpdate, QuoteSubmit
from app.schemas.message import MessagePost
from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score
from app.services.workflow_events import emit_event
from app.services.notifications import create_notification
from app.services.expiry_helpers import (
    enrich_rfq_dict,
    enrich_quote_dict,
    compute_rfq_valid_until,
    rfq_is_expired,
    compute_quote_valid_until,
    quote_is_expired,
)
from app.services import message_thread

router = APIRouter()


def _serialize_rfq_enriched(raw: dict | None) -> dict | None:
    doc = serialize_doc(raw)
    if doc:
        enrich_rfq_dict(doc)
    return doc


async def _maybe_emit_rfq_expired(db, rfq_raw: dict, rfq_oid: ObjectId):
    """One-shot workflow + buyer notification when RFQ passes validUntil (demo / no cron)."""
    now = datetime.datetime.utcnow()
    vu = compute_rfq_valid_until(rfq_raw.get("createdAt"), rfq_raw.get("validUntil"))
    if not vu or not rfq_is_expired(now, vu, rfq_raw.get("status")):
        return
    exists = await db.workflow_events.find_one({
        "entity_type": "rfq",
        "entity_id": rfq_oid,
        "event_type": "RFQ_EXPIRED",
    })
    if exists:
        return
    buyer_id = rfq_raw.get("buyerId")
    actor = buyer_id if isinstance(buyer_id, ObjectId) else ObjectId(str(buyer_id)) if buyer_id else rfq_oid
    await emit_event("rfq", rfq_oid, actor, "system", "RFQ_EXPIRED", "RFQ validity ended", {})
    if buyer_id:
        bid = buyer_id if isinstance(buyer_id, ObjectId) else ObjectId(str(buyer_id))
        await create_notification(bid, "RFQ expired", "Your RFQ is past its validity window.", "rfq_expired", "rfq", str(rfq_oid))


async def _populate_rfq_items(db, items):
    out = []
    for it in items:
        pid = it.get("productId")
        prod = await db.products.find_one({"_id": pid}) if pid else None
        doc = dict(it)
        doc["productId"] = serialize_doc(prod) if prod else (str(pid) if pid else None)
        if isinstance(doc.get("productId"), dict) and "_id" in doc.get("productId", {}):
            doc["productId"] = serialize_doc(doc["productId"])
        out.append(doc)
    return out


@router.post("/create-from-cart", status_code=201)
async def create_from_cart(request: Request, body: RfqCreate, user: dict = Depends(require_roles("buyer"))):
    """Create RFQ from current cart. Body is merged with fromCart=true; include delivery, dates, etc."""
    merged = body.model_copy(update={"fromCart": True})
    return await create(request, merged, user)


@router.post("", status_code=201)
async def create(request: Request, body: RfqCreate, user: dict = Depends(require_roles("buyer"))):
    db = get_db()
    uid = ObjectId(user["id"])
    rfq_items = body.items
    if body.fromCart:
        cart_items = []
        async for c in db.cartitems.find({"buyerId": uid}):
            prod = await db.products.find_one({"_id": c["productId"]})
            if prod:
                cart_items.append({"productId": c["productId"], "quantity": c.get("quantity", 1), "notes": c.get("notes") or ""})
        if not cart_items:
            raise HTTPException(status_code=400, detail=error_response("Cart is empty.", "VALIDATION_ERROR", path=str(request.url.path)))
        rfq_items = cart_items
    if not rfq_items or len(rfq_items) == 0:
        raise HTTPException(status_code=400, detail=error_response("RFQ must have at least one item.", "VALIDATION_ERROR", path=str(request.url.path)))
    items_doc = []
    for x in rfq_items:
        if isinstance(x, dict):
            pid = x["productId"]
            if isinstance(pid, str):
                pid = ObjectId(pid)
            qn = int(x.get("quantity", 1) or 0)
            if qn < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each line item quantity must be at least 1.", "VALIDATION_ERROR", path=str(request.url.path)),
                )
            items_doc.append({"productId": pid, "quantity": qn, "notes": x.get("notes") or ""})
        else:
            if int(x.quantity) < 1:
                raise HTTPException(
                    status_code=400,
                    detail=error_response("Each line item quantity must be at least 1.", "VALIDATION_ERROR", path=str(request.url.path)),
                )
            items_doc.append({"productId": ObjectId(x.productId), "quantity": x.quantity, "notes": x.notes or ""})
    now = datetime.datetime.utcnow()

    dloc = (body.deliveryLocation or "").strip()
    if not dloc:
        raise HTTPException(
            status_code=400,
            detail=error_response("deliveryLocation is required.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    rbd = _naive_utc(body.requiredByDate) if body.requiredByDate else None
    if not rbd:
        raise HTTPException(
            status_code=400,
            detail=error_response("requiredByDate is required.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    if rbd <= now:
        raise HTTPException(
            status_code=400,
            detail=error_response("requiredByDate cannot be in the past.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    if body.validUntil is not None:
        vu = _naive_utc(body.validUntil)
        if vu <= now:
            raise HTTPException(
                status_code=400,
                detail=error_response("validUntil must be in the future if provided.", "VALIDATION_ERROR", path=str(request.url.path)),
            )
        valid_until = vu
    else:
        valid_until = now + datetime.timedelta(days=7)
    buy_notes = (body.buyerNotes or "").strip() or None
    pri = body.priority or "normal"
    doc = {
        "buyerId": uid,
        "items": items_doc,
        "status": "sent",
        "createdAt": now,
        "validUntil": valid_until,
        "deliveryLocation": dloc,
        "requiredByDate": rbd,
        "buyerNotes": buy_notes,
        "priority": pri,
    }
    r = await db.rfqs.insert_one(doc)
    await emit_event("rfq", r.inserted_id, uid, "buyer", "RFQ_CREATED", "RFQ created", {})
    product_ids = [it.get("productId") for it in items_doc if it.get("productId")]
    if product_ids:
        products_for_sellers = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
        seller_ids = list({p["seller"] for p in products_for_sellers if p.get("seller")})
        for sid in seller_ids:
            await create_notification(sid, "New RFQ", "You have a new RFQ matching your products.", "rfq_created", "rfq", str(r.inserted_id))
    if body.fromCart:
        await db.cartitems.delete_many({"buyerId": uid})
    rfq = await db.rfqs.find_one({"_id": r.inserted_id})
    populated_items = await _populate_rfq_items(db, rfq.get("items", []))
    out = _serialize_rfq_enriched(rfq)
    if out:
        out["items"] = populated_items
    return success_response(data={"rfq": out})


@router.get("/me")
async def get_my(request: Request, user: dict = Depends(require_roles("buyer"))):
    db = get_db()
    cursor = db.rfqs.find({"buyerId": ObjectId(user["id"])}).sort("createdAt", -1)
    rfqs = []
    async for rfq in cursor:
        items = await _populate_rfq_items(db, rfq.get("items", []))
        doc = _serialize_rfq_enriched(rfq)
        if doc:
            doc["items"] = items
        rfqs.append(doc)
    return success_response(data={"rfqs": rfqs})


@router.get("/assigned")
async def get_assigned(request: Request, user: dict = Depends(require_roles("seller"))):
    db = get_db()
    my_products = await db.products.find({"seller": ObjectId(user["id"])}, projection={"_id": 1}).to_list(None)
    my_ids = [p["_id"] for p in my_products]
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
    return success_response(data={"rfqs": rfqs})


@router.get("/{id}")
async def get_by_id(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    items = await _populate_rfq_items(db, rfq.get("items", []))
    buyer = await db.users.find_one({"_id": rfq["buyerId"]}, projection={"name": 1, "email": 1}) if rfq.get("buyerId") else None
    product_ids = coerce_object_id_list([it.get("productId") for it in rfq.get("items", []) if it.get("productId")])
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    is_buyer = buyer_oid is not None and str(buyer_oid) == user["id"]
    is_seller = user["id"] in seller_ids
    is_admin = user.get("role") == "admin"
    if not is_buyer and not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    await _maybe_emit_rfq_expired(db, rfq, oid)
    doc = _serialize_rfq_enriched(rfq)
    if doc:
        doc["items"] = items
        doc["buyerId"] = serialize_doc(buyer) if buyer else None
        linked = await db.orders.find_one({"rfqId": oid}, sort=[("createdAt", -1)], projection={"_id": 1})
        if linked:
            doc["linkedOrderId"] = str(linked["_id"])
    return success_response(data={"rfq": doc})


@router.put("/{id}/status")
async def update_status(id: str, request: Request, body: RfqStatusUpdate, user: dict = Depends(require_roles("buyer"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(rfq["buyerId"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Only buyer can update status.", "FORBIDDEN", path=str(request.url.path)))
    await db.rfqs.update_one({"_id": oid}, {"$set": {"status": body.status}})
    updated = await db.rfqs.find_one({"_id": oid})
    items = await _populate_rfq_items(db, updated.get("items", []))
    doc = serialize_doc(updated)
    if doc:
        doc["items"] = items
    return success_response(data={"rfq": doc})


def _naive_utc(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


async def _seller_quote_line_items(db, rfq: dict, seller_oid: ObjectId, body_items: list, request_path: str = ""):
    """Build Mongo quote `items` for this seller's RFQ lines. Raises HTTPException on validation failure."""
    product_ids = coerce_object_id_list([it.get("productId") for it in rfq.get("items", []) if it.get("productId")])
    my_products = await db.products.find({"seller": seller_oid, "_id": {"$in": product_ids}}).to_list(None)
    my_pid_set = {p["_id"] for p in my_products}
    seller_rfq_lines = [it for it in rfq.get("items", []) if coerce_object_id(it.get("productId")) in my_pid_set]
    if not seller_rfq_lines:
        raise HTTPException(
            status_code=403,
            detail=error_response("No items in this RFQ are from you.", "FORBIDDEN", path=request_path or ""),
        )
    by_pid = {ObjectId(x.productId): x for x in body_items}
    if set(by_pid.keys()) != my_pid_set:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "Quote items must include exactly one line per product you supply on this RFQ.",
                "VALIDATION_ERROR",
                path=request_path or "",
            ),
        )
    quote_items = []
    for line in seller_rfq_lines:
        pid = line["productId"]
        x = by_pid[pid]
        row = {
            "productId": pid,
            "unitPrice": float(x.unitPrice),
            "availableQty": int(x.availableQty),
            "deliveryDays": int(x.deliveryDays),
        }
        if getattr(x, "itemNote", None) and str(x.itemNote).strip():
            row["itemNote"] = str(x.itemNote).strip()[:2000]
        quote_items.append(row)
    return quote_items


@router.post("/{id}/quote", status_code=201)
async def submit_quote(id: str, request: Request, body: QuoteSubmit, user: dict = Depends(require_roles("seller"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    seller_oid = ObjectId(user["id"])
    existing = await db.quotes.find_one({"rfqId": oid, "sellerId": seller_oid})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "You already submitted a quote for this RFQ. Use PUT /api/quote/{quoteId} to revise it.",
                "CONFLICT",
                path=str(request.url.path),
            ),
        )
    now_q = datetime.datetime.utcnow()
    qvu = _naive_utc(body.quoteValidUntil)
    if qvu <= now_q:
        raise HTTPException(
            status_code=400,
            detail=error_response("quote_valid_until must be in the future.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    quote_items = await _seller_quote_line_items(db, rfq, seller_oid, body.items, str(request.url.path))
    q_msg = (body.message or "").strip()
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
    }
    r = await db.quotes.insert_one(quote_doc)
    await db.rfqs.update_one({"_id": oid}, {"$set": {"status": "quoted"}})
    await emit_event("rfq", oid, ObjectId(user["id"]), "seller", "QUOTE_SUBMITTED", "Quote submitted", {"quoteId": str(r.inserted_id)})
    buyer_id = rfq.get("buyerId")
    if buyer_id:
        await create_notification(buyer_id, "New Quote", "A supplier submitted a quote for your RFQ.", "quote_submitted", "rfq", str(oid))
    quote = await db.quotes.find_one({"_id": r.inserted_id})
    items = await _populate_rfq_items(db, quote.get("items", []))
    seller = await db.users.find_one({"_id": quote["sellerId"]}, projection={"name": 1, "email": 1}) if quote.get("sellerId") else None
    doc = serialize_doc(quote)
    if doc:
        doc["items"] = items
        doc["sellerId"] = serialize_doc(seller) if seller else None
        enrich_quote_dict(doc)
    return success_response(data={"quote": doc})


@router.get("/{id}/quotes")
async def get_quotes_by_rfq(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    product_ids = coerce_object_id_list([it.get("productId") for it in rfq.get("items", []) if it.get("productId")])
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products if p.get("seller")})
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    is_buyer = buyer_oid is not None and str(buyer_oid) == user["id"]
    is_admin = user.get("role") == "admin"
    is_assigned_seller = user.get("role") == "seller" and user["id"] in seller_ids
    if not is_buyer and not is_admin and not is_assigned_seller:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    cursor = db.quotes.find({"rfqId": oid}).sort("createdAt", -1)
    quotes_raw = []
    async for q in cursor:
        quotes_raw.append(q)
    if is_assigned_seller and not is_buyer and not is_admin:
        quotes_raw = [q for q in quotes_raw if str(q.get("sellerId")) == user["id"]]
    rfq_items = rfq.get("items", [])
    all_totals = []
    quotes = []
    for q in quotes_raw:
        items = await _populate_rfq_items(db, q.get("items", []))
        total_price = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in q.get("items", []))
        all_totals.append(total_price)
    for q in quotes_raw:
        items = await _populate_rfq_items(db, q.get("items", []))
        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None
        supplier_score = score_data.get("total_score", 0) if score_data else 0
        quote_score_val = compute_quote_score(q.get("items", []), rfq_items, supplier_score, all_totals)
        doc = serialize_doc(q)
        if doc:
            doc["items"] = items
            doc["sellerId"] = serialize_doc(seller) if seller else None
            if doc["sellerId"]:
                doc["sellerId"]["trustScore"] = supplier_score
                doc["sellerId"]["trustLevel"] = (score_data or {}).get("trust_level", "Low Trust")
            doc["quoteScore"] = quote_score_val
            enrich_quote_dict(doc)
        quotes.append(doc)
    return success_response(data={"quotes": quotes})


@router.get("/{id}/quote-comparison")
async def get_quote_comparison(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(rfq["buyerId"]) != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Only buyer can view quote comparison.", "FORBIDDEN", path=str(request.url.path)))
    cursor = db.quotes.find({"rfqId": oid}).sort("createdAt", -1)
    quotes_raw = []
    async for q in cursor:
        quotes_raw.append(q)
    rfq_items = rfq.get("items", [])
    all_totals = []
    for q in quotes_raw:
        total_price = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in q.get("items", []))
        all_totals.append(total_price)
    now_cmp = datetime.datetime.utcnow()
    rows = []
    for q in quotes_raw:
        items = q.get("items", [])
        total_amount = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in items)
        avg_delivery = sum(it.get("deliveryDays") or 7 for it in items) / len(items) if items else 7
        available_qty = min((it.get("availableQty") or 0 for it in items), default=0) if items else 0
        seller = await db.users.find_one({"_id": q["sellerId"]}, projection={"name": 1, "email": 1, "isVerifiedSupplier": 1}) if q.get("sellerId") else None
        company = await db.companyprofiles.find_one({"user": q["sellerId"]}, projection={"companyName": 1, "city": 1}) if q.get("sellerId") else None
        score_data = await get_supplier_score_for_response(q["sellerId"]) if q.get("sellerId") else None
        supplier_score = score_data.get("total_score", 0) if score_data else 0
        quote_score_val = compute_quote_score(items, rfq_items, supplier_score, all_totals)
        qvu = compute_quote_valid_until(q.get("createdAt"), q.get("quoteValidUntil"))
        q_exp = quote_is_expired(now_cmp, qvu, q.get("status"))
        # average_rating: derived from supplier score buyer_rating component (0–100) → 1–5 scale for display
        br = float((score_data or {}).get("buyer_rating", 70) or 70)
        average_rating = round(min(5.0, max(1.0, br / 20.0)), 2)
        rows.append({
            "quoteId": str(q["_id"]),
            "seller_id": str(q["sellerId"]),
            "seller_name": (seller or {}).get("name") or (company or {}).get("companyName") or "Supplier",
            "company_name": (company or {}).get("companyName") or "",
            "verified_supplier": bool((seller or {}).get("isVerifiedSupplier")),
            "trust_score": supplier_score,
            "trust_level": (score_data or {}).get("trust_level", "Low Trust"),
            "quoted_price": total_amount,
            "delivery_days": round(avg_delivery, 0),
            "available_qty": available_qty,
            "total_amount": total_amount,
            "average_rating": average_rating,
            "quote_valid_until": qvu.isoformat() if qvu and hasattr(qvu, "isoformat") else None,
            "is_expired": q_exp,
            "quote_score": quote_score_val,
            "best_quote": False,
        })
    rows.sort(key=lambda x: (-x["quote_score"], x["quoted_price"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["best_quote"] = i == 1
    return success_response(data={"comparison": rows})


@router.post("/{id}/accept-quote/{quoteId}", status_code=201)
async def accept_quote(id: str, quoteId: str, request: Request, user: dict = Depends(require_roles("buyer"))):
    try:
        rfq_oid = ObjectId(id)
        quote_oid = ObjectId(quoteId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": rfq_oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(rfq["buyerId"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Only buyer can accept a quote.", "FORBIDDEN", path=str(request.url.path)))
    quote = await db.quotes.find_one({"_id": quote_oid})
    if not quote or str(quote["rfqId"]) != id:
        raise HTTPException(status_code=404, detail=error_response("Quote not found.", "NOT_FOUND", path=str(request.url.path)))
    if quote.get("status") == "rejected":
        raise HTTPException(status_code=400, detail=error_response("Quote was rejected.", "VALIDATION_ERROR", path=str(request.url.path)))
    now_acc = datetime.datetime.utcnow()
    qvu_acc = compute_quote_valid_until(quote.get("createdAt"), quote.get("quoteValidUntil"))
    if quote_is_expired(now_acc, qvu_acc, quote.get("status")):
        raise HTTPException(status_code=400, detail=error_response("Quote validity has expired.", "VALIDATION_ERROR", path=str(request.url.path)))
    total = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in quote.get("items", []))
    order_items = [{"productId": it.get("productId"), "quantity": it.get("availableQty") or 1, "agreedUnitPrice": it.get("unitPrice", 0)} for it in quote.get("items", [])]
    now = datetime.datetime.utcnow()
    order_doc = {
        "rfqId": rfq_oid,
        "quoteId": quote_oid,
        "buyerId": ObjectId(user["id"]),
        "sellerId": quote["sellerId"],
        "items": order_items,
        "totalAmount": total,
        "status": "created",
        "createdAt": now,
        "paymentStatus": "payment_pending",
    }
    r = await db.orders.insert_one(order_doc)
    await db.quotes.update_many({"rfqId": rfq_oid}, {"$set": {"status": "rejected"}})
    await db.quotes.update_one({"_id": quote_oid}, {"$set": {"status": "accepted"}})
    await db.rfqs.update_one({"_id": rfq_oid}, {"$set": {"status": "accepted"}})
    await emit_event("rfq", rfq_oid, ObjectId(user["id"]), "buyer", "QUOTE_ACCEPTED", "Quote accepted", {"quoteId": str(quote_oid)})
    await emit_event("order", r.inserted_id, ObjectId(user["id"]), "buyer", "ORDER_CREATED", "Order created", {"rfqId": str(rfq_oid)})
    seller_id = quote.get("sellerId")
    if seller_id:
        await create_notification(seller_id, "Quote Accepted", "Your quote was accepted.", "quote_accepted", "rfq", str(rfq_oid))
        await create_notification(seller_id, "New Order", "You received a new order.", "order_created", "order", str(r.inserted_id))
    await create_notification(
        ObjectId(user["id"]),
        "Order placed",
        "Your order was created from the accepted quote.",
        "order_placed",
        "order",
        str(r.inserted_id),
    )
    order = await db.orders.find_one({"_id": r.inserted_id})
    items = await _populate_rfq_items(db, order.get("items", []))
    buyer = await db.users.find_one({"_id": order["buyerId"]}, projection={"name": 1, "email": 1}) if order.get("buyerId") else None
    seller = await db.users.find_one({"_id": order["sellerId"]}, projection={"name": 1, "email": 1}) if order.get("sellerId") else None
    doc = serialize_doc(order)
    if doc:
        doc["items"] = items
        doc["buyerId"] = serialize_doc(buyer) if buyer else None
        doc["sellerId"] = serialize_doc(seller) if seller else None
    return success_response(data={"order": doc})




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


@router.get("/{id}/counter-offers")
async def get_counter_offers(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path))
        )
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    product_ids = coerce_object_id_list([it.get("productId") for it in rfq.get("items", []) if it.get("productId")])
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    is_buyer = buyer_oid is not None and str(buyer_oid) == user["id"]
    is_seller = user["id"] in seller_ids
    is_admin = user.get("role") == "admin"
    if not is_buyer and not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    out: list[dict] = []
    col = db["buyer_counter_offers"]
    async for doc in col.find({"rfqId": oid}).sort("createdAt", -1):
        if is_seller and not is_buyer and not is_admin:
            q = await db.quotes.find_one({"_id": doc.get("quoteId")}, projection={"sellerId": 1})
            if not q or str(q.get("sellerId")) != user["id"]:
                continue
        buyer_u = None
        if doc.get("buyerId"):
            buyer_u = await db.users.find_one(
                {"_id": doc["buyerId"]},
                projection={"name": 1, "email": 1},
            )
        d = serialize_doc(doc)
        if d:
            d["buyerId"] = serialize_doc(buyer_u) if buyer_u else None
        out.append(d)
    return success_response(data={"counterOffers": out})


@router.post("/{id}/counter-offer", status_code=201)
async def post_counter_offer(
    id: str,
    request: Request,
    body: BuyerCounterOfferCreate,
    user: dict = Depends(require_roles("buyer")),
):
    try:
        rfq_oid = ObjectId(id)
        quote_oid = ObjectId(body.quoteId)
    except Exception:
        raise HTTPException(
            status_code=400, detail=error_response("Invalid ID", "VALIDATION_ERROR", path=str(request.url.path))
        )
    msg = body.message.strip()
    if not msg:
        raise HTTPException(
            status_code=400, detail=error_response("message is required.", "VALIDATION_ERROR", path=str(request.url.path))
        )
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": rfq_oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(rfq.get("buyerId")) != user["id"]:
        raise HTTPException(
            status_code=403, detail=error_response("Only the buyer can send a counter-offer.", "FORBIDDEN", path=str(request.url.path))
        )
    if rfq.get("status") in ("accepted", "rejected", "closed"):
        raise HTTPException(
            status_code=400,
            detail=error_response("This RFQ is not open for negotiation.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    quote = await db.quotes.find_one({"_id": quote_oid})
    if not quote or str(quote.get("rfqId")) != id:
        raise HTTPException(status_code=404, detail=error_response("Quote not found.", "NOT_FOUND", path=str(request.url.path)))
    if quote.get("status") in ("accepted", "rejected"):
        raise HTTPException(
            status_code=400, detail=error_response("This quote is already final.", "VALIDATION_ERROR", path=str(request.url.path))
        )
    now = datetime.datetime.utcnow()
    qvu = compute_quote_valid_until(quote.get("createdAt"), quote.get("quoteValidUntil"))
    if quote_is_expired(now, qvu, quote.get("status")):
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "This quote is past its validity date. The supplier can submit a new revision.",
                "VALIDATION_ERROR",
                path=str(request.url.path),
            ),
        )
    doc = {
        "rfqId": rfq_oid,
        "quoteId": quote_oid,
        "buyerId": ObjectId(user["id"]),
        "message": msg[:5000],
        "proposedTotal": body.proposedTotal,
        "createdAt": now,
    }
    r = await db["buyer_counter_offers"].insert_one(doc)
    ins = await db["buyer_counter_offers"].find_one({"_id": r.inserted_id})
    seller_id = quote.get("sellerId")
    if seller_id:
        preview = (msg[:180] + "…") if len(msg) > 180 else msg
        await create_notification(
            seller_id,
            "Buyer counter-offer",
            f"The buyer sent a counter-offer: {preview}",
            "buyer_counter",
            "rfq",
            str(rfq_oid),
        )
    await emit_event(
        "rfq",
        rfq_oid,
        ObjectId(user["id"]),
        "buyer",
        "BUYER_COUNTER_OFFER",
        "Buyer sent a counter-offer",
        {"quoteId": str(quote_oid)},
    )
    buyer_u = await db.users.find_one({"_id": ObjectId(user["id"])}, projection={"name": 1, "email": 1})
    d = serialize_doc(ins) if ins else None
    if d:
        d["buyerId"] = serialize_doc(buyer_u) if buyer_u else None
    return success_response(data={"counterOffer": d})


@router.get("/{id}/messages")
async def rfq_messages_get(id: str, user: dict = Depends(get_current_user)):
    """Alias of GET /api/messages/{rfqId} for /api/rfqs/{id}/messages."""
    return await message_thread.get_thread_response(id, user)


@router.post("/{id}/messages", status_code=201)
async def rfq_messages_post(id: str, body: MessagePost, user: dict = Depends(get_current_user)):
    """Alias of POST /api/messages/{rfqId}."""
    return await message_thread.post_message_response(id, user, body.text, confirm_send=bool(body.confirm_send))


@router.get("/{id}/timeline")
async def get_rfq_timeline(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    product_ids = coerce_object_id_list([it.get("productId") for it in rfq.get("items", []) if it.get("productId")])
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    is_buyer = buyer_oid is not None and str(buyer_oid) == user["id"]
    is_seller = user["id"] in seller_ids
    is_admin = user.get("role") == "admin"
    if not is_buyer and not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    cursor = db.workflow_events.find({"entity_type": "rfq", "entity_id": oid}).sort("created_at", 1)
    events = [serialize_doc(e) async for e in cursor]
    return success_response(data={"timeline": events})
