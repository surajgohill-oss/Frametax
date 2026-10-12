"""GET /projects/{id}/evaluation/optimizer-list: every optimizer entry reachable by cursor, nothing evaluated, foreign cursors refused. One bounded synthetic evaluation (partner
universe restricted as in test_served_contract_bounded) on the isolated database."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.v1.evaluation import get_jurisdiction_winner, list_optimizer_entries
from app.services import canonical_evaluation as ce
from app.services.canonical_production_view import build_production_and_structures, encode_candidate_cursor
from tests.test_served_contract_bounded import _restrict_partners, db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


async def _walk(db, pid, kind, limit):
    out, cursor, meta = [], None, None
    while True:
        page = await list_optimizer_entries(pid, kind=kind, limit=limit, cursor=cursor, db=db)
        assert page["status"] == "OK" and page["evaluation_freshness"] == "CURRENT"
        out += page["entries"]
        meta = page
        if not page["has_more"]:
            return out, meta
        cursor = page["next_cursor"]


async def test_every_optimizer_entry_is_reachable_through_the_pages_exactly_once(db, isolated_hybrid_project, monkeypatch):
    pid = isolated_hybrid_project.id
    _restrict_partners(monkeypatch)
    await ce.evaluate_project(db, pid)
    view = await build_production_and_structures(db, pid, optimizer_list_limit=100)
    a = view["structures"]["allocated_structures"]
    for kind, name, total_key in (("evaluated", "evaluated_optimizer_alternatives", "evaluated_optimizer_alternatives_total"),
                                  ("candidates", "optimizer_candidates", "optimizer_candidates_total")):
        entries, last = await _walk(db, pid, kind, 12)
        assert last["total"] > 12, "the bounded universe must be large enough to need several pages"
        ids = [e["structure_id"] for e in entries]
        assert len(ids) == len(set(ids)) == a[total_key] == a[f"{name}_page"]["total"], (kind, len(ids), a[total_key])
        assert last["total"] == a[total_key]
    assert all("segments" in e for e in a["evaluated_optimizer_alternatives"]), "evaluated entries stay complete"
    first_page = await list_optimizer_entries(pid, kind="evaluated", limit=5, cursor=None, db=db)
    foreign = encode_candidate_cursor("0" * 64, 5)
    with pytest.raises(HTTPException) as bad:
        await list_optimizer_entries(pid, kind="evaluated", limit=5, cursor=foreign, db=db)
    assert bad.value.status_code == 409 and first_page["returned"] == 5
    with pytest.raises(HTTPException) as unknown:
        await list_optimizer_entries(pid, kind="nope", limit=5, cursor=None, db=db)
    assert unknown.value.status_code == 422


async def test_the_served_winners_are_compact_and_the_complete_winner_is_read_on_demand_with_every_value_preserved(db, isolated_hybrid_project, monkeypatch):
    pid = isolated_hybrid_project.id
    _restrict_partners(monkeypatch)
    await ce.evaluate_project(db, pid)
    served = (await build_production_and_structures(db, pid))["structures"]["allocated_structures"]["best_per_jurisdiction"]
    full = (await build_production_and_structures(db, pid, compact_winners=False))["structures"]["allocated_structures"]["best_per_jurisdiction"]
    assert served.keys() == full.keys() and served
    traced = 0
    for code, w in served.items():
        f = full[code]
        for k, v in f.items():
            if k in ("segments", "conditional_programs", "role_qualification", "opportunities"):
                continue
            assert w[k] == v, (code, k)
        for ws, fs in zip(w["segments"], f["segments"]):
            assert "qualification_trace" not in ws and all(ws[k] == v for k, v in fs.items() if k != "qualification_trace")
            if "qualification_trace" in fs:
                traced += 1
                assert ws["qualification_trace_omitted"] == len(fs["qualification_trace"]) and ws["detail_ref"]["code"] == code
        on_demand = (await get_jurisdiction_winner(pid, code, db=db))["structure"]
        assert on_demand == f, "the route returns the complete winner"
    assert traced, "the fixture must exercise the omitted trace"
    with pytest.raises(HTTPException) as missing:
        await get_jurisdiction_winner(pid, "XX-NOPE", db=db)
    assert missing.value.status_code == 404
