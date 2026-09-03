// ── CineGlobe Overview Top Four — final repair regression protection ────
//
// Run with: npm test (node --test)
//
// Pure logic tests for lib/productionOptions.js's Top Four selection
// (selectTopFour / selectMaxPotentialCard / cardStatus) and
// lib/format.jsx's compactIncentiveRate — no JSX, no backend, no
// economics: every input is a hand-built structure/allocated payload
// shaped like the real canonical_production_view.py / little_utopia_
// state.py response.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { selectTopFour, selectMaxPotentialCard, cardStatus } from "../src/lib/productionOptions.js";
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

// ── 1/2. Distinct currencies/rates must never collapse to one fallback ──
// (the real live-runtime defect this closeout traced and fixed was a test
// -isolation bug in the BACKEND's fx_refresh test suite corrupting the
// shared dev database with a dummy 1.5-for-every-currency fixture — see
// backend/tests/test_fx_freshness_architecture.py's own header comment.
// This frontend-side guard protects the presentation half: no literal
// fallback constant may exist in the FX rendering path.)
test("components/FXStrip.jsx and lib/todayCompute.js contain no hardcoded fallback rate constant", () => {
  const fxStripSrc = read("components/FXStrip.jsx");
  const computeSrc = read("lib/todayCompute.js");
  assert.ok(!/:\s*1\.5\b/.test(fxStripSrc), "found a literal 1.5 in FXStrip.jsx");
  assert.ok(!/:\s*1\.5\b/.test(computeSrc), "found a literal 1.5 in todayCompute.js");
});

// ── 3. Overview renders exactly four Top Four cards, never a variable
// count up to six (the prior Production Options contract) ──────────────
test("selectTopFour never returns more than four candidates", () => {
  const structs = Array.from({ length: 8 }, (_, i) =>
    structure({ structure_id: `s${i}`, primary_jurisdiction: `J${i}`, npc_with_adjustments_usd: 1_000_000 - i * 1000 }),
  );
  const result = selectTopFour(allocated(structs));
  assert.ok(result.length <= 4, `expected at most 4, got ${result.length}`);
});

test("selectTopFour returns the three highest-ranked priced structures as Cards 1-3, ordered", () => {
  const structs = [
    structure({ structure_id: "a", npc_with_adjustments_usd: 500_000 }),
    structure({ structure_id: "b", npc_with_adjustments_usd: 300_000 }),
    structure({ structure_id: "c", npc_with_adjustments_usd: 400_000 }),
  ];
  const ranking = [
    { structure_id: "b", rank: 1, is_fully_priced: true },
    { structure_id: "c", rank: 2, is_fully_priced: true },
    { structure_id: "a", rank: 3, is_fully_priced: true },
  ];
  const result = selectTopFour(allocated(structs, ranking));
  assert.deepEqual(result.slice(0, 3).map((s) => s.structure_id), ["b", "c", "a"]);
});

// ── 4. Card #4 exercises the maximum-potential path when a real,
// disclosed opportunity exists — never fabricated, never silently
// skipped in favor of the plain 4th-ranked structure. ───────────────────
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
  assert.equal(result.potentialUsd, 5_500_000);
});

test("selectMaxPotentialCard never fabricates a potential figure — falls back to null when nothing disclosed exists among candidates with no upside gap", () => {
  const plain = structure({ structure_id: "plain", segments: [] });
  const result = selectMaxPotentialCard(allocated([plain]), new Set());
  assert.equal(result, null);
});

test("selectTopFour falls back to the canonical next-best modeled structure for Card 4 when no legitimate opportunity exists (item 9's explicit fallback)", () => {
  const structs = [
    structure({ structure_id: "a", npc_with_adjustments_usd: 100 }),
    structure({ structure_id: "b", npc_with_adjustments_usd: 200 }),
    structure({ structure_id: "c", npc_with_adjustments_usd: 300 }),
    structure({ structure_id: "d", npc_with_adjustments_usd: 400 }),
  ];
  const ranking = structs.map((s, i) => ({ structure_id: s.structure_id, rank: i + 1, is_fully_priced: true }));
  const result = selectTopFour(allocated(structs, ranking));
  assert.equal(result.length, 4);
  assert.equal(result[3].structure_id, "d");
  assert.ok(!result[3].__isOpportunity, "the fallback 4th card must not be mislabeled as an opportunity");
});

// ── 5. Generic production populates Top Four without project-specific
// IDs — no hardcoded jurisdiction/structure-id branch anywhere. ─────────
test("productionOptions.js's CODE (not its explanatory comments) contains no hardcoded jurisdiction name, project ID, or Little-Utopia-specific structure ID", () => {
  const src = stripComments(read("lib/productionOptions.js"));
  assert.ok(!/Mauritius|ALLOC-BASELINE-MU|Little Utopia|Lips Like Sugar/i.test(src), "found a project/jurisdiction-specific literal in actual code, not just a historical-bug comment");
});

// ── 7. A long statutory program name can never occupy the compact
// economic-value line — compactIncentiveRate reads ONLY rate_floor/
// rate_ceiling, never program_display_name/program_slug. ───────────────
test("compactIncentiveRate never includes the program name, even when segments carry a long statutory name", () => {
  const s = structure({
    segments: [{ claims_incentive: true, rate_floor: 0.45, rate_ceiling: 0.65, program_slug: "ca_mb_fvptc" }],
    program_display_name: "Manitoba Film and Video Production Tax Credit",
  });
  const rate = compactIncentiveRate(s);
  assert.equal(rate, "45% · up to 65%");
  assert.ok(!rate.includes("Manitoba"), "the compact rate line must never include the program's name");
});

test("compactIncentiveRate: a deterministic exact rate is plain, never 'Up to'", () => {
  const s = structure({ segments: [{ claims_incentive: true, rate_floor: 0.60, rate_ceiling: 0.60 }] });
  assert.equal(compactIncentiveRate(s), "60%");
});

// ── 8. Status line — exactly the four defined states, never a fifth
// invented one, and never N/A. ───────────────────────────────────────────
test("cardStatus returns only LEADING/OPTIMIZE/VIABLE/OPPORTUNITY — never N/A or NO INCENTIVE", () => {
  const leading = structure({ structure_id: "lead" });
  const viable = structure({ structure_id: "viable", segments: [{ claims_incentive: true, rate_floor: 0.3, rate_ceiling: 0.3 }] });
  const optimize = structure({ structure_id: "optimize", segments: [{ claims_incentive: true, rate_floor: 0.3, rate_ceiling: 0.4 }] });
  const opportunity = { ...structure({ structure_id: "opp" }), __isOpportunity: true };

  assert.equal(cardStatus(leading, 0, null), "LEADING");
  assert.equal(cardStatus(viable, 1, null), "VIABLE");
  assert.equal(cardStatus(optimize, 1, null), "OPTIMIZE");
  assert.equal(cardStatus(opportunity, 3, null), "OPPORTUNITY");

  for (const s of [cardStatus(leading, 0, null), cardStatus(viable, 1, null), cardStatus(optimize, 1, null), cardStatus(opportunity, 3, null)]) {
    assert.ok(["LEADING", "OPTIMIZE", "VIABLE", "OPPORTUNITY"].includes(s), `unexpected status value: ${s}`);
  }
});

test("cardStatus: a manually-selected Leading structure overrides rank-based LEADING, not just cardIndex 0", () => {
  const s = structure({ structure_id: "second" });
  assert.equal(cardStatus(s, 1, "second"), "LEADING");
  assert.equal(cardStatus(s, 1, "someone-else"), "VIABLE");
});

// ── 9. Project Globe implementation is never touched by this feature. ──
test("productionOptions.js and IncentiveIntelligence.jsx never import from a Globe engine module", () => {
  const optionsSrc = stripComments(read("lib/productionOptions.js"));
  const iiSrc = stripComments(read("components/IncentiveIntelligence.jsx"));
  for (const src of [optionsSrc, iiSrc]) {
    assert.ok(!/from\s+["'][^"']*(Globe3D|globeData|globeFit)/.test(src), "Top Four selection/rendering must never import the Globe engine");
  }
});
