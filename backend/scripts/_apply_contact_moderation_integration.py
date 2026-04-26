"""Apply message schema, router, message_thread, admin, test script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# --- message.py ---
mp = ROOT / "backend/app/schemas/message.py"
t = mp.read_text(encoding="utf-8")
if "confirm_send" not in t:
    t = """from typing import Optional

from pydantic import BaseModel, Field


class MessagePost(BaseModel):
    text: str = Field(..., min_length=1)
    confirm_send: Optional[bool] = False
"""
    mp.write_text(t, encoding="utf-8")
    print("message.py")

# --- messages.py ---
mr = ROOT / "backend/app/routers/messages.py"
t = mr.read_text(encoding="utf-8")
old = """@router.post("/{rfqId}", status_code=201)
async def post_message(rfqId: str, body: MessagePost, user: dict = Depends(get_current_user)):
    return await message_thread.post_message_response(rfqId, body.text, user)
"""
new = """@router.post("/{rfqId}", status_code=201)
async def post_message(rfqId: str, body: MessagePost, user: dict = Depends(get_current_user)):
    return await message_thread.post_message_response(
        rfqId,
        user,
        body.text,
        confirm_send=bool(body.confirm_send),
    )
"""
if old in t:
    mr.write_text(t.replace(old, new), encoding="utf-8")
    print("messages.py")

# --- message_thread.py (replace post + helpers) ---
mt = ROOT / "backend/app/services/message_thread.py"
full = r'''"""
RFQ-scoped messaging (messagethreads collection).
Contact moderation via app.services.contact_moderation (layered detection).
"""
from __future__ import annotations

import datetime
import re
from bson import ObjectId
from fastapi import HTTPException
from app.database import get_db
from app.schemas.common import success_response, error_response, serialize_doc, coerce_object_id, coerce_object_id_list
from app.services.contact_moderation import analyze_contact, redact_contact_content


def _mask_sensitive_preview(text: str) -> str:
    t = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[redacted]", text)
    t = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10,15}\b", "[redacted]", t)
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
    display = m.get("displayMessage") or m.get("text", "")
    if m.get("moderationFlag") and not viewer_is_admin:
        out["text"] = display if m.get("redactionApplied") else _mask_sensitive_preview(display)
        out["displayMasked"] = True
    else:
        out["text"] = display
        out["displayMasked"] = False
    out["displayMessage"] = display
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


def _prior_flags_in_thread(thread: dict, user_id: str) -> int:
    n = 0
    for m in thread.get("messages", []) or []:
        if m.get("moderationFlag") and str(m.get("senderId")) == user_id:
            n += 1
    return n


async def get_thread_response(rfq_id: str, user: dict):
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


async def post_message_response(rfq_id: str, user: dict, text: str, *, confirm_send: bool = False):
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

    thread = await ensure_thread(db, oid, rfq)
    prior = _prior_flags_in_thread(thread, user["id"])
    raw_text = (text or "").strip()
    mod = analyze_contact(raw_text, prior_thread_flags=prior)

    if mod["status"] == "blocked":
        try:
            from app.services.admin_audit import admin_action_log

            adm = await db.users.find_one({"role": "admin"}, projection={"_id": 1})
            if adm:
                await admin_action_log(
                    adm["_id"],
                    "CONTACT_SHARING_ATTEMPT",
                    rfq_id,
                    {"actorId": user["id"], "score": mod["score"], "reasons": mod["reasons"][:12], "blocked": True},
                )
        except Exception:
            pass
        try:
            from app.services.workflow_events import emit_event
            await emit_event(
                "rfq",
                oid,
                ObjectId(user["id"]),
                user.get("role") or "user",
                "CONTACT_SHARING_BLOCKED",
                "Blocked message (contact sharing)",
                {"score": mod["score"], "types": mod.get("detected_types", [])},
            )
        except Exception:
            pass
        try:
            async for adm in db.users.find({"role": "admin"}, projection={"_id": 1}):
                from app.services.notifications import create_notification
                await create_notification(
                    adm["_id"],
                    "Moderation: blocked attempt",
                    f"RFQ {rfq_id}: contact-sharing blocked (score {mod['score']}).",
                    "moderation_blocked",
                    "rfq",
                    str(oid),
                )
        except Exception:
            pass
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "code": "CONTACT_SHARING_BLOCKED",
                "message": "Direct contact sharing is restricted. Please continue communication inside SmartB2B.",
                "moderation": {k: mod[k] for k in ("status", "score", "reasons", "detected_types", "detected_spans", "normalized_preview", "display_message") if k in mod},
            },
        )

    if mod["status"] == "confirm_required" and not confirm_send:
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "code": "MODERATION_CONFIRM_REQUIRED",
                "message": "This message may contain contact details. Please edit it or confirm sending for admin review.",
                "moderation": {k: mod[k] for k in ("status", "score", "reasons", "detected_types", "detected_spans", "normalized_preview", "display_message") if k in mod},
            },
        )

    display = raw_text
    mod_flag = mod["status"] in ("warn", "confirm_required")
    redaction = mod["status"] in ("warn", "confirm_required")
    if mod_flag:
        display = redact_contact_content(raw_text, mod)

    msg = {
        "_id": ObjectId(),
        "senderId": ObjectId(user["id"]),
        "senderRole": user.get("role") or "user",
        "text": display,
        "rawMessage": raw_text,
        "displayMessage": display,
        "createdAt": datetime.datetime.utcnow(),
        "isRead": False,
        "containsContactAttempt": mod["score"] >= 45,
        "moderationFlag": mod_flag,
        "moderationReason": ", ".join(mod.get("reasons", [])[:12]) or None,
        "moderationStatus": mod["status"],
        "moderationScore": mod["score"],
        "moderationReasons": mod.get("reasons", []),
        "detectedTypes": mod.get("detected_types", []),
        "redactionApplied": redaction,
    }
    thread["messages"].append(msg)
    await db.messagethreads.update_one({"_id": thread["_id"]}, {"$set": {"messages": thread["messages"]}})
    try:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$inc": {"contactModerationCount": 1}})
    except Exception:
        pass

    if mod_flag:
        try:
            from app.services.workflow_events import emit_event
            await emit_event(
                "rfq",
                oid,
                ObjectId(user["id"]),
                user.get("role") or "user",
                "CONTACT_ATTEMPT",
                "Message flagged for moderation review",
                {"score": mod["score"], "reasons": mod.get("reasons", [])[:8]},
            )
        except Exception as e:
            print("workflow emit message flag:", e)
        try:
            async for adm in db.users.find({"role": "admin"}, projection={"_id": 1}):
                from app.services.notifications import create_notification
                await create_notification(
                    adm["_id"],
                    "RFQ message flagged",
                    f"RFQ {rfq_id}: message may contain contact details (score {mod['score']}).",
                    "moderation_flag",
                    "rfq",
                    str(oid),
                )
        except Exception:
            pass
        try:
            from app.services.admin_audit import admin_action_log

            adm2 = await db.users.find_one({"role": "admin"}, projection={"_id": 1})
            if adm2:
                await admin_action_log(
                    adm2["_id"],
                    "CONTACT_SHARING_ATTEMPT",
                    rfq_id,
                    {"actorId": user["id"], "score": mod["score"], "saved": True},
                )
        except Exception:
            pass

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
'''

mt.write_text(full, encoding="utf-8")
print("message_thread.py rewritten")

# --- rfq.py alias for messages - if it calls post_message_response ---
rfq_router = ROOT / "backend/app/routers/rfq.py"
rt = rfq_router.read_text(encoding="utf-8")
old_rf = "    return await message_thread.post_message_response(id, body.text, user)\n"
new_rf = "    return await message_thread.post_message_response(id, user, body.text, confirm_send=bool(getattr(body, \"confirm_send\", False) or body.model_dump().get(\"confirm_send\")))\n"
# MessagePost may not have confirm on rfq alias - use body
if "post_message_response(id, body.text, user)" in rt:
    rt = rt.replace(
        "return await message_thread.post_message_response(id, body.text, user)",
        "return await message_thread.post_message_response(id, user, body.text, confirm_send=bool(body.confirm_send))",
    )
    rfq_router.write_text(rt, encoding="utf-8")
    print("rfq.py messages alias")

print("done")
