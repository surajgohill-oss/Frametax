"""Person Nationality Resolution: talent_profiles provenance columns

Extends the EXISTING canonical person model (TalentProfile) rather than
building a parallel one. primary_nationality already existed and remains
the single canonical ISO 3166-1 alpha-2 field qualification engines read;
these columns add ONLY the provenance a real external resolution needs,
additive/nullable, nothing existing rewritten:

  nationality_resolution_status  — "resolved" | "unresolved_no_match" |
                                    "unresolved_ambiguous" | "lookup_failed" |
                                    "not_attempted" (never silently absent —
                                    an attempted-but-failed lookup is a
                                    distinct, disclosed state from "never
                                    tried")
  nationality_source             — e.g. "wikidata" (provider identity)
  nationality_source_entity_id   — e.g. "Q7461586" (the resolved entity,
                                    for exact re-verification)
  nationality_evidence           — JSONB: every documented citizenship
                                    (not just the one chosen as primary),
                                    plus the raw match evidence used for
                                    disambiguation and a retrieval
                                    timestamp — dual/multiple citizenship
                                    is never silently discarded even
                                    though primary_nationality holds one
  nationality_confidence         — reuses the EXISTING ConfidenceTier
                                    enum (DISCOVERY for an unreviewed
                                    external match), never a new
                                    parallel confidence vocabulary
  nationality_resolved_at        — ISO timestamp string, same style
                                    known_residencies' entries already use

Revision ID: 0069
Revises: 0068
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0069"
down_revision: Union[str, None] = "0068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("talent_profiles", sa.Column("nationality_resolution_status", sa.String(length=40), nullable=True))
    op.add_column("talent_profiles", sa.Column("nationality_source", sa.String(length=40), nullable=True))
    op.add_column("talent_profiles", sa.Column("nationality_source_entity_id", sa.String(length=100), nullable=True))
    op.add_column("talent_profiles", sa.Column("nationality_evidence", postgresql.JSONB(), nullable=True))
    op.add_column("talent_profiles", sa.Column("nationality_confidence", sa.String(length=20), nullable=True))
    op.add_column("talent_profiles", sa.Column("nationality_resolved_at", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("talent_profiles", "nationality_resolved_at")
    op.drop_column("talent_profiles", "nationality_confidence")
    op.drop_column("talent_profiles", "nationality_evidence")
    op.drop_column("talent_profiles", "nationality_source_entity_id")
    op.drop_column("talent_profiles", "nationality_source")
    op.drop_column("talent_profiles", "nationality_resolution_status")
