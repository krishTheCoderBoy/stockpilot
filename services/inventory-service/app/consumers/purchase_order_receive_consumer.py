"""Apply receipt events emitted by the procurement service."""
import json
import logging
import pika
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.database import SessionLocal
from app.core.events.publisher import EXCHANGE_NAME
from app.modules.inventory_movements.service import MovementService
logger=logging.getLogger(__name__)
QUEUE_NAME="inventory.purchase-order-receipts"
EVENT_NAME="ReceivePurchaseOrderItems"
def process_event(event: dict) -> None:
    event_id=str(event["event_id"]); key=f"processed_event:{event_id}"
    try:
        if redis_client.get(key): return
    except Exception:
        # Continue during Redis outages; RabbitMQ remains the delivery mechanism.
        logger.exception("Receipt deduplication cache unavailable")
    db=SessionLocal()
    try:
        movements=MovementService(db)
        for item in event["items"]:
            movements.record_receive(product_id=item["product_id"],warehouse_id=event["warehouse_id"],quantity=item["quantity"],unit_cost=item["unit_cost"],reference_id=event["po_id"],performed_by=event["performed_by"],notes=f"Receipt against {event['po_number']}")
        db.commit()
        try: redis_client.set(key,"1",ex=86400)
        except Exception: logger.exception("Could not record receipt deduplication key")
    except Exception:
        db.rollback(); raise
    finally: db.close()
def on_message(channel,method,properties,body):
    try:
        process_event(json.loads(body)); channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.exception("Could not apply procurement receipt event")
        channel.basic_nack(delivery_tag=method.delivery_tag,requeue=True)
def start_consumer():
    connection=pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url)); channel=connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME,exchange_type="topic",durable=True)
    channel.queue_declare(queue=QUEUE_NAME,durable=True); channel.queue_bind(exchange=EXCHANGE_NAME,queue=QUEUE_NAME,routing_key=EVENT_NAME)
    channel.basic_qos(prefetch_count=1); channel.basic_consume(queue=QUEUE_NAME,on_message_callback=on_message)
    logger.info("Listening for %s",EVENT_NAME); channel.start_consuming()
if __name__=="__main__": start_consumer()
