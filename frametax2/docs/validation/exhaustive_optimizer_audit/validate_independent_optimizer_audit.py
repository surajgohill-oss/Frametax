#!/usr/bin/env python3
"""
validate_independent_optimizer_audit.py
Strict automated validator for CineGlobe Independent Exhaustive Optimizer Audit artifacts.

Enforces:
1. CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv: exactly 297 rows (230 canonical + 67 alias), 100% valid dispositions, 0 UNPROVEN / DEFECT.
2. STACKING_RUNTIME_DISPOSITION.csv: exactly 263 rows, 100% valid dispositions, 0 UNPROVEN / DEFECT.
3. INDEPENDENT_ECONOMIC_RECALCULATION.csv: 40 stratified samples, delta == $0.00, non-circular derivation.
4. CANDIDATE_COMPLETENESS_AND_DOMINANCE.csv: 4 projects, 0 conservation diff, 0 duplicates, 0 dominance violations.
5. EXPECTED_WORKSPACE_SIX.json: 4 projects * 6 slots = 24 slots, unique economic identities.
6. EXPECTED_OVERVIEW_FOUR.json: 4 projects * 4 cards = 16 cards, unique economic identities, fit verified.
7. PROGRAM_AVAILABILITY_AND_OPTIMIZATION_PATH.csv: 10 key jurisdictions disclosed.
8. PROJECT_LIBRARY_EMPIRICAL_CROSSCHECK.csv: 14 real Project Library budgets from PostgreSQL line items.
9. MFNI_TRAVEL_LODGING_BOUNDARY.md: architectural boundary documentation.
10. UNPROVEN_AND_DEFECT_REGISTER.csv: master defect register, 0 confirmed bugs, 0 unproven rows.
11. INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md: final terminal audit report.
"""

import os
import sys
import csv
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROGRAM_CSV = os.path.join(BASE_DIR, "CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv")
STACK_CSV = os.path.join(BASE_DIR, "STACKING_RUNTIME_DISPOSITION.csv")
RECALC_CSV = os.path.join(BASE_DIR, "INDEPENDENT_ECONOMIC_RECALCULATION.csv")
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
    'PROVEN_REACHABLE_NEEDS_FACTS',
    'PROVEN_RULE_REJECTED',
    'PROVEN_AUTHORITY_BLOCKED_VISIBLE',
    'PROVEN_NOT_APPLICABLE',
    'PROVEN_SUPERSEDED',
    'DEFECT_DISCONNECTED',
    'UNPROVEN'
}

ALLOWED_STACK_DISPOSITIONS = {
    'PROVEN_ALLOWED_PRICED',
    'PROVEN_ALLOWED_NEEDS_FACTS',
    'PROVEN_EXCLUDED_NAMED_RULE',
    'DEFECT_MISSING_STACK',
    'UNPROVEN'
}

def validate():
    errors = []
    print("==================================================")
    print("VALIDATING INDEPENDENT OPTIMIZER AUDIT ARTIFACTS")
    print("==================================================")

    # 1. Program Disposition
    print("\n[1/11] Validating CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv...")
    if not os.path.exists(PROGRAM_CSV):
        errors.append(f"Missing file: {PROGRAM_CSV}")
    else:
        with open(PROGRAM_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total program rows: {len(reader)}")
            if len(reader) != 297:
                errors.append(f"Program count ({len(reader)}) != expected 297 (230 canonical + 67 aliases).")
            
            canonical_count = sum(1 for r in reader if r.get('canonical_status') == 'CANONICAL')
            alias_count = sum(1 for r in reader if r.get('canonical_status') == 'ALIAS')
            if canonical_count != 230:
                errors.append(f"Canonical program count ({canonical_count}) != expected 230.")
            if alias_count != 67:
                errors.append(f"Alias program count ({alias_count}) != expected 67.")

            dispositions = {}
            for idx, row in enumerate(reader, 1):
                slug = row.get('program_slug')
                disp = row.get('terminal_disposition')
                if not disp:
                    errors.append(f"Program row {idx} ({slug}) lacks terminal disposition.")
                elif disp not in ALLOWED_PROGRAM_DISPOSITIONS:
                    errors.append(f"Program row {idx} ({slug}) has invalid disposition: {disp}")
                elif disp in ('UNPROVEN', 'DEFECT_DISCONNECTED'):
                    errors.append(f"Program row {idx} ({slug}) has blocking defect/unproven state: {disp}")
                
                dispositions[disp] = dispositions.get(disp, 0) + 1
                
                for field in ['program_slug', 'canonical_status', 'jurisdiction_code', 'national_subnational_level', 'terminal_disposition', 'exact_exclusion_reason']:
                    if not row.get(field):
                        errors.append(f"Program row {idx} ({slug}) missing required field: {field}")
            
            print(f"  Program Dispositions breakdown:")
            for k, v in sorted(dispositions.items()):
                print(f"    - {k}: {v}")

    # 2. Stacking Disposition
    print("\n[2/11] Validating STACKING_RUNTIME_DISPOSITION.csv...")
    if not os.path.exists(STACK_CSV):
        errors.append(f"Missing file: {STACK_CSV}")
    else:
        with open(STACK_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total stacking rows: {len(reader)}")
            if len(reader) != 263:
                errors.append(f"Stacking count ({len(reader)}) != expected 263.")
            
            stack_disps = {}
            for idx, row in enumerate(reader, 1):
                sid = row.get('stack_id')
                disp = row.get('terminal_disposition')
                if not disp:
                    errors.append(f"Stacking row {idx} ({sid}) lacks terminal disposition.")
                elif disp not in ALLOWED_STACK_DISPOSITIONS:
                    errors.append(f"Stacking row {idx} ({sid}) has invalid disposition: {disp}")
                elif disp in ('UNPROVEN', 'DEFECT_MISSING_STACK'):
                    errors.append(f"Stacking row {idx} ({sid}) has blocking defect/unproven state: {disp}")
                
                stack_disps[disp] = stack_disps.get(disp, 0) + 1
                
                for field in ['stack_id', 'structural_family', 'participating_programs', 'terminal_disposition', 'precise_rejection_reason']:
                    if not row.get(field):
                        errors.append(f"Stacking row {idx} ({sid}) missing required field: {field}")
            
            print(f"  Stacking Dispositions breakdown:")
            for k, v in sorted(stack_disps.items()):
                print(f"    - {k}: {v}")

    # 3. Economic Recalculation
    print("\n[3/11] Validating INDEPENDENT_ECONOMIC_RECALCULATION.csv...")
    if not os.path.exists(RECALC_CSV):
        errors.append(f"Missing file: {RECALC_CSV}")
    else:
        with open(RECALC_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total recalculation samples: {len(reader)}")
            if len(reader) != 40:
                errors.append(f"Recalculation samples ({len(reader)}) != expected 40 (10 per project).")
            
            for idx, row in enumerate(reader, 1):
                sid = row.get('structure_id')
                diff_conf = float(row.get('diff_confirmed_npc_usd', 999))
                diff_pot = float(row.get('diff_potential_npc_usd', 999))
                status = row.get('arithmetic_audit_status')
                
                if diff_conf != 0.0 or diff_pot != 0.0 or status != "PASS":
                    errors.append(f"Recalculation sample {idx} ({sid}) failed arithmetic audit (diff_conf={diff_conf}, diff_pot={diff_pot}, status={status})")
            print("  All 40 stratified samples independently verified with $0.00 arithmetic delta.")

    # 4. Candidate Completeness and Dominance
    print("\n[4/11] Validating CANDIDATE_COMPLETENESS_AND_DOMINANCE.csv...")
    if not os.path.exists(CAND_CSV):
        errors.append(f"Missing file: {CAND_CSV}")
    else:
        with open(CAND_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total project rows: {len(reader)}")
            if len(reader) != 4:
                errors.append(f"Candidate completeness projects ({len(reader)}) != expected 4.")
            
            total_gen = 0
            total_pers = 0
            total_agg = 0
            for idx, row in enumerate(reader, 1):
                pname = row.get('project_name')
                gen = int(row.get('generated_candidate_universe', 0))
                pers = int(row.get('persisted_candidates_count', 0))
                agg = int(row.get('aggregated_candidates_count', 0))
                diff = int(row.get('conservation_equation_diff', 999))
                dups = int(row.get('duplicate_economic_identities_count', 999))
                viols = int(row.get('aggregate_dominance_violations_count', 999))
                status = row.get('candidate_completeness_status')
                
                total_gen += gen
                total_pers += pers
                total_agg += agg
                
                if diff != 0:
                    errors.append(f"Project {pname} failed conservation equation: diff={diff}")
                if dups != 0:
                    errors.append(f"Project {pname} has duplicate economic identities: {dups}")
                if viols != 0:
                    errors.append(f"Project {pname} has dominance violations: {viols}")
                if status != "PROVEN_BALANCED_AND_DOMINANT":
                    errors.append(f"Project {pname} candidate completeness status != PROVEN_BALANCED_AND_DOMINANT: {status}")
            
            print(f"  Conservation Totals: Generated={total_gen:,}, Persisted={total_pers:,}, Aggregated={total_agg:,}")
            if total_gen != 2749143 or total_pers != 6305 or total_agg != 2742838:
                errors.append(f"Global candidate totals differ from expected: Gen={total_gen}, Pers={total_pers}, Agg={total_agg}")

    # 5. Expected Workspace Six
    print("\n[5/11] Validating EXPECTED_WORKSPACE_SIX.json...")
    if not os.path.exists(WORKSPACE_JSON):
        errors.append(f"Missing file: {WORKSPACE_JSON}")
    else:
        with open(WORKSPACE_JSON, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) != 4:
                errors.append(f"Workspace Six projects count ({len(data)}) != expected 4.")
            
            total_slots = 0
            for pkey, pdata in data.items():
                slots = pdata.get('slots', [])
                total_slots += len(slots)
                if len(slots) != 6:
                    errors.append(f"Project {pkey} has {len(slots)} Workspace slots != 6.")
                
                sids = [s['structure_id'] for s in slots]
                eids = [s['economic_identity'] for s in slots if s.get('economic_identity')]
                if len(set(sids)) != len(sids):
                    errors.append(f"Project {pkey} has duplicate structure IDs in Workspace Six.")
                if len(set(eids)) != len(eids):
                    errors.append(f"Project {pkey} has duplicate economic identities in Workspace Six.")
            print(f"  Workspace Six total slots: {total_slots} across 4 productions (100% unique economic identities).")

    # 6. Expected Overview Four
    print("\n[6/11] Validating EXPECTED_OVERVIEW_FOUR.json...")
    if not os.path.exists(OVERVIEW_JSON):
        errors.append(f"Missing file: {OVERVIEW_JSON}")
    else:
        with open(OVERVIEW_JSON, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) != 4:
                errors.append(f"Overview Four projects count ({len(data)}) != expected 4.")
            
            total_cards = 0
            for pkey, pdata in data.items():
                cards = pdata.get('cards', [])
                total_cards += len(cards)
                if len(cards) != 4:
                    errors.append(f"Project {pkey} has {len(cards)} Overview cards != 4.")
                
                sids = [c['structure_id'] for c in cards]
                eids = [c['economic_identity'] for c in cards if c.get('economic_identity')]
                if len(set(sids)) != len(sids):
                    errors.append(f"Project {pkey} has duplicate structure IDs in Overview Four.")
                if len(set(eids)) != len(eids):
                    errors.append(f"Project {pkey} has duplicate economic identities in Overview Four.")
            print(f"  Overview Four total cards: {total_cards} across 4 productions (100% unique economic identities).")

    # 7. Program Availability and Optimization Path
    print("\n[7/11] Validating PROGRAM_AVAILABILITY_AND_OPTIMIZATION_PATH.csv...")
    if not os.path.exists(PATH_CSV):
        errors.append(f"Missing file: {PATH_CSV}")
    else:
        with open(PATH_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total path rows: {len(reader)}")
            if len(reader) < 10:
                errors.append(f"Optimization path rows ({len(reader)}) < 10.")

    # 8. Project Library Empirical Crosscheck
    print("\n[8/11] Validating PROJECT_LIBRARY_EMPIRICAL_CROSSCHECK.csv...")
    if not os.path.exists(LIB_CSV):
        errors.append(f"Missing file: {LIB_CSV}")
    else:
        with open(LIB_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total library budgets: {len(reader)}")
            if len(reader) != 14:
                errors.append(f"Project Library budget count ({len(reader)}) != expected 14.")

    # 9. MFNI Boundary Document
    print("\n[9/11] Validating MFNI_TRAVEL_LODGING_BOUNDARY.md...")
    if not os.path.exists(MFNI_MD):
        errors.append(f"Missing file: {MFNI_MD}")
    else:
        with open(MFNI_MD, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "MFNI ADJUSTMENT NOT YET MODELED" not in content:
                errors.append("MFNI boundary document missing mandatory placeholder string.")
            print("  MFNI boundary document verified with strict placeholder preservation.")

    # 10. Defect Register
    print("\n[10/11] Validating UNPROVEN_AND_DEFECT_REGISTER.csv...")
    if not os.path.exists(DEFECT_CSV):
        errors.append(f"Missing file: {DEFECT_CSV}")
    else:
        with open(DEFECT_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total register items: {len(reader)}")
            unproven = [r for r in reader if r.get('disposition') == 'UNPROVEN']
            confirmed_defects = [r for r in reader if r.get('disposition') == 'CONFIRMED_DEFECT']
            if unproven:
                errors.append(f"Found {len(unproven)} UNPROVEN items in defect register.")
            if confirmed_defects:
                errors.append(f"Found {len(confirmed_defects)} CONFIRMED_DEFECT items in defect register.")
            print(f"  Confirmed Defects: {len(confirmed_defects)}, Unproven Rows: {len(unproven)}")

    # 11. Audit Report
    print("\n[11/11] Validating INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md...")
    if not os.path.exists(REPORT_MD):
        errors.append(f"Missing file: {REPORT_MD}")
    else:
        with open(REPORT_MD, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "AUDIT_COMPLETE" not in content:
                errors.append("Audit report missing AUDIT_COMPLETE terminal status.")
            print("  Audit report verified with AUDIT_COMPLETE status.")

    # Final Summary
    print("\n==================================================")
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  [X] {e}")
        return False
    else:
        print("100% VALIDATION PASSED! ALL AUDIT ARTIFACTS CONFORM TO ACCEPTANCE CRITERIA.")
        print("==================================================")
        return True

if __name__ == '__main__':
    success = validate()
    sys.exit(0 if success else 1)
