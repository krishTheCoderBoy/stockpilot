import redis
from rq import Queue

from app.core.config import settings

rq_redis_conn = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    db=settings.redis_db,
    ssl=False,
    decode_responses=False,
)

email_queue = Queue("emails", connection=rq_redis_conn)
notification_queue = Queue("notifications", connection=rq_redis_conn)