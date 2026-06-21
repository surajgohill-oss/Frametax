"""0020 — ProgramAdminDetails for 10 remaining Tier-1 programs.

Fills the gap for: ca_federal_cptc, on_ofttc, or_opif, nm_film_production,
nohfc_production_fund, fr_trip, it_tax_credit_foreign, cy_film_rebate,
hr_cash_rebate, hu_hipa_rebate.

Revision ID: 0020
Revises: 0019
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0020-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# (slug, payment_timing_weeks, payment_timing_notes, audit_required,
#  audit_authority, audit_cost_estimate_usd, is_assignable, assignability_notes,
#  processing_timeline_weeks, financing_friction_notes,
#  first_window_open_relative, final_claim_deadline, confidence_tier, notes)
_ADMIN_DETAILS = [
    (
        "ca_federal_cptc",
        52,
        "CRA processes CPTC refund via corporate tax return. Timeline 10-14 months from filing.",
        True,
        "Canada Revenue Agency (CRA) + CAVCO (Canadian Audio-Visual Certification Office) — "
        "CAVCO Part A/B certification required before CRA filing",
        20_000,
        False,
        "CPTC is refundable via CRA tax return — not directly assignable. "
        "Bridge financing available from Canadian chartered banks secured against expected refund.",
        52,
        "Canadian chartered banks (TD, RBC, BNS, BDC) routinely lend against CPTC. "
        "Refundable credit — no transfer market needed. "
        "Timeline 10–14 months is predictable and well-understood by Canadian lenders.",
        "CAVCO Part A application filed before production commences",
        "CAVCO Part B (completion) filed within 24 months of end of tax year of production",
        "PARSED",
        "Canada Federal CPTC admin details from CAVCO/CRA T4283 programme documentation.",
    ),
    (
        "on_ofttc",
        39,
        "Ontario Creates processes OFTTC within 8-10 months from audit completion.",
        True,
        "Ontario Creates — CPA audit of Ontario labour expenditures required",
        18_000,
        False,
        "OFTTC is NOT directly assignable. "
        "Bridge financing from Canadian chartered banks secured against expected refund. "
        "Cannot be bridged via secondary market.",
        39,
        "Strong Canadian bridge lending market for Ontario OFTTC. "
        "Chartered banks lend against OFTTC refundable credit at predictable rates. "
        "Timeline 8–10 months is well-understood in Canadian film finance market.",
        "Application filed with Ontario Creates before principal photography commences",
        "Final cost report and audit filed within 24 months of production completion",
        "PARSED",
        "Ontario OFTTC admin details from Ontario Creates programme documentation.",
    ),
    (
        "or_opif",
        26,
        "Oregon Film processes OPIF rebates within 5-7 months of complete application.",
        True,
        "Oregon Film + Oregon Business Development Department (BDD) — "
        "independent CPA certification of Oregon qualifying expenditures required",
        12_000,
        None,
        "Oregon OPIF bridge lending not well-established in international market. "
        "Assignability to lenders not confirmed from primary source. "
        "Treat as uncollateralisable for conservative budget modelling.",
        26,
        "OPIF is a direct cash rebate paid by Oregon. "
        "Limited bridge lending infrastructure vs Louisiana or New Mexico. "
        "5–7 month processing timeline is predictable.",
        "Oregon Film Office pre-certification required before production commences in Oregon",
        "Rebate claim filed within 6 months of completion of Oregon qualifying production",
        "PARSED",
        "Oregon OPIF admin details from Oregon Film Office programme documentation.",
    ),
    (
        "nm_film_production",
        39,
        "NM Film Office / NMTRD processes refund within 8-10 months of audit completion.",
        True,
        "New Mexico Film Office + NM Taxation and Revenue Department (NMTRD) — "
        "certified New Mexico CPA audit required",
        15_000,
        True,
        "NM film credit is refundable and can be assigned to lenders. "
        "Active bridge lending market for New Mexico credits. "
        "Western Commerce Bank and other NM-focused lenders accept credit assignments.",
        39,
        "Strong regional bridge lending for NM film credit. "
        "Refundable and assignable credit. "
        "8–10 month processing timeline predictable and well-understood.",
        "Production must be registered with NM Film Office before principal photography",
        "Refund claim filed with NMTRD within 2 years of end of qualifying production",
        "PARSED",
        "New Mexico film credit admin details from NM Film Office and NMTRD documentation.",
    ),
    (
        "nohfc_production_fund",
        None,
        "NOHFC award timeline is variable and discretionary. "
        "Grant disbursement occurs after project approval and milestone achievement. "
        "No fixed payment timeline.",
        True,
        "Northern Ontario Heritage Fund Corporation (NOHFC) — "
        "project reporting and milestone audits required post-award",
        5_000,
        False,
        "NOHFC grant is paid directly to the production company and is NOT assignable. "
        "Discretionary award — cannot be used as collateral for bridge financing. "
        "Budget modelling must not assume NOHFC until award confirmed.",
        None,
        "NOHFC is discretionary — no guarantee of award. "
        "Cannot be bridged. "
        "Critical: NOHFC grant must be deducted from OPSTC and CPTC qualifying spend basis "
        "per government assistance rules (ITA § 125.4(1) and Ontario Reg 37/09).",
        "Application submitted to NOHFC before production commences in Northern Ontario; "
        "must demonstrate Northern Ontario production activity",
        "Project completion report submitted to NOHFC within 12 months of production completion",
        "PARSED",
        "NOHFC admin details from NOHFC programme documentation. "
        "Grant reduces OPSTC and CPTC qualifying spend via government assistance rules.",
    ),
    (
        "fr_trip",
        26,
        "CNC processes TRIP reimbursements within 5-7 months of complete claim submission.",
        True,
        "CNC (Centre national du cinéma et de l'image animée) — "
        "French certified accountant audit of French production expenditures required",
        18_000,
        True,
        "French TRIP credit can be assigned to lenders. "
        "French banks (BNP Paribas Media, Société Générale) are familiar with TRIP financing. "
        "Interim claims not available — single post-production claim.",
        39,
        "CNC is efficient relative to Spain/Italy. "
        "Credit assignable to banks — bridge financing available at standard French rates. "
        "5–7 month CNC processing is predictable.",
        "Application registered with CNC before commencement of French qualifying expenditure",
        "Final claim submitted to CNC within 24 months of production completion",
        "PARSED",
        "France CNC TRIP admin details from CNC programme documentation and market knowledge.",
    ),
    (
        "it_tax_credit_foreign",
        65,
        "Italian Ministry processing is slow. 12-18 months from audit to credit certification.",
        True,
        "DGCinema (Direzione Generale Cinema e Audiovisivo) — "
        "Italian certified accountant audit required; MiC approval required",
        20_000,
        True,
        "Italian tax credit can be assigned to Italian tax-paying entities or lenders. "
        "Italian banks (Mediobanca, UniCredit) provide film finance against Italian credit. "
        "Secondary market less liquid than UK or France.",
        65,
        "Italian public administration is slow. "
        "12–18 month processing is typical; delays common. "
        "Bridge financing available through Italian banks at higher carry cost than UK/France. "
        "Recommend carry cost assumption of 18 months minimum.",
        "Application submitted to DGCinema before commencement of Italian production",
        "Final audit and claim submitted within 12 months of completion of Italian production",
        "PARSED",
        "Italy DGCinema admin details from DGCinema programme documentation and market knowledge.",
    ),
    (
        "cy_film_rebate",
        30,
        "Cyprus Film Advisory Body processes rebate within 6-8 months of audit completion.",
        True,
        "Cyprus Investment Promotion Agency (Invest Cyprus) + Ministry of Finance — "
        "independent auditor required",
        12_000,
        None,
        "Assignability of Cyprus rebate to international lenders not confirmed from primary source. "
        "Cyprus film market is developing — bridge lending infrastructure limited.",
        30,
        "Limited international bridge lending infrastructure for Cyprus rebate. "
        "Treat as uncollateralisable for conservative budget modelling. "
        "6–8 month processing predictable.",
        "Application submitted before commencement of production in Cyprus",
        "Final audit and rebate claim submitted within 6 months of production completion",
        "PARSED",
        "Cyprus film rebate admin details from Invest Cyprus programme documentation.",
    ),
    (
        "hr_cash_rebate",
        39,
        "HAVC processes rebate claims within 8-10 months of complete audit.",
        True,
        "HAVC (Croatian Audiovisual Centre) — certified Croatian accountant audit required",
        12_000,
        None,
        "Assignability of Croatian rebate to international lenders not confirmed. "
        "Croatian film finance market has limited bridge lending infrastructure.",
        39,
        "Limited international bridge lending for Croatian rebate. "
        "8–10 month processing predictable. "
        "Treat as uncollateralisable for conservative initial budget models.",
        "Application submitted to HAVC before commencement of Croatian production",
        "Final audit and claim submitted within 9 months of production completion",
        "PARSED",
        "Croatia HAVC cash rebate admin details from HAVC programme documentation.",
    ),
    (
        "hu_hipa_rebate",
        26,
        "HIPA + NFI process rebate efficiently within 5-7 months of complete application.",
        True,
        "HIPA (Hungarian Investment Promotion Agency) + National Film Institute Hungary (NFI) — "
        "independent auditor required; Hungarian CPA certification",
        15_000,
        True,
        "Hungarian rebate has active bridge lending market. "
        "OTP Bank and other Hungarian institutions lend against HIPA rebate. "
        "Hungary has one of the most developed film finance markets in CEE.",
        26,
        "Best financing infrastructure in CEE for film production. "
        "HIPA rebate is assignable to lenders. "
        "5–7 month processing is among the fastest in Europe. "
        "OTP Bank routinely provides bridge financing against HIPA rebate.",
        "Application submitted to HIPA before commencement of Hungarian production; "
        "HIPA approval letter required before principal photography",
        "Final audit and rebate claim submitted within 6 months of production completion",
        "PARSED",
        "Hungary HIPA admin details from HIPA programme documentation and market knowledge.",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    for (slug, pay_weeks, pay_notes, audit_req, audit_auth, audit_cost,
         is_assign, assign_notes, proc_weeks, fin_friction,
         window_open, claim_deadline, tier, notes) in _ADMIN_DETAILS:
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
                    :pay_weeks, :pay_notes,
                    :audit_req, :audit_auth, :audit_cost,
                    :is_assign, :assign_notes,
                    :proc_weeks, :fin_friction,
                    :window_open, :claim_deadline,
                    :tier, :notes, :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_admin_details d WHERE d.program_id = p.id
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"admin:{slug}"), "slug": slug,
                "pay_weeks": pay_weeks, "pay_notes": pay_notes,
                "audit_req": audit_req, "audit_auth": audit_auth, "audit_cost": audit_cost,
                "is_assign": is_assign, "assign_notes": assign_notes,
                "proc_weeks": proc_weeks, "fin_friction": fin_friction,
                "window_open": window_open, "claim_deadline": claim_deadline,
                "tier": tier, "notes": notes, "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug, *_ in _ADMIN_DETAILS:
        conn.execute(
            sa.text("DELETE FROM program_admin_details WHERE id = :id"),
            {"id": _uid(f"admin:{slug}")},
        )
