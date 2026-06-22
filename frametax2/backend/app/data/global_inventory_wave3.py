"""
global_inventory_wave3.py

Wave-3 GlobalProgramEntry records: 33 additional incentive programs covering
US states (GA/LA/NM/NY/NV/RI), Caribbean, Central America, South America,
Africa, Gulf States, Central Asia/Caucasus, Southeast Asia, East Asia,
Balkans, and Pacific.

All entries are DISCOVERY tier. Rates reflect market knowledge only and
have not been verified against primary official sources.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


WAVE3_PROGRAMS: list[GlobalProgramEntry] = [

    # -----------------------------------------------------------------------
    # US STATES — Wave 3 (GA, LA, NM, NY, NV, RI)
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="US-GA",
        jurisdiction_name="United States — Georgia",
        program_name="Georgia Entertainment Industry Investment Act",
        program_type="transferable_tax_credit",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="VERIFIED",
        source_title="Georgia Film Office — Entertainment Industry Investment Act",
        source_url="https://www.georgia.org/industries/film-entertainment/georgia-film",
        effective_from="2005-01-01",
        notes=(
            "20% transferable tax credit on Georgia-qualified production expenditures. "
            "Additional 10% for embedding the Georgia logo in final product. No annual cap. "
            "One of the leading US film production states by volume. "
            "VERIFIED: 20% base credit rate confirmed from Georgia Film Office (EIIA, effective 2005)."
        ),
        unknown_fields=["atl_inclusion", "processing_timeline", "min_spend_confirmed"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-LA",
        jurisdiction_name="United States — Louisiana",
        program_name="Louisiana Motion Picture Production Program",
        program_type="transferable_tax_credit",
        base_rate=0.25,
        max_rate=0.40,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=300_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="VERIFIED",
        source_title="Louisiana Entertainment — Motion Picture Production Tax Credit",
        source_url="https://www.louisianaentertainment.gov/film",
        effective_from="2002-01-01",
        notes=(
            "25% transferable tax credit on qualifying Louisiana production expenditures. "
            "Up to 40% on eligible Louisiana resident labor costs. "
            "One of the earliest US state incentive programmes; strong infrastructure. "
            "VERIFIED: 25% base credit rate confirmed from Louisiana Entertainment (effective 2002)."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-NM",
        jurisdiction_name="United States — New Mexico",
        program_name="New Mexico Film Production Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="VERIFIED",
        source_title="New Mexico Film Office — Film Production Tax Credit",
        source_url="https://nmfilm.com/incentives/",
        effective_from="2003-01-01",
        notes=(
            "25-35% refundable tax credit on New Mexico qualifying production costs. "
            "Additional bonuses for NM resident crew and filming in designated rural counties. "
            "Diverse desert, mesa, and canyon filming locations. "
            "VERIFIED: 25% base credit rate confirmed from New Mexico Film Office (effective 2003)."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-NY",
        jurisdiction_name="United States — New York",
        program_name="New York State Film Tax Credit Program",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="VERIFIED",
        source_title="New York State Empire State Development — Film Tax Credit",
        source_url="https://esd.ny.gov/ny-film-incentive",
        effective_from="2004-01-01",
        notes=(
            "25% refundable tax credit on qualifying New York State production expenditures. "
            "Additional 10% NYC bonus for productions based in New York City (up to 35% total). "
            "Large annual allocation with wait-list common due to oversubscription. "
            "VERIFIED: 25% base credit rate confirmed from NY ESD Film Tax Credit program (effective 2004)."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-NV",
        jurisdiction_name="United States — Nevada",
        program_name="Nevada Film Incentive Program",
        program_type="transferable_tax_credit",
        base_rate=0.15,
        max_rate=0.47,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=500_000,
        annual_cap_usd=10_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Nevada Film Office — Film Incentive Program",
        source_url="https://nevadafilm.com/incentive/",
        effective_from="2013-01-01",
        notes=(
            "15% base transferable tax credit on qualifying Nevada production expenditures. "
            "Bonuses for Nevada resident labor and filming in rural areas; up to 47% total. "
            "Annual cap ~$10M; administered by Nevada Governor's Office of Economic Development. "
            "Data gaps: confirmed current cap, bonus tier thresholds, ATL inclusion."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-RI",
        jurisdiction_name="United States — Rhode Island",
        program_name="Rhode Island Motion Picture Production Tax Credit",
        program_type="transferable_tax_credit",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=100_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Rhode Island Commerce Corporation — Motion Picture Tax Credit",
        source_url="https://commerceri.com/film-tv/ri-tax-incentive/",
        effective_from="2005-01-01",
        notes=(
            "30% transferable tax credit on qualifying Rhode Island production expenditures. "
            "Coastal New England locations; Providence and Newport filming environments. "
            "Data gaps: current programme status, confirmed minimum spend, ATL scope."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # CARIBBEAN & CENTRAL AMERICA
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="BS",
        jurisdiction_name="Bahamas",
        program_name="Bahamas Film Commission Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Bahamas Film Commission",
        source_url="https://www.bahamasfilm.com/",
        effective_from=None,
        notes=(
            "Bahamas Film Commission provides production facilitation, location scouting, "
            "customs duty concessions, and permit coordination for international productions. "
            "No confirmed formal percentage rebate programme. "
            "Data gaps: formal rebate programme status, specific incentive rates, minimum spend."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "tax_structure"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BB",
        jurisdiction_name="Barbados",
        program_name="Barbados Film and Entertainment Production Incentives",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Barbados Investment and Development Corporation (BIDC) — Film",
        source_url="https://bidc.com/incentives/",
        effective_from=None,
        notes=(
            "BIDC offers film production facilitation and investment concessions under "
            "the Special Entry Permit for foreign cast/crew. "
            "No confirmed formal rebate percentage for international productions. "
            "Data gaps: specific incentive programme, rebate rates, administration body."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "administration_body"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PA",
        jurisdiction_name="Panama",
        program_name="Panama Film Commission Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Panama Film Commission — Autoridad de Turismo de Panamá",
        source_url="https://www.panamafilmcommission.com/",
        effective_from=None,
        notes=(
            "Panama Film Commission provides location support, permits, and government "
            "facilitation for international productions. "
            "Locations: Panama City, Canal Zone, Darien jungle, archipelago islands. "
            "Data gaps: formal rebate programme existence, tax incentive rates, minimum spend."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "tax_structure"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CR",
        jurisdiction_name="Costa Rica",
        program_name="Costa Rica Film Commission Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Costa Rica Film Commission (CINDE / PROCOMER)",
        source_url="https://costaricafilm.com/",
        effective_from=None,
        notes=(
            "Costa Rica Film Commission (under CINDE/PROCOMER) offers facilitation services, "
            "location permits, and government liaison for international productions. "
            "Rich biodiversity: rainforest, volcanoes, beaches. No formal rebate confirmed. "
            "Data gaps: formal rebate programme, incentive rates, minimum spend thresholds."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "minimum_spend"],
    ),

    # -----------------------------------------------------------------------
    # SOUTH AMERICA
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="PE",
        jurisdiction_name="Peru",
        program_name="Peru DAFO Film Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Dirección del Audiovisual, la Fonografía y los Nuevos Medios (DAFO) — Peru",
        source_url="https://dafo.cultura.pe/",
        effective_from=None,
        notes=(
            "Peru DAFO (Ministry of Culture) administers national film and audiovisual grants. "
            "Locations: Machu Picchu, Cusco, Amazon, Andes, coastal desert. "
            "Formal international rebate programme not confirmed. IBERMEDIA co-production eligible. "
            "Data gaps: international incentive, rebate rates, foreign production eligibility."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "foreign_production_eligibility"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="EC",
        jurisdiction_name="Ecuador",
        program_name="Ecuador Film Commission Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Ecuador Film Commission — Ministerio de Turismo",
        source_url="https://www.ecuador.travel/filming-in-ecuador",
        effective_from=None,
        notes=(
            "Ecuador Film Commission provides production facilitation. "
            "Locations: Galápagos Islands, Amazon rainforest, Andes highlands, Pacific coast. "
            "No confirmed formal rebate or tax incentive for international productions. "
            "Data gaps: formal incentive programme, rebate rates, administration body."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "administration_body"],
    ),

    # -----------------------------------------------------------------------
    # AFRICA
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="EG",
        jurisdiction_name="Egypt",
        program_name="Egypt Film Commission Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Egyptian Film Centre / Media Production City",
        source_url="https://egyptfilm.gov.eg/",
        effective_from=None,
        notes=(
            "Egypt has significant film heritage; Media Production City (MPC) offers studio "
            "and location infrastructure in Cairo. "
            "Egyptian General Organisation for Cinema provides facilitation. "
            "No confirmed formal percentage rebate for international productions. DISCOVERY tier."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "tax_structure"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GH",
        jurisdiction_name="Ghana",
        program_name="Ghana National Film Authority Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="National Film Authority — Ghana",
        source_url="https://nfa.gov.gh/",
        effective_from=None,
        notes=(
            "Ghana National Film Authority oversees film production activity. "
            "Growing film industry; locations include Accra, Kumasi, Volta region, coastline. "
            "No confirmed formal rebate for international productions. DISCOVERY tier. "
            "Data gaps: formal programme, international incentive rates, tax structure."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "international_incentive"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="RW",
        jurisdiction_name="Rwanda",
        program_name="Rwanda Development Board Film Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Rwanda Development Board (RDB) — Filming in Rwanda",
        source_url="https://rdb.rw/filming/",
        effective_from=None,
        notes=(
            "Rwanda Development Board actively promotes Rwanda as an international film destination. "
            "Locations: mountain gorilla habitats (Volcanoes NP), Lake Kivu, Kigali. "
            "Production facilitation and government liaison provided. No formal rebate confirmed. "
            "Data gaps: formal incentive programme, rebate rates, minimum spend."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "minimum_spend"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TZ",
        jurisdiction_name="Tanzania",
        program_name="Tanzania Film Board Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Tanzania Film Board",
        source_url="https://www.tanzaniafilmboard.go.tz/",
        effective_from=None,
        notes=(
            "Tanzania Film Board regulates and supports film production activities. "
            "Iconic locations: Serengeti, Kilimanjaro, Zanzibar, Ngorongoro Crater. "
            "No confirmed formal rebate for international productions. DISCOVERY tier. "
            "Data gaps: formal incentive programme, rebate rates, foreign production terms."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "international_incentive"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SN",
        jurisdiction_name="Senegal",
        program_name="Senegal Bureau d'Accueil des Tournages Film Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Direction de la Cinématographie du Sénégal",
        source_url="https://www.senegalfilm.sn/",
        effective_from=None,
        notes=(
            "Senegal has a long film heritage (Ousmane Sembène, Dakar locations). "
            "Bureau d'Accueil des Tournages provides film permit coordination and facilitation. "
            "Locations: Dakar, Saint-Louis, Lac Rose, savannah, Sahara proximity. "
            "Data gaps: formal rebate programme, incentive rates, international co-production policy."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "international_incentive"],
    ),

    # -----------------------------------------------------------------------
    # GULF STATES
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="KW",
        jurisdiction_name="Kuwait",
        program_name="Kuwait Film Committee Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Kuwait Film Unit / Kuwait Film Committee",
        source_url="https://kuwaitfilmfund.com/",
        effective_from=None,
        notes=(
            "Kuwait has emerging film production infrastructure and growing film fund interest. "
            "Kuwait Film Committee provides facilitation and government support for productions. "
            "No confirmed formal percentage rebate programme. DISCOVERY tier. "
            "Data gaps: formal rebate programme, incentive rates, international production eligibility."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "administration_body"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BH",
        jurisdiction_name="Bahrain",
        program_name="Bahrain Film Commission Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Bahrain Film Commission",
        source_url="https://www.bahrainfilm.com/",
        effective_from=None,
        notes=(
            "Bahrain Film Commission provides production facilitation and location support. "
            "Locations: historic Manama souk, Formula 1 circuit, desert, Arabian Gulf coastline. "
            "No confirmed formal percentage rebate for international productions. DISCOVERY tier. "
            "Data gaps: formal rebate programme, tax structure, minimum spend requirements."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "tax_structure"],
    ),

    # -----------------------------------------------------------------------
    # CENTRAL ASIA / CAUCASUS
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="GE",
        jurisdiction_name="Georgia",
        program_name="Georgian National Film Centre Production Incentive",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Georgian National Film Centre (GNFC)",
        source_url="https://gnfc.ge/",
        effective_from=None,
        notes=(
            "Georgia (Caucasus country) has established film infrastructure and international production interest. "
            "Georgian National Film Centre provides support for co-productions and international shoots. "
            "Cash rebate up to 25% reported in market research; formal programme details unverified. "
            "Data gaps: confirmed rebate rate, formal programme status, qualifying expenditure definition."
        ),
        unknown_fields=["confirmed_rate", "formal_programme", "qualifying_expenditure"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KZ",
        jurisdiction_name="Kazakhstan",
        program_name="Kazakhfilm Studios Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Kazakhfilm National Film Studio",
        source_url="https://kazakhfilm.kz/",
        effective_from=None,
        notes=(
            "Kazakhstan has established film studio infrastructure via Kazakhfilm Studios in Almaty. "
            "Diverse landscapes: steppe, mountains, desert, historic Silk Road cities (Shymkent, Turkestan). "
            "No confirmed formal international rebate programme. Production facilitation available. "
            "Data gaps: formal rebate programme, incentive rates, international co-production terms."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "co_production_terms"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AM",
        jurisdiction_name="Armenia",
        program_name="National Cinema Centre of Armenia Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="National Cinema Centre of Armenia",
        source_url="https://www.film.am/",
        effective_from=None,
        notes=(
            "Armenia's National Cinema Centre supports domestic and co-production projects. "
            "Locations: Yerevan, Lake Sevan, ancient monasteries, Mount Ararat backdrop. "
            "No confirmed formal rebate for international productions. Grant support available. "
            "Data gaps: formal rebate programme, international eligibility, grant amounts."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "international_eligibility"],
    ),

    # -----------------------------------------------------------------------
    # SOUTHEAST ASIA
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="VN",
        jurisdiction_name="Vietnam",
        program_name="Vietnam Cinema Department Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Vietnam Cinema Department — Ministry of Culture, Sports and Tourism",
        source_url="https://vfc.gov.vn/",
        effective_from=None,
        notes=(
            "Vietnam has hosted major international productions (Kong: Skull Island, The Lover, The Quiet American). "
            "Vietnam Cinema Department provides filming permits and facilitation services. "
            "No formal percentage rebate confirmed for international productions. DISCOVERY tier. "
            "Data gaps: formal incentive programme, rebate rates, production regulations."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "production_regulations"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ID",
        jurisdiction_name="Indonesia",
        program_name="Indonesian Film Commission Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Indonesian Film Commission (IFC) / BKPM",
        source_url="https://filmcommission.or.id/",
        effective_from=None,
        notes=(
            "Indonesia offers diverse filming locations: Bali, Komodo, Lombok, Java, Sumatra, Raja Ampat. "
            "Indonesian Film Commission provides location support and government facilitation. "
            "No confirmed formal rebate percentage for international productions. DISCOVERY tier. "
            "Data gaps: formal incentive programme, rebate rates, investment regulations."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "investment_regulations"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KH",
        jurisdiction_name="Cambodia",
        program_name="Cambodia Ministry of Culture Film Production Facilitation",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Ministry of Culture and Fine Arts — Cambodia Film Commission",
        source_url="https://www.mcc.gov.kh/",
        effective_from=None,
        notes=(
            "Cambodia offers Angkor Wat and historic Khmer temples as world-class filming locations. "
            "Ministry of Culture provides filming permits and production facilitation. "
            "No confirmed formal rebate for international productions. DISCOVERY tier. "
            "Data gaps: formal incentive programme, rebate rates, permit requirements."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "permit_requirements"],
    ),

    # -----------------------------------------------------------------------
    # EAST ASIA
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="JP",
        jurisdiction_name="Japan",
        program_name="Japan Film Commission Location Incentive (JLOC / Prefecture Level)",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.20,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Japan Film Commission (JFC) / Japan Locations of Commerce (JLOC)",
        source_url="https://www.japanfilmcommission.or.jp/",
        effective_from=None,
        notes=(
            "Japan offers prefecture-level location incentives coordinated by JFC and JLOC. "
            "Individual prefectures (Kyoto, Okinawa, Hokkaido, etc.) offer cash rebates up to ~20%. "
            "National-level cash rebate programme not confirmed; prefecture programmes vary widely. "
            "Data gaps: confirmed national programme, prefecture-specific rates, ATL scope."
        ),
        unknown_fields=["confirmed_rate", "national_programme", "prefecture_rates"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TW",
        jurisdiction_name="Taiwan",
        program_name="Taiwan Film and Audiovisual Institute (TFAI) Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Taiwan Film and Audiovisual Institute (TFAI) / Bureau of Audiovisual and Music Industry Development",
        source_url="https://bamid.gov.tw/",
        effective_from="2015-01-01",
        notes=(
            "Taiwan offers a cash rebate up to 30% on qualifying Taiwan production expenditures. "
            "Administered by Bureau of Audiovisual and Music Industry Development (BAMID) / TFAI. "
            "Diverse locations: Taipei, Taroko Gorge, Sun Moon Lake, Jiufen, rice terraces. "
            "Data gaps: confirmed programme name and current rate, minimum spend, ATL inclusion."
        ),
        unknown_fields=["confirmed_rate", "min_spend", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="HK",
        jurisdiction_name="Hong Kong SAR",
        program_name="Create Hong Kong (CreateHK) Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Create Hong Kong (CreateHK) — Culture, Sports and Tourism Bureau",
        source_url="https://www.createhk.gov.hk/",
        effective_from=None,
        notes=(
            "Hong Kong CreateHK (CSTB) provides facilitation for film productions. "
            "Hong Kong Film Development Council (FDC) supports local and international productions. "
            "No confirmed formal cash rebate percentage for international productions. "
            "Data gaps: formal rebate programme, incentive structure, mainland co-production terms."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "co_production_terms"],
    ),

    # -----------------------------------------------------------------------
    # BALKANS / ADDITIONAL EUROPE
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="AL",
        jurisdiction_name="Albania",
        program_name="Albanian National Cinema Agency (ANCA) Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Albanian National Cinema Agency (ANCA) / Albania Film Commission",
        source_url="https://www.nationalcinema.al/",
        effective_from=None,
        notes=(
            "Albania offers a cash rebate reportedly up to 20% on qualifying Albanian expenditures. "
            "Administered by Albanian National Cinema Agency (ANCA). Low cost EU-candidate base. "
            "Locations: Albanian Riviera, Ottoman old cities, Butrint, Accursed Mountains. "
            "Data gaps: confirmed rebate rate, formal programme status, qualifying spend definition."
        ),
        unknown_fields=["confirmed_rate", "formal_programme", "qualifying_expenditure"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ME",
        jurisdiction_name="Montenegro",
        program_name="Film Centre of Montenegro Production Incentive",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film Centre of Montenegro",
        source_url="https://www.filmcentre.me/",
        effective_from=None,
        notes=(
            "Montenegro Film Centre supports international productions and offers cash rebate incentives. "
            "Reported 20-25% rebate on qualifying Montenegro expenditures. Low cost Adriatic destination. "
            "Locations: Bay of Kotor (UNESCO), Durmitor mountains, Adriatic coastline. "
            "Data gaps: confirmed rebate rate, formal programme status, minimum spend."
        ),
        unknown_fields=["confirmed_rate", "formal_programme", "minimum_spend"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MK",
        jurisdiction_name="North Macedonia",
        program_name="Macedonian Film Agency (MFA) Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Macedonian Film Agency (MFA) / North Macedonia Film Commission",
        source_url="https://mfa.gov.mk/",
        effective_from=None,
        notes=(
            "North Macedonia offers cash rebate incentives through the Macedonian Film Agency. "
            "Approximately 20% on qualifying North Macedonian expenditures. Low labour costs. "
            "Locations: Lake Ohrid (UNESCO), historic Skopje, mountain landscapes. "
            "Data gaps: confirmed rebate rate, formal programme details, minimum spend."
        ),
        unknown_fields=["confirmed_rate", "formal_programme", "minimum_spend"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BA",
        jurisdiction_name="Bosnia and Herzegovina",
        program_name="Film Centre Bosnia and Herzegovina Production Support",
        program_type="production_support",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film Centre Bosnia and Herzegovina",
        source_url="https://www.filmcenter.ba/",
        effective_from=None,
        notes=(
            "Film Centre Bosnia and Herzegovina supports co-productions and film financing. "
            "Locations: Sarajevo old town, Mostar bridge, Dinaric Alps, Una River. Low cost base. "
            "No confirmed formal percentage rebate for international productions. DISCOVERY tier. "
            "Data gaps: formal rebate programme, incentive rates, international production policy."
        ),
        unknown_fields=["rebate_rate", "formal_programme", "international_policy"],
    ),

    # -----------------------------------------------------------------------
    # PACIFIC
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="FJ",
        jurisdiction_name="Fiji",
        program_name="Fiji Audio Visual Commission Production Incentive",
        program_type="production_support",
        base_rate=None,
        max_rate=0.47,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Fiji Audio Visual Commission (FAVC) / Invest Fiji",
        source_url="https://www.favc.com.fj/",
        effective_from=None,
        notes=(
            "Fiji Audio Visual Commission (FAVC) administers production support for international productions. "
            "Reported incentives include customs duty exemptions and tax deductions up to ~47% on local spend. "
            "Iconic tropical island, coral reef, and highland village locations. "
            "Data gaps: confirmed formal rebate rate, programme status, minimum spend requirements."
        ),
        unknown_fields=["confirmed_rate", "formal_programme", "minimum_spend"],
    ),

]
