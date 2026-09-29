from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.redis_client import redis_client
from app.modules.users.routes import router as users_router
from app.modules.auth.routes import router as auth_router

app = FastAPI(
    title="StockPilot Auth Service",
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

app.include_router(users_router)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    try:
        redis_client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unreachable"
    return {"status": "ok", "service": "auth", "environment": settings.environment, "redis": redis_status}