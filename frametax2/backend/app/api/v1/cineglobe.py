"""
cineglobe.py

Phase 8A API surface for the current (Phase 4-8) CineGlobe engines.
Deliberately bypasses the legacy stack `optimization.py` still calls
(structuring_advisor / mediterranean_comparison / generate_structure_
scenarios / rank_production_structures) — every route here calls the
current opportunity_discovery / production_structure_composer /
production_recommendation_engine / legal_engine directly, or the
ui_presentation.py adapters over their output.

No business logic lives in this file. Every route:
  1. reads the single cached LittleUtopiaState (app.demo.little_utopia_state),
  2. optionally reshapes via dataclasses.asdict() / ui_presentation.py, and
  3. returns.

No route computes a number, applies a threshold, or makes a
qualification/legal determination — those all happened already, inside
the engines, before this file ever runs.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.models.project_person import ProjectPerson
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.project_fact import ProjectFact
from app.models.talent import TalentProfile
from app.models.enums import ProjectFactSourceType
from app.data.little_utopia_people import PersonOverride, primary_person_name

from app.calculators.optimization_engine import RiskCase
from app.calculators.production_constraint_engine import (
    ConstraintKind,
    ProductionConstraint,
    build_constraint_set,
    filter_candidates_by_constraints,
)
from app.calculators.production_recommendation_engine import RecommendationCategory
from app.calculators.production_scenario_engine import ProductionScenario, ScenarioKind, run_scenario
from app.calculators.qualification_model import is_authoritative_citation
from app.calculators.ui_presentation import (
    attribute_fact_to_display,
    case_dict_to_display,
    evidence_chain_to_display,
    group_recommendations_by_category,
)
from app.demo.little_utopia_state import (
    ANSWERABLE_FACTS,
    SPV_PRODUCTION_STRUCTURE_DEFAULT,
    apply_economics_controls,
    apply_fact_answers,
    apply_location_overrides,
    apply_people_facts,
    build_financing_model,
    build_inkind_model,
    build_normalized_structures,
    current_contingency_state,
    current_economics_controls,
    current_fact_answers,
    current_people_facts,
    deploy_contingency,
    get_awarded_rate,
    get_state,
    hydrate_location_overrides,
    hydrate_people_overrides,
    reset_contingency_allocations,
    LOCATION_TAXONOMY,
    PRODUCTION_NAME,
)
from app.calculators.mauritius_economics import compute_mauritius_economics
from app.calculators.qualification_model import QualificationState

router = APIRouter(prefix="/cineglobe", tags=["cineglobe"])


# ── Project Library Phase C closeout: persisted source of truth ─────────────
# People (writer/director/producer-primary nationality/residency/name) and
# location-category overrides now live in Postgres (ProjectPerson +
# TalentProfile; ProjectLocationRequirement.category_key/override) instead
# of only the process-local dicts little_utopia_state.py already reads for
# engine computation. Rather than rebuild the engine's read/derive paths,
# each request re-hydrates those existing in-memory stores from Postgres
# before calling get_state() — the engine's own override-application logic
# (apply_people_facts / apply_location_overrides / build_little_utopia_
# people / _derive_location_categories) is completely unchanged. Slot
# roles with no persisted row yet (lead_cast_2/3, dop, editor, composer)
# and cast (genuinely unknown) still serve/write purely from the demo
# module — an explicit, minimal, documented fallback, not a silent gap.

async def _get_project(db: AsyncSession) -> Project | None:
    return (
        await db.execute(select(Project).where(Project.title == PRODUCTION_NAME))
    ).scalar_one_or_none()


async def _hydrate_people_from_db(db: AsyncSession, project: Project) -> None:
    """Load the writer/director/producer-primary TalentProfile rows for
    this project and feed them into the in-memory override store as
    PersonOverrides, so build_little_utopia_people() reflects Postgres
    truth for this request (and after a restart) without any change to
    how it merges an override."""
    rows = (
        await db.execute(
            select(ProjectPerson, TalentProfile)
            .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
            .where(ProjectPerson.project_id == project.id)
        )
    ).all()
    overrides: dict[str, PersonOverride] = {}
    for role_key in ("writer", "director", "producer"):
        primary_name = primary_person_name(role_key)
        match = next(
            (tp for pp, tp in rows if pp.role == role_key and tp.name == primary_name),
            None,
        )
        if match is None:
            continue
        residency = None
        if match.known_residencies:
            first = match.known_residencies[0]
            residency = first.get("jurisdiction_code") if isinstance(first, dict) else None
        overrides[role_key] = PersonOverride(
            nationality=match.primary_nationality, residency=residency, name=match.name,
        )
    hydrate_people_overrides(overrides)


async def _hydrate_locations_from_db(db: AsyncSession, project: Project) -> None:
    """Load category-keyed override rows for this project and feed them
    into the in-memory override store, so _derive_location_categories()
    reflects Postgres truth for this request (and after a restart)
    without any change to how it merges an override."""
    rows = (
        await db.execute(
            select(ProjectLocationRequirement).where(
                ProjectLocationRequirement.project_id == project.id,
                ProjectLocationRequirement.category_key.isnot(None),
            )
        )
    ).scalars().all()
    overrides = {r.category_key: r.override for r in rows if r.override is not None}
    hydrate_location_overrides(overrides)


# ── Production facts (Engine Integration Phase 1, Seam B) ───────────────────
# Question Engine answers become engine inputs: an answered fact feeds
# qualification derivation / structure composition and resolves the
# corresponding missing-input question. No route below computes anything —
# apply_fact_answers() invalidates the cached state and the engines
# recompute on the next get_state().

@router.get("/facts")
async def get_facts() -> dict[str, Any]:
    return {
        "answers": current_fact_answers(),
        "answerable": {
            key: {
                "type": spec["type"].__name__,
                "answers_question": spec["answers_question"],
                "description": spec["description"],
            }
            for key, spec in ANSWERABLE_FACTS.items()
        },
    }


class FactAnswers(BaseModel):
    answers: dict[str, Any]


# ── Contingency (Task 91) ────────────────────────────────────────────────────
# Undeployed contingency is excluded from QPE by default (canonical rule,
# qualification_derivation.py step 5.5). A producer explicitly DEPLOYS
# part or all of a contingency line to a real destination budget line;
# the deployed amount then inherits the RECEIVING line's own eligibility
# treatment. No blanket "qualify contingency" toggle exists anywhere in
# this surface — every dollar's fate is either the untouched
# per-program contingency rule (undeployed remainder) or the untouched
# per-program rule for the producer-chosen destination category
# (deployed amount).

def _contingency_dict() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for code, alloc in current_contingency_state().items():
        out[code] = {
            "source_account_code": alloc.source_account_code,
            "source_description": alloc.source_description,
            "original_amount_usd": alloc.original_amount_usd,
            "deployed_amount_usd": alloc.deployed_amount_usd,
            "undeployed_amount_usd": alloc.undeployed_amount_usd,
            "state": alloc.state.value,
            "deployments": [
                {
                    "destination_account_code": d.destination_account_code,
                    "destination_description": d.destination_description,
                    "destination_spend_category": d.destination_spend_category,
                    "amount_usd": d.amount_usd,
                    "note": d.note,
                    "deployed_by": d.deployed_by,
                    "deployed_at": d.deployed_at,
                }
                for d in alloc.deployments
            ],
        }
    return out


@router.get("/contingency")
async def get_contingency() -> dict[str, Any]:
    return {"allocations": _contingency_dict()}


class ContingencyDeploymentRequest(BaseModel):
    source_account_code: str
    destination_account_code: str
    destination_description: str
    destination_spend_category: str
    amount_usd: float
    note: str
    deployed_by: str = "producer"


@router.post("/contingency/deploy")
async def post_contingency_deploy(body: ContingencyDeploymentRequest) -> dict[str, Any]:
    try:
        deploy_contingency(
            source_account_code=body.source_account_code,
            destination_account_code=body.destination_account_code,
            destination_description=body.destination_description,
            destination_spend_category=body.destination_spend_category,
            amount_usd=body.amount_usd,
            note=body.note,
            deployed_by=body.deployed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"allocations": _contingency_dict()}


@router.post("/contingency/reset")
async def post_contingency_reset() -> dict[str, Any]:
    reset_contingency_allocations()
    return {"allocations": _contingency_dict()}


@router.post("/facts")
async def post_facts(body: FactAnswers) -> dict[str, Any]:
    try:
        apply_fact_answers(body.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    s = get_state()
    conservative = next(
        (c for c in s.composition.candidates if c.is_fully_priced), None,
    )
    return {
        "answers": current_fact_answers(),
        "open_questions": len(s.package.missing_inputs),
        "conservative_qpe_usd": (
            conservative.cases[RiskCase.CONSERVATIVE].qpe_usd if conservative else None
        ),
        "candidate_ids": [c.candidate_id for c in s.composition.candidates],
    }


# ── Screen 1: Production ─────────────────────────────────────────────────────

@router.get("/production")
async def get_production(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    # Phase C: resolve the real persistent Project row backing this demo
    # production, if the one-time migration has run. Never creates a
    # Project here; a missing row just means the migration hasn't run
    # (fields come back null, nothing breaks).
    project_row = await _get_project(db)

    # Phase C closeout: rehydrate the location-category override store
    # from Postgres BEFORE get_state() — this response's own
    # physical_requirements.location_categories, and the cached engine
    # state get_state() builds, both read that in-memory store. Must
    # happen first so a cold-restarted process (or any request that
    # hasn't hit /locations yet) still reflects persisted overrides.
    if project_row is not None:
        await _hydrate_locations_from_db(db, project_row)

    s = get_state()
    rr = s.rate_resolution

    return {
        "production_id": s.production_id,
        "production_name": s.production_name,
        "jurisdiction_code": s.jurisdiction_code,
        "project_id": str(project_row.id) if project_row else None,
        "lifecycle": project_row.lifecycle if project_row else None,
        "leading_structure_id": str(project_row.leading_structure_id) if project_row and project_row.leading_structure_id else None,
        "gross_budget_usd": s.gross_budget_usd,
        "rate": s.rate,
        # Permanent rate-authority rules: the rate's full statutory
        # provenance, condition evaluations, guaranteed floor, and any
        # budget-vs-database conflict (reported, never absorbed).
        "rate_resolution": (
            {
                "modeled_rate": rr.modeled_rate,
                "floor_rate": rr.floor_rate,
                "is_band_ceiling": rr.is_band_ceiling,
                "tier_id": rr.tier_id,
                "basis": rr.basis,
                "conditions": [asdict(c) for c in rr.conditions_evaluated],
                "unverified_claims": [asdict(u) for u in rr.unverified_claims],
                "conflicts": [asdict(c) for c in rr.conflicts],
            }
            if rr is not None else None
        ),
        "rate_warnings": list(s.rate_warnings),
        # Real-budget reconciliation: the source PDF's own stated Grand
        # Total (the controlling gross budget) vs. the sum of its 44
        # parsed leaf accounts, and the accepted source-document rounding
        # variance between them — never hidden, never balanced away.
        "budget_reconciliation": {
            "authoritative_gross_usd": s.budget_authoritative_gross_usd,
            "leaf_account_sum_usd": s.budget_leaf_account_sum_usd,
            "variance_usd": s.budget_reconciliation_variance_usd,
            "note": s.budget_reconciliation_note,
        },
        # Permanent production-structure default — explicit and traceable
        # (local SPV; foreign people/vendors not assumed offshore).
        "production_structure_default": SPV_PRODUCTION_STRUCTURE_DEFAULT,
        # Part 4: physical production requirements derived from the real
        # budget's own account spend (no screenplay text on file — see
        # module docstring) and their match against each candidate's
        # known jurisdiction capabilities.
        "physical_requirements": s.physical_requirements,
        "territory_physical_match": s.territory_physical_match,
        "as_of_date": "2026-07-10",
        # Canonical recomputation stamp — identifies THIS computed state.
        # version is a deterministic fingerprint over every effective input
        # (facts + people + location overrides + economics controls);
        # computed_at is when the state was actually (re)built. Both change
        # on every real input change, letting any consumer confirm it is
        # reading the current computation and not a stale one.
        "computation": {
            "version": s.computation_version,
            "computed_at": s.computed_at,
        },
    }


# ── Production economics (headline: floor / ceiling / in-kind options) ──────

class EconomicsControlsRequest(BaseModel):
    financing_method: str | None = None          # none | rate_time | hard_cost
    financing_source: str | None = None          # user_input | document_input
    financing_annual_rate: float | None = None
    financing_weeks: float | None = None
    financing_amount_pct: float | None = None
    financing_hard_cost_usd: float | None = None
    awarded_rate: float | None = None
    in_kind_post_available: bool | None = None
    in_kind_post_fmv_usd: float | None = None
    in_kind_post_accepted_as_qpe: str | None = None  # unknown | yes | no
    replacement_post_cost_if_lost_usd: float | None = None
    post_location: str | None = None             # mauritius | elsewhere
    # Part 5 — travel normalization
    origin_city: str | None = None                # "LA" | "NYC" | custom
    business_travelers: float | None = None
    economy_travelers: float | None = None
    rotations_per_year: float | None = None
    hotel_nights: float | None = None
    per_diem_days: float | None = None
    travel_pricing_mode: str | None = None         # benchmark_estimate | live_lookup
    budgeted_travel_override_usd: float | None = None
    # Part 7 — FX normalization
    fx_rate_source: str | None = None              # live | historical | user_override
    fx_historical_date: str | None = None          # "YYYY-MM-DD", required for historical
    fx_user_rate: float | None = None
    fx_scenario_delta_pct: float | None = None


def _economics_payload() -> dict[str, Any]:
    s = get_state()
    verified_cash_qpe = round(
        sum(a.amount_usd for a in s.register if a.state == QualificationState.QUALIFIES), 2
    )
    rr = s.rate_resolution
    rate_floor = rr.floor_rate if rr is not None else 0.30
    rate_ceiling = rr.modeled_rate if rr is not None else 0.40
    financing = build_financing_model()
    inkind = build_inkind_model()
    econ = compute_mauritius_economics(
        gross_cash_budget_usd=s.gross_budget_usd,
        verified_cash_qpe_usd=verified_cash_qpe,
        rate_floor=rate_floor,
        rate_ceiling=rate_ceiling,
        financing=financing,
        inkind=inkind,
        awarded_rate=get_awarded_rate(),
    )

    def _case(r) -> dict[str, Any]:
        return {
            "label": r.label,
            "gross_cash_budget_usd": r.gross_cash_budget_usd,
            "off_budget_inkind_usd": r.off_budget_inkind_usd,
            "qpe_usd": r.qpe_usd,
            "incentive_rate": r.incentive_rate,
            "rate_authority_status": r.rate_authority_status,
            "incentive_usd": r.incentive_usd,
            "financing_cost_usd": r.financing_cost_usd,
            "financing_source": r.financing_source,
            "financing_formula": r.financing_formula,
            "net_benefit_usd": r.net_benefit_usd,
            "net_production_cost_usd": r.net_production_cost_usd,
            "economic_production_value_usd": r.economic_production_value_usd,
            "conditions": list(r.conditions),
            "notes": r.notes,
        }

    payload: dict[str, Any] = {
        "production_structure_default": SPV_PRODUCTION_STRUCTURE_DEFAULT,
        "verified_cash_qpe_usd": verified_cash_qpe,
        "verified_floor_case": _case(econ["verified_floor_case"]),
        "potential_ceiling_case": _case(econ["potential_ceiling_case"]),
        "inkind_post_options": {
            k: _case(v) for k, v in econ["inkind_post_options"].items()
        },
        "financing_source": financing.source.value,
        "controls": current_economics_controls(),
    }
    if "user_elected_case" in econ:
        payload["user_elected_case"] = _case(econ["user_elected_case"])
    # Parts 5-7: travel + FX + in-kind layered onto each composed
    # candidate's cash NPC — a SEPARATE, explicitly-labeled ranking; never
    # blended into the primary /structures ranking above.
    payload["normalized_structures"] = build_normalized_structures(s)
    # Part 7: engine-side current/1M/6M/12M FX data (no UI built here —
    # this is what a future UI would render). None for any horizon this
    # session's sourced fetches didn't cover (e.g. MUR beyond current).
    from app.calculators.production_normalization import fx_rate_snapshot, _JURISDICTION_CURRENCY
    # Workspace's FX strip needs a rate lookup for whichever jurisdiction is
    # currently Leading (client-side selection state, not known to the
    # backend) — so this serves every currency the engine has a real
    # jurisdiction mapping for, not just the fixed EUR/CAD/GBP trio. Any
    # currency with no FX_RATE_SNAPSHOTS entry still returns cleanly (every
    # horizon None) via fx_rate_snapshot's own honest-unavailable path.
    fx_codes = sorted({"MUR", "EUR", "GBP", "CAD"} | set(_JURISDICTION_CURRENCY.values()))
    payload["fx_horizons"] = {c: fx_rate_snapshot(c) for c in fx_codes}
    # jurisdiction_code -> currency_code, real ISO identity only (see
    # _JURISDICTION_CURRENCY's own docstring) — lets the frontend resolve
    # "the current Leading Structure's local currency" without duplicating
    # this mapping client-side.
    payload["jurisdiction_currency"] = dict(_JURISDICTION_CURRENCY)
    # Executable Jurisdiction Knowledge: real QPE/incentive/NPC/travel/FX
    # for every jurisdiction with classified doctrine + rate rules on
    # file; every other cataloged jurisdiction is excluded, not priced at
    # a guessed rate.
    from app.demo.little_utopia_state import (
        build_alternative_jurisdiction_comparisons, build_available_funds,
    )
    payload["alternative_jurisdictions"] = build_alternative_jurisdiction_comparisons(s)
    payload["available_funds"] = build_available_funds()
    # Production Structuring Engine (structuring_advisor) — connected live,
    # driven by the real register/facts/rate. Each recommendation keeps its
    # full explainability (authority/support/evidence/risk/reasoning);
    # routing_decisions is the "what work happens where" allocation seed.
    payload["structuring_advisory"] = _serialize_structuring_advisory(s.structuring_advisory)
    return payload


def _serialize_structuring_advisory(adv: Any) -> Optional[dict[str, Any]]:
    """Serialize StructuringAdvisoryResult to plain JSON, preserving every
    explainability field. Enums -> their .value."""
    if adv is None:
        return None
    return {
        "production_title": adv.production_title,
        "jurisdiction_code": adv.jurisdiction_code,
        "program_rate": adv.program_rate,
        "advisor_version": adv.advisor_version,
        "total_immediate_rebate_uplift": adv.total_immediate_rebate_uplift,
        "total_medium_term_rebate_uplift": adv.total_medium_term_rebate_uplift,
        "total_edb_conditional_rebate_uplift": adv.total_edb_conditional_rebate_uplift,
        "total_potential_rebate_uplift": adv.total_potential_rebate_uplift,
        "unknown_items": list(adv.unknown_items),
        "edb_questions": list(adv.edb_questions),
        "routing_decisions": list(adv.routing_decisions),
        "recommendations": [
            {
                "recommendation_id": r.recommendation_id,
                "title": r.title,
                "time_horizon": r.time_horizon.value,
                "transaction_type": r.transaction_type.value,
                "current_structure": r.current_structure,
                "suggested_structure": r.suggested_structure,
                "reason": r.reason,
                "financial_impact_usd": r.financial_impact_usd,
                "qualification_impact_usd": r.qualification_impact_usd,
                "rebate_impact_usd": r.rebate_impact_usd,
                "required_documentation": list(r.required_documentation),
                "audit_risk": r.audit_risk.value,
                "confidence": r.confidence.value,
                "implementation_difficulty": r.implementation_difficulty.value,
                "published_support": r.published_support,
                "requires_official_interpretation": r.requires_official_interpretation,
                "interpretation_body": r.interpretation_body,
                "interpretation_question": r.interpretation_question,
                "notes": r.notes,
            }
            for r in adv.recommendations
        ],
    }


@router.get("/economics")
async def get_economics() -> dict[str, Any]:
    return _economics_payload()


@router.post("/economics/controls")
async def post_economics_controls(body: EconomicsControlsRequest) -> dict[str, Any]:
    try:
        apply_economics_controls(body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _economics_payload()


# ── People (Part 2) ──────────────────────────────────────────────────────────

class PeopleAnswers(BaseModel):
    answers: dict[str, Any]


_DB_BACKED_PEOPLE_ROLES: tuple[str, ...] = ("writer", "director", "producer")


async def _resolve_primary_talent(db: AsyncSession, project: Project, role: str) -> TalentProfile | None:
    """The persisted TalentProfile row for a role's PRIMARY person (see
    little_utopia_people.primary_person_name — matches idx==0, the only
    person an override in this role currently applies to). Writer/director
    have exactly one row; producer has two, disambiguated by matching the
    verified original name. Known, narrow limitation (documented, not
    fixed, per Phase C closeout scope): renaming the primary producer via
    a `producer_name` write breaks this name-based match on a SUBSEQUENT
    request, since the lookup key is the original verified name, not
    whatever it was most recently renamed to."""
    primary_name = primary_person_name(role)
    if primary_name is None:
        return None
    rows = (
        await db.execute(
            select(TalentProfile)
            .join(ProjectPerson, ProjectPerson.talent_id == TalentProfile.id)
            .where(ProjectPerson.project_id == project.id, ProjectPerson.role == role)
        )
    ).scalars().all()
    if len(rows) == 1:
        return rows[0]
    return next((tp for tp in rows if tp.name == primary_name), None)


# Maps a DB-backed (role, field_name) people-fact edit to the matching
# ProjectFact.fact_key migrated by 0063 — the SAME edit updates both the
# live TalentProfile row (what /people and the engine read) and the fact's
# audit-trail row (what a future Facts/Record UI reads), never two
# independently-writable copies. Residency has no matching migrated fact
# key (0063 never migrated a residency fact) — a residency edit updates
# TalentProfile only, which is correct, not a gap.
_PERSON_FIELD_TO_FACT_KEY: dict[tuple[str, str], str] = {
    ("writer", "name"): "writer_name",
    ("writer", "nationality"): "writer_nationality",
    ("director", "name"): "director_name",
    ("director", "nationality"): "director_nationality",
    ("producer", "name"): "producer_1_name",
    ("producer", "nationality"): "producer_1_nationality",
}


async def _persist_person_field(db: AsyncSession, project: Project, role: str, field_name: str, value: object) -> None:
    """Write-through for the subset of people-fact edits backed by a real
    TalentProfile row (writer, director, producer-primary). Slot roles
    (lead_cast_2/3, dop, editor, composer) and non-primary producers have
    no persisted row and are intentionally left to the existing in-memory-
    only fallback — an explicit, minimal, documented gap, not silent."""
    if role not in _DB_BACKED_PEOPLE_ROLES:
        return
    talent = await _resolve_primary_talent(db, project, role)
    if talent is None:
        return
    if field_name == "name":
        talent.name = value
    elif field_name == "nationality":
        talent.primary_nationality = value
    elif field_name == "residency":
        talent.known_residencies = [{"jurisdiction_code": value, "confirmed": True}] if value else []

    fact_key = _PERSON_FIELD_TO_FACT_KEY.get((role, field_name))
    if fact_key is not None:
        fact = (
            await db.execute(
                select(ProjectFact).where(
                    ProjectFact.project_id == project.id, ProjectFact.fact_key == fact_key,
                )
            )
        ).scalar_one_or_none()
        if fact is not None:
            fact.value = value
            fact.source_type = ProjectFactSourceType.USER_OVERRIDE.value


@router.get("/people")
async def get_people(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await _get_project(db)
    if project is not None:
        await _hydrate_people_from_db(db, project)

    s = get_state()
    pkg = s.package.package

    def _people(role_people) -> list[dict[str, Any]]:
        return [
            {
                "person_id": p.person_id, "name": p.name,
                "nationality": p.nationality.value, "nationality_state": p.nationality.state.value,
                "residency": p.residency.value, "residency_state": p.residency.state.value,
            }
            for p in role_people
        ]

    # Slot roles — user-supplied person facts for roles the discovery
    # pipeline has no person for yet (extra lead-cast slots + the
    # recurring cultural-test creative roles). Served straight from the
    # canonical override store: an empty list means "slot open".
    overrides = current_people_facts()

    def _slot(role: str) -> list[dict[str, Any]]:
        o = overrides.get(role) or {}
        if not (o.get("name") or o.get("nationality")):
            return []
        return [{
            "person_id": f"{role}-1", "name": o.get("name"),
            "nationality": o.get("nationality"),
            "nationality_state": "known" if o.get("nationality") else "unknown",
            "residency": o.get("residency"),
            "residency_state": "known" if o.get("residency") else "unknown",
        }]

    return {
        "writers": _people(pkg.writers),
        "directors": _people(pkg.directors),
        "cast": _people(pkg.cast),
        "producers": _people(pkg.producers),
        "lead_cast_2": _slot("lead_cast_2"),
        "lead_cast_3": _slot("lead_cast_3"),
        "dop": _slot("dop"),
        "editor": _slot("editor"),
        "composer": _slot("composer"),
        "overrides": overrides,
        "missing_inputs": [
            m.identifier for m in s.package.missing_inputs
            if "NATIONALITY" in m.identifier or "RESIDENCY" in m.identifier
        ],
    }


@router.post("/people")
async def post_people(body: PeopleAnswers, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        apply_people_facts(body.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Phase C closeout: mirror the DB-backed subset of this write into
    # Postgres so it survives a restart. apply_people_facts() above
    # already validated every key/role/type and applied it to the
    # in-memory store the engine reads — this only adds durability for
    # writer/director/producer-primary; slot roles are unaffected.
    project = await _get_project(db)
    if project is not None:
        for key, value in body.answers.items():
            role, field_name = key.rsplit("_", 1)
            await _persist_person_field(db, project, role, field_name, value)
        await db.commit()

    return await get_people(db)


class LocationOverrides(BaseModel):
    overrides: dict[str, Any]


@router.post("/locations")
async def post_locations(body: LocationOverrides, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Persist user-confirmed major-location categories into the canonical
    Production Record (override layer over the script-derived seeds) and
    invalidate the cached state so territory matching and recommendations
    recompute. Returns the updated effective category set.

    Phase C closeout: also writes each change to Postgres
    (ProjectLocationRequirement.category_key/override) so it survives a
    restart. apply_location_overrides() below remains the single
    validation + engine-recompute path, unchanged; the DB write here is
    purely additive durability alongside it."""
    try:
        apply_location_overrides(body.overrides)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    project = await _get_project(db)
    if project is not None:
        for slug, value in body.overrides.items():
            if slug not in LOCATION_TAXONOMY:
                continue  # already rejected above; defensive only
            row = (
                await db.execute(
                    select(ProjectLocationRequirement).where(
                        ProjectLocationRequirement.project_id == project.id,
                        ProjectLocationRequirement.category_key == slug,
                    )
                )
            ).scalar_one_or_none()
            if value is None:
                if row is not None:
                    row.override = None
                continue
            if row is None:
                row = ProjectLocationRequirement(
                    project_id=project.id,
                    description=LOCATION_TAXONOMY[slug],
                    category_key=slug,
                    override=bool(value),
                )
                db.add(row)
            else:
                row.override = bool(value)
        await db.commit()

    s = get_state()
    return {"location_categories": s.physical_requirements["location_categories"]}


# ── Screen 2: Package Intelligence (Budget / Script / Questions) ────────────

@router.get("/package")
async def get_package() -> dict[str, Any]:
    s = get_state()
    pkg = s.package
    return {
        "production_id": pkg.production_id,
        "confidence": pkg.confidence.value,
        "is_ready_for_downstream_engines": pkg.is_ready_for_downstream_engines,
        "register": [
            {
                "account_code": a.account_code,
                "description": a.description,
                "amount_usd": a.amount_usd,
                "state": a.state.value,
                "confidence": a.confidence.value,
                "authority_basis": a.authority_basis.value,
                "reason": a.reason,
                # Part 4 A-F: why a line is grey (null unless state is grey).
                # The UI's Grey-Area panel renders this as the "why".
                "grey_reason": a.grey_reason.value if a.grey_reason else None,
                "financial_impact_usd": a.financial_impact_usd,
                "structuring_mechanism": a.structuring_mechanism,
                "resolving_evidence": a.resolving_evidence,
                "incentive_upside_usd": a.incentive_upside_usd,
            }
            for a in s.register
        ],
        "budget": {
            "known": pkg.budget.known,
            "filename": pkg.budget.filename,
            "currency_code": pkg.budget.currency_code,
            "total_budget_usd": pkg.budget.total_budget_usd,
            "line_item_count": pkg.budget.line_item_count,
            "atl_total_usd": pkg.budget.atl_total_usd,
            "btl_total_usd": pkg.budget.btl_total_usd,
            "post_total_usd": pkg.budget.post_total_usd,
            "other_total_usd": pkg.budget.other_total_usd,
            "labor_usd": pkg.budget.labor_usd,
            "non_labor_usd": pkg.budget.non_labor_usd,
            "totals_by_spend_category_usd": pkg.budget.totals_by_spend_category_usd,
            "opportunity_hints": [asdict(h) for h in pkg.budget.opportunity_hints],
        },
        "script": {
            "known": pkg.script.known,
            "filename": pkg.script.filename,
            "page_count": pkg.script.page_count,
            "word_count": pkg.script.word_count,
            "locations_mentioned": list(pkg.script.locations_mentioned),
            "character_names": list(pkg.script.character_names),
            "attributes": {k: attribute_fact_to_display(v) for k, v in pkg.script.attributes.items()},
        },
        "package_people_count": len(pkg.package.all_people),
        "package_entities_count": len(pkg.package.all_entities),
        "location_count": len(pkg.location.locations),
        "missing_inputs": [
            {
                "identifier": m.identifier,
                "question": m.question,
                "why_it_matters": m.why_it_matters,
                "downstream_engines": [e.value for e in m.downstream_engines],
                "optimizer_value": m.optimizer_value.value,
                "blocking": m.blocking,
                "discovery_hooks": [asdict(h) for h in m.discovery_hooks],
            }
            for m in pkg.missing_inputs
        ],
    }


# ── Screen 3: Recommendations (Financial / Structural / Creative / Legal) ──

@router.get("/recommendations")
async def get_recommendations() -> dict[str, Any]:
    s = get_state()
    recs = s.recommendations.recommendations
    grouped = group_recommendations_by_category(recs)
    legal_gated = [r for r in recs if r.requires_counsel_approval]

    def _rec_dict(r) -> dict[str, Any]:
        d = asdict(r)
        d["category"] = r.category.value
        d["confidence"] = r.confidence.value
        d["status"] = r.status.value
        return d

    return {
        "total": len(recs),
        "by_category": {
            "financial": [_rec_dict(r) for r in grouped[RecommendationCategory.FINANCIAL.value]],
            "structural": [_rec_dict(r) for r in grouped[RecommendationCategory.STRUCTURAL.value]],
            "creative": [_rec_dict(r) for r in grouped[RecommendationCategory.CREATIVE.value]],
            "required_input": [_rec_dict(r) for r in grouped[RecommendationCategory.REQUIRED_INPUT.value]],
        },
        "legal": [_rec_dict(r) for r in legal_gated],
    }


# ── Screen 4: Scenarios (Structures / Risk cases / Optimizer outputs) ──────

@router.get("/structures")
async def get_structures() -> dict[str, Any]:
    """
    Serves the CANONICAL optimizer output: allocated_structures (the
    account->jurisdiction allocation + multi-register pricing keystone,
    little_utopia_state.build_allocated_structures), whose .ranking the UI
    consumes. `candidates` is the opportunity-discovery composition set,
    retained because the recommendation engine consumes it. The legacy
    top-level `ranking` (global_scenario_ranker STRUCT-* order) was removed:
    it was computed every request but consumed by no screen — the canonical
    ranking is allocated_structures.ranking.
    """
    s = get_state()

    def _candidate_dict(c) -> dict[str, Any]:
        return {
            "candidate_id": c.candidate_id,
            "label": c.label,
            "participating_jurisdictions": list(c.participating_jurisdictions),
            "priceable_pct": c.priceable_pct,
            "unknown_pct": c.unknown_pct,
            "is_fully_priced": c.is_fully_priced,
            "cases": case_dict_to_display(c.cases),
            "informational_upside_usd": c.informational_upside_usd,
            "constraints": [asdict(x) for x in c.constraints],
            "included_opportunity_ids": list(c.included_opportunity_ids),
        }

    from app.demo.little_utopia_state import build_allocated_structures

    return {
        # composition candidates (opportunity discovery) — the input the
        # recommendation engine consumes; retained here for that surface.
        "candidates": [_candidate_dict(c) for c in s.composition.candidates],
        "pruned": s.composition.pruned,
        # Account->jurisdiction allocation surface (production_allocation +
        # allocation_pricing): the CANONICAL served optimizer — per-structure
        # account allocations, per-jurisdiction partial-register segment
        # economics, qualification traces, unresolved conditions, approval
        # dependencies, gated structure recommendations, and the ranking the
        # UI reads (allocated_structures.ranking).
        "allocated_structures": build_allocated_structures(s),
    }


class ScenarioRequest(BaseModel):
    kind: str
    target_jurisdiction: str | None = None


@router.post("/scenarios")
async def post_scenario(body: ScenarioRequest) -> dict[str, Any]:
    s = get_state()
    try:
        kind = ScenarioKind(body.kind)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown scenario kind '{body.kind}'.")

    scenario = ProductionScenario(
        scenario_id=f"API-{kind.value}", kind=kind,
        description=f"{kind.value} (via API)", target_jurisdiction=body.target_jurisdiction,
    )
    result = run_scenario(
        scenario, s.collection, graph=s.graph, register=s.register,
        gross_budget_usd=s.gross_budget_usd, rate=s.rate, grey_areas=s.grey_areas_baseline,
    )
    return {
        "scenario_id": scenario.scenario_id,
        "kind": kind.value,
        "notes": result.notes,
        "baseline_candidate_id": result.baseline_candidate_id,
        "scenario_candidate_id": result.scenario_candidate_id,
        "baseline_risk_adjusted_npc_usd": result.baseline_risk_adjusted_npc_usd,
        "scenario_risk_adjusted_npc_usd": result.scenario_risk_adjusted_npc_usd,
        "delta_usd": result.delta_usd,
        "relevant_structuring_opportunities": [
            {"opportunity_id": o.opportunity_id, "description": o.description, "subtype": o.subtype}
            for o in result.relevant_structuring_opportunities
        ],
    }


@router.get("/constraints/check")
async def check_constraints() -> dict[str, Any]:
    """Demonstrates production_constraint_engine against the real
    composed candidates — jurisdiction_required is the only kind
    checkable without a producer-supplied budget ceiling, so that's what
    this read-only demo route exercises."""
    s = get_state()
    constraints = build_constraint_set([
        ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value=s.jurisdiction_code),
    ])
    compatible, results = filter_candidates_by_constraints(s.composition.candidates, constraints)
    return {
        "compatible_candidate_ids": [c.candidate_id for c in compatible],
        "results": [
            {
                "candidate_id": r.candidate_id,
                "compatible": r.compatible,
                "violated_constraint_ids": list(r.violated_constraint_ids),
                "unverifiable_constraint_ids": list(r.unverifiable_constraint_ids),
            }
            for r in results
        ],
    }


# ── Screen 5: Evidence (Authority / Grey Areas / Evidence Trace) ───────────

@router.get("/legal")
async def get_legal() -> dict[str, Any]:
    s = get_state()

    def _grey_area_dict(g) -> dict[str, Any]:
        return {
            "item_id": g.item_id,
            "account_codes": list(g.account_codes),
            "amount_usd": g.amount_usd,
            "jurisdiction_code": g.jurisdiction_code,
            "authority_to_ask": g.authority_to_ask,
            "resolving_evidence": g.resolving_evidence,
            "status": g.status.value,
            "ruling_citation": g.ruling_citation,
            # Provenance flag: False when the resolution's citation is
            # mock/demo research output (never statutory evidence).
            "citation_is_authoritative": is_authoritative_citation(g.ruling_citation),
            "off_budget": g.off_budget,
            "graph_rule_id": g.graph_rule_id,
            # Part 5: precise classification + concrete producer resolution
            # paths for a genuine grey (never auto-resolved by mock).
            "grey_kinds": list(g.grey_kinds),
            "resolution_paths": list(g.resolution_paths),
        }

    evidence_trace: list[dict[str, Any]] = []
    authority_scores: dict[str, Any] = {}
    if s.legal_commit is not None and s.legal_commit.score is not None:
        chain = s.legal_engine.evidence_graph.trace_rule(s.legal_commit.committed_id)
        evidence_trace = evidence_chain_to_display(chain)
        authority_scores[s.legal_commit.committed_id] = {
            "composite": s.legal_commit.score.composite,
            "confidence": s.legal_commit.score.confidence.value,
            "breakdown": asdict(s.legal_commit.score.breakdown),
        }

    return {
        # RESEARCH VIEW ONLY: everything below reflects the Legal
        # Engine's mock-connector research cycle. It never feeds the
        # primary production register/QPE served by /package and
        # /structures — those are computed from the raw statutory
        # register exclusively.
        "is_research_view": True,
        "grey_areas_current": [_grey_area_dict(g) for g in s.legal_rerun.grey_areas_used],
        "questions_detected": len(s.legal_cycle.questions),
        "questions_auto_executed": list(s.legal_cycle.executed_task_ids),
        "questions_awaiting_verification": list(s.legal_cycle.awaiting_verification),
        "committed_rule_id": s.legal_commit.committed_id if s.legal_commit else None,
        "authority_scores": authority_scores,
        "evidence_trace": evidence_trace,
        "connector_source_label": "MockConnector (no live retrieval — see legal_authority_acquisition.py)",
        "conservative_npc_before_usd": (
            s.legal_rerun_before.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        ),
        "conservative_npc_after_usd": (
            s.legal_rerun.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        ),
    }


# ── Mature UI restoration: ONE project-parameterized combined state ────────
#
# The 8 routes above were built for exactly one production (get_state()'s
# single in-memory LittleUtopiaState) — that architecture is correct and
# unchanged for Little Utopia, whose curated register/legal/economics/
# people intelligence genuinely has no generic equivalent for any other
# project. This route lets ANY project's project_id drive the SAME mature
# component tree (Overview/Workspace/Scenarios/ProjectGlobe/Reports/
# Knowledge): for Little Utopia's own project_id, it returns byte-identical
# data to the 8 routes above (same functions, called directly — zero
# duplication, zero drift risk). For any other project, `production` and
# `structures` come from canonical_production_view.py — the generic,
# canonical-evaluation-backed adapter every project already has real data
# for — and the remaining sections (package/recommendations/legal/
# economics/people/facts), which were never migrated off Little Utopia's
# own hand-curated demo state, return honest empty shapes rather than
# Little Utopia's data or a fabricated substitute.
EMPTY_PKG: dict[str, Any] = {
    "production_id": None, "confidence": "unknown", "is_ready_for_downstream_engines": False,
    "register": [],
    "budget": {
        "known": False, "filename": None, "currency_code": None, "total_budget_usd": None,
        "line_item_count": 0, "atl_total_usd": None, "btl_total_usd": None, "post_total_usd": None,
        "other_total_usd": None, "labor_usd": None, "non_labor_usd": None,
        "totals_by_spend_category_usd": {}, "opportunity_hints": [],
    },
    "script": {
        "known": False, "filename": None, "page_count": None, "word_count": None,
        "locations_mentioned": [], "character_names": [], "attributes": {},
    },
    "package_people_count": 0, "package_entities_count": 0, "location_count": 0,
    "missing_inputs": [],
}
EMPTY_RECOMMENDATIONS: dict[str, Any] = {
    "total": 0,
    "by_category": {"financial": [], "structural": [], "creative": [], "required_input": []},
    "legal": [],
}
EMPTY_LEGAL: dict[str, Any] = {
    "is_research_view": True, "grey_areas_current": [], "questions_detected": 0,
    "questions_auto_executed": [], "questions_awaiting_verification": [],
    "committed_rule_id": None, "authority_scores": {}, "evidence_trace": [],
    "connector_source_label": None, "conservative_npc_before_usd": None, "conservative_npc_after_usd": None,
}
EMPTY_ECONOMICS: dict[str, Any] = {
    "production_structure_default": None, "verified_cash_qpe_usd": None,
    "verified_floor_case": None, "potential_ceiling_case": None, "inkind_post_options": {},
    "financing_source": None, "controls": {}, "normalized_structures": [],
    "fx_horizons": {}, "jurisdiction_currency": {}, "alternative_jurisdictions": [],
    "available_funds": [], "structuring_advisory": None,
}
EMPTY_PEOPLE: dict[str, Any] = {
    "writers": [], "directors": [], "cast": [], "producers": [],
    "lead_cast_2": [], "lead_cast_3": [], "dop": [], "editor": [], "composer": [],
    "overrides": {}, "missing_inputs": [],
}
EMPTY_FACTS: dict[str, Any] = {"answers": {}, "answerable": {}}


@router.get("/projects/{project_id}/state")
async def get_project_state(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    from app.services.canonical_production_view import build_production_and_structures

    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    is_demo_project = project.title == PRODUCTION_NAME
    if is_demo_project:
        # Byte-identical to the 8 individual routes above — same functions,
        # called directly. Never a second implementation of Little Utopia's
        # own served data.
        return {
            "production": await get_production(db),
            "pkg": await get_package(),
            "recommendations": await get_recommendations(),
            "structures": await get_structures(),
            "legal": await get_legal(),
            "economics": await get_economics(),
            "people": await get_people(db),
            "facts": await get_facts(),
        }

    view = await build_production_and_structures(db, project_id)
    if view.get("status") != "OK":
        raise HTTPException(status_code=404, detail=view.get("status", "PROJECT_NOT_FOUND"))
    return {
        "production": view["production"],
        "pkg": EMPTY_PKG,
        "recommendations": EMPTY_RECOMMENDATIONS,
        "structures": view["structures"],
        "legal": EMPTY_LEGAL,
        "economics": EMPTY_ECONOMICS,
        "people": EMPTY_PEOPLE,
        "facts": EMPTY_FACTS,
    }
