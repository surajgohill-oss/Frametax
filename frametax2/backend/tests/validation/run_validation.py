"""
Validation harness for FrameTax calculation engine.

Run with:
  cd backend && python -m tests.validation.run_validation

Prints a pass/fail table for each registered validation case.
No pytest — runs standalone for quick smoke-test before a DB migration.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable

from app.calculators.run_full_analysis import StructureAnalysisResult, run_full_analysis
from tests.fixtures.georgia_validation import (
    EXPECTED,
    FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT,
    FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT,
)


@dataclass
class ValidationCase:
    name: str
    expected: float | str | bool
    actual: float | str | bool
    tolerance_pct: float = 0.0
    source: str = ""
    at_least: bool = False  # if True, check actual >= expected

    @property
    def passed(self) -> bool:
        if isinstance(self.expected, bool):
            return bool(self.actual) == self.expected
        if isinstance(self.expected, str):
            return self.actual == self.expected
        if self.at_least:
            return float(self.actual) >= float(self.expected)
        if self.tolerance_pct > 0 and isinstance(self.expected, (int, float)):
            tol = abs(self.expected) * (self.tolerance_pct / 100)
            return abs(float(self.actual) - self.expected) <= tol
        return float(self.actual) == self.expected


def _run_fixture(fixture: dict) -> StructureAnalysisResult:
    return run_full_analysis(
        structure_id="validation-harness",
        jurisdiction=fixture["jurisdiction"],
        line_items=fixture["line_items"],
        programs_with_categories=fixture["programs_with_categories"],
        stacking_rules=fixture.get("stacking_rules", []),
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=None,
        production_details=None,
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


def _build_cases() -> list[ValidationCase]:
    no_uplift   = _run_fixture(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    with_uplift = _run_fixture(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)

    qs_no = sum(r.get("qualifying_spend_usd", 0) or 0
                for r in no_uplift.qualified_spend_results)
    qs_with = sum(r.get("qualifying_spend_usd", 0) or 0
                  for r in with_uplift.qualified_spend_results)

    cases = [
        ValidationCase(
            name="Total input budget (no uplift)",
            expected=EXPECTED["total_budget_usd"],
            actual=no_uplift.total_input_budget_usd,
            source="Sum of GEORGIA_LINE_ITEMS",
        ),
        ValidationCase(
            name="Qualifying spend >= BTL+Post minimum",
            expected=EXPECTED["qualifying_spend_min_usd"],
            actual=qs_no,
            tolerance_pct=0.0,
            at_least=True,
            source="O.C.G.A. § 48-7-40.26(a)(1) — BTL+Post categories all qualify",
        ),
        ValidationCase(
            name="Qualifying spend target (ATL+BTL+Post)",
            expected=EXPECTED["qualifying_spend_target_usd"],
            actual=qs_no,
            tolerance_pct=5.0,
            source="O.C.G.A. § 48-7-40.26(a)(1) — all eligible categories",
        ),
        ValidationCase(
            name="Incentive economic value > 0 (no uplift)",
            expected=True,
            actual=no_uplift.total_incentive_economic_value_usd > 0,
            source="Engine must produce non-zero output with VERIFIED rates",
        ),
        ValidationCase(
            name="Credit no-uplift >= min expected",
            expected=EXPECTED["credit_no_uplift_min_usd"] * 0.90,
            actual=no_uplift.total_incentive_economic_value_usd,
            tolerance_pct=0.0,
            at_least=True,
            source="20% of min qualifying spend × 90% transferable value",
        ),
        ValidationCase(
            name="Logo uplift increases economic value",
            expected=True,
            actual=with_uplift.total_incentive_economic_value_usd
                   > no_uplift.total_incentive_economic_value_usd,
            source="O.C.G.A. § 48-7-40.26(b)(2) — +10% logo uplift",
        ),
        ValidationCase(
            name="Logo uplift ratio ~1.5x (30%/20%)",
            expected=1.50,
            actual=(with_uplift.total_incentive_economic_value_usd
                    / max(no_uplift.total_incentive_economic_value_usd, 1)),
            tolerance_pct=2.0,
            source="30% credit (with logo) / 20% credit (without) = 1.5x",
        ),
        ValidationCase(
            name="Economic value with uplift (target ±5%)",
            expected=EXPECTED["economic_value_target_usd"],
            actual=with_uplift.total_incentive_economic_value_usd,
            tolerance_pct=5.0,
            source="$2,675,000 × 30% × 90% = $722,250",
        ),
        ValidationCase(
            name="True net cost with uplift (target ±5%)",
            expected=EXPECTED["true_net_cost_target_usd"],
            actual=with_uplift.true_net_cost_usd,
            tolerance_pct=5.0,
            source="$2,950,000 − $722,250 = $2,227,750",
        ),
        ValidationCase(
            name="Net cost non-negative",
            expected=True,
            actual=with_uplift.true_net_cost_usd >= 0,
            source="Engine invariant",
        ),
        ValidationCase(
            name="Net cost < gross budget",
            expected=True,
            actual=with_uplift.true_net_cost_usd < with_uplift.total_input_budget_usd,
            source="Engine invariant with positive incentive value",
        ),
        ValidationCase(
            name="No stacking violations",
            expected=True,
            actual=with_uplift.stacking_violations == [],
            source="Single program — no stacking possible",
        ),
        ValidationCase(
            name="Engine version",
            expected="0.1.0",
            actual=with_uplift.engine_version,
            source="ENGINE_VERSION constant",
        ),
        ValidationCase(
            name="Calculation trace populated",
            expected=True,
            actual=len(with_uplift.calculation_trace.get("steps", [])) > 0,
            source="Full trace required for audit",
        ),
    ]
    return cases


def _fmt_value(v) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:>14,.2f}"
    return str(v)


def main() -> int:
    print("\n" + "=" * 80)
    print("  FrameTax Georgia EIIA Validation Harness")
    print("  Source: O.C.G.A. § 48-7-40.26")
    print("=" * 80)

    try:
        cases = _build_cases()
    except Exception as exc:
        print(f"\nFATAL: Could not build validation cases — {exc}\n")
        return 1

    passed = 0
    failed = 0
    col_name = 50
    col_val  = 16

    header = f"  {'Case':<{col_name}} {'Expected':>{col_val}}  {'Actual':>{col_val}}  Status"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for case in cases:
        status = "PASS" if case.passed else "FAIL"
        if case.at_least:
            tol_str = " (>=)"
        elif case.tolerance_pct:
            tol_str = f" (±{case.tolerance_pct:.0f}%)"
        else:
            tol_str = ""
        exp_str = _fmt_value(case.expected) + tol_str
        act_str = _fmt_value(case.actual)
        flag = "" if case.passed else " <<<<<"
        print(f"  {case.name:<{col_name}} {exp_str:>{col_val + len(tol_str)}}  {act_str:>{col_val}}  {status}{flag}")
        if case.source:
            print(f"    {'':>{col_name}} source: {case.source}")
        if case.passed:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 80)
    print(f"  RESULT: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
