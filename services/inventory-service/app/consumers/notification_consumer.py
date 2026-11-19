import logging
from functools import partial
from typing import Callable

import pika
from sqlalchemy.orm import Session

from app.consumers.retry import declare_consumer_topology, handle_delivery
from app.core.auth_client import get_notification_recipients
from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.email_jobs import send_email_job
from app.modules.products.models import Product

logger = logging.getLogger(__name__)

QUEUE_NAME = "notifications.consumer"
BOUND_EVENT_TYPES = ["StockLow", "PurchaseOrderApproved"]


def handle_stock_low(payload: dict, db: Session) -> None:
    product = db.query(Product).filter(Product.id == payload["product_id"]).first()
    name = product.name if product else "Unknown product"
    # A lookup failure raises, which sends the event down the retry path instead of
    # acking it with nobody notified.
    for email in get_notification_recipients():
        send_email_job(
            to_email=email,
            subject=f"StockPilot: {name} is low on stock",
            body=(
                f"{name} has dropped to {payload.get('available_quantity', payload['on_hand_quantity'])} "
                f"available units (on hand: {payload['on_hand_quantity']}, "
                f"reorder point: {payload['reorder_point']})."
            ),
        )


def handle_po_approved(payload: dict, db: Session) -> None:
    for email in get_notification_recipients():
        send_email_job(
            to_email=email,
            subject="StockPilot: Purchase order approved",
            body=f"Purchase order {payload['po_id']} has been approved and is ready to order.",
        )


HANDLERS: dict[str, Callable[[dict, Session], None]] = {
    "StockLow": handle_stock_low,
    "PurchaseOrderApproved": handle_po_approved,
}


def process_event(event: dict) -> None:
    handler = HANDLERS.get(event.get("event_type", ""))
    if handler is None:
        return
    db = SessionLocal()
    try:
        handler(event, db)
    finally:
        db.close()


def start_consumer() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    declare_consumer_topology(channel, QUEUE_NAME, BOUND_EVENT_TYPES)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=partial(handle_delivery, queue_name=QUEUE_NAME, process=process_event),
    )
    logger.info("Notification consumer listening for: %s", BOUND_EVENT_TYPES)
    channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_consumer()
