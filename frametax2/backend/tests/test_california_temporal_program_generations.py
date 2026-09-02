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


async def test_lips_california_baseline_is_recognized_but_not_priced():
    """Runtime proof of the fail-closed half.

    California is a COMPETITIVE, ranked allocation requiring a Credit
    Allocation Letter before principal photography -- not an entitlement. So
    Lips' baseline must be RECOGNIZED (US-CA, disclosed, with the reason) and
    must carry NO deterministic economics. A blocked baseline must also never
    hand the recommendation to an incomparable relocation.
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
    assert summary["baseline_blocked"] is True
    baseline = summary["baseline"]
    assert baseline is not None, (
        "failing closed must DISCLOSE the baseline, not drop it -- no number, "
        "never no row"
    )
    assert baseline["is_baseline"] is True
    assert baseline["true_net_cost_usd"] is None
    assert baseline["total_incentive_value_usd"] is None
    assert "NON_GUARANTEED_SELECTIVE" in (baseline["reason"] or "")

    assert summary["top_result"] is None, (
        "an incomparable relocation was promoted over a recognized baseline "
        "purely because its raw NPC is lowest"
    )


def test_competitive_allocation_implies_non_guaranteed_selective():
    """The generic invariant behind the repair: the two canonical registries
    may never disagree about whether an award is an entitlement."""
    from app.data.authority_coverage_registry import coverage_state
    from app.data.program_requirements import all_program_requirements

    for slug, profile in all_program_requirements().items():
        allocation = str(getattr(profile, "allocation_type", "") or "").upper()
        if "COMPETITIVE" not in allocation:
            continue
        assert coverage_state(slug) != "PRICEABLE_VALIDATED", (
            f"{slug} is declared COMPETITIVE but is treated as a guaranteed "
            "entitlement by the authority-coverage gate"
        )
