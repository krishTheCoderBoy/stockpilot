import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.core.redis_client import redis_client
from app.core.security_headers import SecurityHeadersMiddleware
from app.modules.chat.llm import llm_client
from app.modules.chat.routes import router as chat_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="StockPilot Chatbot Service",
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
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(chat_router)


@app.get("/health")
async def health_check():
    try:
        await redis_client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unreachable"
    return {
        "status": "ok",
        "service": "chatbot",
        "environment": settings.environment,
        "redis": redis_status,
        "llm_provider": llm_client.describe(),
    }
