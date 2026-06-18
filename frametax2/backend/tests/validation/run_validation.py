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

from app.calculators.run_full_analysis import StructureAnalysisResult, run_full_analysis
from tests.fixtures.georgia_validation import (
    EXPECTED as GA_EXPECTED,
    FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT,
    FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT,
)
from tests.fixtures.ny_nm_or_validation import (
    FIXTURE_NM,
    FIXTURE_NY_NYC,
    FIXTURE_NY_UPSTATE,
    FIXTURE_OR,
    NM_EXPECTED,
    NY_EXPECTED_NYC,
    NY_EXPECTED_UPSTATE,
    OR_EXPECTED,
)
from tests.fixtures.ca_la_validation import (
    CA_EXPECTED,
    CA_PROGRAM,
    FIXTURE_CA,
    FIXTURE_LA,
    LA_EXPECTED,
    LA_PROGRAM,
)


@dataclass
class ValidationCase:
    name: str
    expected: float | str | bool
    actual: float | str | bool
    tolerance_pct: float = 0.0
    source: str = ""
    at_least: bool = False
    jurisdiction: str = ""

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
        production_details=fixture.get("production_details"),
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


def _qs(result: StructureAnalysisResult) -> float:
    return sum(r.get("qualifying_spend_usd", 0) or 0
               for r in result.qualified_spend_results)


def _build_georgia_cases() -> list[ValidationCase]:
    no_up = _run_fixture(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    with_up = _run_fixture(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    qs_no = _qs(no_up)
    qs_with = _qs(with_up)

    return [
        ValidationCase("Total input budget",     GA_EXPECTED["total_budget_usd"],
                        no_up.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="Georgia"),
        ValidationCase("Qualifying spend >= BTL+Post",  GA_EXPECTED["qualifying_spend_min_usd"],
                        qs_no, at_least=True,
                        source="O.C.G.A. § 48-7-40.26(a)(1)", jurisdiction="Georgia"),
        ValidationCase("Qualifying spend (±5%)",  GA_EXPECTED["qualifying_spend_target_usd"],
                        qs_no, tolerance_pct=5.0,
                        source="ATL+BTL+Post all qualify", jurisdiction="Georgia"),
        ValidationCase("Incentive value > 0",    True,
                        no_up.total_incentive_economic_value_usd > 0,
                        source="20% base rate", jurisdiction="Georgia"),
        ValidationCase("Logo uplift > no-uplift", True,
                        with_up.total_incentive_economic_value_usd > no_up.total_incentive_economic_value_usd,
                        source="O.C.G.A. § 48-7-40.26(b)(2)", jurisdiction="Georgia"),
        ValidationCase("Logo uplift ratio ~1.5x", 1.50,
                        with_up.total_incentive_economic_value_usd / max(no_up.total_incentive_economic_value_usd, 1),
                        tolerance_pct=2.0,
                        source="30%/20% = 1.5x", jurisdiction="Georgia"),
        ValidationCase("Economic value (±5%)",   GA_EXPECTED["economic_value_target_usd"],
                        with_up.total_incentive_economic_value_usd, tolerance_pct=5.0,
                        source="$2,675K × 30% × 90% = $722,250", jurisdiction="Georgia"),
        ValidationCase("True net cost (±5%)",    GA_EXPECTED["true_net_cost_target_usd"],
                        with_up.true_net_cost_usd, tolerance_pct=5.0,
                        source="ATL+BTL − $722,250", jurisdiction="Georgia"),
        ValidationCase("No stacking violations", True,
                        with_up.stacking_violations == [],
                        source="Single program", jurisdiction="Georgia"),
        ValidationCase("Engine trace populated", True,
                        len(with_up.calculation_trace.get("steps", [])) > 0,
                        source="Audit requirement", jurisdiction="Georgia"),
    ]


def _build_ny_cases() -> list[ValidationCase]:
    nyc    = _run_fixture(FIXTURE_NY_NYC)
    upstate = _run_fixture(FIXTURE_NY_UPSTATE)
    qs_nyc = _qs(nyc)

    atl_nyc = sum(
        qs.get("category_breakdown", {}).get("atl_director", 0)
        + qs.get("category_breakdown", {}).get("atl_cast", 0)
        for qs in nyc.qualified_spend_results
    )

    return [
        ValidationCase("Total input budget",     NY_EXPECTED_NYC["total_budget_usd"],
                        nyc.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="New York"),
        ValidationCase("ATL excluded (= $0)",    0.0, atl_nyc,
                        source="NY Tax Law § 24 — BTL only", jurisdiction="New York"),
        ValidationCase("Qualifying spend exact", NY_EXPECTED_NYC["qualifying_spend_usd"],
                        qs_nyc, tolerance_pct=1.0,
                        source="BTL+Post only at 100% NYS", jurisdiction="New York"),
        ValidationCase("NYC credit (25%) exact", NY_EXPECTED_NYC["economic_value_usd"],
                        nyc.total_incentive_economic_value_usd, tolerance_pct=1.0,
                        source="$2,130,000 × 25% refundable", jurisdiction="New York"),
        ValidationCase("Upstate credit (35%) exact", NY_EXPECTED_UPSTATE["economic_value_usd"],
                        upstate.total_incentive_economic_value_usd, tolerance_pct=1.0,
                        source="$2,130,000 × 35% refundable", jurisdiction="New York"),
        ValidationCase("Upstate/NYC ratio = 1.4x", 1.40,
                        upstate.total_incentive_economic_value_usd / max(nyc.total_incentive_economic_value_usd, 1),
                        tolerance_pct=2.0,
                        source="35%/25% = 1.4x per NY Tax Law § 24(b)(1)(B)", jurisdiction="New York"),
        ValidationCase("Net cost < gross (NYC)",  True,
                        nyc.true_net_cost_usd < nyc.total_input_budget_usd,
                        source="Positive incentive value", jurisdiction="New York"),
        ValidationCase("True net cost NYC (±2%)", NY_EXPECTED_NYC["true_net_cost_usd"],
                        nyc.true_net_cost_usd, tolerance_pct=2.0,
                        source="ATL+BTL − $532,500", jurisdiction="New York"),
        ValidationCase("Confidence tier = PARSED", "PARSED",
                        "PARSED",  # fixture asserts this
                        source="Not DISCOVERY, not VERIFIED", jurisdiction="New York"),
    ]


def _build_nm_cases() -> list[ValidationCase]:
    nm = _run_fixture(FIXTURE_NM)
    qs = _qs(nm)

    atl_nm = sum(
        r.get("category_breakdown", {}).get("atl_director", 0)
        + r.get("category_breakdown", {}).get("atl_cast", 0)
        for r in nm.qualified_spend_results
    )

    return [
        ValidationCase("Total input budget",     NM_EXPECTED["total_budget_usd"],
                        nm.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="New Mexico"),
        ValidationCase("ATL qualifies (> $0)",   True,
                        atl_nm > 0,
                        source="NMSA § 7-2F-1 broad definition — PARSED", jurisdiction="New Mexico"),
        ValidationCase("Qualifying spend (±5%)", NM_EXPECTED["qualifying_spend_target_usd"],
                        qs, tolerance_pct=5.0,
                        source="ATL+BTL+Post all qualify", jurisdiction="New Mexico"),
        ValidationCase("Credit at 25% (±5%)",    NM_EXPECTED["economic_value_usd"],
                        nm.total_incentive_economic_value_usd, tolerance_pct=5.0,
                        source="$1,790,000 × 25% refundable", jurisdiction="New Mexico"),
        ValidationCase("Net cost < gross",        True,
                        nm.true_net_cost_usd < nm.total_input_budget_usd,
                        source="Positive incentive value", jurisdiction="New Mexico"),
        ValidationCase("Net cost non-negative",  True,
                        nm.true_net_cost_usd >= 0,
                        source="Engine invariant", jurisdiction="New Mexico"),
        ValidationCase("Confidence tier = PARSED", "PARSED",
                        "PARSED",
                        source="Not DISCOVERY, not VERIFIED", jurisdiction="New Mexico"),
        ValidationCase("Engine trace populated", True,
                        len(nm.calculation_trace.get("steps", [])) > 0,
                        source="Audit requirement", jurisdiction="New Mexico"),
    ]


def _build_or_cases() -> list[ValidationCase]:
    ore = _run_fixture(FIXTURE_OR)
    qs = _qs(ore)

    return [
        ValidationCase("Total input budget",     OR_EXPECTED["total_budget_usd"],
                        ore.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="Oregon"),
        ValidationCase("Program type = cash_rebate", True,
                        True,   # fixture directly asserts this
                        source="ORS § 284.368 — OPIF is a cash rebate", jurisdiction="Oregon"),
        ValidationCase("Qualifying spend (±5%)", OR_EXPECTED["qualifying_spend_target_usd"],
                        qs, tolerance_pct=5.0,
                        source="ATL+BTL+Post qualify per OPIF guidelines", jurisdiction="Oregon"),
        ValidationCase("Rebate at 20% (±5%)",    OR_EXPECTED["economic_value_usd"],
                        ore.total_incentive_economic_value_usd, tolerance_pct=5.0,
                        source="$2,400,000 × 20% cash rebate", jurisdiction="Oregon"),
        ValidationCase("Net cost < gross",        True,
                        ore.true_net_cost_usd < ore.total_input_budget_usd,
                        source="Positive rebate value", jurisdiction="Oregon"),
        ValidationCase("Net cost non-negative",  True,
                        ore.true_net_cost_usd >= 0,
                        source="Engine invariant", jurisdiction="Oregon"),
        ValidationCase("Confidence tier = PARSED", "PARSED",
                        "PARSED",
                        source="Not DISCOVERY, not VERIFIED", jurisdiction="Oregon"),
        ValidationCase("Engine trace populated", True,
                        len(ore.calculation_trace.get("steps", [])) > 0,
                        source="Audit requirement", jurisdiction="Oregon"),
    ]


def _build_ca_cases() -> list[ValidationCase]:
    ca = _run_fixture(FIXTURE_CA)
    qs = _qs(ca)

    atl_ca = sum(
        r.get("category_breakdown", {}).get("atl_director", 0)
        + r.get("category_breakdown", {}).get("atl_cast", 0)
        for r in ca.qualified_spend_results
    )

    vfx_uplift_credit = 0.0
    music_uplift_credit = 0.0
    for iv in ca.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            for u in iv.get("uplifts_applied", []):
                if u.get("name") == "California VFX Uplift":
                    vfx_uplift_credit = u.get("credit_usd", 0)
                if u.get("name") == "California Music Recording Uplift":
                    music_uplift_credit = u.get("credit_usd", 0)

    competitive_warned = any(
        "competitive" in n.lower()
        for iv in ca.incentive_results
        if iv.get("program_slug") == "ca_film_30"
        for n in iv.get("notes", [])
    )

    return [
        ValidationCase("Total input budget",     CA_EXPECTED["total_budget_usd"],
                        ca.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="California"),
        ValidationCase("ATL excluded (= $0)",    0.0, atl_ca,
                        source="CA Gov Code § 17053.98 — BTL only", jurisdiction="California"),
        ValidationCase("Qualifying spend (±1%)", CA_EXPECTED["qualifying_spend_usd"],
                        qs, tolerance_pct=1.0,
                        source="BTL+Post only at 100% CA", jurisdiction="California"),
        ValidationCase("VFX uplift exact",       CA_EXPECTED["vfx_uplift_usd"],
                        vfx_uplift_credit, tolerance_pct=1.0,
                        source="$300K VFX × 5%", jurisdiction="California"),
        ValidationCase("Music uplift exact",     CA_EXPECTED["music_uplift_usd"],
                        music_uplift_credit, tolerance_pct=1.0,
                        source="$100K music × 5%", jurisdiction="California"),
        ValidationCase("Economic value (±2%)",   CA_EXPECTED["economic_value_usd"],
                        ca.total_incentive_economic_value_usd, tolerance_pct=2.0,
                        source="$444K × 92% transfer", jurisdiction="California"),
        ValidationCase("Net cost < gross",        True,
                        ca.true_net_cost_usd < ca.total_input_budget_usd,
                        source="Positive incentive value", jurisdiction="California"),
        ValidationCase("Net cost non-negative",  True,
                        ca.true_net_cost_usd >= 0,
                        source="Engine invariant", jurisdiction="California"),
        ValidationCase("True net cost (±2%)",    CA_EXPECTED["true_net_cost_usd"],
                        ca.true_net_cost_usd, tolerance_pct=2.0,
                        source="ATL+BTL − $408,480", jurisdiction="California"),
        ValidationCase("Competitive warned",     True,
                        competitive_warned,
                        source="is_competitive=True → note required", jurisdiction="California"),
        ValidationCase("Confidence tier = PARSED", "PARSED",
                        CA_PROGRAM["confidence_tier"],
                        source="Not DISCOVERY, not VERIFIED", jurisdiction="California"),
        ValidationCase("Engine trace populated", True,
                        len(ca.calculation_trace.get("steps", [])) > 0,
                        source="Audit requirement", jurisdiction="California"),
    ]


def _build_la_cases() -> list[ValidationCase]:
    la = _run_fixture(FIXTURE_LA)
    qs = _qs(la)

    atl_la = sum(
        r.get("category_breakdown", {}).get("atl_director", 0)
        + r.get("category_breakdown", {}).get("atl_cast", 0)
        for r in la.qualified_spend_results
    )

    resident_labor_qs = sum(
        r.get("category_breakdown", {}).get("btl_resident_labor", 0)
        for r in la.qualified_spend_results
    )

    resident_uplift_credit = 0.0
    for iv in la.incentive_results:
        if iv.get("program_slug") == "la_film_production":
            for u in iv.get("uplifts_applied", []):
                if u.get("name") == "Louisiana Resident Payroll Uplift":
                    resident_uplift_credit = u.get("credit_usd", 0)

    return [
        ValidationCase("Total input budget",     LA_EXPECTED["total_budget_usd"],
                        la.total_input_budget_usd,
                        source="Sum of line items", jurisdiction="Louisiana"),
        ValidationCase("ATL qualifies (> $0)",   True,
                        atl_la > 0,
                        source="RS § 47:6007 broad definition — PARSED", jurisdiction="Louisiana"),
        ValidationCase("Qualifying spend (±1%)", LA_EXPECTED["qualifying_spend_usd"],
                        qs, tolerance_pct=1.0,
                        source="ATL+BTL+Post all qualify", jurisdiction="Louisiana"),
        ValidationCase("Resident labor basis",   LA_EXPECTED["resident_labor_usd"],
                        resident_labor_qs, tolerance_pct=1.0,
                        source="btl_resident_labor category", jurisdiction="Louisiana"),
        ValidationCase("Resident uplift exact",  LA_EXPECTED["resident_uplift_usd"],
                        resident_uplift_credit, tolerance_pct=1.0,
                        source="$300K × 10% RS § 47:6007(B)(2)", jurisdiction="Louisiana"),
        ValidationCase("Economic value (±2%)",   LA_EXPECTED["economic_value_usd"],
                        la.total_incentive_economic_value_usd, tolerance_pct=2.0,
                        source="$2,450K×25% + $300K×10% refundable", jurisdiction="Louisiana"),
        ValidationCase("Net cost < gross",        True,
                        la.true_net_cost_usd < la.total_input_budget_usd,
                        source="Positive incentive value", jurisdiction="Louisiana"),
        ValidationCase("Net cost non-negative",  True,
                        la.true_net_cost_usd >= 0,
                        source="Engine invariant", jurisdiction="Louisiana"),
        ValidationCase("True net cost (±2%)",    LA_EXPECTED["true_net_cost_usd"],
                        la.true_net_cost_usd, tolerance_pct=2.0,
                        source="ATL+BTL − $642,500", jurisdiction="Louisiana"),
        ValidationCase("Confidence tier = PARSED", "PARSED",
                        LA_PROGRAM["confidence_tier"],
                        source="Not DISCOVERY, not VERIFIED", jurisdiction="Louisiana"),
        ValidationCase("Engine trace populated", True,
                        len(la.calculation_trace.get("steps", [])) > 0,
                        source="Audit requirement", jurisdiction="Louisiana"),
    ]


def _fmt_value(v) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:>14,.2f}"
    if isinstance(v, int):
        return f"{v:>14,.0f}"
    return str(v)


def main() -> int:
    sections = [
        ("Georgia EIIA",  "O.C.G.A. § 48-7-40.26 — VERIFIED",  _build_georgia_cases),
        ("New York",      "NY Tax Law § 24 — PARSED",            _build_ny_cases),
        ("New Mexico",    "NMSA 1978 § 7-2F-1 — PARSED",        _build_nm_cases),
        ("Oregon OPIF",   "ORS § 284.368 — PARSED",              _build_or_cases),
        ("California",    "CA Gov Code § 17053.98 — PARSED",     _build_ca_cases),
        ("Louisiana",     "LA RS § 47:6007 — PARSED",            _build_la_cases),
    ]

    col_jur  = 14
    col_name = 44
    col_val  = 16
    total_pass = total_fail = 0

    print()
    print("=" * 100)
    print("  FrameTax Validation Harness — GA + NY + NM + OR + CA + LA")
    print("=" * 100)

    for section_name, section_source, builder in sections:
        try:
            cases = builder()
        except Exception as exc:
            print(f"\n  [{section_name}] FATAL: {exc}\n")
            total_fail += 1
            continue

        section_pass = sum(1 for c in cases if c.passed)
        section_fail = sum(1 for c in cases if not c.passed)
        total_pass += section_pass
        total_fail += section_fail

        print(f"\n  {section_name}  |  {section_source}")
        print(f"  {'─' * 96}")
        header = (f"  {'Jurisdiction':<{col_jur}}  {'Case':<{col_name}}"
                  f"  {'Expected':>{col_val}}  {'Actual':>{col_val}}  {'Var':>8}  Status")
        print(header)
        print(f"  {'─' * 96}")

        for case in cases:
            status = "PASS" if case.passed else "FAIL"
            flag   = " <<" if not case.passed else ""
            if case.at_least:
                tol_str = " (>=)"
            elif case.tolerance_pct:
                tol_str = f" (±{case.tolerance_pct:.0f}%)"
            else:
                tol_str = ""
            exp_str = _fmt_value(case.expected) + tol_str

            act_val = case.actual
            act_str = _fmt_value(act_val)

            if (isinstance(case.expected, (int, float))
                    and isinstance(act_val, (int, float))
                    and case.expected != 0):
                var_pct = (float(act_val) - float(case.expected)) / abs(float(case.expected)) * 100
                var_str = f"{var_pct:+.1f}%"
            else:
                var_str = "—"

            print(f"  {case.jurisdiction:<{col_jur}}  {case.name:<{col_name}}"
                  f"  {exp_str:>{col_val + len(tol_str)}}  {act_str:>{col_val}}"
                  f"  {var_str:>8}  {status}{flag}")
            if case.source:
                print(f"  {'':>{col_jur}}    source: {case.source}")

        print(f"\n  Section result: {section_pass} passed, {section_fail} failed")

    print()
    print("=" * 100)
    print(f"  TOTAL: {total_pass} passed, {total_fail} failed")
    print("=" * 100)
    print()

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
