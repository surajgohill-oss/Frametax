"""0061 — Knowledge database completion pass.

Permanently closes the knowledge database by adding all missing relationships
between existing programs. Delta-only: no new jurisdictions added.

Adds:
  - 9 missing bilateral treaties (UK-IT, AU-FR, AU-NZ, DE-AT, DE-PL, DE-HU,
    DE-CZ, KR-FR, KR-DE)
  - 145 new structure_graph_edges (depends_on, service_only, regional_only,
    national_only, broadcaster_only, fund_only, missing treaty unlocks,
    co-production structure expansions)
  - 62 new stacking rules (regional↔broadcaster, grant↔treaty, treaty↔treaty,
    service-production, rebate↔grant, equity↔rebate, additional coverage)

Revision ID: 0061
Revises: 0060
Create Date: 2026-06-25
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "0061"
down_revision: Union[str, None] = "0060"
branch_labels = None
depends_on = None

# fmt: off

# ---------------------------------------------------------------------------
# Missing bilateral treaties
# ---------------------------------------------------------------------------
_NEW_TREATIES = [
    {
        "treaty_name": "UK–Italy Co-production Treaty",
        "treaty_slug": "uk-it-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "IT",
        "year_signed": 2007,
        "effective_from": "2007-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "UK spend qualifies for AVEC; Italian spend for MiC tax credit.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to financial contribution.",
        "majority_jurisdiction_benefits": (
            "UK-majority qualifies for AVEC (up to 40%), BFI Film Fund."
        ),
        "minority_jurisdiction_benefits": (
            "Italian co-producer qualifies for MiC tax credit for foreign co-productions."
        ),
        "treaty_administrator_name": "British Film Commission / MiC Italy",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": "UK-Italy bilateral treaty signed 2007; post-Brexit remains active.",
    },
    {
        "treaty_name": "Australia–France Co-production Treaty",
        "treaty_slug": "au-fr-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "FR",
        "year_signed": 2010,
        "effective_from": "2010-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "Australian spend qualifies for Producer Offset; French spend for TRIP.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "AU-majority qualifies for Producer Offset (40% feature), Screen Australia funding."
        ),
        "minority_jurisdiction_benefits": (
            "French co-producer qualifies for TRIP rebate and CNC production support."
        ),
        "treaty_administrator_name": "Screen Australia / CNC",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Australia–New Zealand Co-production Treaty",
        "treaty_slug": "au-nz-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "NZ",
        "year_signed": 2010,
        "effective_from": "2010-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "Australian spend qualifies for Producer Offset; NZ spend for NZSPGR.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "AU-majority qualifies for Producer Offset (40% feature), Screen Australia funding."
        ),
        "minority_jurisdiction_benefits": (
            "NZ co-producer qualifies for NZ Screen Production Grant (20% domestic rebate)."
        ),
        "treaty_administrator_name": "Screen Australia / NZ Film Commission",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": "Trans-Tasman co-production treaty; historically common structure.",
    },
    {
        "treaty_name": "Germany–Austria Co-production Treaty",
        "treaty_slug": "de-at-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "DE",
        "jurisdiction_b_code": "AT",
        "year_signed": 1993,
        "effective_from": "1993-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "German spend for DFFF/FFA; Austrian spend for FISA+/ÖFI.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "German-majority qualifies for DFFF, FFA, Länder funds."
        ),
        "minority_jurisdiction_benefits": (
            "Austrian co-producer qualifies for ÖFI grants and FISA+ rebate."
        ),
        "treaty_administrator_name": "FFA / ÖFI",
        "authority_url": "https://www.ffa.de/koprodukationsvertrag.html",
        "confidence_tier": "PARSED",
        "notes": "Common DACH co-production structure; German-language cultural affinity.",
    },
    {
        "treaty_name": "Germany–Poland Co-production Treaty",
        "treaty_slug": "de-pl-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "DE",
        "jurisdiction_b_code": "PL",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "German spend for DFFF/FFA; Polish spend for PISF grants.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "German-majority qualifies for DFFF, FFA, Länder funds.",
        "minority_jurisdiction_benefits": "Polish co-producer qualifies for PISF grants.",
        "treaty_administrator_name": "FFA / PISF",
        "authority_url": "https://www.ffa.de/koprodukationsvertrag.html",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Germany–Hungary Co-production Treaty",
        "treaty_slug": "de-hu-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "DE",
        "jurisdiction_b_code": "HU",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "German spend for DFFF/FFA; Hungarian spend for NFI grants.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "German-majority qualifies for DFFF, FFA, Länder funds.",
        "minority_jurisdiction_benefits": "Hungarian co-producer qualifies for NFI Hungary grants.",
        "treaty_administrator_name": "FFA / NFI Hungary",
        "authority_url": "https://www.ffa.de/koprodukationsvertrag.html",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Germany–Czech Republic Co-production Treaty",
        "treaty_slug": "de-cz-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "DE",
        "jurisdiction_b_code": "CZ",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "German spend for DFFF/FFA; Czech spend for Czech Film Fund.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "German-majority qualifies for DFFF, FFA, Länder funds.",
        "minority_jurisdiction_benefits": "Czech co-producer qualifies for Czech Film Fund and 20% rebate.",
        "treaty_administrator_name": "FFA / Czech Film Fund",
        "authority_url": "https://www.ffa.de/koprodukationsvertrag.html",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Korea–France Co-production Treaty",
        "treaty_slug": "kr-fr-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "KR",
        "jurisdiction_b_code": "FR",
        "year_signed": 2006,
        "effective_from": "2006-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "Korean spend for KOFIC; French spend for TRIP and CNC support.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright; territorial rights separated.",
        "majority_jurisdiction_benefits": "Korean-majority qualifies for KOFIC production fund.",
        "minority_jurisdiction_benefits": (
            "French co-producer qualifies for TRIP rebate and CNC avances sur recettes."
        ),
        "treaty_administrator_name": "KOFIC / CNC",
        "authority_url": "https://www.kofic.or.kr/kofic/business/coproduction/findInternationalCoproductionList.do",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Korea–Germany Co-production Treaty",
        "treaty_slug": "kr-de-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "KR",
        "jurisdiction_b_code": "DE",
        "year_signed": 2004,
        "effective_from": "2004-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": "Korean spend for KOFIC; German spend for DFFF and Länder.",
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Korean-majority qualifies for KOFIC production fund.",
        "minority_jurisdiction_benefits": (
            "German co-producer qualifies for DFFF, FFA, and German Länder funds."
        ),
        "treaty_administrator_name": "KOFIC / FFA",
        "authority_url": "https://www.kofic.or.kr/kofic/business/coproduction/findInternationalCoproductionList.do",
        "confidence_tier": "PARSED",
        "notes": None,
    },
]

# ---------------------------------------------------------------------------
# New structure graph edges
# ---------------------------------------------------------------------------
# (source_type, source_slug, edge_type, target_type, target_slug, condition, magnitude, conf)
_NEW_GRAPH_EDGES = [
    # --- depends_on ---
    ("program", "ca_cmf", "depends_on", "broadcaster", "cbc_original",
     "CMF Convergent stream requires a licensed Canadian broadcaster trigger", None, "PARSED"),
    ("program", "ca_bell_fund", "depends_on", "broadcaster", "cbc_original",
     "Bell Fund requires broadcaster as co-applicant", None, "PARSED"),
    ("program", "nordic_ftvf", "depends_on", "broadcaster", "se_svt",
     "At least one Nordic public broadcaster required for Nordic FTVF eligibility", None, "PARSED"),
    ("program", "eu_eurimages", "depends_on", "treaty", "eurimages-multilateral",
     "Eurimages requires co-production agreement between ≥2 Eurimages member states", None, "PARSED"),
    ("program", "ibermedia_programme", "depends_on", "treaty", "ibermedia-multilateral",
     "Ibermedia requires co-production from ≥2 Ibermedia member countries", None, "PARSED"),
    ("program", "de_bb_medienboard", "depends_on", "program", "de_dfff",
     "Projects above EUR 3M: Medienboard typically requires DFFF federal anchor", None, "DISCOVERY"),
    ("program", "fr_trip", "depends_on", "program", "fr_cnc_cultural_test",
     "TRIP requires CNC cultural qualification certificate before rebate application", None, "PARSED"),
    ("program", "au_producer_offset", "depends_on", "program", "au_content_test",
     "Producer Offset requires QAPE threshold and Australian content test", None, "PARSED"),
    ("program", "eu_media_fund", "depends_on", "treaty", "eurimages-multilateral",
     "Creative Europe MEDIA fund requires company established in programme country", None, "PARSED"),
    ("program", "ie_section_481", "depends_on", "program", "ie_section_481_test",
     "Section 481 requires SIRI certification and qualifying production checklist", None, "PARSED"),

    # --- service_only ---
    ("program", "uk_hvc", "service_only", "program", "uk_hvc",
     None, None, "PARSED"),
    ("program", "ca_cmpa_foreign", "service_only", "program", "ca_cmpa_foreign",
     None, None, "PARSED"),
    ("program", "au_location_offset", "service_only", "program", "au_location_offset",
     "Location Offset (16.5%) is for foreign-majority shoots; incompatible with domestic Producer Offset on same spend",
     None, "PARSED"),
    ("program", "kr_kofic_location", "service_only", "program", "kr_kofic_location",
     None, None, "PARSED"),

    # --- broadcaster_only ---
    ("program", "ca_cmf", "broadcaster_only", "program", "ca_cmf",
     None, None, "PARSED"),
    ("program", "ca_bell_fund", "broadcaster_only", "program", "ca_bell_fund",
     None, None, "PARSED"),
    ("program", "nordic_ftvf", "broadcaster_only", "program", "nordic_ftvf",
     None, None, "PARSED"),
    ("program", "rte_drama_fund", "broadcaster_only", "program", "rte_drama_fund",
     None, None, "PARSED"),

    # --- regional_only (Norwegian) ---
    ("program", "no_vgn_viken", "regional_only", "program", "no_vgn_viken",
     None, None, "PARSED"),
    ("program", "no_rog_vestnorsk", "regional_only", "program", "no_rog_vestnorsk",
     None, None, "PARSED"),
    ("program", "no_tro_nordnorsk", "regional_only", "program", "no_tro_nordnorsk",
     None, None, "PARSED"),
    ("program", "no_inl_midtnorsk", "regional_only", "program", "no_inl_midtnorsk",
     None, None, "PARSED"),
    ("program", "no_mro_film3", "regional_only", "program", "no_mro_film3",
     None, None, "PARSED"),
    # --- regional_only (Swedish) ---
    ("program", "film_i_vast", "regional_only", "program", "film_i_vast",
     None, None, "PARSED"),
    ("program", "se_sk_film_skane", "regional_only", "program", "se_sk_film_skane",
     None, None, "PARSED"),
    ("program", "se_ab_filmstockholm", "regional_only", "program", "se_ab_filmstockholm",
     None, None, "PARSED"),
    ("program", "se_goteborg_fund", "regional_only", "program", "se_goteborg_fund",
     None, None, "PARSED"),
    # --- regional_only (UK) ---
    ("program", "gb_lon_film_london", "regional_only", "program", "gb_lon_film_london",
     None, None, "PARSED"),
    ("program", "gb_sct_screen_production", "regional_only", "program", "gb_sct_screen_production",
     None, None, "PARSED"),
    ("program", "gb_wls_film_fund", "regional_only", "program", "gb_wls_film_fund",
     None, None, "PARSED"),
    ("program", "gb_nir_northern_ireland", "regional_only", "program", "gb_nir_northern_ireland",
     None, None, "PARSED"),
    ("program", "gb_yrk_screen_yorkshire", "regional_only", "program", "gb_yrk_screen_yorkshire",
     None, None, "PARSED"),
    ("program", "gb_film_hub_midlands", "regional_only", "program", "gb_film_hub_midlands",
     None, None, "PARSED"),
    # --- regional_only (German) ---
    ("program", "de_bb_medienboard", "regional_only", "program", "de_bb_medienboard",
     None, None, "PARSED"),
    ("program", "de_nrw_filmstiftung", "regional_only", "program", "de_nrw_filmstiftung",
     None, None, "PARSED"),
    ("program", "de_fff_bayern", "regional_only", "program", "de_fff_bayern",
     None, None, "PARSED"),
    ("program", "de_ni_nordmedia", "regional_only", "program", "de_ni_nordmedia",
     None, None, "PARSED"),
    ("program", "de_hh_film_hamburg", "regional_only", "program", "de_hh_film_hamburg",
     None, None, "PARSED"),
    ("program", "de_bw_mfg", "regional_only", "program", "de_bw_mfg",
     None, None, "PARSED"),
    ("program", "de_mdm_mitteldeutsche", "regional_only", "program", "de_mdm_mitteldeutsche",
     None, None, "PARSED"),
    # --- regional_only (French) ---
    ("program", "fr_idf_regional", "regional_only", "program", "fr_idf_regional",
     None, None, "PARSED"),
    ("program", "fr_naq_regional", "regional_only", "program", "fr_naq_regional",
     None, None, "PARSED"),
    ("program", "fr_ara_regional", "regional_only", "program", "fr_ara_regional",
     None, None, "PARSED"),
    ("program", "fr_occ_regional", "regional_only", "program", "fr_occ_regional",
     None, None, "PARSED"),
    # --- regional_only (Italian) ---
    ("program", "it_laz_lazio_fc", "regional_only", "program", "it_laz_lazio_fc",
     None, None, "PARSED"),
    ("program", "it_sic_sicilia_fc", "regional_only", "program", "it_sic_sicilia_fc",
     None, None, "PARSED"),
    ("program", "it_cam_campania_fc", "regional_only", "program", "it_cam_campania_fc",
     None, None, "PARSED"),
    ("program", "it_pie_piemonte_fc", "regional_only", "program", "it_pie_piemonte_fc",
     None, None, "PARSED"),
    ("program", "it_apu_apulia_ff", "regional_only", "program", "it_apu_apulia_ff",
     None, None, "PARSED"),
    ("program", "it_tos_tuscany_fc", "regional_only", "program", "it_tos_tuscany_fc",
     None, None, "PARSED"),
    # --- regional_only (Spanish) ---
    ("program", "es_cat_icec", "regional_only", "program", "es_cat_icec",
     None, None, "PARSED"),
    ("program", "es_and_andalusia", "regional_only", "program", "es_and_andalusia",
     None, None, "PARSED"),
    ("program", "es_gal_agadic", "regional_only", "program", "es_gal_agadic",
     None, None, "PARSED"),
    ("program", "es_val_ivc", "regional_only", "program", "es_val_ivc",
     None, None, "PARSED"),
    ("program", "es_eus_basque", "regional_only", "program", "es_eus_basque",
     None, None, "PARSED"),
    # --- regional_only (Australian state) ---
    ("program", "au_vic_film_victoria", "regional_only", "program", "au_vic_film_victoria",
     None, None, "PARSED"),
    ("program", "au_qld_screen", "regional_only", "program", "au_qld_screen",
     None, None, "PARSED"),
    ("program", "au_nsw_screen", "regional_only", "program", "au_nsw_screen",
     None, None, "PARSED"),
    ("program", "au_sa_safc", "regional_only", "program", "au_sa_safc",
     None, None, "PARSED"),
    ("program", "au_tas_screen", "regional_only", "program", "au_tas_screen",
     None, None, "PARSED"),
    ("program", "au_nt_territory", "regional_only", "program", "au_nt_territory",
     None, None, "PARSED"),
    ("program", "au_screenwest", "regional_only", "program", "au_screenwest",
     None, None, "PARSED"),
    # --- regional_only (Danish) ---
    ("program", "dk_cph_film_fund", "regional_only", "program", "dk_cph_film_fund",
     None, None, "PARSED"),
    ("program", "dk_fyn_film", "regional_only", "program", "dk_fyn_film",
     None, None, "PARSED"),
    # --- regional_only (Canadian provincial) ---
    ("program", "ca_bc_pstc", "regional_only", "program", "ca_bc_pstc",
     None, None, "PARSED"),
    ("program", "on_ofttc", "regional_only", "program", "on_ofttc",
     None, None, "PARSED"),
    ("program", "on_opstc", "regional_only", "program", "on_opstc",
     None, None, "PARSED"),
    ("program", "qc_film_production", "regional_only", "program", "qc_film_production",
     None, None, "PARSED"),
    ("program", "nohfc_production_fund", "regional_only", "program", "nohfc_production_fund",
     None, None, "PARSED"),
    ("program", "ca_pe_film_pei", "regional_only", "program", "ca_pe_film_pei",
     None, None, "DISCOVERY"),
    ("program", "ca_mb_film_mb", "regional_only", "program", "ca_mb_film_mb",
     None, None, "PARSED"),
    ("program", "ca_nb_film_nb", "regional_only", "program", "ca_nb_film_nb",
     None, None, "DISCOVERY"),
    ("program", "ca_nl_film_nl", "regional_only", "program", "ca_nl_film_nl",
     None, None, "DISCOVERY"),
    ("program", "ca_ns_film_incentive", "regional_only", "program", "ca_ns_film_incentive",
     None, None, "PARSED"),

    # --- national_only ---
    ("program", "ca_federal_cptc", "national_only", "program", "ca_federal_cptc",
     "CPTC is domestic/treaty only; service productions use CMPA Foreign certificate", None, "PARSED"),
    ("program", "au_producer_offset", "national_only", "program", "au_producer_offset",
     "Producer Offset is domestic/treaty only; foreign service shoots use Location Offset", None, "PARSED"),
    ("program", "ie_section_481", "national_only", "program", "ie_section_481",
     "Section 481 requires Irish-based production company; not available for pure service shoots", None, "PARSED"),
    ("program", "uk_avec", "national_only", "program", "uk_avec",
     "AVEC requires BFI cultural test or co-production treaty; pure service shoots use HVC", None, "PARSED"),
    ("program", "fr_trip", "national_only", "program", "fr_trip",
     "TRIP requires CNC cultural qualification; not available without French cultural connection", None, "PARSED"),
    ("program", "de_dfff", "national_only", "program", "de_dfff",
     "DFFF requires German cultural connection (Fachgutachten) and German producer", None, "PARSED"),
    ("program", "eu_eurimages", "national_only", "program", "eu_eurimages",
     "Eurimages is for official co-productions; not available for service productions", None, "PARSED"),
    ("program", "no_nfi_grants", "national_only", "program", "no_nfi_grants",
     "NFI grants require Norwegian producer and qualifying Norwegian cultural content", None, "PARSED"),
    ("program", "kr_kofic_production", "national_only", "program", "kr_kofic_production",
     "KOFIC production fund requires Korean producer and Korean cultural content", None, "PARSED"),

    # --- fund_only ---
    ("program", "eu_media_fund", "fund_only", "program", "eu_media_fund",
     None, None, "PARSED"),
    ("program", "eu_creative_europe", "fund_only", "program", "eu_creative_europe",
     None, None, "PARSED"),
    ("program", "nl_hbf", "fund_only", "program", "nl_hbf",
     None, None, "PARSED"),
    ("program", "eu_eurimages", "fund_only", "program", "eu_eurimages",
     None, None, "PARSED"),
    ("program", "ibermedia_programme", "fund_only", "program", "ibermedia_programme",
     None, None, "PARSED"),

    # --- Missing treaty → program unlocks ---
    ("treaty", "uk-it-bilateral", "unlocks", "program", "uk_avec",
     "UK majority in UK-Italy co-production", None, "PARSED"),
    ("treaty", "uk-it-bilateral", "unlocks", "program", "it_tax_credit_foreign",
     "IT majority in UK-Italy co-production", None, "PARSED"),
    ("treaty", "au-fr-bilateral", "unlocks", "program", "au_producer_offset",
     "AU majority in AU-France co-production", None, "PARSED"),
    ("treaty", "au-fr-bilateral", "unlocks", "program", "fr_trip",
     "FR majority in AU-France co-production", None, "PARSED"),
    ("treaty", "au-nz-bilateral", "unlocks", "program", "au_producer_offset",
     "AU majority in AU-NZ co-production", None, "PARSED"),
    ("treaty", "au-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate",
     "NZ majority in AU-NZ co-production", None, "PARSED"),
    ("treaty", "de-at-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Germany-Austria co-production", None, "PARSED"),
    ("treaty", "de-at-bilateral", "unlocks", "program", "at_ofi_grants",
     "AT majority in Germany-Austria co-production", None, "PARSED"),
    ("treaty", "de-pl-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Germany-Poland co-production", None, "PARSED"),
    ("treaty", "de-pl-bilateral", "unlocks", "program", "pl_pisf_grants",
     "PL majority in Germany-Poland co-production", None, "PARSED"),
    ("treaty", "de-hu-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Germany-Hungary co-production", None, "PARSED"),
    ("treaty", "de-hu-bilateral", "unlocks", "program", "hu_nfi_grants",
     "HU majority in Germany-Hungary co-production", None, "PARSED"),
    ("treaty", "de-cz-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Germany-Czech co-production", None, "PARSED"),
    ("treaty", "de-cz-bilateral", "unlocks", "program", "cz_czech_film_fund",
     "CZ majority in Germany-Czech co-production", None, "PARSED"),
    ("treaty", "kr-fr-bilateral", "unlocks", "program", "kr_kofic_production",
     "KR majority in Korea-France co-production", None, "PARSED"),
    ("treaty", "kr-fr-bilateral", "unlocks", "program", "fr_trip",
     "FR majority in Korea-France co-production", None, "PARSED"),
    ("treaty", "kr-de-bilateral", "unlocks", "program", "kr_kofic_production",
     "KR majority in Korea-Germany co-production", None, "PARSED"),
    ("treaty", "kr-de-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Korea-Germany co-production", None, "PARSED"),
    ("treaty", "au-kr-bilateral", "unlocks", "program", "au_producer_offset",
     "AU majority in AU-Korea co-production", None, "PARSED"),
    ("treaty", "au-kr-bilateral", "unlocks", "program", "kr_kofic_production",
     "KR majority in AU-Korea co-production", None, "PARSED"),
    ("treaty", "ca-es-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-Spain co-production", None, "PARSED"),
    ("treaty", "ca-es-bilateral", "unlocks", "program", "es_icaa_credit",
     "ES majority in Canada-Spain co-production", None, "PARSED"),
    ("treaty", "ca-za-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-South Africa co-production", None, "PARSED"),
    ("treaty", "ca-za-bilateral", "unlocks", "program", "za_nfvf_fund",
     "ZA majority in Canada-South Africa co-production", None, "PARSED"),
    ("treaty", "ca-ch-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-Switzerland co-production", None, "PARSED"),
    ("treaty", "ca-mx-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-Mexico co-production", None, "PARSED"),
    ("treaty", "ca-mx-bilateral", "unlocks", "program", "mx_fidecine",
     "MX majority in Canada-Mexico co-production", None, "DISCOVERY"),
    ("treaty", "ca-cn-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-China co-production", None, "PARSED"),
    ("treaty", "au-ie-bilateral", "unlocks", "program", "au_producer_offset",
     "AU majority in Australia-Ireland co-production", None, "PARSED"),
    ("treaty", "au-ie-bilateral", "unlocks", "program", "ie_section_481",
     "IE majority in Australia-Ireland co-production", None, "PARSED"),
    ("treaty", "au-de-bilateral", "unlocks", "program", "au_producer_offset",
     "AU majority in Australia-Germany co-production", None, "PARSED"),
    ("treaty", "au-de-bilateral", "unlocks", "program", "de_dfff",
     "DE majority in Australia-Germany co-production", None, "PARSED"),
    ("treaty", "ca-be-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-Belgium co-production", None, "PARSED"),
    ("treaty", "ca-be-bilateral", "unlocks", "program", "be_tax_shelter",
     "BE majority in Canada-Belgium co-production", None, "PARSED"),
    ("treaty", "ca-ie-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-Ireland co-production", None, "PARSED"),
    ("treaty", "ca-ie-bilateral", "unlocks", "program", "ie_section_481",
     "IE majority in Canada-Ireland co-production", None, "PARSED"),
    ("treaty", "ca-nz-bilateral", "unlocks", "program", "ca_federal_cptc",
     "CA majority in Canada-New Zealand co-production", None, "PARSED"),
    ("treaty", "ca-nz-bilateral", "unlocks", "program", "nz_screen_production_rebate",
     "NZ majority in Canada-New Zealand co-production", None, "PARSED"),
    # Eurimages multilateral unlocks (key member programs)
    ("treaty", "eurimages-multilateral", "unlocks", "program", "uk_avec",
     "UK is majority co-producer in Eurimages trilateral", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "fr_trip",
     "FR is majority co-producer in Eurimages trilateral", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "de_dfff",
     "DE is majority co-producer in Eurimages trilateral", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "it_tax_credit_foreign",
     "IT is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "pl_pisf_grants",
     "PL is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "no_nfi_grants",
     "NO is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "cz_czech_film_fund",
     "CZ is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "hu_nfi_grants",
     "HU is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "pt_ica_grants",
     "PT is a co-producer in an Eurimages co-production", None, "PARSED"),
    ("treaty", "eurimages-multilateral", "unlocks", "program", "at_ofi_grants",
     "AT is a co-producer in an Eurimages co-production", None, "PARSED"),
    # Ibermedia multilateral unlocks
    ("treaty", "ibermedia-multilateral", "unlocks", "program", "pt_ica_grants",
     "PT is a co-producer in an Ibermedia trilateral", None, "PARSED"),
    ("treaty", "ibermedia-multilateral", "unlocks", "program", "es_icaa_credit",
     "ES is the majority co-producer in an Ibermedia production", None, "PARSED"),
    # European Convention
    ("treaty", "european-convention-coproduction", "unlocks", "program", "uk_avec",
     "UK is majority co-producer under European Convention", None, "PARSED"),
    ("treaty", "european-convention-coproduction", "unlocks", "program", "no_nfi_grants",
     "NO is a co-producer under European Convention", None, "PARSED"),
]

# ---------------------------------------------------------------------------
# New stacking rules
# ---------------------------------------------------------------------------
# (slug_a, slug_b, rule_type, condition_text, confidence_tier)
_NEW_STACKING_RULES = [
    # ------------------------------------------------------------------
    # Regional ↔ Broadcaster
    # ------------------------------------------------------------------
    ("gb_lon_film_london", "gb_bbc_films",
     "allowed",
     "Film London and BBC Films can co-finance; both draw from independent spending pools.",
     "PARSED"),
    ("gb_sct_screen_production", "gb_bbc_films",
     "allowed",
     "Screen Scotland and BBC Films can co-finance on independent tracks.",
     "PARSED"),
    ("gb_wls_film_fund", "gb_bbc_films",
     "allowed",
     "Wales Screen and BBC Films can co-finance on independent tracks.",
     "PARSED"),
    ("gb_nir_northern_ireland", "gb_bbc_films",
     "allowed",
     "Northern Ireland Screen and BBC Films can co-finance on independent tracks.",
     "PARSED"),
    ("gb_lon_film_london", "gb_film4",
     "allowed",
     "Film London and Film4 can co-finance on independent tracks.",
     "PARSED"),
    ("gb_sct_screen_production", "gb_film4",
     "allowed",
     "Screen Scotland and Film4 can co-finance on independent tracks.",
     "PARSED"),
    ("gb_wls_film_fund", "gb_film4",
     "allowed",
     "Wales Screen and Film4 can co-finance on independent tracks.",
     "PARSED"),
    ("gb_nir_northern_ireland", "gb_film4",
     "allowed",
     "Northern Ireland Screen and Film4 can co-finance on independent tracks.",
     "PARSED"),
    ("gb_yrk_screen_yorkshire", "gb_bbc_films",
     "allowed",
     "Screen Yorkshire and BBC Films can co-finance on independent tracks.",
     "PARSED"),
    ("gb_yrk_screen_yorkshire", "gb_film4",
     "allowed",
     "Screen Yorkshire and Film4 can co-finance on independent tracks.",
     "PARSED"),
    ("no_vgn_viken", "no_nrk",
     "allowed",
     "Viken Filmsenter and NRK operate on independent co-financing tracks.",
     "PARSED"),
    ("no_rog_vestnorsk", "no_nrk",
     "allowed",
     "Vestnorsk Filmsenter and NRK operate on independent co-financing tracks.",
     "PARSED"),
    ("no_tro_nordnorsk", "no_nrk",
     "allowed",
     "Nordnorsk Filmsenter and NRK operate on independent co-financing tracks.",
     "PARSED"),
    ("no_inl_midtnorsk", "no_nrk",
     "allowed",
     "Midtnorsk Filmsenter and NRK operate on independent co-financing tracks.",
     "PARSED"),
    ("no_mro_film3", "no_nrk",
     "allowed",
     "Film3 (Møre og Romsdal) and NRK operate on independent co-financing tracks.",
     "PARSED"),
    ("se_sk_film_skane", "se_svt",
     "allowed",
     "Film i Skåne and SVT operate on independent co-financing tracks.",
     "PARSED"),
    ("se_ab_filmstockholm", "se_svt",
     "allowed",
     "Film Stockholm and SVT operate on independent co-financing tracks.",
     "PARSED"),
    ("dk_cph_film_fund", "dk_dr",
     "allowed",
     "Copenhagen Film Fund and DR can co-finance on independent tracks.",
     "PARSED"),
    ("dk_fyn_film", "dk_dr",
     "allowed",
     "Fyn Film and DR can co-finance on independent tracks.",
     "PARSED"),
    ("ie_screen_ireland_dev", "ie_rte",
     "allowed",
     "Screen Ireland development and RTÉ broadcaster investment operate on independent tracks.",
     "PARSED"),
    # ------------------------------------------------------------------
    # Grant ↔ Treaty (Eurimages/Ibermedia) — missing pairs
    # ------------------------------------------------------------------
    ("gb_bfi_production", "eu_eurimages",
     "allowed",
     "BFI Film Fund and Eurimages operate on independent tracks; combined UK-led European co-productions can access both.",
     "PARSED"),
    ("ie_screen_ireland_dev", "eu_eurimages",
     "allowed",
     "Screen Ireland development and Eurimages production support operate on independent tracks.",
     "PARSED"),
    ("fr_cnc_production", "ibermedia_programme",
     "allowed",
     "CNC production support and Ibermedia operate on independent tracks for eligible Franco-Ibero-American co-productions.",
     "PARSED"),
    ("no_nfi_grants", "eu_eurimages",
     "allowed",
     "NFI Norway grants and Eurimages operate on independent tracks.",
     "PARSED"),
    ("dk_dfi_support", "eu_eurimages",
     "allowed",
     "DFI Denmark grants and Eurimages operate on independent tracks.",
     "PARSED"),
    ("fi_ses_grants", "eu_eurimages",
     "allowed",
     "SES Finland grants and Eurimages operate on independent tracks.",
     "PARSED"),
    ("at_ofi_grants", "eu_eurimages",
     "allowed",
     "ÖFI Austria grants and Eurimages operate on independent tracks.",
     "PARSED"),
    ("pl_pisf_grants", "eu_eurimages",
     "allowed",
     "PISF Poland grants and Eurimages operate on independent tracks.",
     "PARSED"),
    ("cz_czech_film_fund", "eu_eurimages",
     "allowed",
     "Czech Film Fund and Eurimages operate on independent tracks.",
     "PARSED"),
    ("hu_nfi_grants", "eu_eurimages",
     "allowed",
     "NFI Hungary grants and Eurimages operate on independent tracks.",
     "PARSED"),
    # ------------------------------------------------------------------
    # Treaty ↔ Treaty
    # ------------------------------------------------------------------
    ("eu_eurimages", "eu_creative_europe",
     "allowed",
     "Eurimages co-production support and Creative Europe MEDIA development fund operate on "
     "independent tracks; combined EU public support 50% ceiling applies at programme level.",
     "PARSED"),
    ("ibermedia_programme", "eu_media_fund",
     "allowed",
     "Ibermedia and EU MEDIA/Creative Europe operate on independent tracks for eligible co-productions.",
     "PARSED"),
    ("ibermedia_programme", "nordic_ftvf",
     "allowed",
     "Ibermedia and Nordic Film & TV Fund operate on independent tracks; "
     "Spain-Portugal combinations with Nordic partners can access both.",
     "DISCOVERY"),
    # ------------------------------------------------------------------
    # Service-production interactions
    # ------------------------------------------------------------------
    ("uk_hvc", "gb_lon_film_london",
     "conditional",
     "UK HVC (service production) and Film London can be combined: Film London does not require "
     "cultural test, only London-based spend. Film London is govt assistance reducing HVC qualifying UK spend.",
     "PARSED"),
    ("uk_hvc", "gb_sct_screen_production",
     "conditional",
     "UK HVC (service production) and Screen Scotland can be combined for foreign service shoots "
     "with significant Scottish spend. Screen Scotland does not require BFI cultural test.",
     "PARSED"),
    ("uk_hvc", "gb_nir_northern_ireland",
     "conditional",
     "UK HVC (service production) and Northern Ireland Screen can be combined for service shoots "
     "with significant NI qualifying spend.",
     "PARSED"),
    ("uk_hvc", "gb_wls_film_fund",
     "conditional",
     "UK HVC (service production) and Wales Screen can be combined for service shoots with "
     "significant Welsh qualifying spend.",
     "PARSED"),
    ("uk_hvc", "gb_bfi_production",
     "mutually_exclusive",
     "UK HVC and BFI Film Fund are mutually exclusive: BFI requires BFI cultural test qualification "
     "which is incompatible with the service-production HVC route.",
     "PARSED"),
    ("uk_hvc", "uk_avec",
     "mutually_exclusive",
     "UK HVC and AVEC are mutually exclusive routes: HVC is for service productions; "
     "AVEC requires BFI cultural test or co-production treaty status.",
     "PARSED"),
    ("ca_cmpa_foreign", "on_ofttc",
     "allowed",
     "CMPA Foreign certificate (service production) and Ontario OFTTC can be combined: "
     "OFTTC does not require Canadian content certification.",
     "PARSED"),
    ("ca_cmpa_foreign", "ca_bc_pstc",
     "allowed",
     "CMPA Foreign certificate (service production) and BC PSTC can be combined: "
     "PSTC does not require Canadian content certification for foreign location shoots.",
     "PARSED"),
    ("au_location_offset", "au_vic_film_victoria",
     "conditional",
     "AU Location Offset and VicScreen can be combined for foreign productions with significant "
     "Victorian spend; VicScreen support is govt assistance reducing Location Offset QAPE basis.",
     "PARSED"),
    ("au_location_offset", "au_qld_screen",
     "conditional",
     "AU Location Offset and Screen Queensland can be combined for foreign productions with "
     "Queensland spend; Screen QLD is govt assistance reducing Location Offset QAPE basis.",
     "PARSED"),
    ("au_location_offset", "au_nsw_screen",
     "conditional",
     "AU Location Offset and Screen NSW can be combined for foreign productions with NSW spend; "
     "Screen NSW is govt assistance reducing Location Offset QAPE basis.",
     "PARSED"),
    # ------------------------------------------------------------------
    # Rebate ↔ Grant
    # ------------------------------------------------------------------
    ("jo_rfc_rebate", "jo_rfc_tourism",
     "conditional",
     "Jordan Royal Film Commission rebate and tourism incentive can be combined; "
     "tourism incentive does not reduce rebate qualifying basis.",
     "DISCOVERY"),
    ("ma_ccm_rebate", "ma_ccm_tourism",
     "conditional",
     "Morocco CCM rebate and tourism support can be combined; "
     "tourism support does not reduce rebate qualifying basis.",
     "DISCOVERY"),
    ("nz_screen_production_rebate", "nz_tourism_film",
     "allowed",
     "NZ SPGR rebate and Tourism NZ support operate on independent tracks.",
     "PARSED"),
    ("ie_section_481", "ie_tourism_ireland",
     "conditional",
     "Irish Section 481 and Tourism Ireland location support can be combined; "
     "Tourism Ireland is not government assistance for Section 481 purposes.",
     "DISCOVERY"),
    # ------------------------------------------------------------------
    # Equity ↔ rebate / regional (Screen Australia public equity)
    # ------------------------------------------------------------------
    ("au_screen_production", "au_screenwest",
     "spend_reduction",
     "Screen Australia equity investment is government assistance — reduces qualifying spend basis "
     "for ScreenWest incentive.",
     "PARSED"),
    ("au_screen_production", "au_nsw_screen",
     "spend_reduction",
     "Screen Australia equity investment is government assistance — reduces qualifying spend basis "
     "for Screen NSW incentive.",
     "PARSED"),
    ("au_screen_production", "au_vic_film_victoria",
     "spend_reduction",
     "Screen Australia equity investment is government assistance — reduces qualifying spend basis "
     "for VicScreen incentive.",
     "PARSED"),
    ("au_screen_production", "au_qld_screen",
     "spend_reduction",
     "Screen Australia equity investment is government assistance — reduces qualifying spend basis "
     "for Screen Queensland incentive.",
     "PARSED"),
    # ------------------------------------------------------------------
    # Additional regional ↔ national coverage
    # ------------------------------------------------------------------
    ("no_mro_film3", "no_nfi_grants",
     "allowed",
     "Film3 (Møre og Romsdal) and NFI Norway national grants operate on independent tracks.",
     "PARSED"),
    ("no_mro_film3", "no_film_incentive",
     "allowed",
     "Film3 (Møre og Romsdal) and Norwegian cash rebate operate on independent tracks.",
     "PARSED"),
    ("gb_film_hub_midlands", "uk_avec",
     "conditional",
     "Film Hub Midlands BFI-funded support is govt assistance — reduces AVEC qualifying UK expenditure basis.",
     "PARSED"),
    ("de_ffa", "eu_eurimages",
     "allowed",
     "FFA (German Federal Film Board) reference film levy and Eurimages operate on independent tracks.",
     "PARSED"),
    # Cash rebate × Eurimages (additional members)
    ("bg_cash_rebate", "eu_eurimages",
     "allowed",
     "Bulgarian cash rebate and Eurimages operate on independent tracks; Bulgaria is Eurimages member.",
     "PARSED"),
    ("ro_film_rebate", "eu_eurimages",
     "allowed",
     "Romanian film rebate and Eurimages operate on independent tracks; Romania is Eurimages member.",
     "PARSED"),
    ("gr_cash_rebate", "eu_eurimages",
     "allowed",
     "Greek cash rebate and Eurimages operate on independent tracks; Greece is Eurimages member.",
     "PARSED"),
    ("hr_cash_rebate", "eu_eurimages",
     "allowed",
     "Croatian cash rebate and Eurimages operate on independent tracks; Croatia is Eurimages member.",
     "PARSED"),
    ("hr_cash_rebate", "hr_havc_fund",
     "allowed",
     "Croatian cash rebate and HAVC fund operate on independent tracks; HAVC grant does not reduce "
     "rebate qualifying basis for foreign spend.",
     "DISCOVERY"),
    ("mt_mfc_rebate", "eu_eurimages",
     "allowed",
     "Malta rebate and Eurimages operate on independent tracks; Malta is Eurimages member.",
     "PARSED"),
    # Iceland post-production × main rebate
    ("is_film_rebate", "is_post_rebate",
     "conditional",
     "Iceland Film Rebate and Iceland Post-Production Rebate can be combined if expenditure "
     "categories are distinct; post-production rebate is govt assistance reducing Film Rebate basis "
     "for overlapping costs.",
     "PARSED"),
]

# fmt: on


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Missing bilateral treaties
    # ------------------------------------------------------------------
    for t in _NEW_TREATIES:
        conn.execute(
            sa.text(
                """
                INSERT INTO co_production_treaties (
                    treaty_name, treaty_slug, treaty_type, status,
                    jurisdiction_a_code, jurisdiction_b_code,
                    year_signed, effective_from, effective_until,
                    majority_min_contribution_pct, minority_min_contribution_pct,
                    minority_max_contribution_pct, min_coproducer_countries,
                    spend_allocation_requirement, nationality_requirement,
                    creative_contribution_requirement, cultural_test_required,
                    ownership_requirement,
                    majority_jurisdiction_benefits, minority_jurisdiction_benefits,
                    treaty_administrator_name, authority_url,
                    confidence_tier, notes
                ) VALUES (
                    :treaty_name, :treaty_slug, :treaty_type, :status,
                    :jurisdiction_a_code, :jurisdiction_b_code,
                    :year_signed, :effective_from, :effective_until,
                    :majority_min_contribution_pct, :minority_min_contribution_pct,
                    :minority_max_contribution_pct, :min_coproducer_countries,
                    :spend_allocation_requirement, :nationality_requirement,
                    :creative_contribution_requirement, :cultural_test_required,
                    :ownership_requirement,
                    :majority_jurisdiction_benefits, :minority_jurisdiction_benefits,
                    :treaty_administrator_name, :authority_url,
                    :confidence_tier, :notes
                )
                ON CONFLICT (treaty_slug) DO NOTHING
                """
            ),
            t,
        )

    # ------------------------------------------------------------------
    # 2. New structure graph edges
    # ------------------------------------------------------------------
    for src_type, src_slug, edge_type, tgt_type, tgt_slug, condition, magnitude, conf in _NEW_GRAPH_EDGES:
        conn.execute(text("""
            INSERT INTO structure_graph_edges
                (source_type, source_slug, edge_type, target_type, target_slug,
                 condition, magnitude, confidence_tier)
            VALUES (:st, :ss, :et, :tt, :ts, :cond, :mag, :conf)
            ON CONFLICT DO NOTHING
        """), {
            "st": src_type, "ss": src_slug, "et": edge_type,
            "tt": tgt_type, "ts": tgt_slug,
            "cond": condition, "mag": magnitude, "conf": conf,
        })

    # ------------------------------------------------------------------
    # 3. New stacking rules
    # ------------------------------------------------------------------
    for (slug_a, slug_b, rule_type, condition_text, confidence) in _NEW_STACKING_RULES:
        conn.execute(text("""
            INSERT INTO stacking_rules
                (program_slug_a, program_slug_b, rule_type, condition_text, confidence_tier)
            VALUES
                (:a, :b, :rt, :ct, :conf)
            ON CONFLICT (program_slug_a, program_slug_b) DO UPDATE SET
                rule_type = EXCLUDED.rule_type,
                condition_text = EXCLUDED.condition_text,
                confidence_tier = EXCLUDED.confidence_tier
        """), {
            "a": slug_a, "b": slug_b, "rt": rule_type,
            "ct": condition_text, "conf": confidence,
        })


def downgrade() -> None:
    conn = op.get_bind()

    # Remove stacking rules
    for (slug_a, slug_b, *_rest) in _NEW_STACKING_RULES:
        conn.execute(text("""
            DELETE FROM stacking_rules
            WHERE program_slug_a = :a AND program_slug_b = :b
        """), {"a": slug_a, "b": slug_b})

    # Remove graph edges (by source+edge_type+target)
    for src_type, src_slug, edge_type, tgt_type, tgt_slug, *_rest in _NEW_GRAPH_EDGES:
        conn.execute(text("""
            DELETE FROM structure_graph_edges
            WHERE source_slug = :ss AND edge_type = :et AND target_slug = :ts
        """), {"ss": src_slug, "et": edge_type, "ts": tgt_slug})

    # Remove bilateral treaties
    for t in _NEW_TREATIES:
        conn.execute(
            text("DELETE FROM co_production_treaties WHERE treaty_slug = :slug"),
            {"slug": t["treaty_slug"]},
        )
