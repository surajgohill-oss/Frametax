// ── GW-OI-001 — Workspace ScenarioCard must never normalize canonical QPE
// away from qpeOf()'s real result ──────────────────────────────────────────
//
// Run with: npm test (node --test)
//
// Codex acceptance found Little Utopia's optimized Workspace Lanes/Split
// card showed Qualified Spend as $4,364,393 (== gross budget) while the
// canonical API, Overview, and Workspace Inspector all correctly showed
// $4,364,395 — a real $2 source-authored variance between the structure's
// allocated component sum (Manitoba $4,302,827 + Newfoundland & Labrador
// $9,068 + Italy $52,500 = $4,364,395) and the declared gross budget
// ($4,364,393). Root cause: ScenarioCard computed QPE locally (duplicating
// qpeOf()'s own segment-first/component-allocation-fallback logic) and then
// ran it through normalizeTrivialVariance(qualifiedSpendRaw, gross), which
// silently collapses any value within $5 of gross to gross itself — hiding
// real canonical data, not rounding noise. Fix: ScenarioCard now renders the
// exact result of the shared qpeOf() adapter, with no post-processing.
//
// Source-based assertions (no JSX renderer in this suite) — same pattern
// already established in fvd-economic-invariants.test.mjs.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { qpeOf } from "../src/lib/productionOptions.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("Workspace.jsx: ScenarioCard renders qualifiedSpend as the exact, unmodified result of the shared qpeOf() adapter", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(
    src,
    /const qualifiedSpend = qpeOf\(structure\);/,
    "qualifiedSpend must be exactly qpeOf(structure) — no local recomputation, no post-processing"
  );
  assert.match(
    src,
    /import\s*\{[^}]*\bqpeOf\b[^}]*\}\s*from\s*"\.\.\/\.\.\/lib\/productionOptions"/,
    "Workspace.jsx must import the shared qpeOf adapter from productionOptions.js — never a second, independently-maintained QPE derivation"
  );
});

test("Workspace.jsx: QPE is never passed through normalizeTrivialVariance — a real canonical value must never be silently collapsed toward gross budget", () => {
  // Check the CODE (not explanatory comments, which legitimately name the
  // removed function for historical context) — same convention already
  // established for hardcoded-name checks elsewhere in this suite.
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.doesNotMatch(
    src,
    /normalizeTrivialVariance/,
    "normalizeTrivialVariance must not appear in Workspace.jsx's code — it silently replaces a canonical QPE within $5 of gross with gross itself, hiding real source-authored variance"
  );
});

// ── Regression oracle: Little Utopia's real canonical structure shape ────
// Expected values are hand-transcribed from the governing Codex audit
// (docs/validation/CODEX_FINAL_GLOBE_WORKSPACE_OVERVIEW_INGESTION_ACCEPTANCE.md)
// and from the live canonical API — never derived from qpeOf() itself.
test("qpeOf: Little Utopia's real optimized structure preserves the exact $2 source-authored variance between QPE and gross budget — never collapsed", () => {
  const littleUtopiaOptimized = {
    structure_id: "559a49ce-6581-4e78-ad8a-733f424e0b74",
    economic_identity: "89f543279d132bcea03c6ce44cde857af6c5a31fdf369938392b36e469bbea05",
    gross_budget_usd: null, // routing/component structure — Overview/Workspace both fall back to project gross 4,364,393
    segments: [],
    component_allocations: [
      { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", allocated_usd: 4_302_827 },
      { jurisdiction_code: "CA-NL", program_slug: "ca_nl_all_spend_credit", allocated_usd: 9_068 },
      { jurisdiction_code: "IT", program_slug: "it_tax_credit_foreign", allocated_usd: 52_500 },
    ],
  };
  const gross = 4_364_393;
  const qpe = qpeOf(littleUtopiaOptimized);
  assert.equal(qpe, 4_364_395, "qpeOf must return the real component-allocation sum");
  assert.notEqual(qpe, gross, "the real QPE differs from gross by exactly $2 — this variance must survive, never be normalized to gross");
});

test("four-project Workspace QPE regression matrix: unchanged by this fix (segments-empty, component-allocation-driven)", () => {
  const cases = [
    { name: "Bad Hombres", allocations: [{ allocated_usd: 2_369_065 }, { allocated_usd: 5_000 }, { allocated_usd: 107_958 }], expected: 2_482_023 },
    { name: "F#K Valentine's Day", allocations: [{ allocated_usd: 4_497_487 }, { allocated_usd: 10_200 }, { allocated_usd: 10_000 }], expected: 4_517_687 },
    { name: "Lips Like Sugar", allocations: [{ allocated_usd: 11_736_880 }, { allocated_usd: 206_774 }, { allocated_usd: 40_000 }], expected: 11_983_654 },
  ];
  for (const c of cases) {
    const structure = { segments: [], component_allocations: c.allocations };
    assert.equal(qpeOf(structure), c.expected, `${c.name}: QPE unaffected by the Little Utopia fix`);
  }
});

// ── Precedence remains exactly as accepted (unchanged by this repair) ────
test("qpeOf precedence is unchanged by this repair: segments win, allocation fallback, neither returns zero, never double counted", () => {
  assert.equal(qpeOf({ segments: [{ qpe_usd: 100 }], component_allocations: [] }), 100);
  assert.equal(qpeOf({ segments: [], component_allocations: [{ allocated_usd: 250 }] }), 250);
  assert.equal(
    qpeOf({ segments: [{ qpe_usd: 100 }], component_allocations: [{ allocated_usd: 999 }] }),
    100,
    "segments win — never summed with component allocations"
  );
  assert.equal(qpeOf({ segments: [], component_allocations: [] }), 0);
});
