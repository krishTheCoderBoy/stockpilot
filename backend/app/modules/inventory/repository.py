from sqlalchemy.orm import Session

from app.modules.inventory.models import Inventory


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_and_warehouse(self, product_id, warehouse_id) -> Inventory | None:
        return (
            self.db.query(Inventory)
            .filter(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
            .first()
        )

    def list_by_product(self, product_id) -> list[Inventory]:
        return self.db.query(Inventory).filter(Inventory.product_id == product_id).all()

    def list_by_warehouse(self, warehouse_id) -> list[Inventory]:
        return self.db.query(Inventory).filter(Inventory.warehouse_id == warehouse_id).all()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Inventory]:
        return self.db.query(Inventory).offset(skip).limit(limit).all()

    def create(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    def get_or_create(self, product_id, warehouse_id) -> Inventory:
        existing = self.get_by_product_and_warehouse(product_id, warehouse_id)
        if existing:
            return existing
        return self.create(Inventory(product_id=product_id, warehouse_id=warehouse_id))