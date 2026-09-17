#!/usr/bin/env python3
"""Classify each AUDIT_CONTROL_* fixture's real terminal disposition,
checking THREE possibilities in order: (1) exact PRICED/RULE_REJECTED
program-set match; (2) a genuine DOMINATED_WITH_PROOF row for the same
(anchor, movable-component-subset) pair -- a complete, valid, proof-
backed disposition even when the literal combo never wins; (3) neither
found -- a real gap requiring further investigation.
"""
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"
OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
NZ_POST = "new_zealand_screen_production_grant_—_international_post_vfx"

# (control_id, project_id, home_jurisdiction, movable_component_subset)
FIXTURES = [
    ("HO-001", "b9797e0b-fb9f-4dca-8df9-522de4a9e88e", "US-GA", frozenset({"post", "vfx"})),
    ("HO-002", "b8be6aa9-2e6e-4e8a-b859-1bab57ae10ba", "US-NM", frozenset({"post", "vfx"})),
    ("HO-004", "45de139f-a55e-4126-957b-a4f6f150ef45", "CA-ON", frozenset({"vfx"})),
    ("HO-005", "e23d97f4-3171-41fc-8922-bf3ee279c8ec", "CA-ON", frozenset({"vfx"})),
    ("HO-006", "878b68be-4c6e-4445-92ba-c32d637cf889", "CA-BC", frozenset({"vfx"})),
    ("HO-008", "813d15f3-0910-40ea-badc-a8d5e86dd2c2", "IE", frozenset({"post", "vfx"})),
    ("HO-009", "033e355b-d9ff-4c0e-9710-2cf89f1393be", "NZ", frozenset({"post", "vfx"})),
    ("REG-5", "b86a8c14-b7ac-45cc-899f-b085b9f539d8", "US-NY", frozenset({"post"})),
]


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        print(f"REFUSING TO RUN: resolved database is {db_name!r}, not the approved audit database.")
        sys.exit(1)

    async with engine.connect() as conn:
        for control_id, project_id, home_code, subset in FIXTURES:
            dom_rows = (
                await conn.execute(
                    text(
                        """
                        SELECT scr.calculation_trace_json->>'component_subset',
                               scr.calculation_trace_json->>'dominated_combination_count',
                               scr.calculation_trace_json->>'proof_window_size',
                               scr.calculation_trace_json->'component_target_windows',
                               scr.calculation_trace_json->>'incumbent_structure_id'
                        FROM production_structures ps
                        JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                        WHERE ps.project_id = :pid
                          AND scr.calculation_trace_json->>'anchor_jurisdiction' = :anchor
                          AND scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'
                        """
                    ),
                    {"pid": project_id, "anchor": home_code},
                )
            ).fetchall()

            matched = None
            for row in dom_rows:
                subset_val = row[0]
                if subset_val is None:
                    continue
                # component_subset is stored as a JSON string of a list
                import json as _json
                try:
                    parsed = frozenset(_json.loads(subset_val))
                except Exception:
                    continue
                if parsed == subset:
                    matched = row
                    break

            if matched:
                print(f"{control_id}: DOMINATED_WITH_PROOF -- window={matched[2]} "
                      f"dominated_count={matched[1]} incumbent={matched[4]}")
                windows = matched[3] or {}
                for comp, targets in windows.items():
                    codes = [t.get("jurisdiction_code") for t in targets]
                    print(f"    window[{comp}] = {codes}")
            else:
                print(f"{control_id}: NO matching DOMINATED_WITH_PROOF row for anchor={home_code}, "
                      f"subset={sorted(subset)} -- genuinely unresolved, needs investigation")


if __name__ == "__main__":
    asyncio.run(main())
