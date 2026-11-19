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

    def list_low_stock(self, limit: int = 50) -> list[dict]:
        return [
            {
                "product_id": product.id,
                "sku": product.sku,
                "product_name": product.name,
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "on_hand_quantity": inventory.on_hand_quantity,
                "reserved_quantity": inventory.reserved_quantity,
                "available_quantity": inventory.available_quantity,
                "reorder_point": product.reorder_point,
            }
            for inventory, product, warehouse in self.repo.list_low_stock_rows(limit)
        ]
