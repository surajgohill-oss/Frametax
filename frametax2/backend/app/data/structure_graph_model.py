from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GraphEdge:
    source_type: str   # "program" | "treaty" | "fund" | "region" | "broadcaster"
    source_slug: str
    edge_type: str     # "unlocks" | "requires" | "improves" | "reduces" | "incompatible_with" |
    #                    "enables" | "complements" | "alternative_to" | "blocks" |
    #                    "majority_only" | "minority_only" | "depends_on" |
    #                    "service_only" | "regional_only" | "national_only" |
    #                    "broadcaster_only" | "fund_only"
    target_type: str   # "program" | "treaty" | "fund" | "test" | "region" | "broadcaster"
    target_slug: str
    condition: str | None = None
    magnitude: float | None = None
    notes: str = ""


_EDGES: list[GraphEdge] = [

    # -------------------------------------------------------------------------
    # Treaty → Program (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "uk_avec",
              condition="Canadian majority co-production"),
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="UK majority co-production"),

    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "ie_section_481"),

    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "fr_trip"),

    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "au_producer_offset"),

    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "de_dfff"),

    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "au_producer_offset"),

    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "it_tax_credit_foreign"),
    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "fr_trip"),

    # -------------------------------------------------------------------------
    # Treaty → Fund (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "eu_eurimages", "unlocks", "fund", "eu_eurimages",
              condition="Member country eligibility for Eurimages grant"),
    GraphEdge("treaty", "ibermedia_programme", "unlocks", "fund", "ibermedia_programme",
              condition="Member country eligibility for Ibermedia fund"),
    GraphEdge("treaty", "eu_european_convention", "unlocks", "fund", "eu_european_convention",
              condition="Signatory country access to European Convention co-production framework"),

    # -------------------------------------------------------------------------
    # Program → Test (requires)
    # -------------------------------------------------------------------------
    GraphEdge("program", "uk_avec", "requires", "test", "uk_bfi_cultural_test"),
    GraphEdge("program", "ca_federal_cptc", "requires", "test", "ca_content_test"),
    GraphEdge("program", "ca_cmf", "requires", "test", "ca_content_test"),
    GraphEdge("program", "au_producer_offset", "requires", "test", "au_content_test"),
    GraphEdge("program", "eu_eurimages", "requires", "test", "eu_eurimages_test"),
    GraphEdge("program", "ibermedia_programme", "requires", "test", "ibermedia_test"),
    GraphEdge("program", "fr_cnc_production", "requires", "test", "fr_cnc_cultural_test"),
    GraphEdge("program", "eu_media_fund", "requires", "test", "eu_european_convention_test"),

    # -------------------------------------------------------------------------
    # Program → Program (improves)
    # -------------------------------------------------------------------------
    GraphEdge("program", "eu_eurimages", "improves", "program", "at_ofi_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Austrian partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "pl_pisf_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Polish partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "cz_czech_film_fund",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Czech partners"),
    GraphEdge("program", "eu_eurimages", "improves", "program", "hu_nfi_grants",
              magnitude=0.2,
              notes="Eurimages membership unlocks joint applications with Hungarian partners"),

    GraphEdge("program", "film_i_vast", "improves", "program", "se_svt",
              magnitude=0.15,
              notes="Regional Swedish production attracts broadcaster interest"),

    GraphEdge("program", "ca_cmf", "improves", "program", "ca_federal_cptc",
              magnitude=0.1,
              notes="Certified Canadian content qualifies for both CMF and CPTC"),
    GraphEdge("program", "ca_bell_fund", "improves", "program", "ca_cmf",
              magnitude=0.1),

    # -------------------------------------------------------------------------
    # Program → Program (reduces)
    # -------------------------------------------------------------------------
    GraphEdge("program", "ie_screen_ireland_dev", "reduces", "program", "ie_section_481",
              condition="Screen Ireland development grants are govt assistance — reduces Section 481 qualifying basis",
              magnitude=0.05),
    GraphEdge("program", "gb_lon_film_london", "reduces", "program", "uk_avec",
              condition="Film London grant reduces AVEC qualifying expenditure basis",
              magnitude=0.05),
    GraphEdge("program", "au_tourism_film", "reduces", "program", "au_producer_offset",
              condition="Tourism Australia grant may constitute govt assistance reducing QAPE",
              magnitude=0.02),
    GraphEdge("program", "ca_telefilm_export", "reduces", "program", "ca_federal_cptc",
              condition="Telefilm export grant is govt assistance potentially reducing CPTC labour basis",
              magnitude=0.03),
    GraphEdge("program", "au_pdv_offset", "reduces", "program", "au_location_offset",
              condition="PDV Offset is govt assistance — reduces QAPE for Location Offset if combined",
              magnitude=0.10),
    GraphEdge("program", "au_pdv_offset", "reduces", "program", "au_producer_offset",
              condition="PDV Offset is govt assistance — reduces QAPE for Producer Offset if combined",
              magnitude=0.10),
    GraphEdge("program", "fr_cnc_animation", "reduces", "program", "fr_trip",
              condition="CNC animation fund is govt assistance reducing TRIP qualifying expenditure",
              magnitude=0.05),

    # -------------------------------------------------------------------------
    # Program → Program (incompatible_with)
    # -------------------------------------------------------------------------
    GraphEdge("program", "au_location_offset", "incompatible_with", "program", "au_producer_offset",
              notes="Same production cannot claim both — different offset tracks"),
    GraphEdge("program", "se_sk_film_skane", "incompatible_with", "program", "se_ab_filmstockholm",
              notes="Swedish regional funds mutually exclusive for same spend"),
    GraphEdge("program", "dk_cph_film_fund", "incompatible_with", "program", "dk_fyn_film",
              notes="Danish regional funds mutually exclusive for same spend"),
    GraphEdge("program", "ae_dxb_dpi", "incompatible_with", "program", "ae_adfc_rebate",
              notes="Dubai and Abu Dhabi rebates cannot both apply to the same spend"),

    # -------------------------------------------------------------------------
    # Broadcaster → Incentive (improves)
    # -------------------------------------------------------------------------
    GraphEdge("program", "gb_bbc_films", "improves", "program", "uk_avec",
              condition="BBC co-production strengthens BFI cultural test British creative element score"),
    GraphEdge("program", "gb_film4", "improves", "program", "uk_avec",
              condition="BBC co-production strengthens BFI cultural test British creative element score"),
    GraphEdge("program", "fr_canal_plus", "improves", "program", "fr_trip",
              condition="CANAL+ co-production evidence of French creative commitment"),
    GraphEdge("program", "se_svt", "improves", "program", "no_nfi_grants",
              condition="SVT/NRK broadcaster co-production demonstrates Nordic market reach; improves NFI application"),
    GraphEdge("program", "no_nrk", "improves", "program", "no_nfi_grants",
              condition="SVT/NRK broadcaster co-production demonstrates Nordic market reach; improves NFI application"),
    GraphEdge("program", "dk_dr", "improves", "program", "dk_dfi_support"),
    GraphEdge("program", "fi_yle", "improves", "program", "fi_ses_grants"),

    # -------------------------------------------------------------------------
    # Regional → National (requires / improves)
    # -------------------------------------------------------------------------
    GraphEdge("region", "no_vgn_viken", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_rog_vestnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_tro_nordnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),
    GraphEdge("region", "no_inl_midtnorsk", "requires", "program", "no_nfi_grants",
              condition="Viken Film typically requires NFI national project to qualify for regional co-funding"),

    GraphEdge("region", "film_i_vast", "improves", "program", "se_svt",
              condition="Västra Götaland-based production demonstrates regional cultural value"),
    GraphEdge("region", "gb_lon_film_london", "improves", "program", "uk_avec",
              condition="Film London increases AVEC qualifying UK spend concentration in London"),
    GraphEdge("region", "gb_sct_screen_production", "improves", "program", "uk_avec"),
    GraphEdge("region", "gb_wls_film_fund", "improves", "program", "uk_avec"),

    GraphEdge("region", "au_vic_film_victoria", "improves", "program", "au_producer_offset",
              condition="VicScreen support increases Australian content credentials"),
    GraphEdge("region", "au_tas_screen", "improves", "program", "au_producer_offset"),
    GraphEdge("region", "au_nt_territory", "improves", "program", "au_producer_offset"),

    # -------------------------------------------------------------------------
    # Streamer → Incentive (unlocks)
    # -------------------------------------------------------------------------
    GraphEdge("program", "streamer_uk_local", "unlocks", "program", "uk_avec",
              condition="Content commissioned to satisfy UK streamer obligation typically qualifies for AVEC"),
    GraphEdge("program", "streamer_uk_local", "unlocks", "program", "gb_bbc_films",
              condition="Streamer-commissioned content may include BBC co-production"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Broadcaster → Incentive (enables / unlocks)
    # -------------------------------------------------------------------------
    # Ireland
    GraphEdge("program", "rte_drama_fund", "enables", "program", "ie_section_481",
              condition="RTE broadcaster commitment unlocks Section 481 for co-produced Irish drama"),
    GraphEdge("program", "virgin_media_tv_fund", "enables", "program", "ie_section_481",
              condition="Virgin Media Ireland commitment supports Section 481 qualifying Irish content"),
    GraphEdge("program", "rte_drama_fund", "improves", "program", "eu_eurimages",
              condition="Irish broadcaster involvement strengthens Eurimages application cultural credibility"),

    # UK
    GraphEdge("program", "gb_bbc_films", "enables", "program", "uk_avec"),
    GraphEdge("program", "gb_film4", "enables", "program", "uk_avec"),
    GraphEdge("program", "sky_uk_drama", "enables", "program", "uk_avec"),
    GraphEdge("program", "channel_4_indie_growth", "enables", "program", "uk_avec"),
    GraphEdge("program", "gb_bbc_films", "improves", "program", "gb_sct_screen_production",
              condition="BBC co-production increases Scottish content credentials"),

    # France
    GraphEdge("program", "fr_canal_plus", "enables", "program", "fr_cnc_production",
              condition="CANAL+ co-production triggers CNC broadcaster levy obligation"),
    GraphEdge("program", "france_televisions_fund", "enables", "program", "fr_cnc_production",
              condition="France Télévisions commitment qualifies production as French broadcast content"),
    GraphEdge("program", "fr_canal_plus", "unlocks", "program", "fr_trip",
              condition="Canal+ co-production triggers French Tax Rebate for International"),
    GraphEdge("program", "france_televisions_fund", "unlocks", "program", "fr_trip"),

    # Canada
    GraphEdge("program", "cbc_original", "enables", "program", "ca_federal_cptc",
              condition="CBC co-production certifies Canadian content; CPTC eligible"),
    GraphEdge("program", "cbc_original", "enables", "program", "ca_cmf",
              condition="CBC broadcast licence triggers CMF eligibility"),
    GraphEdge("program", "bravo_factual", "enables", "program", "ca_cmf"),
    GraphEdge("program", "ca_bell_fund", "enables", "program", "ca_federal_cptc",
              condition="Bell Fund certification implies Canadian content qualification"),
    GraphEdge("program", "cbc_original", "improves", "program", "ca_telefilm_export",
              condition="CBC involvement improves Telefilm export support eligibility"),

    # Australia
    GraphEdge("program", "abc_television_fund", "enables", "program", "au_producer_offset",
              condition="ABC co-production confirms Australian content status"),
    GraphEdge("program", "abc_television_fund", "improves", "program", "au_pdv_offset"),
    GraphEdge("program", "sbs_co_production", "enables", "program", "au_producer_offset"),

    # Nordics
    GraphEdge("program", "se_svt", "enables", "program", "se_goteborg_fund"),
    GraphEdge("program", "no_nrk", "enables", "program", "no_nfi_grants"),
    GraphEdge("program", "fi_yle", "enables", "program", "fi_ses_grants"),
    GraphEdge("program", "dk_dr", "enables", "program", "dk_dfi_support"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Program ↔ Program (complements)
    # -------------------------------------------------------------------------
    # UK stack
    GraphEdge("program", "uk_avec", "complements", "program", "gb_sct_screen_production",
              notes="Scottish production can access both AVEC and Screen Scotland support"),
    GraphEdge("program", "uk_avec", "complements", "program", "gb_wls_film_fund",
              notes="Welsh production accesses both AVEC and Wales Film Fund"),
    GraphEdge("program", "uk_avec", "complements", "program", "gb_lon_film_london",
              notes="London-set production can layer Film London on top of AVEC"),
    GraphEdge("program", "uk_avec", "complements", "program", "gb_bbc_films"),
    GraphEdge("program", "gb_sct_screen_production", "complements", "program", "gb_bbc_films",
              notes="Screen Scotland + BBC joint development pathway"),

    # Ireland stack
    GraphEdge("program", "ie_section_481", "complements", "program", "rte_drama_fund"),
    GraphEdge("program", "ie_section_481", "complements", "program", "eu_eurimages",
              notes="Section 481 + Eurimages is a common Irish-European co-production structure"),

    # France stack
    GraphEdge("program", "fr_trip", "complements", "program", "fr_cnc_production"),
    GraphEdge("program", "fr_trip", "complements", "program", "eu_eurimages"),
    GraphEdge("program", "fr_cnc_animation", "complements", "program", "fr_trip",
              notes="CNC animation + TRIP combination for animated features"),
    GraphEdge("program", "fr_trip", "complements", "program", "eu_media_fund"),

    # Canada stack
    GraphEdge("program", "ca_federal_cptc", "complements", "program", "ca_cmf"),
    GraphEdge("program", "ca_federal_cptc", "complements", "program", "ca_bc_pstc",
              notes="Federal CPTC + BC PSTC common BC-based production stack"),
    GraphEdge("program", "ca_federal_cptc", "complements", "program", "ca_on_ocase",
              notes="Federal CPTC + Ontario OCASE for Ontario VFX/animation"),
    GraphEdge("program", "ca_federal_cptc", "complements", "program", "ca_qc_sodec",
              notes="Federal CPTC + SODEC for Quebec-based productions"),
    GraphEdge("program", "ca_cmf", "complements", "program", "ca_bell_fund"),

    # Australia stack
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_vic_film_victoria",
              notes="Producer Offset + VicScreen support common Melbourne/Victoria stack"),
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_qld_screen",
              notes="Producer Offset + Screen Queensland common stack"),
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_location_incentive",
              notes="Producer Offset + Location Incentive for large international co-productions"),
    GraphEdge("program", "au_pdv_offset", "complements", "program", "au_vic_film_victoria",
              notes="PDV Offset + VicScreen for post/VFX work"),

    # Germany stack
    GraphEdge("program", "de_dfff", "complements", "program", "de_bavarian_film_fund",
              notes="Federal DFFF + Bavarian FFB combination for Munich-based productions"),
    GraphEdge("program", "de_dfff", "complements", "program", "de_mbb_berlin",
              notes="Federal DFFF + MBB for Berlin-based productions"),
    GraphEdge("program", "de_dfff", "complements", "program", "eu_eurimages"),
    GraphEdge("program", "de_dfff", "complements", "program", "eu_media_fund"),

    # Hungary stack
    GraphEdge("program", "hu_nfi_grants", "complements", "program", "eu_eurimages"),
    GraphEdge("program", "hu_nfi_grants", "complements", "program", "eu_media_fund"),

    # Iberia
    GraphEdge("program", "es_icaa_grants", "complements", "program", "ibermedia_programme"),
    GraphEdge("program", "pt_ica_grants", "complements", "program", "ibermedia_programme"),
    GraphEdge("program", "es_icaa_grants", "complements", "program", "eu_eurimages"),
    GraphEdge("program", "pt_ica_grants", "complements", "program", "eu_eurimages"),

    # Nordics
    GraphEdge("program", "no_nfi_grants", "complements", "program", "nordic_ftvf"),
    GraphEdge("program", "dk_dfi_support", "complements", "program", "nordic_ftvf"),
    GraphEdge("program", "fi_ses_grants", "complements", "program", "nordic_ftvf"),
    GraphEdge("program", "se_goteborg_fund", "complements", "program", "nordic_ftvf"),
    GraphEdge("program", "no_nfi_grants", "complements", "program", "eu_eurimages"),

    # EU supranational
    GraphEdge("program", "eu_eurimages", "complements", "program", "eu_media_fund"),
    GraphEdge("program", "eu_eurimages", "complements", "program", "eu_creative_europe"),
    GraphEdge("program", "eu_media_fund", "complements", "program", "eu_creative_europe"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Program → Program (alternative_to)
    # -------------------------------------------------------------------------
    GraphEdge("program", "au_location_offset", "alternative_to", "program", "au_producer_offset",
              notes="Productions choose one track; Location Offset for large non-Australian productions"),
    GraphEdge("program", "ca_federal_cptc", "alternative_to", "program", "ca_cmpa_foreign",
              notes="Foreign production in Canada can use either CPTC (Canadian content) or CMPA foreign services path"),
    GraphEdge("program", "uk_avec", "alternative_to", "program", "uk_hvc",
              notes="AVEC for qualifying British content; HVC for high-value foreign productions"),
    GraphEdge("program", "ie_section_481", "alternative_to", "program", "ie_section_481_tv",
              notes="Section 481 film track vs. TV track (same scheme, different qualifying criteria)"),
    GraphEdge("program", "de_dfff_1", "alternative_to", "program", "de_dfff_2",
              notes="DFFF I (automatisch) vs DFFF II (selektiv) — same fund, different access paths"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Program → Program (majority_only / minority_only)
    # -------------------------------------------------------------------------
    # Majority-only programs (minority co-producer cannot be primary applicant)
    GraphEdge("program", "au_producer_offset", "majority_only", "program", "au_producer_offset",
              notes="Producer Offset: Australian majority producer is the applicant; minority co-producers access own national programs"),
    GraphEdge("program", "ca_federal_cptc", "majority_only", "program", "ca_federal_cptc",
              notes="CPTC: Canadian majority required; minority partner accesses own national program"),
    GraphEdge("program", "no_nfi_grants", "majority_only", "program", "no_nfi_grants",
              notes="NFI: Norwegian majority required for full access; minority co-producers apply to NFI Minority"),

    # Minority-accessible programs
    GraphEdge("program", "eu_eurimages", "minority_only", "program", "eu_eurimages",
              condition="Any member country co-producer can apply regardless of majority/minority status",
              notes="Eurimages does not require majority status — any qualifying co-producer can apply"),
    GraphEdge("program", "nordic_ftvf", "minority_only", "program", "nordic_ftvf",
              notes="Nordic Film & TV Fund: any Nordic co-producer regardless of majority/minority"),
    GraphEdge("program", "ibermedia_programme", "minority_only", "program", "ibermedia_programme",
              notes="Ibermedia: any Iberoamerican member co-producer can apply"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Program → Program (blocks)
    # -------------------------------------------------------------------------
    GraphEdge("program", "uk_hvc", "blocks", "program", "uk_avec",
              condition="Same production cannot use both AVEC and HVC — must choose one track",
              notes="AVEC = qualifying British content; HVC = high-value foreign — mutually exclusive"),
    GraphEdge("program", "ca_cmpa_foreign", "blocks", "program", "ca_federal_cptc",
              condition="Foreign service production under CMPA foreign track is not eligible for Canadian content CPTC"),
    GraphEdge("program", "au_location_offset", "blocks", "program", "au_pdv_offset",
              condition="AU Location Offset and PDV Offset cannot both apply to the same qualifying expenditure"),
    GraphEdge("program", "us_georgia_eitc", "blocks", "program", "us_ny_eitc",
              condition="Cannot claim both Georgia and New York credits on the same spend"),
    GraphEdge("program", "us_la_production_credit", "blocks", "program", "us_ny_eitc",
              condition="Louisiana and New York credits cannot apply to the same production spend"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Treaty → Program (extended bilateral coverage)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "uk-fr-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-fr-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "uk-de-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-de-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "uk-it-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-it-bilateral", "unlocks", "program", "it_tax_credit_foreign"),
    GraphEdge("treaty", "uk-nz-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate"),
    GraphEdge("treaty", "uk-za-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "uk-za-bilateral", "unlocks", "program", "za_nfvf_fund"),
    GraphEdge("treaty", "ca-uk-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-uk-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "ca-de-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-de-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "ca-it-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-it-bilateral", "unlocks", "program", "it_tax_credit_foreign"),
    GraphEdge("treaty", "ca-be-bilateral", "unlocks", "program", "ca_federal_cptc"),
    GraphEdge("treaty", "ca-be-bilateral", "unlocks", "program", "be_tax_shelter"),
    GraphEdge("treaty", "au-uk-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "au-uk-bilateral", "unlocks", "program", "uk_avec"),
    GraphEdge("treaty", "au-fr-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "au-fr-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "au-de-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "au-de-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate"),
    GraphEdge("treaty", "au-it-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "fr-be-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "fr-be-bilateral", "unlocks", "program", "be_tax_shelter"),
    GraphEdge("treaty", "de-at-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "de-at-bilateral", "unlocks", "program", "at_ofi_grants"),
    GraphEdge("treaty", "de-pl-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "de-pl-bilateral", "unlocks", "program", "pl_pisf_grants"),
    GraphEdge("treaty", "de-hu-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "de-hu-bilateral", "unlocks", "program", "hu_nfi_grants"),
    GraphEdge("treaty", "de-cz-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "de-cz-bilateral", "unlocks", "program", "cz_czech_film_fund"),
    GraphEdge("treaty", "kr-fr-bilateral", "unlocks", "program", "kr_kofic_production"),
    GraphEdge("treaty", "kr-fr-bilateral", "unlocks", "program", "fr_trip"),
    GraphEdge("treaty", "kr-de-bilateral", "unlocks", "program", "kr_kofic_production"),
    GraphEdge("treaty", "kr-de-bilateral", "unlocks", "program", "de_dfff"),
    GraphEdge("treaty", "kr-au-bilateral", "unlocks", "program", "kr_kofic_production"),
    GraphEdge("treaty", "kr-au-bilateral", "unlocks", "program", "au_producer_offset"),
    GraphEdge("treaty", "sa-ksa-bilateral", "unlocks", "program", "sa_sfc_fund"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Tourism / Workforce / Export → Tax Credit (complements)
    # -------------------------------------------------------------------------
    GraphEdge("program", "au_tourism_australia", "complements", "program", "au_producer_offset",
              notes="Tourism Australia destination marketing complements Production Offset structure"),
    GraphEdge("program", "nz_tourism_nz", "complements", "program", "nz_screen_production_rebate"),
    GraphEdge("program", "ie_tourism_ireland", "complements", "program", "ie_section_481"),
    GraphEdge("program", "jo_rfc_tourism", "complements", "program", "jo_rfc_rebate"),
    GraphEdge("program", "ma_ccm_tourism", "complements", "program", "ma_ccm_rebate"),
    GraphEdge("program", "gb_screenskills", "complements", "program", "uk_avec",
              notes="ScreenSkills-trained crew satisfies BFI crew certification requirements"),
    GraphEdge("program", "au_screen_talent", "complements", "program", "au_producer_offset"),
    GraphEdge("program", "ie_screen_ireland_dev", "complements", "program", "ie_section_481"),
    GraphEdge("program", "gb_bfi_international", "complements", "program", "uk_avec"),
    GraphEdge("program", "ca_telefilm_export", "complements", "program", "ca_federal_cptc"),
    GraphEdge("program", "kr_kofic_export", "complements", "program", "kr_kofic_production"),
    GraphEdge("program", "de_german_films", "complements", "program", "de_dfff"),
    GraphEdge("program", "fr_unifrance", "complements", "program", "fr_trip"),
    GraphEdge("program", "it_anica_export", "complements", "program", "it_tax_credit_foreign"),

    # -------------------------------------------------------------------------
    # F1 EXPANSION: Program → Cultural Test (requires, additional programs)
    # -------------------------------------------------------------------------
    GraphEdge("program", "ie_section_481", "requires", "test", "ie_section_481_test"),
    GraphEdge("program", "fr_trip", "requires", "test", "fr_cnc_cultural_test"),
    GraphEdge("program", "ibermedia_programme", "requires", "test", "ibermedia_test"),
    GraphEdge("program", "nordic_ftvf", "requires", "test", "nordic_content_test",
              notes="Nordic FTVF requires Nordic cultural content threshold"),
    GraphEdge("program", "nl_hbf", "requires", "test", "global_south_content_test",
              notes="Hubert Bals Fund requires Global South subject matter"),
    GraphEdge("program", "dk_dfi_support", "requires", "test", "dk_content_test"),
    GraphEdge("program", "no_nfi_grants", "requires", "test", "no_content_test"),
    GraphEdge("program", "fi_ses_grants", "requires", "test", "fi_content_test"),
    GraphEdge("program", "se_goteborg_fund", "requires", "test", "se_content_test"),
    GraphEdge("program", "kr_kofic_production", "requires", "test", "kr_content_test"),
    GraphEdge("program", "au_pdv_offset", "requires", "test", "au_content_test"),

    # =========================================================================
    # F1 EXPANSION: 150+ new edges
    # New edge types: blocks, enables, alternative_to, complements (extended),
    #                 majority_only, minority_only
    # =========================================================================

    # Program ↔ Program: Tax credit ↔ Grant compatibility
    GraphEdge("program", "uk_avec", "complements", "program", "uk_bfi_production",
              notes="BFI AVEC rebate pairs well with BFI production fund for high-end UK drama"),
    GraphEdge("program", "uk_avec", "enables", "program", "bbc_drama_production",
              notes="AVEC certification satisfies BBC broadcaster production criteria"),
    GraphEdge("program", "uk_avec", "enables", "program", "sky_uk_drama",
              notes="AVEC-certified productions are preferred by Sky UK commissioning"),
    GraphEdge("program", "uk_avec", "complements", "program", "uk_screen_scotland",
              notes="Screen Scotland fund complements AVEC for Scottish-set productions"),
    GraphEdge("program", "uk_avec", "complements", "program", "gb_bbc_films",
              notes="BBC Films co-finance often layers with AVEC rebate"),
    GraphEdge("program", "uk_avec", "complements", "program", "gb_film4",
              notes="Film4 co-finance typically structures with AVEC UK spend"),
    GraphEdge("program", "uk_avec", "alternative_to", "program", "ie_section_481",
              notes="IE Section 481 is the primary alternative UK producers use for Irish shoots"),
    GraphEdge("program", "uk_avec", "blocks", "program", "ie_section_481",
              condition="same_spend_claimed",
              notes="Cannot double-claim same qualifying spend under both UK AVEC and IE S481"),

    # IE Section 481 ↔ Broadcaster funds
    GraphEdge("program", "ie_section_481", "enables", "program", "rte_drama_fund",
              notes="Section 481 qualification opens RTE Drama Fund eligibility"),
    GraphEdge("program", "ie_section_481", "enables", "program", "virgin_media_tv_fund",
              notes="S481 project qualification preferred by Virgin Media Television Ireland"),
    GraphEdge("program", "rte_drama_fund", "improves", "program", "ie_section_481",
              notes="RTE broadcaster commitment improves S481 cultural test score"),
    GraphEdge("program", "virgin_media_tv_fund", "improves", "program", "ie_section_481",
              notes="Virgin Media commitment improves Irish cultural test score"),
    GraphEdge("program", "ie_section_481", "complements", "program", "uk_avec",
              notes="Irish post-production under S481 can stack with UK main shoot under AVEC"),
    GraphEdge("program", "ie_section_481", "majority_only", "program", "ie_section_481",
              notes="Section 481 full rate only available to Irish majority co-productions"),

    # FR CNC / TRIP ↔ Broadcaster funds
    GraphEdge("program", "fr_cnc_production", "enables", "program", "france_televisions_fund",
              notes="CNC automatic support unlocks France Televisions co-production window"),
    GraphEdge("program", "fr_cnc_production", "enables", "program", "canal_plus_fund",
              notes="CNC production approval is prerequisite for Canal+ co-production slate"),
    GraphEdge("program", "france_televisions_fund", "improves", "program", "fr_cnc_production",
              notes="France Televisions broadcaster commitment increases CNC automatic support rate"),
    GraphEdge("program", "canal_plus_fund", "improves", "program", "fr_cnc_production",
              notes="Canal+ pre-sale improves CNC selective support scoring"),
    GraphEdge("program", "fr_trip", "requires", "program", "fr_cnc_production",
              notes="TRIP tax rebate requires CNC production registration"),
    GraphEdge("program", "fr_cnc_production", "complements", "program", "fr_trip",
              notes="CNC production fund and TRIP tax rebate are commonly combined"),
    GraphEdge("program", "fr_cnc_production", "alternative_to", "program", "de_dfff",
              notes="French CNC and German DFFF are alternative anchors for Franco-German co-productions"),
    GraphEdge("program", "fr_cnc_production", "majority_only", "program", "fr_cnc_production",
              notes="Full CNC automatic support available only to majority French productions"),
    GraphEdge("program", "fr_cnc_production", "minority_only", "program", "fr_cnc_minority_support",
              notes="CNC minority co-production window for non-French majority"),

    # CA Federal CPTC ↔ CMF / Broadcaster funds
    GraphEdge("program", "ca_federal_cptc", "enables", "program", "ca_cmf",
              notes="CAVCO certification for CPTC is prerequisite for CMF project certification"),
    GraphEdge("program", "ca_federal_cptc", "enables", "program", "ca_cmf_tv",
              notes="CPTC certification unlocks CMF TV licence funding stream"),
    GraphEdge("program", "ca_cmf", "requires", "program", "ca_federal_cptc",
              notes="CMF requires CPTC certification as eligibility condition"),
    GraphEdge("program", "ca_cmf_tv", "requires", "program", "ca_federal_cptc",
              notes="CMF TV requires CPTC certification"),
    GraphEdge("program", "cbc_original", "enables", "program", "ca_cmf",
              notes="CBC broadcast commitment is a qualifying trigger for CMF applications"),
    GraphEdge("program", "bravo_factual", "enables", "program", "ca_cmf",
              notes="Bell Media/Bravo broadcast commitment unlocks CMF documentary stream"),
    GraphEdge("program", "ca_cmf", "complements", "program", "ca_federal_cptc",
              notes="CMF equity investment stacks with federal CPTC labour credit"),
    GraphEdge("program", "ca_federal_cptc", "majority_only", "program", "ca_federal_cptc",
              notes="Full CPTC rate requires Canadian majority co-production"),
    GraphEdge("program", "ca_federal_cptc", "minority_only", "program", "ca_federal_cptc_treaty",
              notes="Reduced CPTC treaty rate for minority official co-productions"),
    GraphEdge("program", "ca_cmf", "blocks", "program", "ca_cmf_tv",
              condition="same_project_single_window",
              notes="CMF and CMF TV are separate funding windows; project can only apply to one"),

    # AU Producer Offset ↔ PDV / Location Offset / ABC
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_location_offset",
              notes="Location Offset for international shoots can stack with Producer Offset"),
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_pdv_offset",
              notes="PDV Offset for Australian post/VFX stacks with Producer Offset"),
    GraphEdge("program", "au_pdv_offset", "alternative_to", "program", "au_location_offset",
              notes="VFX-heavy productions may prefer PDV over Location Offset"),
    GraphEdge("program", "abc_television_fund", "enables", "program", "au_producer_offset",
              notes="ABC television broadcast commitment satisfies Australian Content standard"),
    GraphEdge("program", "au_producer_offset", "enables", "program", "abc_television_fund",
              notes="Producer Offset certification supports ABC co-financing applications"),
    GraphEdge("program", "au_producer_offset", "majority_only", "program", "au_producer_offset",
              notes="40% Producer Offset available to Australian majority productions only"),
    GraphEdge("program", "au_producer_offset", "minority_only", "program", "au_official_coproduction",
              notes="20% Producer Offset available to official treaty co-productions as minority partner"),
    GraphEdge("program", "au_location_offset", "blocks", "program", "au_producer_offset",
              condition="same_qualifying_spend",
              notes="Same Australian qualifying spend cannot be claimed under both Location and Producer Offset"),

    # DE DFFF ↔ Regional funds
    GraphEdge("program", "de_dfff", "complements", "program", "bavarian_film_fund",
              notes="Bavaria FilmFernsehFonds stacks with federal DFFF for Munich/Bavaria shoots"),
    GraphEdge("program", "de_dfff", "complements", "program", "berlin_mbb_fund",
              notes="Berlin MBB regional fund stacks with DFFF for Berlin-based productions"),
    GraphEdge("program", "bavarian_film_fund", "requires", "program", "de_dfff",
              notes="FilmFernsehFonds Bayern typically requires DFFF as co-financing condition"),
    GraphEdge("program", "berlin_mbb_fund", "requires", "program", "de_dfff",
              notes="MBB Berlin commonly requires DFFF federal support as co-financing"),
    GraphEdge("program", "de_dfff", "majority_only", "program", "de_dfff",
              notes="Full DFFF rate applies to German majority productions"),
    GraphEdge("program", "bavarian_film_fund", "alternative_to", "program", "berlin_mbb_fund",
              notes="Productions choose Bavaria or Berlin as primary German regional hub, not both"),

    # EU Eurimages / MEDIA / Creative Europe
    GraphEdge("program", "eu_eurimages", "complements", "program", "eu_media_fund",
              notes="Eurimages co-production fund combines with MEDIA development/distribution support"),
    GraphEdge("program", "eu_eurimages", "complements", "program", "eu_creative_europe",
              notes="Creative Europe slate development complements Eurimages production funding"),
    GraphEdge("program", "eu_media_fund", "enables", "program", "eu_eurimages",
              notes="MEDIA development funding strengthens Eurimages co-production applications"),
    GraphEdge("program", "eu_creative_europe", "enables", "program", "eu_media_fund",
              notes="Creative Europe label improves MEDIA fund priority scoring"),

    # Bilateral treaties: unlocks national programs
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "uk_avec",
              notes="UK-Canada bilateral treaty unlocks AVEC for Canadian minority co-productions"),
    GraphEdge("treaty", "uk-ca-bilateral", "unlocks", "program", "ca_federal_cptc",
              notes="UK-Canada treaty unlocks CPTC for UK minority co-productions"),
    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "uk_avec",
              notes="UK-Ireland framework allows Irish spend to count toward AVEC"),
    GraphEdge("treaty", "uk-ie-bilateral", "unlocks", "program", "ie_section_481",
              notes="UK-Ireland framework supports S481 for UK majority with Irish minority"),
    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "ca_federal_cptc",
              notes="Canada-France treaty unlocks CPTC for French minority co-producers"),
    GraphEdge("treaty", "ca-fr-bilateral", "unlocks", "program", "fr_cnc_production",
              notes="Canada-France treaty unlocks CNC for Canadian minority co-producers"),
    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "ca_federal_cptc",
              notes="Canada-Australia treaty unlocks CPTC for Australian minority"),
    GraphEdge("treaty", "ca-au-bilateral", "unlocks", "program", "au_producer_offset",
              notes="Canada-Australia treaty unlocks Producer Offset for Canadian minority"),
    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "fr_cnc_production",
              notes="France-Germany treaty unlocks CNC for German minority"),
    GraphEdge("treaty", "fr-de-bilateral", "unlocks", "program", "de_dfff",
              notes="France-Germany treaty unlocks DFFF for French minority co-producers"),
    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "uk_avec",
              notes="UK-Australia treaty unlocks AVEC for Australian minority producers"),
    GraphEdge("treaty", "uk-au-bilateral", "unlocks", "program", "au_producer_offset",
              notes="UK-Australia treaty unlocks Producer Offset for UK minority"),
    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "it_tax_credit_domestic",
              notes="Italy-France bilateral enables Italian credit for French minority"),
    GraphEdge("treaty", "it-fr-bilateral", "unlocks", "program", "fr_cnc_production",
              notes="Italy-France bilateral enables CNC support for Italian majority"),
    GraphEdge("treaty", "uk-nz-bilateral", "unlocks", "program", "uk_avec",
              notes="UK-NZ treaty unlocks AVEC for NZ minority co-productions"),
    GraphEdge("treaty", "uk-nz-bilateral", "unlocks", "program", "nz_screen_production_grant",
              notes="UK-NZ treaty enables NZ Production Grant for UK minority shoots"),
    GraphEdge("treaty", "de-au-bilateral", "unlocks", "program", "de_dfff",
              notes="Germany-Australia treaty unlocks DFFF for Australian minority"),
    GraphEdge("treaty", "de-au-bilateral", "unlocks", "program", "au_producer_offset",
              notes="Germany-Australia treaty unlocks AU Producer Offset for German minority"),
    GraphEdge("treaty", "fr-be-bilateral", "unlocks", "program", "fr_cnc_production",
              notes="France-Belgium treaty unlocks CNC for Belgian minority co-producers"),
    GraphEdge("treaty", "fr-be-bilateral", "unlocks", "program", "be_screen_brussels",
              notes="France-Belgium treaty unlocks Screen.Brussels for French minority"),
    GraphEdge("treaty", "ca-ie-bilateral", "unlocks", "program", "ca_federal_cptc",
              notes="Canada-Ireland treaty unlocks CPTC for Irish minority co-producers"),
    GraphEdge("treaty", "ca-ie-bilateral", "unlocks", "program", "ie_section_481",
              notes="Canada-Ireland treaty unlocks S481 for Canadian minority shoots in Ireland"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "au_producer_offset",
              notes="Australia-NZ bilateral unlocks Producer Offset for NZ minority"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "nz_screen_production_grant",
              notes="Australia-NZ bilateral unlocks NZ Grant for Australian majority with NZ minority"),

    # Regional fund ↔ Main program relationships
    GraphEdge("program", "uk_screen_scotland", "complements", "program", "uk_avec",
              notes="Screen Scotland Funding stacks with AVEC for Scottish-set features"),
    GraphEdge("program", "uk_screen_scotland", "requires", "program", "uk_avec",
              notes="Screen Scotland typically requires AVEC certification as a condition"),
    GraphEdge("program", "gb_lon_film_london", "complements", "program", "uk_avec",
              notes="Film London Production Fund complements AVEC for London-based productions"),
    GraphEdge("program", "gb_wls_film_fund", "complements", "program", "uk_avec",
              notes="Welsh production fund complements AVEC for Wales-set productions"),
    GraphEdge("program", "fr_regional_funds", "complements", "program", "fr_cnc_production",
              notes="French regional funds (CRC) stack with national CNC support"),
    GraphEdge("program", "ca_bc_interactive", "complements", "program", "ca_federal_cptc",
              notes="BC Interactive Digital Media Credit for VFX stacks with CPTC"),
    GraphEdge("program", "ca_on_ocase", "complements", "program", "ca_federal_cptc",
              notes="Ontario OCASE interactive credit stacks with federal CPTC"),
    GraphEdge("program", "au_vic_film_victoria", "complements", "program", "au_producer_offset",
              notes="Film Victoria regional fund stacks with federal Producer Offset"),
    GraphEdge("program", "au_vic_film_victoria", "requires", "program", "au_producer_offset",
              notes="Film Victoria typically requires federal Producer Offset as co-financing"),
    GraphEdge("program", "es_canary_islands_ztlc", "complements", "program", "es_spain_ife",
              notes="Canary Islands ZTLC 50% credit can be added to mainland IFE rebate"),
    GraphEdge("program", "es_canary_islands_ztlc", "alternative_to", "program", "es_spain_ife",
              notes="Canary Islands ZTLC is an alternative to mainland IFE for Canary Island shoots"),
    GraphEdge("program", "film_i_vast", "complements", "program", "se_sf_production",
              notes="Vastragotaland regional fund complements Swedish Film Institute support"),
    GraphEdge("program", "dk_cph_film_fund", "complements", "program", "dk_dfi_support",
              notes="Copenhagen Film Fund regional grant stacks with DFI national support"),
    GraphEdge("program", "no_vgn_viken", "complements", "program", "no_nfi_grants",
              notes="Viken regional fund complements NFI national grants for Norway shoots"),
    GraphEdge("program", "it_regional_fund", "complements", "program", "it_tax_credit_domestic",
              notes="Italian regional funds (Apulia, Lazio) stack with national tax credit"),

    # Broadcaster ↔ Program: enables / improves
    GraphEdge("program", "bbc_drama_production", "improves", "program", "uk_avec",
              notes="BBC drama commission strengthens AVEC cultural test score"),
    GraphEdge("program", "sky_uk_drama", "improves", "program", "uk_avec",
              notes="Sky UK drama commission improves AVEC programme qualification"),
    GraphEdge("program", "rte_drama_fund", "enables", "program", "ie_section_481",
              notes="RTE broadcaster license is a qualifying route to Section 481"),
    GraphEdge("program", "cbc_original", "enables", "program", "ca_cmf",
              notes="CBC broadcast license triggers CMF application eligibility"),
    GraphEdge("program", "cbc_original", "improves", "program", "ca_federal_cptc",
              notes="CBC commitment strengthens CAVCO certification scoring"),
    GraphEdge("program", "bravo_factual", "improves", "program", "ca_federal_cptc",
              notes="Bravo/Bell Media commitment improves CAVCO creative control assessment"),
    GraphEdge("program", "france_televisions_fund", "enables", "program", "fr_cnc_production",
              notes="France Televisions pre-sale is a qualifying trigger for CNC automatic support"),
    GraphEdge("program", "canal_plus_fund", "enables", "program", "fr_cnc_production",
              notes="Canal+ co-financing triggers CNC production support eligibility"),
    GraphEdge("program", "abc_television_fund", "enables", "program", "au_producer_offset",
              notes="ABC license enables Australian Content Standard certification for Producer Offset"),
    GraphEdge("program", "se_svt", "enables", "program", "se_sf_production",
              notes="SVT Swedish broadcaster commitment strengthens SFI production funding"),
    GraphEdge("program", "no_nrk", "enables", "program", "no_nfi_grants",
              notes="NRK broadcaster commitment supports NFI project certification"),
    GraphEdge("program", "dk_dr", "enables", "program", "dk_dfi_support",
              notes="DR Danish broadcaster supports DFI production fund eligibility"),
    GraphEdge("program", "fi_yle", "enables", "program", "fi_ses_grants",
              notes="YLE Finnish broadcaster is a recognised partner for SES production grants"),

    # majority_only / minority_only for co-production programs
    GraphEdge("program", "ie_section_481", "minority_only", "program", "ie_section_481_minority",
              notes="Reduced Section 481 rate for Irish minority official co-productions"),
    GraphEdge("program", "de_dfff", "minority_only", "program", "de_dfff_minority",
              notes="Minority co-production rate under DFFF for non-German majority"),
    GraphEdge("program", "hu_nfi_grants", "majority_only", "program", "hu_nfi_grants",
              notes="Full NFI grant only for Hungarian majority productions"),
    GraphEdge("program", "hu_nfi_grants", "minority_only", "program", "hu_nfi_minority_grant",
              notes="Minority co-production grant under Hungarian NFI for foreign majority"),
    GraphEdge("program", "kr_kofic_rebate", "majority_only", "program", "kr_kofic_rebate",
              notes="Full KOFIC rebate for Korean majority productions"),
    GraphEdge("program", "nz_screen_production_grant", "majority_only", "program", "nz_screen_production_grant",
              notes="Full NZ Grant for New Zealand majority productions"),
    GraphEdge("program", "nz_screen_production_grant", "minority_only", "program", "nz_official_coproduction",
              notes="Minority rate for official NZFC co-productions with foreign majority"),
    GraphEdge("program", "it_tax_credit_domestic", "majority_only", "program", "it_tax_credit_domestic",
              notes="40% domestic tax credit available only to Italian majority productions"),
    GraphEdge("program", "it_tax_credit_foreign", "minority_only", "program", "it_tax_credit_foreign",
              notes="25% foreign production credit for non-Italian majority shoots in Italy"),
    GraphEdge("program", "pl_pisf_grants", "majority_only", "program", "pl_pisf_grants",
              notes="Full PISF grant available to Polish majority productions"),
    GraphEdge("program", "be_screen_brussels", "majority_only", "program", "be_screen_brussels",
              notes="Full Screen.Brussels support for Belgian majority productions"),
    GraphEdge("program", "gr_ekome_rebate", "minority_only", "program", "gr_ekome_rebate",
              notes="40% EKOME rebate available to international productions"),
    GraphEdge("program", "mt_mfc_cash_rebate", "minority_only", "program", "mt_mfc_cash_rebate",
              notes="Malta 40% rebate available to international non-Maltese productions shooting in Malta"),
    GraphEdge("program", "rs_serbia_film_commission", "minority_only", "program", "rs_serbia_film_commission",
              notes="Serbia 25% rebate available to international productions"),

    # blocks: incompatibilities / exclusions
    GraphEdge("program", "au_location_offset", "blocks", "program", "au_pdv_offset",
              condition="same_production_same_spend",
              notes="Location Offset and PDV Offset cannot be claimed on the same Australian spend"),
    GraphEdge("program", "fr_trip", "blocks", "program", "fr_cnc_selective",
              condition="same_production",
              notes="TRIP and CNC Selective Aid cannot both be claimed for the same production"),
    GraphEdge("program", "es_canary_islands_ztlc", "blocks", "program", "es_spain_ife",
              condition="same_spend_double_claim",
              notes="Canary Islands ZTLC and mainland IFE cannot claim the same qualifying spend"),
    GraphEdge("program", "de_dfff", "blocks", "program", "de_ffa_grant",
              condition="combined_aid_ceiling",
              notes="DFFF and FFA project grant combined cannot exceed state aid ceiling"),

    # alternative_to: lateral choices producers face
    GraphEdge("program", "hu_nfi_grants", "alternative_to", "program", "cz_czech_film_fund",
              notes="Hungary and Czech Republic are commonly compared alternative Central European locations"),
    GraphEdge("program", "cz_czech_film_fund", "alternative_to", "program", "pl_pisf_grants",
              notes="Czech and Polish funds are alternatives for Eastern European shoots"),
    GraphEdge("program", "gr_ekome_rebate", "alternative_to", "program", "mt_mfc_cash_rebate",
              notes="Greece and Malta are alternative Mediterranean location rebate options"),
    GraphEdge("program", "mt_mfc_cash_rebate", "alternative_to", "program", "rs_serbia_film_commission",
              notes="Malta and Serbia are compared as affordable European shoot destinations"),
    GraphEdge("program", "au_producer_offset", "alternative_to", "program", "nz_screen_production_grant",
              notes="Australia and New Zealand are alternative Pacific Rim shoot destinations"),
    GraphEdge("program", "ca_federal_cptc", "alternative_to", "program", "uk_avec",
              notes="Canada and UK are the most common primary incentive anchors for English-language productions"),
    GraphEdge("program", "ie_section_481", "alternative_to", "program", "de_dfff",
              notes="Ireland and Germany are European alternatives for English-language majority productions"),

    # enables: program unlocking another program
    GraphEdge("program", "eu_media_fund", "enables", "program", "eu_eurimages",
              notes="MEDIA label can be used as evidence of European qualification for Eurimages"),
    GraphEdge("program", "eu_creative_europe", "enables", "program", "eu_eurimages",
              notes="Creative Europe production label improves Eurimages scoring"),
    GraphEdge("program", "uk_avec", "enables", "program", "gb_bfi_international",
              notes="AVEC certification enables BFI international sales market support"),
    GraphEdge("program", "ca_federal_cptc", "enables", "program", "ca_telefilm_export",
              notes="CPTC certification enables Telefilm Canada export market funding"),
    GraphEdge("program", "au_producer_offset", "enables", "program", "au_screen_talent",
              notes="Producer Offset project certification enables Screen Australia talent development support"),
    GraphEdge("program", "kr_kofic_rebate", "enables", "program", "kr_kofic_export",
              notes="KOFIC production certification enables KOFIC export market support"),
    GraphEdge("program", "de_dfff", "enables", "program", "de_german_films",
              notes="DFFF certification enables German Films export support eligibility"),
    GraphEdge("program", "fr_cnc_production", "enables", "program", "fr_unifrance",
              notes="CNC production registration enables UniFrance export support"),
    GraphEdge("program", "it_tax_credit_domestic", "enables", "program", "it_anica_export",
              notes="Italian tax credit certification enables ANICA export support"),

    # Additional Program ↔ CulturalTest edges
    GraphEdge("program", "uk_avec", "requires", "test", "uk_cultural_test",
              notes="BFI AVEC requires passing the BFI Cultural Test (min 18/35 points)"),
    GraphEdge("program", "ca_federal_cptc", "requires", "test", "ca_cavco_points_test",
              notes="CPTC requires Canadian content points test via CAVCO (min 6/10 key positions)"),
    GraphEdge("program", "au_producer_offset", "requires", "test", "au_significant_australian_content_test",
              notes="Producer Offset requires passing Significant Australian Content (SAC) test"),
    GraphEdge("program", "de_dfff", "requires", "test", "de_cultural_test",
              notes="DFFF requires passing the German cultural test (min 25 points)"),
    GraphEdge("program", "it_tax_credit_domestic", "requires", "test", "it_cultural_test",
              notes="Italian domestic tax credit requires cultural test"),
    GraphEdge("program", "eu_eurimages", "requires", "test", "eu_european_content_test",
              notes="Eurimages requires majority European content and co-production certification"),
    GraphEdge("program", "be_screen_brussels", "requires", "test", "be_cultural_test",
              notes="Screen.Brussels requires Belgian cultural content certification"),
    GraphEdge("program", "nl_netherlands_film_fund", "requires", "test", "nl_cultural_test",
              notes="Netherlands Film Fund requires Dutch cultural content certification"),
    GraphEdge("program", "pt_ica_grant", "requires", "test", "pt_cultural_test",
              notes="ICA Portugal grant requires Portuguese cultural content scoring"),
    GraphEdge("program", "pl_pisf_grants", "requires", "test", "pl_cultural_test",
              notes="PISF Poland requires Polish cultural significance in the project"),
    GraphEdge("program", "za_nfvf_incentive", "requires", "test", "za_sa_content_test",
              notes="NFVF incentive requires South African Content (SAC) certification"),

    # Cross-program stacking: complements (additional)
    GraphEdge("program", "de_dfff", "complements", "program", "eu_eurimages",
              notes="DFFF and Eurimages are frequently combined for European co-productions"),
    GraphEdge("program", "fr_cnc_production", "complements", "program", "eu_eurimages",
              notes="CNC production support and Eurimages are commonly combined for European co-productions"),
    GraphEdge("program", "ie_section_481", "complements", "program", "eu_eurimages",
              notes="Irish S481 and Eurimages can be combined for European co-productions with Irish involvement"),
    GraphEdge("program", "hu_nfi_grants", "complements", "program", "eu_eurimages",
              notes="Hungarian NFI and Eurimages are frequently combined for Eastern European co-productions"),
    GraphEdge("program", "pl_pisf_grants", "complements", "program", "eu_eurimages",
              notes="PISF and Eurimages combine for Polish-majority European co-productions"),
    GraphEdge("program", "be_screen_brussels", "complements", "program", "eu_eurimages",
              notes="Screen.Brussels and Eurimages commonly combine for Belgian-involved European films"),
    GraphEdge("program", "cz_czech_film_fund", "complements", "program", "eu_eurimages",
              notes="Czech Film Fund and Eurimages combine for Czech co-productions"),
    GraphEdge("program", "au_producer_offset", "complements", "program", "au_pdv_offset",
              notes="PDV Offset for Australian VFX/post stacks cleanly with Producer Offset"),
    GraphEdge("program", "nz_screen_production_grant", "complements", "program", "au_producer_offset",
              notes="NZ Grant and AU Producer Offset combine for trans-Tasman official co-productions"),

    # =========================================================================
    # KNOWLEDGE COMPLETION — Migration 0061
    # =========================================================================

    # -------------------------------------------------------------------------
    # depends_on — sequencing: program A cannot realistically proceed without B
    # -------------------------------------------------------------------------
    GraphEdge("program", "ca_cmf", "depends_on", "broadcaster", "cbc_original",
              condition="CMF Convergent stream requires a licensed Canadian broadcaster trigger",
              notes="CMF will not fund without a broadcaster license agreement as co-applicant"),
    GraphEdge("program", "ca_bell_fund", "depends_on", "broadcaster", "cbc_original",
              condition="Bell Fund requires broadcaster co-applicant",
              notes="Bell Fund requires broadcaster as co-applicant; cannot apply independently"),
    GraphEdge("program", "nordic_ftvf", "depends_on", "broadcaster", "se_svt",
              condition="At least one Nordic public broadcaster required",
              notes="Nordic Film & TV Fund requires at least one Nordic broadcaster attachment from a member country"),
    GraphEdge("program", "eu_eurimages", "depends_on", "treaty", "eurimages-multilateral",
              notes="Eurimages requires a formal co-production agreement between at least two Eurimages member states"),
    GraphEdge("program", "ibermedia_programme", "depends_on", "treaty", "ibermedia-multilateral",
              notes="Ibermedia requires a co-production agreement from at least two Ibermedia member countries"),
    GraphEdge("program", "de_bb_medienboard", "depends_on", "program", "de_dfff",
              condition="Projects above EUR 3M typically",
              notes="Medienboard Berlin-Brandenburg frequently requires DFFF federal anchor on larger projects"),
    GraphEdge("program", "fr_trip", "depends_on", "program", "fr_cnc_cultural_test",
              notes="TRIP requires CNC cultural qualification certification before the rebate application is accepted"),
    GraphEdge("program", "au_producer_offset", "depends_on", "program", "au_content_test",
              notes="Producer Offset requires meeting QAPE threshold and passing the Australian content test"),
    GraphEdge("program", "eu_media_fund", "depends_on", "treaty", "eurimages-multilateral",
              notes="MEDIA/Creative Europe development fund requires company established in Creative Europe country"),
    GraphEdge("program", "ie_section_481", "depends_on", "program", "ie_section_481_test",
              notes="Section 481 requires passing the Irish qualifying production checklist before SIRI certification"),

    # -------------------------------------------------------------------------
    # service_only — program is only available in service-production mode
    # -------------------------------------------------------------------------
    GraphEdge("program", "uk_hvc", "service_only", "program", "uk_hvc",
              notes="UK High-end TV Certificate (HVC) is the service-production route: no BFI cultural test, no UK majority required; incompatible with co-production AVEC"),
    GraphEdge("program", "ca_cmpa_foreign", "service_only", "program", "ca_cmpa_foreign",
              notes="CMPA Foreign Location Shooting Certificate is for service productions only; incompatible with co-production treaty access to CPTC"),
    GraphEdge("program", "au_location_offset", "service_only", "program", "au_location_offset",
              notes="Australian Location Offset (16.5%) is for foreign-majority location shoots; cannot be combined with domestic Producer Offset on same qualifying spend"),
    GraphEdge("program", "kr_kofic_location", "service_only", "program", "kr_kofic_location",
              notes="KOFIC Location Incentive is for foreign productions shooting in Korea; not available for Korean domestic co-productions"),

    # -------------------------------------------------------------------------
    # broadcaster_only — program requires broadcaster as co-applicant or trigger
    # -------------------------------------------------------------------------
    GraphEdge("program", "ca_cmf", "broadcaster_only", "program", "ca_cmf",
              notes="CMF Convergent stream requires a licensed Canadian broadcaster trigger; broadcaster must hold the license"),
    GraphEdge("program", "ca_bell_fund", "broadcaster_only", "program", "ca_bell_fund",
              notes="Bell Fund requires an eligible broadcaster as co-applicant; producers cannot apply without broadcaster"),
    GraphEdge("program", "nordic_ftvf", "broadcaster_only", "program", "nordic_ftvf",
              notes="Nordic Film & TV Fund requires attachment of at least one Nordic public broadcaster (SVT, NRK, DR, YLE, or RÚV)"),
    GraphEdge("program", "rte_drama_fund", "broadcaster_only", "program", "rte_drama_fund",
              notes="RTÉ Drama Fund is available only when RTÉ is a commissioning broadcaster on the project"),

    # -------------------------------------------------------------------------
    # regional_only — program requires qualifying regional spend
    # -------------------------------------------------------------------------
    # Norwegian regional funds
    GraphEdge("program", "no_vgn_viken", "regional_only", "program", "no_vgn_viken",
              notes="Viken Filmsenter funds only projects with significant qualifying spend in the Viken region"),
    GraphEdge("program", "no_rog_vestnorsk", "regional_only", "program", "no_rog_vestnorsk",
              notes="Vestnorsk Filmsenter funds only projects with significant qualifying spend in Western Norway"),
    GraphEdge("program", "no_tro_nordnorsk", "regional_only", "program", "no_tro_nordnorsk",
              notes="Nordnorsk Filmsenter funds only projects with significant qualifying spend in Northern Norway"),
    GraphEdge("program", "no_inl_midtnorsk", "regional_only", "program", "no_inl_midtnorsk",
              notes="Midtnorsk Filmsenter funds only projects with significant qualifying spend in Trøndelag/Innlandet"),
    GraphEdge("program", "no_mro_film3", "regional_only", "program", "no_mro_film3",
              notes="Film3 funds projects with significant qualifying spend in Møre og Romsdal"),
    # Swedish regional funds
    GraphEdge("program", "film_i_vast", "regional_only", "program", "film_i_vast",
              notes="Film i Väst requires significant production activity in Västra Götaland region"),
    GraphEdge("program", "se_sk_film_skane", "regional_only", "program", "se_sk_film_skane",
              notes="Film i Skåne requires production activity in the Skåne region"),
    GraphEdge("program", "se_ab_filmstockholm", "regional_only", "program", "se_ab_filmstockholm",
              notes="Film Stockholm requires production activity in Stockholm-Mälardalen region"),
    GraphEdge("program", "se_goteborg_fund", "regional_only", "program", "se_goteborg_fund",
              notes="Göteborg Film Fund requires production activity in or cultural connection to Gothenburg region"),
    # UK regional funds
    GraphEdge("program", "gb_lon_film_london", "regional_only", "program", "gb_lon_film_london",
              notes="Film London requires London-based qualifying spend"),
    GraphEdge("program", "gb_sct_screen_production", "regional_only", "program", "gb_sct_screen_production",
              notes="Screen Scotland requires Scottish production spend"),
    GraphEdge("program", "gb_wls_film_fund", "regional_only", "program", "gb_wls_film_fund",
              notes="Wales Screen / Creative Wales requires Welsh production spend"),
    GraphEdge("program", "gb_nir_northern_ireland", "regional_only", "program", "gb_nir_northern_ireland",
              notes="Northern Ireland Screen requires NI-based qualifying production spend"),
    GraphEdge("program", "gb_yrk_screen_yorkshire", "regional_only", "program", "gb_yrk_screen_yorkshire",
              notes="Screen Yorkshire requires Yorkshire-based qualifying production spend"),
    GraphEdge("program", "gb_film_hub_midlands", "regional_only", "program", "gb_film_hub_midlands",
              notes="Film Hub Midlands requires qualifying spend in the English Midlands"),
    # German regional funds
    GraphEdge("program", "de_bb_medienboard", "regional_only", "program", "de_bb_medienboard",
              notes="Medienboard Berlin-Brandenburg requires qualifying production spend in Berlin or Brandenburg"),
    GraphEdge("program", "de_nrw_filmstiftung", "regional_only", "program", "de_nrw_filmstiftung",
              notes="Filmstiftung NRW requires qualifying production spend in North Rhine-Westphalia"),
    GraphEdge("program", "de_fff_bayern", "regional_only", "program", "de_fff_bayern",
              notes="FilmFernsehFonds Bayern requires qualifying production spend in Bavaria"),
    GraphEdge("program", "de_ni_nordmedia", "regional_only", "program", "de_ni_nordmedia",
              notes="nordmedia requires qualifying production spend in Lower Saxony or Bremen"),
    GraphEdge("program", "de_hh_film_hamburg", "regional_only", "program", "de_hh_film_hamburg",
              notes="Film Hamburg requires qualifying production spend in Hamburg"),
    GraphEdge("program", "de_bw_mfg", "regional_only", "program", "de_bw_mfg",
              notes="MFG Baden-Württemberg requires qualifying production spend in Baden-Württemberg"),
    GraphEdge("program", "de_mdm_mitteldeutsche", "regional_only", "program", "de_mdm_mitteldeutsche",
              notes="MDM requires qualifying production spend in Saxony, Saxony-Anhalt or Thuringia"),
    # French regional funds
    GraphEdge("program", "fr_idf_regional", "regional_only", "program", "fr_idf_regional",
              notes="Île-de-France regional fund requires qualifying production activity in the Île-de-France region"),
    GraphEdge("program", "fr_naq_regional", "regional_only", "program", "fr_naq_regional",
              notes="Nouvelle-Aquitaine regional fund requires qualifying production activity in Nouvelle-Aquitaine"),
    GraphEdge("program", "fr_ara_regional", "regional_only", "program", "fr_ara_regional",
              notes="Auvergne-Rhône-Alpes regional fund requires qualifying production activity in ARA"),
    GraphEdge("program", "fr_occ_regional", "regional_only", "program", "fr_occ_regional",
              notes="Occitanie regional fund requires qualifying production activity in Occitanie"),
    # Italian regional film commissions
    GraphEdge("program", "it_laz_lazio_fc", "regional_only", "program", "it_laz_lazio_fc",
              notes="Lazio Film Commission requires qualifying production activity in the Lazio region"),
    GraphEdge("program", "it_sic_sicilia_fc", "regional_only", "program", "it_sic_sicilia_fc",
              notes="Sicilia Film Commission requires qualifying production activity in Sicily"),
    GraphEdge("program", "it_cam_campania_fc", "regional_only", "program", "it_cam_campania_fc",
              notes="Campania Film Commission requires qualifying production activity in Campania"),
    GraphEdge("program", "it_pie_piemonte_fc", "regional_only", "program", "it_pie_piemonte_fc",
              notes="Film Commission Torino Piemonte requires qualifying production activity in Piedmont"),
    GraphEdge("program", "it_apu_apulia_ff", "regional_only", "program", "it_apu_apulia_ff",
              notes="Apulia Film Fund requires qualifying production activity in Apulia"),
    GraphEdge("program", "it_tos_tuscany_fc", "regional_only", "program", "it_tos_tuscany_fc",
              notes="Toscana Film Commission requires qualifying production activity in Tuscany"),
    # Spanish regional funds
    GraphEdge("program", "es_cat_icec", "regional_only", "program", "es_cat_icec",
              notes="ICEC requires qualifying production activity in Catalonia"),
    GraphEdge("program", "es_and_andalusia", "regional_only", "program", "es_and_andalusia",
              notes="Andalucía Film Commission requires qualifying production activity in Andalucía"),
    GraphEdge("program", "es_gal_agadic", "regional_only", "program", "es_gal_agadic",
              notes="AGADIC requires qualifying production activity in Galicia"),
    GraphEdge("program", "es_val_ivc", "regional_only", "program", "es_val_ivc",
              notes="Institut Valencià de Cultura requires qualifying production activity in the Valencian Community"),
    GraphEdge("program", "es_eus_basque", "regional_only", "program", "es_eus_basque",
              notes="Basque Audiovisual fund requires qualifying production activity in the Basque Country"),
    # Australian state funds
    GraphEdge("program", "au_vic_film_victoria", "regional_only", "program", "au_vic_film_victoria",
              notes="VicScreen requires significant Victorian qualifying production spend"),
    GraphEdge("program", "au_qld_screen", "regional_only", "program", "au_qld_screen",
              notes="Screen Queensland requires Queensland-based qualifying production spend"),
    GraphEdge("program", "au_nsw_screen", "regional_only", "program", "au_nsw_screen",
              notes="Screen NSW requires NSW-based qualifying production spend"),
    GraphEdge("program", "au_sa_safc", "regional_only", "program", "au_sa_safc",
              notes="SAFC requires South Australian qualifying production spend"),
    GraphEdge("program", "au_tas_screen", "regional_only", "program", "au_tas_screen",
              notes="Screen Tasmania requires Tasmanian qualifying production spend"),
    GraphEdge("program", "au_nt_territory", "regional_only", "program", "au_nt_territory",
              notes="NT Film Office requires Northern Territory qualifying production spend"),
    GraphEdge("program", "au_screenwest", "regional_only", "program", "au_screenwest",
              notes="ScreenWest requires Western Australian qualifying production spend"),
    GraphEdge("program", "au_miff_premiere", "regional_only", "program", "au_miff_premiere",
              notes="MIFF Premiere Fund requires qualifying production with Australian content connection"),
    # Danish regional funds
    GraphEdge("program", "dk_cph_film_fund", "regional_only", "program", "dk_cph_film_fund",
              notes="Copenhagen Film Fund requires qualifying production activity in the Copenhagen/Zealand region"),
    GraphEdge("program", "dk_fyn_film", "regional_only", "program", "dk_fyn_film",
              notes="Fyn Film requires qualifying production activity on the island of Funen"),
    # Canadian provincial funds
    GraphEdge("program", "ca_bc_pstc", "regional_only", "program", "ca_bc_pstc",
              notes="BC PSTC requires qualifying production spend in British Columbia"),
    GraphEdge("program", "on_ofttc", "regional_only", "program", "on_ofttc",
              notes="Ontario OFTTC requires qualifying production spend in Ontario"),
    GraphEdge("program", "on_opstc", "regional_only", "program", "on_opstc",
              notes="Ontario OPSTC requires qualifying production spend in Ontario"),
    GraphEdge("program", "qc_film_production", "regional_only", "program", "qc_film_production",
              notes="Quebec SODEC fund requires qualifying production spend in Quebec"),
    GraphEdge("program", "nohfc_production_fund", "regional_only", "program", "nohfc_production_fund",
              notes="NOHFC requires qualifying production spend in Northern Ontario"),
    GraphEdge("program", "ca_pe_film_pei", "regional_only", "program", "ca_pe_film_pei",
              notes="PEI Film requires qualifying production spend in Prince Edward Island"),
    GraphEdge("program", "ca_mb_film_mb", "regional_only", "program", "ca_mb_film_mb",
              notes="Manitoba Film requires qualifying production spend in Manitoba"),
    GraphEdge("program", "ca_nb_film_nb", "regional_only", "program", "ca_nb_film_nb",
              notes="New Brunswick Film requires qualifying production spend in New Brunswick"),
    GraphEdge("program", "ca_nl_film_nl", "regional_only", "program", "ca_nl_film_nl",
              notes="Newfoundland Film requires qualifying production spend in Newfoundland & Labrador"),
    GraphEdge("program", "ca_ns_film_incentive", "regional_only", "program", "ca_ns_film_incentive",
              notes="Nova Scotia Film Incentive requires qualifying production spend in Nova Scotia"),

    # -------------------------------------------------------------------------
    # national_only — program requires domestic/treaty co-production status;
    #                 not available to pure service productions
    # -------------------------------------------------------------------------
    GraphEdge("program", "ca_federal_cptc", "national_only", "program", "ca_federal_cptc",
              notes="Federal CPTC is for Canadian domestic productions or treaty co-productions only; pure service productions must use the CMPA Foreign certificate instead"),
    GraphEdge("program", "au_producer_offset", "national_only", "program", "au_producer_offset",
              notes="Producer Offset (40%) is for Australian domestic or treaty co-productions; foreign service shoots must use Location Offset instead"),
    GraphEdge("program", "ie_section_481", "national_only", "program", "ie_section_481",
              notes="Section 481 requires Irish-based production company and qualifying spend; not available for foreign service productions without Irish majority participation"),
    GraphEdge("program", "uk_avec", "national_only", "program", "uk_avec",
              notes="AVEC requires passing the BFI cultural test or co-production treaty qualification; not available for pure service productions (those use HVC instead)"),
    GraphEdge("program", "fr_trip", "national_only", "program", "fr_trip",
              notes="TRIP requires CNC cultural qualification; not available for pure service productions without French cultural connection"),
    GraphEdge("program", "de_dfff", "national_only", "program", "de_dfff",
              notes="DFFF requires German cultural connection (Fachgutachten) and German producer; not available for pure service productions"),
    GraphEdge("program", "eu_eurimages", "national_only", "program", "eu_eurimages",
              notes="Eurimages is for official co-productions between member states; not available for service productions"),
    GraphEdge("program", "no_nfi_grants", "national_only", "program", "no_nfi_grants",
              notes="NFI grants require Norwegian producer and qualifying Norwegian cultural content; not service-production eligible"),
    GraphEdge("program", "kr_kofic_production", "national_only", "program", "kr_kofic_production",
              notes="KOFIC production fund requires Korean producer and Korean cultural content; not service-production eligible"),

    # -------------------------------------------------------------------------
    # fund_only — program requires formal fund application / membership
    # -------------------------------------------------------------------------
    GraphEdge("program", "eu_media_fund", "fund_only", "program", "eu_media_fund",
              notes="EU MEDIA / Creative Europe fund requires formal programme application; only accessible through Creative Europe National Desks"),
    GraphEdge("program", "eu_creative_europe", "fund_only", "program", "eu_creative_europe",
              notes="Creative Europe requires application through the Creative Europe Desks; cannot be accessed directly"),
    GraphEdge("program", "nl_hbf", "fund_only", "program", "nl_hbf",
              notes="Hubert Bals Fund is only accessible via formal IFFR submission process; no other route exists"),
    GraphEdge("program", "eu_eurimages", "fund_only", "program", "eu_eurimages",
              notes="Eurimages requires a formal co-production application with all producers from member states; not accessible without Eurimages secretariat approval"),
    GraphEdge("program", "ibermedia_programme", "fund_only", "program", "ibermedia_programme",
              notes="Ibermedia requires formal application through the Ibermedia Programme office; all co-producers must be from Ibermedia member countries"),

    # -------------------------------------------------------------------------
    # Additional treaty → program unlocks (missing from migration 0059)
    # -------------------------------------------------------------------------
    GraphEdge("treaty", "uk-it-bilateral", "unlocks", "program", "uk_avec",
              condition="UK majority in UK-Italy co-production", notes="UK-Italy bilateral treaty (2007)"),
    GraphEdge("treaty", "uk-it-bilateral", "unlocks", "program", "it_tax_credit_foreign",
              condition="IT majority in UK-Italy co-production", notes="UK-Italy bilateral treaty (2007)"),
    GraphEdge("treaty", "au-fr-bilateral", "unlocks", "program", "au_producer_offset",
              condition="AU majority in AU-France co-production", notes="Australia-France bilateral treaty (2010)"),
    GraphEdge("treaty", "au-fr-bilateral", "unlocks", "program", "fr_trip",
              condition="FR majority in AU-France co-production", notes="Australia-France bilateral treaty (2010)"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "au_producer_offset",
              condition="AU majority in AU-NZ co-production", notes="Australia-New Zealand bilateral treaty (2010)"),
    GraphEdge("treaty", "au-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate",
              condition="NZ majority in AU-NZ co-production", notes="Australia-New Zealand bilateral treaty (2010)"),
    GraphEdge("treaty", "de-at-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Germany-Austria co-production", notes="Germany-Austria bilateral treaty (1993)"),
    GraphEdge("treaty", "de-at-bilateral", "unlocks", "program", "at_ofi_grants",
              condition="AT majority in Germany-Austria co-production", notes="Germany-Austria bilateral treaty (1993)"),
    GraphEdge("treaty", "de-pl-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Germany-Poland co-production", notes="Germany-Poland bilateral treaty (1994)"),
    GraphEdge("treaty", "de-pl-bilateral", "unlocks", "program", "pl_pisf_grants",
              condition="PL majority in Germany-Poland co-production", notes="Germany-Poland bilateral treaty (1994)"),
    GraphEdge("treaty", "de-hu-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Germany-Hungary co-production", notes="Germany-Hungary bilateral treaty (1994)"),
    GraphEdge("treaty", "de-hu-bilateral", "unlocks", "program", "hu_nfi_grants",
              condition="HU majority in Germany-Hungary co-production", notes="Germany-Hungary bilateral treaty (1994)"),
    GraphEdge("treaty", "de-cz-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Germany-Czech co-production", notes="Germany-Czech Republic bilateral treaty (1994)"),
    GraphEdge("treaty", "de-cz-bilateral", "unlocks", "program", "cz_czech_film_fund",
              condition="CZ majority in Germany-Czech co-production", notes="Germany-Czech Republic bilateral treaty (1994)"),
    GraphEdge("treaty", "kr-fr-bilateral", "unlocks", "program", "kr_kofic_production",
              condition="KR majority in Korea-France co-production", notes="Korea-France bilateral treaty (2006)"),
    GraphEdge("treaty", "kr-fr-bilateral", "unlocks", "program", "fr_trip",
              condition="FR majority in Korea-France co-production", notes="Korea-France bilateral treaty (2006)"),
    GraphEdge("treaty", "kr-de-bilateral", "unlocks", "program", "kr_kofic_production",
              condition="KR majority in Korea-Germany co-production", notes="Korea-Germany bilateral treaty (2004)"),
    GraphEdge("treaty", "kr-de-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Korea-Germany co-production", notes="Korea-Germany bilateral treaty (2004)"),
    GraphEdge("treaty", "au-kr-bilateral", "unlocks", "program", "au_producer_offset",
              condition="AU majority in AU-Korea co-production", notes="Australia-Korea bilateral treaty (2006)"),
    GraphEdge("treaty", "au-kr-bilateral", "unlocks", "program", "kr_kofic_production",
              condition="KR majority in AU-Korea co-production", notes="Australia-Korea bilateral treaty (2006)"),
    GraphEdge("treaty", "ca-es-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-Spain co-production", notes="Canada-Spain bilateral treaty (1985)"),
    GraphEdge("treaty", "ca-es-bilateral", "unlocks", "program", "es_icaa_credit",
              condition="ES majority in Canada-Spain co-production", notes="Canada-Spain bilateral treaty (1985)"),
    GraphEdge("treaty", "ca-za-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-South Africa co-production", notes="Canada-South Africa bilateral treaty (1997)"),
    GraphEdge("treaty", "ca-za-bilateral", "unlocks", "program", "za_nfvf_fund",
              condition="ZA majority in Canada-South Africa co-production", notes="Canada-South Africa bilateral treaty (1997)"),
    GraphEdge("treaty", "ca-ch-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-Switzerland co-production", notes="Canada-Switzerland bilateral treaty (1988)"),
    GraphEdge("treaty", "ca-mx-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-Mexico co-production", notes="Canada-Mexico bilateral treaty (1999)"),
    GraphEdge("treaty", "ca-mx-bilateral", "unlocks", "program", "mx_fidecine",
              condition="MX majority in Canada-Mexico co-production", notes="Canada-Mexico bilateral treaty (1999)"),
    GraphEdge("treaty", "ca-cn-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-China co-production", notes="Canada-China bilateral treaty (1987)"),
    GraphEdge("treaty", "au-ie-bilateral", "unlocks", "program", "au_producer_offset",
              condition="AU majority in Australia-Ireland co-production", notes="Australia-Ireland bilateral treaty (2008)"),
    GraphEdge("treaty", "au-ie-bilateral", "unlocks", "program", "ie_section_481",
              condition="IE majority in Australia-Ireland co-production", notes="Australia-Ireland bilateral treaty (2008)"),
    GraphEdge("treaty", "au-de-bilateral", "unlocks", "program", "au_producer_offset",
              condition="AU majority in Australia-Germany co-production", notes="Australia-Germany bilateral treaty (2001)"),
    GraphEdge("treaty", "au-de-bilateral", "unlocks", "program", "de_dfff",
              condition="DE majority in Australia-Germany co-production", notes="Australia-Germany bilateral treaty (2001)"),
    GraphEdge("treaty", "ca-be-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-Belgium co-production", notes="Canada-Belgium bilateral treaty (1984)"),
    GraphEdge("treaty", "ca-be-bilateral", "unlocks", "program", "be_tax_shelter",
              condition="BE majority in Canada-Belgium co-production", notes="Canada-Belgium bilateral treaty (1984)"),
    GraphEdge("treaty", "ca-ie-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-Ireland co-production", notes="Canada-Ireland bilateral treaty (1989)"),
    GraphEdge("treaty", "ca-ie-bilateral", "unlocks", "program", "ie_section_481",
              condition="IE majority in Canada-Ireland co-production", notes="Canada-Ireland bilateral treaty (1989)"),
    GraphEdge("treaty", "ca-nz-bilateral", "unlocks", "program", "ca_federal_cptc",
              condition="CA majority in Canada-New Zealand co-production", notes="Canada-New Zealand bilateral treaty (1994)"),
    GraphEdge("treaty", "ca-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate",
              condition="NZ majority in Canada-New Zealand co-production", notes="Canada-New Zealand bilateral treaty (1994)"),

    # -------------------------------------------------------------------------
    # Co-production structures — three/four-country combinations
    # -------------------------------------------------------------------------
    # Eurimages trilateral: UK-FR-DE (the most common trilateral stack)
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "uk_avec",
              condition="UK is majority co-producer in Eurimages UK+FR+DE trilateral",
              notes="UK-France-Germany trilateral under Eurimages: UK AVEC + FR TRIP + DE DFFF all accessible"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "fr_trip",
              condition="FR is majority co-producer in Eurimages trilateral",
              notes="France-Germany-UK trilateral: TRIP accessible to French majority co-producer"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "de_dfff",
              condition="DE is majority co-producer in Eurimages trilateral",
              notes="Germany-France-UK trilateral: DFFF accessible to German majority co-producer"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "it_tax_credit_foreign",
              condition="IT is a co-producer in an Eurimages co-production",
              notes="Italian Tax Credit for Foreign Co-productions is accessible via Eurimages co-production"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "pl_pisf_grants",
              condition="PL is a co-producer in an Eurimages co-production",
              notes="PISF grants are accessible to Polish co-producers in Eurimages co-productions"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "no_nfi_grants",
              condition="NO is a co-producer in an Eurimages co-production",
              notes="NFI grants are accessible to Norwegian co-producers in Eurimages co-productions"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "cz_czech_film_fund",
              condition="CZ is a co-producer in an Eurimages co-production",
              notes="Czech Film Fund is accessible to Czech co-producers in Eurimages co-productions"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "hu_nfi_grants",
              condition="HU is a co-producer in an Eurimages co-production",
              notes="NFI Hungary grants accessible to Hungarian co-producers in Eurimages co-productions"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "pt_ica_grants",
              condition="PT is a co-producer in an Eurimages co-production",
              notes="ICA Portugal grants accessible to Portuguese co-producers in Eurimages co-productions"),
    GraphEdge("treaty", "eurimages-multilateral", "unlocks", "program", "at_ofi_grants",
              condition="AT is a co-producer in an Eurimages co-production",
              notes="ÖFI grants accessible to Austrian co-producers in Eurimages co-productions"),
    # Ibermedia: PT+ES+LATAM trilateral
    GraphEdge("treaty", "ibermedia-multilateral", "unlocks", "program", "pt_ica_grants",
              condition="PT is a co-producer in an Ibermedia trilateral",
              notes="ICA Portugal grants accessible to Portuguese co-producers in Ibermedia productions"),
    GraphEdge("treaty", "ibermedia-multilateral", "unlocks", "program", "es_icaa_credit",
              condition="ES is the majority co-producer in an Ibermedia production",
              notes="ICAA credit accessible to Spanish majority co-producers in Ibermedia productions"),
    GraphEdge("treaty", "ibermedia-multilateral", "unlocks", "program", "mx_fidecine",
              condition="MX is a co-producer in an Ibermedia production",
              notes="FIDECINE accessible to Mexican co-producers in Ibermedia productions"),
    GraphEdge("treaty", "ibermedia-multilateral", "unlocks", "program", "ar_incaa_grants",
              condition="AR is a co-producer in an Ibermedia production",
              notes="INCAA grants accessible to Argentine co-producers in Ibermedia productions"),
    GraphEdge("treaty", "ibermedia-multilateral", "unlocks", "program", "br_ancine_fund",
              condition="BR is a co-producer in an Ibermedia production",
              notes="ANCINE/FSA fund accessible to Brazilian co-producers in Ibermedia productions"),
    # European Convention bilateral (non-EU pairs)
    GraphEdge("treaty", "european-convention-coproduction", "unlocks", "program", "uk_avec",
              condition="UK is majority co-producer under European Convention",
              notes="European Convention unlocks AVEC for UK when UK is majority co-producer with European Convention signatory"),
    GraphEdge("treaty", "european-convention-coproduction", "unlocks", "program", "no_nfi_grants",
              condition="NO is a co-producer under European Convention",
              notes="European Convention provides alternative co-production route for Norway with non-EU Eurimages members"),
    GraphEdge("treaty", "european-convention-coproduction", "unlocks", "program", "ch_suissimage",
              condition="CH is a co-producer under European Convention",
              notes="European Convention provides co-production access for Switzerland (non-EU Eurimages member)"),

    # -------------------------------------------------------------------------
    # Additional complements — missing cross-program combinations
    # -------------------------------------------------------------------------
    GraphEdge("program", "gb_bfi_production", "complements", "program", "eu_eurimages",
              notes="BFI Film Fund and Eurimages combine for UK-majority European co-productions"),
    GraphEdge("program", "ie_screen_ireland_dev", "complements", "program", "eu_eurimages",
              notes="Screen Ireland development support and Eurimages production support combine for Irish-majority European co-productions"),
    GraphEdge("program", "dk_dfi_support", "complements", "program", "eu_eurimages",
              notes="DFI support and Eurimages combine for Danish-majority European co-productions"),
    GraphEdge("program", "fi_ses_grants", "complements", "program", "eu_eurimages",
              notes="SES Finland grants and Eurimages combine for Finnish-majority European co-productions"),
    GraphEdge("program", "no_nfi_grants", "complements", "program", "eu_eurimages",
              notes="NFI Norway grants and Eurimages combine for Norwegian-majority European co-productions"),
    GraphEdge("program", "at_ofi_grants", "complements", "program", "eu_eurimages",
              notes="ÖFI Austria grants and Eurimages combine for Austrian co-productions"),
    GraphEdge("program", "ro_film_rebate", "complements", "program", "eu_eurimages",
              notes="Romanian rebate and Eurimages combine for Romanian co-productions in European projects"),
    GraphEdge("program", "gr_cash_rebate", "complements", "program", "eu_eurimages",
              notes="Greek rebate and Eurimages combine for Greek-involved European co-productions"),
    GraphEdge("program", "bg_cash_rebate", "complements", "program", "eu_eurimages",
              notes="Bulgarian rebate and Eurimages combine for Bulgarian-involved European co-productions"),
    GraphEdge("program", "eu_eurimages", "complements", "program", "ibermedia_programme",
              notes="Eurimages and Ibermedia can combine for co-productions eligible for both (e.g. Spain-France-LATAM)"),
    GraphEdge("program", "nl_hbf", "complements", "program", "eu_eurimages",
              notes="Hubert Bals Fund development support and Eurimages production support combine for Global South co-productions"),
]


# ---------------------------------------------------------------------------
# Public registry — deduplicated by (source_slug, edge_type, target_slug)
# ---------------------------------------------------------------------------

_seen_edge_keys: set[tuple[str, str, str]] = set()
_deduped_edges: list[GraphEdge] = []
for _e in _EDGES:
    _k = (_e.source_slug, _e.edge_type, _e.target_slug)
    if _k not in _seen_edge_keys:
        _seen_edge_keys.add(_k)
        _deduped_edges.append(_e)

STRUCTURE_GRAPH_EDGES: list[GraphEdge] = _deduped_edges


# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------

def get_edges_from(source_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.source_slug == source_slug]


def get_edges_to(target_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.target_slug == target_slug]


def get_edges_by_type(edge_type: str) -> list[GraphEdge]:
    return [e for e in _EDGES if e.edge_type == edge_type]


def get_unlocked_by(source_slug: str) -> list[str]:
    return [e.target_slug for e in _EDGES
            if e.source_slug == source_slug and e.edge_type == "unlocks"]


def get_requirements(target_slug: str) -> list[GraphEdge]:
    return [e for e in _EDGES
            if e.target_slug == target_slug and e.edge_type == "requires"]


def get_incompatibilities(slug: str) -> list[str]:
    results: list[str] = []
    for e in _EDGES:
        if e.edge_type != "incompatible_with":
            continue
        if e.source_slug == slug:
            results.append(e.target_slug)
        elif e.target_slug == slug:
            results.append(e.source_slug)
    return results
