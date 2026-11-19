import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import invalidate_cache
from app.modules.inventory.alerts import publish_stock_low_if_needed
from app.modules.inventory.models import Inventory
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory_reservations.models import ReservationStatus, StockReservation
from app.modules.inventory_reservations.repository import ReservationRepository
from app.modules.inventory_reservations.schemas import ReservationCreate

ALLOWED_TRANSITIONS: dict[ReservationStatus, set[ReservationStatus]] = {
    ReservationStatus.ACTIVE: {ReservationStatus.RELEASED, ReservationStatus.FULFILLED},
    ReservationStatus.RELEASED: set(),
    ReservationStatus.FULFILLED: set(),
}

# Lock order everywhere is inventory row first, then reservation row, so a release and an
# issue touching the same stock can never wait on each other.


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReservationRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def _transition(self, reservation: StockReservation, new_status: ReservationStatus) -> None:
        if new_status not in ALLOWED_TRANSITIONS.get(reservation.status, set()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition reservation from {reservation.status.value} to {new_status.value}",
            )
        reservation.status = new_status

    def get_reservation(self, reservation_id: uuid.UUID) -> StockReservation:
        reservation = self.repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        return reservation

    def list_reservations(
        self,
        product_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        reservation_status: ReservationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[StockReservation]:
        return self.repo.list_all(product_id, warehouse_id, reservation_status, skip, limit)

    def reserve(self, payload: ReservationCreate, created_by: str) -> StockReservation:
        if payload.quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive")
        try:
            inventory = self.inventory_repo.get_by_product_and_warehouse(
                payload.product_id, payload.warehouse_id, for_update=True
            )
            if inventory is None or inventory.available_quantity < payload.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient available stock to reserve",
                )
            inventory.reserved_quantity += payload.quantity
            reservation = self.repo.add(StockReservation(
                **payload.model_dump(),
                status=ReservationStatus.ACTIVE,
                created_by=uuid.UUID(created_by),
            ))
            self.db.commit()
            self.db.refresh(reservation)
        except Exception:
            self.db.rollback()
            raise

        invalidate_cache("dashboard:summary")
        # After commit so a rolled-back reserve never announces a shortage that didn't happen.
        publish_stock_low_if_needed(self.db, inventory)
        return reservation

    def release(self, reservation_id: uuid.UUID) -> StockReservation:
        try:
            reservation = self.get_reservation(reservation_id)
            inventory = self.inventory_repo.get_by_product_and_warehouse(
                reservation.product_id, reservation.warehouse_id, for_update=True
            )
            # Re-read under lock: another request may have released or fulfilled it meanwhile.
            self.db.refresh(reservation, with_for_update=True)
            self._transition(reservation, ReservationStatus.RELEASED)
            if inventory is None or inventory.reserved_quantity < reservation.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Reserved stock is inconsistent with this reservation",
                )
            inventory.reserved_quantity -= reservation.quantity
            reservation.released_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(reservation)
        except Exception:
            self.db.rollback()
            raise
        invalidate_cache("dashboard:summary")
        return reservation

    # --- Called by MovementService inside its own transaction; neither method commits. ---

    def lock_for_fulfilment(
        self, reservation_id: uuid.UUID, product_id: uuid.UUID, warehouse_id: uuid.UUID, quantity: Decimal
    ) -> StockReservation:
        """Validate and lock a reservation an ISSUE intends to consume."""
        reservation = self.repo.get_by_id(reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
        if reservation.status != ReservationStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reservation is {reservation.status.value}, not ACTIVE",
            )
        if reservation.product_id != product_id or reservation.warehouse_id != warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation is for a different product or warehouse",
            )
        if quantity > reservation.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot issue more than the reserved quantity ({reservation.quantity})",
            )
        return reservation

    def complete_fulfilment(
        self, reservation: StockReservation, inventory: Inventory, issued_quantity: Decimal, movement_id: uuid.UUID
    ) -> None:
        self._transition(reservation, ReservationStatus.FULFILLED)
        # The whole hold ends; any unissued remainder returns to available.
        inventory.reserved_quantity -= reservation.quantity
        reservation.fulfilled_quantity = issued_quantity
        reservation.fulfillment_movement_id = movement_id
        reservation.released_at = datetime.now(timezone.utc)
