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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure, rank_allocated_structures
from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    eligible_group_for_combination,
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
    role_known_codes_from_project,
    script_facts_from_project,
    typed_personnel_facts_from_project,
)
from app.calculators import treaty_engine as te
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
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
)
from app.data.executable_jurisdiction_registry import get_doctrine as _get_doctrine
from app.data.program_rate_rules import (
    CONDITION_STATE_AUTHORITY_UNRESOLVED,
    CONDITION_STATE_EXECUTABLE,
    CONDITION_STATE_USER_FACT_REQUIRED,
    RATE_FAILURE_NO_RULES,
    RateResolution,
    classify_rate_resolution_failure,
    resolve_program_rate,
)
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
ENGINE_VERSION = "canonical-1.52.0"

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
        # Batched producer-control closeout (2026-09-03) -- a change to
        # which jurisdictions this PROJECT elects to exclude from its own
        # candidate universe must invalidate any stale cached evaluation
        # row (same reasoning as financing_cost_usd/contingency directly
        # above), or toggling Saudi ON/OFF would silently keep serving
        # the pre-toggle persisted structures forever.
        "excluded_jurisdiction_codes": sorted(excluded_jurisdiction_codes or ()),
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
        and inputs.spend_category_by_code.get(line.account_code, line.spend_category)
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

    rr = resolve_program_rate(program_slug, production_type=inputs.production_type, qpe_usd=qpe)
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
    )
    return pricing, register, rr


def _build_conditional_bilateral_scenario(
    inputs: ProjectEconomicInputs,
    majority_code: str,
    minority_code: str,
    treaty_slug: str,
    baseline_incentive_usd: float | None,
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
    around."""
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

    # Price every unlocked slug through the SAME canonical kernel every
    # ordinary candidate uses -- no new economics. majority_unlocks price
    # against the majority party's own jurisdiction; minority_unlocks
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
    from app.data.program_rate_rules import _RULES_BY_PROGRAM
    from app.data.program_slug_aliases import canonical_slug as _canonical_program_slug

    priced_components: list[dict] = []
    data_gaps: list[str] = []
    candidates_by_jurisdiction: dict[str, list[StackCandidate]] = {}
    for slug in result.unlocked_slugs:
        code = majority_code if slug in treaty.majority_unlocks else (
            minority_code if slug in treaty.minority_unlocks else majority_code
        )
        priced_slug = _canonical_program_slug(slug)
        if priced_slug not in _RULES_BY_PROGRAM:
            data_gaps.append(slug)
            continue
        pricing, register, rr = _price_candidate(inputs, code, priced_slug)
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
    for code, group in candidates_by_jurisdiction.items():
        if len(group) < 2 or not eligible_group_for_combination([c.jurisdiction_code for c in group]):
            total_conditional_incentive += sum(c.selected_incentive_usd for c in group)
            continue
        stack_result = price_program_group_stack(group)
        if stack_result is None:
            # No named, publishable stacking rule covers this exact group
            # -- Codex's "visibility alone is not proof of stacking" rule
            # applies here too: fall back to the raw (unadjusted) sum,
            # disclosed as unverified rather than silently fabricated.
            total_conditional_incentive += sum(c.selected_incentive_usd for c in group)
            stacking_groups.append({
                "jurisdiction_code": code,
                "program_slugs": [c.program_slug for c in group],
                "stacking_verified": False,
                "note": (
                    "No named, publishable stacking rule covers this exact "
                    "program combination -- summed as independent programs, "
                    "not verified against a stacking-compatibility rule."
                ),
            })
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

    if priced_components:
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
    )
    return spec, allocation, pricing


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
        comp = component_for(inputs.spend_category_by_code.get(line.account_code, line.spend_category))
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


async def _coproduction_facts(session: AsyncSession, project_id) -> tuple[float | None, float | None, bool | None]:
    """Canonical Co-production Qualification Reconnection — the treaty-
    bridge disconnect Codex's audit named: canonical_evaluation never
    supplied majority_pct/minority_pct/cultural_test_passed to
    evaluate_bilateral_coproduction_opportunity() at all (always left at
    their None defaults, regardless of what facts might exist). Reads
    the three real fact_key values from the existing generic ProjectFact
    model — the SAME model screen_analyzer_fact_contract.py's future
    facts are expected to land in. Absent facts stay None (never
    invented); neither LU nor FVD has these on file, so their output is
    unchanged, but the plumbing is now real."""
    rows = (await session.execute(
        select(ProjectFact.fact_key, ProjectFact.value).where(
            ProjectFact.project_id == project_id,
            ProjectFact.fact_key.in_((
                "coproduction_majority_pct", "coproduction_minority_pct",
                "coproduction_cultural_test_passed",
            )),
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

    return (
        _float("coproduction_majority_pct"),
        _float("coproduction_minority_pct"),
        _bool("coproduction_cultural_test_passed"),
    )


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
    _copro_majority_pct, _copro_minority_pct, _copro_cultural_test_passed = await _coproduction_facts(
        session, project.id,
    )
    # Batched producer-control closeout (2026-09-03) — fetched once here
    # (same one-query-per-project pattern as role_known_codes/script_facts
    # above) and reused at both use sites (fingerprint below, and the
    # candidate filter further down) — never re-fetched.
    excluded_jurisdiction_codes = frozenset(await _excluded_jurisdiction_codes(session, project_id))
    fingerprint = _compute_fingerprint(
        inputs, role_known_codes=role_known_codes, script_facts=script_facts,
        coproduction_facts=(_copro_majority_pct, _copro_minority_pct, _copro_cultural_test_passed),
        excluded_jurisdiction_codes=excluded_jurisdiction_codes,
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
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
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
                if failure == RATE_FAILURE_NO_RULES:
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
        else:
            _prior_state = _qual_state_by_program[program_slug]
            if _QUAL_STATE_SEVERITY.get(_this_qual_state, 2) < _QUAL_STATE_SEVERITY.get(_prior_state, 2):
                _qual_state_by_program[program_slug] = _this_qual_state
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
        ))
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=pricing.selected_incentive_usd,
            true_net_cost_usd=pricing.npc_verified_usd,
            risk_adjusted_net_cost_usd=pricing.npc_with_adjustments_usd,
            has_unverified_inputs=territorial_state_unknown, warnings=warnings,
            calculation_trace_json={
                "candidate_status": STATUS_PRICED,
                "discovery_classification": classification,
                "modeled_rate": rate_resolution.modeled_rate,
                "rate_basis": rate_resolution.basis,
                "qualifying_spend_usd": round(sum(
                    a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                ), 2),
                "is_baseline": is_baseline,
                # False for every non-baseline structure in this phase: no
                # relocation cost (travel, in-kind replacement) is computed
                # generically yet, so its NPC is priced but not eligible to
                # be selected as the served "winner" over the baseline —
                # see RELOCATION_COMPARABILITY_NOTE. Baseline needs no such
                # adjustment by construction (no relocation occurs).
                "relocation_cost_normalized": is_baseline,
                # Codex Defect 2 — economic priceability (candidate_status
                # == PRICED, always true here) and regional comparability
                # are two different states. is_directly_comparable is the
                # SAME fact as relocation_cost_normalized under an
                # unambiguous name, so a downstream reader never has to
                # infer "comparable" from a field named for something else.
                # is_fully_priced (this candidate priced successfully) must
                # never be overwritten by this — see canonical_production_view.py.
                "is_directly_comparable": is_baseline,
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
        for _member_slug in stack_result.program_slugs:
            _member_disclosure = _competitive_allocation_disclosure(_member_slug)
            if _member_disclosure:
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
        _combination_is_invalid = stack_result.rule_type == "mutually_exclusive"
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
                "candidate_status": (
                    STATUS_RULE_REJECTED
                    if stack_result.rule_type == "mutually_exclusive"
                    else STATUS_PRICED
                ),
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
                "stacking_rule_type": stack_result.rule_type,
                # A rejected combination must explain itself -- never an
                # unexplained drop into the unpriceable bucket.
                "reason": (
                    f"{code}: {' + '.join(stack_result.program_slugs)} are MUTUALLY "
                    "EXCLUSIVE under their own stacking rule"
                    + (f" ({stack_result.condition_text})" if stack_result.condition_text else "")
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
                "total_qualifying_spend_usd": sum(
                    stack_result.per_program_qpe_usd.get(slug, 0.0)
                    for slug in stack_result.program_slugs
                ),
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
                # carries a real, unresolved qualification gap. Only the
                # `state` key is populated (the Recommended-admission gate
                # at _admits_recommended/canonical_production_view.py reads
                # exactly and only this key); per-member detail remains on
                # each single-program candidate's own trace.
                "role_qualification": (
                    {"state": _combo_qual_state} if _combo_qual_state is not None else None
                ),
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
        cat = inputs.spend_category_by_code.get(line.account_code, line.spend_category)
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
                    # Genuinely unresolvable (e.g. the routed component's
                    # allocated QPE doesn't clear the target program's own
                    # minimum-spend threshold) — fail closed, never
                    # persisted as a misleading candidate. Not silently
                    # dropped from the ledger: disclosed as a class in the
                    # capability ledger, not per-instance (would be noise).
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
                for _component_program_slug in (home_program_slug, target.program_slug):
                    if not _component_program_slug:
                        continue
                    _component_disclosure = _competitive_allocation_disclosure(_component_program_slug)
                    if _component_disclosure and _component_disclosure not in _component_warnings:
                        _component_warnings.append(_component_disclosure)
                session.add(StructureCalculationResult(
                    id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                    total_budget_usd=inputs.gross_budget_usd,
                    total_incentive_value_usd=pricing.selected_incentive_usd,
                    true_net_cost_usd=npc,
                    risk_adjusted_net_cost_usd=npc,
                    has_unverified_inputs=True,
                    warnings=_component_warnings,
                    calculation_trace_json={
                        "candidate_status": STATUS_PRICED,
                        "discovery_classification": "component_relocation",
                        "structure_type": "component_relocation",
                        "primary_jurisdiction": home_code,
                        "program_slugs": [s for s in (home_program_slug, target.program_slug) if s],
                        "is_baseline": False,
                        "relocation_cost_normalized": False,
                        "is_directly_comparable": False,
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
    reachable_codes = set(priced_by_code)
    reachable_codes |= {code.split("-")[0] for code in reachable_codes}
    candidate_codes = sorted(reachable_codes)
    # _copro_majority_pct/_copro_minority_pct/_copro_cultural_test_passed
    # fetched once, near the top of this function (see CBA-008 note there
    # — also part of the cache fingerprint now) and reused here.

    MAX_TREATY_PARTNERS = 5
    for partner_code in find_real_bilateral_partners(home_code, candidate_codes)[:MAX_TREATY_PARTNERS]:
        opp = evaluate_bilateral_coproduction_opportunity(
            home_code, partner_code,
            majority_pct=_copro_majority_pct, minority_pct=_copro_minority_pct,
            cultural_test_passed=_copro_cultural_test_passed,
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
                "reason": "; ".join(opp.notes) or "Real ownership/cultural facts required to resolve eligibility.",
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
                "conditional_scenario": _conditional_scenario,
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
        opp = evaluate_bilateral_coproduction_opportunity(
            majority_code, minority_code,
            majority_pct=_copro_majority_pct, minority_pct=_copro_minority_pct,
            cultural_test_passed=_copro_cultural_test_passed,
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
                "reason": "; ".join(opp.notes) or "Real ownership/cultural facts required to resolve eligibility.",
                "feasibility_status": FEASIBILITY_UNKNOWN,
                "feasibility_reasons": [],
                "location_independent_of_service_jurisdiction": True,
                "conditional_scenario": _conditional_scenario,
            },
            input_fingerprint=fingerprint,
        ))

    eurimages_partners = find_eurimages_partners(home_code, candidate_codes)
    if eurimages_partners:
        MAX_EURIMAGES_DISPLAY = 10
        shown = sorted(eurimages_partners)[:MAX_EURIMAGES_DISPLAY]
        # Canonical Co-production Qualification Reconnection — was
        # previously hardcoded to UNRESOLVED_FACTS/cultural_test_resolved
        # =False regardless of any real fact; now genuinely computed via
        # evaluate_eurimages_coproduction_opportunity() (reused
        # unchanged). With no country_pcts fact on file (true for LU/FVD)
        # this still resolves UNRESOLVED_FACTS — same output, real path.
        _eurimages_opp = evaluate_eurimages_coproduction_opportunity(
            [home_code] + shown, cultural_test_passed=_copro_cultural_test_passed,
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
        MAX_FRAMEWORK_DISPLAY = 10
        _fw_shown = sorted(_fw_partners)[:MAX_FRAMEWORK_DISPLAY]
        _fw_opp = _evaluator([home_code] + _fw_shown, cultural_test_passed=_copro_cultural_test_passed)
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
        # Final Consolidated Backend Correction + Global Structuring
        # Intelligence Acceptance, Part 4/CBA-001 — consistent with
        # canonical_production_view.py's own _qualification_admits_
        # recommended: a real but genuinely UNRESOLVED qualification
        # state (Curable Gap/User Fact Required/Script Fact Required/
        # Authority Unresolved/Rule Data Incomplete) is priced and
        # disclosed (already true — it reached `priced` above) but must
        # never be the served "winner"/top_result. Truthful unresolved
        # status is preferable to false recommendation, even when that
        # means no top_result at all.
        state = ((pair[1].calculation_trace_json or {}).get("role_qualification") or {}).get("state")
        return state is None or state in _QUALIFICATION_ADMITS_RECOMMENDED

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
        top_pair = priced[0] if priced else None

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
