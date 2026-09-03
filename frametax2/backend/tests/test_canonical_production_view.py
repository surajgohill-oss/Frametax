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
from app.services.canonical_production_view import build_production_and_structures

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


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
            assert s["structure_type"] in (
                "single_country", "full_relocation", "multi_program",
                "component_relocation", "treaty_coproduction",
            )


async def test_unpriceable_candidates_never_ranked_as_opportunities(db: AsyncSession):
    """Abu Dhabi (or any UNPRICEABLE_AUTHORITY_INSUFFICIENT candidate) must
    never appear as a ranked opportunity — Part N."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        alloc = view["structures"]["allocated_structures"]
        unpriceable_ids = {
            s["structure_id"] for s in alloc["structures"]
            if s["candidate_status"] == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
        }
        assert unpriceable_ids, f"{project_id}: expected at least one unpriceable candidate"
        for r in alloc["ranking"]:
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
            assert "Manitoba" in label
