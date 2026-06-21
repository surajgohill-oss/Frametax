"""0027 — ProgramAdminDetails for 47 wave-2 programs (DISCOVERY tier).

Seeds ProgramAdminDetails for all 47 programs added in migration 0026.
All entries are DISCOVERY tier — financing/admin details not confirmed.

Revision ID: 0027
Revises: 0026
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: Union[str, None] = "0026"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0027-0000-0001-000000000000")

_DISC = "DISCOVERY"
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


# (slug, label)
_ADMIN_DETAILS: list[tuple[str, str]] = [
    # US states/territories
    ("us_hi_film_tax_credit",  "Hawaii Film and Digital Media Income Tax Credit"),
    ("us_ut_film_incentive",   "Utah Motion Picture Incentive Program"),
    ("us_mn_film_credit",      "Minnesota Film Production Tax Credit"),
    ("us_ms_film_credit",      "Mississippi Advantage Film Program"),
    ("us_az_film_credit",      "Arizona Motion Picture Production Program"),
    ("us_pr_film_incentive",   "Puerto Rico Film Industry Economic Incentives Act"),
    # Canadian provinces
    ("ca_sk_production_grant", "Creative Saskatchewan Film and TV Production Grant"),
    ("ca_nl_production_fund",  "Newfoundland & Labrador Film Development Corp Production Incentive"),
    # Europe
    ("se_film_incentive",      "Sweden Film Commission Production Rebate"),
    ("no_film_incentive",      "Norwegian Film Commission Production Incentive"),
    ("fi_film_incentive",      "Business Finland Film Incentive"),
    ("dk_film_incentive",      "Danish Film Institute Production Support"),
    ("pl_film_incentive",      "Polish Film Institute (PISF) Cash Rebate"),
    ("bg_film_incentive",      "Bulgarian Film Commission Cash Rebate"),
    ("ee_film_incentive",      "Film Estonia Cash Rebate"),
    ("lt_film_incentive",      "Lithuanian Film Centre Production Cash Rebate"),
    ("lv_film_incentive",      "National Film Centre of Latvia Production Incentive"),
    ("sk_film_incentive",      "Slovak Audiovisual Fund (AVF) Production Incentive"),
    ("lu_film_incentive",      "Film Fund Luxembourg — Tax Shelter & Production Rebate"),
    ("tr_film_incentive",      "Turkey Cinema General Directorate Production Support"),
    # Asia-Pacific
    ("th_film_incentive",      "Thailand BOI Film Production Incentive"),
    ("my_film_incentive",      "FINAS Malaysia Film Rebate"),
    ("ph_film_incentive",      "Film Development Council of the Philippines (FDCP) Incentive"),
    ("kr_film_incentive",      "Korea Film Council (KOFIC) Location Incentive"),
    ("in_national_film",       "India NFDC and State Incentives"),
    ("lk_film_incentive",      "Sri Lanka Film Commission Production Incentive"),
    # Latin America & Caribbean
    ("mx_eficine_incentive",   "Mexico EFICINE (Article 226) and PROCINE Fund"),
    ("cl_corfo_incentive",     "Chile Corfo Film Incentive"),
    ("jm_film_incentive",      "Jamaica Entertainment Industry Incentive Programme"),
    ("tt_film_incentive",      "Trinidad & Tobago Creative Industries Production Incentive"),
    # Middle East & Africa
    ("il_film_incentive",      "Israel Film Fund / Maslool Incentive"),
    ("qa_film_incentive",      "Qatar Film Commission Production Incentive"),
    ("tn_film_incentive",      "Tunisia CNCI Cash Rebate"),
    ("ke_film_incentive",      "Kenya Film Commission (KFC) Production Incentive"),
    ("ng_film_incentive",      "Nigeria NFC / Creative Economy Incentive"),
    # Grants / Funds
    ("eu_eurimages",           "Eurimages — Council of Europe Co-production Fund"),
    ("eu_media_fund",          "Creative Europe MEDIA Programme"),
    ("nordic_ftvf",            "Nordisk Film & TV Fond"),
    ("ca_cmf",                 "Canada Media Fund (CMF) — Convergent Stream"),
    ("ca_telefilm_dev",        "Telefilm Canada — Canada Feature Film Fund (CFFF)"),
    ("gb_bfi_production",      "BFI Film Fund — Production Funding"),
    ("fr_cnc_production",      "CNC France — Avances sur Recettes"),
    ("au_screen_production",   "Screen Australia — Production Funding"),
    ("nl_hbf",                 "Hubert Bals Fund (IFFR) — Development and Production Fund"),
    ("qa_dfi_fund",            "Doha Film Institute — Grants for Filmmakers"),
    ("us_sundance_doc",        "Sundance Institute — Documentary Fund"),
    ("za_dac_fund",            "NFVF South Africa — Development and Production Fund"),
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
