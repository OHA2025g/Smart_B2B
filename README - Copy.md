# B2Bभारत – Intelligent B2B Marketplace

**Tagline:** *Smarter B2B. Real Deals.*

B2Bभारत is a full-stack B2B marketplace where **buyers** discover products, build wishlists and RFQ carts, raise RFQs, compare seller quotes (with trust and quote scores), and place orders; **sellers** list products, respond with quotes, and manage order fulfillment; **admins** verify suppliers, moderate users, manage categories, and monitor RFQs, orders, and analytics.

This README is the main project overview: **tech stack**, **workflows**, **data model**, **API surface**, **how to run**, and **credentials**. Deeper change logs and file-level notes live in [`update.md`](update.md); specs and deliverables in [`DELIVERABLES.md`](DELIVERABLES.md) and [`PHASE2.md`](PHASE2.md).

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

## What’s built (milestones)

### Phase 1 (MVP)

- Auth: register (buyer / seller), login, JWT, `GET /api/auth/me`
- Company profile (seller): create/update, `GET /api/company/me`
- Products: CRUD, public list with search / category / city, detail, seller’s list
- Inquiries: create, list for buyer
- Admin: summary counts
- Frontend: login, register, role-based dashboard, products, product detail, seller products, company profile, protected routes

### Phase 1.6

- API: `GET /`, `/health`, `/api`, `/docs` (OpenAPI / Swagger)
- Middleware: CORS, rate limiting, centralized validation errors
- Frontend: shared design system, motion, upgraded products / product detail / dashboards / auth flows

### Mid-term upgrade (marketplace + trust + RFQ → order)

- **Wishlist** and **RFQ cart** (buyer); create RFQ from cart
- **RFQ lifecycle:** create → sellers submit quotes → buyer compares (trust + quote scores, verified badges) → accept quote → **order** created
- **Orders:** buyer/seller views; statuses **created → confirmed → processing → shipped → delivered**
- **Supplier trust:** scores and levels; `GET /api/suppliers/:id/score`; admin verify / unverify / recalculate
- **Admin:** users (ban/unban), suppliers, categories, RFQs, orders, activity logs, enriched dashboard and **analytics** endpoints
- **Demo data:** `scripts/generate_demo_data.py` (large synthetic dataset; preserves three fixed test accounts)

### Recent additions (workflow, notifications, dashboards)

- **Workflow events** (`workflow_events` collection): audit-style timeline for RFQs and orders (`GET .../timeline`)
- **In-app notifications** (`notifications` collection): `GET /api/notifications/me`, mark read / mark all read; navbar bell + `/notifications` page
- **Quote comparison API:** ranked quotes for an RFQ (`GET /api/rfq/{id}/quote-comparison`)
- **Supplier public profile:** `GET /api/suppliers/{seller_id}/profile` + frontend **`/suppliers/:id`**
- **Seller / buyer dashboards:** `GET /api/seller/dashboard`, `GET /api/buyer/dashboard` with metrics and summaries for the main **Dashboard** page

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
| `/notifications` | Logged-in |
| `/wishlist`, `/cart`, `/rfq` | Buyer |
| `/rfq/:id` | Logged-in (buyer/seller/admin as per RFQ) |
| `/seller/products`, `/seller/rfqs`, `/seller/orders`, `/profile/company` | Seller |
| `/dashboard` | Logged-in (role-specific content) |
| `/admin/panel` | Admin |

**UI theme:** teal primary + coral CTAs, **Plus Jakarta Sans**, dark heroes and cards on key pages; see `tailwind.config.js`, `index.css`, and [`update.md`](update.md) for design tokens.

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
