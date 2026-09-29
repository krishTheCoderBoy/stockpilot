import json

import pika

from app.core.config import settings

EXCHANGE_NAME = "stockpilot.events"


def _get_connection():
    params = pika.URLParameters(settings.rabbitmq_url)
    return pika.BlockingConnection(params)


def publish_event(event) -> None:
    """
    Publishes a domain event to the topic exchange.
    Routing key = event_type (e.g. "PurchaseOrderApproved"), so consumers
    can bind to specific event types without knowing about every producer.
    Failures here are logged, never allowed to break the caller's transaction —
    same principle as cache failures in Milestone 35.
    """
    try:
        connection = _get_connection()
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=event.event_type,
            body=event.model_dump_json().encode(),
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
        connection.close()
    except Exception as e:
        print(f"[event publish failed] {event.event_type}: {e}")