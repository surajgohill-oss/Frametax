"""
Grants Wave-3 — additional global soft-money, development funds, and
co-production vehicles added in the Phase A-D completeness pass.

Includes:
  - Canada: Bell Fund, NSI, Hot Docs Forum co-finance
  - Germany: Berlinale World Cinema Fund
  - EU/INT: Torino Film Lab
  - Netherlands: IDFA Forum
  - USA: Tribeca Film Institute grants
  - Israel: Jerusalem International Film Lab
  - Australia: MIFF Premiere Fund
  - Sweden: Göteborg Film Festival Fund
  - Burkina Faso: FESPACO (new jurisdiction — BF)
  - Portugal: ICA Co-production Fund
  - Switzerland: Federal Office of Culture International Co-production
  - Mexico: IMCINE production grants
  - Norway: NFI production grants (separate from 25% rebate)
  - Finland: Finnish Film Foundation grants (separate from Business Finland rebate)
  - UK: Creative England (English regional development)
  - South Africa: IDC Film Fund (development finance)
  - Morocco: CCM Avance sur Recettes (separate from rebate)
  - Argentina: INCAA development grants
  - Brazil: ANCINE/FUNCINES development fund
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


GRANTS3_PROGRAMS: list[GlobalProgramEntry] = [

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="Bell Fund — Broadcast and Digital Content Development",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Bell Fund — Broadcast Content Development Programme",
        source_url="https://bellfund.ca/what-we-fund/",
        effective_from=None,
        notes=(
            "Bell Fund provides development and production grants for digital interactive and broadcast content. "
            "CAVCO Canadian content certification required. "
            "Distinct from CMF (Canada Media Fund) — Bell Fund focuses on digital-first convergent projects. "
            "Annual allocation ~CAD $10-20M."
        ),
        unknown_fields=[
            "grant_size_range", "digital_vs_broadcast_breakdown", "annual_allocation_exact",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA",
        jurisdiction_name="Canada",
        program_name="NSI — National Screen Institute Drama Prize and Development Programs",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="National Screen Institute (NSI) Canada",
        source_url="https://www.nsi-canada.ca",
        effective_from=None,
        notes=(
            "NSI provides script development funding and training for emerging Canadian film/TV creators. "
            "Indigenous and equity-deserving creators prioritized through dedicated programs. "
            "Development grants typically $5K-$25K per project. "
            "Separate from CMF and Telefilm Canada."
        ),
        unknown_fields=[
            "grant_size_range", "programme_eligibility_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE",
        jurisdiction_name="Germany",
        program_name="Berlinale World Cinema Fund (WCF) — Development and Production Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Berlinale World Cinema Fund — Grants",
        source_url="https://www.berlinale.de/en/world-cinema-fund/",
        effective_from="2004-01-01",
        notes=(
            "Berlinale World Cinema Fund (WCF) provides development and production grants for films from "
            "Africa, Latin America, Middle East, Central Asia, and Southeast Asia. "
            "Per-project grants typically €50K-€600K. "
            "Co-production vehicle requiring German co-production element. "
            "Annual budget ~€1.5M across development and production."
        ),
        unknown_fields=[
            "exact_grant_range", "selection_criteria_current", "annual_fund_size",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="EU",
        jurisdiction_name="Europe (international — Torino, Italy)",
        program_name="Torino Film Lab — International Development and Production Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Torino Film Lab — TFL Grants",
        source_url="https://www.torinofilmlab.it/activities/production-grants/",
        effective_from=None,
        notes=(
            "Torino Film Lab provides development and production grants for international co-productions. "
            "Creative Europe MEDIA supported. Focus on first and second feature films. "
            "Script development grants and FeatureLab completion/production awards. "
            "Based in Turin, Italy; annual selection of ~10-15 projects."
        ),
        unknown_fields=[
            "exact_grant_range", "selection_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NL",
        jurisdiction_name="Netherlands",
        program_name="IDFA Forum — International Documentary Co-financing Market",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="IDFA Forum (International Documentary Film Festival Amsterdam)",
        source_url="https://www.idfa.nl/en/info/idfa-forum",
        effective_from=None,
        notes=(
            "IDFA Forum connects international documentary projects with broadcasters, distributors, and co-producers. "
            "Not a direct grant — structured co-financing market with broadcaster commissioning. "
            "Projects selected for IDFA Forum often secure co-production contributions at the event. "
            "Amsterdam-based; annual event in November."
        ),
        unknown_fields=[
            "grant_vs_cofinance_distinction", "broadcaster_commitments_average",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US",
        jurisdiction_name="United States",
        program_name="Tribeca Film Institute — Documentary and Narrative Development Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Tribeca Film Institute — Grants and Award Programs",
        source_url="https://tribecafilm.com/institute",
        effective_from=None,
        notes=(
            "Tribeca Film Institute (NYC) provides development grants for independent film and digital projects. "
            "Awards through Tribeca All Access (TAA), Tribeca/ESPN Sports Film Festival grants, and others. "
            "Typically $10K-$50K development grants; production awards up to $100K. "
            "New York-based; linked to Tribeca Film Festival (April)."
        ),
        unknown_fields=[
            "exact_grant_range", "eligibility_criteria", "programme_active_status_current",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IL",
        jurisdiction_name="Israel",
        program_name="Jerusalem International Film Lab — Development Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Jerusalem Film and Television Center — Jerusalem Film Lab",
        source_url="https://www.jff.org.il/en/jerusalem-film-lab/",
        effective_from=None,
        notes=(
            "Jerusalem International Film Lab provides development grants for projects with Israeli creative elements. "
            "Annual lab format: script-to-screen development with international advisors. "
            "Linked to Jerusalem Film Festival."
        ),
        unknown_fields=[
            "exact_grant_range", "israeli_content_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU",
        jurisdiction_name="Australia",
        program_name="Melbourne International Film Festival (MIFF) Premiere Fund",
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
        source_title="MIFF Premiere Fund — Australian Films",
        source_url="https://miff.com.au/industry/premiere-fund",
        effective_from=None,
        notes=(
            "MIFF Premiere Fund provides production grants (typically up to A$500K) for Australian feature films "
            "that will premiere at MIFF. "
            "Australian content requirement: CAVCO-equivalent Australian creative control. "
            "Separate from Screen Australia and state-level funding."
        ),
        unknown_fields=[
            "exact_grant_amount", "eligibility_criteria", "premiere_exclusivity_requirement",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SE",
        jurisdiction_name="Sweden",
        program_name="Göteborg Film Festival — Nordic Co-production Summit Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Göteborg Film Festival — Nordic Co-production Summit",
        source_url="https://www.giff.se/en/industry/",
        effective_from=None,
        notes=(
            "Göteborg Film Festival facilitates Nordic co-production development grants through its "
            "Nordic Co-production Summit. Primarily focuses on Nordic and international co-productions. "
            "Swedish Film Institute and Nordic Film & TV Fund co-supported."
        ),
        unknown_fields=[
            "exact_grant_range", "nordic_co_production_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BF",
        jurisdiction_name="Burkina Faso",
        program_name="FESPACO — Festival Pan-Africain du Cinéma et de la Télévision de Ouagadougou",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="FESPACO — Pan-African Film Festival",
        source_url="https://www.fespaco.bf",
        effective_from="1969-01-01",
        notes=(
            "FESPACO (Ouagadougou) is Africa's largest and oldest film festival, held biennially. "
            "Administers development grants and prizes for African cinema via ACP (Africa, Caribbean, Pacific) funds. "
            "Pan-African eligibility: projects from African states, diaspora, and ACP members. "
            "Prize awards and co-production market grants distinguish FESPACO from direct government grants."
        ),
        unknown_fields=[
            "exact_grant_mechanism", "eligibility_criteria", "prize_vs_grant_distinction",
            "biennial_cycle_application_window",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PT",
        jurisdiction_name="Portugal",
        program_name="ICA — Instituto do Cinema e Audiovisual International Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="ICA — Instituto do Cinema e do Audiovisual — Co-produção Internacional",
        source_url="https://www.ica-ip.pt/pt/apoios/co-producao-internacional/",
        effective_from=None,
        notes=(
            "ICA administers the Portuguese international co-production fund for qualifying projects "
            "with Portuguese creative participation. "
            "Co-production treaties: Brazil, CPLP members (Angola, Mozambique, Cape Verde, etc.), "
            "and bilateral European treaties. "
            "Grants typically €50K-€500K per project."
        ),
        unknown_fields=[
            "grant_size_range", "co_production_treaty_list", "portuguese_participation_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CH",
        jurisdiction_name="Switzerland",
        program_name="BAK Swiss Federal Office of Culture — International Co-production Support",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Swiss Federal Office of Culture (BAK/OFC) — Film Support",
        source_url="https://www.bak.admin.ch/bak/de/home/filmfoerderung.html",
        effective_from=None,
        notes=(
            "Swiss BAK provides co-production grants and cultural support for Swiss-participated projects. "
            "Active bilateral co-production treaties: France, Germany, Austria, Italy, Canada. "
            "Geneva (CPH:DOX links), Zürich, Locarno Film Festival (major competition) are key hubs. "
            "Cantonal funds (Geneva, Vaud, Zurich) provide additional support."
        ),
        unknown_fields=[
            "grant_size_range", "co_production_treaty_details", "cantonal_supplement",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MX",
        jurisdiction_name="Mexico",
        program_name="IMCINE — Instituto Mexicano de Cinematografía — FOPROCINE / FIDECINE",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="IMCINE — Instituto Mexicano de Cinematografía",
        source_url="https://www.imcine.gob.mx/apoyos-y-programas/",
        effective_from=None,
        notes=(
            "IMCINE administers FOPROCINE (Fondo para la Producción Cinematográfica de Calidad) for "
            "quality cinema and FIDECINE (Fondo de Inversión y Estímulos al Cine) for industrial cinema. "
            "Mexico City and multiple states offer location incentives. "
            "Separate from EFICINE 10% tax credit. "
            "Mexico co-production treaties with France, Spain, Brazil, Argentina, Canada."
        ),
        unknown_fields=[
            "foprocine_grant_size", "fidecine_loan_terms",
            "co_production_criteria", "programme_current_status",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NO",
        jurisdiction_name="Norway",
        program_name="Norwegian Film Institute (NFI) — Selective Production Grants",
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
        source_title="Norwegian Film Institute (NFI) — Filmstøtten",
        source_url="https://www.nfi.no/stipender-og-stotter/",
        effective_from=None,
        notes=(
            "NFI provides selective (commissioner-based) grants for Norwegian films and international co-productions. "
            "Separate from Norway 25% cash rebate incentive. "
            "Annual cultural grants ~NOK 200-350M across categories. "
            "Fjords, Bergen, Oslo, Northern Lights/Arctic: major location assets."
        ),
        unknown_fields=[
            "grant_size_range", "international_co_production_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FI",
        jurisdiction_name="Finland",
        program_name="Finnish Film Foundation (SES) — Production Grants",
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
        source_title="Finnish Film Foundation (Suomen Elokuvasäätiö / SES)",
        source_url="https://www.ses.fi/tuki-ja-rahoitus/",
        effective_from=None,
        notes=(
            "SES provides selective production grants for Finnish films and international co-productions. "
            "Separate from Business Finland 25% production rebate. "
            "Annual grants ~€20-25M across development, production, and distribution. "
            "Lapland and Helsinki: location assets for winter/Arctic and Nordic productions."
        ),
        unknown_fields=[
            "grant_size_range", "co_production_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="Creative England — Production Finance (English Regions)",
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
        source_title="Creative England — Production Finance",
        source_url="https://www.creativeengland.co.uk/production/",
        effective_from=None,
        notes=(
            "Creative England provides production investment and development grants for film and TV "
            "with significant English regional (outside London) economic benefit. "
            "Equity investment and selective grants. "
            "Separate from BFI Film Fund, Screen Scotland, Screen Wales, and Northern Ireland Screen. "
            "Focus on Midlands, North West, North East, East of England, South West."
        ),
        unknown_fields=[
            "grant_size_range", "equity_vs_grant_structure", "regional_qualifying_areas",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ZA",
        jurisdiction_name="South Africa",
        program_name="Industrial Development Corporation (IDC) — Film and Television Investment Fund",
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
        source_title="IDC South Africa — Creative Industries",
        source_url="https://www.idc.co.za/sector/creative-industries/",
        effective_from=None,
        notes=(
            "IDC provides concessional development finance (loans and equity) for South African film/TV. "
            "Separate from DTI/NFVF 20% production rebate and DAC fund. "
            "Cape Town: Africa's most established international production hub (SA Film Studios, etc.). "
            "IDC focus: South African majority-controlled productions with employment creation."
        ),
        unknown_fields=[
            "loan_size_range", "equity_terms", "south_african_content_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="MA",
        jurisdiction_name="Morocco",
        program_name="Centre Cinématographique Marocain (CCM) — Avance sur Recettes",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Centre Cinématographique Marocain (CCM) — Soutien à la Production",
        source_url="https://www.ccm.ma/fr/productions/soutien-production",
        effective_from=None,
        notes=(
            "CCM administers Avance sur Recettes (advance on receipts) for Moroccan films and co-productions. "
            "Separate from CCM 20-30% foreign production cash rebate. "
            "Moroccan creative participation or co-production required for cultural grants. "
            "Ouarzazate / Atlas Studios remains one of Africa's largest studio complexes."
        ),
        unknown_fields=[
            "grant_size_range", "moroccan_content_criteria", "repayment_terms",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AR",
        jurisdiction_name="Argentina",
        program_name="INCAA — Foprocine Development and Production Grants",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="INCAA — Instituto Nacional de Cine y Artes Audiovisuales",
        source_url="https://www.incaa.gov.ar/ayudas/",
        effective_from=None,
        notes=(
            "INCAA provides development grants and production loans for Argentine films. "
            "Separate from Argentina cash rebate incentive. "
            "Buenos Aires: major Latin American production market. Patagonia, Iguazú location assets. "
            "Active co-production treaties with France, Spain, Italy, Germany, Canada, and Ibermedia."
        ),
        unknown_fields=[
            "grant_size_range", "co_production_treaty_access", "argentina_content_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BR",
        jurisdiction_name="Brazil",
        program_name="ANCINE — FSA (Fundo Setorial do Audiovisual) Development Fund",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="ANCINE Brazil — Fundo Setorial do Audiovisual (FSA)",
        source_url="https://www.gov.br/ancine/pt-br/assuntos/fsa",
        effective_from="2006-01-01",
        notes=(
            "ANCINE administers FSA (Fundo Setorial do Audiovisual) for Brazilian co-productions. "
            "FSA provides development grants, production loans, and completion finance. "
            "São Paulo and Rio de Janeiro: major production markets. Amazon, Pantanal, Nordeste locations. "
            "Co-production treaties with EU, Canada, Argentina, Portugal and Ibermedia access."
        ),
        unknown_fields=[
            "fund_size_current", "fsa_eligibility_criteria", "loan_vs_grant_breakdown",
        ],
    ),

]
