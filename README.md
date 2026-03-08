# SmartB2B – Intelligent B2B Marketplace (Phase 1 + 1.6)

Phase 1 delivers a working MVP: buyer/seller signup and login, company profile, product listing CRUD, product browse/search, inquiries, and a basic admin summary. No ML in this phase.

**Phase 1.6** adds a professional API surface (GET /, /health, /api, /docs), production-grade middleware (CORS, rate limiting, centralized errors), and a marketplace-grade frontend (design system, framer-motion, lucide-react, upgraded Products, Product detail, Dashboards, Auth pages, Seller listings).

## Tech stack

- **Backend:** Python, FastAPI, MongoDB (Motor), JWT
- **Frontend:** React (Vite), TailwindCSS, React Router, Axios
- **Dev:** ESLint, Prettier
- **Deploy:** Docker Compose (optional) for Mongo + backend + frontend

## Repository structure

```
SmartB2B/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── routers/
│   │   └── schemas/
│   ├── scripts/
│   │   └── seed.py
│   ├── requirements.txt
│   ├── run.py
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   └── pages/
│   ├── .env.example
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Local setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- MongoDB (local or Docker)
- pip, npm or yarn

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python -m scripts.seed   # optional: minimal seed (admin + 2 sellers, 2 buyers, sample data)
python -m scripts.generate_demo_data   # optional: full demo data (12 categories, 25 sellers, 90 buyers, 600 products, RFQs, quotes, orders)
python run.py
```

Backend runs at **http://localhost:5000**.

- **GET /** – HTML landing page (API title, version, links to /health, /api).
- **GET /health** – JSON health check: `status`, `uptime`, `timestamp`, `db`, `version`.
- **GET /api** – JSON route index (auth, company, products, inquiries, admin).
- **GET /docs** – OpenAPI/Swagger UI for all API endpoints (JWT Bearer supported).

### 2. Frontend

```bash
cd frontend
cp .env.example .env
# Optional: set VITE_API_URL if not using Vite proxy (default uses proxy to backend)
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**. API calls are proxied to the backend.

### 3. Seed data and default credentials

**Minimal seed** (admin + 2 sellers, 2 buyers, sample products):

```bash
python -m scripts.seed
```

**Full demo data** for mid-term presentation (12 categories, 25 sellers, 90 buyers, 600 products, 120 RFQs, 260 quotes, 70 orders, supplier scores, admin logs). Safe to rerun (clears previous demo data, keeps the three fixed accounts):

```bash
python -m scripts.generate_demo_data
```

After either command, in `backend`:

| Role   | Email               | Password   |
|--------|---------------------|------------|
| Admin  | admin@smartb2b.com  | Admin@123  |
| Seller | seller@example.com  | Seller@123 |
| Buyer  | buyer@example.com   | Buyer@123  |

The seed also creates a company profile for the seller and sample products.

## Environment variables

### Backend (`.env` or env)

| Variable     | Description                          | Example                    |
|-------------|--------------------------------------|----------------------------|
| PORT        | Server port                          | 5000                       |
| NODE_ENV    | development / production             | development                |
| MONGODB_URI | MongoDB connection string            | mongodb://localhost:27017/smartb2b |
| JWT_SECRET  | Secret for JWT signing               | (use a long random string) |
| JWT_EXPIRES_IN | Token expiry                      | 7d                         |
| CORS_ORIGIN | Allowed frontend origin(s), comma-sep | http://localhost:5173      |

### Frontend (`.env`)

| Variable      | Description                    | Example             |
|---------------|--------------------------------|---------------------|
| VITE_API_URL  | Backend base URL (optional)    | http://localhost:5000 |

If `VITE_API_URL` is not set, the Vite dev server proxies `/api` to the backend.

## Sample API calls

Base URL: `http://localhost:5000`

- **Register (buyer):**  
  `POST /api/auth/register`  
  Body: `{ "email": "b@example.com", "password": "pass123", "role": "buyer", "name": "Buyer" }`

- **Login:**  
  `POST /api/auth/login`  
  Body: `{ "email": "admin@smartb2b.com", "password": "Admin@123" }`  
  Response includes `data.token` and `data.user`.

- **Current user:**  
  `GET /api/auth/me`  
  Header: `Authorization: Bearer <token>`

- **Company profile:**  
  `POST /api/company` (create/update), `GET /api/company/me`  
  Header: `Authorization: Bearer <token>`

- **Products:**  
  `GET /api/products?search=steel&category=Industrial&city=Mumbai`  
  `GET /api/products/:id`  
  `POST /api/products` (seller), `PUT /api/products/:id`, `DELETE /api/products/:id`  
  Seller’s list: `GET /api/products/seller/me`

- **Inquiries:**  
  `POST /api/inquiries` Body: `{ "productId": "...", "message": "...", "quantity": 10 }`  
  `GET /api/inquiries/me`

- **Admin:**  
  `GET /api/admin/summary`  
  Header: `Authorization: Bearer <admin_token>`  
  Returns counts of users, products, inquiries.

## Phase 1 checklist

### Backend

- [x] FastAPI server, clean structure (config, database, routers, schemas)
- [x] Auth: POST /api/auth/register (role buyer|seller), POST /api/auth/login, GET /api/auth/me
- [x] Company: POST /api/company, GET /api/company/me
- [x] Products: POST, GET (list + by id), PUT, DELETE; GET /api/products/seller/me
- [x] Inquiries: POST /api/inquiries, GET /api/inquiries/me
- [x] Admin: GET /api/admin/summary
- [x] Role-based auth (buyer, seller, admin), JWT Bearer
- [x] Input validation, error responses
- [x] Seed script

### Frontend

- [x] /login, /register, /dashboard (role-based), /products, /product/:id, /seller/products, /profile/company
- [x] Tailwind layout, navbar, auth (localStorage + Axios interceptor)
- [x] Protected routes by role
- [x] Forms and basic toasts/alerts

### Quality & docs

- [x] Backend: `python run.py`; Frontend: `npm run dev`
- [x] README with overview, setup, env vars, sample API, seed credentials
- [x] .env.example for frontend

## Docker Compose (optional)

From the project root:

```bash
docker-compose up -d
```

- MongoDB: 27017  
- Backend: 5000 (Python/FastAPI, builds from backend/Dockerfile)  
- Frontend: 5173 (builds from frontend/Dockerfile)

Run seed inside the backend container once DB is up:

```bash
docker-compose exec backend python -m scripts.seed
```

Then open http://localhost:5173 and log in with the seed credentials above.
