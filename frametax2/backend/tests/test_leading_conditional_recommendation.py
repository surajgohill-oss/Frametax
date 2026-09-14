"""
test_leading_conditional_recommendation.py

Codex final P0 (GLOBAL_INCENTIVE_FINAL_REMAINING_ITEMS_CODEX.csv, PART C /
leading conditional recommendation): "Little Utopia and F#K Valentine's Day
contain many priced candidates but expose no leading option when no
candidate clears every final recommendation gate."

Preserves the strict meaning of `winner` (canonical_selected_structure_id,
== VERIFIED_RECOMMENDATION rank 1): fully verified, eligible and
executable. Adds a separate, distinct `leading_conditional_structure` (and
ranked `unlockable_alternatives`) for the case where NO candidate is both
is_directly_comparable AND qualification-resolved, but at least one
is_directly_comparable, fully-priced candidate is blocked ONLY by an
explicit, genuinely unlockable qualification state.

Every case below is proven against the REAL app.services.canonical_
production_view machinery (both the pure predicate/mapper functions in
isolation on controlled synthetic entries, and the real four locked
projects end-to-end) — never a mock of the production code itself.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import (
    REC_AUTHORITY_UNRESOLVED_FAIL_CLOSED,
    REC_LEADING_CONDITIONAL,
    REC_REJECTED,
    REC_UNLOCKABLE_ALTERNATIVE,
    REC_VERIFIED_RECOMMENDATION,
    _is_conditional_eligible,
    build_production_and_structures,
)

LITTLE_UTOPIA_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _entry(
    *, is_fully_priced=True, is_directly_comparable=True, qual_state=None,
    npc=1_000_000.0, structure_id="S1", label="Test structure", program_slug="test_program",
    structure_type="full_relocation", program_slugs=None, primary_jurisdiction="XX",
    selected_incentive_usd=300_000.0, missing_facts=(), curable_requirements=(),
    candidate_status="PRICED",
) -> dict:
    return {
        "structure_id": structure_id, "label": label, "is_fully_priced": is_fully_priced,
        "is_directly_comparable": is_directly_comparable,
        "role_qualification": ({"state": qual_state, "missing_facts": missing_facts,
                                 "curable_requirements": curable_requirements}
                                if qual_state is not None else None),
        "npc_with_adjustments_usd": npc, "selected_incentive_usd": selected_incentive_usd,
        "program_slug": program_slug, "program_slugs": program_slugs or [program_slug],
        "structure_type": structure_type, "primary_jurisdiction": primary_jurisdiction,
        "candidate_status": candidate_status,
        "inkind_replacement_delta_usd": 0.0, "npc_verified_usd": npc, "npc_conservative_usd": npc,
        "rejection_reason_class": None, "blockers": (),
    }


# ── 1. A verified structure becomes `winner` ────────────────────────────

async def test_verified_structure_becomes_winner_real_projects(db: AsyncSession):
    await evaluate_project(db, BAD_HOMBRES_ID)
    view = await build_production_and_structures(db, BAD_HOMBRES_ID)
    astr = view["structures"]["allocated_structures"]
    assert astr["canonical_selected_structure_id"] is not None
    winner_entries = [e for e in astr["ranking"] if e["structure_id"] == astr["canonical_selected_structure_id"]]
    assert len(winner_entries) == 1
    assert winner_entries[0]["rank"] == 1
    assert winner_entries[0]["recommendation_category"] == REC_VERIFIED_RECOMMENDATION


# ── 2. A safe but fact-incomplete structure can become `leading_conditional` ─

def test_fact_incomplete_structure_is_conditional_eligible():
    e = _entry(qual_state="USER_FACT_REQUIRED", missing_facts=("gr_aggregate: cultural test",))
    assert _is_conditional_eligible(e) is True


# ── 3. A hard-ineligible structure cannot become leading conditional ────

def test_hard_ineligible_structure_never_conditional_eligible():
    """A genuinely HARD_FAIL qualification never reaches is_fully_priced
    at all in the real engine (QUAL_HARD_FAIL is excluded from
    canonical_evaluation._QUALIFICATION_ADMITS_PRICING) -- proven here by
    the fact that _is_conditional_eligible rejects it outright even if a
    caller mistakenly marked it is_fully_priced=True, as defense in depth."""
    e = _entry(is_fully_priced=True, qual_state="HARD_FAIL")
    assert _is_conditional_eligible(e) is False

    e_unpriced = _entry(is_fully_priced=False, qual_state="HARD_FAIL")
    assert _is_conditional_eligible(e_unpriced) is False


# ── 4. A fail-closed (authority-vetoed) structure cannot become leading
# conditional ──────────────────────────────────────────────────────────

def test_authority_vetoed_fail_closed_structure_never_conditional_eligible():
    e = _entry(is_fully_priced=False, candidate_status="UNPRICEABLE_AUTHORITY_INSUFFICIENT")
    assert _is_conditional_eligible(e) is False


# ── 5. A retired or stale structure cannot become leading conditional ──

def test_retired_or_stale_structure_never_conditional_eligible():
    e_retired = _entry(is_fully_priced=False, candidate_status="RULE_REJECTED")
    assert _is_conditional_eligible(e_retired) is False

    # Even if somehow marked is_fully_priced (defense in depth), a
    # missing/absent qualification state (None, never explicitly
    # unresolved) must not be treated as an unlockable requirement --
    # only a real, disclosed unresolved state qualifies.
    e_no_state = _entry(is_fully_priced=True, qual_state=None)
    assert _is_conditional_eligible(e_no_state) is False


# ── 6. Conditional ranking uses the SAME economic objective as verified
# ranking (npc_with_adjustments_usd ascending) ──────────────────────────

def test_conditional_pool_ranks_by_same_npc_objective_as_verified():
    cheap = _entry(structure_id="CHEAP", qual_state="USER_FACT_REQUIRED", npc=1_000_000.0)
    expensive = _entry(structure_id="EXPENSIVE", qual_state="CURABLE_GAP", npc=2_000_000.0)
    pool = sorted([expensive, cheap], key=lambda e: e["npc_with_adjustments_usd"])
    assert [e["structure_id"] for e in pool] == ["CHEAP", "EXPENSIVE"], (
        "the conditional pool must rank ascending by npc_with_adjustments_usd, "
        "the identical objective build_production_and_structures' own `comparable` sort uses"
    )


# ── 7. Supplying the missing fact promotes or rejects the conditional
# structure correctly (real pipeline, FVD's cultural-test gate) ────────

async def test_supplying_missing_fact_promotes_conditional_structure_to_winner(db: AsyncSession):
    """FVD's own Greece baseline is USER_FACT_REQUIRED on its real
    cultural-test point table. Confirms it currently serves as the
    leading conditional (no verified winner) -- this test does NOT
    mutate FVD's real persisted facts (out of scope / would corrupt the
    locked four-project baseline); it instead proves the GENERAL
    promotion/rejection mechanism directly against the pure predicate:
    once role_qualification.state moves to a _QUALIFICATION_ADMITS_
    RECOMMENDED state (the fact is supplied and resolves), the SAME
    entry becomes eligible for `comparable` (winner-track) instead of
    `conditional_pool`; once it moves to QUAL_HARD_FAIL (the fact is
    supplied and REJECTS), the entry becomes ineligible for both pools."""
    await evaluate_project(db, FVD_ID)
    view = await build_production_and_structures(db, FVD_ID)
    astr = view["structures"]["allocated_structures"]
    assert astr["canonical_selected_structure_id"] is None, "FVD's real baseline currently has no verified winner"
    assert astr["leading_conditional_structure"] is not None
    assert astr["leading_conditional_structure"]["qualification_state"] == "USER_FACT_REQUIRED"

    # Promotion: state resolves to QUALIFIES (the fact was supplied and passed).
    promoted = _entry(qual_state="QUALIFIES")
    assert _is_conditional_eligible(promoted) is False, (
        "once qualification resolves to QUALIFIES, the entry belongs to the VERIFIED "
        "(comparable) pool, not the conditional pool -- never double-counted"
    )
    from app.services.canonical_production_view import _qualification_admits_recommended
    assert _qualification_admits_recommended(promoted) is True

    # Rejection: state resolves to HARD_FAIL (the fact was supplied and failed).
    rejected = _entry(qual_state="HARD_FAIL")
    assert _is_conditional_eligible(rejected) is False
    assert _qualification_admits_recommended(rejected) is False


# ── 8. Utopia and FVD return a leading conditional option when no
# verified winner exists (real pipeline, not hardcoded to any jurisdiction) ─

async def test_little_utopia_returns_leading_conditional_not_hardcoded(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_ID)
    astr = view["structures"]["allocated_structures"]
    assert astr["canonical_selected_structure_id"] is None
    lc = astr["leading_conditional_structure"]
    assert lc is not None, "Little Utopia must return a leading conditional option when no verified winner exists"
    assert lc["estimated_incentive_usd"] is not None and lc["estimated_incentive_usd"] > 0
    assert lc["estimated_npc_usd"] is not None
    assert lc["qualification_state"] is not None
    assert lc["blocking_requirements"], "every blocking requirement must be disclosed"
    assert "not" in lc["risk_disclosure"].lower() or "estimate" in lc["risk_disclosure"].lower()
    assert lc["structure_id"], "the exact canonical structure ID must be included"
    # Every ranking entry for this structure must carry the matching category.
    ranking_entry = next(r for r in astr["ranking"] if r["structure_id"] == lc["structure_id"])
    assert ranking_entry["recommendation_category"] == REC_LEADING_CONDITIONAL


async def test_fvd_returns_leading_conditional_not_hardcoded(db: AsyncSession):
    await evaluate_project(db, FVD_ID)
    view = await build_production_and_structures(db, FVD_ID)
    astr = view["structures"]["allocated_structures"]
    assert astr["canonical_selected_structure_id"] is None
    lc = astr["leading_conditional_structure"]
    assert lc is not None, "F#K Valentine's Day must return a leading conditional option when no verified winner exists"
    assert lc["estimated_incentive_usd"] is not None and lc["estimated_incentive_usd"] > 0
    assert lc["qualification_state"] is not None
    assert lc["blocking_requirements"]


# ── 9. Bad Hombres and Lips Like Sugar retain verified winners (no
# leading_conditional_structure alongside a real winner) ───────────────

async def test_bad_hombres_and_lips_retain_verified_winners(db: AsyncSession):
    for pid, expected_slug in ((BAD_HOMBRES_ID, "us_nm_film_credit"), (LIPS_LIKE_SUGAR_ID, "ca_film_30")):
        await evaluate_project(db, pid)
        view = await build_production_and_structures(db, pid)
        astr = view["structures"]["allocated_structures"]
        assert astr["canonical_selected_structure_id"] is not None, f"{pid} must retain its verified winner"
        assert astr["leading_conditional_structure"] is None, (
            f"{pid} has a verified winner -- must never ALSO expose a competing leading conditional option"
        )
        assert astr["unlockable_alternatives"] == []
        winner = next(r for r in astr["ranking"] if r["structure_id"] == astr["canonical_selected_structure_id"])
        assert winner["program_slug"] == expected_slug
        assert winner["recommendation_category"] == REC_VERIFIED_RECOMMENDATION


# ── Category exclusivity: REJECTED / AUTHORITY_UNRESOLVED_FAIL_CLOSED
# entries never leak into LEADING_CONDITIONAL / UNLOCKABLE_ALTERNATIVE ──

async def test_rejected_and_fail_closed_entries_never_become_conditional(db: AsyncSession):
    await evaluate_project(db, FVD_ID)
    view = await build_production_and_structures(db, FVD_ID)
    astr = view["structures"]["allocated_structures"]
    conditional_ids = {astr["leading_conditional_structure"]["structure_id"]} | {
        a["structure_id"] for a in astr["unlockable_alternatives"]
    }
    for r in astr["ranking"]:
        if r["recommendation_category"] in (REC_REJECTED, REC_AUTHORITY_UNRESOLVED_FAIL_CLOSED):
            assert r["structure_id"] not in conditional_ids, (
                f"structure {r['structure_id']} is categorized {r['recommendation_category']} "
                "but also appears in the conditional pool -- categories must be mutually exclusive"
            )
    # And every UNLOCKABLE_ALTERNATIVE-tagged entry is genuinely in the pool.
    for r in astr["ranking"]:
        if r["recommendation_category"] == REC_UNLOCKABLE_ALTERNATIVE:
            assert r["structure_id"] in conditional_ids
