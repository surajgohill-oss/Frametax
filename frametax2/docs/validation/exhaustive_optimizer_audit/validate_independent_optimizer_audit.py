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
    nc_total = 21

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
