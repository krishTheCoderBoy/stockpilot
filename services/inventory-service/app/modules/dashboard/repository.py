from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.inventory.models import Inventory
from app.modules.inventory_movements.models import InventoryMovement, MovementType
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse


class DashboardRepository:
    """Read-only aggregates over inventory-owned tables."""

    def __init__(self, db: Session):
        self.db = db

    def count_active_products(self) -> int:
        return self.db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0

    def total_inventory_value(self) -> Decimal:
        # On-hand, not available: reserved stock is still owned and still has a cost.
        return (
            self.db.query(func.sum(Inventory.on_hand_quantity * Inventory.average_unit_cost)).scalar()
            or Decimal("0")
        )

    def count_low_stock(self) -> int:
        return (
            self.db.query(func.count(Inventory.id))
            .join(Product, Product.id == Inventory.product_id)
            .filter(Inventory.available_quantity <= Product.reorder_point)
            .scalar()
            or 0
        )

    def movement_totals_by_period(self, since: datetime) -> list[tuple[str, MovementType, Decimal]]:
        period = func.to_char(InventoryMovement.created_at, "YYYY-MM")
        return (
            self.db.query(period, InventoryMovement.movement_type, func.sum(InventoryMovement.quantity))
            .filter(InventoryMovement.created_at >= since)
            .group_by(period, InventoryMovement.movement_type)
            .order_by(period)
            .all()
        )

    def recent_movements(self, limit: int) -> list[tuple[InventoryMovement, str, str]]:
        return (
            self.db.query(InventoryMovement, Product.name, Warehouse.name)
            .join(Product, Product.id == InventoryMovement.product_id)
            .join(Warehouse, Warehouse.id == InventoryMovement.warehouse_id)
            .order_by(InventoryMovement.created_at.desc())
            .limit(limit)
            .all()
        )
