import re
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.category import CategoryCreate, CategoryUpdate

router = APIRouter()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


@router.get("")
async def list_categories():
    db = get_db()
    cursor = db.categories.find({"isActive": True}).sort("name", 1)
    categories = [serialize_doc(c) async for c in cursor]
    return success_response(data={"categories": categories})


@router.post("", status_code=201)
async def create(request: Request, body: CategoryCreate, user: dict = Depends(require_roles("admin"))):
    db = get_db()
    payload = body.model_dump(exclude_unset=True)
    if not payload.get("slug") and payload.get("name"):
        payload["slug"] = _slug(payload["name"])
    r = await db.categories.insert_one(payload)
    cat = await db.categories.find_one({"_id": r.inserted_id})
    return success_response(data={"category": serialize_doc(cat)})


@router.put("/{id}")
async def update(id: str, request: Request, body: CategoryUpdate, user: dict = Depends(require_roles("admin"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid category ID", "VALIDATION_ERROR", path=request.url.path))
    db = get_db()
    payload = body.model_dump(exclude_unset=True)
    result = await db.categories.update_one({"_id": oid}, {"$set": payload})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=error_response("Category not found.", "NOT_FOUND", path=request.url.path))
    cat = await db.categories.find_one({"_id": oid})
    return success_response(data={"category": serialize_doc(cat)})


@router.delete("/{id}")
async def remove(id: str, request: Request, user: dict = Depends(require_roles("admin"))):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid category ID", "VALIDATION_ERROR", path=request.url.path))
    db = get_db()
    result = await db.categories.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=error_response("Category not found.", "NOT_FOUND", path=request.url.path))
    return success_response(data=None, message="Category deleted.")
