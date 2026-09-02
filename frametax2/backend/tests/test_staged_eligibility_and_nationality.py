"""
test_staged_eligibility_and_nationality.py

ITEMS 2 + 3 -- GRANULAR, STAGED ELIGIBILITY.

Eligibility is a dependency chain, not one switch:

    JURISDICTION -> BASE INCENTIVE -> STACK -> UPLIFT
                 -> CULTURAL QUALIFICATION -> TREATY / CO-PRO

An unresolved fact must withhold ONLY the economics that genuinely depend on
it. Specifically: an UNKNOWN writer or director nationality must not eliminate
a jurisdiction or an unrelated base incentive; only nationality-DEPENDENT
uplift/treaty economics become conditional.

Lips Like Sugar is the live case. Its Writer (Anthony Tambakis) and Director
(Brantley Gutierrez) both carry nationality_resolution_status
'unresolved_no_match' with primary_nationality None. Those facts are
DELIBERATELY left unresolved -- these tests assert the ENGINE's behaviour
under UNKNOWN, and must never be "fixed" by researching those people.

UPSTREAM GAP (recorded, not built here): the chain script credit -> real
person identity -> nationality has no enrichment source that resolved these
two names. TalentProfile already models the whole resolution trail
(nationality_source, nationality_evidence, nationality_confidence,
nationality_resolution_status), and Wikidata returned 'No Wikidata entity
matched this name' for the director and an occupation-corroborated match with
no nationality for the writer. Closing that is an INGESTION/ENRICHMENT
problem, not an economics one. The economics engine's correct behaviour with
the fact absent is what is pinned below.
"""
from __future__ import annotations

import pytest

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard

LIPS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


# ── ITEM 2 -- the requirement BASIS ──────────────────────────────────────

def test_local_spend_floor_is_measured_against_local_spend_not_world_gross():
    """A component below a program's LOCAL floor must not be rescued by the
    worldwide project gross."""
    from app.calculators.canonical_requirements_gate_bridge import (
        evaluate_requirements_gate,
    )
    from app.data.program_requirements import all_program_requirements

    slug = next(
        s for s, p in all_program_requirements().items()
        if getattr(p, "min_local_spend_usd", None)
    )
    floor = float(all_program_requirements()[slug].min_local_spend_usd)

    rescued = evaluate_requirements_gate(
        slug,
        segment_allocated_usd=floor / 100.0,   # local spend far BELOW the floor
        gross_budget_usd=floor * 100.0,        # huge worldwide gross
    )
    local = next(
        e for e in rescued.evaluations if e.requirement == "min_local_spend_usd"
    )
    assert local.state == "FAILED", (
        "a large worldwide gross rescued a component below the program's own "
        "local floor -- the threshold is being measured on the wrong basis"
    )


def test_an_unavailable_figure_is_UNKNOWN_never_SATISFIED():
    from app.calculators.canonical_requirements_gate_bridge import (
        evaluate_requirements_gate,
    )
    from app.data.program_requirements import all_program_requirements

    slug = next(
        s for s, p in all_program_requirements().items()
        if getattr(p, "min_local_spend_usd", None)
    )
    result = evaluate_requirements_gate(slug, segment_allocated_usd=None, gross_budget_usd=None)
    for e in result.evaluations:
        if e.requirement in ("min_local_spend_usd", "min_total_budget_usd"):
            assert e.state in ("UNKNOWN", "NOT_APPLICABLE"), (
                f"{e.requirement} resolved to {e.state} with no figure available"
            )


def test_local_entity_is_a_curable_formation_step_disclosed_never_assumed():
    """ITEM 2's canonical-semantics question. Forming a local entity is
    something the producer DOES in the ordinary course; it is not a fact
    about this production that makes it ineligible. So it is DISCLOSED as
    UNKNOWN (never silently SATISFIED) and never gates -- while a genuine
    computable threshold does gate."""
    from app.calculators.canonical_requirements_gate_bridge import (
        evaluate_requirements_gate,
    )
    from app.data.program_requirements import all_program_requirements

    slug = next(
        s for s, p in all_program_requirements().items()
        if getattr(p, "local_entity_required", False)
    )
    result = evaluate_requirements_gate(slug, segment_allocated_usd=10**9, gross_budget_usd=10**9)
    entity = next(
        (e for e in result.evaluations if e.requirement == "local_entity_required"), None,
    )
    assert entity is not None, "a mandatory local-entity requirement vanished"
    assert entity.state == "UNKNOWN", (
        "an unevidenced local entity was treated as SATISFIED"
    )
    assert entity.role == "ADMINISTRATIVE"

    evidenced = evaluate_requirements_gate(
        slug, segment_allocated_usd=10**9, gross_budget_usd=10**9,
        evidenced_facts=frozenset({"local_entity_required"}),
    )
    entity_ok = next(
        e for e in evidenced.evaluations if e.requirement == "local_entity_required"
    )
    assert entity_ok.state == "SATISFIED", "real evidence must resolve the fact"


# ── ITEM 3 -- UNKNOWN nationality withholds only DEPENDENT economics ─────

async def test_lips_writer_and_director_nationality_stay_unknown():
    """Guard against a future pass silently "resolving" these two people."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.models.project_person import ProjectPerson
    from app.models.talent import TalentProfile

    async with AsyncSession(engine, expire_on_commit=False) as session:
        rows = (await session.execute(
            select(ProjectPerson, TalentProfile)
            .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
            .where(ProjectPerson.project_id == LIPS_PROJECT_ID)
        )).all()

    by_role = {pp.role: profile for pp, profile in rows}
    assert "writer" in by_role and "director" in by_role
    for role, profile in by_role.items():
        assert profile.primary_nationality is None, (
            f"{role} nationality was populated -- this fixture must stay "
            "UNKNOWN; the point is the engine's behaviour without the fact"
        )
        assert profile.nationality_resolution_status == "unresolved_no_match"


async def test_unknown_nationality_does_not_eliminate_jurisdictions_or_base_incentives():
    """The whole point of staged eligibility: an unresolved PERSON fact must
    not collapse the jurisdiction/base-incentive stages that do not depend on
    it."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.services.canonical_evaluation import evaluate_project

    async with AsyncSession(engine, expire_on_commit=False) as session:
        summary = await evaluate_project(session, LIPS_PROJECT_ID)
        await session.commit()

    assert summary["base_jurisdiction_code"] == "US-CA"
    assert summary["priced_count"] > 50, (
        f"only {summary['priced_count']} candidates priced with UNKNOWN "
        "nationality -- an unrelated stage is being eliminated by a person fact"
    )


async def test_nationality_dependent_opportunities_are_conditional_and_unranked():
    """Treaty/co-production economics that DO depend on the unresolved facts
    must be CONDITIONAL: generated and disclosed with the exact missing fact,
    carrying no NPC, and never entering deterministic ranking."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import (
        ENGINE_VERSION,
        current_result_fingerprint,
        evaluate_project,
    )

    async with AsyncSession(engine, expire_on_commit=False) as session:
        summary = await evaluate_project(session, LIPS_PROJECT_ID)
        await session.commit()
        fingerprint = await current_result_fingerprint(session, LIPS_PROJECT_ID)
        rows = (await session.execute(
            select(ProductionStructure, StructureCalculationResult)
            .join(StructureCalculationResult,
                  StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == LIPS_PROJECT_ID,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == fingerprint,
            )
        )).all()

    copro = [
        (s, r) for s, r in rows
        if (r.calculation_trace_json or {}).get("candidate_status") == "CO_PRO_OPPORTUNITY"
    ]
    assert copro, "co-production opportunity generation was lost"

    ranked_ids = {e["structure_id"] for e in summary["ranked"]}
    for structure, result in copro:
        assert result.true_net_cost_usd is None, (
            "a conditional co-production carries deterministic economics"
        )
        assert str(structure.id) not in ranked_ids, (
            "a conditional co-production entered the deterministic ranking"
        )
        assert (result.calculation_trace_json or {}).get("reason"), (
            "a conditional opportunity must state the fact it is waiting on"
        )


async def test_populating_a_nationality_invalidates_the_evaluation_fingerprint():
    """A person fact that CAN change dependent economics must be part of the
    fingerprint, or a later resolution would be served against stale results.
    Sets, measures and RESTORES -- the fixture stays UNKNOWN."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.models.project_person import ProjectPerson
    from app.models.talent import TalentProfile
    from app.services.canonical_evaluation import evaluate_project

    async with AsyncSession(engine, expire_on_commit=False) as session:
        before = (await evaluate_project(session, LIPS_PROJECT_ID))["state_fingerprint"]
        await session.commit()

        writer = (await session.execute(
            select(TalentProfile)
            .join(ProjectPerson, ProjectPerson.talent_id == TalentProfile.id)
            .where(
                ProjectPerson.project_id == LIPS_PROJECT_ID,
                ProjectPerson.role == "writer",
            )
        )).scalars().first()
        original = (writer.primary_nationality, writer.nationality_resolution_status)
        try:
            writer.primary_nationality = "US"
            writer.nationality_resolution_status = "resolved"
            await session.commit()
            after = (await evaluate_project(session, LIPS_PROJECT_ID))["state_fingerprint"]
            await session.commit()
        finally:
            writer.primary_nationality, writer.nationality_resolution_status = original
            await session.commit()
            restored = (await evaluate_project(session, LIPS_PROJECT_ID))["state_fingerprint"]
            await session.commit()

    assert after != before, (
        "resolving a writer's nationality did not invalidate the evaluation "
        "fingerprint -- dependent economics would be served from stale results"
    )
    assert restored == before, "the UNKNOWN fixture was not restored exactly"
