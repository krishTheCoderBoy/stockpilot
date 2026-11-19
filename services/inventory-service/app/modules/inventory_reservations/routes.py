import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, require_role
from app.modules.inventory_reservations.models import ReservationStatus
from app.modules.inventory_reservations.schemas import ReservationCreate, ReservationOut
from app.modules.inventory_reservations.service import ReservationService

# Own prefix instead of /inventory/reservations: /inventory/{product_id}/{warehouse_id}
# would otherwise capture GET /inventory/reservations/{id}.
router = APIRouter(prefix="/stock-reservations", tags=["stock-reservations"])

READ_ROLES = ("ADMIN", "INVENTORY_MANAGER", "PROCUREMENT_MANAGER")
WRITE_ROLES = ("ADMIN", "INVENTORY_MANAGER")


@router.post("/", response_model=ReservationOut, status_code=201)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*WRITE_ROLES)),
):
    service = ReservationService(db)
    return service.reserve(payload, current_user.id)


@router.get("/", response_model=list[ReservationOut])
def list_reservations(
    product_id: uuid.UUID | None = None,
    warehouse_id: uuid.UUID | None = None,
    status: ReservationStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = ReservationService(db)
    return service.list_reservations(product_id, warehouse_id, status, skip, limit)


@router.get("/{reservation_id}", response_model=ReservationOut)
def get_reservation(
    reservation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = ReservationService(db)
    return service.get_reservation(reservation_id)


@router.post("/{reservation_id}/release", response_model=ReservationOut)
def release_reservation(
    reservation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*WRITE_ROLES)),
):
    service = ReservationService(db)
    return service.release(reservation_id)
