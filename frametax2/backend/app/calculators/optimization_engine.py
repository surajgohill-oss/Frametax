"""
optimization_engine.py

Risk-adjusted production optimization engine for CineAtlas.

Consumes a qualification register (qualification_model.py),
StructuringPaths (structuring_paths.py), and GreyAreaItems
(qualification_model.py) and produces four coherent cases:

  CONSERVATIVE   — file today: QUALIFIES accounts + executed, evidence-
                   bound structuring paths + resolved-include grey areas.
  BASE           — the defensible plan: Conservative + approved (not yet
                   executed) structuring paths + counsel-resolved grey
                   areas. Equals Conservative when nothing is approved.
  OPTIMISTIC     — the ceiling: every structuring path structured, every
                   grey area resolved favorably, off-budget in-kind
                   accepted as additive QPE.
  RISK_ADJUSTED  — the ranking metric: Conservative plus confidence-
                   weighted upside from everything not yet realized,
                   net of implementation cost, always clamped inside
                   [Conservative, Optimistic].

Core principle, enforced structurally: unknown must not silently equal
excluded. A GREY_AREA_REQUIRES_AUTHORITY or STRUCTURING_OPPORTUNITY
account is never dropped from a case — it always appears in Optimistic
and Risk-Adjusted, and only leaves Base/Conservative when the caller
proves it belongs there (an approval, or bound evidence).

No LLM calls. All arithmetic is deterministic and testable.
"""
from __future__ import annotations

import copy
import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationConfidence,
    QualificationState,
    get_reinvestment_evidence_request,
)
from app.calculators.structuring_paths import PathStatus, StructuringPath

OPTIMIZATION_ENGINE_VERSION = "1.0.0"


class RiskCase(str, enum.Enum):
    CONSERVATIVE = "conservative"
    BASE = "base"
    OPTIMISTIC = "optimistic"
    RISK_ADJUSTED = "risk_adjusted"


class RiskTolerance(str, enum.Enum):
    """
    Affects ranking/presentation only — never case arithmetic, never an
    approval gate. A CONSERVATIVE tolerance user and an AGGRESSIVE
    tolerance user see identical Conservative/Base/Optimistic/Risk-
    Adjusted dollar figures for the same evidence state.
    """
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


# Canonical confidence -> probability weight mapping used by the
# risk-adjusted case. Documented, global, not per-item invented.
CONFIDENCE_WEIGHTS: dict[QualificationConfidence, float] = {
    QualificationConfidence.HIGH: 0.90,
    QualificationConfidence.MEDIUM: 0.60,
    QualificationConfidence.LOW: 0.25,
    QualificationConfidence.NOT_APPLICABLE: 0.0,
}

# Grey-area weight is capped regardless of confidence: absent authority,
# by policy nothing is more likely than a coin flip.
GREY_AREA_WEIGHT_CAP = 0.50

# Structuring-path recommendation threshold (also the default used by
# structuring_paths.is_recommended).
RECOMMEND_UPSIDE_TO_COST_RATIO = 3.0


@dataclass
class AssumptionOverride:
    """
    An approval or resolution event that moves a StructuringPath or
    GreyAreaItem between lifecycle states. Every override is recorded —
    this is the Production Record entry for the move.
    """
    item_id: str
    item_type: str  # "structuring_path" | "grey_area"
    to_status: str
    approver_role: str  # "producer" | "counsel"
    evidence: Optional[str] = None
    reason: str = ""


@dataclass
class CaseResult:
    case: RiskCase
    qpe_usd: float
    incentive_usd: float
    finance_cost_usd: float
    net_benefit_usd: float
    net_production_cost_usd: float
    included_codes: tuple[str, ...]
    excluded_codes: tuple[str, ...]
    inkind_addon_usd: float = 0.0
    reconciles: bool = True


@dataclass
class OptimizationResult:
    engine_version: str
    jurisdiction_code: str
    rate: float
    gross_budget_usd: float
    cases: dict[RiskCase, CaseResult]
    structuring_paths: list[StructuringPath]
    grey_areas: list[GreyAreaItem]
    evidence_requests: list[str] = field(default_factory=list)
    overrides_applied: list[AssumptionOverride] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _finance_cost(incentive_usd: float, bridge_rate: float, delay_weeks: int) -> float:
    return round(incentive_usd * bridge_rate * (delay_weeks / 52.0), 2)


def _validate_and_apply_override(
    override: AssumptionOverride,
    paths_by_id: dict[str, StructuringPath],
    grey_by_id: dict[str, GreyAreaItem],
) -> None:
    """
    Mutates the copied path/grey-area maps in place after validating the
    approval gate. Raises ValueError on any ungated attempt — this is
    the enforcement point for "counsel-gated moves without evidence are
    rejected."
    """
    if override.item_type == "structuring_path":
        path = paths_by_id.get(override.item_id)
        if path is None:
            raise ValueError(f"Unknown structuring path '{override.item_id}'")
        if override.approver_role not in ("producer", "counsel"):
            raise ValueError(
                f"Structuring path '{override.item_id}' requires producer or counsel "
                f"approval — got '{override.approver_role}'."
            )
        if override.to_status == PathStatus.EXECUTED.value and not override.evidence:
            raise ValueError(
                f"Structuring path '{override.item_id}' cannot be marked EXECUTED "
                "without bound evidence."
            )
        path.status = PathStatus(override.to_status)
        path.evidence_bound = bool(override.evidence) and override.to_status == PathStatus.EXECUTED.value

    elif override.item_type == "grey_area":
        item = grey_by_id.get(override.item_id)
        if item is None:
            raise ValueError(f"Unknown grey area '{override.item_id}'")
        if override.approver_role != "counsel":
            raise ValueError(
                f"Grey area '{override.item_id}' requires counsel approval — "
                f"got '{override.approver_role}'."
            )
        if not override.evidence:
            raise ValueError(
                f"Grey area '{override.item_id}' cannot resolve to {override.to_status} "
                "without bound evidence (a ruling citation) — counsel approval alone "
                "is not sufficient."
            )
        item.status = GreyAreaStatus(override.to_status)
        item.ruling_citation = override.evidence

    else:
        raise ValueError(f"Unknown override item_type '{override.item_type}'")


def build_risk_cases(
    register: list[AccountQualification],
    gross_budget_usd: float,
    rate: float,
    delay_weeks: int = 39,
    bridge_rate: float = 0.08,
    inkind_fmv_usd: float = 0.0,
    structuring_paths: Optional[list[StructuringPath]] = None,
    grey_areas: Optional[list[GreyAreaItem]] = None,
    overrides: Optional[list[AssumptionOverride]] = None,
    risk_tolerance: RiskTolerance = RiskTolerance.BALANCED,
    jurisdiction_code: str = "MU",
) -> OptimizationResult:
    """
    Produce all four risk cases together from a single evidence state.

    risk_tolerance is accepted for future multi-option ranking but does
    not alter any case's arithmetic — see RiskTolerance docstring.
    """
    structuring_paths = copy.deepcopy(structuring_paths or [])
    grey_areas = copy.deepcopy(grey_areas or [])
    overrides = list(overrides or [])

    paths_by_id = {p.path_id: p for p in structuring_paths}
    grey_by_id = {g.item_id: g for g in grey_areas}
    for ov in overrides:
        _validate_and_apply_override(ov, paths_by_id, grey_by_id)

    # ── register partition (source of truth; sums to gross_budget_usd) ──
    qualifies = [a for a in register if a.state == QualificationState.QUALIFIES]
    excluded = [a for a in register if a.state == QualificationState.EXCLUDED]
    not_applicable = [a for a in register if a.state == QualificationState.NOT_APPLICABLE]
    grey_accounts = [a for a in register if a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY]
    structuring_accounts = [a for a in register if a.state == QualificationState.STRUCTURING_OPPORTUNITY]

    base_qpe_total = sum(a.amount_usd for a in qualifies)
    excluded_total = sum(a.amount_usd for a in excluded)
    not_applicable_total = sum(a.amount_usd for a in not_applicable)
    grey_total = sum(a.amount_usd for a in grey_accounts)
    structuring_total = sum(a.amount_usd for a in structuring_accounts)

    register_total = base_qpe_total + excluded_total + not_applicable_total + grey_total + structuring_total
    warnings: list[str] = []
    if abs(register_total - gross_budget_usd) > 0.01:
        warnings.append(
            f"Register total ${register_total:,.2f} does not reconcile to gross budget "
            f"${gross_budget_usd:,.2f} — investigate before trusting any case below."
        )

    on_budget_codes = {a.account_code for a in register}

    def _resolved_include_on_budget(g: GreyAreaItem) -> bool:
        return (not g.off_budget) and g.status == GreyAreaStatus.RESOLVED_INCLUDE

    def _resolved_include_off_budget(g: GreyAreaItem) -> bool:
        return g.off_budget and g.status == GreyAreaStatus.RESOLVED_INCLUDE

    # ── which register accounts move via resolved grey areas ──
    grey_resolved_codes: set[str] = set()
    for g in grey_areas:
        if _resolved_include_on_budget(g):
            grey_resolved_codes.update(c for c in g.account_codes if c in on_budget_codes)
    grey_resolved_amount = sum(
        a.amount_usd for a in grey_accounts if a.account_code in grey_resolved_codes
    )
    grey_offbudget_resolved_amount = sum(
        g.amount_usd for g in grey_areas if _resolved_include_off_budget(g)
    )

    # ── which structuring accounts are executed (evidence-bound) vs approved ──
    executed_codes = {p.account_code for p in structuring_paths if p.status == PathStatus.EXECUTED and p.evidence_bound}
    approved_codes = {
        p.account_code for p in structuring_paths
        if p.status in (PathStatus.APPROVED, PathStatus.EXECUTED)
    }
    executed_amount = sum(a.amount_usd for a in structuring_accounts if a.account_code in executed_codes)
    approved_amount = sum(a.amount_usd for a in structuring_accounts if a.account_code in approved_codes)

    def _make_case(case: RiskCase, qpe_usd: float, included_codes: set[str], inkind_addon: float = 0.0) -> CaseResult:
        incentive = round(qpe_usd * rate, 2)
        finance_cost = _finance_cost(incentive, bridge_rate, delay_weeks)
        net_benefit = round(incentive - finance_cost, 2)
        npc = round(gross_budget_usd - net_benefit, 2)
        excluded_codes = tuple(sorted(a.account_code for a in register if a.account_code not in included_codes))
        # every register dollar remains accounted for regardless of case
        remaining = register_total  # partition never changes, only bucket membership
        reconciles = abs(remaining - gross_budget_usd) <= 0.01
        return CaseResult(
            case=case, qpe_usd=round(qpe_usd, 2), incentive_usd=incentive,
            finance_cost_usd=finance_cost, net_benefit_usd=net_benefit,
            net_production_cost_usd=npc, included_codes=tuple(sorted(included_codes)),
            excluded_codes=excluded_codes, inkind_addon_usd=inkind_addon, reconciles=reconciles,
        )

    # ── CONSERVATIVE ──
    cons_included = {a.account_code for a in qualifies} | executed_codes | grey_resolved_codes
    cons_qpe = base_qpe_total + executed_amount + grey_resolved_amount
    cons_inkind_addon = grey_offbudget_resolved_amount
    conservative = _make_case(RiskCase.CONSERVATIVE, cons_qpe + cons_inkind_addon, cons_included, cons_inkind_addon)

    # ── BASE ── (approved-but-not-executed structuring + counsel-resolved grey; == Conservative if none)
    base_included = {a.account_code for a in qualifies} | approved_codes | grey_resolved_codes
    base_qpe = base_qpe_total + approved_amount + grey_resolved_amount
    base_inkind_addon = grey_offbudget_resolved_amount
    base = _make_case(RiskCase.BASE, base_qpe + base_inkind_addon, base_included, base_inkind_addon)

    # ── OPTIMISTIC ── (everything favorable, in-kind additive)
    opt_included = {a.account_code for a in qualifies} | {a.account_code for a in grey_accounts} | {a.account_code for a in structuring_accounts}
    opt_qpe = base_qpe_total + grey_total + structuring_total
    optimistic = _make_case(RiskCase.OPTIMISTIC, opt_qpe + inkind_fmv_usd, opt_included, inkind_fmv_usd)

    # ── RISK-ADJUSTED ── (Conservative + weighted remaining upside, clamped)
    ra_incentive = conservative.incentive_usd
    for a in grey_accounts:
        if a.account_code in grey_resolved_codes:
            continue
        weight = min(CONFIDENCE_WEIGHTS[a.confidence], GREY_AREA_WEIGHT_CAP)
        ra_incentive += (a.amount_usd * rate) * weight
    for g in grey_areas:
        if g.off_budget and g.status != GreyAreaStatus.RESOLVED_INCLUDE:
            weight = min(0.25, GREY_AREA_WEIGHT_CAP)  # in-kind FMV: UNKNOWN authority, treat as LOW confidence
            ra_incentive += (g.amount_usd * rate) * weight
    for p in structuring_paths:
        if p.status in (PathStatus.EXECUTED, PathStatus.REALIZED) and p.evidence_bound:
            continue  # already inside Conservative's incentive
        weight = CONFIDENCE_WEIGHTS.get(p.confidence, 0.0)
        ra_incentive += (p.upside_incentive_usd * weight) - p.implementation_cost_usd

    ra_incentive = max(conservative.incentive_usd, min(optimistic.incentive_usd, ra_incentive))
    ra_finance_cost = _finance_cost(ra_incentive, bridge_rate, delay_weeks)
    ra_net_benefit = round(ra_incentive - ra_finance_cost, 2)
    ra_npc = round(gross_budget_usd - ra_net_benefit, 2)
    ra_qpe = round(ra_incentive / rate, 2) if rate else 0.0
    risk_adjusted = CaseResult(
        case=RiskCase.RISK_ADJUSTED, qpe_usd=ra_qpe, incentive_usd=round(ra_incentive, 2),
        finance_cost_usd=ra_finance_cost, net_benefit_usd=ra_net_benefit,
        net_production_cost_usd=ra_npc, included_codes=conservative.included_codes,
        excluded_codes=conservative.excluded_codes, inkind_addon_usd=conservative.inkind_addon_usd,
        reconciles=conservative.reconciles,
    )

    # ── reinvestment evidence request (never silently NOT_PERMITTED) ──
    evidence_requests: list[str] = []
    req = get_reinvestment_evidence_request(jurisdiction_code)
    if req:
        evidence_requests.append(req)

    return OptimizationResult(
        engine_version=OPTIMIZATION_ENGINE_VERSION,
        jurisdiction_code=jurisdiction_code,
        rate=rate,
        gross_budget_usd=gross_budget_usd,
        cases={
            RiskCase.CONSERVATIVE: conservative,
            RiskCase.BASE: base,
            RiskCase.OPTIMISTIC: optimistic,
            RiskCase.RISK_ADJUSTED: risk_adjusted,
        },
        structuring_paths=structuring_paths,
        grey_areas=grey_areas,
        evidence_requests=evidence_requests,
        overrides_applied=overrides,
        warnings=warnings,
    )
