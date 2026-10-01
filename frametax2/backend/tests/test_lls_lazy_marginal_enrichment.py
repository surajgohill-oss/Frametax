"""LLS closeout (2026-10-01): lazy marginal-jurisdiction enrichment owned by the bounded-retention
writer, and computing canonical economic identity once per candidate.

DB-free: candidates are streamed through ``_BulkEvaluationWriter`` with a session that is never
touched (no drain/commit); retention is finalized in memory and the persisted-row list inspected.
The same deterministic candidate stream used by the bounded-retention tests is run twice: EAGER
(every priced candidate carries its marginal dict from creation, the pre-repair behavior) and LAZY
(a compact primitive descriptor; the enricher runs only for final retained rows)."""
from __future__ import annotations

import uuid
from collections import Counter

from app.services import canonical_evaluation as ce
from tests.test_bounded_candidate_retention import candidates

N = 4000
KEY = "marginal_jurisdiction_benefits_usd"


def _marginal_for(idx: int) -> dict:
    return {f"J{idx % 30:02d}": float(idx) * 1.5, "NZ": float(idx % 7) * 100_000.0}


def _stream(cands, mode: str, enricher_calls: list | None = None):
    writer = ce._BulkEvaluationWriter(None, chunk_rows=10**9)
    if mode == "lazy":
        def enrich(desc):
            enricher_calls.append(desc)
            return _marginal_for(desc[1])
        writer.set_marginal_enricher(enrich)
    pid = uuid.uuid4()
    sid_by_idx = {}
    for c in cands:
        if c.hold in ("before", "released", "leaked"):
            writer.hold_candidate(f"ARCH-{c.idx:06d}")
        s, r = c.rows(pid, "eng", "f" * 64)
        if c.kind == "proof-uuid-ref":
            r.calculation_trace_json["incumbent_structure_id"] = str(sid_by_idx[c.idx - 1])
        elif c.proof_ref:
            r.calculation_trace_json["incumbent_structure_id"] = c.proof_ref
        sid_by_idx[c.idx] = s.id
        if c.priced and c.status == "PRICED":
            if mode == "eager":
                r.calculation_trace_json[KEY] = _marginal_for(c.idx)
            else:
                r.calculation_trace_json[KEY] = None
                r._lazy_marginal = ("hybrid", c.idx, float(c.npc), ("post",), "ANCHOR")
        writer.add(s)
        writer.add(r)
        if c.hold == "after":
            writer.hold_candidate(str(s.id))
        elif c.hold == "released":
            writer.release_candidate(f"ARCH-{c.idx:06d}")
    writer._finalize_retention()
    return writer


def _by_idx(writer):
    return {int(r.calculation_trace_json["reason"].split()[1]): r for r in writer._results}


def test_eager_and_lazy_marginal_enrichment_produce_identical_retained_rows_and_accounting():
    cands = candidates(N)
    eager = _stream(cands, "eager")
    calls: list = []
    lazy = _stream(cands, "lazy", calls)
    e_rows, l_rows = _by_idx(eager), _by_idx(lazy)

    # identical retained set, ordinals, rankings, identities
    assert set(e_rows) == set(l_rows) and len(l_rows) < N / 2
    assert [r.generation_ordinal for r in sorted(e_rows.values(), key=lambda r: r.generation_ordinal)] == \
        [r.generation_ordinal for r in sorted(l_rows.values(), key=lambda r: r.generation_ordinal)]
    for idx, row in l_rows.items():
        assert row.economic_identity == e_rows[idx].economic_identity
        assert row.true_net_cost_usd == e_rows[idx].true_net_cost_usd
        # every retained PRICED row carries the identical (enriched) marginal disclosure
        assert row.calculation_trace_json.get(KEY) == e_rows[idx].calculation_trace_json.get(KEY)
        assert not hasattr(row, "__dict__") or "_lazy_marginal" not in row.__dict__
    retained_priced = [i for i, r in l_rows.items() if cands[i].priced and cands[i].status == "PRICED"]
    assert retained_priced and all(l_rows[i].calculation_trace_json[KEY] == _marginal_for(i) for i in retained_priced)

    # identical aggregate accounting (exact counts, bounds, identities, group keys)
    def groups(w):
        return sorted(
            (g.ordinal, key, g.count, g.min_npc, g.max_npc, g.min_inc, g.max_inc, g.best_identity)
            for key, g in w._aggregator._groups.items())
    assert groups(eager) == groups(lazy)
    for w in (eager, lazy):
        assert w.generated_results == N == len(w._results) + w._aggregator.total
        assert w._aggregator.total == w._aggregator.counted()
    # nothing retained after finalization: no held candidates, no ring, no descriptor-bearing results
    assert lazy._retention.held == {} and len(lazy._retention._ring) == 0

    # operation counts: the marginal pricing runs only for final retained rows, never aggregated ones
    eager_ops = sum(1 for c in cands if c.priced and c.status == "PRICED")
    assert len(calls) == len(retained_priced) <= len(l_rows)
    assert len(calls) * 2 < eager_ops, (len(calls), eager_ops)
    enriched_idx = {d[1] for d in calls}
    assert enriched_idx == set(retained_priced), "non-retained candidates must never invoke the enricher"


def test_deferred_descriptor_is_compact_primitive_data_only():
    cands = candidates(400)
    calls: list = []
    writer = ce._BulkEvaluationWriter(None, chunk_rows=10**9)
    writer.set_marginal_enricher(lambda d: calls.append(d) or {})
    seen = []
    pid = uuid.uuid4()
    for c in cands:
        s, r = c.rows(pid, "eng", "f" * 64)
        if c.priced and c.status == "PRICED":
            r.calculation_trace_json[KEY] = None
            r._lazy_marginal = ("US-GA", "prog", ("post_vfx_package",), ("NZ",), (("NZ", "p"),), float(c.npc))
            seen.append(r._lazy_marginal)
        writer.add(s)
        writer.add(r)
    writer._finalize_retention()

    def primitive(x):
        return x is None or isinstance(x, (str, int, float)) or (
            isinstance(x, tuple) and all(primitive(i) for i in x))
    assert seen and all(primitive(d) for d in seen)
    assert all(primitive(d) for d in calls)
    assert all("_lazy_marginal" not in r.__dict__ for r in writer._results)


def test_canonical_identity_computed_once_per_candidate_and_byte_identical(monkeypatch):
    cands = candidates(1500)
    counter = Counter()
    real = ce.canonical_economic_identity

    def counting(stype, trace):
        counter["n"] += 1
        return real(stype, trace)
    monkeypatch.setattr(ce, "canonical_economic_identity", counting)
    writer = _stream(cands, "eager")
    priced_routed = sum(1 for c in cands if c.priced and c.status == "PRICED")
    assert counter["n"] == priced_routed, "exactly one identity computation per PRICED candidate"
    for idx, row in _by_idx(writer).items():
        c = cands[idx]
        if c.priced and c.status == "PRICED":
            assert row.economic_identity == c.identity == real(c.stype, c.trace), "identity bytes must be unchanged"


def test_route_descriptor_reconstruction_equals_eager_marginal_on_real_components():
    from app.calculators.qualification_derivation import BudgetLine
    from tests.test_structural_archetype_generator import _economic_inputs

    cats = [("1", "principal photography", "production", 2_000_000.0), ("2", "post sound", "post_production", 400_000.0),
            ("3", "vfx work", "vfx", 300_000.0), ("4", "music score", "music", 100_000.0)]
    lines = [BudgetLine(account_code=c, description=d, amount_usd=a, spend_category=cat, is_memo=False,
                        line_id=f"BL-{c}") for c, d, cat, a in cats]
    inputs = _economic_inputs(
        jurisdiction_code="GR", gross_budget_usd=2_800_000.0, leaf_account_sum_usd=2_800_000.0,
        budget_lines=lines, spend_category_by_code={c: cat for c, _, cat, _ in cats})
    progs = {"US-GA": "us_ga_film_credit", "NZ": "new_zealand_screen_production_grant_—_international_post_vfx"}
    _, comps = ce._build_hybrid_route(inputs, "US-GA", "us_ga_film_credit", ("post",), ["NZ"], progs)
    eager = ce._hybrid_marginal_jurisdiction_benefits(comps, "US-GA", 2_800_000.0, inputs, 2_000_000.0)
    descriptor = ("US-GA", "us_ga_film_credit", ("post",), ("NZ",), tuple(sorted(progs.items())), 2_000_000.0)
    d_anchor, d_prog, d_subset, d_jurs, d_progs, d_npc = descriptor
    _, rebuilt = ce._build_hybrid_route(inputs, d_anchor, d_prog, d_subset, list(d_jurs), dict(d_progs))
    assert rebuilt == comps
    assert ce._hybrid_marginal_jurisdiction_benefits(rebuilt, d_anchor, 2_800_000.0, inputs, d_npc) == eager
    assert eager and set(eager) == {"NZ"}
