"""
Print contact moderation outcomes for acceptance-style cases.
Run from repo root:  python backend/scripts/test_contact_moderation.py
Or from backend:    python scripts/test_contact_moderation.py
"""
from __future__ import annotations

import os
import sys

# Allow imports when cwd is backend/ or repo root
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.services.contact_moderation import analyze_contact  # noqa: E402


def tier(status: str) -> str:
    if status == "blocked":
        return "BLOCK"
    if status == "confirm_required":
        return "CONFIRM"
    if status == "warn":
        return "WARN"
    return "CLEAN"


def main() -> None:
    should_block = [
        "call me on 9876543210",
        "9 8 7 6 5 4 3 2 1 0",
        "91 98765 43210",
        "91\n25\n99\n34\n56",
        "mail me at test@example.com",
        "sales at acme dot com",
        "dr\n45\n67\n@\ngm\n.com",
        "whatsapp me",
        "https://t.me/brandchannel",
        "see wa.me/919876543210 for updates",
        "mailto:sales@acme.com",
        "ring tel:+91-98765-43210",
    ]
    should_warn = [
        "our domain is example dot com",
        "reach me outside platform",
        "contact me",
    ]
    should_allow = [
        "Order quantity is 1000 units",
        "GSTIN is 27ABCDE1234F1Z5",
        "HSN code is 847130",
        "Delivery required in 10 days",
        "Invoice amount is 987654",
    ]

    print("=" * 72)
    print("SHOULD BLOCK (expect BLOCK)")
    print("=" * 72)
    for s in should_block:
        r = analyze_contact(s, prior_thread_flags=0)
        print(f"{tier(r['status']):8} score={r['score']:<4} types={r.get('detected_types')} | {s[:56]!r}")

    print()
    print("=" * 72)
    print("SHOULD WARN / CONFIRM (expect WARN or CONFIRM)")
    print("=" * 72)
    for s in should_warn:
        r = analyze_contact(s, prior_thread_flags=0)
        print(f"{tier(r['status']):8} score={r['score']:<4} types={r.get('detected_types')} | {s[:56]!r}")

    print()
    print("=" * 72)
    print("SHOULD ALLOW (expect CLEAN)")
    print("=" * 72)
    for s in should_allow:
        r = analyze_contact(s, prior_thread_flags=0)
        print(f"{tier(r['status']):8} score={r['score']:<4} types={r.get('detected_types')} | {s[:56]!r}")

    print()
    print("=" * 72)
    print("THREAD: split number across same sender (expect BLOCK for split burst)")
    print("=" * 72)
    thread_cases: list[tuple[str, list[str] | None, str]] = [
        ("0", [str(d) for d in "987654321"], "9..0 split across 10 lines -> valid IN mobile -> BLOCK"),
        ("35", ["72", "234", "34"], "4 short digit lines, 9 digits total -> burst -> BLOCK"),
    ]
    for new_text, recent, note in thread_cases:
        r = analyze_contact(new_text, same_sender_recent=recent or None)
        print(
            f"{tier(r['status']):8} score={r['score']:<4} | {note}\n        reasons={r.get('reasons', [])[:3]!r}\n        new={new_text!r} prior={recent!r}"
        )


if __name__ == "__main__":
    main()
