"""
global_inventory_wave2.py

Wave-2 GlobalProgramEntry records: ~35 additional incentive programs across
Europe, Asia-Pacific, North America (new states/provinces), Latin America,
Middle East, and Africa.

All entries are DISCOVERY tier. Rates are from market knowledge and have
not been verified against primary official sources. Unknown values are None.

Jurisdiction codes (new in this file):
  US states:    US-HI, US-UT, US-MN, US-MS, US-AZ, US-PR
  CA provinces: CA-SK, CA-NL
  Europe:       SE, NO, FI, DK, PL, BG, EE, LT, LV, SK, LU, TR
  Asia-Pacific: TH, MY, PH, KR, IN, LK
  LatAm/Carib:  MX, CL, JM, TT
  ME/Africa:    IL, QA, TN, KE, NG
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


WAVE2_PROGRAMS: list[GlobalProgramEntry] = [

    # -----------------------------------------------------------------------
    # US STATES — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="US-HI",
        jurisdiction_name="United States — Hawaii",
        program_name="Hawaii Film and Digital Media Income Tax Credit",
        program_type="tax_credit",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=200_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Hawaii Film Office — digital media production incentive",
        source_url="https://filmoffice.hawaii.gov/incentives/",
        effective_from="2006-01-01",
        notes=(
            "20% refundable tax credit on Hawaii qualified production costs. "
            "Applies to film, TV, and digital media. Unique natural locations (Oahu, Maui, Kauai). "
            "Data gaps: exact QPE definition, ATL scope, processing timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-UT",
        jurisdiction_name="United States — Utah",
        program_name="Utah Motion Picture Incentive Program",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000,
        annual_cap_usd=8_100_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Utah Film Commission — motion picture incentive",
        source_url="https://film.utah.gov/incentives/",
        effective_from="2004-01-01",
        notes=(
            "20% base cash rebate on Utah qualifying spend; 25% with Utah cast/crew bonus. "
            "Annual fund ~$8.1M. Competitive. Diverse locations from salt flats to canyon country. "
            "Data gaps: current fund size, ATL treatment, exact QPE scope."
        ),
        unknown_fields=["annual_cap", "confirmed_rate", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-MN",
        jurisdiction_name="United States — Minnesota",
        program_name="Minnesota Film Production Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000,
        annual_cap_usd=25_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Minnesota Film TV Board — production tax credit",
        source_url="https://www.revenue.state.mn.us/film-production-credit",
        effective_from="2011-01-01",
        notes=(
            "25% refundable tax credit on Minnesota qualifying expenditures. "
            "Annual cap ~$25M. Minneapolis is an established production centre. "
            "Data gaps: current cap, ATL inclusion, processing timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-MS",
        jurisdiction_name="United States — Mississippi",
        program_name="Mississippi Advantage Film Program",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=50_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Mississippi Film Office — Advantage Film Program",
        source_url="https://filmmississippi.org/incentive/",
        effective_from="2014-01-01",
        notes=(
            "25% base refundable tax credit; up to 35% with MS resident crew bonus. "
            "No annual cap. Natchez, Jackson, and Gulf Coast locations. "
            "Data gaps: ATL treatment, confirmed rate, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-AZ",
        jurisdiction_name="United States — Arizona",
        program_name="Arizona Motion Picture Production Program",
        program_type="cash_rebate",
        base_rate=0.15,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=250_000,
        annual_cap_usd=75_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Arizona Commerce Authority — motion picture program",
        source_url="https://www.azcommerce.com/incentives/motion-picture/",
        effective_from="2023-01-01",
        notes=(
            "15-20% base cash rebate on AZ qualified spend. Annual cap ~$75M. "
            "Diverse locations: desert, canyon, urban Phoenix/Scottsdale. "
            "Programme relaunched 2023. Data gaps: ATL inclusion, exact rate tiers."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-PR",
        jurisdiction_name="Puerto Rico (United States Territory)",
        program_name="Puerto Rico Film Industry Economic Incentives Act",
        program_type="tax_credit",
        base_rate=0.40,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=True,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Puerto Rico Film Commission — Act 421-2012 incentives",
        source_url="https://puertoricofilm.ddec.pr.gov/",
        effective_from="2012-01-01",
        notes=(
            "40% refundable/transferable credit under Act 421-2012 (now harmonized under Act 60). "
            "Among the highest rates in the US. Tropical locations; English and Spanish productions. "
            "Data gaps: current Act 60 rate, ATL cap, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # CANADIAN PROVINCES — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CA-SK",
        jurisdiction_name="Canada — Saskatchewan",
        program_name="Creative Saskatchewan Film and TV Production Grant",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.40,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Creative Saskatchewan — film and television production support",
        source_url="https://www.creativesask.ca/funding/",
        effective_from="2014-01-01",
        notes=(
            "Saskatchewan Film Employment Tax Credit was eliminated 2012. "
            "Creative Saskatchewan now administers discretionary production grants. "
            "Up to ~40% of Saskatchewan expenditures via grant programs; structure unconfirmed. "
            "Data gaps: confirmed current rate, programme structure, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-NL",
        jurisdiction_name="Canada — Newfoundland & Labrador",
        program_name="Newfoundland & Labrador Film Development Corp Production Incentive",
        program_type="tax_credit",
        base_rate=0.40,
        max_rate=0.45,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="NLFDC — Newfoundland & Labrador production incentive",
        source_url="https://picturenl.ca/",
        effective_from="2006-01-01",
        notes=(
            "40-45% on eligible NL labour. Combines with federal CPTC. "
            "Dramatic coastal and Viking heritage locations. "
            "Data gaps: confirmed rates, ATL scope, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # EUROPE — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="SE",
        jurisdiction_name="Sweden",
        program_name="Sweden Film Commission Production Rebate",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=700_000,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Swedish Film Institute — production rebate",
        source_url="https://www.filminstitutet.se/en/film-in-sweden/production-rebate/",
        effective_from="2016-01-01",
        notes=(
            "25% cash rebate on qualifying Swedish expenditures (kulturkoefficient kulturell test). "
            "Administered by Swedish Film Institute. Stockholm, Malmö, Gotland locations. "
            "Data gaps: confirmed rate, ATL scope, min spend in SEK, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NO",
        jurisdiction_name="Norway",
        program_name="Norwegian Film Commission Production Incentive",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_400_000,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Norwegian Film Commission — production incentive",
        source_url="https://www.norwegianfilmcommission.no/incentive/",
        effective_from="2016-01-01",
        notes=(
            "25% cash rebate on Norwegian qualifying expenditures. "
            "Fjords, Arctic, Oslo settings. Cultural test required. "
            "Data gaps: confirmed current rate, ATL treatment, exact min spend in NOK."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FI",
        jurisdiction_name="Finland",
        program_name="Business Finland Film Incentive",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Business Finland — film incentive",
        source_url="https://www.businessfinland.fi/en/for-finnish-customers/services/filming-in-finland",
        effective_from="2017-01-01",
        notes=(
            "25% cash rebate on Finnish qualifying expenditures. "
            "Helsinki, Lapland (aurora borealis), forest locations. "
            "Data gaps: confirmed rate, ATL treatment, min spend, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DK",
        jurisdiction_name="Denmark",
        program_name="Danish Film Institute Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Danish Film Institute — production support",
        source_url="https://www.dfi.dk/en/support/production",
        effective_from="2000-01-01",
        notes=(
            "Danish Film Institute provides production grants and market scheme support. "
            "Market scheme: ~25% on Danish spend via commissioner arrangement. "
            "Cultural test applies. Copenhagen, Zealand, and Greenland locations. "
            "Data gaps: cash rebate vs grant structure, confirmed rate, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "is_refundable", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PL",
        jurisdiction_name="Poland",
        program_name="Polish Film Institute (PISF) Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_200_000,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Polish Film Institute — cash rebate for foreign producers",
        source_url="https://en.pisf.pl/financing/cash-rebate",
        effective_from="2019-01-01",
        notes=(
            "30% cash rebate on qualifying Polish expenditures for foreign co-productions. "
            "Warsaw, Kraków, Wrocław studio infrastructure. Low cost base vs Western Europe. "
            "Data gaps: confirmed current rate, exact QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BG",
        jurisdiction_name="Bulgaria",
        program_name="Bulgarian Film Industry Encouragement Act Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Bulgaria Film Commission — cash rebate",
        source_url="https://www.bulgariafilmcommission.bg/incentives/",
        effective_from="2018-01-01",
        notes=(
            "25% cash rebate on Bulgarian qualifying spend. Very low cost base in EU. "
            "Sofia studios, Black Sea locations, diverse Eastern European settings. "
            "Data gaps: confirmed rate, ATL inclusion, min spend verification."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="EE",
        jurisdiction_name="Estonia",
        program_name="Film Estonia Cash Rebate",
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
        source_title="Film Estonia — cash rebate programme",
        source_url="https://filmestonia.eu/incentive/",
        effective_from="2014-01-01",
        notes=(
            "30% cash rebate on qualifying Estonian expenditures. "
            "Tallinn Old Town UNESCO site, Baltic coast, forests. Very low cost base. "
            "Data gaps: confirmed current rate, min spend, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="LT",
        jurisdiction_name="Lithuania",
        program_name="Lithuanian Film Centre Production Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=200_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Lithuanian Film Centre — cash rebate",
        source_url="https://lfc.lt/en/production/cash-rebate/",
        effective_from="2016-01-01",
        notes=(
            "30% cash rebate on qualifying Lithuanian expenditures. "
            "Vilnius Baroque architecture, diverse landscapes, very low costs. "
            "Data gaps: confirmed rate, ATL treatment, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="LV",
        jurisdiction_name="Latvia",
        program_name="National Film Centre of Latvia Production Incentive",
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
        source_title="National Film Centre of Latvia — production incentive",
        source_url="https://www.nkc.gov.lv/en/film-incentive",
        effective_from="2020-01-01",
        notes=(
            "20-25% cash rebate on qualifying Latvian expenditures. "
            "Riga Art Nouveau architecture, Baltic coast, forests. "
            "Data gaps: confirmed rate, min spend, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SK",
        jurisdiction_name="Slovakia",
        program_name="Slovak Audiovisual Fund (AVF) Production Incentive",
        program_type="cash_rebate",
        base_rate=0.33,
        max_rate=0.33,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Slovak Audiovisual Fund — production incentive",
        source_url="https://www.avf.sk/en/production-incentive",
        effective_from="2018-01-01",
        notes=(
            "33% cash rebate on qualifying Slovak expenditures. "
            "Bratislava, Tatry mountains, diverse Central European landscapes. "
            "Data gaps: confirmed rate, min spend, ATL inclusion, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="LU",
        jurisdiction_name="Luxembourg",
        program_name="Film Fund Luxembourg (Filmfund) — Tax Shelter & Rebate",
        program_type="tax_credit",
        base_rate=0.30,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Filmfund Luxembourg — production support",
        source_url="https://www.filmfund.lu/en/production/",
        effective_from="1999-01-01",
        notes=(
            "Up to 40% on Luxembourg qualifying spend. Tax shelter framework + production rebate. "
            "Important European co-production hub. EU treaties access. "
            "Data gaps: confirmed current rate, ATL treatment, min spend."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TR",
        jurisdiction_name="Turkey",
        program_name="Turkey Cinema General Directorate Film Production Support",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Republic of Turkey Ministry of Culture — cinema support",
        source_url="https://www.sinema.gov.tr/en",
        effective_from="2000-01-01",
        notes=(
            "Turkey's Cinema General Directorate provides co-production and production support grants. "
            "Istanbul, Cappadocia, coastal locations. Growing hub for European and Middle Eastern shoots. "
            "Data gaps: confirmed rebate rate, refundability, QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # ASIA-PACIFIC — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="TH",
        jurisdiction_name="Thailand",
        program_name="Thailand Board of Investment (BOI) Film Incentive",
        program_type="cash_rebate",
        base_rate=0.15,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Thailand Film Office — BOI production incentive",
        source_url="https://www.thailandfilmoffice.org/incentive/",
        effective_from="2017-01-01",
        notes=(
            "15-20% cash rebate on Thai qualifying expenditures via BOI. "
            "Bangkok, Chiang Mai, coastal and island locations. Very low cost base. "
            "Data gaps: confirmed current rate, QPE scope, ATL treatment, min spend."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MY",
        jurisdiction_name="Malaysia",
        program_name="FINAS Malaysia Film Rebate",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="FINAS Malaysia — film rebate incentive",
        source_url="https://www.finas.gov.my/incentive/",
        effective_from="2012-01-01",
        notes=(
            "30% cash rebate on qualifying Malaysian spend administered by FINAS. "
            "Kuala Lumpur, Langkawi, rainforest and coastal locations. "
            "Data gaps: confirmed current rate, min spend, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PH",
        jurisdiction_name="Philippines",
        program_name="Film Development Council of the Philippines (FDCP) Incentive",
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
        source_title="Film Development Council of the Philippines — production incentive",
        source_url="https://fdcp.ph/production-incentives/",
        effective_from="2010-01-01",
        notes=(
            "Up to 20% cash rebate on qualifying Philippine expenditures. "
            "Manila, Palawan, Visayas island locations. Low cost base. "
            "Data gaps: confirmed rate, min spend, QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KR",
        jurisdiction_name="South Korea",
        program_name="Korea Film Council (KOFIC) Location Incentive",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Korean Film Council (KOFIC) — location incentive",
        source_url="https://www.kofic.or.kr/kofic/business/eng/filmLocation/filmLocationMain.do",
        effective_from="2015-01-01",
        notes=(
            "KOFIC provides location incentive and production support for foreign productions. "
            "Seoul, Busan, DMZ, and diverse modern/traditional settings. "
            "Data gaps: confirmed rebate rate, refundability, min spend, QPE scope."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IN",
        jurisdiction_name="India",
        program_name="India National Film Development Corporation (NFDC) and State Incentives",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.30,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="India NFDC — co-production and state film incentives",
        source_url="https://www.nfdcindia.com/",
        effective_from="2000-01-01",
        notes=(
            "Multiple state film incentives: Madhya Pradesh (25%), Rajasthan (20%), Uttar Pradesh (25%), etc. "
            "NFDC facilitates co-productions. Very low cost base; enormous location diversity. "
            "Data gaps: no single national rebate rate; state-level only; ATL treatment varies."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="LK",
        jurisdiction_name="Sri Lanka",
        program_name="Sri Lanka Film Commission Production Incentive",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Sri Lanka Film Commission — production incentive",
        source_url="https://srilankafilmcommission.lk/incentives/",
        effective_from="2015-01-01",
        notes=(
            "Sri Lanka offers production incentives; confirmed rate structure unverified. "
            "Colombo, Sigiriya, tea country, coastal locations. Very low cost base. "
            "Data gaps: confirmed rate, refundability, min spend, QPE scope."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # LATIN AMERICA & CARIBBEAN — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="MX",
        jurisdiction_name="Mexico",
        program_name="Mexico EFICINE (Article 226 Tax Credit) and PROCINE Fund",
        program_type="tax_credit",
        base_rate=0.10,
        max_rate=0.175,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="IMCINE Mexico — EFICINE incentive programme",
        source_url="https://www.imcine.gob.mx/eficine",
        effective_from="2006-01-01",
        notes=(
            "EFICINE (Art. 226 Income Tax Law): 10% tax credit for investors in Mexican film. "
            "PROCINE grants additional direct support up to 17.5% for qualifying projects. "
            "Mexico City, Oaxaca, Baja California locations; major Spanish-language hub. "
            "Data gaps: confirmed current rate, ATL treatment, foreign co-production conditions."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CL",
        jurisdiction_name="Chile",
        program_name="Chile Corfo / CORFO Film Incentive",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Chile Film Commission — Corfo production incentive",
        source_url="https://www.chilefilms.cl/incentivos/",
        effective_from="2012-01-01",
        notes=(
            "20-30% cash rebate on qualifying Chilean expenditures via Corfo. "
            "Santiago, Atacama Desert, Patagonia, Easter Island, Torres del Paine. "
            "Data gaps: confirmed current rate, QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="JM",
        jurisdiction_name="Jamaica",
        program_name="Jamaica Entertainment Industry Incentive Programme",
        program_type="tax_credit",
        base_rate=0.40,
        max_rate=0.50,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Jamaica Film Commission — entertainment incentive",
        source_url="https://www.filmjamaica.com/",
        effective_from="2016-01-01",
        notes=(
            "Up to 50% in combined tax incentives on qualifying Jamaica expenditures. "
            "Kingston, Montego Bay, beach and jungle locations. English-speaking. "
            "Data gaps: confirmed rate structure, refundability details, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TT",
        jurisdiction_name="Trinidad & Tobago",
        program_name="Trinidad & Tobago Creative Industries Production Incentive",
        program_type="tax_credit",
        base_rate=0.35,
        max_rate=0.35,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="TT Film Commission — creative industries incentive",
        source_url="https://filmtt.co.tt/",
        effective_from="2003-01-01",
        notes=(
            "~35% allowance on qualifying T&T expenditures under Creative Industries legislation. "
            "Port of Spain, Tobago beaches, carnival culture backdrop. "
            "Data gaps: confirmed rate, refundability, min spend, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # MIDDLE EAST & AFRICA — NEW
    # -----------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="IL",
        jurisdiction_name="Israel",
        program_name="Israel Film Fund / Maslool Incentive for Foreign Productions",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.30,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Israel Film Fund — production incentives",
        source_url="https://www.filmfund.org.il/en/incentives/",
        effective_from="2010-01-01",
        notes=(
            "Israel Film Fund and co-production treaties provide up to ~30% incentive. "
            "Jerusalem, Tel Aviv, Negev desert, Dead Sea locations. English/Hebrew productions. "
            "Data gaps: confirmed rebate rate structure, refundability, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="QA",
        jurisdiction_name="Qatar",
        program_name="Qatar Film Commission Production Incentive",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Qatar Film Commission — production incentive",
        source_url="https://www.qatarfilm.com/incentives/",
        effective_from="2015-01-01",
        notes=(
            "Qatar Film Commission offers 20-35% in production incentives on Qatar spend. "
            "Doha, desert, and Gulf locations. Increasingly used for prestige international projects. "
            "Data gaps: confirmed rate structure, refundability, QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TN",
        jurisdiction_name="Tunisia",
        program_name="Tunisia National Centre for Cinema and Image (CNCI) Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="CNCI Tunisia — film production incentive",
        source_url="https://www.cnci.com.tn/incitations",
        effective_from="2009-01-01",
        notes=(
            "25-30% cash rebate on qualifying Tunisian expenditures. "
            "Sahara Desert (Star Wars/Indiana Jones locations), Carthage, Medinas. Very low cost base. "
            "Data gaps: confirmed rate, refundability, QPE scope, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="KE",
        jurisdiction_name="Kenya",
        program_name="Kenya Film Commission (KFC) Production Incentive",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.20,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Kenya Film Commission — production incentive",
        source_url="https://kenyafilmcommission.go.ke/",
        effective_from="2016-01-01",
        notes=(
            "Kenya Film Commission offers rebates and support for qualifying productions. "
            "Nairobi, Maasai Mara, Mount Kenya, Indian Ocean coast. East Africa hub. "
            "Data gaps: confirmed rebate rate, refundability, min spend, QPE scope."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NG",
        jurisdiction_name="Nigeria",
        program_name="National Film and Video Censors Board / Creative Economy Incentive",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Nigeria Film Corporation — creative economy incentive",
        source_url="https://www.nfc.gov.ng/incentives/",
        effective_from="2020-01-01",
        notes=(
            "Nigeria (Nollywood) has policy incentive frameworks; formal international rebate unconfirmed. "
            "Lagos, Abuja, diverse African locations. Second-largest film producer globally by volume. "
            "Data gaps: confirmed rate, refundability, formal programme structure, QPE scope."
        ),
        unknown_fields=["confirmed_rate", "is_refundable", "atl_inclusion", "processing_timeline"],
    ),
]
