"""0024 — ProgramSpendTreatment for 43 extended (DISCOVERY-tier) programs.

Seeds exactly 21 ProgramSpendTreatment rows per program for all programs
introduced in migration 0015. All entries are DISCOVERY tier.

Treatment rules applied:
  - contingency: DOES_NOT_QUALIFY (False) — universal across all programs
  - all other categories: UNKNOWN (None) — not confirmed from primary source

This brings structural completeness to the intelligence database:
all 60 current programs have exactly 21 spend treatment rows.

Revision ID: 0024
Revises: 0023
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0024-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# All 43 extended program slugs (from migration 0015)
_SLUGS: list[str] = [
    # US States (16)
    "us_or_opif", "us_wa_mpcp", "us_il_film_credit", "us_nc_film_grant",
    "us_sc_film_credit", "us_ma_film_credit", "us_tx_miip", "us_ct_film_credit",
    "us_pa_film_credit", "us_md_film_credit", "us_va_film_credit",
    "us_co_film_incentive", "us_tn_film_incentive", "us_ok_ofer",
    "us_al_film_incentive", "us_ky_keiia",
    # Canadian Provinces (4)
    "ca_ab_fttc", "ca_mb_fvptc", "ca_ns_pif", "ca_nb_film_credit",
    # Europe (9)
    "nl_nfpi", "at_fisa_plus", "cz_film_incentive", "ro_cnc_rebate",
    "pt_film_incentive", "rs_film_rebate", "is_film_reimbursement",
    "gb_sct_screen_fund", "gb_wls_screen_fund",
    # Asia-Pacific (4)
    "sg_sfc_production", "au_nsw_screen", "au_vic_vicscreen", "au_qld_screen_qld",
    # Latin America (5)
    "co_film_colombia", "do_film_incentive", "uy_xxi_incentive",
    "ar_incaa_incentive", "br_ancine_incentive",
    # Middle East (3)
    "ae_dpip", "sa_sfc_rebate", "jo_rfc_rebate",
    # Africa (2)
    "ma_ccm_rebate", "za_nfvf_rebate",
]

# Exactly 21 labor_type categories (matches all other migrations)
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
