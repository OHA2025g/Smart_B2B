from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.message import MessagePost

router = APIRouter()


@router.get("/{rfqId}")
async def get_thread(rfqId: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(rfqId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    product_ids = [it.get("productId") for it in rfq.get("items", []) if it.get("productId")]
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    is_buyer = str(rfq["buyerId"]) == user["id"]
    is_seller = user["id"] in seller_ids
    if not is_buyer and not is_seller and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    thread = await db.messagethreads.find_one({"rfqId": oid})
    if not thread:
        all_ids = [rfq["buyerId"]] + [p["seller"] for p in products]
        seen = set()
        participants = [x for x in all_ids if (s := str(x)) not in seen and not seen.add(s)]
        r = await db.messagethreads.insert_one({"rfqId": oid, "participants": participants, "messages": []})
        thread = await db.messagethreads.find_one({"_id": r.inserted_id})
    for i, m in enumerate(thread.get("messages", [])):
        if m.get("senderId"):
            sender = await db.users.find_one({"_id": m["senderId"]}, projection={"name": 1, "email": 1})
            if sender:
                thread["messages"][i] = {**m, "senderId": serialize_doc(sender)}
    return success_response(data={"thread": serialize_doc(thread)})


@router.post("/{rfqId}", status_code=201)
async def post_message(rfqId: str, request: Request, body: MessagePost, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(rfqId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=str(request.url.path)))
    product_ids = [it.get("productId") for it in rfq.get("items", []) if it.get("productId")]
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    is_buyer = str(rfq["buyerId"]) == user["id"]
    is_seller = user["id"] in seller_ids
    if not is_buyer and not is_seller:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    thread = await db.messagethreads.find_one({"rfqId": oid})
    if not thread:
        all_ids = [rfq["buyerId"]] + [p["seller"] for p in products]
        seen = set()
        participants = [x for x in all_ids if (s := str(x)) not in seen and not seen.add(s)]
        r = await db.messagethreads.insert_one({"rfqId": oid, "participants": participants, "messages": []})
        thread = await db.messagethreads.find_one({"_id": r.inserted_id})
    thread["messages"].append({"senderId": ObjectId(user["id"]), "text": body.text.strip(), "createdAt": __import__("datetime").datetime.utcnow()})
    await db.messagethreads.update_one({"_id": thread["_id"]}, {"$set": {"messages": thread["messages"]}})
    thread = await db.messagethreads.find_one({"_id": thread["_id"]})
    for i, m in enumerate(thread.get("messages", [])):
        if m.get("senderId"):
            sender = await db.users.find_one({"_id": m["senderId"]}, projection={"name": 1, "email": 1})
            if sender:
                thread["messages"][i] = {**m, "senderId": serialize_doc(sender)}
    return success_response(data={"thread": serialize_doc(thread)})
