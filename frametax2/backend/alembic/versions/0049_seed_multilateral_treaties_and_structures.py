"""0049 — Seed multilateral treaties, treaty_participants, and co-production structures.

Seeds:
  - 3 multilateral treaties: Eurimages, European Convention, Ibermedia
  - Eurimages members (44 countries) in treaty_participants
  - European Convention members (44 countries, same as Eurimages)
  - Ibermedia members (21 Latin American + Iberian countries)
  - ~20 co-production structures linking bilateral and multilateral treaties

Revision ID: 0049
Revises: 0048
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: Union[str, None] = "0048"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Multilateral treaty definitions
# ---------------------------------------------------------------------------
_MULTILATERAL_TREATIES = [
    {
        "treaty_name": "Eurimages Co-production Support Fund",
        "treaty_slug": "eurimages-multilateral",
        "treaty_type": "eurimages",
        "status": "active",
        "jurisdiction_a_code": "EU",
        "jurisdiction_b_code": None,
        "year_signed": 1988,
        "effective_from": "1988-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "10.00",
        "minority_min_contribution_pct": "10.00",
        "minority_max_contribution_pct": None,
        "min_coproducer_countries": 3,
        "spend_allocation_requirement": (
            "Each co-producing country must have a genuine financial and creative contribution. "
            "Minimum 10% of budget per co-producer required for Eurimages eligibility. "
            "At least one co-producer must be from a Council of Europe member state."
        ),
        "nationality_requirement": (
            "Director and majority of cast and crew must be from Council of Europe member states. "
            "No single country's nationals can exceed 80% of key creative personnel."
        ),
        "creative_contribution_requirement": (
            "Each co-producer must make genuine creative contribution. "
            "Project must reflect the cultural heritage of at least one Council of Europe member state."
        ),
        "cultural_test_required": True,
        "ownership_requirement": (
            "Copyright shared proportionally. Exploitation rights by territory. "
            "Each co-producer retains rights in their own territory."
        ),
        "majority_jurisdiction_benefits": (
            "Access to Eurimages co-production fund (up to €500k–€1.5M per feature). "
            "Each national co-producer independently accesses their own national incentives "
            "(UK AVEC, French tax crédit, German DFFF, Italian MiC credit, etc.)."
        ),
        "minority_jurisdiction_benefits": (
            "All co-producers access Eurimages support simultaneously with their own national funds. "
            "Minority co-producers access same national incentives as majority."
        ),
        "treaty_administrator_name": "Council of Europe / Eurimages",
        "authority_url": "https://www.coe.int/en/web/eurimages",
        "confidence_tier": "PARSED",
        "notes": (
            "Eurimages is a pan-European fund requiring minimum 3 co-producers from member states. "
            "Maximum grant ~€1.5M for features; smaller for documentaries and animation."
        ),
    },
    {
        "treaty_name": "European Convention on Cinematographic Co-production",
        "treaty_slug": "european-convention-coproduction",
        "treaty_type": "european_convention",
        "status": "active",
        "jurisdiction_a_code": "EU",
        "jurisdiction_b_code": None,
        "year_signed": 1992,
        "effective_from": "1994-04-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "10.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Budget allocation must reflect each co-producer's creative contribution. "
            "For bilateral co-productions under the Convention, majority party must hold 30–70% "
            "and minority party at least 10%."
        ),
        "nationality_requirement": (
            "Majority of creative personnel must be European. Director must be European. "
            "For bilateral co-productions, key creatives from both countries required."
        ),
        "creative_contribution_requirement": (
            "Both/all parties must make genuine creative contributions. "
            "Applies to Council of Europe member states. Provides a legal framework "
            "making the production 'European' for quota and certification purposes."
        ),
        "cultural_test_required": True,
        "ownership_requirement": (
            "Copyright shared proportionally. "
            "Each co-producer holds rights for their own territory."
        ),
        "majority_jurisdiction_benefits": (
            "Production certified as 'European' — satisfies national quota requirements "
            "in all signatory states. Enables access to national incentive programs "
            "(AVEC, tax crédit, DFFF, MiC, etc.) as if fully national."
        ),
        "minority_jurisdiction_benefits": (
            "Minority co-producers gain 'European' certification for their home territory, "
            "unlocking national incentives and broadcaster quota access."
        ),
        "treaty_administrator_name": "Council of Europe",
        "authority_url": "https://www.coe.int/en/web/conventions/full-list/-/conventions/treaty/147",
        "confidence_tier": "PARSED",
        "notes": (
            "The European Convention provides the foundational legal framework "
            "for bilateral and multilateral European co-productions. "
            "Updated by the 2017 revision (CETS No. 220)."
        ),
    },
    {
        "treaty_name": "Ibermedia Co-production Programme",
        "treaty_slug": "ibermedia-multilateral",
        "treaty_type": "ibermedia",
        "status": "active",
        "jurisdiction_a_code": "ES",
        "jurisdiction_b_code": None,
        "year_signed": 1997,
        "effective_from": "1997-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "10.00",
        "minority_max_contribution_pct": None,
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Projects must involve producers from at least 2 Ibermedia member states. "
            "Budget allocation proportional to creative contribution. "
            "Majority producer holds project lead role."
        ),
        "nationality_requirement": (
            "Director must be a national of an Ibermedia member state. "
            "Majority of key creative personnel from Ibermedia member states."
        ),
        "creative_contribution_requirement": (
            "All co-producers must contribute creatively to the project. "
            "Script must reflect Ibero-American cultural identity."
        ),
        "cultural_test_required": True,
        "ownership_requirement": (
            "Copyright shared proportionally. "
            "Ibermedia requires co-producers to maintain rights in their own territories."
        ),
        "majority_jurisdiction_benefits": (
            "Access to Ibermedia development, co-production and distribution grants "
            "(€60k–€300k per project). Production treated as local in all member states, "
            "enabling full access to each country's national incentives."
        ),
        "minority_jurisdiction_benefits": (
            "All co-producers independently access their national incentives. "
            "Ibermedia grants distributed to all co-producers proportionally."
        ),
        "treaty_administrator_name": "SEGIB / Ibermedia Secretariat",
        "authority_url": "https://www.programaibermedia.com",
        "confidence_tier": "PARSED",
        "notes": (
            "21 member states: Argentina, Bolivia, Brazil, Chile, Colombia, Costa Rica, "
            "Cuba, Dominican Republic, Ecuador, El Salvador, Guatemala, Honduras, "
            "Mexico, Nicaragua, Panama, Paraguay, Peru, Portugal, Spain, Uruguay, Venezuela."
        ),
    },
]

# ---------------------------------------------------------------------------
# Eurimages / European Convention member states (44 countries)
# ---------------------------------------------------------------------------
_EURIMAGES_MEMBERS = [
    ("AL", "Albania"), ("AM", "Armenia"), ("AT", "Austria"), ("AZ", "Azerbaijan"),
    ("BE", "Belgium"), ("BA", "Bosnia and Herzegovina"), ("HR", "Croatia"),
    ("CY", "Cyprus"), ("CZ", "Czech Republic"), ("DK", "Denmark"),
    ("EE", "Estonia"), ("FI", "Finland"), ("FR", "France"), ("GE", "Georgia"),
    ("DE", "Germany"), ("GR", "Greece"), ("HU", "Hungary"), ("IS", "Iceland"),
    ("IE", "Ireland"), ("IT", "Italy"), ("LV", "Latvia"), ("LI", "Liechtenstein"),
    ("LT", "Lithuania"), ("LU", "Luxembourg"), ("MT", "Malta"),
    ("MD", "Moldova"), ("ME", "Montenegro"), ("NL", "Netherlands"),
    ("MK", "North Macedonia"), ("NO", "Norway"), ("PL", "Poland"),
    ("PT", "Portugal"), ("RO", "Romania"), ("SM", "San Marino"),
    ("RS", "Serbia"), ("SK", "Slovakia"), ("SI", "Slovenia"),
    ("ES", "Spain"), ("SE", "Sweden"), ("CH", "Switzerland"),
    ("TR", "Turkey"), ("UA", "Ukraine"), ("GB", "United Kingdom"),
    ("VA", "Vatican City"),
]

# ---------------------------------------------------------------------------
# Ibermedia member states (21 countries)
# ---------------------------------------------------------------------------
_IBERMEDIA_MEMBERS = [
    ("AR", "Argentina"), ("BO", "Bolivia"), ("BR", "Brazil"), ("CL", "Chile"),
    ("CO", "Colombia"), ("CR", "Costa Rica"), ("CU", "Cuba"),
    ("DO", "Dominican Republic"), ("EC", "Ecuador"), ("SV", "El Salvador"),
    ("GT", "Guatemala"), ("HN", "Honduras"), ("MX", "Mexico"),
    ("NI", "Nicaragua"), ("PA", "Panama"), ("PY", "Paraguay"), ("PE", "Peru"),
    ("PT", "Portugal"), ("ES", "Spain"), ("UY", "Uruguay"), ("VE", "Venezuela"),
]

# ---------------------------------------------------------------------------
# Co-production structures
# ---------------------------------------------------------------------------
_STRUCTURES = [
    # UK bilateral structures
    {
        "name": "UK–Canada Official Co-production (UK Majority)",
        "structure_slug": "uk-ca-bilateral-uk-majority",
        "treaty_slug": "uk-ca-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "GB",
        "minority_country_code": "CA",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "ca_federal_cptc,ca_cmf",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Production treated as British for UK nationality test. "
            "Canadian co-producer's spend counts as Canadian content for CMF/CRTC purposes."
        ),
        "cultural_test_impact": (
            "UK majority: Cultural Test administered by BFI; target 18/35 points. "
            "Production does not need to pass BFI Cultural Test separately."
        ),
        "financing_structure_notes": (
            "UK co-producer holds 30–80% of budget; Canadian co-producer holds 20–70%. "
            "UK spend triggers AVEC (20–40% of UK qualifying spend). "
            "Canadian spend triggers CPTC (25% of Canadian qualifying labour)."
        ),
        "eligibility_requirements": (
            "Requires formal co-production agreement approved by BFI and Telefilm Canada. "
            "Application required before principal photography begins."
        ),
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "name": "UK–Canada Official Co-production (Canada Majority)",
        "structure_slug": "uk-ca-bilateral-ca-majority",
        "treaty_slug": "uk-ca-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "CA",
        "minority_country_code": "GB",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "ca_federal_cptc,ca_cmf",
        "unlocks_minority_incentive_slugs": "uk_avec",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Production treated as Canadian for CRTC/CMF purposes. "
            "UK co-producer's spend qualifies for AVEC."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "Canadian co-producer holds 30–80% of budget; UK holds 20–70%. "
            "Canadian spend triggers CPTC and CMF. "
            "UK spend triggers AVEC on UK qualifying portion."
        ),
        "eligibility_requirements": (
            "Formal co-production agreement approved by Telefilm Canada and BFI required."
        ),
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "name": "UK–Australia Official Co-production",
        "structure_slug": "uk-au-bilateral-uk-majority",
        "treaty_slug": "uk-au-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "GB",
        "minority_country_code": "AU",
        "additional_country_codes": None,
        "majority_min_pct": "20.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "80.00",
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "au_producer_offset",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Production treated as British; Australian spend qualifies for Producer Offset."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "UK spend triggers AVEC; Australian spend triggers Producer Offset (40% feature / 20% TV)."
        ),
        "eligibility_requirements": (
            "Formal co-production agreement approved by BFC and Screen Australia required."
        ),
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "name": "UK–France Official Co-production",
        "structure_slug": "uk-fr-bilateral-uk-majority",
        "treaty_slug": "uk-fr-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "GB",
        "minority_country_code": "FR",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "fr_tax_credit_cinema",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as British for UK purposes; treated as French for CNC/Canal+ purposes."
        ),
        "cultural_test_impact": (
            "French side must pass CNC cultural test. UK side: BFI Cultural Test applies."
        ),
        "financing_structure_notes": (
            "UK 30–80%; France 20–70%. UK spend → AVEC. French spend → tax crédit cinéma (30%)."
        ),
        "eligibility_requirements": "Formal co-production agreement approved by BFI and CNC.",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "name": "UK–Ireland Official Co-production",
        "structure_slug": "uk-ie-bilateral-uk-majority",
        "treaty_slug": "uk-ie-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "GB",
        "minority_country_code": "IE",
        "additional_country_codes": None,
        "majority_min_pct": "20.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "80.00",
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "ie_section_481",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "UK-treated production. Irish spend qualifies for Section 481 relief."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "UK spend → AVEC (20–40%). Irish spend → Section 481 (32% on Irish qualifying spend)."
        ),
        "eligibility_requirements": "Approved by BFI and Screen Ireland.",
        "confidence_tier": "PARSED",
        "notes": "Very common structure for Anglo-Irish productions.",
    },
    {
        "name": "Canada–France Official Co-production (Canada Majority)",
        "structure_slug": "ca-fr-bilateral-ca-majority",
        "treaty_slug": "ca-fr-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "CA",
        "minority_country_code": "FR",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "ca_federal_cptc,ca_cmf",
        "unlocks_minority_incentive_slugs": "fr_tax_credit_cinema",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as Canadian content for CRTC/CMF. French portion qualifies for CNC."
        ),
        "cultural_test_impact": (
            "Québec-majority structure may also access QPRDP + CNC simultaneously."
        ),
        "financing_structure_notes": (
            "Canadian 30–80%; France 20–70%. CPTC on Canadian labour; "
            "tax crédit cinéma on French qualifying spend."
        ),
        "eligibility_requirements": "Approved by Telefilm Canada and CNC.",
        "confidence_tier": "PARSED",
        "notes": "Québec + France is a particularly strong structure (QPRDP + tax crédit + CMF).",
    },
    {
        "name": "Eurimages Trilateral Co-production",
        "structure_slug": "eurimages-trilateral-standard",
        "treaty_slug": "eurimages-multilateral",
        "structure_type": "treaty_multilateral",
        "majority_country_code": None,
        "minority_country_code": None,
        "additional_country_codes": None,
        "majority_min_pct": "10.00",
        "minority_min_pct": "10.00",
        "minority_max_pct": None,
        "unlocks_majority_incentive_slugs": None,
        "unlocks_minority_incentive_slugs": None,
        "unlocks_fund_slugs": "eurimages_coproduction_support",
        "nationality_test_impact": (
            "Each co-producer's production is treated as national in their own country, "
            "enabling them to independently access their national incentive programs."
        ),
        "cultural_test_impact": (
            "Cultural test requirements of each territory apply independently. "
            "Project must demonstrate European cultural character."
        ),
        "financing_structure_notes": (
            "Minimum 3 co-producers from Eurimages member states. "
            "Each holds ≥10% of budget. Eurimages grant (up to €1.5M) shared between co-producers. "
            "Each co-producer independently accesses national incentives on their own spend."
        ),
        "eligibility_requirements": (
            "Application to Eurimages required 6 weeks before board meeting. "
            "Must have formal co-production agreements between all parties. "
            "Principal photography must not have started at time of application."
        ),
        "confidence_tier": "PARSED",
        "notes": (
            "Best structure when 3+ European territories are naturally involved. "
            "Eurimages grant is non-repayable up to 17.5% of budget (≤€1.5M for features)."
        ),
    },
    {
        "name": "Eurimages + AVEC + DFFF Trilateral Structure",
        "structure_slug": "eurimages-uk-de-trilateral",
        "treaty_slug": "eurimages-multilateral",
        "structure_type": "treaty_multilateral",
        "majority_country_code": "GB",
        "minority_country_code": "DE",
        "additional_country_codes": "FR",
        "majority_min_pct": "10.00",
        "minority_min_pct": "10.00",
        "minority_max_pct": None,
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "de_dfff",
        "unlocks_fund_slugs": "eurimages_coproduction_support",
        "nationality_test_impact": (
            "UK spend treated as British (AVEC eligible). "
            "German spend treated as German (DFFF eligible). "
            "French spend treated as French (tax crédit eligible)."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "UK, Germany, France co-production with Eurimages backing. "
            "AVEC on UK spend + DFFF on German spend + tax crédit on French spend + Eurimages grant."
        ),
        "eligibility_requirements": (
            "Eurimages application required. Individual national certifications also required."
        ),
        "confidence_tier": "PARSED",
        "notes": "Highest-value structure for major European features.",
    },
    {
        "name": "European Convention Bilateral Co-production",
        "structure_slug": "european-convention-bilateral",
        "treaty_slug": "european-convention-coproduction",
        "structure_type": "treaty_bilateral",
        "majority_country_code": None,
        "minority_country_code": None,
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "10.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": None,
        "unlocks_minority_incentive_slugs": None,
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Production certified as European, satisfying quota requirements in all signatory states. "
            "Each national co-producer accesses their own national incentives."
        ),
        "cultural_test_impact": (
            "European cultural character required. Each territory's national cultural "
            "test may apply independently."
        ),
        "financing_structure_notes": (
            "Framework provides legal basis for bilateral and multilateral European co-productions. "
            "Majority holds 30–70%; minority holds 10–70%. Multiple minorities allowed (each ≥10%)."
        ),
        "eligibility_requirements": (
            "Co-production agreement must reference the European Convention. "
            "Application to competent authority of each co-producing state required."
        ),
        "confidence_tier": "PARSED",
        "notes": (
            "The Convention is the fallback framework for European bilateral structures "
            "where no specific bilateral treaty exists between the parties."
        ),
    },
    {
        "name": "Ibermedia Bilateral Co-production Structure",
        "structure_slug": "ibermedia-bilateral-standard",
        "treaty_slug": "ibermedia-multilateral",
        "structure_type": "treaty_multilateral",
        "majority_country_code": None,
        "minority_country_code": None,
        "additional_country_codes": None,
        "majority_min_pct": "20.00",
        "minority_min_pct": "10.00",
        "minority_max_pct": None,
        "unlocks_majority_incentive_slugs": None,
        "unlocks_minority_incentive_slugs": None,
        "unlocks_fund_slugs": "ibermedia_coproduction_fund",
        "nationality_test_impact": (
            "Production treated as local in all participating Ibermedia member states, "
            "enabling each co-producer to access their own national incentives."
        ),
        "cultural_test_impact": (
            "Must reflect Ibero-American cultural identity. "
            "Cultural test of each participating territory applies."
        ),
        "financing_structure_notes": (
            "Minimum 2 producers from Ibermedia member states. "
            "Majority holds ≥20%; minority holds ≥10%. "
            "Ibermedia grant (€60k–€300k) available. "
            "Each co-producer accesses national incentives on their own spend."
        ),
        "eligibility_requirements": (
            "Application to Ibermedia Secretariat (Madrid) required before production start. "
            "Producers must be nationals of or legally domiciled in Ibermedia member states."
        ),
        "confidence_tier": "PARSED",
        "notes": "Key structure for Spain+Latin America, Portugal+Brazil co-productions.",
    },
    {
        "name": "Canada–Ireland Official Co-production",
        "structure_slug": "ca-ie-bilateral-ca-majority",
        "treaty_slug": "ca-ie-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "CA",
        "minority_country_code": "IE",
        "additional_country_codes": None,
        "majority_min_pct": "20.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "80.00",
        "unlocks_majority_incentive_slugs": "ca_federal_cptc,ca_cmf",
        "unlocks_minority_incentive_slugs": "ie_section_481",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as Canadian content for CRTC/CMF. Irish spend qualifies for Section 481."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "Canadian 20–80%; Ireland 20–80%. CPTC on Canadian labour; Section 481 on Irish qualifying spend."
        ),
        "eligibility_requirements": "Approved by Telefilm Canada and Screen Ireland.",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "name": "France–Germany Official Co-production",
        "structure_slug": "fr-de-bilateral-fr-majority",
        "treaty_slug": "fr-de-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "FR",
        "minority_country_code": "DE",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "fr_tax_credit_cinema",
        "unlocks_minority_incentive_slugs": "de_dfff",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as French for CNC/Canal+ purposes. German spend qualifies for DFFF and Länder funds."
        ),
        "cultural_test_impact": "French cultural test (CNC) applies for French-majority.",
        "financing_structure_notes": (
            "France 30–80%; Germany 20–70%. "
            "French spend → tax crédit cinéma (30%). German spend → DFFF (~20%)."
        ),
        "eligibility_requirements": "Approved by CNC and FFA.",
        "confidence_tier": "PARSED",
        "notes": "Most common continental bilateral structure; Arte involvement common.",
    },
    {
        "name": "France–Belgium Official Co-production",
        "structure_slug": "fr-be-bilateral-fr-majority",
        "treaty_slug": "fr-be-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "FR",
        "minority_country_code": "BE",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "fr_tax_credit_cinema",
        "unlocks_minority_incentive_slugs": "be_tax_shelter",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as French for CNC. Belgian spend qualifies for tax shelter."
        ),
        "cultural_test_impact": "French cultural test (CNC) applies.",
        "financing_structure_notes": (
            "France 30–80%; Belgium 20–70%. "
            "French spend → tax crédit cinéma. Belgian spend → tax shelter (30%)."
        ),
        "eligibility_requirements": "Approved by CNC and Centre du Cinéma / VAF.",
        "confidence_tier": "PARSED",
        "notes": "France-Wallonia structures very common for francophone European co-productions.",
    },
    {
        "name": "UK–Germany Official Co-production",
        "structure_slug": "uk-de-bilateral-uk-majority",
        "treaty_slug": "uk-de-bilateral",
        "structure_type": "treaty_bilateral",
        "majority_country_code": "GB",
        "minority_country_code": "DE",
        "additional_country_codes": None,
        "majority_min_pct": "30.00",
        "minority_min_pct": "20.00",
        "minority_max_pct": "70.00",
        "unlocks_majority_incentive_slugs": "uk_avec",
        "unlocks_minority_incentive_slugs": "de_dfff",
        "unlocks_fund_slugs": None,
        "nationality_test_impact": (
            "Treated as British for UK purposes. German spend qualifies for DFFF."
        ),
        "cultural_test_impact": None,
        "financing_structure_notes": (
            "UK 30–80%; Germany 20–70%. UK spend → AVEC (20–40%). German spend → DFFF (~20%)."
        ),
        "eligibility_requirements": "Approved by BFI and FFA.",
        "confidence_tier": "PARSED",
        "notes": None,
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Seed multilateral treaties
    for t in _MULTILATERAL_TREATIES:
        conn.execute(
            sa.text(
                """
                INSERT INTO co_production_treaties (
                    treaty_name, treaty_slug, treaty_type, status,
                    jurisdiction_a_code, jurisdiction_b_code,
                    year_signed, effective_from, effective_until,
                    majority_min_contribution_pct, minority_min_contribution_pct,
                    minority_max_contribution_pct, min_coproducer_countries,
                    spend_allocation_requirement, nationality_requirement,
                    creative_contribution_requirement, cultural_test_required,
                    ownership_requirement,
                    majority_jurisdiction_benefits, minority_jurisdiction_benefits,
                    treaty_administrator_name, authority_url,
                    confidence_tier, notes
                ) VALUES (
                    :treaty_name, :treaty_slug, :treaty_type, :status,
                    :jurisdiction_a_code, :jurisdiction_b_code,
                    :year_signed, :effective_from, :effective_until,
                    :majority_min_contribution_pct, :minority_min_contribution_pct,
                    :minority_max_contribution_pct, :min_coproducer_countries,
                    :spend_allocation_requirement, :nationality_requirement,
                    :creative_contribution_requirement, :cultural_test_required,
                    :ownership_requirement,
                    :majority_jurisdiction_benefits, :minority_jurisdiction_benefits,
                    :treaty_administrator_name, :authority_url,
                    :confidence_tier, :notes
                )
                ON CONFLICT (treaty_slug) DO NOTHING
                """
            ),
            t,
        )

    # 2. Seed Eurimages treaty_participants
    eurimages_id_row = conn.execute(
        sa.text("SELECT id FROM co_production_treaties WHERE treaty_slug = 'eurimages-multilateral'")
    ).fetchone()
    if eurimages_id_row:
        eurimages_id = eurimages_id_row[0]
        for code, name in _EURIMAGES_MEMBERS:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO treaty_participants
                        (treaty_id, jurisdiction_code, jurisdiction_name, is_founding_member, status)
                    VALUES (:treaty_id, :code, :name, false, 'active')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"treaty_id": eurimages_id, "code": code, "name": name},
            )

    # 3. Seed European Convention treaty_participants
    ecco_id_row = conn.execute(
        sa.text("SELECT id FROM co_production_treaties WHERE treaty_slug = 'european-convention-coproduction'")
    ).fetchone()
    if ecco_id_row:
        ecco_id = ecco_id_row[0]
        for code, name in _EURIMAGES_MEMBERS:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO treaty_participants
                        (treaty_id, jurisdiction_code, jurisdiction_name, is_founding_member, status)
                    VALUES (:treaty_id, :code, :name, false, 'active')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"treaty_id": ecco_id, "code": code, "name": name},
            )

    # 4. Seed Ibermedia treaty_participants
    ibermedia_id_row = conn.execute(
        sa.text("SELECT id FROM co_production_treaties WHERE treaty_slug = 'ibermedia-multilateral'")
    ).fetchone()
    if ibermedia_id_row:
        ibermedia_id = ibermedia_id_row[0]
        for code, name in _IBERMEDIA_MEMBERS:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO treaty_participants
                        (treaty_id, jurisdiction_code, jurisdiction_name, is_founding_member, status)
                    VALUES (:treaty_id, :code, :name, false, 'active')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"treaty_id": ibermedia_id, "code": code, "name": name},
            )

    # 5. Seed co_production_structures
    for s in _STRUCTURES:
        treaty_slug = s.pop("treaty_slug")
        treaty_id_row = conn.execute(
            sa.text("SELECT id FROM co_production_treaties WHERE treaty_slug = :slug"),
            {"slug": treaty_slug},
        ).fetchone()
        treaty_id = treaty_id_row[0] if treaty_id_row else None

        conn.execute(
            sa.text(
                """
                INSERT INTO co_production_structures (
                    name, structure_slug, treaty_id, structure_type,
                    majority_country_code, minority_country_code, additional_country_codes,
                    majority_min_pct, minority_min_pct, minority_max_pct,
                    unlocks_majority_incentive_slugs, unlocks_minority_incentive_slugs,
                    unlocks_fund_slugs,
                    nationality_test_impact, cultural_test_impact,
                    financing_structure_notes, eligibility_requirements,
                    confidence_tier, notes
                ) VALUES (
                    :name, :structure_slug, :treaty_id, :structure_type,
                    :majority_country_code, :minority_country_code, :additional_country_codes,
                    :majority_min_pct, :minority_min_pct, :minority_max_pct,
                    :unlocks_majority_incentive_slugs, :unlocks_minority_incentive_slugs,
                    :unlocks_fund_slugs,
                    :nationality_test_impact, :cultural_test_impact,
                    :financing_structure_notes, :eligibility_requirements,
                    :confidence_tier, :notes
                )
                ON CONFLICT (structure_slug) DO NOTHING
                """
            ),
            {**s, "treaty_id": treaty_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for s in _STRUCTURES:
        conn.execute(
            sa.text(
                "DELETE FROM co_production_structures WHERE structure_slug = :slug"
            ),
            {"slug": s.get("structure_slug", s.get("structure_slug"))},
        )
    for t in _MULTILATERAL_TREATIES:
        conn.execute(
            sa.text(
                "DELETE FROM co_production_treaties WHERE treaty_slug = :slug"
            ),
            {"slug": t["treaty_slug"]},
        )
