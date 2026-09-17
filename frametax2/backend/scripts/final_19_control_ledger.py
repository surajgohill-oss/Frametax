#!/usr/bin/env python3
"""FINAL exact 19-row control ledger for CLAUDE_GENERIC_STRUCTURAL_
DISCOVERY_FINAL_COMPLETION. Supersedes CLAUDE_GENERIC_DISCOVERY_19_
CONTROL_RECONCILIATION.csv (the pre-audit-fixture version). Every status
below reflects REAL evaluate_project() runtime evidence gathered this
pass, not direct-generator unit tests and not invented facts. Statuses:

  NATURAL_EXACT_MATCH                  -- exact PRICED match, real production
  EXPECTED_RULE_REJECTION_EXACT_MATCH  -- exact RULE_REJECTED match, real production
  DOMINATED_WITH_PROOF_VERIFIED        -- audit fixture reached a genuine,
                                           reconstructable DOMINATED_WITH_PROOF
                                           disposition for the exact control
  MULTI_PRINCIPAL_DEFERRED             -- requires >=2 simultaneous
                                           principal_production legs; belongs to
                                           CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION
  GRANT_COMPONENT_UNWIRED_DEFERRED     -- requires a fund_overlay/selective_upside
                                           component the real pipeline can never
                                           construct from any spend_category
  UNRESOLVED_GAP                       -- audit fixture built and run through the
                                           REAL evaluate_project() path, but the
                                           exact control's disposition could not be
                                           conclusively confirmed this pass without
                                           inventing facts; requires further
                                           domain research, carried forward
"""
import csv
import os

OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
NZ_POST = "new_zealand_screen_production_grant_—_international_post_vfx"

ROWS = [
    {
        "control_id": "HO-001", "status": "DOMINATED_WITH_PROOF_VERIFIED",
        "required_program_set": sorted({"us_ga_film_credit", NZ_POST, OCASE}),
        "evidence": "AUDIT_CONTROL_HO_001 (home=US-GA): pigeonhole window=2, dominated_count=108, "
                    "incumbent=ca_mb_film_video_credit+ca_nl_all_spend_credit -- real, better-priced "
                    "Canadian post/vfx alternatives proven superior; independently reproduces the "
                    "same finding already documented for Lips Like Sugar on a clean synthetic fixture.",
        "next_action": "None -- canonically verified via evaluate_project(), reconstructable.",
    },
    {
        "control_id": "HO-002", "status": "DOMINATED_WITH_PROOF_VERIFIED",
        "required_program_set": sorted({"us_nm_film_credit", "au_pdv_offset", OCASE}),
        "evidence": "AUDIT_CONTROL_HO_002 (home=US-NM): pigeonhole window=2, dominated_count=107, "
                    "same CA-MB/CA-NL incumbent pattern as HO-001.",
        "next_action": "None -- canonically verified via evaluate_project(), reconstructable.",
    },
    {
        "control_id": "HO-003", "status": "MULTI_PRINCIPAL_DEFERRED",
        "required_program_set": sorted({"uk_avec", "au_producer_offset", NZ_POST}),
        "evidence": "Confirmed via its own direct-generator test: both uk_avec and au_producer_offset "
                    "are principal_production-type components -- a shape ordinary_component_hybrid "
                    "cannot express (one anchor + movable post/vfx/music only).",
        "next_action": "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream.",
    },
    {
        "control_id": "HO-004", "status": "UNRESOLVED_GAP",
        "required_program_set": sorted({"ca_federal_cptc", "on_ofttc", OCASE}),
        "evidence": "AUDIT_CONTROL_HO_004 (home=CA-ON) built and evaluated. ca_federal_cptc's real "
                    "qualifying-labour reconciliation (allocation_pricing.py's exact-match component-"
                    "basis check) produced inconsistent computed bounds across attempts ($1,860,000 vs "
                    "$2,800,000 depending on whether the amount fact was caller-supplied or auto-probed) "
                    "-- resolving this correctly requires reading the allocation/qualification pipeline "
                    "in more depth than completed this pass. Not forced with a guessed value.",
        "next_action": "Read derive_account_allocation/derive_qualification_register's federal-candidate "
                        "QPE apportionment to find the real exact labour subtotal, then re-run.",
    },
    {
        "control_id": "HO-005", "status": "UNRESOLVED_GAP",
        "required_program_set": sorted({"ca_federal_pstc", "on_opstc", OCASE}),
        "evidence": "Same root cause as HO-004 (ca_federal_pstc uses the identical "
                    "qualified-labour-subtotal gate).",
        "next_action": "Same as HO-004.",
    },
    {
        "control_id": "HO-006", "status": "UNRESOLVED_GAP",
        "required_program_set": sorted({"ca_federal_pstc", "ca_bc_pstc", "ca_bc_dave"}),
        "evidence": "AUDIT_CONTROL_HO_006 (home=CA-BC): the BC-only 2-way leg (ca_bc_pstc+ca_bc_dave) "
                    "PRICED correctly, matching the real Little Utopia production's own behavior. The "
                    "3-way (adding ca_federal_pstc) hit the identical qualifying-labour reconciliation "
                    "gap as HO-004/005.",
        "next_action": "Same as HO-004; the BC-only 2-way leg is already independently confirmed.",
    },
    {
        "control_id": "HO-007", "status": "MULTI_PRINCIPAL_DEFERRED",
        "required_program_set": sorted({"uk_avec", "fr_trip", NZ_POST}),
        "evidence": "Same dual-principal-leg shape as HO-003 (uk_avec + fr_trip both principal_production).",
        "next_action": "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream.",
    },
    {
        "control_id": "HO-008", "status": "DOMINATED_WITH_PROOF_VERIFIED",
        "required_program_set": sorted({"ie_section_481", "au_pdv_offset", OCASE}),
        "evidence": "AUDIT_CONTROL_HO_008 (home=IE): pigeonhole window=2, dominated_count=125, same "
                    "CA-MB/CA-NL incumbent pattern.",
        "next_action": "None -- canonically verified via evaluate_project(), reconstructable.",
    },
    {
        "control_id": "HO-009", "status": "UNRESOLVED_GAP",
        "required_program_set": sorted({"nz_spg_international", "ca_bc_dave", "us_ny_post_production_credit"}),
        "evidence": "AUDIT_CONTROL_HO_009 (home=NZ): NEW FINDING, distinct from HO-001/002/008 -- the "
                    "{post, vfx} 2-component subset for the TRUE home anchor NZ produced ZERO persisted "
                    "rows of any kind (no PRICED, no RULE_REJECTED, no DOMINATED_WITH_PROOF), unlike "
                    "HO-001/002/008 which all reached a genuine dominance proof. Consistent with a "
                    "silent-omission code path (`if any(not lst for lst in _full_lists): continue`) "
                    "triggering for this specific anchor/component combination -- requires direct "
                    "instrumentation to confirm root cause, not yet done this pass.",
        "next_action": "Instrument the hybrid loop for anchor=NZ on this exact fixture to determine "
                        "why _full_lists came back empty (or find the real cause) before this can be "
                        "closed as fixed vs. reported as a genuine production defect.",
    },
    {
        "control_id": "HO-010", "status": "GRANT_COMPONENT_UNWIRED_DEFERRED",
        "required_program_set": sorted({"ca_federal_cptc", "on_ofttc", "ca_sk_creative_saskatchewan_grant"}),
        "evidence": "ca_sk_creative_saskatchewan_grant only exists as component_type=fund_overlay in its "
                    "own direct-generator test; COMPONENT_BY_SPEND_CATEGORY has no mapping from any real "
                    "spend_category to fund_overlay/selective_upside -- the real budget-driven pipeline "
                    "can never construct this component type.",
        "next_action": "Route to whichever workstream connects grant/fund discovery "
                        "(build_available_funds/opportunity_discovery) into the generic generator's "
                        "component vocabulary -- likely REINVESTMENT_IN_KIND_GROSS_UP_OPPORTUNITY_ENGINE.",
    },
    {
        "control_id": "HO-011", "status": "GRANT_COMPONENT_UNWIRED_DEFERRED",
        "required_program_set": sorted({"us_ga_film_credit", NZ_POST, "us_tn_performance_grant"}),
        "evidence": "Same root cause as HO-010 (us_tn_performance_grant is component_type=selective_upside).",
        "next_action": "Same as HO-010.",
    },
    {
        "control_id": "HO-012", "status": "MULTI_PRINCIPAL_DEFERRED",
        "required_program_set": sorted({"uk_avec", "ie_section_481", "fr_trip"}),
        "evidence": "Three simultaneous principal_production legs -- the most extreme case of the "
                    "dual-principal-leg shape.",
        "next_action": "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream.",
    },
    {
        "control_id": "HO-013", "status": "MULTI_PRINCIPAL_DEFERRED",
        "required_program_set": sorted({"uk_avec", "au_producer_offset", NZ_POST, OCASE}),
        "evidence": "Shares HO-003's exact dual-principal-leg pair (uk_avec + au_producer_offset) plus "
                    "two movable legs; the movable legs do not change the underlying blocker.",
        "next_action": "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream.",
    },
    {
        "control_id": "REG-1", "status": "EXPECTED_RULE_REJECTION_EXACT_MATCH",
        "required_program_set": sorted({"ca_bc_pstc", "ca_federal_cptc"}),
        "evidence": "F#K Valentine's Day, real production, exact match, RULE_REJECTED as expected "
                    "(MUTUALLY_EXCLUSIVE).",
        "next_action": "None -- already canonically verified.",
    },
    {
        "control_id": "REG-2", "status": "NATURAL_EXACT_MATCH",
        "required_program_set": sorted({"ca_federal_cptc", "on_ofttc"}),
        "evidence": "F#K Valentine's Day, real production, exact match, PRICED as expected "
                    "(ALLOWED_WITH_SPEND_REDUCTION).",
        "next_action": "None -- already canonically verified.",
    },
    {
        "control_id": "REG-3", "status": "EXPECTED_RULE_REJECTION_EXACT_MATCH",
        "required_program_set": sorted({"ca_federal_cptc", "on_opstc"}),
        "evidence": "F#K Valentine's Day, real production, exact match, RULE_REJECTED as expected "
                    "(MUTUALLY_EXCLUSIVE).",
        "next_action": "None -- already canonically verified.",
    },
    {
        "control_id": "REG-4", "status": "MULTI_PRINCIPAL_DEFERRED",
        "required_program_set": sorted({"ie_section_481", "uk_avec"}),
        "evidence": "Its own direct-generator test (test_registered_control_4_...) builds BOTH "
                    "ie_section_481 and uk_avec via _comp()'s DEFAULT component_type="
                    "'principal_production' -- identical dual-principal-leg shape to HO-003.",
        "next_action": "Defer to CANONICAL_MULTI_PRINCIPAL_COPRODUCTION_COMPOSITION workstream.",
    },
    {
        "control_id": "REG-5", "status": "UNRESOLVED_GAP",
        "required_program_set": sorted({"ny_state_film", "us_ny_post_production_credit"}),
        "evidence": "AUDIT_CONTROL_REG_5 (home=US-NY) built and evaluated: us_ny_post_production_credit "
                    "shares US-NY with the anchor, so it is excluded from hybrid-loop routing "
                    "(`t.jurisdiction_code != _anchor_code`) by construction, and it never appears in "
                    "priced_by_code['US-NY'] as a full-relocation candidate (it can only price its own "
                    "post-specific QPE, not the whole budget), so the same-jurisdiction group-stack "
                    "mechanism (price_program_group_stack) never sees it as combinable either. Distinct "
                    "root cause from multi-principal and from grant-unwired.",
        "next_action": "Requires either a same-jurisdiction-component-specific-credit combination path, "
                        "or confirmation that this control is only ever reachable in real usage via a "
                        "mechanism not yet identified -- carried forward, not forced.",
    },
    {
        "control_id": "REG-6", "status": "EXPECTED_RULE_REJECTION_EXACT_MATCH",
        "required_program_set": sorted({"on_ofttc", "on_opstc"}),
        "evidence": "The Little Utopia, real production, exact match, RULE_REJECTED as expected "
                    "(MUTUALLY_EXCLUSIVE).",
        "next_action": "None -- already canonically verified.",
    },
]

assert len(ROWS) == 19, f"expected exactly 19 rows, got {len(ROWS)}"
counts: dict[str, int] = {}
for r in ROWS:
    counts[r["status"]] = counts.get(r["status"], 0) + 1
assert sum(counts.values()) == 19

print("FINAL STATUS COUNTS:")
for k, v in sorted(counts.items()):
    print(f"  {k}: {v}")
print(f"  TOTAL: {sum(counts.values())}")

out_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "validation",
                         "CLAUDE_GENERIC_DISCOVERY_19_CONTROL_RECONCILIATION.csv")
out_path = os.path.abspath(out_path)
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["control_id", "status", "required_program_set", "evidence", "next_action"])
    w.writeheader()
    for r in ROWS:
        row = dict(r)
        row["required_program_set"] = "|".join(row["required_program_set"])
        w.writerow(row)
print(f"\nWrote FINAL ledger to {out_path} (supersedes the pre-audit-fixture version)")
