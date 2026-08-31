// ── Globe Phase 2 regression protection ─────────────────────────────────
//
// Run with:  npm test          (node --test, built in — no new dependencies)
//
// WHY THESE EXIST. The previous workflow let a technically-responsive canvas
// pass review while the visible composition regressed, and let a pulse rule be
// "fixed" in one code path while a duplicate of the same predicate quietly
// undid it in another. Both are invisible to a build and to a screenshot
// glanced at quickly. Each assertion below corresponds to a defect that was
// actually found and repaired, so a failure here means a real regression and
// not a style preference.
//
// SCOPE, honestly stated. These are logic + geometry checks on pure modules.
// They CANNOT prove visual parity, and they are not a substitute for the
// runtime acceptance matrix in GLOBE_FREEZE_MANIFEST.md, which must still be
// driven in a real browser (the project has no browser-test dependency and
// this batch deliberately did not add one). What they do protect is every
// invariant that is expressible without a GPU — which turned out to include
// the no-clipping property, because that is arithmetic, not opinion.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  CAMERA_FOV_DEG,
  FIT_MARGIN,
  GLOBE_CONTENT_RADIUS,
  GLOBE_GEOMETRY_RADIUS,
  fitCameraDistance,
  resolveRestingFlight,
  silhouetteRadiusPx,
} from "../src/lib/globeFit.js";

import {
  FIXTURE_DISCLOSURE,
  FIXTURE_EXPECTED_COUNTS,
  fixtureRelatedFor,
  fixtureSlotFor,
  isFixtureActive,
} from "../src/lib/globeVisualFixture.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

// Comments in this codebase deliberately quote the defects they replaced, so
// any assertion about CODE has to strip them first — otherwise a well-documented
// fix fails the very test that guards it (which is exactly what happened on the
// first run of the pulse-predicate check below).
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

// The viewports the manifest commits to verifying. Heights are the measured
// canvas heights at those viewports, not the viewport heights.
const VIEWPORTS = [
  { label: "1600x900", canvas: [980, 650] },
  { label: "1440x900", canvas: [820, 650] },
  { label: "1280x800", canvas: [660, 550] },
  { label: "narrow desktop 1180x820", canvas: [560, 570] },
];

// ── Sizing / no-clipping ────────────────────────────────────────────────

test("fit distance keeps the whole sphere inside the frame at every supported viewport", () => {
  for (const { label, canvas: [w, h] } of VIEWPORTS) {
    const d = fitCameraDistance(w, h);
    const r = silhouetteRadiusPx(w, h, d);
    assert.ok(
      r <= h / 2,
      `${label}: sphere radius ${r.toFixed(1)}px exceeds half-height ${(h / 2).toFixed(1)}px`,
    );
    assert.ok(
      r <= w / 2,
      `${label}: sphere radius ${r.toFixed(1)}px exceeds half-width ${(w / 2).toFixed(1)}px`,
    );
  }
});

test("fit distance leaves headroom for the beacons that stand on the sphere", () => {
  // The content radius (sphere + recommendation beacon) must also fit, or the
  // recommendation marker clips against the edge — the originally reported
  // defect. Assert it directly rather than trusting the sphere check.
  for (const { label, canvas: [w, h] } of VIEWPORTS) {
    const d = fitCameraDistance(w, h);
    const rContent = silhouetteRadiusPx(w, h, d, GLOBE_CONTENT_RADIUS);
    const limit = Math.min(w, h) / 2;
    assert.ok(
      rContent <= limit,
      `${label}: content radius ${rContent.toFixed(1)}px exceeds limit ${limit.toFixed(1)}px`,
    );
  }
});

test("the previously shipped fixed distances would have clipped (guards the regression)", () => {
  // 225 was shipped and clipped; 246 was its predecessor and also left no
  // beacon headroom. If a future change makes these pass, the fit has been
  // loosened and the clipping defect is back.
  const [w, h] = [980, 650];
  assert.ok(silhouetteRadiusPx(w, h, 225) > h / 2, "d=225 should overflow the half-height");
  assert.ok(
    silhouetteRadiusPx(w, h, 246, GLOBE_CONTENT_RADIUS) > h / 2,
    "d=246 should leave no beacon headroom",
  );
});

test("fit distance responds to a portrait frame by pulling back, not by clipping", () => {
  const landscape = fitCameraDistance(900, 500);
  const portrait = fitCameraDistance(500, 900);
  assert.ok(portrait > landscape, "a narrower frame must increase the camera distance");
  assert.ok(silhouetteRadiusPx(500, 900, portrait) <= 500 / 2);
});

test("fit geometry constants stay within their documented envelope", () => {
  assert.equal(GLOBE_GEOMETRY_RADIUS, 100, "three-globe's radius is not ours to change");
  assert.ok(GLOBE_CONTENT_RADIUS > GLOBE_GEOMETRY_RADIUS, "content radius must exceed the sphere");
  assert.ok(FIT_MARGIN > 0 && FIT_MARGIN < 0.25);
  assert.equal(CAMERA_FOV_DEG, 50);
});

// ── Semantic system ─────────────────────────────────────────────────────
// globeData.js imports ./jurisdictions and ./globeVisualFixture with explicit
// .js extensions, so Node can load it directly and these assert the real
// exported objects rather than source text.

test("exactly four semantic states, and no legacy fifth", async () => {
  const { GLOBE_SEMANTIC, STATUS_HEX, STATUS_LABEL } = await import("../src/lib/globeData.js");
  const slots = Object.keys(GLOBE_SEMANTIC);
  assert.equal(slots.length, 4, `expected 4 semantic states, got ${slots.join(", ")}`);
  assert.deepEqual(slots.sort(), ["amber", "gold", "jade", "silver"]);
  for (const forbidden of ["darkRed", "red", "charcoal", "graphite"]) {
    assert.ok(!(forbidden in GLOBE_SEMANTIC), `${forbidden} must not be a semantic state`);
    assert.ok(!(forbidden in STATUS_HEX), `${forbidden} must not be in STATUS_HEX`);
  }
  // Derived maps must stay in lockstep with the canonical table.
  assert.deepEqual(Object.keys(STATUS_HEX).sort(), slots.sort());
  assert.deepEqual(Object.keys(STATUS_LABEL).sort(), slots.sort());
});

test("no legacy database-state wording survives in any semantic label", async () => {
  const { STATUS_LABEL } = await import("../src/lib/globeData.js");
  const labels = Object.values(STATUS_LABEL).join(" | ").toLowerCase();
  for (const legacy of [
    "no known incentive",
    "qualified",
    "evaluated",
    "not applicable",
    "candidate",
    "viable",
  ]) {
    assert.ok(!labels.includes(legacy), `legacy wording "${legacy}" found in: ${labels}`);
  }
  // PHASE 3A FINAL CLOSEOUT: labels reconciled a third time to the actual
  // executive terminology — "Optimized" -> "Alternatives", "Opportunity" ->
  // "Co-Pro Opportunities" (compact form; STATUS_FULL_LABEL carries
  // "Co-Production Opportunities" for hover), "Baseline" -> "Excluded".
  // Same four slots, same hex family, same count each time.
  assert.deepEqual(Object.values(STATUS_LABEL).sort(), [
    "Alternatives",
    "Co-Pro Opportunities",
    "Excluded",
    "Recommended",
  ]);
});

test("hover/detail surfaces get the long form of Co-Pro Opportunities", async () => {
  const { STATUS_FULL_LABEL } = await import("../src/lib/globeData.js");
  assert.equal(STATUS_FULL_LABEL.amber, "Co-Production Opportunities");
  assert.equal(STATUS_FULL_LABEL.gold, "Recommended");
  assert.equal(STATUS_FULL_LABEL.jade, "Alternatives");
  assert.equal(STATUS_FULL_LABEL.silver, "Excluded");
});

test("only the recommendation pulses", async () => {
  const { PULSE_TIERS, GLOBE_SEMANTIC } = await import("../src/lib/globeData.js");
  assert.deepEqual([...PULSE_TIERS], ["gold"], "pulse is reserved for the recommendation");
  assert.equal(GLOBE_SEMANTIC.gold.pulse, true);
  for (const slot of ["jade", "amber", "silver"]) {
    assert.equal(GLOBE_SEMANTIC[slot].pulse, false, `${slot} must not pulse`);
  }
});

test("Globe3D derives pulse eligibility from PULSE_TIERS in BOTH code paths", () => {
  // The predicate existed twice (mount path + data-change path) and a
  // hand-written copy in the second silently re-enabled the island/city-state
  // pulse on every data change. Both must read the canonical set.
  const code = stripComments(read("components/Globe3D.jsx"));
  const uses = code.match(/PULSE_TIERS\.has\(/g) || [];
  assert.ok(uses.length >= 2, `expected >=2 PULSE_TIERS.has() call sites, found ${uses.length}`);
  assert.ok(
    !/tier\s*===\s*["']gold["']\s*\|\|\s*isSmallJurisdiction/.test(code),
    "the old island/city-state pulse predicate is back",
  );
});

// ── Legend and Inspector boundary ───────────────────────────────────────

// SUPERSEDED (Phase 3A final correction): Phase 2 deleted the persistent
// legend outright, on the grounds that a Globe needing a colour key had not
// been designed. That rule is EXPLICITLY reversed by direct authorization —
// a compact, production-visible, four-state-only legend is now required
// chrome, not a regression. What must never come back is the OLD legend:
// six categories, legacy database-state wording, and — per the Phase 2
// finding this test preserves — no re-declared colour table of its own.
test("the restored Globe legend carries exactly the four current states, no legacy wording, and no re-declared colours", () => {
  const src = stripComments(read("components/GlobeLegend.jsx"));
  // Must read the canonical semantic table, never a hand-written duplicate —
  // the exact drift Phase 2 fixed once already for the card dots and the
  // fixture badge.
  assert.match(src, /GLOBE_SEMANTIC/, "legend must import the canonical semantic table");
  assert.ok(!/#[0-9a-fA-F]{3,6}/.test(src), "legend must not hardcode a hex colour of its own");
  // Exactly the four current slot keys — no fifth, no legacy category name.
  const orderMatch = /order\s*=\s*\[([^\]]+)\]/.exec(src);
  assert.ok(orderMatch, "legend must declare an explicit state order");
  const slots = orderMatch[1].split(",").map((s) => s.trim().replace(/["']/g, ""));
  assert.deepEqual(slots.sort(), ["amber", "gold", "jade", "silver"]);
  for (const legacy of [
    "no known incentive", "qualified", "conditional", "evaluated",
    "not evaluated", "candidate jurisdiction",
  ]) {
    assert.ok(!src.toLowerCase().includes(legacy), `legacy wording "${legacy}" found in GlobeLegend.jsx`);
  }
});

test("the legend is scoped to Project Globe only, is vertical, and never intercepts a click", () => {
  // "Only the Project Globe rendering" — not Overview, not Workspace. Import
  // check is a reasonable proxy: only ProjectGlobe.jsx may mount it.
  const mounters = ["screens/production/Overview.jsx", "screens/production/Workspace.jsx"]
    .filter((f) => stripComments(read(f)).includes("GlobeLegend"));
  assert.deepEqual(mounters, [], `GlobeLegend must not be mounted outside Project Globe: ${mounters.join(", ")}`);
  assert.match(read("screens/production/ProjectGlobe.jsx"), /<GlobeLegend\s*\/>/);
  // PHASE 3B GLOBE CLOSEOUT: the old "stay tiny, single row" rule is
  // explicitly reversed — the legend was found too small to read and is
  // rebuilt as a larger vertical stack. What must still hold: readable but
  // not modal-sized, and it must never swallow a click meant for the globe
  // underneath/beside it (pointer-events: none).
  const css = read("styles/screens.css");
  const block = /\.globe-legend-vertical\s*\{[^}]*\}/.exec(css);
  assert.ok(block, ".globe-legend-vertical rule not found");
  assert.match(block[0], /font:\s*1[0-4]px/, "legend type must be larger than the old 10px, but still a caption size, not a heading");
  assert.match(block[0], /pointer-events:\s*none/, "legend must never intercept a click meant for the globe");
  assert.match(block[0], /flex-direction:\s*column/, "legend must be vertical, per the closeout instruction");
});

// PHASE 3A FINAL CLOSEOUT: this test previously banned ANY money figure from
// the Globe hover card. That rule is explicitly, deliberately reversed —
// hover shows "a lightweight economic summary" including estimated NPC and
// incentive. PHASE 3B BATCH 1: money must be FULL precision (formatFullUsd /
// Money), never CompactMoney's "$2.6M" abbreviation — an explicit
// requirement this batch. The boundary that survives is narrower, not gone:
// hover must never pull in Inspector-only content (the qualification trace,
// account/source citations, requirements, blockers) — that's still what
// opening the Inspector is for.
test("Globe hover card shows full-precision money and stays clear of Inspector-only content", () => {
  const src = read("screens/production/ProjectGlobe.jsx");
  const fn = /function GlobeHoverCard[\s\S]*?\n}/.exec(src);
  assert.ok(fn, "GlobeHoverCard component not found");
  assert.ok(!/CompactMoney/.test(src), "Phase 3B Batch 1 requires full-precision money — CompactMoney must not appear anywhere in this file");
  assert.ok(/formatFullUsd/.test(src), "hover card must render money via formatFullUsd (no MM/K abbreviation)");
  for (const bodyFnName of ["RecommendedOrAlternativeBody", "CoProductionBody", "ExcludedBody"]) {
    const bodyFn = new RegExp(`function ${bodyFnName}[\\s\\S]*?\\n}`).exec(src);
    assert.ok(bodyFn, `${bodyFnName} not found`);
    for (const forbidden of ["qualification_trace", "account_codes", "requirements", "blockers", "statutory_basis"]) {
      assert.ok(!bodyFn[0].includes(forbidden), `${bodyFnName} must not pull in Inspector-only field "${forbidden}"`);
    }
  }
});

// REGRESSION (found live, Hungary, during Phase 3A final closeout runtime
// verification): buildCountryHoverData's `status` field is the COLOUR-slot
// key ("gold"/"jade"/"amber"/"silver"), never the `semanticState` key
// ("recommended"/"alternative"/"unlockable"/"additional"). An earlier draft
// checked `hover.status === "additional"` / `"unlockable"` — those strings
// never appear in `status`, so the checks silently never matched. PHASE 3B
// BATCH 1 restructured the hover card into three category-specific body
// components dispatched directly in GlobeHoverCard's own render — this test
// now asserts THAT dispatch uses the colour-slot keys, so the exact same
// regression can't reappear silently in the new shape.
test("hover card dispatch keys off the colour-slot status, not semanticState", () => {
  const src = read("screens/production/ProjectGlobe.jsx");
  const cardFn = /function GlobeHoverCard[\s\S]*?\n}/.exec(src)[0];
  assert.ok(cardFn.includes('hover.status === "silver"'), 'GlobeHoverCard must dispatch Excluded on status === "silver"');
  assert.ok(cardFn.includes('hover.status === "amber"'), 'GlobeHoverCard must dispatch Co-Production on status === "amber"');
  assert.ok(!/hover\.status === "additional"/.test(cardFn), 'must not check the semanticState string "additional"');
  assert.ok(!/hover\.status === "unlockable"/.test(cardFn), 'must not check the semanticState string "unlockable"');
});

// PHASE 3B BATCH 1 — click contract: a Globe click must never call the
// backend, rerun optimization, or create/modify a scenario. `selectJurisdiction`
// and `selectStructure` are pure client-state operations (setSelectedJurisdiction
// + openInspector) over data already served; this guards against either
// function growing a fetch/POST call in a future edit.
test("Globe click contract never calls the backend", () => {
  const src = read("screens/production/ProjectGlobe.jsx");
  for (const fnName of ["selectJurisdiction", "selectStructure"]) {
    const fn = new RegExp(`function ${fnName}\\([\\s\\S]*?\\n  }`).exec(src);
    assert.ok(fn, `${fnName} not found`);
    for (const forbidden of ["fetch(", "axios", "POST", ".post(", "await api"]) {
      assert.ok(!fn[0].includes(forbidden), `${fnName} must not call the backend (found "${forbidden}")`);
    }
  }
});

// ── Visual fixture ──────────────────────────────────────────────────────

test("fixture is disabled by default", () => {
  // No env var, no browser, no query string -> must be inert.
  assert.equal(isFixtureActive(), false);
});

test("fixture assigns only canonical slots, and is deterministic", async () => {
  const { GLOBE_SEMANTIC } = await import("../src/lib/globeData.js");
  const probes = ["MU", "GB", "IT", "AU", "US-NY", "CA-BC", "ZZ", "", null, undefined];
  const first = probes.map((c) => fixtureSlotFor(c));
  const second = probes.map((c) => fixtureSlotFor(c));
  assert.deepEqual(first, second, "fixture assignment must be repeatable");
  for (const slot of first) {
    assert.ok(slot in GLOBE_SEMANTIC, `fixture emitted non-canonical slot "${slot}"`);
  }
  // Unlisted / invalid codes fall to Additional, never to a recommendation.
  assert.equal(fixtureSlotFor("ZZ"), "silver");
  assert.equal(fixtureSlotFor(undefined), "silver");
});

test("fixture assigns exactly one Recommended, and populates all four states", () => {
  assert.equal(FIXTURE_EXPECTED_COUNTS.gold, 1, "exactly one Recommended");
  assert.ok(FIXTURE_EXPECTED_COUNTS.jade >= 8, "enough Optimized alternatives to be legible");
  assert.ok(FIXTURE_EXPECTED_COUNTS.amber >= 8, "enough Unlockable opportunities to be legible");
  assert.equal(fixtureSlotFor("MU"), "gold", "Mauritius stays the Recommended jurisdiction");
});

test("fixture codes are globe keys, not collapsing sub-national codes", () => {
  // AU-QLD silently never matched, because Australia is not rendered at
  // admin-1 level so every AU-* code collapses to the globe key "AU". Only US
  // and CA may appear with a sub-national suffix.
  const src = read("lib/globeVisualFixture.js");
  const listed = [...src.matchAll(/"([A-Z]{2}(?:-[A-Z0-9]+)?)"/g)].map((m) => m[1]);
  const subnational = listed.filter((c) => c.includes("-"));
  for (const code of subnational) {
    const parent = code.split("-")[0];
    assert.ok(
      parent === "US" || parent === "CA",
      `${code} is sub-national but ${parent} is not rendered at admin-1 level`,
    );
  }
});

test("fixture carries its disclosure and cannot reach the backend", () => {
  assert.match(FIXTURE_DISCLOSURE, /not optimizer output/i);
  const src = read("lib/globeVisualFixture.js");
  // The contract is "no backend writes / no production contamination", NOT "no
  // client state". `localStorage` is deliberately used to LATCH the dev toggle
  // (see below) — the original blanket ban was the wrong expression of the rule
  // and would have blocked the fix for the fixture silently switching itself
  // off. What must stay absent is anything that leaves the browser.
  //
  // Checked against CODE, not comments — the file-level convention documented
  // at the top of this suite. The Phase 3B reconciliation added a comment
  // naming the real backend structure ids (ALLOC-COMPONENT-POST-<X>), whose
  // text contains "POST"; failing the guard on a comment that merely EXPLAINS
  // the data model is exactly the false positive stripComments exists for. The
  // invariant itself is unchanged and still absolute for executable code.
  const code = stripComments(src);
  for (const forbidden of ["fetch(", "XMLHttpRequest", "POST", "PUT", "PATCH"]) {
    assert.ok(!code.includes(forbidden), `fixture must not use ${forbidden}`);
  }
});

test("fixture activation is durable AND every write path is DEV-gated", () => {
  const code = stripComments(read("lib/globeVisualFixture.js"));
  // Durable: it must not depend on the URL alone. The app's project tabs are
  // react-router links to bare paths, so a query-param-only gate switches
  // itself off on any in-app navigation — the confirmed root cause of the
  // fixture "reverting after refresh".
  assert.match(code, /localStorage/, "activation must latch into durable state");
  assert.match(code, /function readLatch/, "expected a latch reader");
  // Every mutation of that state must be unreachable in a production build.
  assert.match(code, /function devOnly\(\)/);
  assert.match(code, /if \(!devOnly\(\)\) return;/, "disableFixture must be DEV-gated");
  const writeLatch = /function writeLatch[\s\S]*?\n}/.exec(code);
  assert.ok(writeLatch, "writeLatch not found");
  // writeLatch is only ever called from DEV-gated paths.
  assert.ok(
    /if \(devOnly\(\) && typeof window/.test(code),
    "the URL latch must be inside a devOnly() guard",
  );
  // And the whole gate short-circuits in production regardless of stored state.
  assert.match(code, /if \(!devOnly\(\)\) return false;/);
});

test("the fixture badge is the only place the disclosure is rendered, and it is gated", () => {
  const badge = read("components/GlobeFixtureBadge.jsx");
  assert.match(badge, /if \(!isFixtureActive\(\)\) return null;/);
  assert.match(badge, /FIXTURE_DISCLOSURE/);
});

// ── Day/night calibration ───────────────────────────────────────────────

test("GLOBE_THEME is the single source for both themes", () => {
  const src = read("components/Globe3D.jsx");
  // Every day value must be derived from GLOBE_THEME.day, never re-declared.
  for (const name of ["OCEAN_BODY", "NEUTRAL_FILL", "NEUTRAL_STROKE"]) {
    const decl = new RegExp(`const ${name} = ([^;]+);`).exec(src);
    assert.ok(decl, `${name} declaration not found`);
    assert.match(
      decl[1],
      /GLOBE_THEME\.day|GRAPHITE_HEX/,
      `${name} must derive from GLOBE_THEME.day, got: ${decl[1]}`,
    );
  }
  // Both themes must define the same keys, or one of them is under-calibrated.
  const themeBlock = /const GLOBE_THEME = \{([\s\S]*?)\n\};/.exec(src);
  assert.ok(themeBlock, "GLOBE_THEME block not found");
  const dayKeys = [...themeBlock[1].matchAll(/^\s{4}(\w+):/gm)].map((m) => m[1]);
  const seen = new Map();
  for (const k of dayKeys) seen.set(k, (seen.get(k) || 0) + 1);
  for (const [k, n] of seen) {
    assert.equal(n, 2, `GLOBE_THEME key "${k}" appears ${n}x — day and night must both define it`);
  }
});

test("THREE.Clock is not reintroduced (it warns on construction in three 0.185)", () => {
  const src = read("components/Globe3D.jsx");
  assert.ok(!/new THREE\.Clock\(/.test(stripComments(src)), "THREE.Clock is deprecated; use performance.now()");
});

test("ambient motion stays gated on prefers-reduced-motion", () => {
  const src = read("components/Globe3D.jsx");
  assert.match(src, /prefers-reduced-motion/);
  assert.match(src, /stateRef\.current\.ambientMotion/);
});

// ── Emphasis ladder (the "Globe is mostly grey" regression) ─────────────

// Perceived luminance. The same weights used to diagnose the inverted ladder.
const lum = (hex) => {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return 0.299 * r + 0.587 * g + 0.114 * b;
};

test("semantic emphasis increases monotonically above untouched land", async () => {
  const { GLOBE_SEMANTIC, GRAPHITE_HEX } = await import("../src/lib/globeData.js");
  const land = lum(GRAPHITE_HEX);
  const additional = lum(GLOBE_SEMANTIC.silver.hex);
  const optimized = lum(GLOBE_SEMANTIC.jade.hex);
  const unlockable = lum(GLOBE_SEMANTIC.amber.hex);
  const recommended = lum(GLOBE_SEMANTIC.gold.hex);

  // THE DEFECT THIS GUARDS: Additional shipped at #a9b2c0 (luminance 177),
  // BRIGHTER than Optimized alternative (137) and Unlockable (161). Because
  // Additional is the residual bucket — 61 of 86 jurisdictions — the Globe
  // rendered as a field of light grey with the actionable states sitting
  // beneath it. This is an ordering error in the palette; no material or
  // lighting work can compensate for it.
  assert.ok(additional > land, `Additional (${additional.toFixed(0)}) must sit above untouched land (${land.toFixed(0)})`);
  assert.ok(optimized > additional, `Optimized (${optimized.toFixed(0)}) must outrank Additional (${additional.toFixed(0)})`);
  assert.ok(unlockable > additional, `Unlockable (${unlockable.toFixed(0)}) must outrank Additional (${additional.toFixed(0)})`);
  assert.ok(
    recommended > unlockable && recommended > optimized,
    `Recommended (${recommended.toFixed(0)}) must dominate both peer states`,
  );
  // Recommended must DOMINATE, not merely edge ahead.
  assert.ok(
    recommended - Math.max(optimized, unlockable) >= 25,
    `Recommended must lead the peer states by >=25 luminance, got ${(recommended - Math.max(optimized, unlockable)).toFixed(0)}`,
  );
});

test("neutral land has presence: clearly above the ocean it sits in", async () => {
  const { GRAPHITE_HEX } = await import("../src/lib/globeData.js");
  // Untouched countries must not read as empty/black. Compared against the
  // day-mode ocean, which Globe3D declares in GLOBE_THEME.
  const src = read("components/Globe3D.jsx");
  const ocean = /GLOBE_THEME = \{[\s\S]*?day: \{[\s\S]*?ocean: "(#[0-9a-fA-F]{6})"/.exec(src);
  assert.ok(ocean, "day ocean colour not found");
  const gap = lum(GRAPHITE_HEX) - lum(ocean[1]);
  assert.ok(gap >= 55, `neutral land must clear the ocean by >=55 luminance, got ${gap.toFixed(0)}`);
});

test("Additional stays desaturated — it is the quiet state, not a colour", async () => {
  const { GLOBE_SEMANTIC } = await import("../src/lib/globeData.js");
  const h = GLOBE_SEMANTIC.silver.hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const spread = Math.max(r, g, b) - Math.min(r, g, b);
  assert.ok(spread <= 40, `Additional must stay near-neutral, channel spread ${spread}`);
  // And it must not be a WARM grey — warm neutrals reintroduce the muddy cast.
  assert.ok(b >= r, `Additional must be cool/neutral, not warm (r=${r} b=${b})`);
});

// ── US / Canada jurisdiction identity ───────────────────────────────────

test("no US state or Canadian province is labelled with a city name", async () => {
  const { JURISDICTION_COORDS } = await import("../src/lib/jurisdictions.js");
  // A Globe jurisdiction is the state/province that runs the incentive
  // programme. Nine were shipped as cities — CA-BC read "Vancouver", US-GA
  // "Atlanta", US-CA "Los Angeles" — which mislabels the programme itself, not
  // just the marker. Cities may appear inside the Inspector later; never as a
  // Globe jurisdiction.
  const CITIES = [
    "Vancouver", "Toronto", "Montreal", "Los Angeles", "Atlanta",
    "New Orleans", "Portland", "Austin", "Seattle", "Chicago", "Miami",
  ];
  const offenders = [];
  for (const [code, v] of Object.entries(JURISDICTION_COORDS)) {
    if (!/^(US|CA)-/.test(code)) continue;
    if (CITIES.includes(v?.name)) offenders.push(`${code} = ${v.name}`);
  }
  assert.deepEqual(offenders, [], `city names used as jurisdictions: ${offenders.join(", ")}`);
});

test("every US/CA jurisdiction carries a non-empty name", async () => {
  const { JURISDICTION_COORDS } = await import("../src/lib/jurisdictions.js");
  for (const [code, v] of Object.entries(JURISDICTION_COORDS)) {
    if (!/^(US|CA)-/.test(code)) continue;
    assert.ok(v?.name && v.name.length > 2, `${code} has no usable name`);
  }
});

test("no two jurisdictions share a display name", async () => {
  const { JURISDICTION_COORDS } = await import("../src/lib/jurisdictions.js");
  // Caught a real collision introduced while fixing the city-name defect: the
  // COUNTRY Georgia (GE) and the US state Georgia (US-GA) both resolved to
  // "Georgia", so hovering two jurisdictions on opposite sides of the world
  // produced the same label. Asserted against the imported object rather than
  // by regex — the first duplicate-scan missed it because `GE` is an unquoted
  // key, which is exactly the kind of gap a source-text check leaves.
  // The invariant is "two DIFFERENT PLACES must not share a label", so entries
  // at identical coordinates are treated as aliases of one jurisdiction rather
  // than a collision. That distinction is load-bearing: this check also
  // surfaced `AE_AD` / `AE-AD`, a dead underscore-spelling alias with the same
  // coordinates, the same name, no reference anywhere in the frontend, and no
  // counterpart in the backend payload (which emits only `AE-AD`). Harmless.
  // Georgia was the opposite case — GE at 41.72,44.79 and US-GA at
  // 33.75,-84.39 are a continent apart and genuinely ambiguous.
  const byName = new Map();
  for (const [code, v] of Object.entries(JURISDICTION_COORDS)) {
    if (!v?.name) continue;
    if (!byName.has(v.name)) byName.set(v.name, []);
    byName.get(v.name).push({ code, at: `${v.lat},${v.lng}` });
  }
  const dupes = [];
  for (const [name, entries] of byName) {
    const distinctPlaces = new Set(entries.map((e) => e.at));
    if (distinctPlaces.size > 1) {
      dupes.push(`${name} <- ${entries.map((e) => `${e.code}@${e.at}`).join(", ")}`);
    }
  }
  assert.deepEqual(dupes, [], `ambiguous jurisdiction labels: ${dupes.join(" | ")}`);
});

// ── Phase 3B Batch 1: shared hover-presentation helpers ─────────────────

test("formatFullUsd never abbreviates", async () => {
  const { formatFullUsd } = await import("../src/lib/globeHoverFormat.js");
  assert.equal(formatFullUsd(742131), "$742,131");
  assert.equal(formatFullUsd(3622262), "$3,622,262");
  assert.equal(formatFullUsd(null), null);
});

test("incentivePctOfGross divides incentive by GROSS BUDGET, not qualified spend", async () => {
  const { incentivePctOfGross } = await import("../src/lib/globeHoverFormat.js");
  // 742,131 / 4,364,393 = 17.0% — the worked example from the Phase 3B spec.
  assert.equal(incentivePctOfGross(742131, 4364393), "17.0%");
  assert.equal(incentivePctOfGross(null, 4364393), null);
  assert.equal(incentivePctOfGross(742131, 0), null);
  assert.equal(incentivePctOfGross(742131, null), null);
});

test("modeledRateInfo reads rate_ceiling (the engine's real modeled_rate), not rate_floor", async () => {
  const { modeledRateInfo } = await import("../src/lib/globeHoverFormat.js");
  // Confirmed from allocation_pricing.py: rate_ceiling is populated from
  // rr.modeled_rate, the ONLY rate that feeds incentive_ceiling_usd /
  // selected_incentive_usd / npc_with_adjustments_usd.
  const seg = { claims_incentive: true, rate_floor: 0.30, rate_ceiling: 0.40, is_band_ceiling: true };
  const info = modeledRateInfo(seg);
  assert.equal(info.modeledPct, 40, "modeled rate must be the ceiling (40), matching what funds the incentive");
  assert.equal(info.floorPct, 30);
  assert.equal(info.isBandCeiling, true);
  assert.equal(modeledRateInfo({ claims_incentive: false }), null);
  assert.equal(modeledRateInfo(null), null);
});

test("presentExclusionReason truncates to the first real sentence and humanizes snake_case tokens, never a fabricated category", async () => {
  const { presentExclusionReason } = await import("../src/lib/globeHoverFormat.js");
  const raw = "Not production-capable: the production requires marine_filming, open_water_filming, which this jurisdiction cannot provide. Rejected on capability, independent of any incentive.";
  const out = presentExclusionReason(raw);
  assert.ok(!out.includes("_"), "must not leak raw snake_case engine tokens");
  assert.ok(out.includes("marine filming"), "must humanize, not delete, the real requirement token");
  assert.ok(!out.includes("Rejected on capability"), "must be truncated to the first sentence only");
  assert.equal(presentExclusionReason(null), null);
});

test("relatedJurisdictions returns the structure's own real participants, excluding the hovered code", async () => {
  const { relatedJurisdictions } = await import("../src/lib/globeHoverFormat.js");
  const structure = { participants: ["MU", "BE", "FR"] };
  const names = { MU: "Mauritius", BE: "Belgium", FR: "France" };
  const out = relatedJurisdictions(structure, "MU", (c) => names[c]);
  assert.deepEqual(out, [{ code: "BE", name: "Belgium" }, { code: "FR", name: "France" }]);
  assert.deepEqual(relatedJurisdictions(null, "MU", (c) => names[c]), []);
});

// ── Phase 3B Batch 1: category-state diff engine ────────────────────────

test("diffCategories reports only real changes, never a false positive on first observation", async () => {
  const { diffCategories } = await import("../src/lib/globeCategoryDiff.js");
  const prev = new Map([["MU", "gold"], ["BE", "jade"], ["FR", "amber"]]);
  const curr = new Map([["MU", "gold"], ["BE", "amber"], ["FR", "amber"], ["DE", "silver"]]);
  const changes = diffCategories(prev, curr);
  // BE changed jade -> amber: reported. FR unchanged: not reported. DE has
  // no prior entry (first observation): not reported, not a false positive.
  // MU unchanged: not reported.
  assert.deepEqual(changes, [{ iso: "BE", prevCategory: "jade", currCategory: "amber" }]);
});

test("diffCategories against an identical snapshot reports zero changes", async () => {
  const { diffCategories } = await import("../src/lib/globeCategoryDiff.js");
  const snapshot = new Map([["MU", "gold"], ["BE", "jade"]]);
  assert.deepEqual(diffCategories(snapshot, new Map(snapshot)), []);
});

test("category snapshot persistence round-trips through localStorage and is keyed per production", async () => {
  const { loadCategorySnapshot, saveCategorySnapshot } = await import("../src/lib/globeCategoryDiff.js");
  // node --test has no localStorage by default; skip gracefully rather than
  // fail the whole suite if the environment doesn't provide one (the real
  // browser runtime always does).
  if (typeof localStorage === "undefined") return;
  const snap = new Map([["MU", "gold"], ["BE", "jade"]]);
  saveCategorySnapshot("TEST-PROD-A", snap);
  saveCategorySnapshot("TEST-PROD-B", new Map([["MU", "silver"]]));
  const loadedA = loadCategorySnapshot("TEST-PROD-A");
  const loadedB = loadCategorySnapshot("TEST-PROD-B");
  assert.equal(loadedA.get("MU"), "gold");
  assert.equal(loadedA.get("BE"), "jade");
  assert.equal(loadedB.get("MU"), "silver", "productions must not share a snapshot key");
});

// ── Phase 3B Batch 2: border quality, hover illumination, category pulse ──

test("altitudeJitter is deterministic and stays far below the smallest real altitude step", async () => {
  const src = read("components/Globe3D.jsx");
  const fn = /function altitudeJitter[\s\S]*?\n}/.exec(src);
  assert.ok(fn, "altitudeJitter not found");
  // eslint-disable-next-line no-eval
  const altitudeJitter = new Function(`${fn[0]}; return altitudeJitter;`)();
  const a = altitudeJitter("US-GA");
  const b = altitudeJitter("US-GA");
  const c = altitudeJitter("CA-BC");
  assert.equal(a, b, "same ISO must jitter identically every call — never random per frame");
  assert.ok(Math.abs(a) < 2e-5 + 1e-12, `jitter ${a} exceeds its own documented +/-2e-5 bound`);
  // INACTIVE_POLYGON_ALTITUDE = 0.002 is the smallest real semantic step —
  // jitter must be at least an order of magnitude below it or it would
  // visibly perturb the cap/fill, not just tie-break the stroke.
  assert.ok(Math.abs(a) < 0.002 / 10, "jitter must stay far below the smallest real altitude step");
  assert.notEqual(a, c, "different ISOs should (almost always) get different jitter");
});

test("altitudeFn applies the jitter to every branch, so no branch reintroduces exact stroke coincidence", async () => {
  const src = read("components/Globe3D.jsx");
  const fn = /const altitudeFn = \(feat\) => \{[\s\S]*?\n    \};/.exec(src);
  assert.ok(fn, "altitudeFn not found");
  const body = fn[0];
  // Every return in this function must include the jitter term.
  const returns = body.match(/return [^;]+;/g) || [];
  assert.ok(returns.length >= 4, `expected at least 4 return branches, found ${returns.length}`);
  for (const r of returns) {
    assert.ok(r.includes("jitter"), `altitudeFn branch does not apply the jitter: ${r}`);
  }
});

test("ocean drift animates the SAME texture's UV offset only — no geometry, no land motion, gated on ambientMotion", async () => {
  const src = read("components/Globe3D.jsx");
  assert.match(src, /oceanSurfaceTexture\.offset\.x\s*=/, "ocean drift must animate the texture offset");
  assert.ok(!/land.*\.offset\.[xy]\s*=/i.test(src), "land must never be animated by the ocean drift");
  // The drift line must appear strictly between the ambientMotion gate and
  // the frame's requestAnimationFrame call (i.e. inside that gated block,
  // not a separately-scheduled or always-on animation).
  const gateIdx = src.indexOf("if (stateRef.current.ambientMotion)");
  const driftIdx = src.indexOf("oceanSurfaceTexture.offset.x =");
  const rafIdx = src.indexOf("frameId = requestAnimationFrame(animate)");
  assert.ok(gateIdx > -1 && driftIdx > gateIdx && driftIdx < rafIdx, "ocean drift must be inside the ambientMotion-gated animate loop");
});

test("Co-Production Opportunity hover illumination is a no-op for every other category", async () => {
  const src = read("screens/production/ProjectGlobe.jsx");
  const block = /const \{ illuminatedIsos, primaryIlluminatedIso \} = useMemo\(\(\) => \{[\s\S]*?\n  \}, \[/.exec(src);
  assert.ok(block, "illumination useMemo not found");
  assert.match(block[0], /hover\.status !== "amber"/, 'illumination must gate on status === "amber" only');
  assert.match(block[0], /relatedCodes/, "illumination must be built from the real relatedCodes, not invented");
});

test("category pulse only fires on a real rank IMPROVEMENT, using the shared STATUS_RANK", async () => {
  const src = read("screens/production/ProjectGlobe.jsx");
  assert.match(src, /STATUS_RANK\[c\.currCategory\] > STATUS_RANK\[c\.prevCategory\]/, "pulse must gate on an improving STATUS_RANK comparison");
  assert.match(src, /prefers-reduced-motion/, "pulse must check prefers-reduced-motion before scheduling");
  assert.match(src, /clearTimeout\(pulseTimeoutRef\.current\)/, "a new pulse must clear any pending previous pulse timeout, never stack");
});

test("pulse brighten is the strongest of the three tiers, and never invents a new colour", async () => {
  const src = read("components/Globe3D.jsx");
  const capFn = /const capColorFn = \(feat\) => \{[\s\S]*?\n    \};/.exec(src)[0];
  assert.match(capFn, /brightenHex\(base, 0\.45\)/, "pulse must use the documented 0.45 tier");
  assert.match(capFn, /liveRef\.current\.pulsingIsos\?\.has\(iso\)/, "pulse must read from liveRef.current.pulsingIsos");
  // All three tiers (hover/illumination/pulse) must route through the same
  // brightenHex helper — never a second, hardcoded colour system.
  const brightenCalls = (capFn.match(/brightenHex\(/g) || []).length;
  assert.ok(brightenCalls >= 3, "hover, illumination and pulse should all route through brightenHex");
});

test("beacon-rendered jurisdictions (Mauritius/Malta/Singapore) also receive illumination/pulse, not just polygons", async () => {
  const src = read("components/Globe3D.jsx");
  const pointFn = /const pointColorFn = \(d\) => \{[\s\S]*?\n    \};/.exec(src);
  assert.ok(pointFn, "pointColorFn not found");
  assert.match(pointFn[0], /liveRef\.current\.illuminatedIsos\?\.has\(d\.iso\)/, "pointColorFn must check illuminatedIsos");
  assert.match(pointFn[0], /liveRef\.current\.pulsingIsos\?\.has\(d\.iso\)/, "pointColorFn must check pulsingIsos");
  // The repaint-trigger effects must re-invoke pointColor, or a beacon
  // country's illumination would never repaint on hover start/end.
  assert.match(src, /\.polygonStrokeColor\(globe\.polygonStrokeColor\(\)\)\s*\n\s*\.pointColor\(globe\.pointColor\(\)\)/, "illumination repaint effect must re-invoke pointColor too");
});

// ── Phase 3B ledger reconciliation: Co-Production relationship fixture ────
//
// THE DEFECT THESE GUARD. The Phase 3B reconciliation measured live output and
// found `relatedCodes` EMPTY for all 86 jurisdictions, so the Co-Production
// illumination had never fired at runtime despite being implemented and
// unit-tested. Cause: two structures exist per partner — ALLOC-RELOC-<X>
// (participants [X], fully priced -> jade) and ALLOC-COMPONENT-POST-<X>
// (participants [MU, X], blocked -> amber) — and buildCountryStatuses keeps the
// HIGHER STATUS_RANK, so the single-participant one always wins. Live counts
// confirm the same thing: 1 gold / 84 jade / 0 amber / 21 silver, i.e. this
// production has no Co-Production Opportunities at all.

test("the fixture Co-Production relationship is dev-only data and never a colour or a status", () => {
  const rel = fixtureRelatedFor("EG");
  assert.ok(rel, "the fixture must define at least one Co-Production relationship to validate against");
  assert.ok(Array.isArray(rel.related) && rel.related.length >= 2 && rel.related.length <= 4,
    "the relationship must name 2-4 related jurisdictions, per the acceptance fixture contract");
  assert.ok(rel.related.includes(rel.primary), "the primary must be one of the related jurisdictions");
  // Raw globe keys only — never a hex, never a semantic slot name.
  for (const code of rel.related) {
    assert.match(code, /^[A-Z]{2}(-[A-Z0-9]+)?$/, `${code} must be a plain globe key`);
  }
  const src = read("lib/globeVisualFixture.js");
  assert.ok(!/#[0-9a-fA-F]{3,6}/.test(src), "the fixture must never declare a colour of its own");
  assert.equal(fixtureRelatedFor("ZZ-NOT-A-PLACE"), null, "unlisted keys must return null, not a default relationship");
});

test("the fixture relationship anchor is an amber jurisdiction, or illumination could never fire", () => {
  const rel = fixtureRelatedFor("EG");
  assert.equal(fixtureSlotFor("EG"), "amber",
    "illumination is gated on hover.status === 'amber' (ProjectGlobe.jsx), so the anchor must be amber");
  // At least one related jurisdiction must be beacon-rendered, so the
  // pointColorFn path is exercised and not just the polygon path.
  assert.ok(rel.related.includes("MT"),
    "the relationship must include a beacon-rendered jurisdiction (Malta) to exercise pointColorFn");
});

test("fixture relationships can never leak into the real-data path", () => {
  const src = stripComments(read("lib/globeData.js"));
  // The fixture relationship is attached to the entry ONLY inside
  // applyFixtureStates, which is itself only called under isFixtureActive().
  const applyFn = /function applyFixtureStates\(statuses\)[\s\S]*?\n\}/.exec(src);
  assert.ok(applyFn, "applyFixtureStates not found");
  assert.match(applyFn[0], /fixtureRelatedFor\(/, "the relationship must be attached inside applyFixtureStates");
  assert.match(src, /if \(isFixtureActive\(\)\) applyFixtureStates\(statuses\)/,
    "applyFixtureStates must stay gated on isFixtureActive()");
  const others = src.split(/function applyFixtureStates\(statuses\)[\s\S]*?\n\}/).join("");
  assert.ok(!/fixtureRelatedFor\(/.test(others),
    "fixtureRelatedFor must be called from exactly one place — applyFixtureStates");
  // And the hover payload must FALL BACK to the real participants.
  assert.match(src, /entry\.fixtureRelated\?\.related\s*\?\?[\s\S]{0,120}participants/,
    "relatedCodes must fall back to the structure's real participants when no fixture relationship exists");
  assert.match(src, /entry\.fixtureRelated\?\.primary\s*\?\?\s*structure\?\.primary_jurisdiction/,
    "primaryJurisdictionCode must fall back to the structure's real primary_jurisdiction");
});

// ── Production Overview + Project Globe UI regression repair ───────────────
//
// resolveRestingFlight is the extracted decision logic for the camera-flight
// effect's "no selection, no mode-specific focus target" case. VERIFIED root
// cause (traced directly in Globe3D.jsx, unchanged since the Globe's earliest
// commit — 2b961ce): the effect used to `return` immediately whenever there
// was no explicit target, silently leaving the camera at whatever distance a
// PREVIOUS flight (a selected jurisdiction, or Optimizer Overlay's own
// pathway framing) had reached — Jurisdictions mode with nothing selected
// never had a case that returned the camera to its OWN whole-globe resting
// fit. That is what read as "the Globe shrinks/sticks when switching modes".
//
// SCOPE, honestly stated (see file header): this proves the DECISION is
// correct — given a camera away from resting, it computes a flight back to
// resting along the camera's current direction; given a camera already at
// resting, it correctly does nothing. It cannot prove the tween actually
// paints on screen (that needs a real, focused/visible browser tab — the
// project has no browser-test dependency, same limitation the header above
// already states for the rest of this file).

test("resolveRestingFlight flies back to the resting fit when the camera is away from it", () => {
  // Camera sitting on the +Z axis at distance 250 (e.g. Optimizer Overlay's
  // own tighter pathway framing), resting fit is 302 (a typical whole-globe
  // fit at a landscape panel) — this is the exact real-world case that used
  // to leave the Globe "shrunk" after returning to Jurisdictions mode.
  const result = resolveRestingFlight({ x: 0, y: 0, z: 250 }, 302);
  assert.ok(result, "must return a flight when the camera is away from resting");
  assert.equal(result.distance, 302);
  // Direction preserved (still pointing along +Z) — only the distance is
  // corrected, never the orientation the producer (or autorotation) had
  // settled on.
  assert.deepEqual(result.direction, { x: 0, y: 0, z: 1 });
});

test("resolveRestingFlight is a genuine no-op once the camera is already resting", () => {
  assert.equal(resolveRestingFlight({ x: 0, y: 0, z: 302 }, 302), null);
  // Within the same 1.5-unit epsilon applySize's own atRestingFraming check
  // uses — never re-triggers a flight for float noise around the same spot.
  assert.equal(resolveRestingFlight({ x: 0, y: 0, z: 301 }, 302), null);
});

test("resolveRestingFlight preserves the camera's actual 3D direction, not just a Z-axis case", () => {
  // A camera at an arbitrary orbited position (e.g. after manual drag or
  // autorotation) away from resting — the returned direction must be the
  // SAME unit vector, only the magnitude (distance) corrected.
  const pos = { x: 100, y: 50, z: 200 };
  const len = Math.hypot(pos.x, pos.y, pos.z);
  const result = resolveRestingFlight(pos, 302);
  assert.ok(result);
  assert.equal(result.distance, 302);
  assert.ok(Math.abs(result.direction.x - pos.x / len) < 1e-9);
  assert.ok(Math.abs(result.direction.y - pos.y / len) < 1e-9);
  assert.ok(Math.abs(result.direction.z - pos.z / len) < 1e-9);
  // The direction must itself be a unit vector.
  const dirLen = Math.hypot(result.direction.x, result.direction.y, result.direction.z);
  assert.ok(Math.abs(dirLen - 1) < 1e-9);
});

test("resolveRestingFlight never divides by zero at the degenerate origin", () => {
  assert.equal(resolveRestingFlight({ x: 0, y: 0, z: 0 }, 302), null);
});

test("Globe3D's selection-flight effect calls resolveRestingFlight for the no-target case, never a bare return", () => {
  const src = stripComments(read("components/Globe3D.jsx"));
  assert.match(src, /import\s*\{[^}]*resolveRestingFlight[^}]*\}\s*from\s*"\.\.\/lib\/globeFit"/,
    "Globe3D must import resolveRestingFlight from lib/globeFit — the shared, tested decision, never a re-implemented inline copy");
  assert.match(src, /resolveRestingFlight\(camera\.position,\s*restingFit\)/,
    "the no-target branch must call resolveRestingFlight rather than silently returning");
});
