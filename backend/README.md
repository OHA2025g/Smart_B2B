# SmartB2B Backend (Python)

Python/FastAPI port of the SmartB2B Node.js backend. Same API surface and MongoDB schema.

## Stack

- **FastAPI** – API server
- **Motor** – async MongoDB driver
- **Pydantic** – validation and settings
- **python-jose** – JWT
- **passlib[bcrypt]** – password hashing
- **SlowAPI** – rate limiting

## Setup

1. Create a virtualenv and install deps:

   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy env (optional). Defaults work for local dev.

   - `PORT` – default 5000
   - `MONGODB_URI` – default `mongodb://localhost:27017/smartb2b`
   - `JWT_SECRET` – default dev secret; set in production
   - `CORS_ORIGIN` – default `http://localhost:5173`

3. Run the API:

   ```bash
   python run.py
   # or
   uvicorn app.main:app --reload --port 5000
   ```

4. Seed DB (optional):

   ```bash
   python -m scripts.seed
   ```

## Endpoints

Same as the Node backend:

- `GET /`, `GET /health`, `GET /api` – root and health
- `POST/GET /api/auth/*` – register, login, me
- `POST/GET /api/company/*` – company profile
- `GET/POST/PUT/DELETE /api/products/*` – products
- `POST/GET /api/inquiries/*` – inquiries
- `GET/POST/PUT/DELETE /api/categories/*` – categories (admin for write)
- `GET/POST/DELETE /api/wishlist/*` – wishlist (buyer)
- `GET/POST/DELETE /api/cart/*` – cart (buyer)
- `POST/GET /api/rfq/*` – RFQ, quotes, accept-quote
- `PUT /api/quote/:id` – revise quote (seller)
- `GET/PUT /api/orders/*` – orders
- `GET/POST /api/messages/:rfqId` – messages
- `GET/PUT /api/admin/*` – admin summary, users, ban, verify, rfqs, orders, logs

API docs: **http://localhost:5000/docs**
