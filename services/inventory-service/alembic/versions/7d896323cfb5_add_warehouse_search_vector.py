"""add warehouse search vector"""
from alembic import op
import sqlalchemy as sa

revision = '7d896323cfb5'
down_revision = '832942e4a3ce'
branch_labels = None
depends_on = None
def upgrade():
    op.execute("""
        ALTER TABLE warehouses
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(code, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(city, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(state, '')), 'B')
        ) STORED;
    """)
    op.execute("CREATE INDEX idx_warehouses_search_vector ON warehouses USING GIN (search_vector);")

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_warehouses_search_vector;")
    op.execute("ALTER TABLE warehouses DROP COLUMN IF EXISTS search_vector;")
