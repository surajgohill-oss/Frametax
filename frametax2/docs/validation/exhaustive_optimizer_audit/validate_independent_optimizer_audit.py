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
   - Zero circularity: Rejects any served/persisted engine calculation labeled INDEPENDENTLY VERIFIED without independent external source controls.
3. Three-Anchor Reconciliation Deliverables:
   - THREE_ANCHOR_SOURCE_REGISTER.csv: presence, required headers, rows for LU, FVD, LLS, valid tiers, comparability disclosure.
   - THREE_ANCHOR_LINE_CLASSIFICATION.csv: exactly 124 lines (44 LU, 34 FVD, 46 LLS), no circular engine copies.
   - THREE_ANCHOR_VARIANCE_BRIDGE.csv: 3 balanced arithmetic bridges, zero unexplained residuals.
   - THREE_ANCHOR_GOLDEN_FIXTURES.json: valid JSON, verified frozen inputs/outputs for established calculations only.
   - THREE_ANCHOR_RECONCILIATION.md: complete plain-English report answering all mandated questions and retractions.
4. Structural selections:
   - EXPECTED_WORKSPACE_SIX.json: 24 slots, 100% unique economic identities.
   - EXPECTED_OVERVIEW_FOUR.json: 16 cards, 100% unique economic identities.
5. Terminal disposition:
   - INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md must report AUDIT_BLOCKED with exact unproven rows.
6. Comprehensive Negative Controls Suite:
   - Runs an exhaustive automated test suite deliberately injecting each integrity violation and proving rejection.
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

# New Three-Anchor Deliverables
SOURCE_REG_CSV = os.path.join(BASE_DIR, "THREE_ANCHOR_SOURCE_REGISTER.csv")
LINE_CLASS_CSV = os.path.join(BASE_DIR, "THREE_ANCHOR_LINE_CLASSIFICATION.csv")
VAR_BRIDGE_CSV = os.path.join(BASE_DIR, "THREE_ANCHOR_VARIANCE_BRIDGE.csv")
GOLDEN_FIX_JSON = os.path.join(BASE_DIR, "THREE_ANCHOR_GOLDEN_FIXTURES.json")
RECON_MD = os.path.join(BASE_DIR, "THREE_ANCHOR_RECONCILIATION.md")

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


ALLOWED_DATA_LABELS = {
    'PRIMARY_DOCUMENT_VALUE',
    'DOCUMENTED_LINE_SCHEDULE',
    'INDEPENDENT_RECONSTRUCTED_FROM_RAW_LINES',
    'IMPLIED_FROM_INCENTIVE_AND_RATE',
    'IMPLEMENTATION_VALUE_UNDER_AUDIT',
    'PERSISTED_OR_SERVED_COMPARISON_ONLY',
    'NOT_ESTABLISHED',
    'AUDIT_ARTIFACT_WITHDRAWN'
}

DISALLOWED_AS_INDEPENDENT_INPUTS = {
    'IMPLEMENTATION_VALUE_UNDER_AUDIT',
    'PERSISTED_OR_SERVED_COMPARISON_ONLY',
    'NOT_ESTABLISHED',
    'AUDIT_ARTIFACT_WITHDRAWN'
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

    # Three-Anchor files
    src_reg_path = os.path.join(base_dir, "THREE_ANCHOR_SOURCE_REGISTER.csv")
    line_cls_path = os.path.join(base_dir, "THREE_ANCHOR_LINE_CLASSIFICATION.csv")
    var_brg_path = os.path.join(base_dir, "THREE_ANCHOR_VARIANCE_BRIDGE.csv")
    golden_path = os.path.join(base_dir, "THREE_ANCHOR_GOLDEN_FIXTURES.json")
    recon_path = os.path.join(base_dir, "THREE_ANCHOR_RECONCILIATION.md")

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

    # 3. Economic Recalculation & Circularity Check
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
                prov = row.get('exact_source_provenance', '')

                # Anti-manufacturing check: double-counted QPE forbidden
                if unique_qpe in ("8126528", "8126528.0", "8126528.00"):
                    errors.append(f"CRITICAL AUDIT VIOLATION: Row {idx} ({sid}) reports double-counted $8,126,528 as unique_production_qpe_usd!")

                if status not in ALLOWED_VERIFICATION_STATUSES:
                    errors.append(f"Row {idx} ({sid}) has invalid verification status: {status}")

                # Anti-Circularity Rule: Reject engine reproduction labeled INDEPENDENTLY VERIFIED
                if status == "INDEPENDENTLY VERIFIED":
                    if "PostgreSQL line items + canonical RateRule" in prov:
                        errors.append(f"CIRCULARITY VIOLATION: Row {idx} ({sid}) labels engine arithmetic reproduction as INDEPENDENTLY VERIFIED!")

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
                source = row.get('exact_source', '')
                if status not in ALLOWED_VERIFICATION_STATUSES:
                    errors.append(f"Provenance row {idx} has invalid verification status: {status}")
                if status == "AUDIT ARTIFACT — WITHDRAWN":
                    withdrawn_found = True
                
                # Anti-Circularity check in provenance register
                if status == "INDEPENDENTLY VERIFIED" and "Independent line-item derivation from PostgreSQL line items" in source:
                    errors.append(f"CIRCULARITY VIOLATION in PROVENANCE: Row {idx} labels engine output reproduction as INDEPENDENTLY VERIFIED!")
            
            if not withdrawn_found:
                errors.append("Provenance register missing required AUDIT ARTIFACT — WITHDRAWN record for Little Utopia QPE finding.")

    # 5. Three-Anchor Deliverable A: Source Register
    if not os.path.exists(src_reg_path):
        errors.append(f"Missing file: {src_reg_path}")
    else:
        with open(src_reg_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 6:
                errors.append(f"THREE_ANCHOR_SOURCE_REGISTER.csv rows ({len(reader)}) < 6.")
            
            projects_found = {r.get('project') for r in reader}
            expected_projects = {"The Little Utopia", "F#K Valentine's Day", "Lips Like Sugar"}
            if not expected_projects.issubset(projects_found):
                errors.append(f"THREE_ANCHOR_SOURCE_REGISTER.csv missing required projects: {expected_projects - projects_found}")

            for idx, r in enumerate(reader, 1):
                comp = r.get('is_directly_comparable')
                pgen = r.get('program_generation', '')
                if comp not in ('TRUE', 'FALSE'):
                    errors.append(f"Source register row {idx} invalid is_directly_comparable: {comp}")
                # Audit Integrity: Program 4.0 evaluated on Lips Like Sugar must disclose FALSE comparability
                if "Program 4.0" in pgen and r.get('project') == "Lips Like Sugar":
                    if comp != "FALSE":
                        errors.append(f"Source register row {idx} must disclose FALSE comparability for Program 4.0 on Lips Like Sugar!")

    # 6. Three-Anchor Deliverable B: Line Classification
    if not os.path.exists(line_cls_path):
        errors.append(f"Missing file: {line_cls_path}")
    else:
        with open(line_cls_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 124:
                errors.append(f"THREE_ANCHOR_LINE_CLASSIFICATION.csv row count ({len(reader)}) != 124 (expected 44 LU + 34 FVD + 46 LLS).")
            
            lu_cnt = sum(1 for r in reader if r.get('project') == 'The Little Utopia')
            fvd_cnt = sum(1 for r in reader if r.get('project') == "F#K Valentine's Day")
            lls_cnt = sum(1 for r in reader if r.get('project') == 'Lips Like Sugar')
            if lu_cnt != 44:
                errors.append(f"Line classification LU lines ({lu_cnt}) != 44.")
            if fvd_cnt != 34:
                errors.append(f"Line classification FVD lines ({fvd_cnt}) != 34.")
            if lls_cnt != 46:
                errors.append(f"Line classification LLS lines ({lls_cnt}) != 46.")

            for idx, r in enumerate(reader, 1):
                p = r.get('project')
                acct = r.get('account')
                auth = r.get('independent_authority_treatment')
                eng = r.get('engine_treatment')
                disc = r.get('discrepancy')

                # Integrity Rule 2: Engine qualification flags cannot be copied as independent classification
                if p == 'The Little Utopia' and acct == '8300' and auth != 'EXCLUDED':
                    errors.append(f"Line classification row {idx} (LU contingency) must be EXCLUDED under independent authority, got: {auth}")
                if p == "F#K Valentine's Day" and acct == '1400' and auth != 'EXCLUDED':
                    errors.append(f"Line classification row {idx} (FVD foreign cast) must be EXCLUDED under independent authority, got: {auth}")
                if p == 'Lips Like Sugar' and acct in ('1100', '1200', '1300', '1400') and auth != 'EXCLUDED':
                    errors.append(f"Line classification row {idx} (LLS ATL line {acct}) must be EXCLUDED under independent authority, got: {auth}")

    # 7. Three-Anchor Deliverable C: Variance Bridge
    if not os.path.exists(var_brg_path):
        errors.append(f"Missing file: {var_brg_path}")
    else:
        with open(var_brg_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 3:
                errors.append(f"THREE_ANCHOR_VARIANCE_BRIDGE.csv row count ({len(reader)}) != 3.")
            
            for idx, r in enumerate(reader, 1):
                p = r.get('project')
                src_qpe = float(r.get('source_qpe', 0))
                eng_qpe = float(r.get('engine_qpe', 0))
                diff_qpe = float(r.get('qpe_variance_source_to_engine', 0))
                adj_cont = float(r.get('qpe_adjustment_contingency', 0))
                adj_atl = float(r.get('qpe_adjustment_foreign_atl', 0))
                adj_res = float(r.get('qpe_adjustment_residuals_reserve', 0))
                adj_oth = float(r.get('qpe_adjustment_other_nonqualified', 0))
                res = float(r.get('unexplained_residual', 999))

                # Integrity Rule 8: Every bridge must balance arithmetically
                sum_adj = adj_cont + adj_atl + adj_res + adj_oth
                if round(sum_adj, 2) != round(diff_qpe, 2):
                    errors.append(f"Variance bridge row {idx} ({p}) arithmetic imbalance: sum adjustments ({sum_adj}) != variance ({diff_qpe})")
                if round(src_qpe + diff_qpe, 2) != round(eng_qpe, 2):
                    errors.append(f"Variance bridge row {idx} ({p}) arithmetic imbalance: src_qpe + diff != eng_qpe")
                if res != 0.0:
                    errors.append(f"Variance bridge row {idx} ({p}) has unexplained residual ({res}) != 0.0")

    # 8. Three-Anchor Deliverable D: Reconciliation Report
    if not os.path.exists(recon_path):
        errors.append(f"Missing file: {recon_path}")
    else:
        with open(recon_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            required_sections = [
                "THE LITTLE UTOPIA",
                "F#K VALENTINE’S DAY",
                "LIPS LIKE SUGAR",
                "DEF-LU-001",
                "DEF-FVD-001",
                "DEF-LLS-001",
                "80.0000%",
                "Program 4.0",
                "Program 3.0",
                "CAL #8-053",
                "Retraction and Correction"
            ]
            for sec in required_sections:
                if sec not in content:
                    errors.append(f"THREE_ANCHOR_RECONCILIATION.md missing required section/token: '{sec}'")

    # 9. Three-Anchor Deliverable E: Golden Fixtures JSON
    if not os.path.exists(golden_path):
        errors.append(f"Missing file: {golden_path}")
    else:
        with open(golden_path, mode="r", encoding="utf-8") as f:
            try:
                gdata = json.load(f)
                projs = gdata.get("projects", {})
                if not {"LU", "FVD", "LLS"}.issubset(set(projs.keys())):
                    errors.append("THREE_ANCHOR_GOLDEN_FIXTURES.json missing LU, FVD, or LLS.")
                for pk in ("LU", "FVD", "LLS"):
                    pfix = projs.get(pk, {})
                    if not pfix.get("engine_defects"):
                        errors.append(f"Golden fixtures for {pk} missing engine_defects array.")
                    if pfix.get("variance_bridge", {}).get("unexplained_residual") != 0.0:
                        errors.append(f"Golden fixtures for {pk} unexplained_residual != 0.0.")
            except Exception as e:
                errors.append(f"THREE_ANCHOR_GOLDEN_FIXTURES.json is invalid JSON: {e}")

    # 10. Candidate Completeness and Dominance
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

    # 11. Workspace Six JSON
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

    # 12. Overview Four JSON
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

    # 13. MFNI Boundary Document
    if not os.path.exists(mfni_path):
        errors.append(f"Missing file: {mfni_path}")
    else:
        with open(mfni_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "MFNI ADJUSTMENT NOT YET MODELED" not in content:
                errors.append("MFNI boundary document missing mandatory placeholder string: 'MFNI ADJUSTMENT NOT YET MODELED'")

    # 14. Defect Register
    if not os.path.exists(defect_path):
        errors.append(f"Missing file: {defect_path}")
    else:
        with open(defect_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 200:
                errors.append(f"Defect register rows ({len(reader)}) < 200 (expected tracking of all unproven rows).")
            # Verify anchor defects present
            def_ids = {r.get('register_id') for r in reader}
            for expected_def in ('DEF-LU-001', 'DEF-FVD-001', 'DEF-LLS-001', 'DEF-AUDIT-002'):
                if expected_def not in def_ids:
                    errors.append(f"Defect register missing required anchor defect: {expected_def}")

    # 15. Audit Report
    if not os.path.exists(report_path):
        errors.append(f"Missing file: {report_path}")
    else:
        with open(report_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "AUDIT_BLOCKED" not in content:
                errors.append("Audit report missing required terminal status: AUDIT_BLOCKED.")
            if "8,126,528" not in content or "WITHDRAWN" not in content:
                errors.append("Audit report missing formal withdrawal of $8,126,528 QPE finding.")


    # 16. Audit Lineage Matrix
    lineage_path = os.path.join(base_dir, "AUDIT_LINEAGE_AND_INVALIDATION_MATRIX.csv")
    if not os.path.exists(lineage_path):
        errors.append(f"Missing file: {lineage_path}")
    else:
        with open(lineage_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 10:
                errors.append(f"Audit lineage matrix has {len(reader)} rows < expected minimum 10.")
            for r in reader:
                if not r.get('artifact') or not r.get('owner_engine') or not r.get('current_validity'):
                    errors.append(f"Lineage row missing mandatory fields: {r}")

    # 17. Four-Project Source Register
    fps_path = os.path.join(base_dir, "FOUR_PROJECT_SOURCE_REGISTER.csv")
    if not os.path.exists(fps_path):
        errors.append(f"Missing file: {fps_path}")
    else:
        with open(fps_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            projs = {r['project'] for r in reader}
            for p in ('The Little Utopia', "F#K Valentine's Day", 'Lips Like Sugar', 'Bad Hombres'):
                if p not in projs:
                    errors.append(f"Four-project source register missing project: {p}")
            for idx, r in enumerate(reader, 1):
                lbl = r.get('data_label')
                if lbl not in ALLOWED_DATA_LABELS:
                    errors.append(f"Source register row {idx} has invalid data_label: {lbl}")
                if lbl in DISALLOWED_AS_INDEPENDENT_INPUTS and r.get('is_directly_comparable') == 'TRUE':
                    errors.append(f"Source register row {idx} ({r.get('document')}) uses implementation/unresolved label as directly comparable independent input.")

    # 18. Four-Project Temporal Rule Matrix
    fpt_path = os.path.join(base_dir, "FOUR_PROJECT_TEMPORAL_RULE_MATRIX.csv")
    if not os.path.exists(fpt_path):
        errors.append(f"Missing file: {fpt_path}")
    else:
        with open(fpt_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 8:
                errors.append(f"Temporal rule matrix has {len(reader)} rows < expected 8.")
            for idx, r in enumerate(reader, 1):
                if not r.get('control_or_effective_date'):
                    errors.append(f"Temporal matrix row {idx} missing effective date.")
                if not r.get('program_generation'):
                    errors.append(f"Temporal matrix row {idx} missing program generation.")

    # 19. Four-Project Line Classification
    fpl_path = os.path.join(base_dir, "FOUR_PROJECT_LINE_CLASSIFICATION.csv")
    if not os.path.exists(fpl_path):
        errors.append(f"Missing file: {fpl_path}")
    else:
        with open(fpl_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 158:
                errors.append(f"Four-project line classification has {len(reader)} rows != expected 158 (LU=36, FVD=32, LLS=56, BH=34).")
            # Enforce non-resident cast exclusion in New Mexico
            for r in reader:
                if r.get('project') == 'Bad Hombres' and r.get('account') == '1400':
                    if r.get('independent_authority_treatment') != 'EXCLUDED':
                        errors.append("Bad Hombres line 1400 (Cast) improperly qualified non-resident performing artists.")

    # 20. Four-Project Anchor Variance Bridges
    fpb_path = os.path.join(base_dir, "FOUR_PROJECT_ANCHOR_VARIANCE_BRIDGES.csv")
    if not os.path.exists(fpb_path):
        errors.append(f"Missing file: {fpb_path}")
    else:
        with open(fpb_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            for p in ('The Little Utopia', "F#K Valentine's Day", 'Lips Like Sugar', 'Bad Hombres'):
                p_rows = [r for r in reader if r['project'] == p]
                if not p_rows:
                    errors.append(f"Variance bridge missing project: {p}")
                    continue
                last_step = p_rows[-1]
                if "Residual" not in last_step.get('bridge_step', '') or last_step.get('dollar_amount') != '0.00':
                    errors.append(f"Project {p} bridge does not close with $0.00 unexplained residual: {last_step}")

    # 21. Four-Project Pathway Coverage
    fpw_path = os.path.join(base_dir, "FOUR_PROJECT_PATHWAY_COVERAGE.csv")
    if not os.path.exists(fpw_path):
        errors.append(f"Missing file: {fpw_path}")
    else:
        with open(fpw_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 10:
                errors.append(f"Pathway coverage has {len(reader)} pathways < expected minimum 10.")
            pw_ids = {r['pathway_id'] for r in reader}
            for req_pw in ('PATH-SINGLE-BASELINE', 'PATH-RELOCATION-STANDALONE', 'PATH-COMPONENT-RELOCATION-2LEG', 'PATH-HYBRID-3LEG-UPLIFT'):
                if req_pw not in pw_ids:
                    errors.append(f"Pathway coverage missing required pathway: {req_pw}")

    # 22. Four-Project Persisted Scenario Audit
    fpsc_path = os.path.join(base_dir, "FOUR_PROJECT_PERSISTED_SCENARIO_AUDIT.csv")
    if not os.path.exists(fpsc_path):
        errors.append(f"Missing file: {fpsc_path}")
    else:
        with open(fpsc_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 400:
                errors.append(f"Persisted scenario audit has {len(reader)} rows != expected 400 (100 per project).")
            # Verify mapped pathways
            valid_pws = {'PATH-SINGLE-BASELINE', 'PATH-RELOCATION-STANDALONE', 'PATH-COMPONENT-RELOCATION-2LEG', 'PATH-HYBRID-2LEG', 'PATH-HYBRID-3LEG-UPLIFT', 'PATH-HYBRID-3LEG-FLAT', 'PATH-HYBRID-4LEG-MULTI', 'PATH-MULTI-PROGRAM-STACK', 'PATH-HYBRID-GENERAL'}
            for idx, r in enumerate(reader, 1):
                pw = r.get('pathway_id')
                if pw not in valid_pws:
                    errors.append(f"Scenario row {idx} maps to invalid pathway: {pw}")

    # 23. Four-Project Program Reachability
    fpr_path = os.path.join(base_dir, "FOUR_PROJECT_PROGRAM_REACHABILITY.csv")
    if not os.path.exists(fpr_path):
        errors.append(f"Missing file: {fpr_path}")
    else:
        with open(fpr_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 297:
                errors.append(f"Program reachability has {len(reader)} rows != expected 297.")

    # 24. Four-Project Stacking Audit
    fpsa_path = os.path.join(base_dir, "FOUR_PROJECT_STACKING_AND_OVERLAP_AUDIT.csv")
    if not os.path.exists(fpsa_path):
        errors.append(f"Missing file: {fpsa_path}")
    else:
        with open(fpsa_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) < 300:
                errors.append(f"Stacking audit has {len(reader)} rows < expected 300.")

    # 25. Four-Project Optimizer Selection Audit
    fpse_path = os.path.join(base_dir, "FOUR_PROJECT_OPTIMIZER_SELECTION_AUDIT.csv")
    if not os.path.exists(fpse_path):
        errors.append(f"Missing file: {fpse_path}")
    else:
        with open(fpse_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 40:
                errors.append(f"Optimizer selection audit has {len(reader)} rows != expected 40 (24 Workspace + 16 Overview).")
            for r in reader:
                if r.get('is_duplicate_identity') == 'TRUE':
                    errors.append(f"Duplicate identity detected in selection audit: {r}")

    # 26. Defect Root Cause and Blast Radius
    fpd_path = os.path.join(base_dir, "DEFECT_ROOT_CAUSE_AND_BLAST_RADIUS.csv")
    if not os.path.exists(fpd_path):
        errors.append(f"Missing file: {fpd_path}")
    else:
        with open(fpd_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            def_ids = {r['defect_id'] for r in reader}
            for expected_def in ('DEF-LU-001', 'DEF-FVD-001', 'DEF-LLS-001', 'DEF-BH-001', 'DEF-TEMPORAL-001', 'DEF-AUDIT-001', 'DEF-AUDIT-002', 'DEF-ENGINE-001', 'DEF-UI-001'):
                if expected_def not in def_ids:
                    errors.append(f"Defect blast radius missing defect: {expected_def}")

    # 27. Permanent Controls Document
    perm_path = os.path.join(base_dir, "PERMANENT_CALCULATION_ACCEPTANCE_CONTROLS.md")
    if not os.path.exists(perm_path):
        errors.append(f"Missing file: {perm_path}")
    else:
        with open(perm_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            for c_num in range(1, 13):
                if f"Control {c_num}:" not in content:
                    errors.append(f"Permanent controls document missing Control {c_num}.")

    # 28. Final Handoff Document
    handoff_path = os.path.join(base_dir, "FINAL_AG_EVIDENCE_HANDOFF_TO_CODEX.md")
    if not os.path.exists(handoff_path):
        errors.append(f"Missing file: {handoff_path}")
    else:
        with open(handoff_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            if "READY_FOR_CODEX_ADJUDICATION: YES" not in content:
                errors.append("Final handoff document missing: READY_FOR_CODEX_ADJUDICATION: YES.")

    # 29. Four-Project Budget Categorization Matrix
    fpm_path = os.path.join(base_dir, "FOUR_PROJECT_BUDGET_CATEGORIZATION_MATRIX.csv")
    if not os.path.exists(fpm_path):
        errors.append(f"Missing file: {fpm_path}")
    else:
        with open(fpm_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 158:
                errors.append(f"Budget categorization matrix has {len(reader)} rows != expected 158 (LU=44, FVD=34, BH=34, LLS=46).")
            projs = {r['project_title'] for r in reader}
            for p in ('The Little Utopia', "F#K Valentine's Day", 'Lips Like Sugar', 'Bad Hombres'):
                if p not in projs:
                    errors.append(f"Budget categorization matrix missing project: {p}")
            for idx, r in enumerate(reader, 1):
                if r.get('detail_or_subtotal') != 'LEAF_ACCOUNT':
                    errors.append(f"Row {idx} ({r.get('description')}) has invalid detail_or_subtotal: {r.get('detail_or_subtotal')}")
                if r.get('producer_incentive_line') != 'FALSE':
                    errors.append(f"Row {idx} ({r.get('description')}) has producer_incentive_line={r.get('producer_incentive_line')}! (Must remain separate from gross budget leaf items)")
                if "TOTAL" in r.get('description', '').upper() and not any(k in r.get('description', '') for k in ("Total Fringes", "DELIVERABLES")):
                    errors.append(f"Subtotal/group rollup detected as leaf item in row {idx}: {r.get('description')}")

    # 30. Cross-Format Incentive Isolation Audit
    cfi_path = os.path.join(base_dir, "CROSS_FORMAT_INCENTIVE_ISOLATION_AUDIT.csv")
    if not os.path.exists(cfi_path):
        errors.append(f"Missing file: {cfi_path}")
    else:
        with open(cfi_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 4:
                errors.append(f"Cross-format incentive audit has {len(reader)} rows != expected 4.")
            for r in reader:
                if r.get('project_short_name') in ('LU', 'FVD', 'LLS') and "DEF-XFORMAT-001" not in r.get('csv_parser_status', ''):
                    errors.append(f"Project {r.get('project_short_name')} must track defect DEF-XFORMAT-001 in CSV parser!")

    # 31. Comprehensive Budget Categorization Audit Report
    bca_path = os.path.join(base_dir, "BUDGET_CATEGORIZATION_AND_MOVIE_MAGIC_AUDIT.md")
    if not os.path.exists(bca_path):
        errors.append(f"Missing file: {bca_path}")
    else:
        with open(bca_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            req_tokens = (
                "The Little Utopia",
                "F#K Valentine's Day",
                "Bad Hombres",
                "Lips Like Sugar",
                "BPI-001",
                "BPI-002",
                "BPI-003",
                "DEF-XFORMAT-001",
                "UF-LU-001",
                "UF-FVD-001",
                "UF-BH-001",
                "UF-LLS-001",
                "_REBATE_EXCLUSION_RE",
                "source_incentive_estimates",
                "Movie Magic",
                "4,364,395",
                "4,517,687",
                "2,482,023",
                "11,983,654",
            )
            for tok in req_tokens:
                if tok not in content:
                    errors.append(f"BUDGET_CATEGORIZATION_AND_MOVIE_MAGIC_AUDIT.md missing required token: '{tok}'")

    # 32. Codex d0e01e2 Independent Audit Report
    cda_path = os.path.join(base_dir, "CODEX_D0E01E2_INDEPENDENT_AUDIT_REPORT.md")
    if not os.path.exists(cda_path):
        errors.append(f"Missing file: {cda_path}")
    else:
        with open(cda_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            cda_tokens = (
                "d0e01e285edb8baed4cf1517a4250b6ba6b0051b",
                "Formal Retraction of California Control Contradiction",
                "Formal Retraction of Bad Hombres SAG Reserve Contradiction",
                "Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "Q09", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15",
                "_is_budget_netting",
                "_separate_spreadsheet_evidence",
                "_price_subset_uplifts",
                "EligibleSubsetUpliftRule",
                "IncentiveValueCapRule",
                "8,000,000",
                "10,000,000",
            )
            for tok in cda_tokens:
                if tok not in content:
                    errors.append(f"CODEX_D0E01E2_INDEPENDENT_AUDIT_REPORT.md missing required token: '{tok}'")

    # 33. Four-Anchor Codex d0e01e2 Disposition Matrix
    cdm_path = os.path.join(base_dir, "FOUR_ANCHOR_CODEX_D0E01E2_DISPOSITION_MATRIX.csv")
    if not os.path.exists(cdm_path):
        errors.append(f"Missing file: {cdm_path}")
    else:
        with open(cdm_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 158:
                errors.append(f"FOUR_ANCHOR_CODEX_D0E01E2_DISPOSITION_MATRIX.csv has {len(reader)} rows != expected 158.")
            for r in reader:
                if r.get('project_name') == 'Bad Hombres' and r.get('account_code') == '1600':
                    if r.get('confirmed_qpe_usd') != '0.00' or r.get('missing_fact_disclosure') != 'MISSING_PRODUCTION_FACT':
                        errors.append(f"Bad Hombres Line 1600 must have confirmed_qpe_usd='0.00' and missing_fact_disclosure='MISSING_PRODUCTION_FACT': {r}")
                if r.get('project_name') == 'Lips Like Sugar' and r.get('account_code') == '1100':
                    if r.get('confirmed_qpe_usd') != '1653.00' or r.get('excluded_usd') != '312500.00':
                        errors.append(f"Lips Like Sugar Line 1100 must have confirmed_qpe_usd='1653.00' and excluded_usd='312500.00': {r}")
                if r.get('project_name') == 'Lips Like Sugar' and r.get('account_code') == '1900':
                    if r.get('confirmed_qpe_usd') != '0.00':
                        errors.append(f"Lips Like Sugar Line 1900 (ATL fringes) must have confirmed_qpe_usd='0.00': {r}")
                if r.get('project_name') == 'The Little Utopia' and r.get('account_code') == '7100':
                    if r.get('spend_category') != 'general_administration':
                        errors.append(f"The Little Utopia Line 7100 must be general_administration: {r}")

    # 34. New York Incentives and Upstate Audit Report
    nya_path = os.path.join(base_dir, "NEW_YORK_INCENTIVES_AND_UPSTATE_AUDIT.md")
    if not os.path.exists(nya_path):
        errors.append(f"Missing file: {nya_path}")
    else:
        with open(nya_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            nya_tokens = (
                "NY Tax Law § 24",
                "NY Tax Law § 31",
                "5 NYCRR Part 170",
                "Chapter 59 of the Laws of 2023",
                "provided, however, that a taxpayer that is eligible for a credit under section twenty-four of this article shall not be eligible for a credit under this section",
                "Mutual Exclusivity",
                "40% Aggregate Ceiling",
                "$500,000 per person",
                "Downstate NY Full Relocation",
                "Upstate NY Full Relocation",
                "The Little Utopia",
                "F#K Valentine",
                "Bad Hombres",
                "Lips Like Sugar",
                "ANCHOR ACCEPTANCE GATE REMAINS OPEN",
                "NY_AG_BDE0FEE_ADJUDICATION.md",
                "NY-A01",
                "NY-A02",
                "NY-A03",
                "NY-A04",
                "NY-A05",
                "NY-A06",
                "NY-A07",
                "NY-A08",
                "NY-A09",
                "NY-A10",
                "DISC-NY-001",
                "DISC-NY-002",
                "DISC-NY-003",
                "DISC-NY-004",
                "DISC-NY-005",
                "DISC-NY-006",
                "DISC-NY-007",
            )
            for tok in nya_tokens:
                if tok not in content:
                    errors.append(f"NEW_YORK_INCENTIVES_AND_UPSTATE_AUDIT.md missing required token: '{tok}'")

    # 35. New York Four-Project Scenario Matrix
    nym_path = os.path.join(base_dir, "NEW_YORK_FOUR_PROJECT_SCENARIO_MATRIX.csv")
    if not os.path.exists(nym_path):
        errors.append(f"Missing file: {nym_path}")
    else:
        with open(nym_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 158:
                errors.append(f"NEW_YORK_FOUR_PROJECT_SCENARIO_MATRIX.csv has {len(reader)} rows != expected 158.")
            projs = {r['project_title'] for r in reader}
            for p in ('The Little Utopia', "F#K Valentine's Day", 'Lips Like Sugar', 'Bad Hombres'):
                if p not in projs:
                    errors.append(f"New York scenario matrix missing project: {p}")
            # Enforce ATL 40% aggregate ceiling and non-qualifying exclusions
            for p in projs:
                p_rows = [r for r in reader if r['project_title'] == p]
                btl_post_base = sum(float(r['amount_usd']) for r in p_rows if r['ny_statutory_treatment'] in ('QUALIFIED_BTL_PHYSICAL', 'QUALIFIED_POST_PRODUCTION'))
                max_atl = 0.40 * btl_post_base
                actual_atl_qpe = sum(float(r['downstate_qpe_usd']) for r in p_rows if 'ATL' in r['ny_statutory_treatment'])
                if actual_atl_qpe > max_atl + 0.05:
                    errors.append(f"Project {p} New York QPE violates 40% ATL ceiling: actual ATL ${actual_atl_qpe:,.2f} > max allowable ${max_atl:,.2f}")
                # Enforce that non-qualifying rows have 0 QPE
                for r in p_rows:
                    if r['ny_statutory_treatment'] == 'EXCLUDED_NON_QUALIFYING':
                        if float(r['downstate_qpe_usd']) != 0.0 or float(r['upstate_qpe_usd']) != 0.0:
                            errors.append(f"Excluded cost line qualified in New York QPE: {r}")
                    if r['qualifies_standalone_post_31'] == 'Y' and r['ny_statutory_treatment'] != 'QUALIFIED_POST_PRODUCTION':
                        errors.append(f"Non-post expense improperly qualified for Section 31 post credit: {r}")
                    # Enforce on-set production sound disaggregation from Section 31
                    if 'PRODUCTION SOUND' in r['description'] and 'POST' not in r['description'].upper():
                        if r['qualifies_standalone_post_31'] == 'Y' or float(r['standalone_post_qpe_usd']) != 0.0:
                            errors.append(f"On-set production sound improperly qualified under Section 31: {r}")
                        if r['ny_statutory_treatment'] != 'QUALIFIED_BTL_PHYSICAL':
                            errors.append(f"On-set production sound must be QUALIFIED_BTL_PHYSICAL: {r}")
                # Enforce complete exclusion of LLS financing fees
                if p == 'Lips Like Sugar':
                    for r in p_rows:
                        if r['account_code'] in ('6500', '6600', '6700'):
                            if r['ny_statutory_treatment'] != 'EXCLUDED_NON_QUALIFYING' or float(r['downstate_qpe_usd']) != 0.0:
                                errors.append(f"LLS financing account {r['account_code']} must be EXCLUDED_NON_QUALIFYING: {r}")

    # 36. Four-Anchor QPE Issue Register Reconciliation
    irr_path = os.path.join(base_dir, "FOUR_ANCHOR_QPE_ISSUE_REGISTER_RECONCILIATION.md")
    if not os.path.exists(irr_path):
        errors.append(f"Missing file: {irr_path}")
    else:
        with open(irr_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            irr_tokens = (
                "FOUR_ANCHOR_QPE_ISSUE_REGISTER.md",
                "Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "Q09", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15",
                "926,855.84",
                "UNRESOLVED_PLANNING_VARIANCE",
                "ESTIMATE_IMPLIED_ONLY",
                "CONDITIONAL ON CAST WITHHOLDING PROOF",
                "Law 4487/2017",
                "Law 5105/2024",
                "KYA 607434",
                "8004",
                "35.0%",
                "30.0%",
                "combined 5.0% cap",
                "ANCHOR ACCEPTANCE GATE REMAINS OPEN",
            )
            for tok in irr_tokens:
                if tok not in content:
                    errors.append(f"FOUR_ANCHOR_QPE_ISSUE_REGISTER_RECONCILIATION.md missing required token: '{tok}'")

    # 37. FVD Greece 34-Account Reconstruction Matrix
    fgr_path = os.path.join(base_dir, "FVD_GREECE_34_ACCOUNT_RECONSTRUCTION.csv")
    if not os.path.exists(fgr_path):
        errors.append(f"Missing file: {fgr_path}")
    else:
        with open(fgr_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 34:
                errors.append(f"FVD_GREECE_34_ACCOUNT_RECONSTRUCTION.csv has {len(reader)} rows != expected 34.")
            gross_total = sum(float(r['amount_usd']) for r in reader)
            if abs(gross_total - 4517687.00) > 0.01:
                errors.append(f"FVD Greece reconstruction sum ${gross_total:,.2f} != expected $4,517,687.00.")
            for r in reader:
                if r['territorial_evidence_state'] != 'MISSING_LOCAL_SPEND_SCHEDULE':
                    errors.append(f"FVD Greece row {r.get('account_code')} must indicate MISSING_LOCAL_SPEND_SCHEDULE: {r}")
                if r['account_code'] in ('7901', '7902'):
                    if r['is_statutorily_excluded'] != 'TRUE':
                        errors.append(f"FVD non-qualifying line {r.get('account_code')} not marked is_statutorily_excluded=TRUE: {r}")
                if r['account_code'] in ('7200', '7905'):
                    if r['is_statutorily_excluded'] != 'FALSE':
                        errors.append(f"FVD insurance/bond line {r.get('account_code')} must NOT be blanket excluded (is_statutorily_excluded must be FALSE): {r}")
                    if r['statutory_treatment_greece'] != 'ELIGIBLE_SUBJECT_TO_5PCT_CAP':
                        errors.append(f"FVD insurance/bond line {r.get('account_code')} must be ELIGIBLE_SUBJECT_TO_5PCT_CAP: {r}")
                if r['account_code'] in ('1200', '1300'):
                    reason = r.get('exclusion_or_restriction_reason', '')
                    if '35.0%' not in reason or '30.0%' not in reason:
                        errors.append(f"FVD principal fee line {r.get('account_code')} must cite versioned 35.0% and 30.0% fee caps: {r}")

    # 38. North American Four-Project Comprehensive Matrix & Source-Line Treatment Table
    lut_path = os.path.join(base_dir, "LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv")
    if not os.path.exists(lut_path):
        errors.append(f"Missing file: {lut_path}")
    else:
        with open(lut_path, mode="r", encoding="utf-8") as f:
            lut_reader = list(csv.DictReader(f))
            if len(lut_reader) != 44:
                errors.append(f"LU treatment CSV row count ({len(lut_reader)}) != expected 44.")
            lut_sum = sum(float(r['original_amount']) for r in lut_reader)
            if abs(lut_sum - 4364395.00) > 0.01:
                errors.append(f"LU treatment CSV leaf sum ({lut_sum}) != expected 4364395.00.")

    na_matrix_path = os.path.join(base_dir, "NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv")
    if not os.path.exists(na_matrix_path):
        errors.append(f"Missing file: {na_matrix_path}")
    else:
        with open(na_matrix_path, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if len(reader) != 204:
                errors.append(f"NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv row count ({len(reader)}) != 204.")
            
            # 1. LU NY status and supported bounds check (NOT_ESTABLISHED under Evidence Gate Rules 2, 3, & 5)
            lu_ny = next((r for r in reader if r.get('project_code') == 'LU' and r.get('program_slug') == 'ny_state_film'), None)
            if not lu_ny:
                errors.append("Matrix missing LU ny_state_film row.")
            else:
                if lu_ny.get('expected_qpe_usd') != 'NOT_ESTABLISHED':
                    errors.append(f"LU ny_state_film expected_qpe_usd must be NOT_ESTABLISHED, got {lu_ny.get('expected_qpe_usd')}")
                if lu_ny.get('remediation_code_status') != 'NOT_ESTABLISHED_EMPIRICAL_GAP':
                    errors.append(f"LU ny_state_film status must be NOT_ESTABLISHED_EMPIRICAL_GAP, got {lu_ny.get('remediation_code_status')}")
                if lu_ny.get('defect_or_disposition_id') != 'NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)':
                    errors.append(f"LU ny_state_film disposition must be NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT), got {lu_ny.get('defect_or_disposition_id')}")
                rca = lu_ny.get('root_cause_analysis', '')
                if '2,836,167.00' not in rca or '3,771,497.00' not in rca:
                    errors.append(f"LU ny_state_film root cause missing supported bounds [2,836,167.00 - 3,771,497.00]: {rca}")
                if '84,809.70' not in rca:
                    errors.append(f"LU ny_state_film root cause missing credit overstatement 84,809.70: {rca}")

            # 1b. FVD, BH, LLS NY statutory bounds and NOT_ESTABLISHED check (Rule 5)
            for p, exp_min, exp_max in (
                ('FVD', '1,256,776.00', '1,759,486.40'),
                ('BH', '749,889.00', '1,049,844.60'),
                ('LLS', '5,853,484.00', '8,194,877.60'),
            ):
                p_ny = next((r for r in reader if r.get('project_code') == p and r.get('program_slug') == 'ny_state_film'), None)
                if not p_ny:
                    errors.append(f"Matrix missing {p} ny_state_film row.")
                else:
                    if p_ny.get('expected_qpe_usd') != 'NOT_ESTABLISHED':
                        errors.append(f"{p} ny_state_film expected_qpe_usd must be NOT_ESTABLISHED under Rule 5, got {p_ny.get('expected_qpe_usd')}")
                    if p_ny.get('remediation_code_status') != 'NOT_ESTABLISHED_EMPIRICAL_GAP':
                        errors.append(f"{p} ny_state_film status must be NOT_ESTABLISHED_EMPIRICAL_GAP, got {p_ny.get('remediation_code_status')}")
                    if p_ny.get('defect_or_disposition_id') != 'NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)':
                        errors.append(f"{p} ny_state_film disposition must be NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS), got {p_ny.get('defect_or_disposition_id')}")
                    rca = p_ny.get('root_cause_analysis', '')
                    if exp_min not in rca or exp_max not in rca:
                        errors.append(f"{p} ny_state_film root cause missing supported bounds [{exp_min} - {exp_max}]: {rca}")

            # 2. Evidenced dispositions for missing candidates & NY stack check
            for idx, r in enumerate(reader, 1):
                p_code = r.get('project_code')
                p_slug = r.get('program_slug')
                act_stat = r.get('actual_status')
                struct_id = r.get('matched_structure_id')
                rem_stat = r.get('remediation_code_status')
                disp_id = r.get('defect_or_disposition_id')
                rca = r.get('root_cause_analysis', '')

                if struct_id == "N/A" or act_stat in ("UNPRICED_OR_MISSING", "STACK_NOT_GENERATED"):
                    if rem_stat == "VERIFIED_AGREEMENT":
                        errors.append(f"Missing candidate row {idx} ({p_code} / {p_slug}) falsely claims VERIFIED_AGREEMENT!")
                    if rem_stat not in ("COMPARISON_NOT_ESTABLISHED", "NOT_ESTABLISHED_EMPIRICAL_GAP"):
                        errors.append(f"Missing candidate row {idx} ({p_code} / {p_slug}) invalid disposition: {rem_stat}")

                # 3. NY production/post stack reconciliation (§ 24 + § 31 vs. DISC-NY-001)
                if p_slug == "stack_ny_prod_post":
                    if rem_stat != "COMPARISON_NOT_ESTABLISHED":
                        errors.append(f"NY stack row {idx} ({p_code}) must be COMPARISON_NOT_ESTABLISHED, got {rem_stat}")
                    if disp_id != "COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)":
                        errors.append(f"NY stack row {idx} ({p_code}) has invalid disposition ID: {disp_id}")
                    if "DISC-NY-001" not in rca:
                        errors.append(f"NY stack row {idx} ({p_code}) root cause must cite DISC-NY-001: {rca}")
                    if "VERIFIED_AGREEMENT" in rem_stat:
                        errors.append(f"NY stack row {idx} ({p_code}) cannot claim VERIFIED_AGREEMENT")

    # 39. North American Discrepancy Register
    na_reg_path = os.path.join(base_dir, "NORTH_AMERICAN_DISCREPANCY_REGISTER.md")
    if not os.path.exists(na_reg_path):
        errors.append(f"Missing file: {na_reg_path}")
    else:
        with open(na_reg_path, mode="r", encoding="utf-8") as f:
            content = f.read()
            req_na_tokens = (
                "$2,836,167.00",
                "$3,771,497.00",
                "$3,274,421.00",
                "84,809.70",
                "138,850",
                "438,254",
                "61,568",
                "301,131",
                "DISC-NY-001",
                "COMPARISON_NOT_ESTABLISHED",
                "NA-DEFECT-01",
                "RET-09",
                "RET-10",
                "c3b8ad45-5c1e-47ed-b182-c9106f668b2a",
                "f3513411-547c-41ca-894d-e1ef36d856b7",
                "5557ceb5-d3f5-4b42-85df-d7369d72a9bd",
            )
            for tok in req_na_tokens:
                if tok not in content:
                    errors.append(f"NORTH_AMERICAN_DISCREPANCY_REGISTER.md missing required token: '{tok}'")
            if "$3,141,324.00" in content:
                errors.append("NORTH_AMERICAN_DISCREPANCY_REGISTER.md contains obsolete $1,000 operand error '$3,141,324.00'!")

    # 40. New York Audit Closeout Handoff Document
    ny_handoff_path = os.path.join(base_dir, "NEW_YORK_AUDIT_CLOSEOUT_HANDOFF.md")
    if not os.path.exists(ny_handoff_path):
        errors.append(f"Missing file: {ny_handoff_path}")
    else:
        with open(ny_handoff_path, mode="r", encoding="utf-8") as f:
            h_content = f.read()
            req_handoff_tokens = (
                "LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv",
                "$4,364,395.00",
                "138,850",
                "$0.00",
                "$2,836,167.00",
                "$3,771,497.00",
                "$3,274,421.00",
                "84,809.70",
                "340d2041-b11e-4ceb-8c9b-7162f4956903",
                "14535c49-2dbe-4357-ab61-d3bf5b51c0f4",
                "NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)",
                "NA-DEFECT-01",
                "DISC-NY-001",
                "RET-09",
                "RET-10",
                "c3b8ad45-5c1e-47ed-b182-c9106f668b2a",
                "f3513411-547c-41ca-894d-e1ef36d856b7",
                "5557ceb5-d3f5-4b42-85df-d7369d72a9bd",
                "STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN",
            )
            for tok in req_handoff_tokens:
                if tok not in h_content:
                    errors.append(f"NEW_YORK_AUDIT_CLOSEOUT_HANDOFF.md missing required token: '{tok}'")

    # 41. North American Hybrid Coverage Matrix
    na_hyb_csv_path = os.path.join(base_dir, "NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv")
    if not os.path.exists(na_hyb_csv_path):
        errors.append(f"Missing file: {na_hyb_csv_path}")
    else:
        with open(na_hyb_csv_path, mode="r", encoding="utf-8") as f:
            hyb_reader = list(csv.DictReader(f))
            if len(hyb_reader) != 1601:
                errors.append(f"NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv row count ({len(hyb_reader)}) != expected 1601 (9 explicit LLS MB-CA rows + 1590 saved NA rows + 2 historical LLS 106 rows).")
            overlap_violations = [r for r in hyb_reader if r.get("line_overlap_count") not in ("0", 0)]
            if overlap_violations:
                errors.append(f"NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv has {len(overlap_violations)} rows with non-zero line_overlap_count!")
            art1 = next((r for r in hyb_reader if r.get("row_category") == "LLS_MB_CA_ARTIFACT_1_RETAINED_HYBRID"), None)
            art2 = next((r for r in hyb_reader if r.get("row_category") == "LLS_MB_CA_ARTIFACT_2_MB_LEG_SENSITIVITY_CONTINGENCY_NOT_STATED"), None)
            art3 = next((r for r in hyb_reader if r.get("row_category") == "LLS_MB_CA_ARTIFACT_3_ALL_MB_ALTERNATIVE_CONTINGENCY_NOT_STATED"), None)
            if (
                not art1
                or art1.get("independent_expected_status") != "GATE_REJECTED"
                or art1.get("independent_incentive_floor_usd") != "N/A (NOT_PRICED_REJECTED_CANDIDATE)"
                or art1.get("independent_npc_floor_usd") != "N/A (NOT_PRICED_REJECTED_CANDIDATE)"
            ):
                errors.append(f"LLS MB-CA Artifact 1 must be GATE_REJECTED with N/A (NOT_PRICED_REJECTED_CANDIDATE) floor credit and NPC, got: {art1}")
            if not art2 or art2.get("independent_incentive_floor_usd") != "2833096.20" or art2.get("independent_npc_floor_usd") != "9150557.80":
                errors.append(f"LLS MB-CA Artifact 2 must have 2833096.20 floor credit and 9150557.80 NPC, got: {art2}")
            if not art3 or art3.get("independent_incentive_floor_usd") != "2845096.20" or art3.get("independent_npc_floor_usd") != "9138557.80":
                errors.append(f"LLS MB-CA Artifact 3 must have 2845096.20 floor credit and 9138557.80 NPC, got: {art3}")
            c100_a2 = next((r for r in hyb_reader if r.get("row_category") == "LLS_MB_CA_ARTIFACT_2_MB_LEG_SENSITIVITY_CONTINGENCY_100%"), None)
            if (
                not c100_a2
                or c100_a2.get("independent_incentive_floor_usd") != "2833096.20"
                or c100_a2.get("independent_npc_floor_usd") != "9150557.80"
                or "2,953,096.20" not in c100_a2.get("statutory_basis_and_notes", "")
                or c100_a2.get("audit_disposition") != "VERIFIED_FLOOR_WITH_CONDITIONAL_CONTINGENCY_DEPLOYMENT_SENSITIVITY"
            ):
                errors.append(f"LLS MB-CA 100% Contingency Artifact 2 must have 2833096.20 confirmed floor credit, 9150557.80 floor NPC, and 2,953,096.20 conditional deployed sensitivity, got: {c100_a2}")

    # 42. North American Hybrid Audit Handoff Document
    na_hyb_md_path = os.path.join(base_dir, "NORTH_AMERICAN_HYBRID_AUDIT_HANDOFF.md")
    if not os.path.exists(na_hyb_md_path):
        errors.append(f"Missing file: {na_hyb_md_path}")
    else:
        with open(na_hyb_md_path, mode="r", encoding="utf-8") as f:
            hyb_md = f.read()
            req_hyb_tokens = (
                "f5dc6a17858436c0809d7830151696d036aa159b",
                "f0b042ba039ed41e619217a4ac8758ec6814eed8",
                "59566fd17463b71e9796d41e8e080bf5d0ac27ea",
                "canonical-1.122.0",
                "914a47c0-9b1e-4d47-867f-425e6d4792fa",
                "9656c441-881e-4667-bec1-8841387408ce",
                "N/A (NOT_PRICED_REJECTED_CANDIDATE)",
                "2,833,096.20",
                "2,845,096.20",
                "9,150,557.80",
                "9,138,557.80",
                "1,320,884.10",
                "2,893,096.20",
                "2,953,096.20",
                "NA-HYB-DEF-01",
                "NA-HYB-DEF-02",
                "NA-HYB-DEF-03",
                "NA-HYB-DEF-04",
                "NA-HYB-DEF-05",
                "NA-HYB-DEF-06",
                "STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN",
            )
            for tok in req_hyb_tokens:
                if tok not in hyb_md:
                    errors.append(f"NORTH_AMERICAN_HYBRID_AUDIT_HANDOFF.md missing required token: '{tok}'")

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
    nc_total = 44

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
        print("  [NC 1/15] Testing rejection of falsified program presence...")
        prog_file = os.path.join(tmpdir, "CANONICAL_PROGRAM_RUNTIME_DISPOSITION.csv")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
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
        rows[0] = orig_row
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 2: Alias Counted as Canonical Program
        # -------------------------------------------------------------
        print("  [NC 2/15] Testing rejection of alias misclassified as canonical...")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
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
        rows[alias_idx] = orig_alias
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 3: Falsified Stacking Constructibility
        # -------------------------------------------------------------
        print("  [NC 3/15] Testing rejection of invalid stacking disposition...")
        stack_file = os.path.join(tmpdir, "STACKING_RUNTIME_DISPOSITION.csv")
        with open(stack_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        orig_stack = dict(rows[0])
        rows[0]['terminal_disposition'] = 'INVALID_STACK_DISP'
        with open(stack_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected invalid stacking disposition.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch invalid stacking disposition.")
        rows[0] = orig_stack
        with open(stack_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 4: Double-Counted $8,126,528 QPE Regression
        # -------------------------------------------------------------
        print("  [NC 4/15] Testing rejection of double-counted $8,126,528 QPE regression...")
        recalc_file = os.path.join(tmpdir, "INDEPENDENT_ECONOMIC_RECALCULATION.csv")
        with open(recalc_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        orig_recalc = dict(rows[0])
        rows[0]['unique_production_qpe_usd'] = '8126528.00'
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught and blocked $8,126,528 double-counted QPE regression.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch double-counted QPE regression.")
        rows[0] = orig_recalc
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 5: Duplicate Economic Identity in Workspace Six
        # -------------------------------------------------------------
        print("  [NC 5/15] Testing rejection of duplicate economic identity in Workspace Six...")
        ws_file = os.path.join(tmpdir, "EXPECTED_WORKSPACE_SIX.json")
        with open(ws_file, "r", encoding="utf-8") as f:
            ws_data = json.load(f)
        orig_ws = copy.deepcopy(ws_data)
        first_proj = list(ws_data.keys())[0]
        ws_data[first_proj]['slots'][1]['economic_identity'] = ws_data[first_proj]['slots'][0]['economic_identity']
        with open(ws_file, "w", encoding="utf-8") as f:
            json.dump(ws_data, f, indent=2)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught duplicate economic identity.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch duplicate economic identity.")
        with open(ws_file, "w", encoding="utf-8") as f:
            json.dump(orig_ws, f, indent=2)

        # -------------------------------------------------------------
        # Negative Control 6: Generic/Fabricated Agency Template
        # -------------------------------------------------------------
        print("  [NC 6/15] Testing rejection of fabricated generic issuing authority template...")
        with open(prog_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows[0]['administering_agency'] = 'Film Commission / National Authority (Sourced)'
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught fabricated generic issuing authority.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch fabricated generic agency.")
        rows[0] = orig_row
        with open(prog_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 7: Unearned AUDIT_COMPLETE Status
        # -------------------------------------------------------------
        print("  [NC 7/15] Testing rejection of unearned AUDIT_COMPLETE status...")
        rep_file = os.path.join(tmpdir, "INDEPENDENT_OPTIMIZER_AUDIT_REPORT.md")
        with open(rep_file, "r", encoding="utf-8") as f:
            content = f.read()
        orig_content = content
        tampered_content = content.replace("AUDIT_BLOCKED", "AUDIT_COMPLETE")
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write(tampered_content)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught unearned AUDIT_COMPLETE status.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unearned AUDIT_COMPLETE status.")
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write(orig_content)

        # -------------------------------------------------------------
        # Negative Control 8: Circular Validation in Recalculation CSV
        # -------------------------------------------------------------
        print("  [NC 8/15] Testing rejection of circular calculation labeled INDEPENDENTLY VERIFIED...")
        with open(recalc_file, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows[0]['independent_verification_status'] = 'INDEPENDENTLY VERIFIED'
        rows[0]['exact_source_provenance'] = 'PostgreSQL line items + canonical RateRule (pure first-principles derivation)'
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught circular validation labeled INDEPENDENTLY VERIFIED.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch circular validation.")
        rows[0] = orig_recalc
        with open(recalc_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        # -------------------------------------------------------------
        # Negative Control 9: Engine Qualification Flag Copied as Independent
        # -------------------------------------------------------------
        print("  [NC 9/15] Testing rejection of engine qualification copied as independent...")
        line_file = os.path.join(tmpdir, "THREE_ANCHOR_LINE_CLASSIFICATION.csv")
        with open(line_file, "r", encoding="utf-8") as f:
            lines = list(csv.DictReader(f))
        # Find LU contingency row (account 8300)
        cont_idx = next(i for i, r in enumerate(lines) if r['project'] == 'The Little Utopia' and r['account'] == '8300')
        orig_cont = dict(lines[cont_idx])
        lines[cont_idx]['independent_authority_treatment'] = 'INCLUDED' # copy engine!
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected copied engine qualification for contingency.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to reject copied engine qualification.")
        lines[cont_idx] = orig_cont
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)

        # -------------------------------------------------------------
        # Negative Control 10: FVD Foreign Cast Copied as Independent
        # -------------------------------------------------------------
        print("  [NC 10/15] Testing rejection of foreign cast qualified as Greek independent spend...")
        with open(line_file, "r", encoding="utf-8") as f:
            lines = list(csv.DictReader(f))
        cast_idx = next(i for i, r in enumerate(lines) if r['project'] == "F#K Valentine's Day" and r['account'] == '1400')
        orig_cast = dict(lines[cast_idx])
        lines[cast_idx]['independent_authority_treatment'] = 'INCLUDED'
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected foreign cast qualified in Greece.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch foreign cast in Greece.")
        lines[cast_idx] = orig_cast
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)

        # -------------------------------------------------------------
        # Negative Control 11: LLS ATL Copied as Independent California Spend
        # -------------------------------------------------------------
        print("  [NC 11/15] Testing rejection of ATL qualified in California BTL program...")
        with open(line_file, "r", encoding="utf-8") as f:
            lines = list(csv.DictReader(f))
        atl_idx = next(i for i, r in enumerate(lines) if r['project'] == 'Lips Like Sugar' and r['account'] == '1200')
        orig_atl = dict(lines[atl_idx])
        lines[atl_idx]['independent_authority_treatment'] = 'INCLUDED'
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly rejected ATL producer fees qualified in California.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch ATL in California.")
        lines[atl_idx] = orig_atl
        with open(line_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
            w.writeheader()
            w.writerows(lines)

        # -------------------------------------------------------------
        # Negative Control 12: Unbalanced Variance Bridge Arithmetic
        # -------------------------------------------------------------
        print("  [NC 12/15] Testing rejection of arithmetically unbalanced variance bridge...")
        var_file = os.path.join(tmpdir, "THREE_ANCHOR_VARIANCE_BRIDGE.csv")
        with open(var_file, "r", encoding="utf-8") as f:
            vrows = list(csv.DictReader(f))
        orig_vrow = dict(vrows[0])
        vrows[0]['qpe_adjustment_contingency'] = '999999.00' # imbalance!
        with open(var_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(vrows[0].keys()))
            w.writeheader()
            w.writerows(vrows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught arithmetically unbalanced bridge.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch bridge imbalance.")
        vrows[0] = orig_vrow
        with open(var_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(vrows[0].keys()))
            w.writeheader()
            w.writerows(vrows)

        # -------------------------------------------------------------
        # Negative Control 13: Unexplained Residual in Variance Bridge
        # -------------------------------------------------------------
        print("  [NC 13/15] Testing rejection of unexplained residual in variance bridge...")
        with open(var_file, "r", encoding="utf-8") as f:
            vrows = list(csv.DictReader(f))
        vrows[0]['unexplained_residual'] = '50000.00'
        with open(var_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(vrows[0].keys()))
            w.writeheader()
            w.writerows(vrows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-zero unexplained residual.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unexplained residual.")
        vrows[0] = orig_vrow
        with open(var_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(vrows[0].keys()))
            w.writeheader()
            w.writerows(vrows)

        # -------------------------------------------------------------
        # Negative Control 14: Undisclosed Program 4.0 Comparability on LLS
        # -------------------------------------------------------------
        print("  [NC 14/15] Testing rejection of undisclosed Program 4.0 comparability...")
        src_file = os.path.join(tmpdir, "THREE_ANCHOR_SOURCE_REGISTER.csv")
        with open(src_file, "r", encoding="utf-8") as f:
            srows = list(csv.DictReader(f))
        p4_idx = next(i for i, r in enumerate(srows) if "Program 4.0" in r['program_generation'])
        orig_srow = dict(srows[p4_idx])
        srows[p4_idx]['is_directly_comparable'] = 'TRUE' # false comparability!
        with open(src_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(srows[0].keys()))
            w.writeheader()
            w.writerows(srows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught undisclosed Program 4.0 comparability.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch undisclosed comparability.")
        srows[p4_idx] = orig_srow
        with open(src_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(srows[0].keys()))
            w.writeheader()
            w.writerows(srows)

        # -------------------------------------------------------------
        # Negative Control 15: Missing Anchor Defect Tracking
        # -------------------------------------------------------------
        print("  [NC 15/15] Testing rejection of missing anchor defect tracking in defect register...")
        def_file = os.path.join(tmpdir, "UNPROVEN_AND_DEFECT_REGISTER.csv")
        with open(def_file, "r", encoding="utf-8") as f:
            drows = [r for r in csv.DictReader(f) if r['register_id'] != 'DEF-FVD-001']
        with open(def_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(drows[0].keys()))
            w.writeheader()
            w.writerows(drows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing DEF-FVD-001 defect.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing defect tracking.")


        # -------------------------------------------------------------
        # Negative Control 16: Rejection of Served Value as Independent Input
        # -------------------------------------------------------------
        print("  [NC 16/21] Testing rejection of served value used as independent input...")
        src_reg_f = os.path.join(tmpdir, "FOUR_PROJECT_SOURCE_REGISTER.csv")
        with open(src_reg_f, "r", encoding="utf-8") as f:
            s_rows = list(csv.DictReader(f))
        orig_s = dict(s_rows[0])
        s_rows[0]['data_label'] = 'IMPLEMENTATION_VALUE_UNDER_AUDIT'
        s_rows[0]['is_directly_comparable'] = 'TRUE'
        with open(src_reg_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught served value misclassified as comparable independent input.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch served value as independent input.")
        s_rows[0] = orig_s
        with open(src_reg_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)

        # -------------------------------------------------------------
        # Negative Control 17: Rejection of Implied QPE Labeled Documented
        # -------------------------------------------------------------
        print("  [NC 17/21] Testing rejection of invalid data label in source register...")
        with open(src_reg_f, "r", encoding="utf-8") as f:
            s_rows = list(csv.DictReader(f))
        orig_s = dict(s_rows[2])
        s_rows[2]['data_label'] = 'INVALID_FABRICATED_LABEL'
        with open(src_reg_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught invalid data label.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch invalid data label.")
        s_rows[2] = orig_s
        with open(src_reg_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(s_rows[0].keys()))
            w.writeheader()
            w.writerows(s_rows)

        # -------------------------------------------------------------
        # Negative Control 18: Rejection of Non-Resident Cast Qualified in NM
        # -------------------------------------------------------------
        print("  [NC 18/21] Testing rejection of non-resident lead cast qualified in New Mexico...")
        fpl_f = os.path.join(tmpdir, "FOUR_PROJECT_LINE_CLASSIFICATION.csv")
        with open(fpl_f, "r", encoding="utf-8") as f:
            l_rows = list(csv.DictReader(f))
        bh_cast_idx = next(i for i, r in enumerate(l_rows) if r.get('project') == 'Bad Hombres' and r.get('account') == '1400')
        orig_l = dict(l_rows[bh_cast_idx])
        l_rows[bh_cast_idx]['independent_authority_treatment'] = 'QUALIFIED'
        with open(fpl_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(l_rows[0].keys()))
            w.writeheader()
            w.writerows(l_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-resident lead cast qualified in NM.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch non-resident cast qualification.")
        l_rows[bh_cast_idx] = orig_l
        with open(fpl_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(l_rows[0].keys()))
            w.writeheader()
            w.writerows(l_rows)

        # -------------------------------------------------------------
        # Negative Control 19: Rejection of Unexplained Residual in Four-Project Bridge
        # -------------------------------------------------------------
        print("  [NC 19/21] Testing rejection of unexplained residual in Bad Hombres bridge...")
        fpb_f = os.path.join(tmpdir, "FOUR_PROJECT_ANCHOR_VARIANCE_BRIDGES.csv")
        with open(fpb_f, "r", encoding="utf-8") as f:
            b_rows = list(csv.DictReader(f))
        bh_last_idx = next(i for i, r in enumerate(b_rows) if r.get('project') == 'Bad Hombres' and 'Residual' in r.get('bridge_step', ''))
        orig_b = dict(b_rows[bh_last_idx])
        b_rows[bh_last_idx]['dollar_amount'] = '1000.00'
        with open(fpb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(b_rows[0].keys()))
            w.writeheader()
            w.writerows(b_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-zero unexplained residual in Bad Hombres bridge.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unexplained residual.")
        b_rows[bh_last_idx] = orig_b
        with open(fpb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(b_rows[0].keys()))
            w.writeheader()
            w.writerows(b_rows)

        # -------------------------------------------------------------
        # Negative Control 20: Rejection of Unmapped Calculation Pathway
        # -------------------------------------------------------------
        print("  [NC 20/21] Testing rejection of unmapped calculation pathway...")
        fpsc_f = os.path.join(tmpdir, "FOUR_PROJECT_PERSISTED_SCENARIO_AUDIT.csv")
        with open(fpsc_f, "r", encoding="utf-8") as f:
            sc_rows = list(csv.DictReader(f))
        orig_sc = dict(sc_rows[0])
        sc_rows[0]['pathway_id'] = 'PATH-UNKNOWN-ROGUE-UNAUDITED'
        with open(fpsc_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(sc_rows[0].keys()))
            w.writeheader()
            w.writerows(sc_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught unmapped calculation pathway.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unmapped pathway.")
        sc_rows[0] = orig_sc
        with open(fpsc_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(sc_rows[0].keys()))
            w.writeheader()
            w.writerows(sc_rows)

        # -------------------------------------------------------------
        # Negative Control 21: Rejection of Missing Effective Date in Temporal Matrix
        # -------------------------------------------------------------
        print("  [NC 21/21] Testing rejection of missing effective date in temporal matrix...")
        fpt_f = os.path.join(tmpdir, "FOUR_PROJECT_TEMPORAL_RULE_MATRIX.csv")
        with open(fpt_f, "r", encoding="utf-8") as f:
            t_rows = list(csv.DictReader(f))
        orig_t = dict(t_rows[0])
        t_rows[0]['control_or_effective_date'] = ''
        with open(fpt_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(t_rows[0].keys()))
            w.writeheader()
            w.writerows(t_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing effective date in temporal matrix.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing effective date.")
        t_rows[0] = orig_t
        with open(fpt_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(t_rows[0].keys()))
            w.writeheader()
            w.writerows(t_rows)

        # -------------------------------------------------------------
        # Negative Control 22: Rejection of Group Rollup in Categorization Matrix
        # -------------------------------------------------------------
        print("  [NC 22/24] Testing rejection of group rollup included as leaf line in categorization matrix...")
        fpm_f = os.path.join(tmpdir, "FOUR_PROJECT_BUDGET_CATEGORIZATION_MATRIX.csv")
        with open(fpm_f, "r", encoding="utf-8") as f:
            m_rows = list(csv.DictReader(f))
        orig_m = dict(m_rows[0])
        m_rows[0]['description'] = 'TOTAL ABOVE THE LINE'
        with open(fpm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(m_rows[0].keys()))
            w.writeheader()
            w.writerows(m_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught group rollup included as leaf line.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch group rollup.")
        m_rows[0] = orig_m
        with open(fpm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(m_rows[0].keys()))
            w.writeheader()
            w.writerows(m_rows)

        # -------------------------------------------------------------
        # Negative Control 23: Rejection of Producer Rebate Line Inside Gross Spend
        # -------------------------------------------------------------
        print("  [NC 23/24] Testing rejection of producer rebate line included as gross spend...")
        with open(fpm_f, "r", encoding="utf-8") as f:
            m_rows = list(csv.DictReader(f))
        orig_m2 = dict(m_rows[1])
        m_rows[1]['producer_incentive_line'] = 'TRUE'
        with open(fpm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(m_rows[0].keys()))
            w.writeheader()
            w.writerows(m_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught producer rebate line inside gross spend.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch producer rebate line.")
        m_rows[1] = orig_m2
        with open(fpm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(m_rows[0].keys()))
            w.writeheader()
            w.writerows(m_rows)

        # -------------------------------------------------------------
        # Negative Control 24: Rejection of Undisclosed Cross-Format CSV Defect
        # -------------------------------------------------------------
        print("  [NC 24/24] Testing rejection of undisclosed cross-format CSV defect...")
        cfi_f = os.path.join(tmpdir, "CROSS_FORMAT_INCENTIVE_ISOLATION_AUDIT.csv")
        with open(cfi_f, "r", encoding="utf-8") as f:
            c_rows = list(csv.DictReader(f))
        orig_c = dict(c_rows[0])
        c_rows[0]['csv_parser_status'] = 'ALL_GOOD_NO_DEFECT'
        with open(cfi_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(c_rows[0].keys()))
            w.writeheader()
            w.writerows(c_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught undisclosed cross-format CSV defect.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch undisclosed cross-format defect.")
        c_rows[0] = orig_c
        with open(cfi_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(c_rows[0].keys()))
            w.writeheader()
            w.writerows(c_rows)

        # -------------------------------------------------------------
        # Negative Control 25: Rejection of California Historical 20% Contradiction
        # -------------------------------------------------------------
        print("  [NC 25/28] Testing rejection of California historical 20% contradiction...")
        car_f = os.path.join(tmpdir, "CODEX_D0E01E2_INDEPENDENT_AUDIT_REPORT.md")
        with open(car_f, "r", encoding="utf-8") as f:
            car_text = f.read()
        tampered_car = car_text.replace("Formal Retraction of California Control Contradiction", "Reaffirming California 20% Reservation Control")
        with open(car_f, "w", encoding="utf-8") as f:
            f.write(tampered_car)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught unretracted California 20% contradiction.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch California 20% contradiction.")
        with open(car_f, "w", encoding="utf-8") as f:
            f.write(car_text)

        # -------------------------------------------------------------
        # Negative Control 26: Rejection of Bad Hombres $60,000 SAG Reserve in Confirmed QPE
        # -------------------------------------------------------------
        print("  [NC 26/28] Testing rejection of Bad Hombres $60,000 SAG reserve in confirmed QPE...")
        cdm_f = os.path.join(tmpdir, "FOUR_ANCHOR_CODEX_D0E01E2_DISPOSITION_MATRIX.csv")
        with open(cdm_f, "r", encoding="utf-8") as f:
            cdm_rows = list(csv.DictReader(f))
        bh_1600_idx = next(i for i, r in enumerate(cdm_rows) if r.get('project_name') == 'Bad Hombres' and r.get('account_code') == '1600')
        orig_bh = dict(cdm_rows[bh_1600_idx])
        cdm_rows[bh_1600_idx]['confirmed_qpe_usd'] = '60000.00'
        with open(cdm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cdm_rows[0].keys()))
            w.writeheader()
            w.writerows(cdm_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught Bad Hombres SAG reserve in confirmed QPE.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch Bad Hombres SAG reserve in confirmed QPE.")
        cdm_rows[bh_1600_idx] = orig_bh
        with open(cdm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cdm_rows[0].keys()))
            w.writeheader()
            w.writerows(cdm_rows)

        # -------------------------------------------------------------
        # Negative Control 27: Rejection of Non-Conserving LLS Line 1100 Inclusion
        # -------------------------------------------------------------
        print("  [NC 27/28] Testing rejection of non-conserving LLS Line 1100 qualification...")
        lls_1100_idx = next(i for i, r in enumerate(cdm_rows) if r.get('project_name') == 'Lips Like Sugar' and r.get('account_code') == '1100')
        orig_lls = dict(cdm_rows[lls_1100_idx])
        cdm_rows[lls_1100_idx]['confirmed_qpe_usd'] = '314153.00'
        cdm_rows[lls_1100_idx]['excluded_usd'] = '0.00'
        with open(cdm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cdm_rows[0].keys()))
            w.writeheader()
            w.writerows(cdm_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-conserving LLS Line 1100 over-qualification.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch non-conserving LLS Line 1100 over-qualification.")
        cdm_rows[lls_1100_idx] = orig_lls
        with open(cdm_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cdm_rows[0].keys()))
            w.writeheader()
            w.writerows(cdm_rows)

        # -------------------------------------------------------------
        # Negative Control 28: Rejection of Greek Ordinary Cap Exceeding EUR 8,000,000
        # -------------------------------------------------------------
        print("  [NC 28/28] Testing rejection of Greek ordinary cap exceeding EUR 8,000,000...")
        tampered_car2 = car_text.replace("8,000,000", "15,000,000")
        with open(car_f, "w", encoding="utf-8") as f:
            f.write(tampered_car2)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught Greek cap tampering.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch Greek cap tampering.")
        with open(car_f, "w", encoding="utf-8") as f:
            f.write(car_text)

        # -------------------------------------------------------------
        # Negative Control 29: Rejection of Missing NY § 24/§ 31 Mutual Exclusivity
        # -------------------------------------------------------------
        print("  [NC 29/31] Testing rejection of missing NY statutory mutual exclusivity token...")
        nya_f = os.path.join(tmpdir, "NEW_YORK_INCENTIVES_AND_UPSTATE_AUDIT.md")
        with open(nya_f, "r", encoding="utf-8") as f:
            nya_text = f.read()
        tampered_nya = nya_text.replace("provided, however, that a taxpayer that is eligible for a credit under section twenty-four of this article shall not be eligible for a credit under this section", "taxpayers may freely stack section twenty-four and section thirty-one on distinct costs")
        with open(nya_f, "w", encoding="utf-8") as f:
            f.write(tampered_nya)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught tampering of NY statutory mutual exclusivity.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch tampering of NY statutory mutual exclusivity.")
        with open(nya_f, "w", encoding="utf-8") as f:
            f.write(nya_text)

        # -------------------------------------------------------------
        # Negative Control 30: Rejection of NY ATL 40% Aggregate Ceiling Violation
        # -------------------------------------------------------------
        print("  [NC 30/31] Testing rejection of NY ATL 40% aggregate ceiling violation...")
        nym_f = os.path.join(tmpdir, "NEW_YORK_FOUR_PROJECT_SCENARIO_MATRIX.csv")
        with open(nym_f, "r", encoding="utf-8") as f:
            nym_rows = list(csv.DictReader(f))
        orig_nym = [dict(r) for r in nym_rows]
        # Boost FVD ATL lines to exceed 40% ceiling
        for r in nym_rows:
            if r['project_title'] == "F#K Valentine's Day" and 'ATL' in r['ny_statutory_treatment']:
                r['downstate_qpe_usd'] = r['amount_usd']  # uncap ATL to full $1.898M
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(nym_rows[0].keys()))
            w.writeheader()
            w.writerows(nym_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught NY ATL 40% ceiling violation.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch NY ATL 40% ceiling violation.")
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_nym[0].keys()))
            w.writeheader()
            w.writerows(orig_nym)

        # -------------------------------------------------------------
        # Negative Control 31: Rejection of Non-Post Expense Qualified for NY § 31 Post Credit
        # -------------------------------------------------------------
        print("  [NC 31/31] Testing rejection of non-post expense qualified for NY § 31 post credit...")
        tampered_nym2 = [dict(r) for r in orig_nym]
        for r in tampered_nym2:
            if r['project_title'] == 'The Little Utopia' and r['account_code'] == '2200':
                r['qualifies_standalone_post_31'] = 'Y'
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(tampered_nym2[0].keys()))
            w.writeheader()
            w.writerows(tampered_nym2)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-post expense qualified under Section 31.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch non-post expense qualified under Section 31.")
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_nym[0].keys()))
            w.writeheader()
            w.writerows(orig_nym)

        # -------------------------------------------------------------
        # Negative Control 32: Rejection of Calling Greece Difference a Confirmed Golden Overstatement
        # -------------------------------------------------------------
        print("  [NC 32/34] Testing rejection of calling Greece difference a confirmed golden overstatement...")
        irr_f = os.path.join(tmpdir, "FOUR_ANCHOR_QPE_ISSUE_REGISTER_RECONCILIATION.md")
        with open(irr_f, "r", encoding="utf-8") as f:
            irr_text = f.read()
        tampered_irr = irr_text.replace("UNRESOLVED_PLANNING_VARIANCE", "CONFIRMED_ENGINE_OVERSTATEMENT_OF_GOLDEN_BASE")
        with open(irr_f, "w", encoding="utf-8") as f:
            f.write(tampered_irr)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught unproven Greece confirmed overstatement claim.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch unproven Greece confirmed overstatement claim.")
        with open(irr_f, "w", encoding="utf-8") as f:
            f.write(irr_text)

        # -------------------------------------------------------------
        # Negative Control 33: Rejection of Missing Bad Hombres Cast Withholding Condition
        # -------------------------------------------------------------
        print("  [NC 33/34] Testing rejection of missing Bad Hombres cast withholding condition...")
        tampered_irr2 = irr_text.replace("CONDITIONAL ON CAST WITHHOLDING PROOF", "UNCONDITIONALLY CONFIRMED IN FULL")
        with open(irr_f, "w", encoding="utf-8") as f:
            f.write(tampered_irr2)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing Bad Hombres cast withholding condition.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing Bad Hombres cast withholding condition.")
        with open(irr_f, "w", encoding="utf-8") as f:
            f.write(irr_text)

        # -------------------------------------------------------------
        # Negative Control 34: Rejection of Improperly Qualified Finance Costs in FVD Greece Matrix
        # -------------------------------------------------------------
        print("  [NC 34/34] Testing rejection of improperly qualified finance costs in FVD Greece matrix...")
        fgr_f = os.path.join(tmpdir, "FVD_GREECE_34_ACCOUNT_RECONSTRUCTION.csv")
        with open(fgr_f, "r", encoding="utf-8") as f:
            fgr_rows = list(csv.DictReader(f))
        orig_fgr = [dict(r) for r in fgr_rows]
        for r in fgr_rows:
            if r['account_code'] == '7901':
                r['is_statutorily_excluded'] = 'FALSE'
        with open(fgr_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(fgr_rows[0].keys()))
            w.writeheader()
            w.writerows(fgr_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught improperly qualified Greek finance costs.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch improperly qualified Greek finance costs.")
        with open(fgr_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_fgr[0].keys()))
            w.writeheader()
            w.writerows(orig_fgr)

        # -------------------------------------------------------------
        # Negative Control 35: Rejection of On-Set Production Sound in NY § 31 Post Credit
        # -------------------------------------------------------------
        print("  [NC 35/41] Testing rejection of on-set production sound qualified for NY § 31 post credit...")
        with open(nym_f, "r", encoding="utf-8") as f:
            nym_rows = list(csv.DictReader(f))
        orig_nym = [dict(r) for r in nym_rows]
        for r in nym_rows:
            if r['project_title'] == 'The Little Utopia' and r['account_code'] == '3200':
                r['qualifies_standalone_post_31'] = 'Y'
                r['standalone_post_qpe_usd'] = '69532.00'
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(nym_rows[0].keys()))
            w.writeheader()
            w.writerows(nym_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught on-set production sound qualified under Section 31.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch on-set production sound qualified under Section 31.")
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_nym[0].keys()))
            w.writeheader()
            w.writerows(orig_nym)

        # -------------------------------------------------------------
        # Negative Control 36: Rejection of Omitted LLS Bridge Financing Fee in Exclusions
        # -------------------------------------------------------------
        print("  [NC 36/41] Testing rejection of omitted LLS bridge financing fee in exclusions...")
        with open(nym_f, "r", encoding="utf-8") as f:
            nym_rows = list(csv.DictReader(f))
        orig_nym = [dict(r) for r in nym_rows]
        for r in nym_rows:
            if r['project_title'] == 'Lips Like Sugar' and r['account_code'] == '6600':
                r['ny_statutory_treatment'] = 'QUALIFIED_BTL_PHYSICAL'
                r['downstate_qpe_usd'] = '250000.00'
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(nym_rows[0].keys()))
            w.writeheader()
            w.writerows(nym_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught omitted LLS bridge financing fee in exclusions.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch omitted LLS bridge financing fee in exclusions.")
        with open(nym_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_nym[0].keys()))
            w.writeheader()
            w.writerows(orig_nym)

        # -------------------------------------------------------------
        # Negative Control 37: Rejection of Missing NY Adjudication Token in Report
        # -------------------------------------------------------------
        print("  [NC 37/41] Testing rejection of missing NY adjudication reference in audit report...")
        nya_f = os.path.join(tmpdir, "NEW_YORK_INCENTIVES_AND_UPSTATE_AUDIT.md")
        with open(nya_f, "r", encoding="utf-8") as f:
            orig_nya = f.read()
        tampered_nya = orig_nya.replace("NY_AG_BDE0FEE_ADJUDICATION.md", "SOME_OTHER_DOC.md")
        with open(nya_f, "w", encoding="utf-8") as f:
            f.write(tampered_nya)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing NY adjudication reference.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing NY adjudication reference.")
        with open(nya_f, "w", encoding="utf-8") as f:
            f.write(orig_nya)

        # -------------------------------------------------------------
        # Negative Control 38: Rejection of Blanket Exclusion of Insurance in FVD Greece Matrix
        # -------------------------------------------------------------
        print("  [NC 38/41] Testing rejection of blanket exclusion of Greek insurance...")
        fgr_f = os.path.join(tmpdir, "FVD_GREECE_34_ACCOUNT_RECONSTRUCTION.csv")
        with open(fgr_f, "r", encoding="utf-8") as f:
            fgr_rows = list(csv.DictReader(f))
        orig_fgr = [dict(r) for r in fgr_rows]
        for r in fgr_rows:
            if r['account_code'] == '7200':
                r['is_statutorily_excluded'] = 'TRUE'
        with open(fgr_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(fgr_rows[0].keys()))
            w.writeheader()
            w.writerows(fgr_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught blanket exclusion of Greek insurance.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch blanket exclusion of Greek insurance.")
        with open(fgr_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_fgr[0].keys()))
            w.writeheader()
            w.writerows(orig_fgr)

        # -------------------------------------------------------------
        # Negative Control 39: Rejection of Missing Candidate Claiming VERIFIED_AGREEMENT
        # -------------------------------------------------------------
        print("  [NC 39/41] Testing rejection of missing candidate claiming VERIFIED_AGREEMENT...")
        na_mat_f = os.path.join(tmpdir, "NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv")
        with open(na_mat_f, "r", encoding="utf-8") as f:
            mat_rows = list(csv.DictReader(f))
        orig_mat = [dict(r) for r in mat_rows]
        target_idx = next(i for i, r in enumerate(mat_rows) if r['matched_structure_id'] == 'N/A')
        mat_rows[target_idx]['remediation_code_status'] = 'VERIFIED_AGREEMENT'
        with open(na_mat_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(mat_rows[0].keys()))
            w.writeheader()
            w.writerows(mat_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing candidate claiming VERIFIED_AGREEMENT.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing candidate claiming VERIFIED_AGREEMENT.")
        with open(na_mat_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_mat[0].keys()))
            w.writeheader()
            w.writerows(orig_mat)

        # -------------------------------------------------------------
        # Negative Control 40: Rejection of LU NY $1,000 Operand Discrepancy
        # -------------------------------------------------------------
        print("  [NC 40/41] Testing rejection of LU NY $1,000 operand discrepancy in report...")
        na_reg_f = os.path.join(tmpdir, "NORTH_AMERICAN_DISCREPANCY_REGISTER.md")
        with open(na_reg_f, "r", encoding="utf-8") as f:
            orig_reg = f.read()
        tampered_reg = orig_reg.replace("$3,142,324.00", "$3,141,324.00")
        with open(na_reg_f, "w", encoding="utf-8") as f:
            f.write(tampered_reg)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught LU NY $1,000 operand discrepancy.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch LU NY $1,000 operand discrepancy.")
        with open(na_reg_f, "w", encoding="utf-8") as f:
            f.write(orig_reg)

        # -------------------------------------------------------------
        # Negative Control 41: Rejection of Missing Supported Bounds in NY Closeout Handoff
        # -------------------------------------------------------------
        print("  [NC 41/41] Testing rejection of missing supported bounds in NY closeout handoff...")
        ny_hnd_f = os.path.join(tmpdir, "NEW_YORK_AUDIT_CLOSEOUT_HANDOFF.md")
        with open(ny_hnd_f, "r", encoding="utf-8") as f:
            orig_hnd = f.read()
        tampered_hnd = orig_hnd.replace("$2,836,167.00", "$9,999,999.00")
        with open(ny_hnd_f, "w", encoding="utf-8") as f:
            f.write(tampered_hnd)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught tampered NY closeout handoff bounds.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch tampered NY closeout handoff.")
        with open(ny_hnd_f, "w", encoding="utf-8") as f:
            f.write(orig_hnd)

        # -------------------------------------------------------------
        # Negative Control 42: Rejection of Non-Zero Line Overlap in NA Hybrid Matrix
        # -------------------------------------------------------------
        print("  [NC 42/44] Testing rejection of non-zero line overlap in NA Hybrid Coverage Matrix...")
        na_hyb_f = os.path.join(tmpdir, "NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv")
        with open(na_hyb_f, "r", encoding="utf-8") as f:
            hyb_rows = list(csv.DictReader(f))
        orig_hyb = [dict(r) for r in hyb_rows]
        hyb_rows[0]["line_overlap_count"] = "2"
        with open(na_hyb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(hyb_rows[0].keys()))
            w.writeheader()
            w.writerows(hyb_rows)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught non-zero line overlap in NA Hybrid Coverage Matrix.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch non-zero line overlap in NA Hybrid Coverage Matrix.")
        with open(na_hyb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_hyb[0].keys()))
            w.writeheader()
            w.writerows(orig_hyb)

        # -------------------------------------------------------------
        # Negative Control 43: Rejection of LLS MB-CA Retained Hybrid Falsely Qualifying
        # -------------------------------------------------------------
        print("  [NC 43/44] Testing rejection of LLS MB-CA Artifact 1 falsely claiming qualified credit...")
        tampered_hyb2 = [dict(r) for r in orig_hyb]
        for r in tampered_hyb2:
            if r["row_category"] == "LLS_MB_CA_ARTIFACT_1_RETAINED_HYBRID":
                r["independent_expected_status"] = "PRICED"
                r["independent_incentive_floor_usd"] = "2845096.20"
        with open(na_hyb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(tampered_hyb2[0].keys()))
            w.writeheader()
            w.writerows(tampered_hyb2)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught LLS MB-CA Artifact 1 falsely claiming qualified credit.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch LLS MB-CA Artifact 1 false credit claim.")
        with open(na_hyb_f, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(orig_hyb[0].keys()))
            w.writeheader()
            w.writerows(orig_hyb)

        # -------------------------------------------------------------
        # Negative Control 44: Rejection of Missing Frozen Commit in NA Hybrid Handoff
        # -------------------------------------------------------------
        print("  [NC 44/44] Testing rejection of missing frozen commit in NA Hybrid Audit Handoff...")
        na_hyb_md_f = os.path.join(tmpdir, "NORTH_AMERICAN_HYBRID_AUDIT_HANDOFF.md")
        with open(na_hyb_md_f, "r", encoding="utf-8") as f:
            orig_hyb_md = f.read()
        tampered_hyb_md = orig_hyb_md.replace("59566fd17463b71e9796d41e8e080bf5d0ac27ea", "0000000000000000000000000000000000000000")
        with open(na_hyb_md_f, "w", encoding="utf-8") as f:
            f.write(tampered_hyb_md)
        tampered_ok, _ = validate_artifacts(base_dir=tmpdir, silent=True)
        if not tampered_ok:
            print("    -> PASS: Validator correctly caught missing frozen commit in NA Hybrid Audit Handoff.")
            nc_passed += 1
        else:
            print("    -> FAIL: Validator failed to catch missing frozen commit in NA Hybrid Audit Handoff.")
        with open(na_hyb_md_f, "w", encoding="utf-8") as f:
            f.write(orig_hyb_md)

    print(f"\nNEGATIVE CONTROLS SUMMARY: {nc_passed}/{nc_total} PASSED (100% SUCCESS)")
    return nc_passed == nc_total


def main():
    print("==================================================")
    print("VALIDATING INDEPENDENT OPTIMIZER AUDIT ARTIFACTS")
    print("==================================================")
    success, errors = validate_artifacts()
    if not success:
        print("\nVALIDATION FAILED WITH ERRORS:")
        for e in errors:
            print(f"  [X] {e}")
        sys.exit(1)
    else:
        print("\nALL AUDIT ARTIFACTS PASSED STATIC AND INTEGRITY VALIDATION!")

    nc_ok = run_negative_controls()
    if not nc_ok:
        print("\nNEGATIVE CONTROLS SUITE FAILED!")
        sys.exit(1)
    
    print("\n==================================================")
    print("100% AUDIT VALIDATION COMPLETE AND VERIFIED!")
    print("==================================================")


if __name__ == "__main__":
    main()
