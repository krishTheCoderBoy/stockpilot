import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InventoryOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    on_hand_quantity: Decimal
    reserved_quantity: Decimal
    # Read from Inventory.available_quantity so there is one definition of "available".
    available_quantity: Decimal
    average_unit_cost: Decimal
    safety_stock_override: Decimal | None
    last_movement_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LowStockOut(BaseModel):
    product_id: uuid.UUID
    sku: str
    product_name: str
    warehouse_id: uuid.UUID
    warehouse_name: str
    on_hand_quantity: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    reorder_point: Decimal
