"""
little_utopia_state.py

The single canonical production state the CineGlobe API serves: THE
LITTLE UTOPIA (Mauritius). The register is built from the ACTUAL parsed
production budget (app.data.little_utopia_real_budget ->
qualification_model.build_little_utopia_real_register()) — not the
sanitized fixture (tests/fixtures/little_utopia_sanitized.py ->
build_little_utopia_qualification_register()), which remains a distinct,
still-tested capability but is no longer the primary served data.

This module introduces NO new production, NO fabricated people, NO
invented screenplay. Every input here is either:
  - the real, parsed Little Utopia budget/facts/grey-areas (see
    app.data.little_utopia_real_budget's own docstring for exactly how
    to reproduce the parse from the source PDF),
  - a production fact the user has explicitly supplied through the
    facts API (apply_fact_answers), or
  - honestly absent (no screenplay on file, no cast/crew intake on
    file) — Package Intelligence's own "unknown stays unknown"
    discipline handles this correctly; it is not a bug or a stub.

The flow (Engine Integration Phase 1, with the mock-contamination
regression fix restoring the original primary/research separation):

    production facts (defaults + user answers)
      -> derived qualification register (qualification_derivation)
      -> ONE opportunity-discovery + composition + recommendation +
         scenario-ranking pass over the RAW statutory register
      -> API (primary production surfaces)

    SEPARATELY, research-only:
      -> Legal Engine acquisition/commit cycle over ITS OWN copy of the
         grey areas (MockConnector — self-labeled mock retrieval)
      -> legal_* fields consumed by /legal only

MockConnector output is research display, not evidence: it must never
reclassify an account on the primary register, add to served QPE, or be
classified as authoritative. A real (non-mock) authoritative resolution
would enter the primary pipeline only through the statutory knowledge
base (program_spend_rules) after provenance validation — not through
this demo cycle.

The only non-canonical step this module performs is running one Legal
Engine acquisition cycle through MockConnector (the sole connector
implementation this phase ships — see legal_authority_acquisition.py's
own docstring) so the Evidence Graph / Authority Score / Legal Engine
loop has real content to display. Every retrieved excerpt is
self-labeled "MOCK CONNECTOR — no live retrieval performed" by the
connector itself, and the API surfaces that label rather than hiding it.

State is built once per fact-state (module-level cache, cleared whenever
a fact answer changes) since every input is static between answers and
every engine call is a pure function over that input.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from functools import lru_cache

from app.calculators import jurisdiction_comparison as jc
from app.calculators.evidence_graph import AuthorityTier
from app.calculators.jurisdiction_graph import JurisdictionGraph, build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import ConnectorClass, MockConnector
from app.calculators.legal_engine import AcquisitionCycleResult, CommitResult, LegalEngine, RerunResult
from app.calculators.opportunity_discovery import OpportunityCollection, discover_all_opportunities
from app.calculators.production_package_intelligence import (
    ProductionPackage,
    build_production_package,
    production_package_to_cultural_test_inputs,
    production_package_to_relevant_cultural_test_slugs,
    production_package_to_role_known_codes,
)
from app.calculators.production_recommendation_engine import RecommendationSet, generate_production_recommendations
from app.calculators.production_structure_composer import CompositionResult, compose_production_structures
from app.calculators.qualification_derivation import ProductionFacts
from app.data.program_rate_rules import RateResolution, resolve_program_rate
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationState,
    build_little_utopia_real_evidence_graph,
    build_little_utopia_real_grey_areas,
    build_little_utopia_real_register,
)
from app.data.little_utopia_people import build_little_utopia_people
from app.data.little_utopia_real_budget import (
    AUTHORITATIVE_GROSS_BUDGET_USD,
    LEAF_ACCOUNT_SUM_USD,
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
    RECONCILIATION_NOTE,
    RECONCILIATION_VARIANCE_USD,
    SOURCE_PDF_FILENAME,
)
from app.ingestion.budget_parser import BudgetParseResult, ParsedLineItem

PRODUCTION_ID = "LITTLE-UTOPIA"
PRODUCTION_NAME = "The Little Utopia"
JURISDICTION_CODE = "MU"
# The modeled incentive rate. NOT taken from the production budget (whose
# own 'EDB Rebate at 35%' line is ignored per the permanent rate-authority
# rules — see app.data.program_rate_rules): 0.40 is the ceiling of the
# EDB Film Rebate Scheme's 'up to 40%' feature-film band (min QPE USD 1M,
# satisfied). _build_state() re-resolves this via resolve_program_rate()
# against the derived QPE and records the full RateResolution (basis,
# condition evaluations, floor rate, budget-rate conflict report) on the
# state; a mismatch between this constant and the resolver is surfaced as
# a warning rather than silently absorbed.
MU_RATE = 0.40
MU_PRODUCTION_TYPE = "feature_film"
# The production's controlling gross budget: the source PDF's own stated
# Grand Total (AUTHORITATIVE_GROSS_BUDGET_USD), not the sum of the 44
# parsed leaf accounts (LEAF_ACCOUNT_SUM_USD) — the two differ by
# RECONCILIATION_VARIANCE_USD ($2.00), an accepted source-document
# rounding variance (see app.data.little_utopia_real_budget's docstring
# for the full diagnosis). Using the authoritative figure here means
# build_risk_cases()'s own existing reconciliation-warning mechanism
# surfaces the $2 gap on every computed case rather than it being hidden.
MU_GROSS_BUDGET_USD = AUTHORITATIVE_GROSS_BUDGET_USD
AS_OF_DATE = "2026-07-10"


# ── Production facts (Seam B: Question Engine answers are engine inputs) ────
#
# Each answerable fact maps to (a) a ProductionFacts field consumed by
# qualification derivation or structure composition, and (b) the Question
# Engine missing-input it answers — so an answered question stops being
# asked AND changes the engines' inputs. Facts not answered stay at the
# production's real current defaults; nothing is fabricated.

ANSWERABLE_FACTS: dict[str, dict] = {
    "payroll_routing_localized": {
        "type": bool,
        "answers_question": "MISSING-PAYROLL-STRUCTURE",
        "description": (
            "Is cast/crew payroll routed through a local employer-of-record / "
            "production SPV in the baseline jurisdiction? true = local routing "
            "plan in place; false = current offshore routing stands."
        ),
    },
    "post_work_in_jurisdiction": {
        "type": bool,
        "answers_question": None,
        "description": (
            "Will post-production (edit/grade/sound/music/VFX/deliverables) be "
            "performed in the baseline jurisdiction? Overrides the current "
            "known post location for the post spend categories."
        ),
    },
    "treaty_partner_code": {
        "type": str,
        "answers_question": "MISSING-TREATY-PARTNER",
        "description": (
            "Elected co-production treaty partner country (ISO alpha-2). Adds "
            "that jurisdiction set to structure composition."
        ),
    },
    "component_route_post": {
        "type": str,
        "answers_question": None,
        "description": (
            "Producer election routing the movable post/VFX/music components "
            "to a jurisdiction (ISO alpha-2; must be an EXECUTABLE "
            "jurisdiction or the baseline). Drives the account->jurisdiction "
            "allocation model (production_allocation) and the allocated-"
            "structure pricing served on /structures.allocated_structures."
        ),
    },
}

_fact_answers: dict[str, object] = {}


def apply_fact_answers(answers: dict[str, object]) -> None:
    """Record user-supplied production facts and invalidate the cached
    state so every engine recomputes from them. A value of None clears a
    previously-given answer (the fact returns to 'unknown/default')."""
    for key, value in answers.items():
        spec = ANSWERABLE_FACTS.get(key)
        if spec is None:
            raise ValueError(
                f"'{key}' is not an answerable production fact. "
                f"Answerable: {sorted(ANSWERABLE_FACTS)}."
            )
        if value is None:
            _fact_answers.pop(key, None)
            continue
        if not isinstance(value, spec["type"]):
            raise ValueError(
                f"Fact '{key}' expects {spec['type'].__name__}, got {type(value).__name__}."
            )
        if key == "treaty_partner_code":
            code = str(value).upper()
            if code == JURISDICTION_CODE or code not in jc.ALL_PROFILES:
                raise ValueError(
                    f"'{code}' is not a modeled partner jurisdiction "
                    f"(known: {sorted(c for c in jc.ALL_PROFILES if c != JURISDICTION_CODE)})."
                )
            value = code
        if key == "component_route_post":
            from app.data.program_rate_rules import get_rate_rules
            from app.data.program_spend_rules import get_program_doctrine
            code = str(value).upper()
            profile = jc.ALL_PROFILES.get(code)
            executable = (
                code == JURISDICTION_CODE
                or (profile is not None
                    and get_program_doctrine(profile.program_slug) is not None
                    and len(get_rate_rules(profile.program_slug)) > 0)
            )
            if not executable:
                raise ValueError(
                    f"'{code}' is not an executable routing target — the post/"
                    "VFX/music components can only be routed to a jurisdiction "
                    "with classified doctrine + statutory rate rules (or the "
                    "baseline). Routing to a catalog-only jurisdiction would "
                    "price at a guessed rate, which is never done."
                )
            value = code
        _fact_answers[key] = value
    _build_state.cache_clear()


def current_fact_answers() -> dict[str, object]:
    return dict(_fact_answers)


def reset_fact_answers() -> None:
    _fact_answers.clear()
    _economics_controls.clear()
    _people_overrides.clear()
    _location_overrides.clear()
    _build_state.cache_clear()


# ── People facts (Part 2: real, verified nationality data) ──────────────────
# The real writer/director/lead-cast/producer facts (see
# app.data.little_utopia_people — reused verbatim from
# tests/validate_little_utopia_v2.py's verified registration, never
# fabricated here). A user-supplied override corrects or supplies a role's
# nationality/residency (e.g. once a real producer is cast, or to model a
# recast) without touching the verified nationality database.
_people_overrides: dict[str, "PersonOverride"] = {}

# Canonical person-role schema (one shared inventory for the whole app).
# The first four are the discovered/package roles. lead_cast_2/3 are the
# additional lead-cast slots (castable before discovery finds anyone).
# dop / editor / composer are the recurring cultural-test creative roles
# extracted from the populated cultural_qualification_model rules DB
# (role-frequency across programs: composer appears in au_producer_offset
# + uk_avec point rules; editor and dop in the BFI AVEC weighted crew
# sections) — the roles jurisdiction rule engines repeatedly consume.
_PEOPLE_ROLE_KEYS: tuple[str, ...] = (
    "writer", "director", "lead_cast", "lead_cast_2", "lead_cast_3",
    "producer", "dop", "editor", "composer",
)
# Roles that exist ONLY as user-supplied facts (no discovered person in
# the package pipeline yet) — served from the override store.
_SLOT_ROLE_KEYS: tuple[str, ...] = ("lead_cast_2", "lead_cast_3", "dop", "editor", "composer")


def apply_people_facts(answers: dict[str, object]) -> None:
    """Set name/nationality/residency overrides. Recognized keys:
      '{role}_nationality', '{role}_residency', '{role}_name' for role in
      _PEOPLE_ROLE_KEYS. Nationality/residency are ISO2 country codes;
      name is a free-text person name. A value of None clears that field
      back to the discovered/verified default (or UNKNOWN)."""
    from app.data.little_utopia_people import PersonOverride
    for key, value in answers.items():
        parts = key.rsplit("_", 1)
        if len(parts) != 2 or parts[1] not in ("nationality", "residency", "name"):
            raise ValueError(
                f"'{key}' is not a recognized people fact. Expected "
                f"'{{role}}_nationality', '{{role}}_residency' or "
                f"'{{role}}_name' for role in {_PEOPLE_ROLE_KEYS}."
            )
        role, field_name = parts
        if role not in _PEOPLE_ROLE_KEYS:
            raise ValueError(f"'{role}' is not a known role ({_PEOPLE_ROLE_KEYS}).")
        if field_name == "name":
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"'{key}' expects a non-empty name, got: {value!r}")
            value = value.strip() if value else None
        else:
            if value is not None and (not isinstance(value, str) or len(value) != 2):
                raise ValueError(f"'{key}' expects a 2-letter ISO country code, got: {value!r}")
            value = value.upper() if value else None
        current = _people_overrides.get(role, PersonOverride())
        kwargs = {"nationality": current.nationality, "residency": current.residency, "name": current.name}
        kwargs[field_name] = value
        if all(v is None for v in kwargs.values()):
            _people_overrides.pop(role, None)
        else:
            _people_overrides[role] = PersonOverride(**kwargs)
    _build_state.cache_clear()


def current_people_facts() -> dict[str, dict[str, str | None]]:
    return {
        role: {"nationality": o.nationality, "residency": o.residency, "name": o.name}
        for role, o in _people_overrides.items()
    }


def _merge_override_role_codes(role_known_codes: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Feed the slot-role nationalities (lead_cast_2/3, dop, editor,
    composer — user-supplied facts with no package person yet) into the
    cultural-gate role vocabulary. lead_cast_2/3 merge into 'lead_cast'
    (they are lead-cast slots); dop/editor/composer map 1:1 to the
    NationalityRequirement role names the rules DB already uses."""
    merged = dict(role_known_codes)
    for role in _SLOT_ROLE_KEYS:
        o = _people_overrides.get(role)
        if o is None or o.nationality is None:
            continue
        target = "lead_cast" if role.startswith("lead_cast") else role
        merged[target] = tuple(sorted(set(merged.get(target, ())) | {o.nationality}))
    return merged


# ── Permanent production-structure default (explicit + traceable) ────────────
# For every candidate jurisdiction the optimizer assumes a legally
# compliant local production structure designed to MAXIMIZE qualification,
# unless the user supplies contrary facts. This assumption is exposed
# (never hidden) on /production.economics — see get_economics().
SPV_PRODUCTION_STRUCTURE_DEFAULT: dict[str, object] = {
    "jurisdiction_code": JURISDICTION_CODE,
    "assumption": "optimized_legal_local_structure",
    "assumptions": [
        "A Mauritius production SPV is established.",
        "Qualifying production costs are contracted, invoiced, and paid "
        "through that SPV where legally permitted.",
        "Local payroll / vendor routing is used where required.",
        "Foreign people and vendors are NOT assumed to be paid offshore or "
        "incurred offshore merely because they are foreign — the EDB QPE list "
        "explicitly includes 'Labour costs (including non-nationals)'.",
        "Unknown structuring details generate producer questions; they never "
        "create pessimistic exclusions.",
    ],
    "exclusion_gates": [
        "Primary authority explicitly excludes the cost.",
        "A verified production fact fails a requirement.",
        "A required legal condition demonstrably fails.",
    ],
    "user_overridable_via": sorted(ANSWERABLE_FACTS),
}


# ── Production-economics controls (financing / in-kind / awarded rate) ───────
# A light, on-demand store separate from the qualification-fact store: these
# controls feed only the /economics headline results (mauritius_economics),
# never the register/structures. Financing defaults to ZERO; the $625k
# in-kind post is a user-controllable fact, never a hardcoded additive.
_economics_controls: dict[str, object] = {}

_FINANCING_METHODS = {"none", "rate_time", "hard_cost"}
_INKIND_ACCEPTANCE = {"unknown", "yes", "no"}
_POST_LOCATIONS = {"mauritius", "elsewhere"}


_TRAVEL_PRICING_MODES = {"benchmark_estimate", "live_lookup"}
_FX_RATE_SOURCES = {"live", "historical", "user_override"}
_TRAVEL_NUMERIC_KEYS = {
    "business_travelers", "economy_travelers", "rotations_per_year",
    "hotel_nights", "per_diem_days", "budgeted_travel_override_usd",
}
_FX_NUMERIC_KEYS = {"fx_user_rate", "fx_scenario_delta_pct"}


def apply_economics_controls(controls: dict[str, object]) -> None:
    """Set production-economics controls. Recognized keys:
      financing_method: 'none' | 'rate_time' | 'hard_cost'
      financing_annual_rate: float, financing_weeks: int,
      financing_amount_pct: float, financing_hard_cost_usd: float,
      financing_source: 'user_input' | 'document_input'
      awarded_rate: float (within [floor, ceiling])
      in_kind_post_available: bool, in_kind_post_fmv_usd: float,
      in_kind_post_accepted_as_qpe: 'unknown'|'yes'|'no',
      replacement_post_cost_if_lost_usd: float,
      post_location: 'mauritius'|'elsewhere'
      origin_city: str (Part 5), business_travelers/economy_travelers: int,
      rotations_per_year/hotel_nights/per_diem_days: int,
      travel_pricing_mode: 'benchmark_estimate'|'live_lookup',
      budgeted_travel_override_usd: float (else derived from the real
        budget's own ATL+BTL Travel & Living accounts),
      fx_rate_source: 'live'|'historical'|'user_override' (Part 7),
      fx_historical_date: str ('YYYY-MM-DD', required for 'historical'),
      fx_user_rate: float, fx_scenario_delta_pct: float
    A value of None clears that control (returns it to its default)."""
    _numeric = {
        "financing_annual_rate", "financing_amount_pct", "financing_hard_cost_usd",
        "awarded_rate", "in_kind_post_fmv_usd", "replacement_post_cost_if_lost_usd",
        "financing_weeks",
    } | _TRAVEL_NUMERIC_KEYS | _FX_NUMERIC_KEYS
    _enums = {
        "financing_method": _FINANCING_METHODS,
        "in_kind_post_accepted_as_qpe": _INKIND_ACCEPTANCE,
        "post_location": _POST_LOCATIONS,
        "financing_source": {"user_input", "document_input"},
        "travel_pricing_mode": _TRAVEL_PRICING_MODES,
        "fx_rate_source": _FX_RATE_SOURCES,
    }
    for key, value in controls.items():
        if value is None:
            _economics_controls.pop(key, None)
            continue
        if key in _numeric:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"Economics control '{key}' expects a number.")
            _economics_controls[key] = float(value)
        elif key in _enums:
            v = str(value).lower()
            if v not in _enums[key]:
                raise ValueError(f"'{value}' invalid for '{key}' (allowed: {sorted(_enums[key])}).")
            _economics_controls[key] = v
        elif key == "in_kind_post_available":
            if not isinstance(value, bool):
                raise ValueError("in_kind_post_available expects a bool.")
            _economics_controls[key] = value
        elif key in ("origin_city", "fx_historical_date"):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{key} expects a non-empty string.")
            _economics_controls[key] = value
        else:
            raise ValueError(f"'{key}' is not a recognized economics control.")
    # Economics controls are a canonical input (financing, in-kind, awarded
    # rate, travel, FX all shape the served results). Invalidate the cached
    # state so the canonical recomputation stamp — and any state field that
    # comes to depend on these controls — recomputes, exactly as the fact,
    # people, and location stores already do. Without this the stamp would
    # report a fingerprint that no longer matches the live economics inputs.
    _build_state.cache_clear()


def current_economics_controls() -> dict[str, object]:
    return dict(_economics_controls)


def build_financing_model() -> "FinancingModel":
    """The financing model from the current controls. DEFAULT: ZERO — never
    a silent 8%/39wk assumption (Part 2)."""
    from app.calculators.mauritius_economics import (
        FinancingMethod, FinancingModel, FinancingSource,
    )
    c = _economics_controls
    method = c.get("financing_method", "none")
    if method == "none":
        return FinancingModel()  # DEFAULT_ZERO / NONE
    src = FinancingSource(c.get("financing_source", "user_input"))
    if method == "hard_cost":
        return FinancingModel(
            source=src, method=FinancingMethod.HARD_COST,
            hard_cost_usd=c.get("financing_hard_cost_usd", 0.0),
        )
    return FinancingModel(
        source=src, method=FinancingMethod.RATE_TIME,
        annual_rate=c.get("financing_annual_rate"),
        weeks=int(c["financing_weeks"]) if "financing_weeks" in c else None,
        financed_amount_pct=c.get("financing_amount_pct"),
    )


def build_inkind_model() -> "InKindPostModel":
    """The in-kind post model from the current controls. Canonical
    production fact: $625,000 in-kind post, intended in Mauritius (Part 3)."""
    from app.calculators.mauritius_economics import (
        InKindAcceptance, InKindPostModel, PostLocation,
    )
    c = _economics_controls
    return InKindPostModel(
        available=bool(c.get("in_kind_post_available", True)),
        fmv_usd=float(c.get("in_kind_post_fmv_usd", 625_000.0)),
        jurisdiction=JURISDICTION_CODE,
        accepted_as_qpe=InKindAcceptance(c.get("in_kind_post_accepted_as_qpe", "unknown")),
        replacement_post_cost_if_lost_usd=float(c.get("replacement_post_cost_if_lost_usd", 625_000.0)),
        post_location=PostLocation(c.get("post_location", "mauritius")),
    )


def get_awarded_rate() -> float | None:
    v = _economics_controls.get("awarded_rate")
    return float(v) if v is not None else None


def build_travel_inputs() -> "TravelInputs":
    """User-controlled travel inputs (Part 5). Defaults: LA origin, 1
    business traveler, quarterly rotations, 2-week hotel/per-diem — same
    defaults travel_model.estimate_travel_cost() itself already documents."""
    from app.calculators.production_normalization import TravelInputs, TravelPricingMode
    c = _economics_controls
    return TravelInputs(
        origin_city=str(c.get("origin_city", "LA")),
        business_travelers=int(c.get("business_travelers", 1)),
        economy_travelers=int(c.get("economy_travelers", 0)),
        rotations_per_year=int(c.get("rotations_per_year", 4)),
        hotel_nights=int(c.get("hotel_nights", 14)),
        per_diem_days=int(c.get("per_diem_days", 14)),
        pricing_mode=TravelPricingMode(c.get("travel_pricing_mode", "benchmark_estimate")),
    )


def build_fx_inputs() -> "FXInputs":
    """User-controlled FX inputs (Part 7). Defaults to the most recent
    sourced (real, fetched) rate snapshot on file; a historical date,
    scenario delta, or override requires an explicit user value — never
    a fabricated rate. Budget exchange assumptions never enter here — the
    register/budget is USD-denominated and this function reads only
    economics_controls, never the parsed budget document."""
    from app.calculators.production_normalization import FXInputs, FXRateSource
    c = _economics_controls
    return FXInputs(
        rate_source=FXRateSource(c.get("fx_rate_source", "live")),
        historical_date=c.get("fx_historical_date"),
        user_rate=c.get("fx_user_rate"),
        scenario_fx_delta_pct=float(c.get("fx_scenario_delta_pct", 0.0)),
    )


def budgeted_travel_usd(register: list[AccountQualification]) -> float:
    """The real, verified budgeted travel figure — accounts 1600 (ATL
    TRAVEL & LIVING) + 3900 (BTL TRAVEL & LIVING) from the actual parsed
    Little Utopia budget. Overridable by the user (budgeted_travel_override_usd)."""
    override = _economics_controls.get("budgeted_travel_override_usd")
    if override is not None:
        return float(override)
    by_code = {a.account_code: a.amount_usd for a in register}
    return by_code.get("1600", 0.0) + by_code.get("3900", 0.0)


def build_normalized_structures(state: "LittleUtopiaState") -> dict:
    """Parts 5-7 combined: travel normalization + FX normalization + the
    Mauritius in-kind-post scenario (selected via the existing economics
    controls) applied ON TOP of each composed candidate's already-priced
    conservative cash NPC — purely additive, never touching
    optimization_engine.py's math or production_structure_composer.py's
    own ranking. Returns a SEPARATE, explicitly-labeled normalized
    ranking; the primary /structures ranking is untouched."""
    from app.calculators.mauritius_economics import compute_mauritius_economics
    from app.calculators.optimization_engine import RiskCase
    from app.calculators.production_normalization import normalize_candidates

    base_npc: dict[str, float] = {}
    jurisdictions: dict[str, tuple] = {}
    for candidate in state.composition.candidates:
        if candidate.cases is None:
            continue
        conservative = candidate.cases.get(RiskCase.CONSERVATIVE)
        if conservative is None:
            continue
        base_npc[candidate.candidate_id] = conservative.net_production_cost_usd
        jurisdictions[candidate.candidate_id] = candidate.participating_jurisdictions

    # Part 7: in-kind adjustment, MU-participating candidates only. The
    # selected scenario comes from the SAME economics controls /economics
    # already reads (Part 5 of the prior phase) — never a second source
    # of truth. UNKNOWN acceptance (the default) applies zero adjustment:
    # the legal-acceptance question stays gated, never assumed.
    inkind = build_inkind_model()
    verified_cash_qpe = sum(
        a.amount_usd for a in state.register if a.state == QualificationState.QUALIFIES
    )
    rate_floor = state.rate_resolution.floor_rate if state.rate_resolution else 0.30
    econ = compute_mauritius_economics(
        gross_cash_budget_usd=state.gross_budget_usd, verified_cash_qpe_usd=verified_cash_qpe,
        rate_floor=rate_floor, rate_ceiling=state.rate, financing=build_financing_model(), inkind=inkind,
    )
    floor_npc = econ["verified_floor_case"].net_production_cost_usd
    if inkind.post_location.value == "elsewhere":
        selected_npc = econ["inkind_post_options"]["lost_or_moved_outside_mu"].net_production_cost_usd
    elif inkind.accepted_as_qpe.value == "yes":
        selected_npc = econ["inkind_post_options"]["accepted_as_qpe"].net_production_cost_usd
    elif inkind.accepted_as_qpe.value == "no":
        selected_npc = econ["inkind_post_options"]["not_accepted_as_qpe"].net_production_cost_usd
    else:
        selected_npc = floor_npc  # UNKNOWN — gated, no assumption
    inkind_delta = round(selected_npc - floor_npc, 2)
    inkind_by_candidate = {
        cid: inkind_delta for cid, juris in jurisdictions.items() if JURISDICTION_CODE in juris
    }

    results = normalize_candidates(
        base_npc_by_candidate=base_npc,
        participating_jurisdictions_by_candidate=jurisdictions,
        travel_inputs=build_travel_inputs(),
        original_budgeted_travel_usd=budgeted_travel_usd(state.register),
        fx_inputs=build_fx_inputs(),
        original_jurisdiction_code=JURISDICTION_CODE,
        inkind_adjustment_by_candidate=inkind_by_candidate,
    )
    return {
        "version": "2.0.0",
        "note": (
            "SEPARATE from the primary /structures ranking (which prices "
            "cash-only, zero-financing candidates). This ranking additionally "
            "layers an INCREMENTAL travel adjustment (proposed jurisdiction vs. "
            "the original Mauritius shoot geography — not total travel cost), "
            "FX normalization, and the selected in-kind-post scenario on top "
            "of each candidate's cash NPC."
        ),
        "ranking": [
            {
                "candidate_id": r.candidate_id,
                "base_cash_npc_usd": r.base_cash_npc_usd,
                "travel_incremental_delta_usd": r.travel.incremental_delta_usd if r.travel else None,
                "fx_delta_usd": r.fx.delta_usd if r.fx else None,
                "inkind_adjustment_usd": r.inkind_adjustment_usd,
                "normalized_npc_usd": r.normalized_npc_usd,
                "travel_detail": (
                    {
                        "origin_city": r.travel.origin_city,
                        "original_jurisdiction_code": r.travel.original_jurisdiction_code,
                        "proposed_jurisdiction_code": r.travel.jurisdiction_code,
                        "original_budgeted_travel_usd": r.travel.original_budgeted_travel_usd,
                        "original_modeled_travel_usd": r.travel.original_modeled_travel_usd,
                        "proposed_modeled_travel_usd": r.travel.proposed_modeled_travel_usd,
                        "delta_vs_original_budget_usd": r.travel.delta_vs_original_budget_usd,
                        "pricing_mode": r.travel.pricing_mode,
                        "note": r.travel.note,
                    } if r.travel else None
                ),
                "fx_detail": (
                    {
                        "local_currency": r.fx.local_currency,
                        "live_rate": r.fx.live_rate,
                        "rate_used": r.fx.rate_used,
                        "rate_source": r.fx.rate_source,
                        "rate_date": r.fx.rate_date,
                        "note": r.fx.note,
                    } if r.fx else None
                ),
            }
            for r in results
        ],
    }


def build_alternative_jurisdiction_comparisons(state: "LittleUtopiaState") -> dict:
    """Executable Jurisdiction Knowledge phase, Parts 1-3: for every
    jurisdiction in jurisdiction_comparison.ALL_PROFILES whose program has
    BOTH a classified doctrine (program_spend_rules.py) AND rate rules
    (program_rate_rules.py) — i.e. is genuinely EXECUTABLE, never merely
    catalog-present — derive Little Utopia's real budget against that
    jurisdiction's real statutory rate and produce QPE/incentive/NPC,
    plus the SAME travel-incremental and FX deltas already computed for
    treaty candidates (production_normalization.py, reused not
    duplicated). Any jurisdiction lacking doctrine+rate rules is
    EXCLUDED here, not silently priced at a fabricated/guessed rate —
    listed separately as catalog_only with the reason."""
    from app.calculators import jurisdiction_comparison as jc
    from app.calculators.qualification_model import (
        build_little_utopia_register_for_jurisdiction,
    )
    from app.calculators.optimization_engine import build_risk_cases, RiskCase
    from app.calculators.production_normalization import (
        TravelInputs, compute_travel_normalization, compute_fx_normalization,
    )
    from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
    from app.data.program_spend_rules import get_program_doctrine

    travel_inputs = build_travel_inputs()
    origin_budgeted_travel = budgeted_travel_usd(state.register)
    fx_inputs = build_fx_inputs()

    executable: list[dict] = []
    catalog_only: list[dict] = []

    for code in sorted(jc.ALL_PROFILES.keys()):
        if code == JURISDICTION_CODE:
            continue  # Mauritius is the baseline, served separately on /economics
        profile = jc.ALL_PROFILES[code]
        slug = profile.program_slug
        has_doctrine = get_program_doctrine(slug) is not None
        has_rate = len(get_rate_rules(slug)) > 0
        if not (has_doctrine and has_rate):
            catalog_only.append({
                "jurisdiction_code": code,
                "program_slug": slug,
                "program_name": profile.program_name,
                "confidence_tier": profile.confidence_tier,
                "reason": (
                    ("missing doctrine" if not has_doctrine else "")
                    + (" and " if not has_doctrine and not has_rate else "")
                    + ("missing rate rules" if not has_rate else "")
                ) + " — present in the catalog, not yet executable.",
            })
            continue

        register = build_little_utopia_register_for_jurisdiction(code, slug, 0.0)
        from app.calculators.qualification_model import QualificationState as _QS
        qpe = round(sum(a.amount_usd for a in register if a.state == _QS.QUALIFIES), 2)
        excluded = [a.account_code for a in register if a.state == _QS.EXCLUDED]
        excluded_usd = round(sum(a.amount_usd for a in register if a.state == _QS.EXCLUDED), 2)

        rr = resolve_program_rate(slug, production_type="feature_film", qpe_usd=qpe)
        if rr is None:
            catalog_only.append({
                "jurisdiction_code": code, "program_slug": slug,
                "program_name": profile.program_name, "confidence_tier": profile.confidence_tier,
                "reason": "rate rule present but did not resolve for this production "
                          "type/QPE — excluded rather than guessed.",
            })
            continue

        floor_result = build_risk_cases(
            register=register, gross_budget_usd=state.gross_budget_usd, rate=rr.floor_rate,
            structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
        ).cases[RiskCase.CONSERVATIVE]
        ceiling_result = build_risk_cases(
            register=register, gross_budget_usd=state.gross_budget_usd, rate=rr.modeled_rate,
            structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
        ).cases[RiskCase.CONSERVATIVE]

        travel = compute_travel_normalization(code, travel_inputs, origin_budgeted_travel, JURISDICTION_CODE)
        fx = compute_fx_normalization(code, fx_inputs, floor_result.net_production_cost_usd)

        executable.append({
            "jurisdiction_code": code,
            "program_slug": slug,
            "program_name": profile.program_name,
            "confidence_tier": profile.confidence_tier,
            "doctrine": get_program_doctrine(slug).value,
            "qpe_usd": qpe,
            "excluded_accounts": excluded,
            "excluded_usd": excluded_usd,
            "rate_floor": rr.floor_rate,
            "rate_ceiling": rr.modeled_rate,
            "is_band_ceiling": rr.is_band_ceiling,
            "statutory_basis": rr.basis,
            "floor_case": {
                "incentive_usd": floor_result.incentive_usd,
                "net_production_cost_usd": floor_result.net_production_cost_usd,
            },
            "ceiling_case": {
                "incentive_usd": ceiling_result.incentive_usd,
                "net_production_cost_usd": ceiling_result.net_production_cost_usd,
            },
            "travel_incremental_delta_usd": travel.incremental_delta_usd,
            "travel_delta_vs_original_budget_usd": travel.delta_vs_original_budget_usd,
            "fx_delta_usd": fx.delta_usd,
            "marine_suitability": profile.marine_suitability,
        })

    return {
        "version": "1.0.0",
        "note": (
            "Alternative-jurisdiction 'what if the same real budget were made "
            "here instead' comparisons — real QPE/incentive/NPC/travel/FX for "
            "every EXECUTABLE jurisdiction (classified doctrine + rate rules "
            "on file); every other cataloged jurisdiction is excluded, not "
            "priced at a guessed rate, and listed under catalog_only with why."
        ),
        "executable": executable,
        "catalog_only": catalog_only,
    }


def build_available_funds() -> dict:
    """Grants/funds/stacking (Systems Validation phase): fund_economics_
    model.py has 243 real, classified fund/grant/advance entries but
    ProductionStructureCandidate.fund_graph_refs is empty for every
    composed candidate — confirmed via runtime, never wired. This is a
    BOUNDED, HONEST connection: for each of the 4 executable jurisdictions
    (Part 1-3), list the REAL additional funds/grants registered for that
    country prefix, with their REAL classification metadata (rebate/
    grant/tax_credit/advance, repayable/recoupable/equity terms) — never
    a fabricated dollar amount. Little-Utopia-specific award amounts are
    NOT estimated (fund_economics_model has no per-production figures,
    only typical_max_award_usd — a generic industry figure, never
    presented as this production's entitlement).

    STACKING: structure_graph_model.py has 523 real edges. Where an edge's
    slug matches an executable program slug EXACTLY, the real relationship
    (complements / reduces / blocks / enables / unlocks / alternative_to)
    is surfaced per jurisdiction below — no dollar amount computed, only
    the sourced relationship the graph actually stores. Coverage is uneven
    and reported honestly: Ireland's ie_section_481 has rich edges; Greece
    one; Mauritius none; Malta's edges sit under a NON-executable variant
    slug ('mt_mfc_cash_rebate' vs the executable 'mt_mfc_rebate') and are
    NOT force-matched. No stacked NPC is produced — that would require a
    per-fund dollar figure fund_economics_model deliberately does not hold."""
    from app.data.fund_economics_model import get_fund_economics, list_all_slugs
    from app.data.program_spend_rules import get_program_doctrine
    from app.data.program_rate_rules import get_rate_rules
    from app.data.structure_graph_model import STRUCTURE_GRAPH_EDGES

    _EXECUTABLE_PREFIXES = {"MU": "mu_", "MT": "mt_", "IE": "ie_", "GR": "gr_"}
    _EXECUTABLE_BASE_SLUG = {
        "MU": "mu_edb_incentive", "MT": "mt_mfc_rebate",
        "IE": "ie_section_481", "GR": "gr_cash_rebate",
    }

    def _stacking_relationships(base_slug: str) -> list[dict]:
        """Real edges from structure_graph_model touching this base slug
        after CANONICAL slug reconciliation (app.data.program_slug_aliases
        — e.g. the graph's 'mt_mfc_cash_rebate' names the same Malta Film
        Commission rebate as the executable 'mt_mfc_rebate'). Direction
        preserved, nothing inferred; when an edge matched via an alias,
        the variant slug it was recorded under is disclosed."""
        from app.data.program_slug_aliases import canonical_slug
        base = canonical_slug(base_slug)
        rels: list[dict] = []
        for e in STRUCTURE_GRAPH_EDGES:
            src, tgt = canonical_slug(e.source_slug), canonical_slug(e.target_slug)
            if src == base:
                rels.append({
                    "direction": "base_affects",
                    "edge_type": e.edge_type,
                    "other_program_slug": tgt,
                    "magnitude": getattr(e, "magnitude", None),
                    "note": getattr(e, "notes", None),
                    "recorded_under_variant_slug": (
                        e.source_slug if e.source_slug != base else None
                    ),
                })
            elif tgt == base:
                rels.append({
                    "direction": "affects_base",
                    "edge_type": e.edge_type,
                    "other_program_slug": src,
                    "magnitude": getattr(e, "magnitude", None),
                    "note": getattr(e, "notes", None),
                    "recorded_under_variant_slug": (
                        e.target_slug if e.target_slug != base else None
                    ),
                })
        return sorted(rels, key=lambda r: (r["edge_type"], r["other_program_slug"]))

    all_slugs = list_all_slugs()

    by_jurisdiction: dict[str, list[dict]] = {}
    for code, prefix in _EXECUTABLE_PREFIXES.items():
        entries = []
        for slug in sorted(s for s in all_slugs if s.startswith(prefix)):
            e = get_fund_economics(slug)
            is_base_incentive = get_program_doctrine(slug) is not None and len(get_rate_rules(slug)) > 0
            entries.append({
                "program_slug": slug,
                "classification": e.classification,
                "is_repayable": e.is_repayable,
                "is_recoupable": e.is_recoupable,
                "has_equity_participation": e.has_equity_participation,
                "equity_pct": e.equity_pct,
                "is_base_incentive_already_priced": is_base_incentive,
                "note": (
                    "This IS the base incentive already priced in the QPE/NPC figures above."
                    if is_base_incentive else
                    "Additional fund/grant beyond the base incentive — real, sourced classification "
                    "only; no dollar amount estimated for this production (never fabricated)."
                ),
            })
        by_jurisdiction[code] = entries

    # Real stacking relationships per executable jurisdiction — sourced from
    # structure_graph_model, exact-slug-matched only, no dollar figure.
    stacking_by_jurisdiction = {
        code: _stacking_relationships(base) for code, base in _EXECUTABLE_BASE_SLUG.items()
    }
    _edge_counts = {c: len(v) for c, v in stacking_by_jurisdiction.items()}

    return {
        "version": "1.2.0",
        "note": (
            "fund_economics_model.py's real classification data for the 4 executable "
            "jurisdictions. Real stacking RELATIONSHIPS (not dollar amounts) are "
            "surfaced per jurisdiction from structure_graph_model.py after CANONICAL "
            "program-slug reconciliation (app.data.program_slug_aliases): the graph's "
            "'mt_mfc_cash_rebate' / 'gr_ekome_rebate' variants name the same programs "
            "as the executable 'mt_mfc_rebate' / 'gr_cash_rebate'."
        ),
        "by_jurisdiction": by_jurisdiction,
        "stacking_by_jurisdiction": stacking_by_jurisdiction,
        "stacking_status": (
            "CONNECTED AT RELATIONSHIP LEVEL (no stacked dollar figure): "
            f"canonical-slug matches against structure_graph_model.py yield "
            f"IE={_edge_counts['IE']} edges, GR={_edge_counts['GR']}, "
            f"MU={_edge_counts['MU']}, MT={_edge_counts['MT']}. "
            "The former Malta slug mismatch ('mt_mfc_cash_rebate' vs executable "
            "'mt_mfc_rebate') is reconciled via program_slug_aliases — Malta's and "
            "Greece's variant-slug edges now surface, each disclosing the variant "
            "slug it was recorded under. No stacked NPC is computed: "
            "fund_economics_model holds no per-production dollar figure, so a "
            "stacked total would have to be fabricated (never done). Stacking "
            "affects structure economics only through allocated-structure pricing "
            "(one program per segment; multi-program combinations enter only via "
            "enumerate_segment_program_stacks when real multi-program knowledge "
            "exists — see /structures.allocated_structures.stack_combinations)."
        ),
    }


# Executable-jurisdiction discovery now lives in
# app.calculators.production_discovery.discover_executable_jurisdictions —
# the single, data-driven authority that examines EVERY implemented
# jurisdiction (not just ALL_PROFILES) and returns the accepted set with a
# full reasoned audit. build_allocated_structures calls it directly.


_STATED_LOCATION_AUTHORITY = (
    "The production budget's own cover page ('PICTURE EDIT: LA', 'SOUND "
    "EDIT: LA') and account names ('EDITORIAL - USA', 'USA ADMIN COSTS') — "
    "see app.data.little_utopia_real_budget.LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU."
)


def _budget_lines_for_allocation() -> list:
    from app.calculators.qualification_derivation import BudgetLine
    from app.data.little_utopia_real_budget import (
        LITTLE_UTOPIA_REAL_BUDGET_LINES,
        LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
    )
    return [
        BudgetLine(
            account_code=code, description=desc, amount_usd=amt,
            spend_category=LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(code),
            is_memo=False,
        )
        for code, desc, amt, _page in LITTLE_UTOPIA_REAL_BUDGET_LINES
    ]


def build_allocated_structures(state: "LittleUtopiaState") -> dict:
    """The ACCOUNT->JURISDICTION ALLOCATION surface: every structure the
    production's facts/elections currently express, partitioned account-
    by-account (production_allocation), priced from one partial register
    per jurisdiction (allocation_pricing), travel/FX applied once at
    structure level, ranked over fully-priced structures only.

    Structures served:
      - the Mauritius single-jurisdiction baseline;
      - full relocation to every EXECUTABLE alternative (MT/IE/GR today);
      - a component-relocation structure when the producer has elected
        one (component_route_post fact — routes post/VFX/music);
      - a treaty co-production structure when a treaty partner is
        elected (treaty_partner_code fact) — evaluated against the real
        treaty registry; if no instrument covers the pair, the structure
        is served UNPRICED with that exact blocker (never forced).

    Split / multi-party / service / hybrid structures are expressible
    through the same generic StructureSpec (explicit producer splits,
    extra participants, ownership shares) — none is fabricated here
    without a producer election.
    """
    from app.calculators.allocation_pricing import (
        price_allocated_structure,
        rank_allocated_structures,
    )
    from app.calculators.production_allocation import (
        MOVABLE_COMPONENTS,
        StructureSpec,
        derive_account_allocation,
    )
    from app.calculators.production_normalization import (
        compute_fx_normalization,
        compute_travel_normalization,
    )
    from app.data.little_utopia_real_budget import (
        LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
        LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
    )

    lines = _budget_lines_for_allocation()
    # ── GLOBAL DISCOVERY (Phase 6): examine EVERY implemented jurisdiction
    # in the database (not a hand-picked list), reject the non-executable
    # with reasons, accept only those with the classified knowledge to price
    # this production. The accepted set — never a hard-coded country list —
    # is what enters structure generation. Full audit + metrics are exposed
    # on the served payload under `discovery`.
    from app.calculators.production_discovery import discover_executable_jurisdictions
    _verified_qpe = round(
        sum(a.amount_usd for a in state.register if a.state == QualificationState.QUALIFIES), 2
    )
    discovery = discover_executable_jurisdictions(
        production_type=MU_PRODUCTION_TYPE,
        qpe_usd=_verified_qpe,
        home_code=JURISDICTION_CODE,
    )
    alts = discovery.accepted_alternatives(JURISDICTION_CODE)
    slug_by_code = {c: s for c, s in alts}
    fact_answers = state.fact_answers or {}

    # ── structure specs from the production's real facts/elections ──
    specs: list[StructureSpec] = [StructureSpec(
        structure_id="ALLOC-BASELINE-MU",
        structure_type="single_country",
        label="Mauritius single-jurisdiction baseline",
        primary_jurisdiction=JURISDICTION_CODE,
        participants=(JURISDICTION_CODE,),
        incentive_programs={JURISDICTION_CODE: "mu_edb_incentive"},
        notes="The production's current plan: shoot Mauritius, post per the "
              "budget's own stated locations.",
    )]
    for code, slug in alts:
        specs.append(StructureSpec(
            structure_id=f"ALLOC-RELOC-{code}",
            structure_type="full_relocation",
            label=f"Full relocation to {code}",
            primary_jurisdiction=code,
            participants=(code,),
            incentive_programs={code: slug},
            notes="Whole production relocated; stated-location post facts "
                  "carry over unchanged (they are jurisdiction-independent "
                  "producer decisions on the budget's own cover page).",
        ))

    # Component-routing (anchor-component) structures are AUTO-ENUMERATED
    # for every executable partner — MU shoot anchor + the movable
    # post/VFX/music components routed to each executable jurisdiction.
    # These are reachable and executable without any producer election,
    # so the optimizer evaluates them by default (each prices, or blocks
    # honestly on its own program's minimum-spend rule — never omitted).
    # A producer's component_route_post election simply pre-selects one of
    # these (or the MU-only case) and is deduped against the auto set.
    route_target = fact_answers.get("component_route_post")
    route_target = str(route_target).upper() if route_target else None
    auto_component_targets = [code for code, _ in alts]
    if route_target == JURISDICTION_CODE:
        auto_component_targets = [JURISDICTION_CODE]  # producer kept post in MU
    for target in auto_component_targets:
        participants = (
            (JURISDICTION_CODE,) if target == JURISDICTION_CODE
            else (JURISDICTION_CODE, target)
        )
        programs = {JURISDICTION_CODE: "mu_edb_incentive"}
        if target != JURISDICTION_CODE:
            programs[target] = slug_by_code[target]
        elected = " (producer-elected)" if target == route_target else ""
        specs.append(StructureSpec(
            structure_id=f"ALLOC-COMPONENT-POST-{target}",
            structure_type="component_relocation",
            label=(f"Mauritius shoot + post/VFX/music routed to {target} "
                   f"(anchor-component structure){elected}"),
            primary_jurisdiction=JURISDICTION_CODE,
            participants=participants,
            incentive_programs=programs,
            component_routes={c: target for c in sorted(MOVABLE_COMPONENTS)},
            notes=("Auto-evaluated anchor-component structure (no election "
                   "required)." + (" Producer-elected via component_route_post."
                                    if target == route_target else "")),
        ))

    treaty_partner = fact_answers.get("treaty_partner_code")
    if treaty_partner:
        treaty_partner = str(treaty_partner).upper()
        programs = {JURISDICTION_CODE: "mu_edb_incentive"}
        partner_slug = slug_by_code.get(treaty_partner)
        if partner_slug:
            programs[treaty_partner] = partner_slug
        else:
            partner_profile = jc.ALL_PROFILES.get(treaty_partner)
            if partner_profile is not None:
                # The partner claims its program; executability is
                # evaluated (and blocked honestly) by segment pricing.
                programs[treaty_partner] = partner_profile.program_slug
        specs.append(StructureSpec(
            structure_id=f"ALLOC-TREATY-MU-{treaty_partner}",
            structure_type="treaty_coproduction",
            label=f"Treaty co-production MU + {treaty_partner}",
            primary_jurisdiction=JURISDICTION_CODE,
            participants=(JURISDICTION_CODE, treaty_partner),
            incentive_programs=programs,
            notes="Elected via the treaty_partner_code fact; treaty status is "
                  "evaluated against the real treaty registry, never assumed.",
        ))

    # ── allocation + pricing per spec (travel/FX once, structure level) ──
    travel_inputs = build_travel_inputs()
    origin_budgeted_travel = budgeted_travel_usd(state.register)
    fx_inputs = build_fx_inputs()

    # structuring_advisor.routing_decisions as routing-rationale input —
    # the connected "what work happens where" seed, surfaced with the
    # structures it informs.
    advisor_routing = []
    if state.structuring_advisory is not None:
        advisor_routing = list(getattr(state.structuring_advisory, "routing_decisions", []))

    # Off-budget Mauritius in-kind post normalization (Phase 5 canonical
    # economics): the ~$625k MU in-kind post FMV is NOT a budget line and
    # NOT QPE. It enters production economics only as a replacement-cost
    # normalization — a structure that moves the post/VFX/music work out of
    # Mauritius must absorb the equivalent replacement cost; one that keeps
    # the post in Mauritius carries $0. Sourced from the existing in-kind
    # model (economics controls), never fabricated; gated on availability.
    _inkind_model = build_inkind_model()
    _inkind_replacement_cost = (
        _inkind_model.replacement_post_cost_if_lost_usd
        if _inkind_model.available else 0.0
    )

    pricings = []
    for spec in specs:
        # A structure keeps the MU in-kind post benefit iff it is
        # MU-anchored AND does not route the movable post out of MU.
        _routes_post_away = any(
            t != JURISDICTION_CODE for t in spec.component_routes.values()
        )
        _retains_mu_inkind = (
            spec.primary_jurisdiction == JURISDICTION_CODE and not _routes_post_away
        )
        inkind_replacement_delta = (
            0.0 if _retains_mu_inkind else _inkind_replacement_cost
        )
        allocation = derive_account_allocation(
            lines=lines,
            spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
            spec=spec,
            stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
            stated_location_authority=_STATED_LOCATION_AUTHORITY,
            routing_rationales={
                c: (f"Producer election (component_route_post fact): the movable "
                    f"'{c}' component is routed to {spec.component_routes.get(c)}.")
                for c in spec.component_routes
            },
        )
        travel = compute_travel_normalization(
            spec.primary_jurisdiction, travel_inputs,
            origin_budgeted_travel, JURISDICTION_CODE,
        )
        pricing = price_allocated_structure(
            spec=spec, allocation=allocation,
            spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
            offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
            gross_budget_usd=state.gross_budget_usd,
            travel_incremental_delta_usd=travel.incremental_delta_usd,
            fx_delta_usd=None,
            inkind_replacement_delta_usd=inkind_replacement_delta,
        )
        if pricing.is_fully_priced:
            fx = compute_fx_normalization(
                spec.primary_jurisdiction, fx_inputs, pricing.npc_verified_usd,
            )
            pricing = price_allocated_structure(
                spec=spec, allocation=allocation,
                spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
                offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
                gross_budget_usd=state.gross_budget_usd,
                travel_incremental_delta_usd=travel.incremental_delta_usd,
                fx_delta_usd=fx.delta_usd,
                inkind_replacement_delta_usd=inkind_replacement_delta,
            )
        pricings.append(pricing)

    # ── multi-program combination status per executable jurisdiction ──
    # (generate_structure_scenarios is the delegated owner of program/
    # stack combinatorics; with exactly one executable program per
    # jurisdiction today there is nothing to combine — disclosed, never
    # fabricated.)
    programs_by_jur: dict[str, list[str]] = {JURISDICTION_CODE: ["mu_edb_incentive"]}
    for code, slug in alts:
        programs_by_jur.setdefault(code, []).append(slug)
    stack_combinations = {
        code: {
            "executable_programs": slugs,
            "combinations_enumerated": 0,
            "status": (
                "single executable program — nothing to combine; multi-program "
                "combinations delegate to generate_structure_scenarios via "
                "allocation_pricing.enumerate_segment_program_stacks when a "
                "second executable program with real data exists."
                if len(slugs) < 2 else "enumeration available"
            ),
        }
        for code, slugs in sorted(programs_by_jur.items())
    }

    def _seg_dict(s) -> dict:
        return {
            "jurisdiction_code": s.jurisdiction_code,
            "program_slug": s.program_slug,
            "claims_incentive": s.claims_incentive,
            "executable": s.executable,
            "allocated_usd": s.allocated_usd,
            "account_codes": list(s.account_codes),
            "qpe_usd": s.qpe_usd,
            "excluded_usd": s.excluded_usd,
            "unresolved_usd": s.unresolved_usd,
            "rate_floor": s.rate_floor,
            "rate_ceiling": s.rate_ceiling,
            "is_band_ceiling": s.is_band_ceiling,
            "statutory_basis": s.statutory_basis,
            "doctrine": s.doctrine,
            "incentive_floor_usd": s.incentive_floor_usd,
            "incentive_ceiling_usd": s.incentive_ceiling_usd,
            "blockers": list(s.blockers),
            "qualification_trace": list(s.register_trace),
            "notes": list(s.notes),
        }

    def _pricing_dict(p) -> dict:
        return {
            "structure_id": p.structure_id,
            "structure_type": p.structure_type,
            "label": p.label,
            "primary_jurisdiction": p.primary_jurisdiction,
            "participants": list(p.participants),
            "is_fully_priced": p.is_fully_priced,
            "blockers": list(p.blockers),
            "gross_budget_usd": p.gross_budget_usd,
            "total_incentive_floor_usd": p.total_incentive_floor_usd,
            "total_incentive_ceiling_usd": p.total_incentive_ceiling_usd,
            "selected_incentive_usd": p.selected_incentive_usd,
            "travel_incremental_delta_usd": p.travel_incremental_delta_usd,
            "fx_delta_usd": p.fx_delta_usd,
            "inkind_replacement_delta_usd": p.inkind_replacement_delta_usd,
            "financing_cost_usd": p.financing_cost_usd,
            "implementation_cost_usd": p.implementation_cost_usd,
            "npc_verified_usd": p.npc_verified_usd,
            "npc_with_adjustments_usd": p.npc_with_adjustments_usd,
            "npc_conservative_usd": p.npc_conservative_usd,
            "treaty_slug": p.treaty_slug,
            "ownership_shares": p.ownership_shares,
            "stacking_note": p.stacking_note,
            "inkind_note": p.inkind_note,
            "notes": list(p.notes),
            "segments": [_seg_dict(s) for s in p.segments],
            "allocation": {
                "allocation_version": p.allocation.allocation_version,
                "is_complete": p.allocation.is_complete,
                "conserves": p.allocation.conserves,
                "total_allocated_usd": p.allocation.total_allocated_usd,
                "total_budget_lines_usd": p.allocation.total_budget_lines_usd,
                "allocated_by_jurisdiction": p.allocation.allocated_by_jurisdiction(),
                "unallocated_account_codes": list(p.allocation.unallocated_account_codes),
                "duplicate_account_codes": list(p.allocation.duplicate_account_codes),
                "notes": list(p.allocation.notes),
                "assignments": [
                    {
                        "account_code": a.account_code,
                        "description": a.description,
                        "amount_usd": a.amount_usd,
                        "component": a.component,
                        "jurisdiction_code": a.jurisdiction_code,
                        "assignment_kind": a.assignment_kind.value,
                        "rationale": a.rationale,
                        "governing_decision": a.governing_decision,
                        "supporting_facts": list(a.supporting_facts),
                        "authority": a.authority,
                        "unresolved_requirements": list(a.unresolved_requirements),
                        "split_pct": a.split_pct,
                    }
                    for a in p.allocation.assignments
                ],
            },
            "recommendation": (
                {
                    "recommendation_id": p.recommendation.recommendation_id,
                    "action": p.recommendation.action,
                    "gated": p.recommendation.gated,
                    "approval_chain": list(p.recommendation.approval_chain),
                    "reversibility": p.recommendation.reversibility,
                    "dependency_group": list(p.recommendation.dependency_group),
                    "explanation": p.recommendation.explanation,
                }
                if p.recommendation else None
            ),
        }

    # ── Worldwide-coverage report: every structure CATEGORY is evaluated;
    #    a category producing zero PRICED candidates states exactly why.
    #    This is what lets the product honestly claim it considered every
    #    executable worldwide pathway (acceptance requirement), never
    #    silently omitting one.
    from app.calculators import treaty_engine as te

    def _cat(structure_types) -> list:
        return [p for p in pricings if p.structure_type in structure_types]

    def _cat_report(name, structure_types, zero_reason: str) -> dict:
        cands = _cat(structure_types)
        priced = [p for p in cands if p.is_fully_priced]
        return {
            "category": name,
            "candidates_evaluated": len(cands),
            "fully_priced": len(priced),
            "blocked": len(cands) - len(priced),
            "structure_ids": [p.structure_id for p in cands],
            "zero_reason": None if cands else zero_reason,
        }

    # co-production reachability, proven from the real treaty registry
    reachable_treaty_partners = sorted({
        code for code, _ in alts
        if te.get_bilateral_treaty(JURISDICTION_CODE, code) is not None
        or (te.is_european_convention_signatory(JURISDICTION_CODE)
            and te.is_european_convention_signatory(code))
    })
    coprod_zero_reason = (
        f"No co-production treaty instrument is registered between the baseline "
        f"jurisdiction ({JURISDICTION_CODE}) and ANY executable partner "
        f"({[c for c, _ in alts]}) — treaty_engine holds no MU bilateral treaty "
        "and MU is not a Eurimages / Ibermedia / European Convention member. "
        "Official co-production is therefore FACTUALLY unavailable from Mauritius "
        "with the current knowledge base (insufficient treaty knowledge / factual "
        "ineligibility), not omitted. A treaty_partner_code election still composes "
        "the pathway and returns it UNPRICED with this exact blocker."
    )

    coverage = {
        "executable_jurisdictions": [c for c, _ in alts] + [JURISDICTION_CODE],
        "catalog_only_excluded": (
            f"{discovery.metrics['rejected_count']} of "
            f"{discovery.metrics['jurisdictions_examined']} examined jurisdictions "
            "were rejected by global discovery (missing classified doctrine and/or "
            "statutory rate rules, or the production's own conditions unmet) — "
            "insufficient knowledge, never priced at a guess. See `discovery` for "
            "the full per-jurisdiction audit."
        ),
        "reachable_treaty_partners": reachable_treaty_partners,
        "categories": [
            _cat_report("single_jurisdiction", {"single_country", "full_relocation",
                                                "service_production"},
                        "no executable jurisdiction"),
            _cat_report("component_routing_anchor", {"component_relocation"},
                        "no executable partner to route movable components to"),
            _cat_report("co_production_treaty",
                        {"treaty_coproduction", "majority_minority", "multi_party", "hybrid"},
                        coprod_zero_reason),
            _cat_report("split_production", {"split_production"},
                        "split production requires an explicit producer sub-line split "
                        "(account_splits) — none elected; zero-by-design absent that "
                        "input, never fabricated"),
        ],
        "note": (
            "service_production is expressed as the single-jurisdiction case "
            "(a fully foreign-financed shoot in one jurisdiction is priced by the "
            "same partial-register kernel); anchor / hybrid structures are "
            "expressed through component_relocation + treaty specs, not bespoke "
            "calculators. Every category above is EVALUATED; any zero is proven."
        ),
    }

    return {
        "version": "1.1.0",
        "note": (
            "Account->jurisdiction allocated structures: every cash account is "
            "allocated exactly once per structure; each jurisdiction segment is "
            "priced from its own PARTIAL qualification register (same derivation "
            "ladder and pricing kernel as the baseline — never the full-budget "
            "register reused); travel and FX apply once at structure level; only "
            "fully-priced structures are ranked. Component-routing (anchor-"
            "component) structures are auto-evaluated for every executable "
            "partner; co-production is evaluated and proven-zero from the real "
            "treaty registry (see coverage). The $2.00 source-document variance "
            "between the authoritative gross budget and the leaf-account sum is "
            "disclosed, not hidden (see budget_reconciliation on /production)."
        ),
        "coverage": coverage,
        # Requirement-first global discovery audit (Phase 6): every
        # implemented jurisdiction examined, with accept/reject + reason and
        # aggregate metrics. Exposed for debugging; the UI reads only the
        # ranked structures, not this block.
        "discovery": {
            "metrics": discovery.metrics,
            "generated_structures": len(pricings),
            "optimized_structures": sum(1 for p in pricings if p.is_fully_priced),
            "final_ranked_structures": sum(
                1 for r in rank_allocated_structures(pricings) if r.get("rank") is not None
            ),
            "examinations": [
                {
                    "jurisdiction_code": e.jurisdiction_code,
                    "jurisdiction_name": e.jurisdiction_name,
                    "accepted": e.accepted,
                    "reason": e.reason,
                    "program_slug": e.program_slug,
                    "has_doctrine": e.has_doctrine,
                    "has_rate_rules": e.has_rate_rules,
                    "resolves_for_production": e.resolves_for_production,
                }
                for e in discovery.examinations
            ],
        },
        "structures": [_pricing_dict(p) for p in pricings],
        "ranking": rank_allocated_structures(pricings),
        "stack_combinations": stack_combinations,
        "advisor_routing_decisions_input": advisor_routing,
    }


def _production_facts() -> ProductionFacts:
    """The production's real current facts (from the actual budget's own
    header text — see app.data.little_utopia_real_budget), overlaid with
    any answers the user has supplied through the facts API."""
    return ProductionFacts(
        jurisdiction_code=JURISDICTION_CODE,
        accounts_outside_jurisdiction=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
        offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        post_work_in_jurisdiction=_fact_answers.get("post_work_in_jurisdiction"),
        payroll_routing_localized=_fact_answers.get("payroll_routing_localized"),
        treaty_partner_code=_fact_answers.get("treaty_partner_code"),
    )


def _register_to_budget_parse_result(register: list[AccountQualification]) -> BudgetParseResult:
    """The register IS Little Utopia's real, parsed account-level budget
    data (app.data.little_utopia_real_budget). This reshapes it into the
    ParsedLineItem shape build_budget_intelligence() already accepts —
    no new budget data, no re-parsing, no invented department field.
    Real PDF page provenance is looked up by account code and preserved."""
    from app.data.little_utopia_real_budget import LITTLE_UTOPIA_REAL_BUDGET_LINES
    page_by_code = {code: page for code, _desc, _amt, page in LITTLE_UTOPIA_REAL_BUDGET_LINES}
    line_items = [
        ParsedLineItem(
            description=account.description,
            department=None,
            amount_raw=str(account.amount_usd),
            amount_usd=account.amount_usd,
            currency_code="USD",
            source_row=None,
            source_page=page_by_code.get(account.account_code),
        )
        for account in register
    ]
    return BudgetParseResult(
        filename=SOURCE_PDF_FILENAME,
        currency_code="USD",
        total_budget_raw=MU_GROSS_BUDGET_USD,
        origin_note=(
            f"Parsed from the real Movie Magic budget PDF via "
            f"app.ingestion.budget_parser + app.data.little_utopia_real_budget. "
            f"{RECONCILIATION_NOTE}"
        ),
        line_items=line_items,
    )


@dataclass
class LittleUtopiaState:
    production_id: str
    production_name: str
    jurisdiction_code: str
    gross_budget_usd: float
    rate: float
    register: list[AccountQualification]
    grey_areas_baseline: list[GreyAreaItem]
    graph: JurisdictionGraph
    package: ProductionPackage
    collection: OpportunityCollection
    composition: CompositionResult
    recommendations: RecommendationSet
    fact_answers: dict = field(default_factory=dict)
    rate_resolution: RateResolution | None = None
    rate_warnings: list[str] = field(default_factory=list)
    legal_engine: LegalEngine = None
    legal_cycle: AcquisitionCycleResult = None
    legal_commit: CommitResult = None
    legal_rerun_before: RerunResult = None
    legal_rerun: RerunResult = None
    # Real-budget reconciliation (see app.data.little_utopia_real_budget):
    # the source PDF's own stated Grand Total vs. the sum of its 44 parsed
    # leaf accounts, and the accepted $2 source-document rounding variance
    # between them — preserved and served, never hidden or balanced away.
    budget_authoritative_gross_usd: float = AUTHORITATIVE_GROSS_BUDGET_USD
    budget_leaf_account_sum_usd: float = LEAF_ACCOUNT_SUM_USD
    budget_reconciliation_variance_usd: float = RECONCILIATION_VARIANCE_USD
    budget_reconciliation_note: str = RECONCILIATION_NOTE
    # Part 4: physical production requirements derived from the REAL
    # budget's own account descriptions (no screenplay text exists — see
    # module docstring — so this is BUDGET-derived, not script-derived,
    # and disclosed as such) and their match against each composed
    # candidate's known jurisdiction capabilities (jurisdiction_comparison.
    # ALL_PROFILES — existing, not fabricated).
    physical_requirements: dict = field(default_factory=dict)
    territory_physical_match: dict = field(default_factory=dict)

    # Production Structuring Engine (structuring_advisor) output, built from
    # this state's REAL register/facts/rate/people — not demo constants.
    structuring_advisory: object = None

    # Canonical recomputation stamp — the version/time that identifies THIS
    # computed state. computation_version is a deterministic fingerprint of
    # every effective input (facts + people + location overrides +
    # economics controls); computed_at is when this state was actually
    # built. Both are set inside _build_state() at build time, so they
    # change on every real recomputation and stay stable across cache-hit
    # reads — letting downstream consumers distinguish current from stale
    # and confirm they are all showing the same computation version.
    computation_version: str = ""
    computed_at: str = ""


# Effective-input fingerprint: a stable, deterministic hash over every
# input that can change the canonical computation. Used for the
# recomputation version so the same inputs always yield the same version
# and any real input change yields a new one.
def canonical_input_fingerprint() -> dict:
    import hashlib
    import json as _json
    sources = {
        "facts": current_fact_answers(),
        "people": current_people_facts(),
        "locations": current_location_overrides(),
        "economics": current_economics_controls(),
    }
    blob = _json.dumps(sources, sort_keys=True, default=str)
    return {"sources": sources, "sha": hashlib.sha256(blob.encode()).hexdigest()[:16]}


# ── Part 4: physical production requirements -> territory matching ──────────
# The real screenplay, look book, and pitch deck were recovered from
# Google Drive ("THE LITTHE UTOPIA" folder) during the Engine Completion
# phase — script.known now reflects a REAL script, not the earlier
# honest UNKNOWN. Requirements below are read from the actual synopsis,
# director's reflections (look book), and the screenplay's opening
# scenes (Google Drive file "The Little Utopia 1_30_26.pdf" + "THE
# LITTLE UTOPIA LOOK BOOK.pdf") — NOT a full page-by-page script read
# (confidence noted per fact); never fabricated beyond what those
# documents actually say. Cross-checked against the real budget's own
# account spend (3300 SPECIAL EFFECTS & MARINE, 3500 AERIAL/DRONE UNIT)
# for corroboration, not as the sole source anymore.
_MARINE_ACCOUNT_CODE = "3300"
_AERIAL_ACCOUNT_CODE = "3500"

# Script-derived facts (source: synopsis + look book + opening scenes).
# Each carries its own confidence — CONFIRMED (explicit in the read
# material) vs NOT_EVIDENT (absent from what was read; NOT asserted
# false, just unconfirmed — the same "unknown never collapses" discipline
# used throughout this codebase).
SCRIPT_REQUIREMENTS: dict[str, dict] = {
    "marine": {"value": True, "confidence": "CONFIRMED",
               "evidence": "Story opens and centers on a sailing boat ('The Little Utopia') "
                           "sinking at sea; open-water swimming; Mediterranean setting throughout."},
    "open_water_filming": {"value": True, "confidence": "CONFIRMED",
                            "evidence": "EXT. SEA scenes; boat interior/exterior at sea; storm/sinking sequence."},
    "underwater_photography": {"value": None, "confidence": "NOT_EVIDENT",
                                "evidence": "Surface swimming described (character floats, swims); no submerged/"
                                            "underwater cinematography described in the material read."},
    "period": {"value": True, "confidence": "CONFIRMED",
               "evidence": "Dual timeline: 1978 Cornwall (flashback) + 1985 Mediterranean (main story), "
                           "'Inspired by True Events' title card."},
    "night_work": {"value": True, "confidence": "CONFIRMED",
                    "evidence": "EXT. SEA. NIGHT and EXT. BEACH. NIGHT scenes in the screenplay's opening pages."},
    "city": {"value": None, "confidence": "NOT_EVIDENT",
             "evidence": "Setting is boat/open-sea and rural Cornish coast — no urban/city scenes described."},
    "desert": {"value": None, "confidence": "NOT_EVIDENT", "evidence": "Not described anywhere in the material read."},
    "snow": {"value": None, "confidence": "NOT_EVIDENT", "evidence": "Not described anywhere in the material read."},
    "animals": {"value": None, "confidence": "NOT_EVIDENT", "evidence": "Not described in the material read."},
    "vehicles": {"value": None, "confidence": "NOT_EVIDENT",
                 "evidence": "One line of dialogue references a car ('the Fiesta') and other boats being "
                             "traded/stacked — not a vehicle-action-driven production."},
    "crowds": {"value": None, "confidence": "NOT_EVIDENT",
               "evidence": "Small, intimate cast (two couples + family) — no crowd scenes described."},
    "vfx_intensity": {"value": "moderate", "confidence": "CONFIRMED",
                       "evidence": "Real budget VFX department $52,500 + Aerial/Drone $16,215 (modest, not "
                                   "tentpole-scale) — the boat-sinking sequence is the primary VFX/SFX beat."},
}

# Source: full script/synopsis material was NOT exhaustively read
# page-by-page (100+ pages) — this is drawn from the synopsis, director's
# reflections, and the screenplay's opening scenes only. Additional
# script content could surface more requirements; nothing here claims
# completeness beyond what was actually read.
SCRIPT_SOURCE_NOTE = (
    "Google Drive 'THE LITTLE UTOPIA' folder: 'The Little Utopia 1_30_26.pdf' "
    "(screenplay, opening scenes read) and 'THE LITTLE UTOPIA LOOK BOOK.pdf' "
    "(synopsis + director's reflections, read in full). Not a full page-by-"
    "page read of the complete screenplay."
)

# ── Major-location taxonomy (canonical, controlled) ──────────────────────────
# The concise environment taxonomy that materially differentiates
# jurisdiction suitability. Script analysis SEEDS these (mapped from
# SCRIPT_REQUIREMENTS + the read setting evidence, provenance preserved);
# the user may confirm/override each category. Overrides are stored
# separately (never overwriting the script extraction) and resolved into
# an EFFECTIVE value exactly like the fact-answer pattern.
LOCATION_TAXONOMY: dict[str, str] = {
    "beach_coast": "Beach / Coast",
    "marine_open_water": "Marine / Open Water",
    "island_tropical": "Island / Tropical",
    "jungle_rainforest": "Jungle / Rainforest",
    "desert_arid": "Desert / Arid",
    "mountains_alpine": "Mountains / Alpine",
    "snow_arctic": "Snow / Arctic",
    "urban_major_city": "Urban / Major City",
    "small_town_suburban": "Small Town / Suburban",
    "rural_countryside": "Rural / Countryside",
    "forest_woodland": "Forest / Woodland",
    "historic_old_world": "Historic / Old World",
    "studio_stage": "Studio / Stage",
}

# Script-derived seeds: every True value maps to explicit evidence in the
# read material (SCRIPT_REQUIREMENTS / setting facts above). Categories the
# material does not evidence are None ("not evident"), never asserted False.
_LOCATION_SCRIPT_SEED: dict[str, dict] = {
    "beach_coast": {"value": True, "evidence": "EXT. BEACH. NIGHT scenes in the screenplay's opening pages; rural Cornish coast setting (1978 timeline)."},
    "marine_open_water": {"value": True, "evidence": SCRIPT_REQUIREMENTS["marine"]["evidence"]},
    "historic_old_world": {"value": True, "evidence": SCRIPT_REQUIREMENTS["period"]["evidence"]},
    "rural_countryside": {"value": True, "evidence": "Setting is boat/open-sea and rural Cornish coast (city scenes not described)."},
    "urban_major_city": {"value": None, "evidence": SCRIPT_REQUIREMENTS["city"]["evidence"]},
    "desert_arid": {"value": None, "evidence": SCRIPT_REQUIREMENTS["desert"]["evidence"]},
    "snow_arctic": {"value": None, "evidence": SCRIPT_REQUIREMENTS["snow"]["evidence"]},
}
_LOCATION_NOT_EVIDENT = "Not described in the material read."

_location_overrides: dict[str, bool] = {}


def apply_location_overrides(overrides: dict[str, object]) -> None:
    """Record user-confirmed major-location categories. Value True/False
    overrides the script-derived seed for that category; None clears the
    override (the effective value returns to the script seed). Persisted
    in the canonical Production Record store and invalidates the cached
    state so territory matching / recommendations recompute."""
    for slug, value in overrides.items():
        if slug not in LOCATION_TAXONOMY:
            raise ValueError(
                f"'{slug}' is not a major-location category "
                f"({sorted(LOCATION_TAXONOMY)})."
            )
        if value is None:
            _location_overrides.pop(slug, None)
        elif isinstance(value, bool):
            _location_overrides[slug] = value
        else:
            raise ValueError(f"Location category '{slug}' expects true/false/null, got: {value!r}")
    _build_state.cache_clear()


def current_location_overrides() -> dict[str, bool]:
    return dict(_location_overrides)


def _derive_location_categories() -> dict[str, dict]:
    """Effective major-location categories: script seed overridden by any
    user-confirmed value. Script extraction is never overwritten — both
    layers are served so provenance stays visible."""
    out: dict[str, dict] = {}
    for slug, label in LOCATION_TAXONOMY.items():
        seed = _LOCATION_SCRIPT_SEED.get(slug, {"value": None, "evidence": _LOCATION_NOT_EVIDENT})
        override = _location_overrides.get(slug)
        effective = override if override is not None else bool(seed["value"])
        out[slug] = {
            "label": label,
            "script_value": seed["value"],
            "evidence": seed["evidence"],
            "override": override,
            "effective": effective,
            "source": "user_override" if override is not None else "script_analysis",
        }
    return out


def _derive_physical_requirements(register: list[AccountQualification]) -> dict:
    by_code = {a.account_code: a.amount_usd for a in register}
    marine_usd = by_code.get(_MARINE_ACCOUNT_CODE, 0.0)
    aerial_usd = by_code.get(_AERIAL_ACCOUNT_CODE, 0.0)
    script_marine = SCRIPT_REQUIREMENTS["marine"]["value"]
    location_categories = _derive_location_categories()
    marine_cat = location_categories["marine_open_water"]
    # User override on the marine category takes precedence over both the
    # script seed and the budget corroboration (a user-confirmed fact wins,
    # exactly like every other fact answer); otherwise script OR budget.
    marine_required = (
        marine_cat["override"]
        if marine_cat["override"] is not None
        else bool(script_marine) or marine_usd > 0
    )
    return {
        "source": "script_and_real_budget_account_spend",
        "source_note": (
            "The real screenplay/synopsis/look book have been recovered (see "
            "SCRIPT_SOURCE_NOTE) and corroborate the real budget's own account "
            "spend on marine (3300) and aerial (3500) departments."
        ),
        "script_requirements": SCRIPT_REQUIREMENTS,
        "script_source": SCRIPT_SOURCE_NOTE,
        "location_categories": location_categories,
        "marine_required": marine_required,
        "marine_spend_usd": marine_usd,
        "marine_account": f"{_MARINE_ACCOUNT_CODE} SPECIAL EFFECTS & MARINE",
        "aerial_required": aerial_usd > 0,
        "aerial_spend_usd": aerial_usd,
        "aerial_account": f"{_AERIAL_ACCOUNT_CODE} AERIAL/DRONE UNIT",
    }


def _match_territory_physical(requirements: dict, composition: CompositionResult) -> dict:
    """For each composed candidate, check its participating jurisdictions
    against jurisdiction_comparison.ALL_PROFILES's EXISTING marine/aerial-
    relevant capability data (marine_suitability, has_water_tanks,
    has_open_water_filming, vessel_marine_qualifies) — never invented
    capability data; a jurisdiction absent from ALL_PROFILES is reported
    as NO_PROFILE, not assumed either way."""
    if not requirements.get("marine_required"):
        return {}
    match: dict[str, dict] = {}
    for candidate in composition.candidates:
        codes = candidate.participating_jurisdictions
        entries = []
        for code in codes:
            profile = jc.ALL_PROFILES.get(code)
            if profile is None:
                entries.append({"jurisdiction_code": code, "status": "NO_PROFILE"})
                continue
            weak = profile.marine_suitability in (jc.MarineSuitability.LIMITED, jc.MarineSuitability.NONE)
            entries.append({
                "jurisdiction_code": code,
                "marine_suitability": profile.marine_suitability,
                "has_water_tanks": profile.has_water_tanks,
                "has_open_water_filming": profile.has_open_water_filming,
                "vessel_marine_qualifies": profile.vessel_marine_qualifies,
                "status": "WEAK_MARINE_MATCH" if weak else "MATCH",
            })
        match[candidate.candidate_id] = {
            "participating_jurisdictions": list(codes),
            "jurisdictions": entries,
            "any_weak_or_missing": any(e["status"] != "MATCH" for e in entries),
        }
    return match


def _build_structuring_advisory(register, facts, rate, gross_budget_usd, inkind_fmv_usd):
    """Production Structuring Engine, driven by THIS production's real data.

    Derives structuring_advisor's inputs from the live register/facts/rate
    instead of the demo constants baked into LittleUtopiaParams. Only signals
    that are genuinely present in the real data are populated; everything else
    is left at 0 so the corresponding recommendation is skipped (never
    fabricated). For a different production with a different register this
    yields a different advisory — that is the generalization.
    """
    from app.calculators.structuring_advisor import LittleUtopiaParams, build_structuring_advisory

    def _acct_sum(predicate) -> float:
        return round(sum(a.amount_usd for a in register if predicate(a)), 2)

    outside = set(facts.accounts_outside_jurisdiction or ())
    # Routable offshore spend: accounts currently incurred OUTSIDE the
    # jurisdiction that an SPV could route through the local entity.
    routable_offshore = _acct_sum(lambda a: a.account_code in outside)

    def _is_atl(a) -> bool:
        try:
            return int(str(a.account_code)) < 2000 and str(a.state).endswith("QUALIFIES")
        except (TypeError, ValueError):
            return False
    atl_qualifying = _acct_sum(_is_atl)

    qpe_qualifies = _acct_sum(lambda a: str(a.state).endswith("QUALIFIES"))

    inputs = LittleUtopiaParams(
        gross_budget_usd=gross_budget_usd,
        qpe_conservative_usd=qpe_qualifies,
        qpe_base_usd=qpe_qualifies,
        mu_rebate_rate=rate,
        production_title=PRODUCTION_NAME,
        jurisdiction_code=JURISDICTION_CODE,
        # Real signals derived from THIS register; 0 => recommendation skipped.
        frogsquad_usd=routable_offshore,
        atl_qualifying_usd=atl_qualifying,
        inkind_base_usd=round(inkind_fmv_usd or 0.0, 2),
        # Not cleanly derivable from the register without fabrication -> skip.
        hod_accom_usd=0.0,
        local_perdiem_usd=0.0,
        marine_expansion_usd=0.0,
        local_crew_expansion_usd=0.0,
        music_recording_usd=0.0,
    )
    return build_structuring_advisory(inputs)


def get_state() -> LittleUtopiaState:
    """Current state under the current fact answers. Cached per
    fact-state; apply_fact_answers()/reset_fact_answers()/
    apply_people_facts() invalidate."""
    people_key = tuple(sorted(
        (role, o.nationality, o.residency) for role, o in _people_overrides.items()
    ))
    return _build_state(tuple(sorted(_fact_answers.items())), people_key)


@lru_cache(maxsize=8)
def _build_state(_fact_key: tuple, _people_key: tuple = ()) -> LittleUtopiaState:
    facts = _production_facts()
    graph_default = build_jurisdiction_graph(mu_rate=MU_RATE)  # facts-independent world model

    # Facts -> derived qualification register (Seam A+B), from the REAL
    # parsed production budget (app.data.little_utopia_real_budget) — the
    # sanitized fixture no longer contributes to the primary register.
    register = build_little_utopia_real_register(mu_rate=MU_RATE, facts=facts)
    grey_areas = build_little_utopia_real_grey_areas()
    graph = build_jurisdiction_graph(mu_rate=MU_RATE, register=register)

    # Permanent rate-authority rules (app.data.program_rate_rules): the
    # rate is resolved from the statutory rate database against the
    # DERIVED qualifying spend — never from the budget document's own
    # rebate line (Rules 1-3). Conflicts are reported, never absorbed
    # (Rule 5). A divergence between the resolver and the MU_RATE
    # constant used to build the register is a warning, not silence.
    _verified_qpe = sum(
        a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
    )
    rate_resolution = resolve_program_rate(
        "mu_edb_incentive", production_type=MU_PRODUCTION_TYPE, qpe_usd=_verified_qpe,
    )
    rate_warnings: list[str] = []
    if rate_resolution is None:
        rate_warnings.append(
            "No statutory rate rule found for mu_edb_incentive — MU_RATE constant "
            "is running without database backing."
        )
    elif abs(rate_resolution.modeled_rate - MU_RATE) > 1e-9:
        rate_warnings.append(
            f"Statutory rate database resolves {rate_resolution.modeled_rate:.0%} "
            f"but the pipeline is built at {MU_RATE:.0%} — reconcile before "
            "trusting incentive figures."
        )

    budget_parse = _register_to_budget_parse_result(register)
    # People: the real, verified writer/director/lead-cast facts (Part 2)
    # — see app.data.little_utopia_people for provenance (reused from
    # tests/validate_little_utopia_v2.py, never fabricated here). Producer
    # has no verified source anywhere in this codebase and is left
    # UNKNOWN so the Question Engine asks for it. No screenplay/entity/
    # location intake exists — those stay honestly UNKNOWN.
    people = build_little_utopia_people(_people_overrides)
    # Part 4 (script integration): the real screenplay/synopsis/look book
    # were recovered from Google Drive this phase. No full parsed
    # ScreenplayParseResult exists (script.known stays honestly False —
    # this was a synopsis + opening-scenes + look-book read, not a full
    # page-by-page parse), but the CONFIRMED facts from that real content
    # are supplied via known_attributes — every key left out (underwater,
    # stunt_intensity, etc.) stays honestly UNKNOWN rather than guessed.
    # See SCRIPT_REQUIREMENTS/SCRIPT_SOURCE_NOTE for the full fact list
    # and evidence, including the NOT_EVIDENT ones this dict omits.
    package = build_production_package(
        production_id=PRODUCTION_ID,
        budget_parse_result=budget_parse,
        people=people,
        script_known_attributes={
            "marine_usage": "true",
            "period": "true",
            "period_classification": "historical",
            "countries": "GB, TR",
            "setting": "Mediterranean Sea, Cornwall (UK), Turkey",
            "language": "English",
            "source_material": "novel",
            "vfx_intensity": "moderate",
        },
    )
    # Seam B: an answered fact resolves its question — the answer is now
    # an engine input above, so the question is no longer open.
    answered_question_ids = {
        spec["answers_question"]
        for key, spec in ANSWERABLE_FACTS.items()
        if key in _fact_answers and spec["answers_question"]
    }
    if answered_question_ids:
        package = dataclasses.replace(
            package,
            missing_inputs=tuple(
                m for m in package.missing_inputs if m.identifier not in answered_question_ids
            ),
        )

    # HINT-MOVABLE-SPEND is production_package_intelligence.py's own
    # already-computed figure for routable (VFX/music/sound/post/creative
    # fee) spend not physically tied to the shoot location — reused
    # as-is, not recomputed, so opportunity discovery's relocation
    # candidates can price a real jurisdiction-specific upside instead
    # of leaving it uncomputed.
    movable_hint = next(
        (h for h in package.budget.opportunity_hints if h.category == "movable_spend"), None,
    )
    movable_spend_usd = movable_hint.amount_usd if movable_hint else None

    # ── PRIMARY PRODUCTION PIPELINE — authoritative data only ──────────
    # Everything served as primary production state (register, discovery,
    # composition, recommendations, scenarios) is computed from the RAW
    # statutory register and pristine grey areas. The MockConnector legal
    # cycle below runs over ITS OWN copies and feeds only the legal_*
    # research fields — mock/demo research must never alter the primary
    # production calculations. (This restores the separation that existed
    # before commit dee6c2b, whose "Seam C" rewiring let a MockConnector
    # resolution silently add $113,000 to served QPE — the confirmed
    # mock-contamination regression.)

    collection = discover_all_opportunities(
        baseline_jurisdiction=JURISDICTION_CODE, mu_rate=MU_RATE, graph=graph,
        movable_spend_usd=movable_spend_usd,
        register=register, grey_areas=grey_areas,
    )

    # Seam B: an elected treaty partner is an engine input to structure
    # composition (an extra jurisdiction set), not a display string.
    extra_sets: list[tuple[str, ...]] = []
    if facts.treaty_partner_code:
        extra_sets.append((JURISDICTION_CODE, facts.treaty_partner_code))

    # Financing defaults to ZERO across the optimizer too (Part 2): pass
    # delay_weeks=0 / bridge_rate=0 so build_risk_cases never silently
    # applies the old 8%/39-week assumption. Financing is modeled only in
    # the /economics headline (mauritius_economics), and only from explicit
    # user input.
    composition = compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=grey_areas,
        extra_jurisdiction_sets=extra_sets or None,
        delay_weeks=0, bridge_rate=0.0,
    )
    # Part 3: cultural-test relevance mapping — driven entirely by the
    # jurisdictions this package actually knows about from REAL person
    # nationalities (never a hardcoded test list), and the exact
    # per-role, per-test weight each test's own rule table assigns.
    relevant_cultural_test_slugs = production_package_to_relevant_cultural_test_slugs(package)
    cultural_test_inputs = production_package_to_cultural_test_inputs(package)
    # Part 3 (threshold qualification): hard eligibility gates, evaluated
    # BEFORE any cultural-test points scoring, from the same real people
    # facts — never a second source of truth.
    role_known_codes = _merge_override_role_codes(
        production_package_to_role_known_codes(package)
    )
    recommendations = generate_production_recommendations(
        collection, composition_result=composition, register=register, rate=MU_RATE,
        jurisdiction_code=JURISDICTION_CODE,
        relevant_cultural_test_slugs=relevant_cultural_test_slugs,
        cultural_test_inputs=cultural_test_inputs,
        role_known_codes=role_known_codes,
        treaty_partner_code=facts.treaty_partner_code,
    )

    # ── LEGAL / RESEARCH VIEW — explicitly labeled, mock-sourced ───────
    # One acquisition cycle through the sole shipped connector
    # (MockConnector — every excerpt self-labels "MOCK CONNECTOR — no
    # live retrieval performed"). It operates on its OWN fresh copy of
    # the grey areas and feeds ONLY the legal_* fields consumed by
    # /legal — never the primary register/composition above.
    legal_grey_areas = build_little_utopia_real_grey_areas()
    legal_engine = LegalEngine(connectors={
        ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE),
    })
    # Baseline rerun BEFORE any resolution — a fresh LegalEngine over a
    # fresh copy of the grey areas, so the "before" figure reflects zero
    # commits, exactly like any other direct build_risk_cases() caller.
    legal_rerun_before = LegalEngine().rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=build_little_utopia_real_grey_areas(), graph=graph_default,
        jurisdiction_code=JURISDICTION_CODE,
    )

    legal_cycle = legal_engine.run_acquisition_cycle(AS_OF_DATE, grey_areas=legal_grey_areas, graph=graph_default)

    # Part 5: GA-INKIND-FMV is a GENUINE grey (producer election + missing
    # documentation + EDB ruling dependency). It is DELIBERATELY NOT
    # auto-resolved here — the acquisition cycle stages it (surfacing the
    # question and its resolution paths) but the demo never mock-verifies,
    # mock-approves, or mock-commits it. Mock evidence must never resolve a
    # genuine grey or alter any headline number. legal_commit stays None;
    # the in-kind grey stays OPEN with its resolution paths exposed on
    # /legal for the producer to actually satisfy.
    legal_commit = None

    legal_rerun = legal_engine.rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=legal_grey_areas, graph=graph_default, jurisdiction_code=JURISDICTION_CODE,
        as_of_date=AS_OF_DATE,
    )

    physical_requirements = _derive_physical_requirements(register)
    territory_physical_match = _match_territory_physical(physical_requirements, composition)

    # Production Structuring Engine — connected live, driven by the real
    # register/facts/rate above (not demo constants). The in-kind FMV is the
    # production's real off-budget post figure (economics control default).
    structuring_advisory = _build_structuring_advisory(
        register=register, facts=facts, rate=MU_RATE,
        gross_budget_usd=MU_GROSS_BUDGET_USD, inkind_fmv_usd=625_000.0,
    )

    # Canonical recomputation stamp — computed here, at build time, so it
    # marks THIS recomputation and updates whenever the cache is cleared
    # and rebuilt (every real input change).
    from datetime import datetime, timezone
    _fingerprint = canonical_input_fingerprint()

    return LittleUtopiaState(
        production_id=PRODUCTION_ID,
        production_name=PRODUCTION_NAME,
        computation_version=_fingerprint["sha"],
        computed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        jurisdiction_code=JURISDICTION_CODE,
        gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE,
        register=register,
        grey_areas_baseline=grey_areas,
        graph=graph,
        package=package,
        collection=collection,
        composition=composition,
        recommendations=recommendations,
        rate_resolution=rate_resolution,
        rate_warnings=rate_warnings,
        fact_answers=current_fact_answers(),
        legal_engine=legal_engine,
        legal_cycle=legal_cycle,
        legal_commit=legal_commit,
        legal_rerun_before=legal_rerun_before,
        legal_rerun=legal_rerun,
        physical_requirements=physical_requirements,
        territory_physical_match=territory_physical_match,
        structuring_advisory=structuring_advisory,
    )
