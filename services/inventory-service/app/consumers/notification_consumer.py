import json

import pika

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.events.publisher import EXCHANGE_NAME
from app.jobs.email_jobs import send_email_job
from app.modules.products.models import Product
from app.modules.users.models import User, UserRole
from app.core.redis_client import redis_client

QUEUE_NAME = "notifications.consumer"
BOUND_EVENT_TYPES = ["StockLow", "PurchaseOrderApproved"]


def is_duplicate(event_id: str) -> bool:
    key = f"processed_event:{event_id}"
    was_set = redis_client.set(key, "1", nx=True, ex=86400)  # 24h dedup window
    return not was_set


def _get_notify_recipients(db) -> list[User]:
    return (
        db.query(User)
        .filter(User.role.in_([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))
        .filter(User.is_active.is_(True))
        .all()
    )


def handle_stock_low(payload: dict, db) -> None:
    product = db.query(Product).filter(Product.id == payload["product_id"]).first()
    name = product.name if product else "Unknown product"
    for user in _get_notify_recipients(db):
        send_email_job(
            to_email=user.email,
            subject=f"StockPilot: {name} is low on stock",
            body=(
                f"{name} has dropped to {payload['on_hand_quantity']} units "
                f"(reorder point: {payload['reorder_point']})."
            ),
        )


def handle_po_approved(payload: dict, db) -> None:
    for user in _get_notify_recipients(db):
        send_email_job(
            to_email=user.email,
            subject="StockPilot: Purchase order approved",
            body=f"Purchase order {payload['po_id']} has been approved and is ready to order.",
        )


HANDLERS = {
    "StockLow": handle_stock_low,
    "PurchaseOrderApproved": handle_po_approved,
}


MAX_RETRIES = 3

def on_message(channel, method, properties, body):
    event = json.loads(body)
    event_type = event.get("event_type")
    event_id = event.get("event_id")

    if is_duplicate(event_id):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    handler = HANDLERS.get(event_type)
    db = SessionLocal()
    try:
        if handler:
            handler(event, db)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        retry_count = (properties.headers or {}).get("x-retry-count", 0)
        print(f"[consumer error] {event_type}: {e} (retry {retry_count})")

        if retry_count < MAX_RETRIES:
            channel.basic_publish(
                exchange="stockpilot.events.retry",
                routing_key="",
                body=body,
                properties=pika.BasicProperties(
                    headers={"x-retry-count": retry_count + 1},
                    delivery_mode=2,
                ),
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close()


def start_consumer():
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)

    # Dead-letter exchange + queue
    channel.exchange_declare(exchange="stockpilot.events.dlx", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="notifications.consumer.dlq", durable=True)
        # Retry queue: messages sit here for 5s, then automatically route back to the main queue
    channel.exchange_declare(exchange="stockpilot.events.retry", exchange_type="fanout", durable=True)
    channel.queue_declare(
        queue="notifications.consumer.retry",
        durable=True,
        arguments={
            "x-message-ttl": 5000,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": QUEUE_NAME,
        },
    )
    channel.queue_bind(exchange="stockpilot.events.retry", queue="notifications.consumer.retry")

    for event_type in BOUND_EVENT_TYPES:
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=event_type)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)

    print(f"[notification consumer] listening for: {BOUND_EVENT_TYPES}")
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()