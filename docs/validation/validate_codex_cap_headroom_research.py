#!/usr/bin/env python3
"""Integrity validator for the all-program cap-headroom research artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), name
        result = list(reader)
        assert all(len(r) == len(reader.fieldnames) for r in result), name
        return result


ledger = rows("CLAUDE_659_PHYSICAL_RECORD_IDENTITY_LEDGER.csv")
coverage = rows("CODEX_ALL_PROGRAM_CAP_HEADROOM_COVERAGE.csv")
rules = rows("CODEX_CAP_HEADROOM_CATEGORY_RULES.csv")
paths = rows("CODEX_DEFERMENT_REINVESTMENT_AUTHORITY.csv")
matrix = rows("CODEX_CAP_HEADROOM_FOUR_PROJECT_MATRIX.csv")
questions = rows("CODEX_CAP_HEADROOM_AGENCY_RULING_QUESTIONS.csv")
conflicts = rows("CODEX_CAP_HEADROOM_CONFLICTS.csv")

assert len(ledger) == 659
assert len(coverage) == len(ledger)
assert {r["physical_record_id"] for r in coverage} == {r["physical_record_id"] for r in ledger}
assert len({r["physical_record_id"] for r in coverage}) == len(coverage)
assert sum(r["unique_economic_identity"] == "YES" for r in coverage) == 658
assert sum(r["unique_economic_identity"] == "NO" for r in coverage) == 1
assert {r["registry_class"] for r in coverage} == {"EXECUTABLE", "COVERAGE_ONLY", "CATALOG_ONLY"}
assert Counter(r["registry_class"] for r in coverage) == Counter({"CATALOG_ONLY": 425, "EXECUTABLE": 126, "COVERAGE_ONLY": 108})

allowed_coverage = {
    "NO_RELEVANT_CAPPED_EXPENSE_CATEGORY",
    "CAPPED_CATEGORY_AUTHORITY_CONFIRMED",
    "CAPPED_CATEGORY_RULE_IN_DATABASE_AUTHORITY_MISSING",
    "POTENTIAL_CAPPED_CATEGORY_RESEARCH_REQUIRED",
    "SELECTIVE_GRANT_OR_FUND",
    "INACTIVE_OR_SUPERSEDED",
    "DUPLICATE_OR_ALIAS",
    "GENUINE_SCOPE_MISMATCH",
    "PROGRAM_IDENTITY_UNRESOLVED",
}
assert not ({r["disposition"] for r in coverage} - allowed_coverage)
assert all(r["disposition"] != "NO_RELEVANT_CAPPED_EXPENSE_CATEGORY" for r in coverage), "No absence conclusion was earned by silence"

rule_programs = {r["program_id"] for r in rules}
assert len(rule_programs) == 17
assert all(r["source_retrieval_ids"].startswith("CAP-") for r in rules)
assert all(r["payment_deadline"] for r in rules)
assert all(r["related_party_restriction"] for r in rules)
assert all(r["deferment_disposition"] != "DEFERRED_QPE_EXPLICITLY_AUTHORIZED" for r in rules)
assert sum(r["deferment_disposition"] == "DEFERRED_QPE_AUTHORIZED_IF_PAID_BY_DEADLINE" for r in rules) == 1
assert not any(r["cap_is_maximum"] == "YES" and r["deferment_disposition"] == "DEFERRED_QPE_EXPLICITLY_AUTHORIZED" for r in rules)

expected_path_types = {
    "CONTRACTUAL_DEFERRED_COMPENSATION", "CONTINGENT_COMPENSATION", "WAIVED_COMPENSATION",
    "PAID_AND_REINVESTED_COMPENSATION", "CIRCULAR_NON_SUBSTANTIVE_PAYMENT",
    "IN_KIND_CONTRIBUTION", "RELATED_PARTY_CHARGE",
}
assert len(paths) == len(rule_programs) * len(expected_path_types)
for pid in rule_programs:
    assert {r["path_type"] for r in paths if r["program_id"] == pid} == expected_path_types
assert all("Separate payable" in r["deferred_liability_treatment"] for r in paths)
assert all("count once" in r["reinvestment_cash_flow_treatment"] for r in paths)

assert {r["project_name"] for r in matrix} == {"The Little Utopia", "F#K Valentine's Day", "Bad Hombres", "Lips Like Sugar"}
assert len(matrix) == len(rules) * 4
assert all(Decimal(r["theoretically_recognized_additional_qpe_usd"]) == 0 for r in matrix)
assert all(Decimal(r["theoretical_incremental_incentive_usd"]) == 0 for r in matrix)
assert all(Decimal(r["net_permanent_benefit_usd"]) == 0 for r in matrix)
for r in matrix:
    if r["cap_amount_usd"] != "UNKNOWN":
        current = Decimal(r["current_category_amount_usd"])
        cap = Decimal(r["cap_amount_usd"])
        headroom = Decimal(r["unused_headroom_usd"])
        assert headroom == max(Decimal(0), cap - current), r

with (HERE / "CODEX_REINVESTMENT_GROSS_UP_SOURCE_LOG.jsonl").open(encoding="utf-8") as fh:
    log = [json.loads(line) for line in fh if line.strip()]
cap_sources = {r["retrieval_id"]: r for r in log if r.get("retrieval_id", "").startswith("CAP-")}
assert len(cap_sources) == 18
for sid, r in cap_sources.items():
    content = r["retrieved_or_extracted_content"]
    excerpt = r["short_exact_excerpt"]
    context = r["surrounding_extracted_context"]
    assert excerpt in content, sid
    assert context in content, sid
    digest = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    assert digest(content) == r["full_content_sha256"], sid
    assert digest(context) == r["extracted_context_sha256"], sid
    assert digest(excerpt) == r["excerpt_sha256"], sid
    assert int(r["full_content_length"]) == len(content), sid
    assert int(r["excerpt_length"]) == len(excerpt), sid
    assert r["source_classification"] == "PRIMARY_OFFICIAL", sid
    assert not r["final_url"].endswith("/search"), sid

referenced = {x for r in rules for x in r["source_retrieval_ids"].split(";") if x}
assert referenced <= cap_sources.keys()
assert conflicts
assert questions

closeout = (HERE / "CODEX_CAP_HEADROOM_RESEARCH_CLOSEOUT.md").read_text(encoding="utf-8")
assert "original 69-node set = 36 positive" in closeout
assert "later 90-node set = 42 positive" in closeout
assert "Status: `RESEARCH_INCOMPLETE`" in closeout
assert "recognized incremental QPE" in closeout

print("PASS: cap-headroom research artifact integrity")
print(f"coverage={len(coverage)} unique_economic=658 rules={len(rules)} paths={len(paths)} matrix={len(matrix)}")
print(f"strict_sources={len(cap_sources)} unresolved_questions={len(questions)}")
