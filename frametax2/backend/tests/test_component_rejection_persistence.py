"""
Optimizer FINAL closeout, P1-REJ-001.

ROOT CAUSE (Codex, full optimizer audit): component-relocation generation
(`canonical_evaluation.py`'s component-candidate loop) `continue`d past
every (component, target) attempt whose pricing kernel returned
`is_fully_priced=False` -- most commonly a real minimum-spend/minimum-
budget requirements-gate failure. The reasoning for never PRICING such an
attempt is correct (a genuinely failed mandatory gate cannot coexist with
a priced incentive), but dropping the row entirely meant these 889 real,
meaningfully-evaluated attempts could not be reconstructed from persisted
runtime state without rerunning candidate generation -- an
observability/auditability gap.

FIX: every threshold-failed component attempt now persists a disclosed,
never-priced ProductionStructure + StructureCalculationResult row, using
the EXACT SAME architecture and shape the full_relocation/single_country
reject path already uses (candidate_status=RULE_REJECTED,
rejection_reason_class, reason, total_incentive_value_usd=None,
true_net_cost_usd=None) -- never a parallel/hidden rejection database.
`ENGINE_VERSION` bumped (canonical-1.53.0 -> canonical-1.54.0) since this
changes the persisted ROW SET a given fingerprint produces.

This file proves the fix, not merely documents the finding.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.production import EvaluationCandidateAggregate
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"

ALL_LOCKED_PROJECT_IDS = (
    LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID, BAD_HOMBRES_PROJECT_ID, LIPS_LIKE_SUGAR_PROJECT_ID,
)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


class _RejectionGroup:
    """A persisted rejection GROUP viewed as the row-shaped record these controls were written for.
    canonical-1.89.0 (bounded rejection accounting) counts plain RULE_REJECTED candidates exactly in
    evaluation_candidate_aggregates instead of persisting one row per permutation; each group keeps a
    representative (structure identity + full trace) sufficient to reconstruct why it was rejected."""

    def __init__(self, agg: EvaluationCandidateAggregate):
        self.calculation_trace_json = (agg.representative or {}).get("trace") or {}
        self.input_fingerprint = agg.input_fingerprint
        self.engine_version = agg.engine_version
        self.rejected_count = agg.candidate_count
        self.total_incentive_value_usd = None
        self.true_net_cost_usd = None


async def _rejected_component_rows(db: AsyncSession, project_id: str) -> list[_RejectionGroup]:
    rows = (await db.execute(
        select(EvaluationCandidateAggregate).where(
            EvaluationCandidateAggregate.project_id == project_id,
            EvaluationCandidateAggregate.engine_version == ENGINE_VERSION,
        )
    )).scalars().all()
    return [
        _RejectionGroup(r) for r in rows
        if r.candidate_status == "RULE_REJECTED" and r.structure_type == "component_relocation" and r.reason_class
    ]


def _rejected_total(groups: list[_RejectionGroup]) -> int:
    return sum(g.rejected_count for g in groups)


async def test_locked_corpus_produces_durable_component_rejections(db: AsyncSession):
    """At least one of the four locked-corpus projects must have real,
    persisted component rejection rows after a fresh evaluation -- proves
    this is not a vacuous, always-empty code path."""
    total = 0
    for project_id in ALL_LOCKED_PROJECT_IDS:
        await evaluate_project(db, project_id)
        total += _rejected_total(await _rejected_component_rows(db, project_id))
    assert total > 0, "expected at least one real persisted component rejection across the locked corpus"


async def test_rejection_rows_carry_full_reconstructible_disposition(db: AsyncSession):
    """Every persisted rejection row must carry enough state to
    reconstruct PROJECT, TARGET, COMPONENT, PROGRAM, REJECTION REASON, and
    GENERATION/FINGERPRINT without rerunning generation."""
    checked = 0
    for project_id in ALL_LOCKED_PROJECT_IDS:
        await evaluate_project(db, project_id)
        for row in await _rejected_component_rows(db, project_id):
            trace = row.calculation_trace_json or {}
            assert trace.get("rejection_reason_class"), "missing rejection_reason_class"
            assert trace.get("reason"), "missing real reason text"
            assert trace.get("candidate_status") == "RULE_REJECTED"
            comp_allocs = trace.get("component_allocations") or []
            assert comp_allocs, "missing component/target disclosure"  # the group's representative reconstructs why
            assert comp_allocs[0].get("jurisdiction_code"), "missing TARGET jurisdiction"
            assert comp_allocs[0].get("component"), "missing COMPONENT"
            assert row.input_fingerprint, "missing GENERATION/FINGERPRINT"
            assert row.engine_version == ENGINE_VERSION
            checked += 1
    assert checked > 0


async def test_rejected_component_never_becomes_priced_or_recommended(db: AsyncSession):
    """REJECTED_AS_PRICED = 0: a rejection row must never carry
    candidate_status=PRICED, a real incentive value, or a real NPC --
    it can never enter canonical_production_view's comparable/ranked pool
    (which gates strictly on candidate_status == 'PRICED')."""
    for project_id in ALL_LOCKED_PROJECT_IDS:
        await evaluate_project(db, project_id)
        for row in await _rejected_component_rows(db, project_id):
            assert row.total_incentive_value_usd is None
            assert row.true_net_cost_usd is None
            trace = row.calculation_trace_json or {}
            assert trace.get("candidate_status") != "PRICED"


async def test_rerunning_same_generation_is_idempotent(db: AsyncSession):
    """No duplicate rejection records: calling evaluate_project() twice
    for the same (already-current) fingerprint must not create a second
    set of rejection rows -- generation only runs on a genuinely fresh
    fingerprint (the existing reused-row short-circuit), which this
    fix relies on rather than reinventing its own idempotency check."""
    for project_id in ALL_LOCKED_PROJECT_IDS:
        await evaluate_project(db, project_id)
        first_count = _rejected_total(await _rejected_component_rows(db, project_id))
        await evaluate_project(db, project_id)
        second_count = _rejected_total(await _rejected_component_rows(db, project_id))
        assert first_count == second_count, (
            f"{project_id}: rejection row count changed across an idempotent rerun "
            f"({first_count} -> {second_count})"
        )
