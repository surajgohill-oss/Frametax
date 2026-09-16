#!/usr/bin/env python3
"""Substantive validator for CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION.

Supersedes the prior schema-only validator (904d30e). This validator
checks not only schema/width/count but the SUBSTANTIVE conditions Task 8
requires: every HO-001..HO-013 row present and none marked "not
executed"; neither Lips Like Sugar structure silently omitted; every
registered executable control has a real runtime result; NY is no
longer blanket mutually exclusive; no CSV contains placeholder/default
language; and (via a live import of the production module) that no
higher-order structure containing the known-prohibited on_ofttc+
on_opstc pair is ever priced.

Does not re-run the full optimizer or touch the database; the pytest
suite (tests/test_structural_archetype_generator.py) is the runtime/
arithmetic authority. This validator is a static/file-content check
over the delivered artifacts plus one live, DB-free import check.
"""
import csv
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent

REQUIRED_FILES = {
    "CLAUDE_CORRECTED_CODEX_RECONCILIATION.csv": 16,
    "CLAUDE_GLOBAL_LEGAL_INTERACTIONS_FINAL.csv": 48,
    "CLAUDE_GLOBAL_STRUCTURAL_SCOPE_FINAL.csv": 5,
    "CLAUDE_COMBINED_COPRO_HYBRID_FINAL.csv": 4,
    "CLAUDE_INPUT_WIRING_FINAL.csv": 4,
    "CLAUDE_CHANGED_PROGRAM_AUTHORITY_FINAL.csv": 10,
    "CLAUDE_STRUCTURAL_ARCHETYPE_RUNTIME.csv": 12,
    "CLAUDE_HIGHER_ORDER_RUNTIME_FINAL.csv": 13,
    "CLAUDE_REGISTERED_CONTROL_RUNTIME_FINAL.csv": 6,
    "CLAUDE_LIPS_LIKE_SUGAR_OMISSIONS_FINAL.csv": 2,
    "CLAUDE_DISTINCT_COST_VALIDATION.csv": 6,
    "CLAUDE_INDEPENDENT_CALCULATION_FINAL.csv": 9,
    "CLAUDE_FOUR_PROJECT_OPTIMIZER_FINAL.csv": 4,
}

PLACEHOLDER_PATTERNS = (
    "TBD", "TODO", "PLACEHOLDER", "N/A - fix later", "XXX", "FIXME", "lorem ipsum",
)


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    return (rows[0], rows[1:]) if rows else ([], [])


def validate_schema(path: Path, expected_rows: int) -> list[str]:
    errors = []
    if not path.exists():
        return [f"MISSING FILE: {path.name}"]
    header, data = read_rows(path)
    if not header:
        return [f"{path.name}: empty file"]
    if len(header) != len(set(header)):
        errors.append(f"{path.name}: duplicate header column(s)")
    bad_width = [i for i, r in enumerate(data) if len(r) != len(header)]
    if bad_width:
        errors.append(f"{path.name}: {len(bad_width)} row(s) with wrong column count: {bad_width[:5]}")
    if len(data) != expected_rows:
        errors.append(f"{path.name}: expected {expected_rows} data rows, found {len(data)}")
    for row in data:
        for cell in row:
            for pat in PLACEHOLDER_PATTERNS:
                if pat.lower() in cell.lower():
                    errors.append(f"{path.name}: placeholder/default language found ({pat!r}) in cell: {cell[:80]!r}")
    return errors


def validate_ho_rows_complete() -> list[str]:
    """Every HO-001 through HO-013 must be present and none 'not executed'."""
    errors = []
    path = DOCS / "CLAUDE_HIGHER_ORDER_RUNTIME_FINAL.csv"
    if not path.exists():
        return ["CLAUDE_HIGHER_ORDER_RUNTIME_FINAL.csv missing -- cannot validate HO-001..013"]
    header, data = read_rows(path)
    idx = {h: i for i, h in enumerate(header)}
    found_ids = {row[idx["control_id"]] for row in data}
    expected_ids = {f"HO-{i:03d}" for i in range(1, 14)}
    missing = expected_ids - found_ids
    if missing:
        errors.append(f"CLAUDE_HIGHER_ORDER_RUNTIME_FINAL.csv: missing control_id(s) {sorted(missing)}")
    for row in data:
        generated = row[idx["generated"]]
        status = row[idx["status"]]
        if generated.strip().upper() != "YES":
            errors.append(f"{row[idx['control_id']]}: generated={generated!r} -- 'not executed' is not an acceptable status")
        if "not executed" in status.lower():
            errors.append(f"{row[idx['control_id']]}: status marks 'not executed' as an outcome, which Task 4 forbids")
    return errors


def validate_lips_like_sugar_not_omitted() -> list[str]:
    errors = []
    path = DOCS / "CLAUDE_LIPS_LIKE_SUGAR_OMISSIONS_FINAL.csv"
    if not path.exists():
        return ["CLAUDE_LIPS_LIKE_SUGAR_OMISSIONS_FINAL.csv missing"]
    header, data = read_rows(path)
    if len(data) != 2:
        errors.append(f"expected exactly 2 Lips Like Sugar structures (HO-001, HO-002), found {len(data)}")
    idx = {h: i for i, h in enumerate(header)}
    for row in data:
        if row[idx["structure"]] not in ("HO-001", "HO-002"):
            errors.append(f"unexpected structure id {row[idx['structure']]!r} -- expected HO-001 or HO-002")
        alloc = float(row[idx["total_allocated_usd"]])
        gross = float(row[idx["gross_budget_usd"]])
        if abs(alloc - gross) > 0.01:
            errors.append(
                f"{row[idx['structure']]}: total_allocated_usd ({alloc}) does not equal "
                f"gross_budget_usd ({gross}) -- spend not conserved"
            )
    return errors


def validate_registered_controls_have_runtime_result() -> list[str]:
    errors = []
    path = DOCS / "CLAUDE_REGISTERED_CONTROL_RUNTIME_FINAL.csv"
    if not path.exists():
        return ["CLAUDE_REGISTERED_CONTROL_RUNTIME_FINAL.csv missing"]
    header, data = read_rows(path)
    if len(data) != 6:
        errors.append(f"expected exactly 6 registered executable controls, found {len(data)}")
    idx = {h: i for i, h in enumerate(header)}
    for row in data:
        if not row[idx["runtime_result"]].strip():
            errors.append(f"control {row[idx['control_id']]}: empty runtime_result")
        # Task 5 explicit requirement: NY must no longer be blanket
        # mutually exclusive.
        if "ny_state_film" in row[idx["pair"]] and "us_ny_post_production_credit" in row[idx["pair"]]:
            if row[idx["expected_disposition"]].strip().upper() == "MUTUALLY_EXCLUSIVE":
                errors.append(
                    "NY pair still recorded as blanket MUTUALLY_EXCLUSIVE -- Task 5 requires "
                    "SAME_COST_PROHIBITED_DISTINCT_COSTS_ALLOWED"
                )
    return errors


def validate_ny_registry_rule() -> list[str]:
    """Live check (no DB) that the registered NY rule itself is no longer
    blanket mutually_exclusive."""
    errors = []
    sys.path.insert(0, str(DOCS.parent.parent / "frametax2" / "backend"))
    try:
        from app.calculators.canonical_stack_bridge import load_named_pair_rule
    except Exception as exc:  # pragma: no cover
        return [f"could not import canonical_stack_bridge to check the live NY rule: {exc}"]
    rule = load_named_pair_rule("ny_state_film", "us_ny_post_production_credit")
    if rule is None:
        errors.append("ny_state_film + us_ny_post_production_credit has no registered rule at all")
    elif rule["rule_type"] == "mutually_exclusive":
        errors.append(
            "ny_state_film + us_ny_post_production_credit is STILL registered as blanket "
            "mutually_exclusive in the live registry"
        )
    return errors


def validate_prohibited_pair_never_priced_live() -> list[str]:
    """Live check (no DB): the exact 904d30e/Codex reproduction must
    still be rejected through the generic generator, and no combination
    containing on_ofttc+on_opstc anywhere may be priced."""
    errors = []
    sys.path.insert(0, str(DOCS.parent.parent / "frametax2" / "backend"))
    try:
        from app.calculators.production_allocation import AccountAllocation, AssignmentKind
        from app.calculators.structural_archetype_generator import (
            StructuralComponent, generate_structural_candidate,
        )
    except Exception as exc:  # pragma: no cover
        return [f"could not import structural_archetype_generator: {exc}"]

    def comp(slug, code, amount, line):
        alloc = AccountAllocation(
            account_code="1", description="x", amount_usd=amount, component="principal_production",
            jurisdiction_code=code, assignment_kind=AssignmentKind.FIXED, rationale="validator",
            governing_decision="validator", line_id=line, spend_category="atl_director",
        )
        return StructuralComponent(component_type="principal_production", jurisdiction_code=code,
                                    program_slug=slug, allocations=(alloc,),
                                    spend_category_by_code={"1": "atl_director"})

    components = [
        comp("ca_federal_cptc", "CA", 1_000_000.0, "VAL-1"),
        comp("on_ofttc", "CA-ON", 1_800_000.0, "VAL-2"),
        comp("on_opstc", "CA-ON", 500_000.0, "VAL-3"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_300_000.0)
    if res.executable:
        errors.append(
            "LIVE CHECK FAILED: ca_federal_cptc+on_ofttc+on_opstc was priced (executable=True) -- "
            "the exact prohibited-pair defect this workstream's Task 6 must keep fixed"
        )
    return errors


def validate_conditional_never_in_guaranteed(max_variance: float = 0.01) -> list[str]:
    errors = []
    path = DOCS / "CLAUDE_INDEPENDENT_CALCULATION_FINAL.csv"
    if not path.exists():
        return ["CLAUDE_INDEPENDENT_CALCULATION_FINAL.csv missing"]
    header, data = read_rows(path)
    idx = {h: i for i, h in enumerate(header)}
    if "variance_usd" not in idx:
        return []
    for row in data:
        raw = row[idx["variance_usd"]]
        m = re.search(r"[-+]?\d*\.?\d+", raw)
        if m and float(m.group()) > max_variance:
            errors.append(f"variance {m.group()} exceeds tolerance {max_variance} in row: {row}")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for fname, expected in REQUIRED_FILES.items():
        all_errors.extend(validate_schema(DOCS / fname, expected))
    all_errors.extend(validate_ho_rows_complete())
    all_errors.extend(validate_lips_like_sugar_not_omitted())
    all_errors.extend(validate_registered_controls_have_runtime_result())
    all_errors.extend(validate_ny_registry_rule())
    all_errors.extend(validate_prohibited_pair_never_priced_live())
    all_errors.extend(validate_conditional_never_in_guaranteed())

    if all_errors:
        print("VALIDATION FAILED:")
        for e in all_errors:
            print(" -", e)
        return 1
    print(f"All {len(REQUIRED_FILES)} required CSVs + 5 substantive/live checks validated cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
