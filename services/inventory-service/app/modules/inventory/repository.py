from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.inventory.models import Inventory
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_and_warehouse(
        self, product_id, warehouse_id, for_update: bool = False
    ) -> Inventory | None:
        query = self.db.query(Inventory).filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
        if for_update:
            # Serialises concurrent stock changes on one row; without it two requests can
            # both pass the availability guard and oversell.
            query = query.with_for_update()
        return query.first()

    def list_by_product(self, product_id) -> list[Inventory]:
        return self.db.query(Inventory).filter(Inventory.product_id == product_id).all()

    def list_by_warehouse(self, warehouse_id) -> list[Inventory]:
        return self.db.query(Inventory).filter(Inventory.warehouse_id == warehouse_id).all()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Inventory]:
        return self.db.query(Inventory).offset(skip).limit(limit).all()

    def create(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.flush()
        return inventory

    def get_or_create(self, product_id, warehouse_id, for_update: bool = False) -> Inventory:
        existing = self.get_by_product_and_warehouse(product_id, warehouse_id, for_update=for_update)
        if existing:
            return existing
        return self.create(Inventory(product_id=product_id, warehouse_id=warehouse_id))

    def list_low_stock(self, limit: int = 10) -> list[tuple[str, Decimal, Decimal]]:
        """(product name, available, reorder point) for every stock row whose available stock is at or below its reorder point."""
        return (
            self.db.query(Product.name, Inventory.available_quantity, Product.reorder_point)
            .join(Product, Product.id == Inventory.product_id)
            .filter(Inventory.available_quantity <= Product.reorder_point)
            .limit(limit)
            .all()
        )

    def list_low_stock_rows(self, limit: int = 50) -> list[tuple[Inventory, Product, Warehouse]]:
        """Stock rows whose available quantity is at or below the product's reorder point."""
        return (
            self.db.query(Inventory, Product, Warehouse)
            .join(Product, Product.id == Inventory.product_id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .filter(Product.is_active.is_(True), Inventory.available_quantity <= Product.reorder_point)
            .order_by((Inventory.available_quantity - Product.reorder_point).asc())
            .limit(limit)
            .all()
        )
