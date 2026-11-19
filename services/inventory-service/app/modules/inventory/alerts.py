import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.events.publisher import publish_event
from app.core.events.schemas import StockLow
from app.modules.inventory.models import Inventory
from app.modules.products.repository import ProductRepository


def publish_stock_low_if_needed(db: Session, inventory: Inventory) -> None:
    """Emit StockLow when *available* stock is at or below the reorder point.

    Available, not on-hand, because reserved stock cannot be issued: a warehouse with
    plenty on the shelf but everything promised is effectively out of stock.
    """
    product = ProductRepository(db).get_by_id(inventory.product_id)
    if product and inventory.available_quantity <= product.reorder_point:
        publish_event(StockLow(
            event_id=uuid.uuid4(),
            occurred_at=datetime.now(timezone.utc),
            product_id=inventory.product_id,
            warehouse_id=inventory.warehouse_id,
            on_hand_quantity=inventory.on_hand_quantity,
            available_quantity=inventory.available_quantity,
            reorder_point=product.reorder_point,
        ))
