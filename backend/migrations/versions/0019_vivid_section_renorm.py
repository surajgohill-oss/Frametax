"""Renormalize VividSeats section_id values to strip venue-tier qualifiers.

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Already applied to production DB before this file was tracked in git.
    # This stub satisfies alembic's chain validation; the actual SQL was:
    #   UPDATE listings SET section_id = regexp_replace(section_id, ...)
    #   (VividSeats section normalization — no schema change, data-only)
    pass


def downgrade() -> None:
    pass
