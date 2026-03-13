"""
Workflow / audit events for RFQs and Orders.
Stored in workflow_events collection for timeline UI.
"""
import datetime
from bson import ObjectId
from app.database import get_db


async def emit_event(
    entity_type: str,
    entity_id: ObjectId,
    actor_id: ObjectId,
    actor_role: str,
    event_type: str,
    event_label: str,
    metadata: dict | None = None,
):
    db = get_db()
    await db.workflow_events.insert_one({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "event_type": event_type,
        "event_label": event_label,
        "metadata": metadata or {},
        "created_at": datetime.datetime.utcnow(),
    })
