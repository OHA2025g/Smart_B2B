from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.schemas.common import success_response, error_response
from app.services.supplier_score import get_supplier_score_for_response, recalculate_supplier_score

router = APIRouter()


@router.get("/{seller_id}/score")
async def get_supplier_score(seller_id: str, request: Request):
    try:
        oid = ObjectId(seller_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid seller ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    user = await db.users.find_one({"_id": oid}, projection={"role": 1})
    if not user or user.get("role") != "seller":
        raise HTTPException(status_code=404, detail=error_response("Supplier not found.", "NOT_FOUND", path=str(request.url.path)))
    score = await get_supplier_score_for_response(oid)
    if not score:
        raise HTTPException(status_code=404, detail=error_response("Score not found.", "NOT_FOUND", path=str(request.url.path)))
    return success_response(data={"score": score})
