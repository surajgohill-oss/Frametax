"""add venues.timezone and event_outcomes confidence columns

Revision ID: 0027
Revises: 0026
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # venues: per-venue timezone (IANA key)
    op.add_column(
        "venues",
        sa.Column(
            "timezone",
            sa.String(50),
            nullable=False,
            server_default="America/Los_Angeles",
        ),
    )

    # event_outcomes: coverage confidence
    op.add_column(
        "event_outcomes",
        sa.Column("coverage_confidence_score", sa.Numeric(4, 3), nullable=True),
    )
    op.add_column(
        "event_outcomes",
        sa.Column("coverage_confidence_label", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("event_outcomes", "coverage_confidence_label")
    op.drop_column("event_outcomes", "coverage_confidence_score")
    op.drop_column("venues", "timezone")
