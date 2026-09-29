from datetime import date

from sqlalchemy.orm import Session

from app.modules.inventory_batches.models import InventoryBatch


class BatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, batch: InventoryBatch) -> InventoryBatch:
        self.db.add(batch)
        self.db.flush()
        return batch

    def get_consumable_batches(self, product_id, warehouse_id):
        """FIFO-by-expiry: batches with remaining stock, soonest expiry first (NULLs last)."""
        return (
            self.db.query(InventoryBatch)
            .filter(
                InventoryBatch.product_id == product_id,
                InventoryBatch.warehouse_id == warehouse_id,
                InventoryBatch.remaining_quantity > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc().nullslast())
            .all()
        )

    def list_expiring(self, cutoff_date: date):
        return (
            self.db.query(InventoryBatch)
            .filter(
                InventoryBatch.expiry_date.isnot(None),
                InventoryBatch.expiry_date <= cutoff_date,
                InventoryBatch.remaining_quantity > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc())
            .all()
        )

    def list_by_product(self, product_id):
        return (
            self.db.query(InventoryBatch)
            .filter(InventoryBatch.product_id == product_id)
            .order_by(InventoryBatch.expiry_date.asc().nullslast())
            .all()
        )