"""0008 — Seed Tier 1 marine comparison jurisdictions and Secondary Reference Group.

Tier 1 (full programs + QSC entries):
  MU — Mauritius (benchmark, DISCOVERY — no verified incentive)
  MT — Malta (Malta Film Commission Cash Rebate, PARSED)
  GR — Greece (Greece Cash Rebate for International Productions, PARSED)
  CY — Cyprus (Cyprus Film Production Rebate, DISCOVERY)

Secondary Reference Group (programs only, abbreviated QSC):
  IE — Ireland (Section 481)
  FR — France (TRIP)
  IT — Italy (Tax Credit for Foreign Productions)
  ES — Spain (Tax Credit for Foreign Productions / Canary Islands)
  HR — Croatia (Cash Rebate)
  HU — Hungary (Tax Rebate — HIPA)
  BE — Belgium (Tax Shelter)
  DE — Germany (DFFF/GFFF)

Note: GB (United Kingdom) / UK AVEC already seeded in revision 0002.

CONFIDENCE TIERS:
  PARSED  — Malta, Greece, Ireland (public program documentation reviewed)
  DISCOVERY — Cyprus, Mauritius, France, Italy, Spain, Croatia, Hungary, Belgium, Germany
              (rates from market knowledge; must be verified against primary sources before
               use in deterministic recommendations)

DATA GAPS PER JURISDICTION ARE DOCUMENTED IN jurisdiction_comparison.py PROFILES.

Revision ID: 0008
Revises: 0007
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0008-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# Jurisdiction IDs
# ---------------------------------------------------------------------------
MU_ID = _uid("jur:MU")
MT_ID = _uid("jur:MT")
GR_ID = _uid("jur:GR")
CY_ID = _uid("jur:CY")
IE_ID = _uid("jur:IE")
FR_ID = _uid("jur:FR")
IT_ID = _uid("jur:IT")
ES_ID = _uid("jur:ES")
HR_ID = _uid("jur:HR")
HU_ID = _uid("jur:HU")
BE_ID = _uid("jur:BE")
DE_ID = _uid("jur:DE")

# ---------------------------------------------------------------------------
# Program IDs
# ---------------------------------------------------------------------------
PROG_MU_ID = _uid("prog:mu_edb_incentive")
PROG_MT_ID = _uid("prog:mt_mfc_rebate")
PROG_GR_ID = _uid("prog:gr_cash_rebate")
PROG_CY_ID = _uid("prog:cy_film_rebate")
PROG_IE_ID = _uid("prog:ie_section_481")
PROG_FR_ID = _uid("prog:fr_trip")
PROG_IT_ID = _uid("prog:it_tax_credit_foreign")
PROG_ES_ID = _uid("prog:es_tax_credit_foreign")
PROG_HR_ID = _uid("prog:hr_cash_rebate")
PROG_HU_ID = _uid("prog:hu_hipa_rebate")
PROG_BE_ID = _uid("prog:be_tax_shelter")
PROG_DE_ID = _uid("prog:de_dfff")

ALL_JUR_IDS = [
    MU_ID, MT_ID, GR_ID, CY_ID,
    IE_ID, FR_ID, IT_ID, ES_ID, HR_ID, HU_ID, BE_ID, DE_ID,
]
ALL_PROG_IDS = [
    PROG_MU_ID, PROG_MT_ID, PROG_GR_ID, PROG_CY_ID,
    PROG_IE_ID, PROG_FR_ID, PROG_IT_ID, PROG_ES_ID,
    PROG_HR_ID, PROG_HU_ID, PROG_BE_ID, PROG_DE_ID,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jur(jur_id, name, code, iso_code, currency, country_code):
    return {
        "id": jur_id,
        "parent_id": None,
        "name": name,
        "code": code,
        "iso_code": iso_code,
        "level": "country",
        "currency_code": currency,
        "country_code": country_code,
        "is_active": True,
        "notes": None,
        "metadata_json": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _prog(prog_id, jur_id, name, slug, prog_type, credit_basis,
          base_rate, max_rate, is_refundable, is_transferable,
          annual_cap_local, requires_cultural_test, effective_from,
          confidence_tier, authority_url, notes):
    return {
        "id": prog_id,
        "jurisdiction_id": jur_id,
        "source_document_id": None,
        "name": name,
        "slug": slug,
        "program_type": prog_type,
        "credit_basis": credit_basis,
        "base_rate": base_rate,
        "max_rate": max_rate,
        "is_refundable": is_refundable,
        "is_transferable": is_transferable,
        "transferable_value_pct": None,
        "is_competitive": False,
        "annual_cap_local": annual_cap_local,
        "fixed_grant_amount_usd": None,
        "requires_cultural_test": requires_cultural_test,
        "cultural_test_id": None,
        "requires_local_entity": False,
        "effective_from": effective_from,
        "effective_until": None,
        "confidence_tier": confidence_tier,
        "review_status": "pending",
        "authority_url": authority_url,
        "last_verified_date": None,
        "notes": notes,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _qsc(slug, prog_id, category, qualifies, jur_only, notes, tier="DISCOVERY"):
    return {
        "id": _uid(f"qsc:{slug}:{category}"),
        "program_id": prog_id,
        "spend_category": category,
        "qualifies": qualifies,
        "jurisdiction_spend_only": jur_only,
        "notes": notes,
        "confidence_tier": tier,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _rule(prog_id, rule_type, threshold_numeric, threshold_text, fail_action,
          description, statutory_ref, tier="DISCOVERY"):
    return {
        "id": _uid(f"rule:{prog_id}:{rule_type}:{threshold_text or ''}"),
        "program_id": prog_id,
        "source_document_id": None,
        "rule_type": rule_type,
        "threshold_numeric": threshold_numeric,
        "threshold_text": threshold_text,
        "fail_action": fail_action,
        "description": description,
        "source_page": None,
        "source_excerpt": None,
        "statutory_reference": statutory_ref,
        "confidence_tier": tier,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _uplift(prog_id, name, additional_rate, applies_to, condition_type,
            condition_text, tier="DISCOVERY"):
    return {
        "id": _uid(f"uplift:{prog_id}:{name}"),
        "program_id": prog_id,
        "name": name,
        "additional_rate": additional_rate,
        "applies_to": applies_to,
        "condition_type": condition_type,
        "condition_threshold": None,
        "condition_text": condition_text,
        "is_stackable_with_other_uplifts": True,
        "confidence_tier": tier,
        "created_at": NOW,
        "updated_at": NOW,
    }


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

JURISDICTIONS = [
    # Tier 1
    _jur(MU_ID, "Mauritius",   "MU", "MU",   "MUR", "MU"),
    _jur(MT_ID, "Malta",       "MT", "MT",   "EUR", "MT"),
    _jur(GR_ID, "Greece",      "GR", "GR",   "EUR", "GR"),
    _jur(CY_ID, "Cyprus",      "CY", "CY",   "EUR", "CY"),
    # Secondary
    _jur(IE_ID, "Ireland",     "IE", "IE",   "EUR", "IE"),
    _jur(FR_ID, "France",      "FR", "FR",   "EUR", "FR"),
    _jur(IT_ID, "Italy",       "IT", "IT",   "EUR", "IT"),
    _jur(ES_ID, "Spain",       "ES", "ES",   "EUR", "ES"),
    _jur(HR_ID, "Croatia",     "HR", "HR",   "EUR", "HR"),
    _jur(HU_ID, "Hungary",     "HU", "HU",   "HUF", "HU"),
    _jur(BE_ID, "Belgium",     "BE", "BE",   "EUR", "BE"),
    _jur(DE_ID, "Germany",     "DE", "DE",   "EUR", "DE"),
]

PROGRAMS = [
    # ---- Mauritius (Tier 1 — DISCOVERY: no verified program) ----
    _prog(
        PROG_MU_ID, MU_ID,
        "Mauritius EDB Production Incentive (Unverified)",
        "mu_edb_incentive",
        "cash_rebate", "qualifying_spend",
        None, None, None, None, None,
        False, None,
        "DISCOVERY",
        None,
        "No verified structured film production incentive comparable to Malta or Greece identified "
        "as of 2025. Mauritius Film Development Corporation (MFDC) facilitates permits and "
        "locations but does not administer a confirmed cash rebate program. Some secondary sources "
        "reference a 30% rebate; this is unverified. Program rates are null pending primary source "
        "verification. Benchmark as a shoot-location, not an incentive jurisdiction.",
    ),

    # ---- Malta (Tier 1 — PARSED) ----
    _prog(
        PROG_MT_ID, MT_ID,
        "Malta Film Commission Cash Rebate",
        "mt_mfc_rebate",
        "cash_rebate", "qualifying_spend",
        0.25, 0.40, True, None, None,
        False, "2015-01-01",
        "PARSED",
        "https://maltafilmcommission.com",
        "Base 25% on all qualifying Malta expenditure for non-Maltese productions. "
        "Additional uplifts: +2% for Maltese-element productions; +3% MFC cultural contribution; "
        "+3% for VFX/post-production spend in Malta; +7% for small-budget productions (<EUR 3M). "
        "No cultural test required for foreign productions. Min spend EUR 50,000. "
        "ATL costs (director, cast, writer) explicitly eligible. "
        "Vessel charter, underwater equipment, and marine logistics qualify as BTL production spend. "
        "Mediterranean Film Studios (MFS) water tanks: 750,000-gallon outdoor tank + indoor facilities. "
        "Historical productions: Titanic (1943), Gladiator, Troy, Count of Monte Cristo. "
        "Rates at PARSED tier: verify uplifts against current MFC program guidelines.",
    ),

    # ---- Greece (Tier 1 — PARSED) ----
    _prog(
        PROG_GR_ID, GR_ID,
        "Greece Cash Rebate for International Productions",
        "gr_cash_rebate",
        "cash_rebate", "qualifying_spend",
        0.40, 0.40, True, None, None,
        False, "2017-01-01",
        "PARSED",
        "https://enterprisegreece.gov.gr",
        "40% cash rebate on qualifying Greek expenditure for international productions. "
        "No cultural test required. Minimum spend EUR 100,000. "
        "ATL costs (director, cast, writer) qualify as eligible Greek expenditure. "
        "Marine/vessel costs qualify as production expenditure. "
        "16,000+ km coastline; Aegean and Ionian access; Greek shipping industry provides "
        "existing marine logistics infrastructure transferable to film. "
        "No purpose-built water tank equivalent to Malta MFS. "
        "High employer social contributions (~22%) increase local crew cost. "
        "Cashflow risk: Greek administrative process can extend to 12+ months. "
        "Annual program allocation cap not publicly confirmed — verify before committing spend.",
    ),

    # ---- Cyprus (Tier 1 — DISCOVERY) ----
    _prog(
        PROG_CY_ID, CY_ID,
        "Cyprus Film Production Rebate",
        "cy_film_rebate",
        "cash_rebate", "qualifying_spend",
        0.35, 0.35, True, None, None,
        False, "2020-01-01",
        "DISCOVERY",
        "https://cipa.org.cy",
        "35% cash rebate on qualifying Cyprus expenditure. DISCOVERY tier: rate unverified from "
        "statute text. No cultural test. Minimum spend EUR 100,000 (unconfirmed). "
        "ATL treatment expected to qualify (all qualifying spend) but not confirmed. "
        "648 km Mediterranean coastline; vessel and marine costs expected to qualify. "
        "Crew base very shallow — substantially all BTL crew must be imported. "
        "Low employer tax burden (~8%) partially offsets import cost. "
        "Cyprus potentially useful as co-production entity domicile (12.5% CIT) "
        "independent of where production spend is incurred.",
    ),

    # ---- Ireland (Secondary — PARSED) ----
    _prog(
        PROG_IE_ID, IE_ID,
        "Section 481 Film Tax Credit",
        "ie_section_481",
        "tax_credit", "qualifying_spend",
        0.32, 0.32, True, True, None,
        True, "1987-01-01",
        "PARSED",
        "https://revenue.ie",
        "32% tax credit on qualifying Irish expenditure. Refundable. "
        "Cultural test required (Irish Qualifying Test — points based). "
        "Minimum spend EUR 125,000. 80% of total budget or EUR 70M qualifying spend cap (whichever lower). "
        "ATL eligible. Crew base strong (Ardmore Studios, Dublin). "
        "Section 481 credit is assignable to gap lenders — good financing efficiency.",
    ),

    # ---- France (Secondary — DISCOVERY) ----
    _prog(
        PROG_FR_ID, FR_ID,
        "Tax Rebate for International Productions (TRIP)",
        "fr_trip",
        "cash_rebate", "qualifying_spend",
        0.30, 0.30, True, None, None,
        True, "2009-01-01",
        "DISCOVERY",
        "https://cnc.fr",
        "30% rebate on qualifying French expenditure for international productions. "
        "Cultural test required (points-based: 2 of 6 French elements). "
        "Minimum spend EUR 250,000. Administered by CNC (Centre National du Cinéma). "
        "Strong crew base; one of Europe's deepest BTL pools.",
    ),

    # ---- Italy (Secondary — DISCOVERY) ----
    _prog(
        PROG_IT_ID, IT_ID,
        "Italian Tax Credit for Foreign Productions",
        "it_tax_credit_foreign",
        "tax_credit", "qualifying_spend",
        0.40, 0.40, True, None, 20_000_000.0,
        False, "2016-01-01",
        "DISCOVERY",
        "https://mibac.it",
        "40% tax credit on qualifying Italian expenditure. No cultural test for foreign. "
        "Minimum spend EUR 1,000,000. Cap EUR 20M per production. ATL eligible. "
        "Extensive coastline and Mediterranean access; marine costs qualify. "
        "DISCOVERY tier: verify current rules and cap from DL 91/2013 implementing decree.",
    ),

    # ---- Spain (Secondary — DISCOVERY) ----
    _prog(
        PROG_ES_ID, ES_ID,
        "Spanish Tax Credit for Foreign Productions",
        "es_tax_credit_foreign",
        "tax_credit", "qualifying_spend",
        0.30, 0.50, True, None, None,
        False, "2015-01-01",
        "DISCOVERY",
        "https://culture.gob.es",
        "30% tax credit on qualifying Spanish expenditure (mainland). "
        "Canary Islands: 50% — excellent for warm-water marine productions. "
        "Minimum spend EUR 1,000,000 or 50% of total budget in Spain. "
        "No cultural test for foreign. ATL eligible. "
        "Spanish coastline (Atlantic + Mediterranean) and Canary Islands offer strong marine access. "
        "Max rate 50% is specific to Canary Islands production.",
    ),

    # ---- Croatia (Secondary — DISCOVERY) ----
    _prog(
        PROG_HR_ID, HR_ID,
        "Croatia Cash Rebate",
        "hr_cash_rebate",
        "cash_rebate", "qualifying_spend",
        0.25, 0.25, True, None, None,
        False, "2012-01-01",
        "DISCOVERY",
        "https://havc.hr",
        "25% cash rebate on qualifying Croatian expenditure. No cultural test. "
        "Minimum spend EUR 200,000 (Croatia joined Eurozone Jan 2023). "
        "Adriatic Dalmatian coastline: strong marine access. "
        "Historical productions: Game of Thrones (Dubrovnik), Star Wars Rogue One (Dubrovnik). "
        "Moderate crew depth; experienced in mid-size international productions.",
    ),

    # ---- Hungary (Secondary — DISCOVERY) ----
    _prog(
        PROG_HU_ID, HU_ID,
        "Hungarian Tax Rebate (HIPA)",
        "hu_hipa_rebate",
        "cash_rebate", "qualifying_spend",
        0.30, 0.30, True, None, None,
        False, "2004-01-01",
        "DISCOVERY",
        "https://hipa.hu",
        "30% tax rebate on qualifying Hungarian expenditure. No cultural test for foreign. "
        "Minimum spend HUF 20,000,000 (~EUR 55,000 — very low threshold). "
        "Strong studio infrastructure: Origo Studios (Budapest). Deep crew base. "
        "Landlocked: no open-water marine access. "
        "Some studio tank facilities exist at Origo; limited vs Malta MFS.",
    ),

    # ---- Belgium (Secondary — DISCOVERY) ----
    _prog(
        PROG_BE_ID, BE_ID,
        "Belgian Tax Shelter",
        "be_tax_shelter",
        "regional_fund", "qualifying_spend",
        0.17, 0.40, None, None, None,
        True, "2003-01-01",
        "DISCOVERY",
        "https://taxshelter.be",
        "Belgian Tax Shelter: complex financing mechanism, not a direct rebate. "
        "Effective benefit for production: ~16-17% of qualifying Belgian spend via investor fundraising. "
        "Regional cash rebates (Flanders/Wallonia) may reach up to 40% — region-specific programs vary. "
        "Cultural test required (Belgian content points). "
        "Requires Belgian qualifying production expenditure. "
        "DISCOVERY tier: two separate mechanisms (Tax Shelter + regional rebates) require "
        "independent verification. Effective rate depends on deal structure.",
    ),

    # ---- Germany (Secondary — DISCOVERY) ----
    _prog(
        PROG_DE_ID, DE_ID,
        "German Federal Film Fund (DFFF/GFFF)",
        "de_dfff",
        "grant", "qualifying_spend",
        0.25, 0.25, True, None, 25_000_000.0,
        True, "2007-01-01",
        "DISCOVERY",
        "https://filmfoerderungsanstalt.de",
        "DFFF: 25% on qualifying German expenditure. Cultural/economic test required. "
        "Minimum German spend: 30% of total production budget (minimum spend rule). "
        "Cap EUR 25M per production (DFFF); higher allocations possible via GFFF for large productions. "
        "Very deep crew base; Bavaria Studios (Munich), Babelsberg (Berlin). "
        "Minimal marine access (North Sea/Baltic limited for warm-water productions). "
        "GFFF (Großer Filmförderfonds) supplements DFFF for large-budget productions.",
    ),
]

# ---------------------------------------------------------------------------
# Qualifying Spend Categories — Tier 1 (full entries)
# ---------------------------------------------------------------------------

QSC_ATL = [
    # All ATL categories qualify for Malta, Greece, Cyprus
    # (cash rebates cover all qualifying spend including ATL)
    *[_qsc("mt_mfc_rebate", PROG_MT_ID, cat, True, True,
           "ATL costs qualify as eligible Malta expenditure under MFC rebate.",
           "PARSED")
      for cat in ("atl_director", "atl_writer", "atl_producer", "atl_cast", "atl_rights")],

    *[_qsc("gr_cash_rebate", PROG_GR_ID, cat, True, True,
           "ATL costs qualify as eligible Greek expenditure under the 40% rebate.",
           "PARSED")
      for cat in ("atl_director", "atl_writer", "atl_producer", "atl_cast", "atl_rights")],

    *[_qsc("cy_film_rebate", PROG_CY_ID, cat, True, True,
           "ATL treatment expected to qualify; not confirmed from program statute. DISCOVERY.",
           "DISCOVERY")
      for cat in ("atl_director", "atl_writer", "atl_producer", "atl_cast")],

    # Mauritius: unknown
    *[_qsc("mu_edb_incentive", PROG_MU_ID, cat, False, True,
           "No verified incentive program. Flagged non-qualifying pending program confirmation.",
           "DISCOVERY")
      for cat in ("atl_director", "atl_writer", "atl_producer", "atl_cast")],
]

QSC_BTL = [
    # Malta — BTL categories
    *[_qsc("mt_mfc_rebate", PROG_MT_ID, cat, True, True,
           "BTL production costs qualify as eligible Malta expenditure.", "PARSED")
      for cat in (
          "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
          "btl_equipment_rental", "btl_stage_facility", "btl_location_fees",
          "btl_set_construction", "btl_transportation", "btl_catering",
      )],
    _qsc("mt_mfc_rebate", PROG_MT_ID, "vessel_marine", True, True,
         "Vessel charter, marine equipment, and underwater camera hire qualify as BTL production "
         "expenditure. Mediterranean Film Studios water tanks (750K gallon outdoor) add unique "
         "controlled water-filming capability with qualifying rebate.",
         "PARSED"),
    _qsc("mt_mfc_rebate", PROG_MT_ID, "payroll_fringes", True, True,
         "Maltese employer payroll fringes qualify as production expenditure.", "PARSED"),
    _qsc("mt_mfc_rebate", PROG_MT_ID, "travel", False, True,
         "Travel costs for non-Maltese cast/crew typically excluded or limited.", "DISCOVERY"),
    _qsc("mt_mfc_rebate", PROG_MT_ID, "lodging", True, True,
         "Accommodation costs for on-location stays qualify in many cash-rebate programs; "
         "verify against current MFC guidelines.", "DISCOVERY"),

    # Greece — BTL categories
    *[_qsc("gr_cash_rebate", PROG_GR_ID, cat, True, True,
           "BTL production costs qualify as eligible Greek expenditure.", "PARSED")
      for cat in (
          "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
          "btl_equipment_rental", "btl_stage_facility", "btl_location_fees",
          "btl_set_construction", "btl_transportation", "btl_catering",
      )],
    _qsc("gr_cash_rebate", PROG_GR_ID, "vessel_marine", True, True,
         "Vessel charter and marine support qualify as BTL production expenditure incurred in Greece. "
         "Piraeus/Greek shipping industry provides existing commercial vessel market.",
         "PARSED"),
    _qsc("gr_cash_rebate", PROG_GR_ID, "payroll_fringes", True, True,
         "Greek employer social contributions qualify as production expenditure.", "PARSED"),

    # Cyprus — BTL categories
    *[_qsc("cy_film_rebate", PROG_CY_ID, cat, True, True,
           "BTL production costs expected to qualify as eligible Cyprus expenditure. DISCOVERY.",
           "DISCOVERY")
      for cat in (
          "btl_crew_labor", "btl_equipment_rental", "btl_location_fees",
          "btl_transportation",
      )],
    _qsc("cy_film_rebate", PROG_CY_ID, "vessel_marine", True, True,
         "Vessel and marine costs expected to qualify; not confirmed from program statute.",
         "DISCOVERY"),

    # Mauritius — BTL (all non-qualifying pending program confirmation)
    *[_qsc("mu_edb_incentive", PROG_MU_ID, cat, False, True,
           "No verified incentive program. Flagged non-qualifying pending program confirmation.",
           "DISCOVERY")
      for cat in ("btl_crew_labor", "btl_equipment_rental", "vessel_marine")],
]

QSC_POST = [
    # Malta — post
    *[_qsc("mt_mfc_rebate", PROG_MT_ID, cat, True, True,
           "Post-production expenditure in Malta qualifies; +3% uplift available for "
           "VFX and post work performed in Malta.", "PARSED")
      for cat in ("post_production", "vfx", "music", "sound")],

    # Greece — post
    *[_qsc("gr_cash_rebate", PROG_GR_ID, cat, True, True,
           "Post-production qualifying spend in Greece eligible at 40% rate.", "PARSED")
      for cat in ("post_production", "vfx", "music", "sound")],

    # Cyprus — post
    *[_qsc("cy_film_rebate", PROG_CY_ID, cat, True, True,
           "Post-production expected to qualify; not confirmed from statute. DISCOVERY.",
           "DISCOVERY")
      for cat in ("post_production", "vfx")],
]

QSC_EXCLUDED = [
    # Finance/insurance/contingency excluded across all programs
    *[_qsc("mt_mfc_rebate", PROG_MT_ID, cat, False, False,
           "Finance costs, insurance, completion bond, and contingency are typically excluded "
           "from qualifying production expenditure under the MFC rebate.", "PARSED")
      for cat in ("finance_costs", "insurance", "completion_bond", "contingency")],

    *[_qsc("gr_cash_rebate", PROG_GR_ID, cat, False, False,
           "Finance costs, insurance, and contingency are excluded from qualifying Greek expenditure.",
           "PARSED")
      for cat in ("finance_costs", "insurance", "completion_bond", "contingency")],
]

# ---------------------------------------------------------------------------
# Qualifying Spend Categories — Secondary (abbreviated, vessel_marine only)
# ---------------------------------------------------------------------------

QSC_SECONDARY_VESSEL = [
    _qsc("ie_section_481", PROG_IE_ID, "vessel_marine", True, True,
         "Vessel and marine costs qualify as Irish production expenditure under Section 481. "
         "Atlantic coastline access. DISCOVERY — confirm from Revenue guidance.", "DISCOVERY"),
    _qsc("fr_trip", PROG_FR_ID, "vessel_marine", True, True,
         "Marine costs qualify as French qualifying expenditure under TRIP. DISCOVERY.", "DISCOVERY"),
    _qsc("it_tax_credit_foreign", PROG_IT_ID, "vessel_marine", True, True,
         "Vessel costs qualify as Italian qualifying expenditure. DISCOVERY.", "DISCOVERY"),
    _qsc("es_tax_credit_foreign", PROG_ES_ID, "vessel_marine", True, True,
         "Marine/vessel costs qualify; Canary Islands (50%) rate particularly advantageous "
         "for warm-water marine productions. DISCOVERY.", "DISCOVERY"),
    _qsc("hr_cash_rebate", PROG_HR_ID, "vessel_marine", True, True,
         "Vessel costs qualify as Croatian production expenditure. Adriatic coastline strong "
         "for marine filming. DISCOVERY.", "DISCOVERY"),
    _qsc("hu_hipa_rebate", PROG_HU_ID, "vessel_marine", False, True,
         "Hungary landlocked; vessel/marine costs would not be incurred in jurisdiction.",
         "DISCOVERY"),
    _qsc("be_tax_shelter", PROG_BE_ID, "vessel_marine", True, True,
         "Marine costs can qualify if Belgian production spend; North Sea coastal access limited. "
         "DISCOVERY.", "DISCOVERY"),
    _qsc("de_dfff", PROG_DE_ID, "vessel_marine", True, True,
         "Vessel costs qualify if incurred in Germany. North Sea/Baltic limited for warm-water. "
         "DISCOVERY.", "DISCOVERY"),
]

# ---------------------------------------------------------------------------
# Incentive Rules — Tier 1 minimum spend
# ---------------------------------------------------------------------------

RULES = [
    # Malta
    _rule(PROG_MT_ID, "minimum_qualified_spend", 50_000.0, "EUR 50,000",
          "disqualify",
          "Minimum qualifying Malta expenditure of EUR 50,000 required to claim MFC rebate.",
          "Malta Film Commission Rebate Guidelines", "PARSED"),

    # Greece
    _rule(PROG_GR_ID, "minimum_qualified_spend", 100_000.0, "EUR 100,000",
          "disqualify",
          "Minimum qualifying Greek expenditure of EUR 100,000 required.",
          "Enterprise Greece — Film Production Rebate Guidelines", "PARSED"),

    # Cyprus
    _rule(PROG_CY_ID, "minimum_qualified_spend", 100_000.0, "EUR 100,000",
          "disqualify",
          "Minimum qualifying Cyprus expenditure of EUR 100,000 (unverified from statute).",
          "CIPA Film Rebate — unverified", "DISCOVERY"),

    # Ireland — 80% spend cap
    _rule(PROG_IE_ID, "spend_cap_pct", 0.80, "80% of total budget",
          "reduce_credit",
          "Qualifying expenditure capped at 80% of total production budget or EUR 70M, "
          "whichever is lower. Prevents 100% Irish spend scenarios.",
          "Finance Act, Section 481", "PARSED"),
    _rule(PROG_IE_ID, "minimum_qualified_spend", 125_000.0, "EUR 125,000",
          "disqualify",
          "Minimum qualifying Irish spend of EUR 125,000.",
          "Finance Act, Section 481", "PARSED"),

    # Italy — project cap
    _rule(PROG_IT_ID, "minimum_qualified_spend", 1_000_000.0, "EUR 1,000,000",
          "disqualify",
          "Minimum qualifying Italian spend of EUR 1,000,000 for foreign productions.",
          "DL 91/2013 and implementing decrees", "DISCOVERY"),

    # Spain — minimum spend
    _rule(PROG_ES_ID, "minimum_qualified_spend", 1_000_000.0, "EUR 1,000,000",
          "disqualify",
          "Minimum qualifying Spanish spend of EUR 1,000,000 (mainland rate). "
          "Canary Islands may have different threshold.",
          "Ley 27/2014, Art. 36", "DISCOVERY"),

    # Croatia
    _rule(PROG_HR_ID, "minimum_qualified_spend", 200_000.0, "EUR 200,000",
          "disqualify",
          "Minimum qualifying Croatian spend of EUR 200,000 (formerly HRK 1.5M; "
          "Croatia adopted EUR Jan 2023).",
          "HAVC Cash Rebate Guidelines", "DISCOVERY"),

    # Hungary
    _rule(PROG_HU_ID, "minimum_qualified_spend", 55_000.0, "HUF 20,000,000 (~EUR 55,000)",
          "disqualify",
          "Minimum qualifying Hungarian spend of HUF 20,000,000 (very low threshold).",
          "Act on Film (2004), Hungarian Film Fund rules", "DISCOVERY"),

    # Germany — 30% local spend requirement
    _rule(PROG_DE_ID, "minimum_jurisdiction_spend_pct", 0.30, "30% of total budget",
          "disqualify",
          "Minimum 30% of total production budget must be qualifying German expenditure "
          "for DFFF eligibility. Structural gate for international co-productions.",
          "DFFF Guidelines, BKM", "DISCOVERY"),
    _rule(PROG_DE_ID, "minimum_qualified_spend", 1_000_000.0, "EUR 1,000,000",
          "disqualify",
          "Minimum qualifying German spend of EUR 1,000,000 for DFFF.",
          "DFFF Guidelines, BKM", "DISCOVERY"),
]

# ---------------------------------------------------------------------------
# Program Uplifts — Malta (most documented)
# ---------------------------------------------------------------------------

UPLIFTS = [
    _uplift(PROG_MT_ID, "Maltese Elements",
            0.02, "same_qualifying_spend",
            "maltese_production_elements",
            "Additional 2% when production includes qualified Maltese cultural elements "
            "(Maltese cast, crew, locations, or cultural content as defined by MFC).",
            "PARSED"),
    _uplift(PROG_MT_ID, "MFC Cultural Contribution",
            0.03, "same_qualifying_spend",
            "maltese_production_elements",
            "Additional 3% MFC cultural contribution for productions meeting MFC content guidelines.",
            "DISCOVERY"),
    _uplift(PROG_MT_ID, "VFX and Post in Malta",
            0.03, "vfx_spend_only",
            "vfx_performed_in_jurisdiction",
            "Additional 3% on VFX and post-production spend when work is performed in Malta.",
            "PARSED"),
    _uplift(PROG_MT_ID, "Small Budget Bonus",
            0.07, "same_qualifying_spend",
            "budget_under",
            "Additional 7% uplift for productions with total budget under EUR 3,000,000.",
            "DISCOVERY"),
    # Spain Canary Islands uplift
    _uplift(PROG_ES_ID, "Canary Islands Rate",
            0.20, "same_qualifying_spend",
            "shooting_location",
            "Productions shooting in the Canary Islands qualify for 50% total rate (base 30% + "
            "20% Canary Islands uplift). Warm-water marine productions: strong candidate.",
            "DISCOVERY"),
]


# ---------------------------------------------------------------------------
# Alembic upgrade / downgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    jur_table = sa.table(
        "jurisdictions",
        sa.column("id", sa.String),
        sa.column("parent_id", sa.String),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("iso_code", sa.String),
        sa.column("level", sa.String),
        sa.column("currency_code", sa.String),
        sa.column("country_code", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("metadata_json", postgresql.JSONB),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )

    prog_table = sa.table(
        "incentive_programs",
        sa.column("id", sa.String),
        sa.column("jurisdiction_id", sa.String),
        sa.column("source_document_id", sa.String),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("program_type", sa.String),
        sa.column("credit_basis", sa.String),
        sa.column("base_rate", sa.Numeric),
        sa.column("max_rate", sa.Numeric),
        sa.column("is_refundable", sa.Boolean),
        sa.column("is_transferable", sa.Boolean),
        sa.column("transferable_value_pct", sa.Numeric),
        sa.column("is_competitive", sa.Boolean),
        sa.column("annual_cap_local", sa.Numeric),
        sa.column("fixed_grant_amount_usd", sa.Numeric),
        sa.column("requires_cultural_test", sa.Boolean),
        sa.column("cultural_test_id", sa.String),
        sa.column("requires_local_entity", sa.Boolean),
        sa.column("effective_from", sa.String),
        sa.column("effective_until", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("review_status", sa.String),
        sa.column("authority_url", sa.String),
        sa.column("last_verified_date", sa.String),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )

    qsc_table = sa.table(
        "qualifying_spend_categories",
        sa.column("id", sa.String),
        sa.column("program_id", sa.String),
        sa.column("spend_category", sa.String),
        sa.column("qualifies", sa.Boolean),
        sa.column("jurisdiction_spend_only", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )

    rule_table = sa.table(
        "incentive_rules",
        sa.column("id", sa.String),
        sa.column("program_id", sa.String),
        sa.column("source_document_id", sa.String),
        sa.column("rule_type", sa.String),
        sa.column("threshold_numeric", sa.Numeric),
        sa.column("threshold_text", sa.String),
        sa.column("fail_action", sa.String),
        sa.column("description", sa.Text),
        sa.column("source_page", sa.Integer),
        sa.column("source_excerpt", sa.Text),
        sa.column("statutory_reference", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )

    uplift_table = sa.table(
        "program_uplifts",
        sa.column("id", sa.String),
        sa.column("program_id", sa.String),
        sa.column("name", sa.String),
        sa.column("additional_rate", sa.Numeric),
        sa.column("applies_to", sa.String),
        sa.column("condition_type", sa.String),
        sa.column("condition_threshold", sa.Numeric),
        sa.column("condition_text", sa.String),
        sa.column("is_stackable_with_other_uplifts", sa.Boolean),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )

    op.bulk_insert(jur_table, JURISDICTIONS)
    op.bulk_insert(prog_table, PROGRAMS)

    all_qsc = QSC_ATL + QSC_BTL + QSC_POST + QSC_EXCLUDED + QSC_SECONDARY_VESSEL
    op.bulk_insert(qsc_table, all_qsc)

    op.bulk_insert(rule_table, RULES)
    op.bulk_insert(uplift_table, UPLIFTS)


def downgrade() -> None:
    prog_ids = ", ".join(f"'{p}'" for p in ALL_PROG_IDS)
    jur_ids = ", ".join(f"'{j}'" for j in ALL_JUR_IDS)

    op.execute(f"DELETE FROM program_uplifts WHERE program_id IN ({prog_ids})")
    op.execute(f"DELETE FROM incentive_rules WHERE program_id IN ({prog_ids})")
    op.execute(f"DELETE FROM qualifying_spend_categories WHERE program_id IN ({prog_ids})")
    op.execute(f"DELETE FROM incentive_programs WHERE id IN ({prog_ids})")
    op.execute(f"DELETE FROM jurisdictions WHERE id IN ({jur_ids})")
