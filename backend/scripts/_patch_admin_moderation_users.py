from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ap = ROOT / "backend/app/routers/admin.py"
t = ap.read_text(encoding="utf-8")

# get_users: buyers only
old_users = '    cursor = db.users.find({}, projection={"password": 0}).sort("createdAt", -1)\n'
new_users = '    cursor = db.users.find({"role": "buyer"}, projection={"password": 0}).sort("createdAt", -1)\n'
if old_users in t:
    t = t.replace(old_users, new_users, 1)
    print("get_users -> buyers only")

# get_suppliers: richer company profile
old_prof = '                profile = await db.companyprofiles.find_one({"user": ObjectId(str(raw_id))}, projection={"companyName": 1, "city": 1})\n'
new_prof = '                profile = await db.companyprofiles.find_one(\n                    {"user": ObjectId(str(raw_id))},\n                    projection={"companyName": 1, "city": 1, "state": 1, "country": 1, "phone": 1, "gstNumber": 1, "description": 1, "website": 1},\n                )\n'
if old_prof in t:
    t = t.replace(old_prof, new_prof, 1)
    block = """                if profile:
                    doc["companyName"] = profile.get("companyName")
                    doc["city"] = profile.get("city")
"""
    new_block = """                if profile:
                    doc["companyName"] = profile.get("companyName")
                    doc["city"] = profile.get("city")
                    doc["state"] = profile.get("state")
                    doc["country"] = profile.get("country")
                    doc["phone"] = profile.get("phone")
                    doc["gstNumber"] = profile.get("gstNumber")
                    doc["description"] = profile.get("description")
                    doc["website"] = profile.get("website")
"""
    if block in t:
        t = t.replace(block, new_block, 1)
    print("get_suppliers -> GST + profile fields")

# Add GET /moderation/messages before flagged-messages or after
marker = '@router.get("/flagged-messages")'
if '/moderation/messages' not in t:
    route = '''

@router.get("/moderation/messages")
async def admin_moderation_messages(request: Request, user: dict = Depends(get_current_user)):
    """Flagged / moderated RFQ chat messages with raw + display text for review."""
    db = get_db()
    out = []
    async for th in db.messagethreads.find({}):
        rfq_id = str(th.get("rfqId", ""))
        for m in th.get("messages", []) or []:
            if not (m.get("moderationFlag") or m.get("containsContactAttempt") or m.get("moderationScore", 0) >= 45):
                continue
            mid = str(m.get("_id", ""))
            sid = m.get("senderId")
            sender = None
            if isinstance(sid, ObjectId):
                sender = await db.users.find_one({"_id": sid}, projection={"name": 1, "email": 1, "role": 1})
            row = {
                "messageId": mid,
                "rfqId": rfq_id,
                "sender": serialize_doc(sender) if sender else None,
                "senderRole": m.get("senderRole"),
                "rawMessage": m.get("rawMessage") or m.get("text"),
                "displayMessage": m.get("displayMessage") or m.get("text"),
                "moderationScore": m.get("moderationScore", 0),
                "moderationReasons": m.get("moderationReasons") or ([m.get("moderationReason")] if m.get("moderationReason") else []),
                "moderationStatus": m.get("moderationStatus"),
                "detectedTypes": m.get("detectedTypes", []),
                "createdAt": m.get("createdAt"),
            }
            out.append(row)
    out.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return success_response(data={"messages": out[:500], "count": len(out[:500])})


'''
    idx = t.find(marker)
    if idx >= 0:
        t = t[:idx] + route + t[idx:]
        print("added /moderation/messages")
    else:
        print("marker not found for moderation route")

ap.write_text(t, encoding="utf-8")
print("admin.py done")
