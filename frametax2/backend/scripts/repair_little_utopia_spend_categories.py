#!/usr/bin/env python3
"""LU Mauritius economics reconciliation — idempotent, keyed-by-identity repair.

Two independently confirmed defects on Little Utopia's REAL persisted data
(see canonical_evaluation.py ENGINE_VERSION "canonical-1.94.0" changelog for
the full investigation and independent QPE reconstruction):

1. PERSISTED_PROJECT_DATA_DEFECT — budget_line_items.spend_category for 16
   of Little Utopia's 44 real budget lines diverged from the already-
   evidenced, per-line-reasoned classification in
   app/data/little_utopia_real_budget.py's LITTLE_UTOPIA_REAL_SPEND_CATEGORY
   (12 non-zero lines sat in the generic "miscellaneous" bucket, 2 in
   "general_administration" — neither has a Mauritius EDB qualification
   rule, so real qualifying spend fell to GREY_AREA_REQUIRES_AUTHORITY).
   Repaired here by account code, matched against this SPECIFIC production's
   SPECIFIC budget document — never a project-title branch in any evaluator.

2. PROJECT_FACT_MISSING — Little Utopia's own real contingency-utilization
   election (100%, LITTLE_UTOPIA_CONTINGENCY_EXPECTED_UTILIZATION_PCT)
   existed only in the legacy demo module, never as a canonical ProjectFact
   row for the real database-backed project, so qualification_derivation.py
   greyed out the entire $301,131 contingency reserve.

Keyed to stable identity (budget_document_id + exact account code parsed
from the line's own description; project_id + fact_key for the fact row —
project_facts has a real UNIQUE(project_id, fact_key) constraint), so this
script is safe to re-run: every statement is a no-op once applied.

Run with (DATABASE_URL must resolve to the approved acceptance database):
    cd frametax2/backend && python3 scripts/repair_little_utopia_spend_categories.py
"""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_optimizer_acceptance_20260919"
LU_PROJECT_TITLE = "The Little Utopia"

# account_code -> corrected spend_category, per
# LITTLE_UTOPIA_REAL_SPEND_CATEGORY (little_utopia_real_budget.py),
# restricted to the codes whose PERSISTED category actually diverges from
# it. "3200" (production_sound) and "7300" (no override, genuine grey) are
# deliberately excluded — see the ENGINE_VERSION changelog for why.
CORRECTED_SPEND_CATEGORY: dict[str, str] = {
    "1000": "atl_writer",              # DEVELOPMENT
    "2000": "btl_crew_labor",          # PRODUCTION STAFF
    "2100": "btl_crew_labor",          # EXTRA TALENT
    "2500": "btl_equipment_rental",    # PROPERTIES
    "2600": "btl_equipment_rental",    # PICTURE VEHICLES AND ANIMALS
    "2700": "btl_equipment_rental",    # WARDROBE
    "3000": "btl_equipment_rental",    # ELECTRICAL
    "3100": "btl_equipment_rental",    # CAMERA
    "3300": "vessel_marine",           # SPECIAL EFFECTS & MARINE
    "3400": "btl_location_fees",       # LOCATION EXPENSE
    "3500": "btl_equipment_rental",    # AERIAL/DRONE UNIT
    "3800": "btl_equipment_rental",    # PRODUCTION LAB & MEDIA MANAGEMENT
    "4000": "btl_equipment_rental",    # SPECIAL SHOOT UNITS ($0, immaterial)
    "6500": "legal_accounting",        # USA ADMIN COSTS ($0, territorially excluded anyway)
    "7000": "production_service_fees", # ADMINISTRATIVE EXPENSES
    "7100": "btl_crew_labor",          # PUBLICITY
}

CONTINGENCY_UTILIZATION_PCT = "100.0"


async def repair(db: AsyncSession) -> dict:
    project_row = (await db.execute(
        text("SELECT id FROM projects WHERE title = :t"), {"t": LU_PROJECT_TITLE}
    )).first()
    if project_row is None:
        return {"error": f"no project titled {LU_PROJECT_TITLE!r} found"}
    project_id = project_row[0]

    doc_row = (await db.execute(
        text("SELECT id FROM budget_documents WHERE project_id = :p AND is_active = true"),
        {"p": project_id},
    )).first()
    if doc_row is None:
        return {"error": "no active budget_document found for Little Utopia"}
    doc_id = doc_row[0]

    category_changes = []
    for code, target_category in CORRECTED_SPEND_CATEGORY.items():
        before = (await db.execute(
            text(
                "SELECT id, description, amount_usd, spend_category FROM budget_line_items "
                "WHERE budget_document_id = :d AND description LIKE :prefix"
            ),
            {"d": doc_id, "prefix": f"{code} %"},
        )).all()
        for row in before:
            line_id, description, amount_usd, current_category = row
            if current_category == target_category:
                continue  # already correct — idempotent no-op
            await db.execute(
                text("UPDATE budget_line_items SET spend_category = :cat WHERE id = :id"),
                {"cat": target_category, "id": line_id},
            )
            category_changes.append({
                "description": description, "amount_usd": float(amount_usd),
                "from": current_category, "to": target_category,
            })

    fact_row = (await db.execute(
        text("SELECT id, value FROM project_facts WHERE project_id = :p AND fact_key = 'contingency_expected_utilization_pct'"),
        {"p": project_id},
    )).first()
    fact_change = None
    if fact_row is None:
        await db.execute(
            text(
                "INSERT INTO project_facts "
                "(id, project_id, fact_key, value, value_type, source_type, source_location, "
                " extraction_confidence, review_status, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :p, 'contingency_expected_utilization_pct', :v, 'number', "
                " 'recovered_demo_state', "
                " 'Production election, no partial-utilization evidence on file (see little_utopia_real_budget.py LITTLE_UTOPIA_CONTINGENCY_EXPECTED_UTILIZATION_PCT)', "
                " 0.9, 'approved', now(), now())"
            ),
            {"p": project_id, "v": CONTINGENCY_UTILIZATION_PCT},
        )
        fact_change = {"from": None, "to": CONTINGENCY_UTILIZATION_PCT}
    elif fact_row[1] != CONTINGENCY_UTILIZATION_PCT:
        await db.execute(
            text("UPDATE project_facts SET value = :v, updated_at = now() WHERE id = :id"),
            {"v": CONTINGENCY_UTILIZATION_PCT, "id": fact_row[0]},
        )
        fact_change = {"from": fact_row[1], "to": CONTINGENCY_UTILIZATION_PCT}
    # else: already correct — idempotent no-op

    await db.commit()
    return {
        "project_id": str(project_id), "budget_document_id": str(doc_id),
        "spend_category_changes": category_changes,
        "contingency_fact_change": fact_change,
    }


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB:
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved database {APPROVED_DB!r}.")
        sys.exit(1)

    async with AsyncSession(engine, expire_on_commit=False) as db:
        result = await repair(db)

    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
