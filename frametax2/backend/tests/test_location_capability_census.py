"""Location-capability census, final closure (2026-10-06): fixed 114 x 10 matrix, owner wiring, combined-category semantics,
authority/provenance, hard/soft fit. Pure tests: no database, no network, no evaluation."""
from __future__ import annotations

import csv
import dataclasses
import importlib.util
import json
from pathlib import Path

from app.calculators import jurisdiction_comparison as jc
from app.calculators import production_requirements as pr
from app.data import jurisdiction_location_capability as data
from app.data.jurisdiction_location_capability import (
    ACCEPTED_TIERS, CELLS, COMPONENT_TOKENS, LOCATION_CENSUS_CATEGORIES, NOT_SUPPORTED, SOURCES, SUPPORTED, TERMINAL_STATUS, UNRESOLVED_NEUTRAL,
)
from app.services import production_fit as pf

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv"
SUMMARY_PATH = CSV_PATH.with_suffix(".summary.json")
BUILDER = Path(__file__).resolve().parents[1] / "scripts/build_location_capability_census.py"
REQUIRED_COLUMNS = [
    "jurisdiction_code", "jurisdiction_name", "category", "terminal_status", "component_capabilities", "canonical_capability_tokens",
    "evidence_proposition", "source_title", "source_url_or_identifier", "publisher", "source_version_or_checked_date", "evidence_tier",
    "derivation_method", "sources_attempted_if_unresolved", "runtime_consumed", "notes",
]


def _reqs(*categories):
    return pr.derive_production_requirements({"location_categories": {c: {"effective": True, "evidence": ["x"]} for c in categories}})


def _builder():
    spec = importlib.util.spec_from_file_location("census_builder", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _all_cells():
    return [(c, cat, cell) for c in jc.location_census_jurisdictions() for cat, cell in jc.location_capability_cells(c).items()]


def _codes(category, status, *, profiles_only=True):
    return sorted(c for c in jc.location_census_jurisdictions() if (c in jc.ALL_PROFILES or not profiles_only)
                  and jc.location_capability_cells(c)[category].status == status)


# ── inventory and terminal states ───────────────────────────────────────────────────────────────────────────────────────
def test_the_frozen_inventory_is_114_jurisdictions_by_10_categories_with_no_duplicate_or_missing_cell():
    codes = jc.location_census_jurisdictions()
    assert len(codes) == 114 == len(jc.ALL_PROFILES) + 1 and "US" in codes and len(set(codes)) == 114
    assert len(LOCATION_CENSUS_CATEGORIES) == 10
    assert set(CELLS) == {(c, cat) for c in codes for cat in LOCATION_CENSUS_CATEGORIES} and len(CELLS) == 1140


def test_every_cell_is_one_of_three_terminal_states_and_there_is_no_generic_unknown():
    assert {c.status for _, _, c in _all_cells()} <= {SUPPORTED, NOT_SUPPORTED, UNRESOLVED_NEUTRAL}
    assert set(TERMINAL_STATUS.values()) == {"AUTHORITY_VERIFIED_SUPPORTED", "AUTHORITY_VERIFIED_NOT_SUPPORTED", "AUTHORITY_UNRESOLVED_NEUTRAL"}
    assert "UNKNOWN" not in {v[0] for v in CELLS.values()}
    rows = list(csv.DictReader(CSV_PATH.open()))
    assert {r["terminal_status"] for r in rows} <= set(TERMINAL_STATUS.values())
    assert not [r for r in rows if "UNKNOWN" in r["terminal_status"]]
    assert json.loads(SUMMARY_PATH.read_text())["generic_unknown_cells"] == 0


def test_no_discovery_tier_record_is_represented_as_verified():
    blob = json.dumps({"sources": SOURCES, "cells": [[v[0], v[2], v[3], v[4]] for v in CELLS.values()]}, default=str).upper()
    assert "DISCOVERY" not in blob and "RETAINED_INVENTORY_RECORD" not in blob and "RETAINED_PROFILE_RECORD" not in blob
    assert not hasattr(data, "RETAINED_SUPPORTED")
    assert {s["tier"] for s in SOURCES.values()} <= set(ACCEPTED_TIERS)
    for _, _, cell in _all_cells():
        assert cell.evidence_tier in ACCEPTED_TIERS if cell.status != UNRESOLVED_NEUTRAL else cell.evidence_tier == ""


def test_every_verified_cell_carries_adequate_authority_and_provenance():
    for code, cat, cell in _all_cells():
        if cell.status == UNRESOLVED_NEUTRAL:
            continue
        assert cell.proposition and cell.derivation_method and cell.source_ids, (code, cat)
        for src in cell.sources:
            for key in ("title", "publisher", "url", "version", "tier", "method"):
                assert src[key], (code, cat, src["title"], key)
            assert src["url"].startswith("http")
        assert cell.evidence_tier in ACCEPTED_TIERS and cell.source_version and cell.publisher, (code, cat)


def test_every_unresolved_cell_records_the_sources_attempted_and_the_missing_proposition():
    rows = [r for r in csv.DictReader(CSV_PATH.open()) if r["terminal_status"] == "AUTHORITY_UNRESOLVED_NEUTRAL"]
    assert len(rows) == sum(1 for _, _, c in _all_cells() if c.status == UNRESOLVED_NEUTRAL) > 0
    for r in rows:
        attempted = r["sources_attempted_if_unresolved"]
        assert len(attempted.split(" | ")) >= 2 and "missing proposition:" in attempted, (r["jurisdiction_code"], r["category"])
        assert r["evidence_tier"] == ""
    for code, cat, cell in _all_cells():
        if cell.status == UNRESOLVED_NEUTRAL and cat != "island_tropical":
            assert cell.sources_attempted, (code, cat)


def test_negative_dispositions_rest_only_on_the_datasets_own_category_definition():
    for code, cat, cell in _all_cells():
        if cell.status != NOT_SUPPORTED:
            continue
        p = cell.proposition.lower()
        assert {"island_tropical": "no marine coastline" in p and "no koppen-geiger group a" in p,
                "jungle_rainforest": "only arid/cold/polar" in p,
                "desert_arid": "no koppen-geiger arid" in p,
                "snow_arctic": "every classified cell is tropical" in p,
                "forest_woodland": "tree-covered area" in p}.get(cat, False), (code, cat, cell.proposition)


# ── combined category: island OR tropical ───────────────────────────────────────────────────────────────────────────────
def test_island_tropical_is_a_combined_category_with_OR_semantics():
    for code, _, cell in [(c, k, v) for c, k, v in _all_cells() if k == "island_tropical"]:
        comp = dict(cell.components)
        assert set(comp) == set(COMPONENT_TOKENS.values()), code
        expected = SUPPORTED if SUPPORTED in comp.values() else NOT_SUPPORTED if set(comp.values()) == {NOT_SUPPORTED} else UNRESOLVED_NEUTRAL
        assert cell.status == expected, (code, comp)


def test_landlocked_alone_never_establishes_not_tropical_or_not_island_tropical():
    landlocked = [c for c, p in jc.ALL_PROFILES.items() if str(p.marine_suitability).lower() == "none"]
    assert landlocked
    for code in landlocked:
        comp = dict(jc.location_capability_cells(code)["island_tropical"].components)
        cell = jc.location_capability_cells(code)["island_tropical"]
        if cell.status == NOT_SUPPORTED:               # only with BOTH components independently proven
            assert comp["tropical_climate_environments"] == NOT_SUPPORTED and "koppen" in cell.proposition.lower()
        # a landlocked profile whose tropical component is not proven absent is never rejected
        if comp["tropical_climate_environments"] != NOT_SUPPORTED:
            assert cell.status != NOT_SUPPORTED


def test_the_runtime_applies_the_OR_rule_to_the_chip_token_and_keeps_components_separate(monkeypatch):
    real = jc.location_capability_cells

    def patched(code):
        cells = dict(real(code))
        if code == "GR":
            c = cells["island_tropical"]
            cells["island_tropical"] = dataclasses.replace(
                c, status=UNRESOLVED_NEUTRAL, components=((COMPONENT_TOKENS["island"], NOT_SUPPORTED), (COMPONENT_TOKENS["tropical"], UNRESOLVED_NEUTRAL)))
        return cells

    monkeypatch.setattr(jc, "location_capability_cells", patched)
    cap = pr.jurisdiction_capability_profile("GR")
    assert "tropical_environments" not in cap.location_not_supported and "tropical_environments" not in cap.provisions
    assert COMPONENT_TOKENS["island"] in cap.location_not_supported                    # the island component alone is denied
    assert pr.assess_location_capability("tropical_environments", cap)[0] == pr.ASSESS_UNKNOWN
    status, _ = pf.classify_jurisdiction_fit("GR", _reqs("island_tropical"))
    assert status in pf.FIT_CONFIRMED_STATUSES                                         # a soft chip never blocks


# ── runtime consumption ────────────────────────────────────────────────────────────────────────────────────────────────
def test_all_114_profiles_resolve_and_only_supported_cells_enter_the_provision_set():
    for code in jc.location_census_jurisdictions():
        cap = pr.jurisdiction_capability_profile(code)
        assert cap.has_capability_data, code
        cells = jc.location_capability_cells(code)
        chip_provisions = {t for t in cap.provisions if t in pr.LOCATION_CENSUS_TOKENS}
        assert chip_provisions == {c.token for c in cells.values() if c.status == SUPPORTED}, code
        assert {t for t in cap.location_not_supported if t in pr.LOCATION_CENSUS_TOKENS} == {c.token for c in cells.values() if c.status == NOT_SUPPORTED}
        assert not chip_provisions & cap.location_not_supported
        for c in cells.values():
            if c.status == UNRESOLVED_NEUTRAL:        # unresolved is neutral: in neither set, assessed UNKNOWN
                assert c.token not in cap.provisions | cap.location_not_supported
                assert pr.assess_location_capability(c.token, cap)[0] == pr.ASSESS_UNKNOWN


def test_national_us_is_a_real_profile_and_state_profiles_stay_independent():
    before = {c: pr.jurisdiction_capability_profile(c) for c in jc.ALL_PROFILES if c.startswith("US-")}
    us = pr.jurisdiction_capability_profile("US")
    assert us.has_capability_data and "open_water_filming" in us.provisions and us.marine_suitability in ("strong", "excellent")
    assert jc.location_capability_cells("US")["desert_arid"].source_ids and "US" not in jc.ALL_PROFILES
    assert pf.classify_jurisdiction_fit("US", _reqs("marine_open_water"))[0] in pf.FIT_CONFIRMED_STATUSES
    for code, cap in before.items():                                    # nothing a national result says rewrites a state
        assert pr.jurisdiction_capability_profile(code) == cap
    nm = pr.jurisdiction_capability_profile("US-NM")
    assert "open_water_filming" not in nm.provisions and pf.classify_jurisdiction_fit("US-NM", _reqs("marine_open_water"))[0] == pf.FIT_WEAK
    assert "island_environments" in nm.location_not_supported and "island_environments" in us.provisions   # state denial vs national support
    assert jc.location_capability_cells("US-NM") is not jc.location_capability_cells("US")


def test_a_verified_desert_jurisdiction_satisfies_the_hard_desert_requirement_a_verified_denial_is_not_suitable_and_unresolved_is_conditional():
    desert = _reqs("desert")
    assert "desert_environments" in desert.required_capabilities          # LLS-style hard requirement
    supported, denied, unresolved = (_codes("desert_arid", s, profiles_only=False) for s in (SUPPORTED, NOT_SUPPORTED, UNRESOLVED_NEUTRAL))
    assert {"QA", "IL", "CL", "PE", "US-AZ", "US-NM", "AE-AD", "AE-DXB", "US"} <= set(supported) and denied and unresolved
    for code in supported:
        status, reasons = pf.classify_jurisdiction_fit(code, desert)
        assert status in pf.FIT_CONFIRMED_STATUSES and not reasons, (code, status, reasons)
    for code in denied:                                                    # affirmatively unsupported hard capability -> Not Suitable
        status, reasons = pf.classify_jurisdiction_fit(code, desert)
        assert status == pf.FIT_WEAK and reasons[0] == "DESERT_ENVIRONMENTS_NOT_SUPPORTED", (code, status, reasons)
    for code in unresolved:                                                # unresolved hard -> Conditional, never unsuitable
        assert pf.classify_jurisdiction_fit(code, desert) == (pf.FIT_UNKNOWN, ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"]), code
    assert pf.classify_jurisdiction_fit("XX", desert)[0] == pf.FIT_UNKNOWN  # no profile at all


def test_soft_capability_absence_or_denial_never_forces_conditional_or_not_suitable():
    chips = {"island_tropical": "island_tropical", "jungle_rainforest": "jungle", "mountains_alpine": "mountain", "urban_major_city": "urban",
             "small_town_suburban": "small_town", "rural_countryside": "rural_countryside", "forest_woodland": "forest", "historic_old_world": "historic_old_world"}
    seen = {NOT_SUPPORTED: 0, UNRESOLVED_NEUTRAL: 0}
    for category, chip in chips.items():
        for code in jc.location_census_jurisdictions():
            status_ = jc.location_capability_cells(code)[category].status
            if status_ == SUPPORTED:
                continue
            status, reasons = pf.classify_jurisdiction_fit(code, _reqs(chip))
            if pf.classify_jurisdiction_fit(code, _reqs()) [0] == pf.FIT_UNKNOWN and code == "XX":
                continue
            assert status in pf.FIT_CONFIRMED_STATUSES and not any(r.endswith(("_NOT_ASSESSABLE", "_NOT_SUPPORTED")) for r in reasons), (code, category, status, reasons)
            seen[status_] += 1
    assert all(seen.values())                                              # both a denial and an unresolved soft cell were exercised


def test_hard_marine_semantics_are_unchanged_by_the_census():
    assert pf.classify_jurisdiction_fit("AT", _reqs("marine_open_water")) == (pf.FIT_WEAK, ["MARINE_MISMATCH"])
    assert pf.classify_jurisdiction_fit("GR", _reqs("marine_open_water"))[0] in pf.FIT_CONFIRMED_STATUSES
    assert pf.classify_jurisdiction_fit("GR", _reqs()) == (pf.FIT_UNKNOWN, ["NO_REQUIREMENTS_ON_FILE"])


def test_capability_evidence_is_served_with_the_fit_for_active_requirements_only():
    entry = pf.classify_entry_fit({"anchor_jurisdiction": "IL"}, _reqs("desert", "urban"))
    ev = {e["token"]: e for e in entry["production_fit_capability_evidence"]}
    assert set(ev) == {"desert_environments", "urban_environments"}
    d = ev["desert_environments"]
    assert d["hard_requirement"] is True and d["terminal_status"] == "AUTHORITY_VERIFIED_SUPPORTED" and d["evidence_tier"] in ACCEPTED_TIERS
    assert d["source_title"] and d["source_url"].startswith("http") and d["derivation_method"] and d["source_version"]
    assert ev["urban_environments"]["hard_requirement"] is False
    unresolved = _codes("desert_arid", UNRESOLVED_NEUTRAL)[0]
    assert pf.classify_entry_fit({"anchor_jurisdiction": unresolved}, _reqs("desert"))["production_fit_capability_evidence"] == []
    assert pf.classify_entry_fit({"anchor_jurisdiction": "IL"}, _reqs())["production_fit_basis"] == "NO_REQUIREMENTS_ON_FILE"


def test_service_only_routing_inherits_no_physical_penalty_and_physical_routing_uses_the_routed_leg():
    desert = _reqs("desert")
    denied, supported = _codes("desert_arid", NOT_SUPPORTED)[0], "IL"
    service = {"anchor_jurisdiction": supported, "component_allocations": [
        {"component": "principal_production", "jurisdiction_code": supported}, {"component": "vfx", "jurisdiction_code": denied}]}
    assert pf.classify_entry_fit(service, desert)["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES
    physical = {"anchor_jurisdiction": supported, "component_allocations": [{"component": "principal_production", "jurisdiction_code": denied}]}
    got = pf.classify_entry_fit(physical, desert)
    assert got["production_fit_status"] == pf.FIT_WEAK and got["production_fit_legs"] == [denied]


# ── artifact, controls, economics ───────────────────────────────────────────────────────────────────────────────────────
def test_the_committed_csv_is_exactly_1140_unique_rows_and_equals_the_owner():
    with CSV_PATH.open() as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == REQUIRED_COLUMNS
        rows = list(reader)
    assert len(rows) == 1140 and len({(r["jurisdiction_code"], r["category"]) for r in rows}) == 1140
    built = _builder().build_rows()
    assert rows == [{k: str(v) for k, v in r.items()} for r in built]
    summary = json.loads(SUMMARY_PATH.read_text())
    assert summary == json.loads(json.dumps(_builder().summarize(built)))
    assert summary["rows"] == 1140 and sum(summary["terminal_status"].values()) == 1140


def test_all_13_ui_controls_still_reach_a_canonical_requirement_and_a_structured_capability_field():
    matrix = pr.location_category_matrix()
    assert [r["chip"] for r in matrix] == list(pr.LOCATION_TAXONOMY) and len(matrix) == 13
    assert all(r["changes_effective_requirements"] and r["disposition"] == "CANONICAL_AND_CONSUMED" for r in matrix)
    assert {r["chip"] for r in matrix if r["suitability_class"] == "HARD"} == {"marine_open_water", "desert_arid", "snow_arctic"}


def test_every_location_chip_flows_from_effective_requirement_to_served_status_reason_and_evidence():
    """UI chip -> canonical category -> effective requirement token -> capability lookup -> hard/soft classification -> served
    status / reason / soft signal / evidence (the persistence + fingerprint half is pinned in test_location_and_content_gate_wiring)."""
    for chip, category in pr.CHIP_TO_CATEGORY.items():
        reqs = _reqs(category)
        assert reqs.environments | reqs.required_capabilities, chip
        census_category = next((c for c, tok in LOCATION_CENSUS_CATEGORIES.items() if tok in reqs.environments | reqs.required_capabilities), None)
        if census_category is None:                    # beach/coast, marine/open water, studio: structured marine/studio fields (unchanged)
            assert chip in ("beach_coast", "marine_open_water", "studio_stage"), chip
            continue
        token = LOCATION_CENSUS_CATEGORIES[census_category]
        hard = token in reqs.required_capabilities
        supported = _codes(census_category, SUPPORTED)[0]
        entry = pf.classify_entry_fit({"anchor_jurisdiction": supported}, reqs)
        assert entry["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES
        assert token in {e["token"] for e in entry["production_fit_capability_evidence"]}
        assert any(e["hard_requirement"] is hard for e in entry["production_fit_capability_evidence"] if e["token"] == token)
        if not hard:
            assert f"{supported}:{token}" in entry["production_fit_soft_signals"]["matched"]
        unresolved = _codes(census_category, UNRESOLVED_NEUTRAL)[0]
        got = pf.classify_entry_fit({"anchor_jurisdiction": unresolved}, reqs)
        if hard:
            assert got["production_fit_status"] == pf.FIT_UNKNOWN and any(r.endswith("_NOT_ASSESSABLE") for r in got["production_fit_reasons"])
        else:
            assert got["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES and f"{unresolved}:{token}" in got["production_fit_soft_signals"]["unassessed"]
        denied = _codes(census_category, NOT_SUPPORTED)
        if denied:
            got = pf.classify_entry_fit({"anchor_jurisdiction": denied[0]}, reqs)
            assert (got["production_fit_status"] == pf.FIT_WEAK) is hard
            assert not hard or got["production_fit_status"] == pf.FIT_WEAK


def test_the_census_changes_no_economics_module_and_no_fingerprint_hashed_source():
    from app.services.canonical_runtime_attribution import _SEMANTIC_PRICING_MODULES

    touched = {"app.calculators.jurisdiction_comparison", "app.calculators.production_requirements", "app.services.production_fit",
               "app.data.jurisdiction_location_capability", "app.services.canonical_production_view"}
    assert not touched & set(_SEMANTIC_PRICING_MODULES)                    # generations / candidate identities / economics keep their fingerprint
