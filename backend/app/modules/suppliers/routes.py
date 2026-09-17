import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.suppliers.schemas import SupplierCreate, SupplierOut, SupplierUpdate
from app.modules.suppliers.service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.PROCUREMENT_MANAGER)
READ_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)


@router.post("/", response_model=SupplierOut, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*WRITE_ROLES)),
):
    service = SupplierService(db)
    return service.create_supplier(payload)


@router.get("/", response_model=list[SupplierOut])
def list_suppliers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = SupplierService(db)
    return service.list_suppliers(skip, limit)


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = SupplierService(db)
    return service.get_supplier(supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: uuid.UUID,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*WRITE_ROLES)),
):
    service = SupplierService(db)
    return service.update_supplier(supplier_id, payload)