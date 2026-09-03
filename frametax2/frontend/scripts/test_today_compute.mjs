// Minimal regression coverage for Today's Hero computation and Today.jsx's
// structural facts (FX strip absence, key art, toolbar placement, Ask
// CineGlobe honesty). Plain Node + assert — this frontend has no test
// runner installed, and one is deliberately not introduced here (see
// lib/todayCompute.js). Run with:
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

test("Little Utopia (Evaluation, $4,364,393) aggregates budget/count correctly under Evaluation only", () => {
  const productions = [{ stageMeta: { key: "evaluation" }, budget: 4364393, npc: 2622262, momentum: { rank: 4 } }];
  const stages = buildHeroStages(STATUSES, productions);
  const byKey = Object.fromEntries(stages.map((s) => [s.key, s]));
  assert.equal(byKey.evaluation.count, 1);
  assert.equal(byKey.evaluation.budget, 4364393);
  assert.equal(byKey.development.count, 0);
  assert.equal(byKey.development.budget, 0);
  assert.equal(byKey.production.count, 0);
  assert.equal(byKey.production.budget, 0);
});

// ── Per-stage NPC and attention aggregates (new: Production Slate's
// collapsible group rows need these alongside count/budget) ────────────
test("buildHeroStages sums NPC only for productions with a real priced NPC (never a fabricated substitute)", () => {
  const productions = [
    { stageMeta: { key: "evaluation" }, budget: 4364393, npc: 2622262, momentum: { rank: 4 } },
  ];
  const stages = buildHeroStages(STATUSES, productions);
  const evaluation = stages.find((s) => s.key === "evaluation");
  assert.equal(evaluation.npc, 2622262);
});

test("buildHeroStages treats a null (unpriced) NPC as zero contribution, not a crash or NaN", () => {
  const productions = [{ stageMeta: { key: "development" }, budget: 1000000, npc: null, momentum: { rank: 4 } }];
  const stages = buildHeroStages(STATUSES, productions);
  const development = stages.find((s) => s.key === "development");
  assert.equal(development.npc, 0);
});

test("buildHeroStages counts Attention as Blocked(rank 0) or Stalled(rank 1) only", () => {
  const productions = [
    { stageMeta: { key: "evaluation" }, budget: 100, npc: 90, momentum: { rank: 0 } }, // blocked
    { stageMeta: { key: "evaluation" }, budget: 100, npc: 90, momentum: { rank: 1 } }, // stalled
    { stageMeta: { key: "evaluation" }, budget: 100, npc: 90, momentum: { rank: 2 } }, // advanced — not attention
    { stageMeta: { key: "evaluation" }, budget: 100, npc: 90, momentum: { rank: 4 } }, // healthy — not attention
  ];
  const stages = buildHeroStages(STATUSES, productions);
  const evaluation = stages.find((s) => s.key === "evaluation");
  assert.equal(evaluation.attention, 2);
  assert.equal(evaluation.count, 4);
});

test("buildHeroStages carries the productions array itself per stage (for the Slate's expanded rows)", () => {
  const p = { stageMeta: { key: "production" }, budget: 5, npc: 4, momentum: { rank: 4 } };
  const stages = buildHeroStages(STATUSES, [p]);
  const production = stages.find((s) => s.key === "production");
  assert.equal(production.productions.length, 1);
  assert.equal(production.productions[0], p);
});

// ── FX pure-computation coverage (buildFxItems is still a real, correct
// utility — it is simply no longer rendered on Today; see the FX-absence
// checks below) ─────────────────────────────────────────────────────────
const RECIPROCAL_TOLERANCE = 1e-4;
const SAMPLE_FX_HORIZONS = {
  MUR: { current: 47.053589, "1m": null, "6m": null, "12m": null },
  EUR: { current: 0.87679, "1m": 0.86453, "6m": 0.85807, "12m": 0.85594 },
  GBP: { current: 0.74699, "1m": 0.74613, "6m": 0.74309, "12m": 0.74099 },
  CAD: { current: 1.4135, "1m": 1.3988, "6m": 1.3877, "12m": 1.3701 },
};

test("FX strip codes are exactly EUR, CAD, GBP in that order", () => {
  assert.deepEqual(FX_STRIP_CODES, ["EUR", "CAD", "GBP"]);
});

test("EUR, GBP, and CAD all compute as available from real snapshots", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  const byCode = Object.fromEntries(items.map((it) => [it.code, it]));
  assert.equal(byCode.EUR.available, true);
  assert.equal(byCode.GBP.available, true);
  assert.equal(byCode.CAD.available, true);
});

test("a currency with no snapshot still computes an honest unavailable state (fallback path intact)", () => {
  const items = buildFxItems({ EUR: { current: 0.87679, "12m": 0.85594 } });
  const cad = items.find((it) => it.code === "CAD");
  assert.equal(cad.available, false);
  assert.equal(cad.current, undefined, "a missing currency must not carry a fabricated rate");
});

test("reverse pairs equal 1 / current for every available currency (calculated, not stored)", () => {
  const items = buildFxItems(SAMPLE_FX_HORIZONS);
  for (const code of ["EUR", "GBP", "CAD"]) {
    const it = items.find((i) => i.code === code);
    assert.ok(it.available);
    assert.ok(Math.abs(it.reverse - 1 / it.current) < RECIPROCAL_TOLERANCE, `${code} reverse must equal 1/current`);
  }
});

test("no independent reverse-rate constants exist in todayCompute.js (reverse is always 1/current)", () => {
  const computeSrc = readFileSync(join(__dirname, "../src/lib/todayCompute.js"), "utf8")
    .split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");
  assert.match(computeSrc, /reverse:\s*Number\(\(1\s*\/\s*h\.current\)/, "reverse must be computed as 1 / current, not a stored value");
  assert.ok(!/reverse\s*:\s*[\d.]/.test(computeSrc), "found a numeric literal assigned to reverse — must be calculated, not fabricated");
});

test("FX_FLAGS map the foreign currency (EU / Canada / UK), not USD", () => {
  assert.equal(FX_FLAGS.EUR, "🇪🇺");
  assert.equal(FX_FLAGS.CAD, "🇨🇦");
  assert.equal(FX_FLAGS.GBP, "🇬🇧");
  assert.ok(!Object.values(FX_FLAGS).includes("🇺🇸"), "no US flag on any group — the flag identifies the foreign currency");
});

// ── Source-shape guards ────────────────────────────────────────────────
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
  assert.ok(!todaySrc.includes("structures.ranking"), "found a reference to the legacy top-level structures.ranking");
  assert.ok(!todaySrc.includes("is_priceable"), "found the legacy is_priceable field — that belongs to the old ranking shape");
  assert.ok(!todaySrc.includes("conservative_npc_usd"), "found the legacy conservative_npc_usd field — that belongs to the old ranking shape");
});

// ── FX absence (2026-08-04 correction): project-specific FX intelligence
// belongs in the production screens, never on Today. ───────────────────
test("Today.jsx contains no FX strip — zero fx_horizons references", () => {
  const refs = (todaySrc.match(/fx_horizons/g) || []).length;
  assert.equal(refs, 0, `expected zero fx_horizons references on Today, found ${refs}`);
});

test("Today.jsx does not import buildFxItems (no FX rendering path)", () => {
  assert.ok(!todaySrc.includes("buildFxItems"), "Today.jsx must not import/call buildFxItems");
});

test("Today.jsx has no FX strip markup (tdy-fxstrip / tdy-fx-*)", () => {
  assert.ok(!todaySrc.includes("tdy-fxstrip"), "found tdy-fxstrip in Today.jsx");
  assert.ok(!todaySrc.includes("tdy-fx-"), "found tdy-fx-* markup in Today.jsx");
});

// ── Company Intelligence removed from the primary Today flow (2026-08-04):
// the section (and its underlying data) still exists elsewhere; only its
// rendering on Today's executive view is gone. ─────────────────────────
test("Today.jsx no longer renders a Company Intelligence section", () => {
  assert.ok(!todaySrc.includes("Company Intelligence"), "Company Intelligence must not render on Today");
  assert.ok(!todaySrc.includes("tdy-intel"), "found tdy-intel markup in Today.jsx");
});

// ── Toolbar placement (2026-08-04): theme toggle + New Production are a
// page-level toolbar, upper right — not inside the hero, not scoped to
// the Slate header. ─────────────────────────────────────────────────────
const toolbarBlock = todaySrc.slice(todaySrc.indexOf('className="tdy-toolbar"'), todaySrc.indexOf('className="ovx-sec tdy-hero"'));
const heroBlock = todaySrc.slice(todaySrc.indexOf('className="ovx-sec tdy-hero"'), todaySrc.indexOf('className="tdy-cols"'));

test("theme toggle renders in the page toolbar and reuses the canonical theme module", () => {
  assert.ok(toolbarBlock.includes("toggleTheme"), "expected the toolbar to call the canonical toggleTheme()");
  assert.ok(todaySrc.includes('from "../../lib/theme"'), "expected Today.jsx to import the canonical theme module, not a new implementation");
});

test("New Production renders in the page toolbar, not inside the State of the Studio hero", () => {
  assert.ok(toolbarBlock.includes("New Production"), "expected New Production in the toolbar");
  assert.ok(!heroBlock.includes("New Production"), "New Production must not render inside the hero");
});

// ── Ask CineGlobe (2026-08-04): honest UI, no fabricated backend ───────
test("Ask CineGlobe renders and is honestly labeled engine-pending (no fake response wiring)", () => {
  assert.ok(todaySrc.includes("Ask CineGlobe"), "expected an Ask CineGlobe section");
  assert.ok(todaySrc.includes("engine pending"), "expected an honest engine-pending disclosure near Ask CineGlobe");
  assert.ok(todaySrc.includes('disabled title={ASK_REASON}'), "expected the Ask submit control to be disabled with the honest reason, not wired to a fake responder");
});

// ── Key art (2026-08-04): canonical asset, no gradient placeholder ─────
test("Production Slate rows use the canonical project key art asset, not a gradient placeholder", () => {
  assert.ok(todaySrc.includes('import heroArt from "../../assets/production-art/little-utopia-hero-clean.png"'), "expected Today.jsx to import the canonical Hero art asset");
  assert.ok(todaySrc.includes('src={heroArt}'), "expected the key-art <img> to render the canonical asset");
  assert.ok(!todaySrc.includes("radial-gradient"), "found a gradient placeholder reference in Today.jsx — key art must be the real asset");
});

// ── Collapsible lifecycle groups (2026-08-04) ───────────────────────────
test("Production Slate renders three collapsible groups (Evaluation, Development, Production)", () => {
  assert.ok(todaySrc.includes("tdy-stagegrp"), "expected collapsible stage group markup");
  assert.ok(todaySrc.includes("tdy-stagehead"), "expected a clickable stage header (collapse/expand)");
  assert.ok(todaySrc.includes("heroStages.map"), "expected the Slate to iterate the same buildHeroStages() output the hero derives from");
});

// ── CineGlobe Overview FX Strip + Vertical Scrolling closeout ──────────
// buildLeaderFxItems is exported here (not just imported above for the
// fixed trio) so this file — and the shared components/FXStrip.jsx
// engine that consumes it — stay independently testable with plain node.
import { buildLeaderFxItems } from "../src/lib/todayCompute.js";

test("buildLeaderFxItems: a leader structure whose currency IS the base currency shows a truthful no-conversion state, never a fabricated pair or 'rate unavailable'", () => {
  const economics = { fx_horizons: { EUR: { current: 0.9 } }, jurisdiction_currency: { US: "USD" } };
  const structure = { primary_jurisdiction: "US-CA", participants: ["US-CA"] };
  const items = buildLeaderFxItems(economics, structure, "LEADING");
  assert.equal(items.length, 1);
  assert.equal(items[0].code, "USD");
  assert.equal(items[0].noConversion, true);
  assert.equal(items[0].available, true, "no-conversion is a resolved state, not an unavailable one");
});

test("buildLeaderFxItems: a real foreign currency with no sourced snapshot renders honest unavailable, never fabricated", () => {
  const economics = { fx_horizons: { SAR: { current: null, "1m": null, "6m": null, "12m": null } }, jurisdiction_currency: { SA: "SAR" } };
  const structure = { primary_jurisdiction: "SA", participants: ["SA"] };
  const items = buildLeaderFxItems(economics, structure, "TOP PRICED");
  assert.equal(items.length, 1);
  assert.equal(items[0].code, "SAR");
  assert.equal(items[0].available, false);
  assert.equal(items[0].noConversion, undefined, "unavailable is a distinct state from no-conversion");
});

test("buildLeaderFxItems: a real foreign currency WITH a sourced snapshot reads the rate verbatim, matching DISPLAYED FX == MODEL-CONSUMED FX", () => {
  const economics = { fx_horizons: { EUR: { current: 0.87679, "12m": 0.85594 } }, jurisdiction_currency: { GR: "EUR" } };
  const structure = { primary_jurisdiction: "GR", participants: ["GR"] };
  const items = buildLeaderFxItems(economics, structure, "TOP PRICED");
  assert.equal(items.length, 1);
  assert.equal(items[0].current, 0.87679, "the displayed rate must be the same snapshot value the model consumes, never re-derived");
  assert.ok(Math.abs(items[0].reverse - 1 / 0.87679) < RECIPROCAL_TOLERANCE);
});

test("buildLeaderFxItems: no structure (no Leading selection, no Top Priced candidate) never fabricates a leader cell", () => {
  assert.deepEqual(buildLeaderFxItems({ fx_horizons: {} }, null, null), []);
});

test("buildLeaderFxItems: does not import flagEmoji/format.jsx — stays plain-node testable, flags resolve in the React presentation layer", () => {
  const computeSrc = readFileSync(join(__dirname, "../src/lib/todayCompute.js"), "utf8");
  assert.ok(!/from\s+["']\.\/format\.jsx["']/.test(computeSrc), "todayCompute.js must not import from format.jsx (breaks plain-node testability)");
});

// ── One shared FX engine, not two — Overview and Workspace both mount
// components/FXStrip.jsx; neither re-implements FX rendering. ──────────
const overviewSrc = readFileSync(join(__dirname, "../src/screens/production/Overview.jsx"), "utf8");
const workspaceSrc = readFileSync(join(__dirname, "../src/screens/production/Workspace.jsx"), "utf8");
const fxStripSrc = readFileSync(join(__dirname, "../src/components/FXStrip.jsx"), "utf8");

test("Overview.jsx renders the shared components/FXStrip.jsx, not a second FX implementation", () => {
  assert.ok(overviewSrc.includes('import FXStrip from "../../components/FXStrip"'), "expected Overview.jsx to import the shared FXStrip component");
  assert.ok(overviewSrc.includes("<FXStrip"), "expected Overview.jsx to render <FXStrip");
  assert.ok(!overviewSrc.includes("wsx-fx-row"), "Overview.jsx must not carry its own copy of the FX strip markup");
});

test("Workspace.jsx renders the shared components/FXStrip.jsx, not its former inline copy", () => {
  assert.ok(workspaceSrc.includes('import FXStrip from "../../components/FXStrip"'), "expected Workspace.jsx to import the shared FXStrip component");
  assert.ok(workspaceSrc.includes("<FXStrip"), "expected Workspace.jsx to render <FXStrip");
  assert.ok(!workspaceSrc.includes("function buildLeaderFxItems"), "Workspace.jsx must not carry its own copy of buildLeaderFxItems");
});

test("components/FXStrip.jsx propagates real source + as-of metadata (the backend->UI propagation gap this closeout repairs)", () => {
  assert.ok(fxStripSrc.includes("economics?.fx_source"), "expected FXStrip.jsx to read economics.fx_source");
  assert.ok(fxStripSrc.includes("economics?.fx_horizon_dates?.current"), "expected FXStrip.jsx to read economics.fx_horizon_dates.current");
});

// ── Overview vertical scrolling: the shared .workspace-main scroll
// container (AppShell.jsx) is not overridden or duplicated by Overview's
// own markup — the same architecture every other production route uses.
const appShellSrc = readFileSync(join(__dirname, "../src/shell/AppShell.jsx"), "utf8");
test("AppShell.jsx's single .workspace-main scroll container wraps every routed screen, including Overview", () => {
  assert.match(appShellSrc, /className="workspace-main"/, "expected the shared scrollable body region");
  assert.ok(!overviewSrc.includes("overflow-y"), "Overview.jsx must not declare its own scroll container — it relies on the shared .workspace-main region");
  assert.ok(!overviewSrc.includes("100vh"), "Overview.jsx must not fix its own height — that would defeat the shared scroll container");
});

console.log("");
if (failures > 0) {
  console.log(`${failures} test(s) failed.`);
  process.exit(1);
}
console.log("All tests passed.");
