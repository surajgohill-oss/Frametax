"""0031 — ProgramSpendTreatment for 43 wave-3 programs (DISCOVERY tier).

Seeds exactly 21 ProgramSpendTreatment rows per program for all programs
added in migration 0029. All entries are DISCOVERY tier.

Treatment rules applied:
  - contingency: DOES_NOT_QUALIFY (False) — universal across all programs
  - all other categories: UNKNOWN (None) — not confirmed from primary source

Revision ID: 0031
Revises: 0030
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: Union[str, None] = "0030"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0031-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_SLUGS: list[str] = [
    # US states wave 3
    "us_ga_film_credit", "us_la_film_incentive", "us_nm_film_credit",
    "us_ny_film_credit", "us_nv_film_incentive", "us_ri_film_credit",
    # Caribbean & Central America
    "bs_film_incentive", "bb_film_incentive", "pa_film_incentive", "cr_film_incentive",
    # South America
    "pe_film_incentive", "ec_film_incentive",
    # Africa
    "eg_film_incentive", "gh_film_incentive", "rw_film_incentive",
    "tz_film_incentive", "sn_film_incentive",
    # Gulf States
    "kw_film_incentive", "bh_film_incentive",
    # Central Asia / Caucasus
    "ge_film_incentive", "kz_film_incentive", "am_film_incentive",
    # Southeast Asia
    "vn_film_incentive", "id_film_incentive", "kh_film_incentive",
    # East Asia
    "jp_film_incentive", "tw_film_incentive", "hk_film_incentive",
    # Balkans / Additional Europe
    "al_film_incentive", "me_film_incentive", "mk_film_incentive", "ba_film_incentive",
    # Pacific
    "fj_film_incentive",
    # Grants / Funds
    "ibermedia_programme", "de_fff_bayern", "de_nrw_filmstiftung", "hk_film_dev_fund",
    "in_nfdc_coproduction", "sg_imda_film_fund", "tw_taicca_fund",
    "film_i_vast", "acpfilms_fund", "us_itvs_fund",
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
