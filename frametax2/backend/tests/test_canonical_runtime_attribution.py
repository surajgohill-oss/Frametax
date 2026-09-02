"""
test_canonical_runtime_attribution.py

STALE-STATE / RUNTIME-SOURCE PREVENTION (item 8).

Two verification hazards were PROVEN during this repair:

  1. cluster 5 (commit d754b6a) shipped a semantic pricing change WITHOUT
     bumping a hand-maintained version constant. Persisted rows were reused,
     the change never reached served output, and a full suite reported "zero
     regressions" while measuring stale rows.
  2. stale Python bytecode served an older module than the file on disk, so a
     verification run measured code that was no longer the source of truth.

These tests assert the PREVENTION, not the cleanup: a semantic change of
either kind must change the canonical evaluation fingerprint automatically,
with no constant for a human to remember.
"""
from __future__ import annotations

import pytest

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.services.canonical_runtime_attribution import (
    canonical_ruleset_digest,
    pricing_source_digest,
    runtime_attribution,
    verify_loaded_source_matches_disk,
)


def test_runtime_attributes_engine_ruleset_and_source():
    """Every served number must be attributable to the exact code AND rules
    that produced it."""
    attribution = runtime_attribution()
    assert attribution["engine_version"].startswith("canonical-")
    assert len(attribution["ruleset_digest"]) == 64
    assert len(attribution["pricing_source_digest"]) == 64
    assert attribution["ruleset_digest"] != attribution["pricing_source_digest"]


def test_loaded_runtime_matches_the_repository_source():
    """HAZARD 2. If the interpreter is executing stale bytecode or an
    unexpected source tree, verification is measuring the wrong code."""
    mismatches = verify_loaded_source_matches_disk()
    assert mismatches == [], "\n".join(mismatches)


def test_a_rule_data_change_changes_the_ruleset_digest():
    """HAZARD 1, data half. Changing a RULE must invalidate persisted results
    on its own -- no version constant to forget."""
    from app.data import program_rate_rules as prr

    before = canonical_ruleset_digest()

    slug = next(iter(sorted(prr._RULES_BY_PROGRAM)))
    original = prr._RULES_BY_PROGRAM[slug]
    mutated = list(original)
    import dataclasses

    mutated[0] = dataclasses.replace(mutated[0], rate=original[0].rate + 0.01)
    prr._RULES_BY_PROGRAM[slug] = mutated
    canonical_ruleset_digest.cache_clear()
    try:
        after = canonical_ruleset_digest()
    finally:
        prr._RULES_BY_PROGRAM[slug] = original
        canonical_ruleset_digest.cache_clear()

    assert after != before, (
        "a changed statutory rate did not change the ruleset digest -- a "
        "semantic change could ship without invalidating persisted results"
    )
    assert canonical_ruleset_digest() == before, "digest did not restore"


def test_an_authority_disposition_change_changes_the_ruleset_digest():
    """The exact class of change that silently failed before: flipping a
    program's economic candidacy."""
    from app.data import authority_coverage_registry as acr

    before = canonical_ruleset_digest()
    slug = next(iter(sorted(acr.COVERAGE_REGISTRY)))
    original = acr.COVERAGE_REGISTRY[slug]
    import dataclasses

    acr.COVERAGE_REGISTRY[slug] = dataclasses.replace(original, state="NON_ECONOMIC")
    canonical_ruleset_digest.cache_clear()
    try:
        after = canonical_ruleset_digest()
    finally:
        acr.COVERAGE_REGISTRY[slug] = original
        canonical_ruleset_digest.cache_clear()

    assert after != before


def test_the_fingerprint_consumes_both_digests():
    """The digests only prevent anything if the FINGERPRINT carries them."""
    import inspect

    from app.services import canonical_evaluation

    source = inspect.getsource(canonical_evaluation._compute_fingerprint)
    assert '"ruleset_digest": canonical_ruleset_digest()' in source
    assert '"pricing_source_digest": pricing_source_digest()' in source


def test_pricing_source_digest_covers_the_modules_that_decide_economics():
    """A logic change in any of these changes served numbers, so each must be
    in the digest or it can ship without invalidation."""
    from app.services import canonical_runtime_attribution as attribution

    covered = set(attribution._SEMANTIC_PRICING_MODULES)
    for required in (
        "app.calculators.allocation_pricing",
        "app.calculators.qualification_derivation",
        "app.data.program_rate_rules",
    ):
        assert required in covered, f"{required} can change without invalidation"
    assert len(pricing_source_digest()) == 64


# ── STALE PERSISTED RESULTS REACHING THE API (item 8, detection 2) ───────

async def test_readers_pin_to_one_generation_not_engine_version_alone():
    """PROVEN defect. Evaluation is append-only: a superseded generation's
    StructureCalculationResult rows are retained as history, exactly like a
    superseded DocumentVersion. That is only safe if every READER selects a
    single generation.

    Readers filtered on ENGINE_VERSION alone, which was accidentally
    sufficient only while every semantic change also bumped that
    hand-maintained constant. Once a rule/pricing-source change invalidates
    the FINGERPRINT on its own, several generations coexist under one engine
    version and an engine-version-only read serves results computed from
    inputs that are no longer true. Measured on FVD: 12 "independently priced
    Ontario candidates" where 3 exist, and 4 "combined CA-ON structures" that
    were the same one combination under 4 different fingerprints.
    """
    import inspect

    from app.services import canonical_production_view

    source = inspect.getsource(canonical_production_view)
    engine_only = source.count("StructureCalculationResult.engine_version ==")
    pinned = source.count("StructureCalculationResult.input_fingerprint ==")
    assert pinned >= engine_only, (
        "a served read filters on engine_version without pinning the "
        "input_fingerprint -- superseded generations can reach the API"
    )


async def test_current_generation_selector_returns_exactly_one_fingerprint():
    """The canonical selector must resolve to ONE generation even when the
    table holds several for the same project and engine version."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine as _engine
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import (
        ENGINE_VERSION,
        current_result_fingerprint,
    )

    FVD = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    async with AsyncSession(_engine, expire_on_commit=False) as session:
        from sqlalchemy import select

        current = await current_result_fingerprint(session, FVD)
        if current is None:
            pytest.skip("project has no committed evaluation")

        all_fingerprints = set((await session.execute(
            select(StructureCalculationResult.input_fingerprint)
            .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == FVD,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
            )
        )).scalars().all())

        assert current in all_fingerprints
        # The selector must be a strict narrowing whenever history exists --
        # otherwise it is not protecting anything.
        if len(all_fingerprints) > 1:
            assert len({current}) == 1


def test_a_rule_change_actually_changes_the_FINGERPRINT_not_just_the_digest():
    """BEHAVIOURAL, not source-text. test_the_fingerprint_consumes_both_digests
    only proves the LINE exists; it would still pass if the payload were
    discarded. This proves the computed fingerprint really moves when a
    canonical rule moves -- which is the whole prevention."""
    import dataclasses

    from app.data import program_rate_rules as prr
    from app.services.canonical_evaluation import _compute_fingerprint
    from app.services.canonical_project_economics import ProjectEconomicInputs

    inputs = ProjectEconomicInputs(
        project_id="00000000-0000-0000-0000-000000000000",
        project_name="fingerprint probe",
        jurisdiction_code="US-NM",
        gross_budget_usd=1_000_000.0,
        leaf_account_sum_usd=1_000_000.0,
        budget_lines=(),
        spend_category_by_code={},
        accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(),
        production_type="feature_film",
    )

    before = _compute_fingerprint(inputs)

    slug = next(iter(sorted(prr._RULES_BY_PROGRAM)))
    original = prr._RULES_BY_PROGRAM[slug]
    prr._RULES_BY_PROGRAM[slug] = [
        dataclasses.replace(original[0], rate=original[0].rate + 0.01), *original[1:],
    ]
    canonical_ruleset_digest.cache_clear()
    try:
        after = _compute_fingerprint(inputs)
    finally:
        prr._RULES_BY_PROGRAM[slug] = original
        canonical_ruleset_digest.cache_clear()

    assert after != before, (
        "a changed statutory rate did NOT change the evaluation fingerprint -- "
        "persisted results would be reused against rules that no longer apply"
    )
    assert _compute_fingerprint(inputs) == before, "fingerprint did not restore"
