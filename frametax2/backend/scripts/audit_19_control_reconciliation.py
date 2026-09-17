#!/usr/bin/env python3
"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION -- exact 19-row
control reconciliation. ONE set-based extraction (not per-control scans).
Runs against the isolated audit database only -- refuses otherwise.
"""
import asyncio
import csv
import json
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"
ENGINE_VERSION = "canonical-1.72.0"

REAL_PROJECT_IDS = [
    "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "4355ae88-a636-4c18-af60-ad73b2646124",
    "ab10b319-978e-44d3-9331-af2a5f2cccc2",
]

OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
NZ_POST = "new_zealand_screen_production_grant_—_international_post_vfx"

# MULTI_PRINCIPAL: controls whose defining set requires >=2 simultaneous
# principal_production-type legs (national "general production" credits
# in different countries) -- a shape the current ordinary_component_
# hybrid generator cannot express (its only anchor is home/alternate
# principal photography; every OTHER leg is restricted to movable
# post/vfx/music). Deferred to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_
# COMPOSITION, the next workstream -- never forced or faked here.
MULTI_PRINCIPAL = {"HO-003", "HO-007", "HO-012", "HO-013", "REG-4"}
# Distinct root cause, same consequence: HO-010's Saskatchewan grant leg
# and HO-011's Tennessee grant leg use component_type="fund_overlay" /
# "selective_upside" in their own direct-generator tests, but
# COMPONENT_BY_SPEND_CATEGORY (production_allocation.py) has ZERO
# entries mapping any real BudgetLineItem.spend_category to either
# type -- the real budget-driven pipeline can never construct one.
# Grants/funds are handled by a wholly separate, unconnected mechanism
# (build_available_funds/opportunity_discovery). Not fixable by a
# fixture without mislabeling grant spend as post/VFX/music -- the same
# violation in spirit as the dual-principal-leg forcing this workstream
# already ruled out. Reported under the same DEFERRED status (closest
# fit in the required taxonomy) but its natural next home is closer to
# the reinvestment/in-kind/gross-up opportunity engine workstream than
# the multi-principal one -- noted explicitly in each row's reason.
GRANT_COMPONENT_UNWIRED = {"HO-010", "HO-011"}
# REG-4 (ie_section_481 + uk_avec) confirmed to share the identical
# dual-principal-leg shape: its own direct-generator test
# (test_registered_control_4_ireland_uk_uses_separate_jurisdictional_
# components) builds BOTH components via _comp()'s DEFAULT
# component_type="principal_production" -- no override to "post"/"vfx"/
# "music" for either. Two simultaneous principal_production legs in
# different countries is exactly the shape evaluate_project()'s current
# ordinary_component_hybrid generator cannot express (one anchor +
# movable-only routing). Deferred alongside HO-003/007/012/013, never
# forced by mislabeling Ireland's or the UK's spend as a movable
# component -- that would misrepresent what the fixture actually proves.

CONTROLS = {
    "HO-001": {
        "set": frozenset({"us_ga_film_credit", NZ_POST, OCASE}),
        "expected": "PRICED",
    },
    "HO-002": {
        "set": frozenset({"us_nm_film_credit", "au_pdv_offset", OCASE}),
        "expected": "PRICED",
    },
    "HO-003": {
        "set": frozenset({"uk_avec", "au_producer_offset", NZ_POST}),
        "expected": "PRICED",
    },
    "HO-004": {
        "set": frozenset({"ca_federal_cptc", "on_ofttc", OCASE}),
        "expected": "RULE_REJECTED",
    },
    "HO-005": {
        "set": frozenset({"ca_federal_pstc", "on_opstc", OCASE}),
        "expected": "RULE_REJECTED",
    },
    "HO-006": {
        "set": frozenset({"ca_federal_pstc", "ca_bc_pstc", "ca_bc_dave"}),
        "expected": "RULE_REJECTED",
    },
    "HO-007": {
        "set": frozenset({"uk_avec", "fr_trip", NZ_POST}),
        "expected": "PRICED",
    },
    "HO-008": {
        "set": frozenset({"ie_section_481", "au_pdv_offset", OCASE}),
        "expected": "PRICED",
    },
    "HO-009": {
        "set": frozenset({"nz_spg_international", "ca_bc_dave", "us_ny_post_production_credit"}),
        "expected": "PRICED",
    },
    "HO-010": {
        "set": frozenset({"ca_federal_cptc", "on_ofttc", "ca_sk_creative_saskatchewan_grant"}),
        "expected": "PRICED",
    },
    "HO-011": {
        "set": frozenset({"us_ga_film_credit", NZ_POST, "us_tn_performance_grant"}),
        "expected": "PRICED",
    },
    "HO-012": {
        "set": frozenset({"uk_avec", "ie_section_481", "fr_trip"}),
        "expected": "PRICED",
    },
    "HO-013": {
        "set": frozenset({"uk_avec", "au_producer_offset", NZ_POST, OCASE}),
        "expected": "PRICED",
    },
    "REG-1": {"set": frozenset({"ca_bc_pstc", "ca_federal_cptc"}), "expected": "RULE_REJECTED"},
    "REG-2": {"set": frozenset({"ca_federal_cptc", "on_ofttc"}), "expected": "PRICED"},
    "REG-3": {"set": frozenset({"ca_federal_cptc", "on_opstc"}), "expected": "RULE_REJECTED"},
    "REG-4": {"set": frozenset({"ie_section_481", "uk_avec"}), "expected": "PRICED"},
    "REG-5": {"set": frozenset({"ny_state_film", "us_ny_post_production_credit"}), "expected": "PRICED"},
    "REG-6": {"set": frozenset({"on_ofttc", "on_opstc"}), "expected": "RULE_REJECTED"},
}

assert len(CONTROLS) == 19, f"expected exactly 19 controls, got {len(CONTROLS)}"


def subsets_missing_one(full_set: frozenset) -> list[frozenset]:
    """Every (n-1)-element subset of an n-element control set -- a
    genuine 'leg' one program short of the full control."""
    if len(full_set) < 3:
        return []
    return [full_set - {x} for x in full_set]


async def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2")
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
                           scr.calculation_trace_json->>'rejection_reason_class' AS rejection_reason_class,
                           scr.calculation_trace_json->'program_slugs' AS program_slugs,
                           ps.id AS structure_id, scr.id AS result_id, scr.input_fingerprint
                    FROM production_structures ps
                    JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                    JOIN projects p ON p.id = ps.project_id
                    WHERE scr.engine_version = :ev
                      AND p.id = ANY(:pids)
                      AND scr.calculation_trace_json ? 'program_slugs'
                    """
                ),
                {"ev": ENGINE_VERSION, "pids": REAL_PROJECT_IDS},
            )
        ).mappings().all()

    print(f"Single extraction: {len(rows)} rows across the 4 real productions under {ENGINE_VERSION}.\n")

    # Index by exact frozenset of program_slugs for O(1) exact lookup.
    by_exact_set: dict[frozenset, list] = {}
    for r in rows:
        key = frozenset(r["program_slugs"] or [])
        by_exact_set.setdefault(key, []).append(r)

    ledger = []
    for cid, spec in CONTROLS.items():
        full_set = spec["set"]
        expected = spec["expected"]
        exact_matches = by_exact_set.get(full_set, [])

        if cid in MULTI_PRINCIPAL or cid in GRANT_COMPONENT_UNWIRED:
            status = "MULTI_PRINCIPAL_DEFERRED_NEXT_WORKSTREAM"
            if cid in MULTI_PRINCIPAL:
                reason = (
                    "Requires >=2 simultaneous principal_production-type legs "
                    "(national general-production credits in different countries), "
                    "a shape the current ordinary_component_hybrid generator cannot "
                    "express regardless of anchor scope or fixture design. Belongs to "
                    "CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION."
                )
                next_action = "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream."
            else:
                reason = (
                    "DIFFERENT root cause from multi-principal: requires a "
                    "fund_overlay/selective_upside grant leg, but "
                    "COMPONENT_BY_SPEND_CATEGORY has no mapping to either "
                    "component type from any real spend_category -- the real "
                    "budget-driven pipeline can never construct one. Grants/funds "
                    "are handled by a separate, unconnected mechanism "
                    "(build_available_funds/opportunity_discovery). Natural home "
                    "is closer to REINVESTMENT_IN_KIND_GROSS_UP_OPPORTUNITY_ENGINE "
                    "than the multi-principal workstream."
                )
                next_action = (
                    "Defer -- requires wiring grant/selective-award discovery into the "
                    "generic generator's component vocabulary; route to whichever of "
                    "the next two workstreams actually owns grant/fund connection."
                )
            evidence = exact_matches[0] if exact_matches else None
            if exact_matches:
                # If it turns out the exact set DOES already exist naturally,
                # that would override the deferral -- report it plainly.
                status = "NATURAL_EXACT_MATCH" if evidence["status"] == "PRICED" else "EXPECTED_RULE_REJECTION_EXACT_MATCH"
                reason = "Exact set already present in canonical runtime -- deferral does not apply."
                next_action = "No fixture needed; already canonically verified."
        elif exact_matches:
            evidence = exact_matches[0]
            observed_status = evidence["status"]
            if observed_status == expected == "PRICED":
                status = "NATURAL_EXACT_MATCH"
            elif observed_status == expected == "RULE_REJECTED":
                status = "EXPECTED_RULE_REJECTION_EXACT_MATCH"
            else:
                status = f"MISMATCH:expected={expected},observed={observed_status}"
            reason = f"Exact {len(full_set)}-program set found verbatim in real production canonical runtime."
            next_action = "No fixture needed; already canonically verified through evaluate_project()."
        else:
            leg_matches = []
            for leg in subsets_missing_one(full_set):
                leg_rows = by_exact_set.get(leg, [])
                if leg_rows:
                    leg_matches.append((leg, leg_rows[0]))
            if leg_matches:
                evidence = leg_matches[0][1]
                status = "PARTIAL_LEG_ONLY_FIXTURE_REQUIRED"
                reason = (
                    f"Full {len(full_set)}-program set not found, but a genuine "
                    f"(n-1)-program leg ({sorted(leg_matches[0][0])}) arises naturally "
                    f"with disposition {evidence['status']} -- the missing program(s) "
                    "must be supplied via an AUDIT_CONTROL_* fixture."
                )
                next_action = f"Build AUDIT_CONTROL_{cid.replace('-', '_')} fixture; full set not naturally reachable."
            else:
                evidence = None
                status = "NO_NATURAL_MATCH_FIXTURE_REQUIRED"
                reason = "Neither the full set nor any (n-1)-program leg of it appears among the real productions."
                next_action = f"Build AUDIT_CONTROL_{cid.replace('-', '_')} fixture from scratch."

        ledger.append({
            "control_id": cid,
            "status": status,
            "required_program_set": sorted(full_set),
            "observed_program_set": sorted(evidence["program_slugs"]) if evidence else None,
            "project": evidence["title"] if evidence else None,
            "input_fingerprint": evidence["input_fingerprint"] if evidence else None,
            "structural_family": evidence["structural_family"] if evidence else None,
            "current_disposition": evidence["status"] if evidence else None,
            "fixture_required": status in (
                "PARTIAL_LEG_ONLY_FIXTURE_REQUIRED", "NO_NATURAL_MATCH_FIXTURE_REQUIRED",
            ),
            "reason": reason,
            "next_action": next_action,
        })

    assert len(ledger) == 19
    status_counts: dict[str, int] = {}
    for row in ledger:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    total_check = sum(status_counts.values())
    assert total_check == 19, f"status counts sum to {total_check}, not 19"

    print("STATUS COUNTS:")
    for k, v in sorted(status_counts.items()):
        print(f"  {k}: {v}")
    print(f"  TOTAL: {total_check}\n")

    for row in ledger:
        print(json.dumps(row, indent=2, default=str))

    out_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "validation",
                             "CLAUDE_GENERIC_DISCOVERY_19_CONTROL_RECONCILIATION.csv")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ledger[0].keys()))
        w.writeheader()
        for row in ledger:
            r = dict(row)
            r["required_program_set"] = "|".join(r["required_program_set"])
            r["observed_program_set"] = "|".join(r["observed_program_set"]) if r["observed_program_set"] else ""
            w.writerow(r)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
