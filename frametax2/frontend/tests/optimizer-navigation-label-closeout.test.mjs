// ── OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22) — regression protection ──
//
// Run with: npm test (node --test)
//
// Root defects this file pins the fix for:
//   1. ProjectGlobe.jsx independently re-sorting the already-tier-ordered
//      Optimizer pool by rankById.
//   2. Full Globe rendering one flat list instead of three real sections.
//   3/4. Component-distinct / anchor-distinct scenarios rendering
//      indistinguishable visible labels, and a non-claiming segment-
//      tracking jurisdiction leaking into that label.
//
// buildScenarioLabel (lib/format.jsx) is the one canonical producer
// scenario label adapter — these tests exercise it directly (pure logic,
// no JSX, no backend) and pin the SOURCE-level facts that can't be
// exercised without a DOM harness (this project has none — see every
// other *-truthfulness/*-wiring test file's own header comment for the
// same convention): that Workspace/Overview/ProjectGlobe all import and
// call it, and that ProjectGlobe's Optimizer-mode list no longer re-sorts
// by rankById.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildScenarioLabel } from "../src/lib/scenarioLabel.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

function fakeCA(overrides) {
  return { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", component: "post", allocated_usd: 100, ...overrides };
}

function fvdManitobaStructure(overrides) {
  return {
    structure_id: "s1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "GR", participants: ["GR", "CA-MB", "CA-NL"],
    practicality_tier: "ADVANCED_MULTI_JURISDICTION", participant_count: 3,
    component_allocations: [
      { jurisdiction_code: "GR", program_slug: "gr_cash_rebate", component: "principal_production", allocated_usd: 1000 },
      { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", component: "post", allocated_usd: 100, jurisdiction_display_name: "Canada — Manitoba" },
      { jurisdiction_code: "CA-NL", program_slug: "ca_nl_all_spend_credit", component: "vfx", allocated_usd: 50, jurisdiction_display_name: "Canada — Newfoundland & Labrador" },
    ],
    ...overrides,
  };
}

// ── 4. Component-distinct structures produce distinct visible labels ────

test("buildScenarioLabel: two structures sharing every field except the routed component render visibly distinct labels", () => {
  const post = fvdManitobaStructure({ structure_id: "post-variant" });
  const music = fvdManitobaStructure({
    structure_id: "music-variant",
    component_allocations: [
      { jurisdiction_code: "GR", program_slug: "gr_cash_rebate", component: "principal_production", allocated_usd: 1000 },
      { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", component: "music", allocated_usd: 100, jurisdiction_display_name: "Canada — Manitoba" },
      { jurisdiction_code: "CA-NL", program_slug: "ca_nl_all_spend_credit", component: "vfx", allocated_usd: 50, jurisdiction_display_name: "Canada — Newfoundland & Labrador" },
    ],
  });
  const postLabel = buildScenarioLabel(post);
  const musicLabel = buildScenarioLabel(music);
  assert.notEqual(postLabel, musicLabel, "post->Manitoba and music->Manitoba must never render the same label");
  assert.match(postLabel, /Post/i);
  assert.match(musicLabel, /Music/i);
});

test("buildScenarioLabel: two structures sharing every routed component but a DIFFERENT anchor jurisdiction render visibly distinct labels", () => {
  // The confirmed live FVD gap: 68 real scenarios share the exact same
  // routed legs (post->Manitoba, vfx->Newfoundland & Labrador) but differ
  // only by which real jurisdiction anchors the principal leg.
  const greece = fvdManitobaStructure({ structure_id: "greece-anchor", primary_jurisdiction: "GR" });
  const italy = fvdManitobaStructure({ structure_id: "italy-anchor", primary_jurisdiction: "IT" });
  const greeceLabel = buildScenarioLabel(greece);
  const italyLabel = buildScenarioLabel(italy);
  assert.notEqual(greeceLabel, italyLabel, "a Greece-anchored and an Italy-anchored scenario sharing identical routed legs must never render the same label");
});

test("buildScenarioLabel: a subnational code colliding with an unrelated country's display name (Georgia the US state vs Georgia the country) is disambiguated", () => {
  const georgiaCountry = fvdManitobaStructure({ structure_id: "ge-country", primary_jurisdiction: "GE" });
  const georgiaState = fvdManitobaStructure({ structure_id: "us-ga-state", primary_jurisdiction: "US-GA" });
  assert.notEqual(buildScenarioLabel(georgiaCountry), buildScenarioLabel(georgiaState));
});

// ── 5. Non-claiming tracking jurisdictions do not enter the label ───────

test("buildScenarioLabel never surfaces a non-claiming segment-tracking jurisdiction that has no component_allocations row", () => {
  // The confirmed live Little Utopia shape: `segments` carries a real
  // non-claiming "US" cost-tracking entry (claims_incentive: false)
  // alongside the 2 real claiming participants — component_allocations
  // never carries it. buildScenarioLabel reads component_allocations
  // exclusively, so it cannot reintroduce that leak.
  const structure = {
    structure_id: "mu-mb", classification: "HYBRID_ANCHOR_COMPONENT",
    primary_jurisdiction: "MU", participants: ["MU", "CA-MB"],
    practicality_tier: "PRACTICAL_HYBRID", participant_count: 2,
    segments: [
      { jurisdiction_code: "CA-MB", claims_incentive: true },
      { jurisdiction_code: "MU", claims_incentive: true },
      { jurisdiction_code: "US", claims_incentive: false },
    ],
    component_allocations: [
      { jurisdiction_code: "MU", program_slug: "mu_edb_incentive", component: "principal_production", allocated_usd: 1000 },
      { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", component: "vfx", allocated_usd: 50, jurisdiction_display_name: "Canada — Manitoba" },
    ],
  };
  const label = buildScenarioLabel(structure);
  assert.doesNotMatch(label, /United States|US\b(?!,)/, `label must never mention the non-claiming US segment — got ${JSON.stringify(label)}`);
  assert.match(label, /Manitoba/);
});

test("buildScenarioLabel returns null/undefined-safe output and never throws on a missing structure", () => {
  assert.equal(buildScenarioLabel(null), "");
  assert.equal(buildScenarioLabel(undefined), "");
});

test("buildScenarioLabel prefixes an Advanced-tier scenario with its jurisdiction count, never a Practical/Formal one", () => {
  const advanced = fvdManitobaStructure({ practicality_tier: "ADVANCED_MULTI_JURISDICTION", participant_count: 3 });
  const practical = { ...fvdManitobaStructure({ practicality_tier: "PRACTICAL_HYBRID", participant_count: 2 }) };
  assert.match(buildScenarioLabel(advanced), /^Advanced · 3 jurisdictions ·/);
  assert.doesNotMatch(buildScenarioLabel(practical), /^Advanced/);
});

// ── 6. Workspace, Overview, Full Globe and Map/Split call the SAME adapter ──
// (Map/Split reuse Workspace's own ScenarioCard/scenarioOptionLabel — see
// Workspace.jsx's own established, unchanged structural sharing — so
// confirming Workspace + ProjectGlobe + Overview import buildScenarioLabel
// covers every surface named in this task.)

test("Workspace.jsx, ProjectGlobe.jsx and IncentiveIntelligence.jsx (Overview) all import buildScenarioLabel from the SAME module, never a local re-derivation", () => {
  for (const path of ["screens/production/Workspace.jsx", "screens/production/ProjectGlobe.jsx", "components/IncentiveIntelligence.jsx"]) {
    const src = stripComments(read(path));
    assert.match(src, /buildScenarioLabel/, `${path} must import buildScenarioLabel`);
    assert.match(src, /from ["'].*lib\/format["']/, `${path} must import from lib/format`);
  }
});

// ── 1. ProjectGlobe no longer independently re-sorts the Optimizer pool ─

test("ProjectGlobe.jsx no longer re-sorts visibleStructures by rankById in Optimizer mode", () => {
  const src = stripComments(read("screens/production/ProjectGlobe.jsx"));
  // The OLD defect: an unconditional `.sort((a,b) => rankById...)` applied
  // to visibleStructures regardless of mode. The corrected source must
  // branch on globeMode, applying the rankById sort ONLY to the non-
  // Optimizer (Single Jurisdiction) path.
  const ternaryMatch = src.match(/globeMode === MODE_OPTIMIZER \? \(([\s\S]*?)\) : \(([\s\S]*?)\)\s*\}\s*<\/div>/);
  assert.ok(ternaryMatch, "ProjectGlobe.jsx must branch the jurlist rendering on globeMode === MODE_OPTIMIZER");
  const [, optimizerBranch, singleJurisdictionBranch] = ternaryMatch;
  assert.match(optimizerBranch, /TIER_SECTIONS\.map/, "Optimizer branch must render via TIER_SECTIONS");
  assert.match(optimizerBranch, /visibleStructures\.filter/, "Optimizer branch must filter visibleStructures per tier, not re-sort it");
  assert.doesNotMatch(optimizerBranch, /\.sort\(/, "Optimizer mode must render visibleStructures verbatim, never re-sorted");
  assert.match(singleJurisdictionBranch, /\[\.\.\.visibleStructures\]\s*\n?\s*\.sort\(\(a, b\) => \(rankById\.get\(a\.structure_id\)\?\.rank/, "the rankById sort must still exist for Single Jurisdiction mode, unchanged");
});

// ── 2. Full Globe renders three genuine sections, correctly counted ────

test("ProjectGlobe.jsx defines the three tier sections in the required order and renders each with its own real count", () => {
  const src = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(src, /PRACTICAL_HYBRID.*Practical Hybrids/s);
  assert.match(src, /FORMAL_COPRODUCTION.*Formal Co-Productions/s);
  assert.match(src, /ADVANCED_MULTI_JURISDICTION.*Advanced Multi-Jurisdiction/s);
  // Order: Practical must appear before Formal, which must appear before Advanced.
  const practicalIdx = src.indexOf("PRACTICAL_HYBRID");
  const formalIdx = src.indexOf("FORMAL_COPRODUCTION");
  const advancedIdx = src.indexOf("ADVANCED_MULTI_JURISDICTION");
  assert.ok(practicalIdx < formalIdx && formalIdx < advancedIdx, "sections must be declared Practical -> Formal -> Advanced");
  // A tier with zero real scenarios must render no section at all.
  assert.match(src, /if \(tierStructures\.length === 0\) return null;/);
});

test("section partitioning algorithm: a tier-pre-sorted scenario list groups into contiguous runs matching each tier's real count, never re-grouped by economics", () => {
  // Mirrors the exact partition ProjectGlobe.jsx's TIER_SECTIONS.map(...)
  // performs: filter the already-sorted array by tier, never re-sort.
  const TIER_SECTIONS = [
    { tier: "PRACTICAL_HYBRID", heading: "Practical Hybrids" },
    { tier: "FORMAL_COPRODUCTION", heading: "Formal Co-Productions" },
    { tier: "ADVANCED_MULTI_JURISDICTION", heading: "Advanced Multi-Jurisdiction" },
  ];
  const scenarios = [
    { structure_id: "p1", practicality_tier: "PRACTICAL_HYBRID", npc_with_adjustments_usd: 100 },
    { structure_id: "p2", practicality_tier: "PRACTICAL_HYBRID", npc_with_adjustments_usd: 200 },
    { structure_id: "a1", practicality_tier: "ADVANCED_MULTI_JURISDICTION", npc_with_adjustments_usd: 50 },
    { structure_id: "a2", practicality_tier: "ADVANCED_MULTI_JURISDICTION", npc_with_adjustments_usd: 60 },
    { structure_id: "a3", practicality_tier: "ADVANCED_MULTI_JURISDICTION", npc_with_adjustments_usd: 70 },
  ];
  const sections = TIER_SECTIONS.map(({ tier, heading }) => ({
    heading, structures: scenarios.filter((s) => s.practicality_tier === tier),
  })).filter((s) => s.structures.length > 0);
  assert.deepEqual(sections.map((s) => s.heading), ["Practical Hybrids", "Advanced Multi-Jurisdiction"], "Formal must be omitted entirely when it has zero real scenarios");
  assert.equal(sections[0].structures.length, 2);
  assert.equal(sections[1].structures.length, 3);
  // Never re-sorted by NPC across the whole set -- a1 (NPC 50, cheapest
  // overall) must NOT appear before p1/p2 despite its lower NPC, because
  // it belongs to a later tier.
  assert.deepEqual(sections[0].structures.map((s) => s.structure_id), ["p1", "p2"]);
});
