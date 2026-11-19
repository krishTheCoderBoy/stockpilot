from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.inventory_movements.models import MovementType


class DashboardSummary(BaseModel):
    total_products: int
    total_inventory_value: Decimal
    # None when procurement-service is unreachable, so the card can show "unavailable"
    # instead of a misleading 0.
    pending_purchase_orders: int | None
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
