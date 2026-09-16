#!/usr/bin/env python3
"""Hard validator for the frozen Codex worldwide stacking audit artifacts."""
from __future__ import annotations

import csv
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        assert rows, f"{name}: empty"
        width = len(rows[0])
        assert all(len(row) == width for row in rows), f"{name}: malformed row"
        return rows


nodes = read("CODEX_GLOBAL_STACKING_PROGRAM_NODES.csv")
pairs = read("CODEX_GLOBAL_STACKING_ALL_PAIRS.csv")
plausible = read("CODEX_GLOBAL_STACKING_PLAUSIBLE_PAIRS.csv")
authority = read("CODEX_GLOBAL_STACKING_AUTHORITY_EVIDENCE.csv")
gaps = read("CODEX_GLOBAL_STACKING_REGISTRY_GAPS.csv")
higher = read("CODEX_GLOBAL_STACKING_HIGHER_ORDER.csv")
runtime = read("CODEX_GLOBAL_STACKING_RUNTIME_COMPARISON.csv")
spots = read("CODEX_GLOBAL_STACKING_CALCULATION_SPOTCHECKS.csv")
findings = read("CODEX_GLOBAL_STACKING_FINDINGS.csv")

node_ids = [row["program_id"] for row in nodes]
assert len(node_ids) == 126, f"node count {len(node_ids)} != 126"
assert len(node_ids) == len(set(node_ids)), "duplicate node ID"

expected_pairs = {"::".join(pair) for pair in itertools.combinations(sorted(node_ids), 2)}
actual_pairs = [row["pair_id"] for row in pairs]
assert len(actual_pairs) == 126 * 125 // 2 == 7875
assert len(actual_pairs) == len(set(actual_pairs)), "duplicate unordered pair"
assert set(actual_pairs) == expected_pairs, "missing or extraneous unordered pair"
assert all(row["preliminary_classification"] for row in pairs)
assert all(row["plausible"] in {"YES", "NO"} for row in pairs)

plausible_ids = [row["pair_id"] for row in plausible]
assert len(plausible_ids) == len(set(plausible_ids)), "duplicate plausible pair"
assert set(plausible_ids) == {row["pair_id"] for row in pairs if row["plausible"] == "YES"}
assert all(row["final_disposition"] and row["final_disposition"] != "UNKNOWN" for row in plausible)
assert {row["pair_id"] for row in authority} == set(plausible_ids)

registered = [row for row in gaps if row["record_type"] == "REGISTERED_RULE"]
assert len(registered) == 229, f"registered rule count {len(registered)} != 229"
assert all(row["pair_id"] in expected_pairs or row["finding"] == "REGISTERED_RULE_PROGRAM_NOT_EXECUTABLE" for row in registered)
missing = [row for row in gaps if row["record_type"] == "MISSING_RULE"]
assert {row["pair_id"] for row in missing} == {
    row["pair_id"] for row in plausible if row["existing_rule"] == "NO"
}

for row in higher:
    programs = row["programs"].split(" | ")
    assert len(programs) == int(row["size"]) >= 3
    assert len(programs) == len(set(programs))
    assert set(programs) <= set(node_ids)
    assert all("::".join(sorted(pair)) in set(plausible_ids) for pair in itertools.combinations(programs, 2))

oracle_ids = {("PAIR", row["pair_id"]) for row in plausible}
oracle_ids |= {("HIGHER_ORDER", row["combination_id"]) for row in higher}
runtime_ids = {(row["combination_type"], row["combination_id"]) for row in runtime}
assert runtime_ids == oracle_ids, "runtime comparison does not cover the oracle"
allowed_runtime = {
    "GENERATED_AND_PRICED", "GENERATED_CONDITIONAL", "PRECISELY_REJECTED",
    "SILENTLY_OMITTED", "GENERATED_WITH_WRONG_PROGRAM_SET",
    "GENERATED_WITH_WRONG_INTERACTION_RULE", "NOT_TRIGGERED_BY_ANY_OF_FOUR_PROJECTS",
}
assert all(row["runtime_classification"] in allowed_runtime for row in runtime)

assert len(spots) == 12
assert all(row["result"] == "PASS" for row in spots)
assert max(abs(float(row["variance_usd"])) for row in spots) <= 0.01
assert findings

summary = ROOT / "CODEX_GLOBAL_STACKING_AUDIT.md"
assert summary.stat().st_size > 1000
assert "GLOBAL_STACKING_ORACLE_COMPLETE" in summary.read_text(encoding="utf-8")

print(
    "PASS nodes=126 pairs=7875 plausible={} registered=229 higher={} "
    "runtime={} spotchecks=12 findings={}".format(
        len(plausible), len(higher), len(runtime), len(findings)
    )
)
