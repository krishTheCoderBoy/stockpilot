from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.inventory.models import Inventory
from app.modules.purchase_orders.models import PurchaseOrder, POStatus
from app.modules.inventory_movements.models import InventoryMovement, MovementType
from app.modules.warehouses.models import Warehouse

PENDING_PO_STATUSES = {POStatus.DRAFT, POStatus.SUBMITTED, POStatus.APPROVED, POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED}
INCREASE_TYPES = {MovementType.RECEIVE, MovementType.ADJUSTMENT_INCREASE, MovementType.TRANSFER_IN}
DECREASE_TYPES = {MovementType.ISSUE, MovementType.ADJUSTMENT_DECREASE, MovementType.TRANSFER_OUT}


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> dict:
        total_products = self.db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0

        total_inventory_value = (
            self.db.query(func.sum(Inventory.on_hand_quantity * Inventory.average_unit_cost)).scalar()
            or Decimal("0")
        )

        pending_purchase_orders = (
            self.db.query(func.count(PurchaseOrder.id))
            .filter(PurchaseOrder.status.in_(PENDING_PO_STATUSES))
            .scalar()
            or 0
        )

        low_stock_items = (
            self.db.query(func.count(Inventory.id))
            .join(Product, Product.id == Inventory.product_id)
            .filter(Inventory.on_hand_quantity <= Product.reorder_point)
            .scalar()
            or 0
        )

        return {
            "total_products": total_products,
            "total_inventory_value": total_inventory_value,
            "pending_purchase_orders": pending_purchase_orders,
            "low_stock_items": low_stock_items,
        }

    def get_inventory_trend(self, months: int = 6) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=30 * months)

        rows = (
            self.db.query(
                func.to_char(InventoryMovement.created_at, "YYYY-MM").label("period"),
                InventoryMovement.movement_type,
                func.sum(InventoryMovement.quantity).label("total"),
            )
            .filter(InventoryMovement.created_at >= since)
            .group_by("period", InventoryMovement.movement_type)
            .order_by("period")
            .all()
        )

        buckets: dict[str, dict] = {}
        for period, movement_type, total in rows:
            bucket = buckets.setdefault(period, {"period": period, "stock_in": Decimal("0"), "stock_out": Decimal("0")})
            if movement_type in INCREASE_TYPES:
                bucket["stock_in"] += total
            elif movement_type in DECREASE_TYPES:
                bucket["stock_out"] += total

        return sorted(buckets.values(), key=lambda b: b["period"])

    def get_recent_movements(self, limit: int = 5) -> list[dict]:
        rows = (
            self.db.query(InventoryMovement, Product.name, Warehouse.name)
            .join(Product, Product.id == InventoryMovement.product_id)
            .join(Warehouse, Warehouse.id == InventoryMovement.warehouse_id)
            .order_by(InventoryMovement.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "product_name": product_name,
                "movement_type": movement.movement_type,
                "quantity": movement.quantity,
                "warehouse_name": warehouse_name,
                "created_at": movement.created_at,
            }
            for movement, product_name, warehouse_name in rows
        ]