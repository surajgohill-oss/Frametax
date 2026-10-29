# NA allocation calculation closeout (Claude)

Base: `93571b55100a561e5b8db9b9731a5367c5d2fd91` (ancestor of `origin/claude/global-optimizer-remediation`, which was at that SHA at start). Branch `claude/global-optimizer-remediation`. Final SHA: see the commit that adds this file (reported in the closing message; a report cannot contain its own hash).
Work was done in a separate worktree off `93571b55`; the live checkout (still at `516136c3` with the user's three uncommitted documentation edits) was not pulled, reset, stashed or edited.

## Changed files
`backend/app/calculators/canadian_labour_basis.py`, `backend/app/calculators/per_payee_limits.py`, `backend/app/calculators/line_allocations.py` (message only), `backend/app/services/line_inputs.py`, `backend/app/services/ny_producer_facts.py`, `frontend/src/components/LineInputsSection.jsx`, `frontend/src/lib/lineInputs.js`; new `backend/tests/test_na_allocation_calculation_closeout_controls.py` (26), `frontend/tests/line-input-percent-share.test.mjs` (5); this report, the handoff (00m) and the ledger section. None of these modules is in `_SEMANTIC_PRICING_MODULES`, so no production is staled by digest (see the retained-result caution below).

## Defect / reproducer / result
| # | Reproducer | Result |
|---|---|---|
| 1 | $100,000 line, 60% resident + 100% in Canada | relevant basis $60,000; gross 150,000 and the other line unchanged (`test_sixty_percent...`); priced input after a browser save: `ca_federal_pstc_qualified_labour_usd` = 400,000 for 40% of a 1,000,000 line, gross 2,300,000 unchanged |
| 2 | assumed 100% -> explicit 0% -> explicit 40%/100% -> reset | persistence, disclosure and priced input at each step (`test_assumed_to_zero_to_partial_to_reset...`); browser repeated it |
| 3 | 70% resident, 60% in Canada, no intersection | floor 30,000 (guaranteed overlap); not 42,000 (product) and not 60,000 (minimum); the 30%..60% range is disclosed; explicit intersection 55 -> 55,000; one share at 100% or 0% makes the other exact |
| 4 | person holds $300,000 / $700,000 of a $1,000,000 line, Georgia W-2 cap $500,000 | 0 excluded / 200,000 excluded; qualified 1,000,000 / 800,000; remainder uncapped and disclosed UNRESOLVED; every line conserved (before: 500,000 cut in both) |
| 5 | two payees $600,000 each on a $1,200,000 line | each capped once: 200,000 excluded, 1,000,000 qualified, no UNRESOLVED note |
| 6 | percentages with unknown headcount | no payee ordinal or allocation fact is derived; an over-cap line with only shares stays UNRESOLVED at its qualified amount |
| 7 | allocation save / edit / reset | `payee_type`, `canadian_status`, shares and `role` unchanged; only an explicit edit of the fact changes it; browser repeated it |
| 8 | -1, 100.01, 101, NaN, +/-inf, "50", true, unknown keys, inconsistent intersection | `ValueError` before any write; the valid row of the same request is not written; DB rows identical |
| 9 | direct vs stack | one `limits_facts_from_amount_facts` produces the ProductionFacts for both; home and relocated legs exclude the same dollars |
| 10 | selection pinning from `93571b55` | `test_na25_selection_allocation_integrity_controls.py` passes in the affected group; in the browser run the leading selection stayed `user_selected: true, unavailable: false` across regenerations |

15 of the 26 new backend controls fail on the unmodified `93571b55` (the other 11 are the invariants that must not move: full-allocation division, the two-payee case, cross-line single cap, parity of the unchanged legs).

## Percentage / default / provenance contract
* Three separate line facts, 0-100 of THIS line: `canadian_resident_share_pct`, `service_in_canada_share_pct`, `resident_and_in_canada_share_pct` (qualifying intersection). Stored as ordinary `line_fact:<line>:<field>` rows (project + budget-line identity, USER_OVERRIDE provenance); consumed by the federal PSTC labour basis only, because [PSTC-GUIDE] requires BOTH conditions. CPTC is deliberately not gated (no CPTC residency test was read; unchanged note in the module).
* Validation: finite, 0-100, number only; intersection cannot exceed either share nor fall below `r + s - 100`; checked on stored + incoming values; unknown keys still refused by name.
* The share scales the line once (and the look-through wage figure with it); assistance is deducted once afterwards; the gross and unrelated lines are untouched. Arithmetic is rounded to cents.
* Two partial shares never become a product or a minimum: exact only when one share is 0% or 100%; otherwise the guaranteed overlap is the priced floor and the range is disclosed.
* Contradictory statements (status `nonresident` with a share above 0, etc.) give 0 with a stated conflict, not a choice.
* **Assumed default.** Unstated shares on below-the-line crew / resident-labour lines are planned at 100% (the scenario rule of `scenario_local_labour`), derived on every load, never stored, labelled ASSUMED, removed by `scenario_btl_nonlocal`. Above-the-line roles and budget-classified non-resident labour are never defaulted (the project rule keeps their residency separately evidenced; this deviates from the instruction's blanket wording on purpose). The intersection field is never defaulted.
* **The assumption is NOT priced.** `eligible_usd` (stated evidence) is the only figure that reaches `ca_federal_pstc_qualified_labour_usd`; the assumption is a separate `planning_eligible_usd` served in the line-inputs view and the editor. Feeding it into pricing would put an unverified fact into a guaranteed floor and would change every project's fingerprint; threading an "assumed" tier through the pricing and trace layers (digest modules) needs separate authorization and is OPEN.

## Conservation and per-payee limits
* A person's cap share of a register entry is `allocated USD / line amount` (was `allocated USD / allocated total`, which made a partial allocation own the whole line). Allocated + remainder = line; a full allocation divides exactly as before.
* A line not fully allocated is not "decided": the remainder carries an UNRESOLVED note; no headcount, equal split, exemption or confirmed-uncapped amount is invented.
* Limit: the person's dollars are spread proportionally over the line's register entries (their qualifying and non-qualifying parts), as before; which dollars are theirs is not known.
* Retained-result caution: `per_payee_limits` is not digested, so a retained generation computed with the old arithmetic is not flagged stale. The audit found 0 allocation rows in all 7 `frametax2*` databases, so no real result changes.

## payee_type
`ny_producer_facts` no longer clears `payee_type` when allocations are saved or reset; it remains the line's own classification (the Canadian look-through reads it per line). Payee identity, completeness and the Montana person facts are still replaced by the people editor. The editor no longer hides the line's payee type once people exist.

## The 41 affected controls (8 files, test database `frametax2_pytest`)
Result: 0 passed, 41 failed, 41 blocked. Identical node set and identical result before (`93571b55`) and after; none is an implementation failure; none was run against real data.
* Cause: `PROJECT_NOT_FOUND` for all four anchor ids in the isolated database (probe: each id returns only `status`). The nodes hard-code the locked corpus.
* Source data is not available in a usable form: no local database holds a current-engine generation for any anchor. Highest retained engine version per anchor: acceptance DB `frametax2_claude_optimizer_acceptance_20260919` Bad Hombres 1.106.0, FVD 1.106.0, LLS 1.110.0, LU 1.109.0; `frametax2` 1.72.0; generic-discovery audit DB 1.84-1.86; codex audit DBs 1.64.0. Current is `canonical-1.130.0`. A current generation exists only by cold-evaluating a real production, which PROJECT_RULES (rule 1) forbids for test preparation and which cannot fit the 120/180-second command limits. Not done; defaulting, skipping or weakening is also not done.
* Exact missing IDs/access: `fa5cade5-0669-4816-bfe6-72146f8d3bae`, `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`, `4355ae88-a636-4c18-af60-ad73b2646124`, `ab10b319-978e-44d3-9331-af2a5f2cccc2` at `canonical-1.130.0` in a database the run is authorized for.
* Additionally 9 nodes in these files and 14 in the affected group are deselected by the repository's own real-anchor guard (needs `CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS`); not run, not counted as passes.

| # | Node | Failure | Disposition |
|---|---|---|---|
| 1 | `test_canonical_production_view.py::test_current_producer_projection_is_complete_and_preserves_exhaustive_optimizer` | KeyError: 'structures' | missing real-anchor data/setup |
| 2 | `test_canonical_production_view.py::test_co_pro_opportunity_status_and_conditional_user_fact_required_classification_are_the_same_rows` | KeyError: 'structures' | missing real-anchor data/setup |
| 3 | `test_canonical_production_view.py::test_relocation_candidates_never_outrank_the_baseline` | AssertionError: assert 'PROJECT_NOT_FOUND' == 'OK' | missing real-anchor data/setup |
| 4 | `test_canonical_production_view.py::test_every_structure_has_a_non_null_type_and_jurisdiction` | KeyError: 'structures' | missing real-anchor data/setup |
| 5 | `test_canonical_production_view.py::test_unpriceable_candidates_never_ranked_as_opportunities` | KeyError: 'structures' | missing real-anchor data/setup |
| 6 | `test_canonical_production_view.py::test_little_utopia_project_id_still_resolves_project_id` | KeyError: 'production' | missing real-anchor data/setup |
| 7 | `test_canonical_production_view.py::test_structure_labels_use_the_trimmed_producer_facing_jurisdiction_name` | KeyError: 'structures' | missing real-anchor data/setup |
| 8 | `test_canonical_production_view.py::test_optimizer_candidates_is_complete_never_capped_at_the_family_backstop_limit` | KeyError: 'structures' | missing real-anchor data/setup |
| 9 | `test_canonical_production_view.py::test_optimizer_candidates_deduplicated_by_economic_identity` | KeyError: 'structures' | missing real-anchor data/setup |
| 10 | `test_canonical_production_view.py::test_optimizer_candidates_scoped_to_priced_optimizer_families_only` | KeyError: 'structures' | missing real-anchor data/setup |
| 11 | `test_canonical_production_view.py::test_optimizer_candidates_sorted_by_ascending_verified_npc` | KeyError: 'structures' | missing real-anchor data/setup |
| 12 | `test_canonical_production_view.py::test_optimizer_candidates_carry_full_participant_and_component_detail` | KeyError: 'structures' | missing real-anchor data/setup |
| 13 | `test_canonical_production_view.py::test_optimizer_candidates_scoped_to_current_engine_generation` | KeyError: 'structures' | missing real-anchor data/setup |
| 14 | `test_canonical_production_view.py::test_optimizer_scenarios_no_longer_wrongly_collapses_the_fvd_manitoba_component_routing_differences` | KeyError: 'structures' | missing real-anchor data/setup |
| 15 | `test_canonical_production_view.py::test_optimizer_scenarios_never_collapses_a_materially_different_route` | KeyError: 'structures' | missing real-anchor data/setup |
| 16 | `test_canonical_production_view.py::test_optimizer_scenarios_total_equals_optimizer_candidates_total_when_no_genuine_duplicates_exist` | KeyError: 'structures' | missing real-anchor data/setup |
| 17 | `test_canonical_production_view.py::test_practicality_tier_classifies_two_jurisdiction_hybrids_as_practical` | KeyError: 'structures' | missing real-anchor data/setup |
| 18 | `test_canonical_production_view.py::test_practicality_tier_classifies_three_plus_jurisdiction_structures_as_advanced` | KeyError: 'structures' | missing real-anchor data/setup |
| 19 | `test_canonical_production_view.py::test_optimizer_scenarios_ordered_practical_then_formal_then_advanced_ascending_npc_within_tier` | KeyError: 'structures' | missing real-anchor data/setup |
| 20 | `test_canonical_production_view.py::test_workspace_headline_cards_favor_practical_over_advanced_for_fvd` | KeyError: 'structures' | missing real-anchor data/setup |
| 21 | `test_canonical_production_view.py::test_optimizer_scenarios_every_raw_candidate_is_accounted_for_exactly_once` | KeyError: 'structures' | missing real-anchor data/setup |
| 22 | `test_canonical_production_view.py::test_optimizer_candidates_untouched_by_scenario_grouping` | KeyError: 'structures' | missing real-anchor data/setup |
| 23 | `test_canonical_production_view.py::test_little_utopia_source_incentive_estimate_is_served_and_never_alters_gross_budget` | KeyError: 'pkg' | missing real-anchor data/setup |
| 24 | `test_canonical_production_view.py::test_fvd_source_incentive_estimate_is_served_and_never_alters_gross_budget` | KeyError: 'pkg' | missing real-anchor data/setup |
| 25 | `test_canonical_production_view.py::test_bad_hombres_has_no_fabricated_source_incentive_estimate` | KeyError: 'pkg' | missing real-anchor data/setup |
| 26 | `test_canonical_production_view.py::test_lips_like_sugar_ca_allocation_letter_is_canonical_project_evidence` | KeyError: 'facts' | missing real-anchor data/setup |
| 27 | `test_canonical_production_view.py::test_lips_like_sugar_program_version_safeguard_prevents_silent_repricing` | KeyError: 'facts' | missing real-anchor data/setup |
| 28 | `test_canonical_production_view.py::test_little_utopia_has_no_ca_program_version_caution` | KeyError: 'facts' | missing real-anchor data/setup |
| 29 | `test_canonical_scenario_participants.py::test_component_relocation_participants_include_the_routed_destination` | KeyError: 'structures' | missing real-anchor data/setup |
| 30 | `test_canonical_scenario_participants.py::test_bilateral_treaty_with_home_as_a_party_includes_home_in_participants` | KeyError: 'structures' | missing real-anchor data/setup |
| 31 | `test_canonical_scenario_participants.py::test_bilateral_treaty_between_two_other_candidates_excludes_home` | KeyError: 'structures' | missing real-anchor data/setup |
| 32 | `test_canonical_scenario_participants.py::test_multilateral_treaty_opportunity_includes_home_as_a_genuine_member` | KeyError: 'structures' | missing real-anchor data/setup |
| 33 | `test_canonical_scenario_participants.py::test_single_country_and_full_relocation_still_serve_exactly_one_participant` | KeyError: 'structures' | missing real-anchor data/setup |
| 34 | `test_canonical_scenario_participants.py::test_generated_participants_equal_persisted_trace_participants_cross_project` | KeyError: 'structures' | missing real-anchor data/setup |
| 35 | `test_canonical_scenario_participants.py::test_component_participants_exactly_equal_claiming_segments_not_merely_at_least_two` | KeyError: 'structures' | missing real-anchor data/setup |
| 36 | `test_canonical_scenario_participants.py::test_little_utopia_named_regression_structure_excludes_non_claiming_us` | KeyError: 'structures' | missing real-anchor data/setup |
| 37 | `test_canonical_scenario_participants.py::test_single_country_and_treaty_participants_unaffected_by_p0_2_fix` | KeyError: 'structures' | missing real-anchor data/setup |
| 38 | `test_canonical_scenario_participants.py::test_p0_part_001_non_claiming_primary_excluded_across_broader_corpus` | KeyError: 'structures' | missing real-anchor data/setup |
| 39 | `test_canonical_generation_freshness.py::test_fvd_and_lls_have_genuine_multi_fingerprint_history` | AssertionError: expected F#K Valentine's Day to have real multi-fingerprint history, got 0 | missing real-anchor data/setup |
| 40 | `test_canonical_generation_freshness.py::test_structure_and_package_views_reconcile_across_locked_corpus` | KeyError: 'production' | missing real-anchor data/setup |
| 41 | `test_canonical_generation_freshness.py::test_current_generation_fingerprint_is_the_single_shared_source` | AssertionError: 6c6f1c13-2d49-4bbc-bafb-2a12efa93112: expected a real current fingerprint | missing real-anchor data/setup |

Separate pre-existing finding (not among the 41, unchanged by this work): `test_canadian_labour_basis.py::test_assistance_reduces_eligible_labour` fails identically on the unmodified checkout. It asserts that CPTC assistance reduces labour, which engine 1.119.0 (RC4164) deliberately stopped doing; the assertion is obsolete. Not edited here (outside scope; `test_cptc_labour_basis_assistance_controls.py` encodes the current rule).

## Verification
* New backend controls 26/26; affected-path group (22 files): 312 passed, 1 failed (the obsolete assertion above), 14 deselected, plus 152 passed in the second half; frontend 519/519 (5 new).
* Browser (isolated stack: backend 8011 and Vite 5174 on `frametax2_pytest`, synthetic Missouri-home project, 100/169 page): typed 0 -> note "0% of this line = 0 USD (stated)", Save, cold reload shows STATED 0; typed 40 + 100 -> "40% of this line = 400,000 USD (stated)", Save, API and cold reload agree, labour basis 400,000 stated; Cancel restored 0 / blank and left Save disabled; payee type set to loan-out via the select, saved; on a Montana-pick structure a person (600,000 of 1,000,000, 400,000 shown not assigned) was added and saved: stored `allocations` row plus `payee_type=loan_out_corp` and both shares intact; Remove person + Save deleted the allocations row, `payee_type` and shares intact; back on the Canadian structure, Reset to scenario default on both shares + Save removed the rows, fields returned to ASSUMED 100%, payee_type intact. The synthetic project was deleted afterwards (`frametax2_pytest` again holds only "The Little Utopia"). UI status: IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION (not a self-certified acceptance; the independent protected preview is still required).

## Timeouts and retries
1 timeout: the combined 22-file affected group at 175 s (process stopped by the harness timeout). Split into two groups and re-run once: 24 s and 134 s, both completed. No identical command was repeated. Servers were stopped afterwards.

## Remaining items
* The 41 controls and the 214-control anchor inventory: blocked on current-generation anchor data (above).
* Pricing the assumed planning default (tiered ASSUMED fact through pricing and trace) - needs digest-module authorization.
* Per-person Canadian eligibility remains unsupported by design (line-level shares only).
* Locality sources and the other ledger obligations (unchanged).
* The live checkout needs `git pull`; the user's uncommitted edit of `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` overlaps the remote copy.

## Untouched
No real production id was opened, evaluated or regenerated; the acceptance database and `frametax2` were only read (engine-version inventory and anchor presence, read-only transactions). No rollout, backend restart of any shared server, ROW work, funds work or benchmark. Parked work untouched.
