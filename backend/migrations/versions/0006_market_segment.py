"""add market_segment to listings and listing_snapshots

Revision ID: 0006
Revises: 0005
Create Date: 2024-01-06 00:00:00.000000

Nullable on all existing rows (SeatGeek/StubHub listings get NULL,
which the API/UI treat as "n/a"). Ticketmaster listings populate this
with "primary" or "verified_resale" at ingest time.

Allowed values: primary | verified_resale | NULL
NULL = marketplace does not segment supply (backward-compatible default).
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings",          sa.Column("market_segment", sa.String(20), nullable=True))
    op.add_column("listing_snapshots", sa.Column("market_segment", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("listing_snapshots", "market_segment")
    op.drop_column("listings",          "market_segment")
