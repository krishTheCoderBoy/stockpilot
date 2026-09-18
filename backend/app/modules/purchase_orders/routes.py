import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import User, UserRole
from app.modules.purchase_orders.schemas import PurchaseOrderCreate, PurchaseOrderOut
from app.modules.purchase_orders.service import PurchaseOrderService
from app.modules.purchase_orders.schemas import ReceiveRequest

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.PROCUREMENT_MANAGER)
READ_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)
APPROVE_ROLES = (UserRole.ADMIN,)


@router.post("/", response_model=PurchaseOrderOut, status_code=201)
def create_po(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.create_po(payload, created_by=current_user.id)


@router.get("/", response_model=list[PurchaseOrderOut])
def list_pos(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*READ_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.list_pos(skip, limit)


@router.get("/{po_id}", response_model=PurchaseOrderOut)
def get_po(
    po_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*READ_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.get_po(po_id)


@router.post("/{po_id}/submit", response_model=PurchaseOrderOut)
def submit_po(
    po_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.submit(po_id)


@router.post("/{po_id}/approve", response_model=PurchaseOrderOut)
def approve_po(
    po_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*APPROVE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.approve(po_id, approved_by=current_user.id)


@router.post("/{po_id}/mark-ordered", response_model=PurchaseOrderOut)
def mark_ordered(
    po_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.mark_ordered(po_id)


@router.post("/{po_id}/close", response_model=PurchaseOrderOut)
def close_po(
    po_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.close(po_id)

@router.post("/{po_id}/receive", response_model=PurchaseOrderOut)
def receive_po(
    po_id: uuid.UUID,
    payload: ReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*WRITE_ROLES)),
):
    service = PurchaseOrderService(db)
    return service.receive(po_id, payload, performed_by=current_user.id)