"""
global_inventory_wave4.py

Wave-4 GlobalProgramEntry records: 21 additional programs covering
countries identified in the Phase 2 region completion pass.

All entries are DISCOVERY tier. Source URLs point to official government
ministries, film commissions, or national film agencies.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"
_DISC_NOTES_SUFFIX = (
    "DISCOVERY tier — rates and detailed eligibility rules not confirmed from primary source. "
    "Verify with local film authority before budget finalisation."
)


WAVE4_PROGRAMS: list[GlobalProgramEntry] = [

    # -----------------------------------------------------------------------
    # Central Asia / Caucasus
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="AZ",
        jurisdiction_name="Azerbaijan",
        program_name="Azerbaijan Film Fund Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Azerbaijan Film Fund (Azərbaycankino)",
        source_url="https://www.azfilm.az",
        effective_from=None,
        notes=(
            "The Azerbaijan Film Fund (Azərbaycankino) provides state support for "
            "domestic and international co-productions. Support includes grants for "
            "script development and production. Foreign productions must partner with "
            "an Azerbaijani co-producer. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["base_rate", "max_grant_usd", "co_production_required",
                        "cultural_test_details", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="UZ",
        jurisdiction_name="Uzbekistan",
        program_name="Uzbekkino National Film Support Program",
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
        source_title="Uzbekkino National Agency for Cinema",
        source_url="https://www.uzbekkino.uz",
        effective_from=None,
        notes=(
            "Uzbekkino (National Agency for Cinema) administers state support for "
            "film production in Uzbekistan. International co-productions may access "
            "studio facilities, locations, and crew through Uzbekkino. "
            "Uzbekfilm Studios provides infrastructure for foreign productions. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # Middle East
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="OM",
        jurisdiction_name="Oman",
        program_name="Oman Film Commission Production Support",
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
        source_title="Oman Film Commission",
        source_url="https://www.omanfilmcommission.com",
        effective_from=None,
        notes=(
            "Oman Film Commission facilitates international film and TV productions "
            "in Oman, providing location permits, crew connections, and government "
            "liaison services. Some productions receive in-kind government support "
            "for infrastructure and military/police assets. No confirmed cash rebate "
            "or formal incentive rate. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "cash_rebate_pct",
                        "min_spend", "eligible_spend_categories"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="LB",
        jurisdiction_name="Lebanon",
        program_name="Centre du Cinéma Libanais (CCL) Production Support",
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
        source_title="Centre du Cinéma Libanais — Ministère de la Culture",
        source_url="https://www.culture.gov.lb",
        effective_from=None,
        notes=(
            "Lebanon's Centre du Cinéma Libanais (CCL) supports Lebanese film "
            "productions and international co-productions with Lebanese partners. "
            "Support is primarily for development and production grants. Economic "
            "crisis since 2019 has severely constrained programme funding. "
            "Verify current programme status with Ministry of Culture before budget finalisation. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["grant_amount_usd", "programme_status", "co_production_required",
                        "min_spend", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # South America
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="VE",
        jurisdiction_name="Venezuela",
        program_name="CNAC Venezuela Film Production Fund",
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
        source_title="Centro Nacional Autónomo de Cinematografía (CNAC)",
        source_url="https://www.cnac.gob.ve",
        effective_from=None,
        notes=(
            "CNAC (Centro Nacional Autónomo de Cinematografía) administers Venezuela's "
            "national film fund. Support available for national and international "
            "co-productions with Venezuelan partners. Economic and political constraints "
            "have significantly limited fund availability since 2015. "
            "Verify current programme status before budgeting. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["fund_amount_usd", "programme_status", "min_spend",
                        "co_production_terms", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GY",
        jurisdiction_name="Guyana",
        program_name="Guyana Tourism Authority Film Production Support",
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
        source_title="Guyana Tourism Authority — Filming in Guyana",
        source_url="https://www.guyanatourism.com",
        effective_from=None,
        notes=(
            "Guyana Tourism Authority (GTA) facilitates international film and TV "
            "productions seeking to film in Guyana. Support includes location scouting, "
            "permit assistance, and crew referrals. No confirmed cash incentive or "
            "formal rebate programme. Growing interest from productions following "
            "oil discovery economic growth. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_incentive_programme",
                        "min_spend", "eligible_categories"],
    ),

    # -----------------------------------------------------------------------
    # Central America
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="GT",
        jurisdiction_name="Guatemala",
        program_name="Guatemala Film Commission (INGUAT) Production Facilitation",
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
        source_title="Instituto Guatemalteco de Turismo (INGUAT)",
        source_url="https://www.inguat.net",
        effective_from=None,
        notes=(
            "Instituto Guatemalteco de Turismo (INGUAT) acts as the de facto film "
            "commission for Guatemala. Provides location permits, government liaison "
            "services, and crew referrals. No formal cash incentive or rebate "
            "programme confirmed. Rich Mayan heritage and diverse landscapes attract "
            "international productions. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_costs", "eligible_locations"],
    ),

    # -----------------------------------------------------------------------
    # Africa
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="NA",
        jurisdiction_name="Namibia",
        program_name="Namibia Film Commission Production Incentive",
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
        source_title="Namibia Film Commission",
        source_url="https://www.namibiafilmcommission.com",
        effective_from=None,
        notes=(
            "Namibia Film Commission (NFC) administers production support and "
            "financial incentives for international productions. A cash rebate "
            "on qualifying Namibian spend has been reported; exact rate requires "
            "verification with NFC. Namibia hosts large international productions "
            "(Mad Max: Fury Road, etc.) for its unique desert landscapes. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["base_rate", "min_spend_usd", "qualifying_spend_definition",
                        "processing_timeline", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BW",
        jurisdiction_name="Botswana",
        program_name="Botswana Film Commission Production Support",
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
        source_title="Botswana Film Commission",
        source_url="https://www.botswanafilm.co.bw",
        effective_from=None,
        notes=(
            "Botswana Film Commission (BFC) facilitates film and TV productions "
            "in Botswana. Provides location permits, government liaison, and crew "
            "assistance. No formal cash rebate rate confirmed. Botswana is a popular "
            "filming destination for wildlife and conservation documentaries. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_rebate_programme",
                        "min_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ET",
        jurisdiction_name="Ethiopia",
        program_name="Ethiopian Film Commission Production Support",
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
        source_title="Ethiopian Film Commission — Ministry of Culture and Tourism",
        source_url="https://www.moct.gov.et",
        effective_from=None,
        notes=(
            "Ethiopia has a national film commission operating under the Ministry of "
            "Culture and Tourism. Provides location facilitation and permit support "
            "for international productions. No formal cash incentive programme confirmed. "
            "Ethiopia's diverse landscapes and ancient heritage attract documentary "
            "and drama productions. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "min_spend", "permit_process"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CI",
        jurisdiction_name="Côte d'Ivoire",
        program_name="Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support",
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
        source_title="Centre National de Cinéma de Côte d'Ivoire (CNCI)",
        source_url="https://www.culture.gouv.ci",
        effective_from=None,
        notes=(
            "Côte d'Ivoire has an active film industry centred in Abidjan. The Centre "
            "National de Cinéma de Côte d'Ivoire (CNCI) provides support for domestic "
            "and co-production films. International co-productions with Ivorian partners "
            "may access state support. No formal foreign rebate programme confirmed. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["grant_amount", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CM",
        jurisdiction_name="Cameroon",
        program_name="Cameroon Centre National de la Cinématographie (CNC-Cameroon)",
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
        source_title="Ministère des Arts et de la Culture — Cameroon",
        source_url="https://www.minac.cm",
        effective_from=None,
        notes=(
            "Cameroon has a dedicated directorate for cinema under the Ministry of "
            "Arts and Culture (MINAC). State support is available for Cameroonian "
            "productions and international co-productions. Nollywood and French-language "
            "African productions frequently film in Cameroon. No formal foreign "
            "production rebate confirmed. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["grant_amount", "co_production_terms",
                        "min_local_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AO",
        jurisdiction_name="Angola",
        program_name="Angola Instituto do Cinema e Audiovisual (ICA) Production Support",
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
        source_title="Instituto do Cinema e Audiovisual de Angola (ICA)",
        source_url="https://www.mincult.gov.ao",
        effective_from=None,
        notes=(
            "Angola's Instituto do Cinema e Audiovisual (ICA), under the Ministry of "
            "Culture, administers support for domestic and international film productions. "
            "Angola is a Portuguese-speaking market with growing production infrastructure. "
            "Co-productions with Angolan entities may access state support. "
            "No formal foreign rebate programme confirmed. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["grant_amount", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="UG",
        jurisdiction_name="Uganda",
        program_name="Uganda Film Commission Production Support",
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
        source_title="Uganda Film Commission",
        source_url="https://www.ugandafilmcommission.org",
        effective_from=None,
        notes=(
            "Uganda Film Commission facilitates international film and TV productions. "
            "Provides location permits, crew connections, and government liaison. "
            "Uganda offers diverse landscapes from mountain gorilla habitats to Lake "
            "Victoria. No formal cash rebate or production incentive confirmed. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "permit_costs",
                        "min_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MZ",
        jurisdiction_name="Mozambique",
        program_name="Mozambique Instituto do Cinema Film Support",
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
        source_title="Instituto do Cinema de Moçambique — Ministério da Cultura",
        source_url="https://www.cultura.gov.mz",
        effective_from=None,
        notes=(
            "Mozambique has a national cinema institute operating under the Ministry "
            "of Culture. Provides support for domestic productions and location "
            "facilitation for international productions. Portuguese-speaking market "
            "with coastal and savannah locations. No formal cash rebate confirmed. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "min_spend", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ZM",
        jurisdiction_name="Zambia",
        program_name="Zambia Film Commission Production Support",
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
        source_title="Zambia Film Commission",
        source_url="https://www.zfc.gov.zm",
        effective_from=None,
        notes=(
            "Zambia Film Commission regulates and facilitates film production in Zambia. "
            "Provides location permits and production liaison services. Zambia's wildlife "
            "and Victoria Falls attract nature documentary productions. "
            "No formal cash rebate or incentive programme confirmed. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_costs", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ZW",
        jurisdiction_name="Zimbabwe",
        program_name="Zimbabwe Film and Broadcasting Authority Production Support",
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
        source_title="Zimbabwe Film and Broadcasting Authority (ZBFTA)",
        source_url="https://www.zbfta.co.zw",
        effective_from=None,
        notes=(
            "Zimbabwe Broadcasting and Film Training Authority (ZBFTA) regulates "
            "and facilitates film production. Zimbabwe Film Commission also operates. "
            "Victoria Falls, Great Zimbabwe ruins, and wildlife are key filming "
            "attractions. No formal cash rebate or financial incentive confirmed. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_costs", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # East Asia
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CN",
        jurisdiction_name="China",
        program_name="China Film Administration Domestic Co-production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="China Film Administration (National Radio and Television Administration)",
        source_url="https://www.nrta.gov.cn",
        effective_from=None,
        notes=(
            "China Film Administration (under NRTA) administers co-production agreements "
            "with foreign film bodies. Official co-productions gain access to the "
            "Chinese domestic market and may benefit from domestic financing mechanisms. "
            "Access is tightly controlled; projects must pass cultural and content review. "
            "Not a cash rebate — market access is the primary incentive. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["co_production_financial_terms", "content_requirements",
                        "approval_timeline", "market_access_terms"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MN",
        jurisdiction_name="Mongolia",
        program_name="Mongolian Film Commission Production Support",
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
        source_title="Mongolian National Broadcaster / Ministry of Culture",
        source_url="https://www.mcta.gov.mn",
        effective_from=None,
        notes=(
            "Mongolia has become a popular destination for international documentary "
            "and drama productions seeking steppe, desert (Gobi), and nomadic culture "
            "settings. The government facilitates permitting through the Ministry of "
            "Culture. No formal cash rebate or financial incentive programme confirmed. "
            + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "formal_programme_status",
                        "permit_process", "min_spend"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MO",
        jurisdiction_name="Macau SAR",
        program_name="Macau Cultural Industries Fund Film Production Support",
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
        source_title="Instituto Cultural (IC) — Macau SAR Government",
        source_url="https://www.ic.gov.mo",
        effective_from=None,
        notes=(
            "Macau's Instituto Cultural administers cultural industry support including "
            "film production grants. The Macau Cultural Industries Fund provides "
            "development and production support. International co-productions with "
            "Macanese entities may access support. Limited scale compared to "
            "mainland China and Hong Kong incentives. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["grant_amount_usd", "co_production_terms",
                        "min_spend", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # South Asia
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="BD",
        jurisdiction_name="Bangladesh",
        program_name="Bangladesh Film Development Corporation (BFDC) Production Support",
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
        source_title="Bangladesh Film Development Corporation (BFDC)",
        source_url="https://www.bfdc.gov.bd",
        effective_from=None,
        notes=(
            "Bangladesh Film Development Corporation (BFDC) under the Ministry of "
            "Information manages state film infrastructure including studio facilities "
            "in Dhaka. BFDC provides studio access and production support for domestic "
            "and some international productions. No formal cash rebate for foreign "
            "productions confirmed. " + _DISC_NOTES_SUFFIX
        ),
        unknown_fields=["financial_incentive_rate", "foreign_production_access",
                        "studio_hire_rates", "processing_timeline"],
    ),
]
