import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.warehouses.schemas import WarehouseCreate, WarehouseOut, WarehouseUpdate
from app.modules.warehouses.service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.post("/", response_model=WarehouseOut, status_code=201)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    service = WarehouseService(db)
    return service.create_warehouse(payload)


@router.get("/", response_model=list[WarehouseOut])
def list_warehouses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)
    ),
):
    service = WarehouseService(db)
    return service.list_warehouses(skip, limit)


@router.get("/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)
    ),
):
    service = WarehouseService(db)
    return service.get_warehouse(warehouse_id)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(
    warehouse_id: uuid.UUID,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    service = WarehouseService(db)
    return service.update_warehouse(warehouse_id, payload)