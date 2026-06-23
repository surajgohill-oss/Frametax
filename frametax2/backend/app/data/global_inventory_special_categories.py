"""
global_inventory_special_categories.py — Phase A-D final sweep.

New program categories:
  - VFX / post-production incentives
  - Animation incentives
  - Post-production-only funds
  - Streamer production support obligations
  - Workforce and training subsidies
  - Export promotion funds
  - Tourism board / destination marketing production support
  - Airline / transport production support
  - National cultural ministry production grants (remaining)
  - Special regional funds

All DISCOVERY unless primary source data confirms otherwise.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

SPECIAL_CATEGORY_PROGRAMS: list[GlobalProgramEntry] = [

    # =========================================================================
    # VFX / POST-PRODUCTION / ANIMATION INCENTIVES
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Post, Digital and Visual Effects (PDV) Offset",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="Australia's PDV Offset — Screen Australia",
        source_url=None,
        effective_from="2001-01-01",
        notes=(
            "30% rebate on qualifying Australian post, digital, and VFX expenditure. "
            "Minimum A$500k qualifying PDV expenditure. Available to foreign productions "
            "for Australian PDV work regardless of where principal photography occurred. "
            "Government financial assistance — reduces QAPE for Location/Producer Offsets if combined."
        ),
        unknown_fields=["atl_inclusion", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NZ",
        jurisdiction_name="New Zealand",
        program_name="New Zealand Screen Production Grant — International Post/VFX",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="New Zealand Film Commission — Post/Digital/VFX",
        source_url=None,
        effective_from=None,
        notes=(
            "New Zealand PDV/post rebate: 20% base + up to 5% cultural uplift on qualifying NZ "
            "post-production and VFX expenditure. Available to foreign productions spending in NZ. "
            "UNKNOWN: current annual cap, minimum qualifying spend threshold in USD."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "atl_inclusion", "min_spend_usd"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-ON",
        jurisdiction_name="Ontario, Canada",
        program_name="Ontario Computer Animation and Special Effects Tax Credit (OCASE)",
        program_type="tax_credit",
        base_rate=0.18,
        max_rate=0.18,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="Ontario OCASE — Ontario Creates",
        source_url=None,
        effective_from=None,
        notes=(
            "OCASE: 18% refundable tax credit on qualifying Ontario computer animation and "
            "special effects labour expenditure. Applies to animation and VFX work performed in Ontario. "
            "Can be combined with OFTTC or OPSTC depending on production type. "
            "Government assistance — reduces qualifying labour basis for CPTC calculation."
        ),
        unknown_fields=["annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-BC",
        jurisdiction_name="British Columbia, Canada",
        program_name="BC Interactive Digital Media Tax Credit (IDMTC)",
        program_type="tax_credit",
        base_rate=0.175,
        max_rate=0.175,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="BC IDMTC — BC Ministry of Finance",
        source_url=None,
        effective_from=None,
        notes=(
            "BC IDMTC: 17.5% refundable credit on qualifying BC labour for interactive digital media. "
            "Covers VFX, animation, and interactive content with defined qualifying criteria. "
            "Generally independent of BC PSTC (different eligibility track). "
            "May be government assistance if combined with other federal credits."
        ),
        unknown_fields=["annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IS",
        jurisdiction_name="Iceland",
        program_name="Iceland Post-production and VFX Incentive",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Icelandic Film Centre — Production Incentive (Post component)",
        source_url=None,
        effective_from=None,
        notes=(
            "Iceland's 25% production incentive applies to post-production and VFX work performed in Iceland, "
            "not only on-location principal photography. UNKNOWN: whether separate post-only track exists vs. "
            "general incentive scheme; minimum qualifying post spend in Iceland."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "atl_inclusion", "min_spend_usd"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SG",
        jurisdiction_name="Singapore",
        program_name="IMDA — Digital Media Content Programme (Animation/VFX)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="IMDA — Info-communications Media Development Authority",
        source_url=None,
        effective_from=None,
        notes=(
            "IMDA (Infocomm Media Development Authority) provides grants for digital content "
            "including animation and VFX productions with Singapore-based studios. "
            "Covers digital co-productions, animation series, and VFX facility development. "
            "UNKNOWN: current grant amounts, eligibility criteria, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KR",
        jurisdiction_name="South Korea",
        program_name="KOCCA — Korea Creative Content Agency Animation and VFX Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="KOCCA — Korea Creative Content Agency",
        source_url=None,
        effective_from=None,
        notes=(
            "KOCCA provides selective grants for Korean animation and VFX productions, including "
            "international co-productions with Korean studios. Separate from KOFIC film incentive. "
            "Also supports Korean game/digital content exports. "
            "UNKNOWN: current maximum, eligibility criteria, co-production requirements."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="CNC — Crédit d'Impôt Animation et Jeux Vidéo",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="CNC — Crédit d'impôt pour les dépenses de production d'œuvres d'animation",
        source_url=None,
        effective_from=None,
        notes=(
            "French animation tax credit: 25-30% of qualifying French animation production expenditure. "
            "Applies to qualifying French animation series, films, and video game content. "
            "Separate from the domestic tax crédit cinéma and TRIP. "
            "Minimum qualifying spend required. Government support — interactions with CNC avance may apply."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "min_spend_usd"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="JP",
        jurisdiction_name="Japan",
        program_name="VIPO — Visual Industry Promotion Organization Animation Support",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=220_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="VIPO — Visual Industry Promotion Organization",
        source_url=None,
        effective_from=None,
        notes=(
            "VIPO provides support for international co-productions involving Japanese animation "
            "and content studios. Separate from Japan's location incentive programs. "
            "UNKNOWN: current grant amounts, eligibility criteria, co-production requirements."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    # =========================================================================
    # EXPORT PROMOTION FUNDS
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="BFI International — Export Development and Distribution Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=220_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="BFI International — British Film Institute",
        source_url=None,
        effective_from=None,
        notes=(
            "BFI International provides grants for international sales, distribution, and market "
            "participation for UK films. Separate from BFI Film Fund production financing. "
            "UNKNOWN: current maximum per project, annual budget, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="UniFrance — International Distribution and Promotion Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=110_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="UniFrance — French cinema international promotion",
        source_url=None,
        effective_from=None,
        notes=(
            "UniFrance distributes CNC-funded grants for international promotion, market attendance, "
            "and distribution of French films. Separate from production tax credits. "
            "UNKNOWN: per-project grant amounts, current annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE",
        jurisdiction_name="Germany",
        program_name="German Films International — Export and Market Promotion",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=110_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="German Films — Germany's international sales export agency",
        source_url=None,
        effective_from=None,
        notes=(
            "German Films (FFA-funded export service organisation) provides market attendance "
            "and international promotion support for German films. "
            "UNKNOWN: per-project grant amounts, current annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT",
        jurisdiction_name="Italy",
        program_name="ANICA / MiC — Italian Film International Distribution Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=220_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="ANICA — Associazione Nazionale Industrie Cinematografiche",
        source_url=None,
        effective_from=None,
        notes=(
            "MiC administers selective distribution grants for international release of Italian films. "
            "ANICA coordinates industry support for export. "
            "UNKNOWN: current per-project maximum, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="Telefilm Canada — Export Development Program",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Telefilm Canada — Export Development",
        source_url=None,
        effective_from=None,
        notes=(
            "Telefilm Canada Export Development Program provides funding for Canadian producers to attend "
            "international markets and pursue international distribution for Canadian content. "
            "Government assistance under ITA §125.4 — reduces qualifying labour basis for CPTC. "
            "UNKNOWN: current per-project maximum, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KR",
        jurisdiction_name="South Korea",
        program_name="KOFIC — International Co-production and Export Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=275_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="KOFIC — Korean Film Council International",
        source_url=None,
        effective_from=None,
        notes=(
            "KOFIC international programmes support Korean film exports, international co-productions, "
            "and Korean representation at major markets (EFM, Cannes, AFM, TIFF). "
            "Separate from KOFIC Location Incentive. "
            "UNKNOWN: current per-project maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    # =========================================================================
    # WORKFORCE / TRAINING SUBSIDIES
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="ScreenSkills — Production Training Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="ScreenSkills — UK's skills body for the screen industries",
        source_url=None,
        effective_from=None,
        notes=(
            "ScreenSkills manages the High-end TV (HETV) and Film Skills Fund, funded by a training "
            "contribution from qualifying productions (0.5% of HETV budget, 1% of film budget). "
            "Contributes to industry training, apprenticeships, and skills development. "
            "Not a direct cash incentive — reduces net AVEC effective rate marginally. "
            "UNKNOWN: current training levy rate, annual fund size."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Screen Australia — Talent and Business Development Programs",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=165_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Screen Australia — Talent programs",
        source_url=None,
        effective_from=None,
        notes=(
            "Screen Australia talent programs provide development grants for Australian screen talent: "
            "development funding, co-production market support, and international attachments. "
            "Separate from Screen Australia equity production investment. "
            "Government financial assistance — may reduce QAPE if combined with offsets. "
            "UNKNOWN: per-project amounts, annual budget, specific eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IE",
        jurisdiction_name="Ireland",
        program_name="Screen Ireland — Development and Skills Programme",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=275_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Screen Ireland — Development funding",
        source_url=None,
        effective_from=None,
        notes=(
            "Screen Ireland (formerly Irish Film Board) provides development funding for Irish projects, "
            "skills training, and industry development. Separate from Section 481 production finance. "
            "Not government assistance for Section 481 qualifying expenditure (separate fund). "
            "UNKNOWN: per-project amounts, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    # =========================================================================
    # STREAMER PRODUCTION SUPPORT OBLIGATIONS
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="EU",
        jurisdiction_name="European Union",
        program_name="EU AVMS Directive — Local Content Investment Obligations (Streamers)",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="EU Audiovisual Media Services Directive (AVMSD) 2018/1808",
        source_url=None,
        effective_from="2018-01-01",
        notes=(
            "EU AVMSD requires streamers (Netflix, Amazon, Disney+, Apple TV+) operating in EU member "
            "states to invest a percentage of revenues in European content or contribute to national funds. "
            "Implemented differently per country: France (25% of revenues), Germany (2.5%), "
            "Italy (17-20%), Spain (5%), Sweden (TBD). "
            "These obligations trigger real production spend but are not direct subsidies to producers. "
            "UNKNOWN: per-jurisdiction investment rates, exact compliance mechanisms per country."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="Chronologie des médias — SVOD Investment Obligation (France)",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="PARSED",
        source_title="CSA/ARCOM — Agreements with Netflix, Amazon, Disney+, Apple TV+",
        source_url=None,
        effective_from="2022-01-01",
        notes=(
            "French SVOD providers (Netflix, Amazon Prime Video, Disney+, Apple TV+) must invest "
            "20-25% of French revenues in French audiovisual and cinematographic works. "
            "Netflix agreement 2022: invest approximately €200M/year in French content. "
            "These investments qualify as co-financing and do not reduce CNC tax credit qualifying spend. "
            "UNKNOWN: exact per-platform commitment amounts, exact implementation details."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Australian Content Standard — Streaming Service Investment Obligations",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="ACMA — Australian Content Standard for Streaming Services",
        source_url=None,
        effective_from="2023-01-01",
        notes=(
            "Australia's reformed Content Standard (Broadcasting Services Act) requires streaming "
            "services above revenue thresholds to invest in Australian content. "
            "Specific investment obligations TBD under final implementation. "
            "Not government assistance for offset calculations — investment is commercial. "
            "UNKNOWN: exact investment percentage, revenue threshold, implementation timeline."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="CRTC — Online Streaming Act (Bill C-11) Local Content Obligations",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="CRTC — Online Streaming Act (Broadcasting Act reform)",
        source_url=None,
        effective_from="2023-01-01",
        notes=(
            "Canada's Online Streaming Act (Bill C-11, 2023) requires online streaming services "
            "to contribute to Canadian content creation and discovery. "
            "CRTC implementing regulations require contributions to CMF and other Canadian funds. "
            "Not government assistance for CPTC/OFTTC calculations. "
            "UNKNOWN: exact streaming service contribution rates, implementation details."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    # =========================================================================
    # TOURISM BOARD / DESTINATION MARKETING PRODUCTION SUPPORT
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Tourism Australia — Film and Content Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Tourism Australia — Filming in Australia",
        source_url=None,
        effective_from=None,
        notes=(
            "Tourism Australia provides non-financial production facilitation and co-marketing "
            "support for international productions filming in Australia. May include location "
            "assistance, co-promotion value, and access to iconic locations at reduced or no cost. "
            "UNKNOWN: financial value of support, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NZ",
        jurisdiction_name="New Zealand",
        program_name="Tourism New Zealand — Screen Tourism Programme",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Tourism New Zealand — Screen Tourism",
        source_url=None,
        effective_from=None,
        notes=(
            "Tourism New Zealand's screen tourism programme co-ordinates support for international "
            "productions filming in New Zealand to maximise tourism impact. Primarily non-financial "
            "co-marketing and facilitation support. Separate from NZ Screen Production Rebate. "
            "UNKNOWN: financial value of support, per-production eligibility."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IE",
        jurisdiction_name="Ireland",
        program_name="Tourism Ireland / Fáilte Ireland — Film Tourism Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Tourism Ireland / Fáilte Ireland — Film locations",
        source_url=None,
        effective_from=None,
        notes=(
            "Tourism Ireland and Fáilte Ireland provide non-financial production support and "
            "co-marketing for international productions filming in Ireland. Separate from Section 481. "
            "UNKNOWN: any financial component, per-production eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="JO",
        jurisdiction_name="Jordan",
        program_name="Royal Film Commission Jordan — Tourism and Hospitality Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Royal Film Commission Jordan — Production Support",
        source_url=None,
        effective_from=None,
        notes=(
            "RFC Jordan provides hotel and accommodation discounts, airport facilitation, logistics "
            "coordination, and customs duty exemptions for foreign productions filming in Jordan. "
            "These are non-financial or in-kind support services. Separate from RFC Jordan cash rebate. "
            "UNKNOWN: financial value of discounts, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MA",
        jurisdiction_name="Morocco",
        program_name="Centre Cinématographique Marocain (CCM) — Tourism Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Centre Cinématographique Marocain (CCM)",
        source_url=None,
        effective_from=None,
        notes=(
            "CCM provides permits, location facilitation, customs exemptions, and military/security "
            "coordination for international productions in Morocco. Separate from CCM rebate programme "
            "and CCM development grants. Not a financial incentive. "
            "UNKNOWN: any financial component, per-production eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    # =========================================================================
    # AIRLINE / TRANSPORT PRODUCTION SUPPORT
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="AE",
        jurisdiction_name="United Arab Emirates",
        program_name="Emirates Airline — Film Production Partnerships and In-Kind Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Emirates Group — Media partnerships",
        source_url=None,
        effective_from=None,
        notes=(
            "Emirates Airline and Emirates Group provide in-kind and commercial production support "
            "including reduced airfare rates, cargo handling, and logistical assistance for "
            "international productions with Dubai or UAE connections. "
            "Non-financial or below-market-value commercial arrangements. "
            "UNKNOWN: financial value, eligibility criteria, formal programme details."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NZ",
        jurisdiction_name="New Zealand",
        program_name="Air New Zealand — Screen Production Partnership Programme",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Air New Zealand — Screen Production",
        source_url=None,
        effective_from=None,
        notes=(
            "Air New Zealand historically provided transportation partnerships and in-kind support "
            "for major international productions filming in New Zealand (e.g., Lord of the Rings). "
            "Separate from NZSPG rebate. Commercial partnership at below-market rates. "
            "UNKNOWN: current programme status, financial value, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    # =========================================================================
    # NATIONAL CULTURAL MINISTRY GRANTS (additional)
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="GR",
        jurisdiction_name="Greece",
        program_name="Greek Film Centre (GFC) — Selective Production Grants",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Hellenic Film Commission — Greek Film Centre",
        source_url=None,
        effective_from=None,
        notes=(
            "Greek Film Centre provides selective production grants for Greek films and "
            "international co-productions with Greek participation. Eurimages member. "
            "Separate from Greece Cash Rebate for foreign productions. "
            "UNKNOWN: current maximum per-project, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SA-KSA",
        jurisdiction_name="Saudi Arabia",
        program_name="Saudi Film Commission — Production Grants and Selective Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Saudi Film Commission — Ministry of Culture Saudi Arabia",
        source_url=None,
        effective_from="2020-01-01",
        notes=(
            "Saudi Film Commission provides selective production support for Saudi content "
            "and international co-productions with Saudi studios. "
            "Separate from Saudi Film Commission's production rebate for foreign productions. "
            "Vision 2030 cultural program driving rapid expansion of Saudi film industry. "
            "UNKNOWN: current grant amounts, eligibility criteria, annual budget."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TR",
        jurisdiction_name="Turkey",
        program_name="Ministry of Culture and Tourism (KÜLTÜR) — Film Production Grants",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=220_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="KÜLTÜR — Turkish Ministry of Culture Cinema General Directorate",
        source_url=None,
        effective_from=None,
        notes=(
            "Turkey's Cinema General Directorate provides selective grants for Turkish film production "
            "and international co-productions. Separate from Turkey's production support cash rebate. "
            "UNKNOWN: current maximum per-project, annual budget, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    # =========================================================================
    # ADDITIONAL SPECIAL REGIONAL FUNDS
    # =========================================================================

    GlobalProgramEntry(
        jurisdiction_code="SE-SK",
        jurisdiction_name="Skåne, Sweden",
        program_name="Film i Skåne — Regional Co-production Fund (Scania)",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Film i Skåne — Scania region co-production fund",
        source_url=None,
        effective_from=None,
        notes=(
            "Film i Skåne (Scania region, southern Sweden) co-produces Nordic film and TV drama "
            "with Malmö/Lund area qualifying spend. Works alongside Film i Väst and SFI. "
            "Non-repayable grants and recoupable advances. Minimum Skåne regional spend required. "
            "UNKNOWN: current maximum, exact grant/advance split."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SE-AB",
        jurisdiction_name="Stockholm, Sweden",
        program_name="Filmregion Stockholm-Mälardalen — Regional Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=275_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Filmregion Stockholm-Mälardalen",
        source_url=None,
        effective_from=None,
        notes=(
            "Filmregion Stockholm-Mälardalen supports film and TV productions in the Stockholm "
            "metropolitan region. Works alongside Film i Väst, Film i Skåne, and SFI. "
            "UNKNOWN: current maximum, grant vs. advance split, minimum regional spend."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NO-ROG",
        jurisdiction_name="Rogaland/Vestland, Norway",
        program_name="Vestnorsk Filmsenter — Western Norway Regional Film Centre",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=220_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Vestnorsk Filmsenter",
        source_url=None,
        effective_from=None,
        notes=(
            "Vestnorsk Filmsenter (Bergen/Stavanger region) provides production grants "
            "for Norwegian film and TV with Western Norway qualifying spend. "
            "Works alongside NFI and NRK co-production. "
            "UNKNOWN: current maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NO-TRO",
        jurisdiction_name="Tromsø, Norway",
        program_name="Nord Norsk Filmsenter — Northern Norway Regional Film Centre",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=165_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Nord Norsk Filmsenter",
        source_url=None,
        effective_from=None,
        notes=(
            "Nord Norsk Filmsenter (Tromsø/Arctic Norway) supports film and TV productions "
            "with Northern Norway content or production spend. "
            "UNKNOWN: current maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DK-CPH",
        jurisdiction_name="Copenhagen, Denmark",
        program_name="Copenhagen Film Fund — Regional Co-production Support",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Copenhagen Film Fund",
        source_url=None,
        effective_from=None,
        notes=(
            "Copenhagen Film Fund supports film and TV productions in the Copenhagen "
            "metropolitan area. Works alongside DFI selective support and Eurimages. "
            "Non-repayable grants with Copenhagen/Zealand qualifying spend requirement. "
            "UNKNOWN: current maximum, annual budget, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-TAS",
        jurisdiction_name="Tasmania, Australia",
        program_name="Screen Tasmania — Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=275_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Screen Tasmania",
        source_url=None,
        effective_from=None,
        notes=(
            "Screen Tasmania provides production support grants for Tasmania-based productions "
            "and international productions spending in Tasmania. "
            "Government financial assistance — may reduce QAPE if combined with AU offsets. "
            "UNKNOWN: current maximum, eligibility criteria, qualifying spend threshold."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-NT",
        jurisdiction_name="Northern Territory, Australia",
        program_name="Territory Screen — Northern Territory Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=275_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Territory Screen (NT Screen)",
        source_url=None,
        effective_from=None,
        notes=(
            "Territory Screen (NT) provides production support grants for Northern Territory "
            "screen projects and international productions spending in the NT. "
            "Government financial assistance — may reduce QAPE if combined with AU offsets. "
            "UNKNOWN: current maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB-LON",
        jurisdiction_name="London, England",
        program_name="Film London — Production Finance Market and Support",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=110_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Film London",
        source_url=None,
        effective_from=None,
        notes=(
            "Film London provides production support for London-based productions including "
            "micro-budget production support (up to £100k) and industry market events. "
            "Not government assistance for AVEC. Small fund relative to national scale. "
            "UNKNOWN: current maximum, annual budget, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-PE",
        jurisdiction_name="Prince Edward Island, Canada",
        program_name="Film PEI — Prince Edward Island Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=110_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Film PEI",
        source_url=None,
        effective_from=None,
        notes=(
            "Film PEI provides production support grants for productions filming in Prince Edward Island. "
            "Government assistance under ITA §125.4 — reduces qualifying labour for CPTC if applicable. "
            "Small fund. Combines with federal CPTC and federal development programs. "
            "UNKNOWN: current maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-MB",
        jurisdiction_name="Manitoba, Canada",
        program_name="Manitoba Film & Music — Production Support Grants",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Manitoba Film & Music",
        source_url=None,
        effective_from=None,
        notes=(
            "Manitoba Film & Music provides production support for productions filming in Manitoba. "
            "Manitoba also offers the Manitoba Film and Video Production Tax Credit (MFVPTC: 45-65% of labour). "
            "Grants are government assistance reducing CPTC qualifying labour. "
            "UNKNOWN: current grant maximum, eligibility criteria."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

]
