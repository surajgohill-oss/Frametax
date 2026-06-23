"""0047 — Phase A+B schema: co_production_treaties, treaty_participants, co_production_structures.

Adds three new tables to support the treaty intelligence layer (Phase A) and
co-production structure database (Phase B):

  co_production_treaties        — bilateral and multilateral co-production treaties
  treaty_participants           — per-country participation for multilateral treaties
  co_production_structures      — eligible co-production structures that arise from treaties/funds

Revision ID: 0047
Revises: 0046
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0047"
down_revision: Union[str, None] = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # co_production_treaties
    # -------------------------------------------------------------------------
    op.create_table(
        "co_production_treaties",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        # Treaty identity
        sa.Column("treaty_name", sa.String(300), nullable=False),
        sa.Column("treaty_slug", sa.String(120), nullable=False, unique=True),
        sa.Column("treaty_type", sa.String(30), nullable=False,
                  comment=(
                      "bilateral | multilateral | european_convention | "
                      "ibermedia | eurimages"
                  )),
        sa.Column("status", sa.String(20), nullable=False, server_default="active",
                  comment="active | suspended | in_negotiation | historical"),
        # Parties (bilateral: a + b; multilateral: a=lead country, b=null)
        sa.Column("jurisdiction_a_code", sa.String(20), nullable=False,
                  comment="ISO 3166-1 alpha-2 of primary/first party."),
        sa.Column("jurisdiction_b_code", sa.String(20), nullable=True,
                  comment="ISO 3166-1 alpha-2 of second party (null for multilateral)."),
        # Dates
        sa.Column("year_signed", sa.Integer, nullable=True),
        sa.Column("effective_from", sa.String(20), nullable=True),
        sa.Column("effective_until", sa.String(20), nullable=True,
                  comment="Null = indefinite / still active."),
        # Co-production contribution thresholds
        sa.Column("majority_min_contribution_pct", sa.Numeric(5, 2), nullable=True,
                  comment="Minimum % of budget the majority co-producer must contribute."),
        sa.Column("minority_min_contribution_pct", sa.Numeric(5, 2), nullable=True,
                  comment="Minimum % of budget the minority co-producer must contribute."),
        sa.Column("minority_max_contribution_pct", sa.Numeric(5, 2), nullable=True,
                  comment="Maximum % the minority co-producer can contribute."),
        sa.Column("min_coproducer_countries", sa.Integer, nullable=True, server_default="2",
                  comment="Minimum number of co-producing countries required."),
        # Requirements
        sa.Column("spend_allocation_requirement", sa.Text, nullable=True,
                  comment="Narrative on how budget must be allocated across territories."),
        sa.Column("nationality_requirement", sa.Text, nullable=True,
                  comment="Narrative on required nationality of key creative contributors."),
        sa.Column("creative_contribution_requirement", sa.Text, nullable=True,
                  comment="Script, director, cast, crew requirements per party."),
        sa.Column("cultural_test_required", sa.Boolean, nullable=True),
        sa.Column("ownership_requirement", sa.Text, nullable=True,
                  comment="IP ownership / copyright allocation requirements."),
        # Benefits by party
        sa.Column("majority_jurisdiction_benefits", sa.Text, nullable=True,
                  comment="Incentives unlocked for the majority co-production jurisdiction."),
        sa.Column("minority_jurisdiction_benefits", sa.Text, nullable=True,
                  comment="Incentives unlocked for the minority co-production jurisdiction."),
        # Administration
        sa.Column("treaty_administrator_name", sa.String(255), nullable=True),
        sa.Column("authority_url", sa.String(2048), nullable=True),
        # Intelligence tier
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_cpt_slug", "co_production_treaties", ["treaty_slug"])
    op.create_index("ix_cpt_jur_a", "co_production_treaties", ["jurisdiction_a_code"])
    op.create_index("ix_cpt_jur_b", "co_production_treaties", ["jurisdiction_b_code"])
    op.create_index("ix_cpt_type", "co_production_treaties", ["treaty_type"])

    # -------------------------------------------------------------------------
    # treaty_participants (for multilateral treaties)
    # -------------------------------------------------------------------------
    op.create_table(
        "treaty_participants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("treaty_id", UUID(as_uuid=True),
                  sa.ForeignKey("co_production_treaties.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("jurisdiction_code", sa.String(20), nullable=False),
        sa.Column("jurisdiction_name", sa.String(255), nullable=True),
        sa.Column("is_founding_member", sa.Boolean, nullable=True),
        sa.Column("joined_date", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active",
                  comment="active | suspended | withdrawn"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_tp_treaty_jur", "treaty_participants",
                    ["treaty_id", "jurisdiction_code"], unique=True)

    # -------------------------------------------------------------------------
    # co_production_structures
    # -------------------------------------------------------------------------
    op.create_table(
        "co_production_structures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("structure_slug", sa.String(120), nullable=False, unique=True),
        sa.Column("treaty_id", UUID(as_uuid=True),
                  sa.ForeignKey("co_production_treaties.id", ondelete="SET NULL"),
                  nullable=True, index=True,
                  comment="Null for fund-enabled or untreaty'd co-productions."),
        sa.Column("structure_type", sa.String(30), nullable=False,
                  comment=(
                      "treaty_bilateral | treaty_multilateral | fund_coproduction | "
                      "minority_service | majority_principal"
                  )),
        # Geography
        sa.Column("majority_country_code", sa.String(20), nullable=True,
                  comment="ISO code of the majority (lead) co-production country."),
        sa.Column("minority_country_code", sa.String(20), nullable=True,
                  comment="ISO code of the minority co-production country."),
        sa.Column("additional_country_codes", sa.Text, nullable=True,
                  comment="Comma-separated ISO codes for trilateral or larger structures."),
        # Contribution thresholds (may override treaty defaults)
        sa.Column("majority_min_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("minority_min_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("minority_max_pct", sa.Numeric(5, 2), nullable=True),
        # Unlocked benefits (comma-separated program slugs)
        sa.Column("unlocks_majority_incentive_slugs", sa.Text, nullable=True,
                  comment="Slugs of incentive programs unlocked for majority party."),
        sa.Column("unlocks_minority_incentive_slugs", sa.Text, nullable=True,
                  comment="Slugs of incentive programs unlocked for minority party."),
        sa.Column("unlocks_fund_slugs", sa.Text, nullable=True,
                  comment="Slugs of co-production funds eligible via this structure."),
        # Qualification impact
        sa.Column("nationality_test_impact", sa.Text, nullable=True,
                  comment="How official co-production affects nationality tests for each party."),
        sa.Column("cultural_test_impact", sa.Text, nullable=True,
                  comment="How official co-production affects cultural tests for each party."),
        # Operational
        sa.Column("financing_structure_notes", sa.Text, nullable=True),
        sa.Column("eligibility_requirements", sa.Text, nullable=True),
        # Intelligence tier
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_cops_slug", "co_production_structures", ["structure_slug"])
    op.create_index("ix_cops_majority", "co_production_structures", ["majority_country_code"])
    op.create_index("ix_cops_minority", "co_production_structures", ["minority_country_code"])


def downgrade() -> None:
    op.drop_table("co_production_structures")
    op.drop_index("ix_tp_treaty_jur", table_name="treaty_participants")
    op.drop_table("treaty_participants")
    op.drop_index("ix_cpt_slug", table_name="co_production_treaties")
    op.drop_index("ix_cpt_jur_a", table_name="co_production_treaties")
    op.drop_index("ix_cpt_jur_b", table_name="co_production_treaties")
    op.drop_index("ix_cpt_type", table_name="co_production_treaties")
    op.drop_table("co_production_treaties")
