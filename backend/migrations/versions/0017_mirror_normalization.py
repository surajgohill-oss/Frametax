"""Phase 1E-F: add mirror normalization columns to listings

Adds two nullable derived columns to the listings table:
  mirror_group_id   INTEGER  – groups listings that represent the same physical
                               seat block across marketplaces (strict:
                               same section_id + row + quantity).
                               NULL until normalization job writes to it.
  mirror_confidence VARCHAR  – classification: 'confirmed' | 'probable' |
                               'exclusive' | NULL.

These are derived/computed fields. Raw collector outputs are never modified.
The inventory-summary endpoint computes these at query time without writing them.
The background normalization job (future) will persist them here.

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("mirror_group_id", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("mirror_confidence", sa.String(20), nullable=True))
    op.create_index("ix_listings_mirror_group", "listings", ["mirror_group_id"])


def downgrade() -> None:
    op.drop_index("ix_listings_mirror_group", table_name="listings")
    op.drop_column("listings", "mirror_confidence")
    op.drop_column("listings", "mirror_group_id")
