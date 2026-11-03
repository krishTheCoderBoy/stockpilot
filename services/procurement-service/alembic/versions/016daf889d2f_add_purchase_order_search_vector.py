"""add purchase order search vector"""
from alembic import op
import sqlalchemy as sa

revision = '016daf889d2f'
down_revision = '8e1439173f7e'
branch_labels = None
depends_on = None
def upgrade():
    op.execute("""
        ALTER TABLE purchase_orders
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(po_number, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(notes, '')), 'B')
        ) STORED;
    """)
    op.execute("CREATE INDEX idx_pos_search_vector ON purchase_orders USING GIN (search_vector);")

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_pos_search_vector;")
    op.execute("ALTER TABLE purchase_orders DROP COLUMN IF EXISTS search_vector;")
