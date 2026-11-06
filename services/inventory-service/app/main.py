from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.redis_client import redis_client
from app.modules.products.routes import router as products_router
from app.modules.products.categories_routes import router as categories_router
from app.modules.warehouses.routes import router as warehouses_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.inventory_movements.routes import router as movements_router
from app.modules.inventory_batches.routes import router as batches_router

app = FastAPI(
    title="StockPilot Inventory Service",
    docs_url="/docs" if settings.environment != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(products_router)
app.include_router(categories_router)
app.include_router(warehouses_router)
app.include_router(inventory_router)
app.include_router(movements_router)
app.include_router(batches_router)


@app.get("/health")
def health_check():
    try:
        redis_client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unreachable"
    return {"status": "ok", "service": "inventory", "environment": settings.environment, "redis": redis_status}