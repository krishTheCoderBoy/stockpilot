"""Async Redis client. Callers decide whether a Redis failure is tolerable: conversation
history degrades quietly, while confirmation of a mutating action fails closed."""
import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    db=settings.redis_db,
    decode_responses=True,
)
