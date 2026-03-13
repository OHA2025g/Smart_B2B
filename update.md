# SmartB2B – Project Update & Reference

**Tagline:** *Smarter B2B. Real Deals.*

This document summarizes everything done in the project so far: structure, tech stack, features, theme, API, scripts, and how to run it.

---

## 1. Project overview

SmartB2B is an intelligent B2B marketplace where:

- **Buyers** browse products, add to wishlist/RFQ cart, create RFQs, compare seller quotes (with trust & quote scores), and accept quotes to create orders.
- **Sellers** list products, receive RFQs, submit quotes, and manage orders (confirm → processing → shipped → delivered).
- **Admins** manage users (ban/unban), verify suppliers, recalculate trust scores, manage categories, and view RFQs, orders, and activity logs.

Trust is built in: every seller has a **trust score** and **trust level**; products and quotes show **Verified** badges and scores so buyers can compare confidently.

---

## 2. Tech stack

| Layer      | Technology |
|-----------|------------|
| Backend   | Python 3.11+, FastAPI, MongoDB (Motor async driver), JWT (python-jose), Passlib (bcrypt) |
| Frontend  | React 18, Vite 5, React Router 6, Axios, TailwindCSS 3, Framer Motion, Lucide React |
| Database  | MongoDB (collections listed below) |
| Dev/Deploy| ESLint, Prettier; optional Docker Compose for Mongo + backend + frontend |

---

## 3. Repository structure

```
SmartB2B/
├── backend/
│   ├── app/
│   │   ├── config.py           # Settings (PORT, MONGODB_URI, JWT, CORS)
│   │   ├── database.py         # Motor client, get_db
│   │   ├── dependencies.py    # get_current_user, require_roles
│   │   ├── main.py            # FastAPI app, CORS, routers, error handlers
│   │   ├── routers/           # auth, company, products, inquiries, categories,
│   │   │                      # wishlist, cart, rfq, quote, orders, messages, admin, suppliers
│   │   ├── schemas/           # Pydantic models and serialize_doc
│   │   └── services/
│   │       └── supplier_score.py   # Trust score, quote score, recalculate
│   ├── scripts/
│   │   ├── seed.py            # Minimal seed (admin, 2 sellers, 2 buyers, sample data)
│   │   └── generate_demo_data.py   # Full demo (12 categories, 25 sellers, 90 buyers, 600 products, RFQs, quotes, orders)
│   ├── requirements.txt
│   ├── run.py                 # Uvicorn entry
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/client.js      # Axios instance, authApi, productsApi, rfqApi, adminApi, etc.
│   │   ├── components/        # AppShell, Navbar, ProtectedRoute, ui/* (Button, Card, Badge, Input, etc.)
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/             # Home, Login, Register, Products, ProductDetail, Dashboard,
│   │   │                      # Wishlist, Cart, RFQList, RFQDetail, SellerProducts, SellerRFQs,
│   │   │                      # SellerOrders, CompanyProfile, AdminPanel
│   │   ├── utils/getCategoryImage.js   # Category → gradient + label for product cards
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
├── README.md
├── DELIVERABLES.md            # Mid-term upgrade deliverables
├── PHASE2.md                  # Phase 2 feature spec
└── update.md                  # This file
```

---

## 4. What’s done (phases & milestones)

### Phase 1 (MVP)

- Auth: register (buyer/seller), login, JWT, GET /api/auth/me
- Company profile: POST/GET /api/company
- Products: CRUD, list with search/category/city, GET by id, seller list
- Inquiries: POST, GET /api/inquiries/me
- Admin: GET /api/admin/summary
- Frontend: login, register, dashboard, products, product detail, seller products, company profile, protected routes

### Phase 1.6

- API: GET /, /health, /api, /docs (Swagger)
- Middleware: CORS, rate limiting (SlowAPI), centralized validation errors
- Frontend: design system, Framer Motion, Lucide, upgraded Products/Product detail/Dashboards/Auth

### Mid-term upgrade (Phase 2–style)

- **Wishlist** – toggle, list (buyer)
- **RFQ Cart** – add, update quantity/notes, clear, create RFQ from cart
- **RFQ flow** – create RFQ → sellers submit quotes → buyer sees quote comparison (trust score, quote score, verified) → accept quote → order created
- **Orders** – buyer/seller lists, statuses: created, confirmed, **processing**, shipped, delivered
- **Supplier trust score** – formula and levels; GET /api/suppliers/:id/score
- **Admin** – dashboard (users, verified/pending suppliers, RFQs, quotes, orders), users (ban/unban), supplier verification (verify/unverify, recalculate score), categories CRUD, RFQs/orders list, activity logs
- **Demo data script** – `generate_demo_data.py`: 12 categories, 25 sellers, 90 buyers, 600 products, wishlist/cart/RFQs/quotes/orders, supplier_scores, admin logs; preserves admin@smartb2b.com, seller@example.com, buyer@example.com

### UI/UX overhaul

- **Brand:** Teal (primary) + Coral (CTAs); Plus Jakarta Sans (Google Font)
- **Home:** Dark hero (slate + mesh gradient, floating blobs), headline “Smarter B2B. Real Deals.”, stats strip, bento feature cards, quote block, teal CTA section
- **Navbar:** Transparent on home when at top, solid on scroll; gradient logo; coral Sign up; active link underline (teal)
- **Products:** Dark hero, teal category chips, product cards with hover overlay and teal accents
- **Login/Register:** Dark left panel (slate + teal gradient), form with teal focus and role toggles
- **Dashboard:** Dark welcome banner with mesh and teal icon
- **Global:** overflow-x hidden to prevent layout bleed; rounded-2xl cards, shadow-glow, animations (fadeInUp, float, blob, gradientShift)

---

## 5. Theme & design (frontend)

### Colors (Tailwind)

- **Primary (teal):** 50–900 scale; 600 `#0d9488` for buttons/links
- **Coral:** 400–600 for CTAs (Sign up, primary actions)
- **Slate:** backgrounds (50), text (900), borders (200)

### Typography

- **Font:** Plus Jakarta Sans (Google Fonts), fallback system-ui
- Set in `index.html` and `tailwind.config.js` fontFamily.sans

### Animations (Tailwind keyframes)

- `fadeInUp`, `float`, `blob`, `gradientShift`, `shimmer`, `scaleIn`, `slideUp`
- Custom backgrounds: `mesh-dark`, `mesh-hero`, `grid-pattern`, `gradient-teal-coral`
- Shadows: `glow`, `glow-coral`, `card-hover`

### CSS (index.css)

- `:root` CSS variables for brand teal/coral/slate
- `html` / `body`: overflow-x hidden, smooth scroll
- Body dot pattern (::before)
- Focus visible: teal outline

---

## 6. Backend: collections & API summary

### MongoDB collections

| Collection         | Purpose |
|--------------------|--------|
| users              | email, password (hashed), role (admin/buyer/seller), name, isBanned, isVerifiedSupplier, createdAt |
| companyprofiles    | user, companyName, description, city, state, country, phone, website, gstNumber |
| categories         | name, slug |
| products           | seller, title, description, category, price, unit, minOrderQuantity, city, isActive |
| wishlistitems      | buyerId, productId |
| cartitems          | buyerId, productId, quantity, notes |
| rfqs               | buyerId, items[{ productId, quantity, notes }], status, sellers_in_rfq |
| quotes             | rfqId, sellerId, items[{ productId, unit_price, quantity, delivery_days }], message, status |
| orders             | rfqId, quoteId, buyerId, sellerId, items, totalAmount, status |
| supplier_scores    | seller_id, profile_completeness, response_rate, product_strength, buyer_rating, verified_status, total_score, trust_level |
| adminactionlogs    | adminId, actionType, targetId, details |

### API routers (prefixes)

- `/api/auth` – register, login, me
- `/api/company` – upsert, me
- `/api/products` – list, get by id, CRUD (seller), seller/me
- `/api/inquiries` – create, getMe
- `/api/categories` – list, create, update, delete (admin)
- `/api/wishlist` – get, toggle, remove
- `/api/cart` – get, add, update, remove, clear
- `/api/rfq`, `/api/rfqs` – create, me, assigned, get by id, status, quotes, submit quote, accept-quote, create-from-cart
- `/api/quote` – update
- `/api/orders` – me, get by id, update status
- `/api/messages` – get, post (by rfqId)
- `/api/admin` – summary, dashboard, users, ban, unban, verify-supplier, rfqs, orders, logs, suppliers verify/recalculate
- `/api/suppliers/:id/score` – GET supplier trust score

### Trust & quote score (backend logic)

- **Trust score** (0–100):  
  `0.30×profile_completeness + 0.20×response_rate + 0.20×product_strength + 0.15×buyer_rating + 0.15×verified_status`
- **Trust levels:** 85–100 Highly Trusted, 70–84 Trusted, 50–69 Moderate, &lt;50 Low Trust
- **Quote score** (for comparison): 50% price competitiveness + 25% delivery speed + 25% supplier trust

---

## 7. Frontend: routes & roles

| Route              | Page           | Allowed roles   |
|--------------------|----------------|-----------------|
| /                  | Home           | all             |
| /login             | Login          | all             |
| /register          | Register       | all             |
| /products          | Products       | all             |
| /product/:id       | ProductDetail  | all             |
| /wishlist          | Wishlist       | buyer           |
| /cart              | Cart           | buyer           |
| /rfq               | RFQList        | buyer           |
| /rfq/:id           | RFQDetail      | any logged-in   |
| /seller/products   | SellerProducts | seller          |
| /seller/rfqs       | SellerRFQs     | seller          |
| /seller/orders     | SellerOrders   | seller          |
| /profile/company   | CompanyProfile | seller          |
| /admin/panel       | AdminPanel     | admin           |
| /dashboard         | Dashboard      | any logged-in   |

---

## 8. Scripts & credentials

### Seed (minimal)

```bash
cd backend
python -m scripts.seed
```

- Creates admin, 2 sellers, 2 buyers, categories, sample products, wishlist/cart items, supplier_scores, one RFQ/quote/order.

### Full demo data

```bash
cd backend
python -m scripts.generate_demo_data
```

- Preserves: admin@smartb2b.com, seller@example.com, buyer@example.com
- Clears other demo data then creates: 12 categories, 25 sellers, 90 buyers, 600 products, 300 wishlist, 180 cart, 120 RFQs, 260 quotes, ~70 orders, supplier_scores, admin logs
- Demo users (non-preserved): password `Demo@123`

### Default credentials (after seed or demo)

| Role   | Email                | Password   |
|--------|----------------------|------------|
| Admin  | admin@smartb2b.com   | Admin@123  |
| Seller | seller@example.com   | Seller@123 |
| Buyer  | buyer@example.com    | Buyer@123  |

---

## 9. How to run locally

### Prerequisites

- Python 3.11+, Node.js 18+, MongoDB (local or Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m scripts.seed
python -m scripts.generate_demo_data   # optional
python run.py
```

- Runs at **http://localhost:5000**
- GET /docs for Swagger UI

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

- Runs at **http://localhost:5173**
- Vite proxies `/api` to backend when `VITE_API_URL` is unset

### Docker (optional)

```bash
docker-compose up -d
```

- Mongo: 27017, Backend: 5000, Frontend: 5173 (or as in docker-compose)

---

## 10. Environment variables

### Backend

| Variable      | Description           | Example                          |
|---------------|-----------------------|----------------------------------|
| PORT          | Server port           | 5000                             |
| NODE_ENV      | development/production| development                      |
| MONGODB_URI   | MongoDB connection    | mongodb://localhost:27017/smartb2b |
| JWT_SECRET    | JWT signing secret    | (long random string)             |
| JWT_EXPIRES_IN| Token expiry          | 7d                               |
| CORS_ORIGIN   | Allowed origins       | http://localhost:5173            |

### Frontend

| Variable     | Description        | Example                  |
|--------------|--------------------|--------------------------|
| VITE_API_URL | Backend base URL   | http://localhost:5000    |

---

## 11. Important implementation details

- **Serialization:** Backend uses `serialize_doc()` which sets both `id` and `_id` on responses for frontend compatibility.
- **Cart → RFQ:** Buyer creates RFQ from cart via POST `/api/rfq/create-from-cart`; frontend uses `res.data?.data?.rfq?._id || res.data?.rfq?.id` for navigation.
- **Trust on API:** Product list/detail and RFQ quotes include seller `trustScore`, `trustLevel`, `isVerifiedSupplier`; admin user list includes `trustScore`/`trustLevel` for sellers.
- **Order status flow:** created → confirmed → **processing** → shipped → delivered; seller can set Processing between Confirm and Mark Shipped.
- **Layout:** Hero and content are contained (no full-bleed breakout) with `overflow-x: hidden` on html/body and main wrapper to avoid content going off-screen.

---

## 12. Mid-term upgrade deliverables (Phase 2)

### Backend files changed / added

| File | Change |
|------|--------|
| `app/services/workflow_events.py` | **New** – `emit_event()` for RFQ/order/user audit events |
| `app/services/notifications.py` | **New** – `create_notification()` for in-app notifications |
| `app/routers/rfq.py` | Emit events on create/submit-quote/accept-quote; `createdAt` on RFQ/quote; GET `/{id}/timeline`, GET `/{id}/quote-comparison`; notify sellers on RFQ create, buyer on quote, seller on accept/order |
| `app/routers/orders.py` | Emit `ORDER_STATUS_CHANGED` on status update; GET `/{id}/timeline` |
| `app/routers/admin.py` | `createdAt` on admin logs; emit workflow events for ban/unban/verify/unverify; create notifications for verify/ban/unban; GET `/suppliers`, PUT `/suppliers/{id}/unverify`; GET `/categories`; dashboard enriched (totalProducts, rfq/order status dist, topCategories, topSuppliers); GET `/analytics/overview`, `/analytics/top-suppliers`, `/analytics/category-performance` |
| `app/routers/suppliers.py` | GET `/{seller_id}/profile` – company, trust, response rate, counts, categories |
| `app/routers/notifications.py` | **New** – GET `/me`, PUT `/{id}/read`, PUT `/read-all` |
| `app/routers/seller_dashboard.py` | **New** – GET `/dashboard` (products, RFQs, quotes, orders, response time, top products, charts) |
| `app/routers/buyer_dashboard.py` | **New** – GET `/dashboard` (wishlist, cart, RFQs, quotes, orders, recent RFQs/orders) |
| `app/main.py` | Include routers: notifications, seller_dashboard, buyer_dashboard |
| `scripts/generate_demo_data.py` | Clear/seed `workflow_events`, `notifications`; create sample events and notifications |

### Frontend files changed / added

| File | Change |
|------|--------|
| `src/api/client.js` | `rfqApi.getQuoteComparison`, `getTimeline`; `ordersApi.getTimeline`; `adminApi.getSuppliers`, `unverifySupplier`, `getCategories`, analytics; `suppliersApi.getProfile`; `notificationsApi`; `sellerDashboardApi`, `buyerDashboardApi` |
| `src/pages/Home.jsx` | Hero “Find Trusted Suppliers. Raise RFQs. Compare Quotes. Procure Better.”; CTAs Browse Products, Create RFQ; featured categories/products from API; How it works (4 steps); stats strip; footer |
| `src/pages/RFQDetail.jsx` | Timeline panel from `getTimeline`; quote comparison table with rank from `getQuoteComparison` (fallback to quotes); status from quotes for comparison rows |
| `src/pages/SupplierProfile.jsx` | **New** – `/suppliers/:id` – company, verified, trust, metrics, categories, products by supplier |
| `src/pages/Notifications.jsx` | **New** – `/notifications` – list, mark read, mark all read, links to RFQ/order/supplier |
| `src/pages/Dashboard.jsx` | Buyer/seller use `buyerDashboardApi`/`sellerDashboardApi`; admin dashboard shows topSuppliers, topCategories, orderStatusDistribution; buyer recent RFQs/orders |
| `src/pages/AdminPanel.jsx` | Load `getSuppliers`, `getCategories`; suppliers tab shows company/city; handle unverify via `unverifySupplier` |
| `src/components/Navbar.jsx` | Notifications bell with dropdown preview and unread count; link to /notifications |
| `src/App.jsx` | Routes: `/suppliers/:id`, `/notifications` |

### New API routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/rfq/{id}/timeline` | Workflow events for RFQ (buyer/seller/admin) |
| GET | `/api/rfq/{id}/quote-comparison` | Ranked quote comparison (buyer/admin) |
| GET | `/api/orders/{id}/timeline` | Workflow events for order |
| GET | `/api/suppliers/{seller_id}/profile` | Supplier public profile |
| GET | `/api/notifications/me` | Current user notifications |
| PUT | `/api/notifications/{id}/read` | Mark one read |
| PUT | `/api/notifications/read-all` | Mark all read |
| GET | `/api/admin/suppliers` | List sellers with trust/company |
| PUT | `/api/admin/suppliers/{id}/unverify` | Remove verification |
| GET | `/api/admin/categories` | All categories (admin) |
| GET | `/api/admin/analytics/overview` | Overview counts |
| GET | `/api/admin/analytics/top-suppliers` | Top suppliers by orders |
| GET | `/api/admin/analytics/category-performance` | Category product counts |
| GET | `/api/seller/dashboard` | Seller dashboard metrics |
| GET | `/api/buyer/dashboard` | Buyer dashboard metrics |

### New pages / components

- **SupplierProfile** – `/suppliers/:id` – company header, verified badge, trust meter, city, categories, response/order metrics, products list.
- **Notifications** – `/notifications` – full list, mark read / mark all read, click-through to RFQ/order.
- **Navbar** – notifications bell with dropdown (recent 5) and unread badge.

### Demo flows

1. **Buyer:** Login (buyer@example.com) → Browse products → Add to wishlist/cart → Create RFQ (from cart or RFQ page) → Open RFQ detail → See timeline + quote comparison (rank, score) → Accept quote → Order created; check Dashboard (recent RFQs/orders) and Notifications.
2. **Seller:** Login (seller@example.com) → Dashboard (products, RFQs, quotes, orders) → Seller RFQs → Submit quote → Seller Orders → Update order status; check Notifications (New RFQ, Quote accepted, New order).
3. **Admin:** Login (admin@smartb2b.com) → Admin Panel → Overview (dashboard with top suppliers/categories, order status) → Users (ban/unban) → Suppliers (verify/unverify, company/city) → Categories (list all, create/delete) → RFQs / Orders / Logs.

### Schema assumptions

- **workflow_events:** `entity_type` (`rfq` \| `order` \| `user`), `entity_id` (ObjectId), `actor_id`, `actor_role`, `event_type`, `event_label`, `metadata`, `created_at`.
- **notifications:** `user_id`, `title`, `message`, `type`, `related_entity_type`, `related_entity_id`, `is_read`, `created_at`.
- **adminactionlogs:** `createdAt` added on insert (was missing before).
- **rfqs / orders:** `createdAt` set on insert where missing.

### Placeholder / derived logic

- **Supplier profile:** `average_rating` comes from `buyer_rating` in supplier_scores (default 70); no standalone reviews collection.
- **Quote comparison:** `buyer_rating` in response is from trust score breakdown; ranking uses existing `compute_quote_score` (50% price, 25% delivery, 25% trust).
- **Seller dashboard:** `averageResponseTimeHours` computed from quote `createdAt` vs RFQ `createdAt` where available.
- **Products by supplier (SupplierProfile):** Filtered client-side from `productsApi.list()` by seller id; backend product list does not filter by seller for public list.

---

*Last updated to reflect the full project state including Phase 1, Phase 1.6, mid-term upgrade (timeline, quote comparison, supplier profile, notifications, admin/seller/buyer dashboards, demo data), and UI/UX (teal/coral theme, Plus Jakarta Sans, Home/Navbar/Products/Login/Dashboard updates).*
