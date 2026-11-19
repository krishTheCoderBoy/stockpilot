"""Backfill ~6 months of daily ISSUE history so demand forecasting has something to learn from.

    python scripts/seed_demand_history.py --confirm [--days 190]

Run it only against a development database. It does three things to every existing
(product, warehouse) stock row:

  1. inserts one ISSUE movement per day, back-dated, with a per-product base level, a
     slow up/down trend, weekly seasonality (weekends quiet) and noise;
  2. inserts a RECEIVE movement whenever the simulated stock would fall below a floor, so
     the ledger stays physically possible (stock never goes negative);
  3. sets the stock row's on_hand to the simulated end state.

Step 3 changes current quantities, which is why --confirm is required. Back-dated rows do
not create inventory_batches, so batch totals will not match history; they only matter for
expiry alerts on stock received after this runs.

It refuses to run if ISSUE history older than 30 days already exists, so it cannot be
applied twice.
"""
import argparse
import math
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.modules.inventory.models import Inventory  # noqa: E402
# Imported only so every table is registered on Base.metadata: SQLAlchemy must resolve the
# foreign keys of inventory_movements (warehouses, batches, reservations) to order the insert.
from app.modules.inventory_batches.models import InventoryBatch  # noqa: E402,F401
from app.modules.inventory_reservations.models import StockReservation  # noqa: E402,F401
from app.modules.products.categories_models import ProductCategory  # noqa: E402,F401
from app.modules.warehouses.models import Warehouse  # noqa: E402,F401
from app.modules.inventory_movements.models import InventoryMovement, MovementType, ReferenceType  # noqa: E402
from app.modules.products.models import Product  # noqa: E402

# Monday..Sunday. Business-to-business demand: busy mid-week, quiet weekend.
WEEKDAY_FACTORS = (1.05, 1.15, 1.10, 1.00, 1.20, 0.55, 0.35)
CHUNK_SIZE = 2000


def _daily_demand(base: float, slope_per_day: float, day_index: int, weekday: int, rng: random.Random) -> int:
    trend = max(0.2, 1.0 + slope_per_day * day_index)
    expected = base * trend * WEEKDAY_FACTORS[weekday]
    # Gaussian noise around the expectation; some days legitimately sell nothing.
    value = rng.gauss(expected, max(0.8, expected * 0.25))
    return max(0, int(round(value)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=190, help="days of history to generate (default 190)")
    parser.add_argument("--confirm", action="store_true", help="required: acknowledges that stock quantities are rewritten")
    parser.add_argument("--seed", type=int, default=42, help="random seed, for repeatable data")
    args = parser.parse_args()
    if not args.confirm:
        sys.exit("Refusing to run without --confirm (this rewrites on_hand quantities). See --help.")

    rng = random.Random(args.seed)
    now = datetime.now(timezone.utc)
    first_day = (now - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)

    db = SessionLocal()
    try:
        old_cutoff = now - timedelta(days=30)
        already = (
            db.query(InventoryMovement.id)
            .filter(InventoryMovement.movement_type == MovementType.ISSUE, InventoryMovement.created_at < old_cutoff)
            .first()
        )
        if already:
            sys.exit("ISSUE history older than 30 days already exists; refusing to seed again.")

        rows = (
            db.query(Inventory, Product)
            .join(Product, Product.id == Inventory.product_id)
            .filter(Product.is_active.is_(True))
            .all()
        )
        if not rows:
            sys.exit("No stock rows found. Run scripts/seed.py first.")

        # One base level per product, shared across its warehouses and scaled per row.
        product_profile: dict[uuid.UUID, tuple[float, float]] = {}
        pending: list[InventoryMovement] = []
        issue_total = 0

        for inventory, product in rows:
            base, slope = product_profile.setdefault(
                product.id, (rng.uniform(3, 25), rng.uniform(-0.002, 0.004))
            )
            row_scale = rng.uniform(0.4, 1.0)
            stock = 0
            # Start high enough that the first weeks can be served; replenishment keeps it going.
            opening = int(base * row_scale * 30)
            stock = opening
            pending.append(_movement(inventory, MovementType.RECEIVE, opening, first_day, "Backfill opening stock", product))
            floor = max(int(base * row_scale * 10), 20)

            for day_index in range(args.days):
                day = first_day + timedelta(days=day_index)
                quantity = _daily_demand(base * row_scale, slope, day_index, day.weekday(), rng)
                if stock < floor:
                    top_up = int(math.ceil(base * row_scale * 28))
                    stock += top_up
                    pending.append(_movement(
                        inventory, MovementType.RECEIVE, top_up, day + timedelta(hours=6), "Backfill replenishment", product
                    ))
                if quantity > 0:
                    quantity = min(quantity, stock)
                if quantity > 0:
                    stock -= quantity
                    issue_total += 1
                    pending.append(_movement(
                        inventory, MovementType.ISSUE, quantity,
                        day + timedelta(hours=rng.randint(9, 18), minutes=rng.randint(0, 59)),
                        "Backfill demand", product,
                    ))

            inventory.on_hand_quantity = Decimal(stock)
            inventory.last_movement_at = now

            if len(pending) >= CHUNK_SIZE:
                db.bulk_save_objects(pending)
                pending.clear()

        if pending:
            db.bulk_save_objects(pending)
        db.commit()
        print(f"Seeded {issue_total} ISSUE movements over {args.days} days for {len(rows)} stock rows.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _movement(
    inventory: Inventory, movement_type: MovementType, quantity: int, created_at: datetime, note: str, product: Product
) -> InventoryMovement:
    return InventoryMovement(
        id=uuid.uuid4(),
        product_id=inventory.product_id,
        warehouse_id=inventory.warehouse_id,
        movement_type=movement_type,
        quantity=Decimal(quantity),
        unit_cost=(product.unit_price * Decimal("0.7")) if movement_type == MovementType.RECEIVE else None,
        reference_type=ReferenceType.MANUAL,
        reference_id=None,
        performed_by=None,
        notes=note,
        created_at=created_at,
    )


if __name__ == "__main__":
    main()
