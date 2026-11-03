"""add supplier search vector"""
from alembic import op
import sqlalchemy as sa

revision = '8e1439173f7e'
down_revision = '0001_procurement_tables'
branch_labels = None
depends_on = None
def upgrade():
    op.execute("""
        ALTER TABLE suppliers
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(code, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(contact_person, '')), 'B')
        ) STORED;
    """)
    op.execute("CREATE INDEX idx_suppliers_search_vector ON suppliers USING GIN (search_vector);")

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_suppliers_search_vector;")
    op.execute("ALTER TABLE suppliers DROP COLUMN IF EXISTS search_vector;")