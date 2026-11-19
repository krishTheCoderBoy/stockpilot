"""add inventory movement search vector

Idempotent, like the product and warehouse search migrations: a missing column is
added, a plain (non-generated) one is converted, and an existing generated one is left
alone.

Adding a stored generated column rewrites the table, and inventory_movements is the
ledger, so on a large production table run this in a maintenance window.
"""
from alembic import op
import sqlalchemy as sa

revision = "e6c1f4a83b59"
down_revision = "d5b9e3f72a48"
branch_labels = None
depends_on = None

TABLE = "inventory_movements"
INDEX = "idx_movements_search_vector"
# Must stay identical to MOVEMENT_SEARCH_EXPRESSION in app/modules/inventory_movements/models.py.
EXPRESSION = "setweight(to_tsvector('english', coalesce(notes, '')), 'A')"


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
