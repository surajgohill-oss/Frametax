"""add missing indexes for debug tables

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000

These indexes were declared in ORM __table_args__ but never created by any
migration. Without them, debug/error-log queries scan full tables. They were
previously created only when seed_db_docker.py ran create_all — which also
created duplicate ORM-named indexes alongside the migration-named ones on
listings/listing_snapshots. create_all has been removed from the seed;
Alembic is now the sole owner of schema.
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_scraper_errors_mp_ts",  "scraper_error_logs", ["marketplace", "timestamp"])
    op.create_index("ix_scraper_errors_event",   "scraper_error_logs", ["event_id"])
    op.create_index("ix_scraper_errors_type",    "scraper_error_logs", ["error_type"])
    op.create_index("ix_failure_memory_mp_type", "failure_memory",     ["marketplace", "error_type"])


def downgrade() -> None:
    op.drop_index("ix_failure_memory_mp_type", table_name="failure_memory")
    op.drop_index("ix_scraper_errors_type",    table_name="scraper_error_logs")
    op.drop_index("ix_scraper_errors_event",   table_name="scraper_error_logs")
    op.drop_index("ix_scraper_errors_mp_ts",   table_name="scraper_error_logs")
