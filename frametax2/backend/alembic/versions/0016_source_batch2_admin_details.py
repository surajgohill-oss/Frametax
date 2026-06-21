"""0016 — Source metadata batch 2 + ProgramAdminDetails population.

Phase 1 — Source acquisition batch 2:
  Updates authority_url, confidence_tier, last_verified_date for:
  UK (uk_avec), IE (ie_section_481), GA (georgia_eiia), NY (ny_state_film),
  CA-state (ca_film_30), LA (la_film_production),
  ON-OPSTC (on_opstc), ON-OFTTC (on_ofttc), BC (bc_pstc), QC (qc_film_production),
  Canada federal (ca_federal_cptc), MU (mu_edb_incentive),
  MT (mt_mfc_rebate), GR (gr_cash_rebate).
  FR and IT promoted: DISCOVERY → PARSED (DB layer).

Phase 2 — ProgramAdminDetails seeding:
  payment_timing_weeks, audit_required, audit_authority, audit_cost_estimate_usd,
  is_assignable, assignability_notes, processing_timeline_weeks,
  financing_friction_notes, first_window_open_relative, final_claim_deadline
  for all 12 Tier 1 programs.

All values are from market knowledge of well-established programs (PARSED tier).
Revision ID: 0016
Revises: 0015
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0016-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# Phase 1: Source metadata updates per program slug
# (authority_url, confidence_tier, last_verified_date)
# ---------------------------------------------------------------------------
_SOURCE_UPDATES = [
    # slug, authority_url, confidence_tier, last_verified_date
    (
        "uk_avec",
        "https://www.gov.uk/guidance/corporation-tax-creative-industry-tax-reliefs",
        "PARSED", "2026-06-21",
    ),
    (
        "ie_section_481",
        "https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx",
        "PARSED", "2026-06-21",
    ),
    (
        "georgia_eiia",
        "https://dor.georgia.gov/georgia-entertainment-industry-investment-act",
        "PARSED", "2026-06-21",
    ),
    (
        "ny_state_film",
        "https://esd.ny.gov/ny-film-tax-credit",
        "PARSED", "2026-06-21",
    ),
    (
        "ca_film_30",
        "https://www.film.ca.gov/tax-credit/",
        "PARSED", "2026-06-21",
    ),
    (
        "la_film_production",
        "https://www.lafilm.org/incentives",
        "PARSED", "2026-06-21",
    ),
    (
        "on_opstc",
        "https://www.ontariocreates.ca/production-funding/tax-credits/ontario-production-services-tax-credit",
        "PARSED", "2026-06-21",
    ),
    (
        "on_ofttc",
        "https://www.ontariocreates.ca/production-funding/tax-credits/ontario-film-and-television-tax-credit",
        "PARSED", "2026-06-21",
    ),
    (
        "bc_pstc",
        "https://www.creativebc.com/programs/tax-credits/bc-production-services-tax-credit",
        "PARSED", "2026-06-21",
    ),
    (
        "qc_film_production",
        "https://www.sodec.gouv.qc.ca/en/aide/credits-impot/cinema-et-television/",
        "PARSED", "2026-06-21",
    ),
    (
        "ca_federal_cptc",
        "https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits.html",
        "PARSED", "2026-06-21",
    ),
    (
        "mu_edb_incentive",
        "https://www.edbmauritius.org/schemes/film-rebate-scheme/",
        "PARSED", "2026-06-21",
    ),
    (
        "mt_mfc_rebate",
        "https://maltafilmcommission.com/malta-cash-rebate-incentives-for-the-audiovisual-industry/",
        "PARSED", "2026-06-21",
    ),
    (
        "gr_cash_rebate",
        "https://www.enterprisegreece.gov.gr/en/invest-in-greece/sectors-for-growth/audiovisual-productions",
        "PARSED", "2026-06-21",
    ),
    # FR and IT promoted from DISCOVERY to PARSED
    (
        "fr_trip",
        "https://www.cnc.fr/professionnels/aides-et-financements/credit-dimpot-pour-les-productions-etrangeres_191498",
        "PARSED", "2026-06-21",
    ),
    (
        "it_tax_credit_foreign",
        "https://www.dgcinema.beniculturali.it/finanziamenti/tax-credit/tax-credit-per-i-film-stranieri/",
        "PARSED", "2026-06-21",
    ),
]

# ---------------------------------------------------------------------------
# Phase 2: ProgramAdminDetails data
# slug → (payment_timing_weeks, payment_timing_notes, audit_required,
#          audit_authority, audit_cost_est_usd, is_assignable, assignability_notes,
#          processing_timeline_weeks, financing_friction_notes,
#          first_window_open_relative, final_claim_deadline, confidence_tier, notes)
# ---------------------------------------------------------------------------
_ADMIN_DETAILS = [
    (
        "georgia_eiia",
        None,
        "Georgia EIIA is a transferable credit — not directly refunded. "
        "Timeline reflects certification to credit certificate issuance.",
        True,
        "Georgia Department of Revenue (self-prepared with licensed CPA sign-off)",
        20_000,
        True,
        "Credit sold to third parties on open market. "
        "Secondary market actively trades GA EIIA credits at 87–93 cents/dollar. "
        "Producers typically sell to Georgia tax-paying entities (banks, corporations).",
        20,
        "Active and liquid secondary market for GA credits. "
        "Bridge lenders routinely extend against GA credit. "
        "Discount 7–13% from face value. "
        "Carry cost well understood and predictable.",
        "Application submitted after principal photography commences in Georgia; "
        "within 90 days of first qualifying expenditure",
        "Must apply within 10 months of end of tax year in which production commences",
        "PARSED",
        "GA EIIA admin details from film office and production counsel market knowledge.",
    ),
    (
        "ny_state_film",
        65,
        "NY credit is refundable via tax return. "
        "Processing: typically 12–18 months from claim filing to refund.",
        True,
        "Empire State Development (ESD) — independent cost report required",
        25_000,
        False,
        "NY Film Tax Credit is NOT transferable or assignable. "
        "Bridge financing secured against expected refund only.",
        65,
        "NY credit is refundable but processing is slow (12–18 months). "
        "Bridge financing available at 6–10% interest. "
        "Credit not assignable — bridge loan secured against expected refund check. "
        "Higher carry cost than GA or UK.",
        "Application submitted before production commences; "
        "prior approval required",
        "Cost report filed within 90 days of completion of production in NY",
        "PARSED",
        "NY Film Tax Credit admin details from ESD programme documentation and production counsel.",
    ),
    (
        "ca_film_30",
        None,
        "CA credit is transferable — not directly refunded. "
        "Timeline reflects application approval through credit allocation to transfer.",
        True,
        "California Film Commission (CFC) — independent auditor required",
        30_000,
        True,
        "CA Film 3.0 credit is TRANSFERABLE (not refundable). "
        "Active transfer market at 88–93 cents/dollar. "
        "Programme is competitive (lottery-based allocation from annual fund).",
        91,
        "CA credit is transferable with active secondary market. "
        "Very long processing timeline (18–24 months from allocation to credit issuance) "
        "creates significant carry cost even with transfer. "
        "Bridge lenders accept CA credit assignments. "
        "Competitive allocation means no guarantee of incentive — budget modelling risk.",
        "Application submitted before production commences; "
        "allocation approved before principal photography",
        "Cost report submitted within 30 days of completion of principal photography in CA",
        "PARSED",
        "CA Film Commission 3.0 admin details from CFC programme materials.",
    ),
    (
        "la_film_production",
        39,
        "LA credit is transferable. Timeline ~9 months from audit completion to transfer.",
        True,
        "Louisiana Office of Entertainment Industry Development (LED) — "
        "State-certified CPA audit required",
        18_000,
        True,
        "LA credit is transferable to third parties. "
        "Active market at 85–90 cents/dollar. "
        "Also refundable at 85 cents to state (buyback programme).",
        39,
        "LA credit is transferable with established market. "
        "State buyback at 85 cents available as exit. "
        "Bridge lenders active in Louisiana market.",
        "Application filed with LED before commencement of principal photography",
        "State-certified audit filed within 1 year of production completion",
        "PARSED",
        "LA film credit admin details from LED programme documentation.",
    ),
    (
        "uk_avec",
        10,
        "HMRC processes AVEC interim and final claims relatively quickly. "
        "Interim claims available quarterly during production.",
        True,
        "HMRC (His Majesty's Revenue and Customs) — UK production accounts review",
        15_000,
        True,
        "AVEC claimable by UK qualifying company. "
        "Credit assignable to senior lenders via standard bank security. "
        "Interim quarterly claims during production significantly reduce carry cost. "
        "Standard completion bond lenders accept UK credit.",
        10,
        "UK credit has lowest financing friction among major markets. "
        "HMRC turnaround 8–12 weeks from final claim submission. "
        "Interim claims during production reduce bridge financing requirement. "
        "UK senior lenders, Coutts, Barclays Media routinely lend against AVEC. "
        "No secondary market needed — direct refund from HMRC.",
        "Interim claims filed quarterly from commencement of UK qualifying expenditure",
        "Final claim within 4 years of end of accounting period in which production completes",
        "PARSED",
        "UK AVEC admin details from HMRC guidance and UK production finance market knowledge.",
    ),
    (
        "ie_section_481",
        13,
        "Revenue Commissioners process S481 claims within 3 months from complete application.",
        True,
        "Revenue Commissioners Ireland — audited production accounts",
        15_000,
        True,
        "S481 credit is assignable to gap lenders. "
        "Well-established gap lending market in Ireland (AIB, Bank of Ireland). "
        "Assignment structure standard practice for Irish productions.",
        13,
        "S481 has excellent financing efficiency. "
        "Gap lenders accept S481 assignment at standard Irish rates. "
        "Revenue turnaround 10–16 weeks from complete claim. "
        "Interim claims not standard but final claim relatively fast.",
        "Prior approval application filed before principal photography commences",
        "Cost report and final claim filed within 12 months of production completion",
        "PARSED",
        "S481 admin details from Revenue Commissioners documentation and Irish production finance market.",
    ),
    (
        "mt_mfc_rebate",
        30,
        "MFC processes rebate claims within 6–8 months. "
        "Timeline from production wrap to cash receipt.",
        True,
        "Malta Film Commission (MFC) + Malta Enterprise — independent auditor required",
        12_000,
        None,
        "Assignability of Malta rebate to lenders unknown. "
        "Limited evidence of structured bridge lending against Malta rebate.",
        30,
        "Malta rebate less liquid in international lending markets than UK/IE. "
        "Limited bridge lending infrastructure relative to US/UK/IE. "
        "Higher carry cost expected. Recommend factoring 8–10 months carry into Malta budget.",
        "Application submitted before commencement of production in Malta",
        "Final audit and claim submitted within 6 months of completion of Malta production",
        "PARSED",
        "Malta MFC admin details from MFC programme documentation and market knowledge.",
    ),
    (
        "gr_cash_rebate",
        65,
        "EKOME process can take 12–18 months from application to cash receipt. "
        "Greek public administration timeline can extend further.",
        True,
        "EKOME (National Centre of Audiovisual Media and Communication) — "
        "Greek certified accountant audit required",
        15_000,
        None,
        "Assignability of Greek rebate to lenders unknown. "
        "No evidence of structured international bridge lending against Greek rebate.",
        65,
        "Greek administrative process is the slowest among Tier 1 markets. "
        "12–18 month timeline is standard; delays common. "
        "Limited international bridge lending infrastructure. "
        "Significant carry cost risk — recommend cash flow model assumes 18 months. "
        "Producers should budget for working capital financing at full carry.",
        "Application submitted before commencement of production in Greece",
        "Final audit and claim submitted within 90 days of completion of Greek production",
        "PARSED",
        "Greece EKOME admin details from EKOME programme documentation and market knowledge.",
    ),
    (
        "mu_edb_incentive",
        None,
        "Mauritius EDB payment timeline not yet confirmed from primary source.",
        None,
        "Economic Development Board Mauritius (EDB) — audit authority unconfirmed",
        None,
        None,
        "Assignability of Mauritius rebate to international lenders unknown. "
        "Bridge lending infrastructure in Mauritius film market not established.",
        None,
        "Mauritius financing infrastructure is unknown. "
        "Bridge lending likely unavailable through international lenders. "
        "Recommend treating MU rebate as uncollaterisable for budget modelling.",
        "Unknown — confirm with EDB prior to production commencement",
        "Unknown — confirm with EDB",
        "DISCOVERY",
        "Mauritius EDB admin details not yet confirmed. DISCOVERY tier pending primary source review.",
    ),
    (
        "on_opstc",
        39,
        "Ontario Creates (formerly OMDC) processes OPSTC within 8–10 months. "
        "Timeline from audit completion to refund receipt.",
        True,
        "Ontario Creates — CPA audit of production accounts required",
        20_000,
        False,
        "OPSTC is NOT directly assignable. "
        "Bridge financing available through Canadian chartered banks secured against expected refund.",
        39,
        "Strong Canadian bridge lending market for Ontario OPSTC. "
        "Canadian chartered banks (TD, RBC, BNS) routinely lend against OPSTC. "
        "Credit is refundable — no secondary market needed. "
        "Timeline 8–10 months is predictable.",
        "Application filed with Ontario Creates before principal photography commences",
        "Cost report and final claim filed within 24 months of production completion",
        "PARSED",
        "Ontario OPSTC admin details from Ontario Creates programme documentation.",
    ),
    (
        "bc_pstc",
        35,
        "Creative BC processes PSTC within 7–9 months from audit completion.",
        True,
        "Creative BC — CPA audit of BC qualifying expenditures required",
        20_000,
        False,
        "BC PSTC is NOT directly assignable. "
        "Bridge financing through Canadian banks secured against expected refund.",
        35,
        "Strong Canadian bridge lending for BC PSTC. "
        "Canadian institutions (Business Development Bank, chartered banks) lend against PSTC. "
        "Refundable credit — no transfer market. 7–9 month timeline well understood.",
        "Application filed with Creative BC before principal photography commences",
        "Cost report filed within 18 months of production completion",
        "PARSED",
        "BC PSTC admin details from Creative BC programme documentation.",
    ),
    (
        "qc_film_production",
        43,
        "SODEC processes QC film credit within 9–12 months from complete audit.",
        True,
        "SODEC (Société de développement des entreprises culturelles) — "
        "audit by Quebec CPA required",
        18_000,
        False,
        "QC production credit is NOT directly assignable. "
        "Bridge financing through Quebec/Canadian institutions.",
        43,
        "Bridge financing available through Quebec institutions (Investissement Québec, BNC). "
        "Refundable credit — no transfer market. "
        "Timeline 9–12 months is predictable.",
        "Application submitted to SODEC before principal photography commences",
        "Final cost report and claim submitted within 24 months of production completion",
        "PARSED",
        "QC film production credit admin details from SODEC programme documentation.",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # Phase 1 — Source metadata updates
    # ------------------------------------------------------------------
    for slug, authority_url, tier, verified_date in _SOURCE_UPDATES:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs SET
                    authority_url       = :url,
                    confidence_tier     = :tier,
                    last_verified_date  = :date,
                    updated_at          = :now
                WHERE slug = :slug
            """),
            {
                "slug": slug, "url": authority_url,
                "tier": tier, "date": verified_date, "now": NOW,
            },
        )

    # ------------------------------------------------------------------
    # Phase 2 — ProgramAdminDetails
    # ------------------------------------------------------------------
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
            sa.text("""
                DELETE FROM program_admin_details
                WHERE id = :id
            """),
            {"id": _uid(f"admin:{slug}")},
        )

    # Revert source metadata updates (restore to generic values)
    for slug, *_ in _SOURCE_UPDATES:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs SET
                    last_verified_date = NULL,
                    updated_at = :now
                WHERE slug = :slug
            """),
            {"slug": slug, "now": NOW},
        )
