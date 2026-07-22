"""
test_global_discovery.py

Phase 6 canonical discovery: the optimizer examines EVERY implemented
jurisdiction in the database (data-driven, no hard-coded country list),
rejects the non-executable with reasons, accepts only those it can price,
and exposes discovery metrics. Structure generation flows from the accepted
set; ranking still uses normalized NPC.
"""
from __future__ import annotations

import re

import pytest

from app.calculators.production_discovery import discover_executable_jurisdictions
from app.data import global_inventory as gi
from app.demo.little_utopia_state import build_allocated_structures, get_state, reset_fact_answers


@pytest.fixture(autouse=True)
def _reset():
    reset_fact_answers()
    yield
    reset_fact_answers()


def _discovery():
    from app.calculators.production_requirements import derive_production_requirements
    reqs = derive_production_requirements(get_state().physical_requirements)
    return discover_executable_jurisdictions(
        requirements=reqs, production_type="feature_film", qpe_usd=4_355_327, home_code="MU",
    )


class TestEveryJurisdictionExamined:
    def test_examines_every_implemented_jurisdiction(self):
        d = _discovery()
        # the examined universe equals the distinct jurisdictions in the full
        # program inventory (unioned with structured profiles) — nothing is
        # hand-picked, nothing implemented is skipped.
        inventory_codes = {p.jurisdiction_code for p in gi.ALL_PROGRAMS}
        examined_codes = {e.jurisdiction_code for e in d.examinations}
        assert inventory_codes <= examined_codes
        assert d.metrics["jurisdictions_examined"] == len(d.examinations)
        assert d.metrics["jurisdictions_examined"] >= 200  # ~211 today, not a handful

    def test_every_examination_has_a_reason(self):
        for e in _discovery().examinations:
            assert e.reason and len(e.reason) > 10

    def test_accepted_and_rejected_partition_the_universe(self):
        d = _discovery()
        m = d.metrics
        assert m["incentive_ready_count"] + m["capability_only_count"] + m["rejected_count"] == m["jurisdictions_examined"]


class TestDataDrivenNoHardCoding:
    def test_accepted_set_derived_from_rules_not_a_list(self):
        # every accepted jurisdiction actually has classified doctrine + rate
        # rules AND resolves for the production — proven, not asserted by name.
        from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
        from app.data.program_spend_rules import get_program_doctrine
        for code, slug in _discovery().accepted:
            assert get_program_doctrine(slug) is not None
            assert len(get_rate_rules(slug)) > 0
            assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=4_355_327) is not None

    def test_rejections_are_knowledge_gated_never_guessed(self):
        for e in _discovery().examinations:
            if not e.accepted:
                assert (not e.has_doctrine) or (not e.has_rate_rules) or (not e.resolves_for_production)

    def test_discovery_source_has_no_hardcoded_country_list(self):
        # the discovery engine must iterate registries, not enumerate ISO codes.
        import app.calculators.production_discovery as mod
        src = open(mod.__file__).read()
        # no bracketed list of >3 two-letter country codes
        assert not re.search(r"\[\s*(['\"][A-Z]{2}['\"]\s*,\s*){3,}", src)


class TestServedDiscoveryMetrics:
    def test_allocated_structures_exposes_discovery(self):
        al = build_allocated_structures(get_state())
        d = al["discovery"]
        assert d["metrics"]["jurisdictions_examined"] >= 200
        assert d["metrics"]["accepted_count"] == 4
        assert set(d["metrics"]["accepted_jurisdictions"]) == {"MU", "MT", "IE", "GR"}
        assert d["generated_structures"] >= d["optimized_structures"] >= d["final_ranked_structures"]
        assert len(d["examinations"]) == d["metrics"]["jurisdictions_examined"]

    def test_no_hardcoded_scenario_count(self):
        # structure count must equal 1 baseline + N alternatives (relocation)
        # + N components — a function of the accepted set, not a constant.
        al = build_allocated_structures(get_state())
        n_alt = al["discovery"]["metrics"]["accepted_count"] - 1  # minus home MU
        assert al["discovery"]["generated_structures"] == 1 + n_alt + n_alt

    def test_ranking_uses_normalized_npc_ascending(self):
        al = build_allocated_structures(get_state())
        ranked = [r for r in al["ranking"] if r["rank"] is not None]
        npcs = [r["npc_with_adjustments_usd"] for r in ranked]
        assert npcs == sorted(npcs)
        assert ranked[0]["structure_id"] == "ALLOC-BASELINE-MU"


class TestLocationOverrideDrivesDiscovery:
    """Regression guard: a producer-confirmed location-category override
    must actually reach discovery's required_capabilities — it used to be
    silently defeated because marine_filming/open_water_filming were ALSO
    sourced unconditionally from the raw (non-overridable) script signal,
    and environments/infrastructure only ever grow via set.add(), so the
    raw signal always won regardless of what the override said."""

    def test_default_requires_marine_and_open_water(self):
        assert set(_discovery().metrics["required_capabilities"]) == {
            "marine_filming", "open_water_filming",
        }

    def test_confirmed_no_marine_clears_both_capabilities_and_reclassifies(self):
        from app.demo.little_utopia_state import apply_location_overrides
        before = _discovery().metrics
        apply_location_overrides({"marine_open_water": False})
        try:
            after = _discovery().metrics
            assert after["required_capabilities"] == []
            # a real downstream effect, not just an empty list: at least one
            # jurisdiction that needed marine capability to be production-
            # capable is now reclassified (the whole point of discovery
            # depending on requirements at all).
            assert after["production_capable_count"] > before["production_capable_count"]
            assert after["rejected_count"] < before["rejected_count"]
            # incentive-readiness (statutory doctrine/rate knowledge) is a
            # completely separate axis and must NOT move — capability and
            # pricing knowledge are deliberately independent.
            assert after["incentive_ready_count"] == before["incentive_ready_count"]
        finally:
            apply_location_overrides({"marine_open_water": None})

    def test_clearing_the_override_restores_the_canonical_baseline(self):
        from app.demo.little_utopia_state import apply_location_overrides
        baseline = _discovery().metrics
        apply_location_overrides({"marine_open_water": False})
        apply_location_overrides({"marine_open_water": None})
        restored = _discovery().metrics
        assert restored == baseline


class TestRecommendationTitles:
    def test_structure_titles_are_country_names_not_relocate(self):
        # the frozen presentation formatter titles cards by jurisdiction name;
        # movement lives in the explanation, never the title. Guard the shared
        # formatter source (JSX) against reintroducing "Relocate".
        import os
        fmt = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src", "lib", "format.jsx",
        )
        if os.path.exists(fmt):
            code = re.sub(r"//.*", "", open(fmt).read())
            assert "Relocate to" not in code and "Relocate " not in code
