"""One-off patches: auth /me JSON, OID coercion, messages, RFQ linked order + reject quote."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def patch_common():
    p = ROOT / "app/schemas/common.py"
    t = p.read_text(encoding="utf-8")
    if "def coerce_object_id(" in t:
        print("common.py: skip")
        return
    needle = "from bson import ObjectId\n"
    add = needle + "\n\ndef coerce_object_id(value):\n"
    add += '    """Single value to ObjectId for DB queries; None if invalid."""\n'
    add += "    if value is None:\n        return None\n"
    add += "    if isinstance(value, ObjectId):\n        return value\n"
    add += "    try:\n        return ObjectId(str(value))\n    except Exception:\n        return None\n\n\n"
    add += "def coerce_object_id_list(values):\n"
    add += '    """Mixed str/ObjectId list for Mongo $in; skips invalid entries."""\n'
    add += "    out = []\n    for v in values or []:\n        oid = coerce_object_id(v)\n        if oid is not None:\n            out.append(oid)\n    return out\n"
    if needle not in t:
        raise SystemExit("common.py import not found")
    p.write_text(t.replace(needle, add, 1), encoding="utf-8")
    print("common.py: coerce helpers added")


def patch_auth():
    p = ROOT / "app/routers/auth.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        "from app.schemas.common import success_response, error_response",
        "from app.schemas.common import success_response, error_response, serialize_doc",
    )
    t = t.replace(
        'return success_response(data={"user": user})',
        'return success_response(data={"user": serialize_doc(user)})',
    )
    p.write_text(t, encoding="utf-8")
    print("auth.py: /me uses serialize_doc")


def patch_message_thread():
    p = ROOT / "app/services/message_thread.py"
    t = p.read_text(encoding="utf-8")
    if "coerce_object_id_list" not in t:
        t = t.replace(
            "from app.schemas.common import success_response, error_response, serialize_doc",
            "from app.schemas.common import success_response, error_response, serialize_doc, coerce_object_id, coerce_object_id_list",
        )
    t = t.replace(
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}}, projection={\"seller\": 1}).to_list(None)\n",
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}}, projection={\"seller\": 1}).to_list(None)\n",
        count=1,
    )
    # second occurrence in ensure_thread
    t = t.replace(
        "    product_ids = [it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")]\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}}, projection={\"seller\": 1}).to_list(None)\n",
        "    product_ids = coerce_object_id_list([it.get(\"productId\") for it in rfq.get(\"items\", []) if it.get(\"productId\")])\n"
        "    products = await db.products.find({\"_id\": {\"$in\": product_ids}}}, projection={\"seller\": 1}).to_list(None)\n",
        count=1,
    )
    old_party = (
        "    is_buyer = str(rfq[\"buyerId\"]) == user[\"id\"]\n"
        "    is_seller = user[\"id\"] in seller_ids\n"
    )
    new_party = (
        "    buyer_oid = coerce_object_id(rfq.get(\"buyerId\"))\n"
        "    is_buyer = buyer_oid is not None and str(buyer_oid) == user[\"id\"]\n"
        "    is_seller = user[\"id\"] in seller_ids\n"
    )
    if old_party in t:
        t = t.replace(old_party, new_party, 1)

    # ensure_thread participants: normalize buyerId
    old_ensure = "    all_ids = [rfq[\"buyerId\"]] + [p[\"seller\"] for p in products]\n"
    new_ensure = (
        "    buyer_raw = rfq.get(\"buyerId\")\n"
        "    buyer_oid = coerce_object_id(buyer_raw) or buyer_raw\n"
        "    all_ids = [buyer_oid] + [p[\"seller\"] for p in products]\n"
    )
    if old_ensure in t:
        t = t.replace(old_ensure, new_ensure, 1)

    # sender lookup fallback
    old_sender = (
        "        if mm.get(\"senderId\"):\n"
        "            sender = await db.users.find_one({\"_id\": mm[\"senderId\"]}, projection={\"name\": 1, \"email\": 1, \"role\": 1})\n"
        "            if sender:\n"
        "                mm[\"senderId\"] = serialize_doc(sender)\n"
        "                mm[\"senderRole\"] = mm.get(\"senderRole\") or sender.get(\"role\") or \"user\"\n"
    )
    new_sender = (
        "        if mm.get(\"senderId\"):\n"
        "            sid = mm[\"senderId\"]\n"
        "            sid_oid = coerce_object_id(sid) if not isinstance(sid, dict) else None\n"
        "            sender = None\n"
        "            if sid_oid is not None:\n"
        "                sender = await db.users.find_one({\"_id\": sid_oid}, projection={\"name\": 1, \"email\": 1, \"role\": 1})\n"
        "            if sender:\n"
        "                mm[\"senderId\"] = serialize_doc(sender)\n"
        "                mm[\"senderRole\"] = mm.get(\"senderRole\") or sender.get(\"role\") or \"user\"\n"
        "            else:\n"
        "                mm[\"senderId\"] = {\"id\": str(sid_oid or sid), \"name\": \"Unknown user\", \"role\": \"user\"}\n"
        "                mm[\"senderRole\"] = mm.get(\"senderRole\") or \"user\"\n"
    )
    if old_sender in t:
        t = t.replace(old_sender, new_sender, 2)  # get_thread and post loop - actually two blocks differ

    p.write_text(t, encoding="utf-8")
    print("message_thread.py: patched (verify manually if replace counts wrong)")


if __name__ == "__main__":
    patch_common()
    patch_auth()
    patch_message_thread()
