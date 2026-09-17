import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.inventory.schemas import InventoryOut
from app.modules.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])

ALL_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)


@router.get("/", response_model=list[InventoryOut])
def list_inventory(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*ALL_ROLES)),
):
    service = InventoryService(db)
    return service.list_all(skip, limit)


@router.get("/product/{product_id}", response_model=list[InventoryOut])
def get_inventory_by_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*ALL_ROLES)),
):
    service = InventoryService(db)
    return service.list_by_product(product_id)


@router.get("/warehouse/{warehouse_id}", response_model=list[InventoryOut])
def get_inventory_by_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*ALL_ROLES)),
):
    service = InventoryService(db)
    return service.list_by_warehouse(warehouse_id)


@router.get("/{product_id}/{warehouse_id}", response_model=InventoryOut)
def get_inventory(
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*ALL_ROLES)),
):
    service = InventoryService(db)
    return service.get_inventory(product_id, warehouse_id)