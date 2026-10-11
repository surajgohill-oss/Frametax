"""Remaining anchor-NPC path (the hybrid anchor NPC seeded in the main hybrid search) with a saved contingency election.

SYNTHETIC ONLY and bounded: one lean synthetic project (no vfx line, ~2.5 s per evaluation) evaluated twice inside a rolled-back
transaction on the isolated test database, once with no election and once with a saved 25% election. The undeployed reserve K is
subtracted once from the planned cost, so every hybrid anchor NPC the search persisted must be exactly K lower than without the
election (a search that still started from gross would leave them unchanged), and the baseline NPC must fall by K plus the incentive
the newly-deployed reserve earns (and by no more)."""
from __future__ import annotations

import uuid
from collections import Counter

import pytest
from sqlalchemy import select

from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project_fact import ProjectFact
from app.services import canonical_evaluation as ce
from tests.isolated_records import DEFAULT_LINES, create_synthetic_project, isolated_session

RESERVE = sum(l[4] for l in DEFAULT_LINES if l[2] == "contingency")
PCT = 25.0
K = round(RESERVE * (1 - PCT / 100), 2)


async def _evaluate(pct):
    async with isolated_session() as session:
        pid = await create_synthetic_project(session)
        if pct is not None:
            session.add(ProjectFact(id=uuid.uuid4(), project_id=pid, fact_key="contingency_expected_utilization_pct", value=str(pct),
                                    value_type="number", source_type="user_override"))
            await session.flush()
        result = await ce.evaluate_project(session, pid)
        traces = (await session.execute(
            select(StructureCalculationResult.calculation_trace_json)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(ProductionStructure.project_id == pid)
        )).scalars().all()
        anchors = Counter(round(float(t["anchor_npc_usd"]), 2) for t in traces if t.get("anchor_npc_usd") is not None)
        return float(result["baseline"]["true_net_cost_usd"]), anchors


async def test_hybrid_anchor_npc_starts_from_the_planned_cost_with_a_saved_election():
    base_plain, anchors_plain = await _evaluate(None)
    base_elected, anchors_elected = await _evaluate(PCT)
    assert sum(anchors_plain.values()) > 0 and sum(anchors_plain.values()) == sum(anchors_elected.values())
    assert Counter({round(v - K, 2): n for v, n in anchors_plain.items()}) == anchors_elected      # every anchor NPC is exactly K lower
    # baseline: K lower, plus the incentive the newly-deployed 25% of the reserve earns at the baseline program's rate (a rate between
    # 0 and 40%): never the reserve alone (extra == 0 would mean the deployment earned nothing) and never subtracted twice.
    extra = base_plain - base_elected - K
    assert 0 < extra <= 0.40 * RESERVE * PCT / 100 + 0.02
