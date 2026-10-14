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
from app.data.authority_coverage_registry import economic_block_for_program
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
    frozenset({"ca_federal_cptc", "on_opstc"}): "on_opstc",
    frozenset({"ca_federal_pstc", "on_opstc"}): "on_opstc",
    frozenset({"ca_federal_pstc", "ca_mb_film_video_credit"}): "ca_mb_film_video_credit",
    frozenset({"ca_federal_pstc", "ca_bc_pstc"}): "ca_bc_pstc",
    frozenset({"ca_federal_pstc", "ca_qc_pstc"}): "ca_qc_pstc",
    frozenset({"ca_federal_pstc", "ca_nl_all_spend_credit"}): "ca_nl_all_spend_credit",
    frozenset({"ca_federal_cptc", "ca_nl_all_spend_credit"}): "ca_nl_all_spend_credit",
    frozenset({"ca_bc_film_tv_tax_credit", "ca_federal_cptc"}): "ca_bc_film_tv_tax_credit",
    frozenset({"ca_federal_cptc", "ca_ab_fttc"}): "ca_ab_fttc",
    frozenset({"ca_federal_pstc", "ca_ab_fttc"}): "ca_ab_fttc",
    frozenset({"ca_federal_pstc", "ca_bc_dave"}): "ca_bc_dave",
    frozenset({"ca_bc_dave", "ca_federal_cptc"}): "ca_bc_dave",
    frozenset({"ca_federal_pstc", "on_ofttc"}): "on_ofttc",
    frozenset({"ca_bc_film_tv_tax_credit", "ca_federal_pstc"}): "ca_bc_film_tv_tax_credit",
    frozenset({"ca_federal_cptc", "ca_nb_film_tax_credit"}): "ca_nb_film_tax_credit",
    frozenset({"ca_federal_pstc", "ca_nb_film_tax_credit"}): "ca_nb_film_tax_credit",
    frozenset({"ca_federal_cptc", "ca_ns_production_incentive_fund"}): "ca_ns_production_incentive_fund",
    frozenset({"ca_federal_pstc", "ca_ns_production_incentive_fund"}): "ca_ns_production_incentive_fund",
    frozenset({"ca_federal_pstc", "ca_sk_creative_saskatchewan_grant"}): "ca_sk_creative_saskatchewan_grant",
    frozenset({"ca_federal_pstc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"}): "ontario_computer_animation_and_special_effects_tax_credit_ocase",
    frozenset({"ca_federal_cptc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"}): "ontario_computer_animation_and_special_effects_tax_credit_ocase",
    frozenset({"ca_federal_cptc", "ca_mb_film_video_credit"}): "ca_mb_film_video_credit",
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
    # Codex global optimizer audit, P1-TRACE-001 remediation: the exact
    # set of real BudgetLine.line_id identities this program's own
    # qualification register marked QUALIFIES. Threading true line
    # identity through (not the account_code classification field, which
    # a real budget may legitimately reuse across distinct lines) is what
    # lets a caller compute an EXACT union of unique allocated spend
    # across several stacked programs in the same jurisdiction, instead
    # of a sum (double-counts any overlap) or a max (a lower bound that
    # understates a genuinely disjoint or partially-overlapping base).
    # Defaulted empty so every existing caller that has not been updated
    # to populate it keeps working unchanged.
    qualifying_line_ids: frozenset[str] = field(default_factory=frozenset)
    #: CPTC only (CRA RC4164 / Form T1131 guide): the labour basis the 25% applies to before the cost cap, the production cost the 60% cap is
    #: measured on, and assistance already stated at project level. Assistance in a stack (any provincial tax credit, fund or grant) reduces
    #: the production cost that sets the cap; it never reduces labour expenditure directly. None leaves the generic spend-reduction engine.
    rate_basis_usd: float | None = None
    production_cost_usd: float | None = None
    stated_assistance_usd: float = 0.0
    #: The program's ELECTED floor rate (the segment's own rate_floor: the Manitoba elective credit's rate, the labour credit's rate for BC, the all-spend rate for Quebec and Ontario).
    #: A provincial credit that is assistance to the federal PSTC nets by this rate x the PSTC labour basis (bounded by the credit); None falls back to effective_rate.
    floor_rate: float | None = None


CPTC_SLUG = "ca_federal_cptc"
PSTC_SLUG = "ca_federal_pstc"
OPSTC_SLUG = "on_opstc"
CPTC_COST_CAP_PCT = 0.60     # Form T1131 Part 5: Amount B = 60% of (production cost - assistance)


def cptc_stack_fields(program_slug: str, rate_resolution, production_cost_usd: float | None, amount_facts: dict | None = None) -> dict:
    """StackCandidate keyword arguments for the federal CPTC (empty for every other program)."""
    if program_slug == PSTC_SLUG and rate_resolution is not None and getattr(rate_resolution, "qpe_basis_used", None) is not None:
        return {"rate_basis_usd": float(rate_resolution.qpe_basis_used)}      # the labour basis the OPSTC labour portion is netted against
    if program_slug != CPTC_SLUG or rate_resolution is None or production_cost_usd is None:
        return {}
    basis = getattr(rate_resolution, "qpe_basis_used", None)
    if basis is None:
        return {}
    return {"rate_basis_usd": float(basis), "production_cost_usd": float(production_cost_usd),
            "stated_assistance_usd": float((amount_facts or {}).get("ca_federal_cptc_assistance_usd", 0.0) or 0.0)}


def _is_slug(slug: str, canonical: str) -> bool:
    return canonical in _slug_and_alias_candidates(slug)


MB_SLUG = "ca_mb_film_video_credit"
BC_PSTC_SLUG = "ca_bc_pstc"
QC_PSTC_SLUG = "ca_qc_pstc"
NL_SLUG = "ca_nl_all_spend_credit"
OCASE_SLUG = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
AB_SLUG = "ca_ab_fttc"
DAVE_SLUG = "ca_bc_dave"
NB_SLUG = "ca_nb_film_tax_credit"
NS_SLUG = "ca_ns_production_incentive_fund"
SK_SLUG = "ca_sk_creative_saskatchewan_grant"
#: Provincial credits that are assistance to the federal PSTC to the extent reasonably in respect of Canadian labour: ITA 125.5(1) "qualified Canadian labour expenditure" paragraph (b)
#: (assistance "that can reasonably be considered to be in respect of" the Canadian labour expenditure); CRA RC4385 (Form T1177 guide): "any provincial tax credit allowed in connection
#: with the accredited production is considered assistance"; Ontario Creates OPSTC Guidelines s.3.02: "Only the labour portion of the OPSTC constitutes assistance." The reverse never
#: applies: the federal PSTC is not assistance to the Ontario OPSTC (Guidelines s.3.02), the Manitoba credit (TC-2 guidelines), the BC credit (Income Tax Act (BC) s.79(1) "assistance"
#: excludes amounts deemed paid under ITA 125.4(3) or 125.5(3)) or the Quebec credit (Revenu Québec CO-1029.8.36.SP, note 7).
#: NA-RECONCILIATION-13: the Ontario OFTTC and the BC film and television credit are computed on labour only, so they are wholly assistance in respect of Canadian labour (verified netting).
OFTTC_SLUG = "on_ofttc"
BC_FILM_TV_SLUG = "ca_bc_film_tv_tax_credit"
PSTC_ASSISTING_SLUGS = ("on_opstc", MB_SLUG, BC_PSTC_SLUG, QC_PSTC_SLUG, NL_SLUG, OCASE_SLUG, AB_SLUG, DAVE_SLUG, NB_SLUG, NS_SLUG, SK_SLUG, OFTTC_SLUG, BC_FILM_TV_SLUG)
#: The credits computed on ALL eligible cost (labour included) whose labour share is APPORTIONED by rate x labour: Ontario's is stated by its own guidelines (s.3.02); Manitoba's cost-of-production
#: credit and Quebec's all-spend credit are not, so the apportionment is a disclosed assumption, with the whole-credit figure disclosed as the lower bound.
PSTC_APPORTIONED_SLUGS = (MB_SLUG, QC_PSTC_SLUG, NL_SLUG, AB_SLUG, NB_SLUG, NS_SLUG, SK_SLUG)
MB_COST_CREDIT_RATE = 0.30     # Manitoba Film & Music TC-2 guidelines: the cost-of-production credit (the elective alternative to the 45% cost-of-salaries credit)


def pstc_netted_by_provincial(original: float, rate: float, labour_basis: float, partners):
    """Net the federal PSTC by every provincial credit stacked with it. ``partners`` is [(slug, credit_usd, rate)]; each credit's labour portion is min(credit, rate x PSTC labour basis)
    (a labour-only credit therefore nets in full, an all-spend credit by its labour share). Returns (adjusted PSTC, [(slug, labour_assistance)], reduction)."""
    parts = [(slug, round(min(float(credit), float(prate) * labour_basis), 2)) for slug, credit, prate in partners]
    total = round(sum(a for _, a in parts), 2)
    reduction = round(min(total, labour_basis) * rate, 2)
    return round(max(0.0, original - reduction), 2), parts, reduction


def netting_basis_label(slug: str) -> str:
    """Whether the PSTC labour netting by this provincial credit is VERIFIED (the authority states the labour portion, or the credit is wholly labour) or an ASSUMED ALLOCATION (an all-spend credit whose
    labour share the authorities do not state: rate x PSTC labour basis, with the whole-credit figure as the lower bound). Kept in the adjustment text so a verified reduction is never read as an assumed one."""
    if any(_is_slug(slug, x) for x in PSTC_APPORTIONED_SLUGS):
        return "ASSUMED ALLOCATION (not stated by the authority)"
    return "VERIFIED NETTING (authority-stated or wholly in respect of labour)"


def pstc_basis_phrase(slug: str) -> str:
    if _is_slug(slug, OPSTC_SLUG):
        return "Ontario Creates OPSTC Guidelines s.3.02: only the labour portion of the OPSTC is assistance"
    if any(_is_slug(slug, x) for x in PSTC_APPORTIONED_SLUGS):
        return "all-spend credit, labour share apportioned by rate x labour"
    return "a credit computed on labour, wholly in respect of labour"


def apportionment_note(slug: str, credit: float, rate: float, labour_basis: float, pstc_original: float, pstc_rate: float) -> str:
    """Disclosure for an apportioned all-spend credit (Manitoba cost-of-production, Quebec, Alberta, New Brunswick, Nova Scotia, Saskatchewan): the labour share is an assumption, the whole-credit result is the stated lower bound."""
    labour_part = round(min(float(credit), rate * labour_basis), 2)
    whole = round(max(0.0, pstc_original - min(float(credit), labour_basis) * pstc_rate), 2)
    names = {MB_SLUG: "Manitoba", NL_SLUG: "Newfoundland and Labrador", AB_SLUG: "Alberta", NB_SLUG: "New Brunswick", NS_SLUG: "Nova Scotia", SK_SLUG: "Saskatchewan"}
    name = next((n for k, n in names.items() if _is_slug(slug, k)), "Quebec")
    return (f"Apportionment assumption (not stated by the {name} authority): the {name} credit is computed on all eligible cost, labour included, so the part reasonably in respect of Canadian "
            f"labour (ITA 125.5(1)) is taken as its rate {rate:.1%} x the PSTC labour basis ${labour_basis:,.0f} = ${labour_part:,.0f} (bounded by the credit ${float(credit):,.0f}); the CRA "
            f"(RC4385) calls any provincial tax credit assistance without an allocation, and if the whole credit were assistance the federal PSTC would be ${whole:,.0f} instead.")


#: Disclosed on every priced CPTC segment and every stack that contains the CPTC: its eligibility is a status the budget cannot establish (never a certification, never a gate).
CPTC_PLANNING_NOTE = (
    "Planning assumption, not a certification: the CPTC is the federal credit for CAVCO-certified Canadian-content productions of a Canadian-controlled applicant (the repository's "
    "jurisdiction record: CAVCO's CPTC is for Canadian-content productions; the foreign and service-production credit is the PSTC). Neither a CAVCO certificate nor Canadian control "
    "is stated for this production, so this credit is a conditional planning figure, not a guaranteed floor; the claim follow-ups are the certificate and the applicant's control."
)


def cptc_net_cost_adjusted(original: float, rate: float, labour_basis: float, production_cost: float, stated_assistance: float, assistance: float):
    """CRA RC4164 / Form T1131: qualified labour = min(labour, 60% x (production cost - assistance)); credit = rate x qualified, never above the
    standalone credit. Returns (adjusted credit, cap, qualified labour). Shared by the same-jurisdiction stack and the structural generator."""
    cap = round(CPTC_COST_CAP_PCT * max(0.0, production_cost - stated_assistance - assistance), 2)
    qualified = round(min(labour_basis, cap), 2)
    return round(min(original, qualified * rate), 2), cap, qualified


def pstc_labour_netted(original: float, rate: float, labour_basis: float, opstc_value: float, opstc_rate: float):
    """Ontario Creates OPSTC Guidelines s.3.02: only the LABOUR portion of the OPSTC is assistance to the federal PSTC. Returns (adjusted credit,
    labour assistance, reduction); Ontario labour is taken as the PSTC segment's labour basis. One partner of pstc_netted_by_provincial."""
    adjusted, parts, reduction = pstc_netted_by_provincial(original, rate, labour_basis, [("on_opstc", opstc_value, opstc_rate)])
    return adjusted, parts[0][1], reduction


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
    #: Cluster 8: each constituent's own qualifying spend, so a combined
    #: structure can serve reconciled segments instead of segments=[] with
    #: total_qualifying_spend_usd=0 alongside a non-zero incentive.
    per_program_qpe_usd: dict[str, float] = field(default_factory=dict)
    adjustments: list[dict] = field(default_factory=list)
    legal_review_required: bool = False
    violations: list[dict] = field(default_factory=list)
    conditionals: list[dict] = field(default_factory=list)
    disclosed_limitations: list[str] = field(default_factory=list)
    # CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B: a
    # generic, group-size-independent pairwise-legality gate. The prior
    # `rule_type == "mutually_exclusive"` check (canonical_evaluation.py)
    # only caught this when EVERY pairwise sub-rule in the group shared
    # the identical rule_type -- _rule_type_for_group collapses to
    # "mixed" for any group mixing types (e.g. ca_federal_cptc+on_ofttc+
    # on_opstc: spend_reduction + mutually_exclusive + mutually_exclusive
    # -> "mixed"), silently letting a group containing a real hard
    # incompatibility (on_ofttc+on_opstc, a real production-type
    # election conflict) be served as PRICED. This field is computed
    # directly from every pairwise sub-rule in the group (never from the
    # collapsed group-level rule_type), so it is correct regardless of
    # how many OTHER pairs in the group are compatible.
    contains_blocking_incompatibility: bool = False
    #: The exact failing pair(s), so a rejection is precise and machine-
    #: readable rather than a bare boolean -- "do not silently omit the
    #: structure" (Phase B) requires naming WHICH pair is invalid.
    blocking_pairs: list[dict] = field(default_factory=list)


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
#: no automatic value resolution — e.g. ca_federal_cptc+ca_bc_dave) and
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
    program_values, adjustment_dicts = dict(adj_result.program_values), [
        {"program_a_id": a.program_a_id, "program_b_id": a.program_b_id, "rule_type": a.rule_type, "description": a.description,
         "original_value_usd": a.original_value_usd, "adjustment_usd": a.adjustment_usd, "adjusted_value_usd": a.adjusted_value_usd}
        for a in adj_result.adjustments
    ]
    cptc = next((c for c in candidates if c.program_slug == CPTC_SLUG and c.rate_basis_usd is not None and c.production_cost_usd is not None), None)
    if cptc is not None:
        reducers = {}
        for r in rules:
            if r["rule_type"] == "spend_reduction" and CPTC_SLUG in (r["program_a_id"], r["program_b_id"]) and r.get("reduces") not in (None, CPTC_SLUG):
                reducers[r["reduces"]] = program_values.get(r["reduces"], 0.0)
        if reducers:
            assistance = round(sum(reducers.values()), 2)
            original = float(cptc.selected_incentive_usd)
            adjusted, cap, qualified = cptc_net_cost_adjusted(
                original, cptc.effective_rate, cptc.rate_basis_usd, cptc.production_cost_usd, cptc.stated_assistance_usd, assistance)
            adjustment_dicts = [d for d in adjustment_dicts if not (d["rule_type"] == "spend_reduction" and d["program_b_id"] == CPTC_SLUG)]
            program_values[CPTC_SLUG] = adjusted
            total_assistance = assistance or 1.0
            for slug_r, amount in reducers.items():
                share = (original - adjusted) * (amount / total_assistance)
                adjustment_dicts.append({
                    "program_a_id": slug_r, "program_b_id": CPTC_SLUG, "rule_type": "spend_reduction",
                    "description": (f"Assistance ${assistance:,.0f} (provincial tax credit / fund) reduces the production cost that sets the CPTC cap "
                                    f"(CRA RC4164 T1131 lines 421-430): qualified labour = min(labour ${cptc.rate_basis_usd:,.0f}, "
                                    f"{CPTC_COST_CAP_PCT:.0%} x (cost ${cptc.production_cost_usd:,.0f} - assistance ${cptc.stated_assistance_usd + assistance:,.0f}) = ${cap:,.0f}) "
                                    f"= ${qualified:,.0f}; labour itself is not reduced."),
                    "original_value_usd": original, "adjustment_usd": -share, "adjusted_value_usd": adjusted,
                })
    # Federal PSTC with the Ontario OPSTC: only the LABOUR portion of the OPSTC is assistance to the PSTC (Ontario Creates OPSTC Guidelines s.3.02),
    # so the generic whole-credit reduction is replaced by (OPSTC rate x the PSTC labour basis, bounded by the credit) x the PSTC rate.
    pstc = next((c for c in candidates if _is_slug(c.program_slug, PSTC_SLUG) and c.rate_basis_usd is not None), None)
    pstc_netted = False
    netting_notes: list[str] = []
    if pstc is not None:
        partners = [c for c in candidates if any(_is_slug(c.program_slug, x) for x in PSTC_ASSISTING_SLUGS) and any(
            r["rule_type"] == "spend_reduction" and _is_slug(r["program_a_id"], PSTC_SLUG) + _is_slug(r["program_b_id"], c.program_slug) == 2
            or r["rule_type"] == "spend_reduction" and _is_slug(r["program_b_id"], PSTC_SLUG) + _is_slug(r["program_a_id"], c.program_slug) == 2
            for r in rules)]
        if partners:
            original = float(pstc.selected_incentive_usd)
            pstc_rate = float(pstc.effective_rate)
            # The PSTC's labour basis is the base its own credit was priced on (credit = rate x labour): the resolution's qpe_basis_used can carry the segment's whole qualifying spend in a
            # same-jurisdiction stack (LLS: 9,483,654 against a 2,935,298 labour basis), which would net the whole provincial credit and ignore the labour portion.
            labour_basis = float(pstc.rate_basis_usd)
            if pstc_rate > 0 and float(pstc.selected_incentive_usd) > 0:
                labour_basis = min(labour_basis, float(pstc.selected_incentive_usd) / pstc_rate)
            rates = {c.program_slug: float(c.floor_rate if c.floor_rate else c.effective_rate) for c in partners}
            adjusted, parts, reduction = pstc_netted_by_provincial(
                original, pstc_rate, labour_basis, [(c.program_slug, float(c.selected_incentive_usd), rates[c.program_slug]) for c in partners])
            adjustment_dicts = [d for d in adjustment_dicts if not (d["rule_type"] == "spend_reduction" and d["program_b_id"] == pstc.program_slug)]
            program_values[pstc.program_slug] = adjusted
            total_la = round(sum(la for _, la in parts), 2)
            scale = min(1.0, labour_basis / total_la) if total_la > 0 else 1.0
            running = original
            for i, (c, (slug_c, labour_assistance)) in enumerate(zip(partners, parts)):
                share = round(labour_assistance * scale * pstc_rate, 2)
                running = adjusted if i == len(parts) - 1 else round(running - share, 2)
                adjustment_dicts.append({
                    "program_a_id": slug_c, "program_b_id": pstc.program_slug, "rule_type": "spend_reduction",
                    "description": (f"{netting_basis_label(slug_c)}: only the labour portion of the {slug_c} credit is assistance to the federal PSTC (ITA 125.5(1); CRA RC4385; {pstc_basis_phrase(slug_c)}): "
                                    f"{rates[slug_c]:.1%} x labour ${labour_basis:,.0f} = ${labour_assistance:,.0f} (bounded by the credit ${float(c.selected_incentive_usd):,.0f}) reduces PSTC labour; "
                                    f"PSTC reduction = ${labour_assistance:,.0f} x {pstc_rate:.1%} = ${share:,.0f}. The PSTC segment's labour basis is taken as the provincial labour."),
                    "original_value_usd": original, "adjustment_usd": -share, "adjusted_value_usd": running,
                })
                if any(_is_slug(slug_c, x) for x in PSTC_APPORTIONED_SLUGS):
                    netting_notes.append(apportionment_note(slug_c, float(c.selected_incentive_usd), rates[slug_c], labour_basis, original, pstc_rate))
            pstc_netted = True
    total_raw = adj_result.total_raw_value_usd
    total_adjusted = (round(sum(program_values.values()), 2) if (cptc is not None and reducers) or pstc_netted
                      else adj_result.total_adjusted_value_usd)

    # CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B:
    # scan every INDIVIDUAL pairwise rule in this group -- never the
    # collapsed group-level rule_type -- for a real hard incompatibility.
    # mutually_exclusive is the only hard-block type that can appear here
    # (load_named_rules_for_group already filtered `rules` down to
    # _PUBLISHABLE_RULE_TYPES = {allowed, mutually_exclusive,
    # spend_reduction} -- "prohibited"/"conditional" pairs never reach
    # this function at all, correctly making the WHOLE group ungenerated
    # via fully_covered=False upstream).
    _blocking_rules = [r for r in rules if r["rule_type"] == "mutually_exclusive"]
    contains_blocking_incompatibility = bool(_blocking_rules)
    blocking_pairs = [
        {
            "program_a_id": r["program_a_id"], "program_b_id": r["program_b_id"],
            "rule_type": r["rule_type"], "condition_text": r.get("condition_text"),
        }
        for r in _blocking_rules
    ]

    disclosed_limitations: list[str] = []
    if CPTC_SLUG in slugs:
        disclosed_limitations.append(CPTC_PLANNING_NOTE)
    disclosed_limitations.extend(netting_notes)
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
        raw_incentive_usd=total_raw,
        adjusted_incentive_usd=total_adjusted,
        stacking_reduction_usd=max(0.0, total_raw - total_adjusted),
        per_program_adjusted_usd=program_values,
        per_program_qpe_usd={
            c.program_slug: float(c.qualifying_spend_usd or 0.0) for c in candidates
        },
        adjustments=adjustment_dicts,
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
        contains_blocking_incompatibility=contains_blocking_incompatibility,
        blocking_pairs=blocking_pairs,
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
    # B4 central authority gate (Codex bounded remediation): no automatic
    # stack may contain an accepted authority-exhausted / discretionary-
    # display-only / retired / duplicate identity. Any blocked member ->
    # no stack result; the rejection is preserved by canonical_evaluation.py
    # exactly like every other None return here. Alias spellings inherit the
    # canonical block (economic_block_for_program canonicalizes first).
    if any(economic_block_for_program(c.program_slug) is not None for c in candidates):
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
