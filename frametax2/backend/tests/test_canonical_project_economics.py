"""
Canonical evaluation runtime unification — Phase 1 regression tests.

These lock in the single most important property of the unification: the
CANONICAL economic engine can be driven entirely from generic persisted
project evidence, and doing so reproduces Little Utopia's accepted
economics EXACTLY.

Why this matters (the finding that set this phase's direction):

The DB-backed structures path (`app/api/v1/structures.py` ->
`run_full_analysis`, ENGINE_VERSION 0.1.0) is project-generic but
economically legacy — its call chain references none of the validated
canonical layers. Priced against Little Utopia's real budget it returns
$4,181,808.00 with $0.00 incentive, $1,124,013.10 away from the accepted
$3,057,794.90. Unification therefore had to generalize the CANONICAL
engine rather than migrate Little Utopia onto the legacy one.

`test_little_utopia_canonical_npc_reproduced_from_generic_inputs` is the
acceptance test for that inversion: same canonical calculators, inputs
sourced only from `BudgetDocument` / `BudgetLineItem` / `ProjectFact` /
`Project.home_jurisdiction_id`, exact accepted NPC.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import derive_qualification_register
from app.calculators.qualification_model import MU_TERRITORIAL_TEXT
from app.db.session import engine
from app.services.canonical_project_economics import (
    build_project_economic_inputs,
    production_facts_for,
)

#: The real, already-accepted Little Utopia project row.
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

#: Little Utopia Economic Reconciliation (2026-08-30): the 100%-EXPECTED-
#: UTILIZATION SCENARIO figures — computed from the real chain (source
#: budget -> normalized lines -> qualification register -> allocation ->
#: pricing) with contingency_expected_utilization_pct EXPLICITLY set to
#: 100. These are no longer Little Utopia's currently-persisted default
#: (see CURRENT_NPC_USD/CURRENT_INCENTIVE_USD below) — kept here as a
#: fixed, real reference point for the 0%-vs-100% sensitivity proof
#: (test_zero_percent_utilization_would_exclude_the_full_reserve), which
#: passes an explicit override and never reads the persisted fact.
#:
#: Root cause of the $3,722,483.90 vs $3,812,823.20 difference, confirmed
#: and fixed: the real source budget PDF spells the contingency reserve
#: line "Contigency" (missing the 'n', account 8300, $301,131.00).
#: classify_budget_line_items.py's contingency-detection regex didn't
#: tolerate this real misspelling, so the reserve fell into generic
#: "miscellaneous" BTL spend instead of the dedicated contingency
#: category the contingency_expected_utilization_pct mechanism targets —
#: a genuine, GENERIC gap (any production's budget could have this same
#: typo), independently confirmed against app/data/little_utopia_real_
#: budget.py's own hand-verified, account-code-keyed classification
#: (`"8300": "contingency"`), which always correctly classified this
#: exact account regardless of the description text. Fixed centrally
#: (contin?gency), never a Little-Utopia-specific branch. With the fix,
#: the mechanism is genuinely bidirectional against LU's real data — the
#: 100%-vs-0%-utilization swing reproduces the SAME $90,339.30 marginal
#: incentive delta the mechanism has always modeled (Mauritius's real EDB
#: program qualifies 100% of deployed contingency spend, per its
#: existing, unchanged qualification doctrine — not a new assumption).
ACCEPTED_NPC_USD = 3_722_483.90
ACCEPTED_INCENTIVE_USD = 641_909.10
ACCEPTED_GROSS_BUDGET_USD = 4_364_393.00
ACCEPTED_LEAF_SUM_USD = 4_364_395.00

#: Production Page Integrity Closeout (migration 0071): the CURRENT
#: canonical figures — Little Utopia's stale beta 100% contingency-
#: utilization election (migration 0068, "recovered_demo_state"
#: provenance) was removed as a project-name-branched default that never
#: reflected a real producer decision. With no election on file,
#: derive_qualification_register's own existing, unchanged
#: GREY_AREA_REQUIRES_AUTHORITY doctrine applies to the reserve — never
#: silently assumed 0% or 100%. Reproduces the SAME figures as an
#: explicit 0% election (the reserve is excluded from qualifying QPE
#: either way); the distinction from a genuine 0% election is that this
#: state carries no election at all, not a resolved one.
CURRENT_NPC_USD = 3_812_823.20
CURRENT_INCENTIVE_USD = 551_569.80


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_generic_inputs_resolve_from_persisted_project_evidence_only(db: AsyncSession):
    """Every canonical economic input comes from generic persisted rows —
    no Little-Utopia-specific module constant is read."""
    result = await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result.ok, result.blockers
    inputs = result.inputs

    assert inputs.jurisdiction_code == "MU"
    assert len(inputs.budget_lines) == 44
    assert inputs.unparsed_line_descriptions == []
    # Account codes are READ from the document's own line descriptions.
    assert all(line.account_code.isdigit() for line in inputs.budget_lines)
    # The territorial evidence migrated into ProjectFact, not inferred.
    assert inputs.accounts_outside_jurisdiction == frozenset(
        {"5000", "5100", "5200", "5300", "5400", "5500", "6500"}
    )
    assert inputs.offshore_payroll_accounts == frozenset()


async def test_declared_grand_total_is_the_basis_not_the_leaf_sum(db: AsyncSession):
    """The document's own declared total governs; the $2.00 source-document
    rounding variance against the leaf sum is preserved and disclosed,
    never balanced away (SA-1.5 corpus finding)."""
    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    assert inputs.gross_budget_usd == ACCEPTED_GROSS_BUDGET_USD
    assert inputs.leaf_account_sum_usd == ACCEPTED_LEAF_SUM_USD
    assert inputs.reconciliation_variance_usd == 2.00


async def test_little_utopia_canonical_npc_reproduced_from_generic_inputs(db: AsyncSession):
    """THE acceptance test for the runtime unification.

    Canonical calculators (derive_qualification_register ->
    derive_account_allocation -> price_allocated_structure), driven purely
    from generic persisted project evidence, must reproduce the CURRENT
    Little Utopia baseline economics to the cent — as of Production Page
    Integrity Closeout (migration 0071), that means no persisted
    contingency election at all (inputs.contingency_expected_utilization_pct
    is None), not the retired 100% beta default.
    """
    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    assert inputs.contingency_expected_utilization_pct is None

    register = derive_qualification_register(
        inputs.budget_lines,
        program_slug="mu_edb_incentive",
        facts=production_facts_for(inputs),
        rate=0.40,
        program_territorial_text=MU_TERRITORIAL_TEXT,
    )
    assert len(register) == 44

    spec = StructureSpec(
        structure_id="ALLOC-BASELINE-MU",
        structure_type="single_country",
        label="Mauritius single-jurisdiction baseline",
        primary_jurisdiction=inputs.jurisdiction_code,
        participants=(inputs.jurisdiction_code,),
        incentive_programs={inputs.jurisdiction_code: "mu_edb_incentive"},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    pricing = price_allocated_structure(
        spec=spec,
        allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        # Baseline is the production's own geography: no relocation
        # travel/FX/local-cost delta and no in-kind replacement.
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        # Whatever is actually persisted (None, post migration 0071) —
        # same as the served path (canonical_evaluation._price_candidate)
        # threads through. Never hardcoded to a scenario value here.
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
    )

    assert pricing.is_fully_priced is True
    assert round(pricing.selected_incentive_usd, 2) == CURRENT_INCENTIVE_USD
    assert round(pricing.npc_verified_usd, 2) == CURRENT_NPC_USD


async def test_little_utopia_contingency_election_has_no_stale_default(db: AsyncSession):
    """Production Page Integrity Closeout (migration 0071) acceptance proof.

    Little Utopia's migration-0068 beta 100% expected-contingency-
    utilization election (a stale "recovered_demo_state" default, never a
    real producer decision) is gone. The generic
    canonical_project_economics.build_project_economic_inputs seam reads
    whatever is actually persisted — nothing here, currently — and never
    substitutes a Mauritius or Little-Utopia-specific default anywhere in
    the calculators themselves. Confirms the current, honest state is
    reproduced FOR THE CORRECT REASON (no fact on file), not merely that
    a number matches."""
    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs
    assert inputs.contingency_expected_utilization_pct is None

    import inspect

    from app.calculators import allocation_pricing, qualification_derivation
    from app.services import canonical_evaluation

    # None of these three calculators may special-case THIS PRODUCTION
    # (by project id or fixture id) for contingency treatment. A handful
    # of architecture/history comments elsewhere in canonical_evaluation.py
    # legitimately mention the demo module by name (real documentation of
    # a real, separate module relationship, not a project_id/title branch
    # that alters behavior) — checked here for the one thing that would
    # actually be contamination: the literal project id, or any executable
    # (non-comment) special-case. Genuine per-PROGRAM statutory data (e.g.
    # "mu_edb_incentive" keying Mauritius's own real territorial-text
    # citation — any Mauritius production uses that program, not just this
    # one) is not project contamination either.
    for module in (qualification_derivation, canonical_evaluation, allocation_pricing):
        source = inspect.getsource(module)
        assert LITTLE_UTOPIA_PROJECT_ID not in source
        assert 'project_id ==' not in source.replace(" ", "")
        assert "if project.title" not in source


async def test_zero_percent_utilization_would_exclude_the_full_reserve(db: AsyncSession):
    """Little Utopia Economic Reconciliation (2026-08-30): restored to its
    original intent after the real classifier gap (see ACCEPTED_NPC_USD's
    own docstring above — "Contigency", missing the 'n', defeated
    contingency detection) was fixed centrally. Reconciliation proof,
    opposite direction from the 100%-utilization figures above: an
    explicit 0% election (not Little Utopia's own real 100% election, a
    hypothetical override proving the mechanism is genuinely bidirectional
    and generic) excludes the full $301,131.00 reserve, dropping
    incentive/NPC by exactly the real marginal amount Mauritius's own EDB
    program's existing, unchanged doctrine yields for that swing."""
    inputs = (await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID)).inputs

    spec = StructureSpec(
        structure_id="ALLOC-BASELINE-MU-0PCT",
        structure_type="single_country",
        label="Mauritius single-jurisdiction baseline, 0% expected contingency utilization",
        primary_jurisdiction=inputs.jurisdiction_code,
        participants=(inputs.jurisdiction_code,),
        incentive_programs={inputs.jurisdiction_code: "mu_edb_incentive"},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    pricing = price_allocated_structure(
        spec=spec,
        allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        contingency_expected_utilization_pct=0.0,
    )

    assert pricing.is_fully_priced is True
    # The delta is Mauritius's real effective marginal rate on this band of
    # QPE (not a flat 40%/30% headline figure) applied to the $301,131.00
    # reserve — runtime-verified, not assumed. Reproduces the SAME real
    # $90,339.30 the mechanism always modeled, before the classifier gap
    # existed.
    delta = round(ACCEPTED_INCENTIVE_USD - pricing.selected_incentive_usd, 2)
    assert delta == pytest.approx(90_339.30, abs=0.01)
    assert round(pricing.npc_verified_usd - ACCEPTED_NPC_USD, 2) == pytest.approx(90_339.30, abs=0.01)


async def test_canonical_economics_module_reads_no_project_specific_data(db: AsyncSession):
    """The bridge must never import a per-project data module — that is
    exactly the coupling this phase exists to remove. Checked against real
    import statements and branches only; the module docstring legitimately
    names Little Utopia in prose to explain the coupling it removes, same
    convention as the equivalent guards in test_material_routing.py and
    test_project_evaluation.py."""
    import ast
    import inspect

    from app.services import canonical_project_economics as mod

    tree = ast.parse(inspect.getsource(mod))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

    for module_name in imported:
        assert "little_utopia" not in module_name, (
            f"canonical_project_economics.py must stay project-agnostic; "
            f"it imports {module_name!r}"
        )
        assert not module_name.startswith("app.demo"), (
            f"canonical_project_economics.py must not depend on demo state; "
            f"it imports {module_name!r}"
        )

    src = inspect.getsource(mod)
    for banned in ("LITTLE_UTOPIA_REAL", "MU_GROSS_BUDGET_USD", 'jurisdiction_code == "MU"'):
        assert banned not in src, (
            f"canonical_project_economics.py must stay project-agnostic; found {banned!r}"
        )
