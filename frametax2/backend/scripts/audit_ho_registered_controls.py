#!/usr/bin/env python3
"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION -- control census.

ONE set-based extraction (not 19 repeated full scans): pull every
structural_archetype_generator-classified row for the four real
canonical productions under the current engine version in a single
query, then do the 19 exact program-set comparisons in memory.

Run against the isolated audit database ONLY -- refuses otherwise.
"""
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"

REAL_PROJECT_IDS = {
    "The Little Utopia": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "F#K Valentine's Day": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "Bad Hombres": "4355ae88-a636-4c18-af60-ad73b2646124",
    "Lips Like Sugar": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
}

OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"

HO_CONTROLS = {
    "HO-001": frozenset({"us_ga_film_credit", "new_zealand_screen_production_grant_—_international_post_vfx", OCASE}),
    "HO-002": frozenset({"us_nm_film_credit", "au_pdv_offset", OCASE}),
    "HO-003": frozenset({"uk_avec", "au_producer_offset", "new_zealand_screen_production_grant_—_international_post_vfx"}),
    "HO-004": frozenset({"ca_federal_cptc", "on_ofttc", OCASE}),
    "HO-005": frozenset({"ca_federal_pstc", "on_opstc", OCASE}),
    "HO-005_2WAY": frozenset({"on_opstc", OCASE}),
    "HO-006": frozenset({"ca_federal_pstc", "ca_bc_pstc", "ca_bc_dave"}),
    "HO-006_2WAY": frozenset({"ca_bc_pstc", "ca_bc_dave"}),
    "HO-007": frozenset({"uk_avec", "fr_trip", "new_zealand_screen_production_grant_—_international_post_vfx"}),
    "HO-008": frozenset({"ie_section_481", "au_pdv_offset", OCASE}),
    "HO-009": frozenset({"nz_spg_international", "ca_bc_dave", "us_ny_post_production_credit"}),
    "HO-010": frozenset({"ca_federal_cptc", "on_ofttc", "ca_sk_creative_saskatchewan_grant"}),
    "HO-011": frozenset({"us_ga_film_credit", "new_zealand_screen_production_grant_—_international_post_vfx", "us_tn_performance_grant"}),
    "HO-012": frozenset({"uk_avec", "ie_section_481", "fr_trip"}),
    "HO-013": frozenset({"uk_avec", "au_producer_offset", "new_zealand_screen_production_grant_—_international_post_vfx", OCASE}),
}

REGISTERED_CONTROLS = {
    "REG-1": frozenset({"ca_bc_pstc", "ca_federal_cptc"}),
    "REG-2": frozenset({"ca_federal_cptc", "on_ofttc"}),
    "REG-3": frozenset({"ca_federal_cptc", "on_opstc"}),
    "REG-4": frozenset({"ie_section_481", "uk_avec"}),
    "REG-5": frozenset({"ny_state_film", "us_ny_post_production_credit"}),
    "REG-6": frozenset({"on_ofttc", "on_opstc"}),
}

ALL_CONTROLS = {**{f"HO:{k}": v for k, v in HO_CONTROLS.items()}, **{f"REG:{k}": v for k, v in REGISTERED_CONTROLS.items()}}


async def main() -> None:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2",
    )
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved audit database.")
        sys.exit(1)

    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    """
                    SELECT p.title, scr.calculation_trace_json->>'candidate_status' AS status,
                           scr.calculation_trace_json->>'anchor_jurisdiction' AS anchor,
                           scr.calculation_trace_json->>'structural_family' AS structural_family,
                           scr.calculation_trace_json->'program_slugs' AS program_slugs,
                           ps.id AS structure_id, scr.id AS result_id, scr.input_fingerprint
                    FROM production_structures ps
                    JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                    JOIN projects p ON p.id = ps.project_id
                    WHERE scr.engine_version = 'canonical-1.72.0'
                      AND p.id = ANY(:pids)
                      AND scr.calculation_trace_json ? 'program_slugs'
                    """
                ),
                {"pids": list(REAL_PROJECT_IDS.values())},
            )
        ).mappings().all()

    print(f"Extracted {len(rows)} structural_archetype_generator rows across the 4 real productions in one query.\n")

    matches: dict[str, list] = {k: [] for k in ALL_CONTROLS}
    for r in rows:
        slugs = frozenset(r["program_slugs"] or [])
        for cid, program_set in ALL_CONTROLS.items():
            if slugs == program_set:
                matches[cid].append(r)

    for cid, program_set in ALL_CONTROLS.items():
        found = matches[cid]
        if found:
            r = found[0]
            print(f"{cid}: ARISES NATURALLY  project={r['title']!r} status={r['status']} "
                  f"anchor={r['anchor']} family={r['structural_family']} "
                  f"structure_id={r['structure_id']} result_id={r['result_id']} (n={len(found)})")
        else:
            print(f"{cid}: NOT FOUND among real productions -- needs audit-only fixture "
                  f"(program set: {sorted(program_set)})")


if __name__ == "__main__":
    asyncio.run(main())
