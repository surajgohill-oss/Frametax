"""
test_california_temporal_program_generations.py

ITEM 5 -- HISTORICAL PROJECT EVIDENCE vs CURRENT PROGRAM RULES.

California runs two overlapping regimes:

  PROGRAM 3.0  Credit Allocation Letter issued before 2025-07-01. 25% base
               transferable credit for independent features; 20% base
               non-refundable, non-transferable for studio features/TV.
  PROGRAM 4.0  applications after 2025-07-01, through 2030-06-30. 35-45%,
               with a refundable election.

A project can hold real, VALID evidence issued under an EARLIER generation --
Lips Like Sugar's Program 3.0 letter is exactly that. Two things must both be
true and are easy to get wrong in opposite directions:

  1. that evidence must stay valid HISTORICAL project evidence, tied to the
     generation that was in force when it was issued; and
  2. it must NEVER overwrite or downgrade the CURRENT canonical rules, which
     are what current optimization prices against.

The generic chain is:

  project evidence -> evidence date / effective period -> historical program
  generation -> project baseline        (preserved, never priced-against)

  canonical rules (current generation)  -> current optimization

These tests pin the separation, so ingesting a historical letter can never
silently move a program's live economics.
"""
from __future__ import annotations

import pytest

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard

LIPS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


def test_canonical_california_rules_are_the_CURRENT_generation():
    """The live ruleset must be Program 4.0, not the 3.0 rates a historical
    letter would state."""
    from app.data.program_requirements import get_program_requirements

    rules = get_rate_rules("us_ca_film_credit")
    rates = {r.rate for r in rules}
    assert rates, "California lost its rate rules"
    # 4.0 is 35-45%; 3.0 was 20-25%. A 3.0 rate leaking into the live ruleset
    # is the exact contamination this test exists to catch.
    assert min(rates) >= 0.30, (
        f"California's live rates {sorted(rates)} include a Program 3.0-era "
        "rate -- historical evidence has contaminated the current ruleset"
    )

    profile = get_program_requirements("us_ca_film_credit")
    facts = getattr(profile, "additional_facts", None) or {}
    assert "program_4_0_window" in facts, (
        "the current generation's effective window is no longer recorded"
    )


def test_historical_evidence_categories_exist_and_are_inert():
    """The Phase E categories preserve historical incentive evidence WITH
    provenance. They are a record, not an input: nothing may derive a rate,
    a coverage disposition or a requirement from them."""
    import inspect

    from app.models.enums import DocumentCategory

    historical = {
        DocumentCategory.PRE_QUALIFICATION,
        DocumentCategory.INCENTIVE_ESTIMATE,
        DocumentCategory.INCENTIVE_APPLICATION,
        DocumentCategory.INCENTIVE_CERTIFICATE,
        DocumentCategory.COST_REPORT,
    }
    assert len(historical) == 5

    # No canonical rule/authority module may read a document category at all:
    # that is the only way a historical letter could reach current pricing.
    from app.data import (
        authority_coverage_registry,
        program_rate_rules,
        program_requirements,
        program_spend_rules,
    )

    for module in (
        program_rate_rules, program_requirements,
        program_spend_rules, authority_coverage_registry,
    ):
        source = inspect.getsource(module)
        assert "DocumentCategory" not in source, (
            f"{module.__name__} reads document categories -- a project's "
            "historical evidence could alter the canonical current ruleset"
        )


def test_a_projects_evidence_cannot_change_the_canonical_ruleset_digest():
    """The runtime attribution digest is derived from canonical rule DATA
    only. If a project document could shift it, project evidence would be
    silently pricing every other project too."""
    from app.services.canonical_runtime_attribution import (
        canonical_ruleset_digest,
        _ruleset_fragments,
    )

    fragments = "\n".join(_ruleset_fragments()).lower()
    for token in ("project_id", "lips like sugar", "credit allocation letter",
                  "document_id", "documentversion"):
        assert token not in fragments, (
            f"canonical ruleset digest contains project-scoped token {token!r}"
        )
    assert len(canonical_ruleset_digest()) == 64


async def test_lips_california_baseline_prices_its_deterministic_floor():
    """MASTER RECONCILIATION (2026-09-02) -- supersedes this test's prior
    premise. Git-history reconciliation established that treating
    AllocationType.COMPETITIVE as a program-wide economic block was itself a
    regression: `allocation_type` has been pure disclosure metadata since
    2026-07-26, us_ca_film_credit was individually, deliberately verified
    priceable via a direct primary-source statute fetch (AB 1138,
    leginfo.legislature.ca.gov, commit ee0e380) before last-known-good, and
    it carries a real, unconditional 35% guaranteed-floor RateRule. Program
    4.0's ranked-allocation/CAL mechanics are a REAL administrative/
    competitive-allocation RISK -- disclosed as a warning (see
    canonical_evaluation._competitive_allocation_disclosure), never a reason
    to zero the deterministic floor rate a producer's own statute guarantees
    once they clear it.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.services.canonical_evaluation import evaluate_project

    async with AsyncSession(engine, expire_on_commit=False) as session:
        summary = await evaluate_project(session, LIPS_PROJECT_ID)
        await session.commit()

    assert summary["base_jurisdiction_code"] == "US-CA", (
        "Lips lost its California baseline identity"
    )
    assert summary["baseline_blocked"] is False
    baseline = summary["baseline"]
    assert baseline is not None
    assert baseline["is_baseline"] is True
    assert baseline["true_net_cost_usd"] is not None
    assert baseline["total_incentive_value_usd"] is not None
    assert baseline["total_incentive_value_usd"] > 0

    assert summary["top_result"] is not None, (
        "a recognized, priced baseline with admitted qualification must be "
        "the recommendation"
    )
    assert summary["top_result"]["structure_id"] == baseline["structure_id"]


async def test_lips_california_discloses_administrative_and_competitive_risk():
    """The administrative/competitive-allocation risk must be disclosed on
    the priced baseline, not silently absorbed into a guaranteed number."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import (
        ENGINE_VERSION,
        current_result_fingerprint,
        evaluate_project,
    )

    async with AsyncSession(engine, expire_on_commit=False) as session:
        await evaluate_project(session, LIPS_PROJECT_ID)
        await session.commit()
        fingerprint = await current_result_fingerprint(session, LIPS_PROJECT_ID)
        rows = (await session.execute(
            select(ProductionStructure, StructureCalculationResult)
            .join(StructureCalculationResult,
                  StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == LIPS_PROJECT_ID,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == fingerprint,
            )
        )).all()

    baseline_row = next(
        r for _s, r in rows if (r.calculation_trace_json or {}).get("is_baseline")
    )
    warnings_text = " ".join(baseline_row.warnings or []).lower()
    assert "administrative/allocation risk" in warnings_text
    assert "competitive" in warnings_text or "preapproval" in warnings_text


def test_competitive_or_discretionary_allocation_never_implies_a_full_block():
    """SUPERSEDED (master reconciliation, 2026-09-02): the prior invariant
    here asserted every COMPETITIVE program must be NON_GUARANTEED_
    SELECTIVE -- that derivation is the repealed regression. The correct
    generic invariant is the OPPOSITE constraint: a program's economic
    candidacy must never be decided by allocation_type alone -- only an
    authored COVERAGE_REGISTRY row (a real, evidenced disposition) may block
    it. This is a standing regression guard against the repealed
    mechanism reappearing."""
    import inspect

    from app.data import authority_coverage_registry as acr

    source = inspect.getsource(acr.get_coverage_status)
    # The function BODY (not its docstring, which legitimately explains the
    # repeal) must never read allocation_type/AllocationType.
    body = source.split('"""', 2)[-1] if source.count('"""') >= 2 else source
    assert "allocation_type" not in body
    assert "AllocationType" not in body
    assert "COVERAGE_REGISTRY.get(program_slug)" in body
