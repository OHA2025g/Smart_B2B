from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import success_response, error_response, serialize_doc

router = APIRouter()


@router.get("/me")
async def get_my_notifications(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    cursor = db.notifications.find({"user_id": uid}).sort("created_at", -1).limit(100)
    items = [serialize_doc(n) async for n in cursor]
    unread_count = await db.notifications.count_documents({"user_id": uid, "is_read": False})
    return success_response(data={"notifications": items, "unreadCount": unread_count})


@router.put("/{id}/read")
async def mark_read(id: str, request: Request, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid notification ID", "VALIDATION_ERROR", path=str(request.url.path)))
    db = get_db()
    n = await db.notifications.find_one({"_id": oid})
    if not n:
        raise HTTPException(status_code=404, detail=error_response("Notification not found.", "NOT_FOUND", path=str(request.url.path)))
    if str(n["user_id"]) != user["id"]:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=str(request.url.path)))
    await db.notifications.update_one({"_id": oid}, {"$set": {"is_read": True}})
    return success_response(data={"notification": serialize_doc(await db.notifications.find_one({"_id": oid}))})


@router.put("/read-all")
async def mark_all_read(request: Request, user: dict = Depends(get_current_user)):
    db = get_db()
    uid = ObjectId(user["id"])
    await db.notifications.update_many({"user_id": uid, "is_read": False}, {"$set": {"is_read": True}})
    return success_response(message="All notifications marked as read.")
