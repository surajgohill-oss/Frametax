"""
Bounded candidate retention (canonical-1.90.0): enumeration cardinality never defines persistence cardinality.

A deterministic candidate stream (thousands of candidates: PRICED across five structure types and thirty
jurisdictions with equal-NPC ties, plain RULE_REJECTED permutations, proofs, opportunities, a baseline,
proof-referenced incumbents, an unreferenced held incumbent) is streamed through the bulk writer TWICE in
one rolled-back transaction: as the LEGACY full enumeration (``bounded_retention=False``: every candidate
a row -- exactly what canonical-1.88.0 wrote) and through bounded retention. The expected retained set is
computed INDEPENDENTLY in pure Python from the descriptors (a full sort after the fact) and must equal what
the streaming writer persisted, exactly; everything else must be counted in aggregate groups whose counts,
min/max economics and best identities equal a regrouping of the legacy rows.

Nothing is committed and no real project is touched: a synthetic organization/project lives only inside
the test transaction.
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.production import (
    EvaluationCandidateAggregate, EvaluationGenerationSummary, ProductionStructure, StructureCalculationResult,
)
from app.models.project import Project
from app.services import candidate_aggregation as cagg
from app.services import candidate_retention as cret
from app.services import canonical_evaluation as ce
from app.services.economic_identity import canonical_economic_identity

LEGACY_ENGINE, NEW_ENGINE = "test-legacy-full-enumeration", "test-bounded-retention"
LEGACY_FP, NEW_FP = "1" * 64, "2" * 64
TYPES = ["single_country", "full_relocation", "hybrid", "component_relocation", "multi_program"]
INF = float("inf")


@pytest.fixture
async def project_id():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        org = Organization(name="Candidate Retention Org", slug=f"cand-ret-{uuid.uuid4().hex[:8]}")
        session.add(org)
        await session.flush()
        project = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Candidate Retention {uuid.uuid4().hex[:6]}")
        session.add(project)
        await session.flush()
        yield session, project.id
        await session.rollback()


class Cand:
    """Descriptor of candidate #idx (1-based seq = idx + 1): everything needed to build its rows and to
    compute, independently, whether the retention policy must keep it."""

    def __init__(self, idx: int):
        self.idx, self.seq = idx, idx + 1
        self.status, self.kind = "PRICED", "priced"
        self.stype = TYPES[idx % 5]
        self.jur = f"J{idx % 30:02d}"
        self.npc = 1_000_000.0 + ((idx * 7919) % 5003) * 100.0        # many equal-NPC ties across idx
        self.adj = None if idx % 17 == 0 else self.npc + ((idx * 31) % 700)
        self.incentive = 100_000.0 + idx
        self.reason = None
        self.baseline = False
        self.proof_ref = None
        self.hold = None                                              # None | "before" | "after" | "released"
        m = idx % 50
        if idx == 0:
            self.baseline, self.kind, self.stype, self.jur, self.npc, self.adj = True, "baseline", "single_country", "US", 5_000_000.0, 5_000_100.0
        elif m == 25:
            self.kind, self.hold, self.npc, self.adj = "incumbent-before", "before", 50_000_000.0 + idx, None
        elif m == 26:
            self.status, self.kind, self.npc, self.adj = "DOMINATED_WITH_PROOF", "proof-generator-ref", None, None
            self.proof_ref = f"ARCH-{idx - 1:06d}"
        elif m == 40:
            self.kind, self.hold, self.npc, self.adj = "incumbent-after", "after", 50_000_000.0 + idx, None
        elif m == 41:
            self.status, self.kind, self.npc, self.adj = "DOMINATED_WITH_PROOF", "proof-uuid-ref", None, None
        elif m == 10:
            self.kind, self.hold, self.npc, self.adj = "incumbent-leaked-hold", "leaked", 50_000_000.0 + idx, None
        elif m == 12:
            self.kind, self.hold, self.npc, self.adj = "incumbent-released", "released", 50_000_000.0 + idx, None
        elif idx % 23 == 5:
            self.status, self.kind, self.npc, self.adj = "CO_PRO_OPPORTUNITY", "copro", None, None
        elif idx % 29 == 7:
            self.status, self.kind, self.npc, self.adj, self.reason = "FEASIBILITY_REVIEW_REQUIRED", "feasibility", None, None, "NON_GUARANTEED_SELECTIVE"
        elif idx % 31 == 9:
            self.status, self.kind, self.npc, self.adj, self.reason = "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "authority", None, None, "AUTHORITY_UNRESOLVED"
        elif idx % 97 == 11:
            self.status, self.kind, self.reason = "RULE_REJECTED", "rejected-with-net-cost", "THRESHOLD_NOT_MET"
        elif idx % 19 == 3:
            self.status, self.kind, self.npc, self.adj = "RULE_REJECTED", "plain-rejected", None, None
            self.reason = ["THRESHOLD_NOT_MET", "PAIRWISE_INCOMPATIBLE", "MINIMUM_SPEND_FAIL"][idx % 3]
        self.priced = self.status == "PRICED" and self.npc is not None
        self.trace = {
            "reason": f"candidate {idx}", "is_baseline": self.baseline, "candidate_status": self.status,
            "rejection_reason_class": self.reason, "structure_type": self.stype, "primary_jurisdiction": self.jur,
            "anchor_jurisdiction": "US", "program_slug": f"prog_{idx}", "program_slugs": ["anchor_prog", f"prog_{idx}"],
            "jurisdiction_codes": ["US", self.jur], "structural_generator_structure_id": f"ARCH-{idx:06d}",
            "relocation_cost_normalized": False, "component_types": ["principal_production", ["post", "vfx", "music"][idx % 3]],
        }
        self.identity = canonical_economic_identity(self.stype, self.trace) if self.priced else None

    def rows(self, pid, engine_version, fingerprint):
        sid = uuid.uuid4()
        structure = ProductionStructure(
            id=sid, project_id=pid, name=f"cand {self.idx}", description=f"fixture {self.idx}",
            jurisdiction_allocations=[], claimed_program_ids=["anchor_prog", f"prog_{self.idx}"])
        result = StructureCalculationResult(
            id=uuid.uuid4(), structure_id=sid, engine_version=engine_version, total_budget_usd=1_000_000,
            total_incentive_value_usd=self.incentive if self.npc is not None else None,
            true_net_cost_usd=self.npc, risk_adjusted_net_cost_usd=self.adj, has_unverified_inputs=False,
            warnings=[f"w{self.idx}"], structure_type=self.stype, calculation_trace_json=dict(self.trace),
            input_fingerprint=fingerprint)
        return structure, result


def candidates(n: int) -> list[Cand]:
    return [Cand(i) for i in range(n)]


async def stream(session, pid, cands, *, engine_version, fingerprint, bounded, chunk_rows=50, writer=None):
    writer = writer or ce._BulkEvaluationWriter(session, chunk_rows=chunk_rows, bounded_retention=bounded)
    sid_by_idx = {}
    for c in cands:
        if c.hold in ("before", "released", "leaked"):
            writer.hold_candidate(f"ARCH-{c.idx:06d}")
        s, r, = c.rows(pid, engine_version, fingerprint)
        if c.kind == "proof-uuid-ref":
            r.calculation_trace_json["incumbent_structure_id"] = str(sid_by_idx[c.idx - 1])
        elif c.proof_ref:
            r.calculation_trace_json["incumbent_structure_id"] = c.proof_ref
        sid_by_idx[c.idx] = s.id
        writer.add(s)
        await writer.flush()      # the flush between the pair, exactly as evaluate_project() does
        writer.add(r)
        if c.hold == "after":
            writer.hold_candidate(str(s.id))
        elif c.hold == "released":
            writer.release_candidate(f"ARCH-{c.idx:06d}")
        await writer.flush()
    return writer


async def finish(writer):
    writer._finalize_retention()
    await writer._drain(promote_pending=True)
    return writer


def expected_retained(cands: list[Cand], *, global_top=cret.GLOBAL_TOP, type_top=cret.TYPE_TOP, jur_top=cret.JURISDICTION_TOP,
                      opportunity_cap=cret.OPPORTUNITY_CAP) -> set[int]:
    """The retained set, computed INDEPENDENTLY by a full sort after the fact (never streaming)."""
    keep: set[int] = set()
    priced = [c for c in cands if c.priced and c.status == "PRICED"]
    keys = (lambda c: (c.npc, c.identity, c.seq), lambda c: (c.adj if c.adj is not None else INF, c.identity, c.seq))
    for key in keys:
        keep |= {c.idx for c in sorted(priced, key=key)[:global_top]}
        for t in {c.stype for c in priced}:
            keep |= {c.idx for c in sorted((c for c in priced if c.stype == t), key=key)[:type_top]}
        for j in {c.jur for c in priced if c.stype in cret.LOCAL_STACK_TYPES}:
            keep |= {c.idx for c in sorted((c for c in priced if c.stype in cret.LOCAL_STACK_TYPES and c.jur == j), key=key)[:jur_top]}
    keep |= {c.idx for c in cands if c.baseline}
    seen = Counter()
    for c in cands:                                   # non-priced, non-plain-rejected rows, in generation order, capped per status
        if c.baseline or c.priced:
            continue
        if c.status == "RULE_REJECTED" and c.npc is None:
            continue
        cap = cret.DOMINATED_CAP if c.status == "DOMINATED_WITH_PROOF" else opportunity_cap
        if seen[c.status] < cap:
            keep.add(c.idx)
        seen[c.status] += 1
    for c in cands:                                   # incumbents a retained proof references
        if c.idx in keep and c.status == "DOMINATED_WITH_PROOF":
            ref = c.proof_ref
            target = next((d for d in cands if f"ARCH-{d.idx:06d}" == ref), None) if ref else cands[c.idx - 1]
            keep.add(target.idx)
    return keep


async def _rows(session, engine_version):
    return (await session.execute(text(
        "SELECT ps.name, to_jsonb(ps) - 'id' - 'created_at' - 'updated_at' AS ps, "
        "       to_jsonb(scr) - 'id' - 'structure_id' - 'created_at' - 'updated_at' - 'generation_ordinal' "
        "         - 'economic_identity' - 'engine_version' - 'input_fingerprint' AS scr, scr.generation_ordinal, scr.id, ps.id AS sid "
        "FROM production_structures ps JOIN structure_calculation_results scr ON scr.structure_id = ps.id "
        "WHERE scr.engine_version = :ev ORDER BY (regexp_replace(ps.name, '\\D', '', 'g'))::int"), {"ev": engine_version})).all()


def idx_of(name: str) -> int:
    return int(name.split()[1])


N = 4000


async def test_bounded_retention_equals_full_enumeration_exactly(project_id):
    session, pid = project_id
    cands = candidates(N)
    legacy = await finish(await stream(session, pid, cands, engine_version=LEGACY_ENGINE, fingerprint=LEGACY_FP, bounded=False))
    new = await finish(await stream(session, pid, cands, engine_version=NEW_ENGINE, fingerprint=NEW_FP, bounded=True))
    legacy_rows, new_rows = await _rows(session, LEGACY_ENGINE), await _rows(session, NEW_ENGINE)

    # ---- the legacy path persisted every candidate; the invariant holds on both writers
    assert len(legacy_rows) == legacy.results_written == N
    legacy._assert_accounting()
    new._assert_accounting()
    assert new.generated_results == N == new.results_written + new._aggregator.total
    assert new._aggregator.total == new._aggregator.counted() == N - len(new_rows)

    # ---- retained detailed rows == the independently sorted retention policy, EXACTLY (no more, no less)
    expected = expected_retained(cands)
    assert {idx_of(r.name) for r in new_rows} == expected
    assert len(new_rows) == len(expected) < N / 2                               # bounded, well below enumeration

    # ---- every retained row is economically byte-identical to its legacy row
    import re
    _uuid = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    def no_row_ids(v):   # per-generation random structure uuids embedded in a trace are the only legitimate difference
        if isinstance(v, dict):
            return {k: no_row_ids(x) for k, x in v.items()}
        if isinstance(v, list):
            return [no_row_ids(x) for x in v]
        return "<row-id>" if isinstance(v, str) and _uuid.match(v) else v

    legacy_by_idx = {idx_of(r.name): (r.ps, no_row_ids(r.scr)) for r in legacy_rows}
    for r in new_rows:
        assert (r.ps, no_row_ids(r.scr)) == legacy_by_idx[idx_of(r.name)]

    # ---- exact same winner / baseline, global top-100 (both keys), top-per-family, best-per-jurisdiction
    priced = [c for c in cands if c.priced and c.status == "PRICED"]
    retained_priced = [c for c in priced if c.idx in expected]
    for key in (lambda c: (c.npc, c.identity), lambda c: (c.adj if c.adj is not None else INF, c.identity)):
        assert [c.idx for c in sorted(retained_priced, key=key)[:100]] == [c.idx for c in sorted(priced, key=key)[:100]]
        for t in TYPES:
            assert ([c.idx for c in sorted((c for c in retained_priced if c.stype == t), key=key)[:100]]
                    == [c.idx for c in sorted((c for c in priced if c.stype == t), key=key)[:100]])
        for j in {c.jur for c in priced if c.stype in cret.LOCAL_STACK_TYPES}:
            pick = lambda pool: min((c for c in pool if c.stype in cret.LOCAL_STACK_TYPES and c.jur == j), key=key).idx
            assert pick(retained_priced) == pick(priced)
    assert any(idx_of(r.name) == 0 for r in new_rows)                           # the (poor-NPC) baseline is retained

    # ---- proof-referenced incumbents are retained; the unreferenced held incumbent is not
    proofs = [c for c in cands if c.status == "DOMINATED_WITH_PROOF"]
    assert proofs and all((c.idx - 1) in expected for c in proofs)
    assert not any(c.kind in ("incumbent-released", "incumbent-leaked-hold") and c.idx in expected for c in cands)

    # ---- aggregated remainder: regroup the LEGACY rows that were not retained, independently
    groups: dict = {}
    for r in legacy_rows:
        i = idx_of(r.name)
        if i in expected:
            continue
        c = cands[i]
        ident = cagg.candidate_group_identity(c.status, r.scr["structure_type"], r.scr["calculation_trace_json"], r.ps["claimed_program_ids"])
        g = groups.setdefault(cagg.candidate_group_key(ident), {"n": 0, "min": None, "max": None, "best": None, "inc_min": None, "inc_max": None})
        g["n"] += 1
        if c.priced:
            g["min"] = c.npc if g["min"] is None else min(g["min"], c.npc)
            g["max"] = c.npc if g["max"] is None else max(g["max"], c.npc)
            g["best"] = min(g["best"], (c.npc, c.identity)) if g["best"] else (c.npc, c.identity)
            g["inc_min"] = c.incentive if g["inc_min"] is None else min(g["inc_min"], c.incentive)
            g["inc_max"] = c.incentive if g["inc_max"] is None else max(g["inc_max"], c.incentive)
    got = {r["group_key"]: r for r in new._aggregator.rows(new._retention.dominating_by_type)}
    assert {k: v["n"] for k, v in groups.items()} == {k: r["candidate_count"] for k, r in got.items()}
    for k, v in groups.items():
        r = got[k]
        assert (r["min_npc_usd"], r["max_npc_usd"]) == (v["min"], v["max"])
        assert (r["min_incentive_usd"], r["max_incentive_usd"]) == (v["inc_min"], v["inc_max"])
        assert r["best_economic_identity"] == (v["best"][1] if v["best"] else None)
        assert (r["dominating_structure_id"] is not None) is (r["candidate_status"] == "PRICED")
    # a PRICED group's dominating reference is a RETAINED detailed row of the same type with NPC <= every member
    persisted_ids = {str(r.sid): idx_of(r.name) for r in new_rows}
    for r in got.values():
        if r["candidate_status"] == "PRICED":
            dom = cands[persisted_ids[str(r["dominating_structure_id"])]]
            assert dom.stype == r["structure_type"] and dom.npc <= r["min_npc_usd"]

    # ---- summaries: exact totals identical to full enumeration; the persisted/aggregated split is exact
    lp, np_ = legacy._summary.payload(), new._summary.payload(aggregate_groups=new._aggregator.group_count)
    for key in ("total_rows", "priced_count", "unpriced_count", "by_disposition", "by_reason"):
        assert np_[key] == lp[key], key
    assert np_["persisted_rows"] == len(new_rows) and np_["aggregated_candidates"] == N - len(new_rows)
    assert np_["aggregated_priced"] == new._aggregator.priced_total
    assert set(np_["non_rejected_ordinals"]) <= {o for *_, o, _i, _s in new_rows}
    assert sorted(o for *_, o, _i, _s in new_rows) == list(range(1, len(new_rows) + 1))   # ordinals exactly 1..M over persisted rows


async def test_retained_rows_stay_bounded_as_the_enumeration_grows(project_id):
    """Quadrupling the enumeration does not grow persistence: retained rows stay under the policy bound
    while aggregated candidates absorb all the growth (and stay exact)."""
    session, pid = project_id
    small = await finish(await stream(session, pid, candidates(1500), engine_version="t-small", fingerprint="3" * 64, bounded=True))
    large = await finish(await stream(session, pid, candidates(6000), engine_version="t-large", fingerprint="4" * 64, bounded=True))
    for w, n in ((small, 1500), (large, 6000)):
        w._assert_accounting()
        assert w.generated_results == n
    def non_priced_rows(n):   # proof / opportunity / baseline / net-cost rows: retained in full by policy, not lane-bounded
        return sum(1 for c in candidates(n) if not c.priced and not (c.status == "RULE_REJECTED" and c.npc is None))
    bound = large._retention.bound(structure_types=len(TYPES), jurisdictions=31)
    small_priced = small.results_written - non_priced_rows(1500)
    large_priced = large.results_written - non_priced_rows(6000)
    assert large_priced <= bound + 4                         # lanes + proof-referenced incumbents: the policy bound
    assert large_priced < 1.3 * small_priced + 100           # 4x the enumeration, ~flat PRICED persistence
    assert large._aggregator.total > 3 * small._aggregator.total


async def test_retention_is_deterministic(project_id):
    session, pid = project_id
    cands = candidates(2500)
    a = await finish(await stream(session, pid, cands, engine_version="t-a", fingerprint="5" * 64, bounded=True))
    b = await finish(await stream(session, pid, cands, engine_version="t-b", fingerprint="6" * 64, bounded=True))
    ra, rb = await _rows(session, "t-a"), await _rows(session, "t-b")
    assert [(idx_of(r.name), r.generation_ordinal) for r in ra] == [(idx_of(r.name), r.generation_ordinal) for r in rb]
    strip = lambda rows: [{k: v for k, v in r.items() if k not in ("dominating_structure_id",)} for r in rows]
    assert strip(list(a._aggregator.rows())) == strip(list(b._aggregator.rows()))


async def test_persisted_groups_page_exactly_and_summary_reconciles(project_id):
    session, pid = project_id
    w = await finish(await stream(session, pid, candidates(3000), engine_version=ce.ENGINE_VERSION, fingerprint=NEW_FP, bounded=True))
    w._assert_accounting()
    await w._persist_generation_summary()          # aggregates + summary rows, inside the rolled-back txn
    summary = await ce.load_generation_summary(session, pid, NEW_FP)
    assert (summary.total_rows, summary.persisted_rows, summary.aggregated_candidates, summary.aggregated_priced, summary.aggregate_groups) == (
        3000, w.results_written, w._aggregator.total, w._aggregator.priced_total, w._aggregator.group_count)
    totals = ce.summary_totals(summary)
    assert totals["generated"] == totals["persisted_rows"] + totals["aggregated_candidates"]

    seen, cursor = [], None
    while True:
        page = await ce.candidate_groups_page(session, pid, NEW_FP, limit=13, cursor=cursor, detail=True)
        seen += page["results"]
        assert page["returned"] <= 13 and page["order"] == "group_ordinal"
        cursor = page["next_cursor"]
        assert page["has_more"] is (cursor is not None)
        if not cursor:
            break
    assert [g["group_ordinal"] for g in seen] == list(range(1, len(seen) + 1))
    assert sum(g["candidate_count"] for g in seen) == w._aggregator.total == totals["aggregated_candidates"]
    priced_only = await ce.candidate_groups_page(session, pid, NEW_FP, limit=200, status="PRICED")
    assert priced_only["results"] and all(g["candidate_status"] == "PRICED" for g in priced_only["results"])
    for g in seen:                                  # each representative reconstructs its own group
        rep = g["representative"]
        ident = cagg.candidate_group_identity(g["candidate_status"], rep["structure_type"], rep["trace"], rep["structure"]["claimed_program_ids"])
        assert cagg.candidate_group_key(ident) == g["group_key"] or g["group_key"] == cagg.candidate_group_key(
            cagg.candidate_group_identity(g["candidate_status"], rep["structure_type"], rep["trace"], rep["structure"]["claimed_program_ids"], coarse=True))
        assert rep["trace"]["reason"] and rep["warnings"]
    assert all("representative" not in g for g in (await ce.candidate_groups_page(session, pid, NEW_FP, limit=5))["results"])


async def test_every_accounting_or_reference_violation_fails_closed(project_id):
    session, pid = project_id
    w = await finish(await stream(session, pid, candidates(800), engine_version="t-fc", fingerprint="7" * 64, bounded=True))
    w._assert_accounting()
    w._aggregator.total += 1                                           # a silent double count
    with pytest.raises(ce.EvaluationAccountingError):
        w._assert_accounting()
    w._aggregator.total -= 1
    list(w._aggregator._groups.values())[0].count -= 1                 # a silent omission inside one group
    with pytest.raises(ce.EvaluationAccountingError):
        w._assert_accounting()
    list(w._aggregator._groups.values())[0].count += 1
    w.results_written -= 1                                             # a persisted row that went missing
    with pytest.raises(ce.EvaluationAccountingError):
        w._assert_accounting()
    w.results_written += 1
    w._summary.aggregated_priced += 1                                  # priced split disagreement
    with pytest.raises(ce.EvaluationAccountingError):
        w._assert_accounting()
    w._summary.aggregated_priced -= 1
    w._assert_accounting()

    # a retained proof that references a candidate that is NOT retained fails closed
    w2 = ce._BulkEvaluationWriter(session, chunk_rows=50)
    orphan = Cand(26)                                                  # DOMINATED_WITH_PROOF -> ARCH-000025 never added
    s, r = orphan.rows(pid, "t-fc2", "8" * 64)
    r.calculation_trace_json["incumbent_structure_id"] = "ARCH-000025"
    w2.add(s)
    with pytest.raises(ce.EvaluationAccountingError):
        w2.add(r)


async def test_commit_refuses_to_commit_an_unbalanced_generation(project_id):
    _, pid = project_id

    class _Session:
        commits = 0
        async def flush(self): pass
        async def execute(self, *a, **k): raise AssertionError("nothing may be written for an unbalanced generation")
        async def commit(self): type(self).commits += 1
        async def rollback(self): pass

    writer = ce._BulkEvaluationWriter(_Session())
    s, r = Cand(3).rows(pid, "x", "9" * 64)                            # a plain rejection -> aggregated
    writer.add(s)
    writer.add(r)
    writer._aggregator.total += 5
    with pytest.raises(ce.EvaluationAccountingError):
        await writer.commit()
    assert _Session.commits == 0


async def test_status_caps_overflow_into_exact_aggregates(project_id, monkeypatch):
    session, pid = project_id
    monkeypatch.setattr(cret, "OPPORTUNITY_CAP", 4)
    monkeypatch.setattr(ce, "OPPORTUNITY_CAP", 4)
    cands = candidates(1200)
    w = await finish(await stream(session, pid, cands, engine_version="t-cap", fingerprint="a" * 64, bounded=True))
    w._assert_accounting()
    rows = await _rows(session, "t-cap")
    assert {idx_of(r.name) for r in rows} == expected_retained(cands, opportunity_cap=4)
    by_status = Counter(cands[idx_of(r.name)].status for r in rows)
    assert by_status["CO_PRO_OPPORTUNITY"] == 4 and by_status["FEASIBILITY_REVIEW_REQUIRED"] == 4
    overflow = sum(1 for c in cands if c.status == "CO_PRO_OPPORTUNITY") - 4
    assert sum(g["candidate_count"] for g in w._aggregator.rows() if g["candidate_status"] == "CO_PRO_OPPORTUNITY") == overflow


async def test_group_count_is_bounded_by_the_fine_group_cap_with_exact_counts(project_id, monkeypatch):
    session, pid = project_id
    monkeypatch.setattr(cagg, "FINE_GROUP_CAP", 25)
    cands = candidates(3000)
    w = ce._BulkEvaluationWriter(session, chunk_rows=50)
    w._aggregator = cagg.CandidateAggregator()          # picks up the patched cap
    w = await finish(await stream(session, pid, cands, engine_version="t-fine", fingerprint="b" * 64, bounded=True, writer=w))
    w._assert_accounting()
    fine = sum(1 for g in w._aggregator.rows() if not g["representative"] is None and g["program_slugs"])
    coarse = w._aggregator.group_count - fine
    assert fine <= 25 and coarse > 0
    assert w._aggregator.counted() == w._aggregator.total == 3000 - w.results_written
    assert w._aggregator.group_count < 25 + len(TYPES) * 8 * 32   # coarse groups are keyed by status/type/reason/primary jurisdiction


async def test_a_read_between_structure_and_result_keeps_exact_accounting(project_id):
    """A read that arrives between a structure and its result promotes the pending structure
    (read-your-writes). The result is then a plain physical row, counted once."""
    session, pid = project_id
    writer = ce._BulkEvaluationWriter(session, chunk_rows=1000)
    s, r = Cand(3).rows(pid, "t-ryw", "c" * 64)                        # a plain rejection
    writer.add(s)
    assert (await writer.execute(text("SELECT count(*) FROM production_structures WHERE id = :i"), {"i": s.id})).scalar() == 1
    writer.add(r)
    writer._finalize_retention()
    await writer._drain(promote_pending=True)
    assert writer._aggregator.total == 0 and writer.results_written == 1 and writer.generated_results == 1
    writer._assert_accounting()


async def test_reuse_probe_and_freshness_recognise_a_generation_with_no_detailed_rows(project_id):
    """A generation whose every candidate was aggregated has only its summary row + aggregates: still a
    complete, current, reusable evaluation."""
    session, pid = project_id
    writer = ce._BulkEvaluationWriter(session, chunk_rows=1000)
    for i in (3, 22, 41 + 38):                                          # plain rejections only (idx % 19 == 3)
        c = Cand(i)
        assert c.kind == "plain-rejected"
        s, r = c.rows(pid, ce.ENGINE_VERSION, "d" * 64)
        writer.add(s)
        writer.add(r)
    writer._finalize_retention()
    await writer._drain(promote_pending=True)
    assert writer.results_written == 0 and writer._aggregator.total == 3
    writer._assert_accounting()
    await writer._persist_generation_summary()
    assert await ce.current_result_fingerprint(session, pid) == "d" * 64
