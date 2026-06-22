"""
types.py — Shared dataclasses for the Phase E optimization layer.

All types are pure Python (no SQLAlchemy, no Pydantic). Safe to import
in test environments without a database connection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.data.global_inventory import GlobalProgramEntry

OPTIMIZER_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Confidence penalty rates by tier
# ---------------------------------------------------------------------------
CONFIDENCE_PENALTY: dict[str, float] = {
    "VERIFIED": 0.00,   # source-backed; no discount
    "PARSED": 0.10,     # structurally sound but unverified rate/cap
    "DISCOVERY": 0.25,  # market knowledge only; high uncertainty
}

# ---------------------------------------------------------------------------
# Monetization friction rates
# (fraction of gross incentive value lost to transfer / discount / illiquidity)
# ---------------------------------------------------------------------------
def monetization_friction_rate(
    is_refundable: bool | None,
    is_transferable: bool | None,
) -> float:
    if is_refundable is None or is_transferable is None:
        return 0.05   # unknown — apply moderate friction
    if is_refundable and is_transferable:
        return 0.00   # cash refund, freely assignable — no friction
    if is_refundable:
        return 0.03   # refundable but not freely assignable
    if is_transferable:
        return 0.06   # transferable tax credit — discount for illiquidity
    return 0.12       # non-refundable, non-transferable — theoretical value only


# ---------------------------------------------------------------------------
# Timing penalty rates by program_type
# (fraction of incentive value lost to time-value discounting)
# A rate of 0.02 ≈ one 6-month delay at 4% cost-of-capital
# ---------------------------------------------------------------------------
TIMING_PENALTY_BY_TYPE: dict[str, float] = {
    "tax_credit": 0.02,          # typically 4-8 weeks post-filing
    "cash_rebate": 0.03,         # typically 8-20 weeks
    "regional_fund": 0.04,       # varies widely
    "direct_grant": 0.07,        # competitive, 6-12 month cycle
    "co_production_fund": 0.09,  # 12-18 months decision + disbursement
    "development_fund": 0.10,    # long development timelines
    "discretionary_fund": 0.06,  # semi-annual allocation cycles
}


# ---------------------------------------------------------------------------
# Structure types
# ---------------------------------------------------------------------------

@dataclass
class StructureCandidate:
    """
    A candidate production structure: one or more jurisdictions with
    primary incentives, optional grants, and optional regional funds.
    Not yet filtered for eligibility.
    """
    structure_id: str                          # e.g. "MT:mt_mfc_rebate+EU:eu_eurimages"
    primary_programs: list[GlobalProgramEntry]  # tax_credit / cash_rebate programs
    grant_programs: list[GlobalProgramEntry]    # direct_grant / co_production_fund / development_fund
    regional_programs: list[GlobalProgramEntry] # regional_fund / discretionary_fund
    jurisdiction_codes: list[str]              # union of all involved jurisdiction codes
    structure_type: str = "single"             # "single" | "split" | "grant_stack"
    notes: list[str] = field(default_factory=list)


@dataclass
class StackingViolation:
    program_a_name: str
    program_b_name: str
    rule_type: str   # "prohibited" | "mutually_exclusive" | "spend_reduction" | "conditional"
    condition_text: str
    adjusts_value: bool  # True if this rule changes computed value


@dataclass
class EligibleStructure:
    """
    A candidate structure that has passed eligibility filtering.
    Violations are removed; conditionals and spend-reduction rules are noted.
    """
    candidate: StructureCandidate
    is_eligible: bool
    eligibility_flags: list[str]          # reasons if not eligible
    stacking_violations: list[StackingViolation]       # prohibited / mutually_exclusive
    stacking_conditionals: list[StackingViolation]     # conditional (legal review required)
    spend_reduction_rules: list[StackingViolation]     # spend_reduction (value-adjusting)
    legal_review_required: bool

    # Convenience pass-throughs
    @property
    def primary_programs(self) -> list[GlobalProgramEntry]:
        return self.candidate.primary_programs

    @property
    def grant_programs(self) -> list[GlobalProgramEntry]:
        return self.candidate.grant_programs

    @property
    def regional_programs(self) -> list[GlobalProgramEntry]:
        return self.candidate.regional_programs

    @property
    def structure_id(self) -> str:
        return self.candidate.structure_id

    @property
    def all_programs(self) -> list[GlobalProgramEntry]:
        return (
            self.candidate.primary_programs
            + self.candidate.grant_programs
            + self.candidate.regional_programs
        )


@dataclass
class ValueBreakdown:
    """Economic breakdown for a single program within a scored structure."""
    program_name: str
    jurisdiction_code: str
    program_type: str
    confidence_tier: str
    raw_value_usd: float
    confidence_penalty_usd: float
    friction_penalty_usd: float
    timing_penalty_usd: float
    net_value_usd: float
    notes: list[str] = field(default_factory=list)


@dataclass
class ScoredStructure:
    """
    A structure with full economic scoring applied.
    """
    eligible_structure: EligibleStructure

    # Raw economics
    primary_incentive_raw_usd: float    # base_rate × qualifying_spend
    grant_raw_usd: float                # estimated grant awards
    spend_reduction_usd: float          # grant-reduces-credit penalty
    total_raw_usd: float                # primary + grant - spend_reduction

    # Adjustments
    confidence_penalty_usd: float       # uncertainty discount
    friction_penalty_usd: float         # monetization friction
    timing_penalty_usd: float           # time-value discount

    # Net
    net_producer_benefit_usd: float     # total_raw - all penalties
    effective_rate: float               # net / total_budget
    effective_rate_pct: float           # effective_rate × 100

    # Ranking
    rank: int = 0

    # Metadata
    lowest_confidence_tier: str = "DISCOVERY"
    has_unknowns: bool = False
    unknowns: list[str] = field(default_factory=list)
    value_breakdowns: list[ValueBreakdown] = field(default_factory=list)

    # Convenience
    @property
    def structure_id(self) -> str:
        return self.eligible_structure.structure_id


@dataclass
class StructureExplanation:
    """
    Machine-readable explanation for why a structure ranks where it does.
    Consumable by future UI layers.
    """
    structure_id: str
    rank: int
    summary: str

    # Program lists (human-readable names)
    primary_programs: list[str]
    grant_programs: list[str]
    regional_programs: list[str]

    # Stacking notes
    stacking_notes: list[str]   # why combinations are allowed / conditional

    # Numeric adjustments with reason text
    adjustments: list[dict]     # [{type, amount_usd, reason}]

    # Open questions affecting the score
    unknowns: list[str]

    # Confidence notes
    confidence_notes: list[str]

    # Monetization / financing notes
    monetization_notes: list[str]

    # Full numeric summary
    economics: dict             # keys match ScoredStructure fields


@dataclass
class OptimizationResult:
    """
    Top-level result from run_optimizer().
    """
    jurisdiction_codes: list[str]
    total_budget_usd: float
    qualifying_spend_pct: float
    production_type: str

    structures_enumerated: int
    structures_eligible: int
    structures_ineligible: int

    ranked_structures: list[ScoredStructure]
    explanations: list[StructureExplanation]

    warnings: list[str] = field(default_factory=list)
    optimizer_version: str = OPTIMIZER_VERSION
