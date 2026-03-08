from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.company import CompanyBody

router = APIRouter()


@router.post("")
async def upsert(request: Request, body: CompanyBody, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    payload = body.model_dump(exclude_unset=True)
    payload["user"] = uid
    result = await db.companyprofiles.update_one(
        {"user": uid},
        {"$set": payload},
        upsert=True,
    )
    if result.upserted_id:
        profile = await db.companyprofiles.find_one({"_id": result.upserted_id})
    else:
        profile = await db.companyprofiles.find_one({"user": uid})
    return success_response(data={"company": serialize_doc(profile)})


@router.get("/me")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    profile = await db.companyprofiles.find_one({"user": ObjectId(user["id"])})
    if not profile:
        raise HTTPException(status_code=404, detail=error_response("Company profile not found.", "NOT_FOUND", path=str(request.url.path)))
    return success_response(data={"company": serialize_doc(profile)})
