#!/usr/bin/env python3
"""Semantic acceptance validator for the Codex remaining-authority research set."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import psycopg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DB = "postgresql://frametax:frametax@localhost:5432/frametax2"
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def read_csv(name: str) -> list[dict[str, str]]:
    path = HERE / name
    if not path.exists() or path.stat().st_size == 0:
        fail(f"missing/empty {name}")
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not reader.fieldnames or any(None in row for row in rows):
            fail(f"inconsistent CSV width/header in {name}")
        return rows


def main() -> int:
    census = read_csv("CODEX_REINVESTMENT_GROSS_UP_INTERNAL_CENSUS.csv")
    authority = read_csv("CODEX_REINVESTMENT_GROSS_UP_AUTHORITY_RESEARCH.csv")
    disposition = read_csv("CODEX_REINVESTMENT_GROSS_UP_ECONOMIC_DISPOSITIONS.csv")
    examples = read_csv("CODEX_REINVESTMENT_GROSS_UP_WORKED_EXAMPLES.csv")
    conflicts = read_csv("CODEX_REINVESTMENT_GROSS_UP_CONFLICTS.csv")
    stacking = read_csv("CODEX_31_STACKING_AUTHORITY_RESOLUTION.csv")
    nodes = read_csv("CODEX_90_NODE_STRUCTURAL_SCOPE_RESOLUTION.csv")
    questions = read_csv("CODEX_REMAINING_AUTHORITY_QUESTIONS.csv")
    checks = read_csv("CODEX_AUTHORITY_RESEARCH_MANUAL_CHECKS.csv")

    source_path = HERE / "CODEX_REINVESTMENT_GROSS_UP_SOURCE_LOG.jsonl"
    sources = []
    if not source_path.exists():
        fail("missing source log")
    else:
        for line_no, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                sources.append(json.loads(line))
            except json.JSONDecodeError as exc:
                fail(f"source log line {line_no} invalid JSON: {exc}")
    source_by_id = {s.get("retrieval_id"): s for s in sources}
    if len(source_by_id) != len(sources):
        fail("duplicate retrieval IDs")
    for s in sources:
        if not s.get("exact_locator") or not s.get("short_excerpt_present_in_content"):
            fail(f"retrieval lacks locator/excerpt: {s.get('retrieval_id')}")
        excerpt = s.get("short_excerpt_present_in_content", "")
        if hashlib.sha256(excerpt.encode()).hexdigest() != s.get("extracted_content_sha256"):
            fail(f"retrieval excerpt hash mismatch: {s.get('retrieval_id')}")
        if int(s.get("content_length", -1)) != len(excerpt):
            fail(f"retrieval content length mismatch: {s.get('retrieval_id')}")

    # Reproduce the physical database census. Static records and the zero-row assertion are fixed code/catalog entries.
    try:
        with psycopg.connect(DB) as conn, conn.cursor() as cur:
            cur.execute("select count(*) from qualifying_spend_categories where spend_category in ('deferment','in_kind','reinvestment','equity_participation','travel','lodging','btl_transportation','btl_equipment_rental','btl_stage_facility','btl_location_fees','vessel_marine')")
            qsc = cur.fetchone()[0]
            cur.execute("select count(*) from program_spend_treatments where labor_type in ('travel','accommodation_lodging','per_diem','customs_imports','marine_vessel')")
            pst = cur.fetchone()[0]
            cur.execute("select count(*) from fund_economics")
            funds = cur.fetchone()[0]
            cur.execute("select count(*) from production_contributions")
            contributions = cur.fetchone()[0]
        expected = qsc + pst + funds + 10 + 1
        if len(census) != expected:
            fail(f"census incomplete: {len(census)} != current expected {expected}")
        counts = Counter(r["record_type"] for r in census)
        if counts != Counter({"QPE_CATEGORY": qsc, "SPEND_TREATMENT": pst, "FUND_ECONOMICS": funds, "STATIC_CODE_RECORD": 10, "ZERO_ROW_TABLE_ASSERTION": 1}):
            fail(f"census type counts do not reproduce database/code inventory: {counts}")
        if contributions != 0:
            fail(f"production_contributions changed from locked zero-row census: {contributions}")
    except Exception as exc:
        fail(f"database census reproduction failed: {exc}")

    keys = [(r["storage_location"], r["physical_record_key"]) for r in census]
    if len(keys) != len(set(keys)):
        fail("physical census records were duplicated/collapsed")
    ids = {r["record_id"] for r in census}
    if len(ids) != len(census):
        fail("duplicate census record IDs")
    if {r["record_id"] for r in authority} != ids or {r["record_id"] for r in disposition} != ids:
        fail("authority/disposition row parity with census failed")

    primary = {s["retrieval_id"] for s in sources if s.get("source_classification") == "PRIMARY_OFFICIAL"}
    allowed_cash = {"CASH", "NON_CASH", "CATEGORY_DEPENDENT"}
    positive = {"GROSS_UP_QPE_AND_PRODUCTION_COST", "GROSS_UP_PRODUCTION_COST_ONLY"}
    auth_by_id = {r["record_id"]: r for r in authority}
    for row in authority:
        refs = {x for x in row.get("supporting_retrieval_ids", "").split(";") if x}
        missing = refs - source_by_id.keys()
        if missing:
            fail(f"unknown retrieval references for {row['record_id']}: {sorted(missing)}")
        if row.get("cash_non_cash") not in allowed_cash:
            fail(f"cash/non-cash treatment conflated or absent: {row['record_id']}")
        if not row.get("related_party_treatment") or not row.get("payment_required"):
            fail(f"related-party/payment-timing treatment hidden: {row['record_id']}")
        if not row.get("unresolved_facts"):
            fail(f"unresolved facts hidden: {row['record_id']}")
        if row.get("current_status", "").startswith("RESOLVED") and row["record_id"] != census[-1]["record_id"] and not (refs & primary):
            fail(f"resolved authority row lacks primary retrieval: {row['record_id']}")

    for row in disposition:
        refs = {x for x in row.get("source_retrieval_ids", "").split(";") if x}
        if row["economic_disposition"] in positive:
            if not (refs & primary):
                fail(f"gross-up allowed without primary authority: {row['record_id']}")
            if not row.get("valuation_source") or not row.get("financing_offset_treatment"):
                fail(f"positive gross-up lacks valuation/financing offset: {row['record_id']}")
        if row.get("gross_up_eligibility") == "YES" and row["economic_disposition"] not in positive:
            fail(f"gross-up flag/disposition conflict: {row['record_id']}")
        if "TRAVEL" in row.get("economic_type", "") and row.get("qpe_inclusion_percentage") not in {"0", "PROGRAM_SPECIFIC"}:
            fail(f"travel enters QPE without express authority: {row['record_id']}")
        if "CONDITIONAL" in row["economic_disposition"] and row.get("recommendation_treatment", "").startswith("GUARANTEED"):
            fail(f"conditional support treated as guaranteed: {row['record_id']}")
        if not row.get("double_count_prevention_rule") or "once" not in row["double_count_prevention_rule"].lower():
            fail(f"double-count protection absent: {row['record_id']}")

    # Exact corrected-oracle interaction set.
    try:
        raw = subprocess.check_output(["git", "show", "940ef8f78bb69bb343a954e34f6e9c2151489fd0:docs/validation/CODEX_LEGAL_COMPATIBILITY_ORACLE.csv"], cwd=ROOT, text=True)
        expected_interactions = {r["interaction_id"] for r in csv.DictReader(io.StringIO(raw)) if r["disposition"] == "UNRESOLVED"}
        got = {r["interaction_id"] for r in stacking}
        if len(stacking) != 31 or got != expected_interactions:
            fail("31-interaction corrected-oracle coverage mismatch")
    except Exception as exc:
        fail(f"could not reproduce corrected oracle: {exc}")
    for row in stacking:
        if not row.get("authority") or not row.get("exact_locator") or not row.get("implementation_consequence"):
            fail(f"stacking disposition incomplete: {row.get('interaction_id')}")
        if row["disposition"].startswith("UNRESOLVED") and not row.get("unresolved_facts"):
            fail(f"stacking unresolved fact hidden: {row['interaction_id']}")

    node_hash = hashlib.sha256("\n".join(sorted(r["node_id"] for r in nodes)).encode()).hexdigest()
    allowed_node_classes = {"POSITIVE_STRUCTURAL_SCOPE_CONFIRMED", "NO_DIRECT_STACKING_RELATIONSHIP", "SAME_ECONOMIC_IDENTITY", "TREATY_RELATIONSHIP_REQUIRED", "SELECTIVE_OR_CONDITIONAL_OVERLAY", "GROSS_UP_REINVESTMENT_OR_IN_KIND", "NON_QPE_SUPPORT_ONLY", "AUTHORITY_RESEARCH_REQUIRED"}
    if len(nodes) != 90 or len({r["node_id"] for r in nodes}) != 90 or node_hash != "947a2b858ca10629bd6adb06bed0b28ac2e5e1ea433c43c22ae6fd10ec16c8aa":
        fail("90-node identity coverage mismatch")
    for row in nodes:
        if row.get("classification") not in allowed_node_classes:
            fail(f"node silently/unacceptably classified: {row.get('node_id')}")
        if row["classification"] == "SAME_ECONOMIC_IDENTITY" and not row.get("identity_group"):
            fail(f"alias merged without identity proof group: {row['node_id']}")

    # All required mechanism examples and arithmetic identities.
    expected_mechanisms = {"reinvested_cash", "eligible_contributed_services", "eligible_contributed_goods", "deferred_compensation", "vendor_discount", "government_provided_service", "travel_accommodation", "non_qpe_in_kind"}
    if {r["mechanism"] for r in examples} != expected_mechanisms:
        fail("worked-example mechanism coverage mismatch")
    for row in examples:
        gross, incentive, offset, npc = map(float, (row["grossed_up_production_cost"], row["incentive_after_gross_up"], row["financing_support_adjustment"], row["final_npc"]))
        if abs((gross - incentive - offset) - npc) > 0.01:
            fail(f"worked-example double-count arithmetic failed: {row['mechanism']}")

    # Manual checks cover every census record because every selected row is QPE/NPC/travel/fund-relevant.
    if {r["record_id"] for r in checks} != ids:
        fail("manual checks do not cover every selected census record")
    if not questions or not conflicts:
        fail("question/conflict ledgers empty")
    handoff = HERE / "CODEX_AUTHORITY_IMPLEMENTATION_HANDOFF.md"
    if not handoff.exists() or "GROSS_UP_AUTHORITY_RESEARCH_COMPLETE_WITH_DOCUMENTED_GAPS" not in handoff.read_text(encoding="utf-8"):
        fail("handoff missing permitted final status")

    forbidden = ("TODO", "TBD", "LOREM IPSUM", "GENERATED SUBSTANTIVE VALUE")
    for path in HERE.glob("CODEX_*AUTHORITY*.csv"):
        text = path.read_text(encoding="utf-8").upper()
        for token in forbidden:
            if token in text:
                fail(f"default/generated substantive marker {token} in {path.name}")

    if ERRORS:
        print("VALIDATION: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1
    print("VALIDATION: PASS")
    print(f"census={len(census)} sources={len(sources)} primary={len(primary)} authority={len(authority)} dispositions={len(disposition)} stacking={len(stacking)} nodes={len(nodes)} manual_checks={len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
