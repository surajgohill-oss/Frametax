"""add custom_artwork_url to events

Revision ID: 0028
Revises: 0027
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("custom_artwork_url", sa.String(2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "custom_artwork_url")
