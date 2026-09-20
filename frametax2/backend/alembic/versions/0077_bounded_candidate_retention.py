"""Bounded candidate retention: evaluation_candidate_aggregates + summary accounting columns

Enumeration cardinality must never define persistence cardinality. canonical-1.90.0 evaluates every
candidate but persists only the bounded decision set as detailed rows (baseline; global and
per-structure_type top-100 PRICED; best local candidate per jurisdiction; every proof-bearing and
reviewable/opportunity row; anything a retained proof references). Every other candidate -- all plain
RULE_REJECTED permutations and all PRICED candidates outside the retained sets -- is counted exactly in
evaluation_candidate_aggregates, one narrow row per canonical group, in the same transaction.

evaluation_generation_summaries gains the accounting columns that let a reader verify
    total_rows == persisted_rows + aggregated_candidates
(nullable: canonical-1.88.0 and earlier generations are never served as current and are not backfilled).

Revision ID: 0077
Revises: 0076
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0077"
down_revision: Union[str, None] = "0076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for column in ("persisted_rows", "aggregated_candidates", "aggregated_priced", "aggregate_groups"):
        op.add_column("evaluation_generation_summaries", sa.Column(column, sa.Integer(), nullable=True))
    op.create_table(
        "evaluation_candidate_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("engine_version", sa.String(50), nullable=False),
        sa.Column("group_ordinal", sa.BigInteger(), nullable=False),
        sa.Column("group_key", sa.String(64), nullable=False),
        sa.Column("candidate_status", sa.String(60), nullable=False),
        sa.Column("structure_type", sa.String(100), nullable=False),
        sa.Column("structural_family", sa.String(100), nullable=True),
        sa.Column("reason_class", sa.String(100), nullable=True),
        sa.Column("primary_jurisdiction", sa.String(50), nullable=True),
        sa.Column("jurisdiction_codes", postgresql.JSONB(), nullable=False),
        sa.Column("program_slugs", postgresql.JSONB(), nullable=False),
        sa.Column("component_family", postgresql.JSONB(), nullable=False),
        sa.Column("treaty_family", sa.String(200), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("min_npc_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("max_npc_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("min_incentive_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("max_incentive_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("best_economic_identity", sa.String(64), nullable=True),
        sa.Column("dominating_structure_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production_structures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_candidate_seq", sa.BigInteger(), nullable=False),
        sa.Column("representative", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("project_id", "input_fingerprint", "engine_version", "group_ordinal",
                            name="uq_candidate_aggregate_ordinal"),
        sa.UniqueConstraint("project_id", "input_fingerprint", "engine_version", "group_key",
                            name="uq_candidate_aggregate_key"),
    )
    # supports the ON DELETE SET NULL foreign key (without it every structure delete scans the table)
    op.create_index("ix_candidate_aggregate_dominating_structure", "evaluation_candidate_aggregates", ["dominating_structure_id"])


def downgrade() -> None:
    op.drop_table("evaluation_candidate_aggregates")
    for column in ("aggregate_groups", "aggregated_priced", "aggregated_candidates", "persisted_rows"):
        op.drop_column("evaluation_generation_summaries", column)
