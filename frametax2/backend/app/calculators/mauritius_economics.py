"""
mauritius_economics.py

Deterministic, fully-explainable Mauritius production-economics results.
This is the headline financial output (Mauritius Qualification Closeout +
Production-Economics Controls phase, Part 4): THREE distinct, separated
results —

  1. VERIFIED / FLOOR CASE  (30% statutory floor, verified cash QPE)
  2. POTENTIAL 40% CASE     (40% ceiling, clearly conditional + conditions)
  3. IN-KIND POST OPTIONS   (accepted-as-QPE / not-accepted / lost-or-moved)

— NOT a single blended or "risk-adjusted" headline. Conservative / Base /
Optimistic / Risk-Adjusted are deliberately absent here; they remain an
internal optimizer-ranking heuristic only (optimization_engine.py), never
a headline financial concept.

Nothing here touches the optimizer, the qualification register, or the
statutory rules. It is a pure function of:
  - gross cash budget (authoritative, from the parsed budget)
  - verified cash QPE (the register's QUALIFIES sum)
  - the statutory rate range (floor / ceiling, from program_rate_rules)
  - a FinancingModel (default ZERO — never a silent 8%/39wk assumption)
  - an InKindPostModel (user-controllable production fact, not a hardcoded
    optimistic additive)

Every dollar is explainable: each result carries its substituted formula
strings and the authority status of its rate.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass


# ── Financing controls (Part 2) ──────────────────────────────────────────────

class FinancingSource(str, enum.Enum):
    DEFAULT_ZERO = "default_zero"      # no financing assumed — the default
    USER_INPUT = "user_input"          # producer supplied the inputs
    DOCUMENT_INPUT = "document_input"   # parsed from an uploaded financing doc


class FinancingMethod(str, enum.Enum):
    NONE = "none"
    RATE_TIME = "rate_time"            # annual rate x period x financed amount
    HARD_COST = "hard_cost"           # a flat financing/discount/monetization cost


@dataclass(frozen=True)
class FinancingModel:
    """How the incentive-receivable financing cost is computed. Financing is
    NEVER part of QPE — it affects only net benefit / NPC. Defaults to ZERO;
    a non-zero cost requires explicit user (or document) inputs."""
    source: FinancingSource = FinancingSource.DEFAULT_ZERO
    method: FinancingMethod = FinancingMethod.NONE
    annual_rate: float | None = None            # e.g. 0.08 for 8%/yr
    weeks: int | None = None                    # financing period
    financed_amount_pct: float | None = None    # fraction of the incentive financed (default 1.0)
    hard_cost_usd: float | None = None          # flat cost for HARD_COST method

    def cost(self, incentive_usd: float) -> float:
        if self.method == FinancingMethod.HARD_COST:
            return round(self.hard_cost_usd or 0.0, 2)
        if self.method == FinancingMethod.RATE_TIME:
            rate = self.annual_rate or 0.0
            weeks = self.weeks or 0
            pct = self.financed_amount_pct if self.financed_amount_pct is not None else 1.0
            return round(incentive_usd * pct * rate * (weeks / 52.0), 2)
        return 0.0

    def formula(self, incentive_usd: float) -> str:
        if self.method == FinancingMethod.HARD_COST:
            return f"Financing cost = user hard cost = ${(self.hard_cost_usd or 0.0):,.2f}"
        if self.method == FinancingMethod.RATE_TIME:
            pct = self.financed_amount_pct if self.financed_amount_pct is not None else 1.0
            return (
                f"Financing cost = incentive ${incentive_usd:,.2f} × financed {pct:.0%} × "
                f"annual rate {(self.annual_rate or 0.0):.2%} × ({self.weeks or 0}/52 weeks) "
                f"= ${self.cost(incentive_usd):,.2f}"
            )
        return "Financing cost = $0.00 (no financing assumed — default zero, no user input)"


# ── In-kind post controls (Part 3) ───────────────────────────────────────────

class InKindAcceptance(str, enum.Enum):
    UNKNOWN = "unknown"
    YES = "yes"
    NO = "no"


class PostLocation(str, enum.Enum):
    MAURITIUS = "mauritius"
    ELSEWHERE = "elsewhere"


@dataclass(frozen=True)
class InKindPostModel:
    """The $625,000 in-kind post-production support as a USER-CONTROLLABLE
    production fact — never a hardcoded optimistic additive."""
    available: bool = True
    fmv_usd: float = 625_000.0
    jurisdiction: str = "MU"
    accepted_as_qpe: InKindAcceptance = InKindAcceptance.UNKNOWN
    replacement_post_cost_if_lost_usd: float = 625_000.0
    post_location: PostLocation = PostLocation.MAURITIUS


# ── Result shape ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EconomicsResult:
    label: str
    gross_cash_budget_usd: float
    off_budget_inkind_usd: float          # in-kind FMV, always shown SEPARATELY from cash
    qpe_usd: float
    incentive_rate: float
    rate_authority_status: str            # VERIFIED_FLOOR | CONDITIONAL_CEILING | USER_ELECTED_*
    incentive_usd: float
    financing_cost_usd: float
    financing_source: str
    financing_formula: str
    net_benefit_usd: float                # incentive − financing (financing never in QPE)
    net_production_cost_usd: float        # gross cash − net benefit (CASH only)
    economic_production_value_usd: float  # cash NPC − non-cash in-kind benefit (true economic cost)
    conditions: tuple[str, ...] = ()      # unmet evidence/approval conditions (e.g. for 40%)
    notes: str = ""


MAURITIUS_ECONOMICS_VERSION = "1.0.0"


def _result(
    label: str,
    gross_cash: float,
    inkind_offbudget: float,
    qpe: float,
    rate: float,
    rate_status: str,
    financing: FinancingModel,
    inkind_noncash_benefit: float,
    conditions: tuple[str, ...] = (),
    notes: str = "",
    inkind_incremental_incentive: float = 0.0,
) -> EconomicsResult:
    incentive = round(qpe * rate, 2) + round(inkind_incremental_incentive, 2)
    financing_cost = financing.cost(incentive)
    net_benefit = round(incentive - financing_cost, 2)
    npc = round(gross_cash - net_benefit, 2)
    # Economic production value: the true cost of getting the film made,
    # crediting the non-cash in-kind benefit the production receives for
    # free. Always kept separate from the cash NPC above.
    econ_value = round(npc - inkind_noncash_benefit, 2)
    return EconomicsResult(
        label=label,
        gross_cash_budget_usd=round(gross_cash, 2),
        off_budget_inkind_usd=round(inkind_offbudget, 2),
        qpe_usd=round(qpe, 2),
        incentive_rate=rate,
        rate_authority_status=rate_status,
        incentive_usd=incentive,
        financing_cost_usd=financing_cost,
        financing_source=financing.source.value,
        financing_formula=financing.formula(incentive),
        net_benefit_usd=net_benefit,
        net_production_cost_usd=npc,
        economic_production_value_usd=econ_value,
        conditions=conditions,
        notes=notes,
    )


# Exact unmet conditions the production must satisfy to establish the 40%
# ceiling (Part 1). Discretionary until met — never asserted as certain.
FORTY_PERCENT_CONDITIONS: tuple[str, ...] = (
    "Feature film production type — SATISFIED (production fact).",
    "Minimum QPE of USD 1,000,000 — SATISFIED (verified QPE far exceeds it).",
    "'Up to 40%' is a discretionary band: the awarded rate is set by the "
    "Film Rebate Committee assessment and CEO approval — NOT pre-determinable; "
    "30% is the guaranteed floor.",
    "No sponsorship / financial assistance included in the QPE quantum — "
    "unverified production fact (nothing recorded, but absence is not proof).",
    "Locally incorporated/registered production entity (SPV) — assumed under "
    "the production-structure default; incorporation evidence still required.",
    "Producer 5-year track record — unverified production fact.",
    "Secondary-sourced '90% of filming in Mauritius' claim — NOT found in any "
    "government text; requires EDB written confirmation before it can be "
    "treated as a condition either way.",
)


def compute_mauritius_economics(
    gross_cash_budget_usd: float,
    verified_cash_qpe_usd: float,
    rate_floor: float,
    rate_ceiling: float,
    financing: FinancingModel,
    inkind: InKindPostModel,
    awarded_rate: float | None = None,
) -> dict[str, object]:
    """Produce the three separated headline results. Deterministic; every
    figure carries its formula. See module docstring.

    `awarded_rate` (optional): a user-elected rate within [floor, ceiling]
    for cashflow modeling. When supplied it drives a fourth, clearly-labeled
    USER_ELECTED result; it never replaces the honest floor/ceiling pair.
    """
    # In-kind is ALWAYS off-budget and shown separately from cash QPE. It
    # never silently inflates cash QPE.
    inkind_offbudget = inkind.fmv_usd if inkind.available else 0.0

    # 1. VERIFIED / FLOOR CASE — 30% statutory floor on verified cash QPE.
    floor = _result(
        "verified_floor_30", gross_cash_budget_usd, inkind_offbudget,
        verified_cash_qpe_usd, rate_floor, "VERIFIED_FLOOR", financing,
        inkind_noncash_benefit=0.0,
        notes="30% is the guaranteed statutory floor — awarded regardless of "
              "the discretionary band. Verified cash QPE only; in-kind shown "
              "separately, not in this QPE.",
    )

    # 2. POTENTIAL 40% CASE — same verified QPE, 40% ceiling, conditional.
    ceiling = _result(
        "potential_ceiling_40", gross_cash_budget_usd, inkind_offbudget,
        verified_cash_qpe_usd, rate_ceiling, "CONDITIONAL_CEILING", financing,
        inkind_noncash_benefit=0.0,
        conditions=FORTY_PERCENT_CONDITIONS,
        notes="40% is the DISCRETIONARY ceiling of the 'up to 40%' band — "
              "conditional on the items listed. Not certain; do not rely on "
              "it for committed cashflow without EDB award confirmation.",
    )

    # 3. IN-KIND POST OPTIONS (Part 3). Compared on the honest, guaranteed
    #    floor-rate footing; the ceiling applies identically if awarded.
    base_rate = rate_floor

    # A — accepted as QPE: $625k stays OFF the cash budget; potential
    #     incremental incentive shown SEPARATELY; not added to cash cost.
    inkind_accepted = _result(
        "inkind_accepted_as_qpe", gross_cash_budget_usd, inkind_offbudget,
        verified_cash_qpe_usd, base_rate, "VERIFIED_FLOOR", financing,
        inkind_noncash_benefit=inkind_offbudget,
        inkind_incremental_incentive=(inkind_offbudget * base_rate) if inkind.available else 0.0,
        notes=(
            "In-kind FMV ${:,.0f} accepted as additive QPE (post performed in "
            "Mauritius). Kept OFF the cash budget; the incremental incentive "
            "(FMV × rate = ${:,.2f}) is part of net benefit, but the FMV is NOT "
            "added to cash cost. Requires: FMV evidence, invoice/documentation, "
            "local incurrence, related-party treatment, and EDB acceptance."
            .format(inkind_offbudget, inkind_offbudget * base_rate)
        ) if inkind.available else "No in-kind support available.",
    )

    # B — not accepted as QPE: off cash budget, no incentive on it, but the
    #     $625k economic contribution is preserved as a non-cash benefit.
    inkind_rejected = _result(
        "inkind_not_accepted_as_qpe", gross_cash_budget_usd, inkind_offbudget,
        verified_cash_qpe_usd, base_rate, "VERIFIED_FLOOR", financing,
        inkind_noncash_benefit=inkind_offbudget,
        notes="In-kind FMV kept off the cash budget; no incentive earned on it, "
              "but the ${:,.0f} non-cash economic contribution is preserved "
              "(lowers economic production value, not cash NPC).".format(inkind_offbudget)
        if inkind.available else "No in-kind support available.",
    )

    # C — lost / post moved outside Mauritius: the $625k becomes REAL cash
    #     replacement post cost, added to the cash budget; performed outside
    #     MU so it does not qualify (territorial); no non-cash benefit.
    replacement = inkind.replacement_post_cost_if_lost_usd
    inkind_lost = _result(
        "inkind_lost_post_moved", gross_cash_budget_usd + replacement, 0.0,
        verified_cash_qpe_usd, base_rate, "VERIFIED_FLOOR", financing,
        inkind_noncash_benefit=0.0,
        notes="In-kind support lost / post moved outside Mauritius: ${:,.0f} "
              "added to the CASH budget as replacement post cost. Performed "
              "outside MU, so it does not qualify (territorial); MU QPE "
              "unchanged. This is the cost of losing the in-kind support "
              "(cash NPC rises by the replacement).".format(replacement),
    )

    out: dict[str, object] = {
        "version": MAURITIUS_ECONOMICS_VERSION,
        "verified_floor_case": floor,
        "potential_ceiling_case": ceiling,
        "inkind_post_options": {
            "accepted_as_qpe": inkind_accepted,
            "not_accepted_as_qpe": inkind_rejected,
            "lost_or_moved_outside_mu": inkind_lost,
        },
        "inkind_model": inkind,
        "financing_model": financing,
    }

    if awarded_rate is not None:
        status = (
            "USER_ELECTED_FLOOR" if abs(awarded_rate - rate_floor) < 1e-9 else
            "USER_ELECTED_CEILING" if abs(awarded_rate - rate_ceiling) < 1e-9 else
            "USER_ELECTED_INTERMEDIATE"
        )
        out["user_elected_case"] = _result(
            "user_elected", gross_cash_budget_usd, inkind_offbudget,
            verified_cash_qpe_usd, awarded_rate, status, financing,
            inkind_noncash_benefit=0.0,
            notes=f"User-elected rate {awarded_rate:.0%} for cashflow modeling. "
                  "Authority status shown; this is a modeling election, not an "
                  "EDB award. The honest floor (30%) and conditional ceiling "
                  "(40%) results remain the primary outputs.",
        )

    return out
