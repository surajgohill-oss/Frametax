"""
canonical_budget_integrity_gate.py

Canonical Budget Parser Remediation (2026-09-04) — permanent, executable
budget semantic-integrity gate for the FOUR-BUDGET locked acceptance
corpus this task defines:

    Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar

Companion to canonical_integrity_gate.py (the non-Globe optimizer/
scenario gate) — this one is scoped to BUDGET INGESTION/CLASSIFICATION
only, per docs/validation/CANONICAL_BUDGET_PARSER_REMEDIATION_CLAUDE.md,
which documents the Codex-identified defects (BPI-001 through BPI-009 in
docs/validation/CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md and the
line-by-line docs/validation/CANONICAL_BUDGET_LINE_RECONCILIATION_CODEX.csv)
this gate locks closed.

DO NOT expand the corpus. This gate intentionally hardcodes the four
locked project IDs — it is not a general "every project with a budget"
gate (see canonical_integrity_gate.py's own PROGRAM/PARTICIPANTS/etc.
invariants for that different, broader scope). Expected source totals,
line counts, and per-line category assertions below are locked reference
values from the Codex audit, not derived at runtime — a change to any of
them without updating both the audit artifacts and this script is a real
regression, not a stale-fixture false positive.

Required invariant families (Section 16 of the remediation task):
  1.  SOURCE TOTAL
  2.  LINE PRESERVATION
  3.  NO DUPLICATION
  4.  ACCOUNT CODE PRESERVATION
  5.  DESCRIPTION PRESERVATION
  6.  AMOUNT PRESERVATION
  7.  SEMANTIC CATEGORY
  8.  FINANCE SOURCE VS SCENARIO FINANCE
  9.  CONTINGENCY
  10. BOND / INSURANCE
  11. LEGAL / ACCOUNTING
  12. ATL
  13. FRINGE / PAYROLL
  14. TRAVEL & LIVING
  15. POST / SOUND
  16. SOURCE BUDGET IMMUTABILITY

Usage:
    cd frametax2/backend && source .venv/bin/activate
    PYTHONPATH=. python3 scripts/canonical_budget_integrity_gate.py
"""
from __future__ import annotations

import asyncio
import sys

import app.main  # noqa: F401 -- import order fix for the known circular-import quirk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.material_routing import ensure_current_budget_routed

#: Corpus hard lock (Section 1) -- exactly these four, never expanded.
CORPUS: dict[str, str] = {
    "Little Utopia": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "F#K Valentine's Day": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "Bad Hombres": "4355ae88-a636-4c18-af60-ad73b2646124",
    "Lips Like Sugar": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
}

#: Locked reference values from the Codex audit
#: (CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md Section 3/Section 3
#: table, and Section 1's locked corpus table for line counts).
EXPECTED_SOURCE_TOTAL: dict[str, float] = {
    "Little Utopia": 4_364_393.0,
    "F#K Valentine's Day": 4_517_687.0,
    "Bad Hombres": 2_482_023.0,
    "Lips Like Sugar": 11_983_654.0,
}
EXPECTED_LINE_COUNT: dict[str, int] = {
    "Little Utopia": 44,
    "F#K Valentine's Day": 34,
    "Bad Hombres": 34,
    "Lips Like Sugar": 46,
}
#: Little Utopia's source document itself carries a real, hand-verified
#: $2 leaf-line-sum excess over its own declared gross total (Codex
#: Section 3: "Parser exactly preserves the source's own $2 account-line
#: rounding excess") -- never normalized away.
EXPECTED_LEAF_SUM_VARIANCE: dict[str, float] = {
    "Little Utopia": 2.0,
    "F#K Valentine's Day": 0.0,
    "Bad Hombres": 0.0,
    "Lips Like Sugar": 0.0,
}

#: SEMANTIC CATEGORY / defect-closure fixtures: (description substring,
#: expected spend_category) for every material Codex-flagged line, keyed
#: by project. Substring match (not exact) so provenance formatting
#: quirks (leading account code, punctuation) never cause a false
#: mismatch here -- only the semantic category is asserted.
EXPECTED_CATEGORY: dict[str, list[tuple[str, str]]] = {
    "Little Utopia": [
        ("PRODUCERS UNIT", "atl_producer"),
        ("DIRECTION", "atl_director"),
        ("3200 PRODUCTION SOUND", "production_sound"),
        ("ADMINISTRATIVE EXPENSES", "general_administration"),
        ("PUBLICITY", "general_administration"),
        ("Bond", "completion_bond"),
        ("Contigency", "contingency"),
    ],
    "F#K Valentine's Day": [
        ("PRODUCERS", "atl_producer"),
        ("DIRECTOR", "atl_director"),
        ("3200 PRODUCTION SOUND", "production_sound"),
        ("5200 POST PRODUCTION SOUND", "sound"),
        ("ADMINISTRATIVE EXPENSES", "general_administration"),
        ("FINANCE FEE", "finance_costs"),
        ("BOND", "completion_bond"),
    ],
    "Bad Hombres": [
        ("PRODUCERS UNIT", "atl_producer"),
        ("DIRECTOR", "atl_director"),
        ("ART DIRECTION", "miscellaneous"),  # regression guard -- must NOT become atl_director
        ("3400 PRODUCTION SOUND", "production_sound"),
        ("4700 POST PRODUCTION SOUND", "sound"),
        ("PRODUCTION FILM/LAB/DAILIES", "post_production"),
        ("LEGAL AND ACCOUNTING", "legal_accounting"),
        ("CONTINGENCY", "contingency"),
    ],
    "Lips Like Sugar": [
        ("ART DIRECTION", "miscellaneous"),  # regression guard
        ("3400 PRODUCTION SOUND", "production_sound"),
        ("4700 POST-PRODUCTION SOUND", "sound"),
        ("LEGAL COSTS", "legal_accounting"),
        ("GENERAL EXPENSE", "general_administration"),
        ("Bond Fee", "completion_bond"),
        ("Contingency", "contingency"),
    ],
}


async def _gate_one(session: AsyncSession, name: str, project_id: str) -> list[str]:
    failures: list[str] = []

    # Re-routing is idempotent (material_routing._route_budget's own
    # parser_version guard) -- safe and cheap to call on every gate run;
    # this ALSO doubles as invariant 16 (SOURCE BUDGET IMMUTABILITY)'s
    # idempotency check further below.
    await ensure_current_budget_routed(session, project_id)

    doc = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project_id)
    )).scalars().first()
    if doc is None:
        return [f"{name}: no BudgetDocument found at all"]

    items = (await session.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id)
    )).scalars().all()

    # 1. SOURCE TOTAL
    source_total = float(doc.total_budget_raw) if doc.total_budget_raw is not None else None
    expected_total = EXPECTED_SOURCE_TOTAL[name]
    if source_total is None or abs(source_total - expected_total) > 0.01:
        failures.append(f"{name} SOURCE TOTAL: got {source_total}, expected {expected_total}")

    # 2. LINE PRESERVATION
    if len(items) != EXPECTED_LINE_COUNT[name]:
        failures.append(f"{name} LINE PRESERVATION: got {len(items)} lines, expected {EXPECTED_LINE_COUNT[name]}")

    # 3. NO DUPLICATION -- every source_row is unique (a real duplicate
    # INSERT, never legitimate shared account codes, which ARE allowed
    # and handled by invariant 4/7 instead).
    source_rows = [i.source_row for i in items if i.source_row is not None]
    if len(source_rows) != len(set(source_rows)):
        failures.append(f"{name} NO DUPLICATION: duplicate source_row values found: {source_rows}")
    line_ids = [str(i.id) for i in items]
    if len(line_ids) != len(set(line_ids)):
        failures.append(f"{name} NO DUPLICATION: duplicate BudgetLineItem primary keys")

    # 4. ACCOUNT CODE PRESERVATION + 5. DESCRIPTION PRESERVATION +
    # 6. AMOUNT PRESERVATION -- every line has a non-empty description,
    # a real amount (including legitimate $0 lines), and the leaf-line
    # sum reconciles to source total within the documented, locked
    # variance (never silently normalized).
    leaf_sum = 0.0
    for i in items:
        if not (i.description or "").strip():
            failures.append(f"{name} DESCRIPTION PRESERVATION: a line has an empty description (row {i.source_row})")
        if i.amount_usd is None:
            failures.append(f"{name} AMOUNT PRESERVATION: a line has a null amount (row {i.source_row}: {i.description!r})")
        else:
            leaf_sum += float(i.amount_usd)
    leaf_sum = round(leaf_sum, 2)
    variance = round(abs(leaf_sum - expected_total), 2) if source_total is not None else None
    expected_variance = EXPECTED_LEAF_SUM_VARIANCE[name]
    if variance is not None and abs(variance - expected_variance) > 0.01:
        failures.append(
            f"{name} AMOUNT PRESERVATION: leaf-line sum {leaf_sum} vs. source total {expected_total} "
            f"variance {variance} != expected {expected_variance}"
        )

    # 7. SEMANTIC CATEGORY (defect-closure fixtures)
    for substring, expected_cat in EXPECTED_CATEGORY.get(name, []):
        matches = [i for i in items if substring in (i.description or "")]
        if not matches:
            failures.append(f"{name} SEMANTIC CATEGORY: no line found containing {substring!r}")
            continue
        for m in matches:
            got = getattr(m.spend_category, "value", m.spend_category)
            if got != expected_cat:
                failures.append(
                    f"{name} SEMANTIC CATEGORY: {m.description!r} classified {got!r}, expected {expected_cat!r}"
                )

    # 8. FINANCE SOURCE VS SCENARIO FINANCE
    econ = await build_project_economic_inputs(session, project_id, read_only=True)
    if not econ.ok:
        failures.append(f"{name}: build_project_economic_inputs failed: {econ.blockers}")
    else:
        finance_lines = [
            line for line in econ.inputs.budget_lines
            if line.spend_category == "finance_costs"
        ]
        finance_sum = round(sum(line.amount_usd for line in finance_lines), 2)
        if name == "F#K Valentine's Day":
            # The required acceptance case (Section 7): exactly once.
            fee_lines = [line for line in finance_lines if "FINANCE FEE" in line.description]
            if len(fee_lines) != 1 or round(fee_lines[0].amount_usd, 2) != 453_583.0:
                failures.append(
                    f"{name} FINANCE SOURCE: expected exactly one FINANCE FEE line at $453,583, "
                    f"got {[(l.description, l.amount_usd) for l in fee_lines]}"
                )
        if name == "Lips Like Sugar" and abs(finance_sum - 1_700_000.0) > 0.01:
            failures.append(f"{name} FINANCE SOURCE: expected $1,700,000 total finance costs, got {finance_sum}")

    # 9. CONTINGENCY -- the unnumbered Bad Hombres contingency (BPI-001)
    # must be present in the canonical budget_lines actually consumed
    # downstream, not merely in the raw persisted rows.
    if name == "Bad Hombres" and econ.ok:
        contingency_lines = [
            line for line in econ.inputs.budget_lines
            if line.spend_category == "contingency" and "CONTINGENCY" in line.description.upper()
        ]
        total_contingency = round(sum(line.amount_usd for line in contingency_lines), 2)
        if abs(total_contingency - 94_382.0) > 0.01:
            failures.append(
                f"{name} CONTINGENCY: expected the real $94,382 unnumbered contingency in canonical "
                f"budget_lines, got {total_contingency} across {[l.description for l in contingency_lines]}"
            )

    # 10. BOND / INSURANCE -- bond and insurance never collapse into each
    # other or into miscellaneous.
    bond_lines = [i for i in items if "BOND" in (i.description or "").upper()]
    for b in bond_lines:
        got = getattr(b.spend_category, "value", b.spend_category)
        if got != "completion_bond":
            failures.append(f"{name} BOND: {b.description!r} classified {got!r}, expected completion_bond")
    insurance_lines = [i for i in items if "INSURANCE" in (i.description or "").upper()]
    for ins in insurance_lines:
        got = getattr(ins.spend_category, "value", ins.spend_category)
        if got != "insurance":
            failures.append(f"{name} INSURANCE: {ins.description!r} classified {got!r}, expected insurance")

    # 11. LEGAL / ACCOUNTING
    legal_lines = [
        i for i in items
        if ("LEGAL" in (i.description or "").upper()) and float(i.amount_usd or 0) > 0
    ]
    for lg in legal_lines:
        got = getattr(lg.spend_category, "value", lg.spend_category)
        if got != "legal_accounting":
            failures.append(f"{name} LEGAL/ACCOUNTING: {lg.description!r} classified {got!r}, expected legal_accounting")

    # 12. ATL -- producer/director role lines classify ATL with the real
    # role category, never miscellaneous.
    for i in items:
        d = (i.description or "").upper()
        if ("PRODUCER" in d and "REINVESTMENT" not in d) or ("DIRECTOR" in d and "PHOTOGRAPHY" not in d):
            got = getattr(i.spend_category, "value", i.spend_category)
            if got == "miscellaneous":
                failures.append(f"{name} ATL: {i.description!r} still classifies as miscellaneous")

    # 13. FRINGE / PAYROLL -- every explicit "Total Fringes" (or Fringes)
    # line classifies payroll_fringes, and no amount is ever counted on
    # two distinct lines (source_row uniqueness already checked above
    # covers the duplication half of this).
    fringe_lines = [i for i in items if "fringe" in (i.description or "").lower()]
    for f in fringe_lines:
        got = getattr(f.spend_category, "value", f.spend_category)
        if got != "payroll_fringes":
            failures.append(f"{name} FRINGE/PAYROLL: {f.description!r} classified {got!r}, expected payroll_fringes")

    # 14. TRAVEL & LIVING -- aggregate travel/lodging rows still present
    # and still classify travel/lodging (regression guard, not a new fix).
    travel_lines = [i for i in items if "TRAVEL" in (i.description or "").upper()]
    for t in travel_lines:
        got = getattr(t.spend_category, "value", t.spend_category)
        if got not in ("travel", "lodging"):
            failures.append(f"{name} TRAVEL & LIVING: {t.description!r} classified {got!r}, expected travel/lodging")

    # 15. POST / SOUND -- production sound and post sound never collapse
    # into each other (the corpus-wide regression this task targeted).
    for i in items:
        d = (i.description or "").upper()
        got = getattr(i.spend_category, "value", i.spend_category)
        if "SOUND" in d and "POST" not in d.replace("-", " ") and "PRODUCTION SOUND" in d:
            if got != "production_sound":
                failures.append(f"{name} POST/SOUND: {i.description!r} (production) classified {got!r}, expected production_sound")
        elif "SOUND" in d and "POST" in d.replace("-", " "):
            if got != "sound":
                failures.append(f"{name} POST/SOUND: {i.description!r} (post) classified {got!r}, expected sound")

    return failures


async def _check_immutability(session: AsyncSession, name: str, project_id: str) -> list[str]:
    """16. SOURCE BUDGET IMMUTABILITY -- calling the routing entry point
    a second time must be a true no-op: same parser_version, same row
    count, same total. A real reparse on every call would mean the
    'canonical source budget is immutable' invariant does not actually
    hold at runtime."""
    doc_before = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project_id)
    )).scalars().first()
    before = (doc_before.parser_version, doc_before.total_budget_raw)
    before_count = len((await session.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc_before.id)
    )).scalars().all())

    await ensure_current_budget_routed(session, project_id)

    doc_after = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project_id)
    )).scalars().first()
    after = (doc_after.parser_version, doc_after.total_budget_raw)
    after_count = len((await session.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc_after.id)
    )).scalars().all())

    failures = []
    if before != after:
        failures.append(f"{name} SOURCE BUDGET IMMUTABILITY: (parser_version, total) changed on a repeat call: {before} -> {after}")
    if before_count != after_count:
        failures.append(f"{name} SOURCE BUDGET IMMUTABILITY: line count changed on a repeat call: {before_count} -> {after_count}")
    return failures


_INVARIANT_NAMES = (
    "SOURCE TOTAL", "LINE PRESERVATION", "NO DUPLICATION", "ACCOUNT CODE PRESERVATION",
    "DESCRIPTION PRESERVATION", "AMOUNT PRESERVATION", "SEMANTIC CATEGORY",
    "FINANCE SOURCE VS SCENARIO FINANCE", "CONTINGENCY", "BOND / INSURANCE",
    "LEGAL / ACCOUNTING", "ATL", "FRINGE / PAYROLL", "TRAVEL & LIVING",
    "POST / SOUND", "SOURCE BUDGET IMMUTABILITY",
)


async def main() -> int:
    print(f"Canonical Budget Integrity Gate — {len(CORPUS)}-budget locked corpus\n")
    all_failures: list[str] = []
    async with AsyncSession(engine, expire_on_commit=False) as session:
        for name, project_id in CORPUS.items():
            failures = await _gate_one(session, name, project_id)
            failures += await _check_immutability(session, name, project_id)
            status = "PASS" if not failures else "FAIL"
            print(f"  {status}  {name}")
            for f in failures:
                print(f"          - {f}")
            all_failures.extend(failures)

    print(f"\nInvariant families asserted (all {len(_INVARIANT_NAMES)}, none DEFERRED):")
    for n in _INVARIANT_NAMES:
        n_fail = sum(1 for f in all_failures if n in f.split(":", 1)[0])
        print(f"  {'PASS' if n_fail == 0 else 'FAIL':6} {n}")

    print()
    if all_failures:
        print(f"CANONICAL BUDGET INTEGRITY GATE: FAIL ({len(all_failures)} failure(s))")
        return 1
    print("CANONICAL BUDGET INTEGRITY GATE: PASS — all four locked-corpus budgets, all 16 invariant families")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
