#!/usr/bin/env python3
"""Hard acceptance gates for the Codex forensic gross-up research artifacts."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
errors: list[str] = []


def load_csv(name: str) -> list[dict[str, str]]:
    path = HERE / name
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"missing or empty: {name}")
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


coverage_all = load_csv("CODEX_ALL_PROGRAM_CAP_HEADROOM_COVERAGE.csv")
coverage_ids: list[str] = []
for row in coverage_all:
    if row.get("unique_economic_identity") == "YES" and row.get("canonical_program_id") not in coverage_ids:
        coverage_ids.append(row["canonical_program_id"])
require(len(coverage_ids) == 658, f"coverage must contain 658 unique identities, got {len(coverage_ids)}")

crosswalk = load_csv("CODEX_GROSS_UP_AUTHORITY_CROSSWALK.csv")
cross_ids = [row.get("canonical_program_id", "") for row in crosswalk]
require(len(crosswalk) == 658, f"crosswalk must contain 658 rows, got {len(crosswalk)}")
require(len(set(cross_ids)) == 658, "crosswalk canonical_program_id values are not unique")
require(set(cross_ids) == set(coverage_ids), "crosswalk is not an exact left join of the 658 identity universe")

mandatory_rule_fields = [
    "cost_recognition_rule", "payment_timing_rule", "related_party_rule", "fmv_arm_length_rule",
    "assistance_rebate_rule", "forgiveness_credit_note_netting_rule", "relevant_capped_categories",
    "field_evidence_ids", "source_review_status", "safe_optimizer_behavior",
]
for row in crosswalk:
    pid = row.get("canonical_program_id", "<missing>")
    for field in mandatory_rule_fields:
        require(bool(row.get(field, "").strip()), f"{pid}: hidden/blank required field {field}")
    for letter in "ABCDEFGHIJK":
        value = row.get(f"archetype_{letter}", "")
        require(bool(value), f"{pid}: missing archetype {letter}")
        if "QUALIFYING" in value or "EXCLUDED" in value:
            require(bool(row.get("field_evidence_ids", "")), f"{pid}: completed archetype {letter} lacks field evidence")
    # A cap is never, by itself, proof that deferment or reinvestment qualifies.
    if row.get("relevant_capped_categories") not in ("", "UNRESOLVED"):
        require(row.get("archetype_C") != "AUTHORITY_CONFIRMED_QUALIFYING", f"{pid}: cap improperly treated as reinvestment permission")
    require("NO_POSITIVE_GROSS_UP" in row.get("safe_optimizer_behavior", "") or pid.startswith("ie_section_481") or "catalog-only-3-Section 481" in pid,
            f"{pid}: safe behavior does not fail closed")

archetypes = load_csv("CODEX_GROSS_UP_TRANSACTION_ARCHETYPES.csv")
require([row.get("archetype_id") for row in archetypes] == list("ABCDEFGHIJK"), "archetype table must contain A-K exactly once and in order")
for row in archetypes:
    require(row.get("authoritative_disposition") != "AUTHORITY_CONFIRMED_QUALIFYING" or bool(row.get("evidence_ids")),
            f"archetype {row.get('archetype_id')} has permission without evidence")

practice = load_csv("CODEX_GROSS_UP_PRACTICE_EVIDENCE.csv")
require(len(practice) >= 6, "practice evidence must include the current manual, audit evidence, and negative search")
source_path = HERE / "CODEX_REINVESTMENT_GROSS_UP_SOURCE_LOG.jsonl"
source_rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines() if line.strip()]
source_by_id = {row.get("retrieval_id"): row for row in source_rows}
for row in practice:
    eid = row.get("evidence_id", "")
    require(row.get("source_opened_and_read", "").startswith("YES"), f"{eid}: source not opened/read")
    if eid.startswith("FORENSIC-IE-"):
        src = source_by_id.get(eid)
        require(src is not None, f"{eid}: absent from retained source log")
        if src:
            retained = src.get("retained_source_content", "")
            excerpt = row.get("verified_excerpt", "")
            require(bool(retained), f"{eid}: no retained source content")
            require(excerpt in retained, f"{eid}: verified excerpt is not present in retained source content")
            require(src.get("fetch_status") == "RETRIEVED_OPENED_READ_AND_EXCERPT_VERIFIED", f"{eid}: source read status not verified")
    if row.get("authority_or_practice_only") == "PRACTICE_ONLY":
        require(row.get("authority_level") != "PRIMARY_OFFICIAL_GUIDANCE", f"{eid}: industry/administrative practice mislabeled as authority")
        require(row.get("complete_transaction_example") == "NO", f"{eid}: practice evidence falsely treated as complete transaction authority")

ie = next((row for row in crosswalk if row.get("canonical_program_id") == "ie_section_481"), None)
require(ie is not None, "Ireland Section 481 lead case missing")
if ie:
    require("four months" in ie["payment_timing_rule"].lower(), "Ireland four-month payment deadline missing")
    require("15%" in ie["relevant_capped_categories"] and "10%" in ie["relevant_capped_categories"], "Ireland 15%/10% producer-fee parameters missing")
    require("RULING_REQUIRED" in ie["archetype_C"], "Ireland paid-then-reinvested chain improperly made positive")
    require("RULING_REQUIRED" in ie["archetype_D"], "Ireland receivable contribution improperly made positive")
    require("EXCLUDED" in ie["archetype_H"], "Ireland backend/contingent exclusion missing")
    require("RULING_REQUIRED" in ie["archetype_K"], "Ireland circular-payment chain improperly made positive")

rules = load_csv("CODEX_CAP_HEADROOM_CATEGORY_RULES.csv")
ie_rules = [r for r in rules if r.get("program_id") == "ie_section_481" and r.get("eligible_category", "").startswith("producer_related_fees_")]
require(len(ie_rules) == 2, f"expected two mutually exclusive Ireland producer-fee rows, got {len(ie_rules)}")
require({r.get("cap_percentage") for r in ie_rules} == {"10", "15"}, "Ireland cap parameter set must be 10 and 15")
for row in ie_rules:
    require(row.get("cap_type") == "PERCENT_OF_FINAL_GLOBAL_BUDGET_FIXED_POINT", "Ireland rule must identify changing denominator")
    require("AUTHORITY_SILENT" in row.get("reinvestment_treatment", ""), "Ireland cap permission incorrectly treated as reinvestment permission")
    require("SEPARATE" in row.get("paid_then_reinvested_treatment", ""), "Ireland payment/equity flows are not separated")

matrix = load_csv("CODEX_GROSS_UP_FOUR_PROJECT_FORENSIC_MATRIX.csv")
projects = {row.get("project_name") for row in matrix}
require(projects == {"The Little Utopia", "F#K Valentine's Day", "Bad Hombres", "Lips Like Sugar"}, "four-project corpus changed")
require(len(matrix) == 4 * len(rules), f"matrix must be 4 x {len(rules)} rows, got {len(matrix)}")
for row in matrix:
    pid = f"{row.get('project_name')}/{row.get('program_id')}/{row.get('eligible_category')}"
    require(row.get("recognized_incremental_qpe_usd") == "UNKNOWN_NOT_ZERO", f"{pid}: unresolved QPE silently converted to zero or positive")
    require(row.get("permanent_incentive_benefit_usd") == "UNKNOWN_NOT_AUTHORIZED", f"{pid}: theoretical headroom mislabeled as permanent benefit")
    require(row.get("ultimate_npc_effect_usd") == "UNKNOWN_NOT_AUTHORIZED", f"{pid}: unproven NPC benefit")
    require("Headroom is not QPE" in row.get("double_count_control", ""), f"{pid}: missing headroom/QPE separation")
    require("separate flows" in row.get("double_count_control", ""), f"{pid}: missing payment/financing double-count control")
    if row.get("denominator_changes_with_increment") == "YES":
        current = float(row["current_category_amount_usd"])
        final = float(row["maximum_final_category_amount_usd"])
        headroom = float(row["gross_up_headroom_usd"])
        formula = row.get("fixed_point_formula", "")
        require("/(1 -" in formula.replace(" ", "") or "/ (1 -" in formula, f"{pid}: changing-denominator row lacks fixed-point formula")
        require(math.isclose(final, current + headroom, abs_tol=0.02), f"{pid}: final category does not equal current + headroom")
        rule = next(r for r in rules if r["program_id"] == row["program_id"] and r["eligible_category"] == row["eligible_category"])
        p = float(rule["cap_percentage"]) / 100
        # Recover B algebraically from formula text to validate without silently relying on a separately copied field.
        left = formula.split("*")[1].split("-")[0].strip()
        budget = float(left)
        expected = max(0.0, (p * budget - current) / (1 - p))
        require(math.isclose(headroom, expected, abs_tol=0.02), f"{pid}: naive or incorrect changing-denominator arithmetic")
        if row.get("program_id") == "ie_section_481":
            if headroom > 0:
                require(row.get("immediate_cash_requirement_usd") not in ("", "0.00", "UNKNOWN_NOT_AUTHORIZED"), f"{pid}: paid-fee cash requirement disappeared")
            require(row.get("ultimate_repayment_or_economic_obligation_usd") == row.get("gross_up_headroom_usd"), f"{pid}: deferred/financed obligation disappeared")
            require(row.get("theoretical_incremental_incentive_usd") != row.get("permanent_incentive_benefit_usd"), f"{pid}: theoretical incentive mislabeled as permanent NPC benefit")

questions = load_csv("CODEX_CAP_HEADROOM_AGENCY_RULING_QUESTIONS.csv")
for cid in coverage_ids:
    require(any(q.get("program_id") == cid and q.get("question_id", "").startswith("FORENSIC-Q-") for q in questions), f"{cid}: no exact forensic unresolved/ruling ledger row")

closeout = (HERE / "CODEX_GROSS_UP_FORENSIC_RESEARCH_CLOSEOUT.md").read_text(encoding="utf-8")
require("658 / 658" in closeout, "closeout does not state complete 658 crosswalk")
require("Recognized incremental QPE is not established" in closeout, "closeout obscures recognized QPE status")
require("Permanent NPC benefit is `UNKNOWN_NOT_AUTHORIZED`" in closeout, "closeout obscures permanent NPC benefit status")
require("paid-then-reinvested" in closeout.lower(), "closeout omits paid/reinvested ruling gap")

precedence = json.loads((HERE / "CANONICAL_ARTIFACT_PRECEDENCE_CLAUDE.json").read_text(encoding="utf-8"))
entry = precedence.get("current_gross_up_forensic_research", {})
require(entry.get("runtime_effect", "").startswith("NONE"), "artifact precedence improperly grants runtime effect")

# This workstream may modify validation artifacts only.
changed = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
for line in changed:
    path = line[3:]
    require(path.startswith("docs/validation/"), f"non-validation file changed: {path}")

if errors:
    print("GROSS_UP_FORENSIC_RESEARCH_VALIDATION_FAILED")
    for item in errors:
        print(f"- {item}")
    raise SystemExit(1)

print("GROSS_UP_FORENSIC_RESEARCH_VALIDATION_PASS")
print(json.dumps({
    "unique_program_identities": len(crosswalk),
    "settled_authority_matches": sum(bool(r.get("settled_authority_match")) for r in crosswalk),
    "documented_unambiguous_authority_gaps": sum(not bool(r.get("settled_authority_match")) for r in crosswalk),
    "archetypes": len(archetypes),
    "practice_evidence_rows": len(practice),
    "four_project_rows": len(matrix),
    "authority_rule_rows": len(rules),
    "unresolved_question_rows": len(questions),
}, indent=2))
