"""HEAVY synthetic check (explicit path; deliberately outside the default suite and NOT a skipped test): the UNBOUNDED hybrid production whose real search enumerates
hundreds of thousands of candidates (minutes; it exceeded 640 s here). Its pinned legacy counts were measured at an old engine and must be re-measured before this is
trusted; the bounded-universe equivalent of every assertion lives in tests/test_served_contract_bounded.py.

    DATABASE_URL unset  python -m pytest tests/heavy_synthetic/check_hybrid_bounded_retention_full.py -q"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services import canonical_evaluation as ce
from tests.test_served_contract_bounded import isolated_hybrid_project  # noqa: F401  (fixture)

pytestmark = pytest.mark.asyncio

#: Measured ONCE as the LEGACY full enumeration (every candidate a row) of this exact fixture.
_HYBRID_LEGACY_ENUMERATION = {
    "RULE_REJECTED": 252530, "PRICED": 588, "DOMINATED_WITH_PROOF": 308, "CO_PRO_OPPORTUNITY": 25,
    "FEASIBILITY_REVIEW_REQUIRED": 14, "UNPRICEABLE_AUTHORITY_INSUFFICIENT": 10,
}


async def test_hybrid_production_bounded_retention_keeps_every_proof_and_incumbent_and_reuses_for_free(
    db: AsyncSession, isolated_hybrid_project: Project,
):
    """A throw-away production whose real search enumerates 253,475 candidates (the real hybrid and
    multi-component incumbent-tracking sites and 308 dominance proofs): bounded retention keeps the
    accounting exact against the legacy enumeration, keeps every proof's referenced incumbent, stays
    bounded, and an identical-input rerun is a zero-row reuse."""
    from sqlalchemy import text
    from app.services import candidate_retention as cret
    pid = isolated_hybrid_project.id
    econ = await ce.evaluate_project(db, pid)          # commit() enforces generated == persisted + aggregated
    assert econ["status"] == "EVALUATION_COMPLETE"
    fp = econ["state_fingerprint"]
    summary = await ce.load_generation_summary(db, pid, fp)
    legacy_total = sum(_HYBRID_LEGACY_ENUMERATION.values())
    assert summary.total_rows == legacy_total == summary.persisted_rows + summary.aggregated_candidates
    assert summary.priced_count == _HYBRID_LEGACY_ENUMERATION["PRICED"] == econ["priced_count"]
    by = dict(summary.by_disposition)
    assert by == {k: v for k, v in _HYBRID_LEGACY_ENUMERATION.items() if k != "PRICED"}      # exact, incl. aggregated rejections

    G = "ps.project_id=:p and scr.engine_version=:ev and scr.input_fingerprint=:fp"
    P = {"p": pid, "ev": ce.ENGINE_VERSION, "fp": fp}
    J = "structure_calculation_results scr join production_structures ps on ps.id=scr.structure_id"
    persisted = (await db.execute(text(f"select count(*) from {J} where {G}"), P)).scalar()
    assert persisted == summary.persisted_rows < legacy_total / 100                       # bounded by policy, not enumeration
    types = (await db.execute(text(f"select count(distinct scr.structure_type) from {J} where {G}"), P)).scalar()
    non_priced = (await db.execute(text(f"select count(*) from {J} where {G} and scr.true_net_cost_usd is null"), P)).scalar()
    priced_rows = persisted - non_priced
    assert priced_rows <= cret.BoundedRetention().bound(structure_types=types + 2, jurisdictions=64) + 8

    # every persisted proof is complete AND its incumbent is a persisted row
    proofs = (await db.execute(text(f"select scr.calculation_trace_json trace from {J} where {G} and scr.calculation_trace_json->>'candidate_status'='DOMINATED_WITH_PROOF'"), P)).all()
    assert len(proofs) == _HYBRID_LEGACY_ENUMERATION["DOMINATED_WITH_PROOF"]
    rows = (await db.execute(text(f"select ps.id::text sid, scr.calculation_trace_json->>'structural_generator_structure_id' gen from {J} where {G}"), P)).all()
    known = {r.sid for r in rows} | {r.gen for r in rows if r.gen}
    referenced = 0
    for (t,) in proofs:
        assert isinstance(t.get("incumbent_value_usd"), (int, float)) and t.get("stopping_inequality_holds") is True
        ref = t.get("incumbent_structure_id")
        if ref:
            referenced += 1
            assert str(ref) in known, f"a retained proof references a candidate that is not retained: {ref}"
    assert referenced > 0, "the fixture must exercise proof-referenced incumbents"

    # group accounting reconciles with the summary; the priced remainder is dominated by a retained row
    agg = (await db.execute(text(
        "select coalesce(sum(candidate_count),0), count(*), coalesce(sum(candidate_count) filter (where candidate_status='PRICED'),0) "
        "from evaluation_candidate_aggregates where project_id=:p and input_fingerprint=:fp and engine_version=:ev"), P)).one()
    assert agg[0] == summary.aggregated_candidates and agg[1] == summary.aggregate_groups and agg[2] == summary.aggregated_priced
    assert summary.aggregate_groups <= 5000 + 40 * 64
    assert (await db.execute(text(
        "select count(*) from evaluation_candidate_aggregates a where a.project_id=:p and a.input_fingerprint=:fp and a.engine_version=:ev "
        "and a.candidate_status='PRICED' and a.dominating_structure_id is null"), P)).scalar() == 0

    # identical-input rerun: a zero-row reuse
    counts = lambda: text("select (select count(*) from production_structures where project_id=:p), "
                          "(select count(*) from evaluation_candidate_aggregates where project_id=:p), "
                          "(select count(*) from evaluation_generation_summaries where project_id=:p)")
    before = tuple((await db.execute(counts(), {"p": pid})).one())
    again = await ce.evaluate_project(db, pid)
    assert again["status"] == "EVALUATION_REUSED"
    assert tuple((await db.execute(counts(), {"p": pid})).one()) == before
    assert again["priced_count"] == econ["priced_count"] and again["baseline"] == econ["baseline"]
