import logging
import pika
from app.core.config import settings
logger = logging.getLogger(__name__)
EXCHANGE_NAME = "stockpilot.events"
def publish_event(event) -> None:
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
        try:
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=event.event_type, body=event.model_dump_json().encode(), properties=pika.BasicProperties(delivery_mode=2))
        finally:
            connection.close()
    except Exception:
        logger.exception("Domain event publish failed: %s", getattr(event, "event_type", "unknown"))
