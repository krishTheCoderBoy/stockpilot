import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.inventory_batches.schemas import BatchOut
from app.modules.inventory_batches.service import BatchService

router = APIRouter(prefix="/inventory-batches", tags=["inventory-batches"])

READ_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)


@router.get("/product/{product_id}", response_model=list[BatchOut])
def get_batches_by_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = BatchService(db)
    return service.list_by_product(product_id)


@router.get("/expiring", response_model=list[BatchOut])
def get_expiring_batches(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = BatchService(db)
    return service.list_expiring(days)