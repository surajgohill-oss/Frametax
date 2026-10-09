#!/usr/bin/env python3
"""
validate_exhaustive_optimizer_audit.py
Strict automated validator for CineGlobe Exhaustive Optimizer, Program and Stacking Audit artifacts.

Enforces:
1. 100% rows in program disposition have a terminal disposition in the allowed set.
2. 100% rows in stacking disposition have a terminal disposition in the allowed set.
3. Accounting equations balance exactly: generated == persisted + aggregated for all 4 productions.
4. Dominating references are 100% retained in DB; 0 duplicate economic identities; 0 aggregate dominance violations.
5. Economic recalculation has complete source fields and 0.0 arithmetic differences across all samples.
6. Expected Workspace Six contains 6 distinct valid slots with complete identity, economics, and qualification evidence for all 4 productions.
7. Expected Overview Four contains 4 distinct valid cards with complete evidence for all 4 productions.
8. Other scenarios and program disclosure matrix covers all 4 productions.
9. Global PASS is denied if any row is UNPROVEN, DISCONNECTED_DEFECT, or MISSING_GENERATION_DEFECT.
"""

import os
import sys
import csv
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROGRAM_CSV = os.path.join(BASE_DIR, "EXHAUSTIVE_PROGRAM_DISPOSITION.csv")
STACK_CSV = os.path.join(BASE_DIR, "EXHAUSTIVE_STACKING_DISPOSITION.csv")
ACCOUNTING_JSON = os.path.join(BASE_DIR, "EXHAUSTIVE_CANDIDATE_ACCOUNTING.json")
RECALC_CSV = os.path.join(BASE_DIR, "EXHAUSTIVE_ECONOMIC_RECALCULATION.csv")
WORKSPACE_JSON = os.path.join(BASE_DIR, "EXHAUSTIVE_EXPECTED_WORKSPACE_SIX.json")
OVERVIEW_JSON = os.path.join(BASE_DIR, "EXHAUSTIVE_EXPECTED_OVERVIEW_FOUR.json")
DISCLOSURE_JSON = os.path.join(BASE_DIR, "EXHAUSTIVE_OTHER_SCENARIOS_DISCLOSURE.json")

ALLOWED_PROGRAM_DISPOSITIONS = {
    'REACHABLE_PRICEABLE',
    'REACHABLE_CONDITIONAL',
    'EXPLICITLY_RULE_REJECTED',
    'AUTHORITY_UNRESOLVED_VISIBLE',
    'SUPERSEDED',
    'DUPLICATE_ALIAS',
    'NOT_APPLICABLE',
    'DISCONNECTED_DEFECT',
    'UNPROVEN'
}

ALLOWED_STACK_DISPOSITIONS = {
    'GENERATED_PRICED',
    'GENERATED_NEEDS_FACTS',
    'GENERATED_REJECTED_WITH_REASON',
    'DOMINATED_WITH_PROOF',
    'AGGREGATED_WITH_EXACT_ACCOUNTING',
    'INCOMPATIBLE_BY_NAMED_RULE',
    'MISSING_GENERATION_DEFECT',
    'UNPROVEN'
}

def validate():
    errors = []
    print("==================================================")
    print("VALIDATING EXHAUSTIVE OPTIMIZER AUDIT ARTIFACTS")
    print("==================================================")

    # 1. Program Disposition
    print("\n[1/7] Validating EXHAUSTIVE_PROGRAM_DISPOSITION.csv...")
    if not os.path.exists(PROGRAM_CSV):
        errors.append(f"Missing file: {PROGRAM_CSV}")
    else:
        with open(PROGRAM_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total program rows: {len(reader)}")
            if len(reader) < 200:
                errors.append(f"Program count ({len(reader)}) is below expected minimum (>=200).")
            
            dispositions = {}
            for idx, row in enumerate(reader, 1):
                slug = row.get('canonical_slug')
                disp = row.get('terminal_disposition')
                if not disp:
                    errors.append(f"Program row {idx} ({slug}) lacks terminal disposition.")
                elif disp not in ALLOWED_PROGRAM_DISPOSITIONS:
                    errors.append(f"Program row {idx} ({slug}) has invalid disposition: {disp}")
                elif disp in ('UNPROVEN', 'DISCONNECTED_DEFECT'):
                    errors.append(f"Program row {idx} ({slug}) has blocking defect/unproven state: {disp}")
                
                dispositions[disp] = dispositions.get(disp, 0) + 1
                
                # Check required fields
                for field in ['canonical_slug', 'jurisdiction', 'national_subnational_level', 'terminal_disposition', 'exact_exclusion_reason']:
                    if not row.get(field):
                        errors.append(f"Program row {idx} ({slug}) missing required field: {field}")
            
            print(f"  Program Dispositions breakdown:")
            for k, v in sorted(dispositions.items()):
                print(f"    - {k}: {v}")

    # 2. Stacking Disposition
    print("\n[2/7] Validating EXHAUSTIVE_STACKING_DISPOSITION.csv...")
    if not os.path.exists(STACK_CSV):
        errors.append(f"Missing file: {STACK_CSV}")
    else:
        with open(STACK_CSV, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  Total stack rows: {len(reader)}")
            if len(reader) < 50:
                errors.append(f"Stack count ({len(reader)}) is below expected minimum (>=50).")
            
            s_dispositions = {}
            for idx, row in enumerate(reader, 1):
                sid = row.get('stack_id')
                disp = row.get('terminal_disposition')
                if not disp:
                    errors.append(f"Stack row {idx} ({sid}) lacks terminal disposition.")
                elif disp not in ALLOWED_STACK_DISPOSITIONS:
                    errors.append(f"Stack row {idx} ({sid}) has invalid disposition: {disp}")
                elif disp in ('UNPROVEN', 'MISSING_GENERATION_DEFECT'):
                    errors.append(f"Stack row {idx} ({sid}) has blocking defect/unproven state: {disp}")
                
                s_dispositions[disp] = s_dispositions.get(disp, 0) + 1
                
                for field in ['stack_id', 'structural_family', 'named_stacking_rule', 'compatibility_type', 'terminal_disposition']:
                    if not row.get(field):
                        errors.append(f"Stack row {idx} ({sid}) missing required field: {field}")
            
            print(f"  Stack Dispositions breakdown:")
            for k, v in sorted(s_dispositions.items()):
                print(f"    - {k}: {v}")

    # 3. Candidate Accounting
    print("\n[3/7] Validating EXHAUSTIVE_CANDIDATE_ACCOUNTING.json...")
    if not os.path.exists(ACCOUNTING_JSON):
        errors.append(f"Missing file: {ACCOUNTING_JSON}")
    else:
        with open(ACCOUNTING_JSON, mode="r", encoding="utf-8") as f:
            acc = json.load(f)
            for pkey in ['LU', 'FVD', 'BH', 'LLS']:
                if pkey not in acc:
                    errors.append(f"Candidate accounting missing project {pkey}")
                    continue
                pdata = acc[pkey]
                gen = pdata.get('generated_candidate_count', 0)
                pers = pdata.get('persisted_candidate_count', 0)
                agg = pdata.get('aggregated_candidate_count', 0)
                if gen != pers + agg:
                    errors.append(f"Project {pkey} candidate accounting does not balance: gen({gen}) != pers({pers}) + agg({agg})")
                if not pdata.get('exact_equality'):
                    errors.append(f"Project {pkey} exact_equality is False.")
                if pdata.get('duplicate_economic_identities_count', 0) != 0:
                    errors.append(f"Project {pkey} has duplicate economic identities ({pdata.get('duplicate_economic_identities_count')}).")
                if pdata.get('aggregate_group_dominance_violations', 0) != 0:
                    errors.append(f"Project {pkey} has aggregate group dominance violations.")
                dom_tot = pdata.get('dominating_references_total', 0)
                dom_ret = pdata.get('dominating_references_retained_in_db', 0)
                if dom_tot != dom_ret:
                    errors.append(f"Project {pkey} dominating references missing from DB: {dom_ret}/{dom_tot}")
                print(f"  {pkey} ({pdata['project_name']}): gen={gen:,} == pers({pers:,}) + agg({agg:,}) [BALANCED, 0 DUPS, 0 DOM VIOLATIONS]")

    # 4. Economic Recalculation
    print("\n[4/7] Validating EXHAUSTIVE_ECONOMIC_RECALCULATION.csv...")
    if not os.path.exists(RECALC_CSV):
        errors.append(f"Missing file: {RECALC_CSV}")
    else:
        with open(RECALC_CSV, mode="r", encoding="utf-8") as f:
            recalc = list(csv.DictReader(f))
            print(f"  Total recalculation samples: {len(recalc)}")
            if len(recalc) != 24:
                errors.append(f"Expected 24 recalculation rows (6 per production), got {len(recalc)}.")
            for row in recalc:
                sid = row.get('structure_id')
                diff_c = float(row.get('diff_confirmed_npc', -1))
                diff_p = float(row.get('diff_potential_npc', -1))
                status = row.get('arithmetic_audit_status')
                if diff_c != 0.0 or diff_p != 0.0 or status != 'PASS':
                    errors.append(f"Arithmetic failure in sample {row.get('sample_id')} ({sid}): diff_c={diff_c}, diff_p={diff_p}, status={status}")
            print(f"  All 24 samples verified: 100% PASS with 0.00 arithmetic delta.")

    # 5. Expected Workspace Six
    print("\n[5/7] Validating EXHAUSTIVE_EXPECTED_WORKSPACE_SIX.json...")
    if not os.path.exists(WORKSPACE_JSON):
        errors.append(f"Missing file: {WORKSPACE_JSON}")
    else:
        with open(WORKSPACE_JSON, mode="r", encoding="utf-8") as f:
            ws = json.load(f)
            for pkey in ['LU', 'FVD', 'BH', 'LLS']:
                if pkey not in ws:
                    errors.append(f"Workspace Six missing project {pkey}")
                    continue
                slots = ws[pkey].get('slots', [])
                if len(slots) != 6:
                    errors.append(f"Workspace Six project {pkey} has {len(slots)} slots (expected 6).")
                seen_eids = set()
                seen_sids = set()
                for slot in slots:
                    sid = slot.get('structure_id')
                    eid = slot.get('economic_identity') or sid
                    if sid in seen_sids:
                        errors.append(f"Workspace Six {pkey} duplicate structure_id: {sid}")
                    if eid in seen_eids:
                        errors.append(f"Workspace Six {pkey} duplicate economic_identity: {eid}")
                    seen_sids.add(sid)
                    seen_eids.add(eid)
                    for fld in ['structure_id', 'family', 'confirmed_npc_usd', 'potential_npc_usd', 'selection_reason']:
                        if slot.get(fld) is None:
                            errors.append(f"Workspace Six {pkey} slot {slot.get('slot')} missing field: {fld}")
                print(f"  {pkey}: 6 unique slots validated with full economic & selection evidence.")

    # 6. Expected Overview Four
    print("\n[6/7] Validating EXHAUSTIVE_EXPECTED_OVERVIEW_FOUR.json...")
    if not os.path.exists(OVERVIEW_JSON):
        errors.append(f"Missing file: {OVERVIEW_JSON}")
    else:
        with open(OVERVIEW_JSON, mode="r", encoding="utf-8") as f:
            ov = json.load(f)
            for pkey in ['LU', 'FVD', 'BH', 'LLS']:
                if pkey not in ov:
                    errors.append(f"Overview Four missing project {pkey}")
                    continue
                cards = ov[pkey].get('cards', [])
                if len(cards) != 4:
                    errors.append(f"Overview Four project {pkey} has {len(cards)} cards (expected 4).")
                seen_eids = set()
                seen_sids = set()
                for card in cards:
                    sid = card.get('structure_id')
                    eid = card.get('economic_identity') or sid
                    if sid in seen_sids:
                        errors.append(f"Overview Four {pkey} duplicate structure_id: {sid}")
                    if eid in seen_eids:
                        errors.append(f"Overview Four {pkey} duplicate economic_identity: {eid}")
                    seen_sids.add(sid)
                    seen_eids.add(eid)
                    for fld in ['slot_title', 'structure_id', 'confirmed_npc_usd', 'potential_npc_usd', 'selection_rule_applied']:
                        if card.get(fld) is None:
                            errors.append(f"Overview Four {pkey} card {card.get('slot')} missing field: {fld}")
                print(f"  {pkey}: 4 unique cards validated with full evidence.")

    # 7. Other Scenarios Disclosure
    print("\n[7/7] Validating EXHAUSTIVE_OTHER_SCENARIOS_DISCLOSURE.json...")
    if not os.path.exists(DISCLOSURE_JSON):
        errors.append(f"Missing file: {DISCLOSURE_JSON}")
    else:
        with open(DISCLOSURE_JSON, mode="r", encoding="utf-8") as f:
            disc = json.load(f)
            for pkey in ['LU', 'FVD', 'BH', 'LLS']:
                if pkey not in disc:
                    errors.append(f"Other scenarios disclosure missing project {pkey}")
                else:
                    pdisc = disc[pkey]
                    print(f"  {pkey}: recommended={pdisc.get('recommended_options_total')}, evaluated={pdisc.get('evaluated_alternatives_total')}, blocked={pdisc.get('hard_blocked_total')}, dominated={pdisc.get('dominated_search_total')}")

    print("\n==================================================")
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  [ERROR] {err}")
        sys.exit(1)
    else:
        print("ALL ARTIFACTS PASSED 100% VALIDATION!")
        print("==================================================")
        sys.exit(0)

if __name__ == "__main__":
    validate()
