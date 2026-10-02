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
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): the Optimizer branch now
  // renders via OPTIMIZER_SECTIONS.map (Recommended/Evaluated Alternatives)
  // plus a trailing Needs More Facts block, superseding TIER_SECTIONS — the
  // real, still-load-bearing invariant this test protects (never re-sort
  // the already-ordered optimizerProj arrays) is unchanged.
  // STRUCTURE-AWARE GLOBE (2026-10-01): the Optimizer branch now groups the already-ordered
  // recommended+evaluated pool by ACTUAL canonical structural family (groupByFamily), preserving canonical order.
  assert.match(optimizerBranch, /groupByFamily\(/, "Optimizer branch must render via groupByFamily");
  assert.match(optimizerBranch, /optimizerProj\?\.recommended[\s\S]*optimizerProj\?\.evaluated/, "Optimizer branch must read the optimizerProj arrays straight, never re-filter/re-derive them");
  assert.doesNotMatch(optimizerBranch, /\.sort\(/, "Optimizer mode must render optimizerProj's own arrays verbatim, never re-sorted");
  assert.match(singleJurisdictionBranch, /\[\.\.\.visibleStructures\]\s*\n?\s*\.sort\(\(a, b\) => \(rankById\.get\(a\.structure_id\)\?\.rank/, "the rankById sort must still exist for Single Jurisdiction mode, unchanged");
});

// ── 2. Full Globe renders three genuine sections, correctly counted ────

// OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): SUPERSEDES the prior
// practicality-tier section test — confirmed live across all four
// acceptance productions that PRACTICAL_HYBRID/FORMAL_COPRODUCTION/
// ADVANCED_MULTI_JURISDICTION was a threshold dimension (2 vs 3+
// jurisdictions) within the SAME structural family, not real families, and
// "Advanced Multi-Jurisdiction" as a section heading misrepresented hundreds
// of same-family structures as a different, more complex one. The
// controlling contract's own section boundaries (Recommended / Evaluated
// Alternatives / Needs More Facts) are pinned here instead; structural
// family now shows per-row via OPTIMIZER_FAMILY_LABEL (see globeData.js).
test("ProjectGlobe.jsx groups Optimizer structures by actual structural family, then Needs More Facts, with real counts", () => {
  const src = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(src, /groupByFamily\(\[\.\.\.\(optimizerProj\?\.recommended/);
  assert.match(src, /coproductionNeedsFactsLabel\(optimizerProj\.opportunities\.length\)/);   // 2026-10-02: co-production opportunities, not "programs"
  // A family with zero real entries renders no header (groupByFamily returns only non-empty groups).
  assert.match(src, /optimizerProj\?\.opportunities\?\.length > 0/, "Needs More Facts must only render when real opportunities exist");
  assert.doesNotMatch(src, /Practical Hybrid<|Advanced Multi-Jurisdiction<|heading: "/, "complexity/practicality are badges, never section headings");
  const famIdx = src.indexOf("groupByFamily([...(optimizerProj");
  const factsIdx = src.lastIndexOf("coproductionNeedsFactsLabel(optimizerProj.opportunities.length)");
  assert.ok(famIdx > 0 && famIdx < factsIdx, "family groups render before the trailing Needs More Facts block");
});

test("family grouping keeps canonical order inside each family and never re-sorts by economics", async () => {
  const { groupByFamily } = await import("../src/lib/globeStructure.js");
  const mk = (id, cls, participants) => ({ structure_id: id, classification: cls, participants });
  const pool = [
    mk("r1", "HYBRID_ANCHOR_COMPONENT", ["MU", "GR"]), mk("r2", "HYBRID_ANCHOR_COMPONENT", ["MU", "GR", "IT"]),
    mk("e1", "HYBRID_ANCHOR_COMPONENT", ["MU", "ES"]), mk("e2", "STACKED_PROGRAMS", ["CA-ON"]),
  ];
  const groups = groupByFamily(pool);
  assert.deepEqual(groups.map((g) => g.family), ["stack", "hybrid_two_party", "hybrid_multi_party"]);
  assert.deepEqual(groups.find((g) => g.family === "hybrid_two_party").items.map((s) => s.structure_id), ["r1", "e1"]);
});
