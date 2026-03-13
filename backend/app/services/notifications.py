"""
Create in-app notifications. Stored in notifications collection.
"""
import datetime
from bson import ObjectId
from app.database import get_db


async def create_notification(
    user_id: ObjectId,
    title: str,
    message: str,
    type: str,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
):
    db = get_db()
    await db.notifications.insert_one({
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type,
        "related_entity_type": related_entity_type or "",
        "related_entity_id": related_entity_id or "",
        "is_read": False,
        "created_at": datetime.datetime.utcnow(),
    })
