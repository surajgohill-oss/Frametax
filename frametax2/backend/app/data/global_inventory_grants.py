"""
global_inventory_grants.py

GlobalProgramEntry records for international grants, funds, and cultural
financing vehicles. These are not percentage rebates but rather direct
grants, co-production funds, development funds, and similar discretionary
support mechanisms.

All entries are DISCOVERY tier. Amounts and structures reflect market knowledge
only — not verified against current programme guidelines.

Program types used:
  direct_grant       — discretionary grant awarded to specific projects
  co_production_fund — multi-territory co-production support mechanism
  development_fund   — development/early-stage project funding

Jurisdiction codes:
  EU     — European Union level (Eurimages, Creative Europe)
  NORDIC — Nordic co-production fund (cross-border)
  CA     — Canada (CMF, Telefilm)
  GB     — United Kingdom (BFI)
  FR     — France (CNC)
  AU     — Australia (Screen Australia)
  NL     — Netherlands (Hubert Bals Fund)
  QA     — Qatar (Doha Film Institute)
  US     — United States (Sundance)
  ZA     — South Africa (DAC fund)
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


GRANTS_PROGRAMS: list[GlobalProgramEntry] = [

    GlobalProgramEntry(
        jurisdiction_code="EU",
        jurisdiction_name="European Union / Council of Europe",
        program_name="Eurimages — Council of Europe Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_500_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Eurimages — Council of Europe cultural fund",
        source_url="https://www.coe.int/en/web/eurimages",
        effective_from="1988-01-01",
        notes=(
            "Eurimages supports European co-productions, distribution, and cinema networks. "
            "Up to EUR 1.5M per co-production project. 44 member states. Repayable loan model. "
            "Data gaps: current maximum grant amount, exact cultural test criteria."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="EU",
        jurisdiction_name="European Union",
        program_name="Creative Europe MEDIA Programme",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=2_500_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Creative Europe MEDIA — European Commission",
        source_url="https://creative-europe.eu/media/",
        effective_from="1991-01-01",
        notes=(
            "EU programme supporting European audiovisual sector: development, distribution, promotion. "
            "Selective funding: up to EUR 2.5M for international co-productions. "
            "Requires minimum 3 co-producing countries. Budget 2021-2027: EUR 1.07B. "
            "Data gaps: current call-specific amounts, exact eligibility criteria by strand."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NORDIC",
        jurisdiction_name="Nordic Region (Cross-border Fund)",
        program_name="Nordisk Film & TV Fond",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_400_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Nordisk Film & TV Fond — Nordic co-production fund",
        source_url="https://nordiskfilmogtvfond.com/",
        effective_from="1990-01-01",
        notes=(
            "Nordic Fund supports film and TV co-productions involving at least 2 Nordic countries "
            "(Denmark, Finland, Iceland, Norway, Sweden). Up to SEK 8-15M per project. "
            "Data gaps: confirmed current maximum, SEK/USD rate for cap."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="Canada Media Fund (CMF) — Convergent Stream",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=10_000_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Canada Media Fund — convergent and experimental streams",
        source_url="https://cmf-fmc.ca/funding-programmes/",
        effective_from="2010-01-01",
        notes=(
            "CMF provides CAD$400M+ annually across Convergent and Experimental streams. "
            "Per-project cap up to CAD$10M for major drama. Performance-based envelope model. "
            "Separate from CPTC; stackable with provincial credits. "
            "Data gaps: current per-project maximum, envelope allocation details."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="Telefilm Canada — Canada Feature Film Fund (CFFF)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=5_000_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Telefilm Canada — Canada Feature Film Fund",
        source_url="https://telefilm.ca/en/financing/",
        effective_from="2001-01-01",
        notes=(
            "Telefilm provides equity investment and advances for Canadian feature films. "
            "Up to CAD$5M per project (performance envelope producers). Repayable investment. "
            "Separate development fund also available. Cultural Canadian content required. "
            "Data gaps: current per-project maximum, exact cultural certification criteria."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="BFI Film Fund — Production Funding",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=2_000_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="BFI Film Fund — production award",
        source_url="https://www.bfi.org.uk/get-bfi-funding/bfi-film-fund",
        effective_from="2000-01-01",
        notes=(
            "BFI Film Fund supports ambitious British films. Up to £1.5M per project. "
            "Lottery-funded. Cultural British content test. Not stackable with commercial investment "
            "beyond certain limits. Stacks with UK AVEC rebate. "
            "Data gaps: current per-project maximum, eligibility details."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="CNC France — Avances sur Recettes (Cinema Production Aid)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_500_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="CNC — Avances sur recettes et aides à la production",
        source_url="https://www.cnc.fr/professionnels/aides-et-financements/cinema/production",
        effective_from="1960-01-01",
        notes=(
            "CNC's Avances sur recettes provides selective production grants up to ~EUR 1.2M. "
            "Repayable advance on future receipts. French cultural content required. "
            "Stacks with French TRIP rebate. CNC also funds distribution, exhibition, and VFX. "
            "Data gaps: current maximum, exact eligibility for foreign co-productions."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Screen Australia — Production Funding",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=3_000_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Screen Australia — production funding",
        source_url="https://www.screenaustralia.gov.au/funding-and-support/feature-films/production",
        effective_from="2008-01-01",
        notes=(
            "Screen Australia provides equity investment in Australian feature films and TV. "
            "Up to AUD $3M+ per project for principal production. Repayable equity. "
            "Stacks with federal Location Offset rebate. Cultural Australian content test. "
            "Data gaps: current per-project maximum, exact stackability rules."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NL",
        jurisdiction_name="Netherlands",
        program_name="Hubert Bals Fund (IFFR) — Development and Production Fund",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=150_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="International Film Festival Rotterdam — Hubert Bals Fund",
        source_url="https://iffr.com/en/hubert-bals-fund",
        effective_from="1988-01-01",
        notes=(
            "Hubert Bals Fund supports filmmakers from underrepresented countries and regions. "
            "Up to EUR 10-30K (development) / EUR 50-100K (production). Selective grant. "
            "Based at IFFR Rotterdam. Focuses on Global South directors. "
            "Data gaps: current maximum amounts by category, eligibility details."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="QA",
        jurisdiction_name="Qatar",
        program_name="Doha Film Institute — Grants for Filmmakers",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=300_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Doha Film Institute — grants programme",
        source_url="https://dohafilminstitute.com/financing/grants",
        effective_from="2011-01-01",
        notes=(
            "Doha Film Institute grants up to QAR 1.5M (~USD $400K) per project. "
            "Two annual cycles. Focuses on Arab/international co-productions. "
            "Data gaps: current maximum, eligibility criteria for non-Arab projects."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US",
        jurisdiction_name="United States",
        program_name="Sundance Institute — Documentary Fund",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=300_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Sundance Institute — Documentary Fund",
        source_url="https://www.sundance.org/programs/documentary-fund",
        effective_from="1996-01-01",
        notes=(
            "Sundance Institute Documentary Fund provides grants up to USD $250-300K "
            "for feature documentaries in development and production. Competitive selective award. "
            "Also operates Feature Film Program and International awards. "
            "Data gaps: current maximum grant by category, current eligibility."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ZA",
        jurisdiction_name="South Africa",
        program_name="Department of Arts and Culture (DAC) / NFVF Development Fund",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=250_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="NFVF South Africa — development and production funding",
        source_url="https://www.nfvf.co.za/funding/",
        effective_from="2000-01-01",
        notes=(
            "NFVF provides development and production grants to South African productions. "
            "Up to ZAR 3-4M per project (~USD $200-250K at current rates). Cultural test required. "
            "Stacks with NFVF Foreign Film rebate. "
            "Data gaps: current maximum, exact eligibility, stackability rules."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),
]
