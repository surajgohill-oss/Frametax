"""
test_cache_fingerprint_expansion.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, Part 26/CBA-008 — Codex's audit found the served-evaluation
cache fingerprint excluded personnel, screenplay, co-production,
contingency, and registry/table version inputs, meaning an existing
current-ENGINE_VERSION row could keep serving a stale result after any of
these materially qualification-affecting facts changed. Verifies
_compute_fingerprint() is sensitive to each.
"""
from __future__ import annotations

from app.calculators.qualification_derivation import BudgetLine
from app.services.canonical_evaluation import _compute_fingerprint
from app.services.canonical_project_economics import ProjectEconomicInputs


def _inputs(**overrides) -> ProjectEconomicInputs:
    base = dict(
        project_id="test-project",
        project_name="Test",
        jurisdiction_code="MU",
        production_type="feature_film",
        gross_budget_usd=1_000_000.0,
        leaf_account_sum_usd=1_000_000.0,
        budget_lines=[BudgetLine("1000", "Cast", 500_000.0, spend_category="atl_cast")],
        spend_category_by_code={"1000": "atl_cast"},
        accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(),
    )
    base.update(overrides)
    return ProjectEconomicInputs(**base)


def test_contingency_expected_utilization_pct_changes_fingerprint():
    a = _compute_fingerprint(_inputs(contingency_expected_utilization_pct=None))
    b = _compute_fingerprint(_inputs(contingency_expected_utilization_pct=50.0))
    c = _compute_fingerprint(_inputs(contingency_expected_utilization_pct=100.0))
    assert len({a, b, c}) == 3


def test_role_known_codes_changes_fingerprint():
    a = _compute_fingerprint(_inputs(), role_known_codes={})
    b = _compute_fingerprint(_inputs(), role_known_codes={"director": ("GB",)})
    c = _compute_fingerprint(_inputs(), role_known_codes={"director": ("GB", "US")})
    assert len({a, b, c}) == 3


def test_script_facts_changes_fingerprint():
    a = _compute_fingerprint(_inputs(), script_facts={})
    b = _compute_fingerprint(_inputs(), script_facts={"location": ("Mauritius",)})
    c = _compute_fingerprint(_inputs(), script_facts={"location": ("Mauritius", "France")})
    assert len({a, b, c}) == 3


def test_coproduction_facts_changes_fingerprint():
    a = _compute_fingerprint(_inputs(), coproduction_facts=(None, None, None))
    b = _compute_fingerprint(_inputs(), coproduction_facts=(60.0, 40.0, None))
    c = _compute_fingerprint(_inputs(), coproduction_facts=(60.0, 40.0, True))
    assert len({a, b, c}) == 3


def test_registry_versions_are_present_in_the_payload():
    """Not directly assertable via the hash alone (they're constants within
    one test run), but confirms the fingerprint function actually reads
    the real version constants rather than silently omitting them --
    import failure or a missing attribute would raise here."""
    from app.calculators.qualification_model import QUALIFICATION_MODEL_VERSION
    from app.data.cultural_point_tables import CULTURAL_POINT_TABLES_VERSION
    from app.data.national_cultural_status import NATIONAL_CULTURAL_STATUS_VERSION
    from app.data.program_rate_rules import PROGRAM_RATE_RULES_VERSION

    assert _compute_fingerprint(_inputs())
    assert QUALIFICATION_MODEL_VERSION and CULTURAL_POINT_TABLES_VERSION
    assert NATIONAL_CULTURAL_STATUS_VERSION and PROGRAM_RATE_RULES_VERSION


def test_fingerprint_actually_changes_when_a_registry_version_bumps():
    """OH-001/OH-004 fix (CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT): the previous
    test above only proved the constants are truthy and importable -- it
    never proved the fingerprint is actually SENSITIVE to them changing,
    which is the entire point of including them. Patches each registry
    version constant one at a time (module-qualified, so
    canonical_evaluation's own `from X import Y` re-import inside
    `_compute_fingerprint` picks up the patch) and asserts the resulting
    fingerprint differs from the baseline. Covers every version constant
    OH-001 added this pass, not only the four pre-existing ones."""
    import app.calculators.canonical_role_qualification_bridge as role_bridge_mod
    import app.calculators.qualification_model as qual_model_mod
    import app.calculators.treaty_engine as treaty_mod
    import app.data.authority_coverage_registry as coverage_mod
    import app.data.cultural_point_tables as cultural_mod
    import app.data.executable_jurisdiction_registry as exec_registry_mod
    import app.data.national_cultural_status as national_status_mod
    import app.data.program_authority_provenance as provenance_mod
    import app.data.program_rate_rules as rate_rules_mod
    import app.data.program_requirements as requirements_mod
    import app.data.structuring_opportunity_patterns as structuring_mod
    import app.optimization.stacking_rules as stacking_mod

    baseline = _compute_fingerprint(_inputs())
    targets = [
        (qual_model_mod, "QUALIFICATION_MODEL_VERSION"),
        (cultural_mod, "CULTURAL_POINT_TABLES_VERSION"),
        (national_status_mod, "NATIONAL_CULTURAL_STATUS_VERSION"),
        (rate_rules_mod, "PROGRAM_RATE_RULES_VERSION"),
        (coverage_mod, "AUTHORITY_COVERAGE_REGISTRY_VERSION"),
        (provenance_mod, "PROGRAM_AUTHORITY_PROVENANCE_VERSION"),
        (requirements_mod, "PROGRAM_REQUIREMENTS_VERSION"),
        (stacking_mod, "STACKING_RULES_VERSION"),
        (treaty_mod, "TREATY_ENGINE_VERSION"),
        (structuring_mod, "STRUCTURING_OPPORTUNITY_PATTERNS_VERSION"),
        (exec_registry_mod, "EXECUTABLE_JURISDICTION_REGISTRY_VERSION"),
        (role_bridge_mod, "CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION"),
    ]
    for module, attr in targets:
        original = getattr(module, attr)
        try:
            setattr(module, attr, f"{original}-TEST-PATCHED")
            patched = _compute_fingerprint(_inputs())
            assert patched != baseline, (
                f"fingerprint did NOT change when {module.__name__}.{attr} changed "
                "-- this version is not actually wired into the dependency manifest"
            )
        finally:
            setattr(module, attr, original)


def test_identical_inputs_produce_identical_fingerprint():
    """Determinism — a real precondition for any cache to be trustworthy."""
    kwargs = dict(
        role_known_codes={"director": ("GB",)},
        script_facts={"location": ("Mauritius",)},
        coproduction_facts=(60.0, 40.0, True),
    )
    a = _compute_fingerprint(_inputs(contingency_expected_utilization_pct=40.0), **kwargs)
    b = _compute_fingerprint(_inputs(contingency_expected_utilization_pct=40.0), **kwargs)
    assert a == b
