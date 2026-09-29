"""Initial owned schema baseline for isolated service database."""
from alembic import op
from app.core.database import Base
# Model imports are registered by the service Alembic env.py before this revision runs.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())
def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
