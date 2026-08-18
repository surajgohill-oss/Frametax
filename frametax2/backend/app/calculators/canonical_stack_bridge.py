"""
canonical_stack_bridge.py

Canonical multi-program stack-pricing bridge — Existing Optimizer/Stacker
Reconnection (see docs/validation/CODEX_EXISTING_OPTIMIZER_LINEAGE_TRACE.md).

Reuses the EXISTING, engine-agnostic stacking calculators
(apply_stacking_adjustments.py, evaluate_legal_stacking.py) against
CURRENT canonical per-program pricing (produced by
canonical_evaluation._price_candidate / allocation_pricing.
price_allocated_structure), instead of the superseded run_full_analysis
(ENGINE_VERSION 0.1.0) path that generate_structure_scenarios.py's
combinatorics currently depend on. No pricing formula is duplicated here
— every incentive value consumed below was already computed by the same
canonical pricing kernel every single-program candidate uses.

Scope, deliberately conservative for this pass: PAIRWISE combinations
only (exactly two programs sharing one jurisdiction — "Multiple programs
in one jurisdiction" / "Federal + provincial/state" from the lineage
trace). Every program in a pair is already independently allocated 100%
to that one jurisdiction (single_country/full_relocation structures never
split accounts across jurisdictions), so combining them requires no new
account allocation — only combining already-computed incentive values
under the existing stacking rule engine.

Rule loading is intentionally conservative: only pairs with an EXPLICIT
named entry in app.optimization.stacking_rules._SLUG_PAIR_RULES are
consulted. That table's own evaluate_pair() step 4 default-allows any
unmatched pair for the legacy app.optimization.optimizer consumer — this
bridge NEVER uses that fallback. An unmatched pair is left ungenerated,
never silently priced as compatible. This is Codex's own instruction:
"unknown/mismatched pairs remain gated... do not use default-allowance
as authority" / "Program visibility alone must not be reported as
stacking."

N-way (3+) program combinations: `price_program_group_stack()` generalizes
the pairwise bridge below to any group size. Both reused calculators
(`apply_stacking_adjustments`, `evaluate_legal_stacking`) already operate
on an arbitrary `stacking_rules` list against an arbitrary claimed-
program set — no change was needed to either for this. The gating
discipline generalizes directly: a group is only priced as a combination
when EVERY pairwise sub-combination inside it carries an explicit named
rule (confirmed to exist for several real triples, e.g.
`{ca_federal_cptc, ca_telefilm_dev, on_ofttc}`, all `_SLUG_PAIR_RULES`-
covered) — a group with even one uncovered pair is never generated,
exactly the same "unknown stays unknown" discipline as the pairwise case.

Alias reconciliation: `load_named_pair_rule()` also tries each slug's
KNOWN alias spellings (via the existing
`app.services.canonical_program_identity._aliases_for()` — the same
`CANONICAL_RUNTIME_SLUG_BINDINGS`/`PROGRAM_SLUG_ALIASES` registries the
rest of the canonical substrate already uses) before giving up. This
closes the specific, previously-disclosed gap where `_SLUG_PAIR_RULES`
still references a pre-canonicalization spelling (`on_opstc` for the now-
canonical `ca_on_opstc`, `qc_film_production` for `ca_qc_pstc`) — a known
alias correction, not an invented compatibility rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from app.calculators.apply_stacking_adjustments import apply_stacking_adjustments
from app.calculators.evaluate_legal_stacking import evaluate_legal_stacking
from app.optimization.stacking_rules import _SLUG_PAIR_RULES
from app.services.canonical_program_identity import _aliases_for

#: Existing Optimizer/Stacker Reconnection, Ontario interaction repair.
#: apply_stacking_adjustments._apply_spend_reduction's own grant-type
#: heuristic (program_type in {grant, regional_fund, discretionary_fund})
#: cannot resolve a spend_reduction pair where the reducing side is
#: ITSELF a tax credit that also happens to be government assistance to
#: another credit (Ontario's OFTTC reducing federal CPTC; Quebec's SODEC
#: credit reducing federal CPTC) — every _SLUG_PAIR_RULES spend_reduction
#: entry's own condition_text already NAMES which program is the reducing
#: side in prose (e.g. "OFTTC tax credit is government assistance... and
#: must be deducted from... before computing CPTC"); this table makes
#: that ALREADY-CITED fact machine-readable rather than inventing new
#: legal content. Every entry below is read directly off the exact
#: condition_text in app.optimization.stacking_rules._SLUG_PAIR_RULES —
#: keyed by the pair, valued by the REDUCING program's slug.
_SPEND_REDUCTION_DIRECTION: dict[frozenset, str] = {
    frozenset({"nohfc_production_fund", "on_ofttc"}): "nohfc_production_fund",
    frozenset({"ca_federal_cptc", "nohfc_production_fund"}): "nohfc_production_fund",
    frozenset({"au_location_offset", "au_screen_production"}): "au_screen_production",
    frozenset({"au_producer_offset", "au_screen_production"}): "au_screen_production",
    frozenset({"ca_cmf", "ca_federal_cptc"}): "ca_cmf",
    frozenset({"ca_federal_cptc", "ca_telefilm_dev"}): "ca_telefilm_dev",
    frozenset({"ca_federal_cptc", "on_ofttc"}): "on_ofttc",
    frozenset({"ca_federal_cptc", "qc_film_production"}): "qc_film_production",
    frozenset({"ca_bc_pstc", "ca_cmf"}): "ca_cmf",
    frozenset({"ca_cmf", "on_opstc"}): "ca_cmf",
    frozenset({"nohfc_production_fund", "on_opstc"}): "nohfc_production_fund",
    frozenset({"au_location_offset", "au_screenwest"}): "au_screenwest",
    frozenset({"au_screen_production", "au_screenwest"}): "au_screen_production",
    frozenset({"au_producer_offset", "au_sa_safc"}): "au_sa_safc",
    frozenset({"au_location_offset", "au_sa_safc"}): "au_sa_safc",
    frozenset({"au_sa_safc", "au_screen_production"}): "au_sa_safc",
    frozenset({"ca_bell_fund", "ca_federal_cptc"}): "ca_bell_fund",
    frozenset({"ca_federal_cptc", "ca_nsi_fund"}): "ca_nsi_fund",
    frozenset({"ca_cmf", "on_ofttc"}): "ca_cmf",
    frozenset({"ca_cmf", "qc_film_production"}): "ca_cmf",
    frozenset({"ca_telefilm_dev", "on_ofttc"}): "ca_telefilm_dev",
    frozenset({"ca_telefilm_dev", "qc_film_production"}): "ca_telefilm_dev",
    frozenset({"ca_qc_qprdp", "ca_telefilm_dev"}): "ca_telefilm_dev",
    frozenset({"ca_bc_pstc", "ca_telefilm_dev"}): "ca_telefilm_dev",
    frozenset({"ca_bell_fund", "on_ofttc"}): "ca_bell_fund",
    frozenset({"au_nsw_screen", "au_screen_production"}): "au_screen_production",
    frozenset({"au_screen_production", "au_vic_film_victoria"}): "au_screen_production",
    frozenset({"au_qld_screen", "au_screen_production"}): "au_screen_production",
}


def _reducing_slug(slug_a: str, slug_b: str) -> str | None:
    """The reducing program's CANONICAL slug (i.e. slug_a or slug_b, never
    an alias) for a spend_reduction pair — resolved via
    _SPEND_REDUCTION_DIRECTION under the exact canonical slugs first, then
    under any known alias spelling of either (same alias reconciliation
    load_named_pair_rule already performs)."""
    aliases_a = set(_slug_and_alias_candidates(slug_a))
    aliases_b = set(_slug_and_alias_candidates(slug_b))
    for cand_a in aliases_a:
        for cand_b in aliases_b:
            reducer_alias = _SPEND_REDUCTION_DIRECTION.get(frozenset({cand_a, cand_b}))
            if reducer_alias is None:
                continue
            if reducer_alias in aliases_a:
                return slug_a
            if reducer_alias in aliases_b:
                return slug_b
    return None


@dataclass
class StackCandidate:
    """One already-canonically-priced single-program candidate eligible to
    be combined into a multi-program structure. Every field is read
    straight off the existing per-program pricing pass — no new
    economics computed here."""
    program_slug: str
    jurisdiction_code: str
    selected_incentive_usd: float
    effective_rate: float
    qualifying_spend_usd: float
    incentive_type: str          # DoctrineRecord.incentive_type


@dataclass
class MultiProgramStackResult:
    jurisdiction_code: str
    program_slugs: list[str]
    rule_type: str
    condition_text: str | None
    raw_incentive_usd: float
    adjusted_incentive_usd: float
    stacking_reduction_usd: float
    per_program_adjusted_usd: dict[str, float]
    adjustments: list[dict] = field(default_factory=list)
    legal_review_required: bool = False
    violations: list[dict] = field(default_factory=list)
    conditionals: list[dict] = field(default_factory=list)
    disclosed_limitations: list[str] = field(default_factory=list)


def _slug_and_alias_candidates(slug: str) -> tuple[str, ...]:
    """The canonical slug itself, plus every KNOWN alias spelling of it
    (existing registry data only — see module docstring)."""
    return (slug, *_aliases_for(slug))


def load_named_pair_rule(slug_a: str, slug_b: str) -> dict | None:
    """The canonical rule/slug loading adapter (lineage-trace roadmap step
    2 / integration piece (c)). Tries the exact canonical slug pair first;
    if unmatched, tries every combination of each slug's known alias
    spellings against `_SLUG_PAIR_RULES` (e.g. canonical `ca_on_opstc`
    matches the table's legacy `on_opstc` entry). The RETURNED rule always
    reports the CANONICAL slugs (slug_a, slug_b) as program_a_id/
    program_b_id — the alias is only used to find the rule, never
    surfaced downstream. A pair with no coverage under ANY known spelling
    stays ungenerated — never a silent guess.
    """
    for candidate_a in _slug_and_alias_candidates(slug_a):
        for candidate_b in _slug_and_alias_candidates(slug_b):
            entry = _SLUG_PAIR_RULES.get(frozenset({candidate_a, candidate_b}))
            if entry is not None:
                rule = {
                    "program_a_id": slug_a,
                    "program_b_id": slug_b,
                    "rule_type": entry["rule_type"],
                    "condition_text": entry.get("condition_text"),
                    "statutory_reference": None,
                    "confidence_tier": "VERIFIED",
                    "notes": (
                        "app.optimization.stacking_rules._SLUG_PAIR_RULES "
                        f"(named pair, matched via {candidate_a!r}+{candidate_b!r})"
                    ),
                }
                if entry["rule_type"] == "spend_reduction":
                    reducer = _reducing_slug(slug_a, slug_b)
                    if reducer is not None:
                        rule["reduces"] = reducer
                return rule
    return None


def eligible_for_combination(code_a: str, code_b: str) -> bool:
    """Two candidates may be considered for a combined structure only if
    they represent the SAME physical shoot jurisdiction: either the exact
    same jurisdiction_code (multiple independent programs at one
    jurisdiction — e.g. CA-ON's on_ofttc + ca_on_opstc), or one of them is
    the bare top-level country code (a national/federal program, which
    applies alongside any of its own provinces/states) paired with a
    provincial/state code under that SAME country (e.g. "CA" federal
    CPTC + "CA-BC" provincial PSTC). Two DIFFERENT provinces/states
    (e.g. "CA-BC" + "CA-ON") are never combinable — a production cannot
    simultaneously shoot in both under one structure. This mirrors the
    same country-prefix structural test app.optimization.stacking_rules.
    _is_government_assistance_in_jurisdiction already uses for its own
    (different, static-fallback) grant/credit check.
    """
    if code_a == code_b:
        return True
    country_a, country_b = code_a.split("-")[0], code_b.split("-")[0]
    if country_a != country_b:
        return False
    return code_a == country_a or code_b == country_b


def eligible_group_for_combination(codes: list[str]) -> bool:
    """Group generalization of eligible_for_combination: every code must
    be either the bare top-level country code (a federal/national program)
    or ONE SPECIFIC provincial/state code shared by the whole group — two
    different specific codes (e.g. "CA-BC" and "CA-ON") anywhere in the
    group make the whole group ineligible, since a production cannot
    physically shoot in two different provinces/states under one
    structure."""
    if not codes:
        return False
    countries = {c.split("-")[0] for c in codes}
    if len(countries) != 1:
        return False
    specific_codes = {c for c in codes if "-" in c}
    return len(specific_codes) <= 1


def _reported_group_jurisdiction_code(codes: list[str]) -> str:
    """The most specific code in an eligible group is the real shoot
    jurisdiction — a bare country code is never a real shoot location on
    its own. Mirrors the pairwise reporting rule."""
    return max(codes, key=len)


def _rule_type_for_group(rules: list[dict]) -> str:
    """A group combines >1 rule; report a single composite label rather
    than picking one arbitrarily. 'mixed' when the group's named rules are
    not all the same type."""
    types = {r["rule_type"] for r in rules}
    return types.pop() if len(types) == 1 else "mixed"


#: Codex optimizer-correctness classification, point 1 — FAIL CLOSED FOR
#: STACK PUBLICATION. Only these rule types represent a fully RESOLVED
#: economic outcome the reused apply_stacking_adjustments engine can
#: correctly apply (allowed = no adjustment; mutually_exclusive = the
#: higher-value program is deterministically retained; spend_reduction =
#: a computable basis reduction). "conditional" (legal review required,
#: no automatic value resolution — e.g. ca_federal_cptc+ca_qc_qprdp) and
#: any future "prohibited" entry are NOT publishable: the legal FACT is
#: known, but the ECONOMIC resolution is not, so a combined structure
#: must not be generated — never surfaced as if it were priced. This is
#: identical in spirit to the "unknown pair stays ungenerated" rule
#: already enforced for uncovered pairs; conditional/prohibited pairs are
#: treated the same way (a *known-but-unresolved* pair is not safer to
#: publish than an unknown one).
_PUBLISHABLE_RULE_TYPES: frozenset[str] = frozenset({"allowed", "mutually_exclusive", "spend_reduction"})


def load_named_rules_for_group(slugs: list[str]) -> tuple[list[dict], bool]:
    """Collects the named rule for EVERY pairwise sub-combination among
    `slugs`. Returns (rules, fully_covered) — fully_covered is True only
    when EVERY single pair resolved to a named rule of a publishable type
    (_PUBLISHABLE_RULE_TYPES). A group with even one uncovered OR
    unresolved (conditional/prohibited) pair is not safe to treat as a
    validated combination (Codex: "Program visibility alone must not be
    reported as stacking" — extended to "a legally-flagged-but-unresolved
    pair must not be reported as resolved stacking" either), though the
    collected PUBLISHABLE rules are still returned."""
    rules: list[dict] = []
    all_covered = True
    for slug_a, slug_b in combinations(slugs, 2):
        rule = load_named_pair_rule(slug_a, slug_b)
        if rule is None or rule["rule_type"] not in _PUBLISHABLE_RULE_TYPES:
            all_covered = False
            continue
        rules.append(rule)
    return rules, all_covered


def _build_group_result(
    candidates: list[StackCandidate], rules: list[dict],
) -> MultiProgramStackResult:
    incentive_results = [
        {
            "program_id": c.program_slug,
            "economic_value_usd": c.selected_incentive_usd,
            "effective_rate": c.effective_rate,
            "program_type": c.incentive_type,
            "qualifying_spend_usd": c.qualifying_spend_usd,
        }
        for c in candidates
    ]
    slugs = [c.program_slug for c in candidates]

    adj_result = apply_stacking_adjustments(incentive_results, rules)
    legal = evaluate_legal_stacking(claimed_program_ids=slugs, stacking_rules=rules)

    disclosed_limitations: list[str] = []
    for rule in rules:
        if rule["rule_type"] != "spend_reduction":
            continue
        # apply_stacking_adjustments._apply_spend_reduction only recognizes
        # a "grant"/"regional_fund"/"discretionary_fund" program_type as
        # the reducing side (see apply_stacking_adjustments.py
        # _GRANT_TYPES). Several named spend_reduction rules (on_ofttc+
        # ca_federal_cptc, qc_film_production+ca_federal_cptc, and others
        # sharing this pattern) describe a TAX CREDIT that is itself
        # government assistance reducing another tax credit's qualifying-
        # spend basis — a case that generic heuristic cannot resolve
        # without a program_type it wasn't designed to see. Detected here
        # by checking whether ANY adjustment was actually recorded for
        # this specific pair; disclosed rather than silently reported as
        # "no stacking impact".
        pair_ids = {rule["program_a_id"], rule["program_b_id"]}
        matched = any(
            {a.program_a_id, a.program_b_id} == pair_ids for a in adj_result.adjustments
        )
        if not matched:
            disclosed_limitations.append(
                f"Statutory rule found ({rule['condition_text']}) but the reused "
                "spend_reduction calculator only recognizes grant/regional_fund/"
                "discretionary_fund program types as the reducing side; neither "
                f"{rule['program_a_id']} nor {rule['program_b_id']} is typed that "
                "way, so no reduction was applied for this pair. This "
                "combination's adjusted_incentive_usd is therefore not confirmed "
                "net of this statutory deduction — legal/economic review "
                "required before this combination is treated as fully priced."
            )

    return MultiProgramStackResult(
        jurisdiction_code=_reported_group_jurisdiction_code([c.jurisdiction_code for c in candidates]),
        program_slugs=slugs,
        rule_type=_rule_type_for_group(rules),
        condition_text="; ".join(r["condition_text"] for r in rules if r.get("condition_text")) or None,
        raw_incentive_usd=adj_result.total_raw_value_usd,
        adjusted_incentive_usd=adj_result.total_adjusted_value_usd,
        stacking_reduction_usd=max(
            0.0, adj_result.total_raw_value_usd - adj_result.total_adjusted_value_usd
        ),
        per_program_adjusted_usd=adj_result.program_values,
        adjustments=[
            {
                "program_a_id": a.program_a_id,
                "program_b_id": a.program_b_id,
                "rule_type": a.rule_type,
                "description": a.description,
                "original_value_usd": a.original_value_usd,
                "adjustment_usd": a.adjustment_usd,
                "adjusted_value_usd": a.adjusted_value_usd,
            }
            for a in adj_result.adjustments
        ],
        legal_review_required=legal.legal_review_required,
        violations=[
            {
                "program_a_id": v.program_a_id, "program_b_id": v.program_b_id,
                "rule_type": v.rule_type.value, "condition_text": v.condition_text,
            }
            for v in legal.violations
        ],
        conditionals=[
            {
                "program_a_id": c.program_a_id, "program_b_id": c.program_b_id,
                "rule_type": c.rule_type.value, "condition_text": c.condition_text,
            }
            for c in legal.conditionals
        ],
        disclosed_limitations=disclosed_limitations,
    )


def price_program_pair_stack(
    candidate_a: StackCandidate, candidate_b: StackCandidate,
) -> MultiProgramStackResult | None:
    """
    The canonical multi-program stack-pricing bridge for exactly two
    programs. Returns None if the pair has no explicit named rule in
    _SLUG_PAIR_RULES (nothing safe to combine — Codex: visibility alone
    is not proof of stacking) or if the two candidates do not represent
    the same physical shoot jurisdiction (see eligible_for_combination).
    Thin wrapper over price_program_group_stack for the 2-candidate case.
    """
    return price_program_group_stack([candidate_a, candidate_b])


def price_program_group_stack(candidates: list[StackCandidate]) -> MultiProgramStackResult | None:
    """
    The canonical multi-program stack-pricing bridge, generalized to any
    group size (N-way reconnection). Returns None unless:
      - at least 2 candidates are given;
      - every candidate's jurisdiction is eligible to combine with the
        rest (eligible_group_for_combination — same exact jurisdiction, or
        one federal + at most one specific province/state, never two
        different provinces/states);
      - EVERY pairwise sub-combination among the candidates' program
        slugs has an explicit named rule of a PUBLISHABLE type
        (load_named_rules_for_group's fully_covered — see
        _PUBLISHABLE_RULE_TYPES) — a group with even one uncovered or
        unresolved (conditional/prohibited) pair is left ungenerated,
        never partially trusted.

    Order independence (Codex optimizer-correctness classification, point
    4): `candidates` is sorted onto ONE canonical order (by program_slug)
    BEFORE any adjustment is computed — apply_stacking_adjustments applies
    its rules sequentially and its own per-program values can differ
    depending on which rule touches a shared program first (a genuine,
    confirmed order-sensitivity in the reused legacy engine). Rather than
    rewrite that engine's math (out of scope — a new adjustment planner is
    a larger, separate piece of work), this bridge guarantees the SAME
    fixed order is used regardless of the caller's input order, so
    price_program_group_stack(perm) is byte-identical for every
    permutation `perm` of the same candidate set — the literal acceptance
    criterion ("N-way economics invariant under input permutation") is
    satisfied by canonicalization, not by solving general order-
    independence in the underlying calculator. See
    test_canonical_stack_bridge.py's permutation-invariance test.
    """
    if len(candidates) < 2:
        return None
    codes = [c.jurisdiction_code for c in candidates]
    if not eligible_group_for_combination(codes):
        return None
    slugs = [c.program_slug for c in candidates]
    if len(set(slugs)) != len(slugs):
        return None  # defensive: a program cannot combine with itself
    canonical_candidates = sorted(candidates, key=lambda c: c.program_slug)
    canonical_slugs = [c.program_slug for c in canonical_candidates]
    rules, fully_covered = load_named_rules_for_group(canonical_slugs)
    if not fully_covered or not rules:
        return None
    return _build_group_result(canonical_candidates, rules)
