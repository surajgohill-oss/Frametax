#!/usr/bin/env python3
"""Rebuild HO-004/005/006 fixtures WITH the real required amount facts
(ca_federal_cptc_qualified_labour_usd / ca_federal_pstc_qualified_labour_usd
-- found by reading program_rate_rules_worldwide.py's own RateCondition
definitions for these two programs) that were missing from the first
attempt. Runs against the isolated audit database only.
"""
import asyncio
import os
import sys
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"
OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"

FIXTURES = [
    ("HO-004", "CA-ON", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (Ontario)", 1_800_000.0, "atl_director"),
        ("8100 VFX (OCASE)", 300_000.0, "vfx"),
    ], [("amount_fact:ca_federal_cptc_qualified_labour_usd", "1860000")],
     frozenset({"ca_federal_cptc", "on_ofttc", OCASE})),
    ("HO-005", "CA-ON", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal service)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (Ontario service)", 1_800_000.0, "atl_director"),
        ("8100 VFX (OCASE)", 300_000.0, "vfx"),
    ], [("amount_fact:ca_federal_pstc_qualified_labour_usd", "2800000")],
     frozenset({"ca_federal_pstc", "on_opstc", OCASE})),
    ("HO-006", "CA-BC", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal service)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (BC service)", 1_800_000.0, "atl_director"),
        ("2002 ATL DIRECTOR FEE (BC DAVE)", 300_000.0, "atl_director"),
    ], [("amount_fact:ca_federal_pstc_qualified_labour_usd", "1860000")],
     frozenset({"ca_federal_pstc", "ca_bc_pstc", "ca_bc_dave"})),
]


async def build_and_evaluate(db, ce, control_id, home_code, total_budget, lines, facts, target_set):
    from app.models.budget import BudgetDocument, BudgetLineItem
    from app.models.jurisdiction import Jurisdiction
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.project_fact import ProjectFact
    from app.models.enums import ProjectFactSourceType

    jur = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == home_code))).scalars().first()
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"AUDIT_CONTROL Org {suffix}", slug=f"audit-control-{suffix}")
    db.add(org)
    await db.flush()

    project = Project(
        id=uuid.uuid4(), organization_id=org.id,
        title=f"AUDIT_CONTROL_{control_id.replace('-', '_')}_{suffix}",
        home_jurisdiction_id=jur.id, total_budget_usd=total_budget,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    doc = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="audit_control.pdf", file_type="pdf",
        is_active=True, extraction_status="completed", total_budget_raw=total_budget,
    )
    db.add(doc)
    await db.flush()
    for desc, amt, cat in lines:
        db.add(BudgetLineItem(
            id=uuid.uuid4(), budget_document_id=doc.id, description=desc,
            amount_raw=amt, amount_usd=amt, spend_category=cat,
        ))
    for fact_key, value in facts:
        db.add(ProjectFact(
            id=uuid.uuid4(), project_id=project.id, fact_key=fact_key,
            value=value, value_type="number", source_type=ProjectFactSourceType.USER_OVERRIDE,
        ))
    await db.commit()

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result.get("state_fingerprint")

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->>'rejection_reason_class' AS rejection_reason_class,
                       scr.calculation_trace_json->>'reason' AS reason,
                       scr.calculation_trace_json->'program_slugs' AS program_slugs,
                       scr.calculation_trace_json->'blocking_pairs' AS blocking_pairs,
                       ps.id AS structure_id, scr.id AS result_id
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json ? 'program_slugs'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()

    exact = [r for r in rows if frozenset(r["program_slugs"] or []) == target_set]
    # Also check whether ca_federal_cptc/pstc now appears ANYWHERE at all
    fed_slug = "ca_federal_cptc" if control_id == "HO-004" else "ca_federal_pstc"
    fed_appears = any(fed_slug in (r["program_slugs"] or []) for r in rows)

    return {
        "control_id": control_id, "project_id": str(project.id), "fingerprint": fingerprint,
        "target_set": sorted(target_set), "exact_match": exact[0] if exact else None,
        "federal_program_appears_anywhere": fed_appears, "total_rows": len(rows),
    }


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved audit database.")
        sys.exit(1)

    from app.services import canonical_evaluation as ce

    async with AsyncSession(engine, expire_on_commit=False) as db:
        for control_id, home_code, total_budget, lines, facts, target_set in FIXTURES:
            r = await build_and_evaluate(db, ce, control_id, home_code, total_budget, lines, facts, target_set)
            print(r)


if __name__ == "__main__":
    asyncio.run(main())
