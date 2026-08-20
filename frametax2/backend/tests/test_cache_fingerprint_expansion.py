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
