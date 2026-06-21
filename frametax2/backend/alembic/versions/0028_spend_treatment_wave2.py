"""0028 — ProgramSpendTreatment for 47 wave-2 programs (DISCOVERY tier).

Seeds exactly 21 ProgramSpendTreatment rows per program for all programs
added in migration 0026. All entries are DISCOVERY tier.

Treatment rules applied:
  - contingency: DOES_NOT_QUALIFY (False) — universal across all programs
  - all other categories: UNKNOWN (None) — not confirmed from primary source

Revision ID: 0028
Revises: 0027
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: Union[str, None] = "0027"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0028-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_SLUGS: list[str] = [
    # US states/territories
    "us_hi_film_tax_credit", "us_ut_film_incentive", "us_mn_film_credit",
    "us_ms_film_credit", "us_az_film_credit", "us_pr_film_incentive",
    # Canadian provinces
    "ca_sk_production_grant", "ca_nl_production_fund",
    # Europe
    "se_film_incentive", "no_film_incentive", "fi_film_incentive", "dk_film_incentive",
    "pl_film_incentive", "bg_film_incentive", "ee_film_incentive", "lt_film_incentive",
    "lv_film_incentive", "sk_film_incentive", "lu_film_incentive", "tr_film_incentive",
    # Asia-Pacific
    "th_film_incentive", "my_film_incentive", "ph_film_incentive", "kr_film_incentive",
    "in_national_film", "lk_film_incentive",
    # Latin America & Caribbean
    "mx_eficine_incentive", "cl_corfo_incentive", "jm_film_incentive", "tt_film_incentive",
    # Middle East & Africa
    "il_film_incentive", "qa_film_incentive", "tn_film_incentive",
    "ke_film_incentive", "ng_film_incentive",
    # Grants / Funds
    "eu_eurimages", "eu_media_fund", "nordic_ftvf",
    "ca_cmf", "ca_telefilm_dev", "gb_bfi_production", "fr_cnc_production",
    "au_screen_production", "nl_hbf", "qa_dfi_fund", "us_sundance_doc", "za_dac_fund",
]

_LABOR_TYPES: list[str] = [
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production", "animation",
    "music", "legal_accounting", "customs_imports",
]

_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_UNKNOWN_NOTE = (
    "DISCOVERY tier — spend treatment not confirmed from primary source. "
    "Verify eligibility with local film office before budget finalisation."
)


def upgrade() -> None:
    conn = op.get_bind()

    for slug in _SLUGS:
        for labor_type in _LABOR_TYPES:
            if labor_type == "contingency":
                qualifies = False
                notes = _CONTINGENCY_NOTE
                tier = "DISCOVERY"
            else:
                qualifies = None
                notes = _UNKNOWN_NOTE
                tier = "DISCOVERY"

            conn.execute(
                sa.text("""
                    INSERT INTO program_spend_treatments (
                        id, program_id, labor_type,
                        qualifies, treatment_notes, confidence_tier,
                        created_at, updated_at
                    )
                    SELECT
                        :id, p.id, :labor_type,
                        :qualifies, :notes, :tier,
                        :now, :now
                    FROM incentive_programs p
                    WHERE p.slug = :slug
                      AND NOT EXISTS (
                          SELECT 1 FROM program_spend_treatments t
                          WHERE t.program_id = p.id
                            AND t.labor_type = :labor_type
                      )
                    LIMIT 1
                """),
                {
                    "id": _uid(f"treatment:{slug}:{labor_type}"),
                    "slug": slug,
                    "labor_type": labor_type,
                    "qualifies": qualifies,
                    "notes": notes,
                    "tier": tier,
                    "now": NOW,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    for slug in _SLUGS:
        for labor_type in _LABOR_TYPES:
            conn.execute(
                sa.text("DELETE FROM program_spend_treatments WHERE id = :id"),
                {"id": _uid(f"treatment:{slug}:{labor_type}")},
            )
