"""
Existing Optimizer/Stacker Reconnection, Task C (hybrid/anchor) —
relationship-type independence regression tests.

Proves "HYBRID does not inherently mean TREATY" using real, already-
persisted structures: a component_relocation candidate carries
"component" (and, once a jurisdiction's conditional funds exist,
"conditional_fund") but never "coproduction"; a treaty_coproduction
candidate carries "coproduction" (and now also "conditional_fund" —
Task C's own composition) but never "component" or "stack". No
structure is generated specially for this test.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_component_relocation_never_carries_coproduction_relationship(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]
    assert comp
    for e in comp:
        assert "component" in e["relationship_types"]
        assert "coproduction" not in e["relationship_types"]
        assert "stack" not in e["relationship_types"]


async def test_treaty_coproduction_carries_coproduction_and_conditional_fund_independently(db: AsyncSession):
    """Task C's own composition: a co-production opportunity ALSO
    exposes conditional_programs -- two independent relationships on one
    structure, proving hybrid semantics without inventing a new
    'structure_type' taxonomy."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    assert treaty
    for e in treaty:
        assert "coproduction" in e["relationship_types"]
        assert "component" not in e["relationship_types"]
        assert "stack" not in e["relationship_types"]
        # Whether conditional_fund is present depends on whether real
        # conditional program nodes exist for this jurisdiction -- assert
        # consistency with the underlying data rather than a fixed count.
        has_conditional = bool(e.get("conditional_programs"))
        assert ("conditional_fund" in e["relationship_types"]) == has_conditional


async def test_multi_program_stack_never_carries_component_or_coproduction_relationship(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    stacks = [e for e in entries if e["structure_type"] == "multi_program"]
    assert stacks
    for e in stacks:
        assert "stack" in e["relationship_types"]
        assert "component" not in e["relationship_types"]
        assert "coproduction" not in e["relationship_types"]


async def test_relationship_types_is_always_a_list_never_none(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    assert entries
    for e in entries:
        assert isinstance(e["relationship_types"], list)
