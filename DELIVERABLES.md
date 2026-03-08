# SmartB2B – Mid-term upgrade deliverables

## 1. Files changed

### Backend (Python/FastAPI)

| File | Change |
|------|--------|
| `app/schemas/common.py` | Serialize docs with both `id` and `_id` for frontend compatibility |
| `app/schemas/order.py` | Added `processing` to order status enum |
| `app/config.py` | No change |
| `app/database.py` | No change |
| `app/dependencies.py` | No change |
| `app/main.py` | Registered `suppliers` router; mounted RFQ router at `/api/rfqs` as well |
| `app/routers/products.py` | Enrich product list/detail with seller `trustScore`, `trustLevel`, `isVerifiedSupplier` |
| `app/routers/cart.py` | Added `PUT /{productId}` to update cart item quantity/notes |
| `app/routers/rfq.py` | Added `POST /create-from-cart`; GET quotes returns `quoteScore` and seller trust; accept-quote sets `quoteId` on order |
| `app/routers/admin.py` | Added `GET /dashboard`, `PUT /users/{id}/unban`, `POST /suppliers/{id}/verify`, `POST /suppliers/{id}/recalculate-score`; verify triggers score recalc |
| **New** `app/services/__init__.py` | Services package |
| **New** `app/services/supplier_score.py` | Trust score formula, quote score formula, recalculate, get_or_create |
| **New** `app/routers/suppliers.py` | `GET /api/suppliers/{seller_id}/score` |
| `scripts/seed.py` | Wishlist item, cart item, `supplier_scores` for sellers, `quoteId` on order |

### Frontend (React/Vite)

| File | Change |
|------|--------|
| `src/api/client.js` | `rfqApi.createFromCart`, `cartApi.update`, `adminApi.dashboard`, `unbanUser`, `verifySupplierPost`, `recalculateScore`, `suppliersApi.getScore` |
| `src/pages/Products.jsx` | Verified Supplier badge and Trust % only when `seller` has data |
| `src/pages/Cart.jsx` | Navigate to RFQ using `res.data?.rfq?._id \|\| res.data?.rfq?.id` |
| `src/pages/RFQDetail.jsx` | Stepper (Created → Quoted → Accepted → Order generated); quote table with Trust score, Quote score, Verified badge; quotes sorted by quoteScore |
| `src/pages/AdminPanel.jsx` | Dashboard tab with 6 stat cards; Supplier verification tab (verify, recalculate score); unban via `unbanUser`; load dashboard in `load()` |
| `src/pages/Dashboard.jsx` | Buyer: RFQ/cart/wishlist counts and links; Seller: assigned RFQs and orders counts and links; Admin: dashboard stats (verified suppliers, RFQs, orders) |
| `src/pages/SellerOrders.jsx` | Added “Processing” status and button between Confirm and Mark Shipped |

---

## 2. New backend routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/suppliers/{seller_id}/score` | Supplier trust score (public) |
| POST | `/api/rfq/create-from-cart` | Create RFQ from current cart (buyer) |
| PUT | `/api/cart/{productId}` | Update cart item quantity/notes (buyer) |
| GET | `/api/admin/dashboard` | Dashboard stats (admin) |
| PUT | `/api/admin/users/{id}/unban` | Unban user (admin) |
| POST | `/api/admin/suppliers/{seller_id}/verify` | Verify supplier (admin) |
| POST | `/api/admin/suppliers/{seller_id}/recalculate-score` | Recalculate trust score (admin) |

Existing routes unchanged; RFQ also mounted at `/api/rfqs` (e.g. `GET /api/rfqs/me`, `POST /api/rfqs/create-from-cart`).

---

## 3. New / updated frontend pages

| Route | Page | Updates |
|-------|------|--------|
| `/products` | Products | Verified badge and Trust % on cards (from seller) |
| `/wishlist` | Wishlist | Existing; no structural change |
| `/cart` | Cart | Existing; create RFQ navigates correctly |
| `/rfq` | RFQList | Existing |
| `/rfq/:id` | RFQDetail | Stepper; quote comparison table with Trust score, Quote score, Verified; Accept quote |
| `/seller/rfqs` | SellerRFQs | Existing |
| `/seller/orders` | SellerOrders | Processing status and button |
| `/admin/panel` | AdminPanel | Dashboard tab (6 cards); Supplier verification tab (verify + recalculate); unban |
| `/dashboard` | Dashboard | Buyer: RFQ/cart/wishlist stats + links; Seller: RFQs/orders stats + links; Admin: dashboard stats |

---

## 4. Seed demo credentials

After running `python -m scripts.seed` from `backend/`:

| Role   | Email                | Password   |
|--------|----------------------|------------|
| Admin  | admin@smartb2b.com   | Admin@123  |
| Seller | seller@example.com   | Seller@123 |
| Seller | seller2@example.com  | Seller2@123|
| Buyer  | buyer@example.com    | Buyer@123  |
| Buyer  | buyer2@example.com   | Buyer2@123 |

Seed data includes: categories, 2 sellers with company profiles, 5 products, 1 wishlist item (buyer1), 1 cart item (buyer2), supplier_scores for both sellers, one RFQ with one accepted quote and one order, and a message thread.

---

## 5. Demo flow for mid-term presentation

### Buyer flow (≈3 min)

1. **Login** as `buyer@example.com` / `Buyer@123`.
2. **Dashboard** – Show “My RFQs”, “Cart items”, “Wishlist” and quick links.
3. **Products** – Filter by category; show **Verified Supplier** and **Trust %** on cards; add one product to wishlist (heart), one to **RFQ Cart**.
4. **Wishlist** – Open `/wishlist`, remove or “Add to cart”.
5. **Cart** – Open `/cart`, change quantity/notes, click **Request Quotation (RFQ)** → redirect to RFQ detail.
6. **RFQ detail** – Show **stepper** (Created → Quoted → Accepted → Order generated); **quote comparison** table (seller, quoted price, delivery days, trust score, quote score); click **Accept quote** → order created.
7. Optional: **My RFQs** – List of RFQs with status badges.

### Seller flow (≈2 min)

1. **Login** as `seller@example.com` / `Seller@123`.
2. **Dashboard** – Show “Assigned RFQs”, “My orders” and links.
3. **Assigned RFQs** – Open `/seller/rfqs`, open “Submit Quote” for an RFQ, submit (unit price, qty, delivery days, message).
4. **My orders** – Open `/seller/orders`, show order and status; use **Confirm** → **Processing** → **Mark Shipped** → **Mark Delivered**.

### Admin flow (≈2 min)

1. **Login** as `admin@smartb2b.com` / `Admin@123`.
2. **Dashboard** – Open **Admin Panel** → **Dashboard** tab: total users, verified suppliers, pending suppliers, total RFQs, total quotes, total orders.
3. **Users** – Ban/unban a user.
4. **Supplier verification** – Verify or unverify a seller; **Recalculate score** for a seller.
5. **Categories** – Add/edit/delete categories.
6. **RFQs / Orders** – Browse all RFQs and orders.
7. **Activity logs** – Show admin action log.

### Trust & quote score (talking points)

- **Trust score**: 30% profile + 20% response rate + 20% product strength + 15% buyer rating + 15% verified. Levels: Highly Trusted (85–100), Trusted (70–84), Moderate (50–69), Low (&lt;50).
- **Quote score** (for comparison): 50% price competitiveness + 25% delivery speed + 25% supplier trust. Shown in RFQ quote table; quotes sorted by quote score.

---

## 6. How to run

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m scripts.seed
python run.py
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and use the credentials above.
