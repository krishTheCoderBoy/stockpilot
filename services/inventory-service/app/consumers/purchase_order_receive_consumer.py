"""Apply receipt events emitted by the procurement service."""
import logging
import uuid
from decimal import Decimal
from functools import partial

import pika

from app.consumers.retry import declare_consumer_topology, handle_delivery
from app.core.cache import invalidate_cache
from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.inventory_movements.service import MovementService

logger = logging.getLogger(__name__)

QUEUE_NAME = "inventory.purchase-order-receipts"
EVENT_NAME = "ReceivePurchaseOrderItems"


def process_event(event: dict) -> None:
    db = SessionLocal()
    try:
        movements = MovementService(db)
        for item in event["items"]:
            # The event is JSON, so quantities and IDs arrive as strings; the movement
            # service compares and does arithmetic on them, so restore the real types.
            movements.record_receive(
                product_id=uuid.UUID(item["product_id"]),
                warehouse_id=uuid.UUID(event["warehouse_id"]),
                quantity=Decimal(item["quantity"]),
                unit_cost=Decimal(item["unit_cost"]) if item.get("unit_cost") is not None else None,
                reference_id=uuid.UUID(event["po_id"]),
                performed_by=uuid.UUID(event["performed_by"]),
                notes=f"Receipt against {event['po_number']}",
            )
        # One commit for every line, so a partial failure never leaves half a receipt applied.
        db.commit()
        invalidate_cache("dashboard:summary")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_consumer() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    declare_consumer_topology(channel, QUEUE_NAME, [EVENT_NAME])
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=partial(handle_delivery, queue_name=QUEUE_NAME, process=process_event),
    )
    logger.info("Listening for %s", EVENT_NAME)
    channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_consumer()
