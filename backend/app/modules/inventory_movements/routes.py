import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.modules.users.models import User, UserRole
from app.modules.inventory_movements.schemas import MovementCreate, MovementOut, TransferCreate
from app.modules.inventory_movements.service import MovementService

router = APIRouter(prefix="/inventory-movements", tags=["inventory-movements"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER)
READ_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)


@router.post("/", response_model=MovementOut, status_code=201)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = MovementService(db)
    return service.create_movement(payload, performed_by=current_user.id)


@router.post("/transfer", response_model=list[MovementOut], status_code=201)
def transfer_stock(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = MovementService(db)
    out_movement, in_movement = service.transfer_stock(payload, performed_by=current_user.id)
    return [out_movement, in_movement]


@router.get("/", response_model=list[MovementOut])
def list_movements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_all(skip, limit)


@router.get("/product/{product_id}", response_model=list[MovementOut])
def get_movements_by_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_by_product(product_id)


@router.get("/warehouse/{warehouse_id}", response_model=list[MovementOut])
def get_movements_by_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_by_warehouse(warehouse_id)