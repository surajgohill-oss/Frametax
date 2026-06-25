"""
delta_engine.py

Side-by-side jurisdiction comparison with ROI calculation.

Accepts two ProductionAdjustmentResult objects (one per jurisdiction)
plus incentive values and produces a DeltaResult explaining:
  - gross incentive gain
  - production cost delta
  - travel cost delta
  - net producer benefit
  - ROI of relocation
  - ranked explanation of why one jurisdiction beats the other

No live API calls. No DB access. Pure calculation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.calculators.production_adjustment import (
    AdjustmentCategory,
    AdjustmentMode,
    AdjustmentToggles,
    CrewManifest,
    ProductionAdjustmentInput,
    ProductionAdjustmentResult,
    ProductionBudgetParams,
    calculate_production_adjustment,
)
from app.data.location_cost_benchmarks import get_profile_or_fallback

DELTA_ENGINE_VERSION = "1.0.0"


@dataclass
class JurisdictionIncentive:
    """Incentive value for a single jurisdiction."""
    iso2: str
    gross_incentive_usd: float
    risk_adjusted_incentive_usd: Optional[float] = None  # if available
    incentive_label: str = ""  # e.g. "UK HETV Tax Credit"

    def effective_incentive(self) -> float:
        if self.risk_adjusted_incentive_usd is not None:
            return self.risk_adjusted_incentive_usd
        return self.gross_incentive_usd


@dataclass
class DeltaInput:
    baseline: JurisdictionIncentive
    challenger: JurisdictionIncentive

    home_base_iso2: str = "US"
    home_base_iata: str = "LAX"
    use_jfk_as_secondary: bool = False

    crew: CrewManifest = field(default_factory=CrewManifest)
    budget: ProductionBudgetParams = field(default_factory=ProductionBudgetParams)
    toggles: AdjustmentToggles = field(default_factory=AdjustmentToggles)

    # When the uploaded budget is already scoped to a specific jurisdiction,
    # set this to that jurisdiction's ISO2 so we use EXISTING_BUDGET mode.
    existing_budget_iso2: Optional[str] = None


@dataclass
class ExplanationFactor:
    label: str
    baseline_usd: float
    challenger_usd: float
    delta_usd: float        # positive = challenger is more expensive, negative = cheaper
    impact_direction: str   # "favors_challenger" / "favors_baseline" / "neutral"
    weight: str             # "HIGH" / "MEDIUM" / "LOW"
    notes: str = ""


@dataclass
class DeltaResult:
    delta_engine_version: str

    baseline_iso2: str
    challenger_iso2: str
    home_base_iso2: str
    mode: str

    # Incentive comparison
    baseline_gross_incentive_usd: float
    challenger_gross_incentive_usd: float
    incentive_gain_usd: float          # challenger − baseline (positive = challenger wins on incentive)

    # Production cost comparison
    baseline_production_cost_usd: float
    challenger_production_cost_usd: float
    production_cost_delta_usd: float   # positive = challenger is more expensive

    # Travel / location overhead
    baseline_travel_cost_usd: float
    challenger_travel_cost_usd: float
    travel_delta_usd: float            # positive = challenger travel is more expensive

    # Net calculation
    # net_benefit = incentive_gain − production_cost_delta − travel_delta
    net_producer_benefit_usd: float
    roi: float                          # net_benefit / (production_cost_delta + travel_delta); ∞ if delta ≤ 0

    # Verdict
    winner: str                         # "challenger" / "baseline" / "neutral"
    verdict_summary: str
    confidence: str                     # HIGH / MEDIUM / LOW

    # Excluded adjustments impact
    total_excluded_baseline_usd: float
    total_excluded_challenger_usd: float
    exclusion_warning: str

    # Detailed breakdown
    explanation_factors: list[ExplanationFactor] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _category_total(result: ProductionAdjustmentResult, cat: AdjustmentCategory) -> float:
    return sum(
        it.calculated_amount_usd for it in result.line_items if it.category == cat
    )


def _travel_total(result: ProductionAdjustmentResult) -> float:
    travel_cats = {
        AdjustmentCategory.AIRFARE,
        AdjustmentCategory.HOTEL,
        AdjustmentCategory.PER_DIEM,
        AdjustmentCategory.LOCAL_TRANSPORT,
    }
    return sum(
        it.amount_usd for it in result.line_items if it.category in travel_cats
    )


def _btl_cost_total(result: ProductionAdjustmentResult) -> float:
    btl_cats = {
        AdjustmentCategory.PAYROLL_FRINGE,
        AdjustmentCategory.LEGAL_ACCOUNTING,
        AdjustmentCategory.LOCAL_HIRE_PREMIUM,
        AdjustmentCategory.EQUIPMENT,
        AdjustmentCategory.STAGE_FACILITY,
        AdjustmentCategory.FREIGHT_CARNET,
        AdjustmentCategory.VISA_WORK_PERMIT,
        AdjustmentCategory.CONTINGENCY,
        AdjustmentCategory.FX,
    }
    return sum(
        it.amount_usd for it in result.line_items if it.category in btl_cats
    )


def _build_explanation(
    baseline_result: ProductionAdjustmentResult,
    challenger_result: ProductionAdjustmentResult,
    baseline_incentive: JurisdictionIncentive,
    challenger_incentive: JurisdictionIncentive,
) -> list[ExplanationFactor]:
    factors: list[ExplanationFactor] = []

    # Incentive comparison
    inc_delta = baseline_incentive.effective_incentive() - challenger_incentive.effective_incentive()
    factors.append(ExplanationFactor(
        label="Gross Incentive",
        baseline_usd=baseline_incentive.effective_incentive(),
        challenger_usd=challenger_incentive.effective_incentive(),
        delta_usd=inc_delta,
        impact_direction="favors_challenger" if inc_delta < 0 else ("favors_baseline" if inc_delta > 0 else "neutral"),
        weight="HIGH",
        notes=(
            f"Baseline: {baseline_incentive.incentive_label or baseline_incentive.iso2} "
            f"${baseline_incentive.effective_incentive():,.0f} | "
            f"Challenger: {challenger_incentive.incentive_label or challenger_incentive.iso2} "
            f"${challenger_incentive.effective_incentive():,.0f}"
        ),
    ))

    # Per-category production cost factors
    _FACTOR_DEFS = [
        (AdjustmentCategory.AIRFARE, "Airfare", "HIGH"),
        (AdjustmentCategory.HOTEL, "Hotel Accommodation", "HIGH"),
        (AdjustmentCategory.PER_DIEM, "Per Diem", "HIGH"),
        (AdjustmentCategory.PAYROLL_FRINGE, "Payroll / Fringe", "HIGH"),
        (AdjustmentCategory.EQUIPMENT, "Equipment Rental", "MEDIUM"),
        (AdjustmentCategory.STAGE_FACILITY, "Stage / Facility", "MEDIUM"),
        (AdjustmentCategory.LOCAL_HIRE_PREMIUM, "Local Hire Premium", "MEDIUM"),
        (AdjustmentCategory.FREIGHT_CARNET, "Freight / Carnet", "MEDIUM"),
        (AdjustmentCategory.VISA_WORK_PERMIT, "Visa / Work Permits", "MEDIUM"),
        (AdjustmentCategory.LEGAL_ACCOUNTING, "Legal / Accounting", "LOW"),
        (AdjustmentCategory.LOCAL_TRANSPORT, "Local Transport", "LOW"),
        (AdjustmentCategory.CONTINGENCY, "Contingency Add-on", "LOW"),
        (AdjustmentCategory.FX, "FX Risk", "LOW"),
    ]

    for cat, label, weight in _FACTOR_DEFS:
        b_val = _category_total(baseline_result, cat)
        c_val = _category_total(challenger_result, cat)
        delta = c_val - b_val
        if abs(delta) < 100:
            continue
        direction = (
            "favors_challenger" if delta < 0 else
            "favors_baseline" if delta > 0 else
            "neutral"
        )
        factors.append(ExplanationFactor(
            label=label,
            baseline_usd=b_val,
            challenger_usd=c_val,
            delta_usd=delta,
            impact_direction=direction,
            weight=weight,
            notes=f"Challenger {'costs more' if delta > 0 else 'costs less'}: ${abs(delta):,.0f}",
        ))

    factors.sort(key=lambda f: abs(f.delta_usd), reverse=True)
    return factors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_delta(input_: DeltaInput) -> DeltaResult:
    """
    Compare two jurisdictions across incentive value and production economics.

    When existing_budget_iso2 is set, uses EXISTING_BUDGET mode for both
    calculations so embedded costs are never double-counted.

    Returns:
        DeltaResult with full breakdown, ROI, and explanation factors.
    """
    mode = (
        AdjustmentMode.EXISTING_BUDGET
        if input_.existing_budget_iso2
        else AdjustmentMode.GREENFIELD
    )

    baseline_input = ProductionAdjustmentInput(
        home_base_iso2=input_.home_base_iso2,
        home_base_iata=input_.home_base_iata,
        destination_iso2=input_.baseline.iso2,
        mode=mode,
        existing_budget_iso2=input_.existing_budget_iso2,
        crew=input_.crew,
        budget=input_.budget,
        toggles=input_.toggles,
        use_jfk_as_secondary=input_.use_jfk_as_secondary,
    )

    challenger_input = ProductionAdjustmentInput(
        home_base_iso2=input_.home_base_iso2,
        home_base_iata=input_.home_base_iata,
        destination_iso2=input_.challenger.iso2,
        mode=mode,
        existing_budget_iso2=input_.existing_budget_iso2,
        crew=input_.crew,
        budget=input_.budget,
        toggles=input_.toggles,
        use_jfk_as_secondary=input_.use_jfk_as_secondary,
    )

    baseline_result = calculate_production_adjustment(baseline_input)
    challenger_result = calculate_production_adjustment(challenger_input)

    # Incentive comparison
    incentive_gain = (
        challenger_result.total_adjustment_usd  # not incentive — fix below
    )
    b_incentive = input_.baseline.effective_incentive()
    c_incentive = input_.challenger.effective_incentive()
    incentive_gain = c_incentive - b_incentive

    # Production cost comparison (total active adjustments)
    b_prod_cost = baseline_result.total_adjustment_usd
    c_prod_cost = challenger_result.total_adjustment_usd
    prod_cost_delta = c_prod_cost - b_prod_cost

    # Travel sub-total
    b_travel = _travel_total(baseline_result)
    c_travel = _travel_total(challenger_result)
    travel_delta = c_travel - b_travel

    # Net benefit: incentive gain minus extra costs
    net_benefit = incentive_gain - prod_cost_delta

    # ROI: net_benefit / extra_cost_of_relocation
    extra_cost = max(prod_cost_delta, 0.0)
    roi = (net_benefit / extra_cost) if extra_cost > 1 else float("inf")

    # Verdict
    threshold = 0.0
    if net_benefit > 5000:
        winner = "challenger"
        verdict = (
            f"{input_.challenger.iso2} wins: net producer benefit "
            f"${net_benefit:,.0f} after accounting for production cost differences."
        )
    elif net_benefit < -5000:
        winner = "baseline"
        verdict = (
            f"{input_.baseline.iso2} wins: challenger produces a net COST of "
            f"${abs(net_benefit):,.0f} vs staying with the baseline."
        )
    else:
        winner = "neutral"
        verdict = (
            f"Jurisdictions are economically equivalent within ±$5,000. "
            f"Consider non-financial factors (talent, schedule, creative)."
        )

    # Confidence
    confidences = {baseline_result.confidence, challenger_result.confidence}
    if "LOW" in confidences:
        confidence = "LOW"
    elif "MEDIUM" in confidences:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"

    # Exclusion warnings
    exc_warn = ""
    if baseline_result.total_excluded_usd > 0 or challenger_result.total_excluded_usd > 0:
        exc_warn = (
            f"User exclusions active: baseline excluded ${baseline_result.total_excluded_usd:,.0f}, "
            f"challenger excluded ${challenger_result.total_excluded_usd:,.0f}. "
            f"Net producer benefit excludes these categories. "
            f"Re-enable toggles to see full cost picture."
        )

    # Explanation factors
    explanation = _build_explanation(
        baseline_result, challenger_result,
        input_.baseline, input_.challenger,
    )

    # Combine assumptions
    assumptions = [
        f"Delta engine v{DELTA_ENGINE_VERSION}",
        f"Mode: {mode.value}",
        f"Baseline: {input_.baseline.iso2} incentive ${b_incentive:,.0f}",
        f"Challenger: {input_.challenger.iso2} incentive ${c_incentive:,.0f}",
    ] + baseline_result.assumptions[:3] + ["..."]

    unknowns = baseline_result.unknowns + challenger_result.unknowns

    return DeltaResult(
        delta_engine_version=DELTA_ENGINE_VERSION,
        baseline_iso2=input_.baseline.iso2.upper(),
        challenger_iso2=input_.challenger.iso2.upper(),
        home_base_iso2=input_.home_base_iso2.upper(),
        mode=mode.value,
        baseline_gross_incentive_usd=round(b_incentive, 2),
        challenger_gross_incentive_usd=round(c_incentive, 2),
        incentive_gain_usd=round(incentive_gain, 2),
        baseline_production_cost_usd=round(b_prod_cost, 2),
        challenger_production_cost_usd=round(c_prod_cost, 2),
        production_cost_delta_usd=round(prod_cost_delta, 2),
        baseline_travel_cost_usd=round(b_travel, 2),
        challenger_travel_cost_usd=round(c_travel, 2),
        travel_delta_usd=round(travel_delta, 2),
        net_producer_benefit_usd=round(net_benefit, 2),
        roi=round(roi, 4) if roi != float("inf") else roi,
        winner=winner,
        verdict_summary=verdict,
        confidence=confidence,
        total_excluded_baseline_usd=round(baseline_result.total_excluded_usd, 2),
        total_excluded_challenger_usd=round(challenger_result.total_excluded_usd, 2),
        exclusion_warning=exc_warn,
        explanation_factors=explanation,
        assumptions=assumptions,
        unknowns=unknowns,
    )


def explain_winner(result: DeltaResult, max_factors: int = 5) -> str:
    """
    Return a human-readable narrative explaining the delta result.
    Suitable for displaying in optimizer output or API responses.
    """
    lines: list[str] = []
    lines.append(f"=== Jurisdiction Comparison: {result.baseline_iso2} vs {result.challenger_iso2} ===")
    lines.append(f"Mode: {result.mode}")
    lines.append("")

    lines.append(f"Gross incentive gain ({result.challenger_iso2}): ${result.incentive_gain_usd:+,.0f}")
    lines.append(f"Production cost delta (positive = challenger costs more): ${result.production_cost_delta_usd:+,.0f}")
    lines.append(f"  of which travel: ${result.travel_delta_usd:+,.0f}")
    lines.append(f"Net producer benefit: ${result.net_producer_benefit_usd:+,.0f}")
    if result.roi == float("inf"):
        lines.append("ROI: ∞ (cost savings dominate)")
    else:
        lines.append(f"ROI: {result.roi:.1%}")
    lines.append("")
    lines.append(f"VERDICT: {result.verdict_summary}")
    lines.append(f"Confidence: {result.confidence}")

    if result.exclusion_warning:
        lines.append("")
        lines.append(f"⚠ {result.exclusion_warning}")

    if result.unknowns:
        lines.append("")
        lines.append("Unknowns requiring manual verification:")
        for u in result.unknowns[:3]:
            lines.append(f"  • {u}")

    top_factors = result.explanation_factors[:max_factors]
    if top_factors:
        lines.append("")
        lines.append("Key cost drivers (by impact):")
        for f in top_factors:
            arrow = "→ challenger" if f.impact_direction == "favors_challenger" else "→ baseline" if f.impact_direction == "favors_baseline" else "~"
            lines.append(
                f"  {f.label}: ${f.delta_usd:+,.0f}  [{f.weight}]  {arrow}"
            )

    return "\n".join(lines)
