from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import Date, cast, func, literal_column, or_, select
from sqlalchemy.orm import Session

from app.modules.inventory_movements.models import InventoryMovement, MovementType
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse


class MovementRepository:
    """Append-only. No update/delete methods exist on purpose — the ledger is immutable."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, movement: InventoryMovement) -> None:
        self.db.add(movement)

    def list_by_product(self, product_id, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .filter(InventoryMovement.product_id == product_id)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_warehouse(self, warehouse_id, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .filter(InventoryMovement.warehouse_id == warehouse_id)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(InventoryMovement)
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, query: str, limit: int = 20) -> list[InventoryMovement]:
        """Movements whose notes match, or whose product or warehouse matches.

        Product and warehouse names already have indexed search vectors, so they are
        matched through subqueries instead of copying their text into the (append-only,
        large) movement table.
        """
        ts_query = func.websearch_to_tsquery("english", query)
        matching_products = select(Product.id).where(Product.search_vector.op("@@")(ts_query))
        matching_warehouses = select(Warehouse.id).where(Warehouse.search_vector.op("@@")(ts_query))
        return (
            self.db.query(InventoryMovement)
            .filter(
                or_(
                    InventoryMovement.search_vector.op("@@")(ts_query),
                    InventoryMovement.product_id.in_(matching_products),
                    InventoryMovement.warehouse_id.in_(matching_warehouses),
                )
            )
            # Notes matches rank first; product/warehouse-only matches have rank 0 and
            # fall back to newest first.
            .order_by(
                func.ts_rank(InventoryMovement.search_vector, ts_query).desc(),
                InventoryMovement.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

    def demand_by_bucket(
        self,
        date_from: date,
        date_to: date,
        bucket: Literal["day", "week"],
        product_ids: list[UUID] | None = None,
        warehouse_id: UUID | None = None,
        limit: int = 200_000,
    ) -> list[tuple[UUID, date, Decimal, int]]:
        """Outbound demand per (product, bucket), aggregated in SQL.

        Only ISSUE counts as demand. TRANSFER_OUT just moves stock between our own
        warehouses, DAMAGED is a write-off and ADJUSTMENT_DECREASE is a count correction;
        none of them reflects what customers or production actually wanted, and counting
        them would teach a forecaster to reorder for losses and transfers.
        """
        # The bucket is whitelisted, then inlined: a bound parameter would get a different
        # placeholder in SELECT and GROUP BY, and Postgres would reject the grouping.
        unit = literal_column({"day": "'day'", "week": "'week'"}[bucket])
        # UTC on purpose, so buckets do not shift with the database session time zone.
        bucket_start = cast(func.date_trunc(unit, func.timezone("UTC", InventoryMovement.created_at)), Date)
        start = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

        query = (
            self.db.query(
                InventoryMovement.product_id,
                bucket_start.label("bucket_start"),
                func.sum(InventoryMovement.quantity),
                func.count(InventoryMovement.id),
            )
            .filter(
                InventoryMovement.movement_type == MovementType.ISSUE,
                InventoryMovement.created_at >= start,
                InventoryMovement.created_at < end,
            )
        )
        if product_ids:
            query = query.filter(InventoryMovement.product_id.in_(product_ids))
        if warehouse_id is not None:
            query = query.filter(InventoryMovement.warehouse_id == warehouse_id)
        return (
            query.group_by(InventoryMovement.product_id, bucket_start)
            .order_by(InventoryMovement.product_id, bucket_start)
            .limit(limit)
            .all()
        )
