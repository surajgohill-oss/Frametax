"""
global_inventory_wave5.py

Wave-5 GlobalProgramEntry records: 13 additional programs — final global discovery
pass covering Switzerland, Slovenia, Ukraine, Russia, Cuba, Iran, Algeria, Belarus,
Moldova, Seychelles, Maldives, Bhutan, and Gabon.

All entries are DISCOVERY tier.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"
_DISC_SUFFIX = (
    "DISCOVERY tier — rates and eligibility rules not confirmed from primary source. "
    "Verify with local film authority before budget finalisation."
)


WAVE5_PROGRAMS: list[GlobalProgramEntry] = [

    # -----------------------------------------------------------------------
    # Western / Central Europe
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CH",
        jurisdiction_name="Switzerland",
        program_name="Swiss Federal Office of Culture (FOC) Film Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Federal Office of Culture (FOC) — Film Promotion",
        source_url="https://www.bak.admin.ch/bak/en/home/film/films-in-switzerland.html",
        effective_from=None,
        notes=(
            "The Swiss Federal Office of Culture (FOC/BAK) administers federal film "
            "support including development, production, and distribution grants. "
            "Cantonal funds (Zurich, Geneva, Vaud, Bern etc.) provide additional "
            "regional support. Switzerland also participates in Eurimages and Creative "
            "Europe MEDIA. Swiss co-productions with Swiss partners may access federal "
            "and cantonal support. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount_chf", "co_production_terms",
                        "cultural_test_details", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SI",
        jurisdiction_name="Slovenia",
        program_name="Slovenian Film Centre (SFC) Cash Rebate and Production Support",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Slovenian Film Centre (SFC — Slovenski filmski center)",
        source_url="https://www.film-center.si",
        effective_from=None,
        notes=(
            "The Slovenian Film Centre (SFC) administers a cash rebate programme for "
            "international productions filming in Slovenia, alongside domestic "
            "production grants. The rebate applies to qualifying Slovenian spend. "
            "Slovenia offers Alpine, Adriatic, and urban locations. Rate and "
            "minimum spend require verification with SFC. " + _DISC_SUFFIX
        ),
        unknown_fields=["base_rate", "min_spend_eur", "qualifying_spend_definition",
                        "processing_timeline", "annual_cap_eur"],
    ),

    # -----------------------------------------------------------------------
    # Eastern Europe
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="UA",
        jurisdiction_name="Ukraine",
        program_name="Ukrainian State Film Agency Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Ukrainian State Film Agency (Держкіно)",
        source_url="https://www.dergkino.gov.ua",
        effective_from=None,
        notes=(
            "Ukraine's State Film Agency (Derzhhkino) administers national film "
            "support including co-production grants and development funding. "
            "The Ukrainian Film Fund (Ukrfilmfund) provides additional production "
            "support. Note: production activity severely constrained by the ongoing "
            "Russian invasion (Feb 2022). Verify operational status of programmes "
            "before budgeting. Ukraine has bilateral co-production agreements with "
            "multiple countries. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount_uah", "programme_status_2025",
                        "co_production_terms", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="RU",
        jurisdiction_name="Russia",
        program_name="Russian Cinema Fund (Fond Kino) Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Cinema Fund of Russia (Фонд кино)",
        source_url="https://www.fond-kino.ru",
        effective_from=None,
        notes=(
            "The Cinema Fund of Russia (Fond Kino) provides state support for domestic "
            "Russian film productions including development, production, and distribution. "
            "International co-productions with Russian partners may access this support. "
            "Note: international sanctions since 2022 severely restrict financial "
            "co-operation with Russian entities. Most Western productions have "
            "suspended Russian co-productions. Verify legal and compliance "
            "implications before any engagement. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount_rub", "sanctions_impact",
                        "co_production_access", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BY",
        jurisdiction_name="Belarus",
        program_name="Belarusfilm National Film Studio Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Belarusfilm National Film Studio",
        source_url="https://www.belarusfilm.by",
        effective_from=None,
        notes=(
            "Belarusfilm National Film Studio provides state production infrastructure "
            "including studio facilities, equipment, and crew for domestic and some "
            "international co-productions. Note: international sanctions since 2020 "
            "and 2022 significantly limit Western co-operation with Belarusian "
            "entities. Verify compliance implications before any engagement. "
            + _DISC_SUFFIX
        ),
        unknown_fields=["studio_hire_rates", "sanctions_impact",
                        "financial_incentive_details", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MD",
        jurisdiction_name="Moldova",
        program_name="National Centre for Cinematography Moldova (NCFM)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="National Centre for Cinematography Moldova (NCFM)",
        source_url="https://cnf.md",
        effective_from=None,
        notes=(
            "Moldova's National Centre for Cinematography (NCFM / Centrul Național al "
            "Cinematografiei) administers state support for domestic and co-production "
            "films. Moldova participates in Creative Europe MEDIA and has bilateral "
            "co-production treaties. Growing interest from European productions seeking "
            "Eastern European locations at lower cost. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount_mdl", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # Latin America
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CU",
        jurisdiction_name="Cuba",
        program_name="ICAIC Cuba Film Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Instituto Cubano del Arte e Industria Cinematográficos (ICAIC)",
        source_url="https://www.icaic.cu",
        effective_from=None,
        notes=(
            "ICAIC (Instituto Cubano del Arte e Industria Cinematográficos) is Cuba's "
            "national film institute, providing state support for Cuban film production "
            "and international co-productions with Cuban partners. Co-productions must "
            "have a Cuban partner organisation. US-Cuba trade restrictions may affect "
            "US productions. Havana and Cuba's unique mid-century cityscape attract "
            "international productions. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount", "us_sanctions_impact",
                        "co_production_terms", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # Middle East / North Africa
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="IR",
        jurisdiction_name="Iran",
        program_name="Farabi Cinema Foundation Film Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Farabi Cinema Foundation — فارابی سینما",
        source_url="https://www.farabicinema.com",
        effective_from=None,
        notes=(
            "Iran's Farabi Cinema Foundation (FCF) is the principal state body for "
            "film production support, distribution, and international co-productions. "
            "Support requires cultural content approval. International sanctions "
            "against Iran severely limit financial co-operation with Western entities. "
            "Iranian cinema has a strong international festival reputation. "
            "Verify legal and compliance implications before engagement. " + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount", "content_requirements",
                        "sanctions_impact", "co_production_access"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DZ",
        jurisdiction_name="Algeria",
        program_name="Centre Algérien pour le Développement du Cinéma (CADC) Film Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Centre Algérien pour le Développement du Cinéma (CADC)",
        source_url="https://www.cadc.dz",
        effective_from=None,
        notes=(
            "Algeria's Centre Algérien pour le Développement du Cinéma (CADC) "
            "administers state support for Algerian film productions and co-productions. "
            "The FDATIC (Fonds de Développement de l'Art, de la Technique et de "
            "l'Industrie Cinématographiques) provides production funding. "
            "Algeria's diverse landscapes attract some international productions. "
            + _DISC_SUFFIX
        ),
        unknown_fields=["grant_amount_dzd", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # Africa
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="GA",
        jurisdiction_name="Gabon",
        program_name="Gabon Ministry of Culture Film Commission Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Gabon Tourism and Ministry of Culture",
        source_url="https://www.agence-gabonaise-tourisme.com",
        effective_from=None,
        notes=(
            "Gabon has a Ministry of Culture and established film commission activities. "
            "Central Africa's biodiversity and rainforest attract nature documentary "
            "productions. The country has hosted international productions and provides "
            "government liaison for filming permits. No formal cash incentive confirmed. "
            + _DISC_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_process", "min_spend"],
    ),

    # -----------------------------------------------------------------------
    # Indian Ocean / Small Island States
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="SC",
        jurisdiction_name="Seychelles",
        program_name="Seychelles Tourism Board Film Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Seychelles Tourism Board — Filming in Seychelles",
        source_url="https://www.seychelles.travel",
        effective_from=None,
        notes=(
            "Seychelles Tourism Board facilitates international film and commercial "
            "productions seeking the archipelago's iconic beaches, coral reefs, and "
            "giant tortoises. Location permits are issued through the Tourism Board. "
            "No formal cash rebate or financial incentive programme confirmed. "
            + _DISC_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_costs", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # South / Southeast Asia
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="MV",
        jurisdiction_name="Maldives",
        program_name="Maldives Marketing and PR Corporation (MMPRC) Film Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Maldives Marketing and PR Corporation (MMPRC) — Visit Maldives",
        source_url="https://www.visitmaldives.com",
        effective_from=None,
        notes=(
            "The Maldives Marketing and Public Relations Corporation (MMPRC) facilitates "
            "international film, commercial, and TV productions in the Maldives. "
            "The Maldives is a popular destination for luxury brand campaigns, "
            "underwater filming, and travel documentaries. Location permits and "
            "resort access are coordinated through MMPRC. No formal cash incentive "
            "confirmed. " + _DISC_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_costs", "resort_access_terms"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BT",
        jurisdiction_name="Bhutan",
        program_name="Bhutan Film Commission / Tourism Council Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Tourism Council of Bhutan — Filming in Bhutan",
        source_url="https://www.tourism.gov.bt",
        effective_from=None,
        notes=(
            "Bhutan facilitates international film and documentary productions through "
            "the Tourism Council of Bhutan. A High-Value, Low-Volume tourism policy "
            "applies — daily visitor tariffs (USD 200/day) apply to production teams. "
            "Bhutan's Buddhist monasteries, Himalayan landscapes, and distinct culture "
            "attract documentary and drama productions. No formal cash incentive. "
            + _DISC_SUFFIX
        ),
        unknown_fields=["production_daily_tariff", "permit_process",
                        "cultural_sensitivity_requirements", "financial_incentive_rate"],
    ),
]
