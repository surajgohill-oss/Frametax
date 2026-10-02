"""Hard-timeout wrapper + performance memo equivalence (2026-10-02). No database."""
from __future__ import annotations

import asyncio

import pytest

from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import BudgetLine
from app.services.bounded_regeneration import (
    ACCEPTANCE_DB, HARD_TIMEOUT_SECONDS, RegenerationTimeout, assert_acceptance_database, run_bounded,
)
from app.services.canonical_program_identity import _aliases_for, alias_memo_scope


def test_hard_ceiling_is_720_seconds_and_acceptance_db_is_asserted():
    assert HARD_TIMEOUT_SECONDS == 720
    assert assert_acceptance_database(f"postgresql+psycopg://u:p@h/{ACCEPTANCE_DB}")
    with pytest.raises(RuntimeError):
        assert_acceptance_database("postgresql+psycopg://u:p@h/frametax2")


def test_a_cpu_bound_evaluation_is_interrupted_at_the_ceiling():
    async def spin():
        while True:          # pure CPU: no await point, only the SIGALRM can stop it
            sum(range(1000))

    with pytest.raises(RegenerationTimeout):
        asyncio.run(run_bounded(spin, timeout_s=0.3, label="spin"))


def test_a_fast_evaluation_returns_its_result_and_clears_the_timer():
    async def quick():
        return 7

    assert asyncio.run(run_bounded(quick, timeout_s=5)) == 7


def test_alias_memo_is_scope_only_and_never_stale_outside_it():
    from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES

    before = _aliases_for("sa_film_commission_rebate")
    with alias_memo_scope():
        assert _aliases_for("sa_film_commission_rebate") == before
        PROGRAM_SLUG_ALIASES["__memo_probe__"] = "sa_film_commission_rebate"
        try:
            assert "__memo_probe__" not in _aliases_for("sa_film_commission_rebate")   # memoized inside the scope
        finally:
            del PROGRAM_SLUG_ALIASES["__memo_probe__"]
    PROGRAM_SLUG_ALIASES["__memo_probe__"] = "sa_film_commission_rebate"
    try:
        assert "__memo_probe__" in _aliases_for("sa_film_commission_rebate")             # exact again outside it
    finally:
        del PROGRAM_SLUG_ALIASES["__memo_probe__"]


def test_allocation_memo_returns_exactly_the_uncached_allocation():
    lines = [BudgetLine("1100", "Director", 100.0, "atl_director"), BudgetLine("2100", "Grip", 200.0, "btl_crew_labor"),
             BudgetLine("3100", "VFX", 300.0, "vfx"), BudgetLine("3200", "Post", 400.0, "post_production")]
    spec = StructureSpec(structure_id="s", structure_type="component_relocation", primary_jurisdiction="GR",
                         participants=("GR", "CA-MB"), component_routes={"vfx": "CA-MB"}, label="t", incentive_programs={})
    plain = derive_account_allocation(lines, {}, spec)
    with alias_memo_scope():
        first = derive_account_allocation(lines, {}, spec)
        second = derive_account_allocation(lines, {}, spec)
    assert plain.assignments == first.assignments == second.assignments
    assert plain.total_allocated_usd == first.total_allocated_usd and plain.conserves
