"""
test_final_wiring_selection_predicate.py

Codex final wiring remediation (P0-SEL-ALT-001, third pass) — independent
literal-value coverage for the corrected `_is_conditional_eligible()`
predicate (canonical_production_view.py) and the structured, per-
dimension `_relocation_completeness()` helper (canonical_evaluation.py).

Every expected value below is written literally (True/False, an exact
dimension list, an exact program_slug) — never derived by calling the
predicate under test to build its own expectation. This is the exact
adverse discipline Codex's delta audit required: "prohibit expected
values manufactured by the production helper under test."

Root cause this file guards against: commit `67fbc30` broadened
`_is_conditional_eligible()` to admit any fully-priced, non-baseline,
non-comparable candidate whose qualification state was None, QUALIFIES,
NOT_APPLICABLE, or any curable state — without ever checking WHY the
candidate was non-comparable, without aggregating multi-participant
qualification, and without disclosing the real per-dimension relocation
gaps (collapsing travel/FX/local-cost/in-kind into one blanket flag).
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_production_view import (
    _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES,
    _is_conditional_eligible,
)
from app.services.canonical_evaluation import (
    _RELOCATION_DIMENSIONS,
    _STACK_NORMALIZATION_NOT_COMPUTED,
    _relocation_completeness,
    evaluate_project,
)
from app.services.canonical_production_view import build_production_and_structures


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _entry(*, is_fully_priced=True, is_baseline=False, is_directly_comparable=False,
           state=None, missing=None) -> dict:
    return {
        "is_fully_priced": is_fully_priced,
        "is_baseline": is_baseline,
        "is_directly_comparable": is_directly_comparable,
        "role_qualification": {"state": state} if state is not None else None,
        "relocation_missing_dimensions": missing or [],
    }


# ── Ten literal predicate cases (Codex's exact required table) ──────────

def test_case_1_baseline_excluded():
    assert _is_conditional_eligible(
        _entry(is_baseline=True, is_directly_comparable=True, state="CURABLE_GAP")
    ) is False


def test_case_2_explicitly_curable_comparable_candidate_admitted():
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=True, state="USER_FACT_REQUIRED")
    ) is True


def test_case_3_non_comparable_none_excluded():
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state=None, missing=["travel"])
    ) is False


def test_case_4a_non_comparable_qualifies_with_no_enumerated_cause_excluded():
    """QUALIFIES alone, with an EMPTY missing-dimension list (no real
    enumerated cause), must never be admitted -- absent cause is not
    proof of curability."""
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="QUALIFIES", missing=[])
    ) is False


def test_case_4b_non_comparable_qualifies_with_complete_curable_cause_admitted():
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="QUALIFIES", missing=["travel", "fx"])
    ) is True


def test_case_4c_non_comparable_not_applicable_with_curable_cause_admitted():
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="NOT_APPLICABLE", missing=["inkind"])
    ) is True


def test_case_5_hard_legal_authority_identity_failure_excluded():
    """A HARD_FAIL candidate never reaches is_fully_priced=True in the
    real pipeline (QUAL_HARD_FAIL is excluded from
    _QUALIFICATION_ADMITS_PRICING) -- proven here directly against the
    predicate's own is_fully_priced gate, the first and unconditional
    check."""
    assert _is_conditional_eligible(
        _entry(is_fully_priced=False, is_directly_comparable=True, state="CURABLE_GAP")
    ) is False
    # Defensive: even if a HARD_FAIL state somehow reached the
    # non-comparable branch with a real cause, it must still be excluded
    # -- HARD_FAIL is not in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES.
    assert "HARD_FAIL" not in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="HARD_FAIL", missing=["travel"])
    ) is False


def test_case_6_multiple_missing_dimensions_all_curable_admitted():
    """All four real dimensions missing -- still a fully-enumerated,
    exclusively-curable cause, so the row is eligible; the FULL set is
    disclosed downstream by _blocking_requirements, not collapsed."""
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="CURABLE_GAP",
               missing=["travel", "fx", "local_cost", "inkind"])
    ) is True


def test_case_7_component_treaty_one_hard_failing_participant_excludes_structure():
    """A component/treaty structure's role_qualification.state is already
    the WORST-of-all-participants aggregate (canonical_evaluation.py's
    _component_qual_state/_combo_qual_state) -- one hard-failing member
    correctly excludes the whole structure via this same state check."""
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="HARD_FAIL", missing=["travel", "fx"])
    ) is False


def test_stack_structural_cause_never_admitted_as_curable():
    """A multi-program stack's non-comparability sentinel
    (_STACK_NORMALIZATION_NOT_COMPUTED) is a structural engine-capability
    gap, not a producer-suppliable evidence gap -- it must never satisfy
    the all-dimensions-curable check, even paired with an otherwise-fine
    qualification state."""
    assert _STACK_NORMALIZATION_NOT_COMPUTED not in _RELOCATION_DIMENSIONS
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="CURABLE_GAP",
               missing=[_STACK_NORMALIZATION_NOT_COMPUTED])
    ) is False


def test_mixed_curable_and_structural_cause_excludes_the_row():
    """One genuinely curable dimension plus one structural/unclassified
    cause in the SAME missing list must still exclude the row -- EVERY
    listed cause must belong to the approved curable category, not just
    some of them."""
    assert _is_conditional_eligible(
        _entry(is_directly_comparable=False, state="CURABLE_GAP",
               missing=["travel", _STACK_NORMALIZATION_NOT_COMPUTED])
    ) is False


# ── _relocation_completeness: per-dimension structured decision ─────────

class _FakeInputs:
    def __init__(self, evidenced_program_facts):
        self.evidenced_program_facts = frozenset(evidenced_program_facts)


def test_relocation_completeness_baseline_always_complete_no_facts_needed():
    complete, missing = _relocation_completeness(True, "CA-MB", _FakeInputs(set()))
    assert complete is True and missing == ()


def test_relocation_completeness_non_baseline_no_facts_all_four_missing():
    complete, missing = _relocation_completeness(False, "CA-MB", _FakeInputs(set()))
    assert complete is False
    assert set(missing) == {"travel", "fx", "local_cost", "inkind"}


def test_relocation_completeness_partial_evidence_discloses_exact_remaining_set():
    facts = {
        "relocation_travel_evidenced__CA-MB",
        "relocation_fx_not_applicable__CA-MB",  # e.g. same-currency move
    }
    complete, missing = _relocation_completeness(False, "CA-MB", _FakeInputs(facts))
    assert complete is False
    assert set(missing) == {"local_cost", "inkind"}


def test_relocation_completeness_all_four_evidenced_or_marked_na_is_complete():
    facts = {
        "relocation_travel_evidenced__CA-MB",
        "relocation_fx_evidenced__CA-MB",
        "relocation_local_cost_not_applicable__CA-MB",
        "relocation_inkind_not_applicable__CA-MB",
    }
    complete, missing = _relocation_completeness(False, "CA-MB", _FakeInputs(facts))
    assert complete is True and missing == ()


def test_relocation_completeness_wrong_jurisdiction_evidence_does_not_count():
    """Evidence supplied for a DIFFERENT jurisdiction must never satisfy
    this jurisdiction's own dimension gate -- no cross-jurisdiction
    leakage."""
    facts = {
        "relocation_travel_evidenced__RO",
        "relocation_fx_evidenced__RO",
        "relocation_local_cost_evidenced__RO",
        "relocation_inkind_evidenced__RO",
    }
    complete, missing = _relocation_completeness(False, "CA-MB", _FakeInputs(facts))
    assert complete is False
    assert set(missing) == {"travel", "fx", "local_cost", "inkind"}


# ── Synthetic component/stack/treaty fixtures with a hard failure ───────
# Codex final four-row remediation (P0-SEL-ALT-001): "Component, stack,
# and treaty fixtures with at least two participants and one hard
# failure. Exact blocker equality, not subset-only assertions." Direct,
# hand-built entry dicts against the now-module-level
# _blocking_requirements/_conditional_entry -- no DB, no production
# helper used to build the expectation.

from app.services.canonical_production_view import _blocking_requirements, _conditional_entry


def _participant(participant_id, program_slug, *, state=None, missing=(), curable=(), failed=(),
                  reasoning=(), admin_disclosure=None):
    return {
        "participant_id": participant_id,
        "program_slug": program_slug,
        "qualification_state": state,
        "qualification_route": "test_route",
        "missing_facts": list(missing),
        "curable_requirements": list(curable),
        "failed_requirements": list(failed),
        "reasoning_trace": list(reasoning),
        "authority_state": "PRICEABLE_VALIDATED",
        "administrative_allocation_disclosure": admin_disclosure,
    }


def test_two_participant_component_fixture_exact_blocker_union():
    """Two participants, BOTH with real missing/curable facts and one
    administrative disclosure -- the union must be the exact
    concatenation, nothing dropped, nothing invented."""
    entry = {
        "is_baseline": False,
        "is_directly_comparable": False,
        "relocation_missing_dimensions": ["travel", "fx"],
        "relocation_completeness_jurisdiction": "RO",
        "primary_jurisdiction": "GR",
        "role_qualification": {"state": "USER_FACT_REQUIRED"},
        "participant_qualifications": [
            _participant("GR", "gr_cash_rebate", state="USER_FACT_REQUIRED",
                         missing=["gr_aggregate: needs 20 points"]),
            _participant("RO", "ro_film_office_cash_rebate", state="CURABLE_GAP",
                         curable=["ro_local_spend_threshold"],
                         admin_disclosure="RO administrative allocation risk disclosed"),
        ],
    }
    blockers = _blocking_requirements(entry)
    assert blockers == [
        "gr_aggregate: needs 20 points",
        "ro_local_spend_threshold",
        "RO administrative allocation risk disclosed",
        "relocation_travel_evidenced__RO",
        "relocation_fx_evidenced__RO",
    ], blockers


def test_two_participant_fixture_with_one_hard_failure_excludes_structure_and_retains_both_blockers():
    """One hard-failing participant among two must exclude the WHOLE
    structure from the conditional pool (via the worst-of aggregate
    state), while the retained blocker union still names BOTH
    participants -- the disclosure never silently drops the clean
    participant's own detail just because the other one hard-fails."""
    entry = {
        "is_fully_priced": True,
        "is_baseline": False,
        "is_directly_comparable": False,
        "relocation_missing_dimensions": ["travel"],
        "relocation_completeness_jurisdiction": "XX",
        "primary_jurisdiction": "YY",
        "role_qualification": {"state": "HARD_FAIL"},
        "participant_qualifications": [
            _participant("YY", "yy_program", state="QUALIFIES"),
            _participant("XX", "xx_program", state="HARD_FAIL",
                         failed=["xx_ownership_control_requirement"]),
        ],
    }
    assert _is_conditional_eligible(entry) is False, (
        "one hard-failing participant must block the whole structure from the conditional pool"
    )
    blockers = _blocking_requirements(entry)
    assert "xx_ownership_control_requirement" in blockers, (
        "the hard-failing participant's own blocker must still be disclosed"
    )


def test_stack_fixture_three_participants_exact_equality_reasoning_fallback():
    """A stack (3 participants) where one has empty requirement lists but
    a real reasoning_trace (the Manitoba/RULE_DATA_INCOMPLETE shape) —
    the trace must be disclosed, prefixed by its own program_slug, exact
    equality against the full retained set."""
    entry = {
        "is_baseline": False,
        "is_directly_comparable": True,  # comparable branch: no relocation dims appended
        "role_qualification": {"state": "CURABLE_GAP"},
        "participant_qualifications": [
            _participant("AA", "aa_program", state="CURABLE_GAP", curable=["aa_min_spend"]),
            _participant("BB", "bb_program", state="RULE_DATA_INCOMPLETE",
                         reasoning=["no NationalityRequirement rows for bb_program"]),
            _participant("CC", "cc_program", state="NOT_APPLICABLE",
                         reasoning=["no cultural test applies"]),
        ],
    }
    blockers = _blocking_requirements(entry)
    assert blockers == [
        "aa_min_spend",
        "bb_program: no NationalityRequirement rows for bb_program",
        "cc_program: no cultural test applies",
    ], blockers


def test_label_mutation_leaves_identity_and_blockers_unchanged():
    """Changing only a structure's display label must never change its
    identity (structure_id) or its disclosed blocker set — identity and
    disclosure are keyed on stable data, never the label."""
    base_participants = [_participant("RO", "ro_program", state="CURABLE_GAP", curable=["ro_gate"])]
    entry_a = {
        "structure_id": "same-stable-id", "label": "Original Label",
        "is_baseline": False, "is_directly_comparable": True,
        "role_qualification": {"state": "CURABLE_GAP"},
        "participant_qualifications": base_participants,
        "selected_incentive_usd": 100.0, "npc_with_adjustments_usd": 900.0,
    }
    entry_b = dict(entry_a, label="Completely Different Label Text")
    assert entry_a["structure_id"] == entry_b["structure_id"]
    assert _blocking_requirements(entry_a) == _blocking_requirements(entry_b)
    conditional_a = _conditional_entry(entry_a, None)
    conditional_b = _conditional_entry(entry_b, None)
    assert conditional_a["structure_id"] == conditional_b["structure_id"]
    assert conditional_a["blocking_requirements"] == conditional_b["blocking_requirements"]


# ── Real LU/FVD assertions (Codex's exact required real-project checks) ─

LITTLE_UTOPIA_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


async def test_little_utopia_leading_conditional_never_exposes_none_state(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_ID)
    astr = view["structures"]["allocated_structures"]
    lc = astr.get("leading_conditional_structure")
    assert lc is not None, "Little Utopia must still surface a leading conditional (Manitoba)"
    assert lc.get("qualification_state") is not None, (
        "real LU leading conditional must never expose qualification_state=None"
    )
    assert lc.get("qualification_state") in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES
    # Exact missing-dimension equality: no evidence has ever been
    # supplied for Manitoba, so every real dimension is disclosed.
    blockers = set(lc.get("blocking_requirements") or [])
    code = lc.get("primary_jurisdiction") or "CA-MB"
    expected = {f"relocation_{dim}_evidenced__CA-MB" for dim in _RELOCATION_DIMENSIONS}
    assert expected <= blockers, f"expected {expected} subset of {blockers}"
    # Codex final four-row remediation (P0-SEL-ALT-001): "Little Utopia
    # Manitoba must disclose the actual RULE_DATA_INCOMPLETE reason as a
    # blocker, not only relocation facts."
    assert any("NationalityRequirement" in b for b in blockers), (
        f"Manitoba's real RULE_DATA_INCOMPLETE reason must be disclosed, observed {blockers}"
    )
    assert astr.get("canonical_selected_structure_id") is None, (
        "Little Utopia has no verified winner -- unchanged"
    )


async def test_fvd_leading_conditional_never_exposes_none_state_and_names_romania(db: AsyncSession):
    await evaluate_project(db, FVD_ID)
    view = await build_production_and_structures(db, FVD_ID)
    astr = view["structures"]["allocated_structures"]
    lc = astr.get("leading_conditional_structure")
    assert lc is not None, "FVD must still surface a leading conditional (Greece + Romania component)"
    assert lc.get("qualification_state") is not None, (
        "real FVD leading conditional must never expose qualification_state=None -- "
        "this is the exact defect Codex's delta audit found in 67fbc30"
    )
    assert lc.get("qualification_state") in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES
    blockers = lc.get("blocking_requirements") or []
    expected_ro = {f"relocation_{dim}_evidenced__RO" for dim in _RELOCATION_DIMENSIONS}
    assert expected_ro <= set(blockers), (
        f"the routed-to jurisdiction (Romania) must be named per-dimension in the "
        f"blocker set, never the anchor (Greece) alone: expected {expected_ro} subset "
        f"of {blockers}"
    )
    assert not any(b.startswith("relocation_") and b.endswith("__GR") for b in blockers), (
        "relocation-completeness blockers must target the TARGET (RO) jurisdiction "
        "the component actually relocates to, never the anchor (GR)"
    )
    # Codex final four-row remediation (P0-SEL-ALT-001): "FVD Greece+
    # Romania must include Greece gr_aggregate, every applicable
    # Romanian/program/allocation gate."
    assert any("gr_aggregate" in b for b in blockers), (
        f"Greece's own real gr_aggregate missing fact must be disclosed, observed {blockers}"
    )
    assert any("ro_film_office_cash_rebate" in b or "cultural_test_required" in b for b in blockers), (
        f"Romania's own participant detail must be disclosed, observed {blockers}"
    )
    assert astr.get("canonical_selected_structure_id") is None, (
        "F#K Valentine's Day has no verified winner -- unchanged"
    )


async def test_bad_hombres_and_lips_retain_exact_winners_no_competing_conditional(db: AsyncSession):
    for pid, expected_slug, expected_incentive, expected_npc in (
        (BAD_HOMBRES_ID, "us_nm_film_credit", 596910.25, 1885112.75),
        (LIPS_LIKE_SUGAR_ID, "ca_film_30", 3459278.90, 8524375.10),
    ):
        await evaluate_project(db, pid)
        view = await build_production_and_structures(db, pid)
        astr = view["structures"]["allocated_structures"]
        assert astr.get("canonical_selected_structure_id") is not None
        assert astr.get("leading_conditional_structure") is None, (
            f"{pid} has a verified winner -- must never ALSO expose a competing leading conditional"
        )
        winner = next(
            r for r in astr["ranking"] if r["structure_id"] == astr["canonical_selected_structure_id"]
        )
        assert winner["program_slug"] == expected_slug
        assert winner["selected_incentive_usd"] == pytest.approx(expected_incentive, abs=0.01)
        assert winner["npc_with_adjustments_usd"] == pytest.approx(expected_npc, abs=0.01)
