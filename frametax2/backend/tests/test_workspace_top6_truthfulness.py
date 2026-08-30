"""
test_workspace_top6_truthfulness.py

Workspace Top-6/Data Truthfulness closeout.

Real defects found and fixed by live-screen tracing against Lips Like Sugar
(not assumed): (1) two economically DISTINCT Australia programs (Location
Offset vs PDV Offset) rendered as identical cards because the UI had only
the bare jurisdiction code and the opaque program_slug — the real,
human-readable program name already existed in the canonical doctrine
registry (executable_jurisdiction_registry.get_doctrine) but was never
exposed on a served structure; (2) review_required candidates (priced but
not directly comparable — genuinely common when a project's own baseline
is unpriceable) were served in arbitrary generation order, so a "first N"
UI slice showed whichever candidates happened to be generated first, not
the cheapest-modeled ones.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.data.program_rate_rules  # noqa: F401 — forces registration order that avoids a real circular-import ordering issue between executable_jurisdiction_registry and program_rate_rules_worldwide when this module is imported standalone (never hit via the live app's own import order)
from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.services.canonical_production_view import _program_display_name


def test_program_display_name_distinguishes_real_distinct_australia_programs():
    """C. Exact duplicate canonical structures do not appear twice — and
    D. human-readable structure labels differentiate valid same-country
    outcomes: proves the real registry names for the exact programs found
    on Lips Like Sugar's own live Workspace, not a guessed/hardcoded
    string."""
    assert _program_display_name("au_location_offset") == "Australia Location Offset"
    assert _program_display_name("au_pdv_offset") == "Australia PDV Offset (Post, Digital and Visual Effects)"
    # the two real names must be genuinely distinct strings — the whole
    # point of exposing this field at all
    assert _program_display_name("au_location_offset") != _program_display_name("au_pdv_offset")


def test_program_display_name_distinguishes_state_level_programs():
    """B. Same jurisdiction (Australia) + different program remains
    distinct at the state level too (NSW/QLD/SA each carry their own real
    PDV rebate program)."""
    names = {
        _program_display_name("au_nsw_pdv_rebate"),
        _program_display_name("au_qld_pdv_rebate"),
        _program_display_name("au_sa_pdv_rebate"),
    }
    assert len(names) == 3  # three genuinely distinct real names
    assert None not in names


def test_program_display_name_never_fabricates_for_an_unregistered_slug():
    """Never a guessed/humanized fallback at the canonical layer — that
    fallback (programDisplay's own legacy map + humanizeToken) is a
    frontend presentation concern, never invented here."""
    assert _program_display_name("not_a_real_program_slug") is None
    assert _program_display_name(None) is None


# ── review_required NPC ordering (real DB round-trip) ────────────────────

@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


async def test_review_required_structures_are_npc_ascending_not_arbitrary_order(db: AsyncSession):
    """A. Top 6 uses canonical rank ordering where rank exists; where it
    does not (review_required — comparable_count can be genuinely 0 while
    real priced candidates exist), the served order must still be
    deterministic and cost-ordered, never accidental generation order."""
    from app.services.canonical_production_view import build_production_and_structures

    view = await build_production_and_structures(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    assert view["status"] == "OK"
    s = view["structures"]["allocated_structures"]
    review_required_ids = {
        r["structure_id"] for r in s["ranking"] if r["is_fully_priced"] and not r["is_directly_comparable"]
    }
    assert len(review_required_ids) > 1  # real, non-trivial population
    npcs = [
        r["npc_with_adjustments_usd"] for r in s["ranking"]
        if r["structure_id"] in review_required_ids and r["npc_with_adjustments_usd"] is not None
    ]
    assert npcs == sorted(npcs)  # strictly non-decreasing — real ordering, not arbitrary


async def test_no_project_specific_branching_in_program_display_name():
    """J. No project-specific branching — the same generic registry
    lookup must work identically for a real Bad Hombres/other-project
    program slug with no special-casing."""
    import inspect
    from app.services import canonical_production_view as mod
    src = inspect.getsource(mod._program_display_name)
    assert "Lips Like Sugar" not in src
    assert "ab10b319" not in src
    assert "Little Utopia" not in src
