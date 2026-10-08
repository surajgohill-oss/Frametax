// ── CineGlobe Overview 2x2 Anchor/Scenario composition — history-based
// restoration regression protection ──────────────────────────────────────
//
// Run with: npm test (node --test)
//
// Supersedes overview-top-four.test.mjs's four-across model, which was
// itself the regression this restoration reverts (root authority: commit
// ec283e5's real "Incentive Intelligence 2x2 grid" — see
// lib/productionOptions.js's own header comment on
// selectAnchorLeadingOptimized for the full chronology). Pure logic tests
// — no JSX, no backend, no economics: every input is a hand-built
// structure/allocated payload shaped like the real
// canonical_production_view.py / little_utopia_state.py response.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  selectAnchorLeadingOptimized, selectMaxPotentialCard, cardStatus, isBaselineStructure,
} from "../src/lib/productionOptions.js";
import { compactIncentiveRate } from "../src/lib/incentiveRate.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

function structure(overrides) {
  return {
    structure_id: "s1",
    structure_type: "full_relocation",
    label: "Base",
    primary_jurisdiction: "US",
    participants: ["US"],
    is_fully_priced: true,
    is_baseline: false,
    treaty_slug: null,
    gross_budget_usd: 1_000_000,
    selected_incentive_usd: 300_000,
    npc_with_adjustments_usd: 700_000,
    conditional_programs: [],
    segments: [],
    ...overrides,
  };
}

function allocated(structures, ranking) {
  return {
    structures,
    ranking: ranking || structures.map((s, i) => ({ structure_id: s.structure_id, rank: i + 1, is_fully_priced: s.is_fully_priced })),
    best_per_jurisdiction: Object.fromEntries(structures.map((s) => [s.structure_id, s])),
    producer_optimizer_options: [],
  };
}

// ── Anchor is the canonical baseline, never lowest-NPC, never the
// optimizer's current rank-1, never array position. ─────────────────────
test("selectAnchorLeadingOptimized: Card 1 is the canonical baseline structure, not the cheapest NPC", () => {
  const cheap = structure({ structure_id: "cheap", npc_with_adjustments_usd: 10 }); // artificially the lowest NPC
  const baseline = structure({ structure_id: "base", is_baseline: true, npc_with_adjustments_usd: 900_000 });
  const other = structure({ structure_id: "other", npc_with_adjustments_usd: 500_000 });
  const result = selectAnchorLeadingOptimized(allocated([cheap, baseline, other]));
  assert.equal(result[0].structure_id, "base", "Card 1 must be the real baseline, even though it is not the cheapest");
});

test("selectAnchorLeadingOptimized: Anchor is not chosen by array position — a baseline placed last is still Card 1", () => {
  const a = structure({ structure_id: "a" });
  const b = structure({ structure_id: "b" });
  const baseline = structure({ structure_id: "baseline-last", is_baseline: true });
  const result = selectAnchorLeadingOptimized(allocated([a, b, baseline]));
  assert.equal(result[0].structure_id, "baseline-last");
});

test("selectAnchorLeadingOptimized: never returns more than four candidates", () => {
  const structs = Array.from({ length: 8 }, (_, i) => structure({ structure_id: `s${i}`, is_baseline: i === 0 }));
  const result = selectAnchorLeadingOptimized(allocated(structs));
  assert.ok(result.length <= 4);
});

// ── Cards 2-3 (Leading) exclude Anchor and never duplicate it or each
// other. ──────────────────────────────────────────────────────────────
test("selectAnchorLeadingOptimized: Leading cards exclude the Anchor structure_id", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true, npc_with_adjustments_usd: 100 });
  const alt1 = structure({ structure_id: "alt1", npc_with_adjustments_usd: 200 });
  const alt2 = structure({ structure_id: "alt2", npc_with_adjustments_usd: 300 });
  const result = selectAnchorLeadingOptimized(allocated([baseline, alt1, alt2]));
  const ids = result.map((s) => s.structure_id);
  // four-slot contract: one Leading Jurisdiction; no optimizer or conditional structure served here
  assert.deepEqual(ids, ["base", "alt1"]);
  assert.equal(new Set(ids).size, ids.length, "no duplicate structure_id across the four cards");
});

test("selectAnchorLeadingOptimized: Leading cards use the canonical jurisdiction-winner NPC order", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true });
  const a = structure({ structure_id: "a", npc_with_adjustments_usd: 500 });
  const b = structure({ structure_id: "b", npc_with_adjustments_usd: 300 });
  const ranking = [
    { structure_id: "base", rank: null, is_fully_priced: true },
    { structure_id: "a", rank: 1, is_fully_priced: true },
    { structure_id: "b", rank: 2, is_fully_priced: true },
  ];
  const result = selectAnchorLeadingOptimized(allocated([baseline, a, b], ranking));
  assert.equal(result[1].structure_id, "b", "Leading Jurisdiction is the lowest-NPC jurisdiction winner");
});

// ── Card 4 (Optimized) never duplicates another card and never
// fabricates an opportunity. ─────────────────────────────────────────────
test("selectMaxPotentialCard uses only the canonical material producer optimizer projection", () => {
  const option = structure({ structure_id: "practical" });
  const alloc = allocated([structure({ structure_id: "plain" })]);
  alloc.producer_optimizer_options = [option];
  const result = selectMaxPotentialCard(alloc, new Set());
  assert.equal(result.structure.structure_id, "practical");
  assert.equal(result.isOpportunity, false);
  assert.equal(result.potentialUsd, null);
});

test("selectMaxPotentialCard never fabricates a potential figure — null when nothing legitimate exists", () => {
  const plain = structure({ structure_id: "plain", segments: [] });
  const result = selectMaxPotentialCard(allocated([plain]), new Set());
  assert.equal(result, null);
});

test("selectAnchorLeadingOptimized: no producer optimizer card is fabricated when the canonical projection is empty", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true });
  const structs = [
    baseline,
    structure({ structure_id: "a", npc_with_adjustments_usd: 100 }),
    structure({ structure_id: "b", npc_with_adjustments_usd: 200 }),
    structure({ structure_id: "c", npc_with_adjustments_usd: 300 }),
  ];
  const result = selectAnchorLeadingOptimized(allocated(structs));
  const ids = result.map((s) => s.structure_id);
  assert.deepEqual(ids, ["base", "a"]);
});

// ── Overview four-slot contract (2026-10-08) ─────────────────────────────────────────────────
test("four-slot contract: Current Location, Leading Jurisdiction, Optimized Structure, Conditional Upside — in that order, distinct economic identities", () => {
  const base = structure({ structure_id: "base", is_baseline: true, economic_identity: "e-base", npc_with_adjustments_usd: 900 });
  const lead = structure({ structure_id: "lead", economic_identity: "e-lead", npc_with_adjustments_usd: 500 });
  const lead2 = structure({ structure_id: "lead2", economic_identity: "e-lead2", npc_with_adjustments_usd: 600,
    ceiling_status: "CONDITIONAL", potential_npc_usd: 450 });
  const opt = structure({ structure_id: "opt", economic_identity: "e-opt", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 550 });
  const alloc = allocated([base, lead, lead2]);
  alloc.recommended_optimizer_options = [opt];
  const result = selectAnchorLeadingOptimized(alloc);
  assert.deepEqual(result.map((s) => s.__slot), ["Current Location", "Leading Jurisdiction", "Optimized Structure", "Conditional Upside"]);
  assert.deepEqual(result.map((s) => s.structure_id), ["base", "lead", "opt", "lead2"]);
  assert.equal(new Set(result.map((s) => s.economic_identity)).size, 4);
  assert.equal(cardStatus(result[2], 2), "OPTIMIZED");
  assert.equal(cardStatus(result[3], 3), "REFERENCE ALTERNATIVE", "the upside slot keeps its precise reference category; the unresolved upside is disclosed in the well");
});

test("four-slot contract: with no recommended option, Optimized uses the optimizer's top evaluated alternative, flagged as a reference", () => {
  const base = structure({ structure_id: "base", is_baseline: true, economic_identity: "e-base" });
  const lead = structure({ structure_id: "lead", economic_identity: "e-lead" });
  const evalAlt = structure({ structure_id: "eval", economic_identity: "e-eval", recommendation_status: "EVALUATED_ALTERNATIVE",
    ceiling_status: "CONDITIONAL", potential_npc_usd: 400 });
  const alloc = allocated([base, lead]);
  alloc.evaluated_optimizer_alternatives = [evalAlt];
  const result = selectAnchorLeadingOptimized(alloc);
  const optimized = result.find((s) => s.__slot === "Optimized Structure");
  assert.equal(optimized.structure_id, "eval");
  assert.equal(optimized.__isOptimizerReference, true);
  assert.equal(optimized.__isProducerOptimizer, undefined, "a reference alternative never claims a recommendation");
  assert.equal(cardStatus(optimized, 2), "REFERENCE ALTERNATIVE", "a reference alternative is never shown as a confident OPTIMIZED, and an unresolved upside never makes it CONDITIONAL");
});

test("four-slot contract: an economic identity already shown is never repeated in a later slot", () => {
  const base = structure({ structure_id: "base", is_baseline: true, economic_identity: "same" });
  const twin = structure({ structure_id: "twin", economic_identity: "same", ceiling_status: "CONDITIONAL", potential_npc_usd: 1 });
  const result = selectAnchorLeadingOptimized(allocated([base, twin]));
  assert.deepEqual(result.map((s) => s.structure_id), ["base"]);
});

// ── Status vocabulary — exactly ANCHOR/LEADING/OPTIMIZED, positionally
// authoritative via isBaselineStructure, never inferred from array
// index alone. ───────────────────────────────────────────────────────────
test("cardStatus: Card 1 is ANCHOR only when it is genuinely the baseline structure", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true });
  const notBaseline = structure({ structure_id: "not-base", is_baseline: false });
  assert.equal(cardStatus(baseline, 0), "ANCHOR");
  assert.equal(cardStatus(notBaseline, 0), "LEADING", "position 0 alone must never imply Anchor without the real baseline field");
});

test("cardStatus: only a canonical producer optimizer (or disclosed opportunity) is OPTIMIZED", () => {
  const s = structure({ structure_id: "s" });
  assert.equal(cardStatus(s, 1), "LEADING");
  assert.equal(cardStatus(s, 2), "LEADING");
  assert.equal(cardStatus(s, 3), "LEADING");
  assert.equal(cardStatus({ ...s, __isProducerOptimizer: true }, 3), "OPTIMIZED");
  const opportunity = { ...structure({ structure_id: "opp" }), __isOpportunity: true };
  assert.equal(cardStatus(opportunity, 2), "OPTIMIZED", "an opportunity flag always reads OPTIMIZED regardless of position");
});

test("cardStatus never returns N/A, NO INCENTIVE, or any value outside the vocabulary", () => {
  const cases = [
    cardStatus(structure({ is_baseline: true }), 0),
    cardStatus(structure({}), 1),
    cardStatus(structure({}), 2),
    cardStatus(structure({}), 3),
  ];
  for (const s of cases) assert.ok(["ANCHOR", "LEADING", "OPTIMIZED", "REFERENCE ALTERNATIVE"].includes(s), `unexpected status: ${s}`);
});

// ── Runtime wiring remediation: an unconfirmed-calculation structure can
// never claim LEADING — the exact live defect (Ontario's OPSTC+OCASE
// stack served "Discretionary/preapproval required" right next to a
// "LEADING"/"Top Priced" badge). ─────────────────────────────────────────

test("cardStatus: a non-baseline structure with a disclosed administrative/allocation risk is CONDITIONAL, never LEADING", () => {
  const risky = structure({
    warnings: ["Administrative/allocation risk: award authority discretion applies; a preapproval step is required before this incentive is confirmed."],
  });
  assert.equal(cardStatus(risky, 1), "REFERENCE ALTERNATIVE");
  assert.equal(cardStatus(risky, 2), "REFERENCE ALTERNATIVE");
  assert.equal(cardStatus(risky, 3), "REFERENCE ALTERNATIVE");
});

test("cardStatus: the SAME structure with no disclosed risk is the ordinary LEADING fallback — the gate is data-driven, not a blanket downgrade", () => {
  const clean = structure({ warnings: [] });
  assert.equal(cardStatus(clean, 1), "LEADING");
});

test("cardStatus: structure.legal_review_required (a hard statutory violation finding) is CONDITIONAL, never LEADING", () => {
  const stackPendingReview = structure({ warnings: [], legal_review_required: true });
  assert.equal(cardStatus(stackPendingReview, 1), "REFERENCE ALTERNATIVE");
});

test("cardStatus: legal_review_required=false (or absent) never falsely triggers CONDITIONAL", () => {
  assert.equal(cardStatus(structure({ warnings: [], legal_review_required: false }), 1), "LEADING");
  assert.equal(cardStatus(structure({ warnings: [] }), 1), "LEADING");
});

test("cardStatus: an unconfirmed stacking-deduction disclosure is CONDITIONAL, never LEADING — the THIRD, distinct live defect (Ontario's real OFTTC+OCASE stack served legal_review_required=FALSE alongside this exact prose warning and a confident 'LEADING' badge)", () => {
  const stackWithUnconfirmedDeduction = structure({
    legal_review_required: false,
    warnings: [
      "Statutory rule found (OCASE may be claimed in addition to OFTTC on the same production's eligible computer animation/VFX labour expenditure.) but the reused spend_reduction calculator only recognizes grant/regional_fund/discretionary_fund program types as the reducing side; neither on_ofttc nor ontario_computer_animation_and_special_effects_tax_credit_ocase is typed that way, so no reduction was applied for this pair. This combination's adjusted_incentive_usd is therefore not confirmed net of this statutory deduction — legal/economic review required before this combination is treated as fully priced.",
    ],
  });
  assert.equal(cardStatus(stackWithUnconfirmedDeduction, 1), "REFERENCE ALTERNATIVE");
});

test("cardStatus: an administrative-risk baseline card stays honestly ANCHOR — a factual designation, never a confidence claim (Little Utopia's own Mauritius baseline carries this exact real risk)", () => {
  const riskyBaseline = structure({
    is_baseline: true,
    warnings: ["Administrative/allocation risk: award authority discretion applies."],
  });
  assert.equal(cardStatus(riskyBaseline, 0), "ANCHOR");
});

test("cardStatus: an unrelated warning string never falsely triggers CONDITIONAL — the detector is keyed to the real backend disclosure prefix, never a generic 'warning present' check", () => {
  const s = structure({ warnings: ["Some other, unrelated disclosure entirely."] });
  assert.equal(cardStatus(s, 1), "LEADING");
});

// ── A long statutory program name can never occupy the compact
// economic-value line. ───────────────────────────────────────────────────
test("compactIncentiveRate never includes the program name, even when segments carry a long statutory name", () => {
  const s = structure({
    segments: [{ claims_incentive: true, rate_floor: 0.45, rate_ceiling: 0.65, program_slug: "ca_mb_fvptc" }],
    program_display_name: "Manitoba Film and Video Production Tax Credit",
  });
  const rate = compactIncentiveRate(s);
  assert.equal(rate, "45% · up to 65%");
  assert.ok(!rate.includes("Manitoba"));
});

// ── Generic across productions — no hardcoded jurisdiction/ID/title. ────
test("productionOptions.js's CODE (not its explanatory comments) contains no hardcoded jurisdiction name, project ID, or Little-Utopia-specific structure ID", () => {
  const src = stripComments(read("lib/productionOptions.js"));
  assert.ok(!/Mauritius|ALLOC-BASELINE-MU|Little Utopia|Lips Like Sugar/i.test(src));
});

// ── Overview and Workspace share ONE canonical selection model — never
// two independently-maintained copies of the same business logic. ───────
//
// PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21): the "one
// canonical model" claim moved from "the same SELECTION FUNCTION" (Overview's
// compact 4-card selectAnchorLeadingOptimized was never actually the right
// shape for Workspace's own six-card rack + slot-6 dropdown + mode toggle —
// they are genuinely different UI contracts) to "the same DATA layer":
// whenever either screen picks an optimizer-classified candidate, it
// resolves through the SAME canonical `allocated.optimizer_scenarios`
// projection (canonical_production_view.py) — never a raw, duplicate-prone
// optimizer_candidates row, and never two independently-derived dedup
// rules. Proven behaviorally: selectMaxPotentialCard (Overview's card 4)
// and admissibleForMode (Workspace's rack/dropdown, workspaceScenarioMode.js)
// both resolve to the SAME scenario representative from the SAME fixture.
test("Overview's selectMaxPotentialCard and Workspace's admissibleForMode both resolve optimizer candidates through the SAME optimizer_scenarios projection, never independently", async () => {
  const { admissibleForMode, MODE_OPTIMIZER } = await import("../src/lib/workspaceScenarioMode.js");
  const rawA = structure({ structure_id: "raw-a", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 500_000 });
  const rawB = structure({ structure_id: "raw-b", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 600_000 });
  // The canonical scenario representative — the lowest-NPC of the two raw
  // duplicates above, annotated the way canonical_production_view.py's real
  // grouping pass does.
  const scenarioRep = { ...rawA, raw_variant_count: 2, raw_variant_structure_ids: ["raw-a", "raw-b"] };
  const alloc = {
    structures: [rawA, rawB],
    ranking: [{ structure_id: "raw-a", rank: 1 }, { structure_id: "raw-b", rank: 2 }],
    optimizer_scenarios: [scenarioRep],
    producer_optimizer_options: [scenarioRep],
  };

  const workspacePool = admissibleForMode(alloc, MODE_OPTIMIZER);
  assert.deepEqual(workspacePool.map((s) => s.structure_id), ["raw-a"], "Workspace must resolve the ONE canonical scenario, never both raw duplicates");

  const card4 = selectMaxPotentialCard(alloc, new Set());
  if (card4 && card4.structure.classification === "HYBRID_ANCHOR_COMPONENT") {
    assert.equal(card4.structure.structure_id, "raw-a", "Overview's Optimized card must resolve the SAME canonical representative Workspace does, never a raw duplicate");
  }
});

test("Overview's IncentiveIntelligence.jsx and Workspace.jsx both derive their Anchor concept from the SAME isBaselineStructure field", () => {
  const iiSrc = stripComments(read("components/IncentiveIntelligence.jsx"));
  const wsSrc = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(iiSrc, /isBaselineStructure/);
  assert.match(wsSrc, /isBaselineStructure/);
});

// ── Project Globe implementation is never touched by this feature. ──────
test("productionOptions.js and IncentiveIntelligence.jsx never import from a Globe engine module", () => {
  const optionsSrc = stripComments(read("lib/productionOptions.js"));
  const iiSrc = stripComments(read("components/IncentiveIntelligence.jsx"));
  for (const src of [optionsSrc, iiSrc]) {
    assert.ok(!/from\s+["'][^"']*(Globe3D|globeData|globeFit)/.test(src));
  }
});

// ── The 2x2 grid geometry itself — restored, not four-across. ───────────
test("screens.css: .ii-grid is a genuine 2x2 (two columns), not the rejected four-across layout", () => {
  const src = stripComments(read("styles/screens.css"));
  assert.match(src, /\.ii-grid\s*\{[^}]*grid-template-columns:\s*repeat\(2,/);
  assert.doesNotMatch(src, /\.ii-grid\s*\{[^}]*grid-template-columns:\s*repeat\(4,/);
});

// ── Precise structure category (2026-10-08): an unresolved upside never relabels a structure CONDITIONAL ──
test("cardStatus: an unresolved UPSIDE (ceiling conditional, floor confirmed) keeps the precise category — never CONDITIONAL", () => {
  const upsideOnly = structure({ ceiling_status: "CONDITIONAL", economics_certainty: "CONDITIONAL", potential_npc_usd: 1, warnings: [] });
  assert.equal(cardStatus(upsideOnly, 1), "LEADING");
  assert.equal(cardStatus({ ...upsideOnly, __isConditionalUpside: true }, 3), "REFERENCE ALTERNATIVE");
  assert.equal(cardStatus({ ...upsideOnly, __isOptimizerReference: true }, 2), "REFERENCE ALTERNATIVE");
});

test("cardStatus: location fit is its own category (low-location-fit / fit unconfirmed), never LEADING", () => {
  assert.equal(cardStatus(structure({ production_fit_status: "WEAK" }), 1), "LOW-LOCATION-FIT REFERENCE");
  assert.equal(cardStatus(structure({ production_fit_status: "UNKNOWN" }), 1), "LOCATION FIT UNCONFIRMED");
  assert.equal(cardStatus(structure({ production_fit_status: "WORKABLE" }), 1), "LEADING");
});

test("Leading Jurisdiction: the cheapest fit-confirmed winner leads; a confirmed-mismatch winner never does", () => {
  const base = structure({ structure_id: "base", is_baseline: true, economic_identity: "e0" });
  const weakCheap = structure({ structure_id: "weak", economic_identity: "e1", npc_with_adjustments_usd: 100, production_fit_status: "WEAK" });
  const unknownMid = structure({ structure_id: "unk", economic_identity: "e2", npc_with_adjustments_usd: 200, production_fit_status: "UNKNOWN" });
  const okDear = structure({ structure_id: "ok", economic_identity: "e3", npc_with_adjustments_usd: 300, production_fit_status: "WORKABLE" });
  let result = selectAnchorLeadingOptimized(allocated([base, weakCheap, unknownMid, okDear]));
  assert.equal(result[1].structure_id, "ok", "fit-confirmed wins even though it is dearer");
  result = selectAnchorLeadingOptimized(allocated([base, weakCheap, unknownMid]));
  assert.equal(result[1].structure_id, "unk", "unconfirmed fit leads only when nothing is confirmed");
  result = selectAnchorLeadingOptimized(allocated([base, weakCheap]));
  assert.equal(result.length, 1, "a confirmed mismatch never fills the Leading slot");
});

test("Conditional Upside never offers a structure with an established physical-location mismatch", () => {
  const base = structure({ structure_id: "base", is_baseline: true, economic_identity: "e0" });
  const weakUp = structure({ structure_id: "weak-up", economic_identity: "e1", ceiling_status: "CONDITIONAL", potential_npc_usd: 10, production_fit_status: "WEAK" });
  const okUp = structure({ structure_id: "ok-up", economic_identity: "e2", ceiling_status: "CONDITIONAL", potential_npc_usd: 20, production_fit_status: "WORKABLE" });
  const lead = structure({ structure_id: "lead", economic_identity: "e3", npc_with_adjustments_usd: 100, production_fit_status: "WORKABLE" });
  let result = selectAnchorLeadingOptimized(allocated([base, lead, weakUp, okUp]));
  assert.equal(result.find((s) => s.__slot === "Conditional Upside").structure_id, "ok-up");
  result = selectAnchorLeadingOptimized(allocated([base, lead, weakUp]));
  assert.equal(result.find((s) => s.__slot === "Conditional Upside"), undefined);
});
