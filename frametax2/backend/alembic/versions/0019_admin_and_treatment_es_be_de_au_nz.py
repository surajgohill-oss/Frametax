"""0019 — ProgramAdminDetails + ProgramSpendTreatment for ES, BE, DE, AU, NZ.

Phase 2: AdminDetails for Spain, Belgium, Germany, Australia, New Zealand.
Phase 3: SpendTreatment (21 categories each) for all five programs.

Source basis:
  ES — ICAA/Spanish Ministry of Culture programme documentation
  BE — Belgian Tax Shelter official framework
  DE — DFFF (BKM) programme documentation
  AU — Screen Australia Location Offset guidelines
  NZ — NZFC Screen Production Grant guidelines

ATL notes:
  ES: ATL explicitly qualifies (Ministry of Culture documentation confirms
    director, scriptwriter, principal cast are eligible categories).
  BE: Tax Shelter qualifies all Belgian-incurred expenditure including ATL.
  DE: DFFF qualifies ATL if incurred in Germany.
  AU: Location Offset qualifies all QAPE including ATL incurred in Australia.
  NZ: Screen Production Grant qualifies all QNZPE including ATL.

Revision ID: 0019
Revises: 0018
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0019-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# Phase 2 — ProgramAdminDetails
# (slug, payment_timing_weeks, payment_timing_notes, audit_required,
#  audit_authority, audit_cost_estimate_usd, is_assignable, assignability_notes,
#  processing_timeline_weeks, financing_friction_notes,
#  first_window_open_relative, final_claim_deadline, confidence_tier, notes)
# ---------------------------------------------------------------------------
_ADMIN_DETAILS = [
    (
        "es_tax_credit_foreign",
        None,
        "Spain tax credit is a deduction against corporate tax liability. "
        "Payment mechanism is via tax return offset, not direct cash payment.",
        True,
        "ICAA (Instituto de la Cinematografía y de las Artes Audiovisuales) — "
        "Spanish certified accountant (gestor) audit required",
        22_000,
        True,
        "Spanish tax credit is transferable to Spanish tax-paying entities. "
        "Secondary market exists but less liquid than UK/IE. "
        "Canary Islands productions benefit from higher rate (35–40%) and may "
        "have more active local finance market.",
        78,
        "Spanish public administration is slow. "
        "18–24 month processing timeline is typical. "
        "Limited international bridge lending infrastructure vs UK/US markets. "
        "Recommend treating carry cost as 20 months minimum in budget models. "
        "Canary Islands credit may process faster through ACIISI.",
        "Application submitted before production commences in Spain; "
        "prior registration with ICAA required",
        "Tax return filed within statutory corporate tax deadline "
        "(typically within 12 months of end of fiscal year of production)",
        "PARSED",
        "Spain film credit admin details from ICAA programme documentation and market knowledge.",
    ),
    (
        "be_tax_shelter",
        26,
        "Belgian Tax Shelter delivers financing upfront during production "
        "via investor participation — not post-completion refund. "
        "Typical investment agreements settled within 6 months of production start.",
        True,
        "Belgian Ministry of Finance — Tax Shelter framework administrator. "
        "Independent audit of qualifying Belgian expenditures required.",
        18_000,
        True,
        "Tax Shelter is inherently an assignment/co-investment mechanism. "
        "Investors provide upfront financing against 150% spend obligation. "
        "This is fundamentally different from credit-based programs — "
        "financing friction is front-loaded into investor negotiation, not post-production.",
        30,
        "Belgian Tax Shelter has the most favourable financing structure of "
        "European programs: capital arrives during production rather than "
        "18+ months post-completion. "
        "Key friction is finding Belgian Tax Shelter investors (sheltered companies). "
        "Standard practice: use Belgian co-producer or Tax Shelter facilitator "
        "(e.g., Take Five, Scope Pictures). "
        "Facilitator fee typically 5–8% of Tax Shelter investment.",
        "Tax Shelter agreement executed before production commences; "
        "framework agreement filed with Ministry of Finance",
        "Qualifying Belgian expenditure certification submitted within "
        "24 months of production completion",
        "PARSED",
        "Belgium Tax Shelter admin details from Belgian Ministry of Finance framework and market knowledge.",
    ),
    (
        "de_dfff",
        None,
        "DFFF is a grant, not a tax credit. "
        "Grant disbursement occurs after BKM approval and audit completion.",
        True,
        "Filmförderungsanstalt (FFA) / Federal Film Board — "
        "independent German auditor required for production accounts",
        20_000,
        None,
        "DFFF grant assignability to international lenders not confirmed from primary source. "
        "German grant framework differs from credit programs; bridge lending against DFFF "
        "may require case-by-case negotiation with German banks.",
        39,
        "DFFF is a competitive grant programme with annual funding rounds. "
        "No guarantee of award — budget modelling must account for non-award risk. "
        "BKM processing is moderately efficient by European standards. "
        "German banks (HypoVereinsbank, KfW) may provide production financing "
        "but DFFF bridge lending is less established than UK/Canadian markets.",
        "Application submitted to BKM/FFA before production commences in Germany; "
        "DFFF application must be submitted before principal photography begins",
        "Production completion report and audit submitted within 6 months "
        "of completion of German production",
        "PARSED",
        "Germany DFFF admin details from BKM/FFA programme documentation and market knowledge.",
    ),
    (
        "au_location_offset",
        52,
        "Screen Australia processes Location Offset claims within "
        "10–14 months of complete application. Tax offset mechanism via ATO.",
        True,
        "Screen Australia + Australian Taxation Office (ATO) — "
        "independent Australian auditor required (Big 4 or specialist film CPA)",
        28_000,
        True,
        "Australian Location Offset can be assigned to senior lenders. "
        "Australian bank market (ANZ, NAB, Macquarie) actively lends against "
        "Location Offset for qualifying productions. "
        "Assignment structures well-established in Australian market.",
        52,
        "Strong Australian bridge lending market for Location Offset. "
        "Lenders require AU$50M+ QAPE threshold to be met. "
        "ATO refund timeline is predictable (10–14 months). "
        "Carry cost well understood and manageable.",
        "Producer Offset Certificate application submitted before production "
        "commences; qualifying Australian production expenditure threshold (AU$15M "
        "total budget for large-budget works) must be met",
        "ATO tax return filed within 3 months of the end of the income year "
        "in which production is completed",
        "PARSED",
        "Australia Location Offset admin details from Screen Australia guidelines and ATO documentation.",
    ),
    (
        "nz_spg_international",
        26,
        "NZFC processes Screen Production Grant within 5–7 months "
        "from complete audit submission.",
        True,
        "New Zealand Film Commission (NZFC) — "
        "New Zealand Chartered Accountant audit of QNZPE required",
        18_000,
        True,
        "NZ Screen Production Grant can be assigned to lenders. "
        "New Zealand banks (ANZ NZ, BNZ) and international specialist lenders "
        "accept NZ SPG assignments. Well-established market.",
        26,
        "NZ SPG has one of the best financing efficiency profiles in the Asia-Pacific region. "
        "NZFC is known for efficient administration. "
        "5–7 month turnaround reduces carry cost significantly vs Australian or US programs. "
        "Grant is not refundable per se but functions as cash grant — "
        "no secondary market needed.",
        "Initial application submitted to NZFC before production commences; "
        "minimum QNZPE threshold (NZ$15M for international productions) must be met",
        "Final QNZPE audit submitted within 3 months of production completion",
        "PARSED",
        "NZ Screen Production Grant admin details from NZFC programme documentation.",
    ),
]

# ---------------------------------------------------------------------------
# Phase 3 — ProgramSpendTreatment
# ---------------------------------------------------------------------------

_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_CUSTOMS_UNKNOWN = (
    "Customs/import duties treatment unconfirmed from primary source."
)

_TREATMENTS: list[tuple[str, str, bool | None, str, str]] = [

    # -----------------------------------------------------------------------
    # Spain (es_tax_credit_foreign)
    # ICAA documentation explicitly lists director, scriptwriter, principal
    # cast as eligible categories. All Spain-incurred qualifying spend eligible.
    # Canary Islands rate is higher (35–40%) for same categories.
    # -----------------------------------------------------------------------
    ("es_tax_credit_foreign", "atl_writer",          True,  "ATL writer (scriptwriter) fees incurred in Spain explicitly qualify under Spanish film tax credit (ICAA documentation).", "PARSED"),
    ("es_tax_credit_foreign", "atl_director",        True,  "ATL director fees incurred in Spain explicitly qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "atl_producer",        True,  "ATL producer fees incurred in Spain qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "atl_cast_principal",  True,  "Principal cast fees incurred in Spain explicitly qualify under Spanish film tax credit (ICAA documentation).", "PARSED"),
    ("es_tax_credit_foreign", "atl_cast_supporting", True,  "Supporting cast fees incurred in Spain qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "btl_crew_resident",   True,  "Spanish resident BTL crew qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Spain qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Spain qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "travel",              True,  "Spanish travel expenditure qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "accommodation_lodging", True, "Spanish accommodation qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "per_diem",            True,  "Per diem costs incurred in Spain qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "insurance",           True,  "Spanish-sourced production insurance qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "completion_bond",     True,  "Completion bond costs qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("es_tax_credit_foreign", "marine_vessel",       True,  "Marine vessel hire in Spain qualifies under Spanish film tax credit. Spain (including Canary Islands) is a primary marine production location.", "PARSED"),
    ("es_tax_credit_foreign", "vfx",                 True,  "Spanish VFX expenditure qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "post_production",     True,  "Spanish post-production qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "animation",           True,  "Spanish animation qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "music",               True,  "Spanish music expenditure qualifies under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "legal_accounting",    True,  "Spanish legal and accounting costs qualify under Spanish film tax credit.", "PARSED"),
    ("es_tax_credit_foreign", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # Belgium (be_tax_shelter)
    # Tax Shelter qualifies all Belgian-incurred qualifying expenditure.
    # The 150% spend obligation covers all Belgian production categories.
    # ATL included in qualifying Belgian expenditures.
    # -----------------------------------------------------------------------
    ("be_tax_shelter", "atl_writer",          True,  "ATL writer fees incurred in Belgium qualify as part of Belgian qualified expenditure under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "atl_director",        True,  "ATL director fees incurred in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "atl_producer",        True,  "ATL producer fees incurred in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "atl_cast_principal",  True,  "Principal cast fees incurred in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "atl_cast_supporting", True,  "Supporting cast fees incurred in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "btl_crew_resident",   True,  "Belgian resident BTL crew qualify under Tax Shelter as primary qualifying expenditure.", "PARSED"),
    ("be_tax_shelter", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "travel",              True,  "Belgian travel expenditure qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "accommodation_lodging", True, "Belgian accommodation qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "per_diem",            True,  "Per diem costs incurred in Belgium qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "insurance",           True,  "Belgian-sourced production insurance qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "completion_bond",     True,  "Completion bond costs qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("be_tax_shelter", "marine_vessel",       True,  "Marine vessel hire in Belgium qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "vfx",                 True,  "Belgian VFX expenditure qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "post_production",     True,  "Belgian post-production qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "animation",           True,  "Belgian animation qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "music",               True,  "Belgian music expenditure qualifies under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "legal_accounting",    True,  "Belgian legal and accounting costs qualify under Tax Shelter.", "PARSED"),
    ("be_tax_shelter", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # Germany (de_dfff)
    # DFFF qualifies eligible German production expenditures including ATL
    # if incurred in Germany. Competitive grant — not guaranteed.
    # -----------------------------------------------------------------------
    ("de_dfff", "atl_writer",          True,  "ATL writer fees incurred in Germany qualify under DFFF as eligible German production expenditure.", "PARSED"),
    ("de_dfff", "atl_director",        True,  "ATL director fees incurred in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "atl_producer",        True,  "ATL producer fees incurred in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "atl_cast_principal",  True,  "Principal cast fees incurred in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "atl_cast_supporting", True,  "Supporting cast fees incurred in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "btl_crew_resident",   True,  "German resident BTL crew qualify under DFFF.", "PARSED"),
    ("de_dfff", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "travel",              True,  "German travel expenditure qualifies under DFFF.", "PARSED"),
    ("de_dfff", "accommodation_lodging", True, "German accommodation qualifies under DFFF.", "PARSED"),
    ("de_dfff", "per_diem",            True,  "Per diem costs incurred in Germany qualify under DFFF.", "PARSED"),
    ("de_dfff", "insurance",           True,  "German-sourced production insurance qualifies under DFFF.", "PARSED"),
    ("de_dfff", "completion_bond",     True,  "Completion bond costs qualify under DFFF.", "PARSED"),
    ("de_dfff", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("de_dfff", "marine_vessel",       True,  "Marine vessel hire in Germany qualifies under DFFF.", "PARSED"),
    ("de_dfff", "vfx",                 True,  "German VFX expenditure qualifies under DFFF.", "PARSED"),
    ("de_dfff", "post_production",     True,  "German post-production qualifies under DFFF.", "PARSED"),
    ("de_dfff", "animation",           True,  "German animation qualifies under DFFF.", "PARSED"),
    ("de_dfff", "music",               True,  "German music expenditure qualifies under DFFF.", "PARSED"),
    ("de_dfff", "legal_accounting",    True,  "German legal and accounting costs qualify under DFFF.", "PARSED"),
    ("de_dfff", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # Australia (au_location_offset)
    # Location Offset covers all Qualifying Australian Production Expenditure
    # (QAPE) which includes ATL labor incurred in Australia. Screen Australia
    # guidelines explicitly include remuneration for creative personnel.
    # -----------------------------------------------------------------------
    ("au_location_offset", "atl_writer",          True,  "ATL writer fees incurred in Australia qualify as QAPE under Australian Location Offset. Screen Australia guidelines include creative remuneration.", "PARSED"),
    ("au_location_offset", "atl_director",        True,  "ATL director fees incurred in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "atl_producer",        True,  "ATL producer fees incurred in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "atl_cast_principal",  True,  "Principal cast fees incurred in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "atl_cast_supporting", True,  "Supporting cast fees incurred in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "btl_crew_resident",   True,  "Australian resident BTL crew qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "travel",              True,  "Australian travel expenditure qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "accommodation_lodging", True, "Australian accommodation qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "per_diem",            True,  "Per diem costs incurred in Australia qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "insurance",           True,  "Australian-sourced production insurance qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "completion_bond",     True,  "Completion bond costs qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("au_location_offset", "marine_vessel",       True,  "Marine vessel hire in Australia qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "vfx",                 True,  "Australian VFX expenditure qualifies as QAPE under Australian Location Offset. VFX also eligible for separate PDV Offset.", "PARSED"),
    ("au_location_offset", "post_production",     True,  "Australian post-production qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "animation",           True,  "Australian animation qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "music",               True,  "Australian music expenditure qualifies as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "legal_accounting",    True,  "Australian legal and accounting costs qualify as QAPE under Australian Location Offset.", "PARSED"),
    ("au_location_offset", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # New Zealand (nz_spg_international)
    # NZ Screen Production Grant covers all Qualifying New Zealand Production
    # Expenditure (QNZPE) including ATL labor incurred in NZ.
    # NZ is a broad-based grant covering the full production spend in NZ.
    # -----------------------------------------------------------------------
    ("nz_spg_international", "atl_writer",          True,  "ATL writer fees incurred in New Zealand qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "atl_director",        True,  "ATL director fees incurred in New Zealand qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "atl_producer",        True,  "ATL producer fees incurred in New Zealand qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "atl_cast_principal",  True,  "Principal cast fees incurred in New Zealand qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "atl_cast_supporting", True,  "Supporting cast fees incurred in New Zealand qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "btl_crew_resident",   True,  "NZ resident BTL crew qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in NZ qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in NZ qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "travel",              True,  "NZ travel expenditure qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "accommodation_lodging", True, "NZ accommodation qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "per_diem",            True,  "Per diem costs incurred in NZ qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "insurance",           True,  "NZ-sourced production insurance qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "completion_bond",     True,  "Completion bond costs qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("nz_spg_international", "marine_vessel",       True,  "Marine vessel hire in NZ qualifies as QNZPE under NZ Screen Production Grant. NZ is a significant marine production location.", "PARSED"),
    ("nz_spg_international", "vfx",                 True,  "NZ VFX expenditure qualifies as QNZPE under NZ Screen Production Grant. Wellington (Weta FX) is a world-leading VFX hub.", "PARSED"),
    ("nz_spg_international", "post_production",     True,  "NZ post-production qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "animation",           True,  "NZ animation qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "music",               True,  "NZ music expenditure qualifies as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "legal_accounting",    True,  "NZ legal and accounting costs qualify as QNZPE under NZ Screen Production Grant.", "PARSED"),
    ("nz_spg_international", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),
]


def upgrade() -> None:
    conn = op.get_bind()

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

    # ------------------------------------------------------------------
    # Phase 3 — ProgramSpendTreatment
    # ------------------------------------------------------------------
    for slug, labor_type, qualifies, treatment_notes, tier in _TREATMENTS:
        conn.execute(
            sa.text("""
                INSERT INTO program_spend_treatments (
                    id, program_id, labor_type,
                    qualifies, cap_pct, cap_amount_local,
                    treatment_notes, confidence_tier,
                    created_at, updated_at
                )
                SELECT
                    :id, p.id, :labor_type,
                    :qualifies, NULL, NULL,
                    :notes, :tier,
                    :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_spend_treatments t
                      WHERE t.program_id = p.id AND t.labor_type = :labor_type ::varchar
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"treatment:{slug}:{labor_type}"),
                "slug": slug,
                "labor_type": labor_type,
                "qualifies": qualifies,
                "notes": treatment_notes,
                "tier": tier,
                "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    for slug, *_ in _ADMIN_DETAILS:
        conn.execute(
            sa.text("DELETE FROM program_admin_details WHERE id = :id"),
            {"id": _uid(f"admin:{slug}")},
        )

    for slug, labor_type, *_ in _TREATMENTS:
        conn.execute(
            sa.text("DELETE FROM program_spend_treatments WHERE id = :id"),
            {"id": _uid(f"treatment:{slug}:{labor_type}")},
        )
