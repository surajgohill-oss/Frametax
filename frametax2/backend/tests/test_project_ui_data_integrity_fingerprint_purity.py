"""
PROJECT_UI_DATA_INTEGRITY, Phase 3 whitelist item 1 -- fingerprint purity.

A project's canonical evaluation fingerprint must be identical before and
after production_normalization's live FX global changes (the same global
ensure_fx_freshness() mutates from inside the READ-ONLY GET
/projects/{id}/state), whether the change is triggered by THIS project's
own page view or a completely unrelated project's.
"""
from __future__ import annotations

from app.calculators import production_normalization as fx_doctrine
from app.calculators.qualification_derivation import BudgetLine
from app.services.canonical_evaluation import _compute_fingerprint
from app.services.canonical_project_economics import ProjectEconomicInputs


def _inputs(**overrides) -> ProjectEconomicInputs:
    base = dict(
        project_id="project-a", project_name="Test", jurisdiction_code="MU",
        production_type="feature_film", gross_budget_usd=1_000_000.0, leaf_account_sum_usd=1_000_000.0,
        budget_lines=[BudgetLine("1000", "Cast", 500_000.0, spend_category="atl_cast")],
        spend_category_by_code={"1000": "atl_cast"},
        accounts_outside_jurisdiction=frozenset(), offshore_payroll_accounts=frozenset(),
    )
    base.update(overrides)
    return ProjectEconomicInputs(**base)


def test_fingerprint_unchanged_after_a_live_fx_refresh_and_after_opening_another_project():
    saved = (
        dict(fx_doctrine.FX_RATE_SNAPSHOTS), fx_doctrine.FX_LIVE_SNAPSHOT_DATE,
        fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE, fx_doctrine.FX_FRESHNESS_STATUS,
    )
    try:
        inputs = _inputs()
        fp_before = _compute_fingerprint(inputs)

        # Simulate ensure_fx_freshness() adopting a new live snapshot --
        # exactly what opening THIS project's own /state would trigger.
        fx_doctrine.apply_live_fx_snapshot("2026-09-22", {"EUR": 0.90, "GBP": 0.80}, "test-provider")
        fp_after_own_refresh = _compute_fingerprint(inputs)
        assert fp_after_own_refresh == fp_before, (
            "a live FX refresh must never change this project's own canonical fingerprint"
        )

        # Simulate a SECOND, unrelated project's page open refreshing the
        # SAME shared global again.
        fx_doctrine.apply_live_fx_snapshot("2026-09-23", {"EUR": 0.77, "GBP": 0.66}, "test-provider-2")
        fp_after_other_project = _compute_fingerprint(inputs)
        assert fp_after_other_project == fp_before, (
            "opening/refreshing a DIFFERENT project must never change this project's fingerprint"
        )
    finally:
        fx_doctrine.FX_RATE_SNAPSHOTS.clear()
        fx_doctrine.FX_RATE_SNAPSHOTS.update(saved[0])
        fx_doctrine.FX_LIVE_SNAPSHOT_DATE = saved[1]
        fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE = saved[2]
        fx_doctrine.FX_FRESHNESS_STATUS = saved[3]
