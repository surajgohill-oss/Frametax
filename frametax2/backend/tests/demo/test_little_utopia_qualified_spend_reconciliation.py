from __future__ import annotations

"""Targeted regression tests for the Workspace "Qualified spend can exceed
Gross budget by $2" investigation (producer-reported: Mauritius+SA and
Mauritius+JP cards showing qualified spend of 4,364,395 against a gross
budget of 4,364,393).

Root cause (verified against the real served payload, not assumed): a
structure's "Qualified spend" is the sum of its own segments' qpe_usd,
built from the same 44 real leaf budget accounts
(little_utopia_real_budget.LITTLE_UTOPIA_REAL_BUDGET_LINES). "Gross
budget" is structure.gross_budget_usd, which is
AUTHORITATIVE_GROSS_BUDGET_USD — the source document's own stated Grand
Total, which is $2 LESS than the arithmetic sum of its own 44 leaf lines
(LEAF_ACCOUNT_SUM_USD) due to a pre-existing, disclosed, already-tested
source-document rounding variance (RECONCILIATION_NOTE). Any structure
whose qualification pipeline excludes nothing from any segment therefore
sums to LEAF_ACCOUNT_SUM_USD, which is $2 above the authoritative gross
budget — never more than that, and never for an undisclosed reason.

These tests pin: (1) the invariant that no structure's segment-QPE sum
exceeds gross budget by more than the documented, bounded
RECONCILIATION_VARIANCE_USD; (2) that GET /production continues to serve
the budget_reconciliation disclosure the frontend fix (Workspace.jsx
ScenarioCard) depends on to explain the variance inline instead of
presenting an unexplained contradiction.
"""

from app.data.little_utopia_real_budget import RECONCILIATION_VARIANCE_USD
from app.demo.little_utopia_state import build_allocated_structures, get_state


def _structures():
    state = get_state()
    return build_allocated_structures(state)["structures"]


class TestQualifiedSpendNeverExceedsGrossBudgetUnexplained:
    def test_no_structure_qpe_sum_exceeds_gross_by_more_than_the_disclosed_variance(self):
        for s in _structures():
            gross = s["gross_budget_usd"]
            qpe_sum = sum((sg.get("qpe_usd") or 0) for sg in s.get("segments", []))
            overage = qpe_sum - gross
            assert overage <= RECONCILIATION_VARIANCE_USD + 1e-6, (
                f"{s['structure_id']}: qualified spend ({qpe_sum}) exceeds gross budget "
                f"({gross}) by {overage}, more than the documented "
                f"${RECONCILIATION_VARIANCE_USD} source-document reconciliation variance — "
                "this would be an undisclosed, unexplained overage, not the known variance."
            )

    def test_at_least_one_real_structure_exhibits_the_full_variance(self):
        """Pins the exact reported symptom (Mauritius + SA / Mauritius + JP
        component-relocation cards): confirms the $2 case is real, reachable
        served data, not just a theoretical bound.

        Consolidated Backend Correction, Part 19-20 (CBA-009): by DEFAULT
        (no contingency_expected_utilization_pct fact answered), every
        structure's QPE is now $301,131.00 lower than before — the
        contingency reserve is a disclosed grey area, not silently
        100%-qualifying — so no structure hits exactly the $2 leaf-sum
        variance by default any more. This is orthogonal to the $2 source-
        document rounding case: an explicit producer election of 100%
        expected contingency utilization removes the grey exclusion and
        reproduces the original, unrelated $2 rounding variance exactly,
        proving the mechanism this test exists to pin is still real and
        reachable, not merely a historical artifact."""
        from app.demo.little_utopia_state import apply_fact_answers, reset_fact_answers

        try:
            apply_fact_answers({"contingency_expected_utilization_pct": 100.0})
            overages = [
                sum((sg.get("qpe_usd") or 0) for sg in s.get("segments", [])) - s["gross_budget_usd"]
                for s in _structures()
            ]
            assert any(abs(o - RECONCILIATION_VARIANCE_USD) < 1e-6 for o in overages)
        finally:
            reset_fact_answers()

    def test_mauritius_baseline_qualified_spend_stays_below_gross_budget(self):
        """The single-jurisdiction baseline has real, non-zero exclusions
        under Mauritius's own EDB Film Rebate rules — it must NOT exhibit
        the leaf-sum overage the multi-jurisdiction structures show."""
        baseline = next(s for s in _structures() if s["structure_id"] == "ALLOC-BASELINE-MU")
        qpe_sum = sum((sg.get("qpe_usd") or 0) for sg in baseline["segments"])
        assert qpe_sum < baseline["gross_budget_usd"]


class TestBudgetReconciliationDisclosureServed:
    """The frontend fix (ScenarioCard's inline "†" disclosure) reads
    production.budget_reconciliation from GET /production — pin its shape
    so a future change can't silently drop the field the fix depends on."""

    def test_production_state_carries_reconciliation_fields(self):
        state = get_state()
        assert state.budget_authoritative_gross_usd < state.budget_leaf_account_sum_usd
        assert (
            state.budget_leaf_account_sum_usd - state.budget_authoritative_gross_usd
            == state.budget_reconciliation_variance_usd
        )
        assert state.budget_reconciliation_note
