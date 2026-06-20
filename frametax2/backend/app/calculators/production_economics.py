"""
production_economics.py

Deterministic Production Economics calculator.

Takes a list of ContributionInput (pure dataclass, no ORM) and a gross
budget figure, then computes:

  cash_budget                   — sum of CASH contributions
  contribution_value            — total fair_market_value of all contributions
  effective_production_value    — what it costs to make this film at market rates
                                  (cash_budget + FMV of all non-cash contributions)
  replacement_cost_exposure     — total cost to replace all non-cash contributions
                                  with open-market equivalents
  incentive_qualifying_total    — FMV of contributions that count toward QPE
  normalized_budget_by_jur      — totals grouped by jurisdiction_code
  adjustment_trace              — record of every adjustment and why

No LLM calls.  No database access.  Pure calculation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


CALCULATOR_VERSION = "0.1.0"

NON_CASH_TYPES = frozenset({"deferred", "equity", "in_kind", "sponsorship",
                             "government_support", "vendor_financing"})


@dataclass
class ContributionInput:
    """
    Pure-dataclass representation of one contribution for calculator input.
    Maps 1:1 to ProductionContribution ORM fields but carries no DB state.
    """
    contribution_type: str          # ContributionType.value
    provider: str
    amount: float                   # face / stated value
    fair_market_value: Optional[float] = None   # defaults to amount if None
    replacement_cost: Optional[float] = None    # defaults to fair_market_value if None
    jurisdiction_code: Optional[str] = None
    jurisdiction_specific: bool = False
    qualifies_for_incentive: Optional[bool] = None
    is_conditional: bool = False
    condition_notes: Optional[str] = None
    confidence_tier: str = "PARSED"
    notes: str = ""

    def effective_fmv(self) -> float:
        """Fair market value, falling back to amount if not set."""
        return self.fair_market_value if self.fair_market_value is not None else self.amount

    def effective_replacement_cost(self) -> float:
        """Replacement cost, falling back to FMV if not set."""
        return self.replacement_cost if self.replacement_cost is not None else self.effective_fmv()


@dataclass
class AdjustmentRecord:
    contribution_type: str
    provider: str
    field_adjusted: str
    original_value: float
    adjusted_value: float
    reason: str


@dataclass
class ProductionEconomicsResult:
    calculator_version: str
    gross_budget_usd: float

    # Per-type totals (face value)
    cash_budget: float
    deferred_total: float
    equity_total_fmv: float
    in_kind_total_fmv: float
    sponsorship_total: float
    government_support_total: float
    vendor_financing_total: float

    # Aggregate economics
    contribution_value: float           # sum of all FMVs
    effective_production_value: float   # cash + all non-cash FMV
    replacement_cost_exposure: float    # sum of replacement costs

    # Incentive-qualifying subset
    incentive_qualifying_total: float   # FMV of contributions where qualifies_for_incentive=True
    incentive_qualifying_uncertain: float  # FMV where qualifies_for_incentive=None

    # Budget coverage
    cash_coverage_pct: float            # cash_budget / gross_budget
    total_coverage_pct: float           # effective_production_value / gross_budget
    unfunded_gap_usd: float             # gross_budget - effective_production_value (>0 = underfunded)

    # By jurisdiction
    normalized_budget_by_jurisdiction: dict[str, float]

    # Conditional contributions
    conditional_exposure_usd: float     # FMV of contributions marked is_conditional=True

    # Trace
    adjustment_trace: list[AdjustmentRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def calculate_production_economics(
    contributions: list[ContributionInput],
    gross_budget_usd: float,
) -> ProductionEconomicsResult:
    """
    Compute production economics from a list of contributions and a gross budget.

    Parameters
    ----------
    contributions    : list of ContributionInput (pure dataclass, no ORM)
    gross_budget_usd : gross production budget in USD (from BudgetParseResult or fixture)

    Returns
    -------
    ProductionEconomicsResult with full breakdown and adjustment_trace.
    """
    adjustments: list[AdjustmentRecord] = []
    warnings: list[str] = []

    # Per-type FMV accumulators
    cash_budget = 0.0
    deferred_total = 0.0
    equity_total_fmv = 0.0
    in_kind_total_fmv = 0.0
    sponsorship_total = 0.0
    government_support_total = 0.0
    vendor_financing_total = 0.0

    contribution_value = 0.0
    effective_production_value = 0.0
    replacement_cost_exposure = 0.0
    incentive_qualifying_total = 0.0
    incentive_qualifying_uncertain = 0.0
    conditional_exposure_usd = 0.0

    by_jur: dict[str, float] = {}

    for c in contributions:
        fmv = c.effective_fmv()
        rc = c.effective_replacement_cost()
        ctype = c.contribution_type.lower()

        # Record FMV fallback adjustment
        if c.fair_market_value is None and ctype in NON_CASH_TYPES:
            adjustments.append(AdjustmentRecord(
                contribution_type=ctype,
                provider=c.provider,
                field_adjusted="fair_market_value",
                original_value=0.0,
                adjusted_value=fmv,
                reason="fair_market_value not set; defaulted to amount",
            ))

        if ctype == "cash":
            cash_budget += c.amount
            effective_production_value += c.amount
        elif ctype == "deferred":
            deferred_total += fmv
            effective_production_value += fmv  # deferred work still has market value
        elif ctype == "equity":
            equity_total_fmv += fmv
            effective_production_value += fmv
            if fmv < c.amount:
                adjustments.append(AdjustmentRecord(
                    contribution_type=ctype,
                    provider=c.provider,
                    field_adjusted="equity_discount",
                    original_value=c.amount,
                    adjusted_value=fmv,
                    reason="Equity FMV below face value — risk-adjusted discount applied",
                ))
        elif ctype == "in_kind":
            in_kind_total_fmv += fmv
            effective_production_value += fmv
        elif ctype == "sponsorship":
            sponsorship_total += fmv
            effective_production_value += fmv
        elif ctype == "government_support":
            government_support_total += fmv
            effective_production_value += fmv
        elif ctype == "vendor_financing":
            vendor_financing_total += fmv
            effective_production_value += fmv
        else:
            warnings.append(f"Unknown contribution_type '{ctype}' for provider '{c.provider}' — skipped")
            continue

        contribution_value += fmv
        replacement_cost_exposure += rc

        if c.qualifies_for_incentive is True:
            incentive_qualifying_total += fmv
        elif c.qualifies_for_incentive is None:
            incentive_qualifying_uncertain += fmv
            warnings.append(
                f"{c.provider} ({ctype}): qualifies_for_incentive=None — "
                f"FMV ${fmv:,.2f} excluded from qualifying total but flagged as uncertain"
            )

        if c.is_conditional:
            conditional_exposure_usd += fmv
            adjustments.append(AdjustmentRecord(
                contribution_type=ctype,
                provider=c.provider,
                field_adjusted="conditional_flag",
                original_value=fmv,
                adjusted_value=0.0,
                reason="Contribution is conditional — not guaranteed; reflected in conditional_exposure_usd",
            ))

        if c.jurisdiction_code:
            jur = c.jurisdiction_code.upper()
            by_jur[jur] = by_jur.get(jur, 0.0) + fmv
        else:
            by_jur["UNASSIGNED"] = by_jur.get("UNASSIGNED", 0.0) + fmv

    if gross_budget_usd <= 0:
        warnings.append("gross_budget_usd is zero or negative — coverage ratios undefined")
        cash_coverage_pct = 0.0
        total_coverage_pct = 0.0
    else:
        cash_coverage_pct = cash_budget / gross_budget_usd
        total_coverage_pct = effective_production_value / gross_budget_usd

    unfunded_gap_usd = max(0.0, gross_budget_usd - effective_production_value)
    if unfunded_gap_usd > 0:
        warnings.append(
            f"Unfunded gap: ${unfunded_gap_usd:,.2f} — "
            f"effective_production_value (${effective_production_value:,.2f}) "
            f"< gross_budget_usd (${gross_budget_usd:,.2f})"
        )

    return ProductionEconomicsResult(
        calculator_version=CALCULATOR_VERSION,
        gross_budget_usd=round(gross_budget_usd, 2),
        cash_budget=round(cash_budget, 2),
        deferred_total=round(deferred_total, 2),
        equity_total_fmv=round(equity_total_fmv, 2),
        in_kind_total_fmv=round(in_kind_total_fmv, 2),
        sponsorship_total=round(sponsorship_total, 2),
        government_support_total=round(government_support_total, 2),
        vendor_financing_total=round(vendor_financing_total, 2),
        contribution_value=round(contribution_value, 2),
        effective_production_value=round(effective_production_value, 2),
        replacement_cost_exposure=round(replacement_cost_exposure, 2),
        incentive_qualifying_total=round(incentive_qualifying_total, 2),
        incentive_qualifying_uncertain=round(incentive_qualifying_uncertain, 2),
        cash_coverage_pct=round(cash_coverage_pct, 6),
        total_coverage_pct=round(total_coverage_pct, 6),
        unfunded_gap_usd=round(unfunded_gap_usd, 2),
        normalized_budget_by_jurisdiction={k: round(v, 2) for k, v in by_jur.items()},
        conditional_exposure_usd=round(conditional_exposure_usd, 2),
        adjustment_trace=adjustments,
        warnings=warnings,
    )
