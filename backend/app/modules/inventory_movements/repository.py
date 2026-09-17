from sqlalchemy.orm import Session

from app.modules.inventory_movements.models import InventoryMovement


class MovementRepository:
    """Append-only. No update/delete methods exist on purpose — the ledger is immutable."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, movement: InventoryMovement) -> None:
        self.db.add(movement)

    def list_by_product(self, product_id, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .filter(InventoryMovement.product_id == product_id)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_warehouse(self, warehouse_id, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .filter(InventoryMovement.warehouse_id == warehouse_id)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )