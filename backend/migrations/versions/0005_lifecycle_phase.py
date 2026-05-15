"""add lifecycle_phase to tracked_events

Revision ID: 0005
Revises: 0004
Create Date: 2024-01-05 00:00:00.000000

Observability column only. Values: pre_admission | active | in_progress | completed.
NULL on existing rows is valid; _update_event_statuses populates it on first run.
Lifecycle phase does NOT gate polling — that is the exclusive domain of
compute_poll_interval_minutes returning None.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracked_events",
        sa.Column("lifecycle_phase", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracked_events", "lifecycle_phase")
