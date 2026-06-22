"""0042 — Phase D schema: fund_economics table + ProgramAdminDetails Phase-D columns.

Adds:
  - fund_economics table: repayability, recoupment, equity, matching, stackability
    for grant / co-production fund programmes
  - program_admin_details.is_competitive_allocation: competitive vs entitlement programme
  - program_admin_details.per_project_cap_usd: per-project claim limit

Revision ID: 0042
Revises: 0041
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0042"
down_revision: Union[str, None] = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- ProgramAdminDetails Phase-D additions ---
    op.add_column(
        "program_admin_details",
        sa.Column(
            "is_competitive_allocation",
            sa.Boolean(),
            nullable=True,
            comment=(
                "True = competitive/discretionary fund allocation (committee decision). "
                "False = formula-based entitlement (every qualifying project receives the credit)."
            ),
        ),
    )
    op.add_column(
        "program_admin_details",
        sa.Column(
            "per_project_cap_usd",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Per-project claim cap in USD, distinct from annual programme cap.",
        ),
    )

    # --- fund_economics table ---
    op.create_table(
        "fund_economics",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            "is_repayable", sa.Boolean(), nullable=True,
            comment="Fund advance must be repaid from exploitation receipts.",
        ),
        sa.Column("repayment_terms", sa.Text(), nullable=True),
        sa.Column(
            "is_recoupable", sa.Boolean(), nullable=True,
            comment="Fund recoups investment from gross receipts before producer share.",
        ),
        sa.Column("recoupment_terms", sa.Text(), nullable=True),
        sa.Column(
            "has_equity_participation", sa.Boolean(), nullable=True,
            comment="Fund takes equity / backend participation in IP.",
        ),
        sa.Column("equity_participation_notes", sa.Text(), nullable=True),
        sa.Column(
            "has_matching_requirement", sa.Boolean(), nullable=True,
            comment="Production must demonstrate matching co-financing commitment.",
        ),
        sa.Column("matching_notes", sa.Text(), nullable=True),
        sa.Column(
            "has_territorial_spend_requirement", sa.Boolean(), nullable=True,
            comment="Minimum spend must occur within the fund's territory.",
        ),
        sa.Column("territorial_spend_notes", sa.Text(), nullable=True),
        sa.Column(
            "eligible_formats", sa.Text(), nullable=True,
            comment="Comma-separated list: feature, documentary, animation, series, short, game.",
        ),
        sa.Column(
            "typical_max_award_usd", sa.Numeric(15, 2), nullable=True,
            comment="Typical maximum award in USD.",
        ),
        sa.Column("award_range_notes", sa.Text(), nullable=True),
        sa.Column(
            "is_competitive", sa.Boolean(), nullable=True,
            comment="Competitive / discretionary allocation (committee decision).",
        ),
        sa.Column(
            "stackable_with_incentives", sa.Boolean(), nullable=True,
            comment=(
                "True = stacks with national tax credits without reducing qualifying basis. "
                "False = constitutes government assistance that reduces credit base."
            ),
        ),
        sa.Column("stackability_notes", sa.Text(), nullable=True),
        sa.Column(
            "confidence_tier",
            sa.String(20),
            nullable=False,
            server_default="DISCOVERY",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("fund_economics")
    op.drop_column("program_admin_details", "per_project_cap_usd")
    op.drop_column("program_admin_details", "is_competitive_allocation")
