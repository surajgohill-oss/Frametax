"""0030 — ProgramAdminDetails for 43 wave-3 programs (DISCOVERY tier).

Seeds ProgramAdminDetails for all 43 programs added in migration 0029.
All entries are DISCOVERY tier — financing/admin details not confirmed.

Revision ID: 0030
Revises: 0029
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0030"
down_revision: Union[str, None] = "0029"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0030-0000-0001-000000000000")

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
    # US states wave 3
    ("us_ga_film_credit",    "Georgia Entertainment Industry Investment Act"),
    ("us_la_film_incentive", "Louisiana Motion Picture Production Program"),
    ("us_nm_film_credit",    "New Mexico Film Production Tax Credit"),
    ("us_ny_film_credit",    "New York State Film Tax Credit Program"),
    ("us_nv_film_incentive", "Nevada Film Incentive Program"),
    ("us_ri_film_credit",    "Rhode Island Motion Picture Production Tax Credit"),
    # Caribbean & Central America
    ("bs_film_incentive",    "Bahamas Film Commission Production Support"),
    ("bb_film_incentive",    "Barbados Film and Entertainment Production Incentives"),
    ("pa_film_incentive",    "Panama Film Commission Production Facilitation"),
    ("cr_film_incentive",    "Costa Rica Film Commission Production Facilitation"),
    # South America
    ("pe_film_incentive",    "Peru DAFO Film Production Support"),
    ("ec_film_incentive",    "Ecuador Film Commission Production Facilitation"),
    # Africa
    ("eg_film_incentive",    "Egypt Film Commission Production Support"),
    ("gh_film_incentive",    "Ghana National Film Authority Production Support"),
    ("rw_film_incentive",    "Rwanda Development Board Film Production Support"),
    ("tz_film_incentive",    "Tanzania Film Board Production Facilitation"),
    ("sn_film_incentive",    "Senegal Bureau d'Accueil des Tournages Film Support"),
    # Gulf States
    ("kw_film_incentive",    "Kuwait Film Committee Production Support"),
    ("bh_film_incentive",    "Bahrain Film Commission Production Support"),
    # Central Asia / Caucasus
    ("ge_film_incentive",    "Georgian National Film Centre Production Incentive"),
    ("kz_film_incentive",    "Kazakhfilm Studios Production Facilitation"),
    ("am_film_incentive",    "National Cinema Centre of Armenia Production Support"),
    # Southeast Asia
    ("vn_film_incentive",    "Vietnam Cinema Department Production Facilitation"),
    ("id_film_incentive",    "Indonesian Film Commission Production Facilitation"),
    ("kh_film_incentive",    "Cambodia Ministry of Culture Film Production Facilitation"),
    # East Asia
    ("jp_film_incentive",    "Japan Film Commission Location Incentive (JLOC)"),
    ("tw_film_incentive",    "Taiwan Film and Audiovisual Institute (TFAI) Cash Rebate"),
    ("hk_film_incentive",    "Create Hong Kong (CreateHK) Production Support"),
    # Balkans / Additional Europe
    ("al_film_incentive",    "Albanian National Cinema Agency (ANCA) Cash Rebate"),
    ("me_film_incentive",    "Film Centre of Montenegro Production Incentive"),
    ("mk_film_incentive",    "Macedonian Film Agency (MFA) Cash Rebate"),
    ("ba_film_incentive",    "Film Centre Bosnia and Herzegovina Production Support"),
    # Pacific
    ("fj_film_incentive",    "Fiji Audio Visual Commission Production Incentive"),
    # Grants / Funds
    ("ibermedia_programme",  "IBERMEDIA Programme for Ibero-American Co-productions"),
    ("de_fff_bayern",        "FilmFernsehFonds Bayern (FFF Bayern)"),
    ("de_nrw_filmstiftung",  "Film und Medienstiftung NRW"),
    ("hk_film_dev_fund",     "Hong Kong Film Development Fund (FDF)"),
    ("in_nfdc_coproduction", "NFDC International Co-production Development Fund"),
    ("sg_imda_film_fund",    "IMDA Singapore — Feature Film Production Grant"),
    ("tw_taicca_fund",       "Taiwan Creative Content Agency (TAICCA) International Co-production Fund"),
    ("film_i_vast",          "Film i Väst — Regional Co-production Fund"),
    ("acpfilms_fund",        "ACP Films — EU-ACP Cultural Film Co-production Fund"),
    ("us_itvs_fund",         "ITVS International Documentary Fund"),
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
