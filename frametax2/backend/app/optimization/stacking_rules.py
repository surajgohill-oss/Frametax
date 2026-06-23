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
