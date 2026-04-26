# temp: run as python backend/scripts/message_thread_new.py to copy into app/services/message_thread.py
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "app/services/message_thread.py"
DEST.write_text(
    r'''"""
RFQ-scoped messaging (messagethreads collection).
Anti-disintermediation demo: flag phone/email/off-platform phrases; still persist message.
"""
from __future__ import annotations

import datetime
import re
from bson import ObjectId
from app.database import get_db
from app.schemas.common import success_response, error_response, serialize_doc, coerce_object_id, coerce_object_id_list

# Simple patterns — demonstration only, not production DLP.
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10,15}\b"
)
_OFF_PLATFORM_PHRASES = (
    "call me",
    "whatsapp",
    "whats app",
    "mail me",
    "email me",
    "contact me",
    "text me",
    "dm me",
    "reach me at",
    "my number",
)


def analyze_message_moderation(text: str) -> tuple[bool, bool, str]:
    """Returns (contains_contact_attempt, moderation_flag, moderation_reason)."""
    lower = text.lower()
    reasons: list[str] = []
    contact = False
    if _EMAIL_RE.search(text):
        contact = True
        reasons.append("email_pattern")
    if _PHONE_RE.search(text):
        contact = True
        reasons.append("phone_pattern")
    phrase_hit = any(p in lower for p in _OFF_PLATFORM_PHRASES)
    if phrase_hit:
        contact = True
        reasons.append("off_platform_phrase")
    flagged = bool(reasons)
    return contact, flagged, ", ".join(reasons) if reasons else ""


def _mask_sensitive_preview(text: str) -> str:
    t = _EMAIL_RE.sub("[redacted]", text)
    t = _PHONE_RE.sub("[redacted]", t)
    return t


async def _rfq_party_access(db, rfq: dict, user: dict) -> tuple[bool, bool, bool]:
    raw_ids = [it.get("productId") for it in rfq.get("items", []) if it.get("productId")]
    product_ids = coerce_object_id_list(raw_ids)
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    seller_ids = list({str(p["seller"]) for p in products})
    buyer_oid = coerce_object_id(rfq.get("buyerId"))
    is_buyer = buyer_oid is not None and str(buyer_oid) == user["id"]
    is_seller = user["id"] in seller_ids
    is_admin = user.get("role") == "admin"
    return is_buyer, is_seller, is_admin


def _message_to_client(m: dict, viewer_is_admin: bool) -> dict:
    out = dict(m)
    sender_id = m.get("senderId")
    if isinstance(sender_id, dict):
        out["senderId"] = sender_id
    if m.get("moderationFlag") and not viewer_is_admin:
        out["text"] = _mask_sensitive_preview(m.get("text", ""))
        out["displayMasked"] = True
    else:
        out["displayMasked"] = False
    if "_id" in out and out["_id"] is not None:
        out["id"] = str(out["_id"])
    return out


async def _hydrate_message_sender(db, mm: dict) -> None:
    if not mm.get("senderId"):
        return
    sid = mm["senderId"]
    if isinstance(sid, dict):
        return
    sid_oid = coerce_object_id(sid)
    sender = None
    if sid_oid is not None:
        sender = await db.users.find_one({"_id": sid_oid}, projection={"name": 1, "email": 1, "role": 1})
    if sender:
        mm["senderId"] = serialize_doc(sender)
        mm["senderRole"] = mm.get("senderRole") or sender.get("role") or "user"
    else:
        mm["senderId"] = {"id": str(sid_oid or sid), "name": "Unknown user", "role": "user"}
        mm["senderRole"] = mm.get("senderRole") or "user"


async def ensure_thread(db, rfq_oid: ObjectId, rfq: dict) -> dict:
    thread = await db.messagethreads.find_one({"rfqId": rfq_oid})
    if thread:
        return thread
    raw_ids = [it.get("productId") for it in rfq.get("items", []) if it.get("productId")]
    product_ids = coerce_object_id_list(raw_ids)
    products = await db.products.find({"_id": {"$in": product_ids}}, projection={"seller": 1}).to_list(None)
    buyer_oid = coerce_object_id(rfq.get("buyerId")) or rfq.get("buyerId")
    all_ids = [buyer_oid] + [p["seller"] for p in products]
    seen: set[str] = set()
    participants = []
    for x in all_ids:
        if x is None:
            continue
        s = str(x)
        if s not in seen:
            seen.add(s)
            participants.append(x)
    r = await db.messagethreads.insert_one({"rfqId": rfq_oid, "participants": participants, "messages": []})
    return await db.messagethreads.find_one({"_id": r.inserted_id})


async def get_thread_response(rfq_id: str, user: dict):
    from fastapi import HTTPException

    try:
        oid = ObjectId(rfq_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=""))

    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=""))

    is_buyer, is_seller, is_admin = await _rfq_party_access(db, rfq, user)
    if not is_buyer and not is_seller and not is_admin:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=""))

    thread = await ensure_thread(db, oid, rfq)
    messages_out = []
    for _i, m in enumerate(thread.get("messages", [])):
        mm = dict(m)
        await _hydrate_message_sender(db, mm)
        messages_out.append(_message_to_client(mm, is_admin))

    doc = serialize_doc(thread)
    if doc:
        doc["messages"] = messages_out
    return success_response(data={"thread": doc})


async def post_message_response(rfq_id: str, text: str, user: dict):
    from fastapi import HTTPException
    try:
        oid = ObjectId(rfq_id)
    except Exception:
        raise HTTPException(status_code=400, detail=error_response("Invalid RFQ ID", "VALIDATION_ERROR", path=""))

    db = get_db()
    rfq = await db.rfqs.find_one({"_id": oid})
    if not rfq:
        raise HTTPException(status_code=404, detail=error_response("RFQ not found.", "NOT_FOUND", path=""))

    is_buyer, is_seller, _is_admin = await _rfq_party_access(db, rfq, user)
    if not is_buyer and not is_seller:
        raise HTTPException(status_code=403, detail=error_response("Access denied.", "FORBIDDEN", path=""))

    contact, mod_flag, mod_reason = analyze_message_moderation(text.strip())
    thread = await ensure_thread(db, oid, rfq)
    msg = {
        "_id": ObjectId(),
        "senderId": ObjectId(user["id"]),
        "senderRole": user.get("role") or "user",
        "text": text.strip(),
        "createdAt": datetime.datetime.utcnow(),
        "isRead": False,
        "containsContactAttempt": contact,
        "moderationFlag": mod_flag,
        "moderationReason": mod_reason or None,
    }
    thread["messages"].append(msg)
    await db.messagethreads.update_one({"_id": thread["_id"]}, {"$set": {"messages": thread["messages"]}})
    if mod_flag:
        try:
            from app.services.workflow_events import emit_event
            await emit_event(
                "rfq",
                oid,
                ObjectId(user["id"]),
                user.get("role") or "user",
                "CONTACT_ATTEMPT",
                "Message flagged: keep communication on SmartB2B",
                {"reason": mod_reason or "", "auto": True},
            )
        except Exception as e:
            print("workflow emit message flag:", e)
    thread = await db.messagethreads.find_one({"_id": thread["_id"]})
    messages_out = []
    for m in thread.get("messages", []):
        mm = dict(m)
        await _hydrate_message_sender(db, mm)
        messages_out.append(_message_to_client(mm, False))
    doc = serialize_doc(thread)
    if doc:
        doc["messages"] = messages_out
    return success_response(data={"thread": doc})
''',
    encoding="utf-8",
)
print("wrote", DEST)
