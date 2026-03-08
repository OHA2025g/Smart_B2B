from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.rfq import RfqCreate, RfqStatusUpdate, QuoteSubmit
from app.services.supplier_score import get_supplier_score_for_response, compute_quote_score

router = APIRouter()


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
async def create_from_cart(request: Request, user: dict = Depends(require_roles("buyer"))):
    """Create RFQ from current cart. Same as POST / with body { fromCart: true }."""
    return await create(request, RfqCreate(fromCart=True), user)


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
            items_doc.append({"productId": pid, "quantity": x.get("quantity", 1), "notes": x.get("notes") or ""})
        else:
            items_doc.append({"productId": ObjectId(x.productId), "quantity": x.quantity, "notes": x.notes or ""})
    doc = {"buyerId": uid, "items": items_doc, "status": "sent"}
    r = await db.rfqs.insert_one(doc)
    if body.fromCart:
        await db.cartitems.delete_many({"buyerId": uid})
    rfq = await db.rfqs.find_one({"_id": r.inserted_id})
    populated_items = await _populate_rfq_items(db, rfq.get("items", []))
    out = serialize_doc(rfq)
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
        doc = serialize_doc(rfq)
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
        doc = serialize_doc(rfq)
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
    product_ids = [it.get("productId") for it in rfq.get("items", []) if it.get("productId")]
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    is_buyer = str(rfq["buyerId"]) == user["id"]
    is_seller = user["id"] in seller_ids
    is_admin = user.get("role") == "admin"
    if not is_buyer and not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    doc = serialize_doc(rfq)
    if doc:
        doc["items"] = items
        doc["buyerId"] = serialize_doc(buyer) if buyer else None
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
    product_ids = [it.get("productId") for it in rfq.get("items", [])]
    my_products = await db.products.find({"seller": ObjectId(user["id"]), "_id": {"$in": product_ids}}).to_list(None)
    if not my_products:
        raise HTTPException(status_code=403, detail=error_response("No items in this RFQ are from you.", "FORBIDDEN", path=str(request.url.path)))
    default_items = []
    for it in rfq.get("items", []):
        prod = await db.products.find_one({"_id": it["productId"]})
        default_items.append({"productId": it["productId"], "unitPrice": prod.get("price", 0) if prod else 0, "availableQty": it.get("quantity", 1), "deliveryDays": 7})
    if body.items and len(body.items) > 0:
        quote_items = [{"productId": ObjectId(x.productId), "unitPrice": x.unitPrice, "availableQty": x.availableQty, "deliveryDays": x.deliveryDays} for x in body.items]
    else:
        quote_items = default_items
    quote_doc = {"rfqId": oid, "sellerId": ObjectId(user["id"]), "items": quote_items, "message": body.message or "", "status": "submitted"}
    r = await db.quotes.insert_one(quote_doc)
    await db.rfqs.update_one({"_id": oid}, {"$set": {"status": "quoted"}})
    quote = await db.quotes.find_one({"_id": r.inserted_id})
    items = await _populate_rfq_items(db, quote.get("items", []))
    seller = await db.users.find_one({"_id": quote["sellerId"]}, projection={"name": 1, "email": 1}) if quote.get("sellerId") else None
    doc = serialize_doc(quote)
    if doc:
        doc["items"] = items
        doc["sellerId"] = serialize_doc(seller) if seller else None
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
    if str(rfq["buyerId"]) != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Only buyer can view quotes.", "FORBIDDEN", path=str(request.url.path)))
    cursor = db.quotes.find({"rfqId": oid}).sort("createdAt", -1)
    quotes_raw = []
    async for q in cursor:
        quotes_raw.append(q)
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
        quotes.append(doc)
    return success_response(data={"quotes": quotes})


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
    total = sum(it.get("unitPrice", 0) * (it.get("availableQty") or 1) for it in quote.get("items", []))
    order_items = [{"productId": it.get("productId"), "quantity": it.get("availableQty") or 1, "agreedUnitPrice": it.get("unitPrice", 0)} for it in quote.get("items", [])]
    order_doc = {"rfqId": rfq_oid, "quoteId": quote_oid, "buyerId": ObjectId(user["id"]), "sellerId": quote["sellerId"], "items": order_items, "totalAmount": total, "status": "created"}
    r = await db.orders.insert_one(order_doc)
    await db.quotes.update_many({"rfqId": rfq_oid}, {"$set": {"status": "rejected"}})
    await db.quotes.update_one({"_id": quote_oid}, {"$set": {"status": "accepted"}})
    await db.rfqs.update_one({"_id": rfq_oid}, {"$set": {"status": "accepted"}})
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
