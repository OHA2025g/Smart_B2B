import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import connect_db, close_db
from app.schemas.common import error_response
from app.routers import (
    root,
    auth,
    company,
    products,
    inquiries,
    categories,
    wishlist,
    cart,
    rfq,
    quote,
    orders,
    messages,
    admin,
    suppliers,
    notifications,
    seller_dashboard,
    buyer_dashboard,
)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    _slowapi_available = True
except ImportError:
    _slowapi_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state._start_time = time.time()
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="SmartB2B API",
    version="1.0.0",
    lifespan=lifespan,
)

if _slowapi_available:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"field": str(e.get("loc", [])[-1]), "message": e.get("msg", "")} for e in exc.errors()]
    msg = ", ".join(e.get("msg", "") for e in exc.errors())
    return JSONResponse(status_code=400, content=error_response(msg or "Validation error", "VALIDATION_ERROR", details=details, path=str(request.url.path)))


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router, tags=["root"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(company.router, prefix="/api/company", tags=["company"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(inquiries.router, prefix="/api/inquiries", tags=["inquiries"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["wishlist"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(rfq.router, prefix="/api/rfq", tags=["rfq"])
app.include_router(rfq.router, prefix="/api/rfqs", tags=["rfqs"])
app.include_router(quote.router, prefix="/api/quote", tags=["quote"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(seller_dashboard.router, prefix="/api/seller", tags=["seller"])
app.include_router(buyer_dashboard.router, prefix="/api/buyer", tags=["buyer"])

# Optional: serve frontend in production
if settings.node_env == "production":
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/assets", StaticFiles(directory=frontend_path / "assets"), name="assets")
        # SPA fallback would need a custom route; skip for minimal conversion
