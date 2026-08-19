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

MFNI (regional production-cost normalization) is explicitly NOT applied
here — local_cost_delta_usd is always 0.0, and every persisted result
discloses that limitation. Travel/FX normalization are likewise omitted
generically (no per-project travel/FX input exists yet outside Little
Utopia's own hand-built fixtures) and folded into the same disclosure
rather than silently assumed zero without comment.
"""
from __future__ import annotations

import itertools
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure, rank_allocated_structures
from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    price_program_group_stack,
)
from app.calculators.canonical_opportunity_bridge import (
    discover_cultural_test_gap_opportunity,
    discover_fee_cap_headroom_opportunity,
    discover_national_status_opportunity,
    discover_potential_reinvestment_candidates,
    discover_qualification_gap_opportunity,
    discover_qualification_lever_opportunities,
    opportunity_to_dict,
)
from app.calculators.canonical_qualification_result import qualification_result_to_dict
from app.calculators.canonical_role_qualification_bridge import (
    evaluate_role_qualification,
    role_known_codes_from_project,
)
from app.calculators.canonical_treaty_bridge import (
    evaluate_bilateral_coproduction_opportunity,
    evaluate_eurimages_coproduction_opportunity,
    find_eurimages_partners,
    find_real_bilateral_partners,
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
from app.data.authority_coverage_registry import coverage_state as _coverage_state
from app.data.executable_jurisdiction_registry import get_doctrine as _get_doctrine
from app.data.program_rate_rules import (
    RATE_FAILURE_NO_RULES,
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
ENGINE_VERSION = "canonical-1.29.1"

LIMITATION_NOTE = (
    "Regional production-cost normalization (MFNI) and generic travel/FX "
    "normalization are not yet applied to this comparison — every figure "
    "uses this production's own nominal budget amounts and statutory "
    "incentive rate only."
)

#: Why the baseline structure is always the served "winner" in this phase,
#: never a relocation candidate — see the module-level note below.
RELOCATION_COMPARABILITY_NOTE = (
    "This structure's cost omits real relocation-specific costs (travel, "
    "in-kind post-production replacement) that are not yet computed "
    "generically for any project. Its NPC is therefore NOT a fair, complete "
    "comparison against the production's own base jurisdiction, which needs "
    "no such adjustment by construction. Never treated as beating the "
    "baseline until relocation costs are modeled generically."
)

#: Candidate accounting terminal states (Part N/K).
STATUS_PRICED = "PRICED"
STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT = "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
STATUS_RULE_REJECTED = "RULE_REJECTED"
STATUS_FEASIBILITY_REVIEW_REQUIRED = "FEASIBILITY_REVIEW_REQUIRED"
#: Existing Optimizer/Stacker Reconnection, Task B — a real, registry-
#: backed treaty/co-production pathway exists but cannot (yet) be priced
#: as qualified economics: either real ownership/cultural-test project
#: facts are missing (canonical_treaty_bridge.RESOLUTION_UNRESOLVED_FACTS)
#: or a mandatory requirement failed (RESOLUTION_INELIGIBLE). NEVER
#: STATUS_PRICED — a co-pro opportunity never enters NPC/ranking as
#: resolved economics; see canonical_treaty_bridge.py's own module note.
STATUS_CO_PRO_OPPORTUNITY = "CO_PRO_OPPORTUNITY"


def _compute_fingerprint(inputs: ProjectEconomicInputs) -> str:
    import hashlib
    import json

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
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


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
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        production_type=inputs.production_type,
    )
    return pricing, register, rr


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
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        production_type=inputs.production_type,
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
        v = facts.get(key)
        if v is None or v == "":
            return None
        return str(v).strip().lower() in ("true", "1", "yes")

    return (
        _float("coproduction_majority_pct"),
        _float("coproduction_minority_pct"),
        _bool("coproduction_cultural_test_passed"),
    )


def _role_qualification_for_candidate(
    code: str, program_slug: str, role_known_codes: dict[str, tuple[str, ...]] | None,
) -> dict | None:
    """Canonical Co-production Qualification Reconnection, Task 3 — the
    repaired seam. Calls evaluate_role_qualification() (reusing cultural_
    qualification_model.py's real 24-program registry UNCHANGED) with the
    project's own real, persisted personnel facts. Returns None only when
    role_known_codes itself is unavailable (never a fabricated result);
    the bridge function itself always returns a real
    CanonicalQualificationResult (QUALIFIES/HARD_FAIL/USER_FACT_REQUIRED/
    RULE_DATA_INCOMPLETE/NOT_APPLICABLE) for every program_slug, including
    the 157 slugs cultural_qualification_model.py has no data for."""
    if role_known_codes is None:
        return None
    result = evaluate_role_qualification(program_slug, code, role_known_codes)
    return qualification_result_to_dict(result)


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
            "notes": list(s.notes),
        }
        for s in pricing.segments
    ]


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
    fingerprint = _compute_fingerprint(inputs)

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

    # Canonical Co-production Qualification Reconnection — the first
    # shared disconnect Codex's audit identified: this project's real,
    # persisted personnel (ProjectPerson -> TalentProfile) were never
    # read into the canonical evaluation path at all. One query per
    # project (role-level facts don't vary per candidate), reused by
    # every candidate's role-qualification check below.
    role_known_codes = await role_known_codes_from_project(session, str(project_id))

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
            examination = next((e for e in discovery.examinations if e.jurisdiction_code == code), None)
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
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        pricing, register, rate_resolution = _price_candidate(inputs, code, program_slug)
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
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        is_baseline = code == inputs.jurisdiction_code
        _conditional_program_dicts, _conditional_compatibility_dict = _conditional_data(
            str(structure.id), code, (program_slug,),
        )
        _opportunities = _opportunities_for_candidate(inputs, code, program_slug, register, rate_resolution)
        _role_qualification = _role_qualification_for_candidate(code, program_slug, role_known_codes)
        warnings = [LIMITATION_NOTE] if is_baseline else [LIMITATION_NOTE, RELOCATION_COMPARABILITY_NOTE]
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
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=stack_result.adjusted_incentive_usd,
            true_net_cost_usd=npc,
            risk_adjusted_net_cost_usd=npc,
            has_unverified_inputs=territorial_state_unknown or bool(stack_result.disclosed_limitations),
            warnings=warnings,
            calculation_trace_json={
                "candidate_status": STATUS_PRICED,
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
                "stacking_condition_text": stack_result.condition_text,
                "raw_incentive_usd": stack_result.raw_incentive_usd,
                "selected_incentive_usd": stack_result.adjusted_incentive_usd,
                "npc_verified_usd": npc,
                "npc_conservative_usd": npc,
                "gross_budget_usd": inputs.gross_budget_usd,
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

    # Bounded to the most promising real alternative jurisdictions (by
    # their own already-computed single-program incentive value) — a
    # practical search-space bound, not a doctrine choice; every target
    # considered is a genuinely discovered, independently-priceable
    # candidate, never invented.
    MAX_COMPONENT_TARGETS = 6
    if component_spend:
        target_best_by_code: dict[str, StackCandidate] = {}
        for code, cands in priced_by_code.items():
            if code == home_code:
                continue
            target_best_by_code[code] = max(cands, key=lambda c: c.selected_incentive_usd)
        top_targets = sorted(
            target_best_by_code.values(), key=lambda c: c.selected_incentive_usd, reverse=True,
        )[:MAX_COMPONENT_TARGETS]

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
                            "jurisdiction_display_name": target_jur_row.name if target_jur_row else None,
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
    candidate_codes = list(priced_by_code.keys())
    _copro_majority_pct, _copro_minority_pct, _copro_cultural_test_passed = await _coproduction_facts(
        session, project.id,
    )

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

    await session.commit()
    summary = await _summarize_evaluation(session, project, inputs, fingerprint, reused=False)
    summary["discovery_examined"] = len(discovery.examinations)
    summary["discovery_rejected"] = discovery.metrics.get("rejected_count", 0)
    summary["discovery_capability_only"] = discovery.metrics.get("capability_only_count", 0)
    return summary


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

    baseline_pair = next((pair for pair in priced if _is_baseline(pair)), None)
    # The served "winner"/top_result is the baseline whenever it is priced —
    # never a relocation candidate, in this phase, regardless of whether one
    # shows a lower NPC (see RELOCATION_COMPARABILITY_NOTE: that NPC omits
    # real relocation costs no project has generic data for yet, so it is
    # never a fair comparison to declare a winner over the baseline). Only
    # if the baseline itself could not be priced does the top-ranked
    # (still honestly computed, still disclosed) alternative stand in.
    top_pair = baseline_pair or (priced[0] if priced else None)

    # Repoint leading_structure_id whenever it's unset OR currently points
    # at a structure NOT produced by this canonical engine (a stale legacy
    # result — e.g. the run_full_analysis-backed rows from commit 87440df —
    # must never keep rendering as the current evaluation). Never
    # overwrites a CURRENT canonical result on a repeat/idempotent run.
    if top_pair:
        needs_repoint = project.leading_structure_id is None
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
            if current_structure is None or current_result is None or current_result.engine_version != ENGINE_VERSION:
                needs_repoint = True
        if needs_repoint:
            project.leading_structure_id = top_pair[0].id
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
        "baseline": _entry(*baseline_pair) if baseline_pair else None,
        "top_result": _entry(*top_pair) if top_pair else None,
        "ranked": [_entry(s, r) for s, r in priced],
        "unpriceable": [_entry(s, r) for s, r in unpriced],
        "mfni_limitation": LIMITATION_NOTE,
        "relocation_comparability_limitation": RELOCATION_COMPARABILITY_NOTE,
    }
