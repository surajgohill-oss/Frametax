"""
score_structures.py — Economic scoring + explanation engine (Phase E / Phases 3-5).

Phase 3 — Eligibility filter: removes structures with prohibited stacking.
Phase 4 — Economic scoring: computes net producer benefit for each structure.
Phase 5 — Explanation: generates machine-readable reasoning per structure.

Scoring model (no AI, no heuristics that invent data):

  1. PRIMARY INCENTIVE VALUE
     = base_rate × total_budget × qualifying_spend_pct
     Capped at annual_cap_usd if applicable.
     Grants with no base_rate use estimated per-project award (below).

  2. GRANT VALUE (per-project estimate)
     Competitive grant:  min(annual_cap_usd × 0.25, budget × 0.08)
     Formula-based:      min(annual_cap_usd × 0.40, budget × 0.12)
     Unknown cap:        0 (not estimable)

  3. SPEND REDUCTION (government assistance interaction)
     grant_award_estimate × credit_rate of affected program

  4. TOTAL RAW = primary + grant − spend_reduction

  5. CONFIDENCE PENALTY = total_raw × confidence_rate[lowest_tier]

  6. MONETIZATION FRICTION = (raw − confidence_penalty) × friction_rate

  7. TIMING PENALTY = (raw − confidence_penalty) × timing_rate × 0.5 (blended)

  8. NET PRODUCER BENEFIT = raw − confidence − friction − timing

No DB access. No AI calls. Deterministic.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry
from app.optimization.stacking_rules import evaluate_structure_stacking
from app.optimization.types import (
    CONFIDENCE_PENALTY,
    TIMING_PENALTY_BY_TYPE,
    EligibleStructure,
    OptimizationResult,
    ScoredStructure,
    StackingViolation,
    StructureCandidate,
    StructureExplanation,
    ValueBreakdown,
    monetization_friction_rate,
)

_PRIMARY_TYPES = frozenset({"tax_credit", "cash_rebate"})
_GRANT_TYPES = frozenset({
    "direct_grant", "co_production_fund", "development_fund",
})
_COMPETITIVE_GRANT_TYPES = frozenset({"direct_grant", "co_production_fund"})


# ---------------------------------------------------------------------------
# Phase 3 — Eligibility filter
# ---------------------------------------------------------------------------

def filter_structures(
    candidates: list[StructureCandidate],
) -> tuple[list[EligibleStructure], list[EligibleStructure]]:
    """
    Filter candidate structures for eligibility.

    Returns (eligible, ineligible). Structures with only spend_reduction or
    conditional violations are KEPT (eligible) with notes.
    Structures with prohibited/mutually_exclusive violations are KEPT but
    flagged (legal_review_required=True) — caller may choose to include/exclude.
    """
    eligible: list[EligibleStructure] = []
    ineligible: list[EligibleStructure] = []

    for candidate in candidates:
        all_progs = (
            candidate.primary_programs
            + candidate.grant_programs
            + candidate.regional_programs
        )

        violations, conditionals, spend_reductions = evaluate_structure_stacking(all_progs)

        # Structures with no primary programs are ineligible for scoring
        if not candidate.primary_programs and not candidate.grant_programs:
            ineligible.append(EligibleStructure(
                candidate=candidate,
                is_eligible=False,
                eligibility_flags=["No incentive programs in structure."],
                stacking_violations=[],
                stacking_conditionals=[],
                spend_reduction_rules=[],
                legal_review_required=False,
            ))
            continue

        # Mutually exclusive violations: eligible but flagged
        me_violations = [v for v in violations if v.rule_type == "mutually_exclusive"]
        prohibited = [v for v in violations if v.rule_type == "prohibited"]

        es = EligibleStructure(
            candidate=candidate,
            is_eligible=not prohibited,  # prohibited = ineligible
            eligibility_flags=[v.condition_text for v in prohibited],
            stacking_violations=me_violations,
            stacking_conditionals=conditionals,
            spend_reduction_rules=spend_reductions,
            legal_review_required=bool(me_violations or conditionals),
        )

        if prohibited:
            ineligible.append(es)
        else:
            eligible.append(es)

    return eligible, ineligible


# ---------------------------------------------------------------------------
# Phase 4 — Economic scoring
# ---------------------------------------------------------------------------

def _estimate_grant_value(
    grant: GlobalProgramEntry,
    budget_usd: float,
) -> float:
    """
    Estimate per-project grant award for a GlobalProgramEntry grant program.
    Uses annual_cap_usd as a proxy for program scale.
    """
    if grant.annual_cap_usd is None:
        return 0.0   # not estimable without cap data

    # Competitive grants: expect smaller per-project award
    if grant.program_type in _COMPETITIVE_GRANT_TYPES:
        # Typical per-project = 15-25% of program cap, bounded by budget share
        return min(grant.annual_cap_usd * 0.25, budget_usd * 0.08)
    else:
        # Formula / semi-formula: larger expected share
        return min(grant.annual_cap_usd * 0.40, budget_usd * 0.12)


def _compute_spend_reduction(
    spend_reduction_rules: list[StackingViolation],
    grant_values: dict[str, float],  # program_name → grant_value
    primary_programs: list[GlobalProgramEntry],
) -> float:
    """
    Compute total spend reduction amount (the credit LOST due to grant interaction).

    spend_reduction = grant_value × credit_rate_of_affected_program
    """
    total_reduction = 0.0
    for rule in spend_reduction_rules:
        grant_value = grant_values.get(rule.program_a_name, 0.0)
        if grant_value == 0.0:
            grant_value = grant_values.get(rule.program_b_name, 0.0)
        if grant_value == 0.0:
            continue
        # Find the credit program (b_name, typically the tax credit)
        for prog in primary_programs:
            if prog.program_name == rule.program_b_name and prog.base_rate:
                total_reduction += grant_value * prog.base_rate
                break
            if prog.program_name == rule.program_a_name and prog.base_rate:
                total_reduction += grant_value * prog.base_rate
                break
    return total_reduction


def score_structure(
    eligible: EligibleStructure,
    total_budget_usd: float,
    qualifying_spend_pct: float = 0.65,
    split_spend_fractions: dict[str, float] | None = None,
) -> ScoredStructure:
    """
    Compute full economic scoring for a single eligible structure.

    Parameters
    ----------
    eligible              The eligible structure to score
    total_budget_usd      Total production budget in USD
    qualifying_spend_pct  Fraction of budget that qualifies (default 0.65)
    split_spend_fractions {jurisdiction_code: fraction} for split structures
    """
    qualifying_spend = total_budget_usd * qualifying_spend_pct

    unknowns: list[str] = []
    value_breakdowns: list[ValueBreakdown] = []

    # -----------------------------------------------------------------------
    # 1. Primary incentive value
    # -----------------------------------------------------------------------
    primary_incentive_raw = 0.0

    for prog in eligible.primary_programs:
        if prog.base_rate is None:
            unknowns.append(f"{prog.program_name}: base_rate unknown — cannot compute value")
            continue

        # For split structures, each program applies to its jurisdiction's share
        if split_spend_fractions and prog.jurisdiction_code in split_spend_fractions:
            prog_qualifying = qualifying_spend * split_spend_fractions[prog.jurisdiction_code]
        else:
            prog_qualifying = qualifying_spend

        raw = prog_qualifying * prog.base_rate

        # Apply annual cap
        cap_applied = False
        if prog.annual_cap_usd and raw > prog.annual_cap_usd:
            raw = prog.annual_cap_usd
            cap_applied = True

        # Per-program confidence
        prog_conf_rate = CONFIDENCE_PENALTY.get(prog.confidence_tier, 0.25)
        prog_conf_penalty = raw * prog_conf_rate

        # Per-program friction
        prog_friction_rate = monetization_friction_rate(
            prog.is_refundable, prog.is_transferable
        )
        after_conf = raw - prog_conf_penalty
        prog_friction = after_conf * prog_friction_rate

        # Per-program timing
        prog_timing_rate = TIMING_PENALTY_BY_TYPE.get(prog.program_type, 0.04) * 0.5
        prog_timing = after_conf * prog_timing_rate

        prog_net = raw - prog_conf_penalty - prog_friction - prog_timing

        vb_notes: list[str] = []
        if cap_applied:
            vb_notes.append(f"Annual cap applied: ${prog.annual_cap_usd:,.0f}")
        if prog.unknown_fields:
            unknowns.extend([f"{prog.program_name}: {f}" for f in prog.unknown_fields[:3]])
            vb_notes.append(f"Unknown fields: {', '.join(prog.unknown_fields[:3])}")

        value_breakdowns.append(ValueBreakdown(
            program_name=prog.program_name,
            jurisdiction_code=prog.jurisdiction_code,
            program_type=prog.program_type,
            confidence_tier=prog.confidence_tier,
            raw_value_usd=raw,
            confidence_penalty_usd=prog_conf_penalty,
            friction_penalty_usd=prog_friction,
            timing_penalty_usd=prog_timing,
            net_value_usd=prog_net,
            notes=vb_notes,
        ))
        primary_incentive_raw += raw

    # -----------------------------------------------------------------------
    # 2. Grant value (per-project estimates)
    # -----------------------------------------------------------------------
    grant_raw = 0.0
    grant_values_by_name: dict[str, float] = {}

    for prog in eligible.grant_programs + eligible.regional_programs:
        g_val = _estimate_grant_value(prog, total_budget_usd)
        grant_values_by_name[prog.program_name] = g_val

        if g_val == 0.0 and prog.annual_cap_usd is None:
            unknowns.append(
                f"{prog.program_name}: no cap data — grant value not estimable"
            )
            continue

        prog_conf_rate = CONFIDENCE_PENALTY.get(prog.confidence_tier, 0.25)
        prog_conf_penalty = g_val * prog_conf_rate
        prog_timing_rate = TIMING_PENALTY_BY_TYPE.get(prog.program_type, 0.08) * 0.5
        after_conf = g_val - prog_conf_penalty
        prog_timing = after_conf * prog_timing_rate
        prog_net = g_val - prog_conf_penalty - prog_timing

        value_breakdowns.append(ValueBreakdown(
            program_name=prog.program_name,
            jurisdiction_code=prog.jurisdiction_code,
            program_type=prog.program_type,
            confidence_tier=prog.confidence_tier,
            raw_value_usd=g_val,
            confidence_penalty_usd=prog_conf_penalty,
            friction_penalty_usd=0.0,   # grants typically paid as cash
            timing_penalty_usd=prog_timing,
            net_value_usd=prog_net,
            notes=[] if g_val > 0 else ["Grant value not estimable (no cap data)."],
        ))
        grant_raw += g_val

    # -----------------------------------------------------------------------
    # 3. Spend reduction
    # -----------------------------------------------------------------------
    spend_reduction = _compute_spend_reduction(
        eligible.spend_reduction_rules,
        grant_values_by_name,
        eligible.primary_programs,
    )

    # -----------------------------------------------------------------------
    # 4. Total raw and aggregate adjustments
    # -----------------------------------------------------------------------
    total_raw = primary_incentive_raw + grant_raw - spend_reduction

    # Aggregate confidence penalty (based on lowest tier across all programs)
    all_tiers = [p.confidence_tier for p in eligible.all_programs]
    if "DISCOVERY" in all_tiers:
        lowest_tier = "DISCOVERY"
    elif "PARSED" in all_tiers:
        lowest_tier = "PARSED"
    else:
        lowest_tier = "VERIFIED"

    # Use sum of per-program breakdowns for accuracy
    conf_penalty = sum(vb.confidence_penalty_usd for vb in value_breakdowns)
    friction_penalty = sum(vb.friction_penalty_usd for vb in value_breakdowns)
    timing_penalty = sum(vb.timing_penalty_usd for vb in value_breakdowns)

    net = total_raw - conf_penalty - friction_penalty - timing_penalty
    eff_rate = net / total_budget_usd if total_budget_usd > 0 else 0.0

    return ScoredStructure(
        eligible_structure=eligible,
        primary_incentive_raw_usd=primary_incentive_raw,
        grant_raw_usd=grant_raw,
        spend_reduction_usd=spend_reduction,
        total_raw_usd=total_raw,
        confidence_penalty_usd=conf_penalty,
        friction_penalty_usd=friction_penalty,
        timing_penalty_usd=timing_penalty,
        net_producer_benefit_usd=net,
        effective_rate=eff_rate,
        effective_rate_pct=round(eff_rate * 100, 2),
        lowest_confidence_tier=lowest_tier,
        has_unknowns=bool(unknowns),
        unknowns=unknowns,
        value_breakdowns=value_breakdowns,
    )


def score_all_structures(
    eligible_structures: list[EligibleStructure],
    total_budget_usd: float,
    qualifying_spend_pct: float = 0.65,
) -> list[ScoredStructure]:
    """Score and rank all eligible structures."""
    scored = [
        score_structure(es, total_budget_usd, qualifying_spend_pct)
        for es in eligible_structures
    ]

    # Rank by net_producer_benefit descending
    scored_sorted = sorted(
        scored, key=lambda s: s.net_producer_benefit_usd, reverse=True
    )
    for i, s in enumerate(scored_sorted):
        s.rank = i + 1

    return scored_sorted


# ---------------------------------------------------------------------------
# Phase 5 — Explanation engine
# ---------------------------------------------------------------------------

def explain_structure(scored: ScoredStructure) -> StructureExplanation:
    """
    Generate machine-readable explanation for why a structure ranks where it does.
    """
    es = scored.eligible_structure
    c = es.candidate

    # Stacking notes
    stacking_notes: list[str] = []
    for v in es.stacking_violations:
        stacking_notes.append(
            f"MUTUAL_EXCLUSION: {v.program_a_name} and {v.program_b_name} — "
            f"{v.condition_text}"
        )
    for v in es.stacking_conditionals:
        stacking_notes.append(
            f"CONDITIONAL: {v.program_a_name} and {v.program_b_name} — "
            f"legal review required. {v.condition_text}"
        )
    for v in es.spend_reduction_rules:
        stacking_notes.append(
            f"SPEND_REDUCTION: {v.program_a_name} reduces qualifying spend for "
            f"{v.program_b_name}. {v.condition_text}"
        )
    if not stacking_notes:
        stacking_notes.append("All program combinations are ALLOWED — no stacking violations.")

    # Adjustments list
    adjustments: list[dict] = []
    if scored.spend_reduction_usd > 0:
        adjustments.append({
            "type": "spend_reduction",
            "amount_usd": -round(scored.spend_reduction_usd, 2),
            "reason": "Government assistance reduces qualifying spend basis for credit programs.",
        })
    if scored.confidence_penalty_usd > 0:
        adjustments.append({
            "type": "confidence_penalty",
            "amount_usd": -round(scored.confidence_penalty_usd, 2),
            "reason": (
                f"Lowest confidence tier is {scored.lowest_confidence_tier}. "
                f"Discount rate: {CONFIDENCE_PENALTY.get(scored.lowest_confidence_tier, 0.25):.0%}."
            ),
        })
    if scored.friction_penalty_usd > 0:
        adjustments.append({
            "type": "monetization_friction",
            "amount_usd": -round(scored.friction_penalty_usd, 2),
            "reason": "Discount for transfer/liquidity friction on non-cash credit instruments.",
        })
    if scored.timing_penalty_usd > 0:
        adjustments.append({
            "type": "timing_discount",
            "amount_usd": -round(scored.timing_penalty_usd, 2),
            "reason": "Time-value discount for typical processing delays before cash receipt.",
        })

    # Confidence notes
    confidence_notes: list[str] = []
    for prog in es.all_programs:
        tier = prog.confidence_tier
        rate = CONFIDENCE_PENALTY.get(tier, 0.25)
        if tier == "VERIFIED":
            confidence_notes.append(
                f"{prog.program_name}: VERIFIED — no confidence discount."
            )
        elif tier == "PARSED":
            confidence_notes.append(
                f"{prog.program_name}: PARSED — {rate:.0%} discount applied "
                f"(rate confirmed structurally; primary source not independently audited)."
            )
        else:
            confidence_notes.append(
                f"{prog.program_name}: DISCOVERY — {rate:.0%} discount applied "
                f"(market knowledge only; rate and structure unverified)."
            )

    # Monetization notes
    monetization_notes: list[str] = []
    for prog in es.primary_programs:
        if prog.is_refundable:
            monetization_notes.append(
                f"{prog.program_name}: REFUNDABLE — cash receipt expected from tax authority."
            )
        elif prog.is_transferable:
            monetization_notes.append(
                f"{prog.program_name}: TRANSFERABLE — tax credit can be assigned to lender; "
                f"discount for illiquidity applied."
            )
        elif prog.is_refundable is None:
            monetization_notes.append(
                f"{prog.program_name}: UNKNOWN refundability — moderate friction discount applied."
            )
        else:
            monetization_notes.append(
                f"{prog.program_name}: NON-REFUNDABLE, NON-TRANSFERABLE — "
                f"theoretical value; high friction discount applied."
            )

    if es.legal_review_required:
        monetization_notes.append(
            "Legal review required before financing — may affect bridge loan availability."
        )

    # Summary line
    primary_names = [p.program_name for p in c.primary_programs]
    grant_names = [g.program_name for g in c.grant_programs]
    regional_names = [r.program_name for r in c.regional_programs]

    summary_parts = []
    if primary_names:
        summary_parts.append(f"Primary: {', '.join(primary_names)}")
    if grant_names:
        summary_parts.append(f"Grants: {', '.join(grant_names)}")
    if regional_names:
        summary_parts.append(f"Regional: {', '.join(regional_names)}")

    summary = (
        f"Rank #{scored.rank} — Net benefit ${scored.net_producer_benefit_usd:,.0f} "
        f"({scored.effective_rate_pct:.1f}% effective). "
        + " | ".join(summary_parts)
    )

    return StructureExplanation(
        structure_id=scored.structure_id,
        rank=scored.rank,
        summary=summary,
        primary_programs=primary_names,
        grant_programs=grant_names,
        regional_programs=regional_names,
        stacking_notes=stacking_notes,
        adjustments=adjustments,
        unknowns=scored.unknowns,
        confidence_notes=confidence_notes,
        monetization_notes=monetization_notes,
        economics={
            "total_budget_usd": None,  # set by caller
            "primary_incentive_raw_usd": round(scored.primary_incentive_raw_usd, 2),
            "grant_raw_usd": round(scored.grant_raw_usd, 2),
            "spend_reduction_usd": round(scored.spend_reduction_usd, 2),
            "total_raw_usd": round(scored.total_raw_usd, 2),
            "confidence_penalty_usd": round(scored.confidence_penalty_usd, 2),
            "friction_penalty_usd": round(scored.friction_penalty_usd, 2),
            "timing_penalty_usd": round(scored.timing_penalty_usd, 2),
            "net_producer_benefit_usd": round(scored.net_producer_benefit_usd, 2),
            "effective_rate_pct": scored.effective_rate_pct,
            "lowest_confidence_tier": scored.lowest_confidence_tier,
        },
    )
