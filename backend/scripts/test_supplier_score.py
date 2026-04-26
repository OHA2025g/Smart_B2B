"""
Exercise supplier trust score: one seller, verify / unverify, print components.
Run:  cd backend && python scripts/test_supplier_score.py
"""
from __future__ import annotations

import asyncio
import os
import sys

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("MONGODB_URI", os.environ.get("MONGODB_URI", "mongodb://localhost:27017/smartb2b"))

from bson import ObjectId  # noqa: E402

from app.database import get_db  # noqa: E402
from app.services.supplier_score import (  # noqa: E402
    get_supplier_score_for_response,
    recalculate_supplier_score,
)


def _print_sc(label: str, d: dict | None) -> None:
    if not d:
        print(f"  {label}: (no score document)")
        return
    print(f"  {label} total_score={d.get('total_score')} level={d.get('trust_level')}")
    print(
        f"    profile={d.get('profile_completeness')!s}  response={d.get('response_rate')!s}  "
        f"product={d.get('product_strength')!s}  buyer_rating={d.get('buyer_rating')!s}  "
        f"verified_component={d.get('verified_status')!s}"
    )


async def main() -> None:
    db = get_db()
    seller = await db.users.find_one({"role": "seller"}, sort=[("createdAt", -1)])
    if not seller:
        print("No seller in database. Seed or generate demo data first.")
        return
    sid: ObjectId = seller["_id"]
    print("Using seller", sid, seller.get("email"))
    v0 = bool(seller.get("isVerifiedSupplier"))
    print("\n1) State before (DB verified =", v0, ")")
    s0 = await get_supplier_score_for_response(sid)
    _print_sc("get_supplier_score_for_response", s0)
    t0 = (s0 or {}).get("total_score", 0)

    print("\n2) Force verified = True, recalculate")
    await db.users.update_one({"_id": sid}, {"$set": {"isVerifiedSupplier": True}})
    await recalculate_supplier_score(sid)
    s1 = await get_supplier_score_for_response(sid)
    _print_sc("after verify", s1)
    t1 = (s1 or {}).get("total_score", 0)

    print("\n3) Set verified = False, recalculate")
    await db.users.update_one({"_id": sid}, {"$set": {"isVerifiedSupplier": False}})
    await recalculate_supplier_score(sid)
    s2 = await get_supplier_score_for_response(sid)
    _print_sc("after unverify", s2)
    t2 = (s2 or {}).get("total_score", 0)

    print("\n4) Restore original verified flag and recalculate")
    await db.users.update_one({"_id": sid}, {"$set": {"isVerifiedSupplier": v0}})
    await recalculate_supplier_score(sid)

    print("\nSummary")
    print(f"  Score delta (verify - before): {t1} - {t0} = {t1 - t0}")
    print(f"  Score delta (unverify - verify): {t2} - {t1} = {t2 - t1}")
    if t1 == 100 or t2 == 100:
        print("  Note: 100 is only possible if all components align at 100 (not typical).")
    else:
        print("  OK: no automatic 100 from verify/unverify alone (check components above).")


if __name__ == "__main__":
    asyncio.run(main())
