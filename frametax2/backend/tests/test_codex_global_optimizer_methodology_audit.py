"""Independent, non-mutating probes retained with the global optimizer audit.

These tests pin observed methodology behavior.  They do not repair or bless it.
"""
from __future__ import annotations

import inspect

from app.calculators.canonical_stack_bridge import StackCandidate, price_program_pair_stack
from app.calculators.treaty_engine import all_bilateral_treaties
from app.services import canonical_evaluation as evaluator


def test_independent_ontario_stack_oracle() -> None:
    oftcc = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    cptc = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(oftcc, cptc)
    assert result is not None
    # Independent literal oracle: 200,000 + (1,000,000 - 200,000) * 25%.
    assert result.adjusted_incentive_usd == 400_000.0
    assert result.stacking_reduction_usd == 50_000.0


def test_registered_treaty_degree_exceeds_served_home_partner_cap() -> None:
    degree: dict[str, int] = {}
    for treaty in all_bilateral_treaties():
        for party in (treaty.jurisdiction_a, treaty.jurisdiction_b):
            if party is None:
                continue
            degree[party] = degree.get(party, 0) + 1
    assert max(degree.values()) > 5
    source = inspect.getsource(evaluator.evaluate_project)
    assert "MAX_TREATY_PARTNERS = 5" in source
    assert "[:MAX_TREATY_PARTNERS]" in source


def test_coproduction_facts_are_project_global_not_pair_scoped() -> None:
    source = inspect.getsource(evaluator._coproduction_facts)
    assert "coproduction_majority_pct" in source
    assert "coproduction_minority_pct" in source
    assert "coproduction_cultural_test_passed" in source
    assert "treaty_slug" not in source
    assert "partner_code" not in source


def test_unverified_conditional_stack_is_still_summed() -> None:
    source = inspect.getsource(evaluator._build_conditional_bilateral_scenario)
    assert "if stack_result is None:" in source
    tail = source.split("if stack_result is None:", 1)[1]
    assert "sum(c.selected_incentive_usd for c in group)" in tail
    assert '"stacking_verified": False' in tail


def test_component_generator_selects_only_one_best_program_per_side() -> None:
    source = inspect.getsource(evaluator.evaluate_project)
    assert "home_best = max(home_candidates" in source
    assert "home_program_slug = home_best.program_slug" in source
    assert "target_best_by_code[code] = max(cands" in source


def test_no_executable_combined_structure_type_is_generated() -> None:
    source = inspect.getsource(evaluator.evaluate_project)
    emitted = {
        "single_country",
        "full_relocation",
        "multi_program",
        "component_relocation",
        "treaty_coproduction",
    }
    for structure_type in emitted:
        assert f'"structure_type": "{structure_type}"' in source or structure_type in source
    for absent in ("copro_component", "hybrid_stack", "combined_copro_hybrid_stack"):
        assert f'"structure_type": "{absent}"' not in source
