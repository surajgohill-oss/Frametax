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
        # Every accepted jurisdiction actually has an EXECUTABLE doctrine +
        # rate rules AND resolves for the production — proven, not asserted
        # by name. Doctrine is now RESOLVED (explicit classification,
        # evidence-constrained override, or the module's canonical
        # default-inclusion rule) rather than required to be pre-classified,
        # so the assertion is that a doctrine resolves — not that someone
        # hand-classified it. A missing statutory RATE still blocks, because
        # no rule can supply a number that does not exist.
        from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
        from app.data.program_spend_rules import resolve_program_doctrine
        for code, slug in _discovery().accepted:
            assert resolve_program_doctrine(slug) is not None
            assert len(get_rate_rules(slug)) > 0
            assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=4_355_327) is not None

    def test_rejections_are_gated_never_guessed(self):
        """A rejection must always be explained by a real gate: either the
        production cannot physically be made there (capability), or a
        statutory input is genuinely absent. Since doctrine now always
        resolves, capability is the dominant rejection reason — but every
        rejection must still name one of the two."""
        for e in _discovery().examinations:
            if not e.accepted:
                knowledge_gap = (
                    (not e.has_doctrine)
                    or (not e.has_rate_rules)
                    or (not e.resolves_for_production)
                )
                capability_gap = not e.production_capable
                assert knowledge_gap or capability_gap, (
                    f"{e.jurisdiction_code} was rejected without naming either a "
                    "capability gap or a missing statutory input."
                )

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
        # Invariant-based rather than a snapshot: the accepted set must be
        # EXACTLY the examined jurisdictions that are production-capable AND
        # whose statutory rate resolves — derived from the same examination
        # records the implementation produced, so it never needs a manual
        # edit as doctrine resolution reaches more jurisdictions, while a
        # real wiring defect (accepting something that failed a gate) still
        # fails.
        expected_accepted = {
            e["jurisdiction_code"] for e in d["examinations"]
            if e["production_capable"] and e["resolves_for_production"]
        }
        assert set(d["metrics"]["accepted_jurisdictions"]) == expected_accepted
        assert d["metrics"]["accepted_count"] == len(expected_accepted)
        # The statute-read jurisdictions this suite protects, plus the
        # baseline, must always be among them. Global Data Application: IE
        # (ie_section_481) was reclassified UNPRICEABLE_AUTHORITY_INSUFFICIENT
        # by the completed primary-authority corpus and is therefore correctly
        # no longer accepted — asserted explicitly below so the drop is a
        # stated canonical consequence, never a silent regression.
        assert {"MU", "MT", "GR"} <= set(d["metrics"]["accepted_jurisdictions"])
        from app.data.authority_coverage_registry import coverage_state
        assert coverage_state("ie_section_481") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
        assert "IE" not in set(d["metrics"]["accepted_jurisdictions"])
        assert d["generated_structures"] >= d["optimized_structures"] >= d["final_ranked_structures"]
        assert len(d["examinations"]) == d["metrics"]["jurisdictions_examined"]

    def test_no_hardcoded_scenario_count(self):
        # structure count must equal 1 baseline + N structure partners
        # (relocation) + N structure partners (components) — a function of
        # the accepted (incentive-ready) set UNION the capability-only set,
        # not a constant. Capability-only partners are production-capable
        # but incentive-pending — they still enter structure generation and
        # come back honestly blocked (never priced at a guess), so they
        # count as generated structures same as any other.
        al = build_allocated_structures(get_state())
        m = al["discovery"]["metrics"]
        n_partners = (m["accepted_count"] - 1) + m["capability_only_count"]  # minus home MU
        assert al["discovery"]["generated_structures"] == 1 + n_partners + n_partners

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
            # Capability and statutory knowledge remain deliberately
            # independent axes — but incentive_ready is their INTERSECTION
            # (production-capable AND priceable), so relaxing a capability
            # requirement can only ever admit more jurisdictions, never
            # fewer. (This assertion used to require exact equality, which
            # held only while the doctrine gate capped incentive_ready at 4
            # regardless of capability; with doctrine now resolving under the
            # canonical rule, the intersection genuinely grows.)
            assert after["incentive_ready_count"] >= before["incentive_ready_count"]
        finally:
            apply_location_overrides({"marine_open_water": None})

    def test_clearing_the_override_restores_the_canonical_baseline(self):
        from app.demo.little_utopia_state import apply_location_overrides
        baseline = _discovery().metrics
        apply_location_overrides({"marine_open_water": False})
        apply_location_overrides({"marine_open_water": None})
        restored = _discovery().metrics
        assert restored == baseline


class TestCapabilityOnlyStructureGeneration:
    """Regression guard: capability-only jurisdictions (production-capable,
    incentive pending) were classified and RETAINED by discovery but never
    reached build_allocated_structures — full-relocation and anchor-
    component generation iterated only the incentive-ready set. Discovery's
    own docstring promises capability-only jurisdictions are 'retained, not
    silently discarded'; that promise must hold all the way to the served
    structures, not just the discovery audit."""

    def test_every_production_capable_partner_gets_a_relocation_and_component_structure(self):
        """The original guard was scoped to capability-only partners. Since
        doctrine now resolves under the canonical rule, that set is normally
        EMPTY (a production-capable jurisdiction with rate rules is
        incentive-ready), which would make the old assertion vacuous. The
        promise it protected is therefore asserted in its stronger, still-
        meaningful form: EVERY production-capable partner — incentive-ready
        or not — must reach structure generation, never be silently dropped."""
        al = build_allocated_structures(get_state())
        home = al["discovery"]["examinations"]
        capable_partners = {
            e["jurisdiction_code"] for e in home
            if e["production_capable"] and e["jurisdiction_code"] != "MU"
        }
        assert capable_partners, "fixture must have production-capable partners"
        ids = {s["structure_id"] for s in al["structures"]}
        for code in capable_partners:
            assert f"ALLOC-RELOC-{code}" in ids, f"{code} is production-capable but has no relocation structure"
            assert f"ALLOC-COMPONENT-POST-{code}" in ids

    def test_structures_without_a_statutory_rate_are_never_priced_at_a_guess(self):
        """Doctrine no longer blocks pricing, but a genuinely absent
        statutory RATE still must: no rule can supply a number that does not
        exist. Any structure that is not fully priced must say exactly why."""
        al = build_allocated_structures(get_state())
        for s in al["structures"]:
            if not s["is_fully_priced"]:
                assert s["blockers"], f"{s['structure_id']} unpriced without a stated blocker"

    def test_incentive_ready_partners_unaffected(self):
        # the pre-existing incentive-ready structures (MT/IE/GR) keep their
        # exact ids and at least one still prices — this fix only ADDS
        # capability-only candidates, never changes the priced set.
        al = build_allocated_structures(get_state())
        ids = {s["structure_id"] for s in al["structures"]}
        for code in ("MT", "IE", "GR"):
            assert f"ALLOC-RELOC-{code}" in ids
        priced = [s for s in al["structures"] if s["is_fully_priced"]]
        assert len(priced) == al["discovery"]["final_ranked_structures"]
        assert len(priced) >= 1


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

    def test_scenarios_and_workspace_both_use_the_canonical_title_formatter(self):
        # regression guard: Scenarios.jsx previously rendered the raw
        # backend structure.label ("Full relocation to GR") as its column
        # header instead of the shared scenarioDisplay() formatter Workspace
        # already used — the exact "recurring naming regression" this
        # class exists to prevent. Both screens must call scenarioDisplay
        # for their card/column title, not structure.label directly.
        import os
        base = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "screens", "production")
        for fname in ("Scenarios.jsx", "Workspace.jsx"):
            path = os.path.join(base, fname)
            if not os.path.exists(path):
                continue
            code = re.sub(r"//.*", "", open(path).read())
            assert "scenarioDisplay(" in code, f"{fname} must use the canonical scenarioDisplay formatter"
            # the raw label must not be used for a visible card/column title
            # (className="nm" / className="wsx-nm" are the title slots)
            assert not re.search(r'className="(nm|wsx-nm)[^"]*">\{s\.label\}', code)


class TestWorkspaceScenariosSynchronization:
    """Backend may generate/rank far more structures than a card rack can
    show at once (every discovery-retained partner now composes two
    candidates). Both Workspace and Scenarios must read the SAME canonical
    array from the SAME API payload (no separate/duplicated fetch, no
    frontend slice that truncates backend generation) and both must honor
    the six-visible-plus-overflow-selector contract, not just one screen."""

    def _frontend_source(self, fname):
        import os
        base = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "screens", "production")
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            return None
        return re.sub(r"//.*", "", open(path).read())

    def test_both_screens_read_the_same_allocated_structures_path(self):
        for fname in ("Scenarios.jsx", "Workspace.jsx"):
            code = self._frontend_source(fname)
            if code is None:
                continue
            assert "structures?.allocated_structures" in code or "structures.allocated_structures" in code

    def test_both_screens_cap_visible_scenarios_at_six_with_overflow(self):
        for fname in ("Scenarios.jsx", "Workspace.jsx"):
            code = self._frontend_source(fname)
            if code is None:
                continue
            assert re.search(r"MAX_VISIBLE\s*=\s*6", code), f"{fname} must define the 6-visible contract"
            assert "overflow" in code.lower()

    def test_neither_screen_slices_before_ranking(self):
        # a `.slice(0, 6)` (or similar) applied directly to the raw backend
        # array BEFORE rank-ordering would truncate backend generation
        # rather than present a manageable subset of it. Both screens must
        # sort/order the full array first, then slice.
        for fname in ("Scenarios.jsx", "Workspace.jsx"):
            code = self._frontend_source(fname)
            if code is None:
                continue
            assert not re.search(r"allocated\.structures\.slice\(", code)


class TestFXPresentationHidden:
    """FX is real (allocation_pricing's FXNormalizationResult, threaded as
    fx_basis/fx_delta_usd) but under default economics controls the delta
    is always $0 — an honest 'no currency stress modeled' answer that reads
    to a producer as a meaningful adjustment when it isn't one. Backend
    keeps computing and serving it (see test_allocation_pricing.py); the
    UI's prominent presentation is intentionally hidden until a real
    currency-exposed-spend adjustment view exists."""

    def _frontend_source(self, fname):
        import os
        base = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "screens", "production")
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            return None
        return re.sub(r"//.*", "", open(path).read())

    def test_scenarios_no_longer_renders_an_fx_row(self):
        code = self._frontend_source("Scenarios.jsx")
        if code is None:
            return
        assert "FX basis" not in code
        assert "fxCell" not in code

    def test_workspace_no_longer_renders_a_prominent_fx_chip(self):
        code = self._frontend_source("Workspace.jsx")
        if code is None:
            return
        assert "wsx-lane-fx" not in code
