"""Location-capability census (2026-10-06): fixed 114 x 10 matrix, owner wiring, hard/soft semantics. Pure tests: no database,
no network, no evaluation. The evidence is recovered repository data; UNKNOWN is a valid terminal state and never a mismatch."""
from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

import pytest

from app.calculators import jurisdiction_comparison as jc
from app.calculators import production_requirements as pr
from app.data.jurisdiction_location_capability import LOCATION_CENSUS_CATEGORIES, NOT_SUPPORTED, RETAINED_SUPPORTED, SUPPORTED, UNKNOWN
from app.services import production_fit as pf

CSV_PATH = Path(__file__).resolve().parents[2] / "docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv"
BUILDER = Path(__file__).resolve().parents[1] / "scripts/build_location_capability_census.py"
REQUIRED_COLUMNS = {
    "jurisdiction_code", "jurisdiction_name", "category", "status", "canonical_capability_token", "evidence_proposition",
    "source_title", "source_url_or_identifier", "publisher", "checked_or_effective_date", "evidence_tier", "runtime_consumed", "notes",
}


def _reqs(*categories):
    return pr.derive_production_requirements({"location_categories": {c: {"effective": True, "evidence": ["x"]} for c in categories}})


def _builder():
    spec = importlib.util.spec_from_file_location("census_builder", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _all_cells():
    return [(c, cat, cell) for c in jc.location_census_jurisdictions() for cat, cell in jc.location_capability_cells(c).items()]


def test_the_fixed_inventory_is_114_jurisdictions_by_10_categories_with_no_duplicate_cell():
    codes = jc.location_census_jurisdictions()
    assert len(codes) == 114 == len(jc.ALL_PROFILES) + 1 and "US" in codes and len(set(codes)) == 114
    assert len(LOCATION_CENSUS_CATEGORIES) == 10
    cells = _all_cells()
    assert len(cells) == 1140 and len({(c, cat) for c, cat, _ in cells}) == 1140


def test_every_cell_is_exactly_one_terminal_status_and_every_non_unknown_cell_carries_evidence():
    for code, cat, cell in _all_cells():
        assert cell.status in (SUPPORTED, NOT_SUPPORTED, UNKNOWN), (code, cat)
        assert cell.token == LOCATION_CENSUS_CATEGORIES[cat]
        if cell.status == UNKNOWN:
            assert not cell.proposition and not cell.source_title, (code, cat)
        else:
            assert cell.proposition and cell.source_title and cell.evidence_tier and cell.record_ref, (code, cat)
            assert cell.publisher or cell.evidence_tier == "TIER_0_RUNTIME_STRUCTURED_FIELD", (code, cat)


def test_every_retained_record_quote_really_is_in_the_cited_repository_record():
    inv = _builder()._inventory_notes()
    for (code, cat), rec in RETAINED_SUPPORTED.items():
        quote = re.search(r'"(.+)"', rec.proposition).group(1).lower()
        pool = [jc.ALL_PROFILES[code].notes] if "PROFILE_RECORD" in rec.evidence_tier else [n for u, n in inv.get(code, []) if rec.source_url == u]
        assert any(quote in (t or "").lower() for t in pool), (code, cat, quote)


def test_the_committed_csv_is_exactly_1140_unique_rows_and_equals_the_owner():
    with CSV_PATH.open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1140 and REQUIRED_COLUMNS <= set(rows[0])
    assert len({(r["jurisdiction_code"], r["category"]) for r in rows}) == 1140
    assert {r["status"] for r in rows} <= {SUPPORTED, NOT_SUPPORTED, UNKNOWN}
    built = _builder().build_rows()
    assert [(r["jurisdiction_code"], r["category"], r["status"]) for r in rows] == [(r["jurisdiction_code"], r["category"], r["status"]) for r in built]
    for r in rows:
        if r["status"] != UNKNOWN:
            assert r["evidence_proposition"] and r["source_title"] and r["source_url_or_identifier"] and r["evidence_tier"]
        assert r["repository_classification"] in ("EXISTS_BUT_DISCONNECTED", "CANONICAL_DATA_MISSING", "CANONICAL_AND_CONSUMED")


def test_unknown_cells_are_neutral_and_never_a_mismatch():
    for code, cat, cell in _all_cells():
        if cell.status != UNKNOWN or code not in jc.ALL_PROFILES and code != "US":
            continue
        verdict, reason = pr.assess_location_capability(cell.token, pr.jurisdiction_capability_profile(code))
        assert verdict == pr.ASSESS_UNKNOWN, (code, cat, verdict, reason)


def test_only_supported_cells_enter_the_provision_set_and_only_not_supported_enter_the_denial_set():
    for code in jc.location_census_jurisdictions():
        cap = pr.jurisdiction_capability_profile(code)
        cells = jc.location_capability_cells(code)
        census_provisions = {t for t in cap.provisions if t in pr.LOCATION_CENSUS_TOKENS}
        assert census_provisions == {c.token for c in cells.values() if c.status == SUPPORTED}, code
        assert cap.location_not_supported == {c.token for c in cells.values() if c.status == NOT_SUPPORTED}, code
        assert not census_provisions & cap.location_not_supported


def test_national_us_is_a_real_profile_and_state_profiles_stay_independent():
    before = {c: pr.jurisdiction_capability_profile(c) for c in jc.ALL_PROFILES if c.startswith("US-")}
    us = pr.jurisdiction_capability_profile("US")
    assert us.has_capability_data and "open_water_filming" in us.provisions and us.marine_suitability in ("strong", "excellent")
    assert "desert_environments" in us.provisions                      # supported in constituent states (US-AZ, US-NM)
    assert pf.classify_jurisdiction_fit("US", _reqs("marine_open_water"))[0] in pf.FIT_CONFIRMED_STATUSES
    for code, cap in before.items():                                    # nothing a national result says rewrites a state
        assert pr.jurisdiction_capability_profile(code) == cap
    nm = pr.jurisdiction_capability_profile("US-NM")
    assert "open_water_filming" not in nm.provisions and pf.classify_jurisdiction_fit("US-NM", _reqs("marine_open_water"))[0] == pf.FIT_WEAK
    assert "desert_environments" not in pr.jurisdiction_capability_profile("US-CA").provisions   # no state inherits the national union
    sup_states = {c for c in jc.ALL_PROFILES if c.startswith("US-") and (c, "desert_arid") in RETAINED_SUPPORTED}
    assert sup_states == {"US-AZ", "US-NM"}


def test_a_supported_desert_jurisdiction_satisfies_the_hard_desert_requirement_and_an_unknown_one_stays_conditional():
    desert = _reqs("desert")
    assert "desert_environments" in desert.required_capabilities          # LLS-style hard requirement
    supported = sorted(c for c in jc.location_census_jurisdictions() if jc.location_capability_cells(c)["desert_arid"].status == SUPPORTED)
    assert {"IL", "QA", "CL", "PE", "KZ", "MN", "US-AZ", "US-NM", "AE-AD", "AE-DXB", "US"} == set(supported)
    for code in supported:
        status, reasons = pf.classify_jurisdiction_fit(code, desert)
        assert status in pf.FIT_CONFIRMED_STATUSES and not reasons, (code, status, reasons)
    for code in ("GR", "AT", "ES", "XX"):                                  # unknown / no profile: Conditional, never unsuitable
        status, reasons = pf.classify_jurisdiction_fit(code, desert)
        assert status == pf.FIT_UNKNOWN and status != pf.FIT_WEAK, (code, status)
    assert pf.classify_jurisdiction_fit("GR", desert)[1] == ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"]


def test_an_affirmatively_unsupported_hard_capability_is_not_suitable(monkeypatch):
    real = pr.jurisdiction_capability_profile
    import dataclasses

    def patched(code):
        cap = real(code)
        return dataclasses.replace(cap, location_not_supported=cap.location_not_supported | {"desert_environments", "snow_environments"}) if code == "GR" else cap

    monkeypatch.setattr(pr, "jurisdiction_capability_profile", patched)
    for category, token in (("desert", "DESERT_ENVIRONMENTS"), ("snow", "SNOW_ENVIRONMENTS")):
        status, reasons = pf.classify_jurisdiction_fit("GR", _reqs(category))
        assert status == pf.FIT_WEAK and reasons[0] == f"{token}_NOT_SUPPORTED"
    # the same denial is only a disclosure when the requirement is soft
    soft = pf.classify_jurisdiction_fit("GR", _reqs("urban"))
    assert soft[0] in pf.FIT_CONFIRMED_STATUSES


def test_soft_capability_absence_or_denial_never_forces_conditional_or_not_suitable():
    soft_cats = [c for c in LOCATION_CENSUS_CATEGORIES if c not in ("desert_arid", "snow_arctic")]
    mapping = {"island_tropical": "island_tropical", "jungle_rainforest": "jungle", "mountains_alpine": "mountain", "urban_major_city": "urban",
               "small_town_suburban": "small_town", "rural_countryside": "rural_countryside", "forest_woodland": "forest", "historic_old_world": "historic_old_world"}
    for code in ("GR", "AT", "IL", "US", "US-NM", "CA-AB", "KZ"):          # AT / US-NM / KZ: landlocked => island_tropical NOT_SUPPORTED
        for cat in soft_cats:
            status, reasons = pf.classify_jurisdiction_fit(code, _reqs(mapping[cat]))
            assert status in pf.FIT_CONFIRMED_STATUSES and not any(r.endswith(("_NOT_ASSESSABLE", "_NOT_SUPPORTED")) for r in reasons), (code, cat, status, reasons)
    at = pf.classify_soft_signals("AT", _reqs("island_tropical"))
    assert at["mismatched"] == ["tropical_environments"]                   # disclosed, never blocking


def test_the_capability_evidence_is_served_with_the_fit_for_active_requirements_only():
    entry = pf.classify_entry_fit({"anchor_jurisdiction": "IL"}, _reqs("desert", "urban", "forest"))
    ev = {e["token"]: e for e in entry["production_fit_capability_evidence"]}
    assert set(ev) == {"desert_environments", "urban_environments"}         # no Israeli forest cell: not listed, not invented
    assert ev["desert_environments"]["hard_requirement"] is True and ev["desert_environments"]["evidence_tier"].startswith("RETAINED_INVENTORY_RECORD")
    assert ev["urban_environments"]["hard_requirement"] is False and ev["desert_environments"]["source_url"].startswith("https://")
    assert pf.classify_entry_fit({"anchor_jurisdiction": "GR"}, _reqs("desert"))["production_fit_capability_evidence"] == []
    assert pf.classify_entry_fit({"anchor_jurisdiction": "IL"}, _reqs())["production_fit_basis"] == "NO_REQUIREMENTS_ON_FILE"


def test_no_requirements_on_file_remains_honestly_unconfirmed_even_with_census_data():
    assert pf.classify_jurisdiction_fit("IL", _reqs()) == (pf.FIT_UNKNOWN, ["NO_REQUIREMENTS_ON_FILE"])


def test_the_census_changes_no_economics_module_and_no_fingerprint_hashed_source():
    from app.services.canonical_runtime_attribution import _SEMANTIC_PRICING_MODULES

    touched = {"app.calculators.jurisdiction_comparison", "app.calculators.production_requirements", "app.services.production_fit",
               "app.data.jurisdiction_location_capability", "app.services.canonical_production_view"}
    assert not touched & set(_SEMANTIC_PRICING_MODULES)                    # generations / candidate identities / economics keep their fingerprint
