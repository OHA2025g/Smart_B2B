from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc

router = APIRouter()


@router.get("")
async def get_wishlist(request: Request, user: dict = Depends(require_roles("buyer"))):
    db = get_db()
    cursor = db.wishlistitems.find({"buyerId": ObjectId(user["id"])}).sort("createdAt", -1)
    items = []
    async for w in cursor:
        prod = await db.products.find_one({"_id": w["productId"]}) if w.get("productId") else None
        doc = serialize_doc(w)
        if doc:
            doc["productId"] = serialize_doc(prod) if prod else w.get("productId")
        items.append(doc)
    return success_response(data={"items": items})


@router.post("/{productId}")
async def toggle(productId: str, request: Request, user: dict = Depends(require_roles("buyer"))):
    try:
        pid = ObjectId(productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    existing = await db.wishlistitems.find_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    if existing:
        await db.wishlistitems.delete_one({"_id": existing["_id"]})
        return success_response(data={"added": False, "message": "Removed from wishlist."})
    await db.wishlistitems.insert_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    return success_response(data={"added": True, "message": "Added to wishlist."})


@router.delete("/{productId}")
async def remove(productId: str, request: Request, user: dict = Depends(require_roles("buyer"))):
    try:
        pid = ObjectId(productId)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid product ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    result = await db.wishlistitems.delete_one({"buyerId": ObjectId(user["id"]), "productId": pid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=error_response("Item not in wishlist.", "NOT_FOUND", path=str(request.url.path)))
    return success_response(data=None)
