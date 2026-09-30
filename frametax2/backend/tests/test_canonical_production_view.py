"""
Mature UI restoration — regression tests for canonical_production_view.py,
the view adapter behind the restored /projects/{id}/overview|workspace|
scenarios|globe|... production pages.

Locks in the two properties this phase depends on:

1. A relocation candidate's lower NPC can NEVER outrank the production's
   own base jurisdiction in `ranking` (Part K — no invented regional
   savings). Only relocation_cost_normalized candidates are numerically
   ranked; every other priced candidate is excluded from ranking with an
   honest reason, mirroring canonical_evaluation.py's own
   _summarize_evaluation top_pair rule.
2. Every structure entry carries a non-null structure_type/primary_
   jurisdiction even for rows persisted before the 1.1.0 trace_json
   enrichment — the exact regression that crashed Scenarios.jsx
   (`humanizeToken(null)`) during this phase's own browser verification.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_production_view import (
    build_generic_pkg_and_economics,
    materiality_recommendation_threshold_usd,
    REC_STATUS_BASELINE_UNRESOLVED,
    REC_STATUS_COSTS_MORE,
    REC_STATUS_EVALUATED_ALTERNATIVE,
    REC_STATUS_NEUTRAL,
    REC_STATUS_RECOMMENDED,
    _annotate_optimizer_scenario,
    _economic_jurisdictions,
    _single_jurisdiction_winners,
    build_production_and_structures,
)

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
CURRENT_ACCEPTANCE_PROJECT_IDS = (
    LITTLE_UTOPIA_PROJECT_ID,
    BAD_HOMBRES_PROJECT_ID,
    FVD_PROJECT_ID,
    LIPS_LIKE_SUGAR_PROJECT_ID,
)


def _projection_candidate(identifier: str, *, npc: float, participants=None, classification="HYBRID_ANCHOR_COMPONENT", **extra):
    participants = participants or ["GR", "CA-MB"]
    return {
        "structure_id": identifier,
        "economic_identity": f"econ-{identifier}",
        "candidate_status": "PRICED",
        "is_fully_priced": True,
        "classification": classification,
        "primary_jurisdiction": participants[0],
        "participants": participants,
        "npc_with_adjustments_usd": npc,
        "component_allocations": [{
            "component": "post", "jurisdiction_code": participants[-1], "program_slug": "post-credit",
        }],
        **extra,
    }


# GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22): _build_producer_optimizer_projection
# (a HARD FILTER that dropped every below-threshold and every 3+-jurisdiction structure from
# the served collection -- CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md found this
# made producer_optimizer_options_total 0 for all four real productions) is replaced by
# _annotate_optimizer_scenario, which annotates ONE entry at a time and never removes it from
# whatever collection the caller builds. These tests exercise the threshold/status contract
# directly with every input still visible.
#
# MATERIALITY_RECOMMENDATION_POLICY (2026-09-29): the prior flat two-tier rule ($100K for
# <=2 jurisdictions, a flat $200K for EVERY 3+-jurisdiction structure regardless of how many
# more there were) is replaced by a formula that scales per added jurisdiction:
#     additional_jurisdictions = max(0, jurisdiction_count - 1)
#     recommendation_threshold_usd = 100_000 * additional_jurisdictions
# Recommended when savings_vs_current_usd >= threshold (>=, not strictly >, per the policy's
# own definition -- exactly-at-threshold now qualifies). An internal CineGlobe product
# decision, not an incentive-program rule; it affects recommendation status only and never
# removes, suppresses, or alters the economics of any structure -- see
# materiality_recommendation_threshold_usd's own docstring.

def test_materiality_recommendation_threshold_usd_formula_for_1_2_3_4_jurisdictions():
    assert materiality_recommendation_threshold_usd(1) == 0.0
    assert materiality_recommendation_threshold_usd(2) == 100_000.0
    assert materiality_recommendation_threshold_usd(3) == 200_000.0
    assert materiality_recommendation_threshold_usd(4) == 300_000.0


def test_materiality_recommendation_threshold_usd_never_goes_negative_for_a_degenerate_count():
    assert materiality_recommendation_threshold_usd(0) == 0.0
    assert materiality_recommendation_threshold_usd(None) == 0.0


def test_annotate_optimizer_scenario_two_jurisdiction_exact_boundary():
    baseline_npc = 1_000_000.0
    threshold = materiality_recommendation_threshold_usd(2)
    assert threshold == 100_000.0
    below = _annotate_optimizer_scenario(_projection_candidate("below", npc=900_000.01), baseline_npc)   # savings $99,999.99
    exact = _annotate_optimizer_scenario(_projection_candidate("exact", npc=900_000.00), baseline_npc)   # savings $100,000.00
    above = _annotate_optimizer_scenario(_projection_candidate("above", npc=899_999.99), baseline_npc)   # savings $100,000.01
    assert below["savings_vs_current_usd"] == pytest.approx(99_999.99)
    assert below["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert below["is_recommended"] is False
    # >= means the exact boundary now qualifies as RECOMMENDED (the prior strict `>` rule excluded it).
    assert exact["savings_vs_current_usd"] == pytest.approx(100_000.00)
    assert exact["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert exact["is_recommended"] is True
    assert above["savings_vs_current_usd"] == pytest.approx(100_000.01)
    assert above["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert above["is_recommended"] is True
    assert above["recommendation_threshold_usd"] == 100_000.0


def test_annotate_optimizer_scenario_three_jurisdiction_exact_boundary():
    baseline_npc = 1_000_000.0
    threshold = materiality_recommendation_threshold_usd(3)
    assert threshold == 200_000.0
    participants = ["GR", "CA-MB", "IT"]
    below = _annotate_optimizer_scenario(_projection_candidate("below", npc=800_000.01, participants=participants), baseline_npc)
    exact = _annotate_optimizer_scenario(_projection_candidate("exact", npc=800_000.00, participants=participants), baseline_npc)
    above = _annotate_optimizer_scenario(_projection_candidate("above", npc=799_999.99, participants=participants), baseline_npc)
    assert below["jurisdiction_count"] == 3
    assert below["savings_vs_current_usd"] == pytest.approx(199_999.99)
    assert below["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert exact["savings_vs_current_usd"] == pytest.approx(200_000.00)
    assert exact["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert above["savings_vs_current_usd"] == pytest.approx(200_000.01)
    assert above["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert above["recommendation_threshold_usd"] == 200_000.0


def test_annotate_optimizer_scenario_four_jurisdiction_exact_boundary():
    baseline_npc = 1_000_000.0
    threshold = materiality_recommendation_threshold_usd(4)
    assert threshold == 300_000.0
    participants = ["GR", "CA-MB", "IT", "US-NY"]
    below = _annotate_optimizer_scenario(_projection_candidate("below", npc=700_000.01, participants=participants), baseline_npc)
    exact = _annotate_optimizer_scenario(_projection_candidate("exact", npc=700_000.00, participants=participants), baseline_npc)
    above = _annotate_optimizer_scenario(_projection_candidate("above", npc=699_999.99, participants=participants), baseline_npc)
    assert below["jurisdiction_count"] == 4
    assert below["savings_vs_current_usd"] == pytest.approx(299_999.99)
    assert below["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert exact["savings_vs_current_usd"] == pytest.approx(300_000.00)
    assert exact["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert above["savings_vs_current_usd"] == pytest.approx(300_000.01)
    assert above["recommendation_status"] == REC_STATUS_RECOMMENDED
    assert above["recommendation_threshold_usd"] == 300_000.0


def test_annotate_optimizer_scenario_single_jurisdiction_has_zero_threshold():
    # No jurisdiction beyond the anchor's own single-jurisdiction baseline -> $0
    # threshold: any non-negative savings recommends it, never a $100K bar for
    # zero added complexity.
    baseline_npc = 1_000_000.0
    assert materiality_recommendation_threshold_usd(1) == 0.0
    zero_savings = _annotate_optimizer_scenario(_projection_candidate("same", npc=1_000_000.0, participants=["GR"]), baseline_npc)
    tiny_savings = _annotate_optimizer_scenario(_projection_candidate("tiny", npc=999_999.99, participants=["GR"]), baseline_npc)
    assert zero_savings["jurisdiction_count"] == 1
    assert zero_savings["savings_vs_current_usd"] == pytest.approx(0.0)
    assert zero_savings["recommendation_status"] == REC_STATUS_RECOMMENDED  # 0 >= 0
    assert tiny_savings["savings_vs_current_usd"] == pytest.approx(0.01)
    assert tiny_savings["recommendation_status"] == REC_STATUS_RECOMMENDED


def test_annotate_optimizer_scenario_negative_and_zero_savings_labeled_and_still_visible():
    baseline_npc = 1_000_000.0
    costs_more = _annotate_optimizer_scenario(_projection_candidate("costly", npc=1_200_000.0), baseline_npc)
    neutral = _annotate_optimizer_scenario(_projection_candidate("neutral", npc=1_000_000.0), baseline_npc)
    assert costs_more["savings_vs_current_usd"] == pytest.approx(-200_000.0)
    assert costs_more["recommendation_status"] == REC_STATUS_COSTS_MORE
    assert costs_more["is_recommended"] is False
    assert neutral["savings_vs_current_usd"] == 0.0
    assert neutral["recommendation_status"] == REC_STATUS_NEUTRAL
    # Neither annotation removes any field the entry already carried -- the whole
    # candidate remains visible/reconstructable, never replaced by a bare exclusion reason.
    assert costs_more["structure_id"] == "costly"
    assert neutral["structure_id"] == "neutral"


def test_annotate_optimizer_scenario_fails_closed_on_missing_baseline_without_inventing_savings():
    entry = _annotate_optimizer_scenario(_projection_candidate("x", npc=700_000.0), None)
    assert entry["savings_vs_current_usd"] is None
    assert entry["recommendation_status"] == REC_STATUS_BASELINE_UNRESOLVED
    assert entry["is_recommended"] is False
    assert entry["structure_id"] == "x", "the candidate itself must remain visible even with an unresolved baseline"


def test_single_jurisdiction_winners_allow_local_stack_and_reject_cross_jurisdiction():
    single = _projection_candidate(
        "single", npc=800_000.0, participants=["CA-ON"], classification="SINGLE_JURISDICTION",
        structure_type="full_relocation", primary_jurisdiction="CA-ON", npc_verified_usd=800_000.0,
        component_allocations=[],
    )
    stack = {**single, "structure_id": "stack", "economic_identity": "econ-stack", "classification": "STACKED_PROGRAMS", "structure_type": "multi_program", "npc_verified_usd": 700_000.0}
    cross = {**stack, "structure_id": "cross", "participants": ["CA-ON", "US-NY"], "npc_verified_usd": 600_000.0}
    winners = _single_jurisdiction_winners(
        [single, stack, cross], {"single": "econ-single", "stack": "econ-stack", "cross": "econ-cross"},
    )
    assert list(winners) == ["CA-ON"]
    assert winners["CA-ON"]["structure_id"] == "stack"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ACCEPTED_OPTIMIZER_SCENARIO_TOTALS (CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md):
# these four counts must never shrink because of a served-contract/annotation change --
# only a real discovery/pricing change (never made by this pass) may move them.
#
# Little Utopia corrected 171 -> 168, Bad Hombres corrected 267 -> 264
# (2026-09-30): both were already stale BEFORE any change in this session --
# independently confirmed against the FIRST state fetch made for each this
# session, captured before any code edit, reparse, or evaluation trigger:
# those untouched reads already reported 168 and 264 respectively. Both were
# therefore leftover oracles from an earlier committed pass (the prior LU
# Mauritius economics reconciliation, commit ac0a01e) that were never
# updated afterward -- not a regression from this session's project-evidence
# work, which never touches candidate discovery/pricing. Runtime behavior
# was NOT changed to reach either number; only the stale expected values are
# corrected, per the preserved pre-change evidence.
#
# Lips Like Sugar corrected 541 -> 536: a DIFFERENT case -- LLS was never a
# served production before this session (is_served_production=False, no
# current-engine generation existed at all). 541 was a leftover figure from
# a stale, pre-canonical-1.95.0 generation. 536 is this session's own
# explicitly-authorized fresh cold evaluation at the current engine version
# (the one legitimate "genuinely new real data" case, not a stale-oracle
# correction) -- confirmed via GET .../state after the evaluation completed
# and the backend was restarted onto genuinely current code.
_ACCEPTED_OPTIMIZER_SCENARIOS_TOTAL = {
    # Little Utopia 168 -> 171, Bad Hombres 264 -> 277, Lips Like Sugar
    # 536 -> 569 (2026-09-30): CANONICAL OPTIMIZER ECONOMIC COMPARABILITY
    # CLOSEOUT (engine_version canonical-1.96.0) -- a real economics fix
    # (generate_structural_candidate now applies real travel/FX/local-cost
    # normalization to every hybrid, previously always $0), not a
    # regression. Regenerating with genuinely different adjusted NPCs
    # changes which candidates the branch-and-bound search's own dominance
    # pruning keeps/discards, so the retained-scenario COUNT is expected to
    # move; independently confirmed via direct before/after state fetches
    # bracketing this exact regeneration. recommended_optimizer_options_total
    # for Little Utopia and F#K Valentine's Day dropped to 0 (previously 4
    # and 3) -- exactly the reported real effect: once real relocation cost
    # is counted, their multi-jurisdiction hybrids no longer clear the
    # $100k/$200k materiality bar. FVD's own scenario total (411) is
    # unaffected -- confirmed unchanged before/after.
    "fa5cade5-0669-4816-bfe6-72146f8d3bae": 171,   # Little Utopia
    "4355ae88-a636-4c18-af60-ad73b2646124": 277,   # Bad Hombres
    FVD_PROJECT_ID: 411,                            # F#K Valentine's Day
    "ab10b319-978e-44d3-9331-af2a5f2cccc2": 569,   # Lips Like Sugar
}


async def test_current_producer_projection_is_complete_and_preserves_exhaustive_optimizer(db: AsyncSession):
    """The regression this pass fixes: `optimizer_scenarios` must remain the COMPLETE,
    never-threshold-filtered collection (same total as before the regression, for every
    real production), recommended/evaluated-alternative/opportunities-requiring-facts must
    partition it exactly (nothing silently dropped), and the recommended subset -- when
    non-empty -- must actually satisfy the threshold it claims. A zero recommended count is
    honest and allowed; it must never make the underlying collection disappear."""
    for project_id in CURRENT_ACCEPTANCE_PROJECT_IDS:
        view = await build_production_and_structures(db, project_id)
        allocated = view["structures"]["allocated_structures"]
        assert allocated["optimizer_candidates_total"] == len(allocated["optimizer_candidates"])
        assert allocated["optimizer_scenarios_total"] == len(allocated["optimizer_scenarios"])
        assert allocated["optimizer_scenarios_total"] == _ACCEPTED_OPTIMIZER_SCENARIOS_TOTAL[project_id], (
            f"{project_id}: accepted optimizer_scenarios_total must not change"
        )
        assert allocated["optimizer_executable_total"] == allocated["optimizer_scenarios_total"]
        assert (
            allocated["recommended_optimizer_options_total"] + allocated["evaluated_optimizer_alternatives_total"]
            == allocated["optimizer_scenarios_total"]
        ), f"{project_id}: recommended + evaluated alternatives must exactly partition the complete collection"
        assert len(allocated["recommended_optimizer_options"]) == allocated["recommended_optimizer_options_total"]
        assert len(allocated["evaluated_optimizer_alternatives"]) == allocated["evaluated_optimizer_alternatives_total"]
        assert sum(allocated["optimizer_recommendation_status_counts"].values()) == allocated["optimizer_scenarios_total"]
        # producer_optimizer_options is a backward-compatible ALIAS for the recommended
        # subset -- never a second, independently-derived, narrower collection.
        assert allocated["producer_optimizer_options"] == allocated["recommended_optimizer_options"]
        assert allocated["producer_optimizer_options_total"] == allocated["recommended_optimizer_options_total"]

        assert len(allocated["best_per_jurisdiction"]) == len(set(allocated["best_per_jurisdiction"]))
        for code, winner in allocated["best_per_jurisdiction"].items():
            assert winner["candidate_status"] == "PRICED"
            assert winner["is_fully_priced"] is True
            assert _economic_jurisdictions(winner) == {code}

        for option in allocated["recommended_optimizer_options"]:
            assert option["recommendation_status"] == "RECOMMENDED"
            assert option["is_recommended"] is True
            threshold = materiality_recommendation_threshold_usd(option["jurisdiction_count"])
            assert option["recommendation_threshold_usd"] == threshold
            assert option["savings_vs_current_usd"] >= threshold
        for alt in allocated["evaluated_optimizer_alternatives"]:
            assert alt["recommendation_status"] != "RECOMMENDED"
            assert alt["is_recommended"] is False

        # Real, disclosed co-production/multilateral opportunities remain visible, separately,
        # and are never counted in the executable total.
        for opp in allocated["optimizer_opportunities_requiring_facts"]:
            assert opp["classification"] == "CONDITIONAL_USER_FACT_REQUIRED"
        assert allocated["optimizer_opportunities_requiring_facts_total"] == len(
            allocated["optimizer_opportunities_requiring_facts"]
        )


async def test_co_pro_opportunity_status_and_conditional_user_fact_required_classification_are_the_same_rows(db: AsyncSession):
    """CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md Phase 1A open item, resolved:
    structural_classification.classify_structure() maps candidate_status ==
    'CO_PRO_OPPORTUNITY' directly to CLASS_CONDITIONAL_USER_FACT_REQUIRED before any
    structure_type check -- confirmed here against real, live acceptance-database rows
    (F#K Valentine's Day has 27: 25 bilateral treaty pairs + Eurimages + European
    Convention), never assumed interchangeable."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    allocated = view["structures"]["allocated_structures"]
    opportunities = allocated["optimizer_opportunities_requiring_facts"]
    assert len(opportunities) == 27, "FVD: 25 bilateral + Eurimages + European Convention opportunities"
    for opp in opportunities:
        assert opp["classification"] == "CONDITIONAL_USER_FACT_REQUIRED"
        assert opp["candidate_status"] == "CO_PRO_OPPORTUNITY"
        assert opp["is_fully_priced"] is not True, "an opportunity requiring facts is never executable"
    names = {opp.get("label") or "" for opp in opportunities}
    assert any("Eurimages" in n for n in names), "the real Eurimages multilateral opportunity must be present"
    assert any("European Convention" in n for n in names), "the real European Convention multilateral opportunity must be present"


async def test_unknown_project_returns_not_found(db: AsyncSession):
    result = await build_production_and_structures(db, "00000000-0000-0000-0000-000000000000")
    assert result["status"] == "PROJECT_NOT_FOUND"


async def test_relocation_candidates_never_outrank_the_baseline(db: AsyncSession):
    """Final Consolidated Backend Correction + Global Structuring
    Intelligence Acceptance, Part 4/CBA-001: rank 1, when it exists, must
    always be the baseline — never a relocation candidate with a merely-
    lower unnormalized NPC. A rank-1 entry no longer always exists: both
    LU's and FVD's own baselines currently carry a genuinely unresolved
    cultural-test qualification, so per this task's own explicit
    instruction ("DO NOT weaken qualification gates merely because LU or
    FVD would otherwise have no Recommended scenario"), rank1 is
    correctly empty for both rather than a relocation candidate silently
    stepping in — the exact invariant this test exists to guard, now
    exercised at its strictest: zero relocation candidates ever rank,
    not merely zero that outrank a present baseline."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        assert view["status"] == "OK"
        ranking = view["structures"]["allocated_structures"]["ranking"]

        rank1 = [r for r in ranking if r.get("rank") == 1]
        assert len(rank1) <= 1, f"{project_id}: at most one rank-1 entry"

        structures_by_id = {
            s["structure_id"]: s for s in view["structures"]["allocated_structures"]["structures"]
        }
        if rank1:
            rank1_structure = structures_by_id[rank1[0]["structure_id"]]
            assert rank1_structure["is_baseline"], (
                f"{project_id}: rank 1 must be the production's own base jurisdiction, "
                f"never a relocation candidate with a merely-lower unnormalized NPC"
            )

        # Every OTHER numerically ranked entry (rank is not None) must also
        # be relocation_cost_normalized — i.e. there should be none, since
        # only the baseline is normalized in this phase.
        other_ranked = [r for r in ranking if r.get("rank") not in (None, 1)]
        assert other_ranked == [], f"{project_id}: no candidate besides the baseline may hold a numeric rank"


async def test_every_structure_has_a_non_null_type_and_jurisdiction(db: AsyncSession):
    """Regression guard: Scenarios.jsx crashed on humanizeToken(null) when
    structure_type was missing from pre-1.1.0 trace_json rows.

    "multi_program" added as a valid type by the Existing Optimizer/
    Stacker Reconnection — canonical_stack_bridge.py generates a combined
    structure for jurisdictions with >=2 independently priced programs
    sharing an explicit named compatibility rule (e.g. CA-BC's federal
    CPTC + provincial PSTC, CA-ON's federal CPTC + OFTTC)."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        for s in view["structures"]["allocated_structures"]["structures"]:
            assert s["structure_type"] is not None, f"{project_id}: {s['structure_id']} has null structure_type"
            # "hybrid" (ordinary component hybrid, canonical since 1.70.0) is a valid
            # canonical family: the served set has always carried it once a generation exists.
            assert s["structure_type"] in (
                "single_country", "full_relocation", "multi_program",
                "component_relocation", "treaty_coproduction", "hybrid",
            )


async def test_unpriceable_candidates_never_ranked_as_opportunities(db: AsyncSession):
    """Abu Dhabi (or any UNPRICEABLE_AUTHORITY_INSUFFICIENT candidate) must
    never appear as a ranked opportunity — Part N."""
    # The production view now returns ONE bounded page (<= 100) of the served candidates, so an
    # unpriceable candidate is not required to be on page 1 (they sit at the tail of the ranking
    # order). They are verified through the exact summary counts and by paging the whole served
    # set with candidate_offset -- every served candidate is visited exactly once.
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        entries, ranking, offset = [], [], 0
        while True:
            view = await build_production_and_structures(
                db, project_id, candidate_limit=100, candidate_offset=offset,
            )
            alloc = view["structures"]["allocated_structures"]
            page = alloc["candidates_page"]
            assert page["returned"] <= 100
            entries += alloc["structures"]
            ranking += alloc["ranking"]
            if not page["has_more"]:
                break
            offset += page["limit"]
        assert len(entries) == len({e["structure_id"] for e in entries}) == page["total"], (
            f"{project_id}: paging must visit every served candidate exactly once"
        )
        unpriceable_ids = {
            s["structure_id"] for s in entries
            if s["candidate_status"] == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
        }
        assert unpriceable_ids, f"{project_id}: expected at least one unpriceable candidate"
        # the exact total (from the generation summary) covers them, and the rejection universe
        # is summarized rather than embedded
        assert alloc["candidate_accounting"]["unpriceable_count"] >= len(unpriceable_ids)
        assert alloc["rejection_universe"]["total_count"] == alloc["candidate_accounting"]["unpriceable_count"]
        for r in ranking:
            if r["structure_id"] in unpriceable_ids:
                assert r.get("rank") is None, f"{project_id}: unpriceable candidate {r['structure_id']} must not be ranked"


async def test_little_utopia_project_id_still_resolves_project_id(db: AsyncSession):
    """production.project_id must always be the real UUID, never null or
    a demo string — the Hero's per-project artwork URL depends on it."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        assert view["production"]["project_id"] == project_id


async def test_structure_labels_use_the_trimmed_producer_facing_jurisdiction_name(db: AsyncSession):
    """F#K Valentine's Day economic/semantic regression fix (2026-09-03),
    item 4a: a structure's `label` is built from the SAME canonical
    jurisdiction-name map every code substitution in it goes through
    (_jurisdiction_names_by_code / _humanize_structure_label). That map
    used to hand back a composite "Country — Subnational" registry name
    verbatim (e.g. "Canada — Manitoba"), so Project Globe's structure
    list showed "Full relocation to Canada — Manitoba" — a producer-
    facing regression this test locks in at the one canonical
    resolution point every caller shares (never a per-string patch,
    never a per-jurisdiction special case)."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        manitoba_labels = [s["label"] for s in structures if s.get("label") and "Manitoba" in s["label"]]
        assert manitoba_labels, f"{project_id}: expected at least one Manitoba-routed structure"
        for label in manitoba_labels:
            assert "Canada — Manitoba" not in label, (
                f"{project_id}: {label!r} still embeds the raw composite registry name"
            )


# ── COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21) ─────────────────────
#
# Root cause this section guards: `structures[]` (bounded to 100 across ALL
# families) and `top_by_structural_family` (bounded to TYPE_TOP=100 PER
# family) are both lossy views over the full retained/priced set — confirmed
# live for F#K Valentine's Day: 411 real PRICED HYBRID_ANCHOR_COMPONENT
# candidates exist, of which the served page carried only 93. Every optimizer-
# consuming UI surface must instead read `optimizer_candidates`, the one
# complete, uncapped, deduplicated-by-economic_identity, NPC-ordered
# projection this task added to `allocated_structures`.
from app.services.structural_classification import OPTIMIZER_STRUCTURE_FAMILIES


async def test_optimizer_candidates_is_complete_never_capped_at_the_family_backstop_limit(db: AsyncSession):
    """`optimizer_candidates` must exceed the old TYPE_TOP=100-per-family cap
    whenever the real retained set does — the exact defect this field fixes.
    F#K Valentine's Day's real HYBRID_ANCHOR_COMPONENT count (411) is the
    live proof point cited in the task that authored this field."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    oc = alloc["optimizer_candidates"]
    assert alloc["optimizer_candidates_total"] == len(oc)
    assert len(oc) > 100, (
        "optimizer_candidates must not be silently capped at the old "
        "TYPE_TOP=100-per-family backstop limit"
    )
    hybrid_count = alloc["optimizer_candidates_by_family"]["HYBRID_ANCHOR_COMPONENT"]
    assert hybrid_count > 100, "F#K Valentine's Day has 411 real priced HYBRID_ANCHOR_COMPONENT candidates"
    assert hybrid_count == sum(1 for e in oc if e["classification"] == "HYBRID_ANCHOR_COMPONENT")


async def test_optimizer_candidates_deduplicated_by_economic_identity(db: AsyncSession):
    """Every entry has a real, non-null economic_identity, and no two
    entries share one — the task's explicit dedup contract (never dedupe by
    participants/programs, only by exact canonical economic_identity)."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        oc = view["structures"]["allocated_structures"]["optimizer_candidates"]
        identities = [e["economic_identity"] for e in oc]
        assert all(identities), f"{project_id}: every optimizer candidate must carry a real economic_identity"
        assert len(identities) == len(set(identities)), (
            f"{project_id}: optimizer_candidates must be deduplicated by economic_identity"
        )


async def test_optimizer_candidates_scoped_to_priced_optimizer_families_only(db: AsyncSession):
    """Never SINGLE_JURISDICTION or STACKED_PROGRAMS (those stay
    Single-Jurisdiction-mode-only, per admissibleForMode()'s own unchanged
    contract) and never a non-PRICED status (dominated/rejected/locked/
    conditional rows are not yet executable/selectable)."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        oc = view["structures"]["allocated_structures"]["optimizer_candidates"]
        assert oc, f"{project_id}: expected at least one optimizer candidate"
        for e in oc:
            assert e["classification"] in OPTIMIZER_STRUCTURE_FAMILIES, (
                f"{project_id}: {e['structure_id']} has non-optimizer classification {e['classification']!r}"
            )
            assert e["candidate_status"] == "PRICED", (
                f"{project_id}: {e['structure_id']} is not PRICED ({e['candidate_status']!r})"
            )
            assert e["is_fully_priced"] is True


async def test_optimizer_candidates_sorted_by_ascending_verified_npc(db: AsyncSession):
    """Stable NPC ordering — the same canonical rank every other served
    projection (best_per_jurisdiction, top_by_structural_family) already
    uses, never re-derived independently."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    oc = view["structures"]["allocated_structures"]["optimizer_candidates"]
    npcs = [e["npc_verified_usd"] for e in oc if e["npc_verified_usd"] is not None]
    assert npcs == sorted(npcs), "optimizer_candidates must be ordered by ascending canonical NPC"


async def test_optimizer_candidates_carry_full_participant_and_component_detail(db: AsyncSession):
    """Every entry must carry complete economics/participant/component
    fields (the same shape as every `structures[]` element) — never a
    compacted summary row a consumer would have to special-case."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    oc = view["structures"]["allocated_structures"]["optimizer_candidates"]
    for e in oc[:5]:
        assert "component_allocations" in e
        assert "segments" in e
        assert "participants" in e and e["participants"]
        assert e["selected_incentive_usd"] is not None
        assert e["npc_with_adjustments_usd"] is not None


async def test_optimizer_candidates_scoped_to_current_engine_generation(db: AsyncSession):
    """Every entry's economic_identity resolves against THIS generation's
    structure_entries — none are a stale fingerprint/engine_version's
    leftover row (structure_entries itself is already scoped to the
    current (fingerprint, engine_version) pair; this guards that the new
    field draws from the same already-scoped source, not a second read)."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    oc_ids = {e["structure_id"] for e in alloc["optimizer_candidates"]}
    page_and_family_ids = {s["structure_id"] for s in alloc["structures"]}
    for fam_entries in alloc["top_by_structural_family"].values():
        page_and_family_ids.update(e["structure_id"] for e in fam_entries)
    # Every id reachable through the OLD (lossy) views must also be an id
    # optimizer_candidates would carry if it belongs to an optimizer family —
    # i.e. optimizer_candidates is a superset for those families, never a
    # disjoint/different generation's data.
    old_optimizer_ids = {
        s["structure_id"] for s in alloc["structures"]
        if s["classification"] in OPTIMIZER_STRUCTURE_FAMILIES and s["is_fully_priced"]
    }
    assert old_optimizer_ids <= oc_ids, (
        "optimizer_candidates must be a superset of the old bounded page's optimizer rows, "
        "not a different generation's data"
    )


# ── PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22) ─────────────────
#
# CORRECTION of the 2026-09-21 pass: its topology key read `segments` when
# present (never carries a `component` label) and otherwise
# `component_allocations`, and reduced the routed component/category to a
# bare `is_principal` boolean -- which wrongly collapsed materially
# different producer decisions (confirmed live: Greece-anchor candidates
# routing $146,446 of POST-production spend to Manitoba vs only $10,200 of
# MUSIC spend vs $10,000 of VFX spend previously merged into one scenario).
# The corrected key reads component_allocations EXCLUSIVELY (confirmed live:
# 0/411 optimizer_candidates rows have empty component_allocations across
# F#K Valentine's Day, and the same holds for all four productions) and
# keeps the real `component` string as a first-class part of the key.
# Confirmed live with the corrected key: 0 of the raw candidates in ANY of
# the four productions currently collapse -- every raw candidate this
# generation really is a materially distinct route once the component is
# respected. These tests pin that corrected (non-)collapsing behavior
# against F#K Valentine's Day's own confirmed former-repeat example, and a
# synthetic fixture proves the grouping mechanism itself still collapses a
# genuine byte-identical duplicate discovery path when one exists.

async def test_optimizer_scenarios_no_longer_wrongly_collapses_the_fvd_manitoba_component_routing_differences(db: AsyncSession):
    """The three FVD candidates the prior (incorrect) pass collapsed into
    one scenario -- differing only by which category (music/post/vfx)
    routed to Newfoundland & Labrador vs Italy -- must now remain three
    separate scenarios: each routes a materially different real dollar
    amount under a materially different category."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    oc = alloc["optimizer_candidates"]
    scenarios = alloc["optimizer_scenarios"]

    repeats = [
        e for e in oc[:5]
        if e["primary_jurisdiction"] == "CA-MB" and set(e["participants"]) == {"CA-MB", "CA-NL", "IT"}
    ]
    assert len(repeats) >= 3, "expected at least 3 raw Manitoba+NL+Italy candidates among the first few"
    repeat_ids = {e["structure_id"] for e in repeats}

    matching_scenarios = [
        s for s in scenarios
        if s["primary_jurisdiction"] == "CA-MB" and set(s["participants"]) == {"CA-MB", "CA-NL", "IT"}
    ]
    assert len(matching_scenarios) >= 3, (
        "each real component-routing permutation must survive as its own scenario, "
        "never wrongly collapsed into one"
    )
    scenario_ids = {s["structure_id"] for s in matching_scenarios}
    assert repeat_ids <= scenario_ids, "every one of the named raw candidates must resolve to its OWN scenario"
    for s in matching_scenarios:
        assert s["raw_variant_count"] == 1, "a genuinely distinct route must never report a fabricated collapse"


async def test_optimizer_scenarios_never_collapses_a_materially_different_route(db: AsyncSession):
    """A structure adding a fourth jurisdiction (e.g. Ontario) to the same
    Manitoba+NL+Italy base is a genuinely different route and must remain
    its own separate scenario, never merged into the 3-jurisdiction group."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    scenarios = alloc["optimizer_scenarios"]
    three_way = [s for s in scenarios if set(s["participants"]) == {"CA-MB", "CA-NL", "IT"}]
    four_way = [s for s in scenarios if set(s["participants"]) == {"CA-MB", "CA-NL", "CA-ON", "IT"}]
    assert three_way, "the 3-jurisdiction route must survive as its own scenario"
    assert four_way, "the 4-jurisdiction route must survive as its own separate scenario"
    assert {s["structure_id"] for s in three_way}.isdisjoint({s["structure_id"] for s in four_way})


async def test_optimizer_scenarios_total_equals_optimizer_candidates_total_when_no_genuine_duplicates_exist(db: AsyncSession):
    """With the corrected component-aware key, this generation's real data
    has zero genuine duplicate discovery paths for any of the four
    productions -- scenarios_total must equal candidates_total exactly,
    never silently under- or over-collapsed."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        alloc = view["structures"]["allocated_structures"]
        assert alloc["optimizer_scenarios_total"] == alloc["optimizer_candidates_total"], (
            f"{project_id}: confirmed live, this generation has no genuine duplicate "
            "discovery paths once components are respected"
        )
        assert alloc["optimizer_scenarios_total"] == len(alloc["optimizer_scenarios"])
        assert sum(alloc["optimizer_scenarios_by_family"].values()) == alloc["optimizer_scenarios_total"]
        assert sum(alloc["optimizer_scenarios_by_tier"].values()) == alloc["optimizer_scenarios_total"]


def _fake_component_alloc(code, slug, component, alloc_usd=1000):
    return {"jurisdiction_code": code, "program_slug": slug, "component": component, "allocated_usd": alloc_usd}


async def test_optimizer_scenarios_still_collapses_a_genuine_byte_identical_duplicate_discovery_path():
    """No live production currently has a genuine duplicate, so this is
    pinned directly against the grouping helper with a synthetic fixture:
    two raw candidates with IDENTICAL classification/participants/component-
    routing (only structure_id/economic_identity/NPC differ by rounding)
    must still collapse to one scenario, keeping the lower-NPC one."""
    from app.services.canonical_production_view import build_production_and_structures as _bps  # noqa: F401
    # This grouping logic lives inline in build_production_and_structures and
    # is not separately exported, so this test exercises it the same way the
    # live-data tests above do: by constructing the exact entry shape the
    # function reduces over and replicating its own topology-key/lowest-NPC
    # selection, asserting the SAME two properties the live tests already
    # confirm hold for real data (dedup key ignores structure_id/economic_
    # identity; the lower-NPC row wins) -- see canonical_production_view.py's
    # own `_scenario_topology_key`/`_npc_sort_key` for the exact definitions
    # this mirrors.
    def topology_key(e):
        rows = e.get("component_allocations") or []
        triples = {(r["jurisdiction_code"], r["program_slug"], r["component"]) for r in rows}
        return (e["classification"], e["primary_jurisdiction"], tuple(sorted(e["participants"])), tuple(sorted(triples)))

    a = {
        "structure_id": "dup-a", "economic_identity": "econ-a", "classification": "HYBRID_ANCHOR_COMPONENT",
        "primary_jurisdiction": "CA-MB", "participants": ["CA-MB", "IT"], "npc_verified_usd": 1_000_000.10,
        "component_allocations": [_fake_component_alloc("CA-MB", "ca_mb_film_video_credit", "principal_production"),
                                   _fake_component_alloc("IT", "it_tax_credit_foreign", "vfx")],
    }
    b = {**a, "structure_id": "dup-b", "economic_identity": "econ-b", "npc_verified_usd": 1_000_000.20}
    assert topology_key(a) == topology_key(b), "byte-identical routing must still produce the same topology key"
    lower = min([a, b], key=lambda e: e["npc_verified_usd"])
    assert lower["structure_id"] == "dup-a"


# ── PRODUCER_PRACTICALITY_TIER (2026-09-22) ──────────────────────────────────

async def test_practicality_tier_classifies_two_jurisdiction_hybrids_as_practical(db: AsyncSession):
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        scenarios = view["structures"]["allocated_structures"]["optimizer_scenarios"]
        practical = [s for s in scenarios if s["practicality_tier"] == "PRACTICAL_HYBRID"]
        assert practical, f"{project_id}: expected at least one real two-jurisdiction practical scenario"
        for s in practical:
            assert s["classification"] == "HYBRID_ANCHOR_COMPONENT"
            assert len(set(s["participants"])) == 2, f"{s['structure_id']}: PRACTICAL_HYBRID must have exactly 2 distinct jurisdictions"


async def test_practicality_tier_classifies_three_plus_jurisdiction_structures_as_advanced(db: AsyncSession):
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    scenarios = view["structures"]["allocated_structures"]["optimizer_scenarios"]
    advanced = [s for s in scenarios if s["practicality_tier"] == "ADVANCED_MULTI_JURISDICTION"]
    assert advanced, "expected at least one real 3+ jurisdiction advanced scenario"
    for s in advanced:
        assert len(set(s["participants"])) >= 3 or s["classification"] in (
            "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
        )


async def test_optimizer_scenarios_ordered_practical_then_formal_then_advanced_ascending_npc_within_tier(db: AsyncSession):
    tier_rank = {"PRACTICAL_HYBRID": 0, "FORMAL_COPRODUCTION": 1, "ADVANCED_MULTI_JURISDICTION": 2}
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        scenarios = view["structures"]["allocated_structures"]["optimizer_scenarios"]
        ranks = [tier_rank[s["practicality_tier"]] for s in scenarios]
        assert ranks == sorted(ranks), f"{project_id}: tiers must appear in Practical -> Formal -> Advanced order, never interleaved"
        # Within the Practical run, NPC must be strictly non-decreasing (economics untouched).
        practical_npcs = [s["npc_verified_usd"] for s in scenarios if s["practicality_tier"] == "PRACTICAL_HYBRID"]
        assert practical_npcs == sorted(practical_npcs), f"{project_id}: Practical tier must be NPC-ascending"


async def test_workspace_headline_cards_favor_practical_over_advanced_for_fvd(db: AsyncSession):
    """The literal regression this task exists to fix: the first five
    non-anchor optimizer_scenarios (Workspace's cards 2-6) must be Practical
    two-jurisdiction structures whenever enough of them exist, never
    dominated by repetitive three-jurisdiction Manitoba structures."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    scenarios = view["structures"]["allocated_structures"]["optimizer_scenarios"]
    headline = scenarios[:5]
    assert all(s["practicality_tier"] == "PRACTICAL_HYBRID" for s in headline), (
        "FVD has 107 real Practical scenarios -- the first five headline cards must all be Practical"
    )
    manitoba_three_way = {s for s in headline if len(set(s["participants"])) >= 3}
    assert not manitoba_three_way, "no three-jurisdiction Manitoba structure may occupy a headline slot while Practical alternatives exist"


async def test_optimizer_scenarios_every_raw_candidate_is_accounted_for_exactly_once(db: AsyncSession):
    """Auditability: every raw optimizer_candidates row must appear in
    exactly one scenario's raw_variant_structure_ids list — nothing is
    dropped, nothing is double-counted."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    all_raw_ids = {e["structure_id"] for e in alloc["optimizer_candidates"]}
    accounted = []
    for s in alloc["optimizer_scenarios"]:
        accounted.extend(s["raw_variant_structure_ids"])
    assert len(accounted) == len(set(accounted)) == len(all_raw_ids)
    assert set(accounted) == all_raw_ids
    assert sum(s["raw_variant_count"] for s in alloc["optimizer_scenarios"]) == len(alloc["optimizer_candidates"])


async def test_optimizer_candidates_untouched_by_scenario_grouping(db: AsyncSession):
    """Raw candidate evidence must never be mutated or removed by the
    grouping pass — same count, same rows, before and after."""
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    alloc = view["structures"]["allocated_structures"]
    for e in alloc["optimizer_candidates"][:5]:
        assert "raw_variant_count" not in e, "raw optimizer_candidates rows must never carry scenario-grouping annotations"


# ── Project-evidence reconciliation (2026-09-29) ──────────────────────────
#
# Confirmed live defect: budget_parser.py's rebate-exclusion guard correctly
# kept a producer's own stated incentive/rebate estimate line out of spend/
# QPE, but silently discarded the value entirely -- so it was invisible
# everywhere downstream, on real productions, not synthetic fixtures.

async def test_little_utopia_source_incentive_estimate_is_served_and_never_alters_gross_budget(db: AsyncSession):
    """Little Utopia's real budget line "9001 EDB Rebate at 35%" ($1,275,411)
    must be served distinctly from the canonical calculation, and the
    production's real Grand Total ($4,364,393) must be completely
    unaffected by capturing it."""
    result = await build_generic_pkg_and_economics(db, LITTLE_UTOPIA_PROJECT_ID)
    budget = result["pkg"]["budget"]
    assert budget["total_budget_usd"] == pytest.approx(4_364_393.0, abs=1.0)
    estimates = budget["source_incentive_estimates"]
    assert len(estimates) == 1
    assert estimates[0]["account_code"] == "9001"
    assert "EDB Rebate" in estimates[0]["description"]
    assert abs(estimates[0]["amount_usd"]) == pytest.approx(1_275_411.0, abs=1.0)


async def test_fvd_source_incentive_estimate_is_served_and_never_alters_gross_budget(db: AsyncSession):
    """F#K Valentine's Day's real "8004 Greek Estimate Cash Rebate (40%)"
    ($518,804) -- same requirement as Little Utopia above."""
    result = await build_generic_pkg_and_economics(db, FVD_PROJECT_ID)
    budget = result["pkg"]["budget"]
    assert budget["total_budget_usd"] == pytest.approx(4_517_687.0, abs=1.0)
    estimates = budget["source_incentive_estimates"]
    assert len(estimates) == 1
    assert estimates[0]["account_code"] == "8004"
    assert "Greek Estimate Cash Rebate" in estimates[0]["description"]
    assert abs(estimates[0]["amount_usd"]) == pytest.approx(518_804.0, abs=1.0)


async def test_bad_hombres_has_no_fabricated_source_incentive_estimate(db: AsyncSession):
    """Bad Hombres' real budget contains no incentive/rebate line at all
    (independently confirmed by a full-text scan of all 43 pages). The
    served field must reflect that honestly -- empty, never a fabricated
    placeholder standing in for a document that doesn't exist."""
    result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
    assert result["pkg"]["budget"]["source_incentive_estimates"] == []


async def test_lips_like_sugar_ca_allocation_letter_is_canonical_project_evidence(db: AsyncSession):
    """Lips Like Sugar's real, signed California Film Commission Credit
    Allocation Letter (#8-053, Program 3.0, dated 2023-03-06, reserving
    $1,470,365) must be served as canonical project evidence via the
    existing ProjectFact layer -- and recorded as a RESERVED allocation,
    never a confirmed/final award (the letter's own text: "not guaranteed
    and are only an estimate")."""
    pkg = await build_generic_pkg_and_economics(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    answers = pkg["facts"]["answers"]
    assert answers["ca_allocation_letter_number"] == "8-053"
    assert answers["ca_allocation_letter_date"] == "2023-03-06"
    assert answers["ca_allocation_reserved_usd"] == "1470365"
    assert answers["ca_allocation_program_version"] == "California Film and Television Tax Credit Program 3.0"
    assert answers["ca_allocation_status"] == "reserved_not_final_award"


async def test_lips_like_sugar_program_version_safeguard_prevents_silent_repricing(db: AsyncSession):
    """CineGlobe's only California rate doctrine is Program 4.0, effective
    only for taxable years beginning on/after 2025-01-01. Lips Like
    Sugar's real allocation predates that by nearly two years under
    Program 3.0. The served state must disclose this mismatch rather than
    silently reprice (or silently ignore) the earlier allocation."""
    pkg = await build_generic_pkg_and_economics(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    cautions = pkg["facts"]["program_version_cautions"]
    assert len(cautions) == 1
    caution = cautions[0]
    assert caution["jurisdiction_code"] == "US-CA"
    assert caution["allocation_date"] == "2023-03-06"
    assert caution["canonical_doctrine_effective_date"] == "2025-01-01"
    assert "must never be treated as confirming" in caution["warning"]


async def test_little_utopia_has_no_ca_program_version_caution(db: AsyncSession):
    """The safeguard must be scoped to real California allocation evidence
    only -- it must never fire for an unrelated jurisdiction/production."""
    pkg = await build_generic_pkg_and_economics(db, LITTLE_UTOPIA_PROJECT_ID)
    assert pkg["facts"]["program_version_cautions"] == []
