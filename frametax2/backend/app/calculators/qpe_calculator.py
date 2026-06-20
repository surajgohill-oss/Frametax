"""
qpe_calculator.py

Deterministic three-scenario Qualifying Production Expenditure (QPE) calculator.

Scenarios:
  conservative — only items clearly qualifying under confirmed rules
  base         — conservative + contested items routed through local SPV
  optimistic   — base + items whose qualifying status is plausible but unconfirmed

Each account in the input list carries three boolean flags indicating which
scenarios it qualifies under.  A base-qualifying item must also be
conservative-qualifying (conservative ⊆ base ⊆ optimistic).

Finance cost on rebate receivable is calculated separately and is NOT deducted
from QPE — it is a cashflow cost reported alongside the rebate estimate.

No LLM calls.  All arithmetic is deterministic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


CALCULATOR_VERSION = "0.1.0"


@dataclass
class QPEAccount:
    """
    Single budget account entry with QPE scenario flags.

    amount_usd          — gross spend for this account (USD)
    conservative_qualifies — included in conservative QPE
    base_qualifies      — included in base QPE (must also be True if conservative is True)
    optimistic_qualifies — included in optimistic QPE
    is_memo_line        — True if this is a memo/informational line (excluded from ALL QPE
                          and from gross spend totals)
    account_code        — XX-00 style code, optional
    description         — human-readable label
    department          — ATL / Production / Post Production / Other
    notes               — free-text rationale for the qualifying flags
    """
    amount_usd: float
    conservative_qualifies: bool
    base_qualifies: bool
    optimistic_qualifies: bool
    is_memo_line: bool = False
    is_marine: bool = False          # vessel/marine cluster flag for reporting
    account_code: Optional[str] = None
    description: str = ""
    department: str = ""
    notes: str = ""


@dataclass
class QPEScenarioResult:
    scenario: str               # "conservative" | "base" | "optimistic"
    qpe_usd: float
    rebate_amounts: dict[float, float]  # rate -> rebate_usd
    qualifying_account_count: int


@dataclass
class FinanceCostEstimate:
    """
    Finance cost on rebate receivable (bridge interest until rebate receipt).

    Not included in QPE.  Reported as a standalone cashflow deduction.
    """
    rebate_usd: float
    delay_weeks: int
    annual_rate: float
    finance_cost_usd: float
    net_after_finance_cost_usd: float


@dataclass
class QPECalculationResult:
    calculator_version: str
    jurisdiction_code: str
    gross_budget_usd: float         # sum of all non-memo accounts
    atl_total_usd: float
    btl_total_usd: float
    post_total_usd: float
    other_total_usd: float
    marine_cluster_usd: float       # sum of accounts flagged is_marine=True
    scenarios: list[QPEScenarioResult]
    finance_cost_estimates: list[FinanceCostEstimate]  # one per rate × scenario combination
    excluded_memo_usd: float        # sum of memo lines (rebate rows, VAT memos, etc.)
    warnings: list[str] = field(default_factory=list)


def calculate_qpe(
    accounts: list[QPEAccount],
    rebate_rates: list[float],
    jurisdiction_code: str = "UNKNOWN",
    finance_cost_delay_weeks: int = 39,
    finance_cost_annual_rate: float = 0.08,
) -> QPECalculationResult:
    """
    Calculate QPE for three scenarios and estimate rebate + finance cost.

    Parameters
    ----------
    accounts              : list of QPEAccount (one per budget account/line)
    rebate_rates          : list of decimal rebate rates to evaluate (e.g. [0.30, 0.35])
    jurisdiction_code     : ISO 3166-1 alpha-2 for labelling
    finance_cost_delay_weeks : weeks from production wrap to rebate receipt
    finance_cost_annual_rate : bridge finance annual interest rate

    Returns
    -------
    QPECalculationResult with per-scenario QPE, rebate amounts, and finance costs.
    """
    warnings: list[str] = []

    # Validate scenario flag ordering: conservative ⊆ base ⊆ optimistic
    for acc in accounts:
        if acc.is_memo_line:
            continue
        if acc.conservative_qualifies and not acc.base_qualifies:
            warnings.append(
                f"Account '{acc.account_code or acc.description}': conservative=True but "
                f"base=False — base must include all conservative items. Correcting base=True."
            )
            acc.base_qualifies = True
        if acc.base_qualifies and not acc.optimistic_qualifies:
            warnings.append(
                f"Account '{acc.account_code or acc.description}': base=True but "
                f"optimistic=False — optimistic must include all base items. Correcting optimistic=True."
            )
            acc.optimistic_qualifies = True

    # Separate memo lines
    non_memo = [a for a in accounts if not a.is_memo_line]
    memo = [a for a in accounts if a.is_memo_line]
    excluded_memo_usd = sum(a.amount_usd for a in memo)

    # Gross budget totals by department
    def _dept_total(dept_keyword: str) -> float:
        return sum(
            a.amount_usd for a in non_memo
            if dept_keyword.lower() in a.department.lower()
        )

    gross_budget_usd = sum(a.amount_usd for a in non_memo)
    atl_total_usd = _dept_total("above the line")
    btl_total_usd = _dept_total("production")
    post_total_usd = _dept_total("post")
    other_total_usd = _dept_total("other")

    marine_cluster_usd = sum(a.amount_usd for a in non_memo if a.is_marine)

    # Build scenario results
    scenario_defs = [
        ("conservative", lambda a: a.conservative_qualifies),
        ("base",         lambda a: a.base_qualifies),
        ("optimistic",   lambda a: a.optimistic_qualifies),
    ]

    scenario_results: list[QPEScenarioResult] = []
    finance_cost_estimates: list[FinanceCostEstimate] = []

    for scenario_name, qualifier in scenario_defs:
        qualifying = [a for a in non_memo if qualifier(a)]
        qpe = sum(a.amount_usd for a in qualifying)

        rebate_amounts: dict[float, float] = {}
        for rate in rebate_rates:
            rebate_usd = qpe * rate
            rebate_amounts[rate] = rebate_usd

            # Finance cost: simple interest on rebate over delay period
            delay_years = finance_cost_delay_weeks / 52.0
            finance_cost = rebate_usd * finance_cost_annual_rate * delay_years
            finance_cost_estimates.append(FinanceCostEstimate(
                rebate_usd=rebate_usd,
                delay_weeks=finance_cost_delay_weeks,
                annual_rate=finance_cost_annual_rate,
                finance_cost_usd=round(finance_cost, 2),
                net_after_finance_cost_usd=round(rebate_usd - finance_cost, 2),
            ))

        scenario_results.append(QPEScenarioResult(
            scenario=scenario_name,
            qpe_usd=round(qpe, 2),
            rebate_amounts={r: round(v, 2) for r, v in rebate_amounts.items()},
            qualifying_account_count=len(qualifying),
        ))

    return QPECalculationResult(
        calculator_version=CALCULATOR_VERSION,
        jurisdiction_code=jurisdiction_code,
        gross_budget_usd=round(gross_budget_usd, 2),
        atl_total_usd=round(atl_total_usd, 2),
        btl_total_usd=round(btl_total_usd, 2),
        post_total_usd=round(post_total_usd, 2),
        other_total_usd=round(other_total_usd, 2),
        marine_cluster_usd=round(marine_cluster_usd, 2),
        scenarios=scenario_results,
        finance_cost_estimates=finance_cost_estimates,
        excluded_memo_usd=round(excluded_memo_usd, 2),
        warnings=warnings,
    )


def get_scenario(result: QPECalculationResult, name: str) -> QPEScenarioResult:
    """Convenience: retrieve a named scenario from a result."""
    for s in result.scenarios:
        if s.scenario == name:
            return s
    raise KeyError(f"Scenario '{name}' not found in result")
