"""0066 — Phase F: artwork-extraction provenance on ingestion_candidates.

One additive change: two nullable columns so an artwork candidate that was
EXTRACTED from a deck/lookbook/screenplay cover page (rather than
discovered as a standalone image file) can carry real provenance —
which original DocumentVersion it came from, and what kind of source page
it was extracted from. commit_candidate() reads these to set the resulting
ProjectAsset's source_document_version_id/source_type/notes correctly
instead of defaulting to DISCOVERED_IMAGE self-reference. Both columns are
NULL for every existing row and for any future standalone-image candidate.

Revision ID: 0066
Revises: 0065
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0066"
down_revision: Union[str, None] = "0065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingestion_candidates",
        sa.Column(
            "extracted_from_document_version_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True,
        ),
    )
    op.add_column(
        "ingestion_candidates",
        sa.Column("artwork_extraction_kind", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ingestion_candidates", "artwork_extraction_kind")
    op.drop_column("ingestion_candidates", "extracted_from_document_version_id")
