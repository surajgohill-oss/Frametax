"""
stacking_rules.py — Static stacking rule lookup for the Phase E optimizer.

Rules are encoded from Phase D migrations (0022, 0039, 0044) and from
structural analysis of the global incentive inventory.

No DB access. These rules parallel what is seeded in the DB via migrations
but are expressed in terms of program types and jurisdiction codes so the
optimizer can operate from GlobalProgramEntry without slug lookups.

Rule encoding hierarchy (first match wins):
  1. Named slug-pair rules (from migration data — highest precision)
  2. Structural type rules (government_assistance programs → spend_reduction)
  3. Default rules (grant + primary = allowed; same-type same-jur = mutually_exclusive)
"""
from __future__ import annotations

#: OH-001 fix: included in canonical_evaluation._compute_fingerprint()
#: so a stacking-compatibility/reduction-rule change invalidates cached
#: served evaluations, including combined-structure results. Bump on any
#: material change.
STACKING_RULES_VERSION = "1.0.0"

from app.data.global_inventory import GlobalProgramEntry
from app.optimization.types import StackingViolation


# ---------------------------------------------------------------------------
# Slug inference: maps name fragments to known slugs for high-precision rules
# ---------------------------------------------------------------------------

_NAME_SLUG_RULES: list[tuple[str, str, str]] = [
    # (jurisdiction_code, name_fragment_lower, slug)
    ("FR",     "trip",                        "fr_trip"),
    ("FR",     "avances sur recettes",        "fr_cnc_production"),
    ("FR",     "cnc france",                  "fr_cnc_production"),
    ("GB",     "audio visual expenditure",    "uk_avec"),
    ("GB",     "avec",                        "uk_avec"),
    ("GB",     "bfi film fund",               "gb_bfi_production"),
    ("IE",     "section 481",                 "ie_section_481"),
    ("MT",     "malta film commission",       "mt_mfc_rebate"),
    ("GR",     "greece cash rebate",          "gr_cash_rebate"),
    ("MU",     "mauritius edb",               "mu_edb_incentive"),
    ("MU",     "edb film rebate",             "mu_edb_incentive"),
    ("CA",     "canada production tax credit","ca_federal_cptc"),
    ("CA",     "cptc",                        "ca_federal_cptc"),
    ("CA",     "canada media fund",           "ca_cmf"),
    ("CA",     "cmf",                         "ca_cmf"),
    ("CA",     "telefilm canada",             "ca_telefilm_dev"),
    ("CA-ON",  "ontario film television",     "on_ofttc"),
    ("CA-ON",  "ontario production services", "on_opstc"),
    ("CA-ON",  "nohfc",                       "nohfc_production_fund"),
    ("CA-ON",  "northern ontario heritage",   "nohfc_production_fund"),
    ("AU",     "screen australia",            "au_screen_production"),
    ("AU",     "location offset",             "au_location_offset"),
    ("AU",     "producer offset",             "au_producer_offset"),
    ("EU",     "eurimages",                   "eu_eurimages"),
    ("EU",     "creative europe media",       "eu_media_fund"),
    ("NORDIC", "nordisk film",                "nordic_ftvf"),
    ("NL",     "hubert bals",                 "nl_hbf"),
    ("DE-BY",  "filmfernsehfonds",            "de_fff_bayern"),
    ("DE-BY",  "fff bayern",                  "de_fff_bayern"),
    ("DE-NW",  "medienstiftung nrw",          "de_nrw_filmstiftung"),
    ("SE-VG",  "film i väst",                 "film_i_vast"),
    ("SE-VG",  "film i vast",                 "film_i_vast"),
    ("IBERO",  "ibermedia",                   "ibermedia_programme"),
    # Wave-6 — Canadian provinces
    ("CA-BC",  "production services tax credit", "ca_bc_pstc"),
    ("CA-BC",  "bc production services",         "ca_bc_pstc"),
    ("CA-ON",  "opstc",                          "ca_on_opstc"),
    ("CA-QC",  "québec production tax",          "ca_qc_qprdp"),
    ("CA-QC",  "quebec production tax",          "ca_qc_qprdp"),
    ("CA-QC",  "qprdp",                          "ca_qc_qprdp"),
    # Wave-6 — Australian states
    ("AU-WA",  "screenwest",                     "au_screenwest"),
    # Wave-6 — US California
    ("US-CA",  "california film",                "us_ca_ftc"),
    # Existing programs: add slug rules for cleaner pair matching
    ("IT",     "italian tax credit for foreign", "it_tax_credit_foreign"),
    ("HR",     "croatia film cash rebate",       "hr_cash_rebate"),
    ("BG",     "bulgarian film industry",        "bg_cash_rebate"),
    ("MT",     "malta film commission",          "mt_mfc_rebate"),  # already in list; harmless duplicate
    # Grants Wave-3 — new grant programs
    ("CA",     "bell fund",                      "ca_bell_fund"),
    ("CA",     "national screen institute",      "ca_nsi_fund"),
    ("CA",     "nsi",                            "ca_nsi_fund"),
    ("DE",     "berlinale world cinema fund",    "de_berlinale_wcf"),
    ("AU",     "miff premiere fund",             "au_miff_premiere"),
    ("SE",     "göteborg film festival",         "se_goteborg_fund"),
    ("NO",     "norwegian film institute",       "no_nfi_grants"),
    ("FI",     "finnish film foundation",        "fi_ses_grants"),
    ("GB",     "creative england",               "gb_creative_england"),
    ("ZA",     "industrial development corporation", "za_idc_film"),
    # DB-sync programs (from migrations 0002/0007 synced to Python path)
    ("CA-ON",  "film and television tax credit", "on_ofttc"),
    ("CA-ON",  "ofttc",                          "on_ofttc"),
    ("CA-QC",  "film and television production", "qc_film_production"),
    ("CA-QC",  "sodec",                          "qc_film_production"),
    # Phase C — French/Belgian/German regional funds
    ("FR-IDF", "île-de-france",                  "fr_idf_regional"),
    ("FR-IDF", "ile-de-france",                  "fr_idf_regional"),
    ("FR-IDF", "cinema regional",                "fr_idf_regional"),
    ("FR-NAQ", "nouvelle-aquitaine",             "fr_naq_regional"),
    ("FR-ARA", "auvergne",                       "fr_ara_regional"),
    ("FR-ARA", "rhône-alpes",                    "fr_ara_regional"),
    ("FR-OCC", "occitanie",                      "fr_occ_regional"),
    ("BE-WAL", "wallimage",                      "be_wal_wallimage"),
    ("BE-VLG", "vaf",                            "be_vlg_vaf"),
    ("BE-VLG", "vlaams audiovisueel",            "be_vlg_vaf"),
    ("BE-BRU", "screen.brussels",                "be_bru_screen"),
    ("BE-BRU", "brussels production",            "be_bru_screen"),
    ("DE-NI",  "nordmedia",                      "de_ni_nordmedia"),
    # Phase E3 — German regional funds (wave-6 programs)
    ("DE-BB",  "medienboard",                    "de_bb_medienboard"),
    ("DE-BB",  "berlin-brandenburg",             "de_bb_medienboard"),
    ("DE-HH",  "film- und medienstiftung hamburg", "de_hh_film_hamburg"),
    ("DE-HH",  "film hamburg",                   "de_hh_film_hamburg"),
    ("DE-BW",  "mfg medien",                     "de_bw_mfg"),
    ("DE-BW",  "mfg",                            "de_bw_mfg"),
    ("DE-MDM", "mitteldeutsche",                 "de_mdm_mitteldeutsche"),
    ("DE-MDM", "mdm",                            "de_mdm_mitteldeutsche"),
    # Phase E3 — Italian regional funds (wave-6 programs)
    ("IT-LAZ", "lazio cinema",                   "it_laz_lazio_fc"),
    ("IT-LAZ", "lazio international",            "it_laz_lazio_fc"),
    ("IT-SIC", "sicilia film",                   "it_sic_sicilia_fc"),
    ("IT-CAM", "campania",                       "it_cam_campania_fc"),
    ("IT-TOS", "toscana",                        "it_tos_tuscany_fc"),
    ("IT-TOS", "tuscany",                        "it_tos_tuscany_fc"),
    ("IT-PIE", "piemonte",                       "it_pie_piemonte_fc"),
    ("IT-APU", "apulia",                         "it_apu_apulia_ff"),
    # Phase E3 — Spanish regional funds (wave-6 programs)
    ("ES-CAT", "icec",                           "es_cat_icec"),
    ("ES-CAT", "català de les empreses",         "es_cat_icec"),
    ("ES-AND", "andalucia film commission",      "es_and_andalusia"),
    ("ES-AND", "andalucía",                      "es_and_andalusia"),
    ("ES-GAL", "agadic",                         "es_gal_agadic"),
    ("ES-GAL", "galega",                         "es_gal_agadic"),
    ("ES-VAL", "institut valencià",              "es_val_ivc"),
    ("ES-VAL", "ivc",                            "es_val_ivc"),
    ("ES-EUS", "basque country",                 "es_eus_basque"),
    ("ES-EUS", "eusko",                          "es_eus_basque"),
    # Phase E3 — Australian states
    ("AU-SA",  "south australian film",          "au_sa_safc"),
    ("AU-SA",  "safc",                           "au_sa_safc"),
    # Phase E3 — Canada provincial slugs (aliases for existing)
    ("CA-ON",  "ontario production services",    "on_opstc"),
    # Phase E3 — Italian national credit
    ("IT",     "mic tax credit",                 "it_mic_national"),
    ("IT",     "tax credit nazionale",           "it_mic_national"),
    # Phase E3 — Danish Film Institute
    ("DK",     "danish film institute",          "dk_dfi_support"),
    # Phase E3 — FFA Germany national
    ("DE",     "filmförderungsanstalt",          "de_ffa"),
    ("DE",     "ffa",                            "de_ffa"),
    ("DE",     "german federal film fund",       "de_dfff"),
    ("DE",     "dfff",                           "de_dfff"),
    # Phase A closeout — broadcaster fund slugs
    ("GB",     "bbc films",                      "gb_bbc_films"),
    ("GB",     "film4",                          "gb_film4"),
    ("GB",     "channel 4 film",                 "gb_film4"),
    ("DE",     "zdf",                            "de_zdf"),
    ("DE",     "das kleine fernsehspiel",        "de_zdf"),
    ("DE",     "wdr",                            "de_wdr_ard"),
    ("DE",     "ard",                            "de_wdr_ard"),
    ("FR",     "arte france",                    "de_arte"),
    ("DE",     "arte",                           "de_arte"),
    ("FR",     "canal+",                         "fr_canal_plus"),
    ("FR",     "canal plus",                     "fr_canal_plus"),
    ("SE",     "svt",                            "se_svt"),
    ("NO",     "nrk",                            "no_nrk"),
    ("DK",     "dr",                             "dk_dr"),
    ("DK",     "danish broadcasting",            "dk_dr"),
    ("FI",     "yle",                            "fi_yle"),
    ("IE",     "rtÉ",                            "ie_rte"),
    ("IE",     "rte",                            "ie_rte"),
    ("IT",     "rai cinema",                     "it_rai_cinema"),
    ("ES",     "rtve",                           "es_rtve"),
    ("AT",     "orf",                            "at_orf"),
    ("AT",     "österreichisches filminstitut",  "at_ofi_grants"),
    ("AT",     "austrian film institute",        "at_ofi_grants"),
    ("NL",     "vpro",                           "nl_npo"),
    ("NL",     "npo",                            "nl_npo"),
    # Phase A closeout — additional national fund slugs
    ("PL",     "polski instytut",                "pl_pisf_grants"),
    ("PL",     "pisf",                           "pl_pisf_grants"),
    ("CZ",     "czech film fund",                "cz_czech_film_fund"),
    ("CZ",     "státní fond",                    "cz_czech_film_fund"),
    ("HU",     "nemzeti filmintézet",            "hu_nfi_grants"),
    ("HU",     "national film institute",        "hu_nfi_grants"),
    ("PT",     "ica",                            "pt_ica_grants"),
    ("PT",     "instituto do cinema",            "pt_ica_grants"),
    ("CH",     "succès cinéma",                  "ch_bak_grants"),
    ("CH",     "bak",                            "ch_bak_grants"),
    # ---------------------------------------------------------------------------
    # Phase A-D final sweep — slug inference for all previously unregistered programs
    # ---------------------------------------------------------------------------
    # Cash rebates — EU/Europe
    ("CY",     "cyprus film",                    "cy_film_rebate"),
    ("HU",     "hungary film tax rebate",        "hu_hipa_rebate"),
    ("HU",     "hipa",                           "hu_hipa_rebate"),
    ("NL",     "netherlands film production incentive", "nl_nfpi"),
    ("NL",     "nfpi",                           "nl_nfpi"),
    ("AT",     "fisa+",                          "at_fisa_plus"),
    ("AT",     "fisa plus",                      "at_fisa_plus"),
    ("CZ",     "czech film incentive",           "cz_film_incentive"),
    ("CZ",     "czech republic audiovisual",     "cz_film_incentive"),
    ("RO",     "romanian film office",           "ro_film_rebate"),
    ("PT",     "portugal film commission",       "pt_film_incentive"),
    ("PT",     "iapmei",                         "pt_film_incentive"),
    ("RS",     "serbia film commission",         "rs_film_rebate"),
    ("IS",     "icelandic film reimbursement",   "is_film_rebate"),
    ("IS",     "icelandic film",                 "is_film_rebate"),
    ("GB-SCT", "screen scotland production growth", "gb_sct_screen_production"),
    ("GB-WLS", "wales screen production fund",   "gb_wls_film_fund"),
    ("GB-WLS", "ffilm cymru",                    "gb_wls_film_fund"),
    ("AL",     "albanian national cinema",       "al_anca_rebate"),
    ("ME",     "film centre of montenegro",      "me_film_rebate"),
    ("MK",     "macedonian film agency",         "mk_mfa_rebate"),
    ("SI",     "slovenian film centre",          "si_sfc_rebate"),
    ("GE",     "georgian national film centre",  "ge_gnfc_rebate"),
    ("TR",     "turkey cinema general",          "tr_cinema_support"),
    # Cash rebates — Scandinavia / Nordic
    ("SE",     "sweden film commission",         "se_film_rebate"),
    ("NO",     "norwegian film commission",      "no_film_incentive"),
    ("FI",     "business finland film",          "fi_business_finland"),
    ("EE",     "film estonia",                   "ee_film_estonia"),
    ("LT",     "lithuanian film centre",         "lt_lcc_rebate"),
    ("LV",     "national film centre of latvia", "lv_nkmp_rebate"),
    ("SK",     "slovak audiovisual fund",        "sk_avf_incentive"),
    # Cash rebates — Asia-Pacific
    ("NZ",     "new zealand screen production",  "nz_nzspg"),
    ("NZ",     "nzspg",                          "nz_nzspg"),
    ("SG",     "singapore film commission",      "sg_sfc_production"),
    ("AU-NSW", "nsw government screen",          "au_nsw_screen"),
    ("AU-NSW", "create nsw",                     "au_nsw_screen"),
    ("AU-VIC", "vicscreen",                      "au_vic_vicscreen"),
    ("AU-QLD", "screen queensland production",   "au_qld_screen"),
    ("TH",     "thailand board of investment",   "th_boi_film"),
    ("MY",     "finas malaysia",                 "my_finas_rebate"),
    ("PH",     "film development council of the philippines", "ph_fdcp_incentive"),
    ("KR",     "korea film council",             "kr_kofic_location"),
    ("KR",     "kofic",                          "kr_kofic_location"),
    ("LK",     "sri lanka film commission",      "lk_film_rebate"),
    ("JP",     "japan film commission",          "jp_jloc_incentive"),
    ("JP",     "jloc",                           "jp_jloc_incentive"),
    ("TW",     "taiwan film and audiovisual",    "tw_tfai_rebate"),
    ("TW",     "tfai",                           "tw_tfai_rebate"),
    # Cash rebates — Middle East / Africa
    ("AE",     "dubai film commission",          "ae_dxb_dpi"),
    ("AE",     "dubai production incentive",     "ae_dxb_dpi"),
    ("AE",     "abu dhabi film commission",      "ae_adfc_rebate"),
    ("AE",     "adfc",                           "ae_adfc_rebate"),
    ("SA",     "saudi film commission",          "sa_sfc_rebate"),
    ("JO",     "royal film commission jordan",   "jo_rfc_rebate"),
    ("QA",     "qatar film commission",          "qa_film_rebate"),
    ("IL",     "israel film fund",               "il_maslool_rebate"),
    ("IL",     "maslool",                        "il_maslool_rebate"),
    ("MA",     "centre cinématographique marocain", "ma_ccm_rebate"),
    ("MA",     "ccm",                            "ma_ccm_rebate"),
    ("TN",     "tunisia national centre",        "tn_cnci_rebate"),
    ("KE",     "kenya film commission",          "ke_kfc_rebate"),
    ("ZA",     "nfvf",                           "za_dti_film_rebate"),
    ("ZA",     "department of trade & industry", "za_dti_film_rebate"),
    ("NA",     "namibia film commission",        "na_nfc_rebate"),
    # Cash rebates — Americas
    ("US-OR",  "oregon production investment",   "us_or_opif"),
    ("US-WA",  "washington state motion picture","us_wa_mpcp"),
    ("US-NC",  "north carolina film",            "us_nc_film_grant"),
    ("US-TX",  "texas moving image",             "us_tx_miip"),
    ("US-CO",  "colorado film incentive",        "us_co_film_incentive"),
    ("US-TN",  "tennessee film",                 "us_tn_film_incentive"),
    ("US-OK",  "oklahoma film enhancement",      "us_ok_film_rebate"),
    ("US-UT",  "utah motion picture",            "us_ut_film_incentive"),
    ("US-AZ",  "arizona motion picture",         "us_az_film_incentive"),
    ("CA-NS",  "nova scotia film",               "ca_ns_film_incentive"),
    ("CO",     "colombia film commission",       "co_film_rebate"),
    ("DO",     "dominican republic film",        "do_film_rebate"),
    ("UY",     "uruguay xxi",                    "uy_film_rebate"),
    ("AR",     "incaa",                          "ar_incaa_rebate"),
    ("CL",     "corfo",                          "cl_corfo_rebate"),
    # Production-support / facilitation programs
    ("BS",     "bahamas film commission",        "bs_film_commission"),
    ("BB",     "barbados film",                  "bb_film_commission"),
    ("PA",     "panama film commission",         "pa_film_commission"),
    ("CR",     "costa rica film commission",     "cr_film_commission"),
    ("EC",     "ecuador film commission",        "ec_film_commission"),
    ("EG",     "egypt film commission",          "eg_film_commission"),
    ("GH",     "ghana national film",            "gh_film_commission"),
    ("RW",     "rwanda development board",       "rw_film_commission"),
    ("TZ",     "tanzania film board",            "tz_film_commission"),
    ("SN",     "senegal bureau",                 "sn_film_commission"),
    ("KW",     "kuwait film committee",          "kw_film_commission"),
    ("BH",     "bahrain film commission",        "bh_film_commission"),
    ("KZ",     "kazakhfilm",                     "kz_film_commission"),
    ("VN",     "vietnam cinema department",      "vn_film_commission"),
    ("ID",     "indonesian film commission",     "id_film_commission"),
    ("KH",     "cambodia ministry of culture",   "kh_film_commission"),
    ("HK",     "create hong kong",               "hk_createhk"),
    ("BA",     "film centre bosnia",             "ba_film_centre"),
    ("FJ",     "fiji audio visual commission",   "fj_film_commission"),
    ("UZ",     "uzbekkino",                      "uz_film_commission"),
    ("OM",     "oman film commission",           "om_film_commission"),
    ("GY",     "guyana tourism authority film",  "gy_film_commission"),
    ("GT",     "guatemala film commission",      "gt_film_commission"),
    ("BW",     "botswana film commission",       "bw_film_commission"),
    ("ET",     "ethiopian film commission",      "et_film_commission"),
    ("UG",     "uganda film commission",         "ug_film_commission"),
    ("MZ",     "mozambique instituto",           "mz_film_commission"),
    ("ZM",     "zambia film commission",         "zm_film_commission"),
    ("ZW",     "zimbabwe film",                  "zw_film_commission"),
    ("CN",     "china film administration",      "cn_film_coproduction"),
    ("MN",     "mongolian film commission",      "mn_film_commission"),
    ("BD",     "bangladesh film development",    "bd_film_commission"),
    ("BY",     "belarusfilm",                    "by_film_commission"),
    ("GA",     "gabon ministry of culture",      "ga_film_commission"),
    ("SC",     "seychelles tourism board",       "sc_film_commission"),
    ("MV",     "maldives marketing",             "mv_film_commission"),
    ("BT",     "bhutan film commission",         "bt_film_commission"),
    # New Phase A categories — VFX, animation, post-production
    ("AU",     "post, digital and visual",       "au_pdv_offset"),
    ("AU",     "pdv offset",                     "au_pdv_offset"),
    ("NZ",     "new zealand post-production",    "nz_pdv_rebate"),
    ("CA-ON",  "ontario computer animation",     "ca_on_ocase"),
    ("CA-ON",  "ocase",                          "ca_on_ocase"),
    ("CA-BC",  "interactive digital media",      "ca_bc_idmtc"),
    ("CA-BC",  "idmtc",                          "ca_bc_idmtc"),
    ("IS",     "iceland post",                   "is_post_rebate"),
    ("IS",     "visual effects iceland",         "is_post_rebate"),
    ("SG",     "digital media content",          "sg_imda_digital"),
    ("SG",     "imda",                           "sg_imda_digital"),
    ("KR",     "kocca",                          "kr_kocca_animation"),
    ("KR",     "korea creative content",         "kr_kocca_animation"),
    ("FR",     "tax crédit jeu vidéo",           "fr_cnc_animation"),
    ("FR",     "cnc animation",                  "fr_cnc_animation"),
    ("JP",     "vipo",                           "jp_vipo_animation"),
    ("JP",     "visual industry promotion",      "jp_vipo_animation"),
    # New Phase A categories — export promotion
    ("GB",     "bfi international",              "gb_bfi_international"),
    ("FR",     "unifrance",                      "fr_unifrance"),
    ("DE",     "german films international",     "de_german_films"),
    ("IT",     "anica",                          "it_anica_export"),
    ("CA",     "telefilm export",                "ca_telefilm_export"),
    ("AU",     "screen australia international", "au_screen_international"),
    ("ES",     "icaa export",                    "es_icaa_export"),
    ("KR",     "kofic international",            "kr_kofic_export"),
    # New Phase A categories — workforce / training
    ("GB",     "screenskills",                   "gb_screenskills"),
    ("AU",     "screen australia talent",        "au_screen_talent"),
    ("IE",     "screen ireland development",     "ie_screen_ireland_dev"),
    # New Phase A categories — streamer support
    ("GB",     "netflix",                        "streamer_uk_local"),
    # New Phase A categories — tourism / destination marketing
    ("AU",     "tourism australia film",         "au_tourism_film"),
    ("NZ",     "tourism new zealand",            "nz_tourism_film"),
    ("IE",     "tourism ireland film",           "ie_tourism_film"),
    ("JO",     "jordan royal film commission tourism", "jo_rfc_tourism"),
    ("SC",     "seychelles tourism",             "sc_tourism_film"),
    ("MV",     "maldives",                       "mv_tourism_film"),
    ("FJ",     "fiji",                           "fj_tourism_film"),
    # Airline / transport production support
    ("AE",     "emirates",                       "ae_emirates_support"),
    ("NZ",     "air new zealand",                "nz_air_production"),
    # Swedish regional
    ("SE-SK",  "film i skåne",                   "se_sk_film_skane"),
    ("SE-AB",  "filmregion stockholm",           "se_ab_filmstockholm"),
    # Norwegian regional
    ("NO-VGN", "viken filmsenter",               "no_vgn_viken"),
    ("NO-INL", "midtnorsk filmsenter",           "no_inl_midtnorsk"),
    ("NO-ROG", "vestnorsk filmsenter",           "no_rog_vestnorsk"),
    ("NO-TRO", "nord norsk filmsenter",          "no_tro_nordnorsk"),
    ("NO-MRO", "film3",                          "no_mro_film3"),
    # Danish regional
    ("DK-CPH", "copenhagen film fund",           "dk_cph_film_fund"),
    ("DK-FYN", "film fyn",                       "dk_fyn_film"),
    # Australian state additional funds
    ("AU-VIC", "film victoria",                  "au_vic_film_victoria"),
    ("AU-NSW", "screen nsw",                     "au_nsw_screen_fund"),
    ("AU-TAS", "screen tasmania",                "au_tas_screen"),
    ("AU-NT",  "territory screen",               "au_nt_territory"),
    # UK additional regional
    ("GB-LON", "film london",                    "gb_lon_film_london"),
    ("GB",     "film hub midlands",              "gb_film_hub_midlands"),
    # Canadian additional
    ("CA-PE",  "film pei",                       "ca_pe_film_pei"),
    ("CA-NL",  "newfoundland",                   "ca_nl_film_nl"),
    ("CA-MB",  "manitoba film",                  "ca_mb_film_mb"),
    ("CA-NB",  "new brunswick film",             "ca_nb_film_nb"),
    # Additional national institutes
    ("GR",     "greek film centre",              "gr_gnf_grants"),
    ("SA-KSA", "saudi film commission",          "sa_sfc_grants"),
]


def infer_slug(entry: GlobalProgramEntry) -> str | None:
    """Infer the DB slug for a GlobalProgramEntry via name fragment matching."""
    name_lower = entry.program_name.lower()
    for jur, fragment, slug in _NAME_SLUG_RULES:
        if entry.jurisdiction_code == jur and fragment in name_lower:
            return slug
    return None


# ---------------------------------------------------------------------------
# Named slug-pair stacking rules (from DB migrations 0007, 0022, 0044)
# Key: frozenset({slug_a, slug_b})
# ---------------------------------------------------------------------------

_SLUG_PAIR_RULES: dict[frozenset, dict] = {
    # Migration 0007 — NOHFC spend reductions
    frozenset({"nohfc_production_fund", "on_ofttc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC grant reduces OFTTC qualifying labour expenditure basis "
            "(OMDC guidelines)."
        ),
    },
    frozenset({"nohfc_production_fund", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC grant is government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    # Migration 0044 — Fund/credit interactions
    frozenset({"fr_cnc_production", "fr_trip"}): {
        "rule_type": "allowed",
        "condition_text": (
            "CNC avance and TRIP operate on separate eligibility tracks. "
            "Co-productions may access both under treaty arrangements."
        ),
    },
    frozenset({"gb_bfi_production", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI equity investment does not reduce UK qualifying expenditure "
            "for AVEC purposes (co-financing, not government assistance)."
        ),
    },
    frozenset({"eu_eurimages", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to UK co-producers does not reduce "
            "UK qualifying expenditure for AVEC."
        ),
    },
    frozenset({"eu_eurimages", "ie_section_481"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Irish co-producers does not reduce "
            "Irish qualifying expenditure for Section 481."
        ),
    },
    frozenset({"au_screen_production", "au_location_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screen Australia equity is government financial assistance; "
            "reduces qualifying Australian production expenditure (QAPE) "
            "for Location Offset (ITAA97 §376-170)."
        ),
    },
    frozenset({"au_screen_production", "au_producer_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screen Australia equity is government financial assistance; "
            "reduces QAPE for Producer Offset."
        ),
    },
    frozenset({"ca_cmf", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under ITA §125.4; "
            "reduce qualified labour expenditure before computing CPTC (T4283)."
        ),
    },
    frozenset({"ca_telefilm_dev", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    # Migration 0022 — Ontario/BC/QC domestic-vs-foreign-service track rules
    # CPTC (domestic content ITA §125.4) and PSTC (foreign service ITA §125.5) are
    # mutually exclusive production tracks — a production cannot be both.
    frozenset({"ca_bc_pstc", "ca_federal_cptc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": (
            "CPTC applies only to Canadian domestic content productions (ITA §125.4). "
            "BC PSTC applies only to accredited foreign service productions (ITA §125.5). "
            "A production cannot simultaneously qualify for both — production type is mutually exclusive."
        ),
    },
    frozenset({"on_opstc", "ca_federal_cptc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": (
            "CPTC applies only to Canadian domestic content productions (ITA §125.4). "
            "Ontario OPSTC applies only to accredited foreign service productions (ITA §125.5). "
            "A production cannot simultaneously qualify for both — production type is mutually exclusive."
        ),
    },
    frozenset({"on_ofttc", "on_opstc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": (
            "OFTTC applies to Ontario domestic Canadian content productions. "
            "OPSTC applies to foreign service productions using Ontario. "
            "A production cannot be both a domestic content production (OFTTC) and a foreign "
            "service production (OPSTC) simultaneously."
        ),
    },
    # OFTTC is government assistance reducing CPTC qualified labour (ITA §125.4)
    frozenset({"on_ofttc", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "OFTTC tax credit is government assistance under ITA §125.4(1)(b) and must be "
            "deducted from Qualified Canadian Labour Expenditure (QCLE) before computing CPTC. "
            "Net QCLE = gross QCLE minus OFTTC amount received or receivable."
        ),
    },
    # QC SODEC domestic credit reduces CPTC basis
    frozenset({"qc_film_production", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Quebec SODEC film production credit is government assistance under ITA §125.4(1)(b). "
            "QC credit amount must be deducted from QCLE before computing CPTC."
        ),
    },
    # UK AVEC + IE Section 481 — allowed for multi-territory co-productions
    frozenset({"uk_avec", "ie_section_481"}): {
        "rule_type": "allowed",
        "condition_text": (
            "UK AVEC and IE Section 481 can both be claimed for the same production when "
            "qualifying expenditure is incurred in both the UK and Ireland. "
            "Each credit applies only to its own territory's qualifying spend — no double-counting."
        ),
    },
    # QPRDP (foreign service track) can stack with CPTC — but production type means
    # they're typically different tracks. Conditionally allowed for co-productions.
    frozenset({"ca_qc_qprdp", "ca_federal_cptc"}): {
        "rule_type": "conditional",
        "condition_text": (
            "Quebec QPRDP (foreign service) and CPTC (domestic content) are typically "
            "different production tracks. Stacking may be possible for official treaty "
            "co-productions where both domestic and foreign elements qualify. "
            "Legal review required before claiming both."
        ),
    },
    # Government assistance (CMF) reduces provincial tax credit qualifying basis too
    frozenset({"ca_cmf", "ca_bc_pstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under provincial income tax acts; "
            "reduce qualifying BC labour expenditure for PSTC computation."
        ),
    },
    frozenset({"ca_cmf", "on_opstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under Ontario CTA; "
            "reduce qualifying Ontario labour expenditure for OPSTC computation."
        ),
    },
    frozenset({"nohfc_production_fund", "on_opstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC is government assistance under Ontario CTA; "
            "reduces qualifying Ontario labour expenditure for OPSTC (OMDC guidelines)."
        ),
    },
    # Eurimages stacks with additional national incentives
    frozenset({"eu_eurimages", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Italian co-producers does not reduce "
            "Italian qualifying expenditure for the MiC tax credit for foreign productions."
        ),
    },
    frozenset({"eu_eurimages", "mt_mfc_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Maltese co-producers does not reduce "
            "qualifying expenditure for Malta Film Commission rebate."
        ),
    },
    frozenset({"eu_eurimages", "hr_cash_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Croatian co-producers does not reduce "
            "qualifying expenditure for HAVC Croatia cash rebate."
        ),
    },
    # Screenwest (WA) is government assistance → reduces Australian offset QAPE
    frozenset({"au_screenwest", "au_location_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance is government financial assistance; "
            "reduces qualifying Australian production expenditure (QAPE) for the Location Offset."
        ),
    },
    frozenset({"au_screenwest", "au_screen_production"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance reduces qualifying Australian production expenditure "
            "for Screen Australia grant eligibility and matching calculations."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase D.5 — expanded stacking interaction graph
    # ---------------------------------------------------------------------------
    # UK devolved regions + AVEC: all allowed (each qualifies on its own territory's spend)
    frozenset({"gb_scot_creative_scotland", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Creative Scotland equity is not government assistance reducing UK qualifying expenditure "
            "for AVEC — it is co-financing. Both can be claimed on qualifying UK spend."
        ),
    },
    frozenset({"gb_wls_creative_wales", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Creative Wales equity is co-financing, not government assistance. "
            "Does not reduce AVEC qualifying UK expenditure."
        ),
    },
    frozenset({"gb_nir_northern_ireland", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Northern Ireland Screen funding is co-financing, not government assistance. "
            "Does not reduce AVEC qualifying UK expenditure."
        ),
    },
    frozenset({"gb_yrk_screen_yorkshire", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Screen Yorkshire equity is co-financing, not government assistance. "
            "Does not reduce AVEC qualifying UK expenditure."
        ),
    },
    # German regional funds + DFFF: all allowed
    frozenset({"de_fff_bayern", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "FFF Bayern regional fund and DFFF national fund operate on separate "
            "application tracks and may both be claimed for the same production "
            "when production qualifies under each fund's criteria independently."
        ),
    },
    frozenset({"de_nrw_filmstiftung", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Filmstiftung NRW and DFFF operate on separate tracks. "
            "Both may be claimed for the same production when qualifying criteria are met independently."
        ),
    },
    frozenset({"de_ni_nordmedia", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "nordmedia (Lower Saxony / Bremen) and DFFF operate on separate application tracks. "
            "Both may be claimed for the same production."
        ),
    },
    # Belgian tax shelter + Belgian regional funds: all allowed
    frozenset({"be_tax_shelter", "be_wal_wallimage"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Belgian tax shelter and Wallimage operate on independent tracks. "
            "Tax shelter is a financing instrument; Wallimage is a regional production fund. "
            "Both may be used on the same production with Wallonia qualifying spend."
        ),
    },
    frozenset({"be_tax_shelter", "be_vlg_vaf"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Belgian tax shelter and VAF Flanders operate on independent tracks. "
            "Tax shelter is a financing instrument; VAF is a regional production fund. "
            "Both may be used on the same production with Flanders qualifying spend."
        ),
    },
    frozenset({"be_tax_shelter", "be_bru_screen"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Belgian tax shelter and Screen.Brussels operate on independent tracks. "
            "Both may be used on the same production with Brussels qualifying spend."
        ),
    },
    # Eurimages + DFFF: allowed
    frozenset({"eu_eurimages", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to German co-producers does not reduce "
            "German qualifying expenditure for DFFF. Each fund applies to its own "
            "national qualifying spend independently."
        ),
    },
    # Eurimages + Belgian tax shelter: allowed
    frozenset({"eu_eurimages", "be_tax_shelter"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Belgian co-producers does not reduce "
            "Belgian tax shelter qualifying eligible expenditure. "
            "Both are available for the same official European co-production."
        ),
    },
    # French national + French regional: all allowed
    frozenset({"fr_cnc_production", "fr_idf_regional"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Île-de-France regional aid and CNC national support operate on independent tracks. "
            "Both may be claimed for the same production with qualifying Paris-region spend."
        ),
    },
    frozenset({"fr_cnc_production", "fr_naq_regional"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Nouvelle-Aquitaine regional aid and CNC national support operate on independent tracks."
        ),
    },
    frozenset({"fr_cnc_production", "fr_ara_regional"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Auvergne-Rhône-Alpes regional aid and CNC national support operate on independent tracks."
        ),
    },
    frozenset({"fr_cnc_production", "fr_occ_regional"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Occitanie regional aid and CNC national support operate on independent tracks."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Germany: remaining regional funds + DFFF
    # ---------------------------------------------------------------------------
    frozenset({"de_bb_medienboard", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Medienboard Berlin-Brandenburg and DFFF operate on separate application tracks. "
            "Both may be claimed for the same production when qualifying criteria are met independently."
        ),
    },
    frozenset({"de_hh_film_hamburg", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Film Hamburg and DFFF operate on separate application tracks. "
            "Both may be claimed for the same production."
        ),
    },
    frozenset({"de_bw_mfg", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "MFG Baden-Württemberg and DFFF operate on separate application tracks. "
            "Both may be claimed for the same production."
        ),
    },
    frozenset({"de_mdm_mitteldeutsche", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "MDM Mitteldeutsche Medienförderung and DFFF operate on separate application tracks. "
            "Both may be claimed for the same production."
        ),
    },
    # Germany national FFA + all regional: allowed
    frozenset({"de_ffa", "de_fff_bayern"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and FFF Bayern operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_nrw_filmstiftung"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and Filmstiftung NRW operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_bb_medienboard"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and Medienboard Berlin-Brandenburg operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_ni_nordmedia"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and nordmedia operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_hh_film_hamburg"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and Film Hamburg operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_bw_mfg"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and MFG Baden-Württemberg operate on independent tracks.",
    },
    frozenset({"de_ffa", "de_mdm_mitteldeutsche"}): {
        "rule_type": "allowed",
        "condition_text": "FFA and MDM Mitteldeutsche Medienförderung operate on independent tracks.",
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Italy: regional funds + MiC national credit
    # ---------------------------------------------------------------------------
    frozenset({"it_laz_lazio_fc", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Lazio Cinema International regional fund and Italian MiC tax credit operate on "
            "independent tracks. Both claimable on qualifying Italian spend."
        ),
    },
    frozenset({"it_sic_sicilia_fc", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": "Sicilia Film Commission and MiC national credit operate on independent tracks.",
    },
    frozenset({"it_cam_campania_fc", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": "Campania Film Commission and MiC national credit operate on independent tracks.",
    },
    frozenset({"it_tos_tuscany_fc", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": "Tuscany Film Commission and MiC national credit operate on independent tracks.",
    },
    frozenset({"it_pie_piemonte_fc", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": "Piemonte Film Commission and MiC national credit operate on independent tracks.",
    },
    frozenset({"it_apu_apulia_ff", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": "Apulia Film Fund and MiC national credit operate on independent tracks.",
    },
    # Italian regional: Eurimages + all Italian regional (allowed)
    frozenset({"eu_eurimages", "it_laz_lazio_fc"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Lazio regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "it_sic_sicilia_fc"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Sicilia regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "it_tos_tuscany_fc"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Tuscany regional qualifying spend.",
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Spain: regional funds + ICAA national (all allowed)
    # ---------------------------------------------------------------------------
    frozenset({"es_cat_icec", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Catalonia ICEC regional support and Spanish ICAA national deduction "
            "operate on independent tracks."
        ),
    },
    frozenset({"es_and_andalusia", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": "Andalusia Film Commission support and ICAA operate on independent tracks.",
    },
    frozenset({"es_gal_agadic", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": "Galicia AGADIC support and ICAA operate on independent tracks.",
    },
    frozenset({"es_val_ivc", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": "Valencia IVC support and ICAA operate on independent tracks.",
    },
    frozenset({"es_eus_basque", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": "Basque Country film support and ICAA operate on independent tracks.",
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Australia: Producer Offset + state funds
    # ---------------------------------------------------------------------------
    frozenset({"au_sa_safc", "au_producer_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "SAFC (South Australian Film Corporation) financial assistance is government "
            "financial assistance reducing qualifying Australian production expenditure (QAPE) "
            "for Producer Offset (ITAA97 §376-170)."
        ),
    },
    frozenset({"au_sa_safc", "au_location_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "SAFC financial assistance reduces qualifying QAPE for Location Offset."
        ),
    },
    frozenset({"au_sa_safc", "au_screen_production"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "SAFC financial assistance reduces qualifying QAPE for Screen Australia matching calculations."
        ),
    },
    # Producer Offset + Screen Australia (already have spend_reduction) - confirm both directions
    frozenset({"au_miff_premiere", "au_producer_offset"}): {
        "rule_type": "allowed",
        "condition_text": (
            "MIFF Premiere Fund grant is not government financial assistance; "
            "does not reduce QAPE for Producer Offset."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Canada: additional provincial + federal combinations
    # ---------------------------------------------------------------------------
    # BC PSTC (foreign service) — CMF spend_reduction already exists;
    # add BC Film Investment Program (BCPTC) rules if it arises from treaty
    frozenset({"ca_bell_fund", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Bell Fund grants are government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    frozenset({"ca_nsi_fund", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NSI fund grants are government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    # CMF + Ontario OFTTC (spend_reduction both ways)
    frozenset({"ca_cmf", "on_ofttc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under Ontario CTA; "
            "reduce qualifying Ontario labour expenditure for OFTTC computation."
        ),
    },
    # CMF + QC SODEC (spend_reduction)
    frozenset({"ca_cmf", "qc_film_production"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under Quebec CTA; "
            "reduce qualifying Quebec labour expenditure for SODEC credit computation."
        ),
    },
    # Telefilm + provincial credits (spend_reduction)
    frozenset({"ca_telefilm_dev", "on_ofttc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance; "
            "reduces qualifying Ontario labour expenditure for OFTTC."
        ),
    },
    frozenset({"ca_telefilm_dev", "qc_film_production"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance; "
            "reduces qualifying Quebec labour expenditure for SODEC credit."
        ),
    },
    frozenset({"ca_telefilm_dev", "ca_qc_qprdp"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance; "
            "reduces qualifying Quebec labour expenditure for QPRDP."
        ),
    },
    frozenset({"ca_telefilm_dev", "ca_bc_pstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance; "
            "reduces qualifying BC labour expenditure for PSTC."
        ),
    },
    # NOHFC + QC SODEC: no overlap (different provinces) — not applicable
    # Bell Fund + OFTTC (spend_reduction)
    frozenset({"ca_bell_fund", "on_ofttc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Bell Fund grants are government assistance under Ontario CTA; "
            "reduce qualifying Ontario labour expenditure for OFTTC."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Eurimages: additional national fund interactions
    # ---------------------------------------------------------------------------
    frozenset({"eu_eurimages", "fr_tax_credit_cinema"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to French co-producers does not reduce "
            "French qualifying expenditure for the tax crédit cinéma."
        ),
    },
    frozenset({"eu_eurimages", "fr_cnc_production"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support does not reduce CNC avance sur recettes eligibility."
        ),
    },
    frozenset({"eu_eurimages", "gr_cash_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Greek co-producers does not reduce "
            "Greek qualifying expenditure for the Hellenic cash rebate."
        ),
    },
    frozenset({"eu_eurimages", "no_nfi_grants"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support does not reduce Norwegian Film Institute qualifying spend."
        ),
    },
    frozenset({"eu_eurimages", "fi_ses_grants"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support does not reduce Finnish Film Foundation qualifying spend."
        ),
    },
    frozenset({"eu_eurimages", "nl_hbf"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support does not reduce Hubert Bals Fund qualifying spend."
        ),
    },
    frozenset({"eu_eurimages", "bg_cash_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support does not reduce Bulgarian cash rebate qualifying spend."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — BFI + devolved/regional UK funds
    # ---------------------------------------------------------------------------
    frozenset({"gb_bfi_production", "gb_scot_creative_scotland"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI Film Fund and Creative Scotland both provide equity co-financing "
            "on independent terms. Both may invest in the same production."
        ),
    },
    frozenset({"gb_bfi_production", "gb_wls_creative_wales"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI Film Fund and Creative Wales both provide equity co-financing. "
            "Both may invest in the same production."
        ),
    },
    frozenset({"gb_bfi_production", "gb_nir_northern_ireland"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI Film Fund and Northern Ireland Screen both provide equity co-financing. "
            "Both may invest in the same production."
        ),
    },
    frozenset({"gb_bfi_production", "gb_yrk_screen_yorkshire"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI Film Fund and Screen Yorkshire both provide equity co-financing. "
            "Both may invest in the same production."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase E3 — Ibermedia interactions
    # ---------------------------------------------------------------------------
    frozenset({"ibermedia_programme", "fr_tax_credit_cinema"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Ibermedia grants do not reduce French qualifying expenditure for tax crédit cinéma. "
            "Applicable when Ibermedia project includes French co-producer."
        ),
    },
    frozenset({"ibermedia_programme", "ie_section_481"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Ibermedia grants do not reduce Irish qualifying expenditure for Section 481. "
            "Portugal and Spain are Ibermedia members; Ireland is not, but applicable "
            "for IE minority service arrangements."
        ),
    },
    frozenset({"ibermedia_programme", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Ibermedia and Eurimages both operate as co-production funds on independent tracks. "
            "Portugal and Spain are members of both; trilateral structures may access both."
        ),
    },
    # ---------------------------------------------------------------------------
    # Phase A closeout — broadcaster fund stacking interactions
    # ---------------------------------------------------------------------------
    # UK broadcaster funds + AVEC: all allowed (co-financing, not government assistance)
    frozenset({"gb_bbc_films", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BBC Films co-financing is not government assistance for AVEC purposes. "
            "Does not reduce UK qualifying expenditure. Both available for same production."
        ),
    },
    frozenset({"gb_film4", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Film4/Channel 4 co-financing is not government assistance for AVEC purposes. "
            "Does not reduce UK qualifying expenditure."
        ),
    },
    frozenset({"gb_bbc_films", "gb_bfi_production"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BBC Films and BFI Film Fund both provide equity co-financing. "
            "Both may invest in the same production independently."
        ),
    },
    frozenset({"gb_film4", "gb_bfi_production"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Film4 and BFI Film Fund both provide equity co-financing. "
            "Both may invest in the same production independently."
        ),
    },
    frozenset({"gb_bbc_films", "gb_scot_creative_scotland"}): {
        "rule_type": "allowed",
        "condition_text": "BBC Films and Creative Scotland both provide co-financing independently.",
    },
    frozenset({"gb_bbc_films", "gb_nir_northern_ireland"}): {
        "rule_type": "allowed",
        "condition_text": "BBC Films and Northern Ireland Screen both provide co-financing independently.",
    },
    frozenset({"gb_bbc_films", "gb_wls_creative_wales"}): {
        "rule_type": "allowed",
        "condition_text": "BBC Films and Creative Wales both provide co-financing independently.",
    },
    frozenset({"gb_film4", "gb_scot_creative_scotland"}): {
        "rule_type": "allowed",
        "condition_text": "Film4 and Creative Scotland both provide co-financing independently.",
    },
    frozenset({"gb_film4", "gb_nir_northern_ireland"}): {
        "rule_type": "allowed",
        "condition_text": "Film4 and Northern Ireland Screen both provide co-financing independently.",
    },
    # German broadcaster funds + DFFF: allowed
    frozenset({"de_zdf", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": (
            "ZDF co-production does not reduce German qualifying spend for DFFF. "
            "Both available for same production."
        ),
    },
    frozenset({"de_wdr_ard", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": "WDR/ARD co-production does not reduce German qualifying spend for DFFF.",
    },
    frozenset({"de_arte", "de_dfff"}): {
        "rule_type": "allowed",
        "condition_text": "Arte co-production does not reduce German qualifying spend for DFFF.",
    },
    frozenset({"de_zdf", "de_ffa"}): {
        "rule_type": "allowed",
        "condition_text": "ZDF co-production and FFA operate on independent tracks.",
    },
    frozenset({"de_arte", "de_ffa"}): {
        "rule_type": "allowed",
        "condition_text": "Arte and FFA operate on independent tracks.",
    },
    frozenset({"de_arte", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Arte co-production and Eurimages both operate on independent financing tracks.",
    },
    frozenset({"de_zdf", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "ZDF co-production and Eurimages both operate on independent financing tracks.",
    },
    # French broadcaster + CNC national: allowed
    frozenset({"fr_canal_plus", "fr_cnc_production"}): {
        "rule_type": "allowed",
        "condition_text": (
            "CANAL+ pre-purchase does not reduce CNC avance sur recettes eligibility. "
            "Both available for same French production."
        ),
    },
    frozenset({"fr_canal_plus", "fr_trip"}): {
        "rule_type": "allowed",
        "condition_text": "CANAL+ pre-purchase does not reduce qualifying French spend for TRIP.",
    },
    frozenset({"de_arte", "fr_cnc_production"}): {
        "rule_type": "allowed",
        "condition_text": "Arte co-production does not reduce CNC avance sur recettes eligibility.",
    },
    frozenset({"de_arte", "fr_trip"}): {
        "rule_type": "allowed",
        "condition_text": "Arte co-production does not reduce qualifying French spend for TRIP.",
    },
    # Irish broadcaster + Section 481
    frozenset({"ie_rte", "ie_section_481"}): {
        "rule_type": "allowed",
        "condition_text": (
            "RTÉ co-investment is not government assistance reducing Irish qualifying expenditure "
            "for Section 481. Both available for same Irish production."
        ),
    },
    frozenset({"ie_rte", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "RTÉ co-investment and Eurimages both operate on independent financing tracks.",
    },
    # Italian broadcaster + MiC credit
    frozenset({"it_rai_cinema", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": (
            "RAI Cinema broadcaster obligation does not reduce qualifying Italian expenditure "
            "for the MiC tax credit. Both available for same Italian production."
        ),
    },
    frozenset({"it_rai_cinema", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "RAI Cinema and Eurimages both operate on independent financing tracks.",
    },
    # Spanish broadcaster + ICAA
    frozenset({"es_rtve", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": (
            "RTVE broadcaster investment obligation does not reduce qualifying Spanish expenditure "
            "for the ICAA audiovisual production deduction. Both available for same Spanish production."
        ),
    },
    frozenset({"es_rtve", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "RTVE and Eurimages both operate on independent financing tracks.",
    },
    frozenset({"es_rtve", "ibermedia_programme"}): {
        "rule_type": "allowed",
        "condition_text": "RTVE and Ibermedia both operate on independent financing tracks.",
    },
    # Nordic broadcaster + national grant: allowed
    frozenset({"se_svt", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "SVT co-production and Eurimages both operate on independent financing tracks.",
    },
    frozenset({"no_nrk", "no_nfi_grants"}): {
        "rule_type": "allowed",
        "condition_text": (
            "NRK broadcaster commission does not reduce NFI selective grant qualifying spend. "
            "Both available for same Norwegian production."
        ),
    },
    frozenset({"no_nrk", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "NRK and Eurimages both operate on independent financing tracks.",
    },
    frozenset({"dk_dr", "dk_dfi_support"}): {
        "rule_type": "allowed",
        "condition_text": (
            "DR broadcaster commission does not reduce DFI selective grant qualifying spend. "
            "Both available for same Danish production."
        ),
    },
    frozenset({"dk_dr", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "DR and Eurimages both operate on independent financing tracks.",
    },
    frozenset({"fi_yle", "fi_ses_grants"}): {
        "rule_type": "allowed",
        "condition_text": (
            "YLE broadcaster commission does not reduce SES (Finnish Film Foundation) qualifying spend. "
            "Both available for same Finnish production."
        ),
    },
    frozenset({"fi_yle", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "YLE and Eurimages both operate on independent financing tracks.",
    },
    # ---------------------------------------------------------------------------
    # Phase D closeout — additional stacking rules
    # ---------------------------------------------------------------------------
    # AU state funds (mutually exclusive with each other — only one state per production)
    frozenset({"au_screenwest", "au_sa_safc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": (
            "Australian state film funds (Screenwest WA and SAFC SA) are generally mutually exclusive "
            "as they require territorial spend in competing states. "
            "A production qualifying primarily in WA would not typically also qualify in SA."
        ),
    },
    # IT regional funds — can stack if production spends in multiple regions
    frozenset({"it_laz_lazio_fc", "it_sic_sicilia_fc"}): {
        "rule_type": "conditional",
        "condition_text": (
            "Multiple Italian regional film commissions may be stackable if the production "
            "incurs qualifying spend in both regions. Requires separate applications to each "
            "regional commission and regional spend documentation."
        ),
    },
    frozenset({"it_laz_lazio_fc", "it_cam_campania_fc"}): {
        "rule_type": "conditional",
        "condition_text": (
            "Lazio and Campania regional funds may be stackable if qualifying spend is incurred "
            "in both regions. Each commission reviews regional spend independently."
        ),
    },
    frozenset({"it_laz_lazio_fc", "it_pie_piemonte_fc"}): {
        "rule_type": "conditional",
        "condition_text": (
            "Lazio and Piemonte regional funds may be stackable if qualifying spend is incurred "
            "in both regions."
        ),
    },
    frozenset({"it_laz_lazio_fc", "it_apu_apulia_ff"}): {
        "rule_type": "conditional",
        "condition_text": "Lazio and Apulia regional funds may be stackable with qualifying regional spend in each.",
    },
    frozenset({"it_laz_lazio_fc", "it_tos_tuscany_fc"}): {
        "rule_type": "conditional",
        "condition_text": "Lazio and Tuscany regional funds may be stackable with qualifying regional spend in each.",
    },
    frozenset({"it_sic_sicilia_fc", "it_cam_campania_fc"}): {
        "rule_type": "conditional",
        "condition_text": "Sicilia and Campania regional funds may be stackable with qualifying regional spend in each.",
    },
    frozenset({"it_pie_piemonte_fc", "it_apu_apulia_ff"}): {
        "rule_type": "conditional",
        "condition_text": "Piemonte and Apulia regional funds may be stackable with qualifying regional spend in each.",
    },
    # ES regional funds — mutually exclusive (typically one region)
    frozenset({"es_cat_icec", "es_and_andalusia"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": (
            "Spanish regional film funds (Catalonia ICEC and Andalusia Film Commission) are generally "
            "mutually exclusive as they require territorial spend in each respective region. "
            "A production cannot typically meet qualifying spend thresholds in both simultaneously."
        ),
    },
    frozenset({"es_cat_icec", "es_gal_agadic"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Catalonia and Galicia regional funds are generally mutually exclusive by territorial spend.",
    },
    frozenset({"es_cat_icec", "es_val_ivc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Catalonia ICEC and Valencia IVC are generally mutually exclusive by territorial spend.",
    },
    frozenset({"es_cat_icec", "es_eus_basque"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Catalonia ICEC and Basque Audiovisual are generally mutually exclusive by territorial spend.",
    },
    frozenset({"es_and_andalusia", "es_gal_agadic"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Andalusia and Galicia regional funds are generally mutually exclusive by territorial spend.",
    },
    frozenset({"es_and_andalusia", "es_val_ivc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Andalusia Film Commission and Valencia IVC are generally mutually exclusive by territorial spend.",
    },
    frozenset({"es_gal_agadic", "es_val_ivc"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "Galicia AGADIC and Valencia IVC are generally mutually exclusive by territorial spend.",
    },
    # FR regional funds — conditional (production spanning multiple regions is uncommon)
    frozenset({"fr_idf_regional", "fr_naq_regional"}): {
        "rule_type": "conditional",
        "condition_text": (
            "French regional funds (Île-de-France and Nouvelle-Aquitaine) may be conditionally "
            "stackable if a production has qualifying spend in both regions, but this is unusual "
            "and requires separate applications to each regional council."
        ),
    },
    frozenset({"fr_idf_regional", "fr_ara_regional"}): {
        "rule_type": "conditional",
        "condition_text": "IDF and Auvergne-Rhône-Alpes regional funds conditionally stackable with regional spend in each.",
    },
    frozenset({"fr_idf_regional", "fr_occ_regional"}): {
        "rule_type": "conditional",
        "condition_text": "IDF and Occitanie regional funds conditionally stackable with regional spend in each.",
    },
    frozenset({"fr_naq_regional", "fr_ara_regional"}): {
        "rule_type": "conditional",
        "condition_text": "Nouvelle-Aquitaine and Auvergne-Rhône-Alpes regional funds conditionally stackable.",
    },
    frozenset({"fr_naq_regional", "fr_occ_regional"}): {
        "rule_type": "conditional",
        "condition_text": "Nouvelle-Aquitaine and Occitanie regional funds conditionally stackable.",
    },
    frozenset({"fr_ara_regional", "fr_occ_regional"}): {
        "rule_type": "conditional",
        "condition_text": "Auvergne-Rhône-Alpes and Occitanie regional funds conditionally stackable.",
    },
    # TRIP (French rebate) + French regional: allowed
    frozenset({"fr_trip", "fr_idf_regional"}): {
        "rule_type": "allowed",
        "condition_text": "TRIP (foreign productions rebate) and IDF regional fund operate on independent tracks.",
    },
    frozenset({"fr_trip", "fr_naq_regional"}): {
        "rule_type": "allowed",
        "condition_text": "TRIP and Nouvelle-Aquitaine regional fund operate on independent tracks.",
    },
    frozenset({"fr_trip", "fr_ara_regional"}): {
        "rule_type": "allowed",
        "condition_text": "TRIP and Auvergne-Rhône-Alpes regional fund operate on independent tracks.",
    },
    frozenset({"fr_trip", "fr_occ_regional"}): {
        "rule_type": "allowed",
        "condition_text": "TRIP and Occitanie regional fund operate on independent tracks.",
    },
    # Eurimages + additional national funds
    frozenset({"eu_eurimages", "dk_dfi_support"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce DFI (Danish Film Institute) qualifying spend.",
    },
    frozenset({"eu_eurimages", "fr_idf_regional"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce IDF regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "fr_naq_regional"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Nouvelle-Aquitaine regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "de_bb_medienboard"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Medienboard Berlin-Brandenburg qualifying spend.",
    },
    frozenset({"eu_eurimages", "de_ni_nordmedia"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce nordmedia qualifying spend.",
    },
    frozenset({"eu_eurimages", "be_wal_wallimage"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Wallimage qualifying spend.",
    },
    frozenset({"eu_eurimages", "be_vlg_vaf"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce VAF Flanders qualifying spend.",
    },
    frozenset({"eu_eurimages", "it_cam_campania_fc"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Campania regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "it_pie_piemonte_fc"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Piemonte regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "it_apu_apulia_ff"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Apulia regional qualifying spend.",
    },
    frozenset({"eu_eurimages", "pl_pisf_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce PISF (Polish Film Institute) qualifying spend.",
    },
    frozenset({"eu_eurimages", "cz_czech_film_fund"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Czech Film Fund qualifying spend.",
    },
    frozenset({"eu_eurimages", "hu_nfi_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce NFI Hungary qualifying spend.",
    },
    frozenset({"eu_eurimages", "pt_ica_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce ICA Portugal qualifying spend.",
    },
    frozenset({"eu_eurimages", "at_ofi_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce ÖFI (Austrian Film Institute) qualifying spend.",
    },
    frozenset({"eu_eurimages", "film_i_vast"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages support does not reduce Film i Väst (Sweden) qualifying spend.",
    },
    # Ibermedia + regional Spanish: allowed
    frozenset({"ibermedia_programme", "es_cat_icec"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia grant and Catalonia ICEC both operate on independent tracks.",
    },
    frozenset({"ibermedia_programme", "es_eus_basque"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia grant and Basque Audiovisual fund operate on independent tracks.",
    },
    frozenset({"ibermedia_programme", "es_gal_agadic"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia grant and Galicia AGADIC operate on independent tracks.",
    },
    frozenset({"ibermedia_programme", "es_icaa_credit"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia grant and Spanish ICAA national deduction operate on independent tracks.",
    },
    frozenset({"ibermedia_programme", "pt_ica_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia grant and ICA Portugal grant operate on independent tracks.",
    },
    # Film i Väst + national funds: allowed
    frozenset({"film_i_vast", "se_svt"}): {
        "rule_type": "allowed",
        "condition_text": "Film i Väst and SVT both operate as co-production sources on independent tracks.",
    },
    frozenset({"film_i_vast", "nordic_ftvf"}): {
        "rule_type": "allowed",
        "condition_text": "Film i Väst and Nordic Film & TV Fond operate on independent tracks.",
    },

    # ===========================================================================
    # KNOWLEDGE COMPLETION — Migration 0061
    # ===========================================================================

    # ---------------------------------------------------------------------------
    # Regional ↔ Broadcaster (new category)
    # ---------------------------------------------------------------------------
    # UK regional ↔ BBC Films
    frozenset({"gb_lon_film_london", "gb_bbc_films"}): {
        "rule_type": "allowed",
        "condition_text": "Film London and BBC Films can co-finance; both are government assistance but draw from independent spending pools.",
    },
    frozenset({"gb_sct_screen_production", "gb_bbc_films"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Scotland and BBC Films can co-finance on independent tracks.",
    },
    frozenset({"gb_wls_film_fund", "gb_bbc_films"}): {
        "rule_type": "allowed",
        "condition_text": "Wales Screen and BBC Films can co-finance on independent tracks.",
    },
    frozenset({"gb_nir_northern_ireland", "gb_bbc_films"}): {
        "rule_type": "allowed",
        "condition_text": "Northern Ireland Screen and BBC Films can co-finance on independent tracks.",
    },
    # UK regional ↔ Film4
    frozenset({"gb_lon_film_london", "gb_film4"}): {
        "rule_type": "allowed",
        "condition_text": "Film London and Film4 can co-finance on independent tracks.",
    },
    frozenset({"gb_sct_screen_production", "gb_film4"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Scotland and Film4 can co-finance on independent tracks.",
    },
    frozenset({"gb_wls_film_fund", "gb_film4"}): {
        "rule_type": "allowed",
        "condition_text": "Wales Screen and Film4 can co-finance on independent tracks.",
    },
    frozenset({"gb_nir_northern_ireland", "gb_film4"}): {
        "rule_type": "allowed",
        "condition_text": "Northern Ireland Screen and Film4 can co-finance on independent tracks.",
    },
    # Norwegian regional ↔ NRK
    frozenset({"no_vgn_viken", "no_nrk"}): {
        "rule_type": "allowed",
        "condition_text": "Viken Filmsenter and NRK operate on independent co-financing tracks.",
    },
    frozenset({"no_rog_vestnorsk", "no_nrk"}): {
        "rule_type": "allowed",
        "condition_text": "Vestnorsk Filmsenter and NRK operate on independent co-financing tracks.",
    },
    frozenset({"no_tro_nordnorsk", "no_nrk"}): {
        "rule_type": "allowed",
        "condition_text": "Nordnorsk Filmsenter and NRK operate on independent co-financing tracks.",
    },
    frozenset({"no_inl_midtnorsk", "no_nrk"}): {
        "rule_type": "allowed",
        "condition_text": "Midtnorsk Filmsenter and NRK operate on independent co-financing tracks.",
    },
    frozenset({"no_mro_film3", "no_nrk"}): {
        "rule_type": "allowed",
        "condition_text": "Film3 and NRK operate on independent co-financing tracks.",
    },
    # Swedish regional ↔ SVT
    frozenset({"se_sk_film_skane", "se_svt"}): {
        "rule_type": "allowed",
        "condition_text": "Film i Skåne and SVT operate on independent co-financing tracks.",
    },
    frozenset({"se_ab_filmstockholm", "se_svt"}): {
        "rule_type": "allowed",
        "condition_text": "Film Stockholm and SVT operate on independent co-financing tracks.",
    },
    # Danish regional ↔ DR
    frozenset({"dk_cph_film_fund", "dk_dr"}): {
        "rule_type": "allowed",
        "condition_text": "Copenhagen Film Fund and DR can co-finance on independent tracks.",
    },
    frozenset({"dk_fyn_film", "dk_dr"}): {
        "rule_type": "allowed",
        "condition_text": "Fyn Film and DR can co-finance on independent tracks.",
    },
    # Irish regional dev ↔ RTÉ
    frozenset({"ie_screen_ireland_dev", "ie_rte"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Ireland development and RTÉ broadcaster investment operate on independent tracks.",
    },

    # ---------------------------------------------------------------------------
    # Grant ↔ Treaty (Eurimages/Ibermedia) — missing pairs
    # ---------------------------------------------------------------------------
    frozenset({"gb_bfi_production", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "BFI Film Fund and Eurimages operate on independent tracks; combined UK-led European co-productions can access both.",
    },
    frozenset({"ie_screen_ireland_dev", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Ireland development support and Eurimages production support operate on independent tracks.",
    },
    frozenset({"fr_cnc_production", "ibermedia_programme"}): {
        "rule_type": "allowed",
        "condition_text": "CNC production support and Ibermedia operate on independent tracks for eligible Franco-Ibero-American co-productions.",
    },
    frozenset({"no_nfi_grants", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "NFI Norway grants and Eurimages operate on independent tracks; Norwegian co-producers in Eurimages projects access both.",
    },
    frozenset({"dk_dfi_support", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "DFI Denmark grants and Eurimages operate on independent tracks.",
    },
    frozenset({"fi_ses_grants", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "SES Finland grants and Eurimages operate on independent tracks.",
    },
    frozenset({"at_ofi_grants", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "ÖFI Austria grants and Eurimages operate on independent tracks.",
    },

    # ---------------------------------------------------------------------------
    # Treaty ↔ Treaty (multilateral co-programme interactions)
    # ---------------------------------------------------------------------------
    frozenset({"eu_eurimages", "eu_creative_europe"}): {
        "rule_type": "allowed",
        "condition_text": "Eurimages co-production support and Creative Europe MEDIA development fund operate on independent tracks; combined EU public support ceiling of 50% of total budget applies at programme level.",
    },
    frozenset({"ibermedia_programme", "eu_media_fund"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia and EU MEDIA/Creative Europe operate on independent tracks for eligible co-productions involving Ibero-American and European parties.",
    },
    frozenset({"ibermedia_programme", "nordic_ftvf"}): {
        "rule_type": "allowed",
        "condition_text": "Ibermedia and Nordic Film & TV Fund operate on independent tracks; Spain-Portugal combinations with Nordic partners can access both.",
    },

    # ---------------------------------------------------------------------------
    # Service-production interactions
    # ---------------------------------------------------------------------------
    frozenset({"uk_hvc", "gb_lon_film_london"}): {
        "rule_type": "conditional",
        "condition_text": "UK HVC (service production) and Film London regional fund can be combined; Film London does not require cultural test, only London-based spend.",
    },
    frozenset({"uk_hvc", "gb_sct_screen_production"}): {
        "rule_type": "conditional",
        "condition_text": "UK HVC (service production) and Screen Scotland can be combined for foreign service shoots with significant Scottish spend.",
    },
    frozenset({"uk_hvc", "gb_nir_northern_ireland"}): {
        "rule_type": "conditional",
        "condition_text": "UK HVC (service production) and Northern Ireland Screen can be combined for foreign service shoots with significant NI spend.",
    },
    frozenset({"uk_hvc", "gb_wls_film_fund"}): {
        "rule_type": "conditional",
        "condition_text": "UK HVC (service production) and Wales Screen can be combined for foreign service shoots with significant Welsh spend.",
    },
    frozenset({"uk_hvc", "gb_bfi_production"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "UK HVC (service production) and BFI Film Fund are mutually exclusive: BFI requires cultural test which precludes HVC service route.",
    },
    frozenset({"uk_hvc", "uk_avec"}): {
        "rule_type": "mutually_exclusive",
        "condition_text": "UK HVC and AVEC are mutually exclusive: HVC is the service-production route, AVEC requires BFI cultural test or co-production treaty.",
    },
    frozenset({"ca_cmpa_foreign", "on_ofttc"}): {
        "rule_type": "allowed",
        "condition_text": "CMPA Foreign certificate (service production) and Ontario OFTTC can be combined: OFTTC does not require Canadian content certification.",
    },
    frozenset({"ca_cmpa_foreign", "ca_bc_pstc"}): {
        "rule_type": "allowed",
        "condition_text": "CMPA Foreign certificate (service production) and BC PSTC can be combined: PSTC does not require Canadian content certification for foreign shoots.",
    },
    frozenset({"au_location_offset", "au_vic_film_victoria"}): {
        "rule_type": "conditional",
        "condition_text": "AU Location Offset and VicScreen can be combined for foreign productions with significant Victorian spend; VicScreen support is government assistance reducing Location Offset QAPE basis.",
    },
    frozenset({"au_location_offset", "au_qld_screen"}): {
        "rule_type": "conditional",
        "condition_text": "AU Location Offset and Screen Queensland can be combined for foreign productions with significant Queensland spend; Screen QLD support reduces Location Offset QAPE basis.",
    },
    frozenset({"au_location_offset", "au_nsw_screen"}): {
        "rule_type": "conditional",
        "condition_text": "AU Location Offset and Screen NSW can be combined for foreign productions with significant NSW spend; Screen NSW support reduces Location Offset QAPE basis.",
    },

    # ---------------------------------------------------------------------------
    # Rebate ↔ Grant (combinations where explicit documentation exists)
    # ---------------------------------------------------------------------------
    frozenset({"jo_rfc_rebate", "jo_rfc_tourism"}): {
        "rule_type": "conditional",
        "condition_text": "Jordan Royal Film Commission rebate and tourism incentive can be combined; tourism incentive is conditional on rebate certification and does not reduce rebate basis.",
    },
    frozenset({"ma_ccm_rebate", "ma_ccm_tourism"}): {
        "rule_type": "conditional",
        "condition_text": "Morocco CCM rebate and tourism support can be combined; tourism support is conditional on CCM rebate application and does not reduce rebate basis.",
    },
    frozenset({"nz_screen_production_rebate", "nz_tourism_film"}): {
        "rule_type": "allowed",
        "condition_text": "NZ SPGR rebate and Tourism NZ film support operate on independent tracks.",
    },
    frozenset({"nz_screen_production_rebate", "nz_air_production"}): {
        "rule_type": "allowed",
        "condition_text": "NZ SPGR rebate and Air NZ production support operate on independent tracks.",
    },
    frozenset({"ie_section_481", "ie_tourism_ireland"}): {
        "rule_type": "conditional",
        "condition_text": "Irish Section 481 and Tourism Ireland location support can be combined; Tourism Ireland is not government assistance for Section 481 purposes.",
    },

    # ---------------------------------------------------------------------------
    # Loan (recoupable advance) ↔ rebate/credit
    # ---------------------------------------------------------------------------
    # In France, CNC avances sur recettes (advance against receipts) is technically
    # a recoupable loan; its interaction with TRIP is already captured as govt_assistance.
    # Screen Australia development investment is equity-like; already captured.
    # The remaining cases are soft-loan programs:
    frozenset({"is_film_rebate", "is_post_rebate"}): {
        "rule_type": "conditional",
        "condition_text": "Iceland Film Rebate and Iceland Post-Production Rebate can be combined if expenditure categories are distinct; post-production rebate is government assistance reducing Film Rebate qualifying basis for overlapping costs.",
    },
    frozenset({"bg_cash_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Bulgarian cash rebate and Eurimages operate on independent tracks; Eurimages does not reduce Bulgarian qualifying spend basis.",
    },
    frozenset({"ro_film_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Romanian film rebate and Eurimages operate on independent tracks; Eurimages does not reduce Romanian qualifying spend basis.",
    },
    frozenset({"si_sfc_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Slovenian film rebate and Eurimages operate on independent tracks.",
    },
    frozenset({"hr_cash_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Croatian cash rebate and Eurimages operate on independent tracks.",
    },
    frozenset({"gr_cash_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Greek cash rebate and Eurimages operate on independent tracks.",
    },

    # ---------------------------------------------------------------------------
    # Cash rebate ↔ broadcaster
    # ---------------------------------------------------------------------------
    frozenset({"mt_mfc_rebate", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Malta rebate and Eurimages operate on independent tracks for Malta-involved European co-productions.",
    },
    frozenset({"hr_cash_rebate", "hr_havc_fund"}): {
        "rule_type": "allowed",
        "condition_text": "Croatian cash rebate and HAVC fund operate on independent tracks; HAVC grant does not reduce rebate qualifying basis for foreign spend.",
    },
    frozenset({"il_rebate", "il_film_fund"}): {
        "rule_type": "allowed",
        "condition_text": "Israeli rebate and Israeli Film Fund operate on independent tracks; Film Fund grant does not reduce rebate qualifying basis.",
    },
    frozenset({"th_film_rebate", "th_film_fund"}): {
        "rule_type": "allowed",
        "condition_text": "Thailand film rebate and Thailand Creative Economy fund operate on independent tracks.",
    },

    # ---------------------------------------------------------------------------
    # Additional regional ↔ national (completing coverage)
    # ---------------------------------------------------------------------------
    frozenset({"no_mro_film3", "no_nfi_grants"}): {
        "rule_type": "allowed",
        "condition_text": "Film3 (Møre og Romsdal) and NFI Norway national grants operate on independent tracks.",
    },
    frozenset({"no_mro_film3", "no_film_incentive"}): {
        "rule_type": "allowed",
        "condition_text": "Film3 (Møre og Romsdal) and Norwegian cash rebate operate on independent tracks.",
    },
    frozenset({"gb_film_hub_midlands", "uk_avec"}): {
        "rule_type": "conditional",
        "condition_text": "Film Hub Midlands and AVEC can be combined; Film Hub Midlands BFI-funded support is government assistance reducing AVEC qualifying UK expenditure basis.",
    },
    frozenset({"gb_yrk_screen_yorkshire", "gb_bbc_films"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Yorkshire and BBC Films can co-finance on independent tracks.",
    },
    frozenset({"gb_yrk_screen_yorkshire", "gb_film4"}): {
        "rule_type": "allowed",
        "condition_text": "Screen Yorkshire and Film4 can co-finance on independent tracks.",
    },
    frozenset({"de_ffa", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "FFA (German Federal Film Board) reference film levy and Eurimages operate on independent tracks.",
    },
    frozenset({"pl_pisf_grants", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "PISF Poland grants and Eurimages operate on independent tracks; Eurimages support improves PISF application competitiveness.",
    },
    frozenset({"cz_czech_film_fund", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "Czech Film Fund and Eurimages operate on independent tracks.",
    },
    frozenset({"hu_nfi_grants", "eu_eurimages"}): {
        "rule_type": "allowed",
        "condition_text": "NFI Hungary grants and Eurimages operate on independent tracks.",
    },

    # ---------------------------------------------------------------------------
    # Equity ↔ rebate (public equity / fund equity interactions)
    # ---------------------------------------------------------------------------
    frozenset({"au_screen_production", "au_screenwest"}): {
        "rule_type": "spend_reduction",
        "condition_text": "Screen Australia equity investment is government assistance — reduces qualifying spend basis for ScreenWest WA incentive.",
    },
    frozenset({"au_screen_production", "au_nsw_screen"}): {
        "rule_type": "spend_reduction",
        "condition_text": "Screen Australia equity investment is government assistance — reduces qualifying spend basis for Screen NSW incentive.",
    },
    frozenset({"au_screen_production", "au_vic_film_victoria"}): {
        "rule_type": "spend_reduction",
        "condition_text": "Screen Australia equity investment is government assistance — reduces qualifying spend basis for VicScreen incentive.",
    },
    frozenset({"au_screen_production", "au_qld_screen"}): {
        "rule_type": "spend_reduction",
        "condition_text": "Screen Australia equity investment is government assistance — reduces qualifying spend basis for Screen Queensland incentive.",
    },
}


# ---------------------------------------------------------------------------
# Structural rules — applied when no slug-pair rule matches
# ---------------------------------------------------------------------------

# jurisdiction_codes whose grants are "government assistance" → spend_reduction
# when stacked with that jurisdiction's primary incentive
_GOV_ASSISTANCE_JURISDICTIONS: dict[str, str] = {
    # (grant_jur): credit_jur
    "CA": "CA",          # CMF, Telefilm → CPTC
    "CA-ON": "CA",       # NOHFC → CPTC
    "CA-ON_CA-ON": "CA-ON",  # NOHFC → OFTTC
    "AU": "AU",          # Screen Australia → Offsets
}

# program_types that are "primary incentives" (tax credit / rebate)
_PRIMARY_TYPES = frozenset({"tax_credit", "cash_rebate"})

# program_types that are "grant/fund" programs
_GRANT_TYPES = frozenset({
    "direct_grant", "co_production_fund", "development_fund", "discretionary_fund",
})

# program_types that are "regional funds"
_REGIONAL_TYPES = frozenset({"regional_fund", "discretionary_fund"})


def _is_government_assistance_in_jurisdiction(
    grant: GlobalProgramEntry,
    credit: GlobalProgramEntry,
) -> bool:
    """
    True if `grant` is government assistance that reduces `credit`'s qualifying spend.
    Based on the structural rule that government grants from the same
    jurisdiction reduce the qualifying spend basis for national tax credits.
    """
    # Explicit slug-pair rules take precedence (checked before calling this)
    # Structural check: same top-level jurisdiction, grant is a fund type
    grant_jur = grant.jurisdiction_code.split("-")[0]
    credit_jur = credit.jurisdiction_code.split("-")[0]
    if grant_jur != credit_jur:
        return False
    if grant.program_type not in _GRANT_TYPES:
        return False
    if credit.program_type not in _PRIMARY_TYPES:
        return False
    # Only apply for known government assistance jurisdictions
    return grant_jur in ("CA", "AU")


def evaluate_pair(
    prog_a: GlobalProgramEntry,
    prog_b: GlobalProgramEntry,
) -> StackingViolation | None:
    """
    Evaluate stacking compatibility of two programs.
    Returns a StackingViolation if non-trivially interesting, else None (allowed by default).
    """
    slug_a = infer_slug(prog_a)
    slug_b = infer_slug(prog_b)

    # 1. Named slug-pair rules
    if slug_a and slug_b:
        rule = _SLUG_PAIR_RULES.get(frozenset({slug_a, slug_b}))
        if rule:
            rt = rule["rule_type"]
            if rt == "allowed":
                return None  # no violation
            return StackingViolation(
                program_a_name=prog_a.program_name,
                program_b_name=prog_b.program_name,
                rule_type=rt,
                condition_text=rule["condition_text"],
                adjusts_value=(rt == "spend_reduction"),
            )

    # 2. Mutual exclusivity: same jurisdiction + same primary type
    if (
        prog_a.jurisdiction_code == prog_b.jurisdiction_code
        and prog_a.program_type in _PRIMARY_TYPES
        and prog_b.program_type in _PRIMARY_TYPES
    ):
        return StackingViolation(
            program_a_name=prog_a.program_name,
            program_b_name=prog_b.program_name,
            rule_type="mutually_exclusive",
            condition_text=(
                f"Only one primary incentive can be claimed per jurisdiction "
                f"({prog_a.jurisdiction_code}). Higher-value program is retained."
            ),
            adjusts_value=True,
        )

    # 3. Government assistance → spend_reduction
    # Check both directions (grant reduces credit)
    for grant, credit in [(prog_a, prog_b), (prog_b, prog_a)]:
        if _is_government_assistance_in_jurisdiction(grant, credit):
            return StackingViolation(
                program_a_name=grant.program_name,
                program_b_name=credit.program_name,
                rule_type="spend_reduction",
                condition_text=(
                    f"{grant.program_name} is government assistance; reduces "
                    f"qualifying spend basis for {credit.program_name}."
                ),
                adjusts_value=True,
            )

    # 4. Default: allowed
    return None


def evaluate_structure_stacking(
    programs: list[GlobalProgramEntry],
) -> tuple[list[StackingViolation], list[StackingViolation], list[StackingViolation]]:
    """
    Evaluate all pairwise stacking interactions in a structure.

    Returns (prohibited_or_mutually_exclusive, conditionals, spend_reductions).
    """
    violations: list[StackingViolation] = []
    conditionals: list[StackingViolation] = []
    spend_reductions: list[StackingViolation] = []

    for i, prog_a in enumerate(programs):
        for prog_b in programs[i + 1:]:
            v = evaluate_pair(prog_a, prog_b)
            if v is None:
                continue
            if v.rule_type in ("prohibited", "mutually_exclusive"):
                violations.append(v)
            elif v.rule_type == "conditional":
                conditionals.append(v)
            elif v.rule_type == "spend_reduction":
                spend_reductions.append(v)

    return violations, conditionals, spend_reductions
