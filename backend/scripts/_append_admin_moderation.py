from pathlib import Path

APPEND = r'''

@router.get("/flagged-messages")
async def admin_flagged_messages(request: Request, user: dict = Depends(get_current_user)):
    """Messages with moderation flag (off-platform / contact attempt)."""
    db = get_db()
    out = []
    async for t in db.messagethreads.find({}):
        rfq_id = t.get("rfqId")
        for m in t.get("messages", []):
            if m.get("moderationFlag") or m.get("containsContactAttempt"):
                out.append(
                    {
                        "threadId": str(t.get("_id")),
                        "rfqId": str(rfq_id) if rfq_id else None,
                        "messageId": str(m.get("_id") or m.get("id", "")),
                        "senderId": str(m.get("senderId", "")) if m.get("senderId") is not None else None,
                        "senderRole": m.get("senderRole"),
                        "text": m.get("text"),
                        "createdAt": m.get("createdAt").isoformat() if getattr(m.get("createdAt"), "isoformat", None) else None,
                        "moderationFlag": bool(m.get("moderationFlag")),
                        "moderationReason": m.get("moderationReason"),
                    }
                )
    out.sort(key=lambda x: x.get("createdAt") or "", reverse=True)
    return success_response(data={"flagged": out[:500], "count": len(out[:500])})
'''

p = Path(__file__).resolve().parent.parent / "app/routers/admin.py"
text = p.read_text(encoding="utf-8")
if "admin_flagged_messages" in text:
    print("skip - already have route")
else:
    # add import if get_current_user is used - already there
    if "from app.dependencies" not in text and "get_current_user" in APPEND:
        pass
    p.write_text(text.rstrip() + "\n" + APPEND, encoding="utf-8")
    print("appended flagged messages")
