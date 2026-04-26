from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
p = ROOT / "README.md"
t = p.read_text(encoding="utf-8")
if "Release highlights" in t:
    print("skip")
    raise SystemExit(0)
insert = """
### Release highlights (shipped in this tree)
- **Supplier directory** — `GET /api/suppliers` and `/suppliers` in the SPA; trust filters and profile links.
- **RFQ logistics** — Cart and API require **delivery location** and **required-by**; optional priority, notes, and RFQ validity.
- **Quotes & orders** — Compare quotes, accept (creates order with `paymentStatus`), seller/admin order status, **escrow demo** actions, **print** PO/invoice on order detail.
- **Governance** — Admin **Moderation** tab lists **flagged RFQ messages** (contact-sharing detection); activity logs and dashboards as before.

"""
t = t.replace("## Quick start (production-style)\n\n### Prerequisites", "## Quick start (production-style)\n" + insert + "\n### Prerequisites", 1)
p.write_text(t, encoding="utf-8")
print("README highlights added")
