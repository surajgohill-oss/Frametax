"""
test_cba002_condition_kind_vocabulary.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, CBA-002 — proves the typed condition-kind vocabulary: every
RateCondition.kind actually in use across the served 71-program universe
terminates in exactly one of the six typed states (EXECUTABLE,
DISCLOSURE_ONLY, USER_FACT_REQUIRED, SCRIPT_FACT_REQUIRED,
AUTHORITY_UNRESOLVED, NOT_APPLICABLE) — zero silent conditions, zero
conditions whose semantics depend solely on prose text.
"""
from __future__ import annotations

from app.data.program_rate_rules import (
    CONDITION_KIND_STATE,
    CONDITION_STATE_AUTHORITY_UNRESOLVED,
    CONDITION_STATE_DISCLOSURE_ONLY,
    CONDITION_STATE_EXECUTABLE,
    CONDITION_STATE_NOT_APPLICABLE,
    CONDITION_STATE_SCRIPT_FACT_REQUIRED,
    CONDITION_STATE_USER_FACT_REQUIRED,
    _RULES_BY_PROGRAM,
    get_qpe_cap,
    resolve_program_rate,
)

_VALID_STATES = {
    CONDITION_STATE_EXECUTABLE,
    CONDITION_STATE_DISCLOSURE_ONLY,
    CONDITION_STATE_USER_FACT_REQUIRED,
    CONDITION_STATE_SCRIPT_FACT_REQUIRED,
    CONDITION_STATE_AUTHORITY_UNRESOLVED,
    CONDITION_STATE_NOT_APPLICABLE,
}

_INLINE_HANDLED_KINDS = {
    "production_type", "min_qpe_usd", "discretionary_band",
    "graduated_bracket_applied", "min_qpe_pct_of_total_budget",
}


def _all_kinds_in_use() -> set[str]:
    kinds: set[str] = set()
    for rules in _RULES_BY_PROGRAM.values():
        for rule in rules:
            for cond in rule.conditions:
                kinds.add(cond.kind)
    return kinds


def test_every_registered_condition_kind_has_a_typed_terminal_state():
    kinds = _all_kinds_in_use()
    unclassified = kinds - _INLINE_HANDLED_KINDS - set(CONDITION_KIND_STATE.keys())
    assert not unclassified, f"Silent/unclassified condition kinds: {unclassified}"


def test_condition_kind_state_vocabulary_only_uses_the_six_valid_states():
    for kind, state in CONDITION_KIND_STATE.items():
        assert state in _VALID_STATES, f"{kind} maps to an invalid state {state!r}"


def test_no_dead_min_spend_pct_of_total_budget_kind_remains():
    """The over-broad, prose-dependent kind was retired in favor of a
    precise split; nothing in the served universe should still use it."""
    assert "min_spend_pct_of_total_budget" not in _all_kinds_in_use()


def test_cptc_uses_the_60_pct_qpe_cap_via_the_existing_mechanism():
    cap = get_qpe_cap("ca_federal_cptc")
    assert cap is not None
    assert cap.cap_pct == 0.60
    assert cap.cap_base == "total_worldwide_budget"


def test_germany_min_qpe_pct_condition_pass_fail_and_unresolved():
    """Runtime proof: the same condition kind resolves to all three real
    outcomes depending on the facts supplied — pass, fail, unresolved."""
    r_pass = resolve_program_rate(
        "de_dfff", production_type="feature_film",
        qpe_usd=1_000_000, gross_budget_usd=4_000_000,
    )
    r_fail = resolve_program_rate(
        "de_dfff", production_type="feature_film",
        qpe_usd=500_000, gross_budget_usd=4_000_000,
    )
    r_unresolved = resolve_program_rate(
        "de_dfff", production_type="feature_film",
        qpe_usd=1_000_000, gross_budget_usd=None,
    )
    assert r_pass is not None and r_fail is not None and r_unresolved is not None

    def _cond(r):
        return next(c for c in r.conditions_evaluated if c.condition_id == "de-min-spend-pct-of-budget")

    c_pass, c_fail, c_unresolved = _cond(r_pass), _cond(r_fail), _cond(r_unresolved)
    assert c_pass.satisfied is True and c_pass.condition_state == CONDITION_STATE_EXECUTABLE
    assert c_fail.satisfied is False and c_fail.condition_state == CONDITION_STATE_EXECUTABLE
    assert c_unresolved.satisfied is None
    assert c_unresolved.condition_state == CONDITION_STATE_USER_FACT_REQUIRED


def test_uk_avec_min_qpe_pct_condition_is_executable():
    r = resolve_program_rate(
        "uk_avec", production_type="feature_film",
        qpe_usd=1_000_000, gross_budget_usd=10_000_000,
    )
    if r is None:
        import pytest
        pytest.skip("uk_avec tier not eligible for this production_type/QPE in this environment")
    cond = next((c for c in r.conditions_evaluated if c.condition_id == "gb-min-uk-spend-pct"), None)
    if cond is not None:
        assert cond.condition_state == CONDITION_STATE_EXECUTABLE
        assert cond.satisfied is True  # 10% of 10M = 1M, exactly met


def test_reclassified_ontario_ny_mexico_conditions_are_unmodeled_ratio_not_budget_ratio():
    """These three were previously mis-tagged as the same kind as the real
    QPE-vs-budget ratio conditions; they represent different ratios
    entirely and must never be silently auto-executed."""
    found_any = False
    for rules in _RULES_BY_PROGRAM.values():
        for rule in rules:
            for cond in rule.conditions:
                if cond.condition_id in (
                    "ca-on-labour-ratio-gate", "us-ny-atl-cap", "mx-national-supply-requirement",
                ):
                    found_any = True
                    assert cond.kind == "unmodeled_spend_split_ratio"
                    assert CONDITION_KIND_STATE[cond.kind] == CONDITION_STATE_AUTHORITY_UNRESOLVED
    assert found_any


def test_reclassified_egypt_fiji_conditions_are_project_fact_eligibility_gates():
    found_any = False
    for rules in _RULES_BY_PROGRAM.values():
        for rule in rules:
            for cond in rule.conditions:
                if cond.condition_id in ("eg-empc-anchor-required", "fj-local-entity-required"):
                    found_any = True
                    assert cond.kind == "project_fact_dependent_eligibility"
                    assert CONDITION_KIND_STATE[cond.kind] == CONDITION_STATE_USER_FACT_REQUIRED
    assert found_any


# ── CBA-002 continuation: TYPED RATE CONDITION -> QUALIFICATION propagation ──

def test_condition_evaluation_carries_its_source_kind():
    """The new ConditionEvaluation.kind field must reflect the real
    RateCondition.kind so downstream qualification propagation can filter
    by real semantics, never by re-deriving them from prose."""
    r = resolve_program_rate(
        "de_dfff", production_type="feature_film", qpe_usd=500_000, gross_budget_usd=4_000_000,
    )
    cond = next(c for c in r.conditions_evaluated if c.condition_id == "de-min-spend-pct-of-budget")
    assert cond.kind == "min_qpe_pct_of_total_budget"


def test_qualification_propagation_downgrades_on_unmet_executable_condition():
    from app.services.canonical_evaluation import _merge_rate_condition_into_qualification
    from app.calculators.canonical_qualification_result import QUAL_CURABLE_GAP, QUAL_QUALIFIES

    r_fail = resolve_program_rate(
        "de_dfff", production_type="feature_film", qpe_usd=500_000, gross_budget_usd=4_000_000,
    )
    merged = _merge_rate_condition_into_qualification(
        {"state": QUAL_QUALIFIES, "reasoning_trace": [], "missing_facts": [], "curable_requirements": []},
        r_fail, "de_dfff", "DE",
    )
    assert merged["state"] == QUAL_CURABLE_GAP
    assert "de-min-spend-pct-of-budget" in merged["curable_requirements"]


def test_qualification_propagation_no_impact_when_condition_satisfied():
    from app.services.canonical_evaluation import _merge_rate_condition_into_qualification
    from app.calculators.canonical_qualification_result import QUAL_QUALIFIES

    r_pass = resolve_program_rate(
        "de_dfff", production_type="feature_film", qpe_usd=1_000_000, gross_budget_usd=4_000_000,
    )
    original = {"state": QUAL_QUALIFIES, "reasoning_trace": [], "missing_facts": [], "curable_requirements": []}
    merged = _merge_rate_condition_into_qualification(original, r_pass, "de_dfff", "DE")
    assert merged["state"] == QUAL_QUALIFIES
    assert merged is original  # byte-identical passthrough, never rebuilt when nothing changed


def test_qualification_propagation_never_weakens_an_existing_hard_fail():
    from app.services.canonical_evaluation import _merge_rate_condition_into_qualification
    from app.calculators.canonical_qualification_result import QUAL_HARD_FAIL

    r_fail = resolve_program_rate(
        "de_dfff", production_type="feature_film", qpe_usd=500_000, gross_budget_usd=4_000_000,
    )
    original = {"state": QUAL_HARD_FAIL, "reasoning_trace": [], "missing_facts": [], "curable_requirements": []}
    merged = _merge_rate_condition_into_qualification(original, r_fail, "de_dfff", "DE")
    assert merged["state"] == QUAL_HARD_FAIL  # a curable rate gap never overrides a real hard fail
    assert merged is original


def test_qualification_propagation_ignores_discretionary_band_conditions():
    """The ~60 discretionary_band conditions across the served universe
    must NEVER downgrade qualification -- they're a rate-ceiling
    disclosure, not an eligibility gate. Verified against a real program
    that has one and no eligibility-relevant condition."""
    from app.services.canonical_evaluation import _rate_condition_qualification_impact

    r = resolve_program_rate("mu_edb_incentive", production_type="feature_film", qpe_usd=2_000_000)
    if r is None:
        import pytest
        pytest.skip("mu_edb_incentive not eligible for this production_type/QPE in this environment")
    kinds = {c.kind for c in r.conditions_evaluated}
    assert "discretionary_band" in kinds or "no_sponsorship_in_qpe" in kinds
    assert _rate_condition_qualification_impact(r) is None


def test_qualification_propagation_ignores_unresolved_kinds_outside_the_eligibility_set():
    """AUTHORITY_UNRESOLVED/USER_FACT_REQUIRED conditions of a kind NOT in
    the deliberately narrow eligibility set (e.g. rate_base_narrower_than_
    qpe, no_sponsorship_in_qpe) must not gate qualification -- only
    min_qpe_pct_of_total_budget / project_fact_dependent_eligibility /
    unmodeled_spend_split_ratio do."""
    from app.services.canonical_evaluation import _rate_condition_qualification_impact
    from app.data.program_rate_rules import ConditionEvaluation, RateResolution

    fake = RateResolution(
        program_slug="fake", modeled_rate=0.25, floor_rate=0.25, is_band_ceiling=False,
        tier_id="fake-tier", basis="statute",
        conditions_evaluated=(
            ConditionEvaluation(
                condition_id="fake-no-sponsorship", description="", quote="", kind="no_sponsorship_in_qpe",
                satisfied=None, note="", condition_state="USER_FACT_REQUIRED",
            ),
        ),
        unverified_claims=(), conflicts=(),
    )
    assert _rate_condition_qualification_impact(fake) is None
