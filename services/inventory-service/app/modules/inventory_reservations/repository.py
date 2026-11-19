import uuid

from sqlalchemy.orm import Session

from app.modules.inventory_reservations.models import ReservationStatus, StockReservation


class ReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reservation_id: uuid.UUID, for_update: bool = False) -> StockReservation | None:
        query = self.db.query(StockReservation).filter(StockReservation.id == reservation_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def list_all(
        self,
        product_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        status: ReservationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[StockReservation]:
        query = self.db.query(StockReservation)
        if product_id is not None:
            query = query.filter(StockReservation.product_id == product_id)
        if warehouse_id is not None:
            query = query.filter(StockReservation.warehouse_id == warehouse_id)
        if status is not None:
            query = query.filter(StockReservation.status == status)
        return query.order_by(StockReservation.created_at.desc()).offset(skip).limit(limit).all()

    def add(self, reservation: StockReservation) -> StockReservation:
        self.db.add(reservation)
        self.db.flush()
        return reservation
