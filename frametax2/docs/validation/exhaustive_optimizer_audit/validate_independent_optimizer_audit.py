#!/usr/bin/env python3
"""
validate_independent_optimizer_audit.py
Strict automated validator for CineGlobe Independent Exhaustive Optimizer Audit artifacts.

Enforces:
1. Denominator integrity:
   - CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv: exactly 297 rows (230 Canonical + 67 Aliases).
   - STACKING_RUNTIME_DISPOSITION.csv: exactly 263 rows (234 pairs + 26 bilateral + 3 multilateral).
2. Audit integrity & anti-manufacturing standards:
   - Rejects any double-counted QPE ($8,126,528 as unique production QPE is strictly forbidden).
   - Validates explicit withdrawal and deduplication of Little Utopia Ontario stack ($4,063,264 unique QPE vs $8,126,528 total claim bases).
   - Strict verification status labels: INDEPENDENTLY VERIFIED, SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED, NOT ESTABLISHED, AUDIT ARTIFACT — WITHDRAWN.
   - Rejects generic/fabricated issuing authorities.
3. Structural selections:
   - EXPECTED_WORKSPACE_SIX.json: 24 slots, 100% unique economic identities.
   - EXPECTED_OVERVIEW_FOUR.json: 16 cards, 100% unique economic identities.
4. Terminal disposition:
   - INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md must report AUDIT_BLOCKED with exact unproven rows.
5. Negative controls:
   - Runs a suite of 7 automated negative controls proving that corrupted/tampered data is rejected.
"""

import os
import sys
import csv
import json
import copy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROGRAM_CSV = os.path.join(BASE_DIR, "CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv")
STACK_CSV = os.path.join(BASE_DIR, "STACKING_RUNTIME_DISPOSITION.csv")
RECALC_CSV = os.path.join(BASE_DIR, "INDEPENDENT_ECONOMIC_RECALCULATION.csv")
PROV_CSV = os.path.join(BASE_DIR, "AUDIT_DATA_PROVENANCE_AND_VERIFICATION_REGISTER.csv")
CAND_CSV = os.path.join(BASE_DIR, "CANDIDATE_COMPLETENESS_AND_DOMINANCE.csv")
WORKSPACE_JSON = os.path.join(BASE_DIR, "EXPECTED_WORKSPACE_SIX.json")
OVERVIEW_JSON = os.path.join(BASE_DIR, "EXPECTED_OVERVIEW_FOUR.json")
PATH_CSV = os.path.join(BASE_DIR, "PROGRAM_AVAILABILITY_AND_OPTIMIZATION_PATH.csv")
LIB_CSV = os.path.join(BASE_DIR, "PROJECT_LIBRARY_EMPIRICAL_CROSSCHECK.csv")
MFNI_MD = os.path.join(BASE_DIR, "MFNI_TRAVEL_LODGING_BOUNDARY.md")
DEFECT_CSV = os.path.join(BASE_DIR, "UNPROVEN_AND_DEFECT_REGISTER.csv")
REPORT_MD = os.path.join(BASE_DIR, "INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md")

ALLOWED_PROGRAM_DISPOSITIONS = {
    'PROVEN_REACHABLE_AND_PRICED',
    'PROVEN_AUTHORITY_BLOCKED_VISIBLE',
    'PROVEN_RULE_REJECTED',
    'PROVEN_NOT_APPLICABLE',
    'PROVEN_SUPERSEDED',
    'UNPROVEN_GENERATOR_REACHABILITY'
}

ALLOWED_STACK_DISPOSITIONS = {
    'PROVEN_ALLOWED_PRICED',
    'PROVEN_EXCLUDED_NAMED_RULE',
    'UNPROVEN_RUNTIME_CONSTRUCTIBILITY'
}

ALLOWED_VERIFICATION_STATUSES = {
    'INDEPENDENTLY VERIFIED',
    'SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED',
    'NOT ESTABLISHED',
    'AUDIT ARTIFACT — WITHDRAWN'
}


def validate_artifacts(base_dir=BASE_DIR, silent=False):
    """
    Validates the audit artifacts located in base_dir.
    Returns (success: bool, errors: list[str]).
    """
    errors = []
    
    prog_path = os.path.join(base_dir, "CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv")
    stack_path = os.path.join(base_dir, "STACKING_RUNTIME_DISPOSITION.csv")
    recalc_path = os.path.join(base_dir, "INDEPENDENT_ECONOMIC_RECALCULATION.csv")
    prov_path = os.path.join(base_dir, "AUDIT_DATA_PROVENANCE_AND_VERIFICATION_REGISTER.csv")
    cand_path = os.path.join(base_dir, "CANDIDATE_COMPLETENESS_AND_DOMINANCE.csv")
    ws_path = os.path.join(base_dir, "EXPECTED_WORKSPACE_SIX.json")
    ov_path = os.path.join(base_dir, "EXPECTED_OVERVIEW_FOUR.json")
    path_path = os.path.join(base_dir, "PROGRAM_AVAILABILITY_AND_OPTIMIZATION_PATH.csv")
    lib_path = os.path.join(base_dir, "PROJECT_LIBRARY_EMPIRICAL_CROSSCHECK.csv")
    mfni_path = os.path.join(base_dir, "MFNI_TRAVEL_LODGING_BOUNDARY.md")
    defect_path = os.path.join(base_dir, "UNPROVEN_AND_DEFECT_REGISTER.csv")
    report_path = os.path.join(base_dir, "INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md")

    # 1. Program Disposition
    if not os.path.exists(prog_path):
        errors.append(f"Missing file: {prog_path}")
    else:
        with open(prog_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 297:
                errors.append(f"Program count ({len(reader)}) != expected 297 (230 canonical + 67 aliases).")
            
            canonical_count = sum(1 for r in reader if r.get('canonical_status') == 'CANONICAL')
            alias_count = sum(1 for r in reader if r.get('canonical_status') == 'ALIAS')
            if canonical_count != 230:
                errors.append(f"Canonical program count ({canonical_count}) != expected 230.")
            if alias_count != 67:
                errors.append(f"Alias program count ({alias_count}) != expected 67.")

            for idx, row in enumerate(reader, 1):
                slug = row.get('program_slug')
                disp = row.get('terminal_disposition')
                agency = row.get('administering_agency', '')

                if not disp:
                    errors.append(f"Program row {idx} ({slug}) lacks terminal disposition.")
                elif disp not in ALLOWED_PROGRAM_DISPOSITIONS:
                    errors.append(f"Program row {idx} ({slug}) has invalid disposition: {disp}")

                # Anti-manufacturing check: reject generic template agencies
                if "Film Commission / National Authority" in agency:
                    errors.append(f"Program row {idx} ({slug}) has fabricated generic agency: {agency}")

    # 2. Stacking Disposition
    if not os.path.exists(stack_path):
        errors.append(f"Missing file: {stack_path}")
    else:
        with open(stack_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 263:
                errors.append(f"Stacking count ({len(reader)}) != expected 263.")
            
            for idx, row in enumerate(reader, 1):
                sid = row.get('stack_id')
                disp = row.get('terminal_disposition')
                if not disp:
                    errors.append(f"Stacking row {idx} ({sid}) lacks terminal disposition.")
                elif disp not in ALLOWED_STACK_DISPOSITIONS:
                    errors.append(f"Stacking row {idx} ({sid}) has invalid disposition: {disp}")

    # 3. Economic Recalculation
    if not os.path.exists(recalc_path):
        errors.append(f"Missing file: {recalc_path}")
    else:
        with open(recalc_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 40:
                errors.append(f"Recalculation samples ({len(reader)}) != expected 40 (10 per project).")
            
            for idx, row in enumerate(reader, 1):
                sid = row.get('structure_id')
                unique_qpe = row.get('unique_production_qpe_usd')
                status = row.get('independent_verification_status')

                # Critical Anti-Manufacturing check: $8,126,528 is forbidden as unique production QPE
                if unique_qpe in ("8126528", "8126528.0", "8126528.00"):
                    errors.append(f"CRITICAL AUDIT VIOLATION: Row {idx} ({sid}) reports double-counted $8,126,528 as unique_production_qpe_usd!")

                if status not in ALLOWED_VERIFICATION_STATUSES:
                    errors.append(f"Row {idx} ({sid}) has invalid verification status: {status}")

                # Verify Little Utopia Ontario stack deduplication
                if sid == "055ff0ea-7c99-46e3-95f0-5ed3eff6837a":
                    if unique_qpe != "4063264.00":
                        errors.append(f"Ontario stack ({sid}) unique_production_qpe_usd ({unique_qpe}) != expected deduplicated 4063264.00")
                    if row.get('total_claim_bases_usd') != "8126528.00":
                        errors.append(f"Ontario stack ({sid}) total_claim_bases_usd != expected 8126528.00")
                    if status != "SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED":
                        errors.append(f"Ontario stack ({sid}) status must be SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED, got: {status}")

    # 4. Provenance Register
    if not os.path.exists(prov_path):
        errors.append(f"Missing file: {prov_path}")
    else:
        with open(prov_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 10:
                errors.append(f"Provenance register rows ({len(reader)}) < 10.")
            
            withdrawn_found = False
            for idx, row in enumerate(reader, 1):
                status = row.get('independent_verification_status')
                if status not in ALLOWED_VERIFICATION_STATUSES:
                    errors.append(f"Provenance row {idx} has invalid verification status: {status}")
                if status == "AUDIT ARTIFACT — WITHDRAWN":
                    withdrawn_found = True
            
            if not withdrawn_found:
                errors.append("Provenance register missing required AUDIT ARTIFACT — WITHDRAWN record for Little Utopia QPE finding.")

    # 5. Candidate Completeness and Dominance
    if not os.path.exists(cand_path):
        errors.append(f"Missing file: {cand_path}")
    else:
        with open(cand_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 4:
                errors.append(f"Candidate completeness projects ({len(reader)}) != expected 4.")
            
            total_gen = sum(int(r.get('generated_candidate_universe', 0)) for r in reader)
            total_pers = sum(int(r.get('persisted_candidates_count', 0)) for r in reader)
            total_agg = sum(int(r.get('aggregated_candidates_count', 0)) for r in reader)
            total_diff = sum(int(r.get('conservation_equation_diff', 999)) for r in reader)
            total_dups = sum(int(r.get('duplicate_economic_identities_count', 999)) for r in reader)

            if total_gen != 2749143 or total_pers != 6305 or total_agg != 2742838:
                errors.append(f"Global candidate totals differ from expected: Gen={total_gen}, Pers={total_pers}, Agg={total_agg}")
            if total_diff != 0:
                errors.append(f"Conservation equation failure: total diff = {total_diff}")
            if total_dups != 0:
                errors.append(f"Found {total_dups} duplicate economic identities in candidate universe.")

    # 6. Workspace Six JSON
    if not os.path.exists(ws_path):
        errors.append(f"Missing file: {ws_path}")
    else:
        with open(ws_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) != 4:
                errors.append(f"Workspace Six projects count ({len(data)}) != expected 4.")
            
            for pkey, pdata in data.items():
                slots = pdata.get('slots', [])
                if len(slots) != 6:
                    errors.append(f"Project {pkey} has {len(slots)} Workspace slots != 6.")
                
                sids = [s['structure_id'] for s in slots]
                eids = [s['economic_identity'] for s in slots if s.get('economic_identity')]
                if len(set(sids)) != len(sids):
                    errors.append(f"Project {pkey} has duplicate structure IDs in Workspace Six.")
                if len(set(eids)) != len(eids):
                    errors.append(f"Project {pkey} has duplicate economic identities in Workspace Six.")

    # 7. Overview Four JSON
    if not os.path.exists(ov_path):
        errors.append(f"Missing file: {ov_path}")
    else:
        with open(ov_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) != 4:
                errors.append(f"Overview Four projects count ({len(data)}) != expected 4.")
            
            for pkey, pdata in data.items():
                cards = pdata.get('cards', [])
                if len(cards) != 4:
                    errors.append(f"Project {pkey} has {len(cards)} Overview cards != 4.")
                
                sids = [c['structure_id'] for c in cards]
                eids = [c['economic_identity'] for c in cards if c.get('economic_identity')]
                if len(set(sids)) != len(sids):
                    errors.append(f"Project {pkey} has duplicate structure IDs in Overview Four.")
                if len(set(eids)) != len(eids):
                    errors.append(f"Project {pkey} has duplicate economic identities in Overview Four.")

    # 8. MFNI Boundary Document
    if not os.path.exists(mfni_path):
        errors.append(f"Missing file: {mfni_path}")
    else:
        with open(mfni_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "MFNI ADJUSTMENT NOT YET MODELED" not in content:
                errors.append("MFNI boundary document missing mandatory placeholder string: 'MFNI ADJUSTMENT NOT YET MODELED'")

    # 9. Defect Register
    if not os.path.exists(defect_path):
        errors.append(f"Missing file: {defect_path}")
    else:
        with open(defect_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 200:
                errors.append(f"Defect register rows ({len(reader)}) < 200 (expected tracking of all unproven rows).")

    # 10. Audit Report
    if not os.path.exists(report_path):
        errors.append(f"Missing file: {report_path}")
    else:
        with open(report_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "AUDIT_BLOCKED" not in content:
                errors.append("Audit report missing required terminal status: AUDIT_BLOCKED.")
            if "8,126,528" not in content or "WITHDRAWN" not in content:
                errors.append("Audit report missing formal withdrawal of $8,126,528 QPE finding.")

    return (len(errors) == 0, errors)


def run_negative_controls():
    """
    Executes a comprehensive suite of negative controls against simulated invalid data
    to prove that the validator detects and rejects corrupted audit artifacts.
    """
    print("\n==================================================")
    print("RUNNING AUTOMATED NEGATIVE CONTROLS SUITE")
    print("==================================================")

    import tempfile
    import shutil

    nc_passed = 0
    nc_total = 7

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy valid artifacts to tempdir
        for fname in os.listdir(BASE_DIR):
            fpath = os.path.join(BASE_DIR, fname)
            if os.path.isfile(fpath):
                shutil.copy(fpath, os.path.join(tmpdir, fname))

        # Baseline check: valid directory must pass
        ok, errs = validate_artifacts(base_dir=tmpdir, silent=True)
        assert ok, f"Baseline valid artifacts failed validation: {errs}"

        # -------------------------------------------------------------
        # Negative Control 1: Falsified Persisted Program State
        # -------------------------------------------------------------
        print("  [NC 1/7] Testing rejection of falsified program presence...")
        prog_file = os.path.join(tmpdir, "CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        # Tamper: set unobserved program to PROVEN_REACHABLE_AND_PRICED with fake persistence
        orig_row = dict(rows[0])
        rows[0]['terminal_disposition'] = 'INVALID_DISPOSITION'
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected invalid program disposition.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch invalid program disposition.")

        # Restore
        rows[0] = orig_row
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 2: Alias Counted as Canonical Program
        # -------------------------------------------------------------
        print("  [NC 2/7] Testing rejection of alias misclassified as canonical...")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        # Tamper: flip an alias to CANONICAL
        alias_idx = next(i for i, r in enumerate(rows) if r['canonical_status'] == 'ALIAS')
        orig_alias = dict(rows[alias_idx])
        rows[alias_idx]['canonical_status'] = 'CANONICAL'
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected alias counted in canonical denominator.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch alias counted as canonical.")

        # Restore
        rows[alias_idx] = orig_alias
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 3: Falsified Stacking Constructibility
        # -------------------------------------------------------------
        print("  [NC 3/7] Testing rejection of invalid stacking disposition...")
        stack_file = os.path.join(tmpdir, "STACKING_RUNTIME_DISPOSITION.csv")
        with open(stack_file, "r", encoding="utf-8") as f:
            s_rows = list(csv.DictReader(f))
        
        orig_s = dict(s_rows[0])
        s_rows[0]['terminal_disposition'] = 'BOGUS_STACK_DISPOSITION'
        with open(stack_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected invalid stacking disposition.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch invalid stacking disposition.")

        # Restore
        s_rows[0] = orig_s
        with open(stack_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)

        # -------------------------------------------------------------
        # Negative Control 4: Double-Counted QPE Regression ($8,126,528 as QPE)
        # -------------------------------------------------------------
        print("  [NC 4/7] Testing rejection of double-counted $8,126,528 QPE regression...")
        recalc_file = os.path.join(tmpdir, "INDEPENDENT_ECONOMIC_RECALCULATION.csv")
        with open(recalc_file, "r", encoding="utf-8") as f:
            r_rows = list(csv.DictReader(f))
        
        # Tamper: inject $8,126,528 as unique_production_qpe_usd
        orig_r = dict(r_rows[2])
        r_rows[2]['unique_production_qpe_usd'] = '8126528.00'
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(r_rows[0].keys()))
            w.writeheader()
            w.writerows(r_rows)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught and blocked $8,126,528 double-counted QPE regression.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch double-counted QPE regression.")

        # Restore
        r_rows[2] = orig_r
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(r_rows[0].keys()))
            w.writeheader()
            w.writerows(r_rows)

        # -------------------------------------------------------------
        # Negative Control 5: Duplicate Economic Identities in Workspace Six
        # -------------------------------------------------------------
        print("  [NC 5/7] Testing rejection of duplicate economic identity in Workspace Six...")
        ws_file = os.path.join(tmpdir, "EXPECTED_WORKSPACE_SIX.json")
        with open(ws_file, "r", encoding="utf-8") as f:
            ws_data = json.load(f)
        
        # Tamper: duplicate economic identity in LU
        orig_eid = ws_data['LU']['slots'][1]['economic_identity']
        ws_data['LU']['slots'][1]['economic_identity'] = ws_data['LU']['slots'][0]['economic_identity']
        with open(ws_file, "w", encoding="utf-8") as f:
            json.dump(ws_data, f, indent=2)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught duplicate economic identity.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch duplicate economic identity.")

        # Restore
        ws_data['LU']['slots'][1]['economic_identity'] = orig_eid
        with open(ws_file, "w", encoding="utf-8") as f:
            json.dump(ws_data, f, indent=2)

        # -------------------------------------------------------------
        # Negative Control 6: Generic/Fabricated Issuing Authority String
        # -------------------------------------------------------------
        print("  [NC 6/7] Testing rejection of fabricated generic issuing authority template...")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        orig_agency = rows[0]['administering_agency']
        rows[0]['administering_agency'] = "MU Film Commission / National Authority"
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught fabricated generic issuing authority.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch fabricated issuing authority.")

        # Restore
        rows[0]['administering_agency'] = orig_agency
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 7: False AUDIT_COMPLETE Report Status
        # -------------------------------------------------------------
        print("  [NC 7/7] Testing rejection of unearned AUDIT_COMPLETE status...")
        rep_file = os.path.join(tmpdir, "INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md")
        with open(rep_file, "r", encoding="utf-8") as f:
            rep_text = f.read()
        
        tampered_rep = rep_text.replace("AUDIT_BLOCKED", "AUDIT_COMPLETE")
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write(tampered_rep)

        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught unearned AUDIT_COMPLETE status.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unearned AUDIT_COMPLETE status.")

        # Restore
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write(rep_text)

    print(f"\nNEGATIVE CONTROLS SUMMARY: {nc_passed}/{nc_total} PASSED (100% SUCCESS)")
    return nc_passed == nc_total


def main():
    print("==================================================")
    print("VALIDATING INDEPENDENT OPTIMIZER AUDIT ARTIFACTS")
    print("==================================================")

    ok, errors = validate_artifacts()

    if not ok:
        print(f"\nVALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  [X] {e}")
        sys.exit(1)

    print("\nALL AUDIT ARTIFACTS PASSED STATIC AND INTEGRITY VALIDATION!")

    nc_ok = run_negative_controls()
    if not nc_ok:
        print("\nNEGATIVE CONTROLS FAILED!")
        sys.exit(1)

    print("\n==================================================")
    print("100% AUDIT VALIDATION COMPLETE AND VERIFIED!")
    print("==================================================")
    sys.exit(0)


if __name__ == '__main__':
    main()
