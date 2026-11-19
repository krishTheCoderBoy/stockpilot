import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role, get_current_user, CurrentUser
from app.modules.inventory_movements.schemas import DemandBucketOut, MovementCreate, MovementOut, TransferCreate
from app.modules.inventory_movements.service import MovementService

router = APIRouter(prefix="/inventory-movements", tags=["inventory-movements"])

WRITE_ROLES = ("ADMIN", "INVENTORY_MANAGER")
READ_ROLES = ("ADMIN", "INVENTORY_MANAGER", "PROCUREMENT_MANAGER")


@router.post("/", response_model=MovementOut, status_code=201)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*WRITE_ROLES)),
):
    service = MovementService(db)
    return service.create_movement(payload, performed_by=current_user.id)


@router.post("/transfer", response_model=list[MovementOut], status_code=201)
def transfer_stock(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*WRITE_ROLES)),
):
    service = MovementService(db)
    out_movement, in_movement = service.transfer_stock(payload, performed_by=current_user.id)
    return [out_movement, in_movement]


@router.get("/", response_model=list[MovementOut])
def list_movements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_all(skip, limit)


@router.get("/demand-history", response_model=list[DemandBucketOut])
def get_demand_history(
    product_id: uuid.UUID | None = None,
    # Repeatable (?product_ids=a&product_ids=b) so a caller can fetch a batch of products
    # in one request without pulling the whole ledger.
    product_ids: list[uuid.UUID] | None = Query(default=None),
    warehouse_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    bucket: Literal["day", "week"] = "day",
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    ids = list(product_ids or [])
    if product_id is not None:
        ids.append(product_id)
    return service.demand_history(date_from, date_to, bucket, ids or None, warehouse_id)


@router.get("/search", response_model=list[MovementOut])
def search_movements(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.search_movements(q, limit)


@router.get("/product/{product_id}", response_model=list[MovementOut])
def get_movements_by_product(
    product_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_by_product(product_id, skip, limit)


@router.get("/warehouse/{warehouse_id}", response_model=list[MovementOut])
def get_movements_by_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = MovementService(db)
    return service.list_by_warehouse(warehouse_id)