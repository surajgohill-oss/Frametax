"""
test_knowledge_completion.py — Knowledge database completion pass (migration 0061).

Validates:
  1. All new edge types are present in the graph model
  2. depends_on, service_only, broadcaster_only, regional_only, national_only, fund_only
  3. Key bilateral treaty unlock edges exist
  4. New stacking rules are encoded in _SLUG_PAIR_RULES
  5. Co-production structure edges (Eurimages, Ibermedia, European Convention)
  6. Service-production mutual exclusions are correct
  7. Structural consistency checks
"""
import pytest

from app.data.structure_graph_model import (
    STRUCTURE_GRAPH_EDGES,
    get_edges_by_type,
    get_edges_from,
    get_edges_to,
    get_unlocked_by,
)
from app.optimization.stacking_rules import _SLUG_PAIR_RULES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_edge(source_slug: str, edge_type: str, target_slug: str) -> bool:
    return any(
        e.source_slug == source_slug and e.edge_type == edge_type and e.target_slug == target_slug
        for e in STRUCTURE_GRAPH_EDGES
    )


def _stacking_rule(slug_a: str, slug_b: str) -> dict | None:
    return _SLUG_PAIR_RULES.get(frozenset({slug_a, slug_b}))


# ---------------------------------------------------------------------------
# 1. New edge types exist
# ---------------------------------------------------------------------------

def test_kc_depends_on_edges_exist():
    edges = get_edges_by_type("depends_on")
    assert len(edges) >= 8, f"Expected ≥8 depends_on edges, got {len(edges)}"


def test_kc_service_only_edges_exist():
    edges = get_edges_by_type("service_only")
    assert len(edges) >= 3, f"Expected ≥3 service_only edges, got {len(edges)}"


def test_kc_broadcaster_only_edges_exist():
    edges = get_edges_by_type("broadcaster_only")
    assert len(edges) >= 3, f"Expected ≥3 broadcaster_only edges, got {len(edges)}"


def test_kc_regional_only_edges_exist():
    edges = get_edges_by_type("regional_only")
    assert len(edges) >= 40, f"Expected ≥40 regional_only edges, got {len(edges)}"


def test_kc_national_only_edges_exist():
    edges = get_edges_by_type("national_only")
    assert len(edges) >= 6, f"Expected ≥6 national_only edges, got {len(edges)}"


def test_kc_fund_only_edges_exist():
    edges = get_edges_by_type("fund_only")
    assert len(edges) >= 3, f"Expected ≥3 fund_only edges, got {len(edges)}"


# ---------------------------------------------------------------------------
# 2. depends_on — specific key dependencies
# ---------------------------------------------------------------------------

def test_kc_cmf_depends_on_broadcaster():
    assert _has_edge("ca_cmf", "depends_on", "cbc_original"), \
        "ca_cmf should depend_on cbc_original (broadcaster trigger)"


def test_kc_eurimages_depends_on_treaty():
    assert _has_edge("eu_eurimages", "depends_on", "eurimages-multilateral"), \
        "eu_eurimages should depend_on eurimages-multilateral"


def test_kc_ibermedia_depends_on_treaty():
    assert _has_edge("ibermedia_programme", "depends_on", "ibermedia-multilateral"), \
        "ibermedia_programme should depend_on ibermedia-multilateral"


def test_kc_au_producer_offset_depends_on_content_test():
    assert _has_edge("au_producer_offset", "depends_on", "au_content_test"), \
        "au_producer_offset should depend_on au_content_test"


def test_kc_fr_trip_depends_on_cultural_test():
    assert _has_edge("fr_trip", "depends_on", "fr_cnc_cultural_test"), \
        "fr_trip should depend_on fr_cnc_cultural_test"


def test_kc_nordic_ftvf_depends_on_broadcaster():
    assert _has_edge("nordic_ftvf", "depends_on", "se_svt"), \
        "nordic_ftvf should depend_on se_svt (at least one Nordic broadcaster)"


# ---------------------------------------------------------------------------
# 3. service_only — specific programs
# ---------------------------------------------------------------------------

def test_kc_uk_hvc_is_service_only():
    assert _has_edge("uk_hvc", "service_only", "uk_hvc"), \
        "uk_hvc should be service_only"


def test_kc_ca_cmpa_foreign_is_service_only():
    assert _has_edge("ca_cmpa_foreign", "service_only", "ca_cmpa_foreign"), \
        "ca_cmpa_foreign should be service_only"


def test_kc_au_location_offset_is_service_only():
    assert _has_edge("au_location_offset", "service_only", "au_location_offset"), \
        "au_location_offset should be service_only"


# ---------------------------------------------------------------------------
# 4. broadcaster_only — specific programs
# ---------------------------------------------------------------------------

def test_kc_ca_cmf_is_broadcaster_only():
    assert _has_edge("ca_cmf", "broadcaster_only", "ca_cmf"), \
        "ca_cmf should be broadcaster_only"


def test_kc_bell_fund_is_broadcaster_only():
    assert _has_edge("ca_bell_fund", "broadcaster_only", "ca_bell_fund"), \
        "ca_bell_fund should be broadcaster_only"


def test_kc_nordic_ftvf_is_broadcaster_only():
    assert _has_edge("nordic_ftvf", "broadcaster_only", "nordic_ftvf"), \
        "nordic_ftvf should be broadcaster_only"


# ---------------------------------------------------------------------------
# 5. regional_only — spot checks across jurisdictions
# ---------------------------------------------------------------------------

_EXPECTED_REGIONAL_ONLY = [
    "no_vgn_viken", "no_rog_vestnorsk", "no_tro_nordnorsk", "no_inl_midtnorsk",
    "film_i_vast", "se_sk_film_skane", "se_ab_filmstockholm",
    "gb_lon_film_london", "gb_sct_screen_production", "gb_wls_film_fund", "gb_nir_northern_ireland",
    "de_bb_medienboard", "de_nrw_filmstiftung", "de_fff_bayern",
    "fr_idf_regional", "fr_naq_regional", "fr_ara_regional", "fr_occ_regional",
    "it_laz_lazio_fc", "it_sic_sicilia_fc", "it_cam_campania_fc",
    "es_cat_icec", "es_eus_basque", "es_gal_agadic",
    "au_vic_film_victoria", "au_qld_screen", "au_nsw_screen", "au_sa_safc",
    "ca_bc_pstc", "on_ofttc", "qc_film_production", "nohfc_production_fund",
    "dk_cph_film_fund", "dk_fyn_film",
]


@pytest.mark.parametrize("slug", _EXPECTED_REGIONAL_ONLY)
def test_kc_regional_only_slug(slug: str):
    assert _has_edge(slug, "regional_only", slug), \
        f"{slug} should have regional_only self-edge"


# ---------------------------------------------------------------------------
# 6. national_only — key programs
# ---------------------------------------------------------------------------

_EXPECTED_NATIONAL_ONLY = [
    "ca_federal_cptc", "au_producer_offset", "ie_section_481",
    "uk_avec", "fr_trip", "de_dfff",
]


@pytest.mark.parametrize("slug", _EXPECTED_NATIONAL_ONLY)
def test_kc_national_only_slug(slug: str):
    assert _has_edge(slug, "national_only", slug), \
        f"{slug} should have national_only self-edge"


# ---------------------------------------------------------------------------
# 7. fund_only — key programs
# ---------------------------------------------------------------------------

def test_kc_eu_media_fund_is_fund_only():
    assert _has_edge("eu_media_fund", "fund_only", "eu_media_fund")


def test_kc_eu_eurimages_is_fund_only():
    assert _has_edge("eu_eurimages", "fund_only", "eu_eurimages")


def test_kc_ibermedia_is_fund_only():
    assert _has_edge("ibermedia_programme", "fund_only", "ibermedia_programme")


# ---------------------------------------------------------------------------
# 8. Missing bilateral treaty unlocks
# ---------------------------------------------------------------------------

def test_kc_uk_it_unlocks_avec():
    assert _has_edge("uk-it-bilateral", "unlocks", "uk_avec")


def test_kc_uk_it_unlocks_italian_tax_credit():
    assert _has_edge("uk-it-bilateral", "unlocks", "it_tax_credit_foreign")


def test_kc_au_fr_unlocks_producer_offset():
    assert _has_edge("au-fr-bilateral", "unlocks", "au_producer_offset")


def test_kc_au_fr_unlocks_trip():
    assert _has_edge("au-fr-bilateral", "unlocks", "fr_trip")


def test_kc_au_nz_unlocks_producer_offset():
    assert _has_edge("au-nz-bilateral", "unlocks", "au_producer_offset")


def test_kc_au_nz_unlocks_nz_rebate():
    assert _has_edge("au-nz-bilateral", "unlocks", "nz_screen_production_rebate")


def test_kc_de_at_unlocks_dfff():
    assert _has_edge("de-at-bilateral", "unlocks", "de_dfff")


def test_kc_de_at_unlocks_ofi():
    assert _has_edge("de-at-bilateral", "unlocks", "at_ofi_grants")


def test_kc_de_pl_unlocks_pisf():
    assert _has_edge("de-pl-bilateral", "unlocks", "pl_pisf_grants")


def test_kc_de_hu_unlocks_nfi_hungary():
    assert _has_edge("de-hu-bilateral", "unlocks", "hu_nfi_grants")


def test_kc_de_cz_unlocks_czech_fund():
    assert _has_edge("de-cz-bilateral", "unlocks", "cz_czech_film_fund")


def test_kc_kr_fr_unlocks_kofic():
    assert _has_edge("kr-fr-bilateral", "unlocks", "kr_kofic_production")


def test_kc_kr_fr_unlocks_trip():
    assert _has_edge("kr-fr-bilateral", "unlocks", "fr_trip")


def test_kc_kr_de_unlocks_dfff():
    assert _has_edge("kr-de-bilateral", "unlocks", "de_dfff")


def test_kc_au_kr_unlocks_kofic():
    assert _has_edge("au-kr-bilateral", "unlocks", "kr_kofic_production")


# ---------------------------------------------------------------------------
# 9. Eurimages multilateral structure
# ---------------------------------------------------------------------------

def test_kc_eurimages_multilateral_unlocks_avec():
    assert _has_edge("eurimages-multilateral", "unlocks", "uk_avec")


def test_kc_eurimages_multilateral_unlocks_trip():
    assert _has_edge("eurimages-multilateral", "unlocks", "fr_trip")


def test_kc_eurimages_multilateral_unlocks_dfff():
    assert _has_edge("eurimages-multilateral", "unlocks", "de_dfff")


def test_kc_eurimages_multilateral_unlocks_pisf():
    assert _has_edge("eurimages-multilateral", "unlocks", "pl_pisf_grants")


def test_kc_ibermedia_multilateral_unlocks_ica():
    assert _has_edge("ibermedia-multilateral", "unlocks", "pt_ica_grants")


def test_kc_ibermedia_multilateral_unlocks_icaa():
    assert _has_edge("ibermedia-multilateral", "unlocks", "es_icaa_credit")


def test_kc_european_convention_unlocks_avec():
    assert _has_edge("european-convention-coproduction", "unlocks", "uk_avec")


# ---------------------------------------------------------------------------
# 10. New stacking rules — regional ↔ broadcaster
# ---------------------------------------------------------------------------

def test_kc_stacking_film_london_bbc():
    rule = _stacking_rule("gb_lon_film_london", "gb_bbc_films")
    assert rule is not None, "Film London + BBC Films should have stacking rule"
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_screen_scotland_bbc():
    rule = _stacking_rule("gb_sct_screen_production", "gb_bbc_films")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_wales_film4():
    rule = _stacking_rule("gb_wls_film_fund", "gb_film4")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_viken_nrk():
    rule = _stacking_rule("no_vgn_viken", "no_nrk")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_skane_svt():
    rule = _stacking_rule("se_sk_film_skane", "se_svt")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


# ---------------------------------------------------------------------------
# 11. New stacking rules — grant ↔ treaty
# ---------------------------------------------------------------------------

def test_kc_stacking_bfi_eurimages():
    rule = _stacking_rule("gb_bfi_production", "eu_eurimages")
    assert rule is not None, "BFI Film Fund + Eurimages should have stacking rule"
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_screen_ireland_eurimages():
    rule = _stacking_rule("ie_screen_ireland_dev", "eu_eurimages")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_cnc_ibermedia():
    rule = _stacking_rule("fr_cnc_production", "ibermedia_programme")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_nfi_norway_eurimages():
    rule = _stacking_rule("no_nfi_grants", "eu_eurimages")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


# ---------------------------------------------------------------------------
# 12. Treaty ↔ Treaty
# ---------------------------------------------------------------------------

def test_kc_stacking_eurimages_creative_europe():
    rule = _stacking_rule("eu_eurimages", "eu_creative_europe")
    assert rule is not None, "Eurimages + Creative Europe should have stacking rule"
    assert rule["rule_type"] == "allowed"


def test_kc_stacking_ibermedia_eu_media():
    rule = _stacking_rule("ibermedia_programme", "eu_media_fund")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


# ---------------------------------------------------------------------------
# 13. Service-production stacking mutual exclusions
# ---------------------------------------------------------------------------

def test_kc_stacking_hvc_avec_mutually_exclusive():
    rule = _stacking_rule("uk_hvc", "uk_avec")
    assert rule is not None, "uk_hvc + uk_avec must have stacking rule"
    assert rule["rule_type"] == "mutually_exclusive"


def test_kc_stacking_hvc_bfi_mutually_exclusive():
    rule = _stacking_rule("uk_hvc", "gb_bfi_production")
    assert rule is not None
    assert rule["rule_type"] == "mutually_exclusive"


def test_kc_stacking_hvc_film_london_conditional():
    rule = _stacking_rule("uk_hvc", "gb_lon_film_london")
    assert rule is not None, "uk_hvc + Film London should have stacking rule"
    assert rule["rule_type"] == "conditional"


def test_kc_stacking_cmpa_foreign_ontario_ofttc_allowed():
    rule = _stacking_rule("ca_cmpa_foreign", "on_ofttc")
    assert rule is not None
    assert rule["rule_type"] == "allowed"


# ---------------------------------------------------------------------------
# 14. Equity ↔ rebate / regional
# ---------------------------------------------------------------------------

def test_kc_stacking_screen_au_screenwest():
    rule = _stacking_rule("au_screen_production", "au_screenwest")
    assert rule is not None
    assert rule["rule_type"] == "spend_reduction"


def test_kc_stacking_screen_au_vicscreen():
    rule = _stacking_rule("au_screen_production", "au_vic_film_victoria")
    assert rule is not None
    assert rule["rule_type"] == "spend_reduction"


# ---------------------------------------------------------------------------
# 15. Structural integrity of new edges
# ---------------------------------------------------------------------------

def test_kc_no_duplicate_edges():
    edge_keys = [
        (e.source_slug, e.edge_type, e.target_slug)
        for e in STRUCTURE_GRAPH_EDGES
    ]
    assert len(edge_keys) == len(set(edge_keys)), \
        "Duplicate edges found in STRUCTURE_GRAPH_EDGES"


def test_kc_all_edges_have_required_fields():
    for e in STRUCTURE_GRAPH_EDGES:
        assert e.source_type, f"Missing source_type on edge {e}"
        assert e.source_slug, f"Missing source_slug on edge {e}"
        assert e.edge_type, f"Missing edge_type on edge {e}"
        assert e.target_type, f"Missing target_type on edge {e}"
        assert e.target_slug, f"Missing target_slug on edge {e}"


def test_kc_total_edges_count():
    """Sanity check that the graph has grown to a meaningful size."""
    assert len(STRUCTURE_GRAPH_EDGES) >= 440, \
        f"Expected ≥440 total edges, got {len(STRUCTURE_GRAPH_EDGES)}"


def test_kc_stacking_rules_count():
    """Verify total slug-pair rules grew significantly."""
    assert len(_SLUG_PAIR_RULES) >= 180, \
        f"Expected ≥180 _SLUG_PAIR_RULES, got {len(_SLUG_PAIR_RULES)}"


# ---------------------------------------------------------------------------
# 16. Edge type distribution
# ---------------------------------------------------------------------------

def test_kc_edge_type_distribution():
    from collections import Counter
    counts = Counter(e.edge_type for e in STRUCTURE_GRAPH_EDGES)
    for edge_type in ["unlocks", "requires", "improves", "reduces", "incompatible_with",
                      "enables", "complements", "alternative_to", "blocks",
                      "majority_only", "minority_only",
                      "depends_on", "service_only", "regional_only",
                      "national_only", "broadcaster_only", "fund_only"]:
        assert counts[edge_type] > 0, f"No edges of type {edge_type!r}"
