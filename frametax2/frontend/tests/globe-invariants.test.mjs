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
  silhouetteRadiusPx,
} from "../src/lib/globeFit.js";

import {
  FIXTURE_DISCLOSURE,
  FIXTURE_EXPECTED_COUNTS,
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
  assert.deepEqual(Object.values(STATUS_LABEL).sort(), [
    "Additional",
    "Optimized alternative",
    "Recommended",
    "Unlockable opportunity",
  ]);
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

test("no persistent Globe legend component or CSS exists", () => {
  assert.throws(() => read("components/GlobeLegend.jsx"), "GlobeLegend.jsx must stay deleted");
  const css = read("styles/screens.css");
  // Comments may reference the removed class; actual selectors may not.
  const selectors = css.match(/^\s*\.globe-legend[\w-]*\s*[,{]/gm) || [];
  assert.equal(selectors.length, 0, `legend selectors reintroduced: ${selectors.join(", ")}`);
});

test("no Globe hover card renders money", () => {
  // The Inspector owns figures, with their qualification trace and citations.
  for (const file of [
    "screens/production/ProjectGlobe.jsx",
    "screens/production/Workspace.jsx",
    "screens/production/Overview.jsx",
  ]) {
    const src = read(file);
    for (const m of src.matchAll(/<div className="globe-tooltip">([\s\S]*?)<\/div>\s*\)/g)) {
      assert.ok(
        !/incentiveUsd|npcUsd|<Money/.test(m[1]),
        `${file}: hover card renders money`,
      );
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
  for (const forbidden of ["fetch(", "XMLHttpRequest", "POST", "PUT", "PATCH"]) {
    assert.ok(!src.includes(forbidden), `fixture must not use ${forbidden}`);
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
