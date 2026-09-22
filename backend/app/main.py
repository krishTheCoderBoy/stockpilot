from fastapi import FastAPI

from app.core.config import settings
from app.modules.users.routes import router as users_router
from app.modules.auth.routes import router as auth_router
from app.modules.products.routes import router as products_router
from app.modules.products.categories_routes import router as categories_router
from app.modules.warehouses.routes import router as warehouses_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.inventory_movements.routes import router as movements_router
from app.modules.suppliers.routes import router as suppliers_router
from app.modules.purchase_orders.routes import router as po_router
from fastapi.middleware.cors import CORSMiddleware
from app.modules.dashboard.routes import router as dashboard_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.limiter import limiter
from app.core.security_headers import SecurityHeadersMiddleware


app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(po_router)
app.include_router(suppliers_router)
app.include_router(inventory_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(movements_router)
app.include_router(dashboard_router)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # replace with your real deployed frontend URL later
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}