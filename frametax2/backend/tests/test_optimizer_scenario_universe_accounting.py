"""Optimizer scenario-universe accounting (canonical-1.104.0, SCENARIO_UNIVERSE_ACCOUNTING).

Reuse-only reads of the four acceptance productions' CURRENT persisted generations (bounded SQL over the
generation summary, the retained rows, the aggregate groups and the proof rows -- never a whole-generation
ORM load, never an evaluation). Each assertion is an independent recomputation of an accounting identity:

  * generated == persisted detailed rows + sum(aggregate group counts); priced splits the same way;
  * every hybrid branch-and-bound search accounts for its whole candidate space:
    total == prod(candidate list sizes) == visited + bound-dominated, and
    visited == evaluated (a persisted or aggregated candidate) + labelled non-route visits;
    the hybrid candidates in the generation are exactly the searches' evaluated combinations;
  * a relocated (non-home) principal anchor routes a SINGLE movable unit (ARCH-01..04) -- the silent drop
    this engine version closes -- while the home anchor's single-unit routes stay in component_relocation;
  * the home component_relocation family reaches every per-component destination program the hybrid
    search routes;
  * the served view reconciles to the same generation (optimizer universe, curation partitions, the
    217-row single-jurisdiction contract).
"""
from __future__ import annotations

import math
import uuid
from collections import Counter

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint
from app.services.canonical_production_view import build_production_and_structures

ACCEPTANCE_DB = "frametax2_claude_optimizer_acceptance_20260919"
PROJECTS = {
    "LU": uuid.UUID("fa5cade5-0669-4816-bfe6-72146f8d3bae"),
    "FVD": uuid.UUID("6c6f1c13-2d49-4bbc-bafb-2a12efa93112"),
    "BH": uuid.UUID("4355ae88-a636-4c18-af60-ad73b2646124"),
    "LLS": uuid.UUID("ab10b319-978e-44d3-9331-af2a5f2cccc2"),
}
HYBRID_FAMILY = "ordinary_component_hybrid"


@pytest.fixture
async def db():
    assert engine.url.database == ACCEPTANCE_DB, f"refusing to run against {engine.url.database!r}"
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.rollback()


async def _generation(db: AsyncSession, project_id):
    fp = await current_generation_fingerprint(db, project_id)
    assert fp, f"{project_id}: no current {ENGINE_VERSION} generation"
    return {"pid": project_id, "fp": fp, "ev": ENGINE_VERSION}


_ROWS = """
    FROM structure_calculation_results r JOIN production_structures ps ON ps.id = r.structure_id
    WHERE ps.project_id = :pid AND r.engine_version = :ev AND r.input_fingerprint = :fp
"""
_AGGS = """
    FROM evaluation_candidate_aggregates
    WHERE project_id = :pid AND engine_version = :ev AND input_fingerprint = :fp
"""


async def _proof_traces(db: AsyncSession, g: dict) -> list[dict]:
    return [t for (t,) in (await db.execute(text(
        "SELECT r.calculation_trace_json" + _ROWS
        + " AND r.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'"
        + " AND r.calculation_trace_json->>'structural_family' = :fam"
    ), {**g, "fam": HYBRID_FAMILY})).all()]


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_generated_equals_persisted_plus_aggregated(db: AsyncSession, name: str):
    g = await _generation(db, PROJECTS[name])
    s = (await db.execute(text(
        "SELECT total_rows, priced_count, unpriced_count, persisted_rows, aggregated_candidates, aggregated_priced,"
        " aggregate_groups, by_disposition FROM evaluation_generation_summaries"
        " WHERE project_id = :pid AND engine_version = :ev AND input_fingerprint = :fp"
    ), g)).one()
    physical, physical_priced = (await db.execute(text(
        "SELECT count(*), count(*) FILTER (WHERE r.true_net_cost_usd IS NOT NULL)" + _ROWS
    ), g)).one()
    groups, grouped, grouped_priced = (await db.execute(text(
        "SELECT count(*), coalesce(sum(candidate_count), 0),"
        " coalesce(sum(candidate_count) FILTER (WHERE candidate_status = 'PRICED'), 0)" + _AGGS
    ), g)).one()
    assert s.total_rows == s.persisted_rows + s.aggregated_candidates == physical + grouped
    assert s.persisted_rows == physical and s.aggregated_candidates == grouped and s.aggregate_groups == groups
    assert s.priced_count == physical_priced + s.aggregated_priced and s.aggregated_priced == grouped_priced
    assert s.total_rows == s.priced_count + s.unpriced_count
    assert sum(s.by_disposition.values()) == s.unpriced_count


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_every_hybrid_search_accounts_for_its_whole_candidate_space(db: AsyncSession, name: str):
    g = await _generation(db, PROJECTS[name])
    proofs = await _proof_traces(db, g)
    assert proofs
    evaluated = 0
    for t in proofs:
        lists = t["component_candidate_lists"]
        assert set(lists) == set(t["component_subset"])  # JSONB does not keep key order
        total, visited = t["total_candidate_combinations"], t["visited_combination_count"]
        assert total == math.prod(len(v) for v in lists.values())
        assert total == visited + t["dominated_combination_count"]
        non_route = t["non_route_combination_counts"]
        assert set(non_route) == {"same_destination_nested_bundle", "same_destination_separate_bundles",
                                  "degenerate_route", "duplicate_route"}
        assert visited == t["evaluated_combination_count"] + sum(non_route.values())
        assert t["stopping_bound_usd"] is None or t["stopping_bound_usd"] <= t["incumbent_value_usd"]
        evaluated += t["evaluated_combination_count"]
    retained = (await db.execute(text(
        "SELECT count(*)" + _ROWS + " AND r.structure_type = 'hybrid'"
        " AND r.calculation_trace_json->>'structural_family' = :fam"
        " AND r.calculation_trace_json->>'candidate_status' <> 'DOMINATED_WITH_PROOF'"
    ), {**g, "fam": HYBRID_FAMILY})).scalar_one()
    aggregated = (await db.execute(text(
        "SELECT coalesce(sum(candidate_count), 0)" + _AGGS + " AND structure_type = 'hybrid' AND structural_family = :fam"
    ), {**g, "fam": HYBRID_FAMILY})).scalar_one()
    # Every hybrid candidate in the generation was produced by exactly one proven search, and every
    # evaluated combination is a candidate: nothing priced outside a proof, nothing proven but missing.
    assert retained + aggregated == evaluated


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_relocated_principal_routes_a_single_movable_unit(db: AsyncSession, name: str):
    pid = PROJECTS[name]
    g = await _generation(db, pid)
    home = (await db.execute(text(
        "SELECT r.calculation_trace_json->>'primary_jurisdiction'" + _ROWS
        + " AND (r.calculation_trace_json->>'is_baseline')::boolean"
    ), g)).scalars().first()
    proofs = await _proof_traces(db, g)
    anchors = {t["anchor_jurisdiction"] for t in proofs}
    units = {u for t in proofs for u in t["component_subset"]}
    single = Counter((t["anchor_jurisdiction"], t["component_subset"][0]) for t in proofs if len(t["component_subset"]) == 1)
    assert home in anchors
    # Expected value: one single-unit search per (non-home anchor, movable unit) -- none for the home anchor,
    # whose single-unit routes are the component_relocation family.
    assert set(single) == {(a, u) for a in anchors - {home} for u in units}
    assert all(n == 1 for n in single.values())
    two_party = (await db.execute(text(
        "SELECT count(*)" + _ROWS + " AND r.structure_type = 'hybrid'"
        " AND r.calculation_trace_json->>'candidate_status' = 'PRICED'"
        " AND r.calculation_trace_json->>'anchor_jurisdiction' <> :home"
        " AND jsonb_array_length(r.calculation_trace_json->'component_allocations') = 2"
    ), {**g, "home": home})).scalar_one()
    assert two_party > 0, f"{name}: no priced relocated-principal two-jurisdiction hybrid is retained"


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_home_component_family_reaches_every_per_component_destination_program(db: AsyncSession, name: str):
    pid = PROJECTS[name]
    g = await _generation(db, pid)
    proofs = await _proof_traces(db, g)
    home = (await db.execute(text(
        "SELECT r.calculation_trace_json->>'primary_jurisdiction'" + _ROWS
        + " AND (r.calculation_trace_json->>'is_baseline')::boolean"
    ), g)).scalars().first()
    wanted = {
        (unit, e["jurisdiction_code"], e["program_slug"])
        for t in proofs if t["anchor_jurisdiction"] == home
        for unit, lst in t["component_candidate_lists"].items() for e in lst
    }
    have = set()
    for (allocs,) in (await db.execute(text(
        "SELECT r.calculation_trace_json->'component_allocations'" + _ROWS + " AND r.structure_type = 'component_relocation'"
    ), g)).all():
        have |= {(a["component"], a["jurisdiction_code"], a["program_slug"]) for a in allocs or []}
    for comps, codes, slugs in (await db.execute(text(
        "SELECT component_family, jurisdiction_codes, program_slugs" + _AGGS + " AND structure_type = 'component_relocation'"
    ), g)).all():
        # a single-route group: its one destination and that destination's program(s)
        for comp in comps or []:
            for code in (c for c in codes if c != home):
                for slug in (s for s in slugs if s):
                    have.add((comp, code, slug))
    assert wanted, f"{name}: the home anchor's hybrid searches list no destinations"
    assert wanted <= have, f"{name}: single-component routes missing from component_relocation: {sorted(wanted - have)[:5]}"


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_served_universe_reconciles_to_the_generation(db: AsyncSession, name: str):
    pid = PROJECTS[name]
    g = await _generation(db, pid)
    view = await build_production_and_structures(db, str(pid))
    a = view["structures"]["allocated_structures"]
    total, persisted, aggregated = (await db.execute(text(
        "SELECT total_rows, persisted_rows, aggregated_candidates FROM evaluation_generation_summaries"
        " WHERE project_id = :pid AND engine_version = :ev AND input_fingerprint = :fp"
    ), g)).one()
    assert a["version"] == ENGINE_VERSION
    assert (a["retention"]["generated_candidates"], a["retention"]["retained_rows"], a["retention"]["aggregated_candidates"]) == (
        total, persisted, aggregated)
    # Every retained priced optimizer-family row is one served optimizer candidate: no identity collapse.
    optimizer_rows = (await db.execute(text(
        "SELECT count(DISTINCT r.economic_identity)" + _ROWS
        + " AND r.true_net_cost_usd IS NOT NULL AND r.structure_type IN ('hybrid', 'component_relocation')"
    ), g)).scalar_one()
    assert a["optimizer_candidates_total"] == len(a["optimizer_candidates"]) == optimizer_rows
    curated, suppressed, music = a["optimizer_scenarios"], a["optimizer_scenarios_music_suppressed"], a["music_carveout"]
    assert sum(e["raw_variant_count"] for e in curated + suppressed) == a["optimizer_candidates_total"]
    assert music["scenarios_before_curation_total"] == len(curated) + len(suppressed)
    assert music["curated_scenarios_total"] == a["optimizer_scenarios_total"] == len(curated)
    assert music["suppressed_total"] == len(suppressed)
    assert all(e["music_carveout_status"] in ("SUPPRESSED_BELOW_THRESHOLD", "SUPPRESSED_COUNTERPART_NOT_ESTABLISHED")
               and e["music_carveout_reason"] for e in suppressed)
    assert a["recommended_optimizer_options_total"] + a["evaluated_optimizer_alternatives_total"] == len(curated)
    assert sum(a["optimizer_recommendation_status_counts"].values()) == len(curated)
    assert a["optimizer_production_fit_counts"]["scenario_total"] == len(curated)
    contract = a["jurisdiction_accounting"]["single_jurisdiction_contract"]
    assert len(contract) == len({r["jurisdiction_code"] for r in contract}) == 217
    assert all(r["category"] for r in contract)
    assert a["optimizer_opportunities_requiring_facts_total"] == len(a["optimizer_opportunities_requiring_facts"])


@pytest.mark.parametrize("name", list(PROJECTS))
async def test_post_vfx_music_package_is_a_real_route_and_never_a_comparison_only_value(db: AsyncSession, name: str):
    """canonical-1.105.0: with Post/VFX and Music spend, the package is a searched routable unit, never searched with its
    own member bundles, so every same-destination collision is the package's own route (zero separate-bundle visits)
    and package structures are persisted/aggregated candidates with distinct economic identities."""
    g = await _generation(db, PROJECTS[name])
    proofs = await _proof_traces(db, g)
    units = {u for t in proofs for u in t["component_subset"]}
    package = "post_vfx_music_package"
    for t in proofs:
        subset = set(t["component_subset"])
        assert not (package in subset and subset & {"post_vfx_package", "music_package"})
    if not {"post_vfx_package", "music_package"} <= units:
        assert package not in units
        return
    assert package in units
    assert sum(t["non_route_combination_counts"]["same_destination_separate_bundles"] for t in proofs) == 0
    packaged = (await db.execute(text(
        "SELECT count(*), count(DISTINCT r.economic_identity)" + _ROWS
        + " AND r.true_net_cost_usd IS NOT NULL AND r.calculation_trace_json::text LIKE '%post_vfx_music_package%'"
    ), g)).one()
    assert packaged[0] > 0 and packaged[0] == packaged[1]
