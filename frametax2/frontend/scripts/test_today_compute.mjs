// Minimal regression coverage for Today's Hero and FX computation. Plain
// Node + assert — this frontend has no test runner installed, and one is
// deliberately not introduced here (see lib/todayCompute.js). Run with:
//   node scripts/test_today_compute.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { HERO_STAGE_KEYS, buildHeroStages, FX_STRIP_CODES, FX_FLAGS, buildFxItems } from "../src/lib/todayCompute.js";

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
const RECIPROCAL_TOLERANCE = 1e-4;
// Mirrors the real served economics.fx_horizons shape (backend
// FX_RATE_SNAPSHOTS): EUR/GBP/CAD all sourced from ECB reference rates.
const SAMPLE_FX_HORIZONS = {
  MUR: { current: 47.053589, "1m": null, "6m": null, "12m": null },
  EUR: { current: 0.87679, "1m": 0.86453, "6m": 0.85807, "12m": 0.85594 },
  GBP: { current: 0.74699, "1m": 0.74613, "6m": 0.74309, "12m": 0.74099 },
  CAD: { current: 1.4135, "1m": 1.3988, "6m": 1.3877, "12m": 1.3701 },
};

test("FX strip contains exactly EUR, CAD, GBP in that order", () => {
  assert.deepEqual(FX_STRIP_CODES, ["EUR", "CAD", "GBP"]);
});

test("EUR, GBP, and CAD all render as available from real snapshots", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const byCode = Object.fromEntries(items.map((it) => [it.code, it]));
  assert.equal(byCode.EUR.available, true);
  assert.equal(byCode.EUR.current, 0.87679);
  assert.equal(byCode.GBP.available, true);
  assert.equal(byCode.CAD.available, true, "CAD now has a real canonical snapshot (ECB via frankfurter.dev)");
  assert.equal(byCode.CAD.current, 1.4135, "CAD current must be the real stored ECB rate");
});

test("a currency with no snapshot still renders an honest unavailable state (fallback path intact)", () => {
  // Guards the honest-fallback branch generically, decoupled from CAD:
  // any currency whose canonical snapshot is absent must degrade cleanly.
  const items = buildFxItems({ EUR: { current: 0.87679, "12m": 0.85594 } });
  const cad = items.find((it) => it.code === "CAD");
  assert.equal(cad.available, false);
  assert.equal(cad.current, undefined, "a missing currency must not carry a fabricated rate");
  assert.equal(cad.reverse, undefined, "a missing currency must not carry a fabricated reverse either");
});

// ── FX reciprocal display ───────────────────────────────────────────────
test("EUR reverse pair equals 1 / USD_EUR (calculated, not a stored constant)", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const eur = items.find((it) => it.code === "EUR");
  assert.ok(eur.available);
  assert.ok(
    Math.abs(eur.reverse - 1 / eur.current) < RECIPROCAL_TOLERANCE,
    `EUR/USD (${eur.reverse}) must equal 1 / USD/EUR (${eur.current}) = ${1 / eur.current}`
  );
});

test("GBP reverse pair equals 1 / USD_GBP (calculated, not a stored constant)", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const gbp = items.find((it) => it.code === "GBP");
  assert.ok(gbp.available);
  assert.ok(
    Math.abs(gbp.reverse - 1 / gbp.current) < RECIPROCAL_TOLERANCE,
    `GBP/USD (${gbp.reverse}) must equal 1 / USD/GBP (${gbp.current}) = ${1 / gbp.current}`
  );
});

test("CAD reverse pair equals 1 / USD_CAD (calculated from the canonical rate)", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const cad = items.find((it) => it.code === "CAD");
  assert.ok(cad.available, "CAD must be available now that it is in the canonical snapshot");
  assert.ok(
    Math.abs(cad.reverse - 1 / cad.current) < RECIPROCAL_TOLERANCE,
    `CAD/USD (${cad.reverse}) must equal 1 / USD/CAD (${cad.current}) = ${1 / cad.current}`
  );
});

test("canonical CAD snapshot is present in the backend FX source (not hardcoded in Today.jsx)", () => {
  // Root cause of the prior "Rate not yet loaded": FX_RATE_SNAPSHOTS lacked
  // CAD and the API built fx_horizons for MUR/EUR/GBP only. CAD must live
  // in the shared canonical table + be served through the same path.
  const fxSrc = readFileSync(join(__dirname, "../../backend/app/calculators/production_normalization.py"), "utf8");
  assert.ok(/"CAD":\s*1\.4135/.test(fxSrc), "CAD current snapshot must be in FX_RATE_SNAPSHOTS");
  const apiSrc = readFileSync(join(__dirname, "../../backend/app/api/v1/cineglobe.py"), "utf8");
  assert.ok(/fx_rate_snapshot\(c\) for c in \([^)]*"CAD"/.test(apiSrc), "the API must serve CAD through fx_horizons");
  const todayRaw = readFileSync(join(__dirname, "../src/screens/company/Today.jsx"), "utf8");
  assert.ok(!/1\.4135/.test(todayRaw), "CAD rate must NOT be hardcoded in Today.jsx");
});

test("no independent reverse-rate constants exist in todayCompute.js (reverse is always 1/current)", () => {
  const computeSrc = readFileSync(join(__dirname, "../src/lib/todayCompute.js"), "utf8")
    .split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");
  // The only acceptable way "reverse" is produced is `1 / h.current` (or
  // equivalent division by the canonical field) — never a second object,
  // table, or hardcoded EUR/GBP/CAD number assigned to it.
  assert.match(computeSrc, /reverse:\s*Number\(\(1\s*\/\s*h\.current\)/, "reverse must be computed as 1 / current, not a stored value");
  assert.ok(!/reverse\s*:\s*[\d.]/.test(computeSrc), "found a numeric literal assigned to reverse — must be calculated, not fabricated");
});

test("both pair labels (USD/{code} and {code}/USD) render in Today.jsx for EUR, CAD, GBP", () => {
  const raw = readFileSync(join(__dirname, "../src/screens/company/Today.jsx"), "utf8");
  assert.ok(raw.includes("USD / {it.code}"), "expected the USD/{code} label to render for every currency");
  assert.ok(raw.includes("{it.code} / USD"), "expected the {code}/USD reverse label to render for every currency");
});

// ── FX flags (foreign-currency identity, never a USD flag on every pair) ─
test("FX_FLAGS map the foreign currency (EU / Canada / UK), not USD", () => {
  assert.equal(FX_FLAGS.EUR, "🇪🇺", "EUR must carry the EU flag");
  assert.equal(FX_FLAGS.CAD, "🇨🇦", "CAD must carry the Canadian flag");
  assert.equal(FX_FLAGS.GBP, "🇬🇧", "GBP must carry the UK flag");
  const usFlag = "🇺🇸";
  assert.ok(!Object.values(FX_FLAGS).includes(usFlag), "no US flag on any group — the flag identifies the foreign currency");
});

test("buildFxItems carries the correct flag on every currency group", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const byCode = Object.fromEntries(items.map((it) => [it.code, it]));
  assert.equal(byCode.EUR.flag, "🇪🇺");
  assert.equal(byCode.GBP.flag, "🇬🇧");
  assert.equal(byCode.CAD.flag, "🇨🇦");
  // The flag is present even on the honest-unavailable fallback path.
  const missing = buildFxItems({ EUR: { current: 0.87679, "12m": 0.85594 } }).find((it) => it.code === "CAD");
  assert.equal(missing.flag, "🇨🇦", "an unavailable group must still carry its flag for the header");
  assert.equal(missing.available, false);
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

// ── Hero heading + New Production placement (section-scoped structural
// checks — the heading and button are static JSX facts, so a scoped
// substring check is the focused available assertion). ─────────────────
// Isolate the three top-level sections by their className markers.
const heroBlock = todaySrc.slice(todaySrc.indexOf('className="ovx-sec tdy-hero"'), todaySrc.indexOf('className="ovx-sec tdy-fxstrip"'));
const slateBlock = todaySrc.slice(todaySrc.indexOf('className="ovx-sec tdy-slate"'), todaySrc.indexOf('COMPANY INTELLIGENCE'));

test("hero heading is exactly 'Production Summary' (not 'Pipeline Value')", () => {
  assert.ok(todaySrc.includes(">Production Summary<"), "expected the exact 'Production Summary' heading");
  assert.ok(!todaySrc.includes("Pipeline Value"), "found 'Pipeline Value' — must be replaced by 'Production Summary'");
});

test("New Production does NOT render inside the State of the Studio hero", () => {
  assert.ok(!heroBlock.includes("New Production"), "New Production must be removed from the hero");
  assert.ok(!heroBlock.includes("tdy-newprod"), "the New Production button must not appear in the hero section");
});

test("New Production renders inside the Production Slate header", () => {
  assert.ok(slateBlock.includes("New Production"), "New Production must render in the Production Slate header");
  assert.ok(slateBlock.includes("tdy-newprod"), "the New Production button belongs in the Slate header");
});

console.log("");
if (failures > 0) {
  console.log(`${failures} test(s) failed.`);
  process.exit(1);
}
console.log("All tests passed.");
