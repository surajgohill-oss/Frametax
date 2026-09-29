"""
test_multi_program_qpe_reconciliation.py

Independent expected-value tests for the multi-program QPE double-counting
defect: canonical_evaluation.py's multi-program stack path already computes
both total_claim_bases_usd (the sum of each stacked program's own reusable
claim base — legitimately overlapping) and total_qualifying_spend_usd (the
TRUE exact union of qualifying line IDs, overlapping lines counted once),
but canonical_production_view.py never served either field, so every
consumer fell back to summing segments[].qpe_usd — which equals
total_claim_bases_usd, the WRONG, doubled figure for any structure whose
stacked programs share a spend base (Little Utopia's real Ontario
OPSTC+OCASE stack: served "Qualified Spend $8,126,528" instead of the real
$4,063,264).

Live DB integration test against the acceptance database (asserts the exact
DB name before running, per the required hard gate) — the only way to prove
canonical_production_view.py's own serving code, not a re-derivation.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    from app.db.session import engine
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB:
        pytest.skip(f"resolved database is {db_name!r}, not the approved acceptance database {APPROVED_DB!r}")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_ontario_multi_program_stack_serves_the_true_unique_qpe_not_the_doubled_claim_base_sum(db: AsyncSession):
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    # Mirrors the real GET /state route exactly: evaluate_project() first
    # (idempotent/reused when the persisted generation is already current),
    # then the view builder — build_production_and_structures() alone does
    # not populate the bounded structures[] page.
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]
    all_entries = (
        (structures.get("structures") or [])
        + (structures.get("optimizer_scenarios") or [])
        + (structures.get("optimizer_candidates") or [])
        + list((structures.get("best_per_jurisdiction") or {}).values())
    )
    ontario_stacks = [
        e for e in all_entries
        if e and e.get("primary_jurisdiction") == "CA-ON"
        and e.get("total_claim_bases_usd") is not None
        and e.get("total_qualifying_spend_usd") is not None
    ]
    assert ontario_stacks, "expected at least one served Ontario multi-program stack with both QPE fields populated"
    entry = ontario_stacks[0]

    claim_bases = entry["total_claim_bases_usd"]
    unique_qpe = entry["total_qualifying_spend_usd"]
    served_qpe = entry["qpe_usd"]

    # The confirmed live defect: claim_bases is the doubled sum (both
    # programs claiming against the same underlying spend); unique_qpe is
    # the real, exact, de-duplicated total.
    assert claim_bases > unique_qpe, (
        "the sum of per-program claim bases must be strictly greater than the true unique "
        "qualifying spend for a genuinely overlapping multi-program stack — if they're equal, "
        "either the stack no longer overlaps (fine) or the fixture/data changed; investigate"
    )
    # The one authoritative field every consumer (Overview/Workspace/Globe/
    # Inspector/hero) must read: the TRUE unique figure, never the claim-base sum.
    assert served_qpe == unique_qpe, (
        f"qpe_usd (${served_qpe:,.2f}) must equal the real unique total_qualifying_spend_usd "
        f"(${unique_qpe:,.2f}), never the doubled total_claim_bases_usd (${claim_bases:,.2f})"
    )

    # Per-program disclosure must still be real and inspectable — never
    # hidden just because the top-level qpe_usd is now the reconciled figure.
    segments = entry.get("segments") or []
    on_segments = [s for s in segments if s.get("jurisdiction_code") == "CA-ON"]
    assert len(on_segments) >= 2, "both stacked Ontario programs' own per-program QPE must remain individually disclosed in segments[]"


async def test_every_served_multi_program_stack_across_the_project_has_a_reconciled_qpe_at_least_as_small_as_its_claim_base_sum(db: AsyncSession):
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]
    all_entries = (
        (structures.get("structures") or [])
        + (structures.get("optimizer_scenarios") or [])
        + (structures.get("optimizer_candidates") or [])
    )
    checked = 0
    for e in all_entries:
        claim_bases = e.get("total_claim_bases_usd")
        unique_qpe = e.get("total_qualifying_spend_usd")
        if claim_bases is None or unique_qpe is None:
            continue
        checked += 1
        assert unique_qpe <= claim_bases, (
            f"{e.get('structure_id')}: total_qualifying_spend_usd (${unique_qpe:,.2f}) can never exceed "
            f"total_claim_bases_usd (${claim_bases:,.2f}) — the union of qualifying lines is always <= the sum of overlapping claim bases"
        )
        assert e.get("qpe_usd") == unique_qpe
    assert checked > 0, "expected at least one served multi-program stack with both QPE fields present"
