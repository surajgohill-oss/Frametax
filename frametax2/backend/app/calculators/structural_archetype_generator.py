"""
structural_archetype_generator.py

CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION, Task 2.

A single, generic multi-component structure generator/pricer covering all
twelve corrected Codex structural archetypes (CODEX_STRUCTURAL_COMPONENT_
ARCHETYPES.csv) -- national+subnational, principal+post, principal+VFX,
post+VFX, principal+post+VFX across three jurisdictions, treaty-participant
combinations, treaty+component, bilateral/multilateral participants,
formulaic+conditional-fund overlays, selective-upside overlays, and
three-/four-program structures -- with ONE generic mechanism, never a
per-archetype or per-program special case.

A "structure" here is a list of StructuralComponent objects. Each component
is a real, already-allocated slice of the production's own budget (its own
AccountAllocation lines) assigned to exactly one (jurisdiction_code,
program_slug) pair. The generator:

  1. Refuses (never silently permits) any two components that share a
     source budget-line ID -- same-cost double counting is prevented by
     CONSTRUCTION, not by a downstream reduction heuristic.
  2. Enumerates every unordered pair of the structure's program_slugs and
     resolves it through the SAME canonical compatibility system the
     existing same-jurisdiction stacking bridge uses
     (canonical_stack_bridge.load_named_pair_rule /
     economic_block_for_program) -- a single prohibited/mutually-exclusive/
     unresolved-required pair invalidates the WHOLE structure, exactly like
     canonical_stack_bridge.MultiProgramStackResult.contains_blocking_
     incompatibility (904d30e), generalized here to structures whose
     components are NOT required to share one physical jurisdiction.
  3. Prices each component independently via the EXISTING, unmodified
     app.calculators.allocation_pricing.price_segment kernel -- no new
     pricing math is introduced; every dollar is the same number
     price_segment would produce for that component alone.
  4. Separates GUARANTEED (formulaic, non-selective, non-band-ceiling-only)
     value from CONDITIONAL upside (selective/competitive/ceiling-only)
     value at the component level, then sums each axis independently --
     conditional value never inflates guaranteed NPC.
  5. Deduplicates economically identical routes (same canonical component
     set, same jurisdictions/programs/line-id sets) to one canonical
     structure with a deterministic ID.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from itertools import combinations

from app.calculators.allocation_pricing import price_segment, SegmentEconomics
from app.calculators.apply_stacking_adjustments import StackingAdjustment, apply_stacking_adjustments
from app.calculators.canonical_stack_bridge import load_named_pair_rule
from app.calculators.production_allocation import AccountAllocation
from app.data.authority_coverage_registry import economic_block_for_program
from app.data.executable_jurisdiction_registry import _REGISTRY as _DOCTRINE_REGISTRY


def _incentive_type(program_slug: str) -> str:
    rec = _DOCTRINE_REGISTRY.get(program_slug)
    return rec.incentive_type if rec is not None else "tax_credit"


@dataclass(frozen=True)
class StructuralComponent:
    """One real, already-allocated slice of the production's own budget,
    assigned to exactly one (jurisdiction_code, program_slug) pair."""
    component_type: str          # e.g. "principal_production", "post", "vfx",
                                  # "treaty_participant", "fund_overlay",
                                  # "selective_upside"
    jurisdiction_code: str
    program_slug: str
    allocations: tuple[AccountAllocation, ...]
    spend_category_by_code: dict[str, str] = field(default_factory=dict)
    offshore_payroll_accounts: frozenset[str] = frozenset()
    production_type: str = "feature_film"
    evidenced_requirement_facts: frozenset[str] = frozenset()
    amount_facts: dict[str, float] = field(default_factory=dict)

    @property
    def allocated_usd(self) -> float:
        return round(sum(a.amount_usd for a in self.allocations), 2)

    @property
    def line_ids(self) -> frozenset[str]:
        return frozenset(a.line_id for a in self.allocations if a.line_id)


@dataclass(frozen=True)
class PairwiseCheck:
    program_a: str
    program_b: str
    disposition: str            # rule_type, or "UNRESOLVED_NO_AUTHORITY", or "BLOCKED_AUTHORITY"
    condition_text: str | None
    blocks: bool


@dataclass(frozen=True)
class ComponentEconomics:
    component: StructuralComponent
    segment: SegmentEconomics
    is_guaranteed: bool          # a real, non-band-ceiling-only, non-blocked disposition
    guaranteed_incentive_usd: float
    conditional_incentive_usd: float   # 0.0 when is_guaranteed (no separate upside kept)


@dataclass(frozen=True)
class StructuralCandidateResult:
    structure_id: str
    component_types: tuple[str, ...]
    program_slugs: tuple[str, ...]
    jurisdiction_codes: tuple[str, ...]
    executable: bool
    rejection_reason: str | None
    blocking_pairs: tuple[PairwiseCheck, ...]
    component_economics: tuple[ComponentEconomics, ...]
    total_allocated_usd: float
    total_guaranteed_incentive_usd: float
    total_conditional_incentive_usd: float
    gross_budget_usd: float
    npc_usd: float | None            # gross - guaranteed only; None if not executable
    anchor_npc_usd: float | None
    incremental_benefit_vs_anchor_usd: float | None
    materiality_recommended: bool | None   # incremental benefit >= $100,000
    disclosed_limitations: tuple[str, ...] = ()
    # NUM-002 (optimizer audit defect remediation, 2026-09-18): True when
    # ANY component program in this structure carries a real discretionary/
    # competitive-allocation/preapproval disclosure (the same canonical
    # per-program helper the single_country/multi_program/component_
    # relocation families already call) -- a discretionary component
    # propagates risk to the COMPLETE structure, never silently confined
    # to its own segment. administrative_allocation_risk_reasons carries
    # each real, non-duplicate disclosure text, in component order.
    administrative_allocation_risk: bool = False
    administrative_allocation_risk_reasons: tuple[str, ...] = ()
    # NUM-003: full stacking-adjustment reconstruction bridge. raw_
    # component_incentives_usd is each GUARANTEED component's own pre-
    # adjustment incentive (program_slug -> usd); stacking_adjustments is
    # every real ordered adjustment apply_stacking_adjustments() applied
    # (rule identity, base, delta, post-adjustment value), exactly as
    # already computed in generate_structural_candidate() but previously
    # discarded after only its aggregate total was kept; post_adjustment_
    # component_incentives_usd is each guaranteed component's own value
    # AFTER every adjustment. sum(post_adjustment_component_incentives_usd
    # .values()) reconciles exactly to total_guaranteed_incentive_usd.
    raw_component_incentives_usd: dict[str, float] = field(default_factory=dict)
    stacking_adjustments: tuple["StackingAdjustment", ...] = ()
    post_adjustment_component_incentives_usd: dict[str, float] = field(default_factory=dict)


UNRESOLVED_REQUIRED_TYPES = frozenset({"conditional", "prohibited"})
#: Same publishable set canonical_stack_bridge.py's own group-stacking bridge
#: already uses -- kept identical so a program pair is never treated
#: differently by the two mechanisms.
_PUBLISHABLE_RULE_TYPES = frozenset({"allowed", "mutually_exclusive", "spend_reduction"})


def _structure_id(components: list[StructuralComponent]) -> str:
    """Deterministic, order-independent structure ID: a stable hash of the
    canonical (sorted) (jurisdiction_code, program_slug, sorted(line_ids))
    tuple set -- two structures naming the exact same components, in any
    input order, collapse to the SAME ID (deduplication of economically
    identical routes)."""
    canon = sorted(
        (c.jurisdiction_code, c.program_slug, tuple(sorted(c.line_ids)))
        for c in components
    )
    digest = hashlib.sha256(repr(canon).encode()).hexdigest()[:16]
    return f"ARCH-{digest}"


def _same_authority_scope(code_a: str, code_b: str) -> bool:
    """True when two jurisdiction codes share one national authority --
    identical code, or one is the bare country prefix of the other's
    subnational code (e.g. "CA" and "CA-ON"). Mirrors canonical_stack_
    bridge.eligible_for_combination's own same-country test. Two
    genuinely disjoint countries (e.g. "US-GA" and "NZ") are NOT in the
    same authority scope."""
    if code_a == code_b:
        return True
    country_a, country_b = code_a.split("-")[0], code_b.split("-")[0]
    if country_a != country_b:
        return False
    return code_a == country_a or code_b == country_b


def check_all_pairs(components: list["StructuralComponent"]) -> list[PairwiseCheck]:
    """Enumerate every unordered pair and resolve it through the SAME
    canonical compatibility system the existing group-stacking bridge
    uses.

    CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION, Task 2/Locked
    Structural Policy point 2: "allow structurally separate programs
    when the relationship is component composition rather than same-cost
    stacking." CODEX_LEGAL_COMPATIBILITY_ORACLE.csv itself is scoped
    ONLY to SAME_JURISDICTION and NATIONAL_SUBNATIONAL relationship
    classes -- it says nothing about, and was never meant to gate, two
    programs in genuinely disjoint countries with no treaty between them
    (e.g. a principal-photography credit in the US and a post credit in
    New Zealand). For a pair in the SAME authority scope (same
    jurisdiction, or national+subnational of the same country), absence
    of a registered rule is treated as UNRESOLVED_NO_AUTHORITY (blocking)
    -- the same conservative default canonical_stack_bridge.py already
    uses for same-jurisdiction stacking. For a pair in DISJOINT authority
    scopes, absence of a rule means no researched conflict exists and the
    programs are structurally independent by construction (separately
    allocated, non-overlapping budget lines, enforced earlier in
    generate_structural_candidate) -- allowed by default. An EXPLICIT
    registered prohibited/mutually_exclusive rule still blocks regardless
    of jurisdiction scope, since a real, researched conflict was found."""
    checks: list[PairwiseCheck] = []
    by_slug = {c.program_slug: c for c in components}
    for a, b in combinations(sorted(by_slug), 2):
        rule = load_named_pair_rule(a, b)
        if rule is not None:
            rt = rule["rule_type"]
            # "same_cost_prohibited_distinct_costs_allowed" (e.g. ny_state_film
            # + us_ny_post_production_credit, corrected per Codex): this
            # generator ALREADY refuses any two components sharing a
            # source line_id (the same-cost guard runs before this check),
            # so distinct-cost structural composition is safe here by
            # construction -- this disposition is non-blocking at the
            # generic-generator layer, unlike the older same-jurisdiction
            # group-stacking bridge (canonical_stack_bridge.py), which has
            # no distinct-cost awareness and must keep treating it as a
            # hard block.
            if rt == "same_cost_prohibited_distinct_costs_allowed":
                checks.append(PairwiseCheck(a, b, rt, rule.get("condition_text"), blocks=False))
                continue
            blocks = rt not in _PUBLISHABLE_RULE_TYPES or rt == "mutually_exclusive"
            checks.append(PairwiseCheck(a, b, rt, rule.get("condition_text"), blocks=blocks))
            continue
        same_scope = _same_authority_scope(by_slug[a].jurisdiction_code, by_slug[b].jurisdiction_code)
        if same_scope:
            checks.append(PairwiseCheck(a, b, "UNRESOLVED_NO_AUTHORITY", None, blocks=True))
        else:
            checks.append(PairwiseCheck(
                a, b, "DISTINCT_COMPONENT_COMPOSITION",
                "no registered rule and no shared national authority -- structurally "
                "independent components, not a same-cost stacking question",
                blocks=False,
            ))
    return checks


def _price_component(component: StructuralComponent) -> SegmentEconomics:
    # Locked Structural Policy point 10 (application/preapproval/annual
    # allocation/first-come are disclosures, not discretionary vetoes):
    # reuses the SAME established, already-accepted producer-controlled
    # administrative fact set canonical_evaluation.py's own pricing paths
    # union in (never a new or looser policy invented here).
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS

    return price_segment(
        jurisdiction_code=component.jurisdiction_code,
        program_slug=component.program_slug,
        allocations=list(component.allocations),
        spend_category_by_code=component.spend_category_by_code,
        offshore_payroll_accounts=component.offshore_payroll_accounts,
        production_type=component.production_type,
        evidenced_requirement_facts=(
            component.evidenced_requirement_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
        ),
        amount_facts=component.amount_facts,
    )


def generate_structural_candidate(
    components: list[StructuralComponent],
    gross_budget_usd: float,
    anchor_npc_usd: float | None = None,
) -> StructuralCandidateResult:
    """The one generic entry point. Never a per-archetype function --
    every one of the twelve corrected Codex archetypes is just a
    different SHAPE of `components` passed to this same code."""
    structure_id = _structure_id(components)
    component_types = tuple(c.component_type for c in components)
    program_slugs = tuple(c.program_slug for c in components)
    jurisdiction_codes = tuple(c.jurisdiction_code for c in components)

    # 1. Same-cost double-count refusal -- BY CONSTRUCTION, never a
    # downstream heuristic. Locked Structural Policy point 5/6: same
    # costs may never be counted twice; distinct-cost routing is always
    # allowed. Two components sharing a line_id is exactly a same-cost
    # double-claim attempt.
    seen_lines: dict[str, str] = {}
    for c in components:
        for lid in c.line_ids:
            if lid in seen_lines:
                return StructuralCandidateResult(
                    structure_id=structure_id, component_types=component_types,
                    program_slugs=program_slugs, jurisdiction_codes=jurisdiction_codes,
                    executable=False,
                    rejection_reason=(
                        f"budget line {lid!r} is claimed by more than one component "
                        f"({seen_lines[lid]!r} and {c.program_slug!r}) -- the same cost "
                        "may never be counted toward two programs' qualifying spend."
                    ),
                    blocking_pairs=(), component_economics=(),
                    total_allocated_usd=0.0, total_guaranteed_incentive_usd=0.0,
                    total_conditional_incentive_usd=0.0, gross_budget_usd=gross_budget_usd,
                    npc_usd=None, anchor_npc_usd=anchor_npc_usd,
                    incremental_benefit_vs_anchor_usd=None, materiality_recommended=None,
                )
            seen_lines[lid] = c.program_slug

    # 2. Pairwise legality -- every unordered pair, one blocking pair
    # invalidates the WHOLE structure (Locked Structural Policy point 7/8).
    pair_checks = check_all_pairs(components)
    blocking = tuple(p for p in pair_checks if p.blocks)
    if blocking:
        reason = "; ".join(
            f"{p.program_a} + {p.program_b}: {p.disposition}"
            + (f" ({p.condition_text})" if p.condition_text else "")
            for p in blocking
        )
        return StructuralCandidateResult(
            structure_id=structure_id, component_types=component_types,
            program_slugs=program_slugs, jurisdiction_codes=jurisdiction_codes,
            executable=False,
            rejection_reason=f"blocked by {len(blocking)} pairwise incompatibility(ies): {reason}",
            blocking_pairs=blocking, component_economics=(),
            total_allocated_usd=round(sum(c.allocated_usd for c in components), 2),
            total_guaranteed_incentive_usd=0.0, total_conditional_incentive_usd=0.0,
            gross_budget_usd=gross_budget_usd, npc_usd=None, anchor_npc_usd=anchor_npc_usd,
            incremental_benefit_vs_anchor_usd=None, materiality_recommended=None,
        )

    # 3. Price every component independently via the EXISTING kernel.
    #
    # A component explicitly labeled "selective_upside" or "fund_overlay"
    # (a genuinely competitive/negotiated award, e.g. us_tn_performance_
    # grant, ca_sk_creative_saskatchewan_grant) is EXPECTED to sometimes
    # fail to resolve any rate at all (FAIL_CLOSED at the B4 authority
    # gate) -- Locked Structural Policy point 9 requires such support to
    # remain conditional upside, never to block an otherwise-valid
    # structure built from real, formulaic components. It contributes
    # $0/$0, disclosed, rather than invalidating the whole structure. Any
    # OTHER component type failing its own real threshold IS a genuine
    # structure-invalidating rejection (Task 3: "If a program ultimately
    # fails a real threshold, persist a precise rejection").
    comp_econ: list[ComponentEconomics] = []
    selective_zero_notes: list[str] = []
    for c in components:
        seg = _price_component(c)
        if not seg.executable:
            if c.component_type in ("selective_upside", "fund_overlay"):
                selective_zero_notes.append(
                    f"{c.jurisdiction_code}/{c.program_slug} (selective/negotiated) did not "
                    f"resolve a rate: {'; '.join(seg.blockers) if seg.blockers else 'no incentive resolved'} "
                    "-- contributes $0/$0, disclosed, does not block the rest of the structure."
                )
                comp_econ.append(ComponentEconomics(
                    component=c, segment=seg, is_guaranteed=False,
                    guaranteed_incentive_usd=0.0, conditional_incentive_usd=0.0,
                ))
                continue
            return StructuralCandidateResult(
                structure_id=structure_id, component_types=component_types,
                program_slugs=program_slugs, jurisdiction_codes=jurisdiction_codes,
                executable=False,
                rejection_reason=(
                    f"{c.jurisdiction_code}/{c.program_slug} did not clear its own real "
                    f"threshold: {'; '.join(seg.blockers) if seg.blockers else 'no incentive resolved'}"
                ),
                blocking_pairs=(), component_economics=(),
                total_allocated_usd=round(sum(x.allocated_usd for x in components), 2),
                total_guaranteed_incentive_usd=0.0, total_conditional_incentive_usd=0.0,
                gross_budget_usd=gross_budget_usd, npc_usd=None, anchor_npc_usd=anchor_npc_usd,
                incremental_benefit_vs_anchor_usd=None, materiality_recommended=None,
            )
        # Locked Structural Policy point 9/14: a band-ceiling-only
        # resolution (no guaranteed floor) or a program the coverage
        # registry marks non-guaranteed is CONDITIONAL upside, never
        # guaranteed NPC -- the SAME distinction canonical_evaluation.py's
        # single-program path already applies.
        is_ceiling_only = seg.is_band_ceiling and seg.incentive_floor_usd <= 0.0 < seg.incentive_ceiling_usd
        is_guaranteed = not is_ceiling_only
        guaranteed = seg.incentive_floor_usd if is_guaranteed else 0.0
        conditional = 0.0 if is_guaranteed else seg.incentive_ceiling_usd
        comp_econ.append(ComponentEconomics(
            component=c, segment=seg, is_guaranteed=is_guaranteed,
            guaranteed_incentive_usd=guaranteed, conditional_incentive_usd=conditional,
        ))

    total_allocated = round(sum(ce.segment.allocated_usd for ce in comp_econ), 2)

    # 4. Cross-component spend_reduction adjustments -- reuses the SAME,
    # already-tested apply_stacking_adjustments engine canonical_stack_
    # bridge.py's same-jurisdiction group stacking already uses, applied
    # ONLY across the GUARANTEED components (Locked Structural Policy
    # point 9: conditional value never enters guaranteed NPC, so it is
    # never passed into this adjustment pass at all).
    guaranteed_econ = [ce for ce in comp_econ if ce.is_guaranteed]
    guaranteed_rules = [
        r for a, b in combinations(sorted({ce.component.program_slug for ce in guaranteed_econ}), 2)
        if (r := load_named_pair_rule(a, b)) is not None and r["rule_type"] in _PUBLISHABLE_RULE_TYPES
    ]
    disclosed_limitations: list[str] = []
    # NUM-003: raw (pre-adjustment) per-program guaranteed incentive --
    # always available regardless of whether any adjustment rule fires,
    # so a structure with zero adjustments still reconstructs (raw ==
    # post-adjustment == total_guaranteed_incentive_usd trivially).
    raw_component_incentives_usd: dict[str, float] = {
        ce.component.program_slug: round(ce.guaranteed_incentive_usd, 2) for ce in guaranteed_econ
    }
    stacking_adjustments: tuple[StackingAdjustment, ...] = ()
    post_adjustment_component_incentives_usd: dict[str, float] = dict(raw_component_incentives_usd)
    if guaranteed_econ and guaranteed_rules:
        adj = apply_stacking_adjustments(
            [
                {
                    "program_id": ce.component.program_slug,
                    "economic_value_usd": ce.guaranteed_incentive_usd,
                    "effective_rate": (
                        ce.segment.rate_floor if ce.segment.rate_floor is not None else 0.0
                    ),
                    "program_type": _incentive_type(ce.component.program_slug),
                    "qualifying_spend_usd": ce.segment.qpe_usd,
                }
                for ce in guaranteed_econ
            ],
            guaranteed_rules,
        )
        total_guaranteed = round(adj.total_adjusted_value_usd, 2)
        # NUM-003: persist the FULL bridge, not just the aggregate total --
        # adj already carries every real ordered adjustment (rule
        # identity, base, delta, post-adjustment value); previously
        # discarded here once total_guaranteed was extracted.
        stacking_adjustments = tuple(adj.adjustments)
        post_adjustment_component_incentives_usd = {
            pid: round(v, 2) for pid, v in adj.program_values.items()
        }
        # Same disclosure canonical_stack_bridge._build_group_result already
        # makes for the identical, pre-existing limitation: the reused
        # apply_stacking_adjustments spend_reduction heuristic only
        # recognizes a grant/regional_fund/discretionary_fund program_type
        # as the reducing side -- a real statutory reduction between two
        # tax-credit-typed programs (e.g. on_ofttc+ocase, ca_federal_cptc+
        # on_ofttc) is not applied, and must be disclosed rather than
        # silently served as though it were.
        for rule in guaranteed_rules:
            if rule["rule_type"] != "spend_reduction":
                continue
            pair_ids = {rule["program_a_id"], rule["program_b_id"]}
            matched = any({a.program_a_id, a.program_b_id} == pair_ids for a in adj.adjustments)
            if not matched:
                disclosed_limitations.append(
                    f"Statutory rule found ({rule['condition_text']}) but the reused "
                    "spend_reduction calculator only recognizes grant/regional_fund/"
                    f"discretionary_fund program types as the reducing side; neither "
                    f"{rule['program_a_id']} nor {rule['program_b_id']} is typed that way, "
                    "so no reduction was applied for this pair. This structure's "
                    "guaranteed total is therefore NOT confirmed net of this statutory "
                    "deduction -- legal/economic review required before treating it as "
                    "fully verified."
                )
    else:
        total_guaranteed = round(sum(ce.guaranteed_incentive_usd for ce in guaranteed_econ), 2)
    total_conditional = round(sum(ce.conditional_incentive_usd for ce in comp_econ), 2)
    npc = round(gross_budget_usd - total_guaranteed, 2)
    incremental = round(anchor_npc_usd - npc, 2) if anchor_npc_usd is not None else None
    materiality = (incremental is not None and incremental >= 100_000.0)

    # NUM-002: derived from EVERY component program (not just guaranteed
    # ones -- a selective_upside/fund_overlay component contributing $0/$0
    # is itself the discretionary risk this exists to disclose), via the
    # SAME canonical per-program helper the single_country/multi_program/
    # component_relocation families already call -- never a hybrid-only
    # re-derivation. Lazy import: structural_archetype_generator.py is
    # itself imported lazily by canonical_evaluation.py (no module-level
    # cycle to begin with), so this stays a plain function-local import.
    from app.services.canonical_evaluation import _competitive_allocation_disclosure
    _admin_risk_reasons: list[str] = []
    for ce in comp_econ:
        _disclosure = _competitive_allocation_disclosure(ce.component.program_slug)
        if _disclosure and _disclosure not in _admin_risk_reasons:
            _admin_risk_reasons.append(_disclosure)

    return StructuralCandidateResult(
        structure_id=structure_id, component_types=component_types,
        program_slugs=program_slugs, jurisdiction_codes=jurisdiction_codes,
        executable=True, rejection_reason=None, blocking_pairs=(),
        component_economics=tuple(comp_econ),
        total_allocated_usd=total_allocated,
        total_guaranteed_incentive_usd=total_guaranteed,
        total_conditional_incentive_usd=total_conditional,
        gross_budget_usd=gross_budget_usd, npc_usd=npc, anchor_npc_usd=anchor_npc_usd,
        incremental_benefit_vs_anchor_usd=incremental, materiality_recommended=materiality,
        disclosed_limitations=tuple(selective_zero_notes) + tuple(disclosed_limitations),
        administrative_allocation_risk=bool(_admin_risk_reasons),
        administrative_allocation_risk_reasons=tuple(_admin_risk_reasons),
        raw_component_incentives_usd=raw_component_incentives_usd,
        stacking_adjustments=stacking_adjustments,
        post_adjustment_component_incentives_usd=post_adjustment_component_incentives_usd,
    )
