"""0011 — Create production_contributions table.

Tracks every form of value entering a production: cash, deferred fees,
equity deals, in-kind goods/services, sponsorships, government support,
and vendor financing arrangements.

Revision ID: 0011
Revises: 0010
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "production_contributions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),

        # Foreign keys
        sa.Column("project_id", UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("jurisdiction_id", UUID(as_uuid=True),
                  sa.ForeignKey("jurisdictions.id"),
                  nullable=True, index=True),
        sa.Column("source_document_id", UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id"),
                  nullable=True),

        # Core fields
        sa.Column("contribution_type", sa.String(30), nullable=False, index=True),
        sa.Column("provider", sa.String(512), nullable=False),

        # Monetary values
        sa.Column("amount", sa.Numeric(18, 2), nullable=False,
                  comment="Face / stated value of the contribution in USD"),
        sa.Column("fair_market_value", sa.Numeric(18, 2), nullable=True,
                  comment="Arm's-length market value; may differ from amount for equity/in-kind"),
        sa.Column("replacement_cost", sa.Numeric(18, 2), nullable=True,
                  comment="Cost to replace this contribution at open-market rates if withdrawn"),

        # Jurisdiction and incentive linkage
        sa.Column("jurisdiction_specific", sa.Boolean, nullable=False, default=False,
                  comment="True if this contribution is tied to spend in a specific jurisdiction"),
        sa.Column("qualifies_for_incentive", sa.Boolean, nullable=True,
                  comment="Whether this contribution counts toward qualifying spend in the linked programme"),

        # Conditionality
        sa.Column("is_conditional", sa.Boolean, nullable=False, default=False,
                  comment="True if this contribution only materialises upon a condition"),
        sa.Column("condition_notes", sa.Text, nullable=True),

        # Provenance
        sa.Column("confidence_tier", sa.String(20), nullable=False, default="DISCOVERY"),
        sa.Column("effective_date", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_index(
        "ix_production_contributions_project_type",
        "production_contributions",
        ["project_id", "contribution_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_production_contributions_project_type",
                  table_name="production_contributions")
    op.drop_table("production_contributions")
