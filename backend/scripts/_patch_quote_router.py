from pathlib import Path

QUOTE = r'''import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.quote import QuoteUpdate
from app.routers.rfq import _seller_quote_line_items
from app.services.workflow_events import emit_event
from app.services.notifications import create_notification
from app.services.expiry_helpers import enrich_quote_dict

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
    if quote.get("status") in ("accepted", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=error_response("Cannot revise an accepted or rejected quote.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    payload = {}
    if body.items is not None:
        rfq = await db.rfqs.find_one({"_id": quote["rfqId"]})
        if not rfq:
            raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
        payload["items"] = await _seller_quote_line_items(
            db, rfq, ObjectId(user["id"]), body.items, str(request.url.path)
        )
    if body.message is not None:
        payload["message"] = body.message
    if body.commitment_note is not None:
        payload["commitmentNote"] = body.commitment_note
    if body.deliveryCommitment is not None:
        d = (body.deliveryCommitment or "").strip() or None
        payload["deliveryCommitment"] = d
        if body.commitment_note is None:
            payload["commitmentNote"] = d
    if body.warrantyOrSupportNote is not None:
        payload["warrantyOrSupportNote"] = (body.warrantyOrSupportNote or "").strip() or None
    if body.termsAndConditions is not None:
        payload["termsAndConditions"] = (body.termsAndConditions or "").strip() or None
    if body.quoteValidUntil is not None:
        qvu = body.quoteValidUntil.replace(tzinfo=None) if body.quoteValidUntil.tzinfo else body.quoteValidUntil
        now_u = datetime.datetime.utcnow()
        if qvu <= now_u:
            raise HTTPException(
                status_code=400,
                detail=error_response("quote_valid_until must be in the future.", "VALIDATION_ERROR", path=str(request.url.path)),
            )
        payload["quoteValidUntil"] = qvu
    if not payload:
        raise HTTPException(
            status_code=400,
            detail=error_response("No changes supplied.", "VALIDATION_ERROR", path=str(request.url.path)),
        )
    payload["status"] = "revised"
    await db.quotes.update_one({"_id": oid}, {"$set": payload})
    updated = await db.quotes.find_one({"_id": oid})
    rfq_oid = updated.get("rfqId")
    if rfq_oid:
        await emit_event("rfq", rfq_oid, ObjectId(user["id"]), "seller", "QUOTE_REVISED", "Quote revised", {"quoteId": str(oid)})
        rfq = await db.rfqs.find_one({"_id": rfq_oid})
        if rfq and rfq.get("buyerId"):
            await create_notification(
                rfq["buyerId"],
                "Quote updated",
                "A supplier revised their quote on your RFQ.",
                "quote_revised",
                "rfq",
                str(rfq_oid),
            )
    items = await _populate_quote_items(db, updated.get("items", []))
    seller = await db.users.find_one({"_id": updated["sellerId"]}, projection={"name": 1, "email": 1}) if updated.get("sellerId") else None
    doc = serialize_doc(updated)
    if doc:
        doc["items"] = items
        doc["sellerId"] = serialize_doc(seller) if seller else None
        enrich_quote_dict(doc)
    return success_response(data={"quote": doc})
'''

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    (base / "app/routers/quote.py").write_text(QUOTE, encoding="utf-8")
    print("quote router written")
