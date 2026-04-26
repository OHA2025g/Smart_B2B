"""Persist admin actions to adminactionlogs (shared to avoid router import cycles)."""
import datetime
from bson import ObjectId
from app.database import get_db


async def admin_action_log(admin_id: ObjectId, action_type: str, target_id: str, details: dict | None = None):
    db = get_db()
    try:
        await db.adminactionlogs.insert_one({
            "adminId": admin_id,
            "actionType": action_type,
            "targetId": target_id,
            "details": details or {},
            "createdAt": datetime.datetime.utcnow(),
        })
    except Exception as e:
        print("AdminActionLog error:", e)
