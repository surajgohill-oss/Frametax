"""
Producer Display Names + Budget Rail User Assumptions closeout — Finance
Costs regression tests.

Mirrors the existing contingency_expected_utilization_pct precedent
end-to-end: a producer-settable ProjectFact (financing_cost_usd), read
generically by build_project_economic_inputs, threaded into
price_allocated_structure's existing financing_cost_usd NPC parameter
(never a new economic doctrine — see allocation_pricing.price_allocated_
structure's own "Financing... default to zero — explicit inputs only"
docstring), and covered by the evaluation cache fingerprint so a change
can never serve a stale NPC.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import derive_qualification_register
from app.calculators.qualification_model import MU_TERRITORIAL_TEXT
from app.db.session import engine
from app.models.enums import ProjectFactSourceType
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import _compute_fingerprint
from app.services.canonical_project_economics import (
    FACT_FINANCING_COST_USD,
    build_project_economic_inputs,
    production_facts_for,
)

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
        # Never leave test-written financing_cost_usd facts behind — this
        # fixture cleans up after every test in this file regardless of
        # outcome, so a failed assertion can't leak persisted test data
        # into the real project row.
        await session.execute(
            delete(ProjectFact).where(
                ProjectFact.project_id == LITTLE_UTOPIA_PROJECT_ID,
                ProjectFact.fact_key == FACT_FINANCING_COST_USD,
            )
        )
        await session.commit()


async def _price_little_utopia(inputs):
    register = derive_qualification_register(
        inputs.budget_lines,
        program_slug="mu_edb_incentive",
        facts=production_facts_for(inputs),
        rate=0.40,
        program_territorial_text=MU_TERRITORIAL_TEXT,
    )
    spec = StructureSpec(
        structure_id="TEST-MU-FINANCING",
        structure_type="single_country",
        label="MU — test",
        primary_jurisdiction="MU",
        participants=("MU",),
        incentive_programs={"MU": "mu_edb_incentive"},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    return price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
    )


async def test_financing_cost_defaults_to_unset_not_zero(db: AsyncSession):
    """Genuinely absent — never coerced to 0.0 at the input-resolution
    layer (price_allocated_structure applies its own 0.0 default at the
    pricing boundary, same as every other adjustment)."""
    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    assert inputs.financing_cost_usd is None


async def test_financing_cost_persists_through_the_generic_project_fact_write_path(db: AsyncSession):
    """The SAME ProjectFact table / USER_OVERRIDE precedence as
    contingency_expected_utilization_pct — no second persistence
    mechanism. Writes directly against the model (equivalent to what
    POST /projects/{id}/assumptions does) and confirms the read path
    resolves it back."""
    db.add(ProjectFact(
        id=uuid.uuid4(), project_id=LITTLE_UTOPIA_PROJECT_ID, fact_key=FACT_FINANCING_COST_USD,
        value="15000", value_type="number",
        source_type=ProjectFactSourceType.USER_OVERRIDE.value,
    ))
    await db.commit()

    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    assert inputs.financing_cost_usd == 15000.0


async def test_financing_cost_shifts_npc_by_exactly_the_persisted_amount_never_qpe(db: AsyncSession):
    """The exact canonical treatment already documented in
    allocation_pricing.price_allocated_structure: financing_cost_usd adds
    straight onto NPC (npc_verified_usd / npc_with_adjustments_usd) and
    never touches selected_incentive_usd/QPE — a financing assumption is
    not automatically incentive-qualifying spend merely because a
    producer enters it."""
    baseline_inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    baseline_pricing = await _price_little_utopia(baseline_inputs)

    db.add(ProjectFact(
        id=uuid.uuid4(), project_id=LITTLE_UTOPIA_PROJECT_ID, fact_key=FACT_FINANCING_COST_USD,
        value="15000", value_type="number",
        source_type=ProjectFactSourceType.USER_OVERRIDE.value,
    ))
    await db.commit()

    adjusted_inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    adjusted_pricing = await _price_little_utopia(adjusted_inputs)

    assert adjusted_pricing.npc_verified_usd == round(baseline_pricing.npc_verified_usd + 15000.0, 2)
    assert adjusted_pricing.npc_with_adjustments_usd == round(baseline_pricing.npc_with_adjustments_usd + 15000.0, 2)
    # Never QPE-affecting: the selected incentive is untouched by a pure
    # NPC-side financing assumption.
    assert adjusted_pricing.selected_incentive_usd == baseline_pricing.selected_incentive_usd
    # Source budget is untouched — editing the assumption never rewrites
    # the imported gross budget.
    assert adjusted_pricing.gross_budget_usd == baseline_pricing.gross_budget_usd


async def test_financing_cost_participates_in_the_evaluation_cache_fingerprint(db: AsyncSession):
    """A change to the persisted assumption must invalidate any
    previously-cached evaluation row — same mechanism already proven for
    contingency_expected_utilization_pct."""
    inputs_unset = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    fp_unset = _compute_fingerprint(inputs_unset)

    db.add(ProjectFact(
        id=uuid.uuid4(), project_id=LITTLE_UTOPIA_PROJECT_ID, fact_key=FACT_FINANCING_COST_USD,
        value="15000", value_type="number",
        source_type=ProjectFactSourceType.USER_OVERRIDE.value,
    ))
    await db.commit()

    inputs_set = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    fp_set = _compute_fingerprint(inputs_set)

    assert fp_unset != fp_set


async def test_financing_cost_assumption_endpoint_key_is_whitelisted_generically(db: AsyncSession):
    """POST /projects/{id}/assumptions' whitelist accepts financing_cost_usd
    for ANY project — no project id/title branch. Import-level check
    (avoids spinning up the full ASGI app in this module): confirms the
    key is present in the same generic whitelist contingency uses."""
    from app.api.v1.cineglobe import _PROJECT_ASSUMPTION_FACT_KEYS
    assert "financing_cost_usd" in _PROJECT_ASSUMPTION_FACT_KEYS
    assert "contingency_expected_utilization_pct" in _PROJECT_ASSUMPTION_FACT_KEYS
