"""add resolution_source to tracked_events

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-04 00:00:00.000000

Tracks how external_event_id was obtained so demo fixtures, API-resolved,
and page-fetch-resolved events are distinguishable at query time.

Values: 'seeded' | 'resolved_api' | 'resolved_page_fetch' | 'manual'
NULL means the event is still pending Stage 2 resolution.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracked_events",
        sa.Column("resolution_source", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracked_events", "resolution_source")
