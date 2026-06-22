"""0033 — ProgramAdminDetails for 21 wave-4 programs (DISCOVERY tier).

Seeds ProgramAdminDetails for all 21 programs added in migration 0032.
All entries are DISCOVERY tier.

Revision ID: 0033
Revises: 0032
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: Union[str, None] = "0032"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0033-0000-0001-000000000000")

_DISC_ASSIGN_NOTES = (
    "DISCOVERY tier — assignability to lenders and bridge financing terms "
    "not confirmed from primary source. Treat as uncollateralisable for "
    "conservative budget modelling until verified."
)
_DISC_FIN_NOTES = (
    "DISCOVERY tier — processing timeline, bridge lending availability, "
    "and financing terms not confirmed from primary source."
)
_DISC_WINDOW = (
    "Application typically required before commencement of qualifying "
    "production activity in the relevant jurisdiction. Verify with local "
    "film office before pre-production."
)


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_ADMIN_DETAILS: list[tuple[str, str]] = [
    ("az_film_incentive",  "Azerbaijan Film Fund Production Support"),
    ("uz_film_incentive",  "Uzbekkino National Film Support Program"),
    ("om_film_commission", "Oman Film Commission Production Support"),
    ("lb_film_incentive",  "Centre du Cinéma Libanais (CCL) Production Support"),
    ("ve_cnac_fund",       "CNAC Venezuela Film Production Fund"),
    ("gy_film_commission", "Guyana Tourism Authority Film Production Support"),
    ("gt_film_commission", "Guatemala Film Commission (INGUAT) Production Facilitation"),
    ("na_film_commission", "Namibia Film Commission Production Incentive"),
    ("bw_film_commission", "Botswana Film Commission Production Support"),
    ("et_film_commission", "Ethiopian Film Commission Production Support"),
    ("ci_film_incentive",  "Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support"),
    ("cm_film_incentive",  "Cameroon Centre National de la Cinématographie Film Support"),
    ("ao_film_incentive",  "Angola Instituto do Cinema e Audiovisual (ICA) Production Support"),
    ("ug_film_commission", "Uganda Film Commission Production Support"),
    ("mz_film_incentive",  "Mozambique Instituto do Cinema Film Support"),
    ("zm_film_commission", "Zambia Film Commission Production Support"),
    ("zw_film_commission", "Zimbabwe Film and Broadcasting Authority Production Support"),
    ("cn_film_incentive",  "China Film Administration Domestic Co-production Support"),
    ("mn_film_commission", "Mongolian Film Commission Production Support"),
    ("mo_film_fund",       "Macau Cultural Industries Fund Film Production Support"),
    ("bd_film_incentive",  "Bangladesh Film Development Corporation (BFDC) Production Support"),
]


def upgrade() -> None:
    conn = op.get_bind()

    for slug, label in _ADMIN_DETAILS:
        pay_notes = (
            f"{label} — payment timing, audit requirements, and processing "
            "timeline not confirmed from primary source. DISCOVERY tier."
        )
        notes = (
            f"{label} admin and financing details: DISCOVERY tier. "
            "No primary source verification completed. "
            "Verify with local film office / funding body before budget finalisation."
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
                "slug": slug,
                "pay_notes": pay_notes,
                "assign_notes": _DISC_ASSIGN_NOTES,
                "fin_notes": _DISC_FIN_NOTES,
                "window_open": _DISC_WINDOW,
                "notes": notes,
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug, _ in _ADMIN_DETAILS:
        conn.execute(
            sa.text("DELETE FROM program_admin_details WHERE id = :id"),
            {"id": _uid(f"admin:{slug}")},
        )
