"""
Wave-6 inventory — sub-national completion pass and major gap fills.

Adds:
  - Canada: BC (PSTC 28%), Ontario (OPSTC 21.5%), Quebec (QPRDP 20%)
  - USA: California Film Tax Credit Program 3.0 (20-25%, transferable)
  - Australia: Western Australia (Screenwest 35%), South Australia (SAFC)
  - Germany regional: Berlin-Brandenburg (MBB), Hamburg (HSH), Baden-Württemberg (MFG)
  - Italy regional: Lazio, Sicily, Campania, Tuscany
  - Spain regional: Catalonia (ICEC), Andalusia, Galicia (Agadic), Valencia (IVC)
  - UAE: Abu Dhabi Film Commission (ADFC) 30% rebate (second AE entry, distinct from Dubai)
  - UK: Screen Yorkshire regional fund
  - PT: ICA Production Grants (development stream)

All new entries are DISCOVERY tier — rates and structures from industry knowledge;
primary source documents not yet validated.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


WAVE6_PROGRAMS: list[GlobalProgramEntry] = [

    # ==========================================================================
    # CANADA — Major provinces (critical gap: BC, Ontario, Quebec not yet listed)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="CA-BC",
        jurisdiction_name="Canada — British Columbia",
        program_name="BC Production Services Tax Credit (PSTC)",
        program_type="tax_credit",
        base_rate=0.28,
        max_rate=0.36,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="BC Ministry of Finance — Production Services Tax Credit",
        source_url="https://www2.gov.bc.ca/gov/content/taxes/income-taxes/corporate/credits/film-video",
        effective_from=None,
        notes=(
            "28% refundable credit on qualifying BC labour for foreign service productions. "
            "No cultural test. Regional uplift +6% for non-Metro Vancouver locations. "
            "Stacks additively with federal CPTC (25% on same labour base). "
            "Vancouver is North America's third-largest production market. "
            "Rate 28% from industry knowledge; primary source URL not yet validated against current regulations."
        ),
        unknown_fields=[
            "regional_uplift_exact_conditions", "animation_digital_rate", "atl_qualifying_scope",
            "min_spend_threshold", "processing_timeline",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-ON",
        jurisdiction_name="Canada — Ontario",
        program_name="Ontario Production Services Tax Credit (OPSTC)",
        program_type="tax_credit",
        base_rate=0.215,
        max_rate=0.215,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Ontario Creates — OPSTC Programme",
        source_url="https://ontariocreates.ca/tax-credits/opstc",
        effective_from=None,
        notes=(
            "21.5% refundable credit on qualifying Ontario labour for foreign service productions. "
            "No cultural test. Stacks additively with federal CPTC. "
            "Toronto is Canada's largest production market (Pinewood Toronto, various stage facilities). "
            "Rate 21.5% from industry knowledge; primary source not yet validated."
        ),
        unknown_fields=[
            "exact_qualifying_labour_definition", "atl_treatment", "animation_supplement",
            "annual_programme_cap", "processing_timeline",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-QC",
        jurisdiction_name="Canada — Quebec",
        program_name="Quebec Production Tax Credit — Foreign Productions (QPRDP)",
        program_type="tax_credit",
        base_rate=0.20,
        max_rate=0.28,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Revenu Québec / SODEC — Crédit d'impôt pour productions étrangères (QPRDP)",
        source_url="https://www.revenuquebec.ca/en/businesses/tax-credits/film-production-tax-credit/",
        effective_from=None,
        notes=(
            "20% refundable credit on qualifying Quebec labour for foreign service productions. "
            "28% for animation and VFX. "
            "SODEC (Société de développement des entreprises culturelles) issues the certificate. "
            "Montreal: major animation hub (Disney, Netflix, Framestore VFX). "
            "Stacks additively with federal CPTC. "
            "Rate 20%/28% from industry knowledge; primary source not yet validated."
        ),
        unknown_fields=[
            "animation_uplift_conditions", "min_spend_threshold", "atl_qualifying_scope",
            "processing_timeline",
        ],
    ),

    # ==========================================================================
    # USA — California (major market, critical gap)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="US-CA",
        jurisdiction_name="United States — California",
        program_name="California Film & Television Tax Credit Program 3.0",
        program_type="transferable_tax_credit",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=1_000_000.0,
        annual_cap_usd=330_000_000.0,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="California Film Commission — Tax Credit Program 3.0",
        source_url="https://film.ca.gov/tax-credit/",
        effective_from="2020-07-01",
        notes=(
            "20% base credit on qualified expenditures. Up to 25% for TV series relocating to California, "
            "qualified visual effects, and music score recorded in CA. "
            "Non-refundable — transferable to tax liability buyers (market ~88-93 cents/dollar). "
            "Annual allocation $330M (Program 3.0, effective FY2020-21). "
            "Minimum spend $1M for features, $1M per episode for TV. "
            "Competitive scoring rubric (jobs, local spend, diversity). "
            "Los Angeles is the world's largest entertainment production market. "
            "Rate 20-25% from California Film Commission public documentation."
        ),
        unknown_fields=[
            "exact_qualified_expenditure_definition", "scoring_rubric_current_weights",
            "programme_extension_status_2025_onwards", "vfx_uplift_threshold",
        ],
    ),

    # ==========================================================================
    # AUSTRALIA — Missing states
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="AU-WA",
        jurisdiction_name="Australia — Western Australia",
        program_name="Screenwest WA — Production Attraction Strategy (PAS)",
        program_type="cash_rebate",
        base_rate=0.35,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=1_000_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Screenwest — Production Attraction Strategy",
        source_url="https://www.screenwest.com.au/funding/production-attraction/",
        effective_from=None,
        notes=(
            "35% cash rebate on qualifying Western Australia production expenditure. "
            "Applies to location fees, accommodation, local crew, equipment hired in WA. "
            "Perth, Fremantle, Rottnest Island, Kimberley region: diverse location assets. "
            "Rate 35% from Screenwest public programme summaries; primary PDF not yet validated."
        ),
        unknown_fields=[
            "exact_qualifying_spend_definition", "annual_cap_amount",
            "cultural_test_if_any", "processing_timeline",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-SA",
        jurisdiction_name="Australia — South Australia",
        program_name="South Australian Film Corporation (SAFC) — Production Incentive",
        program_type="cash_rebate",
        base_rate=0.10,
        max_rate=0.15,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000.0,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="South Australian Film Corporation (SAFC) — Production Incentives",
        source_url="https://safilm.com.au/incentives/",
        effective_from=None,
        notes=(
            "SAFC offers cash incentives and production grants for productions spending in SA. "
            "Rate estimated 10-15% on qualifying SA spend; SAFC also provides direct financial grants. "
            "Adelaide Studios (Glenside): major soundstage facility in South Australia. "
            "Rate from industry knowledge; programme structure and primary source not yet validated."
        ),
        unknown_fields=[
            "exact_rate", "programme_structure_grant_vs_rebate",
            "min_spend_exact", "annual_fund_size",
        ],
    ),

    # ==========================================================================
    # GERMANY — Regional funds (Berlin-Brandenburg, Hamburg, Baden-Württemberg)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="DE-BB",
        jurisdiction_name="Germany — Berlin-Brandenburg",
        program_name="Medienboard Berlin-Brandenburg (MBB) — Film Production Fund",
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
        source_title="Medienboard Berlin-Brandenburg — Filmförderung",
        source_url="https://www.medienboard.de/foerderung/film/",
        effective_from=None,
        notes=(
            "Berlin-Brandenburg regional film production fund. "
            "Grants for fiction, documentary, and animation; cultural and regional economic impact criteria. "
            "Spend requirement: typically 150% of grant amount in Berlin-Brandenburg. "
            "Berlin is Germany's largest film market (Berlinale, Babelsberg Studios, UFA). "
            "Annual fund ~€35-40M; per-project amounts vary widely."
        ),
        unknown_fields=[
            "grant_pct_of_budget", "max_grant_per_project",
            "eligibility_criteria_exact", "spend_requirement_pct",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE-HH",
        jurisdiction_name="Germany — Hamburg / Schleswig-Holstein",
        program_name="Film- und Medienstiftung Hamburg Schleswig-Holstein",
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
        source_title="Film- und Medienstiftung Hamburg Schleswig-Holstein — Filmförderung",
        source_url="https://www.filmfoerderung.de",
        effective_from=None,
        notes=(
            "Hamburg/Schleswig-Holstein joint regional film fund. "
            "Grants for feature films, series, documentaries with regional economic impact. "
            "Hamburg: major port city, diverse location assets, Spiegel-Verlag backdrop. "
            "Spend requirement typically 150-175% of fund grant in the region."
        ),
        unknown_fields=[
            "grant_rate", "max_grant_per_project", "eligibility_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE-BW",
        jurisdiction_name="Germany — Baden-Württemberg",
        program_name="MFG Medien- und Filmgesellschaft Baden-Württemberg",
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
        source_title="MFG Baden-Württemberg — Filmförderung",
        source_url="https://www.mfg.de/foerderung/film/",
        effective_from=None,
        notes=(
            "Baden-Württemberg regional film fund; based in Stuttgart. "
            "Grants for film/TV with BW regional economic and cultural impact. "
            "Stuttgart, Black Forest, Lake Constance: diverse location assets. "
            "Annual fund ~€6-8M."
        ),
        unknown_fields=[
            "grant_rate", "max_grant_amount", "eligibility_criteria",
        ],
    ),

    # ==========================================================================
    # ITALY — Regional programs (Lazio, Sicily, Campania, Tuscany)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="IT-LAZ",
        jurisdiction_name="Italy — Lazio (Rome)",
        program_name="Lazio Cinema International — Film Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Lazio Cinema International / Lazio Innova — Film Fund",
        source_url="https://www.lazioinnova.it/finanziamenti/incentivi-alle-imprese/lazio-cinema-international/",
        effective_from=None,
        notes=(
            "Lazio (Rome) regional film incentive. Up to 40% cash rebate on qualifying Lazio expenditure. "
            "Stacks with national Italian tax credit for foreign productions (40%). "
            "Rome: Cinecittà Studios, ENI Tor Tre Teste and other major facilities. "
            "Administered by Lazio Innova / Regione Lazio. "
            "Rate up to 40% from industry reports; primary programme document not yet validated."
        ),
        unknown_fields=[
            "exact_rate_and_tiers", "min_spend", "annual_fund_size",
            "application_process", "competitive_vs_formula",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT-SIC",
        jurisdiction_name="Italy — Sicily",
        program_name="Sicilia Film Commission — Film Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Sicilia Film Commission — Incentivi",
        source_url="https://www.siciliafilmcommission.it/incentivi/",
        effective_from=None,
        notes=(
            "Sicily regional film fund. Production grants for qualifying productions in Sicily. "
            "Up to 25% on qualifying Sicily expenditure. "
            "Strong location assets: Agrigento temples, Palermo, Taormina, Etna. "
            "Stacks with national Italian tax credit."
        ),
        unknown_fields=[
            "exact_rate", "min_spend", "annual_fund_size", "eligibility_criteria",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT-CAM",
        jurisdiction_name="Italy — Campania (Naples)",
        program_name="Film Commission Campania — Production Fund",
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
        source_title="Film Commission Campania",
        source_url="https://www.filmcommissioncampania.it",
        effective_from=None,
        notes=(
            "Campania (Naples) regional production support fund. "
            "Naples, Amalfi Coast, Pompeii, Herculaneum: iconic Italian locations. "
            "Grants for qualifying productions with Campania regional spend."
        ),
        unknown_fields=[
            "grant_rate", "min_spend", "programme_size", "application_process",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT-TOS",
        jurisdiction_name="Italy — Tuscany",
        program_name="Film Commission Toscana — Production Support",
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
        source_title="Film Commission Toscana / Regione Toscana",
        source_url="https://www.filmcommissiontoscana.it",
        effective_from=None,
        notes=(
            "Tuscany (Florence, Siena, Chianti, Lucca) regional production support. "
            "Grants for qualifying productions with Tuscany regional spend. "
            "Strong international location track record (The English Patient, Hannibal, many others)."
        ),
        unknown_fields=[
            "grant_rate", "min_spend", "programme_size",
        ],
    ),

    # ==========================================================================
    # SPAIN — Regional programs (Catalonia, Andalusia, Galicia, Valencia)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="ES-CAT",
        jurisdiction_name="Spain — Catalonia",
        program_name="ICEC — Institut Català de les Empreses Culturals Film Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.25,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="ICEC — Institut Català de les Empreses Culturals",
        source_url="https://icec.gencat.cat/ca/ajuts_i_subvencions/cinema/",
        effective_from=None,
        notes=(
            "Catalonia (Barcelona) regional film production support via ICEC. "
            "Selective grants for Catalan cultural projects and international co-productions. "
            "Barcelona, Costa Brava, Pyrenees: highly sought international locations. "
            "Stacks with national Spanish tax incentive (mainland 30% or Canary Islands 50%)."
        ),
        unknown_fields=[
            "grant_rate_pct", "min_spend", "language_requirement_scope",
            "international_co_production_rules", "annual_fund_size",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ES-AND",
        jurisdiction_name="Spain — Andalusia",
        program_name="Andalucia Film Commission — Audiovisual Production Incentive",
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
        source_title="Andalucia Film Commission (AFC)",
        source_url="https://www.andaluciafilm.com",
        effective_from=None,
        notes=(
            "Andalusia regional film commission incentives and production support. "
            "Seville, Granada, Almería (desert film location), Cádiz, Málaga. "
            "Almería: birthplace of Spaghetti Westerns (Sergio Leone); still heavily used. "
            "FAAC coordinates production services and incentive facilitation."
        ),
        unknown_fields=[
            "programme_structure", "grant_rate", "min_spend", "application_process",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ES-GAL",
        jurisdiction_name="Spain — Galicia",
        program_name="Agadic — Axencia Galega das Industrias Culturais Film Production Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=0.35,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Agadic — Axencia Galega das Industrias Culturais",
        source_url="https://agadic.xunta.gal/gl/axudas",
        effective_from=None,
        notes=(
            "Galicia (Santiago de Compostela, Atlantic coast, Rías Baixas) regional film production grants. "
            "Agadic administers subsidy support for projects with Galician cultural/economic benefit. "
            "Up to 35% subsidy on qualifying Galician spend (market knowledge). "
            "Galician language and/or regional economic impact criteria apply. "
            "Stacks with national Spanish tax incentive."
        ),
        unknown_fields=[
            "exact_rate", "min_spend", "language_requirement_exact",
            "annual_fund_size",
        ],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ES-VAL",
        jurisdiction_name="Spain — Valencia",
        program_name="Institut Valencià de Cultura (IVC) — Audiovisual Production Fund",
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
        source_title="Institut Valencià de Cultura (IVC)",
        source_url="https://ivc.gva.es/va/produccio-audiovisual",
        effective_from=None,
        notes=(
            "Valencia Community (Valencia, Alicante, Castellón) audiovisual production support. "
            "Mediterranean coast, historic city of Valencia, rice paddy landscapes. "
            "IVC funds projects with Valencian cultural or economic benefit. "
            "Stacks with national Spanish incentive."
        ),
        unknown_fields=[
            "programme_structure", "grant_rate", "eligibility_criteria",
        ],
    ),

    # ==========================================================================
    # UAE — Abu Dhabi (second AE entry, distinct from Dubai Film Commission)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="AE",
        jurisdiction_name="United Arab Emirates — Abu Dhabi",
        program_name="Abu Dhabi Film Commission (ADFC) — Production Rebate",
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
        source_title="Abu Dhabi Film Commission (ADFC) — Production Rebate",
        source_url="https://www.abudhabifilmcommission.ae/en/incentives",
        effective_from=None,
        notes=(
            "Abu Dhabi Film Commission offers ~30% production rebate on qualifying Abu Dhabi expenditure. "
            "Separate from Dubai Film Commission (also AE). "
            "Location assets: AlUla-adjacent desert, Abu Dhabi modern architecture, Ferrari World, "
            "Warner Bros. World, Yas Island, Liwa desert, Empty Quarter edges. "
            "Image Nation Abu Dhabi is the major co-financing entity. "
            "Rate 30% from market knowledge; primary official programme document not yet validated."
        ),
        unknown_fields=[
            "exact_rate", "min_spend", "programme_structure",
            "content_restrictions", "processing_timeline",
        ],
    ),

    # ==========================================================================
    # UK — Screen Yorkshire (additional regional fund)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="GB-YRK",
        jurisdiction_name="United Kingdom — Yorkshire",
        program_name="Screen Yorkshire — Yorkshire Content Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Screen Yorkshire — Yorkshire Content Fund",
        source_url="https://www.screenyorkshire.co.uk/funding/",
        effective_from=None,
        notes=(
            "Screen Yorkshire administers the Yorkshire Content Fund for film and TV productions. "
            "Selective grants for projects with significant Yorkshire production spend. "
            "Spend requirement: significant Yorkshire expenditure (typically 50%+ of fund in region). "
            "Yorkshire: major UK location (Emmerdale, Happy Valley, Last Tango in Halifax, many features). "
            "Stacks with UK AVEC."
        ),
        unknown_fields=[
            "grant_rate", "max_grant_amount", "spend_in_region_requirement",
        ],
    ),

    # ==========================================================================
    # PORTUGAL — ICA Production Grants (second PT entry, distinct from cash rebate)
    # ==========================================================================

    GlobalProgramEntry(
        jurisdiction_code="PT",
        jurisdiction_name="Portugal",
        program_name="ICA — Instituto do Cinema e Audiovisual Selective Production Grants",
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
        source_title="ICA Instituto do Cinema e do Audiovisual — Apoios à Produção",
        source_url="https://www.ica-ip.pt/pt/apoios/producao-audiovisual/",
        effective_from=None,
        notes=(
            "ICA administers selective production grants for Portuguese films and international co-productions. "
            "Separate from Portugal Film Commission 25% cash rebate. "
            "Lisbon: growing international hub (Netflix Originals, Amazon Series). "
            "Portugal co-production treaties with Brazil, CPLP members. "
            "Annual fund: ~€7-10M allocated across categories."
        ),
        unknown_fields=[
            "grant_size_range", "cultural_criteria", "co_production_terms",
        ],
    ),

]
