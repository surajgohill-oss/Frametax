// Overview UI contract — "Production Options" (up to six primary
// structure cards on Overview, replacing the previous 4-slot per-
// jurisdiction representative grid). Pure selection/classification logic
// over the SAME allocated_structures/ranking data every other screen
// already reads (Workspace's ScenarioCard, Scenarios.jsx) — no new
// economics, no new ranking, nothing recalculated. Kept in a plain .js
// module (not the .jsx component) so it can be unit-tested directly, the
// same separation globeFit.js/globeData.js already use.
//
// Does NOT import workspaceScenarioMode.js's optimizerProjection() —
// workspaceScenarioMode.js itself imports isBaselineStructure from THIS
// module, so importing back would be a circular dependency. Reads the
// same `recommended_optimizer_options` (falling back to the
// `producer_optimizer_options` backward-compatible alias) field directly
// instead — the identical data optimizerProjection() reads, just without
// its re-sort (selectMaxPotentialCard only needs the first entry, and the
// backend already serves recommended_optimizer_options pre-sorted
// Practical -> Formal -> Advanced, NPC ascending).

import { hasAdministrativeAllocationRisk, hasUnconfirmedStackingDeduction } from "./allocationRisk.js";
import { optimizerProjection } from "./workspaceScenarioMode.js";

export const CLASSIFICATIONS = {
  current: { key: "current", label: "Current / Base Production", accent: "gold" },
  relocation: { key: "relocation", label: "Full Relocation", accent: "jade" },
  hybrid: { key: "hybrid", label: "Hybrid / Component", accent: "amber" },
  treaty: { key: "treaty", label: "Official Treaty Co-Production", accent: "silver" },
};

// `structure_type === "single_country"` is set by the backend ONLY for
// the production's own home jurisdiction (canonical_evaluation.py:
// "single_country" if code == inputs.jurisdiction_code else
// "full_relocation" -- true for both the generic path and
// little_utopia_state.py, which uses the literal string exactly once,
// for its base Mauritius structure). `is_baseline` is the same fact on
// the generic canonical_production_view.py entries, but little_utopia_
// state.py's own richer per-structure dict does not carry that field at
// all -- checking structure_type first means Current/Base classifies
// correctly on BOTH data sources, not just the generic one.
export function isBaselineStructure(entry) {
  return !!(entry.is_baseline || entry.structure_type === "single_country");
}

// Canonical served wiring repair (Codex Defect 2) — is_directly_comparable
// on a RANKING entry only exists on the generic canonical_production_view.py
// path (added this batch). little_utopia_state.py's own rank_allocated_
// structures() has no such field and never will need one: LU's rich
// per-structure pricing already includes real travel/FX/in-kind deltas
// (unlike the generic path's hard-set zeros), so every one of ITS ranked
// candidates already IS directly comparable by construction -- which is
// exactly what its existing is_fully_priced always meant. Falling back to
// is_fully_priced when is_directly_comparable is absent therefore
// preserves LU's existing, already-correct behavior unchanged, while the
// generic path (which always sets the field explicitly) gets the real fix.
export function isDirectlyComparable(rankingEntry) {
  return rankingEntry?.is_directly_comparable ?? rankingEntry?.is_fully_priced ?? false;
}

// The UI must stop treating every multi-jurisdiction structure as a
// "co-production." `treaty_slug` is the one EXPLICIT field the backend
// already sets only when a real bilateral/multilateral treaty applies
// (app/calculators/treaty_engine.py's _BILATERAL/_MULTILATERAL tables,
// threaded through structure_generator.py / production_structure_composer.py) --
// classification reads that flag, never infers treaty status from a
// structure having two participants or from its structure_type string.
export function classifyStructure(entry) {
  if (isBaselineStructure(entry)) return CLASSIFICATIONS.current;
  if (entry.treaty_slug) return CLASSIFICATIONS.treaty;
  if (entry.structure_type === "full_relocation") return CLASSIFICATIONS.relocation;
  return CLASSIFICATIONS.hybrid;
}

// Top Six selection (UI only, see CineGlobe Overview UI contract):
// 1. First five valid/comparable options from the EXISTING ranking order
//    (allocated.ranking, already sorted by npc_with_adjustments_usd --
//    canonical_production_view.py / little_utopia_state.py's own rule
//    that only is_directly_comparable candidates rank numerically).
// 2. Sixth slot: the best not-yet-shown structure whose treaty_slug is
//    explicitly set, if one exists; otherwise the next valid/comparable
//    option in the same existing order.
// Never manufactures a sixth option -- fewer than six is a valid result.
//
// Canonical served wiring repair (Codex Defect 2): filters on
// is_directly_comparable, NOT is_fully_priced. Priced-but-not-regionally-
// comparable structures (FVD has 29) are real, differentiated economics —
// they belong in Scenarios' Review section (see selectReviewOptions
// below), never silently promoted into "the six primary options" just
// because they happen to be priced.
export function selectTopOptions(allocated) {
  if (!allocated?.ranking || !allocated?.structures) return [];
  const structById = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  const pricedRanked = allocated.ranking.filter(isDirectlyComparable);

  const firstFive = pricedRanked.slice(0, 5)
    .map((r) => structById.get(r.structure_id))
    .filter(Boolean);
  const shownIds = new Set(firstFive.map((s) => s.structure_id));

  const treatyCandidates = allocated.structures.filter(
    (s) => s.is_fully_priced && s.treaty_slug && !shownIds.has(s.structure_id),
  );
  let sixth = null;
  if (treatyCandidates.length > 0) {
    sixth = treatyCandidates.reduce((best, s) => {
      const bestNpc = best?.npc_with_adjustments_usd ?? Infinity;
      const sNpc = s.npc_with_adjustments_usd ?? Infinity;
      return sNpc < bestNpc ? s : best;
    }, null);
  } else if (pricedRanked.length > 5) {
    sixth = structById.get(pricedRanked[5].structure_id) || null;
  }

  const options = [...firstFive];
  if (sixth && !shownIds.has(sixth.structure_id)) options.push(sixth);
  return options.slice(0, 6);
}

// OAD-001: every Optimizer-family structure (built by the structural
// generator) carries segments: [] and only populates component_allocations
// — this silently displayed "Optimized Qualified Spend $0" on Overview's
// OPTIMIZED card, not a real zero. Same canonical segment-first/component-
// allocation-fallback precedence Workspace's ScenarioCard already uses
// (screens/production/Workspace.jsx's qualifiedSpendRaw) — never both
// summed together (they are alternate representations, not additive).
// Multi-program QPE reconciliation: a stacked-program structure (e.g.
// Ontario OPSTC + OCASE, both claiming against the SAME underlying QPE)
// serves segments[].qpe_usd PER PROGRAM for disclosure — summing them (the
// old behavior below) silently doubles the real unique qualifying spend.
// canonical_production_view.py now serves the exact, real, already-
// reconciled union as structure.qpe_usd whenever it differs from a plain
// per-segment sum being correct; that real backend value always wins here.
// Falls back to the existing segment/component-allocation sum ONLY for a
// row persisted before this field existed — same graceful-degradation
// precedent used throughout the served view.
export function qpeOf(structure) {
  if (typeof structure.qpe_usd === "number") return structure.qpe_usd;
  return structure.segments?.length
    ? structure.segments.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0)
    : (structure.component_allocations || []).reduce((sum, ca) => sum + (ca.allocated_usd || 0), 0);
}

// OAD-002: an Optimizer-family structure carries gross_budget_usd: null (it's
// a routing/component structure, not a top-level production record) — the
// real, already-served project-wide production.gross_budget_usd is the
// correct fallback for display, never a derivation from QPE/incentive/NPC.
// The structure's own value always wins when genuinely populated; render
// "—" (the caller's job, not this function's) only when both are absent.
export function resolveGrossBudget(structure, projectGrossBudgetUsd) {
  return structure.gross_budget_usd ?? projectGrossBudgetUsd ?? null;
}

// CineGlobe Overview Top Four (final adversarial repair pass, 2026-09-03).
// Card 1-3: the three highest-ranked CURRENTLY MODELED structures, same
// existing ranking order/filter selectTopOptions already uses
// (is_directly_comparable). Card 4: the highest-value LEGITIMATE
// potentially-optimized opportunity not already shown — never fabricated,
// always sourced from real, disclosed canonical optimizer fields:
//   1. A structure carrying real conditional_programs (grants/funds with
//      their own documented_cap_usd — a genuine published ceiling, e.g.
//      Canada Media Fund/Telefilm) — ranked by total disclosed cap.
//   2. A real, disclosed treaty/co-production opportunity
//      (treaty_slug set, or the CO_PRO_OPPORTUNITY terminal status).
//   3. A currently-modeled structure with its OWN genuine rate_floor <
//      rate_ceiling gap (a real, already-resolved-by-the-optimizer
//      upside on that structure itself) not already in cards 1-3.
//   4. Fallback per item 9: the canonical next-best current modeled
//      structure (4th-ranked), same semantics as cards 1-3 — never a
//      fabricated "opportunity" when no legitimate one exists.
// `isOpportunity: true` (cases 1-2) means this card represents a real,
// disclosed pathway that is NOT current earned economics — the caller
// must render it with OPPORTUNITY status and must never format its
// figure through compactIncentiveRate (that would misrepresent a
// disclosed cap/opportunity as an earned resolved rate).
// The "top ranked, currently modeled" ordering item 9's Cards 1-3 need is
// a BROADER concept than isDirectlyComparable (which narrowly means
// "regionally/currency comparable to the production's own home
// jurisdiction" — Little Utopia's own real data has exactly ONE such
// structure, its Mauritius baseline, which made Card 1-3 collapse to a
// single entry when this reused isDirectlyComparable, caught live in the
// rendered app: header read "Top Structures 2", not 4). The correct,
// already-established convention is Workspace.jsx's own
// visibleStructures() ordering — rank first (allocated.ranking's own
// order), tie-broken by ascending NPC for a priced structure with no
// formal rank — reused here instead of a second, narrower selection
// rule, over every is_fully_priced structure.
// Exported (not just internal) so Workspace.jsx's own lane ordering can
// reuse this exact function instead of carrying a second, independently-
// maintained copy of the same rank-then-NPC rule (item 7: "Do not
// duplicate business logic independently in two React components").
export function rankOrNpcOrder(allocated) {
  return _rankOrNpcOrder(allocated);
}

function _rankOrNpcOrder(allocated) {
  const rankById = new Map((allocated.ranking || []).map((r) => [r.structure_id, r]));
  return [...allocated.structures]
    .filter((s) => s.is_fully_priced)
    .sort((a, b) => {
      const ra = rankById.get(a.structure_id)?.rank ?? Infinity;
      const rb = rankById.get(b.structure_id)?.rank ?? Infinity;
      if (ra !== rb) return ra - rb;
      const an = a.npc_with_adjustments_usd ?? Infinity;
      const bn = b.npc_with_adjustments_usd ?? Infinity;
      return an - bn;
    });
}

// F#K Valentine's Day economic/semantic regression fix (2026-09-03):
// this used to sum every conditional_programs[].documented_cap_usd and
// present the total as "Potential up to $X" — for FVD's real Manitoba
// candidate that summed FIVE unrelated NATIONAL funds' own per-project
// CEILINGS (Canada Media Fund $10M + Telefilm CFFF $5M + Telefilm Export
// $550K + Manitoba Film & Music $550K = $16.1M) for a production with a
// $4.5M total source budget — a program-wide cap sized for "major drama"
// productions much larger than this one, presented as if it were this
// project's own achievable potential. A per-project cap is real and
// disclosable, but summing several unrelated funds' own maximums (each
// independently competitive/discretionary, never simultaneously
// guaranteed) is not a project-level figure at all (item 5.C/5.D: a
// program cap/maximum must never be presented as the project's
// calculated incentive, and must never exceed what's mathematically
// permissible for this project). Fix: disclose the REAL fund names/count
// (still real, disclosed, non-fabricated data) without manufacturing a
// dollar figure no single fund, let alone their sum, actually guarantees
// this specific production.
export function selectMaxPotentialCard(allocated, excludeIds) {
  if (!allocated?.structures) return null;
  const recommended = allocated.recommended_optimizer_options || allocated.producer_optimizer_options || [];
  const practical = recommended.find((s) => !excludeIds.has(s.structure_id));
  if (practical) {
    return { structure: practical, isOpportunity: false, isProducerOptimizer: true, potentialUsd: null, fundCount: 0, fundNames: [] };
  }

  // No canonical recommended-optimizer candidate exists — fall back to a
  // real, disclosed conditional_programs opportunity (the Manitoba shape:
  // a structure carrying genuine per-project fund caps, e.g. Canada Media
  // Fund/Telefilm). Ranked by summed disclosed cap to surface the
  // strongest real opportunity, but per the regression fixed above, the
  // cap sum itself is NEVER shown as a dollar figure — only the real,
  // disclosed fund count/names are.
  const withPrograms = allocated.structures
    .filter((s) => !excludeIds.has(s.structure_id) && (s.conditional_programs || []).length > 0)
    .map((s) => ({
      structure: s,
      capSum: s.conditional_programs.reduce((sum, p) => sum + (p.documented_cap_usd || 0), 0),
    }))
    .sort((a, b) => b.capSum - a.capSum);
  if (withPrograms.length > 0) {
    const best = withPrograms[0].structure;
    return {
      structure: best,
      isOpportunity: true,
      isProducerOptimizer: false,
      potentialUsd: null,
      fundCount: best.conditional_programs.length,
      fundNames: best.conditional_programs.map((p) => p.program_name),
    };
  }

  return null;
}

// OVERVIEW FOUR-SLOT CONTRACT (2026-10-08, supersedes Anchor + 2 Leading + Max-Potential): four
// distinct cards in a fixed order, each filled only from structures the backend already serves:
//   1. Current Location     -- the canonical baseline (isBaselineStructure).
//   2. Leading Jurisdiction -- the lowest-NPC jurisdiction winner (best_per_jurisdiction).
//   3. Optimized Structure  -- the optimizer's own first-presented scenario (optimizerProjection,
//      the SAME ordering Workspace's Optimizer mode uses): a recommended option when one exists,
//      otherwise its top evaluated alternative, flagged as a reference so it never claims a
//      recommendation it does not have.
//   4. Conditional Upside   -- the CONDITIONAL-ceiling structure with the lowest served maximum
//      potential NPC (potential_npc_usd).
// No economic identity appears twice. A slot the served universe cannot fill is left out, never
// padded or fabricated. No figure is computed here; only served fields are compared for ordering.
const _econKey = (s) => s.economic_identity || s.structure_id;
export function selectAnchorLeadingOptimized(allocated) {
  if (!allocated?.structures) return [];
  const cards = [];
  const shownIds = new Set();
  const shownEcon = new Set();
  const isNew = (s) => s && !shownIds.has(s.structure_id) && !shownEcon.has(_econKey(s));
  const add = (s, slot, extra = {}) => {
    cards.push({ ...s, __slot: slot, ...extra });
    shownIds.add(s.structure_id);
    shownEcon.add(_econKey(s));
  };

  const anchor = allocated.structures.find(isBaselineStructure) || null;
  if (anchor) add(anchor, "Current Location");

  const winners = Object.values(allocated.best_per_jurisdiction || {})
    .filter(Boolean)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity));
  const leading = winners.find(isNew);
  if (leading) add(leading, "Leading Jurisdiction");

  const projection = optimizerProjection(allocated);
  const recommended = projection.recommended.find(isNew);
  const optimized = recommended || projection.evaluated.find(isNew);
  if (optimized) {
    add(optimized, "Optimized Structure", recommended
      ? { __isProducerOptimizer: true }
      : { __isOptimizerReference: true });
  }

  const conditional = [...allocated.structures, ...winners, ...projection.recommended, ...projection.evaluated]
    .filter((s) => s.ceiling_status === "CONDITIONAL" && s.potential_npc_usd != null && isNew(s))
    .sort((a, b) => a.potential_npc_usd - b.potential_npc_usd)[0];
  if (conditional) add(conditional, "Conditional Upside", { __isConditionalUpside: true });

  return cards;
}

// Card status — the restored ANCHOR/LEADING/LEADING/OPTIMIZED vocabulary
// (item 10 of the prior pass's LEADING/OPTIMIZE/VIABLE/OPPORTUNITY
// wording is superseded by this history-based restoration). `cardIndex`
// is the position selectAnchorLeadingOptimized itself returned the
// structure at — never re-derived from array order elsewhere, so Anchor
// can never be assigned to array position 0 by accident when
// selectAnchorLeadingOptimized had no real baseline to put there (the
// `isBaselineStructure` check below is the actual authority, cardIndex
// is only a hint consistent with it by construction).
// Runtime wiring remediation (unresolved-calculation promotion): the bare
// "LEADING" fallback below previously applied unconditionally to ANY
// non-baseline, non-opportunity/optimizer card — including a structure
// whose incentive is not yet confirmed, via ANY of three real, distinct,
// backend-disclosed unresolved-calculation states:
//   1. hasAdministrativeAllocationRisk — an award authority's own
//      discretion, a competitive/capacity-limited allocation, or a
//      mandatory preapproval step (the SAME generic detector Workspace/
//      IncentiveIntelligence already use for the "requires confirmation"
//      caption).
//   2. structure.legal_review_required — a hard statutory VIOLATION/
//      mutual-exclusivity finding on a multi-program stack
//      (canonical_stack_bridge.py's MultiProgramStackResult.legal_
//      review_required, served verbatim by canonical_production_view.py).
//   3. hasUnconfirmedStackingDeduction — a GENUINELY DIFFERENT disclosure
//      from #2 despite the similar name: a real statutory stacking-
//      deduction rule was found between two stacked programs but could
//      not be applied by the reused spend_reduction calculator, so the
//      served adjusted_incentive_usd is not confirmed net of it. A live
//      production's real Ontario OFTTC+OCASE stack served exactly this
//      state with legal_review_required=FALSE (state 2 does not cover
//      it) alongside a confident "LEADING"/"Top Priced" badge — caught
//      only by matching the disclosure's own prose, since no dedicated
//      boolean field exists for it.
// ANCHOR and OPTIMIZED are untouched — a baseline's ANCHOR status is a
// factual "this is the production's own current base" designation, never
// a confidence/recommendation claim (Little Utopia's own Mauritius
// baseline carries real administrative risk and is still honestly
// ANCHOR), and OPTIMIZED's existing selection criteria are a separate,
// already-established contract this fix does not reopen.
export function cardStatus(structure, cardIndex) {
  if (structure.__isOpportunity) return "OPTIMIZED";
  if (structure.__isConditionalUpside) return "CONDITIONAL";
  // The optimizer's top evaluated alternative (no recommended option served): never a confident
  // OPTIMIZED claim while its maximum is still conditional.
  if (structure.__isOptimizerReference) {
    return structure.ceiling_status === "CONDITIONAL" || structure.economics_certainty === "CONDITIONAL"
      || hasAdministrativeAllocationRisk(structure) || structure.legal_review_required
      ? "CONDITIONAL" : "OPTIMIZED";
  }
  if (cardIndex === 0 && isBaselineStructure(structure)) return "ANCHOR";
  if (structure.__isProducerOptimizer) return "OPTIMIZED";
  if (
    hasAdministrativeAllocationRisk(structure)
    || structure.legal_review_required
    || hasUnconfirmedStackingDeduction(structure)
  ) return "CONDITIONAL";
  return "LEADING";
}

// GW-OI-002/003: Overview's four/six "Featured" cards were the ONLY
// optimizer-universe presentation — a real producer had no way to see that
// e.g. Little Utopia has 171 executable optimizer scenarios (66
// Recommended, 105 Evaluated Alternatives) and 25 real Official
// Co-production opportunities still needing facts, or that
// OFFICIAL_COPRODUCTION/COMBINED_COPRO_HYBRID_STACK/
// MULTI_PRINCIPAL_MULTILATERAL are real, defined families genuinely at
// zero for this production (never fabricated, never silently omitted).
// Sources EXCLUSIVELY existing served aggregate fields
// (optimizer_scenarios_by_family/_by_tier, the recommended/evaluated/
// needs-more-facts totals, top_by_structural_family for a real
// representative) — no new economics, no re-derivation, no recomputed
// counts; this is a pure presentation adapter over data the backend
// already serves.
export const OPTIMIZER_FAMILIES = [
  "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
];
export const PRACTICALITY_TIERS = ["PRACTICAL_HYBRID", "FORMAL_COPRODUCTION", "ADVANCED_MULTI_JURISDICTION"];

export function buildOptimizerCategorySummary(allocated) {
  if (!allocated) return null;
  const byFamily = allocated.optimizer_scenarios_by_family || {};
  const byTier = allocated.optimizer_scenarios_by_tier || {};
  const topByFamily = allocated.top_by_structural_family || {};
  const families = OPTIMIZER_FAMILIES.map((key) => ({
    key,
    executableCount: byFamily[key] ?? 0,
    // top_by_structural_family[key] is the backend's own real ranked
    // representative list for this family (never re-ranked here) — the
    // first entry is the single best real representative, or null when
    // the family is genuinely empty for this production.
    representative: (topByFamily[key] || [])[0] || null,
  }));
  const tiers = PRACTICALITY_TIERS.map((key) => ({ key, executableCount: byTier[key] ?? 0 }));
  return {
    families,
    tiers,
    executableTotal: allocated.optimizer_executable_total ?? 0,
    recommendedTotal: allocated.recommended_optimizer_options_total ?? 0,
    evaluatedTotal: allocated.evaluated_optimizer_alternatives_total ?? 0,
    needsMoreFactsTotal: allocated.optimizer_opportunities_requiring_facts_total ?? 0,
  };
}

// Single Jurisdiction mode's own category picture — far simpler (no
// family/tier axes; every winner is by construction the single best
// executable candidate for its own jurisdiction) but the same principle:
// the real winner count/uniqueness, sourced from the existing served
// best_per_jurisdiction projection, never re-derived from the bounded
// structures[] page.
// GW-OI-005: exact-NPC ties are not automatically the same economic
// outcome. A same-NPC group of routes must be classified, never blindly
// collapsed on NPC alone (a materially different QPE/incentive/status pair
// sharing the same final NPC is a coincidence, not a duplicate) and never
// left as an undifferentiated wall of visually-identical rows either (a
// group that genuinely shares every economic figure is presentation
// noise, not N different producer decisions). Sources only the structure's
// own already-served fields (qpeOf's existing canonical precedence,
// selected_incentive_usd, npc_with_adjustments_usd, recommendation_status,
// candidate_status) — never a new economic derivation, never touches
// economic_identity itself.
function economicSignature(structure) {
  return [
    structure.npc_with_adjustments_usd ?? "",
    qpeOf(structure),
    structure.selected_incentive_usd ?? "",
    structure.recommendation_status ?? "",
    structure.candidate_status ?? "",
  ].join("|");
}

export function classifyRouteTies(structures) {
  const byNpc = new Map();
  for (const s of structures || []) {
    const npc = s.npc_with_adjustments_usd;
    if (npc == null) continue;
    if (!byNpc.has(npc)) byNpc.set(npc, []);
    byNpc.get(npc).push(s);
  }
  const groups = [];
  for (const [npc, members] of byNpc) {
    if (members.length < 2) continue; // not a tie at all
    const bySignature = new Map();
    for (const s of members) {
      const sig = economicSignature(s);
      if (!bySignature.has(sig)) bySignature.set(sig, []);
      bySignature.get(sig).push(s);
    }
    const signatureGroups = [...bySignature.values()];
    // A stable, deterministic representative/order for compact surfaces —
    // never structure_id or enumeration order: economic_identity is the
    // one field guaranteed both present and stable per real distinct route.
    for (const sg of signatureGroups) sg.sort((a, b) => String(a.economic_identity || "").localeCompare(String(b.economic_identity || "")));
    if (signatureGroups.length === 1) {
      groups.push({ type: "EQUIVALENT_ROUTE_VARIANTS", npc, members: signatureGroups[0], representative: signatureGroups[0][0] });
    } else {
      groups.push({
        type: "NPC_ONLY_TIE",
        npc,
        members,
        // Each distinct real economic outcome sharing this NPC, in the
        // same stable order — an NPC-only tie never collapses these. Each
        // variant carries its OWN full member list (a variant can itself
        // contain more than one economically-identical route), so a
        // consumer collapsing equivalent variants within an NPC tie has
        // every real structure_id to mark, never just the representative.
        variants: signatureGroups.map((sg) => ({ representative: sg[0], members: sg, equivalentCount: sg.length })),
      });
    }
  }
  return groups;
}

export function buildSingleJurisdictionCategorySummary(allocated) {
  if (!allocated) return null;
  const winners = Object.values(allocated.best_per_jurisdiction || {}).filter(Boolean);
  const stackedProgramCount = (allocated.top_by_structural_family?.STACKED_PROGRAMS || []).length;
  return {
    winnerCount: winners.length,
    uniqueJurisdictionCount: new Set(winners.map((w) => w.primary_jurisdiction)).size,
    stackedProgramCount,
  };
}
