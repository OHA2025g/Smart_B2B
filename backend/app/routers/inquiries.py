from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.inquiry import InquiryCreate

router = APIRouter()


async def _populate_inquiry(db, inquiry):
    product = await db.products.find_one({"_id": inquiry["product"]}) if inquiry.get("product") else None
    buyer = await db.users.find_one({"_id": inquiry["buyer"]}, projection={"name": 1, "email": 1}) if inquiry.get("buyer") else None
    seller = await db.users.find_one({"_id": inquiry["seller"]}, projection={"name": 1, "email": 1}) if inquiry.get("seller") else None
    doc = serialize_doc(inquiry)
    if doc:
        doc["product"] = serialize_doc(product) if product else None
        doc["buyer"] = serialize_doc(buyer) if buyer else None
        doc["seller"] = serialize_doc(seller) if seller else None
    return doc


@router.post("", status_code=201)
async def create(request: Request, body: InquiryCreate, user: dict = Depends(get_current_user)):
    if user.get("role") != "buyer":
        raise HTTPException(status_code=403, detail=error_response("Access denied for this role.", "FORBIDDEN", path=str(request.url.path)))
    try:
        product_oid = ObjectId(body.productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Valid product ID required", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    product = await db.products.find_one({"_id": product_oid})
    if not product:
        raise HTTPException(status_code=404, detail=error_response("Product not found.", "NOT_FOUND", path=str(request.url.path)))
    doc = {
        "buyer": ObjectId(user["id"]),
        "product": product_oid,
        "seller": product["seller"],
        "message": body.message.strip(),
        "quantity": body.quantity,
        "status": "pending",
    }
    r = await db.inquiries.insert_one(doc)
    inquiry = await db.inquiries.find_one({"_id": r.inserted_id})
    populated = await _populate_inquiry(db, inquiry)
    return success_response(data={"inquiry": populated})


@router.get("/me")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    if user.get("role") == "buyer":
        filter_q = {"buyer": uid}
    elif user.get("role") == "seller":
        filter_q = {"seller": uid}
    else:
        filter_q = {}
    cursor = db.inquiries.find(filter_q).sort("createdAt", -1)
    inquiries = []
    async for inv in cursor:
        inv_doc = await _populate_inquiry(db, inv)
        if inv_doc and inv_doc.get("product"):
            inv_doc["product"] = {k: inv_doc["product"].get(k) for k in ("id", "title", "category", "price") if inv_doc["product"].get(k) is not None}
        inquiries.append(inv_doc)
    return success_response(data={"inquiries": inquiries})
