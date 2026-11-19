"""Small JSON cache over Redis. Every failure is swallowed: the cache is an optimisation,
never a dependency, so a Redis outage must not break a request."""
import json
import logging
from typing import Any

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


def cache_get_json(key: str) -> Any | None:
    try:
        raw = redis_client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        logger.warning("Cache read failed for %s", key, exc_info=True)
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        logger.warning("Cache write failed for %s", key, exc_info=True)
