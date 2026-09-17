#!/usr/bin/env python3
"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION -- audit-only
control fixtures. Builds real Project/BudgetDocument/BudgetLineItem rows
(the _make_or_project pattern from test_oregon_full_db_pipeline.py) for
the 8 controls confirmed architecturally reachable, runs each through
the REAL evaluate_project() path, and reports the actual terminal
disposition for the exact target program set -- never forcing an
outcome. Deterministic, audit-only, title-prefixed AUDIT_CONTROL_.

Runs ONLY against the isolated audit database.
"""
import asyncio
import os
import sys
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"
OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
NZ_POST = "new_zealand_screen_production_grant_—_international_post_vfx"

# (control_id, home_jurisdiction_code, total_budget, [(desc, amount, spend_category)], target_program_set)
FIXTURES = [
    ("HO-001", "US-GA", 11_983_654.0, [
        ("2000 ATL DIRECTOR FEE", 11_332_424.0, "atl_director"),
        ("8000 POST PRODUCTION", 611_230.0, "post_production"),
        ("8100 VFX", 40_000.0, "vfx"),
    ], frozenset({"us_ga_film_credit", NZ_POST, OCASE})),
    ("HO-002", "US-NM", 11_983_654.0, [
        ("2000 ATL DIRECTOR FEE", 11_332_424.0, "atl_director"),
        ("8000 POST PRODUCTION", 611_230.0, "post_production"),
        ("8100 VFX", 40_000.0, "vfx"),
    ], frozenset({"us_nm_film_credit", "au_pdv_offset", OCASE})),
    ("HO-004", "CA-ON", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (Ontario)", 1_800_000.0, "atl_director"),
        ("8100 VFX (OCASE)", 300_000.0, "vfx"),
    ], frozenset({"ca_federal_cptc", "on_ofttc", OCASE})),
    ("HO-005", "CA-ON", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal service)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (Ontario service)", 1_800_000.0, "atl_director"),
        ("8100 VFX (OCASE)", 300_000.0, "vfx"),
    ], frozenset({"ca_federal_pstc", "on_opstc", OCASE})),
    ("HO-006", "CA-BC", 3_100_000.0, [
        ("2000 ATL DIRECTOR FEE (federal service)", 1_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (BC service)", 1_800_000.0, "atl_director"),
        ("2002 ATL DIRECTOR FEE (BC DAVE)", 300_000.0, "atl_director"),
    ], frozenset({"ca_federal_pstc", "ca_bc_pstc", "ca_bc_dave"})),
    ("HO-008", "IE", 6_000_000.0, [
        ("2000 ATL DIRECTOR FEE (Irish principal)", 5_000_000.0, "atl_director"),
        ("8000 POST PRODUCTION (AU PDV)", 700_000.0, "post_production"),
        ("8100 VFX (OCASE)", 300_000.0, "vfx"),
    ], frozenset({"ie_section_481", "au_pdv_offset", OCASE})),
    ("HO-009", "NZ", 6_800_000.0, [
        ("2000 ATL DIRECTOR FEE (NZ principal)", 5_000_000.0, "atl_director"),
        ("2001 ATL DIRECTOR FEE (BC DAVE)", 300_000.0, "atl_director"),
        ("8000 POST PRODUCTION (NY)", 1_500_000.0, "post_production"),
    ], frozenset({"nz_spg_international", "ca_bc_dave", "us_ny_post_production_credit"})),
    ("REG-5", "US-NY", 4_500_000.0, [
        ("2000 ATL DIRECTOR FEE (NY principal)", 3_000_000.0, "atl_director"),
        ("8000 POST PRODUCTION (NY post)", 1_500_000.0, "post_production"),
    ], frozenset({"ny_state_film", "us_ny_post_production_credit"})),
]


async def build_and_evaluate(db, engine_module, control_id, home_code, total_budget, lines, target_set):
    from app.models.budget import BudgetDocument, BudgetLineItem
    from app.models.jurisdiction import Jurisdiction
    from app.models.organization import Organization
    from app.models.project import Project

    jur = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == home_code))).scalars().first()
    if jur is None:
        return {"control_id": control_id, "error": f"jurisdiction {home_code} not seeded"}

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
    await db.commit()

    try:
        result = await engine_module.evaluate_project(db, project.id)
    except Exception as exc:
        return {"control_id": control_id, "project_id": str(project.id), "error": f"evaluate_project raised: {exc}"}

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
    return {
        "control_id": control_id,
        "project_id": str(project.id),
        "project_title": project.title,
        "fingerprint": fingerprint,
        "evaluation_status": result.get("status"),
        "target_set": sorted(target_set),
        "exact_match_found": bool(exact),
        "exact_match": exact[0] if exact else None,
        "total_rows_this_fingerprint": len(rows),
    }


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved audit database.")
        sys.exit(1)

    from app.services import canonical_evaluation as ce

    results = []
    async with AsyncSession(engine, expire_on_commit=False) as db:
        for control_id, home_code, total_budget, lines, target_set in FIXTURES:
            print(f"=== Building and evaluating {control_id} (home={home_code}) ===", flush=True)
            r = await build_and_evaluate(db, ce, control_id, home_code, total_budget, lines, target_set)
            results.append(r)
            print(r, flush=True)
            print(flush=True)

    print("\n\n=== SUMMARY ===")
    for r in results:
        if "error" in r:
            print(f"{r['control_id']}: ERROR -- {r['error']}")
        else:
            m = r["exact_match"]
            if m:
                print(f"{r['control_id']}: DISPOSITIONED -- status={m['status']} "
                      f"rejection_class={m['rejection_reason_class']} structure_id={m['structure_id']}")
            else:
                print(f"{r['control_id']}: EXACT TARGET SET NOT FOUND among {r['total_rows_this_fingerprint']} "
                      f"rows for this fingerprint -- needs investigation (not yet dispositioned)")


if __name__ == "__main__":
    asyncio.run(main())
