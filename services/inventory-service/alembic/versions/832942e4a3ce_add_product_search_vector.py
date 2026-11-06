"""add product search vector"""
from alembic import op
import sqlalchemy as sa

revision = '832942e4a3ce'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE products
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(sku, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
        ) STORED;
    """)
    op.execute("CREATE INDEX idx_products_search_vector ON products USING GIN (search_vector);")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_products_search_vector;")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS search_vector;")
