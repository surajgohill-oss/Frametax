"""0034 — ProgramSpendTreatment for 21 wave-4 programs (DISCOVERY tier).

Seeds exactly 21 ProgramSpendTreatment rows per program for all programs
added in migration 0032. All entries are DISCOVERY tier.

Treatment rules applied:
  - contingency: DOES_NOT_QUALIFY (False) — universal across all programs
  - all other categories: UNKNOWN (None) — not confirmed from primary source

Revision ID: 0034
Revises: 0033
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: Union[str, None] = "0033"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0034-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_SLUGS: list[str] = [
    "az_film_incentive", "uz_film_incentive", "om_film_commission",
    "lb_film_incentive", "ve_cnac_fund", "gy_film_commission",
    "gt_film_commission", "na_film_commission", "bw_film_commission",
    "et_film_commission", "ci_film_incentive", "cm_film_incentive",
    "ao_film_incentive", "ug_film_commission", "mz_film_incentive",
    "zm_film_commission", "zw_film_commission", "cn_film_incentive",
    "mn_film_commission", "mo_film_fund", "bd_film_incentive",
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
            else:
                qualifies = None
                notes = _UNKNOWN_NOTE

            conn.execute(
                sa.text("""
                    INSERT INTO program_spend_treatments (
                        id, program_id, labor_type,
                        qualifies, treatment_notes, confidence_tier,
                        created_at, updated_at
                    )
                    SELECT
                        :id, p.id, :labor_type,
                        :qualifies, :notes, 'DISCOVERY',
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
