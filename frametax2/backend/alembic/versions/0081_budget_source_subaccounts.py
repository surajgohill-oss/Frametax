"""Preserve authored budget detail totals without duplicating gross spend."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision = "0081"
down_revision = "0080"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("budget_line_items", sa.Column("source_subaccounts", JSONB(), nullable=True))

def downgrade():
    op.drop_column("budget_line_items", "source_subaccounts")
