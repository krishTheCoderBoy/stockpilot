from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.cache import cache_result
from app.core.procurement_client import get_purchase_order_summary
from app.modules.dashboard.repository import DashboardRepository
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory_movements.service import DECREASE_TYPES, INCREASE_TYPES


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DashboardRepository(db)
        self.inventory_repo = InventoryRepository(db)

    # Cached under "dashboard:summary", which movements and reservations invalidate.
    # Pending POs are deliberately outside the cache: they come from another service, and
    # a failed lookup must not be served as null for the next minute.
    @cache_result(key="dashboard:summary", ttl=60)
    def _inventory_summary(self) -> dict:
        return {
            "total_products": self.repo.count_active_products(),
            "total_inventory_value": str(self.repo.total_inventory_value()),
            "low_stock_items": self.repo.count_low_stock(),
        }

    def get_summary(self, authorization: str | None = None) -> dict:
        summary = self._inventory_summary()
        po_summary = get_purchase_order_summary(authorization)
        return {
            **summary,
            "pending_purchase_orders": po_summary["pending_count"] if po_summary else None,
        }

    def get_inventory_trend(self, months: int = 6) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=30 * months)
        buckets: dict[str, dict] = {}
        for period, movement_type, total in self.repo.movement_totals_by_period(since):
            bucket = buckets.setdefault(
                period, {"period": period, "stock_in": Decimal("0"), "stock_out": Decimal("0")}
            )
            if movement_type in INCREASE_TYPES:
                bucket["stock_in"] += total
            elif movement_type in DECREASE_TYPES:
                bucket["stock_out"] += total
        return sorted(buckets.values(), key=lambda bucket: bucket["period"])

    def get_recent_movements(self, limit: int = 5) -> list[dict]:
        return [
            {
                "product_name": product_name,
                "movement_type": movement.movement_type,
                "quantity": movement.quantity,
                "warehouse_name": warehouse_name,
                "created_at": movement.created_at,
            }
            for movement, product_name, warehouse_name in self.repo.recent_movements(limit)
        ]

    def get_notifications(self, authorization: str | None = None) -> list[dict]:
        """Low-stock items plus POs awaiting approval.

        Called per request (with the user's token) and by the daily job (without one);
        the PO line is simply omitted when procurement is unreachable.
        """
        notifications: list[dict] = [
            {
                "type": "LOW_STOCK",
                "message": f"{name} is low on stock ({available} available, reorder at {reorder_point})",
            }
            for name, available, reorder_point in self.inventory_repo.list_low_stock(limit=10)
        ]
        po_summary = get_purchase_order_summary(authorization)
        if po_summary and po_summary["awaiting_approval_count"] > 0:
            notifications.append({
                "type": "PO_PENDING_APPROVAL",
                "message": f"{po_summary['awaiting_approval_count']} purchase order(s) awaiting approval",
            })
        return notifications
