from pathlib import Path

p = Path(__file__).resolve().parent.parent / "app/services/message_thread.py"
t = p.read_text(encoding="utf-8")
needle = """    await db.messagethreads.update_one({\"_id\": thread[\"_id\"]}, {\"$set\": {\"messages\": thread[\"messages\"]}})
    thread = await db.messagethreads.find_one({\"_id\": thread[\"_id\"]})"""
insert = """    await db.messagethreads.update_one({\"_id\": thread[\"_id\"]}, {\"$set\": {\"messages\": thread[\"messages\"]}})
    if mod_flag:
        try:
            from app.services.workflow_events import emit_event
            await emit_event(
                \"rfq\",
                oid,
                ObjectId(user[\"id\"]),
                user.get(\"role\") or \"user\",
                \"CONTACT_ATTEMPT\",
                \"Message flagged: keep communication on SmartB2B\",
                {\"reason\": mod_reason or \"\", \"auto\": True},
            )
        except Exception as e:
            print(\"workflow emit message flag:\", e)
    thread = await db.messagethreads.find_one({\"_id\": thread[\"_id\"]})"""
if "CONTACT_ATTEMPT" in t:
    print("skip")
else:
    if needle not in t:
        raise SystemExit("needle not found")
    t = t.replace(needle, insert, 1)
    p.write_text(t, encoding="utf-8")
    print("ok")
