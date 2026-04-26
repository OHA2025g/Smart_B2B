import time
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.database import get_db
from app.schemas.common import success_response

router = APIRouter()

VERSION = "1.0.0"


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    base = str(request.base_url).rstrip("/")
    env = "development"  # could read from settings
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SmartB2B API</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; max-width: 720px; margin: 0 auto; padding: 2rem; color: #1a1a1a; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    a {{ color: #4f46e5; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    ul {{ padding-left: 1.25rem; }}
    li {{ margin: 0.5rem 0; }}
    pre {{ background: #f4f4f5; padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; }}
    .section {{ margin-top: 1.5rem; }}
    code {{ background: #f4f4f5; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>SmartB2B API</h1>
  <p class="meta">
    <strong>Version</strong> {VERSION} &bull;
    <strong>ENV</strong> {env} &bull;
    <strong>Server</strong> Python/FastAPI
  </p>
  <p>Intelligent B2B Marketplace – Phase 1 API. Use the links and sample commands below to explore.</p>
  <ul>
    <li><a href="{base}/health">/health</a> – Health check (JSON)</li>
    <li><a href="{base}/api">/api</a> – Route index (JSON)</li>
  </ul>
  <div class="section">
    <h2>Sample requests</h2>
    <p><strong>Login</strong></p>
    <pre>curl -X POST {base}/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"email":"admin@smartb2b.com","password":"Admin@123"}}'</pre>
    <p><strong>List products</strong></p>
    <pre>curl "{base}/api/products?search=steel"</pre>
  </div>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/api/public/stats")
async def public_market_stats():
    """Anonymous-friendly counts for marketing / landing page."""
    db = get_db()
    products_c = await db.products.count_documents({"isActive": True})
    sellers_c = await db.users.count_documents({"role": "seller"})
    rfqs_c = await db.rfqs.count_documents({})
    orders_c = await db.orders.count_documents({})
    return success_response(data={
        "stats": {
            "totalProducts": products_c,
            "suppliers": sellers_c,
            "totalRfqs": rfqs_c,
            "totalOrders": orders_c,
        }
    })


@router.get("/health")
async def health(request: Request):
    import datetime
    db_state = "disconnected"
    try:
        db = get_db()
        await db.command("ping")
        db_state = "connected"
    except Exception:
        pass
    return {
        "status": "ok",
        "uptime": int(time.time() - (request.app.state._start_time if hasattr(request.app.state, "_start_time") else time.time())),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "db": db_state,
        "version": VERSION,
    }


@router.get("/api")
async def api_index():
    return {
        "name": "SmartB2B API",
        "version": VERSION,
        "routes": [
            {"path": "/api/auth", "description": "Authentication: register, login, me"},
            {"path": "/api/company", "description": "Company profile: create/update, get my profile"},
            {"path": "/api/products", "description": "Products: list, get by id, seller CRUD, seller/me"},
            {"path": "/api/inquiries", "description": "Inquiries: create (buyer), get my inquiries"},
            {"path": "/api/categories", "description": "Categories: list (public), CRUD (admin)"},
            {"path": "/api/wishlist", "description": "Wishlist: get, toggle, remove (buyer)"},
            {"path": "/api/cart", "description": "RFQ Cart: get, add, remove, clear (buyer)"},
            {"path": "/api/rfq", "description": "RFQ: create, my, assigned, quotes, accept-quote"},
            {"path": "/api/quote", "description": "Quote: revise (seller)"},
            {"path": "/api/orders", "description": "Orders: my, by id, update status"},
            {"path": "/api/messages", "description": "Messages: get/post by rfqId"},
            {"path": "/api/admin", "description": "Admin: summary, users, ban, verify-supplier, rfqs, orders, logs"},
        ],
        "docs": "/docs",
    }
