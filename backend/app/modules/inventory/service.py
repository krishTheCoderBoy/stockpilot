from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.inventory.models import Inventory
from app.modules.inventory.repository import InventoryRepository


class InventoryService:
    def __init__(self, db: Session):
        self.repo = InventoryRepository(db)

    def get_inventory(self, product_id, warehouse_id) -> Inventory:
        inventory = self.repo.get_by_product_and_warehouse(product_id, warehouse_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No inventory record for this product at this warehouse",
            )
        return inventory

    def list_by_product(self, product_id) -> list[Inventory]:
        return self.repo.list_by_product(product_id)

    def list_by_warehouse(self, warehouse_id) -> list[Inventory]:
        return self.repo.list_by_warehouse(warehouse_id)

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Inventory]:
        return self.repo.list_all(skip, limit)