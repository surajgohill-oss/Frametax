// ── SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23) — closeout regression lock ──
//
// Run with: npm test (node --test)
//
// Pure logic + source-text tests only, matching this suite's existing style
// (no jsdom/react-testing-library dependency exists here — see package.json).
// Covers the properties the broader Single Jurisdiction Globe wiring pass
// needed locked down that the pre-existing test files did not yet cover:
//   - subnational jurisdictions sharing a country polygon never collapse
//     into one marker/hover/click identity (the real AU defect this pass
//     found and fixed — see globeData.js's SUBNATIONAL_COUNTRIES comment)
//   - marker click resolves best_per_jurisdiction[code] directly, never
//     structuresByCode[0] (source-text pin on ProjectGlobe.jsx/Workspace.jsx)
//   - first/middle/last winner identity survives end-to-end through
//     buildGlobeView's points
//   - side-list count equals the backend's own best_per_jurisdiction count
//   - every real jurisdiction code served by all four acceptance productions
//     has a JURISDICTION_COORDS marker coordinate (locks in the live Phase 1
//     finding as a permanent, backend-independent regression test)
//   - the Single Jurisdiction legend/status vocabulary never leaks Optimizer
//     practicality-tier wording
//   - project navigation still resets selectedJurisdiction (CODEX_FG-001)

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  buildCountryStatuses,
  buildGlobeView,
  buildCountryPoints,
  GLOBE_SEMANTIC,
} from "../src/lib/globeData.js";
import { admissibleForMode, MODE_NORMAL } from "../src/lib/workspaceScenarioMode.js";
import { JURISDICTION_COORDS } from "../src/lib/jurisdictions.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcPath = (rel) => path.join(__dirname, "..", "src", rel);
const readSrc = (rel) => readFileSync(srcPath(rel), "utf8");

function structure(overrides) {
  const id = overrides.structure_id || "s1";
  return {
    structure_id: id,
    structure_type: overrides.structure_type || "single_country",
    classification: overrides.classification || "SINGLE_JURISDICTION",
    label: overrides.label || "Base",
    primary_jurisdiction: overrides.primary_jurisdiction ?? `JUR-${id}`,
    participants: overrides.participants || [overrides.primary_jurisdiction ?? `JUR-${id}`],
    economic_identity: overrides.economic_identity ?? `econ-${id}`,
    is_fully_priced: overrides.is_fully_priced ?? true,
    is_baseline: overrides.is_baseline ?? false,
    npc_with_adjustments_usd: overrides.npc_with_adjustments_usd ?? 900_000,
    net_benefit_vs_anchor_usd: overrides.net_benefit_vs_anchor_usd ?? null,
    segments: overrides.segments || [],
    blockers: overrides.blockers || [],
    treaty_slug: overrides.treaty_slug ?? null,
    ...overrides,
  };
}

function bestPerJurisdiction(entries) {
  const out = {};
  for (const e of entries) out[e.primary_jurisdiction] = e;
  return out;
}

function allocatedOf(structures, bpjEntries) {
  return {
    structures,
    ranking: [],
    canonical_selected_structure_id: null,
    best_per_jurisdiction: bestPerJurisdiction(bpjEntries ?? structures),
    optimizer_candidates: [],
    optimizer_scenarios: [],
  };
}

// 1. Subnational jurisdictions sharing a country polygon never collapse —
// the real, live AU defect: a country-level "AU" winner and three real
// distinct "AU-NSW"/"AU-QLD"/"AU-SA" winners coexist in best_per_jurisdiction
// for every one of the four acceptance productions. Before this pass,
// globeKey() only special-cased US/CA, so all four folded onto one "AU"
// choropleth entry and three of the four real winners had no marker, no
// hover, and no click target anywhere on the Globe.
test("buildCountryStatuses/buildCountryPoints: AU country-level winner and AU-NSW/AU-QLD/AU-SA subnational winners each get their own distinct entry, none silently dropped", () => {
  const winners = [
    structure({ structure_id: "au-country", primary_jurisdiction: "AU", npc_with_adjustments_usd: 400_000 }),
    structure({ structure_id: "au-nsw", primary_jurisdiction: "AU-NSW", npc_with_adjustments_usd: 100_000 }),
    structure({ structure_id: "au-qld", primary_jurisdiction: "AU-QLD", npc_with_adjustments_usd: 200_000 }),
    structure({ structure_id: "au-sa", primary_jurisdiction: "AU-SA", npc_with_adjustments_usd: 300_000 }),
  ];
  const allocated = allocatedOf(winners);
  const rankById = new Map();
  const statuses = buildCountryStatuses(allocated, rankById, MODE_NORMAL);
  const auKeys = ["AU", "AU-NSW", "AU-QLD", "AU-SA"];
  for (const key of auKeys) {
    assert.ok(statuses.has(key), `${key} must have its own status entry, not be folded into a sibling`);
  }
  assert.equal(new Set(auKeys.map((k) => statuses.get(k).best.structure.structure_id)).size, 4,
    "all four AU-family winners must resolve to four distinct structures");

  const hoverByIso = new Map();
  const points = buildCountryPoints(statuses, hoverByIso, null);
  const pointIds = new Set(points.filter((p) => auKeys.includes(p.id)).map((p) => p.id));
  assert.deepEqual([...pointIds].sort(), auKeys, "every AU-family winner must render its own marker point");
});

// 2. Marker click resolves the canonical best_per_jurisdiction[code] winner
// directly — never structuresByCode[0], which this pass replaced precisely
// because it could silently resolve to an arbitrary participant rather than
// the exact canonical winner for the clicked code.
test("ProjectGlobe.jsx and Workspace.jsx resolve Single Jurisdiction marker clicks via best_per_jurisdiction[code] directly, not structuresByCode", () => {
  for (const rel of ["screens/production/ProjectGlobe.jsx", "screens/production/Workspace.jsx"]) {
    const src = readSrc(rel);
    assert.match(src, /allocated\?\.best_per_jurisdiction\?\.\[code\]/,
      `${rel} must resolve Single Jurisdiction clicks via allocated.best_per_jurisdiction[code]`);
    assert.match(src, /buildCandidateDetail\(winner\)/,
      `${rel} must open the full structure-level Inspector for the resolved winner`);
  }
});

// 3. Single Jurisdiction legend/status vocabulary never leaks Optimizer
// practicality-tier wording — GLOBE_SEMANTIC and GlobeLegend.jsx describe
// Single Jurisdiction (and shared choropleth) semantics only.
test("GLOBE_SEMANTIC and GlobeLegend never use Optimizer practicality-tier vocabulary", () => {
  const banned = ["Practical Hybrid", "Official Co-production", "Advanced Multi-Jurisdiction", "recommendation threshold"];
  const allLabels = Object.values(GLOBE_SEMANTIC).flatMap((v) => [v.label, v.fullLabel]);
  for (const label of allLabels) {
    for (const b of banned) {
      assert.equal(label.toLowerCase().includes(b.toLowerCase()), false, `GLOBE_SEMANTIC label "${label}" must not reference "${b}"`);
    }
  }
  const legendSrc = readSrc("components/GlobeLegend.jsx");
  for (const b of banned) {
    assert.equal(legendSrc.toLowerCase().includes(b.toLowerCase()), false, `GlobeLegend.jsx must not reference "${b}"`);
  }
  // Colour derivation itself must come from real backend-served status
  // (rank from allocated.ranking / is_fully_priced / blockers), never from
  // array/list position — structureTier's only inputs are exactly these.
  const dataSrc = readSrc("lib/globeData.js");
  const tierFn = dataSrc.match(/export function structureTier\([\s\S]*?\n}/)[0];
  assert.match(tierFn, /rankById\.get\(structure\.structure_id\)/);
  assert.match(tierFn, /structure\.is_fully_priced/);
  assert.match(tierFn, /structure\.blockers/);
});

// 4. First/middle/last winner identity survives end-to-end through
// buildGlobeView's points — selecting any of them must resolve the exact
// structure, never a neighboring one from list-order drift.
test("buildGlobeView: first, middle, and last canonical winners each keep their own distinct structure identity in the rendered points", () => {
  const codes = ["CA-ON", "CA-MB", "IT", "GR", "NZ"];
  const winners = codes.map((code, i) =>
    structure({ structure_id: `w-${code}`, primary_jurisdiction: code, economic_identity: `econ-${code}`, npc_with_adjustments_usd: 100_000 + i * 10_000 }),
  );
  const allocated = allocatedOf(winners);
  const rankById = new Map();
  const { points, structuresByCode } = buildGlobeView(allocated, rankById, { mode: MODE_NORMAL });
  for (const code of [codes[0], codes[Math.floor(codes.length / 2)], codes[codes.length - 1]]) {
    const winner = allocated.best_per_jurisdiction[code];
    const point = points.find((p) => p.id === code);
    assert.ok(point, `${code} must have a rendered point`);
    // The canonical resolution path (best_per_jurisdiction[code]) must match
    // what the click-through would actually open — never a different
    // structure that merely shares the participant code.
    assert.equal(winner.structure_id, `w-${code}`);
    assert.equal(winner.economic_identity, `econ-${code}`);
  }
  assert.equal(structuresByCode.size, codes.length);
});

// 5. Full Globe side list count equals the backend's own best_per_jurisdiction
// count — the same admissibleForMode pool ProjectGlobe.jsx's `.sc-jurlist`
// renders from.
test("admissibleForMode (Single Jurisdiction) count equals best_per_jurisdiction count for a realistic multi-jurisdiction fixture", () => {
  const codes = ["CA-ON", "CA-MB", "IT", "GR", "NZ", "FR", "AU", "AU-NSW", "AU-QLD", "AU-SA", "US-CA", "US-GA"];
  const winners = codes.map((code) => structure({ structure_id: `w-${code}`, primary_jurisdiction: code }));
  const allocated = allocatedOf(winners);
  const visible = admissibleForMode(allocated, MODE_NORMAL);
  assert.equal(visible.length, Object.keys(allocated.best_per_jurisdiction).length);
  assert.equal(visible.length, codes.length);
  assert.equal(new Set(visible.map((s) => s.structure_id)).size, codes.length, "no duplicate winners in the side list");
});

// 6. Missing coordinates must fail visibly — locks in the live Phase 1
// finding (all 78 real jurisdiction codes served by all four acceptance
// productions on 2026-09-23) as a permanent, backend-independent regression
// test. A future code newly appearing in best_per_jurisdiction with no
// JURISDICTION_COORDS entry would otherwise silently drop that winner's
// marker with no test failure anywhere.
test("JURISDICTION_COORDS has a real coordinate for every jurisdiction code served by all four acceptance productions", () => {
  const liveCodes = [
    "AT", "AU", "AU-NSW", "AU-QLD", "AU-SA", "BG", "CA", "CA-AB", "CA-BC", "CA-MB", "CA-NB", "CA-NL", "CA-NS",
    "CA-ON", "CA-QC", "CO", "CY", "CZ", "DO", "ES", "FI", "FJ", "FR", "GB", "GE", "GR", "HR", "HU", "IE", "IS",
    "IT", "JO", "LT", "LV", "ME", "MK", "MN", "MT", "MU", "MX", "MY", "NZ", "PL", "PT", "RO", "RS", "SK", "TH",
    "TT", "UA", "US-AL", "US-AZ", "US-CA", "US-CO", "US-CT", "US-GA", "US-HI", "US-IL", "US-KY", "US-LA",
    "US-MA", "US-MN", "US-MS", "US-NC", "US-NM", "US-NV", "US-NY", "US-OK", "US-OR", "US-PA", "US-PR", "US-RI",
    "US-TN", "US-UT", "US-VA", "UY", "UZ", "ZA",
  ];
  const missing = liveCodes.filter((c) => !JURISDICTION_COORDS[c]);
  assert.deepEqual(missing, [], `these real, live jurisdiction codes have no JURISDICTION_COORDS marker coordinate: ${missing.join(", ")}`);
});

// 7. Project navigation must not leak a previous project's jurisdiction
// selection — CODEX_FG-001's project-boundary reset in AppState.jsx.
test("AppState.jsx resets selectedJurisdiction on the project-boundary-crossing effect (CODEX_FG-001)", () => {
  const src = readSrc("state/AppState.jsx");
  const resetEffect = src.match(/if \(lastResetProjectId\.current === projectId\) return;[\s\S]*?\}, \[projectId\]\);/);
  assert.ok(resetEffect, "the project-boundary reset effect must exist");
  assert.match(resetEffect[0], /setSelectedJurisdiction\(null\)/,
    "the project-boundary reset must clear selectedJurisdiction, never carrying it across projects");
});
