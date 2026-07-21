// Minimal regression coverage for Today's Hero and FX computation. Plain
// Node + assert — this frontend has no test runner installed, and one is
// deliberately not introduced here (see lib/todayCompute.js). Run with:
//   node scripts/test_today_compute.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { HERO_STAGE_KEYS, buildHeroStages, FX_STRIP_CODES, buildFxItems } from "../src/lib/todayCompute.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
let failures = 0;
function test(name, fn) {
  try {
    fn();
    console.log(`ok   - ${name}`);
  } catch (err) {
    failures++;
    console.log(`FAIL - ${name}`);
    console.log(`       ${err.message}`);
  }
}

const STATUSES = [
  { key: "evaluation", label: "Evaluation" },
  { key: "development", label: "Development" },
  { key: "packaging", label: "Packaging" },
  { key: "pre_production", label: "Pre-Production" },
  { key: "production", label: "Production" },
  { key: "post_production", label: "Post-Production" },
  { key: "delivery", label: "Delivery" },
  { key: "released", label: "Released" },
  { key: "archived", label: "Archived" },
];

// ── Hero: exact labels, exact order ────────────────────────────────────
test("hero stage keys are exactly Evaluation, Development, Production, in that order", () => {
  assert.deepEqual(HERO_STAGE_KEYS, ["evaluation", "development", "production"]);
});

test("Evaluation precedes Development in hero stage order", () => {
  assert.ok(HERO_STAGE_KEYS.indexOf("evaluation") < HERO_STAGE_KEYS.indexOf("development"));
});

test("no unauthorized hero labels (Shaping / Active Production / Wrapping / Archived)", () => {
  const stages = buildHeroStages(STATUSES, []);
  const labels = stages.map((s) => s.label);
  for (const banned of ["Shaping", "Active Production", "Wrapping", "Archived"]) {
    assert.ok(!labels.includes(banned), `unauthorized label rendered: ${banned}`);
  }
  assert.deepEqual(labels, ["Evaluation", "Development", "Production"]);
});

test("Little Utopia (Evaluation, $4,364,393) aggregates correctly under Evaluation only", () => {
  const productions = [{ stageMeta: { key: "evaluation" }, budget: 4364393 }];
  const stages = buildHeroStages(STATUSES, productions);
  const byKey = Object.fromEntries(stages.map((s) => [s.key, s]));
  assert.equal(byKey.evaluation.count, 1);
  assert.equal(byKey.evaluation.budget, 4364393);
  assert.equal(byKey.development.count, 0);
  assert.equal(byKey.development.budget, 0);
  assert.equal(byKey.production.count, 0);
  assert.equal(byKey.production.budget, 0);
});

// ── FX strip ────────────────────────────────────────────────────────────
test("FX strip contains exactly EUR, CAD, GBP in that order", () => {
  assert.deepEqual(FX_STRIP_CODES, ["EUR", "CAD", "GBP"]);
});

test("real EUR/GBP snapshots render as available; CAD (no real data) renders unavailable, never fabricated", () => {
  const fxHorizons = {
    MUR: { current: 47.05, "1m": null, "6m": null, "12m": null },
    EUR: { current: 0.87679, "1m": 0.86453, "6m": 0.85807, "12m": 0.85594 },
    GBP: { current: 0.74699, "1m": 0.74613, "6m": 0.74309, "12m": 0.74099 },
  };
  const items = buildFxItems(fxHorizons);
  const byCode = Object.fromEntries(items.map((it) => [it.code, it]));
  assert.equal(byCode.EUR.available, true);
  assert.equal(byCode.EUR.current, 0.87679);
  assert.equal(byCode.GBP.available, true);
  assert.equal(byCode.CAD.available, false, "CAD has no real snapshot anywhere in this codebase — must render unavailable");
  assert.equal(byCode.CAD.current, undefined, "unavailable CAD must not carry a fabricated rate");
});

// ── Source-shape guards: don't reintroduce the legacy-ranking bug ──────
// Comments are stripped before these checks — this file's own comments
// legitimately mention "structures.ranking" and "fx_horizons" by name
// while explaining what NOT to do / where the real data comes from;
// only actual code should trip these guards.
const todaySrcRaw = readFileSync(join(__dirname, "../src/screens/company/Today.jsx"), "utf8");
const todaySrc = todaySrcRaw
  .split("\n")
  .map((line) => line.replace(/\/\/.*$/, ""))
  .join("\n");

test("Today.jsx reads the canonical allocated_structures ranking for Net Cost", () => {
  assert.ok(todaySrc.includes("structures.allocated_structures"), "expected structures.allocated_structures to be read");
  assert.ok(todaySrc.includes("npc_with_adjustments_usd"), "expected the canonical NPC field to be read");
});

test("Today.jsx does not read the legacy top-level structures.ranking for best/NPC", () => {
  // The only acceptable "ranking" reference is allocated.ranking (the
  // canonical one); a bare `structures.ranking` or `r.is_priceable` /
  // `conservative_npc_usd` would mean the legacy STRUCT-* pair crept
  // back in (see LESSON in the commit that fixed this originally).
  assert.ok(!todaySrc.includes("structures.ranking"), "found a reference to the legacy top-level structures.ranking");
  assert.ok(!todaySrc.includes("is_priceable"), "found the legacy is_priceable field — that belongs to the old ranking shape");
  assert.ok(!todaySrc.includes("conservative_npc_usd"), "found the legacy conservative_npc_usd field — that belongs to the old ranking shape");
});

test("FX is not duplicated in Company Intelligence (no fx_horizons read outside the FX strip build)", () => {
  const fxHorizonRefs = (todaySrc.match(/fx_horizons/g) || []).length;
  assert.equal(fxHorizonRefs, 1, `expected exactly 1 reference to fx_horizons (the FX strip build), found ${fxHorizonRefs}`);
});

test("Company Intelligence rows have no sibling .row-value column (the collapse root cause)", () => {
  const intelSectionMatch = todaySrc.match(/COMPANY INTELLIGENCE[\s\S]*$/);
  assert.ok(intelSectionMatch, "could not locate the Company Intelligence section");
  assert.ok(!intelSectionMatch[0].includes("row-value"), "found row-value inside Company Intelligence — reintroduces the collapse bug");
});

console.log("");
if (failures > 0) {
  console.log(`${failures} test(s) failed.`);
  process.exit(1);
}
console.log("All tests passed.");
