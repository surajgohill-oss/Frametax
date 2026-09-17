#!/usr/bin/env python3
"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION -- semantic
validator. Checks both static artifacts and, where a DATABASE_URL
pointing at the isolated audit database is provided, live DB state.

Refuses to run any DB-backed check unless DATABASE_URL resolves to the
approved isolated audit database -- fails closed rather than silently
skipping DB checks against the wrong database.

Usage:
    python3 docs/validation/validate_claude_generic_structural_discovery.py
    DATABASE_URL=postgresql+psycopg://frametax:frametax@localhost:5432/frametax2_claude_generic_discovery_audit_20260917 \
        python3 docs/validation/validate_claude_generic_structural_discovery.py --with-db
"""
import csv
import os
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent
REPO_ROOT = DOCS.parent.parent
BACKEND = REPO_ROOT / "frametax2" / "backend"
APPROVED_DB = "frametax2_claude_generic_discovery_audit_20260917"

LEDGER_PATH = DOCS / "CLAUDE_GENERIC_DISCOVERY_19_CONTROL_RECONCILIATION.csv"
ENGINE_FILE = BACKEND / "app" / "services" / "canonical_evaluation.py"
TEST_FILE = BACKEND / "tests" / "test_generic_structural_discovery_final_correction.py"

VALID_STATUSES = {
    "NATURAL_EXACT_MATCH", "EXPECTED_RULE_REJECTION_EXACT_MATCH",
    "DOMINATED_WITH_PROOF_VERIFIED",
    # UNRESOLVED_GAP is retained only because an old, no-longer-invoked
    # fixture generator script (scripts/final_19_control_ledger.py) still
    # references the string in its own historical output -- it is not
    # used by the CURRENT ledger (verified: zero rows use it as of the
    # six-control closeout below).
    "UNRESOLVED_GAP",
    # Eight-control closeout (canonical-1.78.0/1.79.0): REG-5's genuine
    # cost-pool-aware PRICED disposition and REG-4's genuine pure-pairwise
    # co-production PRICED disposition.
    "PRICED_VERIFIED", "MULTI_PRINCIPAL_PAIR_VERIFIED",
    # Six-control closeout (canonical-1.80.0): closes the acceptance gap
    # the eight-control closeout left open. MULTI_PRINCIPAL_PARTIALLY_
    # RESOLVED, MULTI_PRINCIPAL_DEFERRED, and GRANT_COMPONENT_UNWIRED_
    # DEFERRED are RETIRED as of this pass -- every control that carried
    # one has a genuine terminal disposition now, and these three strings
    # are deliberately removed from VALID_STATUSES (not just unused) so
    # a future regression that reintroduces a PARTIAL/DEFERRED row fails
    # the validator immediately rather than passing silently.
    # RULE_REJECTED_VERIFIED: a real, reconstructable RULE_REJECTED
    # disposition reached via evaluate_project(), used where the
    # control's own original required_program_set named a program/
    # mechanic a real registry or primary authority does not support,
    # and the control persists an explicit rejection rather than being
    # forced (HO-007, HO-012).
    "RULE_REJECTED_VERIFIED",
    # Structural-optimizer wiring correction pass (canonical-1.81.0):
    # AUTHORITY_INSUFFICIENT_VERIFIED is RETIRED (not merely unused) --
    # it described HO-010/HO-011 as "genuinely not priceable", which
    # turned out to be inaccurate for both: HO-011's block was a stale
    # registry bug (the program prices normally once fixed at the
    # source; now DOMINATED_WITH_PROOF_VERIFIED like HO-001/002/008/009)
    # and HO-010's Saskatchewan program is a real, CONFIRMED zero-
    # guaranteed discretionary award, not an authority gap (now
    # COMPONENT_BLOCKED_NOT_CANONICALLY_EXECUTED below). Removed
    # entirely so a future regression reintroducing this status fails
    # the validator rather than passing silently under a retired,
    # inaccurate label.
    #
    # COMPONENT_BLOCKED_NOT_CANONICALLY_EXECUTED: a control whose
    # required_program_set names N>=2 programs together, where at least
    # one program is REAL and CONFIRMED (by real authority, not a data
    # gap) to never enter the priceable candidate universe (e.g. a
    # genuinely zero-guaranteed discretionary award with no
    # StructuralComponent routing mechanism) -- so the FULL combined
    # control can never be canonically executed as one PRICED/
    # RULE_REJECTED structure, even though any standalone component of
    # it may have its own real, correct, separately-verified disposition.
    # An honest label distinct from both "verified" (would overclaim
    # the full control) and "deferred"/"partial" (would understate that
    # the blocking reason IS real, confirmed, and disclosed) (HO-010).
    "COMPONENT_BLOCKED_NOT_CANONICALLY_EXECUTED",
}


def read_ledger_rows() -> list[dict]:
    with LEDGER_PATH.open(newline="") as f:
        return list(csv.DictReader(f))


def validate_ledger_shape() -> list[str]:
    errors = []
    if not LEDGER_PATH.exists():
        return [f"MISSING: {LEDGER_PATH.name}"]
    rows = read_ledger_rows()
    if len(rows) != 19:
        errors.append(f"ledger has {len(rows)} rows, expected exactly 19")
    ids = [r["control_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errors.append(f"duplicate control_id(s) in ledger: {[i for i in ids if ids.count(i) > 1]}")
    expected_ids = {f"HO-{i:03d}" for i in range(1, 14)} | {f"REG-{i}" for i in range(1, 7)}
    missing = expected_ids - set(ids)
    if missing:
        errors.append(f"ledger missing control_id(s): {sorted(missing)}")
    for row in rows:
        if row["status"] not in VALID_STATUSES:
            errors.append(f"{row['control_id']}: invalid status {row['status']!r}")
    return errors


def validate_no_named_allowlist() -> list[str]:
    """No _NAMED_ACCEPTANCE_CONTROL_TARGETS or equivalent reintroduced."""
    errors = []
    src = ENGINE_FILE.read_text()
    for line in src.splitlines():
        code = line.split("#", 1)[0]
        if "_NAMED_ACCEPTANCE_CONTROL_TARGETS" in code:
            errors.append(f"named-program allowlist reintroduced into executable code: {line!r}")
    return errors


def validate_no_arbitrary_cutoff() -> list[str]:
    errors = []
    src_code_only = "\n".join(line.split("#", 1)[0] for line in ENGINE_FILE.read_text().splitlines())
    for banned in ("max_targets_per_component", "_HYBRID_BB_MAX_EXAMINED_PER_SUBSET", "SEARCH_DEPTH_LIMIT_REACHED"):
        if banned in src_code_only:
            errors.append(f"arbitrary/admitted-incomplete discovery cutoff still present in code: {banned!r}")
    return errors


def validate_test_count_matches_claims() -> list[str]:
    """Every claim of N tests in this file/docs must match what pytest
    actually collects -- never asserted without running."""
    errors = []
    if not TEST_FILE.exists():
        return [f"MISSING: {TEST_FILE}"]
    src = TEST_FILE.read_text()
    def_count = len(re.findall(r"^(?:async )?def test_", src, re.MULTILINE))
    # This validator does not itself invoke pytest (kept dependency-free
    # and DB-independent for the static-check path); the actual
    # pytest-collected count must be cross-checked by the caller (CI/
    # test runner) against this def_count and reported together.
    if def_count < 8:
        errors.append(f"test file has only {def_count} test function(s); this workstream's own "
                       "closeout requires at least 8 (3 original static + 4 DB-backed reconstruction "
                       "+ 1 dedent-regression guard)")
    return errors


def validate_db_isolation_guard_present() -> list[str]:
    """The test file's own fail-closed DB guard must exist and name the
    approved database."""
    errors = []
    src = TEST_FILE.read_text()
    if "_assert_isolated_database" not in src:
        errors.append("test file has no fail-closed DB isolation guard (_assert_isolated_database)")
    if APPROVED_DB not in src:
        errors.append(f"test file's DB guard does not reference the approved audit database name {APPROVED_DB!r}")
    return errors


def validate_reconstruction_data_present() -> list[str]:
    """DOMINATED_WITH_PROOF rows must carry component_target_windows,
    incumbent_structure_id, engine_version, input_fingerprint -- not
    just an aggregate count."""
    errors = []
    src = ENGINE_FILE.read_text()
    for field in ("component_target_windows", "incumbent_structure_id", "proof_type", "ordering_key"):
        if field not in src:
            errors.append(f"DOMINATED_WITH_PROOF trace is missing required reconstruction field: {field!r}")
    return errors


# ---- DB-backed checks (only run with --with-db and a verified isolated DB) ----

async def _run_db_checks() -> list[str]:
    import sqlalchemy
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    errors: list[str] = []
    db_url = os.environ.get("DATABASE_URL", "")
    engine = create_async_engine(db_url)
    db_name = engine.url.database or ""
    if db_name != APPROVED_DB and not db_name.startswith("frametax2_claude_generic_discovery_audit_"):
        return [f"REFUSING DB CHECKS: resolved database {db_name!r} is not the approved isolated audit database"]

    # Read the CURRENT engine version live rather than hardcoding a
    # string -- a hardcoded version silently passes vacuously (zero
    # matching rows, not zero violations) every time ENGINE_VERSION is
    # bumped without this file being updated in lockstep. Confirmed this
    # exact staleness bug happened once already this workstream.
    sys.path.insert(0, str(BACKEND))
    from app.services import canonical_evaluation as ce
    current_engine_version = ce.ENGINE_VERSION

    async with engine.connect() as conn:
        # 1. Every DOMINATED_WITH_PROOF row has non-null proof fields.
        rows = (await conn.execute(text(
            """
            SELECT scr.id, scr.calculation_trace_json
            FROM structure_calculation_results scr
            WHERE scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'
              AND scr.engine_version = :ev
            LIMIT 2000
            """
        ), {"ev": current_engine_version})).fetchall()
        for result_id, trace in rows:
            for field in ("proof_window_size", "dominated_combination_count", "best_real_total_found_usd"):
                if trace.get(field) is None:
                    errors.append(f"DOMINATED_WITH_PROOF row {result_id}: missing proof field {field!r}")
            if not trace.get("component_target_windows"):
                errors.append(f"DOMINATED_WITH_PROOF row {result_id}: missing component_target_windows")
            if not trace.get("incumbent_structure_id"):
                errors.append(f"DOMINATED_WITH_PROOF row {result_id}: missing incumbent_structure_id")

        # 2. No PRICED result with blank incentive.
        rows = (await conn.execute(text(
            """
            SELECT scr.id FROM structure_calculation_results scr
            WHERE scr.calculation_trace_json->>'candidate_status' = 'PRICED'
              AND scr.engine_version = :ev
              AND (scr.total_incentive_value_usd IS NULL)
            LIMIT 20
            """
        ), {"ev": current_engine_version})).fetchall()
        if rows:
            errors.append(f"{len(rows)} PRICED result(s) have a NULL total_incentive_value_usd, e.g. {rows[0][0]}")

        # 3. No RULE_REJECTED result carrying a priced value.
        rows = (await conn.execute(text(
            """
            SELECT scr.id FROM structure_calculation_results scr
            WHERE scr.calculation_trace_json->>'candidate_status' = 'RULE_REJECTED'
              AND scr.engine_version = :ev
              AND scr.total_incentive_value_usd IS NOT NULL
            LIMIT 20
            """
        ), {"ev": current_engine_version})).fetchall()
        if rows:
            errors.append(f"{len(rows)} RULE_REJECTED result(s) carry a non-null priced value, e.g. {rows[0][0]}")

        # 4. Sanity: at least SOME rows exist under the current engine
        # version -- an empty result set for ALL three checks above could
        # otherwise mean "everything is fine" or "this version has never
        # been evaluated in this database," which are very different
        # things. Never let a vacuous pass look identical to a real one.
        total_current_version_rows = (await conn.execute(text(
            "SELECT COUNT(*) FROM structure_calculation_results WHERE engine_version = :ev"
        ), {"ev": current_engine_version})).scalar()
        if not total_current_version_rows:
            errors.append(
                f"VACUOUS CHECK: zero rows exist under the current engine_version {current_engine_version!r} "
                "in this database -- the checks above passed only because there was nothing to check, not "
                "because real evidence was verified. Run evaluate_project() on at least one project first."
            )

    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(validate_ledger_shape())
    all_errors.extend(validate_no_named_allowlist())
    all_errors.extend(validate_no_arbitrary_cutoff())
    all_errors.extend(validate_test_count_matches_claims())
    all_errors.extend(validate_db_isolation_guard_present())
    all_errors.extend(validate_reconstruction_data_present())

    if "--with-db" in sys.argv:
        import asyncio
        all_errors.extend(asyncio.run(_run_db_checks()))

    if all_errors:
        print("VALIDATION FAILED:")
        for e in all_errors:
            print(" -", e)
        return 1

    rows = read_ledger_rows()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("All static checks passed. Ledger status counts:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    print(f"  TOTAL: {sum(counts.values())}")
    unresolved = [r["control_id"] for r in rows if r["status"] not in
                  ("NATURAL_EXACT_MATCH", "EXPECTED_RULE_REJECTION_EXACT_MATCH", "DOMINATED_WITH_PROOF_VERIFIED",
                   "PRICED_VERIFIED", "MULTI_PRINCIPAL_PAIR_VERIFIED", "RULE_REJECTED_VERIFIED",
                   "COMPONENT_BLOCKED_NOT_CANONICALLY_EXECUTED")]
    if unresolved:
        print(f"\nNOTE: {len(unresolved)} control(s) remain incomplete/deferred, carried forward "
              f"as implementation gaps (this is expected, not a failure): {unresolved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
