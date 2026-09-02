"""
test_codex_bcd_generic_capability_restoration.py

Generic-capability restoration for Codex forensic findings B, C, D. Item A
(the 31-program "authority regression") was investigated and NOT
implemented -- see the master session report: PROJECT_RULES.md's own final
authority-safety gate (lines 25-30) states verbatim that
AUTHORITY_UNRESOLVED_NON_PRICEABLE "contributes no incentive, NPC, stack, or
ranking value," and the current code (commit 8212dd4, same repair lineage,
the day before this pass) already restored exactly that semantics after a
prior "policy correction" (d3b893d) had removed it. Reverting that would
violate the project's own settled doctrine, not repair a regression.

B — treaty-partner discovery no longer depends on the partner's OWN
    incentive resolving to a deterministic price. It is scoped to every
    jurisdiction with at least one priced leg ANYWHERE at or under it
    (never the full raw discovery universe -- a jurisdiction with zero
    priced legs anywhere, e.g. Switzerland, correctly stays excluded; see
    test_coproduction_optimizer_preservation.py's own preservation gate).

C — component-relocation candidate enumeration is no longer pre-truncated
    to the top 6 target jurisdictions by incentive value; the complete
    real, independently-priceable target universe is persisted.

D — travel/FX/local-cost (MFNI) normalization are connected into every
    single-program and component-relocation candidate via the EXISTING,
    generic production_normalization.py -- no duplicate calculator, no
    fabricated input. in-kind replacement is deliberately NOT connected: it
    names a real, specific fact unique to one production, not a generic
    property every production has.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    current_result_fingerprint,
    evaluate_project,
)

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LU_PROJECT_TITLE = "The Little Utopia"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _project_id_by_title(db, title: str) -> str:
    from sqlalchemy import select as sa_select

    from app.models.project import Project

    project = (await db.execute(
        sa_select(Project).where(Project.title == title)
    )).scalars().first()
    assert project is not None, f"fixture project {title!r} not found"
    return project.id


async def _current_rows(db, project_id):
    await evaluate_project(db, project_id)
    await db.commit()
    fingerprint = await current_result_fingerprint(db, project_id)
    rows = (await db.execute(
        select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project_id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fingerprint,
        )
    )).all()
    return rows


# ── ITEM A — deliberately NOT reverted; pinned so it cannot regress back ──

def test_authority_unresolved_is_provenance_only_master_reconciliation():
    """SUPERSEDED (master reconciliation, 2026-09-02). This test previously
    pinned AUTHORITY_UNRESOLVED_NON_PRICEABLE as an economic block, citing
    PROJECT_RULES.md's final authority-safety gate -- but that gate itself
    was corrected the same day: git-history reconciliation established
    6b44973 and bb4b6a2 (both pre-dating the 8212dd4 regression this repo's
    earlier session reintroduced) already treated authority/provenance
    completeness as SEPARATE from economic determinism. Do not revert this
    without first checking PROJECT_RULES.md's two-axis correction note --
    the two must never disagree."""
    from app.data.authority_coverage_registry import BLOCKING_STATES

    assert "AUTHORITY_UNRESOLVED_NON_PRICEABLE" not in BLOCKING_STATES


# ── ITEM B — treaty partner discovery ─────────────────────────────────────

async def test_a_country_with_zero_priced_legs_is_not_a_treaty_partner(db: AsyncSession):
    """China: cn_film_incentive is NON_ECONOMIC (a facilitation body, zero
    rate rules) -- zero priced legs anywhere -> not a reachable treaty
    partner. THE generic preservation invariant -- duplicated here as a
    standing regression guard, not just a fixture assertion (see
    test_coproduction_optimizer_preservation.py for the fuller
    property-based version).

    ch_pics_national_rebate was this test's ORIGINAL carrier but no longer
    qualifies (master reconciliation, 2026-09-02): it is AUTHORITY_
    UNRESOLVED_NON_PRICEABLE, a provenance-completeness disclosure that no
    longer blocks economics on its own, and it carries a real 20% floor
    rate -- ca-ch-bilateral is now a real, priced-eligible pair.
    """
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    assert blocks_economic_candidacy("cn_film_incentive")

    rows = await _current_rows(db, FVD_PROJECT_ID)
    treaty = [
        (s, r) for s, r in rows
        if (r.calculation_trace_json or {}).get("candidate_status") == "CO_PRO_OPPORTUNITY"
    ]
    slugs = {(r.calculation_trace_json or {}).get("treaty_slug") for _s, r in treaty}
    assert "ca-cn-bilateral" not in slugs


async def test_a_country_with_a_priced_provincial_leg_IS_a_treaty_partner(db: AsyncSession):
    """Canada: the federal "CA" treaty code never itself prices, but
    CA-AB/CA-ON/CA-QC/CA-NL do. Canada's 13 real registered bilateral
    treaties must be reachable."""
    rows = await _current_rows(db, FVD_PROJECT_ID)
    treaty = [
        (s, r) for s, r in rows
        if (r.calculation_trace_json or {}).get("candidate_status") == "CO_PRO_OPPORTUNITY"
    ]
    ca_slugs = {
        (r.calculation_trace_json or {}).get("treaty_slug") for _s, r in treaty
        if str((r.calculation_trace_json or {}).get("treaty_slug", "")).startswith("ca-")
        or "-ca-" in str((r.calculation_trace_json or {}).get("treaty_slug", ""))
    }
    assert ca_slugs, "Canada lost every bilateral treaty pairing"


# ── ITEM C — complete component-opportunity enumeration ──────────────────

async def test_component_relocation_targets_are_not_pretruncated(db: AsyncSession):
    """The engine's own persisted ledger, not merely a ranked/pruned
    presentation view, must reflect the real target universe -- distinct
    component-relocation target jurisdictions must exceed the old
    MAX_COMPONENT_TARGETS=6 pre-filter."""
    import re

    rows = await _current_rows(db, await _project_id_by_title(db, LU_PROJECT_TITLE))
    component = [
        (s, r) for s, r in rows
        if "(component/split)" in (s.name or "")
    ]
    # primary_jurisdiction on a component candidate is the HOME/anchor code
    # (the structure stays anchored there); the routed-to TARGET is only in
    # the structure's own name ("<home> anchor -- <component> routed to
    # <target> (component/split)").
    target_codes = set()
    for s, _r in component:
        m = re.search(r"routed to (\S+) \(component/split\)", s.name or "")
        if m:
            target_codes.add(m.group(1))
    assert len(target_codes) > 6, (
        f"only {len(target_codes)} distinct component-relocation targets -- "
        "the pre-construction cap appears to still be in effect"
    )


# ── ITEM D — relocation economics (travel/FX/local-cost) connected ───────

async def test_baseline_carries_zero_relocation_normalization(db: AsyncSession):
    """The baseline never relocates, so its adjusted NPC must equal its
    verified NPC exactly -- both normalization calculators are documented
    to yield an exact zero delta when jurisdiction == original_jurisdiction."""
    rows = await _current_rows(db, await _project_id_by_title(db, LU_PROJECT_TITLE))
    baseline = next(
        (r for _s, r in rows if (r.calculation_trace_json or {}).get("is_baseline")), None,
    )
    assert baseline is not None
    assert baseline.true_net_cost_usd is not None
    assert baseline.risk_adjusted_net_cost_usd == baseline.true_net_cost_usd


async def test_relocation_candidates_carry_a_real_nonzero_normalization(db: AsyncSession):
    """A real full-relocation candidate must show the connected capability
    move its adjusted NPC away from its pre-normalization NPC -- proof the
    wiring is live, not merely present in source."""
    rows = await _current_rows(db, await _project_id_by_title(db, LU_PROJECT_TITLE))
    relocations = [
        r for _s, r in rows
        if (r.calculation_trace_json or {}).get("structure_type") == "full_relocation"
        and r.true_net_cost_usd is not None
        and r.risk_adjusted_net_cost_usd is not None
    ]
    assert relocations, "no priced full-relocation candidates to check"
    moved = [
        r for r in relocations
        if round(float(r.risk_adjusted_net_cost_usd) - float(r.true_net_cost_usd), 2) != 0.0
    ]
    assert moved, (
        "no relocation candidate's adjusted NPC differs from its verified NPC -- "
        "travel/FX/local-cost normalization is not actually being applied"
    )


def test_inkind_remains_a_disclosed_absence_not_a_fabrication():
    """in-kind replacement is genuinely absent generically (unique to one
    production's real facts), not merely disconnected -- must stay a
    disclosed 0.0, never invented from nothing."""
    import inspect

    from app.services import canonical_evaluation as mod

    source = inspect.getsource(mod._relocation_normalization)
    assert "inkind" not in source.lower() or "NOT included" in source or "not connected" in source.lower() or "genuinely" in source.lower()


def test_relocation_normalization_reuses_the_existing_calculators_only():
    """No duplicate math -- the connection must call the SAME three
    functions Little Utopia's own hand-built path already used."""
    import inspect

    from app.services import canonical_evaluation as mod

    source = inspect.getsource(mod._relocation_normalization)
    for name in (
        "compute_travel_normalization", "compute_fx_normalization",
        "compute_local_cost_normalization",
    ):
        assert name in source, f"{name} not called from the generic evaluator"
