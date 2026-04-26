from pathlib import Path

MD = r"""# SmartB2B — final demo checklist

## Buyer demo

1. Log in as buyer (`buyer@example.com` / `Buyer@123`).
2. Browse **Products**; use search, category, and sort.
3. Open a product; add to **Wishlist** and **RFQ cart** as needed.
4. Open **RFQ cart**; set **delivery location**, **required by**, **priority**, **notes**; create RFQ.
5. Open the RFQ (`/rfq/...` or `/rfqs/...`); review **metadata**, **quotes**, and **quote comparison** / recommended supplier.
6. **Accept** a quote (as buyer); confirm **order** is created and appears under **Orders**.
7. Open **order detail**; use **status** (seller-driven) and **escrow** demo actions; use **Print** for PO/invoice.
8. Check **Notifications** (bell + `/notifications`).

## Seller demo

1. Log in as seller (`seller@example.com` / `Seller@123`).
2. **Seller products** and **Company profile** as needed.
3. **Seller RFQs** — open an RFQ that includes your products; **submit** or **revise** quote (pricing, lead time, T&amp;C, delivery commitment).
4. After a buyer accepts, see **orders**; **update order status**; buyer sees notifications.
5. **Dashboard** for quick metrics.

## Admin demo

1. Log in as admin (`admin@smartb2b.com` / `Admin@123`).
2. **Admin panel** — users, suppliers (verify), categories, RFQs, orders, **flagged messages**, logs, analytics.
3. **Recalculate** supplier trust score for a seller when needed.
4. **Orders** (via `/orders`) for full ledger when logged in as admin.

## Re-seed / demo data

- From the `backend` directory (with MongoDB up and `DATABASE_URL` or compose env set), run:  
  `python scripts/seed.py` and/or `python scripts/generate_demo_data.py`  
- Scripts are designed to be **re-runnable**; review script output for any “skip” or idempotent behavior.

## Known limitations

- **Payments:** No real gateway; `paymentStatus` and escrow steps are a **placeholder** workflow.
- **Messaging:** REST polling only; **not** real-time websockets.
- **Trust score:** Rule-based from platform activity and profile, **not** ML.
- **Escrow** card and actions are for **demonstration** only.

## Build / smoke

- Frontend: `npm run build` and `npm run lint` from `frontend/`.
- Backend: `python -c "from app.main import app"` from `backend/`.
"""

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent
    (root / "FINAL_DEMO_CHECKLIST.md").write_text(MD, encoding="utf-8")
    print("Wrote", root / "FINAL_DEMO_CHECKLIST.md")
