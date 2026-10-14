"""
program_rate_rules.py

Statutory incentive-RATE rules per program, with the PERMANENT
rate-authority doctrine of this application:

  RULE 1 — Budget documents are never authoritative for incentive rates
           or statutory rules.
  RULE 2 — Any incentive percentage appearing in an uploaded budget or
           financial model is IGNORED for calculation purposes. It may
           be recorded (as data) solely so Rule 5 can report the
           conflict.
  RULE 3 — Incentive rates come only from this module (the incentive
           database's static mirror) and the statutory/guidance
           authority cited on each rule row.
  RULE 4 — Cross-border optimization compares jurisdictions using
           database/statutory rates only (jurisdiction_comparison
           profiles must mirror this module for any program it covers).
  RULE 5 — When the database and a production budget disagree, the
           database rate is used and the conflict is reported, never
           silently swallowed.

The same static-mirror discipline as program_spend_rules.py: nothing
here is invented — every rate, threshold, and condition carries the
verbatim quoted language and document it came from.

── Mauritius primary source (read in full, pdftotext, this repository's
   audit trail) ──
EDB "Film Rebate Scheme — Submission Procedures", 31 January 2020,
https://edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf
citing the Economic Development Board (Film Rebate Scheme) Regulation
2018. Corroborated (no additional conditions) by the Mauritius Chamber
of Commerce and Industry's Film Rebate Scheme page (mcci.org).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

# B4 central authority-exhaustion gate (Codex bounded remediation). Safe at
# module top: authority_coverage_registry imports only dataclasses/typing and
# program_slug_aliases (which imports nothing) — no path back to this module.
from app.data.authority_coverage_registry import economic_block_for_program
# B2 identity ruling (Codex bounded remediation): canonicalizes a known
# variant/legacy slug spelling before every rate lookup, so a rekeyed
# identity's old spelling (us_ca_film_credit -> ca_film_30,
# ca_on_opstc/inv-ca-on-... -> on_opstc) still finds the same RateRule data
# -- "old persisted payload readable" without touching every call site.
from app.data.program_slug_aliases import canonical_slug as _canonical_program_slug

# 1.1.0 -- Co-Pro Conditional Pricing Data Reconnection: au_producer_offset
# materialized as an executable RateRule (40% feature / 30% other formats,
# both real, already-cited canonical knowledge -- see program_rate_rules_
# worldwide.py's AU Producer Offset entry) for the first time. Priceable
# ONLY through the conditional official-co-production bridge (deliberately
# not registered into ordinary jurisdiction discovery). Bumped so every
# previously-cached served row (which could only ever report this program
# as CANONICAL_DATA_GAP) is invalidated and recomputed fresh.
#: Codex bounded remediation (GLOBAL_CANONICAL_INCENTIVE_BOUNDED_
#: REMEDIATION_CLAUDE): bumped for the B2 identity rekeys (us_ca_film_
#: credit -> ca_film_30, ca_on_opstc -> on_opstc, us_ny_film_credit ->
#: ny_state_film), the B3 formulaic corrections (fr_trip, ma_ccm_rebate,
#: nl_nfpi, th_film_incentive split from th_boi_incentive, us_or_opif,
#: us_tx_miip, za_nfvf_rebate) and the B4 central authority gate -- every
#: previously-persisted served evaluation must be invalidated and
#: recomputed fresh against this rate-rule data, never silently served
#: from a stale pre-remediation generation.
#: Codex final runtime remediation: bumped again for the 11 B3 formulaic
#: connection repairs (au_location_offset, cz_film_incentive[_animation],
#: fr_trip, is_film_reimbursement_scheme, ma_ccm_rebate, mt_mfc_rebate,
#: nl_film_production_incentive, th_film_incentive, us_or_opif,
#: us_tx_miip, za_nfvf_rebate) and the new RateCondition amount_fact_*/
#: required_boolean_fact_key executable-gate mechanism.
PROGRAM_RATE_RULES_VERSION = "1.5.3"  # 1.5.3 (CR-03/CR-04): principal-fee group scope reconciled to Annex II 1.1-1.5 (known writer/director, proxy cast, unresolved music).  # 1.5.2: Greek category share caps (5% insurance/guarantees, 30% principal fees) from KYA 607434 Annex B.3 -- QpeShareCapRule. 1.5.1: PROJECT_OPEN_ITEM_RECOVERY US/CA/MX repairs -- RI USD7m and MX MXN40m per-project caps now applied; see the data-module notes


@dataclass(frozen=True)
class RateCondition:
    condition_id: str
    description: str
    quote: str           # verbatim language from the cited document
    kind: str            # "production_type" | "min_qpe_usd" | "discretionary_band" |
                         # any other value (e.g. "no_sponsorship_in_qpe",
                         # "cultural_test_required") falls into the generic
                         # fact-dependent branch: satisfied=None, never assumed.
    threshold_usd: float | None = None
    threshold_pct: float | None = None   # for min_qpe_pct_of_total_budget: fraction (0.20 = 20%)

    # Codex final runtime remediation (11 B3 formulaic rows): a genuinely
    # EXECUTABLE, deterministic gate on a caller-supplied numeric fact,
    # keyed by an arbitrary string (a native-currency amount, e.g.
    # "AUD_QAPE"/"MAD_QUALIFYING_SPEND", or a component-basis amount that
    # is NOT the segment's total qpe_usd, e.g. "us_or_payroll_qpe_usd").
    # Never a converted-from-USD or converted-to-USD guess: the fact is
    # asserted directly, in whatever unit the key documents, and the
    # engine never fabricates a conversion in either direction. Exactly
    # one of amount_fact_min/amount_fact_max is normally set on a given
    # condition: _min models an eligibility FLOOR (absence of the fact
    # fails the gate, matching "a missing mandatory fact is not a
    # satisfied one"); _max models a CEILING/CAP (absence of the fact
    # does NOT retroactively fail an otherwise-eligible tier -- there is
    # nothing to disclose a violation of -- but a supplied fact that
    # exceeds it does fail the gate). See resolve_program_rate()'s tier
    # eligibility loop and per-condition disclosure branch.
    amount_fact_key: str | None = None
    amount_fact_min: float | None = None
    amount_fact_max: float | None = None

    # True ONLY when amount_fact_key/amount_fact_min ALSO defines the
    # basis the incentive dollar value is computed against (a genuine
    # component sub-total distinct from the segment's total qpe_usd, e.g.
    # us_or_opif's payroll-only vs other-only spend). False (the default)
    # for the far more common case of a plain ELIGIBILITY THRESHOLD gate
    # (e.g. fr_trip's VFX-spend-exceeds-EUR2m fact, au_location_offset's
    # native AUD minimum, ma_ccm_rebate's native MAD minimum, a cap check)
    # -- those gate WHETHER the tier applies, but the incentive is still
    # computed against the segment's own total qpe_usd, never against the
    # gating fact's own value. See resolve_program_rate()'s qpe_basis_used
    # computation, which consults this flag explicitly rather than
    # inferring component-basis intent from field presence alone.
    is_component_basis: bool = False

    # Codex final wiring remediation (P0-ZA-001, third pass): "Broad
    # production QPE is not a valid upper-bound oracle" for a component
    # basis — the prior bound (0 <= claimed basis <= segment's own total
    # qpe_usd) let a component=production allocation with ZERO classified
    # post/VFX spend accept an arbitrary claimed QSAPPE up to its full
    # broad production total. When set (a tuple of
    # production_allocation.AccountAllocation.component values, e.g.
    # ("post", "vfx") for South Africa's QSAPPE), allocation_pricing.
    # price_segment() computes the REAL traced subtotal by summing this
    # segment's own real AccountAllocation lines whose `component` is in
    # this tuple (deduplicated by line_id) and bounds the claimed/derived
    # basis by THAT exact subtotal instead of the broad segment qpe_usd —
    # "0 <= claimed/derived QSAPPE <= exact qualifying allocated post/VFX
    # subtotal <= allocated/project spend". None (the default) preserves
    # the prior, coarser qpe_usd bound for any other is_component_basis
    # condition that has not yet been given its own traced line-component
    # set (e.g. us_or_opif's payroll/other split, unaffected by this
    # repair, out of its bounded scope).
    component_basis_line_components: tuple[str, ...] | None = None

    # Codex final Oregon full-pipeline completion (P0-OR-001, sixth
    # pass): component_basis_line_components matches on
    # AccountAllocation.component -- a LOCATION-ROUTING tag
    # (production_allocation.COMPONENT_BY_SPEND_CATEGORY maps to
    # "post"/"vfx"/"music"/"above_the_line"/"travel_and_living"/
    # "overhead"/"administration"/"principal_photography", never
    # "payroll"/"production"/"other"). The real production composer
    # NEVER emits a "payroll" component, so an Oregon condition keyed on
    # component_basis_line_components=("payroll",) can never match any
    # real, composer-produced allocation -- only hand-built test
    # fixtures. component_basis_spend_categories matches on the SAME
    # lines' own real spend_category instead (e.g. LABOR_CATEGORIES for
    # payroll) -- the genuinely correct, composer-reachable dimension
    # for Oregon's payroll/other split. None (the default) means this
    # condition uses component_basis_line_components (or neither).
    component_basis_spend_categories: tuple[str, ...] | None = None
    # When set alongside component_basis_spend_categories, matches every
    # traced line whose spend_category is NOT in that tuple (the
    # "other"/complement side of a two-condition split) instead of IN
    # it. False (the default) means "IN" (the payroll side).
    component_basis_spend_categories_exclude: bool = False

    # A genuinely EXECUTABLE boolean gate on a caller-evidenced fact (e.g.
    # preapproval granted, an award confirmed, a certificate issued). The
    # condition is satisfied only when `required_boolean_fact_key` is a
    # member of the `evidenced_facts` frozenset resolve_program_rate()
    # receives -- absence is UNKNOWN/unsatisfied, never assumed true.
    required_boolean_fact_key: str | None = None

    #: The inverse gate: when ANY of these evidenced facts is present the tier is ineligible. Used for a conditional scenario
    #: tier that must disappear once the producer evidences the alternative (e.g. NY post facility inside vs outside the
    #: Metropolitan Commuter Transportation District). Absence leaves the tier eligible as an unresolved scenario.
    blocked_by_boolean_fact_keys: tuple[str, ...] = ()

    # True (the default) when an unsatisfied amount_fact_min/
    # required_boolean_fact_key condition removes its OWN tier from
    # eligibility entirely (correct for an ordinary flat-rate/floor tier:
    # either the production genuinely qualifies for this rate or it does
    # not). Set False ONLY on a condition attached to a LONE band-ceiling
    # tier with no separate floor tier of its own (e.g. us_tx_miip's 31%
    # ceiling) -- there, removing the only tier from `eligible` on an
    # unsatisfied fact would make resolve_program_rate() return None
    # outright, losing the disclosed "up to X%, pending confirmation"
    # ceiling entirely. False keeps the tier eligible/selected and its
    # condition genuinely disclosed (satisfied=True only once evidenced),
    # relying on the EXISTING floorless-ceiling mechanism (see
    # resolve_program_rate/allocation_pricing._price_segment: "a floorless
    # ceiling whose conditions ARE all evaluable stays priced") to make it
    # genuinely price once every such condition resolves True, and to
    # keep it a disclosed-but-zero-guaranteed ceiling until then.
    gates_tier_eligibility: bool = True

    # Codex final-nine remediation: a native-currency threshold evaluated
    # DYNAMICALLY against the segment's OWN qpe_usd, converted at
    # resolution time via the real, dated, sourced FX snapshot
    # (production_normalization.FX_RATE_SNAPSHOTS, through
    # apply_fx_rates.convert_usd_to_local) -- never a fixed number baked
    # into this RateCondition at authoring time (that was the exact
    # "permanently-fixed USD substitute" defect Codex's audit named for
    # mt_mfc_rebate's EUR->USD57,026.20). Use this ONLY when the
    # threshold applies to the SAME quantity qpe_usd already represents
    # (e.g. mt_mfc_rebate's "minimum spend in Malta" IS the segment's own
    # Malta QPE) -- never for a threshold on a genuinely DIFFERENT
    # component the engine cannot derive from qpe_usd alone (that case is
    # amount_fact_key instead, e.g. fr_trip's VFX-specific spend, which
    # is a subset of total QPE, not the whole of it). Requires the
    # currency to actually be present in FX_RATE_SNAPSHOTS -- never
    # applied to an unsourced currency (that stays amount_fact_key,
    # evaluated purely natively with no conversion at all, e.g.
    # au_location_offset's AUD, ma_ccm_rebate's MAD).
    fx_native_currency: str | None = None
    fx_native_threshold_amount: float | None = None

    # Codex final P0 (th_film_incentive): "The 'above THB150m' 25% tier is
    # coded inclusive at exactly THB150m" -- the statutory language names
    # an ADJACENT tier boundary ("20% for THB100-150m; 25% ABOVE THB150m"),
    # where the lower tier's own upper bound is INCLUSIVE (>=100m and
    # <=150m) and the higher tier's threshold is EXCLUSIVE (>150m, never
    # >=150m). False (the default) keeps amount_fact_min's existing
    # inclusive (actual >= min) comparison, correct for every other
    # existing threshold in this codebase (none of which name an adjacent
    # boundary this way). True switches ONLY this condition's comparison
    # to strictly-greater-than (actual > min) -- never changes
    # amount_fact_max's own semantics, which stay inclusive on the lower
    # tier so THB150,000,000 exactly still selects the 20% tier, never
    # neither tier.
    amount_fact_min_exclusive: bool = False

    # SCENARIO local-labour inference (2026-10-02): names the kind of resident-labour percentage this condition's
    # amount_fact_key measures, so the ONE shared inference (services/scenario_local_labour.py) can derive it for a
    # hypothetical relocation when the producer has not evidenced it. "crew_resident_pct" = share of paid CREW (BTL
    # plus above-the-line crew) that are local residents. Cast residency is deliberately NOT inferable
    # (no basis); None = this condition is not a local-labour percentage.
    local_labour_basis: str | None = None

    # Codex final P0 (mt_mfc_rebate): "Certificate fact selects the 40%
    # RateResolution but unresolved limb conditions keep served selected
    # incentive at 30%." A discretionary_band condition (a CRITERION the
    # awarding authority weighs internally -- e.g. Malta's individual
    # +5%/+5% uplift limbs) always discloses satisfied=None on its own,
    # by design (the engine can never pre-evaluate a genuinely
    # discretionary criterion). But once a caller-evidenced fact naming
    # the AUTHORITATIVE AWARD ITSELF is present (e.g.
    # "mt_mfc_uplift_certificate_confirmed" — an actual Commissioner
    # certificate, not a prediction of one), that award IS the real-world
    # confirmation event; the individual criteria that led to it are no
    # longer separate engine-verifiable gates. Set ONLY on a
    # discretionary_band condition, naming the boolean fact key that,
    # once evidenced, supersedes this specific criterion's own
    # unresolved disclosure with a genuine satisfied=True. None (the
    # default) preserves the existing "always None" discretionary
    # disclosure for every condition without a real, separate awarded-
    # fact confirmation.
    superseded_by_boolean_fact_key: str | None = None

    # Codex final wiring remediation (P0-OR-001) — a MULTIPLICATIVE
    # regional/bonus uplift on the already-computed incentive dollar
    # value (e.g. Oregon's "an increase of 10 percent OF THE AMOUNT
    # otherwise allowable" — ORS 284.368 — confirmed multiplicative, NOT
    # +10 percentage points on the rate). When
    # regional_uplift_multiplier_fact_key is evidenced,
    # resolve_program_rate() carries regional_uplift_multiplier through
    # to RateResolution.incentive_uplift_multiplier; allocation_pricing.
    # price_segment() multiplies the rate x basis incentive by it AFTER
    # the base rate calculation and BEFORE the final dollar cap. None
    # (the default) means no uplift multiplier applies (1.0).
    regional_uplift_multiplier_fact_key: str | None = None
    regional_uplift_multiplier: float | None = None


@dataclass(frozen=True)
class SourceProvenance:
    """Structured, durable provenance for one executable economic rule —
    the canonical answer to "where did this number come from" that a
    free-text `citation` string alone does not let the engine query
    programmatically. Attached to a DoctrineRecord (and threaded through
    to every RateRule it derives via rate_rules_for()) so the trace
    PROGRAM -> EXECUTABLE RULE -> SOURCE PROVENANCE is a real object
    graph, not something that only exists in a comment or a report.

    All fields optional except issuing_authority — many legacy/secondary
    citations genuinely don't state a URL-path-level detail, an effective
    date, or a retrieval date, and recording that absence as None is more
    honest than fabricating one. `citation`/`source_ref` on the owning
    DoctrineRecord/RateRule remain the full free-text quote; this struct
    is the queryable index over that text, not a replacement for it."""
    issuing_authority: str          # the administering government/body itself
    source_url: str | None = None   # durable source identifier (page or document)
    citation_detail: str | None = None   # specific statute/section/page/quote anchor
    effective_date: str | None = None    # program/version/effective period, if stated
    verified_date: str | None = None     # verification/retrieval date, if stated
    interpretation_note: str | None = None  # material interpretation needed to
                                             # convert the authority into the rule


@dataclass(frozen=True)
class RateRule:
    """One rate tier of one program. is_band_ceiling=True means the
    source says 'up to' this rate — the exact awarded rate within the
    band is subject to the authority's assessment, so the rate is a
    modeling ceiling, not a guaranteed entitlement.

    graduated_brackets (optional): for a statute-confirmed MARGINAL/
    BRACKETED rate structure (e.g. Spain Art. 36.2: 30% on the first
    EUR 1M, 25% on the excess) — NOT a discretionary approval band like
    MU's 'up to 40%'. A tuple of (bracket_ceiling_usd, rate_in_bracket)
    pairs, applied progressively from 0. `rate` is the FINAL/marginal
    rate applied to any QPE above the last bracket ceiling (kept as a
    real field, not just the top of the tuple, so non-graduated callers
    are unaffected). When set, resolve_program_rate() computes a real
    BLENDED effective rate (total credit / QPE) instead of using `rate`
    flat — this is the maximum-lawful-incentive representation: neither
    the understated flat marginal rate nor an overstated flat top rate.
    """
    program_slug: str
    tier_id: str
    rate: float
    is_band_ceiling: bool
    production_types: tuple[str, ...]
    min_qpe_usd: float | None
    conditions: tuple[RateCondition, ...]
    confidence_tier: str     # DISCOVERY | PARSED | VERIFIED
    citation: str
    source_ref: str
    graduated_brackets: tuple[tuple[float, float], ...] | None = None
    provenance: SourceProvenance | None = None

    # Codex final P0 (us_tx_miip): "Award facts select only maximum 31%;
    # phased tiers and pool not executable" -- "Carry exact awarded
    # rate/tier as structured project fact and validate it against
    # authorized range/period." A TIER whose real award varies by
    # production (a discretionary/competitive fund awards a SPECIFIC
    # rate per production, not always the statutory ceiling) names the
    # caller-supplied numeric fact carrying that EXACT awarded rate
    # (a fraction, e.g. 0.24 for 24%) here -- resolve_program_rate() then
    # uses THIS value (not the tier's own static `rate`, which remains
    # the authorized CEILING for validation) as the modeled/floor rate.
    # A missing, malformed, or out-of-[awarded_rate_min, awarded_rate_max]
    # value fails this tier's eligibility closed -- never silently
    # substitutes the ceiling `rate` as a guessed default. None (the
    # default, every other program) means the tier's own static `rate` is
    # authoritative, unaffected by this mechanism.
    awarded_rate_fact_key: str | None = None
    awarded_rate_min: float | None = None
    awarded_rate_max: float | None = None


@dataclass(frozen=True)
class UnverifiedRateClaim:
    """A condition asserted by a NON-government source that could not be
    confirmed in any primary/government text reviewed. Recorded so the
    engine can disclose it as a risk item — never applied as a rule."""
    program_slug: str
    claim: str
    claimed_by: str
    verification_status: str


@dataclass(frozen=True)
class BudgetEvidencedRate:
    """A rate observed in an uploaded budget/financial model. Per RULE 1
    and RULE 2 this is NEVER an input to any calculation — it exists
    only so RULE 5 can report the conflict against the database rate."""
    program_slug: str
    rate: float
    observed_in: str


@dataclass(frozen=True)
class RateConflict:
    source_kind: str     # "budget_document" | "legacy_db_row"
    claimed_rate: float
    database_rate: float
    resolution: str
    detail: str


@dataclass(frozen=True)
class ConditionEvaluation:
    condition_id: str
    description: str
    quote: str
    satisfied: bool | None   # None = cannot be evaluated from known facts
    note: str
    condition_state: str = "AUTHORITY_UNRESOLVED"
    kind: str = ""   # the source RateCondition.kind — lets downstream consumers
                      # (e.g. canonical_evaluation.py's qualification propagation)
                      # filter by real condition semantics without re-deriving them.


# ── CBA-002: typed condition-kind terminal-state vocabulary ────────────────
# Every RateCondition.kind used anywhere in the canonical 71-program served
# universe terminates in EXACTLY one of these six states (Final Consolidated
# Backend Correction + Global Structuring Intelligence Acceptance, Section 2
# of the governing spec). This is a CLOSED, upfront, data-driven mapping
# decided once from each kind's real statutory meaning -- never a runtime
# string-match/prose-dependent heuristic. Adding a new kind means adding one
# row here (and, if EXECUTABLE, real evaluation logic in resolve_program_
# rate()) -- not adding another special case to the dispatch loop.
CONDITION_STATE_EXECUTABLE = "EXECUTABLE"
CONDITION_STATE_DISCLOSURE_ONLY = "DISCLOSURE_ONLY"
CONDITION_STATE_USER_FACT_REQUIRED = "USER_FACT_REQUIRED"
CONDITION_STATE_SCRIPT_FACT_REQUIRED = "SCRIPT_FACT_REQUIRED"
CONDITION_STATE_AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED"
CONDITION_STATE_NOT_APPLICABLE = "NOT_APPLICABLE"

#: kind -> terminal state. Kinds not listed here fall back to
#: AUTHORITY_UNRESOLVED (never silently NOT_APPLICABLE/EXECUTABLE) --
#: see resolve_program_rate()'s dispatch default.
CONDITION_KIND_STATE: dict[str, str] = {
    # Already executed deterministically at tier-selection time (pre-CBA-002).
    "production_type": CONDITION_STATE_EXECUTABLE,
    "min_qpe_usd": CONDITION_STATE_EXECUTABLE,
    "graduated_bracket_applied": CONDITION_STATE_EXECUTABLE,
    # A ceiling, not an entitlement -- the awarded rate within the "up to"
    # band is an authority discretion call at approval, never pre-satisfiable.
    "discretionary_band": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # Reclassified split of the former, over-broad, mis-tagged
    # "min_spend_pct_of_total_budget": the 2 real QPE-vs-total-budget ratio
    # conditions (Germany, UK) are genuinely EXECUTABLE once gross_budget_usd
    # is known; the 3 conditions that are actually a different ratio
    # (Ontario labour-vs-QPE, New York ATL-vs-other-QPE ceiling, Mexico
    # national-supply-chain-origin) are not this ratio at all and stay
    # unresolved; the 2 that are pure entity/fact gates (Egypt, Fiji) are
    # reclassified onto the existing project_fact_dependent_eligibility kind.
    "min_qpe_pct_of_total_budget": CONDITION_STATE_EXECUTABLE,
    "unmodeled_spend_split_ratio": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # Codex bounded remediation, B3 formulaic spec (SCHEMA_EXTENSION_
    # REQUIRED): a program whose real rate applies to a QPE SUB-COMPONENT
    # (e.g. Oregon's payroll vs. other-expense split) that this engine does
    # not track separately from total QPE. Genuinely different from
    # unmodeled_spend_split_ratio (a labour-vs-QPE RATIO gate) -- this is a
    # different RATE applying to a different BASE entirely, never
    # pre-applicable to total QPE without risking a blended-surrogate
    # misstatement.
    "component_basis_not_modeled": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # Statutory content/points-test certification, ownership/entity facts,
    # and similar eligibility gates the engine cannot pre-evaluate without a
    # project-specific fact the user (not the statute) supplies.
    "project_fact_dependent_eligibility": CONDITION_STATE_USER_FACT_REQUIRED,
    "project_fact_dependent_uplift": CONDITION_STATE_USER_FACT_REQUIRED,
    # Cultural point-table pass/fail is owned by the SEPARATE qualification
    # bridge (canonical_role_qualification_bridge.py / cultural_point_
    # tables.py), not the rate resolver -- disclosed here, never re-decided.
    "cultural_test_required": CONDITION_STATE_DISCLOSURE_ONLY,
    # The statute's real rate base is narrower than modeled QPE (e.g.
    # "qualified Canadian labour expenditure" vs total QPE) but the cited
    # source gives no cap percentage to apply (unlike CPTC, which does and
    # is EXECUTABLE via QPE_CAP_RULES at price_segment() time, upstream of
    # this per-condition evaluation) -- genuinely unresolved without a cap.
    "rate_base_narrower_than_qpe": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    "uplift_on_narrower_base_not_modeled": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # Whether QPE includes/excludes sponsorship/other financial assistance is
    # a real production fact never evidenced from the budget alone.
    "no_sponsorship_in_qpe": CONDITION_STATE_USER_FACT_REQUIRED,
    # A production choosing this program forecloses a named alternative --
    # informational; never blocks or auto-selects either program.
    "mutually_exclusive_alternative_program": CONDITION_STATE_DISCLOSURE_ONLY,
    "alternate_qualification_track": CONDITION_STATE_DISCLOSURE_ONLY,
    # Format-specific tier already fully expressed by the tier's own
    # production_types filter (e.g. Maryland TV-series uplift is its own
    # DoctrineRateTier) -- the condition itself is purely informational
    # once the tier has already been selected.
    "production_type_uplift": CONDITION_STATE_DISCLOSURE_ONLY,
    "sustainability_uplift": CONDITION_STATE_USER_FACT_REQUIRED,
    # Currency convertibility / capital-control risk on the minimum-spend
    # figure -- a genuine external fact, never modeled from statute alone.
    "min_spend_currency_not_convertible": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # Investor-side (not producer-QPE-side) rate proxy -- disclosed so it's
    # never mistaken for the producer's own modeled rate.
    "investor_side_rate_proxy_not_producer_qpe": CONDITION_STATE_DISCLOSURE_ONLY,
    "atl_subcap_not_enforced": CONDITION_STATE_AUTHORITY_UNRESOLVED,
    # A limit that the qualification register already applies line by line (e.g. NY above-the-line limits); shown for
    # provenance, never re-decided at rate-resolution time.
    "applied_in_qualification_register": CONDITION_STATE_DISCLOSURE_ONLY,
    # Funding availability/appropriation risk is a real, material,
    # non-statutory risk factor -- disclosed, never treated as a legal gate.
    "material_funding_risk_not_modeled": CONDITION_STATE_DISCLOSURE_ONLY,
    # A conflicting budget-document-derived rate claim, reported (never
    # substituted) per permanent Rules 1/2/5 -- disclosure only.
    "budget_document": CONDITION_STATE_DISCLOSURE_ONLY,
}


@dataclass(frozen=True)
class RateResolution:
    """The full, explainable outcome of resolving a program's rate for
    one production. modeled_rate is what the engine uses; floor_rate is
    the highest NON-band-ceiling tier the production also satisfies —
    the guaranteed fallback if the authority awards below the ceiling.

    has_guaranteed_floor is False when the program has NO non-band-ceiling
    tier at all. In that case there is no statutory floor to fall back on,
    and floor_rate is only the ceiling repeated — it must NOT be read as a
    guaranteed rate. A ceiling is a LIMIT, never evidence that the limit is
    awarded. Consumers that pay the floor deterministically must check this
    flag (see allocation_pricing._price_segment, which fails closed when a
    floorless ceiling also requires confirmation)."""
    program_slug: str
    modeled_rate: float
    floor_rate: float
    is_band_ceiling: bool
    tier_id: str
    basis: str
    conditions_evaluated: tuple[ConditionEvaluation, ...]
    unverified_claims: tuple[UnverifiedRateClaim, ...]
    conflicts: tuple[RateConflict, ...]
    has_guaranteed_floor: bool = True

    #: Codex final runtime remediation (us_or_opif component-basis model):
    #: the QPE figure the incentive dollar value should actually be
    #: computed against. Equal to the segment's own qpe_usd for every
    #: ordinary program (the overwhelming majority). Differs ONLY when the
    #: selected tier's rate is gated on a component-basis amount_fact (a
    #: sub-portion of the segment's spend, e.g. Oregon's payroll-only vs
    #: other-spend bases) rather than the segment's total QPE -- in that
    #: case this is the matched amount_fact's own value, so a 20% payroll
    #: rate is never multiplied against the segment's full (payroll +
    #: other) total. None means "use qpe_usd" (the ordinary case);
    #: callers should do `basis = resolution.qpe_basis_used
    #: if resolution.qpe_basis_used is not None else qpe_usd`.
    qpe_basis_used: float | None = None

    #: Codex final wiring remediation (P0-ZA-001, third pass) — carries
    #: the winning condition's own RateCondition.component_basis_line_
    #: components through to allocation_pricing.price_segment(), which
    #: uses it to bound qpe_basis_used by the EXACT classified allocated
    #: line subtotal (summed from the segment's own real AccountAllocation
    #: rows whose `component` is in this tuple) instead of the segment's
    #: broad qpe_usd. None (the default, including for every
    #: is_component_basis condition that predates this field, e.g.
    #: us_or_opif's payroll/other split) preserves the prior, coarser
    #: qpe_usd bound.
    qpe_basis_line_components: tuple[str, ...] | None = None

    #: Codex final wiring remediation (P0-OR-001) — a MULTIPLICATIVE
    #: uplift on the computed incentive dollar value, from the winning
    #: tier's own RateCondition.regional_uplift_multiplier (only when its
    #: regional_uplift_multiplier_fact_key is evidenced). None means no
    #: uplift (equivalent to 1.0) — allocation_pricing.price_segment()
    #: must never apply an ADDITIVE percentage-point interpretation.
    incentive_uplift_multiplier: float | None = None

    #: Codex final four-row remediation (P0-OR-001, fourth pass): "ONE
    #: composite calculation: payroll_QPE x 20% + other_QPE x 25%." Set
    #: ONLY by the dedicated Oregon (us_or_opif) composite branch of
    #: resolve_program_rate() when BOTH the payroll and other component
    #: facts are present -- the PRE-UPLIFT gross incentive dollar value,
    #: already summed across both disjoint bases (never a single-tier
    #: basis x rate figure). allocation_pricing.price_segment() must use
    #: this value directly (in place of the ordinary basis x rate
    #: computation) whenever it is not None, then apply the SAME
    #: incentive_uplift_multiplier / dollar-cap machinery every other
    #: program already uses. None (the default) leaves every other
    #: program's arithmetic byte-identical.
    composite_incentive_usd: float | None = None


# ── Mauritius EDB Film Rebate Scheme ────────────────────────────────────────

_MU_CITATION = (
    "EDB 'Film Rebate Scheme — Submission Procedures', 31 Jan 2020, "
    "citing the Economic Development Board (Film Rebate Scheme) "
    "Regulation 2018; corroborated by MCCI Film Rebate Scheme page."
)

MU_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="mu_edb_incentive",
        tier_id="mu_frs_30_general",
        rate=0.30,
        is_band_ceiling=False,
        production_types=(
            "feature_film", "creative_documentary", "digital_animated_film",
            "television_serial", "television_single_drama",
            "factual_television", "natural_history", "lifestyle_magazine",
            "commercial", "music_video", "dubbing",
        ),
        min_qpe_usd=100_000.0,  # foreign production, feature film ($50,000 local)
        conditions=(
            RateCondition(
                condition_id="mu30-qpe-local",
                description="QPE must be incurred locally",
                quote="30% rebate will be applicable on Qualifying Production "
                      "Expenditures (QPE) incurred locally and as described further below",
                kind="min_qpe_usd",
            ),
            RateCondition(
                condition_id="mu-no-sponsorship",
                description="Sponsorships/financial assistance for the Mauritian "
                            "schedule are excluded from the QPE quantum",
                quote="The QPE quantum should not include any forms of sponsorships "
                      "or financial assistance obtained for the Mauritian schedule "
                      "of the project.",
                kind="no_sponsorship_in_qpe",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MU_CITATION,
        source_ref="EDB-2020-Submission-Procedures",
        provenance=SourceProvenance(
            issuing_authority="Economic Development Board (Mauritius)",
            source_url="https://edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf",
            citation_detail="Film Rebate Scheme — Submission Procedures, 31 Jan 2020, "
                             "citing the Economic Development Board (Film Rebate Scheme) "
                             "Regulation 2018.",
            effective_date="2018",
            interpretation_note="Corroborated (no additional conditions) by the Mauritius "
                                 "Chamber of Commerce and Industry's Film Rebate Scheme page "
                                 "(mcci.org).",
        ),
    ),
    RateRule(
        program_slug="mu_edb_incentive",
        tier_id="mu_frs_40_feature",
        rate=0.40,
        is_band_ceiling=True,   # "Up to 40%" — exact rate within the band is discretionary
        production_types=("feature_film", "tv_series"),
        min_qpe_usd=1_000_000.0,
        conditions=(
            RateCondition(
                condition_id="mu40-feature",
                description="Must be a feature film production company "
                            "(or drama series at $150,000/episode)",
                quote="Up to 40% rebate will be applicable on Qualifying Production "
                      "Expenditures (QPE) incurred locally, and as described further "
                      "below, by a feature film production company, subject to a "
                      "minimum QPE of USD 1,000,000 for feature film; and a minimum "
                      "QPE of USD 150,000 per episode of a drama series.",
                kind="production_type",
            ),
            RateCondition(
                condition_id="mu40-min-qpe",
                description="Minimum QPE of USD 1,000,000 (feature film)",
                quote="Eligible for up to 40% rebate — Feature film (including "
                      "animation): 1,000,000 [Minimum QPE (USD), foreign and local "
                      "production]",
                kind="min_qpe_usd",
                threshold_usd=1_000_000.0,
            ),
            RateCondition(
                condition_id="mu40-band-discretion",
                description="'Up to' 40% — the awarded rate within the band is "
                            "subject to Film Rebate Committee assessment and CEO "
                            "approval; 40% is a modeling ceiling, not an entitlement",
                quote="The purpose of the Film Rebate Committee will be to assess "
                      "projects in terms of its economic benefits ... and provide "
                      "recommendations to the Chief Executive Officer who shall "
                      "approve projects.",
                kind="discretionary_band",
            ),
            RateCondition(
                condition_id="mu-no-sponsorship",
                description="Sponsorships/financial assistance for the Mauritian "
                            "schedule are excluded from the QPE quantum",
                quote="The QPE quantum should not include any forms of sponsorships "
                      "or financial assistance obtained for the Mauritian schedule "
                      "of the project.",
                kind="no_sponsorship_in_qpe",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MU_CITATION,
        source_ref="EDB-2020-Submission-Procedures",
        provenance=SourceProvenance(
            issuing_authority="Economic Development Board (Mauritius)",
            source_url="https://edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf",
            citation_detail="Film Rebate Scheme — Submission Procedures, 31 Jan 2020, "
                             "citing the Economic Development Board (Film Rebate Scheme) "
                             "Regulation 2018.",
            effective_date="2018",
            interpretation_note="The 40% ceiling is a Film Rebate Committee/CEO "
                                 "discretionary approval band, not a guaranteed rate — "
                                 "see mu40-band-discretion's own condition.",
        ),
    ),
)

# Conditions asserted by non-government sources only. Searched for and
# NOT found in the primary Submission Procedures document or MCCI's
# corroborating page (both reviewed verbatim). Disclosed, never applied.
MU_UNVERIFIED_CLAIMS: tuple[UnverifiedRateClaim, ...] = (
    UnverifiedRateClaim(
        program_slug="mu_edb_incentive",
        claim="The 40% tier requires 90% of filming to take place in Mauritius.",
        claimed_by="identicalpictures.com (production-services/fixer site); no "
                   "government source or regulation cited for the claim",
        verification_status="RESOLVED — REJECTED. Incentive/Optimizer Core Closeout "
                            "final rule resolution "
                            "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §1.1, "
                            "cross-checked against docs/validation/"
                            "GEMINI_FINAL_RULE_RESOLUTION.md §1 where the two final "
                            "resolutions conflicted): the 90% condition belongs to a "
                            "SEPARATE measure — the Government's 2023/24 Budget "
                            "double deduction available to LOCAL companies "
                            "financing/sponsoring/marketing/distributing an approved "
                            "film — not to the EDB Film Rebate Scheme's 40% uplift, "
                            "per the National Assembly Hansard (14 May 2019) "
                            "explaining Regulations 2018 and the current EDB "
                            "submission guidance, neither of which attaches a 90% "
                            "production test to the rebate uplift. Codex's resolution "
                            "was preferred over Gemini's contrary (unsourced) answer "
                            "because it cites a specific parliamentary record and "
                            "dated primary guidance pages; Gemini's answer cited only "
                            "a generic, non-specific guidelines reference. NOT "
                            "enforced as a gate (confirmed correct, not merely "
                            "un-enforced).",
    ),
    UnverifiedRateClaim(
        program_slug="mu_edb_incentive",
        claim="Remuneration paid to foreign cast and crew must not exceed 40% of "
              "the total production budget allocated to Mauritius.",
        claimed_by="secondary trade sources (search results); no government "
                   "source cited",
        verification_status="NOT FOUND in the primary documents reviewed. Requires "
                            "EDB written confirmation.",
    ),
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # Same class of non-government "fixer"/production-services secondary
    # source as the already-REJECTED 90% claim above -- not corroborated by
    # any government/parliamentary source found this pass. Disclosed per
    # the same discipline, never applied as a gate or cultural test.
    UnverifiedRateClaim(
        program_slug="mu_edb_incentive",
        claim="Lead cast must verbally mention 'Mauritius' as part of scripted "
              "dialogue; the production must credit the EDB and 'Film In "
              "Mauritius' logo in end credits; and must submit a 3-minute video "
              "testimonial from the producer/director/lead cast.",
        claimed_by="identicalpictures.com and soph-oria.com (production-services/"
                   "fixer sites); no EDB or government source cited for these "
                   "specific conditions",
        verification_status="NOT FOUND in the VERIFIED-tier EDB Submission "
                            "Procedures document already on file in this repository. "
                            "Requires EDB written confirmation before being treated as "
                            "a real qualification gate or SCRIPT_FACT_REQUIRED trigger.",
    ),
)

# Rates observed in production documents — Rule 1/2 data, never inputs.
MU_BUDGET_EVIDENCED_RATES: tuple[BudgetEvidencedRate, ...] = (
    BudgetEvidencedRate(
        program_slug="mu_edb_incentive",
        rate=0.35,
        observed_in="Little Utopia production budget line 'EDB Rebate at 35%: "
                    "$(1,275,411)' (also mirrored into migration 0009's "
                    "base_rate=0.35 row, itself budget-evidenced, not "
                    "statute-verified)",
    ),
)


## ── Malta, Ireland, Greece: PARSED-tier conversions ─────────────────────────
#
# Executable Jurisdiction Knowledge phase. Source: jurisdiction_comparison.py's
# own MALTA/IRELAND/GREECE JurisdictionIncentiveProfile records —
# confidence_tier="PARSED" (rates/caps already confirmed from a primary
# source per that module's own discipline: "Do not promote any cell to
# True without a primary-source citation"). This is a CONNECTION of
# already-vetted data to the rate-resolution engine, not new legal
# research — nothing here is invented.
#
# EUR->USD thresholds computed via the EXISTING FX engine
# (apply_fx_rates.convert_to_usd), using the real sourced snapshot rate
# on file (production_normalization.FX_RATE_SNAPSHOTS, EUR=0.87679,
# fetched 2026-07-13) — never a rough/rounded guess.
#   MT min spend  EUR 50,000   -> USD 57,026.20
#   IE min spend  EUR 125,000  -> USD 142,565.49
#   IE cap        EUR 70,000,000 (or 80% of budget, whichever lower) -> USD 79,836,676.97
#   GR min spend  EUR 100,000  -> USD 114,052.40

_MT_CITATION = (
    "CORRECTED 2026-07-26 via Document Retrieval Escalation: the prior "
    "citation here (25% base + three stacked uplifts of +3%/+3%/+7%, "
    "undated, traced only to this repository's own jurisdiction_comparison.py "
    "PARSED-tier notes) is SUPERSEDED. A prior session had downloaded the "
    "real MFC 'Financial Incentives for the Audiovisual Industry: CASH "
    "REBATE GUIDELINES' (Official Document, January 2019, 28 pages) but a "
    "tool parser limitation produced hallucinated placeholder analysis "
    "instead of the real text -- classified precisely as a PARSER FAILURE, "
    "not a retrieval failure, per the Document Retrieval Escalation "
    "doctrine. This session recovered the actual saved PDF and extracted "
    "its real text directly via pypdf, confirming the TRUE rate structure "
    "below. Full detail in app.data.program_requirements mt_mfc_rebate. "
    "Codex final runtime remediation (mt_mfc_rebate, B3:mt_mfc_rebate): "
    "Codex's own accepted manifest controls a EUR 50,000 minimum spend "
    "threshold, superseding this session's earlier preservation of the "
    "PDF-extracted EUR 100,000 / S.2.3 figure. The verbatim S.2.3 quote "
    "below is left UNCHANGED (it genuinely says EUR 100,000 and altering "
    "a verbatim quote would misrepresent the source). Codex's final-nine "
    "audit found the prior pass's EUR->USD conversion (57,026.20) was a "
    "permanently-fixed USD substitute baked into this RateCondition at "
    "authoring time, contrary to the controlling native-currency "
    "requirement. The 'minimum spend in Malta' threshold applies to the "
    "SAME quantity qpe_usd already represents (Malta QPE), so it is now "
    "evaluated via fx_native_currency/fx_native_threshold_amount: the "
    "segment's own qpe_usd is converted to EUR DYNAMICALLY at resolution "
    "time via the real, dated, sourced FX snapshot (production_"
    "normalization.FX_RATE_SNAPSHOTS[\"2026-07-13\"][\"EUR\"]=0.87679), "
    "compared against the native EUR 50,000 minimum -- never a fixed "
    "number baked in ahead of time, and never a new fact the real "
    "production must separately supply (Codex's own acceptance record "
    "expects this program to keep auto-pricing from real project data: "
    "'Candidate prices base'). The 40% ceiling tiers additionally gate on "
    "a caller-evidenced Commissioner uplift-certificate fact "
    "(\"mt_mfc_uplift_certificate_confirmed\") -- absent one, the two "
    "discretionary limb conditions remain disclosed but never auto-"
    "priced, matching \"40% lacks certificate fact\"."
)
MT_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-general-30",
        rate=0.30, is_band_ceiling=False,
        production_types=("feature_film", "tv_series", "creative_documentary"),
        min_qpe_usd=None,  # native EUR 50,000 gate below (Codex final-nine remediation)
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case) — "
                            "EUR 50,000 per Codex's controlling final-runtime ruling "
                            "(supersedes the source document's own EUR 100,000 figure); "
                            "overall production budget must additionally exceed EUR 200,000",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="project_fact_dependent_eligibility",
                fx_native_currency="EUR",
                fx_native_threshold_amount=50_000.0,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " Category A (all qualifying productions except "
                 "Animation/VFX): 30% base on all eligible expenditure for non-Maltese "
                 "productions (S.3.2.1).",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
        provenance=SourceProvenance(
            issuing_authority="Malta Film Commission",
            citation_detail="'Financial Incentives for the Audiovisual Industry: "
                             "CASH REBATE GUIDELINES' (Official Document, January "
                             "2019, 28pp), S.3.2.1 -- 30% base on all eligible "
                             "expenditure for non-Maltese productions.",
            effective_date="2019-01",
            verified_date="2026-07-26",
            interpretation_note="The official MFC PDF was recovered from this "
                                 "repository's own saved copy and its real text "
                                 "extracted directly via pypdf, superseding an "
                                 "earlier hallucinated placeholder analysis "
                                 "(a PARSER failure, not a retrieval failure). "
                                 "Rate structure and section anchors below come "
                                 "from that extracted primary text; full detail "
                                 "in program_requirements.mt_mfc_rebate.",
        ),
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-general-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("feature_film", "tv_series", "creative_documentary"),
        min_qpe_usd=None,  # native EUR 50,000 gate below (Codex final-nine remediation)
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case) — "
                            "EUR 50,000 per Codex's controlling final-runtime ruling "
                            "(supersedes the source document's own EUR 100,000 figure)",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="project_fact_dependent_eligibility",
                fx_native_currency="EUR",
                fx_native_threshold_amount=50_000.0,
            ),
            # Codex final-nine remediation (mt_mfc_rebate, P0): "40% lacks
            # certificate fact." A genuine, caller-evidenced Commissioner
            # uplift-certificate gate makes the 40% ceiling actually
            # resolvable, distinct from the two limb conditions below
            # (which remain disclosure-only -- limb (a) has no published
            # objective points test at all, and limb (b)'s Annex 1
            # benchmarks are evidence criteria, not a self-executing
            # formula, per the Codex final rule resolution already cited
            # in this record's citation).
            RateCondition(
                condition_id="mt-uplift-certificate",
                description="The 40% ceiling requires the Commissioner to "
                            "have actually certified/awarded the combined "
                            "uplift limbs for this production — evaluated "
                            "against a caller-evidenced certificate fact, "
                            "never assumed",
                quote="The Commissioner has the discretion to award an "
                      "additional 10% (5%+5%) ... (MFC Cash Rebate "
                      "Guidelines, Jan 2019, S.3.4)",
                kind="project_fact_dependent_eligibility",
                required_boolean_fact_key="mt_mfc_uplift_certificate_confirmed",
            ),
            # Codex final P0 (mt_mfc_rebate): "Certificate fact selects the
            # 40% RateResolution but unresolved limb conditions keep
            # served selected incentive at 30%." superseded_by_boolean_
            # fact_key names the SAME mt-uplift-certificate gate above --
            # once the Commissioner's actual certificate is evidenced, the
            # individual criteria the Commissioner weighed internally are
            # no longer separate unresolved engine gates; the certificate
            # IS the authoritative awarded-rate confirmation.
            RateCondition(
                condition_id="mt-uplift-limb-a-malta-as-malta",
                description="Limb (a), +5%: Malta portrayed as Malta, or local "
                            "usage of facilities — Commissioner-discretionary, "
                            "no published objective points test for this limb",
                quote="Malta features as Malta or local usage of facilities [5%] "
                      "(MFC Cash Rebate Guidelines, Jan 2019, S.3.4; confirmed "
                      "current per Screen Malta Financial Incentives Guidelines "
                      "2024, S.3.4)",
                kind="discretionary_band",
                superseded_by_boolean_fact_key="mt_mfc_uplift_certificate_confirmed",
            ),
            RateCondition(
                condition_id="mt-uplift-limb-b-local-resources",
                description="Limb (b), +5%: maximisation of local resources — "
                            "Annex 1 gives objective minimum local-crew "
                            "percentages by department (e.g. Production 80%, "
                            "Direction 60%, Locations & Unit 90%, Camera 50%, "
                            "Transport 90%) as EVIDENCE criteria, not a "
                            "self-executing points formula; final award still "
                            "requires Commissioner assessment and audit at "
                            "final submission",
                quote="Maximisation of local resources [5%] ... Annex 1 "
                      "(Screen Malta Financial Incentives Guidelines 2024, "
                      "S.3.4 and Annex 1)",
                kind="discretionary_band",
                superseded_by_boolean_fact_key="mt_mfc_uplift_certificate_confirmed",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " 40% ceiling requires the Commissioner to award both "
                 "independent 5% discretionary limbs on top of the 30% base — the "
                 "guaranteed floor is the 30% base tier. Per the Incentive/Optimizer "
                 "Core Closeout final rule resolution "
                 "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §4.1): limb (b) has "
                 "objective department-level local-crew benchmarks (Annex 1) that "
                 "function as evidence, not an automatic-award formula — final "
                 "certificate percentage controls either way.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
        provenance=SourceProvenance(
            issuing_authority="Malta Film Commission",
            citation_detail="'Financial Incentives for the Audiovisual Industry: "
                             "CASH REBATE GUIDELINES' (Official Document, January "
                             "2019, 28pp), S.3.2.1 -- 30% base on all eligible "
                             "expenditure for non-Maltese productions.",
            effective_date="2019-01",
            verified_date="2026-07-26",
            interpretation_note="The official MFC PDF was recovered from this "
                                 "repository's own saved copy and its real text "
                                 "extracted directly via pypdf, superseding an "
                                 "earlier hallucinated placeholder analysis "
                                 "(a PARSER failure, not a retrieval failure). "
                                 "Rate structure and section anchors below come "
                                 "from that extracted primary text; full detail "
                                 "in program_requirements.mt_mfc_rebate.",
        ),
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-animation-25",
        rate=0.25, is_band_ceiling=False,
        production_types=("animation", "digital_animated_film"),
        min_qpe_usd=None,  # native EUR 50,000 gate below (Codex final-nine remediation)
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case) — "
                            "EUR 50,000 per Codex's controlling final-runtime ruling "
                            "(supersedes the source document's own EUR 100,000 figure)",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="project_fact_dependent_eligibility",
                fx_native_currency="EUR",
                fx_native_threshold_amount=50_000.0,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " Category B (Animation/VFX): 25% base on all eligible "
                 "expenditure (S.3.2.1) — a DIFFERENT, lower base rate than the general "
                 "Category A tier; scoped as its own record since production_types is "
                 "record-level, not tier-level.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
        provenance=SourceProvenance(
            issuing_authority="Malta Film Commission",
            citation_detail="'Financial Incentives for the Audiovisual Industry: "
                             "CASH REBATE GUIDELINES' (Official Document, January "
                             "2019, 28pp), S.3.2.1 -- 30% base on all eligible "
                             "expenditure for non-Maltese productions.",
            effective_date="2019-01",
            verified_date="2026-07-26",
            interpretation_note="The official MFC PDF was recovered from this "
                                 "repository's own saved copy and its real text "
                                 "extracted directly via pypdf, superseding an "
                                 "earlier hallucinated placeholder analysis "
                                 "(a PARSER failure, not a retrieval failure). "
                                 "Rate structure and section anchors below come "
                                 "from that extracted primary text; full detail "
                                 "in program_requirements.mt_mfc_rebate.",
        ),
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-animation-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("animation", "digital_animated_film"),
        min_qpe_usd=None,  # native EUR 50,000 gate below (Codex final-nine remediation)
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case) — "
                            "EUR 50,000 per Codex's controlling final-runtime ruling "
                            "(supersedes the source document's own EUR 100,000 figure)",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="project_fact_dependent_eligibility",
                fx_native_currency="EUR",
                fx_native_threshold_amount=50_000.0,
            ),
            # Codex final-nine remediation: same certificate gate as the
            # general-case ceiling above.
            RateCondition(
                condition_id="mt-uplift-certificate",
                description="The 40% ceiling requires the Commissioner to "
                            "have actually certified/awarded the combined "
                            "uplift for this production — evaluated "
                            "against a caller-evidenced certificate fact, "
                            "never assumed",
                quote="The Commissioner has the discretion to award an "
                      "additional 15% ... Maximum Rebate: 40% (MFC Cash "
                      "Rebate Guidelines, Jan 2019, S.3.2.1)",
                kind="project_fact_dependent_eligibility",
                required_boolean_fact_key="mt_mfc_uplift_certificate_confirmed",
            ),
            RateCondition(
                condition_id="mt-uplifts-animation",
                description="Maximum rate requires Commissioner discretion on the "
                            "combined criteria, not a guaranteed entitlement",
                quote="The Commissioner has the discretion to award an additional 15% "
                      "based on the Maltese cultural elements and on the maximisation "
                      "of local resources. Maximum Rebate: 40% (MFC Cash Rebate "
                      "Guidelines, Jan 2019, S.3.2.1)",
                kind="discretionary_band",
                superseded_by_boolean_fact_key="mt_mfc_uplift_certificate_confirmed",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " 40% ceiling for Animation/VFX requires the full 15% "
                 "Commissioner-discretionary uplift on top of the 25% base.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
        provenance=SourceProvenance(
            issuing_authority="Malta Film Commission",
            citation_detail="'Financial Incentives for the Audiovisual Industry: "
                             "CASH REBATE GUIDELINES' (Official Document, January "
                             "2019, 28pp), S.3.2.1 -- 30% base on all eligible "
                             "expenditure for non-Maltese productions.",
            effective_date="2019-01",
            verified_date="2026-07-26",
            interpretation_note="The official MFC PDF was recovered from this "
                                 "repository's own saved copy and its real text "
                                 "extracted directly via pypdf, superseding an "
                                 "earlier hallucinated placeholder analysis "
                                 "(a PARSER failure, not a retrieval failure). "
                                 "Rate structure and section anchors below come "
                                 "from that extracted primary text; full detail "
                                 "in program_requirements.mt_mfc_rebate.",
        ),
    ),
    # NOTE: 'Difficult Audiovisual Work' (up to 50%, MFC Cash Rebate Guidelines
    # Jan 2019 S.3.2.2/S.3.3) is DELIBERATELY NOT modeled as a RateRule tier.
    # It requires a MAXIMUM total budget of EUR 1,500,000 -- a ceiling
    # condition -- but RateRule/resolve_program_rate() only supports MINIMUM
    # thresholds (min_qpe_usd). Modeling it as a normal tier would make
    # resolve_program_rate() select it as the highest-rate match for ANY
    # Malta production above the EUR 50,000 floor, regardless of actual
    # budget size -- a genuine correctness bug caught during the account-
    # handoff repository consistency audit (2026-07-26) and deliberately
    # avoided rather than shipped. Disclosed as additional_facts only, in
    # both app.data.program_requirements (mt_mfc_rebate) and
    # jurisdiction_comparison.py's MALTA profile -- never priced.
)

_IE_CITATION = (
    "Section 481 Film Tax Credit. Independently fetched revenue.ie "
    "(Revenue Commissioners Ireland, official) directly this task, "
    "verbatim: 'Credit Rate: 32% of whichever is the lowest of' "
    "eligible expenditure, '80% of total qualifying film production "
    "costs,' or a certification-date-dependent cap -- 'EUR 125 million "
    "(for projects certified on or after 28 March 2024) or EUR 70 "
    "million (for earlier certifications).' Confirms the pre-existing "
    "jurisdiction_comparison.py IRELAND profile's 32% flat rate exactly "
    "and CORRECTS the cap figure (previously recorded as a flat EUR "
    "70,000,000 for all certifications -- now confirmed to be EUR 125M "
    "for current-era certifications). Cultural test points system "
    "remains unverified from this fetch (disclosed gap)."
)
IE_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="ie_section_481", tier_id="ie-flat-32",
        rate=0.32, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=142_565.49,
        conditions=(
            RateCondition(
                condition_id="ie-min-spend",
                description="Minimum qualifying Irish expenditure",
                quote="min_spend_local=EUR 125,000 (jurisdiction_comparison.py "
                      "IRELAND profile, PARSED tier)",
                kind="min_qpe_usd", threshold_usd=142_565.49,
            ),
            RateCondition(
                condition_id="ie-cultural-test",
                description="Cultural test required (Irish Qualifying Test) — a "
                            "threshold eligibility gate, not a points contribution "
                            "to this rate; passing threshold/points system itself "
                            "unverified from primary source (disclosed data gap)",
                quote="Cultural test required (Irish Qualifying Test). ... cultural "
                      "test points system unverified. (jurisdiction_comparison.py "
                      "IRELAND profile notes, PARSED tier)",
                kind="cultural_test_required",  # falls into resolve_program_rate()'s
                # generic fact-dependent else-branch (any kind other than the three
                # explicitly dispatched ones) — satisfied=None, never silently assumed.
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_IE_CITATION + " 32% flat refundable tax credit (not tiered — "
                 "base_rate == max_rate). Cap: 80% of budget or the "
                 "certification-date-dependent EUR cap above, whichever is "
                 "lower — this cap is on QUALIFYING SPEND, not on the rate "
                 "itself, and is NOT enforced by this rate-tier model "
                 "(disclosed, not silently applied); see program's "
                 "data_gaps.",
        source_ref="revenue.ie-official-direct-fetch",
        provenance=SourceProvenance(
            issuing_authority="Revenue Commissioners Ireland",
            source_url="https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx",
            citation_detail="'Credit Rate: 32% of whichever is the lowest "
                             "of' eligible expenditure, 80% of qualifying "
                             "costs, or the EUR cap",
            effective_date="EUR 125M cap for projects certified on or "
                            "after 2024-03-28; EUR 70M for earlier "
                            "certifications",
            verified_date="2026-08-17",
            interpretation_note="Cultural test (Irish Qualifying Test) "
                                 "points-scoring thresholds not published "
                                 "on this page and remain unverified -- "
                                 "only the rate/cap figures are VERIFIED.",
        ),
    ),
)

_GR_CITATION = (
    "Greece Cash Rebate for International Productions. Rate (40%, flat; "
    "fiction works must also score at least 23 of 50 cultural-criteria "
    "points -- KYA 607434 Annex I Table A, see cultural_point_tables) "
    "sourced via jurisdiction_comparison.py GREECE "
    "profile (Enterprise Greece / Greek Film Centre, enterprisegreece.gov.gr). "
    "Minimum-spend threshold and the 80% eligible-spend cap (see "
    "program_rate_rules.QPE_CAP_RULES['gr_cash_rebate']) updated per the "
    "Incentive/Optimizer Core Closeout final rule resolution "
    "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §2), itself sourced to "
    "JMD 607434 (Government Gazette B' 87/14.01.2026, arts. 4-6) as amended "
    "by JMD 140524 (Gazette B' 2204/20.04.2026): fiction film/TV film floor "
    "is EUR 200,000 minimum eligible Greek spend AND EUR 400,000 minimum "
    "total production budget — both floors apply, neither substitutes for "
    "the other."
)
GR_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="gr_cash_rebate", tier_id="gr-flat-40",
        rate=0.40, is_band_ceiling=False,
        production_types=("feature_film",),
        # EUR 200,000 fiction-film floor, converted at the same implied
        # EUR/USD ratio (1.140524) already committed to by this program's
        # prior EUR 100,000 -> USD 114,052.40 figure — not a new/fabricated
        # rate, the program's own existing conversion basis reapplied to
        # the corrected threshold.
        min_qpe_usd=228_104.80,
        conditions=(
            RateCondition(
                condition_id="gr-min-spend",
                description="Minimum qualifying Greek expenditure (fiction film/TV film)",
                quote="Minimum eligible Greek spend EUR 200,000 for fiction film/TV "
                      "film (JMD 607434 art. 6 threshold table, as amended by JMD "
                      "140524)",
                kind="min_qpe_usd", threshold_usd=228_104.80,
            ),
            # PROJECT_OPEN_ITEM_RECOVERY G-09 / Q40: the served Greek QPE presumes every non-excluded account is incurred in the
            # Greek territory (the statute taxes only expenses "incurred in the Greek territory"; no per-account Greek-incurrence
            # schedule exists in any retained record). Disclose that presumption instead of presenting it as confirmed. Non-gating:
            # it names the missing facts without blocking or changing the modeled rate.
            RateCondition(
                condition_id="gr-local-incurrence-schedule",
                description="Eligible expenses must be incurred in the Greek territory and be paid and invoiced to the beneficiary "
                            "(KYA 607434 Annex B.1, B.2). The modeled QPE presumes every non-excluded account is Greek-incurred; "
                            "foreign-issued invoices for the director and the two leads are available only above EUR 8,000,000 of "
                            "eligible expense (Law 4487/2017 Art. 26(3) as amended by Law 5043/2023 Art. 61; KYA Art. 5(2)) and, "
                            "for Action A, only where the work was performed entirely in Greece (Annex IV evidence rules).",
                quote="eligible expenses are production expenses 'incurred in the Greek Territory' (Law 4487/2017 Art. 26(1)); "
                      "'implemented in the Greek territory' (KYA 607434 Art. 5(1))",
                kind="project_fact_dependent_eligibility",
                required_boolean_fact_key="gr_local_incurrence_schedule_evidenced",
                gates_tier_eligibility=False,
            ),
            RateCondition(
                condition_id="gr-application-date-and-regime",
                description="Eligibility starts on the application submission date; works that began earlier make the whole plan "
                            "ineligible except preparatory production work (KYA 607434 Art. 5(3)). The governing text depends on "
                            "that date: Law 4487/2017 as amended by Law 5043/2023 (A' 91/13.04.2023), Law 5105/2024 (A' 61) with "
                            "KYA 6376/2025, or KYA 607434 (B' 87/14.01.2026). The modeled caps use the current KYA.",
                quote="'The start date of eligibility of expenses is the date of submission of the funding application' "
                      "(KYA 607434 Art. 5(3))",
                kind="project_fact_dependent_eligibility",
                required_boolean_fact_key="gr_application_date_and_regime_evidenced",
                gates_tier_eligibility=False,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_GR_CITATION,
        source_ref="JMD-607434-art-6-CODEX-final-resolution",
        provenance=SourceProvenance(
            issuing_authority="Hellenic Republic — Joint Ministerial Decision "
                               "607434 (Government Gazette B' 87/14.01.2026), "
                               "administered by Enterprise Greece / Greek Film "
                               "Centre",
            source_url="https://www.enterprisegreece.gov.gr",
            citation_detail="JMD 607434, arts. 4-6: minimum eligible Greek "
                             "spend EUR 200,000 (fiction film/TV film); 40% "
                             "flat rebate rate.",
            effective_date="2026-01-14",
            interpretation_note="80% eligible-spend cap applied separately via "
                                 "QPE_CAP_RULES['gr_cash_rebate'], same JMD "
                                 "source.",
        ),
    ),
)


## ── Spain: Article 36.2 LIS foreign-production deduction ────────────────────
#
# Source: Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades
# (BOE-A-2014-12328), Artículo 36.2 — the deduction for foreign productions
# filming in Spain. Verbatim text confirmed from TWO independent legal-
# database reproductions of the consolidated statute (iberley.es and a
# web-search-corroborated summary of the same law), not a raw self-fetched
# BOE.es document — hence PARSED, not VERIFIED, matching this file's own
# tier discipline.
#
# CORRECTION OF A PRIOR DISCOVERY-TIER ERROR: an earlier pass (recorded in
# jurisdiction_comparison.py's ES profile, confidence_tier=DISCOVERY) also
# surfaced a contradicting 15% figure from a partial BOE preamble fetch —
# that figure was not the operative Article 36.2 rate (likely a pre-
# amendment or misattributed figure) and is superseded by the verbatim
# text below.
#
# REAL, STATUTE-QUOTED STRUCTURE (not a flat rate): "Del 30 por ciento
# respecto del primer millón de base de la deducción y del 25 por ciento
# sobre el exceso" — 30% on the first EUR 1,000,000 of the deduction base,
# 25% on any excess. CORRECTED (worldwide population phase, maximum-
# lawful-incentive review): previously modeled at a flat conservative 25%
# because RateRule had no way to represent a graduated bracket. That
# understated the real, confirmed 30% first-bracket benefit — not the
# "narrowest reusable" representation the project now requires. RateRule
# gained an optional `graduated_brackets` field
# (program_rate_rules.py, RateRule docstring) purely additive, every
# other program unaffected — and resolve_program_rate() now computes a
# real BLENDED effective rate (total credit / QPE) for Spain: for Little
# Utopia's ~$4.36M QPE this comes to ~26.3%, correctly between the flat
# 25% (understates) and flat 30% (overstates) figures.
#
# NOT MODELED — genuine disclosed gap, not a guess: the Canary Islands
# enhanced rate (widely reported at 50%/45% by secondary sources and by
# jurisdiction_comparison.py's own prior DISCOVERY-tier notes) does NOT
# appear anywhere in Article 36 — confirmed by requesting the complete,
# all-subsection text of Article 36 (36.1/36.2/36.3) and finding no
# Canary Islands reference. It must derive from Canary Islands' separate
# special economic/fiscal regime (Régimen Económico y Fiscal de
# Canarias), which has not been located or read. Recorded below as an
# UnverifiedRateClaim — never applied as a rule.
#
# Spend-category / QPE doctrine: Article 36.2 names only two enumerated
# cost categories for the deduction base — creative-personnel costs (with
# an EEA/Spain fiscal-residency condition) and technical-industry/
# supplier costs — and defers further qualifying-expense detail to an
# unretrieved Orden Ministerial ("Reglamentariamente se podrán establecer
# otros requisitos..."). This is NOT enough primary-source basis to
# classify a QualificationDoctrine (OPEN_DEFAULT_INCLUDE vs.
# CLOSED_POSITIVE_LIST would both be a guess without that order's text).
# Intentionally left unclassified in program_spend_rules.py — a disclosed
# gap, not a silent default, per that module's own documented behavior
# for an unclassified program_slug.

_ES_CITATION = (
    "Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades "
    "(BOE-A-2014-12328), Artículo 36.2 — deducción por producciones "
    "extranjeras. Verbatim: 'Del 30 por ciento respecto del primer "
    "millón de base de la deducción y del 25 por ciento sobre el "
    "exceso.' Min spend: 'los gastos realizados en territorio español "
    "sean, al menos, de 1 millón de euros ... en el supuesto de "
    "producciones de animación tales gastos serán, al menos, de "
    "200.000 euros.' Cap: 'El importe de esta deducción no podrá ser "
    "superior a 20 millones de euros, por cada producción realizada' "
    "(10 millones de euros por episodio para series). Registration: "
    "productores inscritos en el Registro Administrativo de Empresas "
    "Cinematográficas y Audiovisuales (ICAA)."
)
ES_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="es_tax_credit_foreign", tier_id="es-graduated-30-25",
        rate=0.25, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=1_140_523.96,
        conditions=(
            RateCondition(
                condition_id="es-min-spend",
                description="Minimum qualifying Spanish expenditure (EUR "
                            "200,000 for animation — not modeled as a "
                            "separate production_type tier here)",
                quote="los gastos realizados en territorio español sean, "
                      "al menos, de 1 millón de euros (Art. 36.2 LIS)",
                kind="min_qpe_usd", threshold_usd=1_140_523.96,
            ),
            RateCondition(
                condition_id="es-bracket-blended",
                description="Statute rate is bracketed (30% first EUR 1M, "
                            "25% excess) — a real, confirmed graduated "
                            "structure, not a discretionary approval band. "
                            "resolve_program_rate() computes a genuine "
                            "blended effective rate from this bracket "
                            "(total credit / QPE), not a flat rate",
                quote="Del 30 por ciento respecto del primer millón de "
                      "base de la deducción y del 25 por ciento sobre "
                      "el exceso (Art. 36.2 LIS)",
                kind="graduated_bracket_applied",
            ),
        ),
        # Global Economic Data + Base Pricing, batch 3: promoted PARSED ->
        # VERIFIED. Citation is a direct verbatim quote of the actual
        # statute (Ley 27/2014, Articulo 36.2, BOE-A-2014-12328) -- the
        # strongest possible provenance tier this registry recognizes.
        confidence_tier="VERIFIED",
        citation=_ES_CITATION,
        source_ref="BOE-A-2014-12328-Art36.2",
        graduated_brackets=((1_140_523.96, 0.30),),
        provenance=SourceProvenance(
            issuing_authority="Agencia Estatal Boletin Oficial del Estado "
                               "(Spanish State) — Impuesto sobre Sociedades, "
                               "producer registration via ICAA",
            source_url="https://www.boe.es",
            citation_detail="Ley 27/2014, de 27 de noviembre, Articulo 36.2 "
                             "(BOE-A-2014-12328) — verbatim statute text",
            interpretation_note="Direct verbatim statute quote — the "
                                 "strongest provenance tier this registry "
                                 "recognizes. The graduated bracket (30% "
                                 "first EUR 1M / 25% excess) is modeled as "
                                 "a real blended effective rate via "
                                 "resolve_program_rate(), not a flat rate.",
        ),
    ),
)

ES_UNVERIFIED_CLAIMS: tuple[UnverifiedRateClaim, ...] = (
    UnverifiedRateClaim(
        program_slug="es_tax_credit_foreign",
        claim="Canary Islands enhanced rate of 50% (mainland 30%) / 45% "
              "(mainland 25% excess) applies to productions filming in "
              "the Canary Islands.",
        claimed_by="Secondary trade/production-services sources and this "
                   "project's own prior DISCOVERY-tier jurisdiction_"
                   "comparison.py notes; not found anywhere in Article 36 "
                   "(all subsections 36.1-36.3 requested and reviewed)",
        verification_status="NOT FOUND in Ley 27/2014 Article 36. Almost "
                            "certainly derives from the separate Canary "
                            "Islands Régimen Económico y Fiscal (REF) "
                            "special tax regime, which has not been "
                            "located or read. Requires that regime's "
                            "primary text before it can be treated as a "
                            "rule either way.",
    ),
)


## ── France: CNC TRIP (Tax Rebate for International Productions) ────────────
#
# Source: CNC (Centre national du cinéma et de l'image animée) official TRIP
# page, cnc.fr — fetched directly and quoted verbatim below. Per the
# reconciliation discipline in docs/architecture/CAPABILITY_LEDGER.md: the
# Alembic migration (0008_seed_marine_jurisdictions.py, later bulk-promoted
# to VERIFIED by 0038 on a weak "source URL confirmed" basis, per that
# migration's own docstring) was checked FIRST as a candidate lead — it had
# the base rate (30%) and min spend (EUR 250,000) right, but MISSED the real
# VFX-uplift band (40% when French VFX spend > EUR 2M) and the real EUR 30M
# cap entirely. This is the same lesson as Spain: a migration's own
# confidence-tier label is not a substitute for reading the actual source.
#
# Quoted from cnc.fr: "The TRIP amounts up to 30% (or 40%, if the French VFX
# expenses are more than EUR 2M) ... can total a maximum of EUR 30 million
# per project." Minimum spend: "EUR 250,000 or 50% of their world budgets in
# French expenditures" (the 50%-of-world-budget alternative threshold is not
# representable in this engine's single min_qpe_usd field — disclosed, not
# computed). Live action also requires "at least 5 days of shooting in
# France" (not modeled — no shooting-days fact exists in this engine).
# Cultural test: "must include elements related to the French culture,
# heritage, and territory" — the migration's claimed "2 of 6 French
# elements" points breakdown was NOT found in the fetched cnc.fr text and is
# NOT carried into this rule (unconfirmed, not asserted). Refundable:
# confirmed ("if the amount of the tax rebate exceeds the corporate income
# tax due for this year, the difference will be paid by the French State").

_FR_CITATION = (
    "CNC (Centre national du cinéma et de l'image animée), official TRIP "
    "page (cnc.fr), fetched directly. 'The TRIP amounts up to 30% (or 40%, "
    "if the French VFX expenses are more than EUR 2M) ... can total a "
    "maximum of EUR 30 million per project.' Min spend: 'EUR 250,000 or "
    "50% of their world budgets in French expenditures' (50%-of-budget "
    "alternative not modeled). Live action also requires >=5 shooting days "
    "in France (not modeled — no shooting-days fact exists in this "
    "engine). Refundable: 'the difference will be paid by the French "
    "State' if the rebate exceeds corporate income tax due."
)
_FR_PROVENANCE = SourceProvenance(
    issuing_authority="Centre national du cinema et de l'image animee (CNC)",
    source_url="https://www.cnc.fr",
    citation_detail="TRIP page — up to 30% (40% if French VFX expenses > "
                     "EUR 2M); cap EUR 30,000,000 per project",
    interpretation_note="50%-of-world-budget alternative minimum-spend "
                         "threshold not modeled (engine only supports an "
                         "absolute min_qpe_usd). The 40% VFX tier is "
                         "modeled as a ceiling since this engine has no "
                         "VFX-specific spend fact to evaluate eligibility "
                         "against total QPE.",
)
FR_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="fr_trip", tier_id="fr-base-30",
        rate=0.30, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=285_130.99,
        conditions=(
            RateCondition(
                condition_id="fr-min-spend",
                description="Minimum qualifying French expenditure (or 50% "
                            "of world budget, whichever the production "
                            "meets — the 50%-of-budget alternative is not "
                            "computed by this engine)",
                quote="EUR 250,000 or 50% of their world budgets in French "
                      "expenditures (cnc.fr, TRIP page)",
                kind="min_qpe_usd", threshold_usd=285_130.99,
            ),
            RateCondition(
                condition_id="fr-cultural-test",
                description="Cultural test required (French/European "
                            "culture, heritage, territory elements) — "
                            "exact points-based criteria not confirmed "
                            "from the primary source fetched; a migration "
                            "claim of '2 of 6 elements' was NOT found in "
                            "the cnc.fr text and is not asserted here",
                quote="must include elements related to the French "
                      "culture, heritage, and territory (cnc.fr, TRIP page)",
                kind="cultural_test_required",
            ),
        ),
        # Global Economic Data + Base Pricing, batch 3: promoted PARSED ->
        # VERIFIED. Citation is CNC's own official TRIP page, fetched
        # directly, with the rate quoted verbatim.
        confidence_tier="VERIFIED",
        citation=_FR_CITATION,
        source_ref="cnc.fr-TRIP-page",
        provenance=_FR_PROVENANCE,
    ),
    RateRule(
        program_slug="fr_trip", tier_id="fr-vfx-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("feature_film",), min_qpe_usd=285_130.99,
        conditions=(
            RateCondition(
                condition_id="fr-min-spend",
                description="Minimum qualifying French expenditure",
                quote="EUR 250,000 or 50% of their world budgets in French "
                      "expenditures (cnc.fr, TRIP page)",
                kind="min_qpe_usd", threshold_usd=285_130.99,
            ),
            RateCondition(
                # Codex bounded remediation, B3 formulaic spec (UPDATE_
                # CONDITION): "Replace discretionary band with objective
                # component-spend condition." The 40% VFX tier is a real,
                # statute-confirmed OBJECTIVE spend threshold (EUR 2,000,000
                # of French VFX expenditure) -- never a discretionary
                # approval call like Mauritius's "up to 40%".
                #
                # Codex final runtime remediation (fr_trip, P0): "EUR2m
                # threshold remains a USD fact/proxy" -- the prior pass
                # made the gate genuinely executable but still compared a
                # caller-supplied fact against a hard-coded, permanently-
                # fixed USD conversion (2,281,047.91) baked into this
                # RateCondition at authoring time. Fixed per the accepted
                # remediation's own alternative ("replace with native EUR
                # component-spend fact"): the fact and the threshold are
                # BOTH now native EUR -- "fr_trip_vfx_spend_eur" compared
                # directly against EUR 2,000,000, with NO conversion in
                # either direction, ever. A production that never
                # evidences this fact stays on the 30% floor; one that
                # does, at or above EUR 2,000,000, resolves the 40%
                # ceiling deterministically.
                condition_id="fr-vfx-threshold",
                description="40% rate requires French VFX expenditure "
                            "exceeding EUR 2,000,000 — a real, objective, "
                            "statute-confirmed spend threshold (not a "
                            "discretionary approval band like MU's 'up to "
                            "40%'), evaluated NATIVELY in EUR against the "
                            "REAL, traced French-jurisdiction VFX-component "
                            "spend, distinct from total French QPE — never "
                            "the whole segment.",
                quote="40%, if the French VFX expenses are more than EUR "
                      "2M (cnc.fr, TRIP page)",
                kind="project_fact_dependent_uplift",
                amount_fact_key="fr_trip_vfx_spend_eur",
                amount_fact_min=2_000_000.0,
                # CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE
                # (Codex P0-CALC-001): this condition previously had NO
                # component-basis dimension, so the generic amount-fact
                # derivation (added in CLAUDE_GENERIC_AMOUNT_GATED_
                # DISCOVERY_REPAIR) incorrectly treated it as a
                # WHOLE_SEGMENT_QPE fact and filled it from the entire
                # French QPE -- which is virtually always well above
                # EUR 2,000,000, so 40% was selected for every French
                # full relocation regardless of real VFX spend. Setting
                # component_basis_line_components here makes this a
                # TRACEABLE_COMPONENT_QPE fact instead: price_segment
                # derives it ONLY from this segment's real allocations
                # whose .component == "vfx" (production_allocation.py's
                # own MOVABLE_COMPONENTS identity), then converts that
                # EUR-denominated subtotal via the canonical FX path --
                # never the whole segment, and never guessed.
                component_basis_line_components=("vfx",),
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_FR_CITATION + " The 40% tier is a real, statute-confirmed "
                 "threshold (VFX spend > EUR 2M), not discretionary "
                 "approval — modeled as a band ceiling because the "
                 "engine's floor/guarantee is the base 30% tier absent an "
                 "evidenced VFX-spend fact; genuinely resolves 40% once "
                 "'fr_trip_vfx_spend_eur' is evidenced at or above the "
                 "native EUR 2,000,000 threshold.",
        source_ref="cnc.fr-TRIP-page",
        provenance=_FR_PROVENANCE,
    ),
)


_RULES_BY_PROGRAM: dict[str, tuple[RateRule, ...]] = {}
for _r in MU_RATE_RULES + MT_RATE_RULES + IE_RATE_RULES + GR_RATE_RULES + ES_RATE_RULES + FR_RATE_RULES:
    _RULES_BY_PROGRAM.setdefault(_r.program_slug, ())
    _RULES_BY_PROGRAM[_r.program_slug] = _RULES_BY_PROGRAM[_r.program_slug] + (_r,)

_UNVERIFIED_BY_PROGRAM: dict[str, tuple[UnverifiedRateClaim, ...]] = {
    "mu_edb_incentive": MU_UNVERIFIED_CLAIMS,
    "es_tax_credit_foreign": ES_UNVERIFIED_CLAIMS,
}
_BUDGET_RATES_BY_PROGRAM: dict[str, tuple[BudgetEvidencedRate, ...]] = {
    "mu_edb_incentive": MU_BUDGET_EVIDENCED_RATES,
}


def get_rate_rules(program_slug: str) -> tuple[RateRule, ...]:
    rules = _RULES_BY_PROGRAM.get(program_slug)
    if rules is None:
        rules = _RULES_BY_PROGRAM.get(_canonical_program_slug(program_slug))
    if rules is None and program_slug:
        # ALIAS SPELLING MUST NOT CHANGE ECONOMIC TREATMENT: the B4 gate already resolves a spelling through BOTH alias graphs
        # (PROGRAM_SLUG_ALIASES and CANONICAL_RUNTIME_SLUG_BINDINGS); the rate lookup must too, otherwise a runtime-bound
        # spelling (e.g. sa_sfc_rebate -> sa_film_commission_rebate) reads "no statutory rate rules" and its verified economics vanish.
        from app.data.authority_coverage_registry import _b4_spellings

        for spelling in sorted(_b4_spellings(program_slug)):
            if spelling != program_slug and spelling in _RULES_BY_PROGRAM:
                rules = _RULES_BY_PROGRAM[spelling]
                break
    return rules or ()


# ── QPE eligible-spend caps (Incentive/Optimizer Core Closeout) ─────────────
#
# A cap on ELIGIBLE SPEND (the QPE base itself), distinct from a rate cap
# or an annual program cap. Applied to a segment's own qpe_usd BEFORE rate
# resolution, so a capped QPE also correctly affects which rate tier's
# min_qpe_usd threshold is met. cap_base:
#   "segment_allocated"      — cap is a % of THIS segment's own allocated
#                               total (a proxy for "total core expenditure"
#                               on a full-relocation structure, where the
#                               segment IS effectively the whole production).
#   "total_worldwide_budget" — cap is a % of the STRUCTURE's entire gross
#                               budget, regardless of how much of it is
#                               allocated to this segment.
@dataclass(frozen=True)
class QpeCapRule:
    program_slug: str
    cap_pct: float
    cap_base: str  # "segment_allocated" | "total_worldwide_budget"
    description: str
    quote: str
    source_ref: str


_GB_CAP_QUOTE = (
    "'AVEC is available on qualifying UK production expenditure, which is "
    "the lower of either 80% of total core expenditure or the actual UK "
    "core expenditure incurred' (bfi.org.uk, corroborated by HMRC "
    "CREC061300/CREC060100: 'the lesser of UK relevant global expenditure "
    "and 80% of total relevant global expenditure/core expenditure')."
)
_GR_CAP_QUOTE = (
    "'implemented within the Greek territory and not exceeding eighty "
    "percent (80%) of the total production cost for the entirety of the "
    "audiovisual production work' — the cap base is the production's total "
    "worldwide cost, not Greek spend alone (JMD 607434, Gazette B' 87/"
    "14.01.2026, arts. 4-5, as amended by JMD 140524)."
)

_CA_CPTC_CAP_QUOTE = (
    "'25 per cent of the qualified labour expenditure' ... qualified labour "
    "expenditure 'must not exceed 60% of the cost of production net of "
    "assistance' (canada.ca / CAVCO official program guidance)."
)

QPE_CAP_RULES: dict[str, QpeCapRule] = {
    "uk_avec": QpeCapRule(
        program_slug="uk_avec", cap_pct=0.80, cap_base="segment_allocated",
        description="Ordinary AVEC qualifying expenditure is capped at the "
                     "lower of actual UK core expenditure or 80% of total "
                     "core expenditure.",
        quote=_GB_CAP_QUOTE, source_ref="HMRC-CREC061300-CREC060100",
    ),
    "gr_cash_rebate": QpeCapRule(
        program_slug="gr_cash_rebate", cap_pct=0.80, cap_base="total_worldwide_budget",
        description="Eligible Greek production expenditure is capped at 80% "
                     "of the production's total (worldwide) production cost. "
                     "Denominator: the text says only 'total production cost' "
                     "(Law 4487/2017 Art. 26(1); KYA 607434 Art. 5(1) and the "
                     "GBER Art. 54 definition at p.101 -- 'the total cost of "
                     "production of the audiovisual works'); the exclusions of "
                     "lending cost, bank expenses, taxes, duties and promotion "
                     "(Art. 26(2)(c)-(d); Annex B.3(iii)-(iv)) are scoped to the "
                     "ELIGIBLE total, not to the denominator. The canonical base "
                     "is therefore the full budget total incl. financing; the "
                     "narrower readings (gross less financing, or the Annex II "
                     "category total) are disclosed sensitivities, not adopted.",
        quote=_GR_CAP_QUOTE, source_ref="JMD-607434-arts-4-5",
    ),
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, CBA-002 -- reuses this EXISTING, already-
    # tested QPE-cap mechanism (no new rate-base-transform engine) for
    # CPTC's own real, cited 60%-of-production-cost cap. This is a
    # deliberate, disclosed APPROXIMATION of the statute's real base
    # (qualified CANADIAN LABOUR expenditure specifically, capped at 60%
    # of net production cost) -- this engine has no labour/non-labour QPE
    # split (a genuine, separately-scoped gap; see ca-cptc-labour-only-
    # base's own RateCondition), so the achievable, real, statutorily-
    # grounded correction is to cap TOTAL QPE at 60% of the production's
    # total budget rather than apply the 25% rate to unbounded QPE. This
    # can only ever REDUCE the credit relative to the prior unbounded
    # calculation -- never invents additional eligible spend.
    "ca_federal_cptc": QpeCapRule(
        program_slug="ca_federal_cptc", cap_pct=0.60, cap_base="total_worldwide_budget",
        description="Qualified Canadian labour expenditure (the CPTC rate "
                     "base) is capped at 60% of the production's cost net of "
                     "assistance. This engine applies the 60% cap to total "
                     "QPE as a real, cited, conservative approximation of "
                     "the labour-only base (no labour/non-labour QPE split "
                     "modeled).",
        quote=_CA_CPTC_CAP_QUOTE, source_ref="canada.ca-cavco-official-final19-committee-agreed",
    ),
    # Codex bounded remediation, B3 formulaic spec (UPDATE_AND_EXTEND,
    # GLOBAL_PROGRAM_FORMULAIC_RATE_RULE_SPEC_CODEX.csv): "eligible basis no
    # more than 80% of budget" for the Czech Film Incentive -- reuses this
    # SAME existing, already-tested QPE-cap mechanism (no new engine) for
    # both the live-action and animation/digital records, since the 80%
    # eligible-base cap is a program-level rule that applies regardless of
    # which production-type tier resolves. The CZK 450,000,000 project
    # incentive cap itself is NOT modeled here (no sourced CZK/USD FX rate
    # in production_normalization.FX_RATE_SNAPSHOTS — left undisclosed
    # rather than fabricated, same discipline as au_location_offset's AUD
    # minimum spend).
    "ca_bc_film_tv_tax_credit": QpeCapRule(
        program_slug="ca_bc_film_tv_tax_credit", cap_pct=0.60, cap_base="total_worldwide_budget",
        description="Qualified BC labour expenditure is the lesser of BC labour and 60% x (total production cost - assistance) - LC (Income Tax Act (BC) s.79(1)). As for the CPTC, the "
                     "60% cap is applied to the total worldwide budget (net-of-assistance is an approximation that can only reduce the credit).",
        quote="PCT x (TPC - TA) - LC where PCT means ... 60% (Income Tax Act (BC) s.79(1), 'qualified BC labour expenditure')",
        source_ref="bc-ita-part-5-s79",
    ),
    "cz_film_incentive": QpeCapRule(
        program_slug="cz_film_incentive", cap_pct=0.80, cap_base="total_worldwide_budget",
        description="Eligible Czech spend is capped at 80% of the production's "
                     "total (worldwide) production budget.",
        quote="eligible basis no more than 80% of budget (Codex bounded "
              "remediation, accepted formulaic correction)",
        source_ref="codex-bounded-remediation-cz-film-incentive-formulaic-spec",
    ),
    "cz_film_incentive_animation": QpeCapRule(
        program_slug="cz_film_incentive_animation", cap_pct=0.80, cap_base="total_worldwide_budget",
        description="Eligible Czech spend is capped at 80% of the production's "
                     "total (worldwide) production budget (same program-level "
                     "cap as the live-action record).",
        quote="eligible basis no more than 80% of budget (Codex bounded "
              "remediation, accepted formulaic correction)",
        source_ref="codex-bounded-remediation-cz-film-incentive-formulaic-spec",
    ),
}


@dataclass(frozen=True)
class QpeShareCapRule:
    """A group of spend categories that may count only up to ``cap_pct`` of the program's TOTAL eligible cost.

    The total is the capped total itself (the statutes cap a group at a share of the total eligible production cost, which
    includes that group), so the cap is resolved as a greatest fixed point together with any percentage QpeCapRule limit.
    The part above the cap is not excluded: which individual payees fall inside the capped group is a production fact the
    topsheet does not carry, so the excess is reported as conditional (unresolved), never as lost or as confirmed."""
    program_slug: str
    group_id: str
    categories: frozenset[str]
    cap_pct: float
    description: str
    quote: str
    source_ref: str
    # Membership the budget cannot settle. ``proxy_categories`` are placed INSIDE the group as a whole-account proxy (the
    # lower QPE envelope); ``outside_unresolved_categories`` stay outside it as a planning value (the upper envelope for
    # that account). Neither is an exact member count: both are disclosed as unresolved, with the fact that would settle them.
    proxy_categories: frozenset[str] = frozenset()
    outside_unresolved_categories: frozenset[str] = frozenset()
    unresolved_fact_id: str | None = None
    unresolved_note: str = ""


QPE_SHARE_CAP_RULES: dict[str, tuple[QpeShareCapRule, ...]] = {
    "gr_cash_rebate": (
        QpeShareCapRule(
            program_slug="gr_cash_rebate", group_id="insurance_and_guarantees",
            categories=frozenset({"insurance", "completion_bond"}), cap_pct=0.05,
            description="Insurance premiums and guarantee costs count in full up to 5% of the total eligible production cost.",
            quote="Annex B.3(i): premiums and guarantee costs are counted in their entirety, with maximum eligible expense the "
                  "corresponding 5% of the total eligible production cost (KYA 607434, Gazette B' 87/14.01.2026); the same 5% "
                  "appears in Law 4487/2017 Art. 26(2)(a).",
            source_ref="KYA-607434-2026-01-14-Annex-B3-i",
        ),
        QpeShareCapRule(
            program_slug="gr_cash_rebate", group_id="principal_fees",
            categories=frozenset({"atl_writer", "atl_director"}), cap_pct=0.30,
            proxy_categories=frozenset({"atl_cast"}), outside_unresolved_categories=frozenset({"music"}),
            unresolved_fact_id="gr-principal-fee-membership",
            unresolved_note=(
                "Annex II 1.1 (screenwriter) and 1.2 (director) are known members by category. Annex II 1.4 counts only lead roles "
                "A' and B': the cast account also holds supporting cast (2.2) and extras (2.3), which are outside the group, so "
                "the whole cast account is placed inside the group as a proxy (lower QPE envelope) until the lead-role split is "
                "evidenced. Annex II 1.5 is the composer's fee for ORIGINAL composition (a member), 6.8 is production services for "
                "original music and songs (ordinary cost), and B.2(vii) makes copyright and licences on pre-existing music "
                "ineligible; the budget's music account does not separate them, so it stays outside the group as a planning "
                "value (upper envelope for that account) and its dollars are reported as unresolved membership, not as exact."),
            description="Music rights (the composer's fee for original composition, Annex II 1.5), the fee of the director and the "
                        "screenwriter, and the fees of the two leading actors count up to 30% of the total eligible production "
                        "cost. Current text only: the producer (1.3) is not in the group and the historical 35% group of Law "
                        "4487/2017 Art. 26(2)(b) (which also contains the producer and music) applies to plans governed by "
                        "that text.",
            quote="Annex B.3(ii): music rights and the fee of the director, the screenwriter and the two leading actors are "
                  "counted up to thirty percent (30%) of the total eligible cost and may not exceed that percentage (KYA 607434, "
                  "Gazette B' 87/14.01.2026).",
            source_ref="KYA-607434-2026-01-14-Annex-B3-ii",
        ),
    ),
    "us_mo_motion_media_production_tax_credit": (
        QpeShareCapRule(
            program_slug="us_mo_motion_media_production_tax_credit", group_id="above_the_line_individuals",
            categories=frozenset({"atl_writer", "atl_director", "atl_producer"}), cap_pct=0.25,
            proxy_categories=frozenset({"atl_cast"}), unresolved_fact_id="mo-principal-cast-membership",
            unresolved_note=("RSMo 135.750 subsection 2(1) names as above-the-line individuals any producer, the screenwriter, the director and principal cast 'at a Screen Actors Guild Schedule F and above payment rate'. "
                             "The cast account also holds cast below Schedule F, which are ordinary qualifying wages, and the topsheet does not split them, so the whole cast account is placed inside the group as a "
                             "proxy (lower QPE envelope) until the Schedule F split is evidenced."),
            description="Compensation and wages paid to above-the-line individuals count toward Missouri qualifying expenses only up to 25% of the overall qualifying expenses.",
            quote="compensation and wages paid to all above-the-line individuals shall be limited to twenty-five percent of the overall qualifying expenses (RSMo 135.750 subsection 2(3)(b))",
            source_ref="rsmo-135.750-subsection-2-3-b",
        ),
    ),
}


def get_qpe_share_caps(program_slug: str) -> tuple[QpeShareCapRule, ...]:
    return QPE_SHARE_CAP_RULES.get(program_slug, ())


def get_qpe_cap(program_slug: str) -> QpeCapRule | None:
    return QPE_CAP_RULES.get(program_slug)


# ── Dollar limit on the QUALIFIED-EXPENDITURE BASE (not on the incentive, not the annual fund) ───────────────────
# A programme can cap how much qualified expenditure the rate applies to (California: "The 35% tax credit applies up to a
# maximum of $120 million of qualified expenditures"; independent film "35% of qualified expenditures, applied to a maximum
# of $20 million"). That is an eligible-base limit: distinct from the annual fund, from a limit on the credit itself, and
# from a percentage-of-budget cap. The independent limit applies only when the independent-film category is evidenced for the
# production (an independent producer may also elect the non-independent category, so it is never inferred); absent that
# fact, the non-independent limit is the applicable one.
@dataclass(frozen=True)
class QpeDollarCapRule:
    program_slug: str
    default_limit_usd: float
    independent_limit_usd: float | None
    independent_fact: str | None
    description: str
    quote: str
    source_ref: str


QPE_DOLLAR_CAP_RULES: dict[str, QpeDollarCapRule] = {
    "ca_film_30": QpeDollarCapRule(
        program_slug="ca_film_30", default_limit_usd=120_000_000.0, independent_limit_usd=20_000_000.0,
        independent_fact="ca_film_independent_category",
        description="California Program 4.0 qualified-expenditure limit: $120M non-independent, $20M independent film.",
        quote="'The 35% tax credit applies up to a maximum of $120 million of qualified expenditures' (non-independent); "
              "'Independent Film applicants are eligible to receive 35% of qualified expenditures, applied to a maximum of $20 "
              "million of the qualified expenditure budget' (CA Film Commission, Program 4.0 Program Guidelines, Jan 1, 2026).",
        source_ref="CFC-Program-4.0-Guidelines-2026-01",
    ),
}


def get_qpe_dollar_cap(program_slug: str) -> QpeDollarCapRule | None:
    return QPE_DOLLAR_CAP_RULES.get(program_slug)


# ── Native-currency INCENTIVE-VALUE cap (Codex final-nine remediation) ──────
#
# Distinct from QpeCapRule above: QpeCapRule caps the ELIGIBLE SPEND BASE
# before the rate is applied; IncentiveValueCapRule caps the CALCULATED
# INCENTIVE DOLLAR VALUE itself (e.g. cz_film_incentive's CZK450m project
# cap, za_nfvf_rebate's ZAR25m project cap) — a hard ceiling on what the
# program can pay out, stated in the program's own native currency.
#
# The prior implementation asked the CALLER to supply the already-computed
# incentive value as a fact and rejected the candidate when it exceeded the
# cap ("a cap must be applied to the engine-calculated incentive, not a
# caller-attested result" — Codex's exact finding). This registry instead
# lets allocation_pricing.price_segment() apply the cap itself, AFTER it
# has already computed the real floor/ceiling incentive in USD, by
# converting the native cap amount to USD via the SAME real, dated, sourced
# FX snapshot every other currency conversion in this codebase uses
# (production_normalization.FX_RATE_SNAPSHOTS via apply_fx_rates.
# convert_to_usd) — never a caller-supplied or guessed conversion. The
# candidate is never rejected for exceeding the cap; the incentive is
# reduced to the cap, exactly like a real statutory ceiling.
@dataclass(frozen=True)
class IncentiveValueCapRule:
    program_slug: str
    cap_currency: str        # ISO 4217 code, e.g. "CZK", "ZAR"
    cap_native_amount: float
    description: str
    quote: str
    source_ref: str

    # Codex final P0 (nl_film_production_incentive): "EUR3m company-year
    # cap ... does not consume prior company-period awards." Set ONLY on
    # a cap that is denominated PER COMPANY PER PERIOD (e.g. NL's "up to
    # EUR 3 million per year per production company" — several
    # productions from the SAME company share ONE annual ceiling, unlike
    # cz_film_incentive's/za_nfvf_rebate's genuinely PER-PROJECT caps).
    # Names the caller-supplied amount_fact_key carrying this company's
    # own prior awards already granted THIS period from its OTHER
    # productions (native currency, same as cap_currency) — reduces the
    # effective remaining cap by that amount before conversion, so two
    # projects for the same company cannot jointly exceed the shared
    # ceiling. None (the default, every other program) means the cap is
    # purely per-project — unaffected by this mechanism.
    company_period_prior_award_fact_key: str | None = None

    # Codex final wiring remediation (P0-NL-001, third pass): "The cap
    # calculation must consume explicit canonical: production-company
    # identity; award period/year; evidence/provenance state for the
    # aggregate; prior awards for that exact program + company + period."
    # The second pass's two caller-supplied booleans described identity
    # binding only in comments -- ProjectEconomicInputs carried neither a
    # company identity nor an award period, so two independent calls
    # using the same scalar both priced identically. Replaced with a
    # THREE-part, engine-computed contract (never a caller-supplied
    # scalar):
    #
    #   company_period_identity_known_fact_key -- evidenced ONLY by
    #   canonical_evaluation.evaluate_project(), generically, from the
    #   real Project.production_company_identifier and
    #   Project.target_shoot_year columns both being non-None. Missing
    #   EITHER means unknown company or period -- this cap stays
    #   conditional/non-priceable, never an affirmative zero. No caller
    #   can set this fact directly; it is derived from canonical project
    #   state, never asserted.
    #
    #   company_period_has_other_productions_fact_key -- evidenced ONLY
    #   by evaluate_project()'s own real cross-project database query
    #   (_company_period_prior_award_facts): every OTHER real, persisted
    #   project sharing the EXACT SAME production_company_identifier and
    #   award_period_year is queried, excluding this project, and its own
    #   priced incentive (if any) for this SAME program is summed. Found
    #   siblings -> evidenced True, with the real aggregate amount in
    #   amount_facts[company_period_prior_award_fact_key]. No siblings
    #   found (identity known, genuinely alone) -> a real, evidenced
    #   zero -- the full native cap applies. Absent identity -> this key
    #   is never set at all, distinct from "evidenced False".
    #
    # The amount itself is therefore ALWAYS engine-derived from real
    # persisted sibling data whenever has_other_productions is
    # engine-evidenced -- never a free caller-supplied scalar, so no
    # separate "aggregate evidenced" flag is needed on top of these two.
    company_period_identity_known_fact_key: str | None = None
    company_period_has_other_productions_fact_key: str | None = None

    # Codex final four-row remediation (P0-NL-001, fourth pass): "Sibling
    # existence with unknown award evidence remains unresolved and no
    # full cap is asserted." Evidenced ONLY by canonical_evaluation.
    # _company_period_prior_award_facts when at least one real
    # IncentiveAwardLedgerEntry row exists for the exact (company,
    # period, program) triple -- i.e. the ledger has genuinely been
    # checked/recorded for every sibling production this cap could be
    # shared with. A sibling Project existing is NOT itself proof of an
    # award (it could be unevaluated, still in progress, or simply never
    # recorded) -- so when siblings exist but this fact is unset, the
    # resolver (allocation_pricing._resolve_incentive_dollar_cap) must
    # fail this segment closed as unresolved, never assert a full/
    # remaining cap from silence. When no siblings exist at all, this key
    # is legitimately never set either -- there being nothing to resolve
    # is a real "alone" state, distinct from "unresolved", and the
    # resolver's existing has_other_productions-unset path already
    # applies the full cap correctly in that case.
    company_period_sibling_coverage_complete_fact_key: str | None = None

    # Codex final wiring remediation (P0-OR-001): "Keep the fund amount/
    # date explicit and fail conditional if missing/stale; never treat
    # missing cap as unlimited." When set, this cap applies ONLY once the
    # named evidenced fact confirms the dated cap_native_amount figure is
    # current (never stale/guessed) -- absent, the WHOLE segment fails
    # closed via the SAME unresolved-detail path company_period_prior_
    # award_fact_key already uses, exactly so a missing/unconfirmed cap
    # can never be silently treated as "no cap" (unlimited). None (the
    # default, every cap without a dated/discretionary fund figure) means
    # the cap always applies unconditionally, unchanged.
    cap_requires_evidence_fact_key: str | None = None

    # A higher statutory ceiling requires an evidenced approval, not an application.
    exception_approval_fact_key: str | None = None
    exception_cap_native_amount: float | None = None


INCENTIVE_VALUE_CAP_RULES: dict[str, IncentiveValueCapRule] = {
    "ca_nl_all_spend_credit": IncentiveValueCapRule(
        program_slug="ca_nl_all_spend_credit", cap_currency="CAD", cap_native_amount=20_000_000.0,
        description="Maximum credit per eligible production per taxation year: CAD 20,000,000 (Regulation 31/23 s.2(c)(ii)), applied to the calculated credit at the dated CAD snapshot.",
        quote="the all-spend film and video production tax credit means the amount that is the lesser of (i) the amount determined by the formula A x (B - C) ... and (ii) $20 million "
              "(Newfoundland and Labrador Regulation 31/23 s.2(c), in force April 7, 2022; Department of Finance: 'to a maximum tax credit of $20 million annually per project')",
        source_ref="assembly.nl.ca-rc230031-s2c",
    ),
    "gr_cash_rebate": IncentiveValueCapRule(
        program_slug="gr_cash_rebate", cap_currency="EUR", cap_native_amount=8_000_000.0,
        description="Ordinary per-work grant cap EUR 8m; EUR 10m only on evidenced strategic-project ministerial approval.",
        quote="Article 4(2): grant shall not exceed EUR 8,000,000 per audiovisual work. Article 23(1): excess up to EUR 10,000,000 may be approved for strategic investment plans by joint ministerial decision.",
        source_ref="EKKOMED-KYA-607434-2026-Articles4-23",
        exception_approval_fact_key="gr_strategic_project_joint_ministerial_approval",
        exception_cap_native_amount=10_000_000.0,
    ),
    "cz_film_incentive": IncentiveValueCapRule(
        program_slug="cz_film_incentive", cap_currency="CZK", cap_native_amount=450_000_000.0,
        description="Maximum incentive per project: CZK 450,000,000, applied to the "
                     "calculated incentive (not a rejection predicate on a caller-"
                     "supplied value).",
        quote="the maximum support per project is CZK 450 million (sfa.gov.cz "
              "production-incentives page)",
        source_ref="rodriqueslaw.com-czech-republic+sfa.gov.cz-official",
    ),
    "cz_film_incentive_animation": IncentiveValueCapRule(
        program_slug="cz_film_incentive_animation", cap_currency="CZK", cap_native_amount=450_000_000.0,
        description="Same CZK 450,000,000 per-project cap as the live-action record.",
        quote="the maximum support per project is CZK 450 million (sfa.gov.cz "
              "production-incentives page)",
        source_ref="rodriqueslaw.com-czech-republic-animation",
    ),
    "za_nfvf_rebate": IncentiveValueCapRule(
        program_slug="za_nfvf_rebate", cap_currency="ZAR", cap_native_amount=25_000_000.0,
        description="Maximum incentive per project: ZAR 25,000,000, applied to the "
                     "calculated incentive (not a rejection predicate on a caller-"
                     "supplied value).",
        quote="production cap R25m (Codex bounded remediation, accepted formulaic correction)",
        source_ref="codex-bounded-remediation-za-nfvf-rebate-formulaic-spec",
    ),
    # Codex final-nine remediation (nl_nfpi, P0): "Program caps absent."
    # This EUR 3,000,000 company cap was ALREADY an accepted, sourced,
    # PRIMARY/CURRENT research fact (program_requirements.py's
    # nl_film_production_incentive ProgramRequirementsProfile,
    # additional_facts["company_cap_eur"], Netherlands Film Fund's own
    # 2026 programme page) -- it was simply never wired into an
    # executable cap. No new research; reconciling already-accepted data.
    # The EUR 20,000,000 annual budget / EUR 5,000,000-per-round figures
    # from the same source are PROGRAM-WIDE (across all applicants that
    # round), not a per-production entitlement, so they are not modeled
    # as this program's per-project cap -- the EUR 3,000,000 company cap
    # is the real, binding per-production ceiling.
    "nl_film_production_incentive": IncentiveValueCapRule(
        program_slug="nl_film_production_incentive", cap_currency="EUR", cap_native_amount=3_000_000.0,
        description="Maximum incentive per year per production company: EUR 3,000,000, "
                     "applied to the calculated incentive.",
        quote="COMPANY CAP: up to EUR 3 million per year per production company — a "
              "real, published company-level cap. (Netherlands Film Fund, 2026 programme)",
        source_ref="filmfonds.nl-netherlands-film-production-incentive-2026",
        # Codex final P0: "does not consume prior company-period awards."
        # This is a PER-COMPANY PER-YEAR cap (several productions from
        # the same company share it), not a per-project cap -- the
        # caller-supplied nl_nfpi_company_period_prior_awards_eur fact
        # (native EUR, the SAME company's other productions' already-
        # granted awards this year) reduces the effective remaining cap
        # for THIS project, so two projects for one company cannot
        # jointly exceed the shared EUR 3,000,000 ceiling.
        company_period_prior_award_fact_key="nl_nfpi_company_period_prior_awards_eur",
        company_period_identity_known_fact_key="nl_nfpi_company_period_identity_known",
        company_period_has_other_productions_fact_key="nl_nfpi_company_period_has_other_productions",
        company_period_sibling_coverage_complete_fact_key="nl_nfpi_company_period_sibling_coverage_complete",
    ),
    # Codex final wiring remediation (P0-OR-001): "Final project award <=
    # 50% of dated annual OPIF fund; current official page says
    # USD21.2m, so current nominal maximum is literal USD10.6m." Both
    # figures are independently verified official-source figures (Oregon
    # Film's own OPIF program page, corroborated by OAR 951-002-0010's
    # 50%-of-fund rule) -- USD, no FX conversion needed (Oregon is a US
    # jurisdiction). "Fail conditional if missing/stale; never treat
    # missing cap as unlimited" is satisfied by construction here: the
    # cap is ALWAYS an explicit, dated, sourced figure (never omitted,
    # never a guessed/unlimited default) -- see source_ref/quote. It
    # applies unconditionally, exactly like every other program's cap,
    # so a provisional (pre-award-confirmation) candidate still shows a
    # real, capped dollar figure -- "show provisional economics only"
    # (P0-OR-001's disposition B) requires a NUMBER, not a second
    # non-priceable gate on top of the qualification-state exclusion
    # already keeping this program out of verified-winner/rank-1 (see
    # program_rate_rules_worldwide.US_OR_DOCTRINE's us-or-award-
    # contract-fund-confirmed / us-or-fund-amount-current conditions,
    # which own the "conditional, never unconditional" requirement).
    "us_or_opif": IncentiveValueCapRule(
        program_slug="us_or_opif", cap_currency="USD", cap_native_amount=10_600_000.0,
        description="Maximum project award: 50% of the current USD21,200,000 annual "
                     "OPIF fund = USD10,600,000, applied to the calculated incentive "
                     "(payroll + other combined, after the regional uplift multiplier).",
        quote="No single qualifying film... can be awarded more than 50% of the "
              "entire OPIF fund... in any given single fiscal year (OAR "
              "951-002-0010(5)); current annual fund USD21.2m (Oregon Film OPIF "
              "program page, oregonfilm.org)",
        source_ref="oregonlegislature.gov-ors284.368+secure.sos.state.or.us-oar951-002-0010+oregonfilm.org-opif",
    ),
    # Codex canonical identity/authority cleanup (Phase 5, Nevada):
    # "Material accepted constraints are not executable" -- the real,
    # already-accepted USD6,000,000 per-project cap (film.nv.gov, the
    # SAME source this program's own doctrine record already cites) was
    # never applied to the calculated incentive at all, letting a large
    # enough qualifying spend price an unbounded credit. Applied here via
    # the SAME dollar-cap mechanism every other capped program in this
    # codebase already uses -- never a rejection predicate, the
    # calculated incentive is reduced to the cap.
    "us_nv_film_credit": IncentiveValueCapRule(
        program_slug="us_nv_film_credit", cap_currency="USD", cap_native_amount=6_000_000.0,
        description="Maximum project award: USD6,000,000 per production, applied to the "
                     "calculated incentive.",
        quote="$6M per-project / $10M program caps (film.nv.gov, official Nevada Film "
              "Office incentive page -- already cited in this program's own doctrine "
              "record's SourceProvenance.citation_detail)",
        source_ref="film.nv.gov-official",
    ),
    # PROJECT_OPEN_ITEM_RECOVERY F-04 (US/Canada/Mexico scope): Rhode Island's per-project cap was
    # recorded in the doctrine record as "not modeled by this schema" and the $40M ANNUAL program cap
    # was the only dollar bound applied, so a large qualifying spend priced past the per-project cap.
    # The cap mechanism exists now; apply the retained USD figure. The statutory waiver (a
    # qualifying production may be waived) has no retained dollar ceiling, so it is NOT modeled --
    # the cap stays conservative and the waiver stays a disclosed unmodeled condition.
    "us_ri_film_credit": IncentiveValueCapRule(
        program_slug="us_ri_film_credit", cap_currency="USD", cap_native_amount=7_000_000.0,
        description="Per-project cap: USD7,000,000 of credits per production (waivable for "
                     "qualifying productions; the waiver is not modeled).",
        quote="Per-project cap $7,000,000 (waivable for qualifying productions) (film.ri.gov, "
              "official Rhode Island Film & TV Office page -- already cited in this program's "
              "own doctrine record's SourceProvenance.citation_detail)",
        source_ref="film.ri.gov-official",
    ),
    # PROJECT_OPEN_ITEM_RECOVERY F-05: Mexico's per-project cap was retained (doctrine citation and
    # requirements profile: "MXN 40 million per beneficiary/production", "Cap per project") but never
    # applied, so a large Mexico candidate priced an uncapped credit. Native MXN, converted only
    # through the canonical FX context (MXN is now a tracked currency); an unavailable MXN rate fails
    # the segment closed, never uncapped. The figure is law-firm-summarized (Baker McKenzie, KPMG);
    # the Decreto defers per-project figures to a Lineamientos document not yet read, so the
    # authority tier is unchanged.
    "ca_nb_film_tax_credit": IncentiveValueCapRule(
        program_slug="ca_nb_film_tax_credit", cap_currency="CAD", cap_native_amount=2_000_000.0,
        description="LIFT Company Cap: no one production company (including sub-companies) may receive more than CAD 2,000,000 (28% of the CAD 7 million program budget). The Major Production stream "
                    "states no separate per-project maximum; the Micro stream's CAD 100,000 maximum is not modelled. The cap is per company, so prior awards to the same company are not netted here.",
        quote="Company Cap: ... no one production company (including their sub-companies incorporated for specific projects) may represent more than 28% of the total LIFT $7M program budget "
              "(Company Cap of $2M) (LIFT Film & TV Production Incentive 2026/2027 Guidelines)",
        source_ref="nb-thc-lift-production-guidelines-2026-27-primary",
    ),
    "ca_ns_production_incentive_fund": IncentiveValueCapRule(
        program_slug="ca_ns_production_incentive_fund", cap_currency="CAD", cap_native_amount=10_000_000.0,
        description="Maximum funding payable to any one project from the Fund: CAD 10 million (s.3.1(e)).",
        quote="The maximum funding from this Fund payable to any project is $10 million (CCTH Nova Scotia Film & Television Production Incentive Fund Guidelines, April 1, 2024, s.3.1(e))",
        source_ref="ccth-nsfpif-guidelines-2024-04-01-primary",
    ),
    "ca_sk_creative_saskatchewan_grant": IncentiveValueCapRule(
        program_slug="ca_sk_creative_saskatchewan_grant", cap_currency="CAD", cap_native_amount=5_000_000.0,
        description="Maximum of CAD 5,000,000 per production for both the Saskatchewan Stream (30%) and the Service Production Stream (25%); previously recorded as annual_cap_usd at CAD-USD par.",
        quote="equivalent to a maximum of 30% of all eligible Saskatchewan expenditures up to a maximum of $5,000,000 ... 25% ... up to a maximum of $5,000,000 (Creative Saskatchewan Feature Film "
              "and Television Production Grant guidelines, fiscal 2026/27)",
        source_ref="creativesask.ca-fy2026-27-guidelines-primary",
    ),
    "mx_federal_film_incentive_2026": IncentiveValueCapRule(
        program_slug="mx_federal_film_incentive_2026", cap_currency="MXN", cap_native_amount=40_000_000.0,
        description="Cap per project / beneficiary: MXN 40,000,000 of tax credit.",
        quote="Individual cap 'MXN 40 million per beneficiary/production' (bakermckenzie.com, "
              "corroborated by KPMG and FisherBroyles; DOF Decreto 2026-02-16 defers the per-project "
              "figures to the Lineamientos)",
        source_ref="bakermckenzie.com-mexico-2026-incentive+dof.gob.mx-decreto-2026-02-16-official",
    ),
}


def get_incentive_value_cap(program_slug: str) -> IncentiveValueCapRule | None:
    return INCENTIVE_VALUE_CAP_RULES.get(program_slug)


def convert_incentive_cap_to_usd(
    cap: IncentiveValueCapRule, fx_context: "CanonicalFXContext | None" = None,
) -> "tuple[FXConversionResult | None, FXRateResolution]":
    """The one place a native incentive-value cap is converted to USD.

    Codex final P0 (canonical_fx): previously read the mutable global
    FX_LIVE_SNAPSHOT_DATE/FX_RATE_SNAPSHOTS fresh on every call and
    called the raising convert_to_usd() — a missing rate raised
    ValueError, a zero rate raised ZeroDivisionError, and a corrupted
    negative rate silently produced a negative cap. Now accepts an
    explicit, immutable fx_context (built once per evaluation via
    production_normalization.build_fx_context() and threaded down from
    price_segment()); fx_context=None builds one fresh, single-call
    context (never a leak across calls). Returns (conversion_or_None,
    resolution) — the caller MUST check resolution.ok before trusting the
    conversion; a non-ok resolution means this cap cannot be safely
    evaluated and the candidate must be treated as non-priceable, never
    silently uncapped or crashed."""
    from app.calculators import apply_fx_rates
    from app.calculators.production_normalization import build_fx_context

    context = fx_context if fx_context is not None else build_fx_context()
    return apply_fx_rates.convert_to_usd_ctx(cap.cap_native_amount, cap.cap_currency, context)


def register_rate_rules(rules: tuple[RateRule, ...]) -> None:
    """Registration hook for executable_jurisdiction_registry.py-derived
    RateRule tuples (worldwide jurisdiction population phase) — lets a
    new jurisdiction's rules be built from ONE canonical DoctrineRecord
    (see executable_jurisdiction_registry.py) without a circular import:
    that module imports RateRule/RateCondition FROM this file, so this
    file cannot import it back at module scope. Per-jurisdiction record
    modules call this function instead; see program_rate_rules_worldwide.py."""
    for rule in rules:
        _RULES_BY_PROGRAM.setdefault(rule.program_slug, ())
        _RULES_BY_PROGRAM[rule.program_slug] = _RULES_BY_PROGRAM[rule.program_slug] + (rule,)


# Bottom-of-file import (after register_rate_rules/_RULES_BY_PROGRAM exist)
# — avoids the circular import that would result from importing this at
# the top: program_rate_rules_worldwide.py itself imports RateRule/
# RateCondition/register_rate_rules FROM this module.
from app.data import program_rate_rules_worldwide  # noqa: F401,E402


def _blended_effective_rate(tier: RateRule, qpe_usd: float | None) -> float:
    """Real blended effective rate (total credit / QPE) for a statute-
    confirmed graduated/bracketed tier — e.g. Spain Art. 36.2's 30% first
    EUR 1M / 25% excess. This is the maximum-lawful-incentive
    representation: NOT the flat marginal/excess rate (understates the
    real benefit for a production of any size) and NOT the flat top-
    bracket rate (overstates it for spend beyond the first bracket).
    Falls back to tier.rate unchanged when graduated_brackets is None —
    every existing non-graduated program is unaffected."""
    if not tier.graduated_brackets or qpe_usd is None or qpe_usd <= 0:
        return tier.rate
    total_credit = 0.0
    prev_ceiling = 0.0
    for ceiling, bracket_rate in tier.graduated_brackets:
        span = max(0.0, min(qpe_usd, ceiling) - prev_ceiling)
        total_credit += span * bracket_rate
        prev_ceiling = ceiling
        if qpe_usd <= ceiling:
            break
    else:
        if qpe_usd > prev_ceiling:
            total_credit += (qpe_usd - prev_ceiling) * tier.rate
    return total_credit / qpe_usd


#: Canonical served wiring repair (Codex Defect 4) — resolve_program_rate()
#: collapses two materially different reasons into the same `None`: a
#: program with NO rate rules at all (authority-insufficient) vs. a program
#: WITH rate rules that simply don't cover this production_type/QPE (a real
#: statutory threshold/rule rejection — e.g. a minimum-QPE gate the
#: production doesn't meet). Callers that need to distinguish these two
#: honestly (never re-evaluating, never changing which rate wins) call this
#: read-only classifier AFTER resolve_program_rate() has already returned
#: None. It mirrors resolve_program_rate()'s own eligibility gate exactly
#: (production_type + min_qpe_usd) and computes nothing new.
RATE_FAILURE_NO_RULES = "NO_RATE_RULES"
RATE_FAILURE_CONDITIONS_UNMET = "STATUTORY_CONDITIONS_UNMET"
#: B4 central authority gate (Codex bounded remediation): resolve_program_rate()
#: refused BEFORE any rule lookup because the program's accepted authority
#: status is exhausted / discretionary-display-only / retired / duplicate.
#: Outranks a stale RateRule. Distinct from NO_RATE_RULES (never had a rule)
#: and STATUTORY_CONDITIONS_UNMET (has rules, production doesn't qualify).
RATE_FAILURE_AUTHORITY_EXHAUSTED = "AUTHORITY_EXHAUSTED_FAIL_CLOSED"


def _fx_native_amount(
    qpe_usd: float | None, currency: str, fx_context: "CanonicalFXContext | None" = None,
) -> "tuple[float, float, str] | None":
    """Converts qpe_usd into `currency` via an explicit CanonicalFXContext
    -- returns (native_amount, rate_used, rate_date) or None when qpe_usd
    is unknown, the currency's rate cannot be safely resolved (missing,
    non-positive, or the context is flagged stale_fallback), or no
    fx_context was given and none could be defaulted. Codex final P0
    (canonical_fx): fx_context=None builds one fresh, single-call context
    via production_normalization.build_fx_context() -- never a leaked
    mid-calculation re-read of the mutable global. See
    _fx_native_amount_resolution() for the full typed disposition when a
    caller needs to disclose WHY this returned None."""
    if qpe_usd is None:
        return None
    result, resolution = _fx_native_amount_resolution(qpe_usd, currency, fx_context)
    if result is None or not resolution.ok:
        return None
    return result.target_amount, result.rate_used, result.rate_date


def _fx_native_amount_resolution(
    qpe_usd: float | None, currency: str, fx_context: "CanonicalFXContext | None" = None,
) -> "tuple[FXConversionResult | None, FXRateResolution]":
    """Full typed disposition backing _fx_native_amount() -- lets a
    caller (resolve_program_rate()'s disclosure loop) report the EXACT
    reason a native-currency threshold could not be evaluated (missing
    rate / non-positive rate / stale-unaccepted snapshot), never a flat
    unexplained None."""
    from app.calculators import apply_fx_rates
    from app.calculators.production_normalization import build_fx_context

    context = fx_context if fx_context is not None else build_fx_context()
    if qpe_usd is None:
        return None, apply_fx_rates.FXRateResolution(
            status=apply_fx_rates.FX_STATUS_MISSING, currency=currency.upper(), rate=None,
            snapshot_date=context.snapshot_date, source=context.source,
            detail="QPE is unknown — cannot convert to evaluate this native threshold.",
        )
    return apply_fx_rates.convert_usd_to_local_ctx(qpe_usd, currency, context)


def _amount_and_boolean_conditions_met(
    rule: RateRule,
    amount_facts: dict[str, float] | None,
    evidenced_facts: frozenset[str] | None,
    qpe_usd: float | None = None,
    fx_context: "CanonicalFXContext | None" = None,
) -> bool:
    """Shared tier-eligibility gate for RateCondition.amount_fact_*/
    required_boolean_fact_key/fx_native_* -- used identically by
    resolve_program_rate() and classify_rate_resolution_failure() so the
    two never diverge."""
    amounts = amount_facts or {}
    evidenced = evidenced_facts or frozenset()
    for cond in rule.conditions:
        if not cond.gates_tier_eligibility:
            continue  # disclosure-only for eligibility purposes; see RateCondition docstring
        if cond.amount_fact_key is not None:
            actual = amounts.get(cond.amount_fact_key)
            if cond.amount_fact_min is not None:
                if actual is None:
                    return False
                if cond.amount_fact_min_exclusive:
                    if actual <= cond.amount_fact_min:
                        return False
                elif actual < cond.amount_fact_min:
                    return False
            if cond.amount_fact_max is not None:
                # A cap is only a violation when a fact IS supplied and
                # exceeds it -- absence never retroactively fails an
                # otherwise-eligible tier (see RateCondition docstring).
                if actual is not None and actual > cond.amount_fact_max:
                    return False
        if cond.required_boolean_fact_key is not None:
            if cond.required_boolean_fact_key not in evidenced:
                return False
        if cond.blocked_by_boolean_fact_keys and any(k in evidenced for k in cond.blocked_by_boolean_fact_keys):
            return False
        if cond.fx_native_currency is not None and cond.fx_native_threshold_amount is not None:
            converted = _fx_native_amount(qpe_usd, cond.fx_native_currency, fx_context)
            if converted is None or converted[0] < cond.fx_native_threshold_amount:
                return False
    return True


#: CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR: currency inferred from an
#: amount_fact_key's suffix, used ONLY to decide how a generic probe/
#: derivation value should be converted -- never changes what a real,
#: caller- or allocation-derived fact means.
_AMOUNT_FACT_CURRENCY_SUFFIXES: dict[str, str] = {
    "_usd": "USD", "_aud": "AUD", "_mad": "MAD", "_thb": "THB",
    "_cad": "CAD", "_eur": "EUR", "_gbp": "GBP", "_nzd": "NZD",
    "_zar": "ZAR", "_mur": "MUR",
}


def _infer_amount_fact_currency(amount_fact_key: str) -> str | None:
    """Best-effort currency inferred from an amount_fact_key's naming
    convention (e.g. 'au_location_qape_aud' -> 'AUD'). None when no
    recognized currency suffix is present -- e.g. a shooting-day count
    like 'ma_ccm_shooting_days_count', which is never a money amount and
    is intentionally left un-inferred here."""
    for suffix, currency in _AMOUNT_FACT_CURRENCY_SUFFIXES.items():
        if amount_fact_key.endswith(suffix):
            return currency
    return None


#: A day-count/labor-hours-style amount_fact_key (no recognizable
#: currency suffix) cannot be derived from a dollar figure at all. This
#: is a deliberately generous, discovery-stage-ONLY placeholder so such a
#: program is not rejected merely because its real count has not yet
#: been evidenced -- the REAL count (a caller-supplied ProjectFact, e.g.
#: a real shooting schedule) is what price_segment/resolve_program_rate
#: test for real pricing; this constant is never threaded into a priced
#: result.
_GENERIC_DISCOVERY_NONMONETARY_PROBE = 1_000_000.0


def build_discovery_amount_probe(
    slug: str,
    qpe_usd: float | None,
    amount_facts: dict[str, float] | None = None,
    fx_context: "CanonicalFXContext | None" = None,
) -> dict[str, float]:
    """GENERIC discovery-stage amount-fact probe
    (CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR). Replaces the old
    us_or_opif-only special case that used to live in
    production_discovery.py / canonical_evaluation.py._price_candidate.

    Discovery (and _price_candidate's early preflight gate) must decide
    whether a (jurisdiction, program) pair is STRUCTURALLY relevant
    before any real candidate has allocated spend -- but many programs'
    RateCondition.amount_fact_key values (au_location_qape_aud,
    ca_bc_dave_qualified_labour_usd, ma_ccm_qualifying_spend_mad,
    th_film_incentive_qualifying_spend_thb, ...) can only be known
    EXACTLY after a real candidate allocation exists. Rejecting the
    candidate here -- before it is ever constructed -- means the real,
    tight, allocation-derived check (price_segment's own component-basis
    derivation, or resolve_program_rate's real amount_facts check) never
    gets a chance to run at all.

    For every amount_fact_key referenced by `slug`'s own rate rules that
    is not already supplied by the caller, this seeds a GENEROUS,
    discovery-only probe value from qpe_usd (the full budget available
    at this stage -- always >= any real per-component subtotal a later
    candidate could allocate, so this can only ever ADMIT a program to
    real candidate construction, never fabricate its final priced
    amount). Currency-suffixed keys are converted via the canonical FX
    path (_fx_native_amount); a key with no recognizable currency suffix
    (a day-count-style fact) gets the generic non-monetary placeholder --
    never a fabricated real value, since it is never threaded into the
    actual priced structure (price_segment recomputes/tests every real
    amount fact independently, from the real allocation or a real
    caller-supplied ProjectFact). A condition with an amount_fact_max
    is skipped: a generous probe could spuriously violate a cap this
    function has no way to know the real basis for, so that condition
    is left to fail exactly as it would have before this change."""
    probe = dict(amount_facts or {})
    if qpe_usd is None:
        return probe
    for rule in get_rate_rules(slug):
        for cond in rule.conditions:
            key = cond.amount_fact_key
            if key is None or key in probe:
                continue
            if cond.amount_fact_max is not None:
                continue
            currency = _infer_amount_fact_currency(key)
            if currency == "USD":
                probe[key] = qpe_usd
            elif currency is not None:
                converted = _fx_native_amount(qpe_usd, currency, fx_context)
                if converted is not None:
                    probe[key] = converted[0]
            else:
                probe[key] = _GENERIC_DISCOVERY_NONMONETARY_PROBE
    return probe


def classify_rate_resolution_failure(
    program_slug: str, production_type: str, qpe_usd: float | None,
    *,
    evidenced_facts: frozenset[str] | None = None,
    amount_facts: dict[str, float] | None = None,
    fx_context: "CanonicalFXContext | None" = None,
) -> str:
    """Read-only: why did resolve_program_rate() return None? Never called
    unless it already did. Returns RATE_FAILURE_AUTHORITY_EXHAUSTED (the B4
    central authority gate refused the program outright),
    RATE_FAILURE_NO_RULES (no statutory rate rules exist for this program) or
    RATE_FAILURE_CONDITIONS_UNMET (rate rules exist, but none apply to this
    production_type/QPE/evidenced-fact/amount-fact combination). The B4
    preflight is identical to resolve_program_rate()'s and runs first."""
    if economic_block_for_program(program_slug) is not None:
        return RATE_FAILURE_AUTHORITY_EXHAUSTED
    rules = get_rate_rules(program_slug)
    if not rules:
        return RATE_FAILURE_NO_RULES
    for rule in rules:
        if production_type not in rule.production_types:
            continue
        if rule.min_qpe_usd is not None and (qpe_usd is None or qpe_usd < _effective_min_qpe(rule, amount_facts)):
            continue
        if not _amount_and_boolean_conditions_met(rule, amount_facts, evidenced_facts, qpe_usd, fx_context):
            continue
        return RATE_FAILURE_CONDITIONS_UNMET  # defensive: resolve_program_rate should not have returned None here
    return RATE_FAILURE_CONDITIONS_UNMET


# ── Oregon (us_or_opif) composite formula (Codex final four-row remediation,
# P0-OR-001, fourth pass) ───────────────────────────────────────────────────

_OREGON_PAYROLL_TIER_ID = "us-or-payroll-ceiling-20"
_OREGON_OTHER_TIER_ID = "us-or-other-ceiling-25"
_OREGON_PAYROLL_RATE = 0.20
_OREGON_OTHER_RATE = 0.25
_OREGON_COMBINED_MIN_QPE_USD = 1_000_000.0
_OREGON_PER_PAYEE_QPE_EXCLUSION_USD = 1_000_000.0


def oregon_per_payee_capped_total(
    payee_amounts_usd: "list[float] | tuple[float, ...]",
    per_payee_cap_usd: float = _OREGON_PER_PAYEE_QPE_EXCLUSION_USD,
) -> float:
    """Codex final four-row remediation (P0-OR-001, fourth pass): OAR
    951-002-0010's real per-individual/company USD1,000,000 QPE
    exclusion, applied BEFORE the 20%/25% rates — a pure, independently
    testable function (never folded silently into resolve_program_rate's
    own arithmetic, and never applied AFTER rating). Each payee's own
    qualifying compensation is capped at per_payee_cap_usd before being
    summed into either component basis; a payee whose real compensation
    exceeds the cap contributes only the cap, never their full amount.
    Raises ValueError on a negative/non-finite entry — a malformed
    payee amount is rejected outright, never silently zeroed or
    included as-is."""
    total = 0.0
    for amt in payee_amounts_usd:
        if not isinstance(amt, (int, float)) or isinstance(amt, bool) or not math.isfinite(amt) or amt < 0:
            raise ValueError(f"payee amount {amt!r} is not a finite, non-negative number")
        total += min(amt, per_payee_cap_usd)
    return round(total, 2)


def _resolve_us_or_opif_composite(
    rules: tuple["RateRule", ...],
    amount_facts: dict[str, float] | None,
    evidenced_facts: frozenset[str] | None,
) -> "RateResolution | None":
    """Codex final four-row remediation (P0-OR-001, fourth pass) — see
    resolve_program_rate's own call site for why this is a dedicated,
    self-contained branch rather than a generalization of the ordinary
    single-winning-tier tournament. Returns None (never a fabricated
    composite) whenever fewer than both component facts are present, or
    either is malformed, or the COMBINED total is below the real
    USD1,000,000 statutory threshold (never each component
    independently — Codex's exact reproducer: USD1,100,000 payroll +
    USD100,000 other, where the "other" component alone is far below
    USD1,000,000, must still combine to USD245,000, never reject on a
    per-component minimum that does not exist in the statute) — in every
    None case the caller falls straight through to the ordinary
    single-tier tournament, unchanged."""
    amount_facts = amount_facts or {}
    evidenced_facts = evidenced_facts or frozenset()
    payroll_qpe = amount_facts.get("us_or_payroll_qpe_usd")
    other_qpe = amount_facts.get("us_or_other_qpe_usd")
    if payroll_qpe is None or other_qpe is None:
        return None

    payroll_tier = next((r for r in rules if r.tier_id == _OREGON_PAYROLL_TIER_ID), None)
    other_tier = next((r for r in rules if r.tier_id == _OREGON_OTHER_TIER_ID), None)
    if payroll_tier is None or other_tier is None:
        return None  # doctrine not registered as expected -- never fabricate a composite

    def _valid(amt) -> bool:
        return isinstance(amt, (int, float)) and not isinstance(amt, bool) and math.isfinite(amt) and amt >= 0

    if not _valid(payroll_qpe) or not _valid(other_qpe):
        return None  # malformed component -- disclosed via the ordinary "did not resolve" path

    combined = round(payroll_qpe + other_qpe, 2)
    if combined < _OREGON_COMBINED_MIN_QPE_USD:
        return None  # below the real COMBINED statutory threshold -- never priced

    gross = round(payroll_qpe * _OREGON_PAYROLL_RATE + other_qpe * _OREGON_OTHER_RATE, 2)
    blended_rate = round(gross / combined, 6) if combined > 0 else 0.0

    incentive_uplift_multiplier: float | None = None
    for tier in (payroll_tier, other_tier):
        for cond in tier.conditions:
            if (cond.regional_uplift_multiplier_fact_key is not None
                    and cond.regional_uplift_multiplier_fact_key in evidenced_facts):
                incentive_uplift_multiplier = cond.regional_uplift_multiplier
                break
        if incentive_uplift_multiplier is not None:
            break

    evaluations: list[ConditionEvaluation] = [
        ConditionEvaluation(
            "us-or-combined-min-spend", "Combined Oregon qualifying expenditure (payroll + other)",
            "a production must directly spend at least US $1 million in Oregon to qualify "
            "(corroborated by 3 sources) -- applied to the COMBINED payroll + other total, "
            "never each disjoint component independently",
            satisfied=True, kind="min_qpe_usd", condition_state=CONDITION_STATE_EXECUTABLE,
            note=(f"combined Oregon QPE ${combined:,.2f} (payroll ${payroll_qpe:,.2f} + "
                  f"other ${other_qpe:,.2f}) vs the real combined threshold "
                  f"${_OREGON_COMBINED_MIN_QPE_USD:,.2f}."),
        ),
        ConditionEvaluation(
            "us-or-payroll-component-basis", "20% Oregon payroll component",
            "Codex bounded remediation, accepted formulaic correction: 'Up to 20% Oregon "
            "payroll plus 25% other Oregon expenses'",
            satisfied=True, kind="project_fact_dependent_eligibility", condition_state=CONDITION_STATE_EXECUTABLE,
            note=f"'us_or_payroll_qpe_usd' = {payroll_qpe:,.2f}, priced at 20%.",
        ),
        ConditionEvaluation(
            "us-or-other-component-basis", "25% other (non-payroll) Oregon component",
            "Codex bounded remediation, accepted formulaic correction: 'Up to 20% Oregon "
            "payroll plus 25% other Oregon expenses'",
            satisfied=True, kind="project_fact_dependent_eligibility", condition_state=CONDITION_STATE_EXECUTABLE,
            note=f"'us_or_other_qpe_usd' = {other_qpe:,.2f}, priced at 25%.",
        ),
    ]
    # The SAME real award/contract/fund-availability/per-payee-compliance
    # gate and the SAME dated-fund-currency gate as the single-tier path
    # (each modeled as its own machine-readable condition, per Codex's
    # "represent ... as separate machine-readable gates (not one bundled
    # boolean)") -- both tiers declare the identical condition_ids, so
    # only the first occurrence of each is emitted here.
    _seen_shared_ids: set[str] = set()
    for tier in (payroll_tier, other_tier):
        for cond in tier.conditions:
            if cond.condition_id not in ("us-or-award-contract-fund-confirmed", "us-or-fund-amount-current"):
                continue
            if cond.condition_id in _seen_shared_ids:
                continue
            _seen_shared_ids.add(cond.condition_id)
            evidenced = cond.required_boolean_fact_key is not None and cond.required_boolean_fact_key in evidenced_facts
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=True if evidenced else None,
                note=("Evidenced by the production." if evidenced
                      else f"'{cond.required_boolean_fact_key}' not yet evidenced — "
                           "absence of a record is not confirmation."),
                condition_state=CONDITION_STATE_EXECUTABLE if evidenced else CONDITION_STATE_USER_FACT_REQUIRED,
                kind=cond.kind,
            ))
    if incentive_uplift_multiplier is not None:
        evaluations.append(ConditionEvaluation(
            "us-or-regional-uplift", "10% regional increase outside the Portland metropolitan zone",
            "an increase of 10 percent of the amount otherwise allowable under subsections "
            "(2) and (3) (ORS 284.368, verified via direct fetch of oregonlegislature.gov)",
            satisfied=True, kind="project_fact_dependent_uplift", condition_state=CONDITION_STATE_EXECUTABLE,
            note="Evidenced regional uplift — multiplies the composite incentive by 1.10.",
        ))

    return RateResolution(
        program_slug="us_or_opif",
        modeled_rate=blended_rate,
        floor_rate=blended_rate,
        has_guaranteed_floor=True,
        is_band_ceiling=False,
        tier_id="us-or-composite-payroll20-other25",
        basis=(
            "Composite calculation (Codex final four-row remediation, P0-OR-001): "
            f"payroll QPE ${payroll_qpe:,.2f} x 20% + other QPE ${other_qpe:,.2f} x 25% = "
            f"${gross:,.2f} gross, before any evidenced regional uplift or fund cap."
        ),
        conditions_evaluated=tuple(evaluations),
        unverified_claims=_UNVERIFIED_BY_PROGRAM.get("us_or_opif", ()),
        conflicts=(),
        composite_incentive_usd=gross,
        incentive_uplift_multiplier=incentive_uplift_multiplier,
    )


def _effective_min_qpe(rule, amount_facts) -> float:
    """A tier's minimum QPE, lowered (never raised) by a caller-computed share-of-worldwide branch. New York's post credit requires qualified
    post costs of at least the LESSER of $1,000,000 or 75% of the worldwide post cost (tax.ny.gov/legal/2025/pit-corp-changes.htm); the
    dollar floor on the tier is only the first branch, so price_segment supplies min(dollar, share x worldwide) under this key when the
    worldwide figure is known. Absent the key, the dollar floor stands."""
    override = (amount_facts or {}).get(f"min_qpe_override:{rule.program_slug}")
    return min(rule.min_qpe_usd, float(override)) if override is not None else rule.min_qpe_usd


def resolve_program_rate(
    program_slug: str,
    production_type: str,
    qpe_usd: float | None,
    gross_budget_usd: float | None = None,
    *,
    evidenced_facts: frozenset[str] | None = None,
    amount_facts: dict[str, float] | None = None,
    fx_context: "CanonicalFXContext | None" = None,
) -> RateResolution | None:
    """
    Resolve the modeled rate for one production from database/statutory
    rules ONLY (Rules 1-3). Returns None when the program has no rate
    rules (absence, not an error — callers must not invent a rate).

    evidenced_facts/amount_facts (Codex final runtime remediation, 11 B3
    formulaic rows): optional, additive, keyword-only. evidenced_facts is
    a frozenset of caller-attested boolean fact-id strings (e.g.
    preapproval granted, an award confirmed); amount_facts is a dict of
    caller-attested numeric facts keyed by an arbitrary string, in
    whatever native currency or component basis that key documents --
    NEVER derived here via a fabricated or guessed conversion. Both
    default to empty, so every existing caller that does not pass them is
    completely unaffected (byte-identical prior behavior). See
    RateCondition.amount_fact_key/amount_fact_min/amount_fact_max/
    required_boolean_fact_key.

    Tier selection: the highest-rate tier whose production_types include
    this production and whose min_qpe_usd is met by qpe_usd. A None
    qpe_usd fails every thresholded tier (unknown is not satisfied).
    Budget-evidenced rates are NEVER considered (Rule 2); any that exist
    for the program are reported as conflicts when they differ from the
    resolved rate (Rule 5).

    B4 central authority gate (Codex bounded remediation): the FIRST
    executable check, before any rule lookup — an accepted authority-
    exhausted / discretionary-display-only / retired / duplicate identity
    resolves to no rate, and a stale RateRule cannot override that.
    """
    if economic_block_for_program(program_slug) is not None:
        return None

    rules = get_rate_rules(program_slug)
    if not rules:
        return None

    # Codex final four-row remediation (P0-OR-001, fourth pass): Oregon's
    # required "ONE composite calculation: payroll_QPE x 20% + other_QPE
    # x 25%" cannot be expressed by the ordinary single-winning-tier
    # tournament below, which selects exactly ONE eligible RateRule by
    # rate. This dedicated, fully self-contained, opt-in branch runs
    # ONLY for us_or_opif and ONLY when BOTH component facts are
    # present; otherwise it returns None and execution falls straight
    # through to the SAME generic tournament every other program uses,
    # completely unchanged (a caller supplying only one component fact
    # still gets that single tier's own pre-existing disclosure/
    # eligibility behavior, byte-identical to before this pass).
    if program_slug == "us_or_opif":
        _composite = _resolve_us_or_opif_composite(rules, amount_facts, evidenced_facts)
        if _composite is not None:
            return _composite

    eligible: list[RateRule] = []
    for rule in sorted(rules, key=lambda r: -r.rate):
        if production_type not in rule.production_types:
            continue
        if rule.min_qpe_usd is not None and (qpe_usd is None or qpe_usd < _effective_min_qpe(rule, amount_facts)):
            continue
        if not _amount_and_boolean_conditions_met(rule, amount_facts, evidenced_facts, qpe_usd, fx_context):
            continue
        eligible.append(rule)

    if not eligible:
        return None

    tier = eligible[0]

    # Codex final P0 (us_tx_miip): "Award facts select only maximum 31%"
    # -- when this tier names an awarded_rate_fact_key, the caller-
    # supplied EXACT awarded rate (validated against [awarded_rate_min,
    # awarded_rate_max]) replaces the tier's own static `rate` for every
    # downstream computation (floor_rate, modeled_rate, incentive
    # dollars). A missing or out-of-range value does NOT change
    # eligibility here (preserving the existing "disclosed, pending
    # confirmation" ceiling semantics for a program with no other
    # guaranteed floor) -- it instead surfaces as a synthetic condition
    # below (satisfied=None if missing, satisfied=False if present but
    # invalid), so the SAME floorless-ceiling fail-closed guard
    # (allocation_pricing.py: "satisfied is not True") already blocks
    # pricing until a genuinely valid awarded rate is evidenced.
    _awarded_rate_value: float | None = None
    _awarded_rate_condition: "ConditionEvaluation | None" = None
    if tier.awarded_rate_fact_key is not None:
        _raw_awarded = (amount_facts or {}).get(tier.awarded_rate_fact_key)
        # Codex adverse finding (P0-TX-001): the ORIGINAL range check used
        # plain `<`/`>` comparisons, which have two distinct defects.
        # (1) NaN fails EVERY comparison (`NaN < min` and `NaN > max` are
        # both False), so a NaN award silently fell through to the "in
        # range" branch and was multiplied directly into a NaN incentive.
        # (2) `awarded_rate_min` was compared with `<` (inclusive), so a
        # rate of EXACTLY 0 passed -- "0 < rate <= 0.31" requires 0 itself
        # to be REJECTED (strictly greater than zero), not merely
        # excluded below zero. `math.isfinite()` is checked FIRST, before
        # any range comparison; the lower bound then uses `<=` against
        # `awarded_rate_min` (an EXCLUSIVE floor) while the upper bound
        # keeps `>` against `awarded_rate_max` (an INCLUSIVE ceiling) —
        # matching the exact authorized range `(min, max]`.
        if _raw_awarded is None:
            _awarded_rate_condition = ConditionEvaluation(
                f"{tier.tier_id}-awarded-rate", "Exact awarded rate/tier for this production",
                "", kind="awarded_rate_fact", satisfied=None,
                note=(f"'{tier.awarded_rate_fact_key}' not evidenced — the authorized "
                      f"rate ceiling ({tier.rate:.0%}) is never assumed to be the actual "
                      "production-specific awarded rate."),
                condition_state=CONDITION_STATE_USER_FACT_REQUIRED,
            )
        elif not isinstance(_raw_awarded, (int, float)) or isinstance(_raw_awarded, bool) or not math.isfinite(_raw_awarded):
            _awarded_rate_condition = ConditionEvaluation(
                f"{tier.tier_id}-awarded-rate", "Exact awarded rate/tier for this production",
                "", kind="awarded_rate_fact", satisfied=False,
                note=(f"'{tier.awarded_rate_fact_key}' = {_raw_awarded!r} is not a finite number "
                      "(NaN/+inf/-inf/non-numeric) — a malformed awarded rate/tier must reject, "
                      "never be multiplied into a corrupted incentive."),
                condition_state=CONDITION_STATE_EXECUTABLE,
            )
        elif (
            (tier.awarded_rate_min is not None and _raw_awarded <= tier.awarded_rate_min)
            or (tier.awarded_rate_max is not None and _raw_awarded > tier.awarded_rate_max)
        ):
            _awarded_rate_condition = ConditionEvaluation(
                f"{tier.tier_id}-awarded-rate", "Exact awarded rate/tier for this production",
                "", kind="awarded_rate_fact", satisfied=False,
                note=(f"'{tier.awarded_rate_fact_key}' = {_raw_awarded:.4f} is outside the "
                      f"authorized range ({tier.awarded_rate_min}, {tier.awarded_rate_max}] "
                      "— a malformed or out-of-range awarded rate/tier must reject, never "
                      "clamp to the ceiling or silently accept."),
                condition_state=CONDITION_STATE_EXECUTABLE,
            )
        else:
            _awarded_rate_value = _raw_awarded
            _awarded_rate_condition = ConditionEvaluation(
                f"{tier.tier_id}-awarded-rate", "Exact awarded rate/tier for this production",
                "", kind="awarded_rate_fact", satisfied=True,
                note=(f"'{tier.awarded_rate_fact_key}' = {_raw_awarded:.4f} is within the "
                      f"authorized range ({tier.awarded_rate_min}, {tier.awarded_rate_max}] — "
                      "this production's own awarded rate, not the program's authorized ceiling."),
                condition_state=CONDITION_STATE_EXECUTABLE,
            )
        if _awarded_rate_value is not None:
            tier = replace(tier, rate=_awarded_rate_value)

    floor_candidates = [r for r in eligible if not r.is_band_ceiling]
    # A lone band ceiling has NO guaranteed floor. floor_rate still repeats
    # the ceiling so existing arithmetic/disclosure is unchanged, but
    # has_guaranteed_floor records the truth so no consumer can silently
    # treat "up to X%" as "X% guaranteed" (a ceiling is a limit, not an
    # award). See allocation_pricing._price_segment for the fail-closed
    # consumption.
    has_guaranteed_floor = bool(floor_candidates)
    floor_rate = floor_candidates[0].rate if floor_candidates else tier.rate
    effective_rate = _blended_effective_rate(tier, qpe_usd)

    # Component-basis substitution (us_or_opif etc.): when the selected
    # tier's rate is gated on a component-basis amount_fact_min (a
    # sub-portion of spend, not the segment's total qpe_usd), the dollar
    # incentive must be computed against THAT component's own amount, not
    # the full segment QPE -- otherwise a 20%-of-payroll-only rate would
    # be silently applied to payroll+other combined. Only ever set from a
    # fact the caller actually supplied; never fabricated.
    qpe_basis_used: float | None = None
    qpe_basis_line_components: tuple[str, ...] | None = None
    for cond in tier.conditions:
        if cond.is_component_basis and cond.amount_fact_key is not None:
            qpe_basis_used = (amount_facts or {}).get(cond.amount_fact_key)
            qpe_basis_line_components = cond.component_basis_line_components
            break
    # CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE (Task 4):
    # a real, discovered second-order defect. A "ceiling-with-a-real-
    # floor" program (e.g. ca_bc_pstc: 36% guaranteed base tier + 48%
    # regional/distant-location discretionary ceiling tier) applies BOTH
    # its floor and ceiling percentage to the SAME real qualifying base
    # (BC labour expenditure) -- the base tier's own component-basis
    # condition was never consulted when the CEILING tier is the one
    # `tier` (selected above) resolves to, so qpe_basis_used stayed None
    # and price_segment fell back to pricing the FLOOR rate off the
    # segment's entire broad QPE -- a real, material overstatement (proven
    # by test_narrower_rate_base_programs_price_off_the_real_traced_
    # labour_subtotal_only: $3,960,000 served instead of the real
    # $144,000). If the selected tier itself declared no component basis,
    # fall back to checking the REAL, separate floor tier's own
    # conditions -- the floor and ceiling of ONE program share ONE
    # underlying qualifying base by construction (a higher percentage of
    # the SAME base, never a different base), so this is safe generically,
    # not a per-program special case.
    if qpe_basis_used is None and floor_candidates and floor_candidates[0].tier_id != tier.tier_id:
        for cond in floor_candidates[0].conditions:
            if cond.is_component_basis and cond.amount_fact_key is not None:
                qpe_basis_used = (amount_facts or {}).get(cond.amount_fact_key)
                qpe_basis_line_components = cond.component_basis_line_components
                break

    # Codex final wiring remediation (P0-OR-001): a MULTIPLICATIVE
    # incentive uplift, applied only once its own evidenced fact is
    # present -- never inferred, never additive on the rate.
    incentive_uplift_multiplier: float | None = None
    for cond in tier.conditions:
        if (cond.regional_uplift_multiplier_fact_key is not None
                and cond.regional_uplift_multiplier_fact_key in (evidenced_facts or frozenset())):
            incentive_uplift_multiplier = cond.regional_uplift_multiplier
            break

    evaluations: list[ConditionEvaluation] = []
    for cond in tier.conditions:
        if cond.kind == "production_type":
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=True,
                note=f"Production type '{production_type}' is within the tier's scope.",
                condition_state=CONDITION_STATE_EXECUTABLE,
            ))
        elif cond.kind == "min_qpe_usd":
            met = qpe_usd is not None and cond.threshold_usd is not None and qpe_usd >= cond.threshold_usd
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=met if cond.threshold_usd is not None else True,
                note=(f"QPE ${qpe_usd:,.0f} vs threshold ${cond.threshold_usd:,.0f}"
                      if qpe_usd is not None and cond.threshold_usd is not None
                      else "Threshold condition evaluated at tier selection."),
                condition_state=CONDITION_STATE_EXECUTABLE,
            ))
        elif cond.kind == "discretionary_band":
            superseding_key = cond.superseded_by_boolean_fact_key
            if superseding_key is not None and superseding_key in (evidenced_facts or frozenset()):
                evaluations.append(ConditionEvaluation(
                    cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                    satisfied=True,
                    note=(f"Confirmed by the authoritative awarded-rate fact "
                          f"'{superseding_key}' — the discretionary criteria this "
                          "condition documents are the awarding authority's own "
                          "internal factors, not a separate engine-verifiable gate "
                          "once the actual award/certificate is evidenced."),
                    condition_state=CONDITION_STATE_EXECUTABLE,
                ))
            else:
                evaluations.append(ConditionEvaluation(
                    cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                    satisfied=None,
                    note="Cannot be pre-satisfied: the awarded rate within the 'up to' "
                         "band is set by the authority at approval. The engine models "
                         "the ceiling; the guaranteed floor is the non-band tier.",
                    condition_state=CONDITION_STATE_AUTHORITY_UNRESOLVED,
                ))
        elif cond.kind == "graduated_bracket_applied":
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=True,
                note=(f"Statute-confirmed bracket, not discretionary — blended to "
                      f"a real effective rate of {effective_rate:.2%} for QPE "
                      f"${qpe_usd:,.0f}." if qpe_usd is not None
                      else "Bracket structure confirmed; blended rate requires a "
                           "known QPE to compute."),
                condition_state=CONDITION_STATE_EXECUTABLE,
            ))
        elif cond.kind == "min_qpe_pct_of_total_budget":
            if qpe_usd is not None and gross_budget_usd and gross_budget_usd > 0 and cond.threshold_pct is not None:
                actual_pct = qpe_usd / gross_budget_usd
                met = actual_pct >= cond.threshold_pct
                evaluations.append(ConditionEvaluation(
                    cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                    satisfied=met,
                    note=(f"QPE is {actual_pct:.1%} of total budget "
                          f"(${qpe_usd:,.0f} / ${gross_budget_usd:,.0f}) vs the "
                          f"statutory minimum of {cond.threshold_pct:.1%}."),
                    condition_state=CONDITION_STATE_EXECUTABLE,
                ))
            else:
                evaluations.append(ConditionEvaluation(
                    cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                    satisfied=None,
                    note="Executable in principle (QPE-to-total-budget ratio), but "
                         "the production's total budget was not supplied to this "
                         "resolution — cannot compute the ratio.",
                    condition_state=CONDITION_STATE_USER_FACT_REQUIRED,
                ))
        elif cond.amount_fact_key is not None:
            actual = (amount_facts or {}).get(cond.amount_fact_key)
            if cond.amount_fact_min is not None:
                if actual is None:
                    satisfied, note, state = (
                        None,
                        f"'{cond.amount_fact_key}' not evidenced — cannot confirm "
                        f"the statutory minimum without this production fact.",
                        CONDITION_STATE_USER_FACT_REQUIRED,
                    )
                else:
                    met = (
                        actual > cond.amount_fact_min if cond.amount_fact_min_exclusive
                        else actual >= cond.amount_fact_min
                    )
                    satisfied, state = met, CONDITION_STATE_EXECUTABLE
                    comparator = "exclusive minimum (strictly above)" if cond.amount_fact_min_exclusive else "minimum"
                    note = (f"'{cond.amount_fact_key}' = {actual:,.2f} vs statutory "
                            f"{comparator} {cond.amount_fact_min:,.2f}.")
            else:  # amount_fact_max (a cap): absence discloses, never fails
                if actual is None:
                    satisfied, note, state = (
                        None,
                        f"'{cond.amount_fact_key}' not evidenced — the "
                        f"{cond.amount_fact_max:,.2f} cap's applicability to this "
                        f"production is undetermined, not assumed clear.",
                        CONDITION_STATE_USER_FACT_REQUIRED,
                    )
                else:
                    met = actual <= cond.amount_fact_max
                    satisfied, state = met, CONDITION_STATE_EXECUTABLE
                    note = (f"'{cond.amount_fact_key}' = {actual:,.2f} vs statutory "
                            f"cap {cond.amount_fact_max:,.2f}.")
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=satisfied, note=note, condition_state=state,
            ))
        elif cond.required_boolean_fact_key is not None:
            evidenced = cond.required_boolean_fact_key in (evidenced_facts or frozenset())
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=True if evidenced else None,
                note=("Evidenced by the production." if evidenced
                      else f"'{cond.required_boolean_fact_key}' not yet evidenced — "
                           "absence of a record is not confirmation."),
                condition_state=CONDITION_STATE_EXECUTABLE if evidenced else CONDITION_STATE_USER_FACT_REQUIRED,
            ))
        elif cond.fx_native_currency is not None and cond.fx_native_threshold_amount is not None:
            converted = _fx_native_amount(qpe_usd, cond.fx_native_currency, fx_context)
            if converted is None:
                _, _fx_res = _fx_native_amount_resolution(qpe_usd, cond.fx_native_currency, fx_context)
                satisfied, note, state = (
                    None,
                    f"Cannot convert to evaluate this native threshold: {_fx_res.detail}",
                    CONDITION_STATE_AUTHORITY_UNRESOLVED,
                )
            else:
                native_amount, rate_used, rate_date = converted
                met = native_amount >= cond.fx_native_threshold_amount
                satisfied, state = met, CONDITION_STATE_EXECUTABLE
                note = (f"QPE ${qpe_usd:,.2f} = {cond.fx_native_currency} {native_amount:,.2f} "
                        f"(rate {rate_used} {cond.fx_native_currency}/USD, {rate_date}, "
                        f"USD->{cond.fx_native_currency}) vs native statutory minimum "
                        f"{cond.fx_native_currency} {cond.fx_native_threshold_amount:,.2f}.")
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=satisfied, note=note, condition_state=state,
            ))
        else:
            state = CONDITION_KIND_STATE.get(cond.kind, CONDITION_STATE_AUTHORITY_UNRESOLVED)
            if state == CONDITION_STATE_NOT_APPLICABLE:
                satisfied: bool | None = True
                note = "Not applicable to this production/program combination."
            elif state == CONDITION_STATE_DISCLOSURE_ONLY:
                satisfied = None
                note = "Disclosure only — informational, never a pass/fail gate on the modeled rate."
            elif state in (CONDITION_STATE_USER_FACT_REQUIRED, CONDITION_STATE_SCRIPT_FACT_REQUIRED):
                satisfied = None
                note = "Production fact not yet evidenced either way — absence of a record is not confirmation."
            else:  # AUTHORITY_UNRESOLVED (includes discretionary-adjacent/unmodeled-ratio/no-cap-cited kinds)
                satisfied = None
                note = "No controlling authority currently on file resolves this condition deterministically."
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote, kind=cond.kind,
                satisfied=satisfied, note=note, condition_state=state,
            ))

    if _awarded_rate_condition is not None:
        evaluations.append(_awarded_rate_condition)

    conflicts: list[RateConflict] = []
    for ber in _BUDGET_RATES_BY_PROGRAM.get(program_slug, ()):
        if abs(ber.rate - tier.rate) > 1e-9:
            conflicts.append(RateConflict(
                source_kind="budget_document",
                claimed_rate=ber.rate,
                database_rate=tier.rate,
                resolution="Database/statutory rate used; budget-document figure "
                           "ignored per permanent Rules 1, 2 and 5.",
                detail=ber.observed_in,
            ))

    if not tier.is_band_ceiling:
        band_note = ""
    elif not any(c.kind == "discretionary_band" for c in tier.conditions):
        band_note = (
            " This higher rate applies only if the project fact named in its condition is evidenced; until then it is a "
            "conditional planning scenario, not an award or a guarantee"
            + (f", and the guaranteed rate is {floor_rate:.0%}." if has_guaranteed_floor else ".")
        )
    elif has_guaranteed_floor:
        band_note = (
            " The source says 'up to' this rate — it is a modeling ceiling subject to "
            f"EDB approval; the guaranteed floor tier is {floor_rate:.0%}."
        )
    else:
        band_note = (
            " The source says 'up to' this rate — it is a modeling ceiling subject to "
            "EDB approval; NO guaranteed floor tier is eligible on the evidenced facts, so "
            "nothing here is a guaranteed amount."
        )
    bracket_note = (
        f" Statute-confirmed marginal/bracketed rate: blended to a real effective "
        f"rate of {effective_rate:.2%} for this QPE (not the flat top-bracket "
        f"marginal rate) — see RateRule.graduated_brackets."
        if tier.graduated_brackets else ""
    )
    return RateResolution(
        program_slug=program_slug,
        modeled_rate=effective_rate,
        floor_rate=floor_rate,
        has_guaranteed_floor=has_guaranteed_floor,
        is_band_ceiling=tier.is_band_ceiling,
        tier_id=tier.tier_id,
        basis=f"{tier.citation}{band_note}{bracket_note}",
        conditions_evaluated=tuple(evaluations),
        unverified_claims=_UNVERIFIED_BY_PROGRAM.get(program_slug, ()),
        conflicts=tuple(conflicts),
        qpe_basis_used=qpe_basis_used,
        qpe_basis_line_components=qpe_basis_line_components,
        incentive_uplift_multiplier=incentive_uplift_multiplier,
    )


#: Stated producer amount facts (days are counts; amounts are USD) read by the British Columbia statutory-formula uplift rules.
BC_DAYS_IN_BC_FACT = "ca_bc_principal_photography_days_in_bc"
BC_DAYS_OUTSIDE_VANCOUVER_FACT = "ca_bc_principal_photography_days_outside_vancouver"
BC_DAYS_DISTANT_FACT = "ca_bc_principal_photography_days_distant_location"
BC_TRAINING_PAYMENTS_FACT = "ca_bc_training_payments_usd"
BC_TRAINING_ASSISTANCE_FACT = "ca_bc_training_assistance_usd"
BC_SCRIPTWRITING_FACT = "ca_bc_scriptwriting_expenditure_usd"
BC_SCRIPTWRITING_ASSISTANCE_FACT = "ca_bc_scriptwriting_assistance_usd"
BC_SCRIPTWRITING_REIMBURSEMENT_FACT = "ca_bc_scriptwriting_parent_reimbursement_usd"
NS_DAYS_TOTAL_FACT = "ca_ns_principal_photography_days_total"
NS_DAYS_ZONE_A_FACT = "ca_ns_principal_photography_days_100_to_150km"
NS_DAYS_ZONE_B_FACT = "ca_ns_principal_photography_days_over_150km"
NS_RURAL_FACT = "ca_ns_rural_majority_principal_photography_confirmed"


@dataclass(frozen=True)
class EligibleSubsetUpliftRule:
    uplift_id: str
    rate: float
    eligible_categories: frozenset[str] | None = None
    excluded_categories: frozenset[str] = frozenset()
    exclusive_group: str | None = None
    eligible_production_types: frozenset[str] | None = None
    excluded_fact: str | None = None
    source_ref: str = ""
    #: Evidenced fact that must be present before ANY of this uplift is confirmed (a statutory prerequisite such as
    #: "majority of principal-photography days in the listed counties"). Absent: the uplift stays an unconfirmed bound.
    prerequisite_fact: str | None = None
    #: Evidenced fact attesting that EVERY eligible qualified line is wholly within the uplift's base, so no per-line
    #: subset is needed. Without it each line needs its own `uplift_basis:` evidenced amount.
    whole_base_fact: str | None = None
    #: True for an uplift that exists only by application/election (e.g. NY Production Plus): without its prerequisite
    #: fact it contributes nothing, not even a bound.
    potential_requires_prerequisite: bool = False
    #: The film's gross budget must be at least this (statutory minimum budget); below it the uplift does not apply.
    min_gross_budget_usd: float | None = None
    #: The film's gross budget must not exceed this (e.g. Alabama's small-budget bracket ends at total production expenditures of $499,999).
    max_gross_budget_usd: float | None = None
    #: Ceiling on the TOTAL base this uplift can apply to across all lines (e.g. an enhanced rate on only the first $240,000 of labour).
    base_cap_usd: float | None = None
    #: NA-RECONCILIATION-16. "subset" (default) prices `rate` on evidenced per-line subsets. The statutory-FORMULA kinds price the host credit's own qualified-labour basis (QLE) and take
    #: their other inputs from stated producer facts only: never proxied from dollars, never defaulted. An unstated input leaves the credit a disclosed, conditional bound.
    #:   "day_ratio":     rate x QLE x (numerator days / denominator days) -- BC regional (ITA (BC) s.81.1, s.82.2) and distant-location (s.81.11, s.82.21) credits.
    #:   "scriptwriting": rate x (SE - (TA + RE)) -- BC scriptwriting credit (s.80.1(3)); SE/TA/RE are stated amounts.
    #:   "training":      the lesser of rate x QLE and net_share x (payments - assistance) -- BC film training credit (s.82(2)).
    kind: str = "subset"
    day_numerator_fact: str | None = None            # amount fact: days of principal photography in the rule's zone (outside the designated Vancouver area, or a distant location)
    day_denominator_fact: str | None = None          # amount fact: total days of principal photography in the province (the statutory TD)
    min_numerator_days: int | None = None            # statutory minimum count of numerator days (regional: at least 5; distant location: at least 1)
    min_share_exclusive: float | None = None         # the numerator share must EXCEED this fraction of the denominator (regional: more than 50%); integer arithmetic at the boundary
    companion_uplift_id: str | None = None           # a day_ratio rule of the same program whose own eligibility this one also requires (distant location requires the regional credit)
    companion_bounds_numerator: bool = False         # the companion's numerator days contain this rule's days (distant days are outside the designated Vancouver area)
    series_needs_episode_facts: bool = False         # a series is computed on its qualifying episodes only, which the budget cannot isolate: confirmed 0, bounded by the whole-production figure
    excluded_production_types: frozenset[str] = frozenset()   # production types the statute excludes for a prospective production (animation regional credits ended for photography from 2024-06-01)
    amount_fact: str | None = None                   # scriptwriting SE / training payments (stated amount, USD)
    assistance_facts: tuple[str, ...] = ()           # stated assistance amounts subtracted from `amount_fact` (scriptwriting TA and RE; training assistance); ALL must be stated for a confirmed figure
    net_share: float | None = None                   # training: share of (payments - assistance)
    #: "tiered_day_ratio" (Nova Scotia distant-location incentive): sum over distance bands of tier_rate x (days in that band / total days), the bands exclusive (a location earns the highest tier it meets).
    tier_rates: tuple[float, ...] = ()
    tier_numerator_facts: tuple[str, ...] = ()
    #: NA-RECONCILIATION-18 formula kinds (all on the host credit's own basis, stated facts only):
    #:   "points_on_base":   `rate` points once `prerequisite_fact` is stated; `excluded_fact` stated = 0 (a mutually exclusive partner); unstated = a bounded potential.
    #:   "share_points":     `rate` points when day_numerator_fact / day_denominator_fact meets `min_share` (inclusive unless `share_exclusive`); stated and short = 0; unstated = bounded potential.
    #:   "tiered_share_points": the highest tier whose cumulative numerator group (tier_numerator_groups, summed) meets `min_share` of the denominator; tier_rates are the points (highest first).
    #:   "count_threshold":  `rate` points when at least `min_count` of `criteria_facts` are stated true (a false is never stored, so fewer = a bounded potential, never 0).
    #:   "day_threshold":    `rate` points when the stated day count in day_numerator_fact is at least `min_numerator_days` (stated and short = 0).
    #:   "hod_shortfall":    Nova Scotia Head-of-Department reduction: `rate` points off per position below the stream minimum (see _price_statutory_formula).
    criteria_facts: tuple[str, ...] = ()
    min_count: int | None = None
    min_share: float | None = None
    share_exclusive: bool = False
    tier_numerator_groups: tuple[tuple[str, ...], ...] = ()
    hod_filled_fact: str | None = None
    hod_resident_fact: str | None = None
    stream_i_fact: str | None = None
    stream_ii_fact: str | None = None
    #: NA-RECONCILIATION-19 kinds:
    #:   "rate_on_amount":      `rate` x a stated amount (capped at the host basis); with `day_numerator_fact` + `min_numerator_days` the stated day count must reach the minimum (studio rental of 20 days or more).
    #:   "share_gate":          prices nothing itself; its stated share test (>= `min_share`, or > when `share_exclusive`) gates every rule that names it in `gate_rule_id` (Saskatchewan 51% activity test).
    #:   "compensation_credits": Montana MCA 15-31-1007(3)(b)(i)-(v): the host's base rate does not apply to compensation ('production expenditure' excludes it, 15-31-1003(13)(b)(i)), so the
    #:                          personnel basis is replaced by per-category credits; `compensation_credits` = ((compensation fact, headcount fact, rate, per-person credit cap USD, per-person compensation cap USD), ...).
    #:   "year_gate":           an agency-stated first expenditure year (`min_year`) for a stated year fact; stated earlier = no credit, unstated = a disclosed timing condition.
    gate_rule_id: str | None = None
    personnel_categories: frozenset[str] = frozenset()
    compensation_credits: tuple[tuple[str, str, float, float | None, float | None], ...] = ()
    bound_rate: float | None = None
    min_year: int | None = None


_NY_LABOR_CATEGORIES = frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"})

# Bases require line-specific evidenced USD portions. A whole-program rate
# confirmation cannot stand in for the qualified subset or its predicates.
SUBSET_UPLIFT_RULES = {
    "ca_film_30": (
        EligibleSubsetUpliftRule("outside_la_zone", .05, source_ref="CFC Program 4.0 Guidelines Jan 2026 III.2: applicable-period qualified out-of-zone expenses; prorate mixed-use goods"),
        EligibleSubsetUpliftRule("local_hire_outside_la", .10, eligible_categories=frozenset({"btl_crew_labor", "btl_resident_labor", "payroll_fringes"}), source_ref="CFC Program 4.0 Guidelines Jan 2026 III.3: qualified resident wages, residence AND work outside LA zone; proof required"),
        EligibleSubsetUpliftRule("qualified_vfx", .05, eligible_categories=frozenset({"vfx"}), excluded_fact="ca_film_independent_category", source_ref="CFC Program 4.0 Guidelines Jan 2026 III.1: eligible non-independent/TV category; $10m CA VFX OR 75% worldwide VFX; eligible vendor categories"),
    ),
    "ny_state_film": (
        EligibleSubsetUpliftRule(
            "upstate_labor", .10, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="ny_all_costs_in_listed_counties",
            min_gross_budget_usd=500_000.0,
            source_ref="Tax Law 24(a)(5) (displayed 2025-07-11) and ESD Guidelines April 2025 p.2: +10% of wages, salaries or other compensation constituting qualified "
                       "production costs for services performed and property used in the listed counties, film budget of at least $500,000; includes qualifying above-the-line "
                       "compensation after the ATL limits"),
        EligibleSubsetUpliftRule(
            "upstate_other_costs", .10, excluded_categories=_NY_LABOR_CATEGORIES, whole_base_fact="ny_all_costs_in_listed_counties",
            prerequisite_fact="ny_majority_principal_photography_days_in_listed_counties", min_gross_budget_usd=500_000.0,
            source_ref="Tax Law 24(a)(5) and ESD Guidelines April 2025 p.2: other qualified costs in the listed counties also earn +10% only if the majority of "
                       "principal-photography shooting days were shot there"),
        EligibleSubsetUpliftRule(
            "scoring", .10, eligible_categories=frozenset({"music"}), prerequisite_fact="ny_scoring_five_musicians_in_state",
            source_ref="Tax Law 24(a)(2) (displayed 2025-07-11): qualified costs attributable to scoring incurred within the state earn +10% when the scoring costs "
                       "include payment to a minimum of five musicians; a music account that also holds licensing needs the scoring portion per line"),
        EligibleSubsetUpliftRule(
            "production_plus_10", .10, exclusive_group="production_plus", whole_base_fact="ny_production_plus_10pct_tier",
            prerequisite_fact="ny_production_plus_10pct_tier", potential_requires_prerequisite=True,
            source_ref="Tax Law 24(a)(6) Production Plus program: additional 10% of qualified production costs in New York by application, where the applicant's "
                       "initial applications total at least $100 million; participation is evidenced, never assumed"),
        EligibleSubsetUpliftRule(
            "production_plus_5", .05, exclusive_group="production_plus", whole_base_fact="ny_production_plus_5pct_tier",
            prerequisite_fact="ny_production_plus_5pct_tier", potential_requires_prerequisite=True,
            source_ref="Tax Law 24(a)(6) Production Plus program: additional 5% where the applicant's initial applications total at least $20 million"),
    ),
    "us_ny_post_production_credit": (
        EligibleSubsetUpliftRule(
            "upstate_post_wages", .10, eligible_categories=frozenset({"post_production", "sound", "vfx"}), min_gross_budget_usd=500_000.0,
            source_ref="Tax Law 31(a)(6) (displayed 2025-07-11): +10% of wages or salaries paid to individuals directly employed at a qualified post facility in the "
                       "listed counties, other than writers, directors, composers, producers and performers; facility fees, equipment and vendor charges are not wages, "
                       "so each line needs its evidenced wage portion"),
    ),
    "on_ofttc": (
        EligibleSubsetUpliftRule(
            "first_time_producer", .05, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="on_ofttc_first_time_producer",
            prerequisite_fact="on_ofttc_first_time_producer", potential_requires_prerequisite=True, base_cap_usd=240_000.0,
            source_ref="Ontario Creates OFTTC page: enhanced 40% (35% + 5 points) on the first $240,000 of qualifying labour expenditure for first-time producers"),
        EligibleSubsetUpliftRule(
            "regional_bonus", .10, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="on_ofttc_labour_outside_gta",
            source_ref="Ontario Creates OFTTC page: 10% bonus on all Ontario labour expenditures for productions shot outside the Greater Toronto Area"),
    ),
    "ca_mb_film_video_credit": (
        EligibleSubsetUpliftRule(
            "frequent_filming", .10, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="mb_frequent_filming_third_film_in_two_years",
            prerequisite_fact="mb_frequent_filming_principal_owner_declared",
            source_ref="Manitoba Film & Music TC1 Cost of Salaries Guidelines (June 2024) section I: +10% on the third film shot in Manitoba within a two-year period "
                       "(series: one credit per two hours of airtime), and a declared Principal Owner (at least 50% of the voting shares throughout principal photography)"),
        EligibleSubsetUpliftRule(
            "manitoba_producer", .05, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="mb_resident_producer_screen_credit",
            source_ref="Manitoba Film & Music TC1 guidelines section K: +5% when a Manitoba resident fills the role of Producer, Co-Producer or Executive Producer and receives a screen credit as such"),
        EligibleSubsetUpliftRule(
            "rural_northern", .05, eligible_categories=_NY_LABOR_CATEGORIES, whole_base_fact="mb_rural_majority_days_35km",
            prerequisite_fact="mb_rural_permanent_establishment_35km",
            source_ref="Manitoba Film & Music TC1 guidelines section J: +5% when the applicant has a permanent establishment in Manitoba at least 35 km from Winnipeg "
                       "AND at least 50% of the Manitoba shooting days (7.5 hours of principal photography = one day) took place at least 35 km from Winnipeg's centre"),
    ),
    "ca_qc_pstc": (
        EligibleSubsetUpliftRule(
            "vfx_labour_enhancement", .16, eligible_categories=frozenset({"vfx"}),
            source_ref="SODEC fact sheet (2024) and Revenu Quebec: additional 16% on qualified computer-animation/VFX LABOUR costs; only 65% of a VFX/animation "
                       "service contract is recognized, so each account needs its evidenced qualifying labour portion"),
    ),
    # NA-RECONCILIATION-16: the British Columbia shooting-day credits, on the exact statutory bases (Income Tax Act (BC), read 2026-10-14 on bclaws.gov.bc.ca). They replace the earlier
    # "labour in the regional zone" boolean, which priced a DOLLAR proxy (labour located in the zone) where the Act takes the DAY ratio. Days are stated producer facts and are never derived from dollars.
    "ca_bc_pstc": (
        EligibleSubsetUpliftRule(
            "regional", .06, kind="day_ratio", day_numerator_fact=BC_DAYS_OUTSIDE_VANCOUVER_FACT, day_denominator_fact=BC_DAYS_IN_BC_FACT,
            min_numerator_days=5, min_share_exclusive=0.5, series_needs_episode_facts=True, excluded_production_types=frozenset({"animation"}),
            source_ref="Income Tax Act (BC) s.82.2(1)-(2): 6% x AQLE x RD/TD; requires the s.82.1 credit, principal photography outside the designated Vancouver area for at least 5 days and "
                       "during more than 50% of the days in British Columbia"),
        EligibleSubsetUpliftRule(
            "distant_location", .06, kind="day_ratio", day_numerator_fact=BC_DAYS_DISTANT_FACT, day_denominator_fact=BC_DAYS_IN_BC_FACT,
            min_numerator_days=1, companion_uplift_id="regional", companion_bounds_numerator=True, series_needs_episode_facts=True, excluded_production_types=frozenset({"animation"}),
            source_ref="Income Tax Act (BC) s.82.21(1)-(2): 6% x AQLE x DLD/TD; requires the s.82.1 and s.82.2 credits and at least one day of principal photography in a distant location"),
    ),
    "ca_bc_film_tv_tax_credit": (
        EligibleSubsetUpliftRule(
            "regional", .125, kind="day_ratio", day_numerator_fact=BC_DAYS_OUTSIDE_VANCOUVER_FACT, day_denominator_fact=BC_DAYS_IN_BC_FACT,
            min_numerator_days=5, min_share_exclusive=0.5, series_needs_episode_facts=True, excluded_production_types=frozenset({"animation"}),
            source_ref="Income Tax Act (BC) s.81.1(1)-(2): 12.5% x QLE x RD/TD; requires the s.80 credit, principal photography outside the designated Vancouver area for at least 5 days and "
                       "during more than 50% of the days in British Columbia"),
        EligibleSubsetUpliftRule(
            "distant_location", .06, kind="day_ratio", day_numerator_fact=BC_DAYS_DISTANT_FACT, day_denominator_fact=BC_DAYS_IN_BC_FACT,
            min_numerator_days=1, companion_uplift_id="regional", companion_bounds_numerator=True, series_needs_episode_facts=True, excluded_production_types=frozenset({"animation"}),
            source_ref="Income Tax Act (BC) s.81.11(1)-(2): 6% x QLE x DLD/TD; requires the s.80 and s.81.1 credits and at least one day of principal photography in a distant location"),
        EligibleSubsetUpliftRule(
            "film_training", .03, kind="training", amount_fact=BC_TRAINING_PAYMENTS_FACT, assistance_facts=(BC_TRAINING_ASSISTANCE_FACT,), net_share=0.30,
            prerequisite_fact="ca_bc_film_training_program_approved_confirmed", potential_requires_prerequisite=True,
            source_ref="Income Tax Act (BC) s.82(1)-(3): the lesser of 3% of QLE and 30% of the amount by which payments attributable to training exceed assistance; requires the s.80 credit, BC-based "
                       "trainees in an approved training program and an eligibility certificate"),
        EligibleSubsetUpliftRule(
            "scriptwriting", .35, kind="scriptwriting", amount_fact=BC_SCRIPTWRITING_FACT, assistance_facts=(BC_SCRIPTWRITING_ASSISTANCE_FACT, BC_SCRIPTWRITING_REIMBURSEMENT_FACT),
            prerequisite_fact="ca_bc_scriptwriting_application_confirmed", potential_requires_prerequisite=True,
            source_ref="Income Tax Act (BC) s.80.1(2)-(3): 35% x (SE - (TA + RE)) on the eligible BC scriptwriting expenditure; requires principal photography to begin in the taxation year, the s.80 "
                       "credit and an eligibility certificate"),
    ),
    # NA-RECONCILIATION-17: Nova Scotia Film & Television Production Incentive Fund Guidelines (April 1, 2024; cch.novascotia.ca, read 2026-10-14), s.6.1/6.2 'Eligible Incentives', both streams: percentage
    # points of additional funding on ALL Eligible Nova Scotia Costs. Location Incentive: +2 points when more than 50% of the principal photography is in a rural/non-metropolitan area in Nova Scotia.
    # Distant Location Incentive: up to 10 points, only for an applicant first eligible for the Location Incentive, tiered by the most direct driving distance from Halifax City Hall: 7% for locations more
    # than 100 km away and 10% for locations more than 150 km away, EACH prorated on the days of principal photography in the distant location to the total days of principal photography. Reading kept
    # labelled: the tiers are exclusive bands (days at 100-150 km earn 7%, days over 150 km earn 10%), because the guideline caps the incentive at 'up to 10%', which the cumulative reading (17%) contradicts.
    "ca_ns_production_incentive_fund": (
        EligibleSubsetUpliftRule(
            "location_rural", .02, whole_base_fact=NS_RURAL_FACT,
            source_ref="NSFPIF Guidelines (April 1, 2024) s.6.1/6.2: Location Incentive, 2 percentage points when more than 50% of the principal photography is in a rural/non-metropolitan area in Nova Scotia"),
        EligibleSubsetUpliftRule(
            "distant_location", .10, kind="tiered_day_ratio", tier_rates=(0.07, 0.10), tier_numerator_facts=(NS_DAYS_ZONE_A_FACT, NS_DAYS_ZONE_B_FACT), day_denominator_fact=NS_DAYS_TOTAL_FACT,
            prerequisite_fact=NS_RURAL_FACT,
            source_ref="NSFPIF Guidelines (April 1, 2024) s.6.1/6.2: Distant Location Incentive, up to 10 points, 7% (more than 100 km) or 10% (more than 150 km from Halifax City Hall) prorated on distant "
                       "days to total days of principal photography; the applicant must first be eligible for the Location Incentive"),
        # NA-RECONCILIATION-18: the remaining Nova Scotia additions and the Head-of-Department reduction (same guideline, s.5, 6, 7), all on ALL Eligible Nova Scotia Costs.
        EligibleSubsetUpliftRule(
            "stream_i_base", .01, kind="points_on_base", prerequisite_fact="ca_ns_stream_i_ownership_control_confirmed", excluded_fact="ca_ns_stream_ii_confirmed",
            source_ref="NSFPIF Guidelines s.6.1/6.2: Stream I base 26% (Nova Scotian ownership and control of production, 50% or more of each of corporate ownership and control, rights, financial and creative "
                       "control and profit participation, s.2(g)) against Stream II 25%; the Stream II base is the guaranteed floor and Stream I is the +1 point"),
        EligibleSubsetUpliftRule(
            "shooting_length", .01, kind="day_threshold", day_numerator_fact="ca_ns_principal_photography_days_in_ns", min_numerator_days=31,
            source_ref="NSFPIF Guidelines s.6.1/6.2: Shooting Length Incentive, 1 percentage point for shoots of MORE THAN 30 days of principal photography in Nova Scotia (31 days or more)"),
        EligibleSubsetUpliftRule(
            "content_performers", .015, kind="share_points", day_numerator_fact="ca_ns_principal_performers_ns_residents", day_denominator_fact="ca_ns_principal_performers_total", min_share=0.6,
            source_ref="NSFPIF Guidelines s.7(a): +1.5 points when no less than 60 per cent of all Principal Performers, actors, stunt performers and stunt actors are Nova Scotia Residents (background performers excluded)"),
        EligibleSubsetUpliftRule(
            "content_three_of_seven", .015, kind="count_threshold", min_count=3,
            criteria_facts=("ca_ns_content_majority_copyright_ns_ownership_confirmed", "ca_ns_content_two_new_trainees_confirmed", "ca_ns_content_post_75pct_in_ns_confirmed",
                            "ca_ns_content_ns_resident_producer_confirmed", "ca_ns_content_ns_spend_75pct_confirmed", "ca_ns_content_ns_writer_confirmed", "ca_ns_content_ns_director_confirmed"),
            source_ref="NSFPIF Guidelines s.7(b): a further +1.5 points for productions meeting at least three of the seven Nova Scotia-content requirements (majority copyright with Nova Scotian ownership and "
                       "control; two trainees with no prior paid experience; 75% of post-production in Nova Scotia; Nova Scotia resident producer of two years; Nova Scotia spend 75% of total cost and over CAD 25,000; "
                       "principal writer a Nova Scotia resident; principal director a Nova Scotia resident)"),
        EligibleSubsetUpliftRule(
            "head_of_department_shortfall", .005, kind="hod_shortfall", hod_filled_fact="ca_ns_hod_positions_filled", hod_resident_fact="ca_ns_hod_positions_held_by_ns_residents",
            stream_i_fact="ca_ns_stream_i_ownership_control_confirmed", stream_ii_fact="ca_ns_stream_ii_confirmed",
            source_ref="NSFPIF Guidelines s.6.1/6.2: the base is reduced by 0.5 (read as percentage points) for each Head of Department position below the stream minimum - Stream I: 50% of filled positions rounded "
                       "up; Stream II: half of the filled positions rounded up where eight or fewer are filled, four where nine or more are filled; the Fund recognises sixteen positions (s.5(a))"),
    ),
    # NA-RECONCILIATION-18: New Brunswick LIFT 2026/2027 Stream 2 stackable bonuses (gnb.ca lift-program-guidelines.pdf, read 2026-10-14) on Total NB Spend, to a combined 35%.
    "ca_nb_film_tax_credit": (
        EligibleSubsetUpliftRule(
            "bonus_heads_of_department_lead_talent", .03, kind="points_on_base", prerequisite_fact="ca_nb_bonus_hod_lead_talent_30pct_confirmed",
            source_ref="LIFT 2026/2027 Guidelines, Stackable Bonuses: +3% when 30%+ of Head of Department positions or Lead Talent are New Brunswick residents (no deemed); read as one stated fact because the "
                       "wording does not say whether the two groups are tested together or separately"),
        EligibleSubsetUpliftRule(
            "bonus_rural_remote", .04, kind="tiered_share_points", tier_rates=(0.04, 0.03), day_denominator_fact="ca_nb_principal_photography_days_total",
            tier_numerator_groups=(("ca_nb_days_remote_151km_plus",), ("ca_nb_days_rural_30_to_150km", "ca_nb_days_remote_151km_plus")), min_share=0.5,
            source_ref="LIFT 2026/2027 Guidelines, Stackable Bonuses: +3% (30-150 km) or +4% (151 km+ from Fredericton, Moncton or Saint John City Hall) when 50%+ of principal photography is in rural NB "
                       "communities; read as the highest band that alone holds 50%+ of the days (4%), else rural and remote together (3%)"),
        EligibleSubsetUpliftRule(
            "bonus_nb_made", .03, kind="count_threshold", min_count=2,
            criteria_facts=("ca_nb_made_spend_50pct_confirmed", "ca_nb_made_copyright_50pct_confirmed", "ca_nb_made_writer_nb_resident_confirmed", "ca_nb_made_director_nb_resident_confirmed",
                            "ca_nb_made_post_20pct_in_nb_confirmed", "ca_nb_made_photography_days_25pct_in_nb_confirmed"),
            source_ref="LIFT 2026/2027 Guidelines, Stackable Bonuses: +3% 'NB Made' when at least two of six content thresholds are met (NB spend 50% of cost; NB copyright 50%; principal writer an NB resident; "
                       "principal director an NB resident; 20% of post-production in NB; 25% of principal-photography days in NB)"),
    ),
    # Missouri RSMo 135.750 subsection 3 (revisor.mo.gov, read 2026-10-14): the 20% base is guaranteed; each stated project fact adds its statutory points. 3(6) is 10% of the 20% base = 2 points.
    "us_mo_motion_media_production_tax_credit": (
        EligibleSubsetUpliftRule("filmed_50pct_in_missouri", .05, kind="points_on_base", prerequisite_fact="mo_filmed_50pct_in_missouri_confirmed",
                                 source_ref="RSMo 135.750 subsection 3(2): +5 points when at least fifty percent of the project is filmed in Missouri"),
        EligibleSubsetUpliftRule("rural_or_blighted_15pct", .05, kind="points_on_base", prerequisite_fact="mo_rural_or_blighted_15pct_confirmed",
                                 source_ref="RSMo 135.750 subsection 3(3): +5 points when at least fifteen percent of the Missouri filming takes place in a rural or blighted area"),
        EligibleSubsetUpliftRule("three_departments_resident_hires", .05, kind="points_on_base", prerequisite_fact="mo_three_departments_missouri_hires_confirmed",
                                 source_ref="RSMo 135.750 subsection 3(4): +5 points when at least three departments hire a Missouri resident ready to advance or learn a new skillset"),
        EligibleSubsetUpliftRule("script_markets_missouri", .05, kind="points_on_base", prerequisite_fact="mo_script_markets_missouri_confirmed",
                                 source_ref="RSMo 135.750 subsection 3(5): +5 points when the script positively markets a Missouri city, region, the state or a tourist attraction (five cleared photographs)"),
        EligibleSubsetUpliftRule("county_class_two_three_four", .02, kind="points_on_base", prerequisite_fact="mo_second_third_fourth_class_county_confirmed",
                                 source_ref="RSMo 135.750 subsection 3(6): the credit authorized under subdivision (1) (the 20% base) is increased by ten percent for a project in a second-, third- or fourth-class county = 2 points"),
    ),
    # Montana MEDIA credit, MCA 15-31-1007(3) and 15-31-1003 (archive.legmt.gov, MCA 2025, read 2026-10-14). 'Production expenditure' EXCLUDES compensation (15-31-1003(13)(b)(i)), so the 20% base applies to
    # non-compensation Montana spend only; compensation earns its own per-category credits, and every addition is limited to a 35% aggregate of base investment (SUBSET_COMBINED_RATE_CAPS).
    "us_mt_media_act_tax_credit": (
        EligibleSubsetUpliftRule(
            "compensation_credits", .20, kind="compensation_credits", bound_rate=0.30,
            personnel_categories=frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"}),
            compensation_credits=(
                ("us_mt_resident_crew_compensation_usd", "us_mt_resident_crew_persons", 0.25, 150_000.0, None),            # (3)(b)(i): 25%, not above a USD 150,000 credit per person
                ("us_mt_nonresident_crew_compensation_usd", "us_mt_nonresident_crew_persons", 0.15, 150_000.0, None),     # (3)(b)(ii): 15% where Montana tax is withheld, USD 150,000 per person
                ("us_mt_talent_compensation_usd", "us_mt_talent_persons", 0.20, None, 7_500_000.0),                       # (3)(b)(iii): 20% of the first USD 7.5 million per actor, director, producer or writer
                ("us_mt_student_compensation_usd", "us_mt_student_persons", 0.30, 50_000.0, None),                        # (3)(b)(iv): 30% for an enrolled student, USD 50,000 per student
                ("us_mt_veteran_tribal_compensation_usd", "us_mt_veteran_tribal_persons", 0.30, 150_000.0, None),         # (3)(b)(v): 30% for a resident veteran or enrolled tribal member, USD 150,000 per person
            ),
            source_ref="MCA 15-31-1007(3)(b)(i)-(v) and 15-31-1003(13)(b)(i): 'production expenditure' does not include compensation, which earns 25% (resident crew), 15% (non-resident crew with Montana tax "
                       "withheld), 20% of the first USD 7.5 million (actors, directors, producers, writers with Montana tax withheld), 30% (students, USD 50,000 each) or 30% (resident veterans and tribal "
                       "members, USD 150,000 each) of compensation; a person counts in one category only (students and veterans exclude the others)"),
        EligibleSubsetUpliftRule(
            "college_payments", .10, kind="rate_on_amount", amount_fact="us_mt_college_campus_payments_usd",
            source_ref="MCA 15-31-1007(3)(b)(vi): an additional 10% of payments to a Montana college or university for stage rentals, equipment rentals or location fees for filming on campus"),
        EligibleSubsetUpliftRule(
            "studio_rental", .10, kind="rate_on_amount", amount_fact="us_mt_studio_rental_expenditure_usd", day_numerator_fact="us_mt_studio_rental_days", min_numerator_days=20,
            source_ref="MCA 15-31-1007(3)(b)(vii): an additional 10% of all in-studio facility and equipment rental expenditures incurred in Montana for a production that rents a studio for 20 days or more"),
        EligibleSubsetUpliftRule(
            "underserved_area", .05, kind="rate_on_amount", amount_fact="us_mt_underserved_area_expenditure_usd",
            source_ref="MCA 15-31-1007(3)(b)(viii): an additional 5% for production expenditures made in an underserved area (a county where 14% or more of people are in poverty, 15-31-1003)"),
        EligibleSubsetUpliftRule(
            "montana_screen_credit", .05, kind="points_on_base", prerequisite_fact="us_mt_screen_credit_furnished_confirmed",
            source_ref="MCA 15-31-1007(3)(b)(ix): an additional 5% of the base investment when the state-certified production includes a Montana screen credit furnished by the state (15-31-1004(7))"),
        EligibleSubsetUpliftRule(
            "first_credit_year", .0, kind="year_gate", day_numerator_fact="us_mt_media_expenditure_year", min_year=2031,
            source_ref="Montana Department of Revenue MEDIA credit page (read 2026-10-14): all of the USD 12 million annual limit goes to approved 2024 productions through 2030 and part of 2031, so 'companies will be "
                       "eligible to start applying for credit for expenses incurred and compensation paid in 2031'; 'no credit will be approved' for productions that filmed or were approved after December 31, 2024 "
                       "(an agency position implementing MCA 15-31-1010(2)(b), distinct from Commerce's certification pause, which states no end date)"),
    ),
    # Saskatchewan Feature Film & Television Production Grant Guidelines (approved April 1, 2026; Bonuses added July 20, 2026; creativesask.ca, read 2026-10-14). Zero guaranteed floor: a discretionary grant.
    "ca_sk_creative_saskatchewan_grant": (
        EligibleSubsetUpliftRule(
            "activity_test", .0, kind="share_gate", day_numerator_fact="ca_sk_principal_photography_days_in_sk", day_denominator_fact="ca_sk_principal_photography_days_total", min_share=0.51,
            source_ref="Creative Saskatchewan FFTV Guidelines, Bonuses, General Bonus Eligibility: live action or scripted projects need at least 51% of principal photography days completed in Saskatchewan (documentary: "
                       "51% of days or of post-production spend; animation: 51% of principal animation days - stated through the same day counts)"),
        EligibleSubsetUpliftRule(
            "saskatchewan_stream", .05, kind="points_on_base", prerequisite_fact="ca_sk_saskatchewan_stream_confirmed", excluded_fact="ca_sk_service_production_stream_confirmed",
            source_ref="Creative Saskatchewan FFTV Guidelines: Saskatchewan Stream 30% of eligible Saskatchewan expenditures against the Service Production Stream 25% (applicant incorporated in Saskatchewan with its head office there "
                       "and substantial ownership control by Saskatchewan residents; copyright share proportional to funding)"),
        EligibleSubsetUpliftRule(
            "rural_bonus", .05, kind="share_points", day_numerator_fact="ca_sk_days_50km_outside_regina_saskatoon", day_denominator_fact="ca_sk_principal_photography_days_total", min_share=0.5, share_exclusive=True,
            gate_rule_id="activity_test",
            source_ref="Creative Saskatchewan FFTV Guidelines, Rural Bonus +5%: the majority (more than half) of principal photography days occur at least 50 km outside Regina or Saskatoon, measured from the centre-most point"),
        EligibleSubsetUpliftRule(
            "post_production_bonus", .05, kind="points_on_base", prerequisite_fact="ca_sk_majority_post_spend_in_sk_confirmed", gate_rule_id="activity_test",
            source_ref="Creative Saskatchewan FFTV Guidelines, Saskatchewan Post Production Bonus +5%: the majority of the post-production spend is incurred in Saskatchewan; it applies to ALL eligible expenses, not only post"),
        EligibleSubsetUpliftRule(
            "production_volume_bonus", .10, kind="points_on_base", prerequisite_fact="ca_sk_volume_threshold_confirmed", gate_rule_id="activity_test",
            source_ref="Creative Saskatchewan FFTV Guidelines, Saskatchewan Production Volume Bonus +10%: a producer significantly involved in at least two eligible completed FFTV projects with combined eligible "
                       "Saskatchewan spend of at least CAD 1.5 million in the current and three prior fiscal years, the projects meeting the activity test"),
    ),
    # Arkansas Ark. Code 15-4-2005 (Act 517 of 2023): the add-ons (+10 below-the-line Arkansas resident / veteran payroll and veteran-owned small business spend, +5 Tier 3/4 county, +5 multi-project) are
    # capped at 30% of the expenditure in total, so on any expenditure they can add at most 5 points to the 25% base; per-line evidenced portions refine the bound (uplift_basis).
    "us_ar_digital_motion_picture_incentive": (
        EligibleSubsetUpliftRule(
            "addons_to_the_30pct_cap", .05,
            source_ref="Ark. Code 15-4-2005(c), (d), (f): add-ons of 10 / 5 / 5 points are limited so that the total claimed on any expenditure does not exceed 30%, i.e. at most 5 points above the 25% base on an "
                       "expenditure that qualifies for any add-on"),
    ),
    # Alabama (revenue.alabama.gov/tax-incentives/film-rebate, read 2026-10-12): the rebate is 25% of certain production expenditures incurred in Alabama
    # PLUS 35% of the payroll paid to Alabama residents (a 10-point addition on resident payroll); a small-budget production (total expenditures of at
    # least $100,000 and at most $499,999) receives 45% of resident payroll instead (a 20-point addition). Payroll to non-residents earns the 25% only.
    "us_al_film_incentive": (
        EligibleSubsetUpliftRule(
            "resident_payroll_35", .10, eligible_categories=frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor"}),
            exclusive_group="al_resident_payroll", whole_base_fact="al_all_payroll_to_alabama_residents",
            source_ref="revenue.alabama.gov film rebate: 25 percent of certain production expenditures plus 35 percent of the payroll paid to Alabama residents"),
        EligibleSubsetUpliftRule(
            "small_budget_resident_payroll_45", .20, eligible_categories=frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor"}),
            exclusive_group="al_resident_payroll", whole_base_fact="al_all_payroll_to_alabama_residents",
            min_gross_budget_usd=100_000.0, max_gross_budget_usd=499_999.0,
            source_ref="revenue.alabama.gov film rebate: small budget qualified production companies receive 45% of the payroll paid to Alabama residents when "
                       "total production expenditures are at least $100,000 and not more than $499,999"),
    ),
    "us_nm_film_credit": (
        EligibleSubsetUpliftRule("rural_location", .10, excluded_categories=frozenset({"btl_nonresident_labor"}), source_ref="TRD FYI-370 July 2025 p4: qualifying rural-location goods/services; rental prorating; excludes nonresident BTL"),
        EligibleSubsetUpliftRule("qualified_facility", .05, exclusive_group="tv_or_facility", source_ref="TRD FYI-370 July 2025 p4: expenses incurred IN qualified facility, not purchases merely brought there"),
        EligibleSubsetUpliftRule("qualified_tv", .05, exclusive_group="tv_or_facility", eligible_production_types=frozenset({"tv_series", "television_series", "tv_pilot", "television_pilot"}), source_ref="TRD FYI-370 July 2025 p4: qualifying pilot or ordered six-episode series; $50k NM per episode; cannot stack facility 5%"),
    ),
}


#: Combined-rate ceilings stated by a program for base plus stackable additions (NA-RECONCILIATION-18). Applied to the host credit's own basis after every addition.
SUBSET_COMBINED_RATE_CAPS: dict[str, tuple[float, str]] = {
    "ca_nb_film_tax_credit": (0.35, "LIFT 2026/2027 Guidelines, Stream 2: a Base Grant of up to 25% plus Stackable Bonuses 'to a combined total of 35% of Total NB Spend'"),
    "us_ar_digital_motion_picture_incentive": (0.30, "Ark. Code 15-4-2005(f): 'The maximum total tax incentives that shall be claimed for an expenditure under this section is thirty percent (30%) of the expenditure'"),
    "us_mo_motion_media_production_tax_credit": (0.42, "RSMo 135.750 subsection 3: 20% + four 5-point increases + 10% of the 20% base credit for a second-, third- or fourth-class county = 42%"),
    "us_mt_media_act_tax_credit": (0.35, "MCA 15-31-1007(3)(a): the credit 'may not in the aggregate exceed 35% of the production company's base investment in the tax year' (base investment = production expenditures and compensation incurred in Montana, 15-31-1003)"),
    "ca_sk_creative_saskatchewan_grant": (0.40, "Creative Saskatchewan FFTV Guidelines (approved April 1, 2026), Bonuses: total funding including bonuses is capped at 40% (Saskatchewan Stream) and 35% (Service Production Stream) of eligible Saskatchewan expenditures; the 35% Service cap applies once that stream is stated"),
}
#: A combined ceiling that is lower once a stream / scenario fact is stated: slug -> (stated fact, lower ceiling).
SUBSET_COMBINED_RATE_CAP_OVERRIDES: dict[str, tuple[str, float]] = {
    "ca_sk_creative_saskatchewan_grant": ("ca_sk_service_production_stream_confirmed", 0.35),
}


#: Per-individual incentive ceilings stated by a program in its native currency (NA-RECONCILIATION-19): the incentive attributable to one individual's compensation may not exceed the cap, so an identified
#: payee's compensation above cap / rate is not eligible. (slug -> (cap amount, currency, categories, source)).
SUBSET_INDIVIDUAL_INCENTIVE_CAPS: dict[str, tuple[float, str, frozenset[str], str]] = {
    "ca_ns_production_incentive_fund": (
        150_000.0, "CAD", frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"}),
        "NSFPIF Guidelines (April 1, 2024) s.3.2(d): no individual may directly or indirectly receive pay budgeted or paid from the Fund greater than $150,000 per project; the cap is the incentive that results when "
        "the eligible incentive percentage is applied to fee payments to an individual (a 25% company: CAD 600,000 of eligible compensation)"),
}

#: Eligible deemed spend added to the host's base (NA-RECONCILIATION-19): slug -> (stated amount fact, maximum share of eligible in-province spend, source).
SUBSET_DEEMED_SPEND: dict[str, tuple[str, float, str]] = {
    "ca_nb_film_tax_credit": (
        "ca_nb_eligible_deemed_spend_usd", 0.15,
        "LIFT 2026/2027 Guidelines: Total NB Spend 'may include up to 15% Eligible Deemed Spend' (costs planned outside New Brunswick, not above-the-line, from the Deemed Spend Worksheet; 'EDS can represent up to "
        "15% of Eligible NB Spend'); read as 15% of the in-province eligible spend, the larger of the two possible readings, so it only ever bounds the potential"),
}

#: Stated amounts removed from the host's base before any point applies (Nova Scotia): slug -> ((stated amount fact, source), ...).
SUBSET_BASE_DEDUCTIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "ca_ns_production_incentive_fund": (
        ("ca_ns_ineligible_supplier_spend_usd",
         "NSFPIF Guidelines s.4(a), (e): Eligible Nova Scotia Costs are goods or services purchased from a Nova Scotia-based supplier with a permanent physical establishment in Nova Scotia and supplied, receipted, consumed "
         "or performed there; fees subcontracted by Nova Scotia companies to out-of-province individuals and organizations, in-kind contributions and capital items are not eligible (s.4(d), (e))"),
        ("ca_ns_equity_tax_credit_financing_usd",
         "NSFPIF Guidelines s.3.2(b): the financing/investment received from a corporation registered under the Equity Tax Credit Act (Nova Scotia) that made a specified issue after June 30, 2015 is deducted from Eligible Nova Scotia Costs"),
    ),
}

#: A smaller-budget stream of the same program, selected by the production's total budget in the program's currency (NA-RECONCILIATION-19).
SUBSET_ALTERNATE_STREAMS: dict[str, dict] = {
    "ca_nb_film_tax_credit": {
        "currency": "CAD", "budget_below_native": 400_000.0, "rate": 0.30, "grant_cap_native": 100_000.0, "min_spend_share": 0.25,
        "source": "LIFT 2026/2027 Guidelines, Stream 1 Micro Production: a grant of up to 30% of Total NB Spend to a maximum of CAD 100,000 for Total Budgets under CAD 400,000; NB Spend at least 25% of the total "
                  "budget; no stackable bonuses (Stream 2 Major Production covers budgets over CAD 400,000: base up to 25% plus bonuses, NB Spend at least 20%)",
        "major_min_spend_share": 0.20,
    },
}


def get_subset_uplift_rules(program_slug: str) -> tuple[EligibleSubsetUpliftRule, ...]:
    return SUBSET_UPLIFT_RULES.get(_canonical_program_slug(program_slug), ())
