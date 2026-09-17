import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory_movements.models import InventoryMovement, MovementType, ReferenceType
from app.modules.inventory_movements.repository import MovementRepository

INCREASE_TYPES = {MovementType.RECEIVE, MovementType.ADJUSTMENT_INCREASE, MovementType.TRANSFER_IN}
DECREASE_TYPES = {MovementType.ISSUE, MovementType.ADJUSTMENT_DECREASE, MovementType.TRANSFER_OUT}


class MovementService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.movement_repo = MovementRepository(db)

    def _apply_single_movement(
        self,
        product_id,
        warehouse_id,
        movement_type: MovementType,
        quantity: Decimal,
        unit_cost: Decimal | None,
        reference_type: ReferenceType,
        reference_id,
        performed_by,
        notes: str | None,
    ) -> InventoryMovement:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive"
            )

        inventory = self.inventory_repo.get_or_create(product_id, warehouse_id)

        if movement_type in INCREASE_TYPES:
            if movement_type == MovementType.RECEIVE and unit_cost is not None:
                old_value = inventory.on_hand_quantity * inventory.average_unit_cost
                new_value = quantity * unit_cost
                new_total_qty = inventory.on_hand_quantity + quantity
                inventory.average_unit_cost = (
                    (old_value + new_value) / new_total_qty if new_total_qty > 0 else unit_cost
                )
            inventory.on_hand_quantity += quantity

        elif movement_type in DECREASE_TYPES:
            if inventory.on_hand_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient stock for this movement",
                )
            inventory.on_hand_quantity -= quantity

        inventory.last_movement_at = datetime.now(timezone.utc)

        movement = InventoryMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            notes=notes,
        )
        self.movement_repo.add(movement)
        return movement

    def create_movement(self, payload, performed_by) -> InventoryMovement:
        try:
            movement = self._apply_single_movement(
                product_id=payload.product_id,
                warehouse_id=payload.warehouse_id,
                movement_type=payload.movement_type,
                quantity=payload.quantity,
                unit_cost=payload.unit_cost,
                reference_type=ReferenceType.MANUAL,
                reference_id=None,
                performed_by=performed_by,
                notes=payload.notes,
            )
            self.db.commit()
            self.db.refresh(movement)
            return movement
        except Exception:
            self.db.rollback()
            raise

    def transfer_stock(self, payload, performed_by) -> tuple[InventoryMovement, InventoryMovement]:
        """Moves stock between warehouses as two linked movements in ONE transaction."""
        if payload.source_warehouse_id == payload.destination_warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination warehouses must differ",
            )
        transfer_id = uuid.uuid4()
        try:
            out_movement = self._apply_single_movement(
                product_id=payload.product_id,
                warehouse_id=payload.source_warehouse_id,
                movement_type=MovementType.TRANSFER_OUT,
                quantity=payload.quantity,
                unit_cost=None,
                reference_type=ReferenceType.TRANSFER,
                reference_id=transfer_id,
                performed_by=performed_by,
                notes=payload.notes,
            )
            in_movement = self._apply_single_movement(
                product_id=payload.product_id,
                warehouse_id=payload.destination_warehouse_id,
                movement_type=MovementType.TRANSFER_IN,
                quantity=payload.quantity,
                unit_cost=None,
                reference_type=ReferenceType.TRANSFER,
                reference_id=transfer_id,
                performed_by=performed_by,
                notes=payload.notes,
            )
            self.db.commit()
            self.db.refresh(out_movement)
            self.db.refresh(in_movement)
            return out_movement, in_movement
        except Exception:
            self.db.rollback()
            raise

    def list_by_product(self, product_id, skip: int = 0, limit: int = 100):
        return self.movement_repo.list_by_product(product_id, skip, limit)

    def list_by_warehouse(self, warehouse_id, skip: int = 0, limit: int = 100):
        return self.movement_repo.list_by_warehouse(warehouse_id, skip, limit)

    def list_all(self, skip: int = 0, limit: int = 100):
        return self.movement_repo.list_all(skip, limit)