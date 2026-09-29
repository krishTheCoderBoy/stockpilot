from sqlalchemy.orm import Session

from app.modules.warehouses.models import Warehouse


class WarehouseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, warehouse_id) -> Warehouse | None:
        return self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

    def get_by_code(self, code: str) -> Warehouse | None:
        return self.db.query(Warehouse).filter(Warehouse.code == code).first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Warehouse]:
        return self.db.query(Warehouse).offset(skip).limit(limit).all()

    def create(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse

    def update(self, warehouse: Warehouse) -> Warehouse:
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse