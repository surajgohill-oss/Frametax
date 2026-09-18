"""
canonical_evaluation.py

THE canonical served evaluation runtime — Phase 2 cutover.

Supersedes `app/services/project_evaluation.py`'s run_full_analysis-backed
path (commit 87440df). bca893a proved that engine is the WRONG one for
served project economics: ENGINE_VERSION 0.1.0, zero references to any
canonical layer (program_spend_rules, program_rate_rules,
authority_coverage_registry, qualification_model, production_allocation,
allocation_pricing), and $1.12M off Little Utopia's accepted NPC when run
against its real budget.

This module builds NO new economics. Every calculation step is reused
byte-for-byte from the validated calculators; only the INPUT ASSEMBLY is
new, and only because it was previously hand-written per project
(`app/demo/little_utopia_state.py`) rather than derived from generic
persisted rows.

Pipeline:

    canonical_project_economics.build_project_economic_inputs()  (bca893a)
      -> derive_production_requirements() + discover_executable_jurisdictions()
         (Phase 6, already generic — app.calculators.production_discovery)
      -> per candidate (home baseline + discovered alternatives):
           derive_qualification_register()   (canonical, generic)
           derive_account_allocation()        (canonical, generic)
           price_allocated_structure()        (canonical, generic)
      -> rank_allocated_structures()          (canonical, generic)
      -> persist ProductionStructure / StructureCalculationResult
      -> one response shape, read back by _summarize_evaluation()

The exact two-pass rate-resolution pattern (register at rate=0.0 to get
a rate-independent QPE classification, then `resolve_program_rate` with
that QPE, then reprice at the resolved rate) and `program_territorial_text
=None` for any program without curated territorial-text evidence are both
reused unchanged from `app.demo.little_utopia_state
.build_alternative_jurisdiction_comparisons` / `qualification_model
.build_little_utopia_register_for_jurisdiction` — the established,
already-served pattern for the vast majority of Little Utopia's own
alternative-jurisdiction comparisons (only 3 of ~30 curate territorial
text; the rest already run with None).

Travel/FX/local-cost (MFNI) normalization ARE applied here, generically,
for every single-program and component-relocation candidate --
_relocation_normalization() connects the existing, real
production_normalization.py (travel_model.py + apply_fx_rates.py +
production_adjustment.py) using only real project figures (the
production's own travel budget line, its real gross budget, its real
jurisdiction codes) and that module's own documented, disclosed static
benchmark/snapshot defaults. The baseline candidate always yields an
exact-zero travel/local-cost delta by construction. in-kind replacement
remains 0.0 -- a genuinely absent generic capability (it names a real,
specific off-budget fact unique to Little Utopia, not a property every
production has), not a disconnected one.
"""
from __future__ import annotations

import functools
import itertools
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure, price_segment, rank_allocated_structures
from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    eligible_group_for_combination,
    load_named_pair_rule,
    price_program_group_stack,
)
from app.calculators.canonical_opportunity_bridge import (
    FACT_AUTHORITY_FACT,
    FACT_PROPOSED_CHANGE,
    FACT_USER_CONFIRMATION_REQUIRED,
    discover_cultural_test_gap_opportunity,
    discover_fee_cap_headroom_opportunity,
    discover_national_status_opportunity,
    discover_non_party_personnel_exception_opportunity,
    discover_potential_reinvestment_candidates,
    discover_qualification_gap_opportunity,
    discover_qualification_lever_opportunities,
    discover_service_to_national_treatment_opportunity,
    opportunity_to_dict,
)
from app.calculators.canonical_qualification_result import (
    QUAL_AUTHORITY_UNRESOLVED,
    QUAL_CURABLE_GAP,
    QUAL_HARD_FAIL,
    QUAL_NOT_APPLICABLE,
    QUAL_QUALIFIES,
    QUAL_RULE_DATA_INCOMPLETE,
    QUAL_SCRIPT_FACT_REQUIRED,
    QUAL_USER_FACT_REQUIRED,
    qualification_result_to_dict,
)
from app.calculators.canonical_role_qualification_bridge import (
    evaluate_role_qualification,
    role_attachment_facts_from_project,
    role_known_codes_from_project,
    script_facts_from_project,
    typed_personnel_facts_from_project,
)
from app.calculators import treaty_engine as te
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
    RESOLUTION_INELIGIBLE,
    evaluate_bilateral_coproduction_opportunity,
    evaluate_eurimages_coproduction_opportunity,
    evaluate_european_convention_coproduction_opportunity,
    evaluate_ibermedia_coproduction_opportunity,
    find_bilateral_treaty_pairs_among_candidates,
    find_eurimages_partners,
    find_european_convention_partners,
    find_ibermedia_partners,
    find_real_bilateral_partners,
    solve_bilateral_minimum_contribution,
)
from app.calculators.conditional_programs import conditional_nodes_for, node_to_dict
from app.calculators.production_allocation import (
    MOVABLE_COMPONENTS,
    StructureSpec,
    component_for,
    derive_account_allocation,
)
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import (
    derive_production_requirements,
    jurisdiction_capability_profile,
)
from app.calculators.qualification_derivation import derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.calculators.structure_compatibility import compatibility_to_dict, evaluate_structure_compatibility
from app.data.authority_coverage_registry import (
    PROVENANCE_DISCLOSURE_STATES,
    STATE_REASON,
    coverage_state,
    coverage_state as _coverage_state,
    economic_block_for_program as _economic_block_for_program,
)
from app.data.executable_jurisdiction_registry import get_doctrine as _get_doctrine
from app.data.program_rate_rules import (
    CONDITION_STATE_AUTHORITY_UNRESOLVED,
    CONDITION_STATE_EXECUTABLE,
    CONDITION_STATE_USER_FACT_REQUIRED,
    RATE_FAILURE_AUTHORITY_EXHAUSTED,
    RATE_FAILURE_NO_RULES,
    RateResolution,
    build_discovery_amount_probe,
    classify_rate_resolution_failure,
    resolve_program_rate,
)
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.services.canonical_project_economics import (
    FACT_STATE_UNKNOWN,
    ProjectEconomicInputs,
    build_physical_requirements,
    build_project_economic_inputs,
    production_facts_for,
)

# Global Priceability Optimizer Restoration: bumped so every project's
# persisted StructureCalculationResult rows are treated as stale and
# regenerated. No candidate-generation/allocation/pricing LOGIC changed in
# this file -- the version bump exists purely to invalidate cached results
# from before the authority_coverage_registry.py Georgia veto correction
# (georgia_eiia/us_ga_film_credit rows removed) and the canonical_program_
# identity.py jurisdiction_code binding fix, both of which are read at
# discovery time but are NOT part of `_compute_fingerprint(inputs)` (that
# fingerprint covers project-specific economic inputs, not registry
# contents) and would otherwise silently keep serving pre-fix results.
# Global Economic Data + Base Pricing, batch 1: 8 more programs promoted
# PARSED -> VERIFIED and their coverage vetoes removed (see authority_
# coverage_registry.py's correction note). Cache-invalidation bump only.
# Global Economic Data + Base Pricing, batch 2: sa_film_commission_rebate
# and si_cash_rebate promoted PARSED -> VERIFIED, coverage vetoes
# removed. Cache-invalidation bump only.
# CineGlobe canonical pricing path + discovery repair: candidate generation
# LOGIC changed (production_discovery.py now examines every independently
# registered (jurisdiction_code, program_slug) pair instead of collapsing
# to one program per code; this file's candidate loop consumes all of
# them, and every PRICED result now also carries a structured
# "adjustments" breakdown, plus a top-level "program_slug" trace field
# previously only present on unpriced/capability_only rows). Bumped so
# every project's persisted rows are regenerated under the corrected
# discovery/candidate universe and enriched trace shape.
# CineGlobe final-19 committee adjudication implementation: canonicalized
# the 19 final zero-evidence programs per the Claude research + Codex
# review (8 AGREE, 11 CORRECT) + Gemini delta confirmation (11/11
# CODEX_CONFIRMED) committee process. New/updated DoctrineRecords: India
# (in_national_film), New Zealand PDV (new_zealand_screen_production_
# grant_—_international_post_vfx), Peru CIPA (pe_film_incentive), Uruguay
# 2026 tax credit (uy_tax_credit_2026), Canada federal CPTC
# (ca_federal_cptc), Portugal RIPAC medium-budget track (pt_scri_pt_
# medium_budget, new sibling to the existing large-scale track), plus cap/
# tier corrections and confidence-tier promotions on ca_nl_all_spend_
# credit, ca_qc_pstc, and pt_scri_pt_cash_rebate. Coverage-registry vetoes
# removed for all of the above; qc_film_production/ca_nl_production_fund/
# pt_film_incentive bound as duplicate aliases; uy_xxi_incentive retired
# (SUPERSEDED); several stay non-guaranteed-selective/non-economic per the
# settled committee classification. Bumped so every project's persisted
# rows are regenerated under the corrected worldwide program universe.
# Cache-invalidation bump only: added missing jurisdiction_comparison.py
# capability profiles for India/Peru/Uruguay (jurisdiction_capability_
# profile() returns has_capability_data=False -> production_capable=False
# unconditionally when no profile exists at all, which was silently
# rejecting these three newly-doctrine-registered programs at the
# capability gate before they ever reached the priceable/incentive_ready
# classification -- discovery LOGIC unchanged, DATA gap closed).
# Existing Optimizer/Stacker Reconnection: additive multi-program
# candidate generation. Every jurisdiction with >=2 independently priced
# programs now ALSO gets a pairwise combined structure for any pair with
# an explicit named rule in app.optimization.stacking_rules.
# _SLUG_PAIR_RULES (canonical_stack_bridge.py). No existing single-program
# candidate is removed or altered. Bumped so every project regenerates
# under the new candidate universe.
# Same pass, corrected: grouping is by top-level COUNTRY prefix, not exact
# jurisdiction_code — federal programs discover under the bare country
# code (e.g. "CA") while provincial/state programs discover under a
# hyphenated code (e.g. "CA-BC"), so the real federal+provincial control
# case was silently generating zero combinations under exact-code
# grouping alone. eligible_for_combination() still refuses two different
# provinces/states. Bumped again so LU/FVD regenerate under the fix.
# Same pass: multi-program structures now carry the same UNKNOWN-
# territorial-fact disclosure their underlying single-program candidates
# already carry (previously silently dropped on the combined row).
# Existing Optimizer/Stacker Reconnection, continuation: N-way (3+)
# combinations now generated wherever EVERY pairwise sub-combination
# carries an explicit named rule (canonical_stack_bridge.
# price_program_group_stack, bounded per physically-coherent location
# group); alias reconciliation added so _SLUG_PAIR_RULES' legacy spellings
# (on_opstc, qc_film_production) resolve onto their current canonical
# slugs (ca_on_opstc, ca_qc_pstc) via the existing canonical_program_
# identity registry. A combined structure at the production's own home
# jurisdiction is now is_directly_comparable (Task 11) under the exact
# same is_baseline rule a single-program candidate already uses -- no new
# comparability concept. Bumped so LU/FVD regenerate under the richer
# combination universe.
# Ontario interaction repair: apply_stacking_adjustments._apply_spend_
# reduction now resolves direction via an explicit "reduces" field
# (canonical_stack_bridge._SPEND_REDUCTION_DIRECTION, sourced from each
# rule's own already-cited condition_text) instead of only the
# grant-type heuristic. on_ofttc+ca_federal_cptc (and qc_film_production/
# ca_qc_pstc+ca_federal_cptc) now correctly compute a real reduction
# instead of disclosing an unresolved-direction limitation. Bumped so
# every project's persisted multi_program rows regenerate under the
# corrected economics.
# Existing Optimizer/Stacker Reconnection, Task 7 — every PRICED
# structure (single-program and multi-program) now carries
# conditional_programs (conditional_programs.py's grants/funds layer) and
# conditional_compatibility (structure_compatibility.py's per-node
# verdicts). Discretionary/editorial opportunity data only — never
# entered into NPC. Bumped so every project regenerates with this field.
# Codex optimizer-correctness classification: (1) fail-closed publication
# — a combined structure is only generated when EVERY pairwise sub-
# combination resolves to a publishable rule type (allowed/mutually_
# exclusive/spend_reduction); a "conditional" (legal-review-required, no
# automatic resolution) or hypothetical "prohibited" pair now correctly
# refuses generation instead of silently publishing unresolved economics.
# (4) N-way order independence — price_program_group_stack now
# canonicalizes candidate/rule order before computing adjustments, so the
# result is provably identical under any input permutation (see
# canonical_stack_bridge.py and its permutation-invariance test). Bumped
# so every project regenerates under the corrected gating.
# Existing Optimizer/Stacker Reconnection, Task A — component/split.
# Additive: for each movable component (post/vfx/music) with real spend
# in the project's own budget, generates candidate structures that route
# that component to the top alternative jurisdictions using the existing
# production_allocation.StructureSpec "component_relocation" type and
# price_allocated_structure kernel unchanged. Bumped so every project
# regenerates with these new candidates.
# Existing Optimizer/Stacker Reconnection, Task B — treaty/official
# co-production opportunities. Additive: generates a real, registry-
# backed (never fabricated) bilateral or Eurimages multilateral
# CO_PRO_OPPORTUNITY structure for each real treaty/membership partner
# among this project's own discovered candidates, via canonical_treaty_
# bridge.py's fail-closed adapter over the existing treaty_engine.py.
# Bumped so every project regenerates with these new candidates.
# Existing Optimizer/Stacker Reconnection, Task C (hybrid/anchor) —
# treaty_coproduction structures now ALSO carry conditional_programs/
# conditional_compatibility (composing two independent relationship
# types: co-production + conditional fund, both reusing the exact same
# _conditional_data() every other structure type already uses). Bumped
# so every project regenerates with this composition.
# Reinvestment + Qualification Opportunity Optimization: every priced
# single-program candidate now carries `opportunities` (canonical_
# opportunity_bridge.py — fee/cap headroom, min-local-spend/min-total-
# budget qualification gaps, cultural-test gap disclosure), reconnecting
# the existing ProgramRequirementsProfile registry and inkind_
# contribution.py scenario model to the served path. Never entered into
# NPC/ranking. Bumped so every project regenerates with this field.
# Proactive Opportunity Discovery Reconciliation: `opportunities` now
# also carries proactive POTENTIAL_REINVESTMENT_OPPORTUNITY candidates
# (triggered by real budget-category totals, no known deal terms
# required — canonical_opportunity_bridge.discover_potential_
# reinvestment_candidates) and QUALIFICATION_LEVER opportunities (a real
# movable post/vfx/music budget amount that could close a real
# min-local-spend gap if relocated — discover_qualification_lever_
# opportunities). Both reuse only real, already-parsed budget-line data;
# neither enters NPC/ranking. Bumped so every project regenerates with
# these new candidates.
# Canonical Co-production Qualification Reconnection: repairs the first
# shared disconnect Codex's audit identified. Every priced single-program
# candidate now carries `role_qualification` (canonical_role_
# qualification_bridge.py, reusing cultural_qualification_model.py's real
# 24-program-slug registry, driven by this project's own real, persisted
# ProjectPerson/TalentProfile rows) -- disclosure only, never a pricing/
# admission gate. The bilateral and Eurimages treaty-opportunity blocks
# now read real coproduction_majority_pct/minority_pct/cultural_test_
# passed ProjectFact values instead of always passing None -- output is
# unchanged for LU/FVD (neither has these facts on file) but the
# plumbing is now real. Bumped so every project regenerates with these.
# Worldwide Qualification, Cultural Test + Official Co-production
# Completion: hr_cash_rebate's cultural_test_points corrected 34 (was
# None -- already documented in its own evidence note but never set);
# nz_spg_international newly confirmed spend-only (real NZFC citation).
# Both change downstream opportunity/qualification trace text for those
# two programs. Bumped so every project regenerates with the correction.
# Worldwide Program Qualification + Cultural Test Completion, batch 2
# (2026-08-19, same phase continued): 7 more program_requirements.py
# records corrected/completed with real primary-authority citations
# (gr_cash_rebate -- FVD's own home program -- cultural_test_points=50/
# threshold=20; ca_federal_pstc, us_or_opif, us_ny_post_production_credit
# confirmed cultural_test_required=False; de_dfff, nz_spg_international
# internal-consistency fixes; kr_kofic_location_incentive disclosure).
# canonical_role_qualification_bridge.py gains AUTHORITY_UNRESOLVED_
# PROGRAMS (mu_edb_incentive, fj_film_rebate) emitting the new
# QUAL_AUTHORITY_UNRESOLVED state with exact researched propositions,
# distinct from generic RULE_DATA_INCOMPLETE. Bumped so every project
# regenerates with these corrections.
# Worldwide Jurisdiction National/Cultural Status + Incentive Pathway
# Completion: fixed a genuine ca_federal_cptc defect (director/writer
# were both independently mandatory; CAVCO's real 10-point rule requires
# only ONE of the two -- alternative_group support added to cultural_
# qualification_model.py). New national_cultural_status.py registry
# (Canada/Australia/New Zealand confirmed separate national pathways,
# US confirmed no relevant regime, 24 more real countries AUTHORITY_
# UNRESOLVED with exact propositions) wired into canonical_opportunity_
# bridge.py's discover_national_status_opportunity(), disclosure-only,
# never fabricates economics. Bumped so every project regenerates.
# Final Worldwide Qualification + Cultural Status + Official Co-production
# Completion: national_cultural_status.py gains 3 more real confirmed
# jurisdictions (NL/SE via internal recovery, JP no-relevant) and a real
# correctness fix (Canada's CPTC/PSTC reclassified UNLOCKS_SEPARATE_
# INCENTIVE, was incorrectly UNLOCKS_ENHANCED_RATE) -- changes served
# opportunity trace text. Bumped so every project regenerates.
# Resume/finish Worldwide Qualification + Cultural + Official Co-pro:
# national_cultural_status.py gains 6 more confirmed jurisdictions
# (KR/PH/ZA/ES/CH/EE) with real economic-consequence detail, plus a new
# CoproductionCoverageStatus registry (Queue C) resolving 7 of the 13
# previously-uncovered countries. Changes served national-status
# opportunity trace text for these jurisdictions. Bumped so every
# project regenerates.
# Continuation from adc5cba (2026-08-19): Israel confirmed (Film Law
# 'Israeli film' definition, a real domestic national-content pathway);
# Taiwan-New Zealand co-production route confirmed via the ANZTEC treaty
# (Chapter 18); AE/SG/TW national-status residuals upgraded with
# additional real research; Queue D (KR/JP/PH bilateral route terms) now
# carries a per-partner partner_contribution_terms disclosure -- real
# terms found for Korea-Canada, explicit fail-closed markers for every
# other route rather than silent omission. Queue B's 21 program-
# qualification cultural-test residuals resolved: real, exact, primary-
# sourced point tables encoded for Austria/Germany/France/Czech Republic/
# Norway/Malaysia/Poland/Portugal; Belgium/Finland confirmed as genuinely
# different (non-point-table) real mechanisms; Cyprus's hard blocker
# upgraded to maximal diligence (the primary legal instrument itself read
# in full, all 36 pages, not merely secondary commentary). Changes served
# national-status and program-qualification trace text. Bumped so every
# project regenerates.
# Worldwide Qualification Consumption Closeout (2026-08-19): the 16
# programs Queue B resolved with real doctrine but which sat DISCONNECTED
# from the served role_qualification trace (RULE_DATA_INCOMPLETE despite
# real point-table/discretionary doctrine on file) are now consumed via
# two new registries (app.data.cultural_point_tables.CULTURAL_POINT_
# TABLES / DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS) dispatched through
# canonical_role_qualification_bridge.evaluate_role_qualification(),
# reusing the SAME project facts (role_known_codes) plus a new
# script_facts_from_project() query -- one consumption path, several
# accepted doctrine sources, zero new economics. Candidates' served
# role_qualification field now reflects QUALIFIES/HARD_FAIL/CURABLE_GAP/
# USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED for these
# 16 (+2 previously-mismarked-spend-only: fr_trip, it_tax_credit_foreign)
# instead of RULE_DATA_INCOMPLETE. Disclosure-only, as this bridge always
# has been -- LU/FVD NPC verified byte-identical. Bumped so every project
# regenerates.
#
# Consolidated Backend Correction, Part 19-20/21 (CBA-009): the
# contingency-category qualification ladder now scales projected QPE by
# a real, typed contingency_expected_utilization_pct fact instead of
# unconditionally including 100% of the reserve -- a genuine economic
# change (LU's own incentive/NPC change; see
# tests/test_contingency_expected_utilization.py and the updated LU
# baseline in tests/test_canonical_project_economics.py). Every project
# with a real contingency-qualifying category must re-evaluate rather
# than serve a stale pre-correction persisted result -- bumped so every
# project regenerates.
#
# 1.30.1: corrected the qualification-admission gate itself (see
# _QUALIFICATION_ADMITS_PRICING's docstring) -- CURABLE_GAP/USER_FACT_
# REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED/RULE_DATA_INCOMPLETE
# are priced and disclosed again (only HARD_FAIL blocks pricing),
# restoring LU's and FVD's own baselines to servable economics. Ranking
# is untouched by qualification state (governed by the pre-existing
# is_directly_comparable/is_fully_priced signals only). Bumped so every
# project regenerates under the corrected gate rather than the brief,
# over-broad 1.30.0 one.
# 1.30.3: Little Utopia's own established contingency-expected-
# utilization project election (100%) is now a real, persisted
# ProjectFact (alembic migration 0068) rather than an unset default --
# reproduces the historical accepted LU baseline through the fully
# generic pipeline. Bumped so LU regenerates under the corrected input.
# 1.31.0: Final Consolidated Backend Correction + Global Structuring
# Intelligence Acceptance, Part 4/CBA-001 -- reinstated the RECOMMENDED-
# ranking qualification gate (both here in _summarize_evaluation's
# top_result selection and in canonical_production_view.py's comparable
# pool): a candidate whose qualification is genuinely unresolved can be
# priced and disclosed but never presented as the recommended winner,
# even when that means a project has no Recommended scenario at all.
# Bumped so every project regenerates under the corrected gate.
# 1.31.1: CBA-008 -- _compute_fingerprint() now also covers personnel
# (role_known_codes), screenplay (script_facts), co-production facts, and
# registry/table knowledge versions, not only budget/territorial/
# contingency inputs. The fingerprint ALGORITHM itself changed (not just
# a project's own data), so bumped here too -- otherwise old-fingerprint
# rows from before this change would sit alongside new-fingerprint rows
# under the SAME engine_version, both matching a same-engine_version-only
# query and silently double-counting/conflating two different evaluation
# generations.
# 1.32.0: Part 4/CBA-004 -- typed_personnel_facts_from_project() (the
# SEPARATE nationality-vs-residency breakdown) is now genuinely wired
# through to evaluate_point_table_qualification, which can consult it for
# any CATEGORY_ROLE criterion whose fact_kind is NATIONALITY or RESIDENCY
# specifically (default EITHER preserves prior behavior for all 13
# currently-encoded tables). Bumped so every project regenerates under
# the corrected, typed-fact-aware qualification path.
# 1.33.0: Part 3/CBA-006 -- European Convention and Ibermedia multilateral
# co-production opportunities (canonical_treaty_bridge's two new
# adapters, reusing treaty_engine.py's own real eligibility functions
# unchanged) now generate real, disclosed treaty_coproduction candidate
# structures, the same fail-closed pattern already proven for Eurimages.
# Also the real backing for Gemini P0 pattern SP_001. Bumped so every
# project regenerates and picks up the two new opportunity structures.
# 1.34.0: Gemini P0 patterns SP_002 (service->national-treatment
# arbitrage) and SP_004 (non-party personnel exception) now surface as
# real, disclosure-only opportunities on any candidate that trigger-
# matches a real registered treaty (canonical_opportunity_bridge's two
# new discover_* functions). Bumped so every project regenerates.
# 1.35.0: OH-001 fix (CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT) -- rows
# persisted at 1.34.0 (2026-08-20) predate several result-affecting
# changes that landed WITHOUT a version bump: combined-structure
# qualification propagation (b245f1b), BC DAVE/AU PDV canonical recovery
# (9d0266b), NY's 60% Production Plus ceiling tier, and the corrected
# provenance/economics separation policy (6b44973) -- none of which
# touched the fingerprint's OLD, incomplete dependency manifest, so those
# pre-change rows kept matching as "current" indefinitely. Two real
# fixes land together here: (1) this bump immediately invalidates every
# row from before this correction, forcing a fresh recompute on next
# request; (2) _compute_fingerprint() now also covers authority-coverage,
# provenance, spend-rule, stacking, treaty, structuring-pattern,
# executable-registry, and role-qualification-bridge versions, so a
# FUTURE change to any of those needs only its own version bump, not a
# manual ENGINE_VERSION edit, to correctly invalidate cached rows.
# 1.36.0: LU Co-Pro Opportunity Trace fix -- bilateral co-production
# opportunity discovery previously only considered a treaty where the
# production's own home/service jurisdiction was one of the two parties
# (find_real_bilateral_partners(home_code, ...)), wrongly treating the
# current shoot/service location as a required treaty party. A new,
# generic loop (find_bilateral_treaty_pairs_among_candidates) now also
# considers real registered treaties between two OTHER genuine candidate
# jurisdictions (e.g. matching creative-personnel nationalities), with the
# SAME fail-closed eligibility adapter -- never a new ontology, never an
# LU-specific branch. New calculation_trace_json fields
# (coproduction_partners with two real parties instead of one,
# location_independent_of_service_jurisdiction) mean this is also a SHAPE
# change, not only a candidate-generation change -- bumped for both
# reasons, per this constant's own established convention.
# 1.37.0: Co-Pro Conditional Pricing Bridge -- an UNRESOLVED_FACTS
# bilateral treaty opportunity now attempts a real conditional scenario:
# solve_bilateral_minimum_contribution() derives the treaty's own
# deterministic minimum contribution split, evaluate_bilateral_
# coproduction_opportunity() re-checks eligibility with that solved
# split, and every unlocked program slug with real canonical rate data
# is priced through the SAME _price_candidate() every ordinary candidate
# uses -- no separate co-pro pricing math. Purely additive
# ("conditional_scenario" trace field); never changes candidate_status,
# is_directly_comparable, or ranking eligibility. New calculation_trace_
# json field on every treaty_coproduction structure -- a shape change,
# bumped per this constant's own established convention.
# 1.38.0: Co-Pro Conditional Pricing Bridge, stacking-correctness follow-
# up -- when a single treaty party's unlocked slugs land in the SAME
# jurisdiction (e.g. a majority country unlocking two of its own
# programs), the conditional total is now computed through the EXISTING
# price_program_group_stack()/eligible_group_for_combination() stacking-
# compatibility engine instead of a hand-built sum -- same engine every
# ordinary multi-program candidate group already goes through. Cross-
# jurisdiction totals (majority vs minority country, the normal bilateral
# shape) are unaffected -- those remain a direct sum of independent
# national incentives, not a same-jurisdiction stacking question. New
# "stacking_groups" trace field when a same-jurisdiction group was
# evaluated -- a shape change, bumped per this constant's own established
# convention.
# 1.39.0: Co-Pro Conditional Pricing Data Reconnection -- three real
# wiring/data fixes to the conditional bilateral pricing loop, no new
# engine: (1) au_producer_offset materialized as an executable RateRule
# from already-cited canonical knowledge (national_cultural_status.py),
# priceable ONLY through this conditional path, never ordinary
# discovery; (2) treaty-unlock slugs are now resolved through the
# existing canonical-slug alias table before pricing (fixes "nz_spgi" vs
# the already-canonical "nz_spg_international" -- a real identity
# mismatch, not a data gap); (3) ca_cmf/fr_tax_credit_cinema/fr_cnc_
# production confirmed genuinely non-formulaic (competitive, recoupable
# funds -- see fund_economics_model.py/authority_coverage_registry.py)
# and deliberately left as disclosed CANONICAL_DATA_GAP/legitimate
# partials, not "fixed". No new pricing math, no new eligibility
# doctrine. conditional_scenario's priced_components/canonical_data_gaps
# values change for affected treaties -- bumped per this constant's own
# established convention.
# 1.40.0: Fresh Project Budget Normalization -- non-unique account code
# support. Root cause: derive_account_allocation's own duplicate
# detection keyed on account_code, a CLASSIFICATION field a real budget
# may legitimately reuse across distinct lines (e.g. Lips Like Sugar's
# real "4900" on both a Total Fringes line and a Main and End Titles
# line) -- the second line sharing a code was silently dropped from
# assignments entirely, breaking conservation and blocking every
# candidate from pricing. Fix: BudgetLine gains a genuine per-line
# identity (line_id, default-generated, real DB primary key threaded
# through on the live ingestion path) and derive_account_allocation now
# dedups by line_id, never account_code -- account_code remains pure
# classification. AccountAllocation also gains line_id for full
# downstream source traceability. No behavior change for any budget
# without a repeated code (every existing production's dedup outcome is
# unchanged); this bump exists only to force a fresh, correctly-
# conserving allocation/pricing recompute for any project whose budget
# does carry a repeated code -- bumped per this constant's own
# established convention.
# 1.41.0: Fresh Project Economic Fidelity -- a real budget-parser rebate-
# exclusion gap. _REBATE_EXCLUSION_RE already excluded "tax credit"/
# "incentive rebate"/"EDB rebate"/"net total" style netting lines (budget
# assumptions, not real spend) but did not match "tax incentive" (e.g.
# Lips Like Sugar's own "9998 - Tax Incentive 25%* BTL (No Disc)"
# ($1,503,074) netting line ahead of its stated "Net total"). That line
# was being parsed as a real, negative, QUALIFIES-eligible BTL account,
# allocated as spend to whichever jurisdiction a candidate priced, and
# subtracted directly from that jurisdiction's QPE -- a real $1,503,074
# QPE/incentive/NPC distortion, not a data-quality fact. Fixed generically
# by adding "tax incentive" to the existing exclusion pattern (same
# semantic family already covered, no project-specific string). Confirmed
# no other current production (Bad Hombres/LU/FVD) has any line
# containing "incentive" -- zero collateral effect. Leaf-line count for
# Lips Like Sugar changes 47 -> 46; leaf-line sum now equals the source
# document's own stated Grand Total exactly ($11,983,654.00, previously
# $10,480,580.00 -- a discrepancy this fix removes rather than papering
# over). Bumped per this constant's own established convention.
#
# canonical-1.42.0 (CineGlobe economics + wiring integrity repair): three
# SEMANTIC pricing/trace changes that persisted rows cannot be allowed to
# outlive, so the version bump is what invalidates and recomputes them:
#   * cluster 6 -- a lone band-ceiling tier no longer becomes a guaranteed
#     floor rate; an unconfirmable "up to X%" fails closed
#     (allocation_pricing._price_segment / program_rate_rules.
#     resolve_program_rate has_guaranteed_floor);
#   * cluster 7 -- canonical dollar caps (per_project_cap_usd,
#     annual_cap_usd) now clip the incentive after base x rate, with an
#     auditable uncapped/cap-type/capped trace;
#   * cluster 11 -- trace provenance stops claiming EXPLICIT_STATUTE for
#     lines included by canonical default. The inclusion is unchanged; the
#     basis is now DEFAULT_INCLUDE_NO_EXCLUSION (and CLOSED_LIST_OMISSION
#     for the closed-list mirror), so an auditor can tell "the authority
#     expressly says this qualifies" from "nothing excludes it".
# Note the authority gate (cluster 1) invalidates independently via
# AUTHORITY_COVERAGE_REGISTRY_VERSION, which the input fingerprint already
# includes.
#
# canonical-1.43.0 (cluster 2): mandatory eligibility now GATES deterministic
# pricing. ProgramRequirementsProfile facts (local entity, minimum spend,
# minimum shoot days, discretionary/competitive allocation) were consumed as
# confidence metadata only; a missing mandatory fact is not a satisfied one.
# Computable thresholds are evaluated against this production's real figures;
# facts the budget cannot decide are UNKNOWN and condition the result;
# administrative process steps are disclosed but never gate. See
# canonical_requirements_gate_bridge.py.
# canonical-1.43.1: the cluster-2 requirements gate is DISCLOSURE-ONLY. An
# intermediate 1.43.0 state blocked on unresolved local-entity/allocation-type
# facts and persisted those blockers; that reading removed Little Utopia's own
# baseline and 34 other accepted results, which cluster 10 forbids. The bump
# invalidates those rows so the disclosure-only behavior actually reaches the
# served output.
# canonical-1.44.0 (cluster 8): a mutually exclusive combination is no longer
# emitted as a PRICED structure (it is retained as an explicit RULE_REJECTED
# incompatibility diagnostic), and a valid combined structure now carries
# reconciled per-program segments and a real total QPE instead of segments=[]
# with total_qualifying_spend_usd=0 beside a non-zero incentive.
#: Optimizer P0 wiring remediation (2026-09-04): bumped for P0-3 — treaty
#: conditional bilateral pricing (_build_conditional_bilateral_scenario)
#: now allocates ONE source budget across majority/minority participants
#: instead of independently pricing the full gross budget in each,
#: changing served conditional_incentive_usd/conditional_npc_usd/
#: fully_priced/participant_allocation_pct for every persisted
#: treaty_coproduction row with an UNRESOLVED_FACTS bilateral opportunity
#: (confirmed live: FVD/Bad Hombres/Lips Like Sugar each have hundreds of
#: such rows). A pure code change with no fingerprint-input difference —
#: without this bump, evaluate_project's own existing-row reuse check
#: would keep serving the OLD, double-counted trace_json forever.
#: Optimizer FINAL closeout (P1-REJ-001): bumped again — component-
#: relocation generation now PERSISTS a disclosed, never-priced reject
#: row for every threshold-failed (component, target) attempt instead of
#: silently `continue`-ing past it. This changes the SET of
#: StructureCalculationResult rows a given fingerprint produces (889 new
#: rows in the current corpus) with no change to any existing priced
#: candidate's own economics — a pure persistence-SHAPE change, exactly
#: like the "1.1.0 segments addition" case this file's own
#: current_result_fingerprint() docstring already documents. Without this
#: bump, every current fingerprint's existing-row reuse check would keep
#: serving the OLD row set — the new reject rows would never be created
#: for any project already evaluated under 1.53.0.
# Codex global optimizer audit P0 remediation (P0-CAND-001/002/003,
# P0-QUAL-001, P0-STACK-001, P0-COMB-001, P1-CLASS-001, P1-TRACE-001):
# bumped so every previously-cached StructureCalculationResult row (all
# generated under the pre-remediation candidate/fact/stacking/topology
# logic) is treated as stale and regenerated fresh on next evaluation,
# never silently served as EVALUATION_REUSED under the corrected engine.
#
# CLAUDE_D743_REJECTED_FINDINGS_REMEDIATION: bumped again -- P0-COMB-001's
# treaty-side allocation (real evidenced contribution-share account_splits,
# every movable component + every target enumerated, stacks on every
# allocated side) and P1-TRACE-001's exact line-level union replaced the
# d743fab implementations Codex's acceptance audit rejected. Every row
# persisted under 1.55.0 reflects the REJECTED behavior and must never be
# served as current under the remediated engine.
#
# PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING: bumped again --
# official co-production treaty eligibility now additionally consumes a
# real, confirmed-vs-unconfirmed creative-personnel gate
# (treaty_engine.PersonnelRequirement + canonical_role_qualification_
# bridge.evaluate_treaty_personnel_gate), and CoproOpportunity carries
# new served fields. Every row persisted under 1.56.0 was generated
# without this gate ever being consulted and must be treated as stale.
ENGINE_VERSION = "canonical-1.82.0"  # 1.82.0: OPTIMIZER_AUDIT_DEFECT_REMEDIATION (2026-09-18), fixing CURRENT_TIP_OPTIMIZER_NUMERICAL_ACCEPTANCE_AUDIT.md's NUM-001..NUM-005, resumed at e880c44. Bumped because both the persisted trace shape and the served workspace contract changed, never because any priced economics changed (all four baseline incentive/NPC figures are confirmed byte-identical before/after). NUM-001: project_workspace_view.py's `top_result = comparable[0]` published a priced-but-genuinely-unresolved baseline (Little Utopia/F#K Valentine's Day) as the served recommendation, contradicting evaluate_project()'s own top_result=null -- fixed by extracting the ONE canonical qualification-admission predicate (new public qualification_admits_recommended(), previously three independent copies: this file's own _summarize_evaluation() closure, canonical_production_view.py's module function, and NONE in project_workspace_view.py) and consuming it from the workspace adapter, never re-implementing a fourth. NUM-002: hybrid (ordinary_component_hybrid) rows never called the SAME per-program discretionary/administrative disclosure helper the single_country/multi_program/component_relocation families already use -- structural_archetype_generator.StructuralCandidateResult now carries administrative_allocation_risk/administrative_allocation_risk_reasons, derived from EVERY component program via _competitive_allocation_disclosure, computed once in generate_structural_candidate() and persisted at both real ordinary_component_hybrid trace sites (the priced-candidate row and its own DOMINATED_WITH_PROOF aggregate is intentionally excluded -- that row has no single priced candidate's economics to attach). NUM-003: apply_stacking_adjustments()'s own StackingAdjustmentResult (raw_values, adjustments, program_values -- already fully computed inside generate_structural_candidate()) was discarded after only its aggregate total was kept; now persisted in full (raw_component_incentives_usd, stacking_adjustments, post_adjustment_component_incentives_usd) so an adjusted hybrid total reconstructs exactly from the trace alone. NUM-004: both DOMINATED_WITH_PROOF trace builders (ordinary_component_hybrid and combined_coproduction_multi_component_stack) now persist the numeric proof itself -- component_cutoff_bounds_usd, component_window_best_usd, an interaction-safe total upper bound (conservative independent-maxima single-component-substitution bound), incumbent_value_usd, and an explicit stopping_inequality/stopping_inequality_holds -- without altering the existing widening-search/stop decision in any way. NUM-005: project_workspace_view.py's evaluation block now returns engine_version/input_fingerprint (evaluate_project()'s own top-level response already did). Supporting validator correction: scripts/canonical_integrity_gate.py's QPE check no longer sums claim-specific qpe_usd across segments and compares to gross budget (a stale oracle -- lawful stacked programs, e.g. Ontario CPTC+OFTTC, correctly share the identical eligible-cost base, so summing produced false positives); replaced with per-segment non-negativity plus a real source-line disjoint-routing check across DIFFERENT components via component_allocations[].line_ids.
# 1.81.0: structural-optimizer wiring correction pass, resumed at ba76cd2f. Corrects three real defects in the six-control closeout above (1.80.0), each a genuine economic-behavior change, never a cosmetic one. HO-013: REMOVED the arbitrary _MULTI_COMPONENT_TARGET_BOUND=200 flat cutoff, which sliced the SAME global, component-AGNOSTIC _combined_top_targets list for every routed component -- a real doctrine violation, since a genuinely component-specific real candidate ranked below 200 in the GLOBAL ranking could be silently excluded even while ranking near the top of its OWN component's real list. Replaced with (1) _hy_component_all_targets[component] -- the SAME real, independently-priced-per-component candidate list the pre-existing ordinary_component_hybrid mechanism already builds via _price_component_relocation_candidate, and (2) a genuine pigeonhole-exchange proof-based widening search (window starts at 2, the proven-sufficient size for 2 simultaneously-routed components, and doubles on failure until a real PRICED combination is found or every real candidate is exhausted), mirroring the SAME proof pattern canonical-1.72.0 already established elsewhere in this file. Runtime dropped from ~36s to ~3s on the real HO-013 fixture as a direct consequence (small, real, component-scoped lists vs. an arbitrary flat 200-candidate slice). HO-012: REVERTED from PRICED to an explicit RULE_REJECTED. Direct primary-authority verification found the prior pass's "each Eurimages co-producer independently accesses its own national incentive" pricing basis unsupported: treaty_engine.py's own eurimages-multilateral TreatyData carries EMPTY majority_unlocks/minority_unlocks (the codebase's own structured, authoritative "this treaty unlocks these specific programs" fields, populated with real slugs for every bilateral treaty) -- only fund_unlocks=["eu_eurimages"] (the fund itself, not each party's own program) is populated. The sole textual support was an uncited free-text `notes` field (confidence_tier="PARSED", no citation field -- contrast TreatyData.non_party_personnel_exception_citation, which DOES exist and IS populated for individually-researched propositions elsewhere in this same dataclass). Real subset-eligibility discovery (participant count, per-party minimum contribution share, cultural test) remains intact and disclosed; only the unsupported pricing claim is removed, persisting RULE_REJECTED/MULTILATERAL_NATIONAL_TREATMENT_UNVERIFIED instead. HO-011: reconciled the two conflicting authority_coverage_registry.py registries AT THEIR SOURCE instead of papering over the disagreement at the consumer site. Direct verification found program_rate_rules_worldwide.py's US_TN_DOCTRINE carries a real, VERIFIED-tier, officially-cited (tn.gov) RateRule -- a single unconditional flat-25%-of-QPE tier, structurally identical in kind to the 18 programs this same file's own changelog already documents removing from _B1_DISCRETIONARY_RULING as "genuinely misclassified as authority-exhausted" -- us_tn_performance_grant was evidently missed by that pass. Removed from _B1_DISCRETIONARY_RULING this pass (AUTHORITY_COVERAGE_REGISTRY_VERSION 1.8.0 -> 1.9.0), which is what actually caused the disagreement the prior pass's consumer-side _capability_only_status() workaround was only papering over; that workaround is removed in the same pass (reverted to its original, simpler form), since the disagreement it existed to disclose no longer exists. us_tn_performance_grant now prices normally (confirmed: $750,000.00 = 25% of $3,000,000 QPE) and participates in the full discovery pipeline (standalone, component_relocation, and structural_archetype_generator paths alike), not a special case. HO-003 and HO-010 needed no code change: direct re-verification found HO-003's literal required target ({uk_avec, au_producer_offset, NZ's international-post-vfx grant}) already reaches an EXACT PRICED match ($1,939,600.00) -- the prior pass's own CSV evidence had simply cited a different, non-literal illustrative example (Uzbekistan) instead of the literal target, a documentation defect, not a code gap, now corrected in the ledger and the prevention test. HO-010's standalone Creative Saskatchewan identity reconciliation (canonical-1.80.0) remains correct and unchanged; both authority registries independently confirm the program is a real, confirmed DISPLAY_ONLY_ZERO_GUARANTEED discretionary award that can never enter priced_by_code, so the FULL 3-program required control is honestly relabeled COMPONENT_BLOCKED_NOT_CANONICALLY_EXECUTED rather than a false full-control verification claim. Invalidates every cached row so this fires fresh.
# 1.80.0: six-control closeout (HO-003, HO-007, HO-012, HO-013, HO-010, HO-011) -- closes the acceptance gap left by 1.79.0's honest-but-incomplete MULTI_PRINCIPAL_PARTIALLY_RESOLVED/MULTI_PRINCIPAL_DEFERRED/GRANT_COMPONENT_UNWIRED_DEFERRED dispositions. HO-003: the binding doctrine ("ranking must never suppress feasible discovery") was being violated by _best_priced_treaty_side_candidate(), which picked ONE overall-best-priced partner program per jurisdiction rather than enumerating every treaty-valid unlock. New _all_priced_treaty_side_candidates() enumerates every program in a treaty's real minority_unlocks/majority_unlocks that independently prices (never inventing one outside the registered unlock list), and the home-anchored/non-home-anchored bilateral loops now iterate every returned candidate instead of a single winner -- _combined_top_targets was likewise flattened from one-best-per-jurisdiction to every-candidate-per-jurisdiction so two genuinely different real programs for the same jurisdiction (e.g. NZ's international-post-vfx grant vs nz_spg_international) can each be reached. This produces the exact literal HO-003 target {uk_avec, au_producer_offset, nz international post/vfx}: PRICED, $1,939,600.00 total incentive on a $7.5M budget. HO-007: the enumeration fix surfaces, for the first time, an explicit per-unlock RULE_REJECTED (NO_PRICEABLE_TREATY_UNLOCK) whenever a treaty's real minority_unlocks contains zero independently-priceable programs, citing each unlock's real authority_coverage_registry/program_rate_rules status -- applied to the real, registered uk-fr-bilateral treaty, whose real minority_unlocks are fr_tax_credit_cinema/fr_cnc_production, never fr_trip (confirmed via direct treaty_engine.py query, not assumed); this control's own literal fr_trip target is therefore a corrected-target RULE_REJECTED, not a forced PRICED. HO-013: new _price_combined_coproduction_multi_component_candidate() generalizes the existing single-component combined-co-production kernel to N>=2 simultaneous movable components with disjoint cost pools (account_splits excludes the union of every routed component's spend_category, never double-counted), wired as a new discovery pass over itertools.combinations of the production's real movable components x itertools.product of every per-component target candidate (bounded by a disclosed _MULTI_COMPONENT_TARGET_BOUND=200 practical search cap, this codebase's own precedented safety-limit pattern, never a doctrine choice); reaches the exact literal HO-013 4-program target {uk_avec, au_producer_offset, nz international post/vfx, OCASE}: PRICED, $2,046,160.00 total incentive on an $8M budget. HO-012: new _price_combined_multilateral_coproduction_candidate() (N-party multilateral generalization of the existing pair kernel, sharing every account across all N real evidenced participant percentages, normalized to sum to 1.0) plus new _real_multilateral_subset_participants() (reads the simpler, treaty-scoped coproduction_participant_pct::{treaty_slug}::{code} fact key rather than requiring a percentage fact for every one of Eurimages' ~37 member states, which made the pre-existing full-membership multilateral mechanism architecturally unreachable for a producer-intended specific N-party structure) together let a real 3-party Eurimages-eligible production reach the exact literal HO-012 target {fr_trip, uk_avec, ie_section_481} -- fr_trip IS a real, valid unlock here because Eurimages is a genuine, separately-registered multilateral fund route distinct from the bilateral UK-France treaty HO-007 depends on, confirmed via direct treaty_engine.py TreatyData reading, not assumed: PRICED, $2,476,080.00 total incentive on a $9M budget. HO-011: _capability_only_status() now checks _economic_block_for_program() (the OLDER, separate authority_coverage_registry.py block dict) before trusting a PRICEABLE_VALIDATED read from the newer coverage_state()/blocks_economic_candidacy() registry, because the two registries were found to genuinely disagree for us_tn_performance_grant and resolve_program_rate() empirically still honors the older block -- this disagreement is a real, disclosed, UNRESOLVED data-integrity gap between the two registries (not fixed this pass, a separate reconciliation project), but the persisted rejection reason now names it explicitly rather than silently returning a misleadingly-optimistic status: UNPRICEABLE_AUTHORITY_INSUFFICIENT/FAIL_CLOSED. HO-010: new canonical_program_slug field on conditional_programs.py's ConditionalProgramNode (plus _CANONICAL_SLUG_BY_NODE_ID reconciliation table, one verified entry so far: Creative Saskatchewan's catalog node -> ca_sk_creative_saskatchewan_grant) bridges the previously-separate conditional-discovery catalog identity and the priceable program_slug rate registry; the single-program capability_only branch now also calls the pre-existing _conditional_data() helper (previously only wired for combined/treaty structure types) so this reconciliation is actually visible on a real persisted structure's conditional_programs/conditional_compatibility disclosure -- disposition remains the real, pre-existing FEASIBILITY_REVIEW_REQUIRED/AUTHORITY_UNRESOLVED_NON_PRICEABLE (never a fabricated fund_overlay component; a genuinely disjoint real second budget line for one would need to be invented, which the explicit no-guessed-allocations constraint forbids), now confirmed via direct query to be a real, reconstructable, non-silently-omitted disposition rather than an unverified DEFERRED claim. Reinvestment/gross-up remains shelved throughout, per explicit instruction. Invalidates every cached row so this fires fresh.
# 1.79.0: eight-control closeout, multi-principal pairwise co-production (REG-4; HO-003/007/013's own pairwise treaty leg) -- confirmed via direct code reading (never assumed) that every EXISTING combined-co-production pricing path in this file (_price_combined_coproduction_component_candidate, both the home-anchored and non-home-anchored loops) unconditionally required a THIRD movable-component target alongside the two treaty parties, so a pure 2-program co-production (a jurisdiction's own national program + its real treaty partner's own national program, no third program) could never be reached even when a real, registered bilateral treaty and real, evidenced majority_pct/minority_pct contribution facts existed for the pair. New _price_combined_coproduction_pair_candidate() is the direct sibling of the existing 3-way function with the routed component omitted: it applies the SAME real, evidenced (never invented) treaty contribution facts as an explicit spec.account_splits entry across every non-memo account (derive_account_allocation's own highest-precedence rule), reusing price_allocated_structure unchanged. Wired into the SAME home-anchored bilateral loop, immediately after the existing 3-way block, gated only on RESOLUTION_ELIGIBLE (never on whether the production happens to have movable post/vfx/music spend to route). This closes the real gap for GB-AU (uk-au-bilateral, unlocks uk_avec/au_producer_offset) and GB-IE (uk-ie-bilateral, unlocks uk_avec/ie_section_481) -- both real, already-registered treaties this codebase's own treaty_engine.py data already carried, confirmed via direct query, never newly researched. Two simultaneous principal_production legs is exactly the shape structural_archetype_generator.py's own generate_structural_candidate already accepted (confirmed by HO-003's own pre-existing direct-generator test); this fix is the missing REAL-runtime allocation source for that shape. Does NOT (this pass) layer authorized-local-stack composition onto either side of the pure-pair candidate, a disclosed scope reduction from the 3-way block's own richer treatment. HO-012 (three SIMULTANEOUS principal legs, fr_trip+ie_section_481+uk_avec) remains a genuine, confirmed gap: IE-FR has no registered bilateral treaty in treaty_engine.py (confirmed via direct query), so no pairwise or transitive treaty basis exists to combine all three without inventing a split -- carried forward, not forced. Invalidates every cached row so this fires fresh.
# 1.78.0: eight-control closeout, REG-5 cost-pool-aware same-jurisdiction pricing -- the location_groups same-jurisdiction group-stack bridge could never price a registered same_cost_prohibited_distinct_costs_allowed pair (e.g. NY's ny_state_film principal credit + us_ny_post_production_credit post credit) because price_program_group_stack's StackCandidate objects are each priced against the WHOLE budget, so naively combining two would double-count the same dollars -- exactly what the rule prohibits. New _try_cost_pool_aware_same_jurisdiction_stack() prices each program against its own REAL, disjoint cost pool instead: it identifies whichever program carries a genuine CLOSED_POSITIVE_LIST of eligible spend categories (never guessed from doctrine alone), partitions the anchor's real per-line AccountAllocation rows into two disjoint pools by each row's own real spend_category (a strict partition of one real tuple, so a line_id can never appear in both pools -- the same same-cost-refusal-by-construction principle structural_archetype_generator.py already uses for movable components), and prices each pool independently via the existing price_segment() partial-register kernel -- never a new pricing path. Only persists PRICED when BOTH pools independently clear their own program's real threshold/rate resolution; otherwise persists a specific, reconstructable RULE_REJECTED (COST_POOL_EMPTY or COST_POOL_MEMBER_UNPRICEABLE), never a fabricated partial result. REG-5 is the only control this pass targets in canonical_evaluation.py itself; multi-principal composition (HO-003/007/012/013, REG-4) and grant/selective-component wiring (HO-010/011) are addressed separately -- see CAPABILITY_LEDGER.md and the 19-control reconciliation CSV for their own disposition. Invalidates every cached row so this fires fresh.
# 1.77.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, REG-5 same-jurisdiction component-exclusion fix -- the ordinary_component_hybrid loop's movable-component target filter unconditionally excluded the anchor's own jurisdiction (t.jurisdiction_code != _anchor_code), which was right for a same-cost/same-program conflict but wrong for a registered same_cost_prohibited_distinct_costs_allowed pair (e.g. NY's ny_state_film principal credit + us_ny_post_production_credit post credit): generate_structural_candidate's own same-cost-by-shared-line_id refusal already makes double-claiming impossible, so this rule type is explicitly non-blocking at that layer (structural_archetype_generator.py's own check_all_pairs). Confirmed via direct instrumentation that us_ny_post_production_credit already appears as a real, independently-priced "post" target in _hy_component_all_targets -- only the anchor-jurisdiction filter was removing it when the anchor was ALSO US-NY. New _hy_same_jurisdiction_distinct_cost_allowed() carves out exactly this one registered rule type; also corrected the prior 1.76.0 fix's own same-jurisdiction group-stack rejection label, which had been calling this exact rule type "UNRESOLVED_NO_AUTHORITY" (implying no rule exists) when a real, cited rule DOES exist -- the true reason is that the OLDER same-jurisdiction bridge has no distinct-cost awareness (a pre-existing, documented, intentionally-unchanged limitation), now labeled RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE and never conflated with a genuine authority gap. Invalidates every cached row so this fires fresh.
# 1.76.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, same-jurisdiction group-stack silent-omission fix -- found via direct instrumentation (not assumed): price_program_group_stack's own docstring already promised "the rejection is preserved by canonical_evaluation.py exactly like every other None return here," but the consuming location_groups loop silently dropped a None result with zero persisted row of any kind whenever a group had a genuinely unresolved pairwise authority gap (confirmed live on a real CPTC+OFTTC+OCASE combo: the combo WAS attempted, price_program_group_stack correctly returned None for the cptc+ocase UNRESOLVED_NO_AUTHORITY gap, and nothing was ever persisted). New _diagnose_group_stack_none() re-derives the exact real reason (economic block, ineligible jurisdiction group, duplicate program, or -- the confirmed common case -- unresolved pairwise authority) in the SAME order price_program_group_stack itself checks, and persists an explicit RULE_REJECTED row naming the real reason, never a fabricated rate and never a silent drop. Invalidates every cached row so this fires fresh.
# 1.75.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, canonical Canadian labour fact model -- replaces treating ATL_DIRECTOR/ATL_WRITER/ATL_PRODUCER/ATL_CAST as CPTC/PSTC-qualifying by spend_category alone (the confirmed defect). New app/calculators/canadian_labour_basis.py derives ca_federal_cptc/ca_federal_pstc qualified-labour amount facts from real, evidenced line-level facts (role, canadian_status, service_location, payee_type, payment_status, look_through_wages_usd, psc_profit_element_eligible, assistance_usd -- ProjectFact rows keyed "line_fact:{line_id}:{field}", no schema migration), applying CPTC's lesser-of-eligible-labour-or-60%-of-net-production-cost cap, PSTC's distinct resident-at-payment/services-in-Canada test, deferred/contingent exclusion, and payee-type look-through, citing the three primary sources fetched this workstream at every substantive rule. A line with no evidenced facts fails closed (excluded, never guessed) rather than qualifying by category. Wired into build_project_economic_inputs() as an additive fill-in (never overrides an explicit caller-supplied amount_fact; emits nothing when a project has zero evidenced Canadian labour lines, so every existing project's behavior is byte-for-byte unchanged). 16 hand-calculated unit tests (tests/test_canadian_labour_basis.py). Scope: Canadian federal CPTC/PSTC only, per explicit instruction not to extend to other programs this pass. Invalidates every cached row so this fires fresh.
# 1.74.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, labour-basis primary-source pass -- added the missing ca_federal_pstc+ca_federal_cptc mutually_exclusive stacking rule (STACKING_RULES_VERSION 1.3.0 -> 1.4.0), confirmed via direct primary-source research (canada.ca CAVCO CPTC/PSTC application guidelines, quoted directly) rather than extrapolation. This was a real, confirmed gap: every OTHER PSTC-equivalent program (ca_bc_pstc, on_opstc) already had this rule against CPTC; the federal pair itself did not. Full statutory research findings (60%-of-net-production-cost cap mechanics, deferral/contingent-remuneration exclusion, loan-out/look-through payee rules, assistance treatment) are recorded in the handoff for the next pass -- NOT implemented as a full per-line canonical fact model this pass; that remains a separate, larger, unbuilt capability (see handoff). Invalidates every cached row so this fires fresh.
# 1.73.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION -- DOMINATED_WITH_PROOF rows previously stored only an aggregate count/window-size, not the actual reconstruction data (which real jurisdiction/program candidates were examined, or which specific priced structure the proof is measured against) -- a genuine gap between "a proof was computed" and "a reviewer can independently verify it without re-running this exact code." Adds component_target_windows (the exact real (jurisdiction_code, program_slug, marginal_value_usd) candidates considered per component), incumbent_structure_id/incumbent_jurisdiction_codes/incumbent_program_slugs (the specific PRICED structure the incumbent bound is measured against), proof_type, ordering_key, and duplicated engine_version/input_fingerprint into the trace for self-contained auditability. Also fixed a real test bug (not a production bug): test_duplicate_economic_routes_persist_once and the two other DB-backed tests were scoped only by engine_version, which conflated legitimate cross-fingerprint historical churn with genuine within-run duplication -- now scoped to the current input_fingerprint, matching how _summarize_evaluation() actually reads served state. Invalidates every cached row so this fires fresh.
# 1.72.0: CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_CORRECTION -- replaces the prior pass's disclosed-but-incomplete SEARCH_DEPTH_LIMIT_REACHED escape hatch with a genuinely COMPLETE, proof-based mechanism: for an r-component subset, a pigeonhole exchange argument proves no candidate ranked below its own component's top-r can ever be part of the true optimum (at most r-1 OTHER components can occupy a jurisdiction, so at least one of any component's own top-r choices is always free). The search starts at this proven-sufficient window and WIDENS (never truncates) on failure until a real, executable combination is found or every candidate has been exhausted, so the disposition for every unexamined remainder is always a genuine DOMINATED_WITH_PROOF -- never an admitted search-budget cutoff. Invalidates every cached row so this fires fresh.
# 1.71.0: CLAUDE_PROMPT_2_GENERIC_DISCOVERY_CORRECTION_AND_HANDOFF -- corrects a real defect: commit 35df531f changed production candidate-generation behavior (component-aware alternate-anchor discovery, plus a since-removed _NAMED_ACCEPTANCE_CONTROL_TARGETS allowlist) WITHOUT bumping ENGINE_VERSION. Removed _NAMED_ACCEPTANCE_CONTROL_TARGETS entirely and replaced the top-3-per-component ranking with a k-way branch-and-bound bounded by a fixed, disclosed search-depth cap.
# 1.70.0: CLAUDE_STRUCTURAL_GENERATOR_CANONICAL_INTEGRATION_CORRECTION -- corrects the false completion boundary from 1.69.0: structural_archetype_generator.py existed but was never imported/invoked by evaluate_project(), so its structures (including the two real Lips Like Sugar HO-001/HO-002 omissions) were provable only in direct-generator tests, never in canonical persisted/served runtime. Adds a new ordinary-component-hybrid candidate loop, immediately after the existing single-component relocation loop, that builds every structurally meaningful >=2-movable-component simultaneous routing from the project's OWN real budget via the SAME derive_account_allocation kernel every other candidate type uses, hands each to generate_structural_candidate for legality/pricing, and persists every generated/rejected candidate as a real ProductionStructure/StructureCalculationResult with structural_family="ordinary_component_hybrid" and evidence_level="CANONICAL_PERSISTED_RUNTIME" -- read back automatically by the existing generic _summarize_evaluation() fingerprint-scoped query, so served-view exposure required no separate wiring.
# 1.69.0: CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION -- adds the generic multi-component structural-archetype generator (app/calculators/structural_archetype_generator.py, covering all 12 corrected Codex archetypes with one mechanism), fixes test-order isolation in test_au_uk_copro_overview_wiring_claude.py, and updates stacking_rules.py (STACKING_RULES_VERSION 1.3.0: 2 missing registry rules added, NY corrected to same_cost_prohibited_distinct_costs_allowed) consumed by the SAME-jurisdiction group-stacking bridge used inside evaluate_project(). Invalidates every cached row so this fires fresh.
# 1.68.1: CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B follow-up -- fixed a second, independent stale mutually_exclusive check that let a "mixed"-rule-type 3+-program group be served PRICED with no incentive.
# 1.68.0: CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B -- fixes a real defect Codex's corrected global-stacking audit identified: a 3+-program combined structure was served PRICED whenever its pairwise rule types were mixed. Also adds two real, primary-source-confirmed stacking rules (on_ofttc+ocase, on_opstc+ocase, per ontariocreates.ca).
# 1.67.0: CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE -- fixes a second-order defect discovered while verifying 1.66.0's ca_bc_pstc/ca_federal_pstc/ca_federal_cptc labour-base fix: a "ceiling with a real floor" program's served incentive was computed off the whole segment instead of the real traced labour subtotal. Also unblocks 18 further programs from a stale FAIL_CLOSED registry.
# 1.66.0: CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE -- real labour-only-base derivation for ca_bc_pstc/ca_federal_pstc/ca_federal_cptc (previously kind="rate_base_narrower_than_qpe", which only disclosed a narrower base was required but never bound one, so these three programs could never price at all), reusing the same component_basis_spend_categories mechanism already established for ca_bc_dave.
# 1.65.0: CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE (France/Latvia P0 fixes) -- corrects Codex P0-CALC-001 (fr_trip's VFX-spend fact was synthesized from whole French QPE instead of the real traced VFX-component subtotal) and P0-CALC-002 (Latvia's 30% ceiling had no evaluable condition; replaced with the National Film Centre of Latvia's real, primary-sourced single flat 30% rate gated on a real converted minimum-spend threshold). See CLAUDE_18_CALCULATION_RECONCILIATION.csv and CLAUDE_LATVIA_PRIMARY_SOURCE_RESOLUTION.md.
# 1.64.0: CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR -- generic repair of the discovery-to-pricing pipeline for formulaically executable programs whose amount_fact_key (spend/labor/shooting-day/tier amount) cannot be known before a candidate has allocated real spend. Replaced the us_or_opif-only discovery/preflight probe special case with program_rate_rules.build_discovery_amount_probe(), applied to EVERY program's amount_fact_key conditions (au_location_offset, ca_bc_dave, ma_ccm_rebate, th_film_incentive, and any other program in this same defect class), and extended allocation_pricing.price_segment's existing component-basis amount-fact derivation to also derive whole-segment (non-component-basis) currency-suffixed amount facts from the segment's own real qpe via the canonical FX path. Invalidates every cached row so this fires fresh.
# 1.63.0: CLAUDE_SPEND_THRESHOLD_AND_ANCHOR_CLOSEOUT -- extended the 1.62.0 producer-controlled-fact union to BOTH discover_executable_jurisdictions() call sites (feasibility_discovery and discovery), which previously used the raw, un-unioned evidenced_program_facts. A program gated only on a producer-controlled boolean (e.g. za_nfvf_rebate, ca_bc_dave) was being rejected at the discovery/acceptance stage -- before ever reaching the 1.62.0-fixed pricing functions -- so the prior fix never took effect for it. Invalidates every cached row so this fires fresh.

#: STALE as of item D (Codex forensic finding D): travel/FX/local-cost (MFNI)
#: normalization ARE now applied generically -- see
#: _relocation_normalization() and true_net_cost_usd vs
#: risk_adjusted_net_cost_usd on every served candidate. Only in-kind
#: replacement remains unconnected (a genuinely absent generic capability,
#: not a disconnected one -- see _relocation_normalization's own docstring).
LIMITATION_NOTE = (
    "Travel/FX/local-cost (MFNI) normalization ARE applied — see this "
    "candidate's risk_adjusted_net_cost_usd for the normalized figure "
    "against true_net_cost_usd's pre-normalization one. In-kind "
    "replacement cost is not yet computed generically for any project "
    "(a real, production-specific fact rather than a generic property)."
)

#: Why the baseline structure is always the served "winner" in this phase,
#: never a relocation candidate — see the module-level note below.
#: STALE as of item D: travel and local-cost ARE now computed generically
#: (risk_adjusted_net_cost_usd); only in-kind post-production replacement
#: remains a genuinely absent generic capability.
RELOCATION_COMPARABILITY_NOTE = (
    "This structure's true_net_cost_usd omits real relocation-specific "
    "costs; see risk_adjusted_net_cost_usd for the travel/FX/local-cost- "
    "normalized figure. In-kind post-production replacement cost is not "
    "yet computed generically for any project (a real, production-specific "
    "fact, not a generic property). Never treated as beating the baseline "
    "until in-kind costs are also modeled generically."
)

#: CLAUDE_PROMPT_2_GENERIC_DISCOVERY_CORRECTION_AND_HANDOFF removed the
#: named-program allowlist (`_NAMED_ACCEPTANCE_CONTROL_TARGETS`) that
#: previously lived here. HO-001/HO-002 visibility is now a property of
#: the generic branch-and-bound discovery in evaluate_project() (see its
#: own docstring at the ordinary-component-hybrid loop), never of a
#: hard-coded slug/jurisdiction list. Do not reintroduce a named list.

#: Candidate accounting terminal states (Part N/K).
STATUS_PRICED = "PRICED"
STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT = "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
STATUS_RULE_REJECTED = "RULE_REJECTED"
STATUS_FEASIBILITY_REVIEW_REQUIRED = "FEASIBILITY_REVIEW_REQUIRED"
#: Consolidated Backend Correction (CBA-001), qualification admission gate
#: — a genuine QUAL_HARD_FAIL never becomes STATUS_PRICED, never enters
#: priced_by_code (so it can never be stacked, combined into a component
#: candidate, or numerically ranked — every downstream consumer reads
#: priced_by_code exclusively, so gating admission here is sufficient),
#: and reports no total_incentive_value_usd/npc as though admitted; real,
#: already-computed pricing is still disclosed as POTENTIAL economics
#: ("what this would be worth"), never as admitted rankable economics.
#:
#: Every OTHER real qualification state (QUALIFIES, NOT_APPLICABLE,
#: CURABLE_GAP, USER_FACT_REQUIRED, SCRIPT_FACT_REQUIRED,
#: AUTHORITY_UNRESOLVED, RULE_DATA_INCOMPLETE) is admitted to full
#: pricing/stacking — per the task's own Part 2 mapping, only HARD_FAIL
#: is "unavailable"; every other unresolved state is "opportunity/
#: disclosure", meaning priced with the gap disclosed, never blocked.
#:
#: An earlier version of this gate additionally excluded CURABLE_GAP/
#: USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED from
#: pricing entirely. Once exercised against a real, uncached evaluation
#: (previously masked by a stale persisted result under the prior
#: ENGINE_VERSION) this was found to silently disqualify Little Utopia's
#: and FVD's own baseline structures from ever being priced, because
#: Mauritius's and Greece's own cultural-test-APPLICABILITY research is
#: itself AUTHORITY_UNRESOLVED — a genuine authority gap about whether a
#: test exists at all, never a reason to withhold a program's own
#: statutory spend-based pricing. Corrected 2026-08-20 to the narrower
#: gate below (pricing admission), paired with a SEPARATE, stricter gate
#: on RECOMMENDED/comparable-ranking admission — see
#: _QUALIFICATION_ADMITS_RECOMMENDED and canonical_production_view.py's
#: _qualification_admits_recommended / this module's own
#: _summarize_evaluation._admits_recommended: a candidate whose
#: qualification is real but unresolved is priced and disclosed but can
#: never be presented as the recommended/comparable winner, even when
#: that leaves a project with no Recommended scenario at all (Part 4:
#: "truthful unresolved status is preferable to false recommendation").
STATUS_QUALIFICATION_HARD_FAIL = "QUALIFICATION_HARD_FAIL"
STATUS_QUALIFICATION_UNRESOLVED = "QUALIFICATION_UNRESOLVED"
_QUALIFICATION_ADMITS_PRICING = frozenset({
    QUAL_QUALIFIES, QUAL_NOT_APPLICABLE, QUAL_CURABLE_GAP,
    QUAL_USER_FACT_REQUIRED, QUAL_SCRIPT_FACT_REQUIRED, QUAL_AUTHORITY_UNRESOLVED,
    QUAL_RULE_DATA_INCOMPLETE,
})

#: Final Consolidated Backend Correction + Global Structuring Intelligence
#: Acceptance, Part 4/CBA-001 — the subset of _QUALIFICATION_ADMITS_PRICING
#: that may enter the COMPARABLE RANKING POOL (eligible for rank #1 /
#: RECOMMENDED). QUALIFIES and NOT_APPLICABLE are priceable AND
#: comparable; every other admitted-to-pricing state (CURABLE_GAP,
#: USER_FACT_REQUIRED, SCRIPT_FACT_REQUIRED, AUTHORITY_UNRESOLVED,
#: RULE_DATA_INCOMPLETE) is priced and disclosed but explicitly must
#: NEVER be presented as the comparable, rankable, RECOMMENDED winner —
#: per this task's own Part 4: "DO NOT weaken qualification gates merely
#: because LU or FVD would otherwise have no Recommended scenario.
#: Truthful unresolved status is preferable to false recommendation."
#: Enforced in canonical_production_view.py's comparable-pool filter,
#: not by withholding economics (those remain visible under ALTERNATIVE/
#: PRICED_LOW_FIT/CO_PRO_OPPORTUNITIES as appropriate).
_QUALIFICATION_ADMITS_RECOMMENDED = frozenset({QUAL_QUALIFIES, QUAL_NOT_APPLICABLE})


def qualification_admits_recommended(role_qualification: dict | None) -> bool:
    """NUM-001 (optimizer audit defect remediation, 2026-09-18) — THE one
    canonical qualification-admission predicate every served surface that
    picks a "winner"/top_result must consume, extracted here so it is
    never re-implemented. Before this fix, three independent copies of
    this same rule existed: this file's own _summarize_evaluation() local
    closure, canonical_production_view.py's module-level function of the
    same name, and NONE at all in project_workspace_view.py (whose
    `top_result = comparable[0]` published a priced-but-genuinely-
    unresolved baseline as the served recommendation for Little Utopia
    and F#K Valentine's Day, confirmed live and independently audited --
    CURRENT_TIP_OPTIMIZER_NUMERICAL_ACCEPTANCE_AUDIT.md). A real but
    genuinely UNRESOLVED qualification state (Curable Gap/User Fact
    Required/Script Fact Required/Authority Unresolved/Rule Data
    Incomplete) is priced and disclosed but must never be the served
    winner -- truthful unresolved status is preferable to false
    recommendation, even when that means no top_result at all. Absent
    role_qualification (a program the bridge has genuinely no data for)
    is treated as admitting -- there is no unresolved STATE to gate on,
    as distinct from a real, resolved-to-unresolved state."""
    state = (role_qualification or {}).get("state")
    return state is None or state in _QUALIFICATION_ADMITS_RECOMMENDED


#: Codex final wiring remediation (P0-SEL-ALT-001, third pass) — the
#: distinct relocation-cost dimensions this codebase can, in principle,
#: evidence per candidate jurisdiction. Mirrors the four adjustment
#: fields already served on every priced candidate's own "adjustments"
#: dict (travel_incremental_delta_usd, fx_delta_usd,
#: local_cost_delta_usd, inkind_replacement_delta_usd). Codex's exact
#: finding on the second pass's single blanket
#: relocation_completeness_evidenced__{code} fact: "one jurisdiction
#: boolean substitutes for dimension-level evidence" — REPLACED here
#: with one evidenced fact PER dimension, so travel/FX/local-cost/
#: in-kind are represented and evaluated individually, never collapsed
#: into a single flag.
_RELOCATION_DIMENSIONS: tuple[str, ...] = ("travel", "fx", "local_cost", "inkind")

#: Codex final wiring remediation — a stack (multi-program) candidate's
#: risk_adjusted_net_cost_usd is still raw, un-normalized NPC (see the
#: multi-program STATUS_PRICED branch below); this is NOT a curable
#: evidence gap a producer can supply a fact to unlock — it is a
#: structural engine-capability gap. Used as the sentinel
#: "missing dimension" for stack candidates so the conditional-pool
#: admission gate in canonical_production_view.py can correctly treat it
#: as an UNCLASSIFIED/non-curable cause (excluded), never conflate it
#: with a genuinely curable, fact-suppliable relocation-evidence gap.
_STACK_NORMALIZATION_NOT_COMPUTED = "stack_normalization_not_computed"


def _relocation_completeness(
    is_baseline: bool, code: str | None, inputs: "ProjectEconomicInputs",
) -> tuple[bool, tuple[str, ...]]:
    """Codex final wiring remediation (P0-SEL-ALT-001, third pass) —
    structured, PER-DIMENSION completeness decision. Supersedes both the
    first (reverted) attempt, which treated "the calculator returned a
    number" as proof of completeness, and the second attempt, which
    required a single blanket jurisdiction-scoped fact standing in for
    every dimension at once — Codex's exact finding: "one jurisdiction
    boolean substitutes for dimension-level evidence... it does not
    disclose the missing dimensions."

    A dimension is accounted for only when an explicit, evidenced
    ProjectFact confirms it — either a real supplied figure
    (f"relocation_{dim}_evidenced__{code}") or an explicit, evidenced
    not-applicable assertion (f"relocation_{dim}_not_applicable__{code}",
    e.g. FX genuinely does not apply to a same-currency relocation).
    Absence of BOTH facts for a dimension is a genuine, disclosed gap —
    "non-applicable dimensions must be explicit, not silently zero"
    (this task's own controlling invariant).

    Returns (is_complete, missing_dimensions). is_complete is always
    True, with an empty missing tuple, for the baseline (no relocation
    occurs, by construction) — every dimension is trivially inapplicable
    to staying in one's own home jurisdiction. No caller in this
    codebase sets any of these facts today, so every non-baseline
    candidate correctly remains incomplete with a FULL, real, per-
    dimension missing list — never a single blanket flag standing in for
    every dimension, and never a fabricated completeness claim."""
    if is_baseline or not code:
        return True, ()
    facts = inputs.evidenced_program_facts
    missing = tuple(
        dim for dim in _RELOCATION_DIMENSIONS
        if f"relocation_{dim}_evidenced__{code}" not in facts
        and f"relocation_{dim}_not_applicable__{code}" not in facts
    )
    return (not missing), missing


#: Existing Optimizer/Stacker Reconnection, Task B — a real, registry-
#: backed treaty/co-production pathway exists but cannot (yet) be priced
#: as qualified economics: either real ownership/cultural-test project
#: facts are missing (canonical_treaty_bridge.RESOLUTION_UNRESOLVED_FACTS)
#: or a mandatory requirement failed (RESOLUTION_INELIGIBLE). NEVER
#: STATUS_PRICED — a co-pro opportunity never enters NPC/ranking as
#: resolved economics; see canonical_treaty_bridge.py's own module note.
STATUS_CO_PRO_OPPORTUNITY = "CO_PRO_OPPORTUNITY"


def _compute_fingerprint(
    inputs: ProjectEconomicInputs,
    role_known_codes: dict[str, tuple[str, ...]] | None = None,
    script_facts: dict | None = None,
    coproduction_facts: tuple | None = None,
    excluded_jurisdiction_codes: frozenset[str] | None = None,
    discretionary_policy_facts: dict[str, str] | None = None,
    role_attachment_facts: dict | None = None,
) -> str:
    import hashlib
    import json

    from app.calculators import production_normalization
    from app.calculators.canonical_role_qualification_bridge import (
        CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION,
    )
    from app.calculators.qualification_model import QUALIFICATION_MODEL_VERSION
    from app.calculators.treaty_engine import TREATY_ENGINE_VERSION
    from app.data.authority_coverage_registry import AUTHORITY_COVERAGE_REGISTRY_VERSION
    from app.data.cultural_point_tables import CULTURAL_POINT_TABLES_VERSION
    from app.data.executable_jurisdiction_registry import (
        EXECUTABLE_JURISDICTION_REGISTRY_VERSION,
    )
    from app.data.national_cultural_status import NATIONAL_CULTURAL_STATUS_VERSION
    from app.data.program_authority_provenance import PROGRAM_AUTHORITY_PROVENANCE_VERSION
    from app.data.program_rate_rules import PROGRAM_RATE_RULES_VERSION
    from app.data.program_requirements import PROGRAM_REQUIREMENTS_VERSION
    from app.data.program_spend_rules import PROGRAM_SPEND_RULES_VERSION
    from app.data.structuring_opportunity_patterns import (
        STRUCTURING_OPPORTUNITY_PATTERNS_VERSION,
    )
    from app.optimization.stacking_rules import STACKING_RULES_VERSION
    from app.services.canonical_runtime_attribution import (
        canonical_ruleset_digest,
        pricing_source_digest,
    )

    payload = {
        "gross_budget_usd": inputs.gross_budget_usd,
        "jurisdiction_code": inputs.jurisdiction_code,
        "production_type": inputs.production_type,
        "lines": sorted(
            (line.account_code, line.description, line.amount_usd, line.spend_category)
            for line in inputs.budget_lines
        ),
        "accounts_outside_jurisdiction": sorted(inputs.accounts_outside_jurisdiction),
        "offshore_payroll_accounts": sorted(inputs.offshore_payroll_accounts),
        # Part 21/CBA-008 — a material new PROJECTED fact that changes
        # qualification outcomes (see qualification_derivation's
        # contingency branch) must invalidate any stale cached result.
        "contingency_expected_utilization_pct": inputs.contingency_expected_utilization_pct,
        # Producer Display Names + Budget Rail User Assumptions closeout —
        # same reasoning as contingency_expected_utilization_pct directly
        # above: a change to this producer-stated NPC input must invalidate
        # any stale cached evaluation row.
        "financing_cost_usd": inputs.financing_cost_usd,
        # Codex final runtime remediation -- the SAME reasoning as
        # financing_cost_usd/contingency directly above: a change to a
        # producer's evidenced program-eligibility/native-currency facts
        # must invalidate any stale cached evaluation row, or evidencing
        # (or retracting) a fact like an AUD/CZK/MAD/ZAR native threshold
        # or a preapproval/award confirmation would silently keep serving
        # the pre-change persisted structures forever.
        "evidenced_program_facts": sorted(inputs.evidenced_program_facts),
        "amount_facts": sorted(inputs.amount_facts.items()),
        # Codex final wiring remediation (P0-NL-001): explicit, even
        # though also implicitly covered via evidenced_program_facts/
        # amount_facts above -- a company/period identity change (or a
        # sibling project's award changing) must invalidate any stale
        # cached row for THIS project.
        "production_company_identifier": inputs.production_company_identifier,
        "award_period_year": inputs.award_period_year,
        # Codex adverse finding (P0-FX-001): hashing ONLY fx_snapshot_date
        # let two contexts sharing a date but differing in rates, source,
        # or freshness_status (e.g. a same-day live-refresh CORRECTION, or
        # a fresh-versus-stale_fallback flip with no date change) collide
        # on the identical fingerprint and silently reuse a stale cached
        # row. The full, deterministic digest below covers every
        # calculation-driving field of the context: the complete
        # normalized rate mapping (sorted, so key order never affects the
        # hash), source, freshness_status, and snapshot_date. Any change
        # to ANY of these must produce a different fingerprint.
        "fx_context_digest": (
            hashlib.sha256(json.dumps({
                "snapshot_date": inputs.fx_context.snapshot_date,
                "rates": sorted(inputs.fx_context.rates.items()),
                "source": inputs.fx_context.source,
                "freshness_status": inputs.fx_context.freshness_status,
            }, sort_keys=True).encode("utf-8")).hexdigest()
            if inputs.fx_context is not None else None
        ),
        # Batched producer-control closeout (2026-09-03) -- a change to
        # which jurisdictions this PROJECT elects to exclude from its own
        # candidate universe must invalidate any stale cached evaluation
        # row (same reasoning as financing_cost_usd/contingency directly
        # above), or toggling Saudi ON/OFF would silently keep serving
        # the pre-toggle persisted structures forever.
        "excluded_jurisdiction_codes": sorted(excluded_jurisdiction_codes or ()),
        # Item B (Final non-Globe closeout, 2026-09-04) -- a change to
        # this project's discretionary/selective-program policy (default
        # or any per-program override) must invalidate any stale cached
        # evaluation row, same reasoning as excluded_jurisdiction_codes
        # directly above -- or toggling a discretionary program ON/OFF
        # would silently keep serving the pre-toggle persisted structures
        # forever.
        "discretionary_policy_facts": sorted((discretionary_policy_facts or {}).items()),
        # CBA-008 (Codex evidence: "fingerprint excludes personnel,
        # screenplay, co-production ... versions") — these three facts can
        # move a candidate between QUALIFIES/CURABLE_GAP/USER_FACT_
        # REQUIRED/SCRIPT_FACT_REQUIRED, so a change to any of them must
        # invalidate an existing current-ENGINE_VERSION row rather than
        # let it keep serving under a now-stale qualification result.
        "role_known_codes": sorted(
            (role, sorted(codes)) for role, codes in (role_known_codes or {}).items()
        ),
        "script_facts": sorted(
            (element_type, sorted(values)) for element_type, values in (script_facts or {}).items()
        ),
        "coproduction_facts": coproduction_facts,
        # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — distinct
        # from role_known_codes above: role_known_codes does not vary
        # with ProjectPerson.is_confirmed at all (an attachment's
        # confirmed status can flip without changing that set), so a
        # producer confirming a previously-proposed attachment must be
        # represented here explicitly or the treaty personnel gate could
        # keep serving a stale (pre-confirmation) resolution forever.
        "role_attachment_facts": sorted(
            (
                role,
                tuple(sorted(f.confirmed_nationality)),
                tuple(sorted(f.confirmed_residency)),
                f.confirmed_attached_unknown_nationality,
                f.confirmed_attached_unknown_residency,
                f.has_unconfirmed_attachment,
                f.has_any_attachment,
            )
            for role, f in (role_attachment_facts or {}).items()
        ),
        # Registry/table knowledge versions (Codex OH-001: "It omits
        # material authority/economic-state, stacking, treaty, opportunity-
        # pattern, spend-rule, executable-registry, and consolidation
        # versions"). This is the complete canonical dependency manifest:
        # every registry a served evaluation actually reads from is
        # represented here by its own version constant. A stale row (a
        # different value on ANY of these) can never be matched as
        # reusable — see the query in evaluate_project() immediately
        # below, which requires an EXACT fingerprint match. Bumping any
        # one of these constants is therefore sufficient, on its own, to
        # invalidate every previously-cached row without touching
        # ENGINE_VERSION — the two mechanisms are complementary, not
        # redundant (ENGINE_VERSION also covers persisted-SHAPE changes
        # the fingerprint can't detect, e.g. a new field being added to
        # calculation_trace_json for unchanged inputs).
        "qualification_model_version": QUALIFICATION_MODEL_VERSION,
        "cultural_point_tables_version": CULTURAL_POINT_TABLES_VERSION,
        "national_cultural_status_version": NATIONAL_CULTURAL_STATUS_VERSION,
        "program_rate_rules_version": PROGRAM_RATE_RULES_VERSION,
        "authority_coverage_registry_version": AUTHORITY_COVERAGE_REGISTRY_VERSION,
        "program_authority_provenance_version": PROGRAM_AUTHORITY_PROVENANCE_VERSION,
        "program_requirements_version": PROGRAM_REQUIREMENTS_VERSION,
        "program_spend_rules_version": PROGRAM_SPEND_RULES_VERSION,
        "stacking_rules_version": STACKING_RULES_VERSION,
        # STALE-STATE PREVENTION (item 8). Every *_VERSION above is
        # HAND-MAINTAINED: a semantic change shipped without bumping one does
        # not invalidate persisted rows, so the change never reaches served
        # output while a full suite still reports "zero regressions" -- exactly
        # what happened with cluster 5 (commit d754b6a). These two digests are
        # DERIVED from what is actually loaded, so no constant has to be
        # remembered:
        #   ruleset_digest        -- the live canonical rule DATA
        #   pricing_source_digest -- the on-disk SOURCE of the modules that
        #                            decide economics
        # Either changing invalidates every persisted result automatically.
        "ruleset_digest": canonical_ruleset_digest(),
        "pricing_source_digest": pricing_source_digest(),
        "treaty_engine_version": TREATY_ENGINE_VERSION,
        "structuring_opportunity_patterns_version": STRUCTURING_OPPORTUNITY_PATTERNS_VERSION,
        "executable_jurisdiction_registry_version": EXECUTABLE_JURISDICTION_REGISTRY_VERSION,
        "canonical_role_qualification_bridge_version": CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION,
        # Overview FX Strip Freshness Architecture: the live FX snapshot
        # date is DERIVED from what production_normalization.py actually
        # has loaded right now (same "derived, not hand-maintained"
        # pattern as ruleset_digest immediately above) -- a freshness
        # refresh that adopts a new day's snapshot changes this fingerprint
        # on its own, so a stale persisted evaluation is never served
        # paired with fresh FX metadata: this is the "DETERMINE WHETHER
        # CURRENT PERSISTED EVALUATION USES SAME ECONOMIC INPUT/
        # FINGERPRINT" step of the required page-open FX flow, reusing
        # this existing generation-based invalidation mechanism rather
        # than inventing a second one.
        "fx_live_snapshot_date": production_normalization.FX_LIVE_SNAPSHOT_DATE,
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _relocation_normalization(
    inputs: "ProjectEconomicInputs", jurisdiction_code: str, allocated_usd: float,
) -> tuple[float, float | None, float]:
    """Codex forensic finding D -- connects the EXISTING, generic
    production_normalization.py (travel_model.py + apply_fx_rates.py +
    production_adjustment.py) into the generic evaluator. This capability
    was real and already reused by Little Utopia's own hand-built
    comparisons, but every candidate this module priced hardcoded
    travel_incremental_delta_usd=0.0, fx_delta_usd=None,
    local_cost_delta_usd=0.0 -- disconnected during the generic cutover,
    not absent. No duplicate calculator: this calls the SAME three
    functions LU's own path already calls, generalized to any
    (jurisdiction_code, allocated_usd) pair.

    Every input is either a real project figure (the production's own
    travel budget line, its real gross budget, the two real jurisdiction
    codes) or that calculator's own documented, disclosed static
    benchmark/snapshot default -- never a fabricated fact. The baseline
    candidate (jurisdiction_code == inputs.jurisdiction_code) yields an
    exact-zero travel/local-cost delta by construction (both calculators'
    own documented behavior), so this cannot move the baseline's own NPC.

    in-kind replacement is deliberately NOT included here: unlike travel/
    FX/local-cost, it has no generic derivation -- it names a real,
    specific, off-budget fact about ONE production (Little Utopia's
    Mauritius in-kind post FMV), not a property every production has. That
    remains a disclosed 0.0, a genuinely absent generic capability rather
    than a disconnected one -- see the module docstring above.
    """
    from app.calculators.production_normalization import (
        FXInputs,
        TravelInputs,
        compute_fx_normalization,
        compute_local_cost_normalization,
        compute_travel_normalization,
    )
    from app.models.enums import SpendCategory

    original_budgeted_travel_usd = round(sum(
        line.amount_usd for line in inputs.budget_lines
        if not line.is_memo
        # Codex BPI-002: the line's own spend_category is authoritative;
        # the shared code-keyed dict is a fallback only (see
        # production_allocation.py's identical fix for the full
        # rationale).
        and (line.spend_category or inputs.spend_category_by_code.get(line.account_code))
        == SpendCategory.TRAVEL.value
    ), 2)

    travel = compute_travel_normalization(
        jurisdiction_code, TravelInputs(),
        original_budgeted_travel_usd=original_budgeted_travel_usd,
        original_jurisdiction_code=inputs.jurisdiction_code,
    )
    local_cost = compute_local_cost_normalization(
        jurisdiction_code, inputs.jurisdiction_code, inputs.gross_budget_usd,
    )
    # scenario_fx_delta_pct defaults to 0.0 (no assumed currency movement) --
    # no per-project FX scenario fact exists yet, so this connects the real
    # rate lookup/disclosure without fabricating a hypothetical movement;
    # delta_usd is honestly 0.0 absent that fact, exactly as before, but now
    # the rate itself is looked up and disclosed rather than skipped.
    fx = compute_fx_normalization(jurisdiction_code, FXInputs(), local_cost_basis_usd=allocated_usd)

    return travel.incremental_delta_usd, fx.delta_usd, local_cost.incremental_delta_usd


@functools.lru_cache(maxsize=None)
def _competitive_allocation_disclosure(program_slug: str) -> str | None:
    """Master reconciliation, 2026-09-02: administrative/pre-certification
    and competitive/capacity allocation are REAL risks, distinct from
    whether the program's rate resolves deterministically. This discloses
    them on every served candidate that reaches STATUS_PRICED -- it never
    withholds economics; that would repeat the repealed _derived_coverage()
    defect (authority_coverage_registry.py's own repeal comment has the
    full accounting).

    Reads only real canonical program_requirements fields --
    allocation_type and preapproval_mandatory -- never a fabricated risk
    assessment. Returns None when neither is set (an ordinary entitlement
    program has nothing to disclose here).
    """
    try:
        from app.data.program_requirements import get_program_requirements
    except Exception:  # pragma: no cover - import cycle safety
        return None
    profile = get_program_requirements(program_slug)
    if profile is None:
        return None
    allocation = getattr(profile, "allocation_type", None)
    preapproval = bool(getattr(profile, "preapproval_mandatory", False))
    allocation_text = str(allocation).upper() if allocation else ""
    is_competitive = "COMPETITIVE" in allocation_text
    is_discretionary = "DISCRETIONARY" in allocation_text
    if not (is_competitive or is_discretionary or preapproval):
        return None

    parts = []
    if is_discretionary:
        parts.append(
            "the award authority has discretion over whether and/or how "
            "much to award"
        )
    elif is_competitive:
        parts.append(
            "allocation is competitive/capacity-limited (ranked selection "
            "or a fixed application-window pool) -- receipt of this "
            "production's own deterministic rate is not guaranteed by "
            "eligibility alone"
        )
    if preapproval:
        parts.append(
            "a preapproval/certification step (e.g. an allocation letter) "
            "is required before this incentive is confirmed"
        )
    return (
        "Administrative/allocation risk (not an economic block -- the "
        "figures below are this program's real deterministic formula, "
        "priced normally): " + "; ".join(parts) + "."
    )


def _hy_result_trace_extras(hy_result) -> dict:
    """NUM-002/NUM-003 (optimizer audit defect remediation, 2026-09-18):
    one shared serializer for the discretionary-risk and stacking-
    adjustment reconstruction fields structural_archetype_generator.
    StructuralCandidateResult now carries, used by every one of this
    file's hybrid trace-construction sites -- never re-derived or
    re-serialized independently at each site. Reconciliation: sum(
    post_adjustment_component_incentives_usd.values()) equals the
    structure's own total_guaranteed_incentive_usd (persisted as this
    row's total_incentive_value_usd) exactly, by construction (see
    generate_structural_candidate's own total_guaranteed computation)."""
    return {
        "administrative_allocation_risk": hy_result.administrative_allocation_risk,
        "administrative_allocation_risk_reasons": list(hy_result.administrative_allocation_risk_reasons),
        "raw_component_incentives_usd": dict(hy_result.raw_component_incentives_usd),
        "stacking_adjustments": [
            {
                "program_a_id": a.program_a_id,
                "program_b_id": a.program_b_id,
                "rule_type": a.rule_type,
                "description": a.description,
                "original_value_usd": a.original_value_usd,
                "adjustment_usd": a.adjustment_usd,
                "adjusted_value_usd": a.adjusted_value_usd,
            }
            for a in hy_result.stacking_adjustments
        ],
        "post_adjustment_component_incentives_usd": dict(hy_result.post_adjustment_component_incentives_usd),
    }


#: CLAUDE_PRE_AG_HANDOFF_CORRECTION: boolean project-fact keys that gate a
#: RateCondition purely on a PRODUCER-CONTROLLED administrative step --
#: preapproval/registration/self-attested activity type/fund-currency
#: confirmation, never a cultural, spend/QPE, or genuinely discretionary
#: test. Per the global CineGlobe assumption policy (administrative
#: requirements must be assumed satisfied, disclosed, never suppressive),
#: these are auto-supplied as satisfied for candidate generation so the
#: optimizer produces a real, disclosed CONDITIONAL price instead of
#: unconditionally rejecting a program whose real spend/cultural facts
#: would otherwise qualify it. This must NEVER include a fact whose own
#: documented description names a genuinely discretionary/comparative
#: agency-selection process (e.g. us_or_opif_award_confirmed, which
#: explicitly names "agency comparative/discretionary approval" -- that
#: one stays a real, unassumed gate) or a substantive content/independence
#: test (e.g. nl_nfpi_points_independence_test_passed) or a spend/format
#: threshold (e.g. nl_nfpi_format_threshold_met) -- those three remain
#: real gates, never auto-assumed. See
#: docs/validation/CLAUDE_EIGHT_FACT_DEPENDENCY_RESOLUTION.csv for the
#: full per-fact classification this set is derived from.
_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS: frozenset[str] = frozenset({
    "ma_ccm_prior_approval_and_fund_availability_confirmed",
    "th_film_incentive_preapproval_confirmed",
    "za_nfvf_accepted_production_confirmed",
    "za_nfvf_post_production_only_confirmed",
    "ca_bc_dave_eligible_activity_confirmed",
    "us_or_opif_fund_amount_current_confirmed",
})


def _price_candidate(
    inputs: ProjectEconomicInputs, jurisdiction_code: str, program_slug: str,
):
    """The established two-pass pattern, generalized: build a rate-
    independent register to classify QPE, resolve the program's real
    statutory rate for that QPE, then price at the resolved rate. Returns
    (pricing, register, rate_resolution) or (None, None, None) if the
    program has no rate rules that resolve for this production."""
    facts = production_facts_for(inputs, jurisdiction_code=jurisdiction_code)
    register_probe = derive_qualification_register(
        inputs.budget_lines, program_slug=program_slug, facts=facts,
        rate=0.0, program_territorial_text=None,
    )
    qpe = round(sum(
        a.amount_usd for a in register_probe if a.state == QualificationState.QUALIFIES
    ), 2)

    # Codex final runtime remediation: this early "does this program even
    # have a resolvable rate" preflight must consult the SAME evidenced/
    # amount facts price_allocated_structure below is given -- otherwise
    # a program whose ONLY resolvable tier is gated on a caller-evidenced
    # fact (e.g. au_location_offset's native AUD threshold) returns None
    # HERE, before ever reaching the pricing call this function threads
    # those facts into, and the fact never has any effect.
    # Codex final Oregon full-pipeline completion (P0-OR-001, sixth
    # pass): this preflight runs BEFORE the real per-line allocation
    # exists, so a composite program's exact, canonical-line-derived
    # component facts (allocation_pricing.price_segment's own
    # reconciliation, the true, strict gate) are not yet available here
    # either -- register_probe (just computed above, from this SAME
    # production's real budget lines) already knows the real QUALIFYING
    # total, though. Using it as a PROBE-ONLY value for both of
    # us_or_opif's composite facts here is safe and narrowly scoped: it
    # only ever affects whether this preflight lets a real, eligible
    # Oregon production continue to the real pricing call below, never
    # an actual priced dollar figure -- price_segment's own strict,
    # exact-match reconciliation (never this probe) remains the sole
    # authority for the real composite basis and the real number.
    # CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR: generic replacement for
    # the old us_or_opif-only special case. `qpe` above is already this
    # SAME production's own real, allocated/qualifying total for this
    # exact jurisdiction/program pair (from register_probe, derived from
    # inputs.budget_lines) — a genuine candidate-derived amount, not a
    # guess — so seeding every one of this program's amount_fact_key
    # conditions from it (currency-converted via the canonical FX path
    # where the key names a native currency) is safe for every
    # amount-gated program, not just Oregon's two composite facts.
    _preflight_amount_facts = build_discovery_amount_probe(
        program_slug, qpe, inputs.amount_facts, inputs.fx_context,
    )
    # CLAUDE_PRE_AG_HANDOFF_CORRECTION: union in the producer-controlled
    # administrative facts (never cultural/spend/discretionary) so a real
    # eligible candidate is not rejected solely because no one has
    # persisted a project-specific ProjectFact confirming, e.g.,
    # preapproval will be sought -- disclosed as an assumption via the
    # normal administrative_allocation_risk/conditional trace, never
    # silently treated as a verified fact.
    _preflight_evidenced_facts = inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
    rr = resolve_program_rate(
        program_slug, production_type=inputs.production_type, qpe_usd=qpe,
        evidenced_facts=_preflight_evidenced_facts, amount_facts=_preflight_amount_facts,
        fx_context=inputs.fx_context,
    )
    if rr is None:
        return None, register_probe, None

    register = derive_qualification_register(
        inputs.budget_lines, program_slug=program_slug, facts=facts,
        rate=rr.modeled_rate, program_territorial_text=None,
    )

    spec = StructureSpec(
        # Program identity, not jurisdiction_code alone, is the uniqueness
        # key — two independent programs sharing one jurisdiction (Ontario's
        # ca_on_opstc/on_ofttc/OCASE) must never collide on this id.
        structure_id=f"CANON-{jurisdiction_code}-{program_slug}",
        structure_type=("single_country" if jurisdiction_code == inputs.jurisdiction_code else "full_relocation"),
        label=(
            f"{jurisdiction_code} — production's current base"
            if jurisdiction_code == inputs.jurisdiction_code
            else f"Full relocation to {jurisdiction_code}"
        ),
        primary_jurisdiction=jurisdiction_code,
        participants=(jurisdiction_code,),
        incentive_programs={jurisdiction_code: program_slug},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, jurisdiction_code, allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        # Producer Display Names + Budget Rail User Assumptions closeout —
        # threads the producer's persisted financing-cost assumption
        # (ProjectFact, same USER_OVERRIDE mechanism as contingency above)
        # into the existing financing_cost_usd NPC parameter. Absent
        # (None) resolves to 0.0 — price_allocated_structure's own
        # documented default ("explicit inputs only, never a silent
        # assumption"), never assumed here.
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        # Codex final runtime remediation — the SAME generic ProjectFact
        # mechanism as financing_cost_usd/contingency above, threading a
        # producer's real, evidenced program-eligibility/native-currency
        # facts into resolve_program_rate() through the actual production
        # pipeline. Absent (empty) is byte-identical prior behavior for
        # every program without such a condition.
        # CLAUDE_PRE_AG_HANDOFF_CORRECTION: uses the same
        # _preflight_evidenced_facts union (real evidenced facts plus the
        # producer-controlled administrative assumption set) as the
        # preflight resolve_program_rate call above, so the real priced
        # segment is consistent with what the preflight already decided
        # was eligible.
        evidenced_requirement_facts=_preflight_evidenced_facts,
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return pricing, register, rr


def _classify_opportunity_relevance(
    resolution_state: str, conditional_scenario: dict | None, project_anchored: bool,
    personnel_gate_state: str | None = None,
) -> str:
    """COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION -- classifies a
    served treaty/co-production opportunity using the AVAILABLE /
    COMPATIBLE / CONDITIONAL / EXECUTABLE / EXCLUDED / AUTHORITY_OR_RULE_
    DATA_INCOMPLETE contract, purely from fields this evaluation ALREADY
    computed (resolution_state, the conditional-pricing scenario's own
    status, and whether this opportunity's own treaty parties include
    this project's real home/service jurisdiction) -- no new eligibility
    math, no invented fact, no change to resolution_state/pricing/ranking.
    Purely a read-only, additive label surfaced alongside the existing
    fields, so the Globe (or any other consumer) never has to re-derive
    it from raw resolution_state/conditional_scenario shape.

      EXECUTABLE  -- resolution_state is ELIGIBLE: real project facts
                     (never an assumption) cleared every mandatory
                     threshold. Always the strongest classification,
                     regardless of anchoring -- real facts are real facts.
      EXCLUDED    -- resolution_state is INELIGIBLE: a real, confirmed
                     disqualification (a failed cultural test, a
                     confirmed-wrong personnel fact, etc.).
      AVAILABLE   -- the treaty/framework is real and registered, but
                     either (a) it is not anchored at this project's own
                     jurisdiction at all AND no real, rule-consumed
                     personnel credit connects it to this project either
                     -- a globally enumerated pair between two OTHER
                     countries, never presented as project-compatible
                     merely because a registry entry exists -- or (b) it
                     IS anchored here (or personnel-qualified) but no
                     achievable modeled path exists yet (a real,
                     unresolvable creative/legal fact, e.g. an
                     unconfirmed cultural test, blocks even the
                     conditional-assumption scenario).
      CONDITIONAL -- (anchored at this project's own jurisdiction, OR a
                     real personnel_requirement genuinely QUALIFIES from
                     this project's own confirmed creative attachments --
                     PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END: a
                     globally-enumerated treaty is no longer forced to
                     AVAILABLE when THIS project's own real, confirmed
                     writer/director facts are the reason it resolves;
                     personnel_gate_state == QUALIFIES only ever occurs
                     from a real project fact clearing a real researched
                     rule, never an assumption, so this is not "presented
                     as project-compatible merely because contribution
                     shares can be assumed" -- the assumption here is
                     ONLY ever the contribution split, same as the
                     anchored case, with a REAL fact-based personnel
                     credit on top) AND the conditional-pricing scenario
                     reached a real priced result using the treaty's own
                     registered minimum contribution as a disclosed,
                     producer-actionable assumption -- never presented as
                     a verified fact or a recommendation (see
                     _admits_recommended/top_pair, which never considers a
                     treaty_coproduction row at all: total_incentive_
                     value_usd/true_net_cost_usd are always None on this
                     row; only the nested conditional_scenario carries a
                     number).
      AUTHORITY_OR_RULE_DATA_INCOMPLETE -- the conditional scenario itself
                     could not resolve for a data-completeness reason (an
                     unresolved same-jurisdiction stacking group, or no
                     canonical rate rule for what the treaty unlocks)
                     rather than a genuine legal/creative blocker.

    Compatible/executable current-fact states never require this helper
    to invent anything: COMPATIBLE (current project facts support the
    pathway short of full executability) does not currently occur in
    this codebase's real data -- every real treaty_coproduction row is
    either a bare registry entry (no contribution-share fact at all) or
    fully solved to ELIGIBLE via a real, evidenced contribution fact
    (EXECUTABLE); there is no intermediate "some but not all current
    facts satisfied" state today. Reserved in the returned vocabulary
    for a future caller that has one."""
    if resolution_state == RESOLUTION_ELIGIBLE:
        return "EXECUTABLE"
    if resolution_state == RESOLUTION_INELIGIBLE:
        return "EXCLUDED"
    personnel_qualifies = personnel_gate_state == QUAL_QUALIFIES
    if not project_anchored and not personnel_qualifies:
        return "AVAILABLE"
    status = (conditional_scenario or {}).get("status")
    if status == "CONDITIONAL_PROJECT_FACT_DEPENDENT":
        return "CONDITIONAL"
    if status in ("RULE_DATA_INCOMPLETE", "CANONICAL_DATA_GAP"):
        return "AUTHORITY_OR_RULE_DATA_INCOMPLETE"
    return "AVAILABLE"


def _build_conditional_bilateral_scenario(
    inputs: ProjectEconomicInputs,
    majority_code: str,
    minority_code: str,
    treaty_slug: str,
    baseline_incentive_usd: float | None,
    personnel_attachment_facts: dict | None = None,
) -> dict | None:
    """Co-Pro Conditional Pricing Bridge — bridges a real, disclosed
    UNRESOLVED_FACTS treaty opportunity to real conditional economics,
    reusing every existing canonical mechanism unchanged:
      - treaty_engine's own real thresholds (solve_bilateral_minimum_
        contribution -- the deterministic portion, never guessed);
      - the SAME evaluate_bilateral_coproduction_opportunity adapter the
        home-anchored/candidate-pair discovery loops already call, now
        given the solved minimum contribution instead of None;
      - the SAME _price_candidate() every ordinary single-program
        candidate is priced through -- no separate co-pro pricing math.

    Generic over ANY bilateral treaty and ANY two candidate jurisdictions
    -- reads only treaty_slug/majority_code/minority_code/inputs, never a
    project ID, program name, or country pair by name.

    Returns None only when the treaty registry lookup itself fails (a
    genuine data-consistency gap, never silently swallowed to the caller
    as "no opportunity"). Otherwise returns a fully-disclosed dict —
    every assumed value tagged with a real fact_classification constant,
    every canonical-data gap named explicitly, never silently priced
    around.

    CORRECT_COPRO_ASSUMPTION_AND_PERSONNEL_POLICY — this treaty's own
    real personnel_requirement (treaty.personnel_requirement, read from
    the SAME registry row already fetched below -- never a second
    lookup) and this project's real attachment facts are now threaded
    into the SAME evaluate_bilateral_coproduction_opportunity() call the
    discovery loop already uses, so a treaty whose personnel clause IS
    researched cannot be conditionally priced around a real, unresolved
    or failed personnel question. When personnel_requirement is None
    (every real treaty today), this is a no-op -- byte-identical to
    calling this function without the new argument."""
    treaty = te.get_bilateral_treaty(majority_code, minority_code)
    if treaty is None:
        return None

    solved = solve_bilateral_minimum_contribution(treaty)

    scenario: dict = {
        "assumed_majority_contribution_pct": solved.majority_pct,
        "assumed_minority_contribution_pct": solved.minority_pct,
        "assumption_fact_classification": FACT_PROPOSED_CHANGE,
        "assumption_basis": (
            f"Deterministic minimum contribution split satisfying {treaty_slug}'s "
            f"own recorded majority_min_pct ({treaty.majority_min_pct}%) and "
            f"minority_min_pct ({treaty.minority_min_pct}%) thresholds -- the "
            "lowest lawful split this engine can construct without inventing a "
            "number the treaty itself does not require."
        ),
        "cultural_test_required": solved.cultural_test_required,
        "deterministically_solvable": solved.deterministically_solvable,
    }
    if not solved.deterministically_solvable:
        scenario["status"] = "USER_DECISION_REQUIRED"
        scenario["fact_classification"] = FACT_USER_CONFIRMATION_REQUIRED
        scenario["blocking_reason"] = solved.blocking_reason
        scenario["conditional_qualification_state"] = "UNRESOLVED_FACTS"
        return scenario

    result = evaluate_bilateral_coproduction_opportunity(
        majority_code, minority_code,
        majority_pct=solved.majority_pct, minority_pct=solved.minority_pct,
        cultural_test_passed=(True if solved.cultural_test_required else None),
        personnel_requirement=treaty.personnel_requirement,
        personnel_attachment_facts=personnel_attachment_facts,
    )
    if result is None or result.resolution_state != RESOLUTION_ELIGIBLE:
        scenario["status"] = "NOT_FEASIBLE"
        scenario["conditional_qualification_state"] = result.resolution_state if result else "INELIGIBLE"
        scenario["disqualification_reasons"] = list(result.disqualification_reasons) if result else (
            "Treaty's own recorded thresholds cannot be satisfied.",
        )
        return scenario

    scenario["conditional_qualification_state"] = RESOLUTION_ELIGIBLE
    scenario["unlocked_slugs"] = list(result.unlocked_slugs)

    # Optimizer P0 wiring remediation (2026-09-04), P0-3 — TREATY
    # CONDITIONAL BUDGET DOUBLE-COUNTING. Root cause (Codex, confirmed
    # live on LU GB/IE: gross $4,364,393, minority/majority minimums
    # 20%/20%, combined QPE $8,126,528 = 186.2% of gross): the loop below
    # used to call _price_candidate(inputs, code, priced_slug) — the SAME
    # kernel single/full_relocation candidates use — with the UNSCALED
    # `inputs.budget_lines`, once per participant. That prices the
    # production's ENTIRE gross budget independently in EVERY treaty
    # participant, as if each party received the whole project, rather
    # than allocating ONE source budget across the two participants.
    #
    # A bilateral treaty's own recorded majority_min_pct/minority_min_pct
    # are MINIMUM CONTRIBUTION FLOORS, not a full partition of the
    # budget by themselves (this treaty's own real thresholds are
    # 20%/20%, summing to only 40% — the remaining 60% is not stated by
    # any treaty fact). No producer-confirmed fact exists that says how
    # much MORE than its own floor either party contributes. The one
    # non-invented, definitionally-correct allocation this engine CAN
    # construct from the treaty's own real facts alone: the MINORITY
    # party contributes exactly its stated minimum (no more — no fact
    # justifies more), and the MAJORITY party — by definition the party
    # holding whatever share is left — takes the complement (1 -
    # minority_pct). This is the SAME canonical allocation semantics
    # every other structure already applies (one source budget, real
    # facts only, never an invented number); it is not a new percentage,
    # only the arithmetic complement of the treaty's own recorded
    # minority floor.
    #
    # Feasibility check: the majority party's OWN recorded minimum must
    # still be satisfied by that complement share. If the minority's
    # floor alone would push the majority's actual share below the
    # majority's own stated minimum (e.g. minority=60%, majority
    # min=50% -> complement=40% < 50%), no allocation can be constructed
    # from known facts, and — per the required invariant — this
    # scenario must NOT be marked fully_priced; it fails closed with an
    # explicit reason, exactly like the deterministically_solvable=False
    # branch above.
    minority_allocation_pct = solved.minority_pct / 100.0
    majority_allocation_pct = 1.0 - minority_allocation_pct
    if majority_allocation_pct * 100.0 + 1e-9 < solved.majority_pct:
        scenario["status"] = "USER_DECISION_REQUIRED"
        scenario["fact_classification"] = FACT_USER_CONFIRMATION_REQUIRED
        scenario["fully_priced"] = False
        scenario["conditional_qualification_state"] = "UNRESOLVED_FACTS"
        scenario["blocking_reason"] = (
            f"Treaty {treaty_slug}'s own recorded minority_min_pct ({treaty.minority_min_pct}%) "
            f"would leave the majority party only {majority_allocation_pct * 100:.1f}% of the "
            f"production budget, below the majority's own recorded minimum "
            f"({treaty.majority_min_pct}%). No producer-confirmed contribution split resolves "
            "this; a complete allocation cannot be constructed from known facts alone."
        )
        return scenario
    scenario["participant_allocation_pct"] = {
        majority_code: round(majority_allocation_pct * 100, 4),
        minority_code: round(minority_allocation_pct * 100, 4),
    }

    # Price every unlocked slug through the SAME canonical kernel every
    # ordinary candidate uses -- no new economics beyond the one real
    # source budget being ALLOCATED (scaled) across participants before
    # each participant's own share is priced. majority_unlocks price
    # against the majority party's own allocated share; minority_unlocks
    # against the minority party's. A slug with no canonical RateRule
    # (CANONICAL_DATA_GAP -- e.g. a program only ever represented in
    # legacy/superseded qualification data, never given canonical rate
    # doctrine) is disclosed by name, never priced around or invented.
    #
    # Co-Pro Conditional Pricing Data Reconnection: treaty_engine.py's own
    # unlock-list spelling is not always the same spelling the canonical
    # rate registry priced the program under (e.g. "nz_spgi" vs the
    # already-canonicalized "nz_spg_international") -- a real IDENTITY/
    # ALIAS MISMATCH, not a genuine data absence. Resolved through the
    # SAME existing, generic canonical-slug table canonical_stack_bridge.py
    # already consults for stacking-rule lookups -- never a per-slug
    # special case here.
    import dataclasses

    from app.data.program_rate_rules import _RULES_BY_PROGRAM
    from app.data.program_slug_aliases import canonical_slug as _canonical_program_slug

    def _allocated_inputs_for(pct: float) -> "ProjectEconomicInputs":
        """A scaled COPY of `inputs` whose every budget line is reduced
        to this participant's own allocated share of the ONE source
        budget -- never a second, independently-invented budget. Reuses
        _price_candidate's own kernel unmodified; only its input is a
        real fraction of the same real dollars, so no source account is
        ever counted more than once across the two participants (their
        shares sum to exactly 1.0 by construction above)."""
        scaled_lines = [
            dataclasses.replace(line, amount_usd=round(line.amount_usd * pct, 2))
            for line in inputs.budget_lines
        ]
        return dataclasses.replace(
            inputs,
            budget_lines=scaled_lines,
            gross_budget_usd=round(inputs.gross_budget_usd * pct, 2),
            leaf_account_sum_usd=(
                round(inputs.leaf_account_sum_usd * pct, 2)
                if inputs.leaf_account_sum_usd is not None else None
            ),
        )

    majority_inputs = _allocated_inputs_for(majority_allocation_pct)
    minority_inputs = _allocated_inputs_for(minority_allocation_pct)

    priced_components: list[dict] = []
    data_gaps: list[str] = []
    candidates_by_jurisdiction: dict[str, list[StackCandidate]] = {}
    for slug in result.unlocked_slugs:
        code = majority_code if slug in treaty.majority_unlocks else (
            minority_code if slug in treaty.minority_unlocks else majority_code
        )
        participant_inputs = majority_inputs if code == majority_code else minority_inputs
        priced_slug = _canonical_program_slug(slug)
        if priced_slug not in _RULES_BY_PROGRAM:
            data_gaps.append(slug)
            continue
        pricing, register, rr = _price_candidate(participant_inputs, code, priced_slug)
        if pricing is None or rr is None:
            data_gaps.append(slug)
            continue
        incentive = pricing.selected_incentive_usd or 0.0
        qualifying_spend = round(sum(
            a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
        ), 2)
        doctrine_record = _get_doctrine(priced_slug)
        candidates_by_jurisdiction.setdefault(code, []).append(StackCandidate(
            program_slug=priced_slug,
            jurisdiction_code=code,
            selected_incentive_usd=incentive,
            effective_rate=rr.modeled_rate,
            qualifying_spend_usd=qualifying_spend,
            incentive_type=doctrine_record.incentive_type if doctrine_record else "",
            qualifying_line_ids=frozenset(
                a.line_id for a in register if a.state == QualificationState.QUALIFIES
            ),
        ))
        priced_components.append({
            "jurisdiction_code": code, "program_slug": priced_slug,
            "modeled_rate": rr.modeled_rate, "selected_incentive_usd": incentive,
        })

    # Same-jurisdiction multi-slug unlocks (e.g. a majority country whose
    # treaty entry unlocks more than one of its own programs) must go
    # through the EXISTING stacking-compatibility engine, never a hand-
    # built sum -- reuses the identical price_program_group_stack every
    # ordinary multi-program candidate group already goes through.
    # Cross-jurisdiction totals (majority vs minority country -- the
    # normal bilateral case) are independent national incentives, not a
    # same-jurisdiction stacking question, so they are summed directly.
    total_conditional_incentive = 0.0
    stacking_groups: list[dict] = []
    # Codex global optimizer audit, P0-STACK-001: "When stackability is
    # unknown, publish no combined incentive or NPC." The prior behavior
    # fell back to a raw, unadjusted SUM whenever price_program_group_stack
    # returned None (no named, publishable rule covers the exact same-
    # jurisdiction program combination) -- disclosure (stacking_verified=
    # False) is not authorization, and that raw sum was still published as
    # conditional_incentive_usd/conditional_npc_usd, letting an economically
    # UNKNOWN combination rank and compare exactly like a verified one.
    # unresolved_stack_groups tracks every such group; its presence makes
    # the WHOLE scenario's combined economics null below, never a partial
    # guess -- the individual, already-priced legs in priced_components
    # remain fully visible and disclosed either way.
    unresolved_stack_groups: list[dict] = []
    for code, group in candidates_by_jurisdiction.items():
        if len(group) < 2 or not eligible_group_for_combination([c.jurisdiction_code for c in group]):
            total_conditional_incentive += sum(c.selected_incentive_usd for c in group)
            continue
        stack_result = price_program_group_stack(group)
        if stack_result is None:
            # No named, publishable stacking rule covers this exact group.
            # THE FIX: never sum the raw incentives into the scenario's
            # combined total -- an unknown relationship contributes no
            # economics at all until a named rule resolves it.
            unresolved_group = {
                "jurisdiction_code": code,
                "program_slugs": [c.program_slug for c in group],
                "stacking_verified": False,
                "rejection_reason_class": "RULE_DATA_INCOMPLETE",
                "note": (
                    "No named, publishable stacking rule covers this exact "
                    "program combination -- economics are withheld (never "
                    "summed as though independent) until a named "
                    "stacking-compatibility rule resolves this group."
                ),
            }
            stacking_groups.append(unresolved_group)
            unresolved_stack_groups.append(unresolved_group)
            continue
        # CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B:
        # the SAME generic pairwise-legality gate as the main candidate
        # loop -- a group containing a real hard incompatibility (e.g.
        # on_ofttc+on_opstc inside a larger mixed-rule-type group) must
        # never contribute economics to this scenario's combined total,
        # exactly like it must never be served as PRICED there.
        if stack_result.contains_blocking_incompatibility:
            _blocked_group = {
                "jurisdiction_code": code,
                "program_slugs": stack_result.program_slugs,
                "stacking_verified": False,
                "rejection_reason_class": "MUTUALLY_EXCLUSIVE_MEMBER_PAIR",
                "blocking_pairs": stack_result.blocking_pairs,
                "note": (
                    "This combination contains at least one mutually-exclusive "
                    "member pair -- economics are withheld (never summed) even "
                    "though other pairs within the group are compatible."
                ),
            }
            stacking_groups.append(_blocked_group)
            unresolved_stack_groups.append(_blocked_group)
            continue
        total_conditional_incentive += stack_result.adjusted_incentive_usd
        stacking_groups.append({
            "jurisdiction_code": code,
            "program_slugs": stack_result.program_slugs,
            "stacking_verified": True,
            "rule_type": stack_result.rule_type,
            "raw_incentive_usd": stack_result.raw_incentive_usd,
            "adjusted_incentive_usd": stack_result.adjusted_incentive_usd,
            "stacking_reduction_usd": stack_result.stacking_reduction_usd,
            "legal_review_required": stack_result.legal_review_required,
            "disclosed_limitations": stack_result.disclosed_limitations,
        })

    scenario["priced_components"] = priced_components
    scenario["canonical_data_gaps"] = data_gaps
    if stacking_groups:
        scenario["stacking_groups"] = stacking_groups
    if data_gaps:
        scenario["canonical_data_gap_note"] = (
            f"{', '.join(data_gaps)} unlock under this treaty per treaty_engine's "
            "own registry, but carry no canonical RateRule in the current served "
            "registry -- a real, disclosed data gap, not priced, not invented, "
            "not researched this pass."
        )

    if unresolved_stack_groups:
        # Codex P0-STACK-001: an unknown same-jurisdiction stacking
        # relationship must publish NO combined incentive or NPC --
        # explicit RULE_DATA_INCOMPLETE, machine-readable, never a
        # silently-summed number that would rank/compare as if verified.
        scenario["conditional_incentive_usd"] = None
        scenario["conditional_npc_usd"] = None
        scenario["fully_priced"] = False
        scenario["status"] = "RULE_DATA_INCOMPLETE"
        scenario["blocking_reason"] = (
            "Unknown stacking relationship for "
            + "; ".join(
                f"{g['jurisdiction_code']}: {'+'.join(g['program_slugs'])}"
                for g in unresolved_stack_groups
            )
            + " -- no named, publishable rule authorizes this combination, so no "
              "combined economics can be published. This candidate remains visible "
              "and conditional, never ranked as a priced/comparable structure."
        )
    elif priced_components:
        conditional_npc = round(inputs.gross_budget_usd - total_conditional_incentive, 2)
        scenario["conditional_incentive_usd"] = round(total_conditional_incentive, 2)
        scenario["conditional_npc_usd"] = conditional_npc
        scenario["fully_priced"] = not data_gaps
        if baseline_incentive_usd is not None:
            baseline_npc = round(inputs.gross_budget_usd - baseline_incentive_usd, 2)
            scenario["baseline_npc_usd"] = baseline_npc
            scenario["net_benefit_vs_baseline_usd"] = round(baseline_npc - conditional_npc, 2)
        scenario["status"] = "CONDITIONAL_PROJECT_FACT_DEPENDENT"
    else:
        scenario["status"] = "CANONICAL_DATA_GAP"
        scenario["fully_priced"] = False

    return scenario


def _price_component_relocation_candidate(
    inputs: ProjectEconomicInputs,
    home_code: str,
    home_program_slug: str | None,
    target_code: str,
    target_program_slug: str,
    component: str,
):
    """Existing Optimizer/Stacker Reconnection, Task A (component/split).
    Reuses the EXISTING production_allocation.StructureSpec
    'component_relocation' type and price_allocated_structure kernel —
    no new allocation or pricing logic. Routes ONE movable component
    (post/vfx/music — production_allocation.MOVABLE_COMPONENTS) to
    `target_code`; every other account stays exactly where
    derive_account_allocation would otherwise place it (principal
    photography/travel at the shoot location, overhead/administration at
    the production's own domicile). This is why no territorial spend is
    invented: the ONLY thing this candidate changes from the single-
    program candidates already generated is WHERE one real, already-
    budgeted component is incurred — the dollar amounts are the
    project's own, never fabricated. price_segment resolves each
    jurisdiction's own rate internally from its own allocated accounts —
    no pre-resolved rate is threaded through here.
    """
    incentive_programs: dict[str, str] = {}
    if home_program_slug:
        incentive_programs[home_code] = home_program_slug
    incentive_programs[target_code] = target_program_slug
    spec = StructureSpec(
        structure_id=f"CANON-COMPONENT-{home_code}-{component}-{target_code}-{target_program_slug}",
        structure_type="component_relocation",
        label=f"{home_code} anchor — {component} routed to {target_code}",
        primary_jurisdiction=home_code,
        participants=(home_code, target_code),
        incentive_programs=incentive_programs,
        component_routes={component: target_code},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    # target_code, not home_code: the component itself is what relocates,
    # so the normalization delta is against the target jurisdiction, using
    # the SAME allocation basis price_allocated_structure prices below.
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, target_code, allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        # Producer Display Names + Budget Rail User Assumptions closeout —
        # threads the producer's persisted financing-cost assumption
        # (ProjectFact, same USER_OVERRIDE mechanism as contingency above)
        # into the existing financing_cost_usd NPC parameter. Absent
        # (None) resolves to 0.0 — price_allocated_structure's own
        # documented default ("explicit inputs only, never a silent
        # assumption"), never assumed here.
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        # Codex final runtime remediation — the SAME generic ProjectFact
        # mechanism as financing_cost_usd/contingency above, threading a
        # producer's real, evidenced program-eligibility/native-currency
        # facts into resolve_program_rate() through the actual production
        # pipeline. Absent (empty) is byte-identical prior behavior for
        # every program without such a condition.
        evidenced_requirement_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return spec, allocation, pricing



class _InvalidCombinedAllocation(Exception):
    """Raised by _price_combined_coproduction_component_candidate when a
    claimed participant would receive a zero or invalid allocation --
    Codex global optimizer audit, P0-COMB-001 remediation: "reject any
    claimed participant with zero or invalid allocation." Carries the
    exact reason so the caller can persist a real, machine-readable
    rejection row instead of silently skipping the attempt."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _best_priced_treaty_side_candidate(
    inputs: ProjectEconomicInputs, code: str, priced_by_code: dict[str, list],
    treaty_unlocks: tuple[str, ...],
):
    """Codex D743 real-treaty-proof remediation: `priced_by_code[code]`
    only contains candidates the MAIN discovery loop happened to price
    for that EXACT code -- a bare federal country code (e.g. "CA") that
    was only synthetically added to the treaty-matching candidate
    universe via P0-CAND-003's prefix union (never itself a genuine
    discovery result) can be absent from priced_by_code even though its
    own treaty-unlocked program prices perfectly well when attempted
    directly (confirmed live: CA/ca_federal_cptc). Falls back to
    directly pricing each of the treaty's own real unlocked slugs for
    this side via the SAME _price_candidate every other path uses,
    exactly the pattern _build_conditional_bilateral_scenario already
    established for this identical problem -- never invents a program,
    only prices the treaty's own real, registered unlocks."""
    existing = priced_by_code.get(code, [])
    best = max(existing, key=lambda c: c.selected_incentive_usd, default=None)
    if best is not None:
        return best
    best_incentive = None
    best_candidate = None
    for slug in treaty_unlocks:
        pricing, register, rr = _price_candidate(inputs, code, slug)
        if pricing is None or rr is None:
            continue
        incentive = pricing.selected_incentive_usd or 0.0
        if best_incentive is None or incentive > best_incentive:
            best_incentive = incentive
            qualifying_spend = round(sum(
                a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
            ), 2)
            doctrine_record = _get_doctrine(slug)
            best_candidate = StackCandidate(
                program_slug=slug, jurisdiction_code=code,
                selected_incentive_usd=incentive, effective_rate=rr.modeled_rate,
                qualifying_spend_usd=qualifying_spend,
                incentive_type=doctrine_record.incentive_type if doctrine_record else "",
                qualifying_line_ids=frozenset(
                    a.line_id for a in register if a.state == QualificationState.QUALIFIES
                ),
            )
    return best_candidate


def _all_priced_treaty_side_candidates(
    inputs: ProjectEconomicInputs, code: str, priced_by_code: dict[str, list],
    treaty_unlocks: tuple[str, ...],
):
    """Eight-control closeout, HO-003 discovery-suppression fix: the
    Locked Structural Policy's own "ranking must never suppress feasible
    discovery" doctrine (already enforced for the movable-component
    target side of a combined co-production candidate -- "never just the
    highest") extends here to the treaty PARTNER side. The prior
    `_best_priced_treaty_side_candidate` (still used by callers that
    genuinely need exactly one, e.g. authorized-local-stack lookups)
    collapsed to a SINGLE candidate two different ways: (1) when
    `priced_by_code[code]` was non-empty it took that jurisdiction's own
    OVERALL best-priced program regardless of whether it was even one of
    this treaty's real unlocks (confirmed live: AU's au_pdv_offset
    out-priced au_producer_offset for a real fixture and silently won,
    even though au_producer_offset -- not au_pdv_offset -- is
    uk-au-bilateral's own real, registered minority_unlocks entry); (2)
    the max()-over-treaty_unlocks fallback path also kept only the single
    best.

    This function instead enumerates and returns EVERY program in
    `treaty_unlocks` that independently prices for this jurisdiction --
    filtered to the treaty's own real, registered unlocks (never a
    program merely priceable for unrelated reasons), preferring an
    already-discovered `priced_by_code` entry when one exists (reuses
    real, already-computed pricing) and falling back to pricing the slug
    directly (same `_price_candidate` every other path uses) otherwise --
    the same bare-federal-code gap `_best_priced_treaty_side_candidate`'s
    own docstring already documents. Never invents a program outside
    `treaty_unlocks`; returns `[]` (never `None`, never a fabricated
    single candidate) when nothing in `treaty_unlocks` prices at all.
    Callers try and persist a real terminal disposition for EVERY
    returned candidate -- ranking/selection happens only AFTER
    persistence, in the served view, never before."""
    existing_by_slug = {c.program_slug: c for c in priced_by_code.get(code, [])}
    results: list = []
    for slug in treaty_unlocks:
        if slug in existing_by_slug:
            results.append(existing_by_slug[slug])
            continue
        pricing, register, rr = _price_candidate(inputs, code, slug)
        if pricing is None or rr is None:
            continue
        incentive = pricing.selected_incentive_usd or 0.0
        qualifying_spend = round(sum(
            a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
        ), 2)
        doctrine_record = _get_doctrine(slug)
        results.append(StackCandidate(
            program_slug=slug, jurisdiction_code=code,
            selected_incentive_usd=incentive, effective_rate=rr.modeled_rate,
            qualifying_spend_usd=qualifying_spend,
            incentive_type=doctrine_record.incentive_type if doctrine_record else "",
            qualifying_line_ids=frozenset(
                a.line_id for a in register if a.state == QualificationState.QUALIFIES
            ),
        ))
    return results


def _price_combined_coproduction_component_candidate(
    inputs: ProjectEconomicInputs,
    home_code: str, home_program_slug: str,
    partner_code: str, partner_program_slug: str,
    component_target_code: str, component_target_program_slug: str,
    component: str, treaty_slug: str,
    majority_pct: float, minority_pct: float,
):
    """Codex global optimizer audit, P0-COMB-001 (rejected on first pass,
    remediated here): "one conserved executable allocation topology
    capable of combining: official co-production; component allocation;
    anchor jurisdiction; authorized local stacks on allocated sides."

    Codex's rejection, first pass: this function supplied ONLY
    component_routes -- ownership_shares/account_splits were empty, so
    derive_account_allocation's own precedence rules (see its docstring)
    fell through every non-component account to the primary jurisdiction
    alone. The treaty partner conserved zero dollars: real co-production
    total-budget conservation without a co-production is not a
    co-production.

    THE FIX: majority_pct/minority_pct are the SAME real, evidenced
    per-treaty contribution facts P0-QUAL-001 already threads into
    evaluate_bilateral_coproduction_opportunity for THIS exact (treaty_
    slug, home_code, partner_code) scope -- never invented here, only
    reused. Every non-memo, non-routed-component budget line is given an
    explicit spec.account_splits entry ({home_code: majority_pct/100,
    partner_code: minority_pct/100}) -- derive_account_allocation's
    HIGHEST-precedence rule (explicit producer split beats every other
    routing rule, including component_routes), so the treaty partner
    receives its real, evidenced contractual share of every account the
    routed component does not claim. The routed component's own accounts
    are deliberately EXCLUDED from account_splits so component_routes
    (precedence rule 3) still sends them entirely to component_target_code
    -- a component relocates as a whole, it does not fractionally split
    between co-production parties.

    Raises _InvalidCombinedAllocation (never returns a silently-zeroed
    participant) when majority_pct/minority_pct are missing, non-positive,
    or when the resulting allocation gives ANY of the three participants
    zero allocated dollars -- "reject any claimed participant with zero
    or invalid allocation," Codex's own required remediation text.

    Reuses the SAME StructureSpec + derive_account_allocation +
    price_allocated_structure kernel every other structure type is priced
    through -- structure_type="hybrid" is a STRUCTURE_TYPES entry the
    architecture already reserved for exactly this combination.
    derive_account_allocation's existing, already-tested invariants
    (is_complete/conserves/no duplicate account codes) remain the
    structural guarantee against double allocation. "Authorized local
    stacks on allocated sides" is layered on AFTER this base pricing by
    the caller (now attempted on every allocated side, not the anchor
    alone -- see _authorized_local_stack_for_side's call sites), via the
    same price_program_group_stack every other stacking path uses -- this
    function prices the base (unstacked) topology only.
    """
    if majority_pct is None or minority_pct is None or majority_pct <= 0 or minority_pct <= 0:
        raise _InvalidCombinedAllocation(
            f"{partner_code} claims a co-production share under {treaty_slug} but no "
            "positive, evidenced majority_pct/minority_pct contribution fact is on file "
            f"(majority_pct={majority_pct}, minority_pct={minority_pct}) -- a claimed "
            "participant may never receive an invented or zero allocation."
        )
    majority_frac = majority_pct / 100.0
    minority_frac = minority_pct / 100.0
    _split_total = round(majority_frac + minority_frac, 6)
    if _split_total <= 0:
        raise _InvalidCombinedAllocation(
            f"{home_code}/{partner_code} contribution shares under {treaty_slug} sum to "
            f"{_split_total} -- cannot derive a valid non-zero split."
        )
    # Normalize to exactly 1.0 (derive_account_allocation requires account_splits
    # percentages to sum to 1.0 within 1e-6) -- the RATIO between the two real,
    # evidenced shares is preserved exactly; only a >100%-summing pair (e.g. a
    # treaty's own recorded minimum thresholds, not a hard 100% split) is rescaled.
    majority_frac, minority_frac = majority_frac / _split_total, minority_frac / _split_total

    account_splits: dict[str, dict[str, float]] = {}
    for line in inputs.budget_lines:
        if line.is_memo or line.account_code in account_splits:
            continue
        category = line.spend_category or inputs.spend_category_by_code.get(line.account_code)
        if component_for(category) == component:
            continue  # routed component's own accounts move as a whole -- see docstring
        account_splits[line.account_code] = {home_code: majority_frac, partner_code: minority_frac}

    spec = StructureSpec(
        structure_id=(
            f"CANON-COMBINED-{home_code}-{partner_code}-{treaty_slug}-"
            f"{component}-{component_target_code}-{component_target_program_slug}"
        ),
        structure_type="hybrid",
        label=(
            f"{home_code} + {partner_code} co-production ({treaty_slug}) "
            f"+ {component} routed to {component_target_code}"
        ),
        primary_jurisdiction=home_code,
        participants=(home_code, partner_code, component_target_code),
        incentive_programs={
            home_code: home_program_slug,
            partner_code: partner_program_slug,
            component_target_code: component_target_program_slug,
        },
        component_routes={component: component_target_code},
        account_splits=account_splits,
        treaty_slug=treaty_slug,
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    _by_jur = allocation.allocated_by_jurisdiction()
    _zero_participants = [p for p in spec.participants if not _by_jur.get(p)]
    if _zero_participants:
        raise _InvalidCombinedAllocation(
            f"Participant(s) {_zero_participants} would receive zero allocated dollars "
            f"in this {home_code}+{partner_code}+{component_target_code} combined "
            "structure -- a claimed participant may never receive a zero allocation."
        )
    # Same convention as _price_component_relocation_candidate: the
    # normalization delta is computed against the jurisdiction the money
    # actually moves to (the component target), using the same allocation
    # basis price_allocated_structure prices below.
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, component_target_code, allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        evidenced_requirement_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return spec, allocation, pricing


def _price_combined_coproduction_multi_component_candidate(
    inputs: ProjectEconomicInputs,
    home_code: str, home_program_slug: str,
    partner_code: str, partner_program_slug: str,
    component_targets: list,  # list[tuple[component, target_code, target_program_slug]], N >= 2
    treaty_slug: str,
    majority_pct: float, minority_pct: float,
):
    """Eight-control closeout, HO-013: the direct N-component
    generalization of _price_combined_coproduction_component_candidate
    (which only ever routes ONE movable component). StructureSpec.
    component_routes is already a dict[str, str] -- derive_account_
    allocation already supports routing an ARBITRARY NUMBER of distinct
    component types to distinct target jurisdictions simultaneously; the
    single-component limit was entirely in the CALLER's own loop
    structure (one _combined_component tried at a time), never in the
    underlying allocation kernel. No new allocation model.

    No double-counting is structurally possible: each routed component
    (e.g. "post" vs "vfx") is, by construction, a DISJOINT category-based
    subset of the real budget lines (component_for() maps each real
    spend_category to exactly one component label) -- the same
    same-cost-refusal-by-construction principle every other mechanism in
    this file already relies on, now simply applied to 2+ components in
    one structure instead of 1. account_splits excludes the union of
    every routed component's own accounts (never just one), so the
    treaty partner's split share is computed over the correct remaining
    base regardless of how many components are routed away.

    Raises _InvalidCombinedAllocation on the same conditions as the
    2-way/3-way siblings: missing/non-positive contribution facts, a
    duplicate component or duplicate target jurisdiction across the
    requested component_targets (never silently collapsed), or any
    participant receiving zero allocated dollars."""
    if len(component_targets) < 2:
        raise _InvalidCombinedAllocation(
            "_price_combined_coproduction_multi_component_candidate requires >= 2 "
            "simultaneously-routed components -- use the single-component sibling for one."
        )
    _components = [c for c, _code, _slug in component_targets]
    if len(set(_components)) != len(_components):
        raise _InvalidCombinedAllocation(
            f"Duplicate component in {component_targets!r} -- each routed component must be distinct."
        )
    _target_codes = [code for _c, code, _slug in component_targets]
    if len(set(_target_codes)) != len(_target_codes):
        raise _InvalidCombinedAllocation(
            f"Duplicate target jurisdiction in {component_targets!r} -- each routed component's "
            "target must be a distinct jurisdiction."
        )
    if majority_pct is None or minority_pct is None or majority_pct <= 0 or minority_pct <= 0:
        raise _InvalidCombinedAllocation(
            f"{partner_code} claims a co-production share under {treaty_slug} but no "
            "positive, evidenced majority_pct/minority_pct contribution fact is on file "
            f"(majority_pct={majority_pct}, minority_pct={minority_pct}) -- a claimed "
            "participant may never receive an invented or zero allocation."
        )
    majority_frac = majority_pct / 100.0
    minority_frac = minority_pct / 100.0
    _split_total = round(majority_frac + minority_frac, 6)
    if _split_total <= 0:
        raise _InvalidCombinedAllocation(
            f"{home_code}/{partner_code} contribution shares under {treaty_slug} sum to "
            f"{_split_total} -- cannot derive a valid non-zero split."
        )
    majority_frac, minority_frac = majority_frac / _split_total, minority_frac / _split_total

    account_splits: dict[str, dict[str, float]] = {}
    for line in inputs.budget_lines:
        if line.is_memo or line.account_code in account_splits:
            continue
        category = line.spend_category or inputs.spend_category_by_code.get(line.account_code)
        if component_for(category) in _components:
            continue  # every routed component's own accounts move as a whole -- see docstring
        account_splits[line.account_code] = {home_code: majority_frac, partner_code: minority_frac}

    spec = StructureSpec(
        structure_id=(
            f"CANON-COMBINED-MULTI-{home_code}-{partner_code}-{treaty_slug}-"
            + "-".join(f"{c}-{code}-{slug}" for c, code, slug in component_targets)
        ),
        structure_type="hybrid",
        label=(
            f"{home_code} + {partner_code} co-production ({treaty_slug}) + "
            + ", ".join(f"{c} routed to {code}" for c, code, _slug in component_targets)
        ),
        primary_jurisdiction=home_code,
        participants=(home_code, partner_code, *_target_codes),
        incentive_programs={
            home_code: home_program_slug,
            partner_code: partner_program_slug,
            **{code: slug for _c, code, slug in component_targets},
        },
        component_routes={c: code for c, code, _slug in component_targets},
        account_splits=account_splits,
        treaty_slug=treaty_slug,
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    _by_jur = allocation.allocated_by_jurisdiction()
    _zero_participants = [p for p in spec.participants if not _by_jur.get(p)]
    if _zero_participants:
        raise _InvalidCombinedAllocation(
            f"Participant(s) {_zero_participants} would receive zero allocated dollars in this "
            f"{home_code}+{partner_code}+{'+'.join(_target_codes)} combined structure -- a "
            "claimed participant may never receive a zero allocation."
        )
    # Normalizes against the FIRST routed component's own target -- an
    # arbitrary but deterministic, disclosed choice for N>1 simultaneous
    # relocation targets, exactly the same secondary-correction status
    # documented on the N-way multilateral sibling above.
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, _target_codes[0], allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        evidenced_requirement_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return spec, allocation, pricing


def _price_combined_coproduction_pair_candidate(
    inputs: ProjectEconomicInputs,
    home_code: str, home_program_slug: str,
    partner_code: str, partner_program_slug: str,
    treaty_slug: str,
    majority_pct: float, minority_pct: float,
):
    """Eight-control closeout, multi-principal composition (REG-4;
    HO-003/007/013's own pairwise treaty leg, independent of whichever
    third movable component they also name). A PURE two-party official
    co-production -- home_code + partner_code, EACH claiming its own real
    national principal-production program on its own real, treaty-
    evidenced contribution share -- with no third movable component
    required at all. This is the sibling of
    _price_combined_coproduction_component_candidate with the routed
    component omitted entirely: every non-memo account (not just the
    ones a routed component doesn't claim) is split home_code/
    partner_code by the SAME real, evidenced majority_pct/minority_pct
    contribution facts _price_combined_coproduction_component_candidate
    already uses -- never invented here, only reused, and never
    guessed when no real fact is on file (see the same _InvalidCombinedAllocation
    guard below). Two SIMULTANEOUS principal_production legs is exactly
    the shape structural_archetype_generator.py's own generate_
    structural_candidate already accepts (confirmed via HO-003's own
    direct-generator test); this function is the missing REAL-runtime
    allocation source for that shape, using the existing treaty bridge's
    own already-evidenced contribution facts -- never a guessed split.

    Raises _InvalidCombinedAllocation on the same conditions as the
    three-way sibling: missing/non-positive contribution facts, or a
    zero-dollar allocation for either participant."""
    if majority_pct is None or minority_pct is None or majority_pct <= 0 or minority_pct <= 0:
        raise _InvalidCombinedAllocation(
            f"{partner_code} claims a co-production share under {treaty_slug} but no "
            "positive, evidenced majority_pct/minority_pct contribution fact is on file "
            f"(majority_pct={majority_pct}, minority_pct={minority_pct}) -- a claimed "
            "participant may never receive an invented or zero allocation."
        )
    majority_frac = majority_pct / 100.0
    minority_frac = minority_pct / 100.0
    _split_total = round(majority_frac + minority_frac, 6)
    if _split_total <= 0:
        raise _InvalidCombinedAllocation(
            f"{home_code}/{partner_code} contribution shares under {treaty_slug} sum to "
            f"{_split_total} -- cannot derive a valid non-zero split."
        )
    majority_frac, minority_frac = majority_frac / _split_total, minority_frac / _split_total

    account_splits: dict[str, dict[str, float]] = {
        line.account_code: {home_code: majority_frac, partner_code: minority_frac}
        for line in inputs.budget_lines if not line.is_memo
    }

    spec = StructureSpec(
        structure_id=f"CANON-COMBINED-PAIR-{home_code}-{partner_code}-{treaty_slug}",
        structure_type="hybrid",
        label=f"{home_code} + {partner_code} co-production ({treaty_slug})",
        primary_jurisdiction=home_code,
        participants=(home_code, partner_code),
        incentive_programs={home_code: home_program_slug, partner_code: partner_program_slug},
        account_splits=account_splits,
        treaty_slug=treaty_slug,
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    _by_jur = allocation.allocated_by_jurisdiction()
    _zero_participants = [p for p in spec.participants if not _by_jur.get(p)]
    if _zero_participants:
        raise _InvalidCombinedAllocation(
            f"Participant(s) {_zero_participants} would receive zero allocated dollars "
            f"in this {home_code}+{partner_code} combined structure -- a claimed "
            "participant may never receive a zero allocation."
        )
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, partner_code, allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        evidenced_requirement_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return spec, allocation, pricing


def _price_combined_multilateral_coproduction_candidate(
    inputs: ProjectEconomicInputs,
    participants: list,  # list[tuple[country_code, program_slug]], N >= 3
    treaty_slug: str,
    country_pcts: dict,  # {country_code: real evidenced pct}
):
    """Eight-control closeout, HO-012: a genuine N-way (N>=3) multilateral
    co-production (Eurimages/European Convention) -- each real member
    country claims its OWN real, independently-priceable national
    program on its own real, evidenced contribution share. The direct
    N-way generalization of _price_combined_coproduction_pair_candidate:
    the SAME real, evidenced (never invented) country_pcts this file's
    own evaluate_eurimages_coproduction_opportunity() already reads
    become an explicit spec.account_splits entry (derive_account_
    allocation's own highest-precedence rule) across every non-memo
    account, reusing price_allocated_structure unchanged. No new
    allocation model, no per-pair special case -- account_splits already
    accepts an arbitrary {jurisdiction: fraction} mapping of any size.

    Raises _InvalidCombinedAllocation when any participant's contribution
    fact is missing/non-positive, or when the resulting allocation gives
    any participant zero allocated dollars -- identical guardrails to the
    2-way sibling, generalized to N parties."""
    if len(participants) < 2:
        raise _InvalidCombinedAllocation("A multilateral co-production requires at least 2 real parties.")
    for code, _slug in participants:
        pct = country_pcts.get(code)
        if pct is None or pct <= 0:
            raise _InvalidCombinedAllocation(
                f"{code} claims a multilateral co-production share under {treaty_slug} but no "
                f"positive, evidenced contribution-share fact is on file (pct={pct}) -- a claimed "
                "participant may never receive an invented or zero allocation."
            )
    total_pct = sum(country_pcts[code] for code, _ in participants)
    if total_pct <= 0:
        raise _InvalidCombinedAllocation(
            f"Combined multilateral contribution shares under {treaty_slug} sum to {total_pct} "
            "-- cannot derive a valid non-zero split."
        )
    # Preserves the real ratio between every party's own evidenced share;
    # only rescaled if the real shares do not already sum to exactly 100
    # (the same normalization the 2-way sibling already applies).
    fracs = {code: country_pcts[code] / total_pct for code, _ in participants}

    account_splits: dict[str, dict[str, float]] = {
        line.account_code: dict(fracs)
        for line in inputs.budget_lines if not line.is_memo
    }

    participant_codes = tuple(code for code, _ in participants)
    spec = StructureSpec(
        structure_id=f"CANON-COMBINED-MULTI-{'-'.join(participant_codes)}-{treaty_slug}",
        structure_type="hybrid",
        label=f"{'+'.join(participant_codes)} multilateral co-production ({treaty_slug})",
        primary_jurisdiction=participant_codes[0],
        participants=participant_codes,
        incentive_programs=dict(participants),
        account_splits=account_splits,
        treaty_slug=treaty_slug,
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines, spend_category_by_code=inputs.spend_category_by_code,
        spec=spec, stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    _by_jur = allocation.allocated_by_jurisdiction()
    _zero_participants = [p for p in participant_codes if not _by_jur.get(p)]
    if _zero_participants:
        raise _InvalidCombinedAllocation(
            f"Participant(s) {_zero_participants} would receive zero allocated dollars in this "
            f"{'+'.join(participant_codes)} multilateral structure -- a claimed participant may "
            "never receive a zero allocation."
        )
    # Normalizes against the LAST participant (an arbitrary but
    # deterministic, disclosed choice -- for N>2 real parties there is no
    # single canonical "new location" the way the 2-way sibling's partner_
    # code is; the normalization delta itself is a small, secondary
    # correction, never the primary economics, exactly as documented on
    # price_segment's own gross_budget_usd/travel parameters).
    _travel_delta, _fx_delta, _local_cost_delta = _relocation_normalization(
        inputs, participant_codes[-1], allocation.total_allocated_usd,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=_travel_delta,
        fx_delta_usd=_fx_delta,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=_local_cost_delta,
        production_type=inputs.production_type,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
        financing_cost_usd=inputs.financing_cost_usd or 0.0,
        evidenced_requirement_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return spec, allocation, pricing


def _authorized_local_stack_for_side(
    priced_by_code: dict[str, list],
    side_code: str, side_program_slug: str,
):
    """P0-COMB-001, "authorized local stacks on allocated sides": checks
    whether `side_code` (one of the combined structure's own allocated
    sides) has a SECOND, distinct, same-jurisdiction priced candidate
    beyond the one already claimed by the base combined structure
    (`side_program_slug`). Returns (stack_result, group) where
    stack_result is price_program_group_stack's own result (None if no
    named, publishable rule covers this exact combination -- P0-STACK-001's
    own fail-closed rule, reused unchanged here) and `group` is the
    candidate pair actually attempted (empty if there is no second
    candidate to attempt at all -- distinct from "attempted and
    unresolved"). Only a resolved NAMED rule may ever be applied to the
    base structure's economics — an unresolved attempt is reported to the
    caller for retention as a REJECTED candidate, never silently applied
    and never silently dropped."""
    same_jurisdiction = [
        c for c in priced_by_code.get(side_code, []) if c.jurisdiction_code == side_code
    ]
    if len(same_jurisdiction) < 2:
        return None, []
    base = next((c for c in same_jurisdiction if c.program_slug == side_program_slug), None)
    other = max(
        (c for c in same_jurisdiction if c.program_slug != side_program_slug),
        key=lambda c: c.selected_incentive_usd, default=None,
    )
    if base is None or other is None:
        return None, []
    group = [base, other]
    if not eligible_group_for_combination([c.jurisdiction_code for c in group]):
        return None, group
    return price_program_group_stack(group), group


def _apply_authorized_stacks_to_combined_sides(
    priced_by_code: dict[str, list],
    sides: list[tuple[str, str]],
):
    """Codex global optimizer audit, P0-COMB-001 remediation: "support
    authorized stacks on every allocated side, not only the anchor."
    Calls _authorized_local_stack_for_side once per (side_code,
    side_program_slug) pair in `sides` (the combined structure's own
    allocated participants -- anchor, treaty partner, AND component
    target) instead of the anchor alone. Returns (total_delta,
    stacking_notes, stacked_program_slugs, unresolved) where
    `unresolved` is a list of (side_code, group) pairs for every side
    with a second same-jurisdiction candidate but no named, publishable
    rule -- the caller persists each as its OWN retained rejected
    candidate, exactly as the anchor-only version already did, just now
    for every side rather than one."""
    total_delta = 0.0
    notes: list[str] = []
    stacked_slugs: list[str] = []
    unresolved: list[tuple[str, list]] = []
    for side_code, side_program_slug in sides:
        stack_result, group = _authorized_local_stack_for_side(priced_by_code, side_code, side_program_slug)
        if stack_result is not None:
            delta = round(
                stack_result.adjusted_incentive_usd
                - next((c.selected_incentive_usd for c in group if c.program_slug == side_program_slug), 0.0),
                2,
            )
            total_delta = round(total_delta + delta, 2)
            notes.append(
                f"Authorized local stack on {side_code}: {'+'.join(stack_result.program_slugs)} "
                f"via named rule '{stack_result.rule_type}', adding ${delta:,.2f}."
            )
            stacked_slugs.extend(stack_result.program_slugs)
        elif group:
            unresolved.append((side_code, group))
    return total_delta, notes, stacked_slugs, unresolved


def _classify_component_rejection(blockers: tuple[str, ...] | list[str]) -> tuple[str, str]:
    """Optimizer FINAL closeout, P1-REJ-001 — classify a rejected
    component-relocation attempt's real blocker text into the SAME
    rejection_reason_class vocabulary the full_relocation/single_country
    reject path already uses (STATUS_RULE_REJECTED /
    STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT), plus MINIMUM_SPEND_FAIL
    for the specific, dominant real failure mode confirmed in the
    rejection ledger: `evaluate_requirements_gate`'s own
    min_local_spend_usd/min_total_budget_usd failure text (see
    allocation_pricing.py's `_LABELS` dict and its "mandatory eligibility
    requirement FAILED" blocker string). Never invents a new taxonomy —
    reuses the exact real blocker text the pricing kernel already
    produced, just as the full_relocation branch already does with
    `pricing.blockers`."""
    text = "; ".join(blockers) if blockers else ""
    if "minimum-spend" in text or "minimum-budget" in text or "mandatory eligibility requirement" in text:
        return STATUS_RULE_REJECTED, "MINIMUM_SPEND_FAIL"
    if "does not conserve" in text or "Unallocated accounts" in text or "Duplicate account" in text:
        return STATUS_RULE_REJECTED, "STATUTORY_CONDITIONS_UNMET"
    return STATUS_RULE_REJECTED, "OTHER_EXPLICIT"


def _opportunities_for_candidate(
    inputs: ProjectEconomicInputs, code: str, program_slug: str, register, rate_resolution,
    role_known_codes: dict[str, tuple[str, ...]] | None = None,
) -> list[dict]:
    """Reinvestment + Qualification Opportunity Optimization — attaches
    real, canonical-data-driven opportunities to a priced candidate.
    Every input here is already computed by the existing canonical
    pricing pass (register, resolved rate) or read directly off the
    project's own real budget lines — never invented. See
    canonical_opportunity_bridge.py's own module docstring for the
    forensic-recovery finding (ProgramRequirementsProfile + inkind_
    contribution.py both EXISTED, engine-agnostic, disconnected)."""
    opportunities: list[dict] = []

    # Real per-component spend totals (post/vfx/music/above_the_line —
    # production_allocation.component_for()'s own vocabulary), computed
    # once from the SAME real budget lines every other candidate branch
    # reads — never invented, never re-derived per opportunity type.
    component_spend: dict[str, float] = {}
    for line in inputs.budget_lines:
        if line.is_memo:
            continue
        # Codex BPI-002: line's own category wins; dict is fallback only.
        comp = component_for(line.spend_category or inputs.spend_category_by_code.get(line.account_code))
        component_spend[comp] = round(component_spend.get(comp, 0.0) + line.amount_usd, 2)

    current_atl_spend = component_spend.get("above_the_line", 0.0)
    fee_opp = discover_fee_cap_headroom_opportunity(
        code, program_slug, current_atl_spend, inputs.gross_budget_usd, rate_resolution.modeled_rate,
    )
    if fee_opp is not None:
        opportunities.append(opportunity_to_dict(fee_opp))

    actual_local_spend = round(sum(
        a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
    ), 2)
    gap_opps = discover_qualification_gap_opportunity(
        code, program_slug, actual_local_spend, inputs.gross_budget_usd,
    )
    for gap_opp in gap_opps:
        opportunities.append(opportunity_to_dict(gap_opp))

    cultural_opp = discover_cultural_test_gap_opportunity(code, program_slug)
    if cultural_opp is not None:
        opportunities.append(opportunity_to_dict(cultural_opp))

    # Worldwide Jurisdiction National/Cultural Status Completion, Task 10
    # — a real, primary-authority-confirmed SEPARATE national/cultural
    # pathway (e.g. Canada's CPTC vs this candidate's PSTC) surfaced as a
    # disclosure-only opportunity when this candidate is priced under the
    # jurisdiction's confirmed foreign/service pathway. Never fabricates
    # an economic figure; never gates this candidate's own real pricing.
    national_status_opp = discover_national_status_opportunity(code, program_slug)
    if national_status_opp is not None:
        opportunities.append(opportunity_to_dict(national_status_opp))

    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 9/CBA-006 — Gemini P0 pattern SP_002
    # (Service to Copro National Treatment Arbitrage): a real registered
    # treaty connects this candidate's jurisdiction to the production's
    # own home jurisdiction, so an official co-production structure here
    # could unlock national-treatment-gated incentives/funds the current
    # service pathway cannot reach. Trigger detection + disclosure only
    # — see canonical_opportunity_bridge.discover_service_to_national_
    # treatment_opportunity's own docstring.
    service_copro_opp = discover_service_to_national_treatment_opportunity(
        code, program_slug, inputs.jurisdiction_code,
    )
    if service_copro_opp is not None:
        opportunities.append(opportunity_to_dict(service_copro_opp))

    # Part 11/CBA-006 — Gemini P0 pattern SP_004 (Non-Party Personnel
    # Exception): a real bilateral treaty connects this candidate's
    # jurisdiction to home, and a known ATL/lead role's nationality is
    # outside both treaty parties. Treaty-specific — never generalizes
    # one treaty's real percentage to another (see the function's own
    # docstring on treaty_engine.TreatyData.non_party_personnel_
    # exception_pct, currently unresolved for every registered treaty).
    non_party_opp = discover_non_party_personnel_exception_opportunity(
        code, program_slug, inputs.jurisdiction_code, role_known_codes,
    )
    if non_party_opp is not None:
        opportunities.append(opportunity_to_dict(non_party_opp))

    # Task 3 — proactive reinvestment/vendor-participation candidates,
    # triggered purely by real budget-category totals (no known deal
    # terms required, unlike discover_reinvestment_opportunity above).
    # Gated to the production's own declared home jurisdiction only: the
    # underlying vendor/service spend is a project-level fact, not a
    # per-candidate one, so surfacing it identically on every one of a
    # project's dozens of alternative-jurisdiction candidates would be
    # pure duplication, not N distinct opportunities.
    if code == inputs.jurisdiction_code:
        for potential_opp in discover_potential_reinvestment_candidates(code, program_slug, component_spend):
            opportunities.append(opportunity_to_dict(potential_opp))

    # Task 5 — qualification levers: a real movable-component amount
    # currently sitting at the production's declared home jurisdiction
    # (never at THIS candidate — routing home spend to itself is a
    # no-op) that could close a real local-spend gap if relocated here.
    if code != inputs.jurisdiction_code and gap_opps:
        movable_elsewhere = {
            comp: amt for comp, amt in component_spend.items() if comp in MOVABLE_COMPONENTS
        }
        for lever_opp in discover_qualification_lever_opportunities(
            code, program_slug, gap_opps, movable_elsewhere,
        ):
            opportunities.append(opportunity_to_dict(lever_opp))

    return opportunities


def _coproduction_fact_scope(treaty_slug: str, participant_codes: tuple[str, ...]) -> str:
    """Codex global optimizer audit, P0-QUAL-001: "Replace project-global
    co-production facts with facts scoped to treaty slug plus ordered
    participant identities." The scope string is the treaty_slug plus the
    ORDERED (never sorted -- majority/minority role and participant
    identity both matter) tuple of participant country codes actually
    passed to the evaluator for this candidate. Facts stored under one
    treaty_slug/participant-set scope are architecturally unreachable from
    any other treaty or any other participant combination, even under the
    same treaty TYPE (e.g. two different Eurimages co-producer sets)."""
    return f"{treaty_slug}::{'-'.join(participant_codes)}"


def _coproduction_fact_keys(scope: str) -> tuple[str, str, str]:
    return (
        f"coproduction_majority_pct::{scope}",
        f"coproduction_minority_pct::{scope}",
        f"coproduction_cultural_test_passed::{scope}",
    )


async def _coproduction_facts(
    session: AsyncSession, project_id, treaty_slug: str, participant_codes: tuple[str, ...],
) -> tuple[float | None, float | None, bool | None]:
    """Canonical Co-production Qualification Reconnection — the treaty-
    bridge disconnect Codex's audit named: canonical_evaluation never
    supplied majority_pct/minority_pct/cultural_test_passed to
    evaluate_bilateral_coproduction_opportunity() at all (always left at
    their None defaults, regardless of what facts might exist). Reads
    the real fact_key values from the existing generic ProjectFact
    model — the SAME model screen_analyzer_fact_contract.py's future
    facts are expected to land in. Absent facts stay None (never
    invented).

    P0-QUAL-001 fix: facts are now scoped to (treaty_slug, ordered
    participant identities) via _coproduction_fact_scope/_coproduction_fact_keys
    instead of three project-global keys. A fact entered for one treaty
    (or one participant combination under a multilateral framework) can
    never be read back for, and therefore never resolve, a different
    treaty or a different participant combination."""
    majority_key, minority_key, cultural_key = _coproduction_fact_keys(
        _coproduction_fact_scope(treaty_slug, participant_codes)
    )
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            ProjectFact.fact_key.in_((majority_key, minority_key, cultural_key)),
        )
    )).all()
    facts = {k: v for k, v in rows}

    def _float(key: str) -> float | None:
        v = facts.get(key)
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _bool(key: str) -> bool | None:
        # CBA-004 fix (Codex audit 4db2cea, finding 5): any non-empty
        # value other than a recognized true/false token previously fell
        # through to `False` — an invalid or "unknown" input became a
        # CONFIRMED FAILED cultural test rather than unresolved input.
        # Only a recognized token now resolves; anything else (including
        # a genuinely invalid or "unknown" string) stays None, matching
        # every other unresolved-fact convention in this module.
        v = facts.get(key)
        if v is None or v == "":
            return None
        normalized = str(v).strip().lower()
        if normalized in ("true", "1", "yes"):
            return True
        if normalized in ("false", "0", "no"):
            return False
        return None

    return (_float(majority_key), _float(minority_key), _bool(cultural_key))


async def _multilateral_coproduction_facts(
    session: AsyncSession, project_id, treaty_slug: str, participant_codes: tuple[str, ...],
) -> tuple[dict[str, float] | None, bool | None]:
    """P0-QUAL-001, "Support participant-specific percentages ... for
    multilateral frameworks" (Eurimages, European Convention, Ibermedia --
    each takes N>=2 co-producers, not a fixed majority/minority pair).
    Reads one scoped per-participant percentage fact
    (coproduction_participant_pct::<scope>::<code>) for EACH code in
    participant_codes, plus the shared scoped cultural-test fact. Returns
    country_pcts=None (never a partially-filled dict) unless EVERY
    participant has an on-file percentage -- evaluate_eurimages_
    coproduction_opportunity and its siblings already treat
    country_pcts=None as UNRESOLVED_FACTS, the correct fail-closed state
    for an incomplete allocation, exactly like the bilateral case."""
    scope = _coproduction_fact_scope(treaty_slug, participant_codes)
    pct_keys = {code: f"coproduction_participant_pct::{scope}::{code}" for code in participant_codes}
    cultural_key = f"coproduction_cultural_test_passed::{scope}"
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            ProjectFact.fact_key.in_((*pct_keys.values(), cultural_key)),
        )
    )).all()
    facts = {k: v for k, v in rows}

    country_pcts: dict[str, float] | None = {}
    for code, key in pct_keys.items():
        raw = facts.get(key)
        try:
            val = float(raw) if raw not in (None, "") else None
        except (TypeError, ValueError):
            val = None
        if val is None:
            country_pcts = None
            break
        country_pcts[code] = val

    cultural_raw = facts.get(cultural_key)
    cultural_test_passed: bool | None
    if cultural_raw is None or cultural_raw == "":
        cultural_test_passed = None
    else:
        normalized = str(cultural_raw).strip().lower()
        if normalized in ("true", "1", "yes"):
            cultural_test_passed = True
        elif normalized in ("false", "0", "no"):
            cultural_test_passed = False
        else:
            cultural_test_passed = None

    return (country_pcts, cultural_test_passed)


async def _real_multilateral_subset_participants(
    session: AsyncSession, project_id, treaty_slug: str, is_member_fn,
) -> tuple[dict, bool | None]:
    """Eight-control closeout, HO-012: the EXISTING _multilateral_
    coproduction_facts() (above) requires a real, on-file percentage for
    EVERY member of the production's FULL discovered candidate set
    (find_eurimages_partners' own return, e.g. 36+ real member
    jurisdictions for a typical production) before it will ever resolve
    country_pcts -- a genuine, pre-existing design choice appropriate for
    "does this production's SHOOT-LOCATION-DISCOVERED candidate universe
    already, collectively, form a co-production," but which makes a
    producer-INTENDED, specific-N-party structure (e.g. exactly Ireland +
    France + the UK) practically unreachable, since it would require
    facts for every OTHER discovered Eurimages member too.

    This is the deliberate, narrower sibling: reads whichever REAL,
    positive, evidenced coproduction_participant_pct::<treaty_slug>::
    <code> facts are actually on file for this project (a simpler key,
    scoped to the treaty only -- no pre-known participant tuple required,
    since the fact set ITSELF defines who the producer has asserted as a
    co-producer), filters to real treaty members only (never invents
    membership), and returns exactly that asserted subset. Requires >= 2
    qualifying members (fewer is not a co-production) and the treaty's
    own real cultural-test fact (coproduction_cultural_test_passed::
    <treaty_slug>, single value for the whole treaty, not per-participant-
    set) -- same real fail-closed contract as the sibling function:
    country_pcts stays {} (never partially trusted with a single
    unsupported party) unless at least 2 real members qualify."""
    prefix = f"coproduction_participant_pct::{treaty_slug}::"
    cultural_key = f"coproduction_cultural_test_passed::{treaty_slug}"
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            or_(
                ProjectFact.fact_key.like(f"{prefix}%"),
                ProjectFact.fact_key == cultural_key,
            ),
        )
    )).all()
    facts = {k: v for k, v in rows}

    country_pcts: dict = {}
    for key, raw in facts.items():
        if not key.startswith(prefix):
            continue
        code = key[len(prefix):].upper()
        if not code or not is_member_fn(code):
            continue  # never invents membership for a code that isn't a real, registered member
        try:
            val = float(raw) if raw not in (None, "") else None
        except (TypeError, ValueError):
            val = None
        if val is not None and val > 0:
            country_pcts[code] = val

    if len(country_pcts) < 2:
        country_pcts = {}

    cultural_raw = facts.get(cultural_key)
    cultural_test_passed: bool | None = None
    if cultural_raw not in (None, ""):
        normalized = str(cultural_raw).strip().lower()
        if normalized in ("true", "1", "yes"):
            cultural_test_passed = True
        elif normalized in ("false", "0", "no"):
            cultural_test_passed = False

    return (country_pcts, cultural_test_passed)


async def _all_coproduction_facts_for_fingerprint(session: AsyncSession, project_id) -> tuple[tuple[str, str], ...]:
    """P0-QUAL-001: the fingerprint must invalidate whenever ANY
    treaty/participant-scoped co-production fact changes, not just one
    hardcoded global tuple. Rather than pre-enumerate every treaty x
    participant-set combination (which would require duplicating the full
    candidate-discovery walk just to compute a cache key), this reads
    every ProjectFact row whose key is one of the three co-production
    fact prefixes, for this project, regardless of scope suffix. Any
    edit, addition, or removal of a scoped co-production fact changes
    this tuple and therefore the fingerprint. Over-invalidation (a
    fingerprint change that turns out not to affect this treaty's
    candidates) is safe; under-invalidation is the exact P0-QUAL-001
    defect this exists to prevent."""
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            or_(
                ProjectFact.fact_key.like("coproduction_majority_pct::%"),
                ProjectFact.fact_key.like("coproduction_minority_pct::%"),
                ProjectFact.fact_key.like("coproduction_cultural_test_passed::%"),
                ProjectFact.fact_key.like("coproduction_participant_pct::%"),
            ),
        )
    )).all()
    return tuple(sorted((k, "" if v is None else str(v)) for k, v in rows))


def _role_qualification_for_candidate(
    code: str, program_slug: str, role_known_codes: dict[str, tuple[str, ...]] | None,
    script_facts: dict[str, tuple[str, ...]] | None = None,
    typed_personnel_facts: dict[str, dict[str, tuple[str, ...]]] | None = None,
) -> dict | None:
    """Canonical Co-production Qualification Reconnection, Task 3 — the
    repaired seam. Calls evaluate_role_qualification() (reusing cultural_
    qualification_model.py's real 24-program registry UNCHANGED) with the
    project's own real, persisted personnel facts. Returns None only when
    role_known_codes itself is unavailable (never a fabricated result);
    the bridge function itself always returns a real
    CanonicalQualificationResult (QUALIFIES/HARD_FAIL/USER_FACT_REQUIRED/
    SCRIPT_FACT_REQUIRED/CURABLE_GAP/RULE_DATA_INCOMPLETE/NOT_APPLICABLE)
    for every program_slug, including the ones neither the role registry
    nor cultural_point_tables.py has data for. Worldwide Qualification
    Consumption Closeout, 2026-08-19: also passes the project's real
    Script Analyzer facts through, so cultural-point-table programs with
    a script-derived criterion can resolve SCRIPT_FACT_REQUIRED correctly
    rather than being starved of that input. Final Consolidated Backend
    Correction, Part 4/CBA-004: also passes the SEPARATE typed nationality-
    vs-residency personnel facts through, for any cultural-point-table
    criterion whose confirmed fact_kind is one specifically."""
    if role_known_codes is None:
        return None
    result = evaluate_role_qualification(
        program_slug, code, role_known_codes, script_facts=script_facts,
        typed_personnel_facts=typed_personnel_facts,
    )
    return qualification_result_to_dict(result)


#: CBA-002 continuation — TYPED RATE CONDITION -> QUALIFICATION propagation.
#: Only these 3 RateCondition kinds gate program ELIGIBILITY itself (whether
#: the program applies at all) rather than merely the RATE quantum (how much
#: it's worth, or the exact ceiling within a discretionary band). Everything
#: else in CONDITION_KIND_STATE (discretionary_band, cultural_test_required
#: — already independently owned by evaluate_role_qualification() itself,
#: never double-gated here — uplifts, rate-base/ATL/currency modeling gaps,
#: disclosure-only kinds) is deliberately EXCLUDED: propagating those would
#: incorrectly downgrade Recommended-admission for the ~60 programs with a
#: mere discretionary band, or any uplift-only condition, none of which are
#: real eligibility gates. This is a narrow, explicit, data-driven set —
#: never a blanket "any unresolved rate condition blocks qualification" rule.
_RATE_CONDITION_ELIGIBILITY_KINDS = frozenset({
    "min_qpe_pct_of_total_budget",       # real QPE-vs-budget ratio: unmet -> curable gap
    "project_fact_dependent_eligibility",  # pure entity/content-certification gate
    "unmodeled_spend_split_ratio",        # a genuine, differently-shaped ratio gate this
                                            # engine doesn't yet model (Ontario/NY/Mexico)
})

#: Severity order for merging the rate-condition-derived qualification signal
#: with the role/cultural qualification state already computed — the WORSE
#: (lower number) of the two always wins; a passing rate condition can never
#: override a real cultural/role-level gap, and vice versa.
#: OH-002 fix (CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT): QUAL_RULE_DATA_
#: INCOMPLETE was previously ABSENT from this table. Every merge site below
#: reads it via `.get(state, 2)`, so a real RULE_DATA_INCOMPLETE state
#: silently fell back to severity 2 -- the SAME tier as QUALIFIES/
#: NOT_APPLICABLE, meaning a stack member ordering like [NOT_APPLICABLE,
#: RULE_DATA_INCOMPLETE] incorrectly resolved to NOT_APPLICABLE (which
#: DOES admit Recommended) instead of RULE_DATA_INCOMPLETE (which must
#: NOT — see _QUALIFICATION_ADMITS_RECOMMENDED below, which excludes it).
#: Explicit entry closes the gap without any `.get(..., default)` reliance.
_QUAL_STATE_SEVERITY = {
    QUAL_HARD_FAIL: 0,
    QUAL_CURABLE_GAP: 1,
    QUAL_USER_FACT_REQUIRED: 1,
    QUAL_SCRIPT_FACT_REQUIRED: 1,
    QUAL_AUTHORITY_UNRESOLVED: 1,
    QUAL_RULE_DATA_INCOMPLETE: 1,
    QUAL_NOT_APPLICABLE: 2,
    QUAL_QUALIFIES: 2,
}


def _rate_condition_qualification_impact(rate_resolution: RateResolution | None) -> tuple[str, tuple[str, ...]] | None:
    """Returns (worst QUAL_* state implied by real eligibility-relevant rate
    conditions, the condition_ids responsible) or None if no such condition
    exists on this resolution, or all of them are satisfied/not-applicable.
    Only ever reads conditions_evaluated -- never re-decides rate mechanics."""
    if rate_resolution is None:
        return None
    worst_state: str | None = None
    worst_severity = 99
    culprits: list[str] = []
    for cond in rate_resolution.conditions_evaluated:
        if cond.kind not in _RATE_CONDITION_ELIGIBILITY_KINDS:
            continue
        if cond.condition_state == CONDITION_STATE_EXECUTABLE:
            if cond.satisfied is False:
                candidate_state = QUAL_CURABLE_GAP  # measurable, curable threshold gap
            else:
                continue  # satisfied or not yet evaluable -> no impact
        elif cond.condition_state == CONDITION_STATE_USER_FACT_REQUIRED:
            candidate_state = QUAL_USER_FACT_REQUIRED
        elif cond.condition_state == CONDITION_STATE_AUTHORITY_UNRESOLVED:
            candidate_state = QUAL_AUTHORITY_UNRESOLVED
        else:
            continue
        sev = _QUAL_STATE_SEVERITY[candidate_state]
        if sev < worst_severity:
            worst_severity, worst_state = sev, candidate_state
        culprits.append(cond.condition_id)
    if worst_state is None:
        return None
    return worst_state, tuple(culprits)


def _merge_rate_condition_into_qualification(
    role_qualification: dict | None, rate_resolution: RateResolution | None,
    regime_id: str, jurisdiction_code: str | None,
) -> dict | None:
    """Combines the role/cultural qualification state (evaluate_role_
    qualification, unchanged) with the rate resolver's own eligibility-
    relevant condition outcomes (CBA-002), taking whichever is WORSE by
    _QUAL_STATE_SEVERITY. Never weakens an existing HARD_FAIL/gap state;
    never invents QUALIFIES where none existed. Returns a dict in the same
    shape qualification_result_to_dict() produces (or None, unchanged, if
    neither source has anything to say)."""
    impact = _rate_condition_qualification_impact(rate_resolution)
    if impact is None:
        return role_qualification
    rate_state, culprit_ids = impact
    if role_qualification is None:
        return {
            "regime_id": regime_id, "jurisdiction_code": jurisdiction_code,
            "state": rate_state, "qualification_route": "rate_condition_eligibility_gate",
            "role_findings": [], "current_points": None, "required_points": None,
            "contribution_requirements": [], "ownership_control_requirements": [],
            "resolved_facts": [], "missing_facts": list(culprit_ids) if rate_state != QUAL_CURABLE_GAP else [],
            "failed_requirements": [], "curable_requirements": list(culprit_ids) if rate_state == QUAL_CURABLE_GAP else [],
            "available_levers": [], "authority_basis": None, "confidence_state": "MEDIUM",
            "reasoning_trace": [f"Rate condition(s) {', '.join(culprit_ids)} resolved to {rate_state}."],
        }
    existing_state = role_qualification.get("state")
    existing_sev = _QUAL_STATE_SEVERITY.get(existing_state, 2)
    rate_sev = _QUAL_STATE_SEVERITY[rate_state]
    if rate_sev >= existing_sev:
        return role_qualification  # existing role/cultural state is already as bad or worse
    merged = dict(role_qualification)
    merged["state"] = rate_state
    merged["reasoning_trace"] = list(role_qualification.get("reasoning_trace") or []) + [
        f"Rate condition(s) {', '.join(culprit_ids)} resolved to {rate_state}, "
        f"downgrading from role/cultural state {existing_state}."
    ]
    if rate_state == QUAL_CURABLE_GAP:
        merged["curable_requirements"] = list(role_qualification.get("curable_requirements") or []) + list(culprit_ids)
    else:
        merged["missing_facts"] = list(role_qualification.get("missing_facts") or []) + list(culprit_ids)
    return merged


def _participant_qualification_aggregate(
    program_slugs: tuple[str, ...],
    qual_detail_by_program: dict[str, tuple[str, dict | None]],
) -> list[dict]:
    """Codex final four-row remediation (P0-SEL-ALT-001) — a generic,
    structured PER-PARTICIPANT qualification/gate aggregate. Replaces the
    prior `{"state": worst_state}` collapse for component/stack
    structures, which discarded every participant's own missing_facts/
    curable_requirements/failed_requirements/reasoning_trace/authority/
    administrative-allocation disclosure — exactly Codex's finding:
    "Component/stack aggregation persists only the worst state and
    discards every participant/program missing fact."

    Retains, for EVERY participant/claimed program in the structure: its
    canonical jurisdiction id, program slug, qualification state/route,
    missing/curable/failed requirements, reasoning trace (the ONLY place
    a RULE_DATA_INCOMPLETE/NOT_APPLICABLE state's real explanation lives
    when the three requirement lists are empty — e.g. Manitoba's "no
    NationalityRequirement rows" note), authority coverage state, and any
    administrative-allocation-risk disclosure. Never collapsed, never
    deduplicated across participants — canonical_production_view.py's
    `_blocking_requirements()` unions every field from every entry here,
    so a structure's disclosed blockers are always the COMPLETE retained
    set, never a subset.

    qual_detail_by_program is keyed by program_slug alone (the same key
    _qual_state_by_program already uses, for the identical federal-
    member-examined-under-a-different-jurisdiction-code reason); each
    value is (jurisdiction_code_captured_under, full_role_qualification_
    dict_or_None). A program_slug this function is asked about that was
    never examined (should not happen for a real candidate's own claimed
    programs, but defensively handled) yields an explicit, empty-detail
    entry rather than a KeyError or a silently dropped participant."""
    out: list[dict] = []
    for slug in program_slugs:
        code, detail = qual_detail_by_program.get(slug, (None, None))
        detail = detail or {}
        out.append({
            "participant_id": code,
            "program_slug": slug,
            "qualification_state": detail.get("state"),
            "qualification_route": detail.get("qualification_route"),
            "missing_facts": list(detail.get("missing_facts") or []),
            "curable_requirements": list(detail.get("curable_requirements") or []),
            "failed_requirements": list(detail.get("failed_requirements") or []),
            "reasoning_trace": list(detail.get("reasoning_trace") or []),
            "authority_state": coverage_state(slug),
            "administrative_allocation_disclosure": _competitive_allocation_disclosure(slug),
        })
    return out


def _capability_only_status(examination) -> tuple[str, str, str]:
    """Real terminal status for a capability_only candidate (Codex Defect
    4) — reads fields discover_executable_jurisdictions() already computed
    (has_doctrine, has_rate_rules, resolves_for_production, program_slug)
    plus the SAME authority-coverage-registry lookup discovery itself
    already consulted for this program. Never re-evaluates a rule or a
    coverage decision; only classifies the terminal state that was already
    reached. Returns (candidate_status, rejection_reason_class, reason)."""
    if examination is None:
        return (
            STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, "AUTHORITY_INSUFFICIENT",
            "Incentive model not yet classified for this program.",
        )
    state = _coverage_state(examination.program_slug)
    if state == "UNPRICEABLE_AUTHORITY_INSUFFICIENT":
        # The registry's OWN explicit adjudication of "no defensible
        # authority" for this program — even where discovery's has_doctrine/
        # has_rate_rules still read True from stale classified data (the
        # completed primary-authority audit overrides that staleness).
        # Same terminal status as "no rules classified at all", never a
        # different bucket for the same underlying cause.
        return (STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, state, examination.reason)
    if state not in ("PRICEABLE_VALIDATED",):
        # NON_GUARANTEED_SELECTIVE / NON_ECONOMIC / SUPERSEDED / DUPLICATE —
        # the completed primary-authority corpus already adjudicated this
        # program as blocked for a reason OTHER than missing data; never
        # flattened into "authority insufficient".
        return (
            STATUS_FEASIBILITY_REVIEW_REQUIRED, state,
            f"{examination.reason} (authority_coverage_registry: {state})",
        )
    if examination.has_doctrine and examination.has_rate_rules and not examination.resolves_for_production:
        # Real statutory rate rules exist for this program; they simply do
        # not resolve for this production's type/QPE (a genuine threshold/
        # rule rejection — e.g. a minimum-QPE gate) — never the same as
        # "no authority data exists".
        return (
            STATUS_RULE_REJECTED, "STATUTORY_CONDITIONS_UNMET",
            examination.reason,
        )
    return (STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, "AUTHORITY_INSUFFICIENT", examination.reason)


#: Canonical authority substrate + feasibility boundary repair, Task 1/2 —
#: PRODUCTION FEASIBILITY (how suitable a jurisdiction is for the creative/
#: logistical requirements) is a permanently separate concept from ECONOMIC
#: DISCOVERY/ELIGIBILITY (whether a defensible incentive can be priced).
#: The prior FVD canonical input assembly repair correctly wired real SA-1
#: script/location data into `derive_production_requirements()`, but then
#: fed it into `discover_executable_jurisdictions()` AS THE gate that
#: decides whether a jurisdiction even reaches structure generation --
#: conflating a soft, informational production-fit signal (a landlocked
#: jurisdiction cannot host a Mediterranean sea-shore scene) with a hard
#: statutory/program eligibility failure. That is corrected here: a
#: SEPARATE discovery pass with the real requirements supplies feasibility
#: DISCLOSURE only (never used to reject a candidate); economic candidate
#: GENERATION uses the same empty-requirements discovery pass used before
#: SA-1 requirements existed, so nothing is removed from the economic
#: universe on capability grounds alone. See evaluate_project() below.
FEASIBILITY_STRONG = "STRONG"
FEASIBILITY_WORKABLE = "WORKABLE"
FEASIBILITY_WEAK = "WEAK"
FEASIBILITY_UNKNOWN = "UNKNOWN"

#: Capability token -> short feasibility reason code. Deterministic,
#: mechanical labeling of the SAME capability vocabulary
#: production_requirements.py already defines -- no new capability
#: concept, no invented reason.
_CAPABILITY_TO_FEASIBILITY_REASON = {
    "open_water_filming": "MARINE_MISMATCH",
    "marine_filming": "MARINE_MISMATCH",
    "underwater_filming": "MARINE_MISMATCH",
    "water_tanks": "MARINE_MISMATCH",
    "desert_environments": "LOCATION_MISMATCH",
    "snow_environments": "LOCATION_MISMATCH",
}
#: marine_suitability values (jurisdiction_comparison.py, unmodified) that
#: read as a genuinely strong production fit when marine capability is
#: actually required -- distinct from merely "workable."
_STRONG_MARINE_SUITABILITY = {"strong", "excellent"}


def _feasibility_status(examination, requirements) -> tuple[str, list[str]]:
    """Classifies ONE jurisdiction's production feasibility from the
    real-requirements discovery examination. Never used to reject a
    candidate from economic discovery -- see the module note above."""
    if examination is None or not examination.has_capability_data:
        return FEASIBILITY_UNKNOWN, []
    if not examination.production_capable:
        reasons = [
            _CAPABILITY_TO_FEASIBILITY_REASON.get(token, "LOCATION_MISMATCH")
            for token in sorted(requirements.required_capabilities)
        ] or ["CAPABILITY_MISMATCH"]
        # Dedupe while preserving order.
        return FEASIBILITY_WEAK, list(dict.fromkeys(reasons))
    if "open_water_filming" in requirements.required_capabilities:
        profile = jurisdiction_capability_profile(examination.jurisdiction_code)
        if str(profile.marine_suitability or "").lower() in _STRONG_MARINE_SUITABILITY:
            return FEASIBILITY_STRONG, []
    return FEASIBILITY_WORKABLE, []


def _conditional_data(structure_id: str, code: str, program_slugs: tuple[str, ...]) -> tuple[list[dict], dict]:
    """Existing Optimizer/Stacker Reconnection, Task 7 — attach the
    EXISTING conditional grants/funds layer (conditional_programs.py) and
    structural compatibility verdicts (structure_compatibility.py) to a
    priced structure. Never touches NPC/economics: every node here stays
    a disclosed opportunity, never a guaranteed value (see
    conditional_programs.py's own module docstring — discretionary
    awards are never estimated, never entered into NPC)."""
    nodes = conditional_nodes_for((code,))
    compat = evaluate_structure_compatibility(
        structure_id=structure_id,
        participants=(code,),
        executable_program_slugs=tuple(program_slugs),
        conditional_nodes=nodes,
    )
    return [node_to_dict(n) for n in nodes], compatibility_to_dict(compat)


def _segment_dicts(pricing) -> list[dict]:
    """Full, generic serialization of `pricing.segments` — the SAME
    SegmentEconomics objects `little_utopia_state.build_allocated_structures`
    already serializes via its own `_seg_dict` (byte-identical field set and
    naming, see qualification_trace below). Canonical served wiring repair
    (Codex Defect 3): previously reduced to a handful of fields, silently
    dropping cap/band/confirmation/floor-ceiling/register-trace data the
    calculator already computed — this is serialization only, no new
    economics, every value already existed on `pricing.segments`."""
    return [
        {
            "jurisdiction_code": s.jurisdiction_code,
            "program_slug": s.program_slug,
            "claims_incentive": s.claims_incentive,
            "executable": s.executable,
            "allocated_usd": s.allocated_usd,
            "account_codes": list(s.account_codes),
            "qpe_usd": s.qpe_usd,
            "excluded_usd": s.excluded_usd,
            "unresolved_usd": s.unresolved_usd,
            "rate_floor": s.rate_floor,
            "rate_ceiling": s.rate_ceiling,
            "is_band_ceiling": s.is_band_ceiling,
            "statutory_basis": s.statutory_basis,
            "doctrine": s.doctrine,
            "incentive_floor_usd": s.incentive_floor_usd,
            "incentive_ceiling_usd": s.incentive_ceiling_usd,
            "ceiling_requires_confirmation": s.ceiling_requires_confirmation,
            "authority_provenance_unresolved": getattr(s, "authority_provenance_unresolved", False),
            "qpe_cap_applied_usd": s.qpe_cap_applied_usd,
            "blockers": list(s.blockers),
            "qualification_trace": list(s.register_trace),
            # Cluster 2/19: the mandatory requirements this program imposes and
            # their adjudicated state, so a producer can see which gates are
            # satisfied, failed or still unresolved rather than only a number.
            "requirement_trace": list(getattr(s, "requirement_trace", ()) or ()),
            "incentive_cap_usd": getattr(s, "incentive_cap_usd", None),
            "incentive_cap_type": getattr(s, "incentive_cap_type", None),
            "incentive_uncapped_usd": getattr(s, "incentive_uncapped_usd", None),
            "incentive_cap_applied_usd": getattr(s, "incentive_cap_applied_usd", 0.0),
            "notes": list(s.notes),
        }
        for s in pricing.segments
    ]


def _canonical_jurisdiction_name(code: str | None) -> str | None:
    """Producer-facing jurisdiction name for a code with no seeded
    Jurisdiction row (AE-AD, AE-DXB, AU-SA). Delegates to the single
    canonical resolver rather than duplicating a name map."""
    from app.services.canonical_program_identity import canonical_jurisdiction_name

    return canonical_jurisdiction_name(code)


def _program_display_name(program_slug: str) -> str:
    """Human-readable program name for structure-label disambiguation only
    (never used for economics) — reads the same DoctrineRecord.program_name
    already carried by executable_jurisdiction_registry.py; falls back to a
    humanized slug for the handful of programs defined as raw RateRule
    tuples with no DoctrineRecord."""
    record = _get_doctrine(program_slug)
    if record is not None and record.program_name:
        return record.program_name
    return program_slug.replace("_", " ").upper()


#: Generic PROJECT-LEVEL candidate-jurisdiction preference fact_key prefix
#: (batched producer-control closeout, 2026-09-03). One ProjectFact row per
#: excluded jurisdiction code: fact_key=f"jurisdiction_preference:{code}",
#: value="excluded" (any other/absent value, including no row at all,
#: means the jurisdiction is INCLUDED -- the default). Never a per-
#: jurisdiction column, never a Saudi-specific flag; the same generic
#: mechanism works for any jurisdiction code any project ever wants to
#: exclude from its own candidate universe.
JURISDICTION_PREFERENCE_FACT_PREFIX = "jurisdiction_preference:"


async def _excluded_jurisdiction_codes(session: AsyncSession, project_id) -> set[str]:
    """The set of jurisdiction codes this PROJECT has elected to exclude
    from its own candidate universe -- a producer MODELING preference,
    never a change to law/doctrine/rate/preapproval/content requirements
    (those are untouched for any jurisdiction that remains in the
    universe). Reads the same generic ProjectFact mechanism/precedence
    every other producer-settable fact already uses (see the coproduction
    facts read above and cineglobe.py's /assumptions endpoint) -- never a
    second persistence mechanism."""
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            ProjectFact.fact_key.like(f"{JURISDICTION_PREFERENCE_FACT_PREFIX}%"),
        )
    )).all()
    excluded = set()
    for fact_key, value in rows:
        if (value or "").strip().lower() == "excluded":
            excluded.add(fact_key[len(JURISDICTION_PREFERENCE_FACT_PREFIX):])
    return excluded


#: Final non-Globe canonical core closeout, Item B (2026-09-04) --
#: generic PROJECT-level discretionary/selective-program policy. Two
#: fact_keys, same ProjectFact mechanism/precedence as
#: JURISDICTION_PREFERENCE_FACT_PREFIX directly above -- never a
#: Saudi-specific column, never a second persistence mechanism, never a
#: country-name if/else:
#:   "discretionary_policy_default" -> "exclude" turns discretionary/
#:     selective programs OFF project-wide. Any other/absent value
#:     (including no row at all) means "include" -- the default, and
#:     the exact behavior every project had before this policy existed,
#:     so no existing evaluation changes unless a project explicitly
#:     opts out.
#:   f"discretionary_policy_program:{program_slug}" -> "include" or
#:     "exclude", overriding the project default for that ONE program
#:     specifically (e.g. keep Saudi's discretionary Film Rebate off
#:     while leaving every OTHER discretionary program in this
#:     project's universe on, or the reverse).
#: Scope: "discretionary" here means program_requirements.allocation_type
#: == AllocationType.DISCRETIONARY -- the SAME real field
#: _competitive_allocation_disclosure already reads (see
#: _is_discretionary_program below), never a second classification.
#: COMPETITIVE / FIRST_COME_FIRST_SERVED programs are a different,
#: non-discretionary allocation-timing risk (still disclosed via
#: administrative_allocation_risk) and are NOT gated by this policy.
#: Authority requirements -- eligibility, preapproval, cultural tests,
#: nationality, minimum spend, local entity, and every other
#: authoritative gate -- are UNCHANGED by this policy; it only decides
#: whether a discretionary program's candidate is generated at all, and
#: every gate still applies in full to any candidate that remains.
DISCRETIONARY_POLICY_DEFAULT_FACT_KEY = "discretionary_policy_default"
DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX = "discretionary_policy_program:"


def _is_discretionary_program(program_slug: str) -> bool:
    """True only for AllocationType.DISCRETIONARY -- the generic
    contract's "discretionary/selective" category (Saudi's Film Rebate,
    Abu Dhabi's fund, etc.). Reads the SAME canonical
    program_requirements.allocation_type field
    _competitive_allocation_disclosure already reads -- never a second
    classification, never a hardcoded program-slug list."""
    try:
        from app.data.program_requirements import AllocationType, get_program_requirements
    except Exception:  # pragma: no cover - import cycle safety
        return False
    profile = get_program_requirements(program_slug)
    if profile is None:
        return False
    return profile.allocation_type == AllocationType.DISCRETIONARY


async def _discretionary_policy_facts(session: AsyncSession, project_id) -> dict[str, str]:
    """Raw discretionary/selective-program policy facts for this PROJECT
    (Item B), keyed exactly as persisted. Fetched ONCE (same
    one-query-per-project pattern as _excluded_jurisdiction_codes/
    role_known_codes elsewhere in this module) and reused at both the
    fingerprint and the candidate-filter use sites -- never re-fetched."""
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            (ProjectFact.fact_key == DISCRETIONARY_POLICY_DEFAULT_FACT_KEY)
            | ProjectFact.fact_key.like(f"{DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX}%"),
        )
    )).all()
    return {fact_key: (value or "").strip().lower() for fact_key, value in rows}


def _discretionary_policy_resolve(program_slug: str, facts: dict[str, str]) -> str:
    """'include' or 'exclude' for this ONE program: per-program override
    wins if present and valid, else the project default, else 'include'
    (the safe, behavior-preserving default). Generic for any
    program_slug -- never a per-jurisdiction or per-country branch."""
    override = facts.get(f"{DISCRETIONARY_POLICY_PROGRAM_FACT_PREFIX}{program_slug}")
    if override in ("include", "exclude"):
        return override
    default = facts.get(DISCRETIONARY_POLICY_DEFAULT_FACT_KEY)
    return default if default in ("include", "exclude") else "include"


async def _company_period_prior_award_facts(
    session: AsyncSession, project: Project, inputs: "ProjectEconomicInputs",
) -> tuple[frozenset[str], dict[str, float]]:
    """Codex final four-row remediation (P0-NL-001, fourth pass) — the
    ONE place any program's company/period-scoped prior-award aggregate
    is ever computed. Codex's exact rejection of the prior (third-pass)
    version: "Do not read StructureCalculationResult or any candidate/
    scenario output as a prior award." A ProductionStructure/
    StructureCalculationResult row is the optimizer's own PRICED
    ESTIMATE for one candidate structure — never a real-world grant,
    approval, or contract; summing those rows let a company's own
    hypothetical, un-awarded candidate economics silently count as if
    they were real awards, and let a sibling that had simply never been
    EVALUATED (not "denied an award" — just never run) silently read as
    "no other production", handing out a fresh full cap that should have
    been unresolved.

    THE FIX: reads ONLY app.models.incentive_award_ledger.
    IncentiveAwardLedgerEntry, via app.services.
    incentive_award_ledger_service — a durable, append-only, explicitly
    real-world-evidenced record, written ONLY by an explicit act
    recording a real grant/denial/pending decision, NEVER auto-populated
    from optimizer output. Every USD figure this function ever touches
    is a native-currency ledger amount converted to USD/back exactly
    ONCE by the caller (allocation_pricing._resolve_incentive_dollar_cap)
    — this function itself performs NO FX conversion at all (the prior
    version's "convert each sibling's stored USD estimate back to EUR"
    round-trip is gone entirely; the ledger already stores native EUR).

    Returns (evidenced_facts, amounts) to be UNIONED into
    inputs.evidenced_program_facts / inputs.amount_facts before pricing
    runs, so the result participates in the SAME fingerprint/cache
    identity every other calculation-driving fact already does.

    THREE-GATE RESOLUTION, generic over every IncentiveValueCapRule
    declaring company_period_prior_award_fact_key (currently only
    nl_film_production_incentive):

    1. IDENTITY GATE — inputs.production_company_identifier and
       inputs.award_period_year must both be set. Missing either means
       company_period_identity_known_fact_key is never added; the cap
       resolver fails this program closed (unknown company/period).

    2. SIBLING-COVERAGE GATE — every OTHER real Project row sharing the
       EXACT SAME company+period (this project excluded) is found. If
       NONE exist, this company genuinely has no other production this
       period — a real, verifiable "alone" state requiring no ledger
       entry at all (company_period_has_other_productions_fact_key is
       simply never set — the cap resolver's existing "no claim -> full
       cap" path applies, unchanged). If ANY sibling projects exist, the
       ledger MUST have at least one entry for this exact
       (company, period, program) triple before anything is trusted —
       absence means "a sibling production's award status is
       unresolved", and company_period_sibling_coverage_complete_
       fact_key is never set, so the cap resolver fails closed. This is
       the EXACT adverse case Codex named: "Sibling existence with
       unknown award evidence remains unresolved and no full cap is
       asserted" — a sibling PROJECT existing is not proof of an award,
       but it IS proof that "we simply never checked" cannot be treated
       as "there is nothing to check".

    3. AWARD-SUM GATE — once sibling coverage is confirmed complete (by
       the ledger having at least one real entry for this triple, even
       if every entry is a non-cap-consuming status like PENDING/
       DENIED), the REAL sum of APPROVED/GRANTED native amounts is the
       trustworthy remaining-cap input — company_period_has_other_
       productions_fact_key is set (even when the sum is exactly $0.00,
       a real EVIDENCED zero, explicitly distinct from the "no ledger
       row at all" unresolved case in gate 2)."""
    from app.data.program_rate_rules import INCENTIVE_VALUE_CAP_RULES
    from app.services.incentive_award_ledger_service import company_period_program_award_summary

    evidenced: set[str] = set()
    amounts: dict[str, float] = {}

    company = inputs.production_company_identifier
    period = inputs.award_period_year
    if company is None or period is None:
        return frozenset(evidenced), amounts

    cap_rules = [
        cap for cap in INCENTIVE_VALUE_CAP_RULES.values()
        if cap.company_period_prior_award_fact_key is not None
    ]
    if not cap_rules:
        return frozenset(evidenced), amounts

    sibling_ids = (await session.execute(
        select(Project.id).where(
            Project.production_company_identifier == company,
            # Codex final three-program conservation repair (P0-NL-001,
            # fifth pass): the real, explicit award_period_year column,
            # never target_shoot_year (a production-planning fact, not a
            # statement of the statutory award period).
            Project.award_period_year == period,
            Project.id != project.id,
        )
    )).scalars().all()

    for cap in cap_rules:
        if cap.company_period_identity_known_fact_key:
            evidenced.add(cap.company_period_identity_known_fact_key)

        if not sibling_ids:
            # Gate 2, real "alone" branch: no other production exists
            # for this company/period at all — nothing to be unresolved
            # about. Coverage is VACUOUSLY complete (there is nothing to
            # cover), so sibling_coverage_complete IS evidenced here —
            # this is what lets the resolver distinguish "genuinely
            # alone" (full cap applies) from "siblings exist but were
            # never checked" (unresolved, below). has_other_productions
            # stays unset either way; the resolver's existing "no claim
            # -> full cap" path applies, unchanged.
            if cap.company_period_sibling_coverage_complete_fact_key:
                evidenced.add(cap.company_period_sibling_coverage_complete_fact_key)
            continue

        has_rows, total_native = await company_period_program_award_summary(
            session,
            production_company_identifier=company,
            award_period_year=period,
            program_slug=cap.program_slug,
            # Codex final three-program conservation repair (P0-NL-001,
            # fifth pass): defense in depth — never numerically combine
            # a mismatched-currency row into this cap's own native total,
            # even though record_incentive_award already refuses to
            # write one in the first place.
            expected_currency=cap.cap_currency,
        )
        if not has_rows:
            # Gate 2 fails: sibling project(s) exist but the ledger has
            # NEVER been checked/recorded for this exact triple — this
            # is genuinely unresolved, never a zero. Neither
            # sibling_coverage_complete nor has_other_productions is
            # set (deliberately NOT added — see docstring gate 2); the
            # cap resolver must fail this segment closed.
            continue

        # Gate 2 passes (real ledger coverage exists); Gate 3: the real,
        # evidenced sum — possibly exactly $0.00 if every recorded row
        # is PENDING/DENIED, which is a genuine, trustworthy zero,
        # distinct from "no ledger row at all" above.
        if cap.company_period_sibling_coverage_complete_fact_key:
            evidenced.add(cap.company_period_sibling_coverage_complete_fact_key)
        if cap.company_period_has_other_productions_fact_key:
            evidenced.add(cap.company_period_has_other_productions_fact_key)
            amounts[cap.company_period_prior_award_fact_key] = round(total_native, 2)

    return frozenset(evidenced), amounts


async def evaluate_project(session: AsyncSession, project_id) -> dict:
    """The canonical served evaluation entry point for any project."""
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    econ = await build_project_economic_inputs(session, project_id)
    if not econ.ok:
        status = (
            "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"
            if any("BUDGET_MISSING" in b for b in econ.blockers)
            else "BLOCKED_INCOMPLETE_INPUTS"
        )
        return {"status": status, "blockers": econ.blockers}
    inputs = econ.inputs

    # Codex final P0 (canonical_fx) — ONE immutable, project-selected FX
    # context built here, ONCE, for this entire evaluation run, and
    # threaded through every price_allocated_structure() call below
    # (which threads it into every segment's price_segment()). Previously
    # each cap/native-threshold conversion re-imported and re-read the
    # mutable production_normalization.FX_LIVE_SNAPSHOT_DATE/
    # FX_RATE_SNAPSHOTS globals at an arbitrary point during its own
    # calculation — if a live FX refresh (app/services/fx_refresh.py)
    # mutated that global mid-evaluation, two candidates in the SAME
    # served result could silently be priced against two different
    # snapshots. Building it once here and passing it explicitly makes
    # "one evaluation, one snapshot" true by construction, never by
    # convention.
    import dataclasses
    from app.calculators.production_normalization import build_fx_context
    fx_context = build_fx_context()
    inputs = dataclasses.replace(inputs, fx_context=fx_context)

    # Codex final wiring remediation (P0-NL-001, third pass): computed
    # ONCE here, from THIS evaluation's own canonical FX context, and
    # unioned into evidenced_program_facts/amount_facts BEFORE the
    # fingerprint below is computed -- so a change in canonical company
    # identity, award period, or a sibling project's own persisted award
    # correctly invalidates any stale cached row for this project (both
    # fields already participate in _compute_fingerprint's existing
    # "evidenced_program_facts"/"amount_facts" payload). See
    # _company_period_prior_award_facts's own docstring for the full
    # identity/query/conversion contract.
    _company_period_evidenced, _company_period_amounts = await _company_period_prior_award_facts(
        session, project, inputs,
    )
    if _company_period_evidenced or _company_period_amounts:
        inputs = dataclasses.replace(
            inputs,
            evidenced_program_facts=inputs.evidenced_program_facts | _company_period_evidenced,
            amount_facts={**inputs.amount_facts, **_company_period_amounts},
        )

    # CLAUDE_CORRECT_FAILED_OPTIMIZER_CLOSEOUT, Section A — the Anchor
    # Budget Contract's own "supplied/embedded incentive" figure, read
    # ONCE here, inside the optimizer's own evaluation path (never in the
    # served-view layer, which only re-presents this same value going
    # forward). A real, honest, pre-existing model column
    # (BudgetLineItem.spend_category == 'incentive') that no code path in
    # this codebase read before this workstream. Already part of the
    # fingerprint implicitly: every budget line (any spend_category,
    # including 'incentive') is already hashed in full in `payload["lines"]`
    # inside _compute_fingerprint above, so adding, removing, or changing
    # a supplied-incentive line already forces a fresh evaluation without
    # any further fingerprint change needed here.
    _anchor_supplied_incentive_row = (await session.execute(
        select(func.sum(BudgetLineItem.amount_usd))
        .join(BudgetDocument, BudgetLineItem.budget_document_id == BudgetDocument.id)
        .where(BudgetDocument.project_id == project.id, BudgetLineItem.spend_category == "incentive")
    )).scalar()
    _anchor_supplied_incentive_usd = (
        float(_anchor_supplied_incentive_row) if _anchor_supplied_incentive_row is not None else None
    )

    # Fresh Project Source-Document Ingestion: the retroactive counterpart
    # to material_routing._route_screenplay's commit-time script analysis
    # -- a project whose screenplay Document/DocumentVersion predates that
    # commit-time wiring has a real, attached script that was simply never
    # analyzed. analyze_project_script is the existing SA-1 pipeline,
    # already idempotent (resolve_active_screenplay bootstraps a
    # ScreenplayDocument on demand; parse_and_persist only reparses on a
    # real input-fingerprint change) -- reused unchanged, never a second
    # script-analysis implementation. Called here, before role_known_
    # codes/script_facts are read below, so a legacy-imported screenplay's
    # facts are available on the SAME Evaluate call that first reaches
    # this point, with no separate manual trigger the product never
    # exposes.
    from app.services.script_analysis_service import analyze_project_script
    await analyze_project_script(session, project_id=project_id)

    # Workspace Data Completeness / Project Key Art: the SAME retroactive-
    # trigger pattern as analyze_project_script above, for cover-art
    # extraction from a screenplay Document/DocumentVersion that predates
    # this task's wiring. Reuses the existing, already-idempotent
    # material_routing.ensure_screenplay_artwork_extracted — never a
    # second extraction implementation, never generated/researched art.
    from app.services.material_routing import ensure_screenplay_artwork_extracted
    await ensure_screenplay_artwork_extracted(session, project_id)

    # CBA-008 — personnel, screenplay, and co-production facts are
    # material qualification inputs (they can move a candidate between
    # QUALIFIES/CURABLE_GAP/USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED) but
    # were previously fetched only later, per-candidate, and never
    # reached the fingerprint — an existing current-ENGINE_VERSION row
    # could keep serving a stale result after only these facts changed.
    # Fetched once here (same one-query-per-project pattern already
    # established below) and reused at both use sites — never re-fetched.
    role_known_codes = await role_known_codes_from_project(session, str(project_id))
    script_facts = await script_facts_from_project(session, str(project_id))
    # Part 4/CBA-004 — the SEPARATE typed nationality-vs-residency
    # breakdown (see evaluate_point_table_qualification's docstring).
    # Same one-query-per-project pattern; role_known_codes above is kept
    # unchanged as the legacy merged source for the 24-slug role registry.
    typed_personnel_facts = await typed_personnel_facts_from_project(session, str(project_id))
    # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — the real,
    # CONFIRMED-vs-unconfirmed attachment facts a treaty's own
    # PersonnelRequirement gate reads (never role_known_codes/
    # typed_personnel_facts above, which do not filter on
    # ProjectPerson.is_confirmed at all — correct for the pre-existing
    # 24-slug program registry those exist for, wrong for a NEW gate that
    # must never credit an unconfirmed attachment as current eligibility).
    # Same one-query-per-project pattern, fetched once and reused at
    # every treaty-loop call site below.
    role_attachment_facts = await role_attachment_facts_from_project(session, str(project_id))
    # Codex global optimizer audit, P0-QUAL-001: co-production facts are now
    # scoped per (treaty_slug, ordered participant identities) -- there is
    # no longer one project-global tuple to fetch here. Each treaty-
    # evaluation call site below fetches its own scoped facts via
    # _coproduction_facts(session, project.id, treaty_slug, participant_codes)
    # immediately before evaluating that candidate. For the fingerprint,
    # _all_coproduction_facts_for_fingerprint reads every scoped
    # co-production fact row for this project so a change to ANY treaty's
    # facts still invalidates the cached result.
    all_coproduction_facts = await _all_coproduction_facts_for_fingerprint(session, project.id)
    # Batched producer-control closeout (2026-09-03) — fetched once here
    # (same one-query-per-project pattern as role_known_codes/script_facts
    # above) and reused at both use sites (fingerprint below, and the
    # candidate filter further down) — never re-fetched.
    excluded_jurisdiction_codes = frozenset(await _excluded_jurisdiction_codes(session, project_id))
    # Item B — fetched once here (same pattern as excluded_jurisdiction_
    # codes directly above) and reused at both the fingerprint and the
    # candidate-filter use sites further down.
    discretionary_policy_facts = await _discretionary_policy_facts(session, project_id)
    fingerprint = _compute_fingerprint(
        inputs, role_known_codes=role_known_codes, script_facts=script_facts,
        coproduction_facts=all_coproduction_facts,
        excluded_jurisdiction_codes=excluded_jurisdiction_codes,
        discretionary_policy_facts=discretionary_policy_facts,
        role_attachment_facts=role_attachment_facts,
    )

    existing = (await session.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == fingerprint,
            # ENGINE_VERSION is part of freshness, not just the fingerprint:
            # a code change that enriches calculation_trace_json (e.g. the
            # 1.1.0 segments addition) must regenerate rows even when the
            # underlying budget/jurisdiction inputs are unchanged — the
            # fingerprint alone can't detect that the SHAPE of what gets
            # persisted changed, only that the ECONOMIC INPUTS didn't.
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).scalars().first()
    if existing is not None:
        return await _summarize_evaluation(session, project, inputs, fingerprint, reused=True)

    # Any prior evaluation for this project (a different fingerprint or an
    # older engine_version — a new budget version, or a stale result from
    # before this phase) is superseded, never left to render as current.
    # Its rows are not destroyed — they simply drop out of the "current"
    # query above, exactly as an unchanged Document/DocumentVersion keeps
    # prior versions rather than deleting them (see is_current elsewhere
    # in this codebase for the same convention).

    # FVD canonical input assembly repair (superseding the prior
    # CANONICAL_SERVED_WIRING_REPAIR.md Defect 1 disclosure-only note
    # below): derive_production_requirements() previously always received
    # {} regardless of real, persisted SA-1 script data. build_physical_
    # requirements() reads SA-1's own persisted ProjectLocationRequirement/
    # ProductionRequirement rows directly (read-only, no side effects) and
    # runs scripted-location text through the existing, generic
    # abstract_location() keyword ontology -- ontology-defined but never
    # wired to any consumer until this repair. No AI interpretation, no
    # invented quantities; a location string with no ontology hit and a
    # project with no SCRIPTED_LOCATION/PERIOD_REFERENCE rows on file both
    # still resolve to the same honest empty signal as before.
    #
    # Canonical authority substrate + feasibility boundary repair, Task 1/2
    # (this is now the ONLY consumer of `requirements` below): an earlier
    # version of this repair fed `requirements` directly into the discovery
    # pass that decides which jurisdictions become economic candidates --
    # conflating a soft production-feasibility signal (a landlocked
    # jurisdiction cannot host a Mediterranean sea-shore scene) with a hard
    # statutory/program eligibility failure, and silently removing 21
    # otherwise economically evaluable jurisdictions. `requirements` is now
    # used ONLY for the separate feasibility_discovery pass below --
    # disclosure, never rejection.
    requirements = derive_production_requirements(
        await build_physical_requirements(session, project_id)
    )
    # Canonical authority substrate + feasibility boundary repair, Task 1/2:
    # TWO discovery passes, deliberately. `feasibility_discovery` runs the
    # real, SA-1-derived requirements through discover_executable_
    # jurisdictions() to obtain each jurisdiction's genuine capability
    # examination (production_capable, capability_reasons) -- disclosure
    # only, NEVER consulted below to decide which jurisdictions become
    # candidates. `discovery` (economic candidate generation) intentionally
    # uses the SAME empty-requirements pass used before real requirements
    # existed, so a soft production-feasibility mismatch can never remove a
    # jurisdiction from the economic universe -- only an actual authority/
    # rate/threshold failure can. discover_executable_jurisdictions() is a
    # pure, side-effect-free function; calling it twice is inexpensive and
    # keeps the two concerns from ever sharing one classification.
    feasibility_discovery = discover_executable_jurisdictions(
        requirements=requirements,
        production_type=inputs.production_type,
        qpe_usd=inputs.gross_budget_usd,
        home_code=inputs.jurisdiction_code,
        # Codex final runtime remediation — the SAME evidenced/amount
        # facts threaded into _price_candidate/price_allocated_structure
        # below. Without this, a program whose only resolvable tier is
        # gated on a caller-evidenced fact (e.g. au_location_offset's
        # native AUD threshold) is classified "rejected" HERE, before
        # ever reaching the pricing pass, and the fact never has any
        # effect on the served structure's classification/blocker text.
        # CLAUDE_SPEND_THRESHOLD_AND_ANCHOR_CLOSEOUT: unioned with the same
        # producer-controlled administrative assumption set used by the real
        # pricing calls below (_price_candidate et al.) -- without this, a
        # program whose ONLY resolvable tier is gated on a producer-
        # controlled boolean fact (e.g. za_nfvf_rebate's accepted-production
        # confirmation, ca_bc_dave's eligible-activity confirmation) is
        # wrongly classified "capability_only"/rejected at DISCOVERY, before
        # the real per-component pricing pass (which already correctly
        # assumes these facts) ever gets a chance to test the real routed
        # spend. This never changes a genuine spend/cultural/discretionary
        # gate -- only the 6 verified-administrative keys in
        # _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS.
        evidenced_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        # CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR: threads the same
        # canonical FX context used everywhere else in this evaluation
        # into discover_executable_jurisdictions()'s generic
        # build_discovery_amount_probe() call, so a native-currency
        # amount_fact_key (AUD/MAD/THB/...) is converted with the real,
        # single-call, already-built context rather than a fresh one.
        fx_context=inputs.fx_context,
    )
    # Canonical program identity, not jurisdiction_code, is the uniqueness
    # key here too — feasibility disclosure is keyed by (code, program_slug)
    # so multiple independent programs sharing one jurisdiction (e.g.
    # CA-ON's ca_on_opstc / on_ofttc / OCASE) each get their OWN feasibility
    # examination rather than silently sharing whichever one a plain
    # code-keyed dict happened to retain last. A code-only fallback is kept
    # for any (code, slug) combination that, for whatever reason, isn't in
    # the pair map (defensive only — every examination is itself keyed by
    # exactly one (code, slug) already).
    feasibility_by_pair = {
        (e.jurisdiction_code, e.program_slug): e for e in feasibility_discovery.examinations
    }
    feasibility_by_code = {e.jurisdiction_code: e for e in feasibility_discovery.examinations}
    discovery = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type=inputs.production_type,
        qpe_usd=inputs.gross_budget_usd,
        home_code=inputs.jurisdiction_code,
        # CLAUDE_SPEND_THRESHOLD_AND_ANCHOR_CLOSEOUT: unioned with the same
        # producer-controlled administrative assumption set used by the real
        # pricing calls below (_price_candidate et al.) -- without this, a
        # program whose ONLY resolvable tier is gated on a producer-
        # controlled boolean fact (e.g. za_nfvf_rebate's accepted-production
        # confirmation, ca_bc_dave's eligible-activity confirmation) is
        # wrongly classified "capability_only"/rejected at DISCOVERY, before
        # the real per-component pricing pass (which already correctly
        # assumes these facts) ever gets a chance to test the real routed
        # spend. This never changes a genuine spend/cultural/discretionary
        # gate -- only the 6 verified-administrative keys in
        # _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS.
        evidenced_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    #: REJECTION TRACE IDENTITY. A jurisdiction can examine SEVERAL programs
    #: (CA-ON alone has three). Keying a rejection lookup by jurisdiction
    #: alone returns whichever examination happens to be first, so a program
    #: could report ANOTHER program's canonical reason. Every disposition must
    #: state its own. Keyed by (jurisdiction_code, program_slug), with a
    #: jurisdiction-only fallback for a candidate that names no program.
    examination_by_pair = {
        (e.jurisdiction_code, e.program_slug): e for e in discovery.examinations
    }
    examination_by_code = {e.jurisdiction_code: e for e in discovery.examinations}

    # CineGlobe canonical pricing path + discovery repair: candidate
    # identity is (jurisdiction_code, program_slug), never jurisdiction_code
    # alone. The previous `next(...)` lookups here took only the FIRST
    # accepted/capability_only program for a given code, silently dropping
    # every other independently-discovered program sharing that
    # jurisdiction (Ontario's ca_on_opstc/on_ofttc/OCASE case). Discovery
    # itself (production_discovery.py) already examines every (code, slug)
    # pair independently; this loop must consume ALL of them, not collapse
    # back to one per code.
    candidates: list[tuple[str, str, str]] = []  # (code, program_slug, discovery_classification)
    for code, slug in discovery.accepted:
        if code == inputs.jurisdiction_code:
            candidates.append((code, slug, "incentive_ready"))
    for code, slug in discovery.accepted_alternatives(inputs.jurisdiction_code):
        candidates.append((code, slug, "incentive_ready"))
    for examination in discovery.examinations:
        if examination.classification == "capability_only" and examination.program_slug:
            candidates.append((examination.jurisdiction_code, examination.program_slug, "capability_only"))
    # Eight-control closeout, HO-011: confirmed via direct instrumentation
    # a real, adjudicated authority-blocked program (economic_block_for_
    # program(slug) is not None -- FAIL_CLOSED/DISPLAY_ONLY_ZERO_
    # GUARANTEED/etc, the SAME real registry every other check in this
    # file already consults) was silently dropped entirely -- never
    # reaching even a persisted RULE_REJECTED row -- whenever production_
    # discovery.py's own capability-first classification landed on
    # "rejected" rather than "capability_only" (its "no structured
    # capability profile and no priceable incentive model" branch, which
    # this file's own candidate-building loop above never consumed at
    # all). The single-program pricing loop immediately below ALREADY
    # persists a real, precise STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT/
    # AUTHORITY_EXHAUSTED_FAIL_CLOSED row for any candidate it receives
    # that carries a real economic block (confirmed by direct code
    # reading) -- the defect was purely that such a candidate never
    # reached that loop for a jurisdiction with no structured capability
    # profile on file. Every already-blocked program is added here
    # exactly once (never duplicating an incentive_ready/capability_only
    # entry the loops above already added), regardless of production_
    # discovery.py's own capability classification -- a REAL,
    # already-adjudicated authority block is never silently omitted, the
    # same "never silently omitted" doctrine already applied to REG-5/
    # HO-007/HO-012 above.
    _already_candidate_pairs = {(c, s) for c, s, _cls in candidates}
    for examination in discovery.examinations:
        if not examination.program_slug:
            continue
        pair = (examination.jurisdiction_code, examination.program_slug)
        if pair in _already_candidate_pairs:
            continue
        if _economic_block_for_program(examination.program_slug) is None:
            continue
        candidates.append((examination.jurisdiction_code, examination.program_slug, "authority_blocked"))
        _already_candidate_pairs.add(pair)

    # Batched producer-control closeout (2026-09-03) -- generic PROJECT-
    # LEVEL candidate-jurisdiction inclusion/exclusion election. A pure
    # producer MODELING preference (which jurisdictions this project's
    # own candidate universe considers), never a change to law/doctrine/
    # rate/preapproval/content requirements -- those stay exactly as
    # discovered/priced for any jurisdiction that IS still in the
    # universe. Read via the SAME generic ProjectFact mechanism/
    # precedence every other producer-settable fact already uses (see
    # _copro_facts above and cineglobe.py's /assumptions endpoint) --
    # never a second persistence mechanism, never a Saudi-specific
    # column. Filtered HERE, at the single earliest point every
    # downstream candidate consumer shares (full_relocation,
    # component_relocation's target routing, and treaty co-production
    # partner discovery all derive from `candidates`/`priced_by_code`
    # below) -- an excluded jurisdiction is removed from the candidate
    # universe itself, never merely hidden by a later filter/CSS, so it
    # cannot become Top Priced Candidate, Top Structure, a
    # recommendation, or a comparison candidate. The production's own
    # home/base jurisdiction can never be excluded from its own
    # candidate universe -- only alternative candidates are eligible.
    if excluded_jurisdiction_codes:
        candidates = [
            c for c in candidates
            if c[0] not in excluded_jurisdiction_codes or c[0] == inputs.jurisdiction_code
        ]

    # Item B (Final non-Globe closeout, 2026-09-04) -- generic
    # discretionary/selective-program policy, applied at the SAME single
    # earliest choke point as the jurisdiction exclusion immediately
    # above (full_relocation, component_relocation target routing, and
    # treaty co-production partner discovery all derive from `candidates`
    # below, so this is generic for every structure type without any
    # per-structure-type code). A program this project's resolved policy
    # excludes never becomes a candidate at all:
    #   CASE 1 (formulaic base + a SEPARATE discretionary add-on program
    #     at the same or a different jurisdiction): only the
    #     discretionary program's own candidate is removed here -- the
    #     formulaic base program is a DIFFERENT program_slug and is
    #     untouched, so its own single-program candidate (and therefore
    #     its own structure) is preserved exactly as before.
    #   CASE 2 (a candidate whose ONLY program is itself discretionary):
    #     removing its sole candidate here means no structure is ever
    #     generated for it -- it leaves the modeled/ranked universe
    #     entirely, per the required economic behavior.
    #   CASE 3 (creator/project-specific fund): unaffected by this
    #     mechanism either way -- filtering is per program_slug, never
    #     per jurisdiction, so a fund never becomes a jurisdiction-wide
    #     uplift merely because of where it is administered.
    # Same home/base-jurisdiction protection as excluded_jurisdiction_
    # codes above, for the same reason: a project's own base candidate
    # can never be removed by a project MODELING preference.
    if discretionary_policy_facts:
        _discretionary_excluded_program_slugs = {
            slug for _, slug, _ in candidates
            if _is_discretionary_program(slug)
            and _discretionary_policy_resolve(slug, discretionary_policy_facts) == "exclude"
        }
        if _discretionary_excluded_program_slugs:
            candidates = [
                c for c in candidates
                if c[1] not in _discretionary_excluded_program_slugs or c[0] == inputs.jurisdiction_code
            ]

    jurisdiction_rows = (await session.execute(select(Jurisdiction))).scalars().all()
    jurisdiction_by_code = {j.code: j for j in jurisdiction_rows}

    # Multiple independent programs can share one jurisdiction_code (Ontario's
    # ca_on_opstc/on_ofttc/OCASE). Every existing single-program jurisdiction's
    # label/description is unchanged (this dict evaluates to 1 for them); only
    # a genuinely multi-program code gets the program name appended, so each
    # of that code's structures stays individually identifiable rather than
    # rendering as N indistinguishable rows sharing one label.
    candidates_per_code: dict[str, int] = {}
    for code, _slug, _classification in candidates:
        candidates_per_code[code] = candidates_per_code.get(code, 0) + 1

    # Existing Optimizer/Stacker Reconnection — "Multiple programs in one
    # jurisdiction" / "Federal + provincial-state" capability. Each
    # successfully-priced single-program candidate is recorded here as it
    # is priced below; after the loop, every jurisdiction with >=2 priced
    # programs is run through the canonical stack-pricing bridge
    # (canonical_stack_bridge.py), which reuses the existing, engine-
    # agnostic apply_stacking_adjustments/evaluate_legal_stacking
    # calculators against this SAME pricing — never the superseded
    # run_full_analysis path generate_structure_scenarios.py depends on.
    # See docs/validation/CODEX_EXISTING_OPTIMIZER_LINEAGE_TRACE.md.
    priced_by_code: dict[str, list[StackCandidate]] = {}
    # CBA-002 continuation, Section 3 — "a stack must inherit the unresolved/
    # failed state of its members correctly." Combined multi-program
    # structures below are built purely from StackCandidate (no
    # qualification field), so without this, a combo's own trace never set
    # role_qualification at all and the Recommended-admission gate's `state
    # is None -> allowed` default let a combo bypass qualification entirely,
    # even when one of its members individually carries a real gap. Recorded
    # per (jurisdiction_code, program_slug) as each single-program candidate
    # is resolved below; consulted when each combo's own trace is built.
    #
    # OH-002 fix (CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT): a combo's own
    # jurisdiction_code (e.g. "CA-ON") is NOT necessarily the code each of
    # its members was individually examined under -- a federal member like
    # ca_federal_cptc is examined under "CA", not "CA-ON". The combo trace
    # builder below used to look up (stack_result.jurisdiction_code, slug),
    # silently missing every federal-under-a-provincial-stack member and
    # letting its real qualification state (which could be HARD_FAIL,
    # USER_FACT_REQUIRED, etc.) drop out of the combo's worst-state
    # computation entirely. Program identity, not jurisdiction_code, is
    # the correct key for this lookup -- also consistent with this exact
    # file's own established "program identity, not jurisdiction_code
    # alone, is the uniqueness key" convention used everywhere else (see
    # e.g. _price_candidate's structure_id). Indexed by slug alone here;
    # _qual_state_by_code_program is kept too (nothing else in this file
    # depends on removing it).
    _qual_state_by_code_program: dict[tuple[str, str], str | None] = {}
    _qual_state_by_program: dict[str, str | None] = {}
    # Codex final four-row remediation (P0-SEL-ALT-001): the FULL merged
    # role_qualification dict (missing_facts/curable_requirements/
    # failed_requirements/reasoning_trace/qualification_route), keyed by
    # program_slug alone (same key as _qual_state_by_program, same
    # worse-wins semantics), so component/stack aggregation can retain
    # every participant's complete detail instead of collapsing to a
    # single severity string. Value is (jurisdiction_code, full_dict) so
    # the aggregate can disclose WHICH jurisdiction the retained detail
    # was captured under, even though the dict itself is looked up by
    # program identity alone (the same federal-member-under-a-different-
    # code reason _qual_state_by_program's own comment already documents).
    _qual_detail_by_program: dict[str, tuple[str, dict | None]] = {}

    # role_known_codes/script_facts (Canonical Co-production Qualification
    # Reconnection / Worldwide Qualification Consumption Closeout) are
    # fetched once, near the top of this function (see CBA-008 note there
    # — they're also part of the cache fingerprint now) and reused here.

    for code, program_slug, classification in candidates:
        jurisdiction = jurisdiction_by_code.get(code)
        disambiguate = candidates_per_code.get(code, 1) > 1
        program_label = f" ({_program_display_name(program_slug)})" if disambiguate else ""
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=(
                f"{code} — production's current base{program_label}"
                if code == inputs.jurisdiction_code else f"Full relocation to {code}{program_label}"
            ),
            description=(
                "The production's own confirmed base jurisdiction, priced as-is."
                if code == inputs.jurisdiction_code else
                "Whole production relocated; nominal budget unchanged (no regional "
                "cost normalization applied)."
            ),
            jurisdiction_allocations=(
                [{"jurisdiction_id": str(jurisdiction.id), "shoot_pct": 100, "budget_pct": 100}]
                if jurisdiction else []
            ),
            claimed_program_ids=[],
        )
        session.add(structure)
        await session.flush()

        # Task 1/2 — feasibility disclosure computed once per candidate,
        # from the real-requirements examination, attached to every terminal
        # branch below. Never consulted for the classification/candidates
        # decisions above — see the module note on _feasibility_status().
        feasibility_status, feasibility_reasons = _feasibility_status(
            feasibility_by_pair.get((code, program_slug), feasibility_by_code.get(code)), requirements,
        )

        if classification == "capability_only":
            # Discovery already knows this program has no priceable route —
            # re-attempting pricing would only rediscover the same fact via
            # a failed derive_qualification_register call. Codex Defect 4:
            # the terminal cause is classified from discovery's own already-
            # computed fields (never re-evaluated), not flattened to a
            # single generic status.
            examination = examination_by_pair.get(
                (code, program_slug), examination_by_code.get(code)
            )
            candidate_status, rejection_reason_class, reason = _capability_only_status(examination)
            # Eight-control closeout, HO-010: the same conditional-program
            # disclosure every combined/treaty structure already carries
            # (_conditional_data(), unchanged) was never attached to a
            # bare single-program candidate row -- so a real, now-
            # reconciled conditional catalog node (e.g. Creative
            # Saskatchewan, canonical_program_slug="ca_sk_creative_
            # saskatchewan_grant") never appeared on the one structure
            # most directly about that exact jurisdiction/program. Purely
            # additive: identical helper, identical shape every other
            # structure type already serves.
            _cap_only_conditional_programs, _cap_only_conditional_compat = _conditional_data(
                str(structure.id), code, (program_slug,) if program_slug else (),
            )
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                structure_type="single_country" if code == inputs.jurisdiction_code else "full_relocation",
                calculation_trace_json={
                    "candidate_status": candidate_status,
                    "rejection_reason_class": rejection_reason_class,
                    "discovery_classification": classification,
                    "program_slug": examination.program_slug if examination else program_slug,
                    "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                    # ITEM 5: a capability_only candidate can BE the
                    # production's baseline (California's competitive credit
                    # is exactly this case). Without this the blocked baseline
                    # was anonymous and the summary reported no baseline at all.
                    "is_baseline": code == inputs.jurisdiction_code,
                    "relocation_cost_normalized": code == inputs.jurisdiction_code,
                    "is_directly_comparable": code == inputs.jurisdiction_code,
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                    "conditional_programs": _cap_only_conditional_programs,
                    "conditional_compatibility": _cap_only_conditional_compat,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        pricing, register, rate_resolution = _price_candidate(inputs, code, program_slug)
        # ITEM 5. Computed BEFORE the unpriceable branch below. It used to be
        # derived only after it, so every authority/rule-blocked candidate
        # persisted a trace with NO is_baseline -- a BLOCKED BASELINE became
        # indistinguishable from a blocked relocation, the summary reported
        # baseline=null (fail-closed silently DROPPED the row instead of
        # disclosing it), and the leader fell through to the lowest-NPC
        # relocation. Failing closed means no NUMBER, never no ROW.
        is_baseline = code == inputs.jurisdiction_code
        if pricing is None or not pricing.is_fully_priced:
            if pricing is None:
                # Codex Defect 4: resolve_program_rate() returned None for
                # one of two materially different reasons — classify which,
                # by mirroring its own eligibility gate read-only (no rule
                # re-evaluation, no changed outcome).
                qpe_for_probe = round(sum(
                    a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                ), 2)
                failure = classify_rate_resolution_failure(
                    program_slug, inputs.production_type, qpe_for_probe,
                )
                if failure == RATE_FAILURE_AUTHORITY_EXHAUSTED:
                    # B4 central authority gate (Codex bounded remediation):
                    # accepted authority-exhausted / discretionary-display-only
                    # / retired / duplicate identity. Fail closed — a visible
                    # ROW carrying zero guaranteed value, never a NUMBER, never
                    # Recommended. A stale RateRule cannot override this.
                    candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
                    rejection_reason_class = "AUTHORITY_EXHAUSTED_FAIL_CLOSED"
                    block = _economic_block_for_program(program_slug)
                    reason = (
                        block.reason if block is not None
                        else "Program authority is exhausted; automatic pricing is refused."
                    )
                elif failure == RATE_FAILURE_NO_RULES:
                    candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
                    rejection_reason_class = "AUTHORITY_INSUFFICIENT"
                    reason = "No statutory rate rules exist for this program."
                else:
                    candidate_status = STATUS_RULE_REJECTED
                    rejection_reason_class = "STATUTORY_CONDITIONS_UNMET"
                    reason = (
                        f"Statutory rate rules exist for this program but do not resolve "
                        f"for this production's type/QPE (${qpe_for_probe:,.2f})."
                    )
            else:
                candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
                rejection_reason_class = "PRICING_BLOCKED"
                reason = "; ".join(pricing.blockers) or "Not fully priced."
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                structure_type="single_country" if code == inputs.jurisdiction_code else "full_relocation",
                calculation_trace_json={
                    "candidate_status": candidate_status,
                    "rejection_reason_class": rejection_reason_class,
                    "discovery_classification": classification,
                    "program_slug": program_slug,
                    "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                    "is_baseline": is_baseline,
                    "relocation_cost_normalized": is_baseline,
                    "is_directly_comparable": is_baseline,
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), code, (program_slug,),
        )
        _opportunities = _opportunities_for_candidate(
            inputs, code, program_slug, register, rate_resolution, role_known_codes,
        )
        _role_qualification = _role_qualification_for_candidate(
            code, program_slug, role_known_codes, script_facts,
            typed_personnel_facts=typed_personnel_facts,
        )
        # CBA-002 continuation: propagate real, eligibility-relevant rate
        # condition outcomes (min_qpe_pct_of_total_budget / project_fact_
        # dependent_eligibility / unmodeled_spend_split_ratio) into the same
        # qualification state both the pricing-admission gate below and the
        # Recommended-admission gate downstream already read — the worse of
        # the role/cultural state and the rate-condition state always wins.
        _role_qualification = _merge_rate_condition_into_qualification(
            _role_qualification, rate_resolution, program_slug, code,
        )
        _this_qual_state = (_role_qualification or {}).get("state")
        _qual_state_by_code_program[(code, program_slug)] = _this_qual_state
        # OH-002 fix: also index by program identity ALONE (see the dict's
        # own declaration comment above for why the combo-trace lookup
        # cannot rely on jurisdiction_code). If the same program_slug is
        # ever examined under more than one code, keep the WORSE of the
        # two states — never silently let a later, better-looking
        # examination erase an earlier real gap.
        if program_slug not in _qual_state_by_program:
            _qual_state_by_program[program_slug] = _this_qual_state
            _qual_detail_by_program[program_slug] = (code, _role_qualification)
        else:
            _prior_state = _qual_state_by_program[program_slug]
            if _QUAL_STATE_SEVERITY.get(_this_qual_state, 2) < _QUAL_STATE_SEVERITY.get(_prior_state, 2):
                _qual_state_by_program[program_slug] = _this_qual_state
                _qual_detail_by_program[program_slug] = (code, _role_qualification)
        warnings = [LIMITATION_NOTE] if is_baseline else [LIMITATION_NOTE, RELOCATION_COMPARABILITY_NOTE]
        # Two-axis authority correction: a program priced under a
        # PROVENANCE_DISCLOSURE_STATES disposition (real rate data, but its
        # structured-provenance citation trail is not yet upgraded to a
        # primary/official source) must disclose that gap on every served
        # result carrying it — priced does not mean fully knowledge-verified.
        _authority_state = coverage_state(program_slug)
        if _authority_state in PROVENANCE_DISCLOSURE_STATES:
            warnings = warnings + [
                f"Authority provenance incomplete ({_authority_state}): "
                + STATE_REASON.get(_authority_state, "")
            ]
            # Codex canonical identity/authority cleanup: a warning STRING
            # alone never prevented this candidate from reaching Recommended/
            # rank-1 -- qualification_state (the field the Recommended-
            # admission gate and _QUALIFICATION_ADMITS_RECOMMENDED actually
            # read) was left untouched. A provenance-unresolved result must
            # never present as fully knowledge-verified: downgrade to
            # QUAL_AUTHORITY_UNRESOLVED via the SAME worse-wins merge every
            # other qualification signal in this function already uses --
            # never weakens an existing worse state (HARD_FAIL/CURABLE_GAP/
            # etc.), never invents QUALIFIES.
            _prov_existing_state = (_role_qualification or {}).get("state")
            if _QUAL_STATE_SEVERITY.get(QUAL_AUTHORITY_UNRESOLVED, 1) < _QUAL_STATE_SEVERITY.get(_prov_existing_state, 2):
                _role_qualification = dict(_role_qualification or {
                    "regime_id": program_slug, "jurisdiction_code": code,
                    "qualification_route": "authority_provenance_gate",
                    "role_findings": [], "current_points": None, "required_points": None,
                    "contribution_requirements": [], "ownership_control_requirements": [],
                    "resolved_facts": [], "failed_requirements": [], "curable_requirements": [],
                    "available_levers": [], "authority_basis": None, "confidence_state": "MEDIUM",
                })
                _role_qualification["state"] = QUAL_AUTHORITY_UNRESOLVED
                _role_qualification["missing_facts"] = list(_role_qualification.get("missing_facts") or []) + [
                    f"{program_slug}_primary_authority_source",
                ]
                _role_qualification["reasoning_trace"] = list(_role_qualification.get("reasoning_trace") or []) + [
                    f"Authority provenance incomplete ({_authority_state}): "
                    + STATE_REASON.get(_authority_state, "")
                ]
                _this_qual_state = QUAL_AUTHORITY_UNRESOLVED
                _qual_state_by_code_program[(code, program_slug)] = _this_qual_state
                if _QUAL_STATE_SEVERITY.get(_this_qual_state, 2) < _QUAL_STATE_SEVERITY.get(
                    _qual_state_by_program.get(program_slug), 2
                ):
                    _qual_state_by_program[program_slug] = _this_qual_state
                    _qual_detail_by_program[program_slug] = (code, _role_qualification)
        # Master reconciliation, 2026-09-02: administrative/competitive-
        # allocation risk is a DIFFERENT axis from whether a deterministic
        # rate exists. A Credit Allocation Letter, an application window, a
        # capacity-limited annual round, or a ranked-selection process does
        # NOT by itself make a program's already-priced, guaranteed floor
        # rate non-deterministic -- it is a real risk about WHETHER this
        # production receives the incentive it has otherwise correctly
        # priced, disclosed here rather than silently zeroing the number
        # (that conflation was exactly the repealed _derived_coverage()
        # defect -- see authority_coverage_registry.py's repeal comment).
        _competitive_disclosure = _competitive_allocation_disclosure(program_slug)
        if _competitive_disclosure:
            warnings = warnings + [_competitive_disclosure]
        # FVD canonical input assembly repair, Task 2 — UNKNOWN territorial
        # facts stay visibly provisional rather than being silently absorbed
        # as though "confirmed none." An absent ProjectFact still resolves
        # to an empty account set for the qualification ladder itself (the
        # only safe input a set-membership check can be given without
        # inventing evidence — see _fact_account_set), but the SERVED result
        # must not read as equivalent to a project that actually confirmed
        # no accounts are stated outside its base jurisdiction. When either
        # territorial fact was never stated at all, this candidate's QPE is
        # flagged has_unverified_inputs=True with an explicit warning —
        # blocking in the sense of requiring confirmation before being
        # treated as final, never blocking the evaluation itself.
        territorial_state_unknown = (
            inputs.accounts_outside_jurisdiction_state == FACT_STATE_UNKNOWN
            or inputs.offshore_payroll_accounts_state == FACT_STATE_UNKNOWN
        )
        if territorial_state_unknown:
            warnings = warnings + [
                "UNKNOWN, not KNOWN EMPTY: no project fact has ever stated which "
                "accounts (if any) are incurred outside the base jurisdiction or "
                "routed through offshore payroll. This QPE assumes none are — the "
                "only input a set-membership check can be given without inventing "
                "evidence — but that assumption is unconfirmed, not verified."
            ]
        # Consolidated Backend Correction, CBA-001 (revised) — qualification
        # is a PRE-ADMISSION gate only for HARD_FAIL. A candidate whose
        # qualification is a genuine but UNRESOLVED gap (Curable Gap/User
        # Fact Required/Script Fact Required/Authority Unresolved/Rule Data
        # Incomplete) is still priced normally below (enters priced_by_code,
        # can be stacked/combined/ranked) — Part 2's own "-> opportunity/
        # disclosure" mapping means disclosed-with-real-economics, not
        # blocked; the real gap is still visible on role_qualification.
        # Only HARD_FAIL reaches this block now and is reported as truly
        # unavailable — no total_incentive_value_usd/npc, no pricing at all.
        _qual_state = (_role_qualification or {}).get("state")
        if _qual_state is not None and _qual_state not in _QUALIFICATION_ADMITS_PRICING:
            _blocked_candidate_status = (
                STATUS_QUALIFICATION_HARD_FAIL if _qual_state == QUAL_HARD_FAIL
                else STATUS_QUALIFICATION_UNRESOLVED
            )
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True,
                warnings=[LIMITATION_NOTE, (
                    f"Qualification state {_qual_state} blocks admission to pricing/stacking/"
                    "ranking. The figures below are POTENTIAL economics only, disclosed as an "
                    "opportunity — they are not a priced, comparable, or rankable result."
                )],
                structure_type="single_country" if code == inputs.jurisdiction_code else "full_relocation",
                calculation_trace_json={
                    "candidate_status": _blocked_candidate_status,
                    "discovery_classification": classification,
                    "program_slug": program_slug,
                    "reason": f"Qualification state {_qual_state} — see role_qualification for the exact gap.",
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                    "is_baseline": is_baseline,
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                    "role_qualification": _role_qualification,
                    "opportunities": _opportunities,
                    "conditional_programs": _conditional_program_dicts,
                    "conditional_compatibility": _conditional_compatibility_dict,
                    # Real, already-computed pricing — disclosed as the
                    # OPPORTUNITY value ("what this would be worth once
                    # qualification resolves"), never as an admitted,
                    # rankable NPC. Part 2's "CURABLE_GAP/USER_FACT_
                    # REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED ->
                    # opportunity/disclosure" requirement.
                    "potential_economics": {
                        "selected_incentive_usd": pricing.selected_incentive_usd,
                        "npc_verified_usd": pricing.npc_verified_usd,
                        "npc_with_adjustments_usd": pricing.npc_with_adjustments_usd,
                        "modeled_rate": rate_resolution.modeled_rate,
                        "qualifying_spend_usd": round(sum(
                            a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                        ), 2),
                    },
                },
                input_fingerprint=fingerprint,
            ))
            continue

        _qpe_for_stack = round(sum(
            a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
        ), 2)
        doctrine_record = _get_doctrine(program_slug)
        priced_by_code.setdefault(code, []).append(StackCandidate(
            program_slug=program_slug,
            jurisdiction_code=code,
            selected_incentive_usd=pricing.selected_incentive_usd or 0.0,
            effective_rate=rate_resolution.modeled_rate,
            qualifying_spend_usd=_qpe_for_stack,
            incentive_type=doctrine_record.incentive_type if doctrine_record else "",
            # Codex global optimizer audit, P1-TRACE-001 remediation: real
            # BudgetLine.line_id identities this program's own register
            # marked QUALIFIES -- the exact-union basis for a later
            # multi-program combination's true unique allocated spend.
            qualifying_line_ids=frozenset(
                a.line_id for a in register if a.state == QualificationState.QUALIFIES
            ),
        ))
        _reloc_complete, _reloc_missing = _relocation_completeness(is_baseline, code, inputs)
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=pricing.selected_incentive_usd,
            true_net_cost_usd=pricing.npc_verified_usd,
            risk_adjusted_net_cost_usd=pricing.npc_with_adjustments_usd,
            has_unverified_inputs=territorial_state_unknown, warnings=warnings,
            structure_type=pricing.structure_type,
            calculation_trace_json={
                "candidate_status": STATUS_PRICED,
                # Canonical optimizer/Globe wiring remediation (2026-09-04),
                # Section 5: MODELED POTENTIAL RATE vs AWARD/EXECUTION
                # CERTAINTY are two different axes -- a program can be
                # deterministically priced and STILL be administratively/
                # discretionarily gated (Saudi is the first real instance,
                # never the only one this is scoped to). Previously this
                # fact lived ONLY inside a prose warnings string a consumer
                # would have to pattern-match; now also served as a real
                # structured boolean, generically derived from the SAME
                # program_requirements.allocation_type/preapproval_mandatory
                # facts _competitive_allocation_disclosure already reads --
                # never a Saudi-specific flag, never a second derivation.
                "administrative_allocation_risk": bool(_competitive_disclosure),
                "discovery_classification": classification,
                "modeled_rate": rate_resolution.modeled_rate,
                "rate_basis": rate_resolution.basis,
                "qualifying_spend_usd": round(sum(
                    a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                ), 2),
                "is_baseline": is_baseline,
                # Codex final wiring remediation (P0-SEL-ALT-001, third
                # pass): replaced the single blanket
                # relocation_completeness_evidenced__{code} fact with a
                # structured, PER-DIMENSION completeness decision — see
                # _relocation_completeness's own docstring. No such fact
                # exists for any project today, so this correctly remains
                # False for every non-baseline candidate exactly like the
                # pre-repair behavior, until real producer-verified
                # per-dimension relocation-completeness facts exist.
                "relocation_cost_normalized": _reloc_complete,
                # Codex Defect 2 — economic priceability (candidate_status
                # == PRICED, always true here) and regional comparability
                # are two different states. is_directly_comparable is the
                # SAME fact as relocation_cost_normalized under an
                # unambiguous name, so a downstream reader never has to
                # infer "comparable" from a field named for something else.
                # is_fully_priced (this candidate priced successfully) must
                # never be overwritten by this — see canonical_production_view.py.
                "is_directly_comparable": _reloc_complete,
                # Codex final wiring remediation (P0-SEL-ALT-001): the
                # EXACT, per-dimension causes of non-comparability — never
                # a single blanket flag. Empty for the baseline and for a
                # fully-evidenced candidate. Consulted by
                # canonical_production_view.py's conditional-pool
                # admission gate to prove every blocker belongs to the
                # approved curable (missing relocation evidence) category
                # before ever admitting a non-comparable row as a
                # conditional alternative.
                "relocation_missing_dimensions": list(_reloc_missing),
                "relocation_completeness_jurisdiction": code,
                "structure_type": pricing.structure_type,
                "primary_jurisdiction": pricing.primary_jurisdiction,
                # Same field already present on unpriced/capability_only
                # trace rows (see below) -- was previously missing here, the
                # one PRICED branch. Needed to disambiguate multiple
                # independent programs sharing one jurisdiction_code (Task
                # 6's Ontario control) at the served view layer.
                "program_slug": program_slug,
                "selected_incentive_usd": pricing.selected_incentive_usd,
                "npc_verified_usd": pricing.npc_verified_usd,
                "npc_conservative_usd": pricing.npc_verified_usd,
                "gross_budget_usd": pricing.gross_budget_usd,
                "segments": _segment_dicts(pricing),
                # CLAUDE_CORRECT_FAILED_OPTIMIZER_CLOSEOUT, Section A — the
                # Anchor Budget Contract, computed and persisted HERE,
                # inside the optimizer's own evaluation path, at the ONE
                # candidate this evaluation resolves as the real anchor
                # (is_baseline True for exactly one candidate). Never
                # recomputed by the served-view layer — canonical_
                # production_view.compute_anchor_budget_contract() reads
                # this field verbatim; it is not the field's source.
                # Never subtracts both supplied and calculated incentives
                # (supplied is disclosure-only, never netted against the
                # calculated figure below); the canonical (calculated)
                # incentive remains optimizer truth. None for every
                # non-baseline candidate (this structure/pricing pass
                # exists for every candidate, but only the real anchor
                # carries this contract).
                "anchor_contract": ({
                    "gross_budget_usd": inputs.gross_budget_usd,
                    "supplied_incentive_usd": _anchor_supplied_incentive_usd,
                    "calculated_anchor_incentive_usd": pricing.selected_incentive_usd,
                    "variance_usd": (
                        round((pricing.selected_incentive_usd or 0.0) - _anchor_supplied_incentive_usd, 2)
                        if _anchor_supplied_incentive_usd is not None and pricing.selected_incentive_usd is not None
                        else None
                    ),
                    "financing_adjustment_usd": pricing.financing_cost_usd or 0.0,
                    "anchor_npc_usd": pricing.npc_verified_usd,
                } if is_baseline else None),
                # Task 3 (canonical pricing path + discovery repair) — ONE
                # canonical served NPC representation. Every dollar between
                # (npc_verified_usd, i.e. budget - incentive) and
                # npc_with_adjustments_usd is a NAMED field here, never a
                # hidden residual — even though every value is currently
                # 0.0/None (no per-project travel/FX/in-kind/local-cost/
                # financing/implementation input exists generically yet; see
                # the module docstring's MFNI note). Reading straight off
                # `pricing` — no new economics, serialization only.
                "adjustments": {
                    "travel_incremental_delta_usd": pricing.travel_incremental_delta_usd,
                    "fx_delta_usd": pricing.fx_delta_usd,
                    "inkind_replacement_delta_usd": pricing.inkind_replacement_delta_usd,
                    "local_cost_delta_usd": pricing.local_cost_delta_usd,
                    "financing_cost_usd": pricing.financing_cost_usd,
                    "implementation_cost_usd": pricing.implementation_cost_usd,
                    "total_adjustments_usd": round(
                        (pricing.npc_with_adjustments_usd or 0.0) - (pricing.npc_verified_usd or 0.0), 2
                    ),
                },
                # Disclosure (does not change this candidate's own
                # qualification outcome — the ladder still receives the same
                # empty-set input either way; see the has_unverified_inputs/
                # warnings block above for how UNKNOWN is now surfaced as
                # provisional): whether the two territorial ProjectFact keys
                # were ever actually stated for this project, and how many
                # real SA-1 ProductionRequirement rows exist on file.
                # SCRIPTED_LOCATION and PERIOD_REFERENCE rows ARE now
                # consumed generically (build_physical_requirements()) for
                # the feasibility_status/feasibility_reasons disclosure
                # below (never for economic discovery/eligibility — see the
                # canonical authority substrate + feasibility boundary
                # repair module note above _feasibility_status()) — this
                # count still includes CHARACTER/EXPLICIT_VEHICLE/
                # EXPLICIT_ANIMAL/EXPLICIT_WEAPON/EXPLICIT_MINOR rows, which
                # have no corresponding capability vocabulary in
                # derive_production_requirements() and remain unmapped.
                "accounts_outside_jurisdiction_state": inputs.accounts_outside_jurisdiction_state,
                "offshore_payroll_accounts_state": inputs.offshore_payroll_accounts_state,
                "production_requirements_on_file": inputs.production_requirements_on_file,
                # Task 1/2 — production feasibility, disclosed alongside a
                # PRICED result, never used to have prevented it from being
                # priced. A jurisdiction can be economically PRICED and
                # feasibility WEAK at the same time (e.g. a landlocked
                # jurisdiction for a marine-heavy screenplay) — the two
                # concepts are independent by design.
                "feasibility_status": feasibility_status,
                "feasibility_reasons": feasibility_reasons,
                # Existing Optimizer/Stacker Reconnection, Task 7 — see
                # _conditional_data()'s own docstring: opportunity data
                # only, never entered into NPC/economics above.
                "conditional_programs": _conditional_program_dicts,
                "conditional_compatibility": _conditional_compatibility_dict,
                # Reinvestment + Qualification Opportunity Optimization —
                # see canonical_opportunity_bridge.py. Never enters NPC/
                # ranking; every dollar figure traces to the SAME register/
                # rate already computed above or to the project's own real
                # budget lines.
                "opportunities": _opportunities,
                # Canonical Co-production Qualification Reconnection —
                # disclosure only (Task 11), never a pricing/admission
                # gate for this already-priced single-program candidate:
                # canonical_role_qualification_bridge.py's real, 24-
                # program-slug-covered role/nationality gate result.
                "role_qualification": _role_qualification,
            },
            input_fingerprint=fingerprint,
        ))

    # Existing Optimizer/Stacker Reconnection — multi-program combinations,
    # N-way (2 or more programs). Additive only: every existing single-
    # program candidate persisted above is untouched.
    #
    # Candidates are grouped into LOCATION GROUPS: for each country, the
    # federal-level candidates (jurisdiction_code == the bare country
    # prefix, e.g. "CA") plus each specific province/state's own
    # candidates form one location group per province/state — mirroring
    # eligible_group_for_combination()'s own rule that a valid combination
    # may span federal + AT MOST ONE specific province/state, never two.
    # This also keeps the search bounded: real production combinations are
    # never a full cross-product of every candidate in one country, only
    # within one physically coherent shoot location.
    priced_by_country: dict[str, list[StackCandidate]] = {}
    for code, stack_candidates in priced_by_code.items():
        priced_by_country.setdefault(code.split("-")[0], []).extend(stack_candidates)

    #: Real fully-covered combinations found in practice are small (pairs,
    #: occasionally triples); this bounds the combinatorial search per
    #: location group as a safety limit, not a doctrine choice — a
    #: location group with more than this many candidates still yields
    #: every combination up to this size.
    MAX_STACK_GROUP_SIZE = 4

    def _diagnose_group_stack_none(candidates: list) -> tuple[str, str]:
        """Re-derives WHY price_program_group_stack(candidates) returned
        None, in the SAME order that function itself checks (never a
        second, divergent set of conditions) -- so the persisted
        rejection reason is always genuinely traceable to the real
        blocking condition, never a generic catch-all."""
        if any(_economic_block_for_program(c.program_slug) is not None for c in candidates):
            blocked = [c.program_slug for c in candidates if _economic_block_for_program(c.program_slug) is not None]
            return "AUTHORITY_BLOCKED", (
                f"{'/'.join(sorted(blocked))}: at least one program in this group carries an "
                "accepted authority-exhausted/discretionary-display-only/retired/duplicate "
                "identity block -- no automatic stack may include it."
            )
        codes = [c.jurisdiction_code for c in candidates]
        if not eligible_group_for_combination(codes):
            return "INELIGIBLE_JURISDICTION_GROUP", (
                f"jurisdictions {sorted(set(codes))} are not eligible to combine (same exact "
                "jurisdiction, or one federal + at most one specific province/state, never two "
                "different provinces/states)."
            )
        slugs = [c.program_slug for c in candidates]
        if len(set(slugs)) != len(slugs):
            return "DUPLICATE_PROGRAM_IN_GROUP", f"program {slugs!r} appears more than once in this group."
        unresolved_pairs = []
        distinct_cost_pairs = []
        for _a, _b in itertools.combinations(sorted(slugs), 2):
            _rule = load_named_pair_rule(_a, _b)
            if _rule is not None and _rule["rule_type"] == "same_cost_prohibited_distinct_costs_allowed":
                # A real, registered rule DOES exist here -- this is NOT
                # an authority gap. price_program_group_stack's own
                # load_named_rules_for_group only recognizes "allowed",
                # "mutually_exclusive", "spend_reduction" as publishable;
                # this rule type is handled correctly (as non-blocking,
                # by the same-cost-refusal-by-shared-line_id mechanism)
                # by generate_structural_candidate's check_all_pairs for
                # the ordinary_component_hybrid family, but the OLDER
                # same-jurisdiction group-stack bridge genuinely has no
                # distinct-cost awareness (a pre-existing, documented,
                # intentionally-unchanged limitation -- see
                # CANONICAL_ARTIFACT_PRECEDENCE_CLAUDE.json). Mislabeling
                # this as "no authority" would misrepresent a real,
                # cited rule as an absence of one.
                distinct_cost_pairs.append((_a, _b, _rule["condition_text"]))
                continue
            if _rule is None or _rule["rule_type"] not in ("allowed", "mutually_exclusive", "spend_reduction"):
                unresolved_pairs.append((_a, _b))
        if distinct_cost_pairs and not unresolved_pairs:
            pair_text = "; ".join(f"{a}+{b}" for a, b, _ in distinct_cost_pairs)
            citation = distinct_cost_pairs[0][2]
            return "RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE", (
                f"{pair_text}: a real, registered same_cost_prohibited_distinct_costs_allowed "
                f"rule exists ({citation}), but this same-jurisdiction group-stack mechanism "
                "(unlike the ordinary_component_hybrid generator's own check_all_pairs) has no "
                "distinct-cost awareness and cannot yet price this combination through this "
                "path -- a real, disclosed mechanism gap, never a fabricated authority gap. "
                "This exact program combination may still be reachable via the "
                "ordinary_component_hybrid discovery path if the target's own jurisdiction is "
                "eligible as a routed movable component."
            )
        if unresolved_pairs:
            pair_text = "; ".join(f"{a}+{b}" for a, b in unresolved_pairs)
            return "UNRESOLVED_NO_AUTHORITY", (
                f"{pair_text}: no registered rule of a publishable type exists for this "
                "pairwise combination within the same jurisdiction/authority family -- a "
                "genuine, disclosed authority gap (never guessed), matching the same "
                "UNRESOLVED_NO_AUTHORITY disposition check_all_pairs already applies for the "
                "ordinary_component_hybrid family."
            )
        return "UNRESOLVED_GROUP_STACK", (
            f"{'/'.join(sorted(slugs))}: price_program_group_stack returned no result for a "
            "reason not captured by the specific checks above -- disclosed rather than dropped."
        )

    def _try_cost_pool_aware_same_jurisdiction_stack(
        combo: list,
    ) -> tuple[dict | None, str | None, str | None]:
        """REG-5 cost-pool-aware pricing. Returns (payload, reason_class,
        reason). payload is non-None only on a genuine success.

        For a same-jurisdiction pair carrying a registered
        same_cost_prohibited_distinct_costs_allowed rule (a jurisdiction's
        own broad principal-production credit plus a separate credit
        scoped to one closed list of eligible spend categories, e.g. a
        post-production-only credit) -- a pair the OLDER
        price_program_group_stack bridge can never price (see the
        RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE branch above:
        that bridge has no distinct-cost awareness) -- prices each
        program against its own REAL, DISJOINT cost pool instead of the
        whole budget for both, so the same dollar can never be counted
        under both programs:

          1. identify which of the two programs carries a genuine, real
             CLOSED_POSITIVE_LIST of eligible spend categories (never
             guessed from doctrine alone -- if neither/both programs
             carry one, this mechanism does not apply and (None, None,
             None) is returned, falling through to the existing, honest
             RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE rejection
             just as before this fix);
          2. derive the anchor's REAL account allocation for this
             jurisdiction via derive_account_allocation() -- the exact
             same call every full_relocation/single_country candidate in
             this file already uses, no second allocation mechanism;
          3. partition those REAL AccountAllocation rows into two
             disjoint pools by each row's own real spend_category -- a
             strict partition of the SAME tuple, so a source line_id can
             never appear in both pools (same-cost-refusal by
             construction, the identical principle
             structural_archetype_generator.py already uses for movable
             components);
          4. price each pool independently via price_segment() -- the
             same partial-register pricing kernel movable-component
             routing already reuses for a spend subset, never a new
             pricing path;
          5. only return a priced payload when BOTH pools independently
             clear their own program's real threshold/rate resolution --
             if either pool does not price, a specific, reconstructable
             rejection reason is returned instead of a fabricated
             partial result.

        Bounded to exactly 2 programs, both in the same jurisdiction --
        generalizing to 3+ simultaneous distinct-cost pools is not
        attempted (no registered rule authorizes it and no known control
        needs it)."""
        if len(combo) != 2:
            return None, None, None
        cand_a, cand_b = combo
        if cand_a.jurisdiction_code != cand_b.jurisdiction_code:
            return None, None, None
        rule = load_named_pair_rule(cand_a.program_slug, cand_b.program_slug)
        if rule is None or rule["rule_type"] != "same_cost_prohibited_distinct_costs_allowed":
            return None, None, None

        from app.data.program_spend_rules import (
            QualificationDoctrine, get_program_rules, resolve_program_doctrine,
        )
        split = None
        for closed_slug, remainder_slug in (
            (cand_a.program_slug, cand_b.program_slug),
            (cand_b.program_slug, cand_a.program_slug),
        ):
            if resolve_program_doctrine(closed_slug).doctrine != QualificationDoctrine.CLOSED_POSITIVE_LIST:
                continue
            categories = tuple(sorted(
                cat for cat, r in get_program_rules(closed_slug).items() if r.qualifies is True
            ))
            if categories:
                split = (closed_slug, remainder_slug, categories)
                break
        if split is None:
            # Neither program carries a genuine closed positive list to
            # ground a real split -- never guess one from overlapping
            # open-inclusion doctrine. Falls through to the existing
            # RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE rejection.
            return None, None, None
        closed_slug, remainder_slug, closed_categories = split
        code = cand_a.jurisdiction_code

        spec = StructureSpec(
            structure_id=f"CANON-{code}-cost-pool-{closed_slug}-{remainder_slug}",
            structure_type="single_country" if code == inputs.jurisdiction_code else "full_relocation",
            label=f"{code} distinct-cost-pool stack ({closed_slug} + {remainder_slug})",
            primary_jurisdiction=code, participants=(code,),
            incentive_programs={code: closed_slug},
        )
        allocation = derive_account_allocation(
            lines=inputs.budget_lines, spend_category_by_code=inputs.spend_category_by_code,
            spec=spec, stated_outside_accounts=inputs.accounts_outside_jurisdiction,
        )
        assignments = [asg for asg in allocation.assignments if asg.jurisdiction_code == code]
        pool_closed = [
            asg for asg in assignments
            if (asg.spend_category or inputs.spend_category_by_code.get(asg.account_code)) in closed_categories
        ]
        _closed_ids = {id(asg) for asg in pool_closed}
        pool_remainder = [asg for asg in assignments if id(asg) not in _closed_ids]

        if not pool_closed:
            return None, "COST_POOL_EMPTY", (
                f"{closed_slug}: no real budget line in this production's {code} allocation "
                f"falls into {closed_slug}'s own closed eligible-category list "
                f"{list(closed_categories)} -- no genuine distinct cost pool exists to price "
                f"separately from {remainder_slug}, so this combination is not formed rather "
                "than invented."
            )

        common_kwargs = dict(
            spend_category_by_code=inputs.spend_category_by_code,
            offshore_payroll_accounts=inputs.offshore_payroll_accounts,
            production_type=inputs.production_type,
            gross_budget_usd=inputs.gross_budget_usd,
            amount_facts=inputs.amount_facts,
            evidenced_requirement_facts=(
                inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
            ),
            fx_context=inputs.fx_context,
        )
        seg_closed = price_segment(code, closed_slug, pool_closed, **common_kwargs)
        seg_remainder = price_segment(code, remainder_slug, pool_remainder, **common_kwargs)

        if not seg_closed.executable:
            return None, "COST_POOL_MEMBER_UNPRICEABLE", (
                f"{closed_slug}: its own real {code} cost pool "
                f"(${sum(asg.amount_usd for asg in pool_closed):,.2f} across categories "
                f"{list(closed_categories)}) did not price on its own -- "
                + ("; ".join(seg_closed.blockers) or "no executable rate resolved for this pool alone.")
            )
        if not seg_remainder.executable:
            return None, "COST_POOL_MEMBER_UNPRICEABLE", (
                f"{remainder_slug}: its own real {code} remainder cost pool "
                f"(${sum(asg.amount_usd for asg in pool_remainder):,.2f}, every account NOT in "
                f"{closed_slug}'s closed category list) did not price on its own -- "
                + ("; ".join(seg_remainder.blockers) or "no executable rate resolved for this pool alone.")
            )

        total_incentive = round(seg_closed.incentive_floor_usd + seg_remainder.incentive_floor_usd, 2)
        payload = {
            "closed_slug": closed_slug, "remainder_slug": remainder_slug,
            "closed_categories": list(closed_categories),
            "seg_closed": seg_closed, "seg_remainder": seg_remainder,
            "pool_closed_line_ids": sorted({asg.line_id for asg in pool_closed}),
            "pool_remainder_line_ids": sorted({asg.line_id for asg in pool_remainder}),
            "total_incentive_usd": total_incentive,
            "jurisdiction_code": code,
        }
        return payload, "PRICED", "cost-pool-aware distinct pricing succeeded"

    seen_combos: set[frozenset] = set()
    location_groups: list[list[StackCandidate]] = []
    for country, stack_candidates in priced_by_country.items():
        federal = [c for c in stack_candidates if c.jurisdiction_code == country]
        specific_codes = sorted({
            c.jurisdiction_code for c in stack_candidates if c.jurisdiction_code != country
        })
        if len(federal) >= 2:
            location_groups.append(federal)
        for code in specific_codes:
            specific = [c for c in stack_candidates if c.jurisdiction_code == code]
            location_groups.append(federal + specific)

    stack_results: list = []
    for group in location_groups:
        if len(group) < 2:
            continue
        max_size = min(len(group), MAX_STACK_GROUP_SIZE)
        for size in range(2, max_size + 1):
            for combo in itertools.combinations(group, size):
                combo_key = frozenset(c.program_slug for c in combo)
                if combo_key in seen_combos:
                    continue
                seen_combos.add(combo_key)
                stack_result = price_program_group_stack(list(combo))
                if stack_result is not None:
                    stack_results.append(stack_result)
                    continue

                # REG-5 cost-pool-aware pricing (canonical-1.78.0): tried
                # BEFORE falling back to the generic RULE_REJECTED
                # diagnosis below, but only for a combo this mechanism
                # actually applies to (exactly 2 same-jurisdiction
                # programs under a registered same_cost_prohibited_
                # distinct_costs_allowed rule with a real closed-list
                # split available) -- every other combo shape returns
                # (None, None, None) immediately and falls through
                # unchanged to the pre-existing diagnostic below.
                _cp_payload, _cp_reason_class, _cp_reason = (
                    _try_cost_pool_aware_same_jurisdiction_stack(list(combo))
                )
                if _cp_payload is not None:
                    _cp_structure_id = uuid.uuid4()
                    session.add(ProductionStructure(
                        id=_cp_structure_id, project_id=project.id,
                        name=(
                            f"{_cp_payload['closed_slug']}+{_cp_payload['remainder_slug']} "
                            f"({_cp_payload['jurisdiction_code']} distinct-cost-pool stack)"
                        ),
                        description=(
                            f"Same-jurisdiction distinct-cost-pool stack: {_cp_payload['closed_slug']} "
                            f"priced only against its own real {_cp_payload['closed_categories']} "
                            f"spend; {_cp_payload['remainder_slug']} priced only against the "
                            "remaining real spend. The two pools partition the same real budget "
                            "by disjoint source BudgetLine ids -- no dollar counted twice."
                        ),
                        jurisdiction_allocations=[], claimed_program_ids=sorted(combo_key),
                        is_official_coproduction=False, coproduction_treaty=None,
                    ))
                    session.add(StructureCalculationResult(
                        id=uuid.uuid4(), structure_id=_cp_structure_id, engine_version=ENGINE_VERSION,
                        total_budget_usd=inputs.gross_budget_usd,
                        total_incentive_value_usd=_cp_payload["total_incentive_usd"],
                        true_net_cost_usd=round(
                            inputs.gross_budget_usd - _cp_payload["total_incentive_usd"], 2,
                        ),
                        risk_adjusted_net_cost_usd=round(
                            inputs.gross_budget_usd - _cp_payload["total_incentive_usd"], 2,
                        ),
                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                        structure_type="same_jurisdiction_distinct_cost_pool_stack",
                        calculation_trace_json={
                            "candidate_status": "PRICED",
                            "discovery_classification": "same_jurisdiction_distinct_cost_pool_stack",
                            "structural_family": "same_jurisdiction_distinct_cost_pool_stack",
                            "evidence_level": "CANONICAL_PERSISTED_RUNTIME",
                            "program_slugs": sorted(combo_key),
                            "jurisdiction_codes": sorted({c.jurisdiction_code for c in combo}),
                            "is_baseline": False, "relocation_cost_normalized": False,
                            "is_directly_comparable": False,
                            "cost_pool_closed_program": _cp_payload["closed_slug"],
                            "cost_pool_remainder_program": _cp_payload["remainder_slug"],
                            "cost_pool_closed_categories": _cp_payload["closed_categories"],
                            "cost_pool_closed_line_ids": _cp_payload["pool_closed_line_ids"],
                            "cost_pool_remainder_line_ids": _cp_payload["pool_remainder_line_ids"],
                            "cost_pool_closed_qpe_usd": _cp_payload["seg_closed"].qpe_usd,
                            "cost_pool_remainder_qpe_usd": _cp_payload["seg_remainder"].qpe_usd,
                            "cost_pool_closed_incentive_usd": _cp_payload["seg_closed"].incentive_floor_usd,
                            "cost_pool_remainder_incentive_usd": _cp_payload["seg_remainder"].incentive_floor_usd,
                        },
                        input_fingerprint=fingerprint,
                    ))
                    continue

                if _cp_payload is None:
                    # CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION:
                    # confirmed real defect, found via direct instrumentation
                    # (not assumed) -- price_program_group_stack's own
                    # docstring already promises "the rejection is preserved
                    # by canonical_evaluation.py exactly like every other
                    # None return here," but nothing downstream ever did
                    # that: a None result was silently dropped, with zero
                    # persisted row of any kind. The most common real cause
                    # (confirmed via instrumentation on a real CPTC+OFTTC+
                    # OCASE combo) is a genuinely unresolved pairwise
                    # authority gap (load_named_rules_for_group's
                    # fully_covered=False) -- exactly the same kind of
                    # disclosed, non-fabricated rejection
                    # generate_structural_candidate's own check_all_pairs
                    # already persists for the ordinary_component_hybrid
                    # family (e.g. "cptc+ocase UNRESOLVED_NO_AUTHORITY").
                    # Diagnoses and persists the SAME class of explicit,
                    # reconstructable rejection here -- never silently
                    # dropped, never a fabricated rate.
                    #
                    # REG-5 addendum: if the cost-pool-aware attempt above
                    # WAS applicable but failed on its own real facts
                    # (COST_POOL_EMPTY / COST_POOL_MEMBER_UNPRICEABLE),
                    # that specific, reconstructable reason is used
                    # in place of the generic diagnostic -- never
                    # overwritten by a less precise catch-all reason.
                    if _cp_reason_class is not None:
                        _none_reason_class, _none_reason = _cp_reason_class, _cp_reason
                    else:
                        _none_reason_class, _none_reason = _diagnose_group_stack_none(list(combo))
                    _rej_structure_id = uuid.uuid4()
                    session.add(ProductionStructure(
                        id=_rej_structure_id, project_id=project.id,
                        name=(
                            f"{'/'.join(sorted(combo_key))} "
                            f"({combo[0].jurisdiction_code} same-jurisdiction group, rejected)"
                        ),
                        description=(
                            "Same-jurisdiction multi-program group stack examined and rejected -- "
                            f"{_none_reason}"
                        ),
                        jurisdiction_allocations=[], claimed_program_ids=sorted(combo_key),
                        is_official_coproduction=False, coproduction_treaty=None,
                    ))
                    session.add(StructureCalculationResult(
                        id=uuid.uuid4(), structure_id=_rej_structure_id, engine_version=ENGINE_VERSION,
                        total_budget_usd=inputs.gross_budget_usd,
                        total_incentive_value_usd=None, true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                        structure_type="same_jurisdiction_group_stack",
                        calculation_trace_json={
                            "candidate_status": "RULE_REJECTED",
                            "rejection_reason_class": _none_reason_class,
                            "reason": _none_reason,
                            "discovery_classification": "same_jurisdiction_group_stack",
                            "structural_family": "same_jurisdiction_group_stack",
                            "evidence_level": "CANONICAL_PERSISTED_RUNTIME",
                            "program_slugs": sorted(combo_key),
                            "jurisdiction_codes": sorted({c.jurisdiction_code for c in combo}),
                            "is_baseline": False, "relocation_cost_normalized": False,
                            "is_directly_comparable": False,
                        },
                        input_fingerprint=fingerprint,
                    ))

    # Codex global optimizer audit, P1-TRACE-001 remediation: "compute
    # exact unique qualifying spend from line-level allocation
    # identities... do not use max(per_program_qpe) as exact unique QPE."
    # A real line-id -> dollar-amount map, built once, is the join key
    # every stacked program's own qualifying_line_ids (StackCandidate,
    # populated straight from derive_qualification_register's real
    # line_id per account) resolves against below -- the TRUE union of
    # unique underlying budget dollars, never a lower-bound approximation.
    _line_amount_by_id: dict[str, float] = {
        line.line_id: line.amount_usd for line in inputs.budget_lines if not line.is_memo
    }

    for stack_result in stack_results:
        code = stack_result.jurisdiction_code
        jurisdiction = jurisdiction_by_code.get(code)
        is_baseline = code == inputs.jurisdiction_code
        npc = round(inputs.gross_budget_usd - stack_result.adjusted_incentive_usd, 2)
        feasibility_status, feasibility_reasons = _feasibility_status(
            feasibility_by_code.get(code), requirements,
        )
        warnings = [LIMITATION_NOTE] if is_baseline else [LIMITATION_NOTE, RELOCATION_COMPARABILITY_NOTE]
        # Two-axis authority correction: any member program of this
        # combination priced under a provenance-disclosure state inherits
        # its own gap into the combined structure, same as the single-
        # program branch above — never silently dropped just because it is
        # now part of a stack.
        _combo_provenance_gaps = [
            (slug, coverage_state(slug)) for slug in stack_result.program_slugs
            if coverage_state(slug) in PROVENANCE_DISCLOSURE_STATES
        ]
        for _gap_slug, _gap_state in _combo_provenance_gaps:
            warnings = warnings + [
                f"Authority provenance incomplete for {_gap_slug} ({_gap_state}): "
                + STATE_REASON.get(_gap_state, "")
            ]
        _stack_administrative_allocation_risk = False
        for _member_slug in stack_result.program_slugs:
            _member_disclosure = _competitive_allocation_disclosure(_member_slug)
            if _member_disclosure:
                _stack_administrative_allocation_risk = True
                warnings = warnings + [_member_disclosure]
        # Same territorial-fact disclosure every underlying single-
        # program candidate this combination is built from already
        # carries (see the STATUS_PRICED branch above) — the combined
        # QPE inherits the same unconfirmed assumption, so the combined
        # structure must disclose it too, not silently drop it.
        territorial_state_unknown = (
            inputs.accounts_outside_jurisdiction_state == FACT_STATE_UNKNOWN
            or inputs.offshore_payroll_accounts_state == FACT_STATE_UNKNOWN
        )
        if territorial_state_unknown:
            warnings = warnings + [
                "UNKNOWN, not KNOWN EMPTY: no project fact has ever stated which "
                "accounts (if any) are incurred outside the base jurisdiction or "
                "routed through offshore payroll. This QPE assumes none are — the "
                "only input a set-membership check can be given without inventing "
                "evidence — but that assumption is unconfirmed, not verified."
            ]
        warnings = warnings + stack_result.disclosed_limitations
        # CBA-002 continuation, Section 3 — the combo's own qualification
        # state is the WORST (least admitted) of its members', never
        # dropped/defaulted to None just because it's a combined structure.
        #
        # OH-002 fix: looked up by PROGRAM IDENTITY alone
        # (_qual_state_by_program), not by (combo's own jurisdiction_code,
        # slug) — a federal member (e.g. ca_federal_cptc, examined under
        # "CA") inside a provincial stack (combo jurisdiction_code
        # "CA-ON") was previously invisible to this lookup because it was
        # recorded under a different code than the combo's own, silently
        # dropping its real qualification state (which could be
        # HARD_FAIL) out of the worst-state computation entirely.
        _combo_member_states = [
            _qual_state_by_program.get(slug) for slug in stack_result.program_slugs
        ]
        _combo_qual_state = min(
            (s for s in _combo_member_states if s is not None),
            key=lambda s: _QUAL_STATE_SEVERITY.get(s, 2),
            default=None,
        )
        # Codex final four-row remediation (P0-SEL-ALT-001): the FULL
        # per-participant aggregate, retaining every member's own
        # missing/curable/failed requirements and reasoning — never
        # collapsed to _combo_qual_state alone (which stays the admission/
        # ranking severity signal, unchanged).
        _combo_participant_qualifications = _participant_qualification_aggregate(
            stack_result.program_slugs, _qual_detail_by_program,
        )
        program_label = " + ".join(stack_result.program_slugs)
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=f"{code} — {program_label} (combined)",
            description=(
                f"Multi-program combination within {code}: "
                + " + ".join(_program_display_name(s) for s in stack_result.program_slugs)
                + f", stacked per {stack_result.rule_type} rule."
            ),
            jurisdiction_allocations=(
                [{"jurisdiction_id": str(jurisdiction.id), "shoot_pct": 100, "budget_pct": 100}]
                if jurisdiction else []
            ),
            claimed_program_ids=list(stack_result.program_slugs),
        )
        session.add(structure)
        await session.flush()
        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), code, tuple(stack_result.program_slugs),
        )
        # CLUSTER 8: a mutually exclusive combination is not a valid priced
        # structure, so it carries NO economics at all -- not an incentive,
        # not an NPC. Leaving those populated made it look priced to the
        # summarizer and it kept appearing in `ranked`.
        #
        # CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT, Phase B:
        # the prior `stack_result.rule_type == "mutually_exclusive"` check
        # only caught this when the group's rule_type COLLAPSED to exactly
        # "mutually_exclusive" -- a 3+-program group mixing rule types
        # (e.g. ca_federal_cptc+on_ofttc+on_opstc: spend_reduction +
        # mutually_exclusive + mutually_exclusive) reports rule_type=
        # "mixed" and was wrongly served PRICED despite containing a real
        # hard incompatibility (on_ofttc+on_opstc). contains_blocking_
        # incompatibility is computed from EVERY individual pairwise
        # sub-rule in the group, independent of group size or how many
        # other pairs are compatible -- see canonical_stack_bridge.py's
        # _build_group_result.
        _combination_is_invalid = stack_result.contains_blocking_incompatibility
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=(
                None if _combination_is_invalid else stack_result.adjusted_incentive_usd
            ),
            true_net_cost_usd=None if _combination_is_invalid else npc,
            risk_adjusted_net_cost_usd=None if _combination_is_invalid else npc,
            has_unverified_inputs=territorial_state_unknown or bool(stack_result.disclosed_limitations),
            warnings=warnings,
            structure_type="multi_program",
            calculation_trace_json={
                # CLUSTER 8. A MUTUALLY EXCLUSIVE combination is not a valid
                # priced structure. The stacking engine already zeroes the
                # suppressed member, so the arithmetic was safe, but the
                # STRUCTURE was still emitted as PRICED -- presenting a
                # combination the programs' own rules forbid. It is retained
                # as an explicitly non-priceable incompatibility diagnostic
                # (the architecture's existing terminal-state pattern) rather
                # than deleted, so the producer can see the pair was
                # considered and why it cannot be combined.
                # CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT,
                # Phase B: this is a SEPARATE computation from
                # _combination_is_invalid above and was missed in the first
                # pass of this fix -- it independently re-implemented the
                # exact same stale `rule_type == "mutually_exclusive"` check,
                # so a 3+-program group with a "mixed" collapsed rule_type
                # was still reported candidate_status=PRICED (with
                # total_incentive_value_usd correctly None from the OTHER,
                # already-fixed check) -- a real, self-contradictory served
                # state (PRICED with no incentive) caught only by running
                # the real four-production batch, not by the unit tests
                # alone. Must use the SAME _combination_is_invalid this
                # whole block already computes.
                "candidate_status": (
                    STATUS_RULE_REJECTED if _combination_is_invalid else STATUS_PRICED
                ),
                # Section 5 -- same generic structured field as the other
                # two STATUS_PRICED-producing paths.
                "administrative_allocation_risk": _stack_administrative_allocation_risk,
                "discovery_classification": "multi_program_stack",
                "structure_type": "multi_program",
                "primary_jurisdiction": code,
                "program_slugs": stack_result.program_slugs,
                "is_baseline": is_baseline,
                "relocation_cost_normalized": is_baseline,
                # Existing Optimizer/Stacker Reconnection, Task 11 — a
                # combined structure is directly comparable under EXACTLY
                # the same rule a single-program candidate already uses:
                # only the production's OWN home jurisdiction needs no
                # relocation-cost normalization (travel, in-kind
                # replacement) by construction. A combined structure at
                # the home jurisdiction (multiple compatible programs
                # available at home) therefore competes in the real
                # numeric ranking; a combined RELOCATION structure carries
                # the identical unmodeled-cost caveat any single-program
                # relocation candidate already carries, so it stays
                # priced-but-review exactly like one. No new comparability
                # concept invented — this is the same is_baseline test.
                "is_directly_comparable": is_baseline,
                # Codex final wiring remediation (P0-SEL-ALT-001): a
                # non-baseline stack's non-comparability is a STRUCTURAL
                # engine-capability gap (relocation-cost normalization is
                # never computed for multi-program stacks at all — see
                # the comment above), never a producer-suppliable
                # evidence gap. The sentinel below is deliberately NOT one
                # of _RELOCATION_DIMENSIONS, so canonical_production_
                # view.py's conditional-pool admission gate correctly
                # treats it as an unclassified/non-curable cause and
                # excludes it — a stack can never wrongly present as a
                # "curable" leading conditional alternative.
                "relocation_missing_dimensions": (
                    [] if is_baseline else [_STACK_NORMALIZATION_NOT_COMPUTED]
                ),
                "relocation_completeness_jurisdiction": code,
                "stacking_rule_type": stack_result.rule_type,
                "blocking_pairs": stack_result.blocking_pairs,
                # A rejected combination must explain itself -- never an
                # unexplained drop into the unpriceable bucket. Phase B:
                # names the EXACT failing pair(s), not just the whole
                # group's program list -- a 3+-program group may have
                # several compatible pairs and only one (or a few)
                # genuinely incompatible pair forcing the rejection.
                "reason": (
                    f"{code}: {' + '.join(stack_result.program_slugs)} cannot be "
                    "combined as a single structure because "
                    + "; ".join(
                        f"{bp['program_a_id']} + {bp['program_b_id']} are MUTUALLY "
                        "EXCLUSIVE under their own stacking rule"
                        + (f" ({bp['condition_text']})" if bp.get("condition_text") else "")
                        for bp in stack_result.blocking_pairs
                    )
                    + ". The combination is disclosed for completeness but cannot be "
                      "claimed together, so it carries no incentive or NPC."
                ) if _combination_is_invalid else None,
                "stacking_condition_text": stack_result.condition_text,
                "raw_incentive_usd": stack_result.raw_incentive_usd,
                "selected_incentive_usd": (
                    None if _combination_is_invalid else stack_result.adjusted_incentive_usd
                ),
                "npc_verified_usd": None if _combination_is_invalid else npc,
                "npc_conservative_usd": None if _combination_is_invalid else npc,
                "gross_budget_usd": inputs.gross_budget_usd,
                # CLUSTER 8: a priced combined structure must carry reconciled
                # per-program segments and a real total QPE. Previously these
                # served segments=[] and total_qualifying_spend_usd=0 next to a
                # multi-million incentive, which is not a trace anyone can audit.
                "segments": [
                    {
                        "jurisdiction_code": code,
                        "program_slug": slug,
                        "program_display_name": _program_display_name(slug),
                        "claims_incentive": True,
                        "executable": True,
                        "qpe_usd": stack_result.per_program_qpe_usd.get(slug, 0.0),
                        "incentive_floor_usd": stack_result.per_program_adjusted_usd.get(slug, 0.0),
                        "incentive_ceiling_usd": stack_result.per_program_adjusted_usd.get(slug, 0.0),
                    }
                    for slug in stack_result.program_slugs
                ],
                # Codex global optimizer audit, P1-TRACE-001 (rejected on
                # first pass -- "max(per_program_qpe) is a lower bound,
                # not exact unique allocated spend" -- remediated here):
                # "Separate unique allocated production spend from
                # reusable per-program claim bases... compute exact
                # unique qualifying spend from line-level allocation
                # identities." total_claim_bases_usd remains the sum of
                # each stacked program's own reusable, possibly-
                # overlapping claim base (never presented as unique
                # spend). total_qualifying_spend_usd is now the TRUE
                # exact union: every stacked program's own real
                # BudgetLine.line_id set (StackCandidate.qualifying_
                # line_ids, populated from derive_qualification_
                # register's own per-line QUALIFIES state -- never
                # account_code, which a real budget may legitimately
                # reuse across distinct lines) is unioned, then summed
                # from the real per-line dollar amounts -- overlapping
                # lines are counted exactly once, disjoint lines are
                # counted in full, never approximated by sum() or max().
                "total_claim_bases_usd": sum(
                    stack_result.per_program_qpe_usd.get(slug, 0.0)
                    for slug in stack_result.program_slugs
                ),
                "total_qualifying_spend_usd": round(sum(
                    _line_amount_by_id.get(lid, 0.0)
                    for lid in frozenset().union(*(
                        c.qualifying_line_ids
                        # priced_by_country, not priced_by_code: a stacked
                        # group may combine a federal-level candidate
                        # (priced_by_code["CA"]) with a specific province/
                        # state candidate (priced_by_code["CA-ON"]) --
                        # priced_by_country[country] already covers both,
                        # matched here by program_slug, the real
                        # cross-code identity every stacking group is
                        # itself built and deduplicated on.
                        for c in priced_by_country.get(code.split("-")[0], [])
                        if c.program_slug in stack_result.program_slugs
                    ))
                ), 2),
                "stacking_reduction_usd": stack_result.stacking_reduction_usd,
                "per_program_adjusted_usd": stack_result.per_program_adjusted_usd,
                "stacking_adjustments": stack_result.adjustments,
                "legal_review_required": stack_result.legal_review_required,
                "stacking_violations": stack_result.violations,
                "stacking_conditionals": stack_result.conditionals,
                "disclosed_limitations": stack_result.disclosed_limitations,
                "feasibility_status": feasibility_status,
                "feasibility_reasons": feasibility_reasons,
                "conditional_programs": _conditional_program_dicts,
                "conditional_compatibility": _conditional_compatibility_dict,
                # CBA-002 continuation — a combined structure is never
                # Recommended-eligible on its own if any member individually
                # carries a real, unresolved qualification gap. `state` is
                # the admission/ranking severity signal
                # (_admits_recommended/canonical_production_view.py read
                # exactly and only this key for that decision).
                # Codex final four-row remediation (P0-SEL-ALT-001):
                # participant_qualifications ALSO now carries every
                # member's own full detail (was: entirely discarded) — see
                # _participant_qualification_aggregate's own docstring.
                "role_qualification": (
                    {"state": _combo_qual_state} if _combo_qual_state is not None else None
                ),
                "participant_qualifications": _combo_participant_qualifications,
            },
            input_fingerprint=fingerprint,
        ))

    # Existing Optimizer/Stacker Reconnection, Task A — component/split.
    # Reuses production_allocation.StructureSpec's existing
    # "component_relocation" type + price_allocated_structure unchanged;
    # the only new code is candidate SELECTION (which movable component,
    # which target jurisdiction). No spend is invented: only components
    # already present in the project's own real budget with real dollar
    # amounts (MOVABLE_COMPONENTS — post/vfx/music) are ever routed, and
    # every other account keeps its existing derive_account_allocation
    # placement (principal photography/travel at the shoot location,
    # overhead/administration at the production's own domicile) — see
    # _price_component_relocation_candidate's own docstring.
    home_code = inputs.jurisdiction_code
    home_candidates = priced_by_code.get(home_code, [])
    home_best = max(home_candidates, key=lambda c: c.selected_incentive_usd, default=None)
    home_program_slug = home_best.program_slug if home_best else None

    component_spend: dict[str, float] = {}
    for line in inputs.budget_lines:
        if line.is_memo:
            continue
        # Codex BPI-002: line's own category wins; dict is fallback only.
        cat = line.spend_category or inputs.spend_category_by_code.get(line.account_code)
        comp = component_for(cat)
        if comp in MOVABLE_COMPONENTS:
            component_spend[comp] = round(component_spend.get(comp, 0.0) + line.amount_usd, 2)

    # Codex forensic finding C -- the engine must enumerate the COMPLETE
    # eligible component-opportunity ledger before any ranking/presentation
    # pruning happens, not truncate the candidate universe before it is even
    # constructed. The prior MAX_COMPONENT_TARGETS=6 pre-filter (its own
    # comment already called it "a practical search-space bound, not a
    # doctrine choice") meant 57 of 63 real, independently-discovered,
    # independently-priceable target jurisdictions for a typical production
    # never got a persisted component-relocation candidate at all -- not
    # pruned from a ranked list, never built. Every target considered here
    # is a genuinely discovered, independently-priceable candidate (never
    # invented), and a target that does not actually clear the routed
    # component's threshold still fails closed below (`is_fully_priced`)
    # and is not persisted -- so removing the pre-filter enumerates the real
    # universe, it does not relax what counts as priceable.
    if component_spend:
        target_best_by_code: dict[str, StackCandidate] = {}
        for code, cands in priced_by_code.items():
            if code == home_code:
                continue
            target_best_by_code[code] = max(cands, key=lambda c: c.selected_incentive_usd)
        top_targets = sorted(
            target_best_by_code.values(), key=lambda c: c.selected_incentive_usd, reverse=True,
        )

        for component, spend_amount in sorted(component_spend.items()):
            if spend_amount <= 0:
                continue
            for target in top_targets:
                spec, allocation, pricing = _price_component_relocation_candidate(
                    inputs, home_code, home_program_slug,
                    target.jurisdiction_code, target.program_slug, component,
                )
                if not pricing.is_fully_priced:
                    # Optimizer FINAL closeout, P1-REJ-001 (Codex, full
                    # optimizer audit): this branch used to `continue`
                    # here -- genuinely unresolvable (e.g. the routed
                    # component's allocated QPE doesn't clear the target
                    # program's own minimum-spend threshold), never
                    # persisted as a misleading candidate. That reasoning
                    # for NEVER PRICING it was and remains correct — but
                    # dropping the ROW ENTIRELY meant 889 real,
                    # meaningfully-evaluated component attempts (each
                    # with an explicit, real blocker from the SAME
                    # pricing kernel every priced candidate uses) could
                    # not be reconstructed from persisted/served runtime
                    # state without rerunning generation — an
                    # observability/auditability gap, not an economics
                    # gap. Fixed by persisting the SAME kind of disclosed,
                    # never-priced reject row the full_relocation branch
                    # already persists a few hundred lines above
                    # (candidate_status/rejection_reason_class/reason,
                    # total_incentive_value_usd=None,
                    # true_net_cost_usd=None) — never converted into an
                    # economic candidate, never surfaced as recommended
                    # (is_fully_priced stays False, so it can never enter
                    # the `comparable`/ranked pool downstream).
                    _rej_status, _rej_class = _classify_component_rejection(pricing.blockers)
                    _rej_structure = ProductionStructure(
                        id=uuid.uuid4(),
                        project_id=project.id,
                        name=(
                            f"{home_code} anchor — {component} routed to "
                            f"{target.jurisdiction_code} (component/split, rejected)"
                        ),
                        description=(
                            f"Anchor production stays in {home_code}; {component} work "
                            f"(${spend_amount:,.0f} of real project budget) considered for "
                            f"relocation to {target.jurisdiction_code} to claim "
                            f"{_program_display_name(target.program_slug)}, but does not "
                            "clear pricing."
                        ),
                        jurisdiction_allocations=[],
                        claimed_program_ids=[s for s in (home_program_slug, target.program_slug) if s],
                    )
                    session.add(_rej_structure)
                    await session.flush()
                    session.add(StructureCalculationResult(
                        id=uuid.uuid4(), structure_id=_rej_structure.id, engine_version=ENGINE_VERSION,
                        total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                        true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                        structure_type="component_relocation",
                        calculation_trace_json={
                            "candidate_status": _rej_status,
                            "rejection_reason_class": _rej_class,
                            "discovery_classification": "component_relocation",
                            "structure_type": "component_relocation",
                            "primary_jurisdiction": home_code,
                            "program_slugs": [s for s in (home_program_slug, target.program_slug) if s],
                            "program_slug": target.program_slug,
                            "reason": "; ".join(pricing.blockers) or "Not fully priced.",
                            "is_baseline": False,
                            "relocation_cost_normalized": False,
                            "is_directly_comparable": False,
                            "anchor_jurisdiction": home_code,
                            "anchor_program": home_program_slug,
                            "component_allocations": [{
                                "component": component,
                                "jurisdiction_code": target.jurisdiction_code,
                                "jurisdiction_display_name": (
                                    jurisdiction_by_code[target.jurisdiction_code].name
                                    if target.jurisdiction_code in jurisdiction_by_code
                                    else _canonical_jurisdiction_name(target.jurisdiction_code)
                                ),
                                "program_slug": target.program_slug,
                                "allocated_usd": spend_amount,
                            }],
                        },
                        input_fingerprint=fingerprint,
                    ))
                    continue

                component_jur = jurisdiction_by_code.get(home_code)
                target_jur_row = jurisdiction_by_code.get(target.jurisdiction_code)
                npc = pricing.npc_with_adjustments_usd
                feasibility_status, feasibility_reasons = _feasibility_status(
                    feasibility_by_code.get(home_code), requirements,
                )
                target_component_seg = next(
                    (s for s in pricing.segments if s.jurisdiction_code == target.jurisdiction_code), None,
                )
                structure = ProductionStructure(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    name=(
                        f"{home_code} anchor — {component} routed to {target.jurisdiction_code} "
                        f"(component/split)"
                    ),
                    description=(
                        f"Anchor production stays in {home_code}; {component} work "
                        f"(${spend_amount:,.0f} of real project budget) relocated to "
                        f"{target.jurisdiction_code} to claim {_program_display_name(target.program_slug)}."
                    ),
                    jurisdiction_allocations=[
                        {
                            "jurisdiction_id": str(component_jur.id), "shoot_pct": 100,
                            "budget_pct": round(100 * (1 - spend_amount / inputs.gross_budget_usd), 2),
                        }
                    ] + (
                        [{
                            "jurisdiction_id": str(target_jur_row.id), "shoot_pct": 0,
                            "budget_pct": round(100 * spend_amount / inputs.gross_budget_usd, 2),
                        }] if target_jur_row else []
                    ),
                    claimed_program_ids=[s for s in (home_program_slug, target.program_slug) if s],
                )
                session.add(structure)
                await session.flush()
                _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
                    str(structure.id), home_code,
                    tuple(s for s in (home_program_slug, target.program_slug) if s),
                )
                _component_territorial_unknown = (
                    inputs.accounts_outside_jurisdiction_state == FACT_STATE_UNKNOWN
                    or inputs.offshore_payroll_accounts_state == FACT_STATE_UNKNOWN
                )
                _component_warnings = [
                    LIMITATION_NOTE,
                    "Component/split candidate: relocating real project spend "
                    "between jurisdictions carries incremental coordination/travel "
                    "costs not yet modeled generically — this NPC is not directly "
                    "comparable to the base jurisdiction's own NPC.",
                ]
                if _component_territorial_unknown:
                    _component_warnings.append(
                        "UNKNOWN, not KNOWN EMPTY: no project fact has ever stated which "
                        "accounts (if any) are incurred outside the base jurisdiction or "
                        "routed through offshore payroll. This QPE assumes none are — the "
                        "only input a set-membership check can be given without inventing "
                        "evidence — but that assumption is unconfirmed, not verified."
                    )
                # Canonical optimizer/Globe wiring remediation (2026-09-04),
                # P0-4 (second half): the audit found component candidates
                # lose the administrative/discretionary-allocation
                # disclosure entirely -- _competitive_allocation_disclosure
                # was already called for full_relocation and stacked/
                # member programs (see the other two call sites in this
                # file) but never for a component route's own claimed
                # programs. Same generic function, same generic call
                # pattern, no jurisdiction-specific check -- either the
                # home or the routed target program can independently
                # carry a real discretionary/preapproval/competitive-
                # allocation doctrine fact.
                _component_administrative_allocation_risk = False
                for _component_program_slug in (home_program_slug, target.program_slug):
                    if not _component_program_slug:
                        continue
                    _component_disclosure = _competitive_allocation_disclosure(_component_program_slug)
                    if _component_disclosure:
                        _component_administrative_allocation_risk = True
                        if _component_disclosure not in _component_warnings:
                            _component_warnings.append(_component_disclosure)
                # Codex final wiring remediation (P0-SEL-ALT-001): a
                # component/split structure has TWO participant programs
                # (the home anchor and the routed target) — its aggregate
                # qualification must be the WORST of both, the SAME
                # worst-of-members pattern the multi-program stack branch
                # already uses (_combo_qual_state above), never left
                # entirely absent. This is the exact gap Codex's audit
                # named: "FVD gr_cash_rebate + ro_film_office_cash_rebate
                # has no aggregate qualification/participant blocker."
                _component_qual_state = min(
                    (s for s in (
                        _qual_state_by_program.get(home_program_slug),
                        _qual_state_by_program.get(target.program_slug),
                    ) if s is not None),
                    key=lambda s: _QUAL_STATE_SEVERITY.get(s, 2),
                    default=None,
                )
                # Codex final four-row remediation (P0-SEL-ALT-001): the
                # FULL per-participant aggregate for BOTH the anchor
                # (home_program_slug -- e.g. FVD's gr_cash_rebate, whose
                # own gr_aggregate cultural-test missing_fact was
                # previously discarded entirely) and the routed target,
                # never collapsed to _component_qual_state alone.
                _component_participant_qualifications = _participant_qualification_aggregate(
                    tuple(s for s in (home_program_slug, target.program_slug) if s),
                    _qual_detail_by_program,
                )
                # The COMPONENT itself relocates to target.jurisdiction_code
                # (never home_code, the anchor that never moves) — relocation
                # completeness is evaluated against the jurisdiction the
                # money actually moves to, per-dimension, never the anchor.
                _reloc_complete, _reloc_missing = _relocation_completeness(
                    False, target.jurisdiction_code, inputs,
                )
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd,
                    total_incentive_value_usd=pricing.selected_incentive_usd,
                    # Canonical optimizer/Globe wiring remediation
                    # (2026-09-04), P0-2: this used to persist the SAME
                    # adjusted value (`npc`, i.e. pricing.
                    # npc_with_adjustments_usd) into BOTH columns --
                    # true_net_cost_usd (which every OTHER structure type
                    # correctly populates from the verified/base figure,
                    # see the single/full_relocation path a few hundred
                    # lines above) collapsed into the adjusted figure,
                    # mislabeling adjusted-as-verified at the exact
                    # served-field boundary canonical_production_view.py
                    # reads from (npc_verified_usd <- true_net_cost_usd).
                    # pricing.npc_verified_usd was ALREADY correctly
                    # computed by price_allocated_structure (the SAME
                    # kernel single/full_relocation uses) and was already
                    # correctly written into this row's own trace_json
                    # below ("npc_verified_usd": pricing.npc_verified_usd)
                    # -- only the top-level DB column read the wrong
                    # value. Same real number, now read from the same
                    # real field, matching the full_relocation
                    # convention exactly.
                    true_net_cost_usd=pricing.npc_verified_usd,
                    risk_adjusted_net_cost_usd=npc,
                    has_unverified_inputs=True,
                    warnings=_component_warnings,
                    structure_type="component_relocation",
                    calculation_trace_json={
                        "candidate_status": STATUS_PRICED,
                        # Section 5 -- same generic structured field as
                        # the single/full_relocation path above.
                        "administrative_allocation_risk": _component_administrative_allocation_risk,
                        "discovery_classification": "component_relocation",
                        "structure_type": "component_relocation",
                        "primary_jurisdiction": home_code,
                        "program_slugs": [s for s in (home_program_slug, target.program_slug) if s],
                        "is_baseline": False,
                        "relocation_cost_normalized": _reloc_complete,
                        "is_directly_comparable": _reloc_complete,
                        "relocation_missing_dimensions": list(_reloc_missing),
                        "relocation_completeness_jurisdiction": target.jurisdiction_code,
                        "role_qualification": (
                            {"state": _component_qual_state} if _component_qual_state is not None else None
                        ),
                        "participant_qualifications": _component_participant_qualifications,
                        "anchor_jurisdiction": home_code,
                        "anchor_program": home_program_slug,
                        "component_allocations": [{
                            "component": component,
                            "jurisdiction_code": target.jurisdiction_code,
                            # A seeded Jurisdiction row wins; otherwise resolve
                            # the name from canonical registries so a modeled-
                            # but-unseeded code (AE-AD, AE-DXB, AU-SA) never
                            # reaches the producer raw.
                            "jurisdiction_display_name": (
                                target_jur_row.name if target_jur_row
                                else _canonical_jurisdiction_name(target.jurisdiction_code)
                            ),
                            "program_slug": target.program_slug,
                            "allocated_usd": target_component_seg.allocated_usd if target_component_seg else spend_amount,
                            "incentive_floor_usd": target_component_seg.incentive_floor_usd if target_component_seg else None,
                            "incentive_ceiling_usd": target_component_seg.incentive_ceiling_usd if target_component_seg else None,
                        }],
                        "selected_incentive_usd": pricing.selected_incentive_usd,
                        "npc_verified_usd": pricing.npc_verified_usd,
                        "npc_conservative_usd": pricing.npc_verified_usd,
                        "gross_budget_usd": inputs.gross_budget_usd,
                        "segments": _segment_dicts(pricing),
                        "feasibility_status": feasibility_status,
                        "feasibility_reasons": feasibility_reasons,
                        "conditional_programs": _conditional_program_dicts,
                        "conditional_compatibility": _conditional_compatibility_dict,
                        # Canonical optimizer/Globe wiring remediation
                        # (2026-09-04), P0-2 (second half): the audit's
                        # own words -- "the trace contains the correct
                        # pre-normalization NPC but omits the
                        # normalization fields". This component trace
                        # never carried an "adjustments" key at all, so
                        # canonical_production_view.py's
                        # `(trace.get("adjustments") or {}).get(...)`
                        # reads silently returned null/0.0 for every
                        # served delta -- reconstructing npc_with_
                        # adjustments_usd from npc_verified_usd + these
                        # deltas was impossible. Same real fields, same
                        # shape, as the single/full_relocation path
                        # above -- reading straight off the SAME
                        # `pricing` kernel object (price_allocated_
                        # structure), never new economics.
                        "adjustments": {
                            "travel_incremental_delta_usd": pricing.travel_incremental_delta_usd,
                            "fx_delta_usd": pricing.fx_delta_usd,
                            "inkind_replacement_delta_usd": pricing.inkind_replacement_delta_usd,
                            "local_cost_delta_usd": pricing.local_cost_delta_usd,
                            "financing_cost_usd": pricing.financing_cost_usd,
                            "implementation_cost_usd": pricing.implementation_cost_usd,
                            "total_adjustments_usd": round(
                                (pricing.npc_with_adjustments_usd or 0.0) - (pricing.npc_verified_usd or 0.0), 2
                            ),
                        },
                    },
                    input_fingerprint=fingerprint,
                ))

    # CLAUDE_STRUCTURAL_GENERATOR_CANONICAL_INTEGRATION_CORRECTION, Task 1
    # -- the canonical integration of app.calculators.structural_
    # archetype_generator into evaluate_project(). Prior workstream
    # (CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION) built the generator
    # and proved it correct in direct-generator tests only; it was never
    # imported or invoked here (GENERATOR_EXISTS_BUT_CANONICAL_
    # INTEGRATION_MISSING). This block is the fix: it builds every
    # structurally meaningful >=2-movable-component simultaneous routing
    # from the SAME component_spend/top_targets the single-component loop
    # immediately above already computed (never a second discovery
    # mechanism), hands each to generate_structural_candidate for
    # legality/pricing (never a second pricing implementation), and
    # persists every generated/rejected candidate as a real
    # ProductionStructure/StructureCalculationResult row under THIS
    # evaluation's fingerprint/ENGINE_VERSION -- read back automatically
    # by _summarize_evaluation's existing generic fingerprint-scoped
    # query, so no separate served-view wiring is required. Every
    # candidate here is, by construction (no treaty_engine call anywhere
    # in this block), structural_family="ordinary_component_hybrid"
    # (Locked Structural Policy point 1) -- this is exactly the family
    # HO-001/HO-002 (Task 3) and Ireland+UK disjoint-component structures
    # must be labeled unless a real treaty evaluation qualifies them.
    from app.calculators.structural_archetype_generator import (
        StructuralComponent as _HybridComponent,
        generate_structural_candidate as _generate_hybrid_candidate,
        _same_authority_scope as _hy_same_authority_scope,
    )

    # Task 1.4/Task 3: HO-001/HO-002 (and the general co-production-free
    # "relocate principal AND route other components elsewhere" archetype)
    # require a PRINCIPAL-photography anchor other than the production's
    # own current base to be tried as well (Georgia/New Mexico for Lips
    # Like Sugar, whose real declared base is California). The anchor
    # candidate pool is therefore, in principle, not just home_code: it
    # could be home_code UNION every jurisdiction with its own
    # independently-priced full-relocation candidate (the SAME
    # `priced_by_code` ledger the single-country/full_relocation
    # candidates above already computed and priced -- never a second
    # discovery mechanism).
    #
    # CLAUDE_STRUCTURAL_GENERATOR_CANONICAL_INTEGRATION_CORRECTION,
    # measured this pass: trying ALL discovered jurisdictions (76 for
    # Lips Like Sugar) as alternate anchors DOES correctly surface
    # us_ga_film_credit/us_nm_film_credit-anchored ordinary_component_
    # hybrid structures (confirmed live), but multiplies this loop's own
    # cost by that same factor (~1,850 generated/persisted candidates for
    # one project) and was measured to make an 8-file regression suite
    # that normally completes in ~2 minutes fail to complete within 5+
    # minutes -- an unacceptable, unresolved performance regression this
    # pass did not have the remaining budget to fix properly (the correct
    # fix is a per-COMPONENT-aware target ranking, so far fewer,
    # genuinely-meaningful candidates are generated per anchor, rather
    # than either a single fixed anchor or every discovered jurisdiction).
    # Scoped BACK to home_code only for this pass so the canonical
    # integration ships without a performance regression; this is a real,
    # disclosed, honest limitation -- the exact HO-001/HO-002 combination
    # (which needs the GA/NM alternate-anchor case) is therefore NOT YET
    # reached through evaluate_project() as of this commit. See
    # CLAUDE_STRUCTURAL_STACKING_RUNTIME_CLOSEOUT.md for the full
    # accounting. Do not re-widen this to "all anchors" without first
    # implementing per-component target ranking and re-measuring.
    _hy_anchor_candidates: dict[str, str] = {}
    if home_program_slug:
        _hy_anchor_candidates[home_code] = home_program_slug
    for _code, _cands in priced_by_code.items():
        if _code == home_code or not _cands:
            continue
        _hy_anchor_candidates[_code] = max(_cands, key=lambda c: c.selected_incentive_usd).program_slug

    # CLAUDE_PROMPT_2_CANONICAL_OPTIMIZER_AND_GROSSUP_OPPORTUNITY_CLOSEOUT,
    # Task A1/C5: per-COMPONENT-aware target ranking, computed ONCE (not
    # once per anchor) -- the fix identified but not implemented in the
    # prior workstream. Each movable component's own candidate targets are
    # ranked by THAT component's own real, independently-priced incentive
    # (reusing the EXISTING _price_component_relocation_candidate kernel
    # the single-component loop above already uses -- never a second
    # pricing implementation), not by each jurisdiction's unrelated best
    # OVERALL incentive. This is what lets NZ's post-specific grant and
    # Ontario's OCASE VFX credit actually surface as top post/vfx targets
    # even though neither is a top-ranked destination OVERALL -- the exact
    # gap that kept HO-001/HO-002 unreachable in the prior pass. Computing
    # this once, up front, and reusing it for every anchor (component
    # economics do not depend on which anchor is tried) avoids the
    # combinatorial anchor x component x jurisdiction re-pricing that
    # would otherwise multiply cost by the anchor count.
    # CLAUDE_PROMPT_2_GENERIC_DISCOVERY_CORRECTION_AND_HANDOFF: the prior
    # pass's top-3-per-component ranking, patched with a small, explicitly
    # named `_NAMED_ACCEPTANCE_CONTROL_TARGETS` list to force HO-001/HO-002
    # visibility, has been REMOVED. Ranking must never decide whether a
    # legally feasible opportunity exists -- so every jurisdiction with a
    # real, independently-priced incentive for a given component is kept
    # here (one entry per JURISDICTION -- its own best-paying program for
    # that component; two DIFFERENT jurisdictions of the same country,
    # e.g. US-GA vs US-NM or CA-ON vs CA-MB, are never collapsed, since
    # they are genuinely different, non-interchangeable destinations).
    _hy_component_all_targets: dict[str, list] = {}
    for _comp in sorted(component_spend):
        if component_spend[_comp] <= 0:
            continue
        _comp_scores: list[tuple[float, str, str]] = []
        for _target_code, _target_cands in priced_by_code.items():
            for _tc in _target_cands:
                try:
                    _, _, _comp_pricing = _price_component_relocation_candidate(
                        inputs, home_code, home_program_slug, _target_code, _tc.program_slug, _comp,
                    )
                except Exception:
                    continue
                if not _comp_pricing.is_fully_priced:
                    continue
                # CLAUDE_PROMPT_2_GENERIC_DISCOVERY_CORRECTION_AND_HANDOFF
                # bugfix: `_comp_pricing.selected_incentive_usd` is the
                # TOTAL for the WHOLE re-priced structure (home anchor +
                # this one routed component combined) -- using it as a
                # per-component "value" for branch-and-bound summation
                # double/triple-counts the anchor's own multi-million-
                # dollar baseline once per component in the subset,
                # producing an upper bound so inflated it almost never
                # converges against a real (correctly non-duplicated)
                # total from generate_structural_candidate, making the
                # search effectively exhaustive over the full N-way grid.
                # The correct per-component value is the TARGET
                # JURISDICTION'S OWN segment contribution alone.
                _target_seg = next(
                    (s for s in _comp_pricing.segments if s.jurisdiction_code == _target_code), None,
                )
                _marginal_val = _target_seg.incentive_floor_usd if _target_seg else 0.0
                if _marginal_val > 0:
                    _comp_scores.append((_marginal_val, _target_code, _tc.program_slug))
        _comp_scores.sort(key=lambda t: t[0], reverse=True)
        _seen_codes: set[str] = set()
        _ranked: list = []
        for _val, _code, _slug in _comp_scores:
            if _code in _seen_codes:
                continue
            _seen_codes.add(_code)
            _ranked.append(StackCandidate(
                program_slug=_slug, jurisdiction_code=_code, selected_incentive_usd=_val,
                effective_rate=0.0, qualifying_spend_usd=0.0, incentive_type="tax_credit",
            ))
        _hy_component_all_targets[_comp] = _ranked

    import heapq

    def _hy_component_type_for(jur_code: str, comp_by_jur: dict[str, str]) -> str:
        return comp_by_jur.get(jur_code, "component")

    for _anchor_code, _anchor_program_slug in sorted(_hy_anchor_candidates.items()):
        _hy_anchor_incentive = next(
            (c.selected_incentive_usd for c in priced_by_code.get(_anchor_code, [])
             if c.program_slug == _anchor_program_slug),
            home_best.selected_incentive_usd if _anchor_code == home_code and home_best else 0.0,
        )
        _hybrid_anchor_npc = round(inputs.gross_budget_usd - _hy_anchor_incentive, 2)
        _hy_seen_structure_ids: set[str] = set()

        # Performance pre-filter (correctness-preserving, not a rank/
        # cutoff heuristic): a target sharing the anchor's national
        # authority scope with no registered pairwise rule is PROVABLY
        # rejected by generate_structural_candidate's own check_all_pairs
        # (UNRESOLVED_NO_AUTHORITY blocks) -- excluding it here skips a
        # real derive_account_allocation + generate_structural_candidate
        # call that would certainly end in the same RULE_REJECTED result,
        # it never excludes a candidate that could otherwise have priced.
        def _hy_provably_illegal_with_anchor(target_program_slug: str, target_code: str) -> bool:
            if not _hy_same_authority_scope(_anchor_code, target_code):
                return False
            rule = load_named_pair_rule(_anchor_program_slug, target_program_slug) if _anchor_program_slug else None
            return rule is None or rule["rule_type"] not in (
                "allowed", "spend_reduction", "same_cost_prohibited_distinct_costs_allowed",
            )

        # CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION (REG-5 fix):
        # a movable component's target list unconditionally excluded the
        # anchor's OWN jurisdiction (t.jurisdiction_code != _anchor_code),
        # on the reasoning that routing a component "back" to the anchor's
        # jurisdiction is meaningless. That reasoning is right for a
        # SAME-cost/same-program situation, but wrong for a registered
        # same_cost_prohibited_distinct_costs_allowed pair (e.g. NY's
        # ny_state_film principal credit + us_ny_post_production_credit
        # post credit): generate_structural_candidate's own same-cost
        # refusal (by shared line_id) already makes double-claiming the
        # SAME dollars structurally impossible, so this rule type is
        # explicitly non-blocking at the generic-generator layer (see
        # structural_archetype_generator.py's own check_all_pairs
        # handling of this exact rule type) -- excluding it here was a
        # genuine gap, not a safety measure. Confirmed via direct
        # instrumentation: us_ny_post_production_credit DOES appear as a
        # real, independently-priced "post" target for US-NY in
        # _hy_component_all_targets; only this anchor-jurisdiction filter
        # was removing it when the anchor was ALSO US-NY.
        def _hy_same_jurisdiction_distinct_cost_allowed(target_program_slug: str, target_code: str) -> bool:
            if target_code != _anchor_code or not _anchor_program_slug:
                return False
            rule = load_named_pair_rule(_anchor_program_slug, target_program_slug)
            return rule is not None and rule["rule_type"] == "same_cost_prohibited_distinct_costs_allowed"

        _hy_movable = sorted(k for k, v in component_spend.items() if v > 0)
        for _r in range(2, len(_hy_movable) + 1):
            for _subset in itertools.combinations(_hy_movable, _r):
                _full_lists = [
                    [
                        t for t in _hy_component_all_targets.get(c, [])
                        if (
                            t.jurisdiction_code != _anchor_code
                            or _hy_same_jurisdiction_distinct_cost_allowed(t.program_slug, t.jurisdiction_code)
                        )
                        and not _hy_provably_illegal_with_anchor(t.program_slug, t.jurisdiction_code)
                    ]
                    for c in _subset
                ]
                if any(not lst for lst in _full_lists):
                    continue

                # CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_CORRECTION:
                # a PROVEN, not arbitrary, search window. For a subset of
                # `_r` components, any candidate ranked below `_r` within
                # its OWN component's descending-value list can never be
                # part of the true optimum (ignoring pairwise legality for
                # a moment): with only `_r - 1` OTHER components able to
                # "occupy" a jurisdiction, at least one of this component's
                # own top-`_r` candidates is always free -- swapping to it
                # can only weakly improve the total, by a standard exchange
                # argument (pigeonhole: `_r` slots, `_r - 1` possible
                # competitors). This is a real mathematical proof, not a
                # heuristic rank cutoff, and it holds at ANY window size
                # W >= `_r`, so widening (below) never invalidates it.
                #
                # The prior version of this mechanism used a single fixed,
                # documented cap (_HYBRID_BB_MAX_EXAMINED_PER_SUBSET) and
                # an honest SEARCH_DEPTH_LIMIT_REACHED disposition when
                # that cap was hit before a mathematical proof could be
                # produced -- correct, but not "complete" in the sense
                # required by this workstream. This version instead WIDENS
                # the window (starting at the proven-sufficient `_r`,
                # doubling on failure) until a real, executable combination
                # is found or every full list is exhausted, so the
                # disposition for the remainder is ALWAYS a genuine
                # DOMINATED_WITH_PROOF (or, in the rare case nothing at all
                # is feasible, no aggregate row is needed since nothing was
                # dominated -- there was simply no winner).
                _window = _r
                _best_found = float("-inf")
                _incumbent_structure_id: str | None = None
                _incumbent_jurisdiction_codes: list[str] = []
                _incumbent_program_slugs: list[str] = []
                while True:
                    _lists = [full[:_window] for full in _full_lists]
                    _visited: set[tuple[int, ...]] = set()
                    _start = tuple([0] * len(_lists))
                    _heap = [(-sum(lst[0].selected_incentive_usd for lst in _lists), _start)]
                    _visited.add(_start)
                    _best_found = float("-inf")
                    _incumbent_structure_id = None
                    _incumbent_jurisdiction_codes = []
                    _incumbent_program_slugs = []
                    while _heap:
                        _neg_bound, _idx = heapq.heappop(_heap)
                        _bound = -_neg_bound
                        if _bound <= _best_found:
                            # Every remaining heap entry has a bound <= this
                            # one (heap invariant), so all are provably
                            # dominated by the best real total already found
                            # WITHIN this window -- proof achieved before
                            # the window was even exhausted.
                            break

                        _cands = [_lists[k][_idx[k]] for k in range(len(_lists))]
                        _jur_codes = [c.jurisdiction_code for c in _cands]
                        if len(set(_jur_codes)) == len(_jur_codes):
                            _comp_by_jur = dict(zip(_jur_codes, _subset))
                            _hy_program_for_jur = {c.jurisdiction_code: c.program_slug for c in _cands}
                            if _anchor_program_slug:
                                _hy_program_for_jur[_anchor_code] = _anchor_program_slug

                            _hy_spec = StructureSpec(
                                structure_id=(
                                    "CANON-HYBRID-BB-" + _anchor_code + "-" + "-".join(
                                        f"{c}={jur}:{_hy_program_for_jur[jur]}"
                                        for jur, c in sorted(_comp_by_jur.items(), key=lambda t: t[1])
                                    )
                                ),
                                structure_type="hybrid",
                                label=(
                                    f"{_anchor_code} ({_anchor_program_slug}) + " + " + ".join(
                                        f"{c}->{jc} ({_hy_program_for_jur[jc]})"
                                        for jc, c in sorted(_comp_by_jur.items())
                                    )
                                ),
                                primary_jurisdiction=_anchor_code,
                                participants=tuple(dict.fromkeys([_anchor_code] + _jur_codes)),
                                incentive_programs=_hy_program_for_jur,
                                component_routes={c: jc for jc, c in _comp_by_jur.items()},
                            )
                            _hy_alloc = derive_account_allocation(
                                lines=inputs.budget_lines,
                                spend_category_by_code=inputs.spend_category_by_code,
                                spec=_hy_spec,
                                stated_outside_accounts=inputs.accounts_outside_jurisdiction,
                            )
                            _hy_allocations_by_jur: dict[str, list] = {}
                            for _a in _hy_alloc.assignments:
                                _hy_allocations_by_jur.setdefault(_a.jurisdiction_code, []).append(_a)

                            _hy_components = []
                            for _jur_code, _accts in sorted(_hy_allocations_by_jur.items()):
                                _program_slug = _hy_program_for_jur.get(_jur_code)
                                if not _program_slug:
                                    continue
                                _component_type = (
                                    "principal_production" if _jur_code == _anchor_code
                                    else _hy_component_type_for(_jur_code, _comp_by_jur)
                                )
                                _hy_components.append(_HybridComponent(
                                    component_type=_component_type,
                                    jurisdiction_code=_jur_code,
                                    program_slug=_program_slug,
                                    allocations=tuple(_accts),
                                    spend_category_by_code=inputs.spend_category_by_code,
                                    offshore_payroll_accounts=inputs.offshore_payroll_accounts,
                                    production_type=inputs.production_type,
                                    evidenced_requirement_facts=inputs.evidenced_program_facts,
                                    amount_facts=inputs.amount_facts,
                                ))

                            if len(_hy_components) >= 2:
                                _hy_result = _generate_hybrid_candidate(
                                    _hy_components, gross_budget_usd=inputs.gross_budget_usd,
                                    anchor_npc_usd=_hybrid_anchor_npc,
                                )
                                if _hy_result.structure_id not in _hy_seen_structure_ids:
                                    _hy_seen_structure_ids.add(_hy_result.structure_id)
                                    if _hy_result.executable:
                                        _hy_status, _hy_rejection_class = STATUS_PRICED, None
                                        # Compare like with like: `_bound` is a
                                        # sum of MARGINAL (non-anchor) component
                                        # values, so `_best_found` must track
                                        # the same marginal quantity from the
                                        # real result -- never the whole
                                        # structure's total_guaranteed_incentive_usd
                                        # (which also includes the anchor's own
                                        # multi-million-dollar baseline and would
                                        # make every bound look dominated after
                                        # the very first real result).
                                        _real_marginal = sum(
                                            ce.guaranteed_incentive_usd for ce in _hy_result.component_economics
                                            if ce.component.jurisdiction_code != _anchor_code
                                        )
                                        if _real_marginal > _best_found:
                                            _best_found = _real_marginal
                                            # Reconstruction data: the SPECIFIC
                                            # real, priced structure that
                                            # establishes the incumbent bound
                                            # every DOMINATED_WITH_PROOF row
                                            # below is measured against --
                                            # never just a bare number.
                                            _incumbent_structure_id = _hy_result.structure_id
                                            _incumbent_jurisdiction_codes = list(_hy_result.jurisdiction_codes)
                                            _incumbent_program_slugs = list(_hy_result.program_slugs)
                                    elif _hy_result.blocking_pairs:
                                        _hy_status, _hy_rejection_class = "RULE_REJECTED", "PAIRWISE_INCOMPATIBLE"
                                    elif _hy_result.rejection_reason and "budget line" in _hy_result.rejection_reason:
                                        _hy_status, _hy_rejection_class = "RULE_REJECTED", "SAME_COST_DOUBLE_CLAIM"
                                    else:
                                        _hy_status, _hy_rejection_class = "RULE_REJECTED", "THRESHOLD_NOT_MET"

                                    _hy_structure_id = uuid.uuid4()
                                    session.add(ProductionStructure(
                                        id=_hy_structure_id, project_id=project.id,
                                        name=_hy_spec.label + (
                                            " (hybrid, rejected)" if not _hy_result.executable else " (hybrid)"
                                        ),
                                        description=(
                                            "Ordinary component hybrid: separately allocated production "
                                            f"components routed to {len(_comp_by_jur)} distinct jurisdiction(s) "
                                            f"beyond the {_anchor_code} anchor, each claiming only its own real, "
                                            "separately allocated spend. No co-production treaty is involved. "
                                            "Discovered via branch-and-bound over every real, independently-"
                                            "priced destination -- never a named/allowlisted program."
                                        ),
                                        jurisdiction_allocations=[],
                                        claimed_program_ids=list(_hy_result.program_slugs),
                                        is_official_coproduction=False,
                                        coproduction_treaty=None,
                                    ))
                                    session.add(StructureCalculationResult(
                                        id=uuid.uuid4(), structure_id=_hy_structure_id, engine_version=ENGINE_VERSION,
                                        total_budget_usd=inputs.gross_budget_usd,
                                        total_incentive_value_usd=(
                                            _hy_result.total_guaranteed_incentive_usd if _hy_result.executable else None
                                        ),
                                        true_net_cost_usd=_hy_result.npc_usd if _hy_result.executable else None,
                                        risk_adjusted_net_cost_usd=_hy_result.npc_usd if _hy_result.executable else None,
                                        has_unverified_inputs=True,
                                        warnings=[LIMITATION_NOTE] + list(_hy_result.disclosed_limitations),
                                        structure_type="hybrid",
                                        calculation_trace_json={
                                            "candidate_status": _hy_status,
                                            "rejection_reason_class": _hy_rejection_class,
                                            "reason": _hy_result.rejection_reason,
                                            "discovery_classification": "structural_archetype_generator",
                                            "discovery_method": "branch_and_bound_upper_bound",
                                            "structural_family": "ordinary_component_hybrid",
                                            "evidence_level": "CANONICAL_PERSISTED_RUNTIME",
                                            "treaty_or_framework_id": None,
                                            "structure_type": "hybrid",
                                            **_hy_result_trace_extras(_hy_result),
                                            "primary_jurisdiction": _anchor_code,
                                            "program_slugs": list(_hy_result.program_slugs),
                                            "jurisdiction_codes": list(_hy_result.jurisdiction_codes),
                                            "component_types": list(_hy_result.component_types),
                                            "structural_generator_structure_id": _hy_result.structure_id,
                                            "is_baseline": False,
                                            "relocation_cost_normalized": False,
                                            "is_directly_comparable": False,
                                            "anchor_jurisdiction": _anchor_code,
                                            "anchor_program": _anchor_program_slug,
                                            "anchor_npc_usd": _hybrid_anchor_npc,
                                            "total_allocated_usd": _hy_result.total_allocated_usd,
                                            "total_guaranteed_incentive_usd": _hy_result.total_guaranteed_incentive_usd,
                                            "total_conditional_incentive_usd": _hy_result.total_conditional_incentive_usd,
                                            "incremental_benefit_vs_anchor_usd": _hy_result.incremental_benefit_vs_anchor_usd,
                                            "materiality_recommended": _hy_result.materiality_recommended,
                                            "blocking_pairs": [
                                                {
                                                    "program_a": p.program_a, "program_b": p.program_b,
                                                    "disposition": p.disposition, "condition_text": p.condition_text,
                                                }
                                                for p in _hy_result.blocking_pairs
                                            ],
                                            "component_allocations": [
                                                {
                                                    "component": ce.component.component_type,
                                                    "jurisdiction_code": ce.component.jurisdiction_code,
                                                    "program_slug": ce.component.program_slug,
                                                    "allocated_usd": ce.component.allocated_usd,
                                                    "guaranteed_incentive_usd": ce.guaranteed_incentive_usd,
                                                    "conditional_incentive_usd": ce.conditional_incentive_usd,
                                                    "line_ids": sorted(ce.component.line_ids),
                                                }
                                                for ce in _hy_result.component_economics
                                            ],
                                        },
                                        input_fingerprint=fingerprint,
                                    ))

                        for _k in range(len(_lists)):
                            _nxt = list(_idx)
                            _nxt[_k] += 1
                            _nxt = tuple(_nxt)
                            if _nxt not in _visited and _nxt[_k] < len(_lists[_k]):
                                _visited.add(_nxt)
                                _nxt_bound = sum(_lists[m][_nxt[m]].selected_incentive_usd for m in range(len(_lists)))
                                heapq.heappush(_heap, (-_nxt_bound, _nxt))
                    # end of inner `while _heap:` -- either a mathematical
                    # dominance proof was reached (bound <= best_found) or
                    # the current window was fully exhausted.
                    if _best_found > float("-inf"):
                        # A real, executable, PROVEN-optimal-within-window
                        # combination was found. By the pigeonhole argument
                        # above (valid at ANY window >= _r), nothing beyond
                        # this window can beat it either -- stop widening.
                        break
                    _max_full_len = max(len(full) for full in _full_lists)
                    if _window >= _max_full_len:
                        # Every full candidate list has been exhausted for
                        # this anchor/subset and NOTHING executable exists
                        # -- not a completeness gap, a genuine real result
                        # (every individual attempt already has its own
                        # persisted RULE_REJECTED/etc. disposition above).
                        break
                    _window = min(_window * 2, _max_full_len)
                    # end of outer widen-loop -- retry with a larger,
                    # still-proof-justified window.

                if _best_found > float("-inf"):
                    _remaining = sum(len(full) for full in _full_lists) - sum(len(lst) for lst in _lists)
                    if _remaining > 0:
                        # Genuine mathematical proof (pigeonhole exchange
                        # argument, valid at the window size actually
                        # reached), not a search-depth admission: every
                        # candidate beyond this window, in every dimension,
                        # is provably incapable of improving on the found,
                        # real, executable total -- recorded as a single
                        # auditable aggregate row, never silently dropped.
                        #
                        # Reconstruction data (CLAUDE_GENERIC_STRUCTURAL_
                        # DISCOVERY_FINAL_CORRECTION follow-on): an aggregate
                        # count alone cannot be independently checked by a
                        # reviewer who does not re-run this exact code path.
                        # `component_target_windows` names the EXACT real
                        # (jurisdiction_code, program_slug, marginal_value_usd)
                        # candidates that were actually examined per
                        # component in the window that produced the proof --
                        # the deterministic ordering key is each target's own
                        # real, independently-priced marginal incentive value
                        # (descending; computed once, above, in
                        # `_hy_component_all_targets`) -- so the exact
                        # examined set, and by construction everything a
                        # reviewer needs to know WAS provably excluded (every
                        # candidate ranked below this window, in every
                        # dimension), is named rather than merely counted.
                        _component_target_windows = {
                            _subset[_k]: [
                                {
                                    "jurisdiction_code": _t.jurisdiction_code,
                                    "program_slug": _t.program_slug,
                                    "marginal_value_usd": round(_t.selected_incentive_usd, 2),
                                }
                                for _t in _lists[_k]
                            ]
                            for _k in range(len(_subset))
                        }
                        # NUM-004 (optimizer audit defect remediation,
                        # 2026-09-18): the numeric proof itself, not just
                        # the window/incumbent identity -- an auditor could
                        # not previously check the stopping inequality
                        # without re-running this exact search. Does NOT
                        # alter which candidates are searched or how the
                        # widening loop decides to stop (that logic above
                        # is untouched) -- purely an after-the-fact
                        # numeric explanation of why the ALREADY-COMPLETE
                        # search proves domination.
                        #
                        # component_cutoff_bounds_usd: the marginal value
                        # of the FIRST candidate just outside each
                        # component's window (None when that component's
                        # full candidate list was entirely exhausted
                        # inside the window -- nothing remains to prove
                        # domination against for that component).
                        _component_cutoff_bounds_usd = {
                            _subset[_k]: (
                                round(_full_lists[_k][_window].selected_incentive_usd, 2)
                                if _window < len(_full_lists[_k]) else None
                            )
                            for _k in range(len(_subset))
                        }
                        # component_window_best_usd: each component's OWN
                        # best (rank-1) in-window value -- descending sort
                        # by construction, so this is _full_lists[_k][0].
                        _component_window_best_usd = {
                            _subset[_k]: round(_full_lists[_k][0].selected_incentive_usd, 2)
                            for _k in range(len(_subset)) if _full_lists[_k]
                        }
                        _sum_window_best_usd = round(sum(_component_window_best_usd.values()), 2)
                        # interaction_safe_total_upper_bound_usd: the
                        # MAXIMUM, over every component that still has a
                        # cutoff, of "every OTHER component held at its own
                        # best in-window value, this ONE component dropped
                        # to its own cutoff" -- a deliberately conservative
                        # (independent-maxima) bound on any single-
                        # component out-of-window substitution, "safe"
                        # because real pairwise/stacking interaction can
                        # only ever REDUCE an achievable total relative to
                        # this independent sum, never increase it. None
                        # when no component has anything left outside its
                        # window to substitute (proof complete by
                        # exhaustion alone, no swap exists to bound).
                        _component_single_swap_upper_bounds_usd = {
                            _name: round(_sum_window_best_usd - _component_window_best_usd[_name] + _cutoff, 2)
                            for _name, _cutoff in _component_cutoff_bounds_usd.items()
                            if _cutoff is not None
                        }
                        _interaction_safe_total_upper_bound_usd = (
                            max(_component_single_swap_upper_bounds_usd.values())
                            if _component_single_swap_upper_bounds_usd else None
                        )
                        _incumbent_value_usd = round(_best_found, 2)
                        _stopping_inequality_holds = (
                            True if _interaction_safe_total_upper_bound_usd is None
                            else _interaction_safe_total_upper_bound_usd <= _incumbent_value_usd
                        )
                        _dom_structure_id = uuid.uuid4()
                        session.add(ProductionStructure(
                            id=_dom_structure_id, project_id=project.id,
                            name=f"{_anchor_code} + {'/'.join(_subset)} hybrid search ({_remaining} combinations proven dominated)",
                            description=(
                                f"Branch-and-bound over {_anchor_code}'s {'/'.join(_subset)} routing search found "
                                f"a real, executable total of ${_best_found:,.2f} within a window of "
                                f"{_window} candidate(s) per component. By a pigeonhole exchange argument "
                                f"(with {_r} components in this subset, no candidate ranked below its own "
                                f"component's top {_window} can ever be part of the true optimum), the "
                                f"remaining {_remaining} combination(s) across every larger-window "
                                "possibility are provably incapable of beating this real result."
                            ),
                            jurisdiction_allocations=[], claimed_program_ids=[],
                            is_official_coproduction=False, coproduction_treaty=None,
                        ))
                        session.add(StructureCalculationResult(
                            id=uuid.uuid4(), structure_id=_dom_structure_id, engine_version=ENGINE_VERSION,
                            total_budget_usd=inputs.gross_budget_usd,
                            total_incentive_value_usd=None, true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                            has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                            structure_type="hybrid",
                            calculation_trace_json={
                                "candidate_status": "DOMINATED_WITH_PROOF",
                                "discovery_classification": "structural_archetype_generator",
                                "discovery_method": "pigeonhole_windowed_branch_and_bound",
                                "structural_family": "ordinary_component_hybrid",
                                "evidence_level": "CANONICAL_PERSISTED_RUNTIME",
                                "structure_type": "hybrid",
                                "primary_jurisdiction": _anchor_code,
                                "component_subset": list(_subset),
                                "is_baseline": False, "relocation_cost_normalized": False,
                                "is_directly_comparable": False,
                                "anchor_jurisdiction": _anchor_code, "anchor_program": _anchor_program_slug,
                                "dominated_combination_count": _remaining,
                                "proof_window_size": _window,
                                "best_real_total_found_usd": round(_best_found, 2),
                                "proof_type": "pigeonhole_membership_exchange_argument",
                                "ordering_key": (
                                    "descending real, independently-priced marginal incentive value "
                                    "of the target jurisdiction's own segment for this component "
                                    "(_price_component_relocation_candidate's incentive_floor_usd, "
                                    "computed once and reused across every anchor)"
                                ),
                                "incumbent_structure_id": _incumbent_structure_id,
                                "incumbent_jurisdiction_codes": _incumbent_jurisdiction_codes,
                                "incumbent_program_slugs": _incumbent_program_slugs,
                                "component_target_windows": _component_target_windows,
                                # NUM-004: the numeric proof itself -- see
                                # the computation's own comment above for
                                # the exact definitions.
                                "incumbent_value_usd": _incumbent_value_usd,
                                "component_cutoff_bounds_usd": _component_cutoff_bounds_usd,
                                "component_window_best_usd": _component_window_best_usd,
                                "interaction_safe_total_upper_bound_usd": _interaction_safe_total_upper_bound_usd,
                                "stopping_inequality_holds": _stopping_inequality_holds,
                                "stopping_inequality": (
                                    "interaction_safe_total_upper_bound_usd <= incumbent_value_usd"
                                    if _interaction_safe_total_upper_bound_usd is not None
                                    else "no component has a candidate outside its own window -- proof complete "
                                         "by exhaustion, no substitution bound is needed"
                                ),
                                "engine_version": ENGINE_VERSION,
                                "input_fingerprint": fingerprint,
                                "reason": (
                                    f"Pigeonhole exchange proof: with {_r} components in this subset, no "
                                    f"candidate ranked below its own component's top {_window} can be part of "
                                    "the true optimum, given a real, executable result was already found "
                                    "using only the top-window candidates."
                                ),
                            },
                            input_fingerprint=fingerprint,
                        ))

    # Existing Optimizer/Stacker Reconnection, Task B — treaty/official
    # co-production opportunities. Reuses the EXISTING treaty_engine.py
    # registries/eligibility functions unchanged via canonical_treaty_
    # bridge.py's fail-closed adapter (see that module's docstring for
    # the exact defect it corrects: registry presence != eligibility, and
    # an unresolved/failed cultural test can never resolve ELIGIBLE).
    # Neither LU nor FVD has any real ownership-share/cultural-test
    # project fact on file, so every generated opportunity here correctly
    # resolves to UNRESOLVED_FACTS — a genuine, disclosed pathway, never
    # priced or comparable economics.
    # Codex forensic finding B -- treaty PARTNER discovery must not depend
    # on the partner's OWN incentive resolving to a deterministic price.
    # `priced_by_code` only contains jurisdictions whose own program priced
    # deterministically, so every blocked/unresolved/non-guaranteed-
    # selective/rule-rejected jurisdiction silently disappeared from treaty
    # partner discovery too. Canada is the proof: its 13 real registered
    # bilateral treaties (uk-ca-bilateral, ca-fr-bilateral, ...) are keyed
    # to the bare federal "CA" code. "CA" is a real, independently
    # DISCOVERED candidate (ca_federal_pstc/ca_federal_cptc) but never
    # prices deterministically (UNPRICEABLE_AUTHORITY_INSUFFICIENT) --
    # dropping "CA" from candidate_codes meant zero Canada-linked
    # co-production opportunities could ever be generated for any
    # production, regardless of how many Canadian provinces DID price.
    #
    # The correct universe is every code production_discovery examined as a
    # genuine candidate (`candidates`, built earlier in this function from
    # discovery.accepted + accepted_alternatives + capability_only
    # examinations) union each code's own bare country prefix -- the same
    # code.split("-")[0] federal-derivation convention already used for
    # stacking above, so a treaty keyed to a country level is reachable
    # even when only a subnational program under that country was
    # independently discovered. This only widens which PAIRS get checked
    # for real treaty-registry presence (find_real_bilateral_partners's own
    # docstring: "registry presence only, never eligibility") -- real
    # eligibility (contribution share, cultural test) is still resolved
    # exactly as before by evaluate_bilateral_coproduction_opportunity, so
    # nothing here fabricates eligibility or economics.
    # NOT the full discovery universe: a jurisdiction with zero priced legs
    # anywhere (e.g. Switzerland, whose only program ch_pics_national_rebate
    # is itself AUTHORITY_UNRESOLVED_NON_PRICEABLE) has no real economic leg
    # and must not be offered as a co-production partner --
    # test_a_blocked_constituent_does_not_destroy_the_capability pins this.
    # The fix is narrower than "discovered": every code that DOES have at
    # least one priced leg, union each such code's bare country prefix (so
    # Canada's federal-level treaty code "CA" is reachable because CA-ON/
    # CA-AB/CA-QC/CA-NL priced, even though "CA" itself never does).
    # Codex global optimizer audit, P0-CAND-003: "candidate identity
    # discovery and economic priceability are improperly coupled." The
    # prior base set (`set(priced_by_code)`) silently dropped every
    # registered treaty partner whose own ordinary program has not YET
    # priced deterministically (RULE_DATA_INCOMPLETE/USER_FACT_REQUIRED/
    # capability_only/etc.) even though that partner is a real, discovered
    # candidate this project's own production_discovery already examined
    # -- exactly the "conditional partner disappears before treaty
    # eligibility is asked" defect. `candidates` (built above from
    # discovery.accepted + accepted_alternatives + capability_only) is
    # the FULL canonical discovery universe -- every code this project
    # genuinely examined, priced or not -- and is now the base set, so a
    # registered partner with only attainable missing facts remains a
    # visible conditional treaty row instead of vanishing.
    reachable_codes = {c[0] for c in candidates} | set(priced_by_code)
    reachable_codes |= {code.split("-")[0] for code in reachable_codes}
    candidate_codes = sorted(reachable_codes)
    # Codex global optimizer audit, P0-QUAL-001: co-production facts are
    # now fetched per-candidate, scoped to (treaty_slug, ordered
    # participant identities) -- never one project-global tuple reused
    # across every treaty (see _coproduction_facts docstring).

    # Codex global optimizer audit, P0-COMB-001 precomputation, hoisted
    # OUT of the per-partner loop below (bounded-pass performance repair:
    # an earlier revision recomputed find_real_bilateral_partners/
    # te.get_bilateral_treaty/_coproduction_facts/evaluate_bilateral_
    # coproduction_opportunity a SECOND time, from scratch, for the exact
    # same partner identities the home-anchored loop immediately below
    # already resolves -- real, avoidable duplicate work, now eliminated
    # by computing the combined co-production + component-allocation +
    # authorized-local-stack candidate INSIDE the same loop iteration,
    # reusing `opp`/`partner_jur` the home-anchored loop already computed
    # for that partner. Only the component-selection precomputation
    # (independent of which partner is being considered) still needs to
    # happen once, up front.
    # Codex global optimizer audit, P0-COMB-001 remediation: "do not limit
    # execution to one component or one third-country target." The
    # rejected first pass took only the single highest-spend component
    # (max(component_spend.items())) and only the single best remaining
    # target (next(...) on the first match). _combined_components now
    # covers EVERY movable component with real spend > 0, and
    # _combined_top_targets (unchanged -- it already covered every real
    # candidate jurisdiction) is walked in full per component below,
    # never truncated to its first match.
    #
    # Eight-control closeout, HO-003 discovery-suppression fix (part 2):
    # per-jurisdiction it was still collapsed to `max(cands, ...)` -- one
    # candidate PER JURISDICTION, silently discarding every other real,
    # independently-priced program that jurisdiction also has (confirmed
    # live: NZ's own PDV/post-vfx-specific grant,
    # new_zealand_screen_production_grant_-international_post_vfx, was
    # suppressed in favor of NZ's differently-cited general international
    # grant, nz_spg_international -- genuinely different real programs,
    # not aliases, confirmed via their own separate RateRule citations).
    # Every real, independently-priced program at every non-home
    # jurisdiction is now included -- the same Locked Structural Policy
    # doctrine (never just the highest) already applied to the component
    # and treaty-partner dimensions.
    _combined_components: list[tuple[str, float]] = []
    _combined_top_targets: list = []
    if component_spend and home_program_slug:
        _combined_components = sorted(
            ((c, amt) for c, amt in component_spend.items() if amt > 0),
            key=lambda kv: kv[1], reverse=True,
        )
        _combined_top_targets = sorted(
            (
                cand
                for code, cands in priced_by_code.items() if code != home_code
                for cand in cands
            ),
            key=lambda c: c.selected_incentive_usd, reverse=True,
        )

    # Codex global optimizer audit, P0-CAND-001: "a presentation bound
    # has become an evaluation bound." The prior MAX_TREATY_PARTNERS=5
    # pre-evaluation slice discarded every REAL, registered bilateral
    # partner beyond the first five in list order (Canada alone has 13
    # registered partners) BEFORE eligibility was ever checked -- a
    # structurally valid 6th+ partner could never be represented at all,
    # in any state (priced, conditional, or rejected). Every registered
    # partner returned by find_real_bilateral_partners is now evaluated;
    # any future display/pagination limit belongs in the SERVED VIEW
    # layer (canonical_production_view.py), never here.
    for partner_code in find_real_bilateral_partners(home_code, candidate_codes):
        # P0-QUAL-001: resolve the real treaty_slug FIRST (a read-only
        # registry lookup, te.get_bilateral_treaty -- no side effects, no
        # pricing) so facts can be fetched scoped to THIS treaty and THIS
        # ordered (majority=home_code, minority=partner_code) participant
        # pair before the evaluator is ever called. If no treaty resolves
        # here (should not happen -- find_real_bilateral_partners is
        # itself registry-presence-only) facts stay None/None/None, which
        # evaluate_bilateral_coproduction_opportunity already treats as
        # UNRESOLVED_FACTS, never a crash or an invented value.
        _treaty_row = te.get_bilateral_treaty(home_code, partner_code)
        _bp_majority_pct = _bp_minority_pct = None
        _bp_cultural_test_passed = None
        if _treaty_row is not None:
            _bp_majority_pct, _bp_minority_pct, _bp_cultural_test_passed = await _coproduction_facts(
                session, project.id, _treaty_row.treaty_slug, (home_code, partner_code),
            )
        opp = evaluate_bilateral_coproduction_opportunity(
            home_code, partner_code,
            majority_pct=_bp_majority_pct, minority_pct=_bp_minority_pct,
            cultural_test_passed=_bp_cultural_test_passed,
            # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING: this
            # treaty's own real, cited personnel-eligibility rule (None
            # for every treaty not yet individually researched) against
            # this project's real, confirmed-vs-unconfirmed attachment
            # facts -- additive, never blocks a treaty whose personnel
            # clause has not been researched (see PersonnelRequirement's
            # own docstring).
            personnel_requirement=_treaty_row.personnel_requirement if _treaty_row else None,
            personnel_attachment_facts=role_attachment_facts,
        )
        if opp is None:
            continue
        partner_jur = jurisdiction_by_code.get(partner_code)
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=f"{home_code} + {partner_code} — official co-production opportunity ({opp.treaty_slug})",
            description=(
                f"A registered bilateral co-production treaty ({opp.treaty_slug}) "
                f"exists between {home_code} and {partner_code}. Real ownership/"
                "spend-share and cultural-test facts are required to resolve "
                "eligibility — not yet on file for this project."
            ),
            jurisdiction_allocations=[],
            claimed_program_ids=[],
        )
        session.add(structure)
        await session.flush()
        # Hybrid/anchor composition (Task C): a co-production opportunity
        # ALSO composes with the conditional grants/funds layer already
        # built for Task 7 — "anchor + treaty + conditional fund" is one
        # of the independent relationship combinations, reusing the exact
        # same _conditional_data() call every other structure type uses,
        # never a second conditional-funds implementation.
        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), home_code, (),
        )
        # Co-Pro Conditional Pricing Bridge: an UNRESOLVED_FACTS treaty
        # opportunity gets a real, priced conditional scenario attempted
        # (never for ELIGIBLE/INELIGIBLE — those already have a real
        # resolved answer). Purely additive disclosure on the SAME
        # structure; never changes candidate_status, is_directly_
        # comparable, or ranking eligibility below.
        _conditional_scenario = None
        if opp.resolution_state == "UNRESOLVED_FACTS":
            _home_candidates = priced_by_code.get(home_code) or []
            _baseline_incentive = max(
                (c.selected_incentive_usd for c in _home_candidates), default=None,
            )
            _conditional_scenario = _build_conditional_bilateral_scenario(
                inputs, home_code, partner_code, opp.treaty_slug, _baseline_incentive,
                personnel_attachment_facts=role_attachment_facts,
            )
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
            true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
            has_unverified_inputs=True,
            warnings=[
                LIMITATION_NOTE,
                "Official co-production opportunity — real ownership/cultural-test "
                "facts are not yet on file for this project; not priced as qualified "
                "economics. Registry presence is real and disclosed; it is never "
                "reported as resolved eligibility.",
            ],
            structure_type="treaty_coproduction",
            calculation_trace_json={
                "candidate_status": STATUS_CO_PRO_OPPORTUNITY,
                "discovery_classification": "treaty_coproduction",
                "structure_type": "treaty_coproduction",
                "primary_jurisdiction": home_code,
                "is_baseline": False,
                "relocation_cost_normalized": False,
                "is_directly_comparable": False,
                "treaty_slug": opp.treaty_slug,
                "conditional_programs": _conditional_program_dicts,
                "conditional_compatibility": _conditional_compatibility_dict,
                "coproduction_partners": [{
                    "jurisdiction_code": partner_code,
                    "jurisdiction_display_name": partner_jur.name if partner_jur else partner_code,
                }],
                "treaty_resolution_state": opp.resolution_state,
                "treaty_cultural_test_required": opp.cultural_test_required,
                "treaty_cultural_test_resolved": opp.cultural_test_resolved,
                "treaty_disqualification_reasons": list(opp.disqualification_reasons),
                # COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION —
                # home_code (this project's own current jurisdiction) IS
                # one of this treaty's two real parties by construction of
                # this loop (find_real_bilateral_partners(home_code, ...))
                # -- always project_anchored=True here. opportunity_relevance
                # is a read-only classification of the ALREADY-computed
                # resolution_state/conditional_scenario, never a new
                # eligibility decision (see _classify_opportunity_relevance's
                # own docstring for the full contract).
                "opportunity_inclusion_source": "home_anchored_bilateral_treaty_registry",
                "project_anchored": True,
                "opportunity_relevance": _classify_opportunity_relevance(
                    opp.resolution_state, _conditional_scenario, True,
                    personnel_gate_state=opp.personnel_gate_state,
                ),
                # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING —
                # the real creative-personnel gate's own served contract:
                # satisfied/failed requirements, missing facts, curable
                # levers, and the next highest-value factual question.
                # personnel_gate_state is NOT_APPLICABLE (never blocking,
                # and not an open data question on this project) for
                # every treaty whose own registry entry carries no
                # researched personnel_requirement at all.
                "personnel_gate_state": opp.personnel_gate_state,
                "personnel_satisfied_requirements": list(opp.personnel_satisfied_requirements),
                "personnel_failed_requirements": list(opp.personnel_failed_requirements),
                "personnel_missing_facts": list(opp.personnel_missing_facts),
                "personnel_curable_levers": list(opp.personnel_curable_levers),
                "personnel_next_question": opp.personnel_next_question,
                "reason": "; ".join(opp.notes) or "Real ownership/cultural facts required to resolve eligibility.",
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
                "conditional_scenario": _conditional_scenario,
            },
            input_fingerprint=fingerprint,
        ))

        # Codex global optimizer audit, P0-COMB-001 — the combined
        # co-production + component-allocation + anchor + authorized-
        # local-stack topology, computed HERE (inside the home-anchored
        # loop, reusing `opp`/`partner_jur` this same iteration already
        # resolved) rather than in a second separate pass over
        # find_real_bilateral_partners -- see the precomputation comment
        # above for why the second pass was removed.
        #
        # Codex rejection remediation (first pass rejected: "the helper
        # does not allocate any spend to its treaty partner"): the base
        # allocation is now built from the SAME real, evidenced
        # majority_pct/minority_pct contribution facts already fetched
        # for THIS treaty/participant scope above (_bp_majority_pct/
        # _bp_minority_pct) -- never invented, never a bare registry
        # guess. A partner with no positive evidenced share raises
        # _InvalidCombinedAllocation and is persisted as its own
        # retained, machine-readable rejected candidate; it is never
        # silently skipped or silently zeroed. Every movable component
        # with real spend (never just the highest) and every genuinely
        # third, distinct candidate target jurisdiction (never just the
        # single best) is attempted per eligible partner -- Codex's own
        # required remediation: "do not limit execution to one component
        # or one third-country target." Authorized local stacks are now
        # attempted on ALL THREE allocated sides (anchor, treaty partner,
        # component target), not the anchor alone. In practice this
        # activates only for a production with genuine treaty ownership
        # facts on file; it is additive and touches no existing candidate.
        if opp.resolution_state == RESOLUTION_ELIGIBLE and _combined_components:
            comb_opp = opp
            # Eight-control closeout, HO-003 discovery-suppression fix:
            # Locked Structural Policy point 2 (ranking must never
            # suppress feasible discovery) applies to the treaty PARTNER
            # side exactly as it already does to the movable-component
            # target side two lines below ("never just the highest").
            # _all_priced_treaty_side_candidates enumerates EVERY real,
            # treaty-valid, independently-priceable partner program (not
            # just the jurisdiction's own overall-best-priced program,
            # which may not even be one of this treaty's real unlocks) --
            # each is tried and persisted with its own real terminal
            # disposition below, never silently narrowed to one winner
            # before persistence.
            _comb_partner_candidates = _all_priced_treaty_side_candidates(
                inputs, partner_code, priced_by_code,
                tuple(_treaty_row.minority_unlocks) if _treaty_row else (),
            )
            if not _comb_partner_candidates:
                # HO-007 closeout: a real, registered treaty whose OWN
                # named unlocks are all currently unpriceable in this
                # codebase (zero rate rules, or an explicit authority-
                # coverage block) must never be silently skipped -- the
                # prior code simply never entered this loop body at all
                # when the single "best" candidate was None, persisting
                # nothing. Persists one explicit, reconstructable
                # RULE_REJECTED row naming every attempted unlock and its
                # real reason (never a generic catch-all).
                from app.data.authority_coverage_registry import get_coverage_status
                from app.data.program_rate_rules import get_rate_rules
                _comb_unlock_reasons = []
                for _comb_unlock_slug in (tuple(_treaty_row.minority_unlocks) if _treaty_row else ()):
                    _comb_unlock_cov = get_coverage_status(_comb_unlock_slug)
                    if _comb_unlock_cov is not None and _comb_unlock_cov.blocks_economic_candidacy:
                        _comb_unlock_reasons.append(
                            f"{_comb_unlock_slug}: {_comb_unlock_cov.state} -- {_comb_unlock_cov.reason}"
                        )
                    elif not get_rate_rules(_comb_unlock_slug):
                        _comb_unlock_reasons.append(
                            f"{_comb_unlock_slug}: no statutory RateRule recorded in this codebase "
                            "(a genuine, disclosed data gap, not a code defect)."
                        )
                    else:
                        _comb_unlock_reasons.append(
                            f"{_comb_unlock_slug}: has a real RateRule but did not independently "
                            "price for this production's real facts."
                        )
                _comb_no_partner_structure = ProductionStructure(
                    id=uuid.uuid4(), project_id=project.id,
                    name=f"{home_code} + {partner_code} co-production ({comb_opp.treaty_slug}, no priceable partner program)",
                    description=(
                        f"{opp.treaty_slug}'s own real, registered minority_unlocks "
                        f"({list(_treaty_row.minority_unlocks) if _treaty_row else []}) contain no "
                        "program independently priceable in this codebase today -- " + " ".join(_comb_unlock_reasons)
                    ),
                    jurisdiction_allocations=[],
                    claimed_program_ids=[home_program_slug] + (list(_treaty_row.minority_unlocks) if _treaty_row else []),
                )
                session.add(_comb_no_partner_structure)
                await session.flush()
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=_comb_no_partner_structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                    structure_type="hybrid",
                    calculation_trace_json={
                        "candidate_status": "RULE_REJECTED",
                        "rejection_reason_class": "NO_PRICEABLE_TREATY_UNLOCK",
                        "discovery_classification": "combined_coproduction_component_stack",
                        "structural_family": "combined_coproduction_component_stack",
                        "structure_type": "hybrid",
                        "primary_jurisdiction": home_code,
                        "treaty_slug": comb_opp.treaty_slug,
                        "program_slugs": [home_program_slug] + (list(_treaty_row.minority_unlocks) if _treaty_row else []),
                        "reason": " ".join(_comb_unlock_reasons),
                        "is_baseline": False, "relocation_cost_normalized": False,
                        "is_directly_comparable": False,
                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                    },
                    input_fingerprint=fingerprint,
                ))
            for partner_best in _comb_partner_candidates:
                for _combined_component, _combined_spend_amount in _combined_components:
                    for _comb_target in _combined_top_targets:
                        if _comb_target.jurisdiction_code in (home_code, partner_code):
                            continue  # the component target must be a THIRD, distinct side
                        if partner_best is None:
                            continue
                        _comb_label = (
                            f"{home_code} + {partner_code} co-production ({comb_opp.treaty_slug}) + "
                            f"{_combined_component} routed to {_comb_target.jurisdiction_code}"
                        )
                        _comb_claimed_programs = [
                            home_program_slug, partner_best.program_slug, _comb_target.program_slug,
                        ]
                        try:
                            spec, allocation, pricing = _price_combined_coproduction_component_candidate(
                                inputs, home_code, home_program_slug, partner_code, partner_best.program_slug,
                                _comb_target.jurisdiction_code, _comb_target.program_slug,
                                _combined_component, comb_opp.treaty_slug,
                                _bp_majority_pct, _bp_minority_pct,
                            )
                        except _InvalidCombinedAllocation as _comb_invalid:
                            _comb_invalid_structure = ProductionStructure(
                                id=uuid.uuid4(), project_id=project.id,
                                name=f"{_comb_label} (combined, rejected)",
                                description=f"Combined candidate rejected: {_comb_invalid.reason}",
                                jurisdiction_allocations=[],
                                claimed_program_ids=_comb_claimed_programs,
                            )
                            session.add(_comb_invalid_structure)
                            await session.flush()
                            session.add(StructureCalculationResult(
                                id=uuid.uuid4(), structure_id=_comb_invalid_structure.id, engine_version=ENGINE_VERSION,
                                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                structure_type="hybrid",
                                calculation_trace_json={
                                    "candidate_status": "RULE_REJECTED",
                                    "rejection_reason_class": "INVALID_COMBINED_ALLOCATION",
                                    "discovery_classification": "combined_coproduction_component_stack",
                                    "structure_type": "hybrid",
                                    "primary_jurisdiction": home_code,
                                    "treaty_slug": comb_opp.treaty_slug,
                                    "program_slugs": _comb_claimed_programs,
                                    "reason": _comb_invalid.reason,
                                    "is_baseline": False,
                                    "relocation_cost_normalized": False,
                                    "is_directly_comparable": False,
                                    "anchor_jurisdiction": home_code,
                                    "anchor_program": home_program_slug,
                                    "coproduction_partners": [
                                        {"jurisdiction_code": home_code}, {"jurisdiction_code": partner_code},
                                    ],
                                    "component_allocations": [{
                                        "component": _combined_component,
                                        "jurisdiction_code": _comb_target.jurisdiction_code,
                                        "program_slug": _comb_target.program_slug,
                                        "allocated_usd": _combined_spend_amount,
                                    }],
                                },
                                input_fingerprint=fingerprint,
                            ))
                            continue

                        if not pricing.is_fully_priced:
                            _comb_rej_status, _comb_rej_class = _classify_component_rejection(pricing.blockers)
                            _comb_rej_structure = ProductionStructure(
                                id=uuid.uuid4(), project_id=project.id,
                                name=f"{_comb_label} (combined, rejected)",
                                description=(
                                    "Combined co-production + component-allocation candidate does "
                                    f"not clear pricing: {'; '.join(pricing.blockers) or 'not fully priced.'}"
                                ),
                                jurisdiction_allocations=[],
                                claimed_program_ids=_comb_claimed_programs,
                            )
                            session.add(_comb_rej_structure)
                            await session.flush()
                            session.add(StructureCalculationResult(
                                id=uuid.uuid4(), structure_id=_comb_rej_structure.id, engine_version=ENGINE_VERSION,
                                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                structure_type="hybrid",
                                calculation_trace_json={
                                    "candidate_status": _comb_rej_status,
                                    "rejection_reason_class": _comb_rej_class,
                                    "discovery_classification": "combined_coproduction_component_stack",
                                    "structure_type": "hybrid",
                                    "primary_jurisdiction": home_code,
                                    "treaty_slug": comb_opp.treaty_slug,
                                    "program_slugs": _comb_claimed_programs,
                                    "reason": "; ".join(pricing.blockers) or "Not fully priced.",
                                    "is_baseline": False,
                                    "relocation_cost_normalized": False,
                                    "is_directly_comparable": False,
                                    "anchor_jurisdiction": home_code,
                                    "anchor_program": home_program_slug,
                                    "coproduction_partners": [
                                        {"jurisdiction_code": home_code}, {"jurisdiction_code": partner_code},
                                    ],
                                    "component_allocations": [{
                                        "component": _combined_component,
                                        "jurisdiction_code": _comb_target.jurisdiction_code,
                                        "program_slug": _comb_target.program_slug,
                                        "allocated_usd": _combined_spend_amount,
                                    }],
                                },
                                input_fingerprint=fingerprint,
                            ))
                            continue

                        # P0-COMB-001 remediation: authorized local stacks
                        # attempted on every allocated side (anchor, treaty
                        # partner, component target), never the anchor alone.
                        _comb_sides = [
                            (home_code, home_program_slug),
                            (partner_code, partner_best.program_slug),
                            (_comb_target.jurisdiction_code, _comb_target.program_slug),
                        ]
                        _comb_stack_delta, _comb_stack_notes, _comb_stack_program_slugs, _comb_unresolved = (
                            _apply_authorized_stacks_to_combined_sides(priced_by_code, _comb_sides)
                        )
                        _comb_selected_incentive = round(pricing.selected_incentive_usd + _comb_stack_delta, 2)
                        _comb_npc = pricing.npc_with_adjustments_usd
                        if _comb_npc is not None:
                            _comb_npc = round(_comb_npc - _comb_stack_delta, 2)
                        _comb_stacking_note = " ".join(_comb_stack_notes)

                        for _unresolved_side, _unresolved_group in _comb_unresolved:
                            # A second same-jurisdiction candidate exists on
                            # this side but no named, publishable rule covers
                            # this exact combination — retained as its OWN
                            # rejected candidate (never silently applied,
                            # never silently dropped), while the base
                            # (unstacked, or stacked on its OTHER sides)
                            # combined structure below still stands on its own.
                            _comb_stack_rej_structure = ProductionStructure(
                                id=uuid.uuid4(), project_id=project.id,
                                name=f"{_comb_label} + unresolved local stack ({_unresolved_side}, rejected)",
                                description=(
                                    f"{_unresolved_side} has a second same-jurisdiction candidate "
                                    f"program ({[c.program_slug for c in _unresolved_group]}) but "
                                    "no named, publishable stacking rule covers this exact "
                                    "combination — withheld, never summed as though independent."
                                ),
                                jurisdiction_allocations=[],
                                claimed_program_ids=_comb_claimed_programs + [
                                    c.program_slug for c in _unresolved_group
                                ],
                            )
                            session.add(_comb_stack_rej_structure)
                            await session.flush()
                            session.add(StructureCalculationResult(
                                id=uuid.uuid4(), structure_id=_comb_stack_rej_structure.id,
                                engine_version=ENGINE_VERSION,
                                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                structure_type="hybrid",
                                calculation_trace_json={
                                    "candidate_status": "RULE_DATA_INCOMPLETE",
                                    "rejection_reason_class": "RULE_DATA_INCOMPLETE",
                                    "discovery_classification": "combined_coproduction_component_stack",
                                    "structure_type": "hybrid",
                                    "primary_jurisdiction": home_code,
                                    "treaty_slug": comb_opp.treaty_slug,
                                    "program_slugs": _comb_claimed_programs + [
                                        c.program_slug for c in _unresolved_group
                                    ],
                                    "reason": (
                                        "No named, publishable stacking rule covers "
                                        f"{_unresolved_side}: {'+'.join(c.program_slug for c in _unresolved_group)}."
                                    ),
                                    "is_baseline": False,
                                    "relocation_cost_normalized": False,
                                    "is_directly_comparable": False,
                                    "anchor_jurisdiction": home_code,
                                    "anchor_program": home_program_slug,
                                },
                                input_fingerprint=fingerprint,
                            ))

                        _comb_home_jur = jurisdiction_by_code.get(home_code)
                        _comb_target_jur = jurisdiction_by_code.get(_comb_target.jurisdiction_code)
                        _comb_by_jur = allocation.allocated_by_jurisdiction()
                        _comb_structure = ProductionStructure(
                            id=uuid.uuid4(), project_id=project.id,
                            name=_comb_label,
                            description=(
                                f"Official co-production between {home_code} (anchor) and "
                                f"{partner_code} under {comb_opp.treaty_slug}, allocated by each "
                                f"party's real evidenced contribution share, with {_combined_component} "
                                f"work (${_combined_spend_amount:,.0f} of real project budget) routed "
                                f"to {_comb_target.jurisdiction_code} to claim "
                                f"{_program_display_name(_comb_target.program_slug)}."
                                + (f" {_comb_stacking_note}" if _comb_stacking_note else "")
                            ),
                            jurisdiction_allocations=[
                                j for j in (
                                    {"jurisdiction_id": str(_comb_home_jur.id), "shoot_pct": 100,
                                     "budget_pct": round(100 * _comb_by_jur.get(home_code, 0.0) / inputs.gross_budget_usd, 2)}
                                    if _comb_home_jur else None,
                                    {"jurisdiction_id": str(partner_jur.id), "shoot_pct": 0,
                                     "budget_pct": round(100 * _comb_by_jur.get(partner_code, 0.0) / inputs.gross_budget_usd, 2)}
                                    if partner_jur else None,
                                    {"jurisdiction_id": str(_comb_target_jur.id), "shoot_pct": 0,
                                     "budget_pct": round(100 * _comb_by_jur.get(_comb_target.jurisdiction_code, 0.0) / inputs.gross_budget_usd, 2)}
                                    if _comb_target_jur else None,
                                ) if j
                            ],
                            claimed_program_ids=_comb_claimed_programs + _comb_stack_program_slugs,
                        )
                        session.add(_comb_structure)
                        await session.flush()
                        _comb_conditional_program_dicts, _comb_conditional_compatibility_dict = _conditional_data(
                            str(_comb_structure.id), home_code, tuple(_comb_claimed_programs),
                        )
                        session.add(StructureCalculationResult(
                            id=uuid.uuid4(), structure_id=_comb_structure.id, engine_version=ENGINE_VERSION,
                            total_budget_usd=inputs.gross_budget_usd,
                            total_incentive_value_usd=_comb_selected_incentive,
                            true_net_cost_usd=pricing.npc_verified_usd,
                            risk_adjusted_net_cost_usd=_comb_npc,
                            has_unverified_inputs=True,
                            warnings=[
                                LIMITATION_NOTE,
                                "Combined co-production + component-allocation + authorized-stack "
                                "candidate: a new, additive structure topology — not directly "
                                "comparable to single-leg structures' own NPC without confirming "
                                "the same normalization basis.",
                            ] + _comb_stack_notes,
                            structure_type="hybrid",
                            calculation_trace_json={
                                "candidate_status": STATUS_PRICED,
                                "discovery_classification": "combined_coproduction_component_stack",
                                "structure_type": "hybrid",
                                "primary_jurisdiction": home_code,
                                "treaty_slug": comb_opp.treaty_slug,
                                "program_slugs": _comb_claimed_programs + _comb_stack_program_slugs,
                                "is_baseline": False,
                                "relocation_cost_normalized": False,
                                "is_directly_comparable": False,
                                "anchor_jurisdiction": home_code,
                                "anchor_program": home_program_slug,
                                "coproduction_partners": [
                                    {
                                        "jurisdiction_code": home_code,
                                        "jurisdiction_display_name": _comb_home_jur.name if _comb_home_jur else home_code,
                                        "allocated_usd": _comb_by_jur.get(home_code, 0.0),
                                    },
                                    {
                                        "jurisdiction_code": partner_code,
                                        "jurisdiction_display_name": partner_jur.name if partner_jur else partner_code,
                                        "allocated_usd": _comb_by_jur.get(partner_code, 0.0),
                                    },
                                ],
                                "treaty_resolution_state": comb_opp.resolution_state,
                                "component_allocations": [{
                                    "component": _combined_component,
                                    "jurisdiction_code": _comb_target.jurisdiction_code,
                                    "jurisdiction_display_name": _comb_target_jur.name if _comb_target_jur else _comb_target.jurisdiction_code,
                                    "program_slug": _comb_target.program_slug,
                                    "allocated_usd": _comb_by_jur.get(_comb_target.jurisdiction_code, 0.0),
                                }],
                                "stacking_note": _comb_stacking_note,
                                "stacked_programs": _comb_stack_program_slugs,
                                "selected_incentive_usd": _comb_selected_incentive,
                                "npc_verified_usd": pricing.npc_verified_usd,
                                "npc_with_adjustments_usd": _comb_npc,
                                "gross_budget_usd": inputs.gross_budget_usd,
                                "segments": _segment_dicts(pricing),
                                "conditional_programs": _comb_conditional_program_dicts,
                                "conditional_compatibility": _comb_conditional_compatibility_dict,
                            },
                            input_fingerprint=fingerprint,
                        ))

                # Six-control correction pass (structural-optimizer wiring
                # closure), HO-013: 2+ SIMULTANEOUS movable components
                # routed to distinct targets in one combined structure --
                # the single-component loop directly above tries exactly
                # one component at a time (a real, disclosed scope limit
                # of the pre-existing mechanism, not a doctrine choice).
                # _price_combined_coproduction_multi_component_candidate
                # (above) already supports an arbitrary number of
                # simultaneously-routed components; this loop is the
                # discovery side.
                #
                # REMOVED this pass: the prior _MULTI_COMPONENT_TARGET_
                # BOUND=200 flat cutoff sliced the SAME global, component-
                # AGNOSTIC _combined_top_targets list for every component,
                # which could silently exclude a genuinely component-
                # specific real candidate (e.g. a post/vfx-specific grant)
                # ranked below 200 in the GLOBAL ranking even though it
                # ranks near the top of its OWN component's real candidate
                # list -- an arbitrary cutoff, not a proof, and a real
                # violation of "ranking must never suppress feasible
                # discovery" for this dimension specifically.
                #
                # Replaced with: (1) COMPONENT-SPECIFIC candidate lists --
                # _hy_component_all_targets[component], the SAME real,
                # independently-priced-per-component list the ordinary_
                # component_hybrid mechanism above already builds via
                # _price_component_relocation_candidate (real per-
                # component eligibility, not a program-name heuristic);
                # (2) a genuine PROOF-BASED widening search identical in
                # structure to that same mechanism's own pigeonhole
                # exchange argument: for exactly 2 simultaneously-routed
                # components, no candidate ranked below its own
                # component's top-2 (by real, independent marginal value)
                # can ever be part of the true optimum, since only 1
                # OTHER component can occupy a jurisdiction (pigeonhole:
                # 2 slots, 1 competitor). The search starts at this
                # proven-sufficient window=2 and WIDENS (doubling, never
                # truncating) on failure until a real, executable PRICED
                # combination is found or every real candidate has been
                # exhausted -- so the disposition for every candidate
                # beyond the window that produced a real result is always
                # a genuine DOMINATED_WITH_PROOF aggregate row, never an
                # admitted search-budget cutoff. Every combination
                # actually tried within the window is still individually
                # priced and persisted exactly as before (PRICED/
                # RULE_REJECTED per pair) -- only the discovery bound
                # changed, not the per-pair pricing/persistence contract.
                if len(_combined_components) >= 2:
                    for _mc_comp_a, _mc_comp_b in itertools.combinations(
                        sorted(c for c, _amt in _combined_components), 2,
                    ):
                        _mc_full_a = [
                            t for t in _hy_component_all_targets.get(_mc_comp_a, [])
                            if t.jurisdiction_code not in (home_code, partner_code)
                        ]
                        _mc_full_b = [
                            t for t in _hy_component_all_targets.get(_mc_comp_b, [])
                            if t.jurisdiction_code not in (home_code, partner_code)
                        ]
                        if not _mc_full_a or not _mc_full_b:
                            continue
                        _mc_window = 2
                        _mc_best_total = float("-inf")
                        _mc_incumbent_structure_id: str | None = None
                        _mc_incumbent_jurisdiction_codes: list[str] = []
                        _mc_incumbent_program_slugs: list[str] = []
                        _mc_tried_pairs: set[tuple[str, str, str, str]] = set()
                        while True:
                            _mc_lists_a = _mc_full_a[:_mc_window]
                            _mc_lists_b = _mc_full_b[:_mc_window]
                            for _mc_target_a, _mc_target_b in itertools.product(_mc_lists_a, _mc_lists_b):
                                _mc_pair_key = (
                                    _mc_target_a.jurisdiction_code, _mc_target_a.program_slug,
                                    _mc_target_b.jurisdiction_code, _mc_target_b.program_slug,
                                )
                                if _mc_pair_key in _mc_tried_pairs:
                                    continue
                                _mc_tried_pairs.add(_mc_pair_key)
                                if _mc_target_a.jurisdiction_code == _mc_target_b.jurisdiction_code:
                                    continue  # each component's target must be a distinct jurisdiction
                                _mc_component_targets = [
                                    (_mc_comp_a, _mc_target_a.jurisdiction_code, _mc_target_a.program_slug),
                                    (_mc_comp_b, _mc_target_b.jurisdiction_code, _mc_target_b.program_slug),
                                ]
                                _mc_claimed_programs = [
                                    home_program_slug, partner_best.program_slug,
                                    _mc_target_a.program_slug, _mc_target_b.program_slug,
                                ]
                                _mc_label = (
                                    f"{home_code} + {partner_code} co-production ({comb_opp.treaty_slug}) + "
                                    f"{_mc_comp_a} routed to {_mc_target_a.jurisdiction_code} + "
                                    f"{_mc_comp_b} routed to {_mc_target_b.jurisdiction_code}"
                                )
                                try:
                                    _mc_spec, _mc_allocation, _mc_pricing = _price_combined_coproduction_multi_component_candidate(
                                        inputs, home_code, home_program_slug, partner_code, partner_best.program_slug,
                                        _mc_component_targets, comb_opp.treaty_slug,
                                        _bp_majority_pct, _bp_minority_pct,
                                    )
                                except _InvalidCombinedAllocation as _mc_invalid:
                                    _mc_invalid_structure = ProductionStructure(
                                        id=uuid.uuid4(), project_id=project.id,
                                        name=f"{_mc_label} (multi-component, rejected)",
                                        description=f"Combined multi-component candidate rejected: {_mc_invalid.reason}",
                                        jurisdiction_allocations=[], claimed_program_ids=_mc_claimed_programs,
                                    )
                                    session.add(_mc_invalid_structure)
                                    await session.flush()
                                    session.add(StructureCalculationResult(
                                        id=uuid.uuid4(), structure_id=_mc_invalid_structure.id, engine_version=ENGINE_VERSION,
                                        total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                        true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                        structure_type="hybrid",
                                        calculation_trace_json={
                                            "candidate_status": "RULE_REJECTED",
                                            "rejection_reason_class": "INVALID_COMBINED_ALLOCATION",
                                            "discovery_classification": "combined_coproduction_multi_component_stack",
                                            "structural_family": "combined_coproduction_multi_component_stack",
                                            "structure_type": "hybrid",
                                            "primary_jurisdiction": home_code,
                                            "treaty_slug": comb_opp.treaty_slug,
                                            "program_slugs": _mc_claimed_programs,
                                            "reason": _mc_invalid.reason,
                                            "is_baseline": False, "relocation_cost_normalized": False,
                                            "is_directly_comparable": False,
                                            "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                                        },
                                        input_fingerprint=fingerprint,
                                    ))
                                    continue
                                if not _mc_pricing.is_fully_priced:
                                    _mc_rej_status, _mc_rej_class = _classify_component_rejection(_mc_pricing.blockers)
                                    _mc_rej_structure = ProductionStructure(
                                        id=uuid.uuid4(), project_id=project.id,
                                        name=f"{_mc_label} (multi-component, rejected)",
                                        description=(
                                            "Combined multi-component candidate does not clear pricing: "
                                            f"{'; '.join(_mc_pricing.blockers) or 'not fully priced.'}"
                                        ),
                                        jurisdiction_allocations=[], claimed_program_ids=_mc_claimed_programs,
                                    )
                                    session.add(_mc_rej_structure)
                                    await session.flush()
                                    session.add(StructureCalculationResult(
                                        id=uuid.uuid4(), structure_id=_mc_rej_structure.id, engine_version=ENGINE_VERSION,
                                        total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                        true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                        structure_type="hybrid",
                                        calculation_trace_json={
                                            "candidate_status": _mc_rej_status,
                                            "rejection_reason_class": _mc_rej_class,
                                            "discovery_classification": "combined_coproduction_multi_component_stack",
                                            "structural_family": "combined_coproduction_multi_component_stack",
                                            "structure_type": "hybrid",
                                            "primary_jurisdiction": home_code,
                                            "treaty_slug": comb_opp.treaty_slug,
                                            "program_slugs": _mc_claimed_programs,
                                            "reason": "; ".join(_mc_pricing.blockers) or "Not fully priced.",
                                            "is_baseline": False, "relocation_cost_normalized": False,
                                            "is_directly_comparable": False,
                                            "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                                        },
                                        input_fingerprint=fingerprint,
                                    ))
                                    continue
                                _mc_by_jur = _mc_allocation.allocated_by_jurisdiction()
                                _mc_home_jur = jurisdiction_by_code.get(home_code)
                                _mc_target_a_jur = jurisdiction_by_code.get(_mc_target_a.jurisdiction_code)
                                _mc_target_b_jur = jurisdiction_by_code.get(_mc_target_b.jurisdiction_code)
                                _mc_structure = ProductionStructure(
                                    id=uuid.uuid4(), project_id=project.id,
                                    name=_mc_label,
                                    description=(
                                        f"Official co-production between {home_code} (anchor) and {partner_code} "
                                        f"under {comb_opp.treaty_slug}, with {_mc_comp_a} routed to "
                                        f"{_mc_target_a.jurisdiction_code} and {_mc_comp_b} routed to "
                                        f"{_mc_target_b.jurisdiction_code} -- two simultaneous movable "
                                        "components with disjoint real cost pools, no dollar counted twice."
                                    ),
                                    jurisdiction_allocations=[
                                        j for j in (
                                            {"jurisdiction_id": str(_mc_home_jur.id), "shoot_pct": 100,
                                             "budget_pct": round(100 * _mc_by_jur.get(home_code, 0.0) / inputs.gross_budget_usd, 2)}
                                            if _mc_home_jur else None,
                                            {"jurisdiction_id": str(partner_jur.id), "shoot_pct": 0,
                                             "budget_pct": round(100 * _mc_by_jur.get(partner_code, 0.0) / inputs.gross_budget_usd, 2)}
                                            if partner_jur else None,
                                            {"jurisdiction_id": str(_mc_target_a_jur.id), "shoot_pct": 0,
                                             "budget_pct": round(100 * _mc_by_jur.get(_mc_target_a.jurisdiction_code, 0.0) / inputs.gross_budget_usd, 2)}
                                            if _mc_target_a_jur else None,
                                            {"jurisdiction_id": str(_mc_target_b_jur.id), "shoot_pct": 0,
                                             "budget_pct": round(100 * _mc_by_jur.get(_mc_target_b.jurisdiction_code, 0.0) / inputs.gross_budget_usd, 2)}
                                            if _mc_target_b_jur else None,
                                        ) if j
                                    ],
                                    claimed_program_ids=_mc_claimed_programs,
                                )
                                session.add(_mc_structure)
                                await session.flush()
                                _mc_conditional_program_dicts, _mc_conditional_compatibility_dict = _conditional_data(
                                    str(_mc_structure.id), home_code, tuple(_mc_claimed_programs),
                                )
                                session.add(StructureCalculationResult(
                                    id=uuid.uuid4(), structure_id=_mc_structure.id, engine_version=ENGINE_VERSION,
                                    total_budget_usd=inputs.gross_budget_usd,
                                    total_incentive_value_usd=_mc_pricing.selected_incentive_usd,
                                    true_net_cost_usd=_mc_pricing.npc_verified_usd,
                                    risk_adjusted_net_cost_usd=_mc_pricing.npc_with_adjustments_usd,
                                    has_unverified_inputs=True,
                                    warnings=[
                                        LIMITATION_NOTE,
                                        "Combined co-production + TWO simultaneous movable-component "
                                        "candidate: a new, additive structure topology -- not directly "
                                        "comparable to single-component combined structures' own NPC "
                                        "without confirming the same normalization basis.",
                                    ],
                                    structure_type="hybrid",
                                    calculation_trace_json={
                                        "candidate_status": STATUS_PRICED,
                                        "discovery_classification": "combined_coproduction_multi_component_stack",
                                        "structural_family": "combined_coproduction_multi_component_stack",
                                        "structure_type": "hybrid",
                                        "primary_jurisdiction": home_code,
                                        "treaty_slug": comb_opp.treaty_slug,
                                        "program_slugs": _mc_claimed_programs,
                                        "is_baseline": False, "relocation_cost_normalized": False,
                                        "is_directly_comparable": False,
                                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                                        "coproduction_partners": [
                                            {"jurisdiction_code": home_code, "allocated_usd": _mc_by_jur.get(home_code, 0.0)},
                                            {"jurisdiction_code": partner_code, "allocated_usd": _mc_by_jur.get(partner_code, 0.0)},
                                        ],
                                        "component_allocations": [
                                            {
                                                "component": _mc_comp_a,
                                                "jurisdiction_code": _mc_target_a.jurisdiction_code,
                                                "program_slug": _mc_target_a.program_slug,
                                                "allocated_usd": _mc_by_jur.get(_mc_target_a.jurisdiction_code, 0.0),
                                            },
                                            {
                                                "component": _mc_comp_b,
                                                "jurisdiction_code": _mc_target_b.jurisdiction_code,
                                                "program_slug": _mc_target_b.program_slug,
                                                "allocated_usd": _mc_by_jur.get(_mc_target_b.jurisdiction_code, 0.0),
                                            },
                                        ],
                                        "selected_incentive_usd": _mc_pricing.selected_incentive_usd,
                                        "npc_verified_usd": _mc_pricing.npc_verified_usd,
                                        "npc_with_adjustments_usd": _mc_pricing.npc_with_adjustments_usd,
                                        "gross_budget_usd": inputs.gross_budget_usd,
                                        "segments": _segment_dicts(_mc_pricing),
                                        "conditional_programs": _mc_conditional_program_dicts,
                                        "conditional_compatibility": _mc_conditional_compatibility_dict,
                                    },
                                    input_fingerprint=fingerprint,
                                ))
                                if _mc_pricing.selected_incentive_usd > _mc_best_total:
                                    _mc_best_total = _mc_pricing.selected_incentive_usd
                                    _mc_incumbent_structure_id = str(_mc_structure.id)
                                    _mc_incumbent_jurisdiction_codes = [
                                        home_code, partner_code,
                                        _mc_target_a.jurisdiction_code, _mc_target_b.jurisdiction_code,
                                    ]
                                    _mc_incumbent_program_slugs = list(_mc_claimed_programs)

                            if _mc_best_total > float("-inf"):
                                # A real, executable combination was found
                                # within this window. By the pigeonhole
                                # exchange argument above (valid at ANY
                                # window >= 2), nothing beyond this window
                                # can beat it either -- stop widening.
                                break
                            _mc_max_len = max(len(_mc_full_a), len(_mc_full_b))
                            if _mc_window >= _mc_max_len:
                                # Every real candidate has been tried for
                                # this component pair and nothing executable
                                # exists -- a genuine real result (every
                                # individual attempt already has its own
                                # persisted RULE_REJECTED/etc. disposition
                                # above), not a completeness gap.
                                break
                            _mc_window = min(_mc_window * 2, _mc_max_len)

                        if _mc_best_total > float("-inf"):
                            _mc_total_possible = len(_mc_full_a) * len(_mc_full_b)
                            _mc_remaining = _mc_total_possible - len(_mc_tried_pairs)
                            if _mc_remaining > 0:
                                # NUM-004: same numeric-proof enrichment as
                                # the ordinary_component_hybrid DOMINATED_
                                # WITH_PROOF site above, adapted to this
                                # search's own fixed 2-component (a, b)
                                # shape -- see that site's own comment for
                                # the full definitions. Does not alter the
                                # widening/stop decision above in any way.
                                _mc_cutoff_a = (
                                    round(_mc_full_a[_mc_window].selected_incentive_usd, 2)
                                    if _mc_window < len(_mc_full_a) else None
                                )
                                _mc_cutoff_b = (
                                    round(_mc_full_b[_mc_window].selected_incentive_usd, 2)
                                    if _mc_window < len(_mc_full_b) else None
                                )
                                _mc_best_a = round(_mc_full_a[0].selected_incentive_usd, 2) if _mc_full_a else 0.0
                                _mc_best_b = round(_mc_full_b[0].selected_incentive_usd, 2) if _mc_full_b else 0.0
                                _mc_sum_window_best = round(_mc_best_a + _mc_best_b, 2)
                                _mc_swap_bounds = []
                                if _mc_cutoff_a is not None:
                                    _mc_swap_bounds.append(round(_mc_sum_window_best - _mc_best_a + _mc_cutoff_a, 2))
                                if _mc_cutoff_b is not None:
                                    _mc_swap_bounds.append(round(_mc_sum_window_best - _mc_best_b + _mc_cutoff_b, 2))
                                _mc_interaction_safe_total_upper_bound_usd = max(_mc_swap_bounds) if _mc_swap_bounds else None
                                _mc_incumbent_value_usd = round(_mc_best_total, 2)
                                _mc_stopping_inequality_holds = (
                                    True if _mc_interaction_safe_total_upper_bound_usd is None
                                    else _mc_interaction_safe_total_upper_bound_usd <= _mc_incumbent_value_usd
                                )
                                # Genuine mathematical proof (pigeonhole
                                # exchange argument, valid at the window
                                # size actually reached), not a search-
                                # depth admission: every (target_a,
                                # target_b) pair beyond this window is
                                # provably incapable of improving on the
                                # found, real, executable total.
                                _mc_dom_structure_id = uuid.uuid4()
                                session.add(ProductionStructure(
                                    id=_mc_dom_structure_id, project_id=project.id,
                                    name=(
                                        f"{home_code} + {partner_code} co-production ({comb_opp.treaty_slug}) "
                                        f"{_mc_comp_a}/{_mc_comp_b} multi-component search "
                                        f"({_mc_remaining} combinations proven dominated)"
                                    ),
                                    description=(
                                        f"Branch-and-bound over {_mc_comp_a}/{_mc_comp_b} simultaneous "
                                        f"routing (home={home_code}, partner={partner_code}) found a real, "
                                        f"executable total of ${_mc_best_total:,.2f} within a window of "
                                        f"{_mc_window} candidate(s) per component. By a pigeonhole exchange "
                                        "argument (2 simultaneously-routed components, no candidate ranked "
                                        f"below its own component's top {_mc_window} can ever be part of the "
                                        f"true optimum), the remaining {_mc_remaining} combination(s) across "
                                        "every larger-window possibility are provably incapable of beating "
                                        "this real result."
                                    ),
                                    jurisdiction_allocations=[], claimed_program_ids=[],
                                ))
                                session.add(StructureCalculationResult(
                                    id=uuid.uuid4(), structure_id=_mc_dom_structure_id, engine_version=ENGINE_VERSION,
                                    total_budget_usd=inputs.gross_budget_usd,
                                    total_incentive_value_usd=None, true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                    structure_type="hybrid",
                                    calculation_trace_json={
                                        "candidate_status": "DOMINATED_WITH_PROOF",
                                        "discovery_classification": "combined_coproduction_multi_component_stack",
                                        "structural_family": "combined_coproduction_multi_component_stack",
                                        "discovery_method": "pigeonhole_windowed_branch_and_bound",
                                        "structure_type": "hybrid",
                                        "primary_jurisdiction": home_code,
                                        "treaty_slug": comb_opp.treaty_slug,
                                        "component_subset": [_mc_comp_a, _mc_comp_b],
                                        "is_baseline": False, "relocation_cost_normalized": False,
                                        "is_directly_comparable": False,
                                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                                        "dominated_combination_count": _mc_remaining,
                                        "proof_window_size": _mc_window,
                                        "best_real_total_found_usd": round(_mc_best_total, 2),
                                        "incumbent_structure_id": _mc_incumbent_structure_id,
                                        "incumbent_jurisdiction_codes": _mc_incumbent_jurisdiction_codes,
                                        "incumbent_program_slugs": _mc_incumbent_program_slugs,
                                        "proof_type": "pigeonhole_membership_exchange_argument",
                                        "ordering_key": (
                                            "descending real, independently-priced marginal incentive value "
                                            "of the target jurisdiction's own segment for this component "
                                            "(_hy_component_all_targets, computed once per component and "
                                            "reused across every anchor/partner)"
                                        ),
                                        "component_target_windows": {
                                            _mc_comp_a: [
                                                {
                                                    "jurisdiction_code": _t.jurisdiction_code,
                                                    "program_slug": _t.program_slug,
                                                    "marginal_value_usd": round(_t.selected_incentive_usd, 2),
                                                }
                                                for _t in _mc_lists_a
                                            ],
                                            _mc_comp_b: [
                                                {
                                                    "jurisdiction_code": _t.jurisdiction_code,
                                                    "program_slug": _t.program_slug,
                                                    "marginal_value_usd": round(_t.selected_incentive_usd, 2),
                                                }
                                                for _t in _mc_lists_b
                                            ],
                                        },
                                        # NUM-004: the numeric proof itself.
                                        "incumbent_value_usd": _mc_incumbent_value_usd,
                                        "component_cutoff_bounds_usd": {
                                            _mc_comp_a: _mc_cutoff_a, _mc_comp_b: _mc_cutoff_b,
                                        },
                                        "component_window_best_usd": {
                                            _mc_comp_a: _mc_best_a, _mc_comp_b: _mc_best_b,
                                        },
                                        "interaction_safe_total_upper_bound_usd": _mc_interaction_safe_total_upper_bound_usd,
                                        "stopping_inequality_holds": _mc_stopping_inequality_holds,
                                        "stopping_inequality": (
                                            "interaction_safe_total_upper_bound_usd <= incumbent_value_usd"
                                            if _mc_interaction_safe_total_upper_bound_usd is not None
                                            else "no component has a candidate outside its own window -- proof "
                                                 "complete by exhaustion, no substitution bound is needed"
                                        ),
                                        "engine_version": ENGINE_VERSION,
                                        "input_fingerprint": fingerprint,
                                        "reason": (
                                            "Pigeonhole exchange proof: with 2 simultaneously-routed "
                                            f"components, no candidate ranked below its own component's top "
                                            f"{_mc_window} can be part of the true optimum, given a real, "
                                            "executable result was already found using only the top-window "
                                            "candidates."
                                        ),
                                    },
                                    input_fingerprint=fingerprint,
                                ))


        # Eight-control closeout, multi-principal composition (REG-4;
        # HO-003/007/013's own pairwise leg). A PURE two-party
        # co-production -- home_code + partner_code ONLY, no third
        # movable component -- is a genuinely distinct real candidate
        # from the combined_coproduction_component_stack block above
        # (which requires _combined_components to be non-empty and
        # always claims a third program). Gated only on
        # RESOLUTION_ELIGIBLE + a real, positive, evidenced contribution
        # fact pair -- never on whether the production happens to have
        # movable post/vfx/music spend. Two simultaneous
        # principal_production legs is exactly the shape
        # structural_archetype_generator.py's own generate_
        # structural_candidate already accepts (HO-003's own
        # direct-generator test) -- this is the missing REAL-runtime
        # allocation source for that shape, reusing the SAME real,
        # evidenced majority_pct/minority_pct treaty facts the three-way
        # block above already fetched for this exact iteration, never a
        # second, divergent fact read. Does not (this pass) layer
        # authorized-local-stack composition onto either side -- a real,
        # disclosed scope reduction from the three-way block's own
        # richer treatment, not a silent omission.
        if opp.resolution_state == RESOLUTION_ELIGIBLE:
            # Eight-control closeout, HO-003/REG-4 discovery-
            # suppression fix: same Locked Structural Policy doctrine
            # as the three-way block above -- every treaty-valid,
            # independently-priceable partner program is tried and
            # persisted, never narrowed to a single "best" one before
            # persistence.
            _pair_candidates = _all_priced_treaty_side_candidates(
                inputs, partner_code, priced_by_code,
                tuple(_treaty_row.minority_unlocks) if _treaty_row else (),
            )
            if not _pair_candidates:
                _pair_claimed_programs = [home_program_slug, partner_code]
                _pair_invalid_structure = ProductionStructure(
                    id=uuid.uuid4(), project_id=project.id,
                    name=f"{home_code} + {partner_code} co-production ({opp.treaty_slug}, pair, rejected)",
                    description=(
                        f"Combined pair candidate rejected: {partner_code} has no "
                        f"independently-priceable program available under {opp.treaty_slug}'s "
                        "minority_unlocks -- a claimed participant must have a real, priceable "
                        "program, never an assumed one."
                    ),
                    jurisdiction_allocations=[], claimed_program_ids=_pair_claimed_programs,
                )
                session.add(_pair_invalid_structure)
                await session.flush()
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=_pair_invalid_structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                    structure_type="hybrid",
                    calculation_trace_json={
                        "candidate_status": "RULE_REJECTED",
                        "rejection_reason_class": "INVALID_COMBINED_ALLOCATION",
                        "discovery_classification": "combined_coproduction_pair_stack",
                        "structural_family": "combined_coproduction_pair_stack",
                        "structure_type": "hybrid",
                        "primary_jurisdiction": home_code,
                        "treaty_slug": opp.treaty_slug,
                        "program_slugs": _pair_claimed_programs,
                        "reason": (
                            f"{partner_code} has no independently-priceable program available "
                            f"under {opp.treaty_slug}'s minority_unlocks -- a claimed participant "
                            "must have a real, priceable program, never an assumed one."
                        ),
                        "is_baseline": False, "relocation_cost_normalized": False,
                        "is_directly_comparable": False,
                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                    },
                    input_fingerprint=fingerprint,
                ))
            for _pair_partner_best in _pair_candidates:
                _pair_claimed_programs = [home_program_slug, _pair_partner_best.program_slug]
                try:
                    _pair_spec, _pair_allocation, _pair_pricing = _price_combined_coproduction_pair_candidate(
                        inputs, home_code, home_program_slug, partner_code, _pair_partner_best.program_slug,
                        opp.treaty_slug, _bp_majority_pct, _bp_minority_pct,
                    )
                except _InvalidCombinedAllocation as _pair_invalid:
                    _pair_invalid_structure = ProductionStructure(
                        id=uuid.uuid4(), project_id=project.id,
                        name=f"{home_code} + {partner_code} co-production ({opp.treaty_slug}, pair, rejected)",
                        description=f"Combined pair candidate rejected: {_pair_invalid.reason}",
                        jurisdiction_allocations=[], claimed_program_ids=_pair_claimed_programs,
                    )
                    session.add(_pair_invalid_structure)
                    await session.flush()
                    session.add(StructureCalculationResult(
                        id=uuid.uuid4(), structure_id=_pair_invalid_structure.id, engine_version=ENGINE_VERSION,
                        total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                        true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                        has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                        structure_type="hybrid",
                        calculation_trace_json={
                            "candidate_status": "RULE_REJECTED",
                            "rejection_reason_class": "INVALID_COMBINED_ALLOCATION",
                            "discovery_classification": "combined_coproduction_pair_stack",
                            "structural_family": "combined_coproduction_pair_stack",
                            "structure_type": "hybrid",
                            "primary_jurisdiction": home_code,
                            "treaty_slug": opp.treaty_slug,
                            "program_slugs": _pair_claimed_programs,
                            "reason": _pair_invalid.reason,
                            "is_baseline": False, "relocation_cost_normalized": False,
                            "is_directly_comparable": False,
                            "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                        },
                        input_fingerprint=fingerprint,
                    ))
                else:
                    if not _pair_pricing.is_fully_priced:
                        _pair_rej_status, _pair_rej_class = _classify_component_rejection(_pair_pricing.blockers)
                        _pair_rej_structure = ProductionStructure(
                            id=uuid.uuid4(), project_id=project.id,
                            name=f"{home_code} + {partner_code} co-production ({opp.treaty_slug}, pair, rejected)",
                            description=(
                                "Pure two-party co-production candidate does not clear pricing: "
                                f"{'; '.join(_pair_pricing.blockers) or 'not fully priced.'}"
                            ),
                            jurisdiction_allocations=[], claimed_program_ids=_pair_claimed_programs,
                        )
                        session.add(_pair_rej_structure)
                        await session.flush()
                        session.add(StructureCalculationResult(
                            id=uuid.uuid4(), structure_id=_pair_rej_structure.id, engine_version=ENGINE_VERSION,
                            total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                            true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                            has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                            structure_type="hybrid",
                            calculation_trace_json={
                                "candidate_status": _pair_rej_status,
                                "rejection_reason_class": _pair_rej_class,
                                "discovery_classification": "combined_coproduction_pair_stack",
                                "structural_family": "combined_coproduction_pair_stack",
                                "structure_type": "hybrid",
                                "primary_jurisdiction": home_code,
                                "treaty_slug": opp.treaty_slug,
                                "program_slugs": _pair_claimed_programs,
                                "reason": "; ".join(_pair_pricing.blockers) or "Not fully priced.",
                                "is_baseline": False, "relocation_cost_normalized": False,
                                "is_directly_comparable": False,
                                "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                            },
                            input_fingerprint=fingerprint,
                        ))
                    else:
                        _pair_home_jur = jurisdiction_by_code.get(home_code)
                        _pair_by_jur = _pair_allocation.allocated_by_jurisdiction()
                        _pair_structure = ProductionStructure(
                            id=uuid.uuid4(), project_id=project.id,
                            name=f"{home_code} + {partner_code} co-production ({opp.treaty_slug})",
                            description=(
                                f"Official co-production between {home_code} (anchor) and {partner_code} "
                                f"under {opp.treaty_slug}, allocated by each party's real evidenced "
                                "contribution share (no third movable component routed)."
                            ),
                            jurisdiction_allocations=[
                                j for j in (
                                    {"jurisdiction_id": str(_pair_home_jur.id), "shoot_pct": 100,
                                     "budget_pct": round(100 * _pair_by_jur.get(home_code, 0.0) / inputs.gross_budget_usd, 2)}
                                    if _pair_home_jur else None,
                                    {"jurisdiction_id": str(partner_jur.id), "shoot_pct": 0,
                                     "budget_pct": round(100 * _pair_by_jur.get(partner_code, 0.0) / inputs.gross_budget_usd, 2)}
                                    if partner_jur else None,
                                ) if j
                            ],
                            claimed_program_ids=_pair_claimed_programs,
                        )
                        session.add(_pair_structure)
                        await session.flush()
                        _pair_conditional_program_dicts, _pair_conditional_compatibility_dict = _conditional_data(
                            str(_pair_structure.id), home_code, tuple(_pair_claimed_programs),
                        )
                        session.add(StructureCalculationResult(
                            id=uuid.uuid4(), structure_id=_pair_structure.id, engine_version=ENGINE_VERSION,
                            total_budget_usd=inputs.gross_budget_usd,
                            total_incentive_value_usd=_pair_pricing.selected_incentive_usd,
                            true_net_cost_usd=_pair_pricing.npc_verified_usd,
                            risk_adjusted_net_cost_usd=_pair_pricing.npc_with_adjustments_usd,
                            has_unverified_inputs=True,
                            warnings=[
                                LIMITATION_NOTE,
                                "Pure two-party official co-production candidate: a new, additive "
                                "structure topology (no third movable component routed, no "
                                "same-jurisdiction local stacking layered on either side this pass) "
                                "-- not directly comparable to single-leg or three-way combined "
                                "structures' own NPC without confirming the same normalization basis.",
                            ],
                            structure_type="hybrid",
                            calculation_trace_json={
                                "candidate_status": STATUS_PRICED,
                                "discovery_classification": "combined_coproduction_pair_stack",
                                "structural_family": "combined_coproduction_pair_stack",
                                "structure_type": "hybrid",
                                "primary_jurisdiction": home_code,
                                "treaty_slug": opp.treaty_slug,
                                "program_slugs": _pair_claimed_programs,
                                "is_baseline": False, "relocation_cost_normalized": False,
                                "is_directly_comparable": False,
                                "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                                "coproduction_partners": [
                                    {
                                        "jurisdiction_code": home_code,
                                        "jurisdiction_display_name": _pair_home_jur.name if _pair_home_jur else home_code,
                                        "allocated_usd": _pair_by_jur.get(home_code, 0.0),
                                    },
                                    {
                                        "jurisdiction_code": partner_code,
                                        "jurisdiction_display_name": partner_jur.name if partner_jur else partner_code,
                                        "allocated_usd": _pair_by_jur.get(partner_code, 0.0),
                                    },
                                ],
                                "treaty_resolution_state": opp.resolution_state,
                                "selected_incentive_usd": _pair_pricing.selected_incentive_usd,
                                "npc_verified_usd": _pair_pricing.npc_verified_usd,
                                "npc_with_adjustments_usd": _pair_pricing.npc_with_adjustments_usd,
                                "gross_budget_usd": inputs.gross_budget_usd,
                                "segments": _segment_dicts(_pair_pricing),
                                "conditional_programs": _pair_conditional_program_dicts,
                                "conditional_compatibility": _pair_conditional_compatibility_dict,
                            },
                            input_fingerprint=fingerprint,
                        ))

    # LU Co-Pro Opportunity Trace fix — a real, generic wiring gap: the
    # loop above only ever considers a bilateral treaty where the
    # production's own home/service jurisdiction (Mauritius for LU) is
    # one of the two parties. CineGlobe is production-centric, not
    # current-jurisdiction-centric — a real registered treaty between two
    # OTHER genuine candidate jurisdictions (e.g. AU/GB, both already
    # independently discovered as relocation candidates for LU, and
    # matching this production's own director/writer nationalities) is a
    # real structuring opportunity even when the shoot/service location
    # is a third country, party to neither treaty. Same fail-closed
    # adapter, same disclosure shape as the home-anchored loop above —
    # only the PAIR SELECTION is generalized, never the eligibility logic.
    # Deduplication against the home-anchored loop above is structural,
    # not a separate tracking set: any pair where home_code IS one of the
    # two parties is explicitly skipped below (`continue`), and that is
    # exactly the only case the home-anchored loop could have already
    # reported — so no treaty_slug can ever be reported by both loops.
    for majority_code, minority_code, treaty_slug in find_bilateral_treaty_pairs_among_candidates(candidate_codes):
        if home_code in (majority_code, minority_code):
            continue  # already covered by the home-anchored loop above
        # P0-QUAL-001: treaty_slug is already known here (returned directly
        # by find_bilateral_treaty_pairs_among_candidates), so facts are
        # fetched scoped to this treaty and this ordered
        # (majority_code, minority_code) participant pair -- no pre-lookup
        # needed, unlike the home-anchored loop above.
        _nb_majority_pct, _nb_minority_pct, _nb_cultural_test_passed = await _coproduction_facts(
            session, project.id, treaty_slug, (majority_code, minority_code),
        )
        # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING: same
        # additive personnel gate as the home-anchored loop above.
        _nb_treaty_row = te.get_bilateral_treaty(majority_code, minority_code)
        opp = evaluate_bilateral_coproduction_opportunity(
            majority_code, minority_code,
            majority_pct=_nb_majority_pct, minority_pct=_nb_minority_pct,
            cultural_test_passed=_nb_cultural_test_passed,
            personnel_requirement=_nb_treaty_row.personnel_requirement if _nb_treaty_row else None,
            personnel_attachment_facts=role_attachment_facts,
        )
        if opp is None:
            continue
        majority_jur = jurisdiction_by_code.get(majority_code)
        minority_jur = jurisdiction_by_code.get(minority_code)
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=f"{majority_code} + {minority_code} — official co-production opportunity ({opp.treaty_slug})",
            description=(
                f"A registered bilateral co-production treaty ({opp.treaty_slug}) exists "
                f"between {majority_code} and {minority_code} — both independently "
                f"discovered as real candidate jurisdictions for this production, neither "
                f"of which is the production's current service/location jurisdiction "
                f"({home_code}). The legal/creative co-production structure and the "
                f"physical production/service location are separate dimensions: this "
                f"structure can potentially compose with a {home_code} service/location "
                "component rather than replacing it. Real ownership/spend-share and "
                "cultural-test facts are required to resolve eligibility — not yet on "
                "file for this project."
            ),
            jurisdiction_allocations=[],
            claimed_program_ids=[],
        )
        session.add(structure)
        await session.flush()
        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), majority_code, (),
        )
        # Co-Pro Conditional Pricing Bridge — same rule as the home-anchored
        # loop above: only for UNRESOLVED_FACTS, purely additive disclosure.
        # Compared against the production's own current home-jurisdiction
        # incentive even though neither treaty party IS home_code — the
        # comparison is "this hypothetical structure vs. what the
        # production currently gets", not "vs. one of these two countries".
        _conditional_scenario = None
        if opp.resolution_state == "UNRESOLVED_FACTS":
            _home_candidates = priced_by_code.get(home_code) or []
            _baseline_incentive = max(
                (c.selected_incentive_usd for c in _home_candidates), default=None,
            )
            _conditional_scenario = _build_conditional_bilateral_scenario(
                inputs, majority_code, minority_code, opp.treaty_slug, _baseline_incentive,
                personnel_attachment_facts=role_attachment_facts,
            )
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
            true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
            has_unverified_inputs=True,
            warnings=[
                LIMITATION_NOTE,
                "Official co-production opportunity between two candidate jurisdictions "
                f"neither of which is {home_code} (this production's current service/"
                "location jurisdiction) — real ownership/cultural-test facts are not yet "
                "on file; not priced as qualified economics. Registry presence is real "
                "and disclosed; it is never reported as resolved eligibility.",
            ],
            structure_type="treaty_coproduction",
            calculation_trace_json={
                "candidate_status": STATUS_CO_PRO_OPPORTUNITY,
                "discovery_classification": "treaty_coproduction",
                "structure_type": "treaty_coproduction",
                "primary_jurisdiction": home_code,
                "is_baseline": False,
                "relocation_cost_normalized": False,
                "is_directly_comparable": False,
                "treaty_slug": opp.treaty_slug,
                "conditional_programs": _conditional_program_dicts,
                "conditional_compatibility": _conditional_compatibility_dict,
                "coproduction_partners": [
                    {"jurisdiction_code": majority_code, "jurisdiction_display_name": majority_jur.name if majority_jur else majority_code},
                    {"jurisdiction_code": minority_code, "jurisdiction_display_name": minority_jur.name if minority_jur else minority_code},
                ],
                "treaty_resolution_state": opp.resolution_state,
                "treaty_cultural_test_required": opp.cultural_test_required,
                "treaty_cultural_test_resolved": opp.cultural_test_resolved,
                "treaty_disqualification_reasons": list(opp.disqualification_reasons),
                # COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION —
                # by construction of this loop (`if home_code in
                # (majority_code, minority_code): continue` above), home_code
                # is NEVER one of this treaty's own real parties -- this is
                # a genuinely, globally registered bilateral treaty between
                # two OTHER real countries, surfaced as a combined-structure
                # building block, never as a claim that THIS project is
                # itself compatible with it. project_anchored is always
                # False here; opportunity_relevance is therefore always
                # AVAILABLE (a legally modeled capability, not yet tied to
                # this project), never CONDITIONAL/EXECUTABLE/COMPATIBLE,
                # regardless of whether the conditional-pricing scenario
                # below happens to solve a modeled split.
                "opportunity_inclusion_source": "global_bilateral_treaty_registry_enumeration",
                "project_anchored": False,
                "opportunity_relevance": _classify_opportunity_relevance(
                    opp.resolution_state, _conditional_scenario, False,
                    personnel_gate_state=opp.personnel_gate_state,
                ),
                # personnel_gate_state is NOT_APPLICABLE (never blocking,
                # and not an open data question on this project) for
                # every treaty whose own registry entry carries no
                # researched personnel_requirement at all.
                "personnel_gate_state": opp.personnel_gate_state,
                "personnel_satisfied_requirements": list(opp.personnel_satisfied_requirements),
                "personnel_failed_requirements": list(opp.personnel_failed_requirements),
                "personnel_missing_facts": list(opp.personnel_missing_facts),
                "personnel_curable_levers": list(opp.personnel_curable_levers),
                "personnel_next_question": opp.personnel_next_question,
                "reason": "; ".join(opp.notes) or "Real ownership/cultural facts required to resolve eligibility.",
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
                "location_independent_of_service_jurisdiction": True,
                "conditional_scenario": _conditional_scenario,
            },
            input_fingerprint=fingerprint,
        ))

        # Codex D743 rejected-findings remediation (real-treaty proof
        # requirement): P0-COMB-001's combined co-production + component
        # + authorized-local-stack topology is ALSO exercised here, in
        # the non-home-anchored bilateral loop -- a genuinely real
        # registered treaty between two candidate jurisdictions NEITHER
        # of which is this production's own home/service jurisdiction
        # (e.g. GB+CA's real uk-ca-bilateral treaty for a Greece-anchored
        # production) is exactly the case a Greece-home project can
        # exercise, since Greece itself has zero registered bilateral
        # treaty parties in canonical data (confirmed by exhaustive
        # search of treaty_engine.py's _BILATERAL registry -- Greece's
        # only real treaty-adjacent relationship is Eurimages/European
        # Convention MEMBERSHIP, a multilateral framework this bounded
        # topology does not extend to). Mirrors the home-anchored loop's
        # own combined-topology block exactly, with majority_code/
        # minority_code standing in for home_code/partner_code and the
        # production's real home_code allowed as a valid THIRD component
        # target (the non-home-anchored loop's own existing philosophy:
        # "this structure can potentially compose with a home_code
        # service/location component rather than replacing it").
        if opp.resolution_state == RESOLUTION_ELIGIBLE and _combined_components:
            _nb_comb_opp = opp
            _nb_treaty_row = te.get_bilateral_treaty(majority_code, minority_code)
            _nb_majority_unlocks = tuple(_nb_treaty_row.majority_unlocks) if _nb_treaty_row else ()
            _nb_minority_unlocks = tuple(_nb_treaty_row.minority_unlocks) if _nb_treaty_row else ()
            _nb_targets = [
                t for t in _combined_top_targets
                if t.jurisdiction_code not in (majority_code, minority_code)
            ]
            # Eight-control closeout, HO-003 discovery-suppression
            # fix, mirrored here for the non-home-anchored path (same
            # Locked Structural Policy doctrine -- never just the
            # highest-priced side).
            for _nb_majority_best in _all_priced_treaty_side_candidates(
                inputs, majority_code, priced_by_code, _nb_majority_unlocks,
            ):
                for _nb_minority_best in _all_priced_treaty_side_candidates(
                    inputs, minority_code, priced_by_code, _nb_minority_unlocks,
                ):
                    for _nb_component, _nb_spend_amount in _combined_components:
                        for _nb_target in _nb_targets:
                            if _nb_majority_best is None or _nb_minority_best is None:
                                continue
                            _nb_label = (
                                f"{majority_code} + {minority_code} co-production ({_nb_comb_opp.treaty_slug}) + "
                                f"{_nb_component} routed to {_nb_target.jurisdiction_code}"
                            )
                            _nb_claimed_programs = [
                                _nb_majority_best.program_slug, _nb_minority_best.program_slug, _nb_target.program_slug,
                            ]
                            try:
                                _nb_spec, _nb_allocation, _nb_pricing = _price_combined_coproduction_component_candidate(
                                    inputs, majority_code, _nb_majority_best.program_slug,
                                    minority_code, _nb_minority_best.program_slug,
                                    _nb_target.jurisdiction_code, _nb_target.program_slug,
                                    _nb_component, _nb_comb_opp.treaty_slug,
                                    _nb_majority_pct, _nb_minority_pct,
                                )
                            except _InvalidCombinedAllocation as _nb_invalid:
                                _nb_invalid_structure = ProductionStructure(
                                    id=uuid.uuid4(), project_id=project.id,
                                    name=f"{_nb_label} (combined, rejected)",
                                    description=f"Combined candidate rejected: {_nb_invalid.reason}",
                                    jurisdiction_allocations=[],
                                    claimed_program_ids=_nb_claimed_programs,
                                )
                                session.add(_nb_invalid_structure)
                                await session.flush()
                                session.add(StructureCalculationResult(
                                    id=uuid.uuid4(), structure_id=_nb_invalid_structure.id, engine_version=ENGINE_VERSION,
                                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                    structure_type="hybrid",
                                    calculation_trace_json={
                                        "candidate_status": "RULE_REJECTED",
                                        "rejection_reason_class": "INVALID_COMBINED_ALLOCATION",
                                        "discovery_classification": "combined_coproduction_component_stack",
                                        "structure_type": "hybrid",
                                        "primary_jurisdiction": home_code,
                                        "treaty_slug": _nb_comb_opp.treaty_slug,
                                        "program_slugs": _nb_claimed_programs,
                                        "reason": _nb_invalid.reason,
                                        "is_baseline": False,
                                        "relocation_cost_normalized": False,
                                        "is_directly_comparable": False,
                                        "anchor_jurisdiction": majority_code,
                                        "anchor_program": _nb_majority_best.program_slug,
                                        "coproduction_partners": [
                                            {"jurisdiction_code": majority_code}, {"jurisdiction_code": minority_code},
                                        ],
                                        "component_allocations": [{
                                            "component": _nb_component,
                                            "jurisdiction_code": _nb_target.jurisdiction_code,
                                            "program_slug": _nb_target.program_slug,
                                            "allocated_usd": _nb_spend_amount,
                                        }],
                                    },
                                    input_fingerprint=fingerprint,
                                ))
                                continue

                            if not _nb_pricing.is_fully_priced:
                                _nb_rej_status, _nb_rej_class = _classify_component_rejection(_nb_pricing.blockers)
                                _nb_rej_structure = ProductionStructure(
                                    id=uuid.uuid4(), project_id=project.id,
                                    name=f"{_nb_label} (combined, rejected)",
                                    description=(
                                        "Combined co-production + component-allocation candidate does "
                                        f"not clear pricing: {'; '.join(_nb_pricing.blockers) or 'not fully priced.'}"
                                    ),
                                    jurisdiction_allocations=[],
                                    claimed_program_ids=_nb_claimed_programs,
                                )
                                session.add(_nb_rej_structure)
                                await session.flush()
                                session.add(StructureCalculationResult(
                                    id=uuid.uuid4(), structure_id=_nb_rej_structure.id, engine_version=ENGINE_VERSION,
                                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                    structure_type="hybrid",
                                    calculation_trace_json={
                                        "candidate_status": _nb_rej_status,
                                        "rejection_reason_class": _nb_rej_class,
                                        "discovery_classification": "combined_coproduction_component_stack",
                                        "structure_type": "hybrid",
                                        "primary_jurisdiction": home_code,
                                        "treaty_slug": _nb_comb_opp.treaty_slug,
                                        "program_slugs": _nb_claimed_programs,
                                        "reason": "; ".join(_nb_pricing.blockers) or "Not fully priced.",
                                        "is_baseline": False,
                                        "relocation_cost_normalized": False,
                                        "is_directly_comparable": False,
                                        "anchor_jurisdiction": majority_code,
                                        "anchor_program": _nb_majority_best.program_slug,
                                        "coproduction_partners": [
                                            {"jurisdiction_code": majority_code}, {"jurisdiction_code": minority_code},
                                        ],
                                        "component_allocations": [{
                                            "component": _nb_component,
                                            "jurisdiction_code": _nb_target.jurisdiction_code,
                                            "program_slug": _nb_target.program_slug,
                                            "allocated_usd": _nb_spend_amount,
                                        }],
                                    },
                                    input_fingerprint=fingerprint,
                                ))
                                continue

                            _nb_sides = [
                                (majority_code, _nb_majority_best.program_slug),
                                (minority_code, _nb_minority_best.program_slug),
                                (_nb_target.jurisdiction_code, _nb_target.program_slug),
                            ]
                            _nb_stack_delta, _nb_stack_notes, _nb_stack_program_slugs, _nb_unresolved = (
                                _apply_authorized_stacks_to_combined_sides(priced_by_code, _nb_sides)
                            )
                            _nb_selected_incentive = round(_nb_pricing.selected_incentive_usd + _nb_stack_delta, 2)
                            _nb_npc = _nb_pricing.npc_with_adjustments_usd
                            if _nb_npc is not None:
                                _nb_npc = round(_nb_npc - _nb_stack_delta, 2)
                            _nb_stacking_note = " ".join(_nb_stack_notes)

                            for _nb_unresolved_side, _nb_unresolved_group in _nb_unresolved:
                                _nb_stack_rej_structure = ProductionStructure(
                                    id=uuid.uuid4(), project_id=project.id,
                                    name=f"{_nb_label} + unresolved local stack ({_nb_unresolved_side}, rejected)",
                                    description=(
                                        f"{_nb_unresolved_side} has a second same-jurisdiction candidate "
                                        f"program ({[c.program_slug for c in _nb_unresolved_group]}) but "
                                        "no named, publishable stacking rule covers this exact "
                                        "combination — withheld, never summed as though independent."
                                    ),
                                    jurisdiction_allocations=[],
                                    claimed_program_ids=_nb_claimed_programs + [
                                        c.program_slug for c in _nb_unresolved_group
                                    ],
                                )
                                session.add(_nb_stack_rej_structure)
                                await session.flush()
                                session.add(StructureCalculationResult(
                                    id=uuid.uuid4(), structure_id=_nb_stack_rej_structure.id,
                                    engine_version=ENGINE_VERSION,
                                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                                    structure_type="hybrid",
                                    calculation_trace_json={
                                        "candidate_status": "RULE_DATA_INCOMPLETE",
                                        "rejection_reason_class": "RULE_DATA_INCOMPLETE",
                                        "discovery_classification": "combined_coproduction_component_stack",
                                        "structure_type": "hybrid",
                                        "primary_jurisdiction": home_code,
                                        "treaty_slug": _nb_comb_opp.treaty_slug,
                                        "program_slugs": _nb_claimed_programs + [
                                            c.program_slug for c in _nb_unresolved_group
                                        ],
                                        "reason": (
                                            "No named, publishable stacking rule covers "
                                            f"{_nb_unresolved_side}: "
                                            f"{'+'.join(c.program_slug for c in _nb_unresolved_group)}."
                                        ),
                                        "is_baseline": False,
                                        "relocation_cost_normalized": False,
                                        "is_directly_comparable": False,
                                        "anchor_jurisdiction": majority_code,
                                        "anchor_program": _nb_majority_best.program_slug,
                                    },
                                    input_fingerprint=fingerprint,
                                ))

                            _nb_majority_jur = jurisdiction_by_code.get(majority_code)
                            _nb_minority_jur = jurisdiction_by_code.get(minority_code)
                            _nb_target_jur = jurisdiction_by_code.get(_nb_target.jurisdiction_code)
                            _nb_by_jur = _nb_allocation.allocated_by_jurisdiction()
                            _nb_structure = ProductionStructure(
                                id=uuid.uuid4(), project_id=project.id,
                                name=_nb_label,
                                description=(
                                    f"Official co-production between {majority_code} and {minority_code} "
                                    f"under {_nb_comb_opp.treaty_slug} (neither party is this production's "
                                    f"current home/service jurisdiction {home_code}), allocated by each "
                                    f"party's real evidenced contribution share, with {_nb_component} work "
                                    f"(${_nb_spend_amount:,.0f} of real project budget) routed to "
                                    f"{_nb_target.jurisdiction_code} to claim "
                                    f"{_program_display_name(_nb_target.program_slug)}."
                                    + (f" {_nb_stacking_note}" if _nb_stacking_note else "")
                                ),
                                jurisdiction_allocations=[
                                    j for j in (
                                        {"jurisdiction_id": str(_nb_majority_jur.id), "shoot_pct": 0,
                                         "budget_pct": round(100 * _nb_by_jur.get(majority_code, 0.0) / inputs.gross_budget_usd, 2)}
                                        if _nb_majority_jur else None,
                                        {"jurisdiction_id": str(_nb_minority_jur.id), "shoot_pct": 0,
                                         "budget_pct": round(100 * _nb_by_jur.get(minority_code, 0.0) / inputs.gross_budget_usd, 2)}
                                        if _nb_minority_jur else None,
                                        {"jurisdiction_id": str(_nb_target_jur.id), "shoot_pct": 0,
                                         "budget_pct": round(100 * _nb_by_jur.get(_nb_target.jurisdiction_code, 0.0) / inputs.gross_budget_usd, 2)}
                                        if _nb_target_jur else None,
                                    ) if j
                                ],
                                claimed_program_ids=_nb_claimed_programs + _nb_stack_program_slugs,
                            )
                            session.add(_nb_structure)
                            await session.flush()
                            _nb_conditional_program_dicts, _nb_conditional_compatibility_dict = _conditional_data(
                                str(_nb_structure.id), majority_code, tuple(_nb_claimed_programs),
                            )
                            session.add(StructureCalculationResult(
                                id=uuid.uuid4(), structure_id=_nb_structure.id, engine_version=ENGINE_VERSION,
                                total_budget_usd=inputs.gross_budget_usd,
                                total_incentive_value_usd=_nb_selected_incentive,
                                true_net_cost_usd=_nb_pricing.npc_verified_usd,
                                risk_adjusted_net_cost_usd=_nb_npc,
                                has_unverified_inputs=True,
                                warnings=[
                                    LIMITATION_NOTE,
                                    "Combined co-production + component-allocation + authorized-stack "
                                    "candidate (non-home-anchored): a new, additive structure topology — "
                                    "not directly comparable to single-leg structures' own NPC without "
                                    "confirming the same normalization basis.",
                                ] + _nb_stack_notes,
                                structure_type="hybrid",
                                calculation_trace_json={
                                    "candidate_status": STATUS_PRICED,
                                    "discovery_classification": "combined_coproduction_component_stack",
                                    "structure_type": "hybrid",
                                    "primary_jurisdiction": home_code,
                                    "treaty_slug": _nb_comb_opp.treaty_slug,
                                    "program_slugs": _nb_claimed_programs + _nb_stack_program_slugs,
                                    "is_baseline": False,
                                    "relocation_cost_normalized": False,
                                    "is_directly_comparable": False,
                                    "anchor_jurisdiction": majority_code,
                                    "anchor_program": _nb_majority_best.program_slug,
                                    "coproduction_partners": [
                                        {
                                            "jurisdiction_code": majority_code,
                                            "jurisdiction_display_name": _nb_majority_jur.name if _nb_majority_jur else majority_code,
                                            "allocated_usd": _nb_by_jur.get(majority_code, 0.0),
                                        },
                                        {
                                            "jurisdiction_code": minority_code,
                                            "jurisdiction_display_name": _nb_minority_jur.name if _nb_minority_jur else minority_code,
                                            "allocated_usd": _nb_by_jur.get(minority_code, 0.0),
                                        },
                                    ],
                                    "treaty_resolution_state": _nb_comb_opp.resolution_state,
                                    "component_allocations": [{
                                        "component": _nb_component,
                                        "jurisdiction_code": _nb_target.jurisdiction_code,
                                        "jurisdiction_display_name": _nb_target_jur.name if _nb_target_jur else _nb_target.jurisdiction_code,
                                        "program_slug": _nb_target.program_slug,
                                        "allocated_usd": _nb_by_jur.get(_nb_target.jurisdiction_code, 0.0),
                                    }],
                                    "stacking_note": _nb_stacking_note,
                                    "stacked_programs": _nb_stack_program_slugs,
                                    "selected_incentive_usd": _nb_selected_incentive,
                                    "npc_verified_usd": _nb_pricing.npc_verified_usd,
                                    "npc_with_adjustments_usd": _nb_npc,
                                    "gross_budget_usd": inputs.gross_budget_usd,
                                    "segments": _segment_dicts(_nb_pricing),
                                    "conditional_programs": _nb_conditional_program_dicts,
                                    "conditional_compatibility": _nb_conditional_compatibility_dict,
                                },
                                input_fingerprint=fingerprint,
                            ))

    eurimages_partners = find_eurimages_partners(home_code, candidate_codes)
    if eurimages_partners:
        # Codex global optimizer audit, P0-CAND-002: "a presentation
        # bound has become an evaluation bound." MAX_EURIMAGES_DISPLAY
        # now bounds ONLY the served `coproduction_partners` list
        # (`shown`, for display/pagination) — the evaluator itself is
        # called against the FULL, real, discovered `eurimages_partners`
        # set below, so an 11th+ eligible member is genuinely evaluated
        # and accounted for, never silently dropped before eligibility
        # is even asked.
        MAX_EURIMAGES_DISPLAY = 10
        all_partners_sorted = sorted(eurimages_partners)
        shown = all_partners_sorted[:MAX_EURIMAGES_DISPLAY]
        # Canonical Co-production Qualification Reconnection — was
        # previously hardcoded to UNRESOLVED_FACTS/cultural_test_resolved
        # =False regardless of any real fact; now genuinely computed via
        # evaluate_eurimages_coproduction_opportunity() (reused
        # unchanged). With no country_pcts fact on file (true for LU/FVD)
        # this still resolves UNRESOLVED_FACTS — same output, real path.
        # P0-QUAL-001: "eurimages" is a fixed treaty_slug constant (no
        # per-pair ambiguity, unlike bilateral treaties), so facts can be
        # fetched directly scoped to (treaty_slug="eurimages",
        # participant_codes) — the exact ordered set passed to the
        # evaluator below.
        _eurimages_participants = tuple([home_code] + all_partners_sorted)
        _eurimages_country_pcts, _eurimages_cultural_test_passed = await _multilateral_coproduction_facts(
            session, project.id, "eurimages", _eurimages_participants,
        )
        _eurimages_opp = evaluate_eurimages_coproduction_opportunity(
            list(_eurimages_participants), country_pcts=_eurimages_country_pcts,
            cultural_test_passed=_eurimages_cultural_test_passed,
            personnel_attachment_facts=role_attachment_facts,
        )
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=f"{home_code} — Eurimages multilateral co-production opportunity",
            description=(
                f"{home_code} is a Eurimages member. {len(eurimages_partners)} of this "
                "production's own discovered candidate jurisdictions are ALSO Eurimages "
                "members (real membership, via treaty_engine's registry) — a genuine "
                "multilateral co-production pathway. Real per-country budget-share and "
                "cultural-test facts are required to resolve eligibility — not yet on "
                "file for this project."
            ),
            jurisdiction_allocations=[],
            claimed_program_ids=[],
        )
        session.add(structure)
        await session.flush()
        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), home_code, (),
        )
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
            true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
            has_unverified_inputs=True,
            warnings=[
                LIMITATION_NOTE,
                "Eurimages multilateral co-production opportunity — real per-country "
                "budget-share and cultural-test facts are not yet on file; not priced "
                "as qualified economics.",
            ],
            structure_type="treaty_coproduction",
            calculation_trace_json={
                "candidate_status": STATUS_CO_PRO_OPPORTUNITY,
                "discovery_classification": "treaty_coproduction",
                "structure_type": "treaty_coproduction",
                "primary_jurisdiction": home_code,
                "is_baseline": False,
                "relocation_cost_normalized": False,
                "is_directly_comparable": False,
                "treaty_slug": "eurimages",
                "conditional_programs": _conditional_program_dicts,
                "conditional_compatibility": _conditional_compatibility_dict,
                "coproduction_partners": [
                    {
                        "jurisdiction_code": code,
                        "jurisdiction_display_name": (
                            jurisdiction_by_code[code].name if code in jurisdiction_by_code else code
                        ),
                    }
                    for code in shown
                ],
                "treaty_resolution_state": _eurimages_opp.resolution_state if _eurimages_opp else "UNRESOLVED_FACTS",
                "treaty_cultural_test_required": _eurimages_opp.cultural_test_required if _eurimages_opp else True,
                "treaty_cultural_test_resolved": _eurimages_opp.cultural_test_resolved if _eurimages_opp else False,
                "treaty_disqualification_reasons": list(_eurimages_opp.disqualification_reasons) if _eurimages_opp else [],
                # COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION —
                # home_code is always the first element of
                # _eurimages_participants (this project's own jurisdiction
                # IS a real Eurimages member/party here) -- project_anchored
                # is always True for a multilateral opportunity. No
                # conditional-pricing scenario exists for multilateral
                # frameworks (unlike bilateral's _build_conditional_
                # bilateral_scenario), so this resolves CONDITIONAL only if
                # resolution_state is ELIGIBLE (-> EXECUTABLE) or INELIGIBLE
                # (-> EXCLUDED); otherwise AVAILABLE (a real, registered
                # multilateral pathway, not yet tied to a real per-country
                # budget-share fact for this project).
                "opportunity_inclusion_source": "multilateral_membership_registry",
                "project_anchored": True,
                "opportunity_relevance": _classify_opportunity_relevance(
                    _eurimages_opp.resolution_state if _eurimages_opp else "UNRESOLVED_FACTS", None, True,
                ),
                "personnel_gate_state": _eurimages_opp.personnel_gate_state if _eurimages_opp else None,
                "personnel_satisfied_requirements": list(_eurimages_opp.personnel_satisfied_requirements) if _eurimages_opp else [],
                "personnel_failed_requirements": list(_eurimages_opp.personnel_failed_requirements) if _eurimages_opp else [],
                "personnel_missing_facts": list(_eurimages_opp.personnel_missing_facts) if _eurimages_opp else [],
                "personnel_curable_levers": list(_eurimages_opp.personnel_curable_levers) if _eurimages_opp else [],
                "personnel_next_question": _eurimages_opp.personnel_next_question if _eurimages_opp else None,
                "reason": (
                    f"{len(eurimages_partners)} real Eurimages member candidate(s) "
                    "discovered; real budget-share and cultural-test facts required "
                    "to resolve eligibility."
                ),
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
            },
            input_fingerprint=fingerprint,
        ))

        # Eight-control closeout, HO-012: a genuine N-way (N>=3) real
        # multilateral co-production route DOES exist (Eurimages,
        # min_coproducer_countries=3, real 10%/10% thresholds, real IE/
        # FR/GB membership -- confirmed via direct treaty_engine.py
        # query) -- but the EXISTING _eurimages_opp above is scoped to
        # this production's FULL discovered candidate universe (often
        # 30+ real Eurimages members), which would require a real
        # contribution fact for every one of them before ever resolving
        # ELIGIBLE -- impractical for a producer-INTENDED, specific-N-
        # party structure. _real_multilateral_subset_participants reads
        # whichever real, evidenced, treaty-scoped facts are actually on
        # file (never a pre-known participant tuple) and treats THAT
        # asserted, real subset as the candidate structure -- same
        # real-facts-only contract, just not gated on the full candidate
        # universe. Each member's own priced candidates (never just its
        # single best) are tried in full cross-product, each combination
        # attempted and persisted with a real terminal disposition.
        _euri_subset_pcts, _euri_subset_cultural_passed = await _real_multilateral_subset_participants(
            session, project.id, "eurimages", te.is_eurimages_member,
        )
        _euri_treaty_row = te.get_multilateral_treaty("eurimages")
        _euri_min_parties = _euri_treaty_row.min_coproducer_countries if _euri_treaty_row else 2
        _euri_min_pct = (
            min(_euri_treaty_row.majority_min_pct, _euri_treaty_row.minority_min_pct)
            if _euri_treaty_row else 0.0
        )
        _euri_subset_codes = sorted(_euri_subset_pcts)
        _euri_below_min = [c for c in _euri_subset_codes if _euri_subset_pcts[c] < _euri_min_pct]
        if _euri_subset_codes and (
            len(_euri_subset_codes) < _euri_min_parties
            or _euri_below_min
            or _euri_subset_cultural_passed is not True
        ):
            _euri_reasons = []
            if len(_euri_subset_codes) < _euri_min_parties:
                _euri_reasons.append(
                    f"only {len(_euri_subset_codes)} real asserted co-producer(s) on file "
                    f"({_euri_subset_codes}) -- eurimages requires at least {_euri_min_parties}."
                )
            if _euri_below_min:
                _euri_reasons.append(
                    f"{_euri_below_min} claim a contribution share below eurimages' own real "
                    f"{_euri_min_pct}% per-party minimum."
                )
            if _euri_subset_cultural_passed is not True:
                _euri_reasons.append(
                    "eurimages requires an explicit, evidenced cultural-test-passed fact "
                    "(coproduction_cultural_test_passed::eurimages) -- none, or an unresolved/"
                    "failed one, is on file."
                )
            _euri_unresolved_structure = ProductionStructure(
                id=uuid.uuid4(), project_id=project.id,
                name=f"{'+'.join(_euri_subset_codes)} multilateral co-production (eurimages, unresolved)",
                description="Asserted multilateral co-production subset does not clear eligibility: "
                + " ".join(_euri_reasons),
                jurisdiction_allocations=[], claimed_program_ids=_euri_subset_codes,
            )
            session.add(_euri_unresolved_structure)
            await session.flush()
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=_euri_unresolved_structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                structure_type="hybrid",
                calculation_trace_json={
                    "candidate_status": "RULE_REJECTED",
                    "rejection_reason_class": "MULTILATERAL_ELIGIBILITY_UNRESOLVED",
                    "discovery_classification": "combined_multilateral_coproduction_stack",
                    "structural_family": "combined_multilateral_coproduction_stack",
                    "structure_type": "hybrid",
                    "primary_jurisdiction": home_code,
                    "treaty_slug": "eurimages",
                    "program_slugs": _euri_subset_codes,
                    "reason": " ".join(_euri_reasons),
                    "is_baseline": False, "relocation_cost_normalized": False,
                    "is_directly_comparable": False,
                    "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                },
                input_fingerprint=fingerprint,
            ))
        _euri_eligible_subset = (
            len(_euri_subset_codes) >= _euri_min_parties
            and not _euri_below_min
            and _euri_subset_cultural_passed is True
        )
        if _euri_eligible_subset:
            _euri_party_candidates = [
                (code, priced_by_code.get(code, []))
                for code in _euri_subset_codes
            ]
            if any(not cands for _code, cands in _euri_party_candidates):
                _euri_missing = [code for code, cands in _euri_party_candidates if not cands]
                _euri_no_partner_structure = ProductionStructure(
                    id=uuid.uuid4(), project_id=project.id,
                    name=f"{'+'.join(_euri_subset_codes)} multilateral co-production (eurimages, no priceable program)",
                    description=(
                        f"{_euri_missing} {'has' if len(_euri_missing) == 1 else 'have'} no "
                        "independently-priceable program discovered for this production -- a "
                        "claimed participant must have a real, priceable program, never an "
                        "assumed one."
                    ),
                    jurisdiction_allocations=[], claimed_program_ids=_euri_subset_codes,
                )
                session.add(_euri_no_partner_structure)
                await session.flush()
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=_euri_no_partner_structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                    structure_type="hybrid",
                    calculation_trace_json={
                        "candidate_status": "RULE_REJECTED",
                        "rejection_reason_class": "NO_PRICEABLE_TREATY_UNLOCK",
                        "discovery_classification": "combined_multilateral_coproduction_stack",
                        "structural_family": "combined_multilateral_coproduction_stack",
                        "structure_type": "hybrid",
                        "primary_jurisdiction": home_code,
                        "treaty_slug": "eurimages",
                        "program_slugs": _euri_subset_codes,
                        "reason": f"No independently-priceable program for: {_euri_missing}.",
                        "is_baseline": False, "relocation_cost_normalized": False,
                        "is_directly_comparable": False,
                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                    },
                    input_fingerprint=fingerprint,
                ))
            else:
                # Structural-optimizer wiring correction pass, HO-012:
                # REVERTED from pricing. The prior pass's _price_combined_
                # multilateral_coproduction_candidate() treated Eurimages
                # membership as "national treatment" authority -- each
                # co-producer's real evidenced contribution share fed
                # directly into THAT PARTY's own separate national program
                # (e.g. uk_avec, ie_section_481, fr_trip), unchanged from
                # how a BILATERAL treaty's real, registered majority_
                # unlocks/minority_unlocks work. Direct primary-authority
                # verification this pass found that basis insufficient:
                # treaty_engine.py's own eurimages-multilateral TreatyData
                # row carries majority_unlocks=[] and minority_unlocks=[]
                # (EMPTY -- the codebase's own STRUCTURED, authoritative
                # "this treaty unlocks these specific programs" fields,
                # populated with real slugs for every bilateral treaty,
                # e.g. uk-au-bilateral's majority_unlocks=["uk_avec"]).
                # Only fund_unlocks=["eu_eurimages"] (the Eurimages FUND
                # itself, a collective co-production support fund -- NOT
                # each party's own national tax credit) is populated. The
                # ONLY textual support for "each co-producer independently
                # accesses national incentives on their own spend" is a
                # free-text `notes` field with confidence_tier="PARSED"
                # and NO citation field populated (TreatyData.citation
                # does not exist on this dataclass at all; contrast
                # PersonnelRequirement.citation / non_party_personnel_
                # exception_citation, which DO exist and ARE populated
                # for other, individually-researched propositions
                # elsewhere in this same file). An uncited free-text note
                # is not primary authority. Per explicit instruction not
                # to treat Eurimages fund membership as co-production/
                # national-treatment authority without primary proof, this
                # branch now persists an explicit, reconstructable
                # RULE_REJECTED for every structurally-eligible subset
                # instead of pricing -- the real subset-discovery work
                # above (participant count, per-party minimum contribution
                # share, cultural test) remains fully intact and disclosed;
                # only the unsupported PRICING claim is removed.
                _euri_no_authority_structure = ProductionStructure(
                    id=uuid.uuid4(), project_id=project.id,
                    name=f"{'+'.join(_euri_subset_codes)} multilateral co-production (eurimages, no national-treatment authority)",
                    description=(
                        "Structurally eligible Eurimages co-production subset "
                        f"({'+'.join(_euri_subset_codes)}), but the real, registered eurimages-"
                        "multilateral TreatyData carries EMPTY majority_unlocks/minority_unlocks "
                        "(only fund_unlocks=['eu_eurimages'] is populated) -- no structured, cited "
                        "primary authority establishes that Eurimages membership itself unlocks a "
                        "co-producer's own separate national incentive on its allocated spend "
                        "share. The free-text 'notes' field's claim is uncited and insufficient."
                    ),
                    jurisdiction_allocations=[], claimed_program_ids=_euri_subset_codes,
                )
                session.add(_euri_no_authority_structure)
                await session.flush()
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=_euri_no_authority_structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                    true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                    has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                    structure_type="hybrid",
                    calculation_trace_json={
                        "candidate_status": "RULE_REJECTED",
                        "rejection_reason_class": "MULTILATERAL_NATIONAL_TREATMENT_UNVERIFIED",
                        "discovery_classification": "combined_multilateral_coproduction_stack",
                        "structural_family": "combined_multilateral_coproduction_stack",
                        "structure_type": "hybrid",
                        "primary_jurisdiction": home_code,
                        "treaty_slug": "eurimages",
                        "program_slugs": _euri_subset_codes,
                        "reason": (
                            "Eurimages membership is structurally eligible (real participant count, "
                            "per-party minimum contribution share, and cultural test all clear), but "
                            "treaty_engine.py's own eurimages-multilateral TreatyData registers EMPTY "
                            "majority_unlocks/minority_unlocks -- no structured, cited primary "
                            "authority establishes that fund membership alone unlocks each "
                            "co-producer's own separate national incentive. The only supporting text "
                            "is an uncited 'notes' field (confidence_tier=PARSED, no citation), "
                            "insufficient to price real dollars. Fails closed rather than manufacturing "
                            "eligibility."
                        ),
                        "is_baseline": False, "relocation_cost_normalized": False,
                        "is_directly_comparable": False,
                        "anchor_jurisdiction": home_code, "anchor_program": home_program_slug,
                    },
                    input_fingerprint=fingerprint,
                ))

    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 3/CBA-006 — the same real, fail-closed
    # multilateral pattern as Eurimages above, for the two other
    # confirmed represented frameworks (European Convention, Ibermedia).
    # No new treaty engine — canonical_treaty_bridge's two new adapters
    # (Part 9/CBA-006) reuse treaty_engine.py's own real, parsed-tier
    # eligibility functions and thresholds unchanged. European Convention
    # is also the real, primary-source-cited backing for Gemini P0
    # pattern SP_001 (Bilateral to Multilateral Upgrade) — see
    # structuring_opportunity_patterns.py.
    for _fw_type, _fw_slug, _fw_name, _finder, _evaluator in (
        ("european_convention", "european-convention-coproduction", "European Convention",
         find_european_convention_partners, evaluate_european_convention_coproduction_opportunity),
        ("ibermedia", "ibermedia-multilateral", "Ibermedia",
         find_ibermedia_partners, evaluate_ibermedia_coproduction_opportunity),
    ):
        _fw_partners = _finder(home_code, candidate_codes)
        if not _fw_partners:
            continue
        # Codex global optimizer audit, P0-CAND-002: same fix as
        # Eurimages above — MAX_FRAMEWORK_DISPLAY bounds only the served
        # `_fw_shown` display list; the evaluator is called against the
        # FULL, real, discovered `_fw_partners` set so an 11th+ eligible
        # party is genuinely evaluated and accounted for.
        MAX_FRAMEWORK_DISPLAY = 10
        _fw_all_sorted = sorted(_fw_partners)
        _fw_shown = _fw_all_sorted[:MAX_FRAMEWORK_DISPLAY]
        # P0-QUAL-001: _fw_slug is a fixed treaty_slug constant for both
        # European Convention and Ibermedia (no per-pair ambiguity), so
        # facts are fetched directly scoped to (treaty_slug, the exact
        # ordered participant set passed to the evaluator below).
        _fw_participants = tuple([home_code] + _fw_all_sorted)
        _fw_country_pcts, _fw_cultural_test_passed = await _multilateral_coproduction_facts(
            session, project.id, _fw_slug, _fw_participants,
        )
        _fw_opp = _evaluator(
            list(_fw_participants), country_pcts=_fw_country_pcts,
            cultural_test_passed=_fw_cultural_test_passed,
            personnel_attachment_facts=role_attachment_facts,
        )
        _fw_structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=f"{home_code} — {_fw_name} multilateral co-production opportunity",
            description=(
                f"{home_code} is a {_fw_name} signatory/member. {len(_fw_partners)} of this "
                "production's own discovered candidate jurisdictions are ALSO real "
                f"{_fw_name} parties (via treaty_engine's registry) — a genuine "
                "multilateral co-production pathway. Real per-country budget-share and "
                "cultural-test facts are required to resolve eligibility — not yet on "
                "file for this project."
            ),
            jurisdiction_allocations=[],
            claimed_program_ids=[],
        )
        session.add(_fw_structure)
        await session.flush()
        _fw_conditional_programs, _fw_conditional_compat = _conditional_data(
            str(_fw_structure.id), home_code, (),
        )
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=_fw_structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
            true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
            has_unverified_inputs=True,
            warnings=[
                LIMITATION_NOTE,
                f"{_fw_name} multilateral co-production opportunity — real per-country "
                "budget-share and cultural-test facts are not yet on file; not priced "
                "as qualified economics.",
            ],
            structure_type="treaty_coproduction",
            calculation_trace_json={
                "candidate_status": STATUS_CO_PRO_OPPORTUNITY,
                "discovery_classification": "treaty_coproduction",
                "structure_type": "treaty_coproduction",
                "primary_jurisdiction": home_code,
                "is_baseline": False,
                "relocation_cost_normalized": False,
                "is_directly_comparable": False,
                "treaty_slug": _fw_slug,
                "conditional_programs": _fw_conditional_programs,
                "conditional_compatibility": _fw_conditional_compat,
                "coproduction_partners": [
                    {
                        "jurisdiction_code": code,
                        "jurisdiction_display_name": (
                            jurisdiction_by_code[code].name if code in jurisdiction_by_code else code
                        ),
                    }
                    for code in _fw_shown
                ],
                "treaty_resolution_state": _fw_opp.resolution_state if _fw_opp else "UNRESOLVED_FACTS",
                "treaty_cultural_test_required": _fw_opp.cultural_test_required if _fw_opp else True,
                "treaty_cultural_test_resolved": _fw_opp.cultural_test_resolved if _fw_opp else False,
                "treaty_disqualification_reasons": list(_fw_opp.disqualification_reasons) if _fw_opp else [],
                # COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION — same
                # reasoning as the Eurimages block above: home_code is
                # always the first element of _fw_participants, so
                # project_anchored is always True for a multilateral
                # opportunity; no conditional-pricing scenario exists for
                # multilateral frameworks.
                "opportunity_inclusion_source": "multilateral_membership_registry",
                "project_anchored": True,
                "opportunity_relevance": _classify_opportunity_relevance(
                    _fw_opp.resolution_state if _fw_opp else "UNRESOLVED_FACTS", None, True,
                ),
                "personnel_gate_state": _fw_opp.personnel_gate_state if _fw_opp else None,
                "personnel_satisfied_requirements": list(_fw_opp.personnel_satisfied_requirements) if _fw_opp else [],
                "personnel_failed_requirements": list(_fw_opp.personnel_failed_requirements) if _fw_opp else [],
                "personnel_missing_facts": list(_fw_opp.personnel_missing_facts) if _fw_opp else [],
                "personnel_curable_levers": list(_fw_opp.personnel_curable_levers) if _fw_opp else [],
                "personnel_next_question": _fw_opp.personnel_next_question if _fw_opp else None,
                "reason": (
                    f"{len(_fw_partners)} real {_fw_name} party candidate(s) discovered; "
                    "real budget-share and cultural-test facts required to resolve "
                    "eligibility."
                ),
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
            },
            input_fingerprint=fingerprint,
        ))

    await session.commit()
    summary = await _summarize_evaluation(session, project, inputs, fingerprint, reused=False)
    summary["discovery_examined"] = len(discovery.examinations)
    summary["discovery_rejected"] = discovery.metrics.get("rejected_count", 0)
    summary["discovery_capability_only"] = discovery.metrics.get("capability_only_count", 0)
    return summary


async def current_result_fingerprint(session, project_id) -> str | None:
    """The input fingerprint of a project's CURRENT evaluation generation.

    STALE-STATE PREVENTION (item 8). Evaluation is deliberately append-only:
    a superseded generation's StructureCalculationResult rows are retained as
    history rather than deleted, exactly as a superseded DocumentVersion is
    retained. That is only safe if every READER selects one generation.

    Readers historically filtered on ENGINE_VERSION alone, which was
    accidentally sufficient only because every semantic change also bumped
    that hand-maintained constant. Now that a rule or pricing-source change
    invalidates the FINGERPRINT on its own (canonical_runtime_attribution),
    several fingerprints legitimately coexist under one engine version, and
    an engine-version-only read serves rows computed from inputs that are no
    longer true -- a stale persisted result reaching the API.

    The newest committed row under the current engine defines the current
    generation. This is a pure read: it computes no economics and writes
    nothing, so read-only callers (the served production view) can use it.
    """
    return (await session.execute(
        select(StructureCalculationResult.input_fingerprint)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project_id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
        .order_by(StructureCalculationResult.created_at.desc())
        .limit(1)
    )).scalars().first()


async def current_generation_fingerprint(session, project_id) -> str | None:
    """Optimizer FINAL closeout, P1-FRESH-001 — the ONE canonical
    generation identity every current-evaluation READ must key off,
    extracted so no second freshness architecture is ever invented.

    ROOT CAUSE (Codex, full optimizer audit + final P0 delta reaudit):
    `current_result_fingerprint()` above answers "what fingerprint did
    the newest current-engine row happen to use" -- a pure history read
    that is only correct when a project's inputs have never been
    reverted. `canonical_production_view.build_production_and_structures`
    already had the CORRECT logic (recompute the fingerprint from the
    project's actual current facts, the exact same computation
    `evaluate_project()` itself uses, falling back to the newest-row
    helper only when a fresh computation is impossible, e.g. no budget
    yet) -- but `build_generic_pkg_and_economics` used the newest-row
    helper directly. For a project whose current facts don't match its
    most-recently-CREATED fingerprint (a reverted assumption, or a
    fingerprint-affecting fact changed and changed back), the structure
    view and the package/register view could each key off a DIFFERENT
    real, legitimately-persisted generation -- an internally
    inconsistent canonical read even though every individual row is
    current-engine. Confirmed live for F#K Valentine's Day and Lips Like
    Sugar (see OPTIMIZER_FINAL_CLOSEOUT_CLAUDE.md, Section 7).

    This function is now THE single canonical generation identity: it
    performs the exact same read-only reconstruction
    `build_production_and_structures` already performed inline, moved
    here so every current-evaluation reader (structure view, package/
    register view, and any future one) calls the SAME function rather
    than each re-implementing or half-implementing it. Falls back to
    `current_result_fingerprint()` (newest-row) ONLY when a project
    cannot currently evaluate at all (e.g. budget still missing) -- the
    same graceful-degradation behavior the structure view already had,
    preserved exactly.
    """
    fingerprint = None
    econ = await build_project_economic_inputs(session, project_id, read_only=True)
    if econ.ok:
        role_known_codes = await role_known_codes_from_project(session, str(project_id))
        script_facts = await script_facts_from_project(session, str(project_id))
        # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING: must match
        # evaluate_project()'s own fingerprint computation exactly, same
        # "two views, two fingerprints" reasoning as every other fact
        # fetched in this function.
        role_attachment_facts = await role_attachment_facts_from_project(session, str(project_id))
        # P0-QUAL-001: must match evaluate_project()'s own fingerprint
        # computation exactly, or this read-only reconstruction can never
        # find the rows evaluate_project() persisted (the same class of
        # divergence this function's own docstring already documents for
        # fx_context/company-period facts, immediately below).
        coproduction_facts = await _all_coproduction_facts_for_fingerprint(session, project_id)
        excluded_jurisdiction_codes = frozenset(await _excluded_jurisdiction_codes(session, project_id))
        discretionary_policy_facts = await _discretionary_policy_facts(session, project_id)
        # Codex final P0 (canonical_fx) — evaluate_project() attaches a
        # freshly-built fx_context to `inputs` (via dataclasses.replace)
        # before computing ITS fingerprint, and that context's
        # snapshot_date is now part of the fingerprint payload (see
        # _compute_fingerprint). This read-only reconstruction MUST do
        # the exact same attachment, or it computes a DIFFERENT
        # fingerprint than evaluate_project() persisted rows under —
        # exactly the "two views, two fingerprints" divergence this
        # function's own docstring exists to prevent.
        import dataclasses
        from app.calculators.production_normalization import build_fx_context
        econ_inputs = dataclasses.replace(econ.inputs, fx_context=build_fx_context())
        # Codex final wiring remediation (P0-NL-001): evaluate_project()
        # ALSO unions the real cross-project company/period facts into
        # evidenced_program_facts/amount_facts before computing ITS
        # fingerprint (see _company_period_prior_award_facts) -- this
        # read-only reconstruction MUST do the exact same union, for the
        # exact same reason the fx_context attachment above does: a
        # fingerprint divergence here would mean build_production_and_
        # structures() can never find the rows evaluate_project() just
        # persisted, for ANY project using this mechanism.
        project_row = await session.get(Project, project_id)
        if project_row is not None:
            _cp_evidenced, _cp_amounts = await _company_period_prior_award_facts(
                session, project_row, econ_inputs,
            )
            if _cp_evidenced or _cp_amounts:
                econ_inputs = dataclasses.replace(
                    econ_inputs,
                    evidenced_program_facts=econ_inputs.evidenced_program_facts | _cp_evidenced,
                    amount_facts={**econ_inputs.amount_facts, **_cp_amounts},
                )
        fingerprint = _compute_fingerprint(
            econ_inputs, role_known_codes=role_known_codes, script_facts=script_facts,
            coproduction_facts=coproduction_facts,
            excluded_jurisdiction_codes=excluded_jurisdiction_codes,
            discretionary_policy_facts=discretionary_policy_facts,
            role_attachment_facts=role_attachment_facts,
        )
    if fingerprint is None:
        fingerprint = await current_result_fingerprint(session, project_id)
    return fingerprint


async def _summarize_evaluation(
    session: AsyncSession, project: Project, inputs: ProjectEconomicInputs,
    fingerprint: str, *, reused: bool,
) -> dict:
    """Read back the persisted, fingerprint-matched rows and rank them.
    Never recomputes — purely a read + rank of what is already committed."""
    rows = (await session.execute(
        select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == fingerprint,
            # Same freshness rule as the "existing" check above: a
            # fingerprint match alone isn't enough once an older
            # engine_version's rows can coexist with a freshly regenerated
            # set for the SAME inputs — only the current engine's rows are
            # "the" evaluation; older ones are superseded history, still in
            # the table, never queried as current.
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).all()

    priced = [(s, r) for s, r in rows if r.true_net_cost_usd is not None]
    unpriced = [(s, r) for s, r in rows if r.true_net_cost_usd is None]
    priced.sort(key=lambda pair: float(pair[1].true_net_cost_usd))

    def _is_baseline(pair) -> bool:
        return bool((pair[1].calculation_trace_json or {}).get("is_baseline"))

    def _admits_recommended(pair) -> bool:
        # NUM-001: delegates to the one shared predicate — see
        # qualification_admits_recommended()'s own docstring.
        return qualification_admits_recommended(
            (pair[1].calculation_trace_json or {}).get("role_qualification")
        )

    baseline_pair = next((pair for pair in priced if _is_baseline(pair)), None)
    # ITEM 5. A project's baseline can be RECOGNIZED but BLOCKED -- e.g.
    # California's Film & Television Tax Credit is a COMPETITIVE, ranked
    # allocation requiring a Credit Allocation Letter before principal
    # photography, so it is NOT an entitlement and must not produce
    # deterministic economics (authority_coverage_registry:
    # NON_GUARANTEED_SELECTIVE). Failing closed means the baseline carries no
    # NUMBER; it must still be DISCLOSED, with its reason, or the producer
    # sees "no baseline" for a production that plainly has one.
    blocked_baseline_pair = (
        None if baseline_pair is not None
        else next((pair for pair in unpriced if _is_baseline(pair)), None)
    )
    # The served "winner"/top_result is the baseline whenever it is priced
    # AND its own qualification admits Recommended — never a relocation
    # candidate in this phase regardless of NPC (see RELOCATION_
    # COMPARABILITY_NOTE). If the baseline IS priced but its qualification
    # is genuinely unresolved, top_result is None — a relocation candidate
    # is never directly comparable enough to stand in for an unresolved
    # baseline either (same reasoning canonical_production_view.py's
    # comparable pool already applies: only the baseline is ever directly
    # comparable by construction). Only when the baseline was NEVER priced
    # at all (e.g. a genuine HARD_FAIL) does the top-ranked other priced
    # candidate stand in — unrelated to, and unchanged by, this gate.
    if baseline_pair is not None:
        top_pair = baseline_pair if _admits_recommended(baseline_pair) else None
    elif blocked_baseline_pair is not None:
        # The production HAS a baseline; it simply cannot be priced
        # deterministically. A relocation is never directly comparable
        # (relocation_cost_normalized is False for every one of them), so
        # promoting the lowest-NPC relocation would present an incomparable
        # candidate as the recommendation purely because its raw number is
        # smallest. No winner is the truthful answer.
        top_pair = None
    else:
        # Optimizer FINAL P0 remediation (P0-SEL-001, Codex broader-
        # corpus audit dcc6dde/8890cc8): this branch runs when the
        # project has NO baseline row at all -- not even a blocked one.
        # `relocation_cost_normalized` (== is_directly_comparable) is
        # True ONLY for the baseline candidate (see every `is_baseline`
        # assignment to it above and in the trace generators); every
        # other priced candidate -- a relocation, a component route, a
        # multi-program stack -- is a real, disclosed number that is
        # never a fair comparison against the base jurisdiction (same
        # RELOCATION_COMPARABILITY_NOTE reasoning canonical_production_
        # view.py's own `comparable` pool already applies). With no
        # baseline row present, therefore, there is definitionally no
        # comparable candidate for THIS project's current evaluation --
        # promoting `priced[0]` (the previous behavior) served the
        # cheapest priced candidate purely because its raw, non-
        # comparable number was smallest, exactly the false-winner
        # pattern this file's own `_admits_recommended` docstring above
        # already rejects for the blocked-baseline case. Confirmed live
        # across the nine broader-corpus projects named in the Codex
        # audit (10 Double Zero, Baron Samedi, Going Places,
        # Interference, Rocky Mountain, The Cure, The System, Twilight
        # of the Dead, Underwater): each has no current baseline row and
        # was persisting its cheapest non-comparable relocation into
        # Project.leading_structure_id while canonical_production_view.py
        # correctly served canonical_selected_structure_id=null -- the
        # exact evaluator/served divergence this fix closes. No project-
        # specific or jurisdiction-specific exception; this is the same
        # generic rule as the baseline-priced and baseline-blocked
        # branches above: only a comparable candidate may ever be a
        # winner, and here there is none.
        top_pair = None

    # Repoint leading_structure_id whenever it's unset OR currently points
    # at a structure NOT produced by this canonical engine (a stale legacy
    # result — e.g. the run_full_analysis-backed rows from commit 87440df —
    # must never keep rendering as the current evaluation). Never
    # overwrites a CURRENT canonical result on a repeat/idempotent run.
    if top_pair:
        needs_repoint = project.leading_structure_id is None
        if not needs_repoint and project.leading_structure_id == top_pair[0].id:
            # Even when the pointer already names the top candidate, its
            # LATEST result can be stale (a superseded fingerprint). Validate
            # rather than assume.
            _self_result = (await session.execute(
                select(StructureCalculationResult)
                .where(StructureCalculationResult.structure_id == project.leading_structure_id)
                .order_by(StructureCalculationResult.created_at.desc())
            )).scalars().first()
            if (
                _self_result is None
                or _self_result.engine_version != ENGINE_VERSION
                or _self_result.input_fingerprint != fingerprint
            ):
                needs_repoint = True
        if not needs_repoint and project.leading_structure_id != top_pair[0].id:
            current_structure = await session.get(ProductionStructure, project.leading_structure_id)
            current_result = (
                (await session.execute(
                    select(StructureCalculationResult)
                    .where(StructureCalculationResult.structure_id == project.leading_structure_id)
                    .order_by(StructureCalculationResult.created_at.desc())
                )).scalars().first()
                if current_structure is not None else None
            )
            # CLUSTER 12: a result is CURRENT only when its engine version AND
            # its input fingerprint both match the current canonical inputs.
            # Checking the engine version alone let a leading pointer survive
            # against a superseded fingerprint -- the same engine, but computed
            # from inputs the project no longer has -- and the project summary
            # then read that stale row as though it were current.
            if (
                current_structure is None
                or current_result is None
                or current_result.engine_version != ENGINE_VERSION
                or current_result.input_fingerprint != fingerprint
            ):
                needs_repoint = True
        if needs_repoint:
            project.leading_structure_id = top_pair[0].id
            await session.commit()
    elif project.leading_structure_id is not None:
        # Final Consolidated Backend Correction + Global Structuring
        # Intelligence Acceptance, Part 4/CBA-001 — top_pair is None
        # (no candidate currently admits Recommended, e.g. this
        # project's baseline qualification is genuinely unresolved
        # under the CURRENT engine/knowledge version). A stale
        # leading_structure_id from a prior evaluation must not keep
        # rendering as though still current and recommended — cleared,
        # never left pointing at a superseded result.
        project.leading_structure_id = None
        await session.commit()

    def _entry(structure, result):
        trace = result.calculation_trace_json or {}
        return {
            "structure_id": str(structure.id),
            "name": structure.name,
            "candidate_status": trace.get("candidate_status"),
            "true_net_cost_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
            "total_incentive_value_usd": (
                float(result.total_incentive_value_usd) if result.total_incentive_value_usd is not None else None
            ),
            "is_baseline": trace.get("is_baseline", False),
            "relocation_cost_normalized": trace.get("relocation_cost_normalized", False),
            "reason": trace.get("reason"),
        }

    return {
        "status": "EVALUATION_REUSED" if reused else "EVALUATION_COMPLETE",
        "engine_version": ENGINE_VERSION,
        "state_fingerprint": fingerprint,
        "gross_budget_usd": inputs.gross_budget_usd,
        "base_jurisdiction_code": inputs.jurisdiction_code,
        "priced_count": len(priced),
        "unpriceable_count": len(unpriced),
        "baseline": (
            _entry(*baseline_pair) if baseline_pair
            else _entry(*blocked_baseline_pair) if blocked_baseline_pair
            else None
        ),
        #: True when the production's baseline is recognized but carries no
        #: deterministic economics -- distinct from having no baseline.
        "baseline_blocked": blocked_baseline_pair is not None,
        "top_result": _entry(*top_pair) if top_pair else None,
        "ranked": [_entry(s, r) for s, r in priced],
        "unpriceable": [_entry(s, r) for s, r in unpriced],
        "mfni_limitation": LIMITATION_NOTE,
        "relocation_comparability_limitation": RELOCATION_COMPARABILITY_NOTE,
    }
