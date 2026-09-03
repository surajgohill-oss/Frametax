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
  assert.deepEqual(ids, ["base", "alt1", "alt2"]);
  assert.equal(new Set(ids).size, ids.length, "no duplicate structure_id across the four cards");
});

test("selectAnchorLeadingOptimized: Leading cards are ranked (rank-then-NPC, the same order Workspace's own rack uses)", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true });
  const a = structure({ structure_id: "a", npc_with_adjustments_usd: 500 });
  const b = structure({ structure_id: "b", npc_with_adjustments_usd: 300 });
  const ranking = [
    { structure_id: "base", rank: null, is_fully_priced: true },
    { structure_id: "a", rank: 1, is_fully_priced: true },
    { structure_id: "b", rank: 2, is_fully_priced: true },
  ];
  const result = selectAnchorLeadingOptimized(allocated([baseline, a, b], ranking));
  assert.deepEqual(result.slice(1, 3).map((s) => s.structure_id), ["a", "b"]);
});

// ── Card 4 (Optimized) never duplicates another card and never
// fabricates an opportunity. ─────────────────────────────────────────────
test("selectMaxPotentialCard prefers a structure with real disclosed conditional_programs, ranked by total documented cap", () => {
  const withFund = structure({
    structure_id: "fund",
    conditional_programs: [
      { program_name: "Regional Fund", documented_cap_usd: 5_000_000 },
      { program_name: "Export Program", documented_cap_usd: 500_000 },
    ],
  });
  const plain = structure({ structure_id: "plain" });
  const result = selectMaxPotentialCard(allocated([withFund, plain]), new Set());
  assert.equal(result.structure.structure_id, "fund");
  assert.equal(result.isOpportunity, true);
  // F#K Valentine's Day economic/semantic regression fix (2026-09-03,
  // item 4b): the total documented_cap_usd stays the internal RANKING
  // signal only (it picks WHICH structure becomes Card 4) — it must
  // never be exposed as a displayable dollar "potential" figure, since
  // summing several unrelated programs' own per-project ceilings is not
  // this project's calculated potential. The public contract is now a
  // truthful fund count/name disclosure instead.
  assert.equal(result.potentialUsd, null, "must never surface a summed-cap dollar figure as this project's potential");
  assert.equal(result.fundCount, 2);
  assert.deepEqual(result.fundNames, ["Regional Fund", "Export Program"]);
});

test("selectMaxPotentialCard never fabricates a potential figure — null when nothing legitimate exists", () => {
  const plain = structure({ structure_id: "plain", segments: [] });
  const result = selectMaxPotentialCard(allocated([plain]), new Set());
  assert.equal(result, null);
});

test("selectAnchorLeadingOptimized: Card 4 falls back to the next-best ranked alternative when no legitimate opportunity exists — never fabricated, never a duplicate of Cards 1-3", () => {
  const baseline = structure({ structure_id: "base", is_baseline: true });
  const structs = [
    baseline,
    structure({ structure_id: "a", npc_with_adjustments_usd: 100 }),
    structure({ structure_id: "b", npc_with_adjustments_usd: 200 }),
    structure({ structure_id: "c", npc_with_adjustments_usd: 300 }),
  ];
  const result = selectAnchorLeadingOptimized(allocated(structs));
  const ids = result.map((s) => s.structure_id);
  assert.equal(ids.length, 4);
  assert.equal(new Set(ids).size, 4, "Card 4 must never duplicate Cards 1-3");
  assert.ok(!result[3].__isOpportunity, "the fallback 4th card must not be mislabeled as an opportunity");
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

test("cardStatus: Cards at index 1-2 are LEADING, index 3 (or an opportunity flag) is OPTIMIZED", () => {
  const s = structure({ structure_id: "s" });
  assert.equal(cardStatus(s, 1), "LEADING");
  assert.equal(cardStatus(s, 2), "LEADING");
  assert.equal(cardStatus(s, 3), "OPTIMIZED");
  const opportunity = { ...structure({ structure_id: "opp" }), __isOpportunity: true };
  assert.equal(cardStatus(opportunity, 2), "OPTIMIZED", "an opportunity flag always reads OPTIMIZED regardless of position");
});

test("cardStatus never returns N/A, NO INCENTIVE, or any value outside the four-word vocabulary", () => {
  const cases = [
    cardStatus(structure({ is_baseline: true }), 0),
    cardStatus(structure({}), 1),
    cardStatus(structure({}), 2),
    cardStatus(structure({}), 3),
  ];
  for (const s of cases) assert.ok(["ANCHOR", "LEADING", "OPTIMIZED"].includes(s), `unexpected status: ${s}`);
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
test("Workspace.jsx imports selectAnchorLeadingOptimized from productionOptions.js rather than deriving its own anchor/leading order", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /import\s*\{[^}]*selectAnchorLeadingOptimized[^}]*\}\s*from\s*["']\.\.\/\.\.\/lib\/productionOptions["']/);
  assert.match(src, /selectAnchorLeadingOptimized\(allocated\)/);
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
