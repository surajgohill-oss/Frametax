"""0023 — ProgramAdminDetails for 43 extended (DISCOVERY-tier) programs.

Seeds ProgramAdminDetails rows for all programs introduced in migration 0015
(global_inventory_extended.py). All entries are DISCOVERY tier — financing
and admin details not confirmed from primary source.

Programs covered (43):
  US States (16): OR, WA, IL, NC, SC, MA, TX, CT, PA, MD, VA, CO, TN, OK, AL, KY
  CA Provinces (4): AB, MB, NS, NB
  Europe (9): NL, AT, CZ, RO, PT, RS, IS, GB-SCT, GB-WLS
  Asia-Pacific (4): SG, AU-NSW, AU-VIC, AU-QLD
  Latin America (5): CO, DO, UY, AR, BR
  Middle East (3): AE, SA, JO
  Africa (2): MA, ZA

Revision ID: 0023
Revises: 0022
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0023-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_DISCOVERY_ASSIGN_NOTES = (
    "DISCOVERY tier — assignability to lenders and bridge financing terms "
    "not confirmed from primary source. Treat as uncollateralisable for "
    "conservative budget modelling until verified."
)
_DISCOVERY_FIN_NOTES = (
    "DISCOVERY tier — processing timeline, bridge lending availability, "
    "and financing terms not confirmed from primary source."
)
_DISCOVERY_WINDOW = (
    "Application typically required before commencement of qualifying "
    "production activity in the relevant jurisdiction. Verify with local "
    "film office before pre-production."
)

# (slug, program_label, pay_notes_suffix)
# Fields not listed default to None (UNKNOWN) for DISCOVERY tier.
_ADMIN_DETAILS: list[tuple[str, str]] = [
    # --- US States ---
    ("us_or_opif",          "Oregon OPIF cash rebate"),
    ("us_wa_mpcp",          "Washington MPCP competitive cash rebate"),
    ("us_il_film_credit",   "Illinois Film Tax Credit"),
    ("us_nc_film_grant",    "North Carolina Film & Entertainment Grant"),
    ("us_sc_film_credit",   "South Carolina Film Production Credit"),
    ("us_ma_film_credit",   "Massachusetts Film Tax Credit"),
    ("us_tx_miip",          "Texas MIIP cash rebate"),
    ("us_ct_film_credit",   "Connecticut Film Tax Credit"),
    ("us_pa_film_credit",   "Pennsylvania Film Production Tax Credit"),
    ("us_md_film_credit",   "Maryland Film Production Activity Tax Credit"),
    ("us_va_film_credit",   "Virginia Motion Picture Production Tax Credit"),
    ("us_co_film_incentive","Colorado Film Incentive cash rebate"),
    ("us_tn_film_incentive","Tennessee Film Incentives"),
    ("us_ok_ofer",          "Oklahoma Film Enhancement Rebate"),
    ("us_al_film_incentive","Alabama Film Incentive"),
    ("us_ky_keiia",         "Kentucky KEIIA refundable tax credit"),
    # --- Canadian Provinces ---
    ("ca_ab_fttc",          "Alberta Film and Television Tax Credit"),
    ("ca_mb_fvptc",         "Manitoba Film & Video Production Tax Credit"),
    ("ca_ns_pif",           "Nova Scotia Film & TV Production Incentive Fund"),
    ("ca_nb_film_credit",   "New Brunswick Film Tax Credit"),
    # --- Europe ---
    ("nl_nfpi",             "Netherlands Film Production Incentive (NFPI)"),
    ("at_fisa_plus",        "Austria FISA+ Film Production Support"),
    ("cz_film_incentive",   "Czech Film Incentive cash rebate"),
    ("ro_cnc_rebate",       "Romanian CNC Film Office Cash Rebate"),
    ("pt_film_incentive",   "Portugal Film Commission Incentive"),
    ("rs_film_rebate",      "Serbia Film Commission Cash Rebate"),
    ("is_film_reimbursement","Icelandic Film Reimbursement Scheme"),
    ("gb_sct_screen_fund",  "Screen Scotland Production Growth Fund"),
    ("gb_wls_screen_fund",  "Wales Screen Production Fund"),
    # --- Asia-Pacific ---
    ("sg_sfc_production",   "Singapore Film Commission Production Assistance"),
    ("au_nsw_screen",       "NSW Government Screen Incentive (Create NSW)"),
    ("au_vic_vicscreen",    "VicScreen Production Investment"),
    ("au_qld_screen_qld",   "Screen Queensland Production Attraction Strategy"),
    # --- Latin America ---
    ("co_film_colombia",    "Colombia Film Commission — Film In Colombia"),
    ("do_film_incentive",   "Dominican Republic Film Commission Incentive"),
    ("uy_xxi_incentive",    "Uruguay XXI Film Incentive"),
    ("ar_incaa_incentive",  "INCAA Argentine Film Institute Incentives"),
    ("br_ancine_incentive", "ANCINE Brazilian Film Commission Tax Incentives"),
    # --- Middle East ---
    ("ae_dpip",             "Dubai Film Commission DPIP cashback"),
    ("sa_sfc_rebate",       "Saudi Film Commission Production Rebate"),
    ("jo_rfc_rebate",       "Royal Film Commission Jordan Production Rebate"),
    # --- Africa ---
    ("ma_ccm_rebate",       "CCM Morocco Production Rebate"),
    ("za_nfvf_rebate",      "NFVF South Africa Foreign Film & TV Production Rebate"),
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
                "assign_notes": _DISCOVERY_ASSIGN_NOTES,
                "fin_notes": _DISCOVERY_FIN_NOTES,
                "window_open": _DISCOVERY_WINDOW,
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
