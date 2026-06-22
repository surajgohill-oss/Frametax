"""0036 — ProgramAdminDetails for 13 wave-5 programs (DISCOVERY tier).

Revision ID: 0036
Revises: 0035
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: Union[str, None] = "0035"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0036-0000-0001-000000000000")

_DISC_ASSIGN_NOTES = (
    "DISCOVERY tier — assignability to lenders not confirmed from primary source."
)
_DISC_FIN_NOTES = (
    "DISCOVERY tier — processing timeline and financing terms not confirmed."
)
_DISC_WINDOW = (
    "Application typically required before commencement of qualifying production. "
    "Verify with local film office before pre-production."
)


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_ADMIN_DETAILS: list[tuple[str, str]] = [
    ("ch_film_support",   "Swiss Federal Office of Culture (FOC) Film Support"),
    ("si_film_incentive", "Slovenian Film Centre (SFC) Cash Rebate and Production Support"),
    ("ua_film_incentive", "Ukrainian State Film Agency Production Support"),
    ("ru_film_incentive", "Russian Cinema Fund (Fond Kino) Production Support"),
    ("by_film_incentive", "Belarusfilm National Film Studio Production Support"),
    ("md_film_incentive", "National Centre for Cinematography Moldova (NCFM)"),
    ("cu_film_incentive", "ICAIC Cuba Film Production Support"),
    ("ir_film_incentive", "Farabi Cinema Foundation Film Production Support"),
    ("dz_film_incentive", "Centre Algérien pour le Développement du Cinéma (CADC) Film Support"),
    ("ga_film_incentive", "Gabon Ministry of Culture Film Commission Support"),
    ("sc_film_incentive", "Seychelles Tourism Board Film Production Support"),
    ("mv_film_incentive", "Maldives Marketing and PR Corporation (MMPRC) Film Facilitation"),
    ("bt_film_incentive", "Bhutan Film Commission / Tourism Council Production Facilitation"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for slug, label in _ADMIN_DETAILS:
        pay_notes = (
            f"{label} — payment timing not confirmed from primary source. DISCOVERY tier."
        )
        notes = (
            f"{label}: DISCOVERY tier. No primary source verification completed. "
            "Verify with local film office before budget finalisation."
        )
        conn.execute(
            sa.text("""
                INSERT INTO program_admin_details (
                    id, program_id,
                    payment_timing_weeks, payment_timing_notes,
                    audit_required, audit_authority, audit_cost_estimate_usd,
                    is_assignable, assignability_notes,
                    processing_timeline_weeks, financing_friction_notes,
                    first_window_open_relative, final_claim_deadline,
                    confidence_tier, notes, created_at, updated_at
                )
                SELECT
                    :id, p.id,
                    NULL, :pay_notes,
                    NULL, NULL, NULL,
                    NULL, :assign_notes,
                    NULL, :fin_notes,
                    :window_open, NULL,
                    'DISCOVERY', :notes, :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_admin_details d WHERE d.program_id = p.id
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"admin:{slug}"),
                "slug": slug, "pay_notes": pay_notes,
                "assign_notes": _DISC_ASSIGN_NOTES,
                "fin_notes": _DISC_FIN_NOTES,
                "window_open": _DISC_WINDOW,
                "notes": notes, "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug, _ in _ADMIN_DETAILS:
        conn.execute(
            sa.text("DELETE FROM program_admin_details WHERE id = :id"),
            {"id": _uid(f"admin:{slug}")},
        )
