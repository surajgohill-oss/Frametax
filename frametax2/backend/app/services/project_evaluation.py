"""
project_evaluation.py

The missing link behind "Begin Evaluation": a generic, project-agnostic
orchestrator that connects a project's already-ingested materials to the
already-existing, already-populated worldwide evaluation engine.

    Project Record
      -> CanonicalProductionState        (SA-1, existing, reused)
      -> ProductionOptimizerInput        (SA-1 handoff, existing, reused)
      -> production_requirements /
         production_discovery            (Phase 6 discovery, existing, reused)
      -> ProductionStructure /
         StructureCalculationResult      (DB-backed structures API, existing,
                                           reused — app/api/v1/structures.py's
                                           calculate_structure_impl and its
                                           underlying run_full_analysis are
                                           called exactly as that route
                                           already calls them)

This module adds NO new economics. It only decides, generically, WHICH
existing structures to generate and calculate for a given project, then
calls the existing generation/calculation code unchanged.

Two things this module intentionally does NOT do, per product policy:

  * MFNI / regional production-cost normalization. `calculate_structure_impl`
    already passes `cost_benchmark=None` (see structures.py's own TODO) —
    every structure here is priced from the production's own nominal,
    unnormalized budget. That limitation is surfaced honestly on every
    result via `extra_warnings`, never silently implied away.
  * Per-line territorial classification. No line in a generically-ingested
    project's budget currently states which jurisdiction it was spent in
    (see CanonicalProductionState's own territorial_basis="UNKNOWN" on
    every line). Every structure therefore uses the SAME jurisdiction_spend_pct
    default `calculate_structure_impl`'s own caller already uses when none
    is supplied (1.0 — the full nominal budget, exactly as a single-location
    production's baseline or a full-relocation candidate already models it
    in the existing dormant structures API). This is not a new assumption;
    it is the pre-existing default of the code being reused.
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.structures import calculate_structure_impl
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import derive_production_requirements
from app.models.budget import BudgetDocument
from app.models.incentive import IncentiveProgram
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_production_state import CanonicalProductionStateBuilder
from app.services.optimizer_handoff import build_optimizer_input

MFNI_LIMITATION_NOTE = (
    "Regional production-cost normalization is not yet applied to this "
    "comparison — figures use this production's own nominal budget "
    "amounts, not jurisdiction-adjusted local costs."
)

#: Generic project.format -> the production_type vocabulary the incentive
#: rate/doctrine registries are keyed on. "feature_film" is the default —
#: not an FVD-specific value, the same default the registries themselves
#: use most broadly (see program_rate_rules.py's own production_types
#: tuples, which name "feature_film" far more than any other token).
_FORMAT_TO_PRODUCTION_TYPE = {
    "feature": "feature_film",
    "series": "tv_series",
    "documentary": "creative_documentary",
    "animation": "animation",
}


def _production_type_for(project: Project) -> str:
    fmt = (project.format or "").lower()
    return _FORMAT_TO_PRODUCTION_TYPE.get(fmt, "feature_film")


async def _derive_home_jurisdiction(session: AsyncSession, project: Project) -> Jurisdiction | None:
    """Generic, deterministic geography derivation from the project's own
    persisted evidence — never fabricated, never project-specific.

    Matches every active Jurisdiction's own name (whole-word, case-
    insensitive) against this project's budget document filenames — the
    same kind of source-evidence match SA-1.5 already treated F#K
    Valentine's Day's Greece basis as established by ("the source budget
    itself, not inferred"), generalized to any project's own budget
    filename rather than encoded as a fact about one project. Only ever
    runs when `project.home_jurisdiction_id` is not already set — never
    overrides a confirmed value.
    """
    if project.home_jurisdiction_id is not None:
        return await session.get(Jurisdiction, project.home_jurisdiction_id)

    docs = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().all()
    filenames = " ".join(d.filename or "" for d in docs)
    if not filenames.strip():
        return None
    # Filenames commonly separate words with "_"/"-"/"." rather than
    # spaces, but those are still \w characters in regex — a plain \b
    # word boundary does not fire between "_" and a letter, so
    # "V-BRAT_V8_Greece_041224" would never match \bGreece\b. Normalize
    # every non-alphanumeric run to a space first so word boundaries land
    # on real word edges regardless of the filename's own punctuation.
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", filenames)

    jurisdictions = (await session.execute(
        select(Jurisdiction).where(Jurisdiction.is_active.is_(True))
    )).scalars().all()
    # Longest name first: "United States" must not be pre-empted by a
    # shorter unrelated match, and a country should not out-match a more
    # specific state/province name also present in the filename.
    for j in sorted(jurisdictions, key=lambda x: len(x.name or ""), reverse=True):
        if not j.name or len(j.name) < 4:
            continue  # too short to word-match safely (e.g. avoid stray 2-letter clashes)
        pattern = r"\b" + re.escape(j.name) + r"\b"
        if re.search(pattern, normalized, re.IGNORECASE):
            return j
    return None


async def _load_program_bundle(session: AsyncSession, jurisdiction_id, program_slug: str) -> dict | None:
    """The same {program, qualifying_categories, uplifts, jurisdiction_spend_pct}
    shape `structures.py::calculate_structure` already builds per claimed
    program — factored out so both call sites stay byte-identical."""
    prog = (await session.execute(
        select(IncentiveProgram).where(
            IncentiveProgram.jurisdiction_id == jurisdiction_id,
            IncentiveProgram.slug == program_slug,
        )
    )).scalars().first()
    if prog is None:
        return None

    from app.models.incentive import QualifyingSpendCategory

    cats = (await session.execute(
        select(QualifyingSpendCategory).where(QualifyingSpendCategory.program_id == prog.id)
    )).scalars().all()
    return {
        "program": {
            "id": str(prog.id),
            "slug": prog.slug,
            "program_type": prog.program_type,
            "base_rate": float(prog.base_rate) if prog.base_rate else None,
            "max_rate": float(prog.max_rate) if prog.max_rate else None,
            "is_refundable": prog.is_refundable,
            "is_transferable": prog.is_transferable,
            "transferable_value_pct": float(prog.transferable_value_pct) if prog.transferable_value_pct else None,
            "is_competitive": prog.is_competitive,
            "annual_cap_local": float(prog.annual_cap_local) if prog.annual_cap_local else None,
            "confidence_tier": prog.confidence_tier,
        },
        "qualifying_categories": [
            {"spend_category": c.spend_category, "qualifies": c.qualifies,
             "jurisdiction_spend_only": c.jurisdiction_spend_only}
            for c in cats
        ],
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
        "program_id": prog.id,
    }


async def begin_evaluation(session: AsyncSession, project_id) -> dict:
    """The full orchestration behind "Begin Evaluation". Idempotent per
    CanonicalProductionState fingerprint: a repeat click against unchanged
    inputs returns the prior run rather than recomputing/duplicating."""
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    state = await CanonicalProductionStateBuilder(session).build(project_id)
    handoff = build_optimizer_input(state)

    if not handoff.accepted:
        blockers = handoff.blockers or ["Incomplete inputs."]
        status = (
            "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"
            if any("BUDGET_MISSING" in b for b in blockers)
            else "BLOCKED_INCOMPLETE_INPUTS"
        )
        return {
            "status": status,
            "blockers": blockers,
            "state_fingerprint": state.input_fingerprint,
        }

    oi = handoff.optimizer_input

    # Idempotency: an existing evaluation run for THIS exact input
    # fingerprint is returned unchanged rather than duplicated.
    existing = (await session.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == state.input_fingerprint,
        )
    )).scalars().all()
    if existing:
        return await _summarize(session, project, state, reused=True)

    home = await _derive_home_jurisdiction(session, project)
    if home is not None and project.home_jurisdiction_id is None:
        project.home_jurisdiction_id = home.id
        await session.flush()

    requirements = derive_production_requirements({})  # honestly empty: SA-1 does not
    # yet populate the environment/infrastructure signal shape this needs.
    production_type = _production_type_for(project)

    discovery = discover_executable_jurisdictions(
        requirements=requirements,
        production_type=production_type,
        # A ceiling, not a qualifying-spend figure: used only to screen
        # which jurisdictions could conceivably clear a minimum-spend
        # gate. The REAL qualifying spend for each priced candidate below
        # comes from run_full_analysis's own category-rule computation
        # against the project's real budget lines.
        qpe_usd=state.gross_budget_usd,
        home_code=(home.code if home is not None else "ZZ"),
    )

    candidate_codes: list[tuple[str, str]] = []
    if home is not None:
        home_prog = next((s for c, s in discovery.accepted if c == home.code), None)
        if home_prog:
            candidate_codes.append((home.code, home_prog))
    candidate_codes.extend(discovery.accepted_alternatives(home.code if home is not None else "ZZ"))

    priced_structure_ids: list[uuid.UUID] = []
    skipped: list[dict] = []

    for code, program_slug in candidate_codes:
        jurisdiction = (await session.execute(
            select(Jurisdiction).where(Jurisdiction.code == code)
        )).scalars().first()
        if jurisdiction is None:
            skipped.append({"jurisdiction_code": code, "reason": "no DB jurisdiction record"})
            continue

        bundle = await _load_program_bundle(session, jurisdiction.id, program_slug)
        if bundle is None:
            skipped.append({"jurisdiction_code": code, "reason": f"no DB program record for {program_slug}"})
            continue

        is_home = home is not None and code == home.code
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=(
                f"{jurisdiction.name} — production's current base"
                if is_home else f"Full relocation to {jurisdiction.name}"
            ),
            description=(
                "The production's own confirmed base jurisdiction, priced as-is."
                if is_home else
                "Whole production relocated; nominal budget unchanged (no regional "
                "cost normalization applied)."
            ),
            jurisdiction_allocations=[{"jurisdiction_id": str(jurisdiction.id), "shoot_pct": 100, "budget_pct": 100}],
            claimed_program_ids=[str(bundle["program_id"])],
            assumed_jurisdiction_spend_pcts={str(bundle["program_id"]): 1.0},
        )
        session.add(structure)
        await session.flush()

        await calculate_structure_impl(
            str(project.id), str(structure.id), session,
            extra_warnings=[MFNI_LIMITATION_NOTE],
            has_unverified_inputs_override=True,
            input_fingerprint=state.input_fingerprint,
        )
        priced_structure_ids.append(structure.id)

    summary = await _summarize(session, project, state, reused=False)
    summary["discovery_examined"] = len(discovery.examinations)
    summary["discovery_rejected"] = discovery.metrics.get("rejected_count", 0)
    summary["discovery_capability_only"] = discovery.metrics.get("capability_only_count", 0)
    summary["skipped_candidates"] = skipped
    return summary


async def _summarize(session: AsyncSession, project: Project, state, *, reused: bool) -> dict:
    """Read back the persisted structures/results for this project and
    rank them by true_net_cost_usd — the same figure the existing
    Analysis panel and structures API already expose. Never recomputes;
    purely a read + rank of what is already in the database."""
    rows = (await session.execute(
        select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == project.id)
        .order_by(StructureCalculationResult.created_at.desc())
    )).all()

    # Keep only the latest result per structure.
    latest_by_structure: dict[uuid.UUID, tuple[ProductionStructure, StructureCalculationResult]] = {}
    for structure, result in rows:
        if structure.id not in latest_by_structure:
            latest_by_structure[structure.id] = (structure, result)

    ranked = sorted(
        latest_by_structure.values(),
        key=lambda pair: (pair[1].true_net_cost_usd if pair[1].true_net_cost_usd is not None else float("inf")),
    )

    baseline_pair = next(
        (pair for pair in ranked if pair[0].description and "confirmed base jurisdiction" in pair[0].description),
        ranked[0] if ranked else None,
    )
    top_pair = ranked[0] if ranked else None

    if top_pair and project.leading_structure_id is None:
        # The lowest-NPC priced structure is the leading one — whether
        # that turns out to be the baseline itself (no relocation beats
        # the production's own base) or an alternative. Never overwrites
        # a human-set leading structure on a re-summarize of an unchanged
        # (idempotent) run.
        project.leading_structure_id = top_pair[0].id
        await session.flush()

    return {
        "status": "EVALUATION_REUSED" if reused else "EVALUATION_COMPLETE",
        "state_fingerprint": state.input_fingerprint,
        "gross_budget_usd": state.gross_budget_usd,
        "priced_count": len(ranked),
        "baseline": (
            {
                "structure_id": str(baseline_pair[0].id),
                "name": baseline_pair[0].name,
                "true_net_cost_usd": (
                    float(baseline_pair[1].true_net_cost_usd)
                    if baseline_pair[1].true_net_cost_usd is not None else None
                ),
            } if baseline_pair else None
        ),
        "top_result": (
            {
                "structure_id": str(top_pair[0].id),
                "name": top_pair[0].name,
                "true_net_cost_usd": (
                    float(top_pair[1].true_net_cost_usd)
                    if top_pair[1].true_net_cost_usd is not None else None
                ),
            } if top_pair else None
        ),
        "ranked": [
            {
                "structure_id": str(s.id),
                "name": s.name,
                "true_net_cost_usd": float(r.true_net_cost_usd) if r.true_net_cost_usd is not None else None,
                "total_incentive_value_usd": (
                    float(r.total_incentive_value_usd) if r.total_incentive_value_usd is not None else None
                ),
            }
            for s, r in ranked
        ],
        "mfni_limitation": MFNI_LIMITATION_NOTE,
    }
