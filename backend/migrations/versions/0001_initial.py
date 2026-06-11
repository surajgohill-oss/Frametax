"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("marketplaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(50)),
        sa.Column("capacity", sa.Integer()),
        sa.Column("map_width", sa.Integer(), default=800),
        sa.Column("map_height", sa.Integer(), default=600),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("venue_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(50)),
        sa.Column("quality_score", sa.Float()),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), default=40),
        sa.Column("height", sa.Float(), default=30),
        sa.Column("shape", sa.String(20), default="rect"),
        sa.Column("shape_data", postgresql.JSONB()),
        sa.Column("stubhub_aliases", postgresql.JSONB()),
        sa.Column("seatgeek_aliases", postgresql.JSONB()),
        sa.UniqueConstraint("venue_id", "section_id"),
    )
    op.create_table("events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_id", sa.String(32), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("artist", sa.String(200)),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("tracked_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("external_event_id", sa.String(100)),
        sa.Column("external_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("poll_interval_minutes", sa.Integer(), default=60),
        sa.Column("last_polled_at", sa.DateTime()),
        sa.Column("next_poll_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("external_listing_id", sa.String(100)),
        sa.Column("section", sa.String(100)),
        sa.Column("section_id", sa.String(50)),
        sa.Column("row", sa.String(20)),
        sa.Column("quantity", sa.Integer(), default=1),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("fees", sa.Numeric(10, 2)),
        sa.Column("all_in_price", sa.Numeric(10, 2)),
        sa.Column("listing_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("event_id", "marketplace_id", "external_listing_id"),
    )
    op.create_table("listing_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("section_id", sa.String(50)),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), default=1),
        sa.Column("snapshot_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("poll_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tracked_event_id", sa.Integer(), sa.ForeignKey("tracked_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("status", sa.String(20), default="running"),
        sa.Column("listings_found", sa.Integer(), default=0),
        sa.Column("new_listings", sa.Integer(), default=0),
        sa.Column("disappeared_listings", sa.Integer(), default=0),
        sa.Column("error_message", sa.Text()),
    )
    op.create_table("scraper_error_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marketplace", sa.String(50), nullable=False),
        sa.Column("event_id", sa.String(100)),
        sa.Column("error_type", sa.String(50), nullable=False),
        sa.Column("selector", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("http_status", sa.Integer()),
        sa.Column("raw_sample", sa.Text()),
        sa.Column("screenshot_path", sa.Text()),
        sa.Column("html_snapshot_path", sa.Text()),
        sa.Column("extra", postgresql.JSONB()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table("failure_memory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marketplace", sa.String(50), nullable=False),
        sa.Column("error_type", sa.String(50), nullable=False),
        sa.Column("failed_pattern", sa.Text(), nullable=False),
        sa.Column("fallback_pattern", sa.Text()),
        sa.Column("fallback_success_count", sa.Integer(), default=0),
        sa.Column("failure_count", sa.Integer(), default=1),
        sa.Column("skip_failed", sa.Boolean(), default=False),
        sa.Column("first_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_success", sa.DateTime()),
        sa.Column("notes", sa.Text()),
        sa.UniqueConstraint("marketplace", "error_type", "failed_pattern"),
    )


def downgrade() -> None:
    for t in ["failure_memory","scraper_error_logs","poll_runs","listing_snapshots","listings","tracked_events","events","venue_sections","venues","marketplaces"]:
        op.drop_table(t)
