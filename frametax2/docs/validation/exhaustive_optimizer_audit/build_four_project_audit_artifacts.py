#!/usr/bin/env python3
"""
build_four_project_audit_artifacts.py
Master builder for the CineGlobe Four-Project Independent Optimizer Audit,
Historical-Audit Reconciliation, and Permanent-Control Design deliverables:

1. AUDIT_LINEAGE_AND_INVALIDATION_MATRIX.csv
2. FOUR_PROJECT_SOURCE_REGISTER.csv
3. FOUR_PROJECT_TEMPORAL_RULE_MATRIX.csv
4. FOUR_PROJECT_LINE_CLASSIFICATION.csv
5. FOUR_PROJECT_ANCHOR_VARIANCE_BRIDGES.csv
6. FOUR_PROJECT_PATHWAY_COVERAGE.csv
7. FOUR_PROJECT_PERSISTED_SCENARIO_AUDIT.csv
8. FOUR_PROJECT_PROGRAM_REACHABILITY.csv
9. FOUR_PROJECT_STACKING_AND_OVERLAP_AUDIT.csv
10. FOUR_PROJECT_OPTIMIZER_SELECTION_AUDIT.csv
11. DEFECT_ROOT_CAUSE_AND_BLAST_RADIUS.csv
12. PERMANENT_CALCULATION_ACCEPTANCE_CONTROLS.md
13. FINAL_AG_EVIDENCE_HANDOFF_TO_CODEX.md
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("==================================================")
    print("BUILDING ALL FOUR-PROJECT AUDIT ARTIFACTS")
    print("==================================================")
    
    # 1-11: Data CSVs
    p1 = os.path.join(BASE_DIR, "make_four_project_artifacts.py")
    if os.path.exists(p1):
        subprocess.check_call([sys.executable, p1])
        
    # 12: Permanent Controls Document
    p2 = os.path.join(BASE_DIR, "make_permanent_controls_doc.py")
    if os.path.exists(p2):
        subprocess.check_call([sys.executable, p2])
        
    # 13: Final Handoff Document
    p3 = os.path.join(BASE_DIR, "make_final_handoff_doc.py")
    if os.path.exists(p3):
        subprocess.check_call([sys.executable, p3])

    print("\nAll 13 four-project audit artifacts built successfully!")

if __name__ == "__main__":
    main()
