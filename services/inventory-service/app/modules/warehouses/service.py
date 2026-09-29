from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.warehouses.models import Warehouse
from app.modules.warehouses.repository import WarehouseRepository
from app.modules.warehouses.schemas import WarehouseCreate, WarehouseUpdate


class WarehouseService:
    def __init__(self, db: Session):
        self.repo = WarehouseRepository(db)

    def create_warehouse(self, payload: WarehouseCreate) -> Warehouse:
        if self.repo.get_by_code(payload.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse code already exists",
            )
        warehouse = Warehouse(**payload.model_dump())
        return self.repo.create(warehouse)

    def get_warehouse(self, warehouse_id) -> Warehouse:
        warehouse = self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
            )
        return warehouse

    def list_warehouses(self, skip: int = 0, limit: int = 50) -> list[Warehouse]:
        return self.repo.list_all(skip, limit)

    def update_warehouse(self, warehouse_id, payload: WarehouseUpdate) -> Warehouse:
        warehouse = self.get_warehouse(warehouse_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(warehouse, field, value)
        return self.repo.update(warehouse)