from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel

from app.modules.inventory_movements.models import MovementType


class DashboardSummary(BaseModel):
    total_products: int
    total_inventory_value: Decimal
    pending_purchase_orders: int
    low_stock_items: int


class TrendPoint(BaseModel):
    period: str
    stock_in: Decimal
    stock_out: Decimal


class RecentMovementOut(BaseModel):
    product_name: str
    movement_type: MovementType
    quantity: Decimal
    warehouse_name: str
    created_at: datetime

class NotificationOut(BaseModel):
    type: str
    message: str