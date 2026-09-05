"""
Canonical Budget Parser Remediation (2026-09-04).

Line-level regression fixtures for the material Codex defects (see
docs/validation/CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md and
docs/validation/CANONICAL_BUDGET_LINE_RECONCILIATION_CODEX.csv), using
REAL persisted rows from the four locked-corpus budgets — never
fabricated test-only production data. Each test locks in one specific,
previously-confirmed defect so it can never silently regress.

The companion executable gate,
frametax2/backend/scripts/canonical_budget_integrity_gate.py, re-asserts
these same facts (and more) across the whole corpus on every run; these
tests exist so `pytest` alone (no separate script invocation) also
catches a regression, and so each defect has its own clearly-named,
independently-runnable case.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.material_routing import ensure_current_budget_routed

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _items(db: AsyncSession, project_id: str) -> list[BudgetLineItem]:
    await ensure_current_budget_routed(db, project_id)
    doc = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project_id)
    )).scalars().first()
    return (await db.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id)
    )).scalars().all()


def _cat(item: BudgetLineItem) -> str:
    return getattr(item.spend_category, "value", item.spend_category)


# ── BPI-001: Bad Hombres' unnumbered contingency, dropped downstream ──────

async def test_bad_hombres_contingency_survives_downstream_exactly_once(db: AsyncSession):
    items = await _items(db, BAD_HOMBRES_PROJECT_ID)
    contingency_rows = [i for i in items if i.description == "CONTINGENCY"]
    assert len(contingency_rows) == 1, "the real unnumbered contingency row must be preserved exactly once"
    assert round(float(contingency_rows[0].amount_usd), 2) == 94_382.0
    assert _cat(contingency_rows[0]) == "contingency"

    econ = await build_project_economic_inputs(db, BAD_HOMBRES_PROJECT_ID, read_only=True)
    assert econ.ok
    canonical_contingency = [
        line for line in econ.inputs.budget_lines
        if line.spend_category == "contingency" and line.description == "CONTINGENCY"
    ]
    assert canonical_contingency, (
        "BPI-001: the real $94,382 contingency must be present in canonical budget_lines, "
        "not silently excluded for lacking a numeric account code"
    )
    assert round(canonical_contingency[0].amount_usd, 2) == 94_382.0
    canonical_sum = round(sum(line.amount_usd for line in econ.inputs.budget_lines), 2)
    assert canonical_sum == 2_482_023.0, "canonical sum must equal the real declared source total"


# ── BPI-002: Lips Like Sugar's duplicate "4900" account-code collision ────

async def test_lips_like_sugar_duplicate_4900_rows_both_survive_with_correct_categories(db: AsyncSession):
    items = await _items(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    fringes = next((i for i in items if i.description == "4900 Total Fringes"), None)
    titles = next((i for i in items if i.description == "4900 MAIN AND END TITLES"), None)
    assert fringes is not None and titles is not None, "both real 4900 rows must survive as distinct lines"
    assert round(float(fringes.amount_usd), 2) == 1_023_115.0
    assert round(float(titles.amount_usd), 2) == 10_500.0
    assert _cat(fringes) == "payroll_fringes", (
        "BPI-002: the fringes row must never be overwritten to miscellaneous by the "
        "later same-code MAIN AND END TITLES row"
    )
    assert _cat(titles) == "post_production"

    # The downstream consumption side (production_allocation.py's own
    # spend_category_by_code fallback map) must also resolve each line's
    # OWN category correctly, not the other row's, when both share account
    # code "4900".
    from app.calculators.production_allocation import component_for
    econ = await build_project_economic_inputs(db, LIPS_LIKE_SUGAR_PROJECT_ID, read_only=True)
    assert econ.ok
    fringes_line = next(l for l in econ.inputs.budget_lines if l.description == "Total Fringes" and round(l.amount_usd, 2) == 1_023_115.0)
    titles_line = next(l for l in econ.inputs.budget_lines if l.description == "MAIN AND END TITLES")
    resolved_fringes_cat = fringes_line.spend_category or econ.inputs.spend_category_by_code.get(fringes_line.account_code)
    resolved_titles_cat = titles_line.spend_category or econ.inputs.spend_category_by_code.get(titles_line.account_code)
    assert resolved_fringes_cat == "payroll_fringes"
    assert resolved_titles_cat == "post_production"
    assert component_for(resolved_fringes_cat) != component_for(resolved_titles_cat)


# ── F#K's $453,583 finance fee: required acceptance case (unchanged) ──────

async def test_fvd_finance_fee_exactly_once_as_source_finance(db: AsyncSession):
    items = await _items(db, FVD_PROJECT_ID)
    fee_rows = [i for i in items if "FINANCE FEE" in (i.description or "")]
    assert len(fee_rows) == 1
    assert round(float(fee_rows[0].amount_usd), 2) == 453_583.0
    assert _cat(fee_rows[0]) == "finance_costs"

    econ = await build_project_economic_inputs(db, FVD_PROJECT_ID, read_only=True)
    assert econ.ok
    canonical_fee = [
        line for line in econ.inputs.budget_lines
        if line.spend_category == "finance_costs" and "FINANCE FEE" in line.description
    ]
    assert len(canonical_fee) == 1
    assert round(canonical_fee[0].amount_usd, 2) == 453_583.0


# ── BPI-004: bare "BOND" account (F#K) ─────────────────────────────────────

async def test_fvd_bare_bond_account_classifies_completion_bond(db: AsyncSession):
    items = await _items(db, FVD_PROJECT_ID)
    bond_rows = [i for i in items if "BOND" in (i.description or "").upper()]
    assert bond_rows, "expected F#K's real 7905 BOND account"
    assert round(float(bond_rows[0].amount_usd), 2) == 72_573.0
    assert _cat(bond_rows[0]) == "completion_bond", (
        "BPI-004: a bare 'BOND' account must classify as completion_bond, not miscellaneous"
    )


# ── BPI-005: legal/accounting (Bad Hombres + Lips Like Sugar) ─────────────

async def test_legal_accounting_classifies_correctly_bad_hombres_and_lips(db: AsyncSession):
    bh_items = await _items(db, BAD_HOMBRES_PROJECT_ID)
    bh_legal = next(i for i in bh_items if "LEGAL AND ACCOUNTING" in (i.description or ""))
    assert round(float(bh_legal.amount_usd), 2) == 24_000.0
    assert _cat(bh_legal) == "legal_accounting"

    lls_items = await _items(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    lls_legal = next(i for i in lls_items if "LEGAL COSTS" in (i.description or ""))
    assert round(float(lls_legal.amount_usd), 2) == 150_000.0
    assert _cat(lls_legal) == "legal_accounting"


# ── BPI-006: ATL producer/director roles (F#K + Bad Hombres) ──────────────

async def test_atl_producer_and_director_roles_classify_correctly(db: AsyncSession):
    for project_id, producer_amount, director_amount in (
        (FVD_PROJECT_ID, 401_831.0, 75_710.0),
        (BAD_HOMBRES_PROJECT_ID, 267_169.0, 75_000.0),
    ):
        items = await _items(db, project_id)
        producer = next(i for i in items if "PRODUCER" in (i.description or "").upper())
        director = next(
            i for i in items
            if "DIRECTOR" in (i.description or "").upper() and "PHOTOGRAPHY" not in (i.description or "").upper()
        )
        assert round(float(producer.amount_usd), 2) == producer_amount
        assert round(float(director.amount_usd), 2) == director_amount
        assert _cat(producer) == "atl_producer", f"BPI-006: {producer.description!r} must classify atl_producer"
        assert _cat(director) == "atl_director", f"BPI-006: {director.description!r} must classify atl_director"
        assert producer.atl_btl == "atl"
        assert director.atl_btl == "atl"


async def test_art_direction_is_never_misclassified_as_the_atl_director_role(db: AsyncSession):
    """Regression guard for a defect introduced and caught DURING this
    same remediation pass: a broadened director-matching pattern must
    never claim 'ART DIRECTION' (a real BTL art-department/production-
    design account, confirmed NO_CONFIRMED_DEFECT by Codex as
    miscellaneous) as the film's own above-the-line director fee."""
    for project_id in (BAD_HOMBRES_PROJECT_ID, LIPS_LIKE_SUGAR_PROJECT_ID):
        items = await _items(db, project_id)
        art_direction = next(i for i in items if i.description == "2200 ART DIRECTION")
        assert _cat(art_direction) != "atl_director"
        assert art_direction.atl_btl != "atl"


# ── BPI-007: fringe/post precedence (Lips Like Sugar's three Total Fringes) ─

async def test_lips_like_sugar_all_three_total_fringes_rows_classify_payroll_fringes(db: AsyncSession):
    items = await _items(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    fringe_rows = [i for i in items if "Total Fringes" in (i.description or "")]
    assert len(fringe_rows) == 4, "expected the real 1900/4900/5900/6900 Total Fringes rows"
    amounts = {round(float(i.amount_usd), 2) for i in fringe_rows}
    assert amounts == {255_291.0, 1_023_115.0, 68_308.0, 0.0}
    for row in fringe_rows:
        assert _cat(row) == "payroll_fringes", (
            f"BPI-007: {row.description!r} must classify payroll_fringes, never post_production "
            "merely because its department text contains 'Post Production'"
        )
    # No amount counted twice: the sum of the four distinct rows must
    # equal the sum of every row whose description mentions fringes.
    total = round(sum(float(i.amount_usd) for i in fringe_rows), 2)
    assert total == 1_346_714.0


# ── BPI-003: production sound vs. post sound (all four budgets) ───────────

async def test_production_sound_and_post_sound_never_collapse_into_each_other(db: AsyncSession):
    cases = {
        LITTLE_UTOPIA_PROJECT_ID: [
            ("3200 PRODUCTION SOUND", "production_sound", "btl"),
            ("5200 SOUND POST PRODUCTION", "sound", "post"),
        ],
        FVD_PROJECT_ID: [
            ("3200 PRODUCTION SOUND", "production_sound", "btl"),
            ("5200 POST PRODUCTION SOUND", "sound", "post"),
        ],
        BAD_HOMBRES_PROJECT_ID: [
            ("3400 PRODUCTION SOUND", "production_sound", "btl"),
            ("4700 POST PRODUCTION SOUND", "sound", "post"),
        ],
        LIPS_LIKE_SUGAR_PROJECT_ID: [
            ("3400 PRODUCTION SOUND", "production_sound", "btl"),
            ("4700 POST-PRODUCTION SOUND", "sound", "post"),
        ],
    }
    for project_id, expectations in cases.items():
        items = await _items(db, project_id)
        for description, expected_cat, expected_bucket in expectations:
            row = next((i for i in items if i.description == description), None)
            assert row is not None, f"{project_id}: expected real row {description!r}"
            assert _cat(row) == expected_cat, (
                f"BPI-003: {description!r} classified {_cat(row)!r}, expected {expected_cat!r}"
            )
            assert row.atl_btl == expected_bucket


# ── BPI-008: film/lab/dailies and main/end titles post-flavored accounts ──

async def test_film_lab_dailies_and_titles_classify_post_production(db: AsyncSession):
    bh_items = await _items(db, BAD_HOMBRES_PROJECT_ID)
    dailies = next(i for i in bh_items if "PRODUCTION FILM/LAB/DAILIES" in (i.description or ""))
    assert round(float(dailies.amount_usd), 2) == 2_000.0
    assert _cat(dailies) == "post_production"

    lls_items = await _items(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    titles = next(i for i in lls_items if "MAIN AND END TITLES" in (i.description or ""))
    assert round(float(titles.amount_usd), 2) == 10_500.0
    assert _cat(titles) == "post_production"


# ── Source totals unchanged across the whole repair ────────────────────────

async def test_source_totals_unchanged_for_all_four_budgets(db: AsyncSession):
    expected = {
        LITTLE_UTOPIA_PROJECT_ID: 4_364_393.0,
        FVD_PROJECT_ID: 4_517_687.0,
        BAD_HOMBRES_PROJECT_ID: 2_482_023.0,
        LIPS_LIKE_SUGAR_PROJECT_ID: 11_983_654.0,
    }
    for project_id, expected_total in expected.items():
        await ensure_current_budget_routed(db, project_id)
        doc = (await db.execute(
            select(BudgetDocument).where(BudgetDocument.project_id == project_id)
        )).scalars().first()
        assert round(float(doc.total_budget_raw), 2) == expected_total, (
            f"{project_id}: source total must be byte-identical before/after this repair"
        )
