"""0037 — ProgramSpendTreatment for 13 wave-5 programs (DISCOVERY tier).

13 programs × 21 labor types = 273 rows.
contingency → DOES_NOT_QUALIFY; all others → UNKNOWN (DISCOVERY tier).

Revision ID: 0037
Revises: 0036
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0037"
down_revision: Union[str, None] = "0036"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0037-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_SLUGS: list[str] = [
    "ch_film_support", "si_film_incentive", "ua_film_incentive",
    "ru_film_incentive", "by_film_incentive", "md_film_incentive",
    "cu_film_incentive", "ir_film_incentive", "dz_film_incentive",
    "ga_film_incentive", "sc_film_incentive", "mv_film_incentive",
    "bt_film_incentive",
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
            qualifies = False if labor_type == "contingency" else None
            notes = _CONTINGENCY_NOTE if labor_type == "contingency" else _UNKNOWN_NOTE
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
                          WHERE t.program_id = p.id AND t.labor_type = :labor_type
                      )
                    LIMIT 1
                """),
                {
                    "id": _uid(f"treatment:{slug}:{labor_type}"),
                    "slug": slug, "labor_type": labor_type,
                    "qualifies": qualifies, "notes": notes, "now": NOW,
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
