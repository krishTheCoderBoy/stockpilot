"""add product search vector

Idempotent: a fresh database gets the generated column here. A database that already
has it as a generated column is left alone, and one that has a plain (non-generated)
search_vector, e.g. from create_all against an older model, is converted.
"""
from alembic import op
import sqlalchemy as sa

revision = '832942e4a3ce'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

TABLE = "products"
INDEX = "idx_products_search_vector"
# Must stay identical to PRODUCT_SEARCH_EXPRESSION in app/modules/products/models.py.
EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(sku, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(description, '')), 'B')"
)


def _search_vector_generation() -> str | None:
    """None if the column is missing, 's' if it is a stored generated column, '' if plain."""
    return op.get_bind().execute(
        sa.text(
            "SELECT attgenerated FROM pg_attribute "
            "WHERE attrelid = to_regclass(:table) AND attname = 'search_vector' AND NOT attisdropped"
        ),
        {"table": TABLE},
    ).scalar()


def upgrade():
    generation = _search_vector_generation()
    if generation != "s":
        if generation is not None:
            op.execute(f"DROP INDEX IF EXISTS {INDEX};")
            op.execute(f"ALTER TABLE {TABLE} DROP COLUMN search_vector;")
        op.execute(
            f"ALTER TABLE {TABLE} ADD COLUMN search_vector tsvector "
            f"GENERATED ALWAYS AS ({EXPRESSION}) STORED;"
        )
    op.execute(f"CREATE INDEX IF NOT EXISTS {INDEX} ON {TABLE} USING GIN (search_vector);")


def downgrade():
    op.execute(f"DROP INDEX IF EXISTS {INDEX};")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS search_vector;")
