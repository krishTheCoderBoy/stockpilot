"""Alembic environment for the Inventory service.

Everything here is service-local: its own settings (and therefore its own .env and
DATABASE_URL), its own Base.metadata and its own versions/ history. Nothing is shared with
the other services' migrations.
"""
from logging.config import fileConfig
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# This service's root. Every service names its package `app`, so putting our own root first
# on sys.path is what makes `app` mean *this* service, whatever directory alembic was
# started from.
service_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(service_root))

from app.core.config import settings
from app.core.database import Base

# Importing a model module registers its tables on Base.metadata. Every model of this
# service must be imported here; a missing one would make `alembic check` and autogenerate
# believe its table should not exist.
from app.modules.products.categories_models import ProductCategory
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse
from app.modules.inventory.models import Inventory
from app.modules.inventory_movements.models import InventoryMovement
from app.modules.inventory_batches.models import InventoryBatch
from app.modules.inventory_reservations.models import StockReservation

config = context.config

# The URL comes from the service settings, never from alembic.ini. Percent signs are doubled
# because ConfigParser treats a single one as interpolation.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
