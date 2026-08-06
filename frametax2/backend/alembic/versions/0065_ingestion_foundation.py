"""0065 — Phase E: ingestion staging foundation.

Two additive changes, no existing data touched:

  1. Widens documents.category from String(20) to String(30) — two of the
     new historical-evidence categories this phase adds
     (incentive_application, incentive_certificate) are 21 characters,
     already exceeding the old width. Same "widen when a genuine sizing
     defect is found" pattern used throughout Phase A/B/C, not a redesign.

  2. Creates ingestion_candidates — the DISCOVER/CLASSIFY/ASSOCIATE
     staging table. Nothing here is a canonical Document; only a reviewed
     row's COMMIT action (application code, not this migration) creates
     real Document/DocumentVersion/DocumentVersionSource rows.

Revision ID: 0065
Revises: 0064
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0065"
down_revision: Union[str, None] = "0064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "documents", "category",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    op.create_table(
        "ingestion_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_pointer", sa.Text(), nullable=False),
        sa.Column("source_display_path", sa.Text(), nullable=True),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("file_extension", sa.String(length=20), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("proposed_category", sa.String(length=30), nullable=False),
        sa.Column("category_confidence", sa.String(length=10), nullable=False),
        sa.Column("proposed_project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("association_confidence", sa.String(length=10), nullable=False),
        sa.Column("association_evidence", sa.Text(), nullable=True),
        sa.Column("version_status", sa.String(length=30), nullable=False),
        sa.Column("duplicate_of_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("cached_storage_path", sa.String(length=1024), nullable=True),
        sa.Column("committed_document_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("committed_project_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("discovered_at", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_candidates_checksum_sha256", "ingestion_candidates", ["checksum_sha256"])
    op.create_index("ix_ingestion_candidates_proposed_project_id", "ingestion_candidates", ["proposed_project_id"])
    op.create_index("ix_ingestion_candidates_status", "ingestion_candidates", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_candidates_status", table_name="ingestion_candidates")
    op.drop_index("ix_ingestion_candidates_proposed_project_id", table_name="ingestion_candidates")
    op.drop_index("ix_ingestion_candidates_checksum_sha256", table_name="ingestion_candidates")
    op.drop_table("ingestion_candidates")
    op.alter_column(
        "documents", "category",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
