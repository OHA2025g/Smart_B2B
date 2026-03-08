from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.quote import QuoteUpdate

router = APIRouter()


async def _populate_quote_items(db, items):
    out = []
    for it in items:
        prod = await db.products.find_one({"_id": it.get("productId")}) if it.get("productId") else None
        doc = dict(it)
        doc["productId"] = serialize_doc(prod) if prod else (str(it["productId"]) if it.get("productId") else None)
        out.append(doc)
    return out


@router.put("/{id}")
async def update_quote(id: str, request: Request, body: QuoteUpdate, user: dict = Depends(require_roles("seller"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid quote ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    quote = await db.quotes.find_one({"_id": oid})
    if not quote:
        raise HTTPException(status_code=404, detail=error_response("Quote not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(quote["sellerId"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Only seller can revise quote.", "FORBIDDEN", path=str(request.url.path)))
    payload = {}
    if body.items is not None:
        payload["items"] = [{"productId": ObjectId(x.productId), "unitPrice": x.unitPrice, "availableQty": x.availableQty, "deliveryDays": x.deliveryDays} for x in body.items]
    if body.message is not None:
        payload["message"] = body.message
    payload["status"] = "revised"
    await db.quotes.update_one({"_id": oid}, {"$set": payload})
    updated = await db.quotes.find_one({"_id": oid})
    items = await _populate_quote_items(db, updated.get("items", []))
    seller = await db.users.find_one({"_id": updated["sellerId"]}, projection={"name": 1, "email": 1}) if updated.get("sellerId") else None
    doc = serialize_doc(updated)
    if doc:
        doc["items"] = items
        doc["sellerId"] = serialize_doc(seller) if seller else None
    return success_response(data={"quote": doc})
