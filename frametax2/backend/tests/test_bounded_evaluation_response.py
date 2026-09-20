"""
Bounded, deterministic evaluation responses.

The unpriced ("rejection") universe -- 525,613 of F#K Valentine's Day's 526,155 rows -- must
never be embedded whole in POST /evaluation/begin or the workspace view, must never be
silently dropped, and must page in a stable order. Synthetic-row tests run in one
always-rolled-back transaction; the DB-backed tests are read-only/idempotent against the real
Bad Hombres project row (same convention as the other canonical_evaluation tests).
"""
from __future__ import annotations

import json
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.evaluation import list_unpriceable_candidates
from app.db.session import engine
from app.models.production import EvaluationGenerationSummary, ProductionStructure, StructureCalculationResult
from app.services import canonical_evaluation as ce
from app.services.project_workspace_view import build_project_workspace_view

BAD_HOMBRES_PROJECT_ID = uuid.UUID("4355ae88-a636-4c18-af60-ad73b2646124")
TEST_ENGINE = "test-bounded-response"
TEST_FP = "c" * 64


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.rollback()


def _row(i: int, *, status: str, reason: str, npc=None, baseline=False):
    sid = uuid.uuid4()
    trace = {
        "candidate_status": status, "rejection_reason_class": reason, "is_baseline": baseline,
        "relocation_cost_normalized": False, "reason": f"reason {i}",
        "primary_jurisdiction": f"J{i:02d}", "program_slug": f"prog_{i:02d}",
        "discovery_classification": "full_relocation",
    }
    structure = ProductionStructure(
        id=sid, project_id=BAD_HOMBRES_PROJECT_ID, name=f"BOUNDED {i}", description="synthetic",
        jurisdiction_allocations=[], claimed_program_ids=[],
    )
    result = StructureCalculationResult(
        id=uuid.uuid4(), structure_id=sid, engine_version=TEST_ENGINE, total_budget_usd=1,
        total_incentive_value_usd=None if npc is None else 10.0, true_net_cost_usd=npc,
        structure_type="full_relocation", calculation_trace_json=trace, input_fingerprint=TEST_FP,
    )
    return structure, result


async def _seed(db: AsyncSession, plan):
    """Persist `plan` through the real bulk writer (ordinals + summary accumulation), then write
    its summary row exactly as commit() would -- but without committing."""
    writer = ce._BulkEvaluationWriter(db, chunk_rows=6)
    for i, (status, reason, npc, *rest) in enumerate(plan):
        structure, result = _row(i, status=status, reason=reason, npc=npc, baseline=bool(rest and rest[0]))
        writer.add(structure)
        await writer.flush()
        writer.add(result)
    await writer._drain()
    await writer._persist_generation_summary()
    return writer


_PLAN = (
    [("RULE_REJECTED", "THRESHOLD_NOT_MET", None)] * 11
    + [("RULE_REJECTED", "PAIRWISE_INCOMPATIBLE", None)] * 6
    + [("DOMINATED_WITH_PROOF", "", None)] * 4
    + [("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "UNRESOLVED_NO_AUTHORITY", None)] * 3
    + [("PRICED", "", 100.0)] * 3
)
# generation order is the plan order: ordinals 1..27; unpriced = 1..24; priced = 25..27


async def _summary(db):
    return await ce.load_generation_summary(db, BAD_HOMBRES_PROJECT_ID, TEST_FP, engine_version=TEST_ENGINE)


async def test_ordinals_are_monotonic_across_chunk_boundaries_and_summary_counts_are_exact(db: AsyncSession):
    await _seed(db, _PLAN)
    ordinals = (await db.execute(
        select(StructureCalculationResult.generation_ordinal)
        .where(StructureCalculationResult.input_fingerprint == TEST_FP,
               StructureCalculationResult.engine_version == TEST_ENGINE)
        .order_by(StructureCalculationResult.generation_ordinal)
    )).scalars().all()
    assert ordinals == list(range(1, 28))  # 1..N, no gaps, in generation order (chunk size 6)

    totals = ce.summary_totals(await _summary(db))
    assert totals["total"] == 24 and totals["priced"] == 3  # PRICED rows are not "unpriced"
    assert totals["by_disposition"] == {
        "DOMINATED_WITH_PROOF": 4, "RULE_REJECTED": 17, "UNPRICEABLE_AUTHORITY_INSUFFICIENT": 3,
    }
    assert totals["by_reason"] == [
        {"candidate_status": "DOMINATED_WITH_PROOF", "rejection_reason_class": None, "count": 4},
        {"candidate_status": "RULE_REJECTED", "rejection_reason_class": "PAIRWISE_INCOMPATIBLE", "count": 6},
        {"candidate_status": "RULE_REJECTED", "rejection_reason_class": "THRESHOLD_NOT_MET", "count": 11},
        {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT",
         "rejection_reason_class": "UNRESOLVED_NO_AUTHORITY", "count": 3},
    ]
    assert totals["total"] == sum(totals["by_disposition"].values()) == sum(g["count"] for g in totals["by_reason"])
    # exactly ONE summary row for the generation
    assert (await db.execute(
        select(func.count()).select_from(EvaluationGenerationSummary).where(
            EvaluationGenerationSummary.input_fingerprint == TEST_FP,
            EvaluationGenerationSummary.engine_version == TEST_ENGINE)
    )).scalar() == 1


async def test_retained_rows_are_exactly_the_non_rejected_ones_plus_any_baseline(db: AsyncSession):
    plan = list(_PLAN) + [("RULE_REJECTED", "THRESHOLD_NOT_MET", None, True)]  # a REJECTED baseline, ordinal 28
    await _seed(db, plan)
    summary = await _summary(db)
    assert summary.non_rejected_ordinals == list(range(18, 29))  # dominated 18-21, unpriceable 22-24, priced 25-27, baseline 28
    retained = await ce.load_retained_rows(db, BAD_HOMBRES_PROJECT_ID, TEST_FP, summary, engine_version=TEST_ENGINE)
    got = [(r.generation_ordinal, r.calculation_trace_json["candidate_status"]) for _, r in retained]
    assert [o for o, _ in got] == sorted(o for o, _ in got)  # generation order
    assert len(got) == 4 + 3 + 3 + 1  # dominated + unpriceable + priced + the rejected baseline
    assert {st for _, st in got} == {"DOMINATED_WITH_PROOF", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "PRICED",
                                     "RULE_REJECTED"}
    assert sum(1 for _, st in got if st == "RULE_REJECTED") == 1  # only the baseline, not the 17 others


async def test_pages_are_bounded_deterministic_exact_and_complete(db: AsyncSession):
    await _seed(db, _PLAN)
    pages, cursor = [], None
    while True:
        page = await ce.unpriceable_page(
            db, BAD_HOMBRES_PROJECT_ID, TEST_FP, engine_version=TEST_ENGINE, limit=5, cursor=cursor)
        assert page["limit"] == 5 and page["returned"] == len(page["results"]) <= 5
        assert page["order"] == ce.UNPRICEABLE_PAGE_ORDER
        pages.append(page)
        cursor = page["next_cursor"]
        assert page["has_more"] is (cursor is not None)
        if not page["has_more"]:
            break
    assert [p["returned"] for p in pages] == [5, 5, 5, 5, 4]  # exact has_more on a non-multiple total
    walked = [e for p in pages for e in p["results"]]
    assert [e["generation_ordinal"] for e in walked] == list(range(1, 25))  # every unpriced row, in order
    assert len({e["structure_id"] for e in walked}) == 24  # exactly once, none dropped
    assert all(e["true_net_cost_usd"] is None for e in walked)  # PRICED rows never appear
    again = await ce.unpriceable_page(db, BAD_HOMBRES_PROJECT_ID, TEST_FP, engine_version=TEST_ENGINE, limit=5)
    assert again == pages[0]  # the same generation pages IDENTICALLY every time


async def test_page_limit_clamp_and_empty_generation(db: AsyncSession):
    await _seed(db, _PLAN)
    clamped = await ce.unpriceable_page(db, BAD_HOMBRES_PROJECT_ID, TEST_FP, engine_version=TEST_ENGINE, limit=10_000)
    assert clamped["limit"] == ce.UNPRICEABLE_PAGE_MAX_LIMIT and clamped["returned"] == 24
    floor = await ce.unpriceable_page(db, BAD_HOMBRES_PROJECT_ID, TEST_FP, engine_version=TEST_ENGINE, limit=0)
    assert floor["limit"] == 1 and floor["has_more"] is True
    nothing = await ce.unpriceable_page(db, BAD_HOMBRES_PROJECT_ID, "d" * 64, engine_version=TEST_ENGINE)
    assert nothing["results"] == [] and nothing["has_more"] is False and nothing["next_cursor"] is None
    with pytest.raises(ce.GenerationSummaryUnavailable):
        await ce.load_generation_summary(db, BAD_HOMBRES_PROJECT_ID, "d" * 64, engine_version=TEST_ENGINE)


async def test_evaluation_begin_payload_is_bounded_and_routes_reproduce_the_universe(db: AsyncSession):
    econ = await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    unpriceable_part = {k: econ[k] for k in (
        "unpriceable_count", "unpriceable", "unpriceable_page", "unpriceable_by_disposition", "unpriceable_by_reason")}
    assert len(econ["unpriceable"]) <= ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert len(json.dumps(unpriceable_part)) < 200_000
    assert econ["unpriceable_page"]["results_route"] == f"/api/v1/projects/{BAD_HOMBRES_PROJECT_ID}/evaluation/unpriceable"
    assert sum(econ["unpriceable_by_disposition"].values()) == econ["unpriceable_count"] == econ["unpriceable_page"]["total"]

    first = await list_unpriceable_candidates(BAD_HOMBRES_PROJECT_ID, limit=40, cursor=None, db=db)
    assert first["status"] == "OK" and first["total_unpriceable_count"] == econ["unpriceable_count"]
    assert first["by_disposition"] == econ["unpriceable_by_disposition"]
    assert first["input_fingerprint"] == econ["state_fingerprint"]
    got, page = list(first["results"]), first
    while page["has_more"]:
        page = await list_unpriceable_candidates(BAD_HOMBRES_PROJECT_ID, limit=40, cursor=page["next_cursor"], db=db)
        assert "total_unpriceable_count" not in page  # totals ride the first page only
        got += page["results"]
    assert len(got) == econ["unpriceable_count"] and len({e["structure_id"] for e in got}) == len(got)
    assert [e["structure_id"] for e in got[: len(econ["unpriceable"])]] == [e["structure_id"] for e in econ["unpriceable"]]
    assert [e["generation_ordinal"] for e in got] == sorted(e["generation_ordinal"] for e in got)

    with pytest.raises(HTTPException) as bad:
        await list_unpriceable_candidates(BAD_HOMBRES_PROJECT_ID, limit=10, cursor="definitely-not-a-cursor", db=db)
    assert bad.value.status_code == 422
    with pytest.raises(HTTPException) as missing:
        await list_unpriceable_candidates(uuid.uuid4(), limit=10, cursor=None, db=db)
    assert missing.value.status_code == 404


async def test_workspace_view_is_bounded_and_carries_the_same_accounting(db: AsyncSession):
    econ = await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    view = await build_project_workspace_view(db, BAD_HOMBRES_PROJECT_ID)
    evaluation = view["evaluation"]
    universe = evaluation["rejection_universe"]
    assert universe["total_count"] == econ["unpriceable_count"]
    assert universe["by_disposition"] == econ["unpriceable_by_disposition"]
    assert universe["by_reason"] == econ["unpriceable_by_reason"]
    assert universe["first_page"]["returned"] <= ce.UNPRICEABLE_PAGE_DEFAULT_LIMIT
    assert universe["first_page"]["has_more"] is (universe["total_count"] > universe["first_page"]["returned"])
    assert [e["structure_id"] for e in universe["first_page"]["results"]] == [e["structure_id"] for e in econ["unpriceable"]]
    assert universe["results_route"].endswith("/evaluation/unpriceable")
    assert evaluation["unpriceable_count"] == len(evaluation["unpriceable"])  # pre-existing list meaning kept
    assert evaluation["baseline"]["true_net_cost_usd"] == econ["baseline"]["true_net_cost_usd"]
    assert evaluation["input_fingerprint"] == econ["state_fingerprint"]
    listed = evaluation["comparable"] + evaluation["review_required"] + evaluation["unpriceable"]
    assert all(c["candidate_status"] != "RULE_REJECTED" for c in listed)  # the rejected mass is never embedded
