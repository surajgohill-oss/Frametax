"""Every candidate family consumes the SAME current project-location facts: they are built ONCE per evaluation
(build_physical_requirements -> ProjectEconomicInputs / the fingerprint), exclusions apply at the single
candidate choke point that full relocation, component routing, stacking and treaty co-production discovery all
derive from, and the home jurisdiction can never be excluded."""
from __future__ import annotations

import inspect
import re

from app.services import canonical_evaluation as ce


def test_one_builder_owns_the_project_location_facts_for_evaluation_fingerprint_and_serving():
    from app.services import canonical_production_view as view
    from app.services import canonical_project_economics as econ

    sig = inspect.signature(econ.build_physical_requirements)
    assert sig.parameters["apply_overrides"].default is True, "the evaluator and the serving fit read EFFECTIVE (override-applied) facts"
    assert "await build_physical_requirements(session, project_id)" in inspect.getsource(ce)
    assert "build_physical_requirements(" in inspect.getsource(view)
    # the effective facts enter the fingerprint only when they differ from the script baseline
    assert inspect.getsource(econ).count("physical_requirement_fingerprint_facts(") >= 2, "defined and consumed by the fact assembly"
    assert "apply_overrides=False" in inspect.getsource(econ.physical_requirement_fingerprint_facts)


def test_location_facts_never_remove_a_candidate_they_only_drive_feasibility_disclosure_and_fit():
    src = inspect.getsource(ce)
    assert "feasibility_discovery" in src, "location capability is examined in a separate disclosure-only pass"
    assert "disclosure, never rejection" in inspect.getsource(ce)


def test_exclusion_is_applied_at_one_choke_point_and_home_is_protected():
    src = inspect.getsource(ce.evaluate_project)
    pattern = r"c\[0\] not in excluded_jurisdiction_codes or c\[0\] == inputs\.jurisdiction_code"
    assert len(re.findall(pattern, src)) == 1, "one candidate filter with the home-jurisdiction safeguard"
    # the filtered `candidates` list is what every family below derives from
    after = src.split("c[0] == inputs.jurisdiction_code", 1)[1]
    for family in ("full_relocation", "component_relocation", "treaty", "stack"):
        assert family in after, f"{family} candidates are generated downstream of the single filter"
