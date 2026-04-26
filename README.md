# B2Bभारत – Intelligent B2B Marketplace

**Tagline:** *Smarter B2B. Real Deals.*

B2Bभारत is a full-stack B2B marketplace where **buyers** discover products, build wishlists and RFQ carts, raise RFQs, compare seller quotes (with trust and quote scores), and place orders; **sellers** list products, respond with quotes, and manage order fulfillment; **admins** verify suppliers, moderate users, manage categories, and monitor RFQs, orders, and analytics.

This README is the main project overview: **everything the product does today**, **tech stack**, **workflows**, **data model**, **API surface**, **how to run**, and **credentials**. Deeper change logs and file-level notes live in [`update.md`](update.md); specs and deliverables in [`DELIVERABLES.md`](DELIVERABLES.md) and [`PHASE2.md`](PHASE2.md).

---

## What B2Bभारत can do today (full feature catalog)

Below is a practical list of **what is implemented end-to-end** (UI + API unless noted). Use it as the single place to see scope of the live website and backend.

### Public & marketing

- **Landing page (`/`)** — Animated hero (Framer Motion), value props (verified suppliers, RFQ flow, B2B network), step-by-step “how it works,” **live stats** from the API (category count, product count), **featured products** and **category** exploration, testimonials-style blocks, and CTAs to register or browse products.
- **Product catalog (`/products`)** — Paginated-style listing with **search**, **category** filter (including quick category chips), and **city** filter; skeleton loading and empty states; each card links to product detail. **Buyers** can **toggle wishlist** (heart) and **add to RFQ cart** from the grid without leaving the page (toasts on actions).
- **Supplier directory (/suppliers)** — List suppliers with search and trust filters; links to **supplier profile** and products.
- **Product detail (`/product/:id`)** — Full product info: title, **₹** price and unit, description, **minimum order quantity**, **city**, seller name, **category** with visual treatment; **supplier trust panel** (trust score %, trust level, verified vs unverified badge). **Logged-in buyers** can send a **product inquiry** (quantity stepper + required message). Guests are prompted to log in as a buyer to inquire.
- **Supplier profile (`/suppliers/:id`)** — Public page: company name, **verified supplier** badge when applicable, location, **trust score / trust level**, activity-style metrics from the profile API, and a **product grid** for that supplier (products loaded from the public list and filtered in the client by seller id).

### Authentication & access control

- **Register (`/register`)** — Email, password, name, **role: buyer or seller**; on success, JWT stored and redirect to dashboard.
- **Login (`/login`)** — JWT session; **`GET /api/auth/me`** restores session on refresh.
- **Protected routes** — Pages are gated by login and, where needed, **role** (buyer-only: wishlist, cart, buyer RFQ list; seller-only: products, seller RFQs/orders, company profile; admin-only: admin panel).
- **API client** — Attaches `Authorization: Bearer` automatically; on **401**, clears storage and sends the user to login.

### Buyer experience

- **Wishlist (`/wishlist`)** — View and manage saved products (backed by wishlist API).
- **RFQ cart (`/cart`)** — Line items with quantities/notes, **update**, **remove**, **clear cart**, and **create RFQ from cart** (navigates to the new RFQ detail). Empty-state guidance when the cart has no items.
- **My RFQs (`/rfq`)** — List of the buyer’s RFQs with status badges; each row links to **RFQ detail**.
- **RFQ detail (`/rfq/:id`)** — Available to participants (buyer, assigned sellers, admin as applicable):
  - **Status stepper** (created → quoted → accepted / order).
  - **Workflow timeline** (dated events with actor role) when the backend returns timeline data.
  - **Line items** (products and quantities).
  - **Quote comparison** (buyer): ranked table when comparison API returns data — rank, seller, **verified** badge, quoted price, delivery days, available qty, **trust score**, **quote score**, status, and **Accept quote** (creates an **order** and updates RFQ/quote state).
  - **RFQ message thread** — Load history and **send messages** tied to the RFQ (buyers, sellers, and others with access use the same thread UI).
- **Dashboard (`/dashboard`)** — Buyer view: **stats** (RFQs, cart items, wishlist items) from **`/api/buyer/dashboard`** with fallback to counting from list endpoints; **recent inquiries** list with product context and links.
- **Notifications (`/notifications`)** — Full list with **mark one read** and **mark all read**; deep links to RFQ, dashboard (orders), or supplier profile when the payload includes related entities.

### Seller experience

- **Company profile (`/profile/company`)** — Create/update seller **company** record (`/api/company`).
- **My products (`/seller/products`)** — **List** own products; **grid/list** toggle; **create**, **edit**, **delete**; form covers title, description, category, price, unit, MOQ, city; loading skeletons and empty state.
- **RFQs for you (/seller/rfqs)** — RFQs that include the seller’s products; **submit** or **revise quote** in the same modal (default pricing from products; PUT /api/quote/:id under the hood). Links into shared **RFQ detail** for messaging and context.
- **My orders (`/seller/orders`)** — Orders after a buyer accepts a quote; **status progression**: created → **Confirm** → confirmed → **Processing** / **Mark shipped** → shipped → **Mark delivered**; badges reflect state including cancelled/delivered styling where applicable.
- **Dashboard (`/dashboard`)** — Seller view: **active RFQs** and **orders received** from **`/api/seller/dashboard`** with fallback counts; **inquiries** relevant to the seller surfaced like the buyer dashboard pattern.

### Admin experience

- **Admin panel (`/admin/panel`)** — Tabbed UI:
  - **Dashboard** — Overview metrics and charts/data from admin dashboard endpoint (plus analytics calls where wired).
  - **Users** — List users; **ban** / **unban**.
  - **Supplier verification** — Verify or remove verification; **recalculate trust score** for a supplier.
  - **Categories** — List and **create** / **update** / **delete** categories (admin APIs + category endpoints).
  - **RFQs** — Browse RFQs across the platform.
  - **Orders** — Browse orders.
  - **Moderation** — **Flagged RFQ messages** (e.g. contact-sharing policy).
  - **Activity logs** — Admin action log stream.
- **Dashboard (`/dashboard`)** — Admin view: **summary** counts and **dashboard** payload for high-level monitoring.

### Cross-cutting UI & UX

- **Navbar** — Role-aware links (buyer: Wishlist, Cart, RFQs, Suppliers; seller: My Products, RFQs, Orders, Company; admin: Admin Panel); **Dashboard** for all logged-in roles; **notification bell** with **unread count**, hover dropdown of latest items, link to **view all**; **logout**; on the home page, **transparent header** that solidifies on scroll.
- **Design system** — Shared **Button**, **Card**, **Badge**, **Input**, **Select**, **Table**, **StatCard**, **EmptyState**, **SkeletonCard**, **Toast** provider; **Tailwind** theme with **teal** primary and **coral** CTAs, **Plus Jakarta Sans**, **Lucide** icons, **Framer Motion** on key pages.
- **Layout** — **`AppShell`** wraps routes with navbar and consistent page container.

### Backend & platform (what powers the site)

- **REST API** under `/api/...` as summarized in [API overview](#api-overview-prefixes); **OpenAPI** at **`/docs`** (Swagger UI).
- **Operational endpoints** — `GET /`, **`/health`**, **`/api`** route index.
- **Security & quality** — **JWT** auth, **CORS**, **rate limiting** (SlowAPI when enabled), centralized validation error shaping.
- **Trust engine** — Supplier **trust scores** and **levels**; admin verify/unverify and **recalculate**; **quote comparison scoring** blends price, delivery, and trust.
- **Automation** — **Workflow events** for audit-style RFQ/order timelines; **in-app notifications** on relevant business events.
- **Data** — MongoDB collections as in [MongoDB collections](#mongodb-collections-main); **seed** and **large demo dataset** scripts for realistic trials.

**Intentionally not in current scope:** ML-based recommendations (called out as deferred in product planning).

---

## Tech stack

| Layer | Technology |
|--------|------------|
| **Backend** | Python 3.11+, **FastAPI**, **Motor** (async MongoDB), **Pydantic** / pydantic-settings, **JWT** (python-jose), **Passlib** (bcrypt), **SlowAPI** (rate limiting) |
| **Frontend** | **React 18**, **Vite 5**, **React Router 6**, **Axios**, **TailwindCSS 3**, **Framer Motion**, **Lucide React** |
| **Database** | **MongoDB** (see collections below) |
| **Tooling** | ESLint, Prettier; optional **Docker Compose** (Mongo + backend + frontend) |

**Not in scope for current phases:** machine learning / recommendation models (explicitly deferred).

---

## How we got here (milestones, brief)

| Stage | Highlights |
|--------|------------|
| **Phase 1 (MVP)** | Auth (buyer/seller), company profile, products CRUD + public catalog, inquiries, basic admin summary, first dashboards and protected SPA routes. |
| **Phase 1.6** | Root/health/api/docs discovery, CORS + rate limiting + validation errors, shared UI kit and motion on core flows. |
| **Marketplace + trust + RFQ → order** | Wishlist, RFQ cart, full RFQ/quote/order lifecycle, supplier trust scores + admin verification, rich admin module, analytics APIs, demo data generator (keeps fixed test accounts). |
| **Recent platform polish** | Workflow timelines, in-app notifications (API + bell + page), quote-comparison endpoint, public supplier profiles, dedicated **buyer/seller dashboard** APIs feeding the Dashboard page. |

For dated or file-level notes, see [`update.md`](update.md).

---

## Business workflow (high level)

### Buyer

1. Register / log in → browse **Products** → wishlist / cart.
2. Create **RFQ** (from cart or RFQ flow) → invited sellers see the RFQ.
3. Compare **quotes** (price, delivery, supplier trust) on RFQ detail → **accept** one quote → **order** is created.
4. Track orders; use **Dashboard** (buyer metrics) and **Notifications** for RFQ/quote/order updates.

### Seller

1. Complete **company profile**, manage **products**.
2. Receive RFQs assigned to you → submit **quotes**.
3. On acceptance, manage **orders** (confirm → processing → shipped → delivered).
4. Use **Dashboard** (seller metrics) and **Notifications** (new RFQ, quote accepted, new order).

### Admin

1. **Admin panel:** overview, users, suppliers (verify / unverify), categories, RFQs, orders, logs.
2. **Analytics** APIs for overview, top suppliers, category performance.
3. Ban/unban and verification actions emit **workflow events** and **notifications** where applicable.

### Trust & quote scoring (backend)

- **Trust score (0–100):** blend of profile completeness, response rate, product strength, buyer rating component, verified status (see `supplier_score` service).
- **Trust levels:** e.g. Highly Trusted / Trusted / Moderate / Low Trust from total score bands.
- **Quote score (comparison):** ~50% price competitiveness, ~25% delivery speed, ~25% supplier trust.

---

## Repository structure

```
B2Bभारत/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── routers/          # auth, company, products, inquiries, categories,
│   │   │                     # wishlist, cart, rfq, quote, orders, messages,
│   │   │                     # admin, suppliers, notifications, seller/buyer dashboard
│   │   ├── schemas/
│   │   └── services/         # e.g. supplier_score, notifications, workflow_events
│   ├── scripts/
│   │   ├── seed.py
│   │   └── generate_demo_data.py
│   ├── requirements.txt
│   ├── run.py
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/       # AppShell, Navbar, ProtectedRoute, ui/*
│   │   ├── context/
│   │   ├── pages/            # Home, auth, products, RFQ, orders, admin, supplier profile, notifications, …
│   │   └── utils/
│   ├── .env.example
│   └── package.json
├── docker-compose.yml
├── README.md                 # this file
├── update.md                 # detailed changelog / implementation reference
├── DELIVERABLES.md
└── PHASE2.md
```

---

## MongoDB collections (main)

| Collection | Purpose |
|------------|---------|
| `users` | Auth, role (admin / buyer / seller), ban, verified supplier flags |
| `companyprofiles` | Seller company info |
| `categories` | Product categories |
| `products` | Listings (seller, pricing, MOQ, city, active flag) |
| `wishlistitems`, `cartitems` | Buyer wishlist / RFQ cart |
| `rfqs`, `quotes` | RFQs and seller quotes |
| `orders` | Orders after quote acceptance |
| `supplier_scores` | Trust breakdown and totals |
| `adminactionlogs` | Admin actions |
| `workflow_events` | Timelines for RFQs / orders / user-related events |
| `notifications` | Per-user in-app notifications |

---

## API overview (prefixes)

- **`/api/auth`** – register, login, me  
- **`/api/company`** – upsert, me  
- **`/api/products`** – list, get, CRUD (seller), seller/me  
- **`/api/inquiries`** – create, me  
- **`/api/categories`** – list; admin write  
- **`/api/wishlist`**, **`/api/cart`** – buyer wishlist / cart  
- **`/api/rfq`**, **`/api/rfqs`** – RFQ create, me, detail, quotes, submit quote, accept quote, create-from-cart, **timeline**, **quote-comparison**  
- **`/api/quote`** – revise quote (seller)  
- **`/api/orders`** – me, get by id, update status, **timeline**  
- **`/api/messages`** – RFQ-thread messages  
- **`/api/admin`** – summary, dashboard, users, ban/unban, suppliers, verify/unverify/unverify, categories, RFQs, orders, logs, **analytics** (`/analytics/overview`, `top-suppliers`, `category-performance`)  
- **`/api/suppliers`** – score, **public profile**  
- **`/api/notifications`** – me, read, read-all  
- **`/api/seller`** – **dashboard**  
- **`/api/buyer`** – **dashboard**  

**Discovery:** `GET /docs` (Swagger UI) on the backend host.

---

## Frontend routes (summary)

| Route | Typical access |
|-------|----------------|
| `/` | Home (public) |
| `/login`, `/register` | Public |
| `/products`, `/product/:id` | Public |
| `/suppliers/:id` | Public supplier profile |
| `/notifications` | Any logged-in role |
| `/wishlist`, `/cart`, `/rfq` | Buyer only (protected) |
| `/rfq/:id` | Logged-in; **shared** by buyer (owner), **assigned sellers**, and **admin** — quotes, comparison, messages, timeline |
| `/seller/products`, `/seller/rfqs`, `/seller/orders`, `/profile/company` | Seller only (protected) |
| `/dashboard` | Logged-in; **content switches** by buyer / seller / admin |
| `/admin/panel` | Admin only (protected) |
| `*` (unknown paths) | Redirect to `/` |

**UI theme:** teal primary + coral CTAs, **Plus Jakarta Sans**, dark heroes and cards on key pages; see `frontend/tailwind.config.js`, `frontend/src/index.css`, and [`update.md`](update.md) for design tokens.

---

## Local setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** (local install or Docker)
- **pip**, **npm** (or yarn)

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python -m scripts.seed                    # optional: minimal seed
python -m scripts.generate_demo_data      # optional: large demo dataset
python run.py
```

- API: **http://localhost:5000**  
- **`GET /`** – HTML landing with links  
- **`GET /health`** – JSON health (`status`, `uptime`, `db`, `version`, …)  
- **`GET /api`** – JSON route index  
- **`GET /docs`** – Swagger UI  

### 2. Frontend

```bash
cd frontend
cp .env.example .env
# Optional: VITE_API_URL=http://localhost:5000 (if not using Vite proxy)
npm install
npm run dev
```

- App: **http://localhost:5173**  
- If `VITE_API_URL` is unset, Vite dev server proxies **`/api`** to the backend (see `vite.config.js`).

### 3. Docker Compose (optional)

Requires **Docker Desktop** (or another engine) to be **running**.

```bash
docker compose up -d --build
```

Typical ports: MongoDB **27017**, backend **5000**, frontend **5173** (confirm in `docker-compose.yml`).

Seed inside the backend container after DB is up:

```bash
docker compose exec backend python -m scripts.seed
```

---

## Seed data and default credentials

**Minimal seed** (`python -m scripts.seed`): admin, two sellers, two buyers, sample categories/products, starter RFQ/quote/order data.

**Full demo** (`python -m scripts.generate_demo_data`): clears prior demo-generated data but **keeps** the three accounts below; generates categories, many sellers/buyers/products, RFQs, quotes, orders, supplier scores, admin logs, plus sample **workflow_events** and **notifications**. Other demo users typically use password **`Demo@123`**.

| Role   | Email               | Password   |
|--------|---------------------|------------|
| Admin  | admin@smartb2b.com  | Admin@123  |
| Seller | seller@example.com  | Seller@123 |
| Buyer  | buyer@example.com   | Buyer@123  |

---

## Environment variables

### Backend (`.env` or process env)

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | HTTP port | `5000` |
| `NODE_ENV` | `development` / `production` | `development` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/smartb2b` |
| `JWT_SECRET` | JWT signing secret | (long random string in production) |
| `JWT_EXPIRES_IN` | Token lifetime | `7d` |
| `CORS_ORIGIN` | Allowed origins (comma-separated) | `http://localhost:5173` |

### Frontend (`.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend base URL (optional if using proxy) | `http://localhost:5000` |

---

## Sample API usage

Base URL: `http://localhost:5000`

- **Register (buyer):** `POST /api/auth/register`  
  Body: `{ "email": "b@example.com", "password": "pass123", "role": "buyer", "name": "Buyer" }`
- **Login:** `POST /api/auth/login`  
  Body: `{ "email": "admin@smartb2b.com", "password": "Admin@123" }`  
  Response includes token and user (shape per OpenAPI).
- **Authenticated calls:** header `Authorization: Bearer <token>`

Use **`/docs`** for full request/response schemas and newer endpoints (notifications, timelines, dashboards, analytics).

---

## Implementation notes (quick reference)

- Responses often use **`serialize_doc()`** so documents expose both `id` and `_id` where needed for the frontend.
- **Order statuses** follow the seller workflow: created → confirmed → **processing** → shipped → delivered.
- **Supplier profile** product lists may use public product listing filtered client-side by seller where the API does not expose a dedicated “by seller” public endpoint; see [`update.md`](update.md) for nuances.
- **Docker:** if `docker compose` fails with “pipe … dockerDesktopLinuxEngine” missing, start **Docker Desktop** (or your Docker engine) and retry.

---

## Checklist (current state)

The authoritative narrative list of capabilities is in the **What B2Bभारत can do today (full feature catalog)** section above; this checklist is a compact completion matrix.

### Backend

- [x] FastAPI app, config, DB lifecycle, routers, schemas, services  
- [x] Auth, company, products, inquiries, categories, wishlist, cart  
- [x] RFQ, quotes, orders, messages  
- [x] Admin (users, suppliers, categories, RFQs, orders, logs, analytics)  
- [x] Supplier scores and profiles  
- [x] Notifications + workflow events + seller/buyer dashboards  
- [x] Rate limiting (when SlowAPI available), validation error shaping  
- [x] Seed + demo data scripts  

### Frontend

- [x] Marketing home, auth, products, product detail, supplier profile  
- [x] Buyer: wishlist, cart, RFQ list/detail (timeline, quote comparison)  
- [x] Seller: products, RFQs, orders, company profile  
- [x] Admin panel; role-based dashboard  
- [x] Notifications page + navbar bell  
- [x] Tailwind UI, motion, protected routes, API client  

### Docs & ops

- [x] README (this file): stack, workflow, structure, run, env, API map  
- [x] `update.md` for detailed file/API changelog  
- [x] Optional Docker Compose; frontend `.env.example`  

---

## License / contributing

Add a `LICENSE` and contribution guidelines if you open the repo publicly; not included in this template.

---

## Quick start (production-style)

### Release highlights (shipped in this tree)
- **Supplier directory** — `GET /api/suppliers` and `/suppliers` in the SPA; trust filters and profile links.
- **RFQ logistics** — Cart and API require **delivery location** and **required-by**; optional priority, notes, and RFQ validity.
- **Quotes & orders** — Compare quotes, accept (creates order with `paymentStatus`), seller/admin order status, **escrow demo** actions, **print** PO/invoice on order detail.
- **Governance** — Admin **Moderation** tab lists **flagged RFQ messages** (contact-sharing detection); activity logs and dashboards as before.


### Prerequisites
- **Python 3.11+**
- **Node 18+**
- **MongoDB** (local or Atlas URI in `backend/.env`)

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# copy .env.example to .env and set MONGODB_URI / JWT_SECRET
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database seed (demo users + baseline data)
```bash
cd backend
python scripts/seed.py
# optional large demo set:
python scripts/generate_demo_data.py
```

**Demo logins (after `seed.py`):**
| Role | Email | Password |
|------|--------|----------|
| Admin | `admin@smartb2b.com` | `Admin@123` |
| Seller | `seller@example.com` | `Seller@123` |
| Buyer | `buyer@example.com` | `Buyer@123` |

### Frontend
```bash
cd frontend
npm install
# dev: Vite proxy uses /api — run backend on same machine or set VITE_API_URL
npm run dev
# production bundle
npm run build
```

### Docker
Use `docker-compose.yml` at the repo root if you prefer an all-in-one stack; ensure env vars match `backend` settings.

### Smoke test
- `cd frontend && npm run build && npm run lint`
- `cd backend && python -c "from app.main import app; print('ok', app.title)"`
- Log in as buyer → RFQ cart → create RFQ → (seller) quote → (buyer) accept → order → print invoice; admin → panel & logs.
