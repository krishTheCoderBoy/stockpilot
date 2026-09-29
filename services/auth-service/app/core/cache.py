import json
from functools import wraps

from app.core.redis_client import redis_client

DEFAULT_TTL_SECONDS = 60


def cache_result(key: str, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Caches a function's JSON-serializable return value in Redis under `key`.
    On cache hit, returns the cached value without calling the function.
    On cache miss (or Redis being unreachable), calls the function and
    attempts to populate the cache, but never lets a Redis failure break
    the actual response.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cached = redis_client.get(key)
                if cached is not None:
                    return json.loads(cached)
            except Exception:
                pass  # Redis unreachable — fall through to computing fresh

            result = func(*args, **kwargs)

            try:
                redis_client.set(key, json.dumps(result, default=str), ex=ttl)
            except Exception:
                pass  # caching is an optimization, never a hard dependency

            return result
        return wrapper
    return decorator


def invalidate_cache(key: str) -> None:
    try:
        redis_client.delete(key)
    except Exception:
        pass