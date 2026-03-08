from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.cart import CartAdd

router = APIRouter()


@router.get("")
async def get_cart(request: Request, user: dict = Depends(require_roles("buyer"))):
    db = get_db()
    cursor = db.cartitems.find({"buyerId": ObjectId(user["id"])}).sort("createdAt", -1)
    items = []
    async for c in cursor:
        prod = await db.products.find_one({"_id": c["productId"]}) if c.get("productId") else None
        doc = serialize_doc(c)
        if doc:
            doc["productId"] = serialize_doc(prod) if prod else c.get("productId")
        items.append(doc)
    return success_response(data={"items": items})


@router.post("")
async def add_or_update(request: Request, body: CartAdd, user: dict = Depends(require_roles("buyer"))):
    try:
        pid = ObjectId(body.productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Valid product ID required", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    quantity = max(1, body.quantity)
    await db.cartitems.update_one(
        {"buyerId": ObjectId(user["id"]), "productId": pid},
        {"$set": {"quantity": quantity, "notes": body.notes or ""}},
        upsert=True,
    )
    item = await db.cartitems.find_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    prod = await db.products.find_one({"_id": pid}) if item else None
    doc = serialize_doc(item)
    if doc:
        doc["productId"] = serialize_doc(prod) if prod else None
    return success_response(data={"item": doc})


@router.put("/{productId}")
async def update_item(productId: str, request: Request, body: CartAdd, user: dict = Depends(require_roles("buyer"))):
    try:
        pid = ObjectId(productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    result = await db.cartitems.find_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    if not result:
        raise HTTPException(status_code=404, detail=error_response("Item not in cart.", "NOT_FOUND", path=str(request.url.path)))
    quantity = max(1, body.quantity)
    await db.cartitems.update_one(
        {"buyerId": ObjectId(user["id"]), "productId": pid},
        {"$set": {"quantity": quantity, "notes": body.notes or ""}},
    )
    item = await db.cartitems.find_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    prod = await db.products.find_one({"_id": pid}) if item else None
    doc = serialize_doc(item)
    if doc:
        doc["productId"] = serialize_doc(prod) if prod else None
    return success_response(data={"item": doc})


@router.post("/clear")
async def clear(request: Request, user: dict = Depends(require_roles("buyer"))):
    db = get_db()
    await db.cartitems.delete_many({"buyerId": ObjectId(user["id"])})
    return success_response(data=None, message="Cart cleared.")


@router.delete("/{productId}")
async def remove(productId: str, request: Request, user: dict = Depends(require_roles("buyer"))):
    try:
        pid = ObjectId(productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    result = await db.cartitems.delete_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=error_response("Item not in cart.", "NOT_FOUND", path=str(request.url.path)))
    return success_response(data=None)
