"""Bounded evaluation responses: generation ordinal, PRICED identity, per-generation summary

An FVD-scale evaluation persists >500K candidate rows, ~99.9% of them unpriced
(almost all RULE_REJECTED). Every served surface used to load, count and embed
that whole rejection universe. This migration adds only what bounded serving
needs -- and nothing is backfilled: the new nullable fields apply PROSPECTIVELY
to rows written by canonical-1.88.0 and later, and every historical row stays
exactly as it was.

structure_calculation_results
  generation_ordinal  BIGINT NULL  -- 1..N, assigned monotonically by the writer in
                                      generation order within one evaluation
  economic_identity   VARCHAR(64) NULL -- stable SHA-256 tie-breaker, written for
                                      PRICED rows only (ranking ties); never indexed

  ix_scr_generation_ordinal (input_fingerprint, engine_version, generation_ordinal)
      The ONLY index added. Within one evaluation the leading columns are constant
      and the ordinal ascends, so inserts append at the right edge of one region of
      the b-tree (cache-friendly, unlike a random-key index). It serves keyset
      pagination of the unpriced rows AND the freshness lookup (fingerprint,
      engine_version prefix) that previously seq-scanned the whole history table
      (measured 20.3 s on 1.7M rows).

evaluation_generation_summaries -- ONE narrow row per (project, fingerprint,
engine), accumulated while the evaluation runs and written in the same
transaction as its rows: total/priced/unpriced counts, counts by disposition and
by (disposition, reason), and the ordinals of every row that is NOT a plain
RULE_REJECTED (plus any baseline), i.e. the few hundred to few thousand rows the
ranking and the workspace actually load. No trace, no row payload.

Revision ID: 0076
Revises: 0075
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0076"
down_revision: Union[str, None] = "0075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("structure_calculation_results", sa.Column("generation_ordinal", sa.BigInteger(), nullable=True))
    op.add_column("structure_calculation_results", sa.Column("economic_identity", sa.String(64), nullable=True))
    op.create_index(
        "ix_scr_generation_ordinal",
        "structure_calculation_results",
        ["input_fingerprint", "engine_version", "generation_ordinal"],
    )
    op.create_table(
        "evaluation_generation_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("engine_version", sa.String(50), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("priced_count", sa.Integer(), nullable=False),
        sa.Column("unpriced_count", sa.Integer(), nullable=False),
        sa.Column("by_disposition", postgresql.JSONB(), nullable=False),
        sa.Column("by_reason", postgresql.JSONB(), nullable=False),
        sa.Column("non_rejected_ordinals", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "input_fingerprint", "engine_version", name="uq_evaluation_generation_summary",
        ),
    )
    op.create_index("ix_evaluation_generation_summaries_id", "evaluation_generation_summaries", ["id"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_generation_summaries_id", table_name="evaluation_generation_summaries")
    op.drop_table("evaluation_generation_summaries")
    op.drop_index("ix_scr_generation_ordinal", table_name="structure_calculation_results")
    op.drop_column("structure_calculation_results", "economic_identity")
    op.drop_column("structure_calculation_results", "generation_ordinal")
