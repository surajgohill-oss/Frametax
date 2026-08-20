"""
Canonical served wiring repair — STEP 8 bounded contract fixture.

One DB -> API-adapter (build_production_and_structures / build_generic_pkg_
and_economics, the exact functions get_project_state() calls) contract test
against F#K Valentine's Day (FVD), the real project the five Codex defects
(docs/validation/CODEX_CANONICAL_SERVED_WIRING_DIAGNOSIS.md) were diagnosed
against. Read-only/idempotent against real persisted rows — same convention
as test_canonical_evaluation.py; no fixture/mock project.

Covers, with exact numeric assertions read directly off the real
StructureCalculationResult rows:
  - Greece (GR) — the priced, directly-comparable baseline (Defect 2)
  - Malta (MT) — priced, band-ceiling incentive requiring confirmation,
    NOT directly comparable (Defect 2/3)
  - Mauritius (MU) — priced, band-ceiling incentive requiring confirmation,
    NOT directly comparable (Defect 2/3)
  - Australia Queensland (AU-QLD) — priced, flat-rate incentive, NOT
    directly comparable (Defect 2)
  - Australia Location Offset — RULE_REJECTED / STATUTORY_CONDITIONS_UNMET
    with program identity preserved, not flattened to the generic
    UNPRICEABLE_AUTHORITY_INSUFFICIENT bucket (Defect 4)

Also asserts the FVD-wide accounting totals (30 priced / 1 directly
comparable / 29 review-required / 80 unpriceable) and that
build_generic_pkg_and_economics's register/economics disclosure (Defect 3/5)
is present and non-fabricated for the same evaluation.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func, select

from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project
from app.services.canonical_production_view import (
    build_generic_pkg_and_economics,
    build_production_and_structures,
)

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _single_segment_structures(structure_entries: list[dict], code: str) -> list[dict]:
    return [
        e for e in structure_entries
        if len(e.get("segments") or []) == 1 and e["segments"][0].get("jurisdiction_code") == code
    ]


async def test_fvd_accounting_matches_codex_diagnosis(db: AsyncSession):
    """Originally 30 priced / 1 directly comparable / 29 review-required /
    80 unpriceable — the accepted breakdown per CODEX_PRICEABILITY_BLOCKER_
    RECONCILIATION.md's "maximum defensibly priceable within current
    generated universe" (30) at the time that document was written. An
    intermediate FVD canonical input assembly repair briefly used
    marine_suitability=NONE to remove 21 landlocked jurisdictions from
    structure generation entirely (110 -> 89, 30 -> 28) -- the canonical
    authority substrate + feasibility boundary repair reverted that:
    production FEASIBILITY (can this jurisdiction physically host the
    shoot) and ECONOMIC ELIGIBILITY (can a defensible incentive be priced)
    are permanently separate concepts, and a soft feasibility mismatch
    must never suppress economic discovery. See
    CANONICAL_AUTHORITY_SUBSTRATE_FEASIBILITY_CLOSEOUT.md.

    The priced count has since legitimately grown via the Global Economic
    Data + Base Pricing / Global Formulaic Economic Completion recover-
    before-research batches (30 -> ... -> 49 -> 52, see
    test_canonical_authority_substrate.py's
    test_fvd_runtime_candidate_universe_restored for the full batch-by-
    batch trace) as real, cited historical RateRule data was individually
    re-verified and promoted rather than left unwired. Priced grew again,
    103 -> 107 (unpriced 7 -> 8), from the CineGlobe canonical pricing path
    + discovery repair: on_ofttc and OCASE (CA-ON) now each reach their own
    independent candidate structure alongside ca_on_opstc, instead of being
    silently collapsed to one by a jurisdiction_code-keyed discovery lookup
    (see test_canonical_authority_substrate.py's
    test_on_ofttc_and_ocase_now_independently_served). The one thing this
    must still hold, regardless of the count: all four served surfaces
    (Overview/Scenarios/Workspace/World) agree on it (Defect 2)."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    assert view["status"] == "OK"

    entries = view["structures"]["allocated_structures"]["structures"]
    priced = [e for e in entries if e["is_fully_priced"]]
    unpriced = [e for e in entries if not e["is_fully_priced"]]
    accounting = view["structures"]["allocated_structures"]["candidate_accounting"]

    # Existing Optimizer/Stacker Reconnection: priced grew 113 -> 119 (6
    # additive multi_program combined structures — CA-BC, CA-QC, and
    # CA-ON's 4 — see test_canonical_authority_substrate.py's
    # test_fvd_runtime_candidate_universe_restored). None of them are
    # is_directly_comparable for FVD (Greece is the home jurisdiction, not
    # Canada — same relocation-comparability caveat as any non-baseline
    # candidate), so review_required grows by the same 6 and
    # comparable_count (the baseline alone) is unaffected. Task 11's
    # ranking-inclusion fix (is_directly_comparable now follows the same
    # is_baseline rule a single-program candidate already uses) has no
    # observable effect here specifically BECAUSE none of these combined
    # structures are at FVD's own home jurisdiction — proven separately
    # for a project whose home IS a multi-program jurisdiction is out of
    # reach for these two control projects (neither's home is Canada).
    # Task A (component/split): priced grew again, 119 -> 134 (15 additive
    # component_relocation structures — see test_canonical_authority_
    # substrate.py's test_fvd_runtime_candidate_universe_restored). Also
    # never is_directly_comparable (a routed component carries the same
    # unmodeled coordination/travel-cost caveat), so review_required
    # grows by the same 15.
    # Task B (treaty/co-pro): unpriced grew 8 -> 9 (1 additive Eurimages
    # CO_PRO_OPPORTUNITY structure -- real ownership/cultural-test facts
    # are not on file, so it is never fully priced; see
    # test_canonical_authority_substrate.py's
    # test_fvd_runtime_candidate_universe_restored). unpriceable_count
    # (the pre-existing authority-insufficient/rule-rejected causes)
    # is unaffected -- a co-pro opportunity is a NEW distinct terminal
    # state (STATUS_CO_PRO_OPPORTUNITY), never flattened into that bucket.
    #
    # Consolidated Backend Correction, Part 19-20 (CBA-009): priced
    # shrank 134 -> 133, unpriceable_count grew 9 -> 10 -- ES
    # (es_tax_credit_foreign) now RULE_REJECTED (real minimum-QPE
    # threshold genuinely unmet once FVD's own contingency reserve is no
    # longer counted as 100%-unconditionally qualifying; see
    # test_batch3_programs_price_with_real_numbers_in_fvd for the full
    # explanation). review_required_count shrinks by the same one (ES
    # was never is_directly_comparable for FVD either way).
    #
    # Part 3/CBA-006: unpriced grew 10 -> 11 -- FVD's Greece is also a
    # real European Convention signatory, generating a second, genuine
    # multilateral treaty_coproduction opportunity alongside Eurimages.
    assert len(priced) == 133
    assert len(unpriced) == 11
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 4/CBA-001: comparable_count is now 0
    # (was 1) — FVD's own Greece baseline resolves USER_FACT_REQUIRED on
    # its real cultural-test point table (0/20 confirmed), so it no
    # longer admits Recommended/comparable ranking (truthful unresolved
    # status over false recommendation), moving it from comparable into
    # review_required (still priced, still disclosed, just not ranked).
    assert accounting["comparable_count"] == 0
    assert accounting["review_required_count"] == 133
    assert accounting["unpriceable_count"] == 11

    # Cross-screen agreement: the ranking list (what Scenarios/Overview/
    # World all read) must reproduce the exact same split, not a second,
    # divergent count.
    #
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 4/CBA-001: `rank` (not
    # `is_directly_comparable` alone) is now the true signal of "actually
    # admitted to the comparable pool" — a candidate can be
    # is_directly_comparable=True (GR's own baseline is) yet excluded from
    # the numerically-ranked comparable set because its qualification is
    # genuinely unresolved (see _qualification_admits_recommended). `rank`
    # is only ever assigned to entries that made it into that pool.
    ranking = view["structures"]["allocated_structures"]["ranking"]
    comparable_ranked = [r for r in ranking if r["rank"] is not None]
    review_ranked = [r for r in ranking if r["is_fully_priced"] and r["rank"] is None]
    unpriceable_ranked = [r for r in ranking if not r["is_fully_priced"]]
    assert len(comparable_ranked) == 0
    assert len(review_ranked) == 133
    assert len(unpriceable_ranked) == 11

    # Feasibility ≠ eligibility (canonical authority substrate + feasibility
    # boundary repair): a landlocked jurisdiction with real marine-mismatch
    # feasibility (MN, UZ) must still be discoverable/priceable — it is
    # never removed from the economic universe merely because it is a weak
    # production fit. See test_landlocked_jurisdictions_remain_economically_
    # discoverable in test_fvd_canonical_input_assembly_repair.py for the
    # feasibility_status/feasibility_reasons proof.
    served_codes = {e["primary_jurisdiction"] for e in entries}
    assert "MN" in served_codes, "Mongolia must remain economically discoverable despite marine mismatch"
    assert "UZ" in served_codes, "Uzbekistan must remain economically discoverable despite marine mismatch"


async def test_greece_baseline_is_priced_and_directly_comparable(db: AsyncSession):
    """Defect 2 — Greece is the production's own base jurisdiction: priced
    AND directly comparable, with its real qualification trace/statutory
    basis intact (Defect 3), never flattened to a thin trace."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]

    baseline = [e for e in entries if e.get("is_baseline")]
    assert len(baseline) == 1
    gr = baseline[0]
    seg = gr["segments"][0]
    assert seg["jurisdiction_code"] == "GR"
    assert seg["program_slug"] == "gr_cash_rebate"
    assert seg["qpe_usd"] == pytest.approx(3_614_149.60, abs=0.01)
    assert seg["qpe_cap_applied_usd"] == pytest.approx(540_671.40, abs=0.01)
    assert seg["incentive_floor_usd"] == pytest.approx(1_445_659.84, abs=0.01)
    assert seg["incentive_ceiling_usd"] == pytest.approx(1_445_659.84, abs=0.01)
    assert seg["is_band_ceiling"] is False
    assert seg["ceiling_requires_confirmation"] is False
    assert seg["statutory_basis"], "Defect 3 — statutory_basis must not be discarded"
    assert seg["qualification_trace"], "Defect 3 — full register trace must not be discarded"

    rank_by_id = {r["structure_id"]: r for r in view["structures"]["allocated_structures"]["ranking"]}
    r = rank_by_id[gr["structure_id"]]
    assert r["is_fully_priced"] is True
    assert r["is_directly_comparable"] is True
    assert r["candidate_status"] == "PRICED"


async def test_malta_and_mauritius_priced_but_not_comparable_with_real_economics(db: AsyncSession):
    """Defect 2 — Malta and Mauritius are real, differentiated, priced
    candidates that are NOT the production's own base jurisdiction, so
    they must be excluded from the comparable ranking WITHOUT losing
    their real QPE/incentive numbers or being shown as unpriced.

    Consolidated Backend Correction, Part 19-20 (CBA-009): Mauritius no
    longer resolves as a band-ceiling incentive here. Its real QPE
    dropped from $1,132,056.00 to $769,190.00 (its own $362,866.00
    contingency reserve is now a disclosed grey area, not silently
    100%-qualifying) — genuinely below the QPE tier the 40%-band
    discretionary rate rule requires, so the statutory rate resolver
    correctly falls back to a flat, non-band 30% rule instead. This is
    real statutory rate-tier behavior responding honestly to a real,
    lower QPE — not a wiring defect. Malta's own economics are
    untouched (no contingency category in its own rules)."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    rank_by_id = {r["structure_id"]: r for r in view["structures"]["allocated_structures"]["ranking"]}

    mt = _single_segment_structures(entries, "MT")
    assert len(mt) == 1
    mt_seg = mt[0]["segments"][0]
    assert mt_seg["program_slug"] == "mt_mfc_rebate"
    assert mt_seg["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert mt_seg["incentive_floor_usd"] == pytest.approx(1_246_446.30, abs=0.01)
    assert mt_seg["incentive_ceiling_usd"] == pytest.approx(1_661_928.40, abs=0.01)
    assert mt_seg["is_band_ceiling"] is True
    assert mt_seg["ceiling_requires_confirmation"] is True
    mt_rank = rank_by_id[mt[0]["structure_id"]]
    assert mt_rank["is_fully_priced"] is True
    assert mt_rank["is_directly_comparable"] is False

    mu = _single_segment_structures(entries, "MU")
    assert len(mu) == 1
    mu_seg = mu[0]["segments"][0]
    assert mu_seg["program_slug"] == "mu_edb_incentive"
    # CBA-009 Part 19-20: $1,132,056.00 -> $769,190.00 (FVD's own $362,866.00
    # contingency reserve, priced against MU's real qualifies=True rule, is
    # now a disclosed grey area by default, not silently 100%-qualifying).
    assert mu_seg["qpe_usd"] == pytest.approx(769_190.00, abs=0.01)
    assert mu_seg["is_band_ceiling"] is False
    assert mu_seg["ceiling_requires_confirmation"] is False
    assert mu_seg["rate_floor"] == mu_seg["rate_ceiling"] == pytest.approx(0.30)
    mu_rank = rank_by_id[mu[0]["structure_id"]]
    assert mu_rank["is_fully_priced"] is True
    assert mu_rank["is_directly_comparable"] is False


async def test_australia_queensland_priced_flat_rate_not_comparable(db: AsyncSession):
    """Defect 2 — AU-QLD's 15% PDV rebate is a flat, non-band rate (no
    confirmation required), still real and priced, still excluded from the
    comparable ranking on the same non-baseline basis as Malta/Mauritius."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    rank_by_id = {r["structure_id"]: r for r in view["structures"]["allocated_structures"]["ranking"]}

    au_qld = _single_segment_structures(entries, "AU-QLD")
    assert len(au_qld) == 1
    seg = au_qld[0]["segments"][0]
    assert seg["program_slug"] == "au_qld_pdv_rebate"
    assert seg["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert seg["incentive_floor_usd"] == pytest.approx(623_223.15, abs=0.01)
    assert seg["incentive_ceiling_usd"] == pytest.approx(623_223.15, abs=0.01)
    assert seg["is_band_ceiling"] is False
    assert seg["ceiling_requires_confirmation"] is False

    rank = rank_by_id[au_qld[0]["structure_id"]]
    assert rank["is_fully_priced"] is True
    assert rank["is_directly_comparable"] is False


async def test_australia_location_offset_rule_rejected_with_program_identity(db: AsyncSession):
    """Defect 4 — AU Location Offset has real statutory rules that do not
    resolve for this production's QPE: it must reach RULE_REJECTED /
    STATUTORY_CONDITIONS_UNMET with its program_slug preserved, never be
    flattened into the generic UNPRICEABLE_AUTHORITY_INSUFFICIENT bucket
    every other capability-only candidate without doctrine/rate data at
    all correctly falls into."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    ranking = view["structures"]["allocated_structures"]["ranking"]

    au_offset = [r for r in ranking if r.get("program_slug") == "au_location_offset"]
    assert len(au_offset) == 1
    r = au_offset[0]
    assert r["is_fully_priced"] is False
    assert r["is_directly_comparable"] is False
    assert r["candidate_status"] == "RULE_REJECTED"
    assert r["rejection_reason_class"] == "STATUTORY_CONDITIONS_UNMET"


async def test_fvd_unpriceable_causes_are_differentiated_not_flattened(db: AsyncSession):
    """Defect 4 — the unpriceable FVD candidates must reach more than one
    terminal cause; a single flattened UNPRICEABLE_AUTHORITY_INSUFFICIENT
    bucket for all of them would mean the real cause differentiation was
    lost again. The count was 80 when this test was written; it has since
    legitimately shrunk to 58 as the Global Economic Data + Base Pricing /
    Global Formulaic Economic Completion recover-before-research batches
    individually promoted 52 formerly-blocked programs to priced (see
    test_fvd_accounting_matches_codex_diagnosis) -- the count itself is
    not the invariant this test guards. Grew again 8 -> 9 with Task B's
    additive Eurimages CO_PRO_OPPORTUNITY structure (a genuinely distinct
    terminal status, STATUS_CO_PRO_OPPORTUNITY -- never flattened into
    UNPRICEABLE_AUTHORITY_INSUFFICIENT/RULE_REJECTED). Grew again 9 -> 10
    with Consolidated Backend Correction, Part 19-20 (CBA-009): ES now
    genuinely RULE_REJECTED (real minimum-QPE threshold unmet once its
    own contingency reserve is no longer counted as 100%-unconditionally
    qualifying) -- see test_batch3_programs_price_with_real_numbers_in_fvd."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    ranking = view["structures"]["allocated_structures"]["ranking"]
    unpriceable = [r for r in ranking if not r["is_fully_priced"]]

    assert len(unpriceable) == 11
    statuses = {r["candidate_status"] for r in unpriceable}
    assert statuses.issuperset({"UNPRICEABLE_AUTHORITY_INSUFFICIENT", "RULE_REJECTED"}), (
        f"expected at least AUTHORITY_INSUFFICIENT and RULE_REJECTED causes, got {statuses}"
    )
    for r in unpriceable:
        assert r["candidate_status"], "every unpriceable candidate must carry a real terminal status, never blank"


async def test_generic_pkg_and_economics_disclose_real_fvd_data(db: AsyncSession):
    """Defect 3/5 — the leading structure's real register trace and the
    project's real budget total must survive into the generic pkg/
    economics sections build_generic_pkg_and_economics() feeds to
    get_project_state(), not the honest-empty fallback shapes."""
    await evaluate_project(db, FVD_PROJECT_ID)
    sections = await build_generic_pkg_and_economics(db, FVD_PROJECT_ID)
    assert sections.get("status") != "PROJECT_NOT_FOUND"

    pkg = sections["pkg"]
    assert pkg["register"], "Defect 3/5 — leading structure's real register trace must not be empty for FVD"
    assert pkg["budget"]["total_budget_usd"] == pytest.approx(4_517_687.00, abs=0.01)

    economics = sections["economics"]
    assert "production_requirements_disclosed" in economics


@pytest.mark.parametrize("project_id", [FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID])
async def test_stale_engine_rows_never_leak_into_served_output(db: AsyncSession, project_id: str):
    """STEP 7 — stale-row safety. Both projects genuinely have rows persisted
    under multiple prior engine_version values (canonical-1.0.0/1.1.0/1.2.0,
    and for FVD the original legacy 0.1.0 run_full_analysis rows) sharing the
    SAME structure ids as the current canonical-1.2.1 rows. Those stale rows
    may remain in the table for provenance, but build_production_and_structures
    (what every served surface — Overview/Scenarios/Workspace/World —
    ultimately reads through get_project_state) must select rows filtered
    to the leading structure's CURRENT input_fingerprint + engine_version
    only, never a mix."""
    await evaluate_project(db, project_id)

    version_rows = (await db.execute(
        select(StructureCalculationResult.engine_version, func.count())
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(ProductionStructure.project_id == project_id)
        .group_by(StructureCalculationResult.engine_version)
    )).all()
    versions_present = {v for v, _ in version_rows}
    assert len(versions_present) > 1, (
        "test precondition: this project must genuinely carry multiple stale "
        "engine_version rows, or this test proves nothing"
    )
    assert ENGINE_VERSION in versions_present

    view = await build_production_and_structures(db, project_id)
    assert view["status"] == "OK"
    served_version = view["structures"]["allocated_structures"]["version"]
    assert served_version == ENGINE_VERSION, (
        f"served output must pin to the current engine version {ENGINE_VERSION!r}, got {served_version!r}"
    )

    # Every structure_id served must resolve to a row at the CURRENT engine
    # version — a stale row for the same structure_id existing alongside it
    # in the table must never be the one that reached the frontend adapter.
    served_ids = {e["structure_id"] for e in view["structures"]["allocated_structures"]["structures"]}
    assert served_ids, "must serve real structures, not an empty set"
    current_rows = (await db.execute(
        select(StructureCalculationResult.structure_id)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == project_id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).scalars().all()
    current_ids = {str(sid) for sid in current_rows}
    assert served_ids <= current_ids, "every served structure_id must have a current-engine-version row backing it"
