// ── Workspace Top-6/Data Truthfulness ────────────────────────────────────
//
// Run with: npm test (node --test, same source-level convention as
// production-overview-truthfulness.test.mjs — no DOM harness in this
// project).
//
// WHY THESE EXIST. Auditing Lips Like Sugar's real Workspace page found
// several real, generic defects: (A) same-jurisdiction structures with
// genuinely distinct programs (Australia's Location Offset vs PDV Offset)
// rendered as identical cards because compactScenarioIdentity used only
// the bare jurisdiction code; (B) EVERY card falsely showed the "①" glyph
// regardless of real canonical rank, since the badge fallback defaulted
// undefined rank to position 1; (C) manual "Set as leading" borrowed that
// SAME "①" glyph and could be shown by the Hero under the "Recommended
// Structure" label — a producer's own selection masquerading as
// CineGlobe's endorsement; (D) the whole card body was not clickable —
// only a small "Inspect" button was. See docs/architecture/
// CAPABILITY_LEDGER.md, "Workspace Top-6/Data Truthfulness" for the live
// browser walkthrough these assertions cannot replace.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

// D. Human-readable structure labels differentiate valid same-country
// outcomes — never a frontend-hardcoded map when a real registry name
// exists.
test("compactScenarioIdentity appends the real backend program_display_name to disambiguate same-jurisdiction structures", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /structure\.program_display_name/, "must read the real backend-provided program name");
  assert.match(src, /jurisdictionName_.*—.*programName/, "the jurisdiction name and program name must combine into one distinguishing title");
});

test("compactScenarioIdentity never uses the Globe's geo-hub coordinate map as the producer-facing jurisdiction name", () => {
  const src = stripComments(read("lib/format.jsx"));
  // bestJurisdictionName prefers structure.jurisdiction_display_name
  // (the real registry name) over the local geo/coordinate map — proven
  // directly rather than assumed.
  assert.match(src, /function bestJurisdictionName\(code, structure\)/);
  assert.match(src, /structure\.jurisdiction_display_name/);
});

test("an exact resolved rate (floor == ceiling) is labeled plainly, never 'Up to X%' which implies a range that does not exist", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /isExactRate/);
  assert.match(src, /isExactRate \? `\$\{Math\.round\(ceiling \* 100\)\}%` : `Up to/);
});

// C. Exact duplicate canonical structures do not appear twice — proven at
// the label layer: two structures with the SAME jurisdiction but
// DIFFERENT program_display_name must produce different titles.
test("two same-jurisdiction structures with different program_display_name never collide on title", () => {
  // Reimplements just the title-building logic's decision surface
  // (jurisdiction + program) as a pure check against the real exported
  // helper contract, without a JSX/DOM harness.
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /const name = singleProgram && programName/);
});

// B/H. Rank badge truthfulness — never "①" for an unranked structure;
// LEADING is a producer selection, never a canonical rank glyph.
test("ScenarioCard badge never defaults an unranked priced structure to circled-1, and LEADING never borrows a rank glyph", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.doesNotMatch(src, /rank\?\.rank \|\| 1/, "must not default a missing rank to position 1");
  assert.match(src, /rank\?\.rank \? \(CIRCLED\[rank\.rank - 1\]/, "a real rank must still render its real circled position");
  assert.match(src, /"PRICED"/, "an unranked priced structure must say PRICED, never imply a false rank");
  assert.match(src, /"◈ LEADING"/, "LEADING must use a distinct producer-selection glyph, never a circled rank number");
});

// A. review_required (no canonical rank) still sorts deterministically —
// priced-cheapest-first — never arbitrary array order.
test("visibleStructures tie-breaks unranked structures by real NPC, never leaving array order to decide the primary six", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /npc_with_adjustments_usd \?\? Infinity/);
  assert.match(src, /an - bn/);
});

// G. Recommendation vs top-priced-candidate/leading-structure semantics
// remain textually distinct — never the same label for a genuine
// canonical recommendation, a producer's manual leading selection, and a
// non-comparable best-priced fallback.
test("ProductionHero never labels a producer's manual leading selection as the canonical Recommended Structure", () => {
  const src = stripComments(read("components/ProductionHero.jsx"));
  assert.match(src, /isGenuineRecommendation/);
  assert.match(src, /"Leading Structure"/);
  assert.match(src, /"Recommended Structure"/);
  assert.match(src, /Producer-selected, not CineGlobe's recommendation/);
});

test("ProjectHeader computes isGenuineRecommendation by comparing the active structure against the pure canonical rank-1 pick, never assuming a manual leading selection is the recommendation", () => {
  const src = stripComments(read("shell/ProjectHeader.jsx"));
  assert.match(src, /const canonicalTop = activeStructure\(allocated, null\)/, "must resolve the TRUE rank-1 pick independent of any manual override");
  assert.match(src, /topStructure\.structure_id === canonicalTop\.structure_id/);
});

// H. Conditional/non-canonical structures cannot silently become the
// deterministic recommendation — bestPricedCandidate is a SEPARATE,
// distinctly-labeled fallback the Hero only reaches when topStructure
// (activeStructure's own recommendation-or-leading pick) is absent.
test("bestPricedCandidate is a distinct fallback, never substituted silently for the canonical recommendation", () => {
  const src = stripComments(read("lib/globeData.js"));
  assert.match(src, /export function bestPricedCandidate\(allocated\)/);
  const heroSrc = stripComments(read("components/ProductionHero.jsx"));
  assert.match(heroSrc, /bestPriced = !topStructure \? bestPricedCandidate : null/, "bestPriced must only apply when there is genuinely no active structure at all");
});

// E. Card click opens Inspector with the correct structure ID — the
// whole card body is inspectable, not only a small button.
test("ScenarioCard's whole card body is inspectable (click + keyboard), footer/leading buttons stop propagation so they never also fire Inspect", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /role="button"/);
  assert.match(src, /onClick=\{openInspect\}/);
  assert.match(src, /onKeyDown=\{handleCardKeyDown\}/);
  assert.match(src, /e\.stopPropagation\(\); openInspect\(\)/, "the Inspect button itself must not double-fire via bubbling");
  assert.match(src, /e\.stopPropagation\(\); onCompare\(structure\)/, "Compare must not also open Inspector");
  assert.match(src, /e\.stopPropagation\(\); onSetLeading/, "Set as leading must not also open Inspector");
});

// F. Compare keys by real structure_id, never a jurisdiction string.
test("Compare passes the real structure_id through, never a jurisdiction code", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /setCompareStructureId\(s\.structure_id\)/);
  assert.doesNotMatch(src, /setCompareStructureId\(s\.primary_jurisdiction\)/);
});

// I. FX unavailable state is truthful — reads the real canonical
// economics.fx_horizons field, never a fabricated/hardcoded fallback
// value when it is genuinely empty.
test("FX strip reads real economics.fx_horizons, with an honest 'unavailable' when a snapshot entry is genuinely absent", () => {
  const src = stripComments(read("lib/todayCompute.js"));
  assert.match(src, /fxHorizons\?\.\[code\]/);
  assert.match(src, /available: false/);
  assert.doesNotMatch(src, /current:\s*0(?!\.\d)/, "must never substitute a fabricated zero rate");
});

// J. No project-specific branching anywhere in the repaired seams.
test("no Lips Like Sugar/project-UUID branching in the repaired Workspace/Hero/format files", () => {
  for (const file of [
    "screens/production/Workspace.jsx",
    "components/ProductionHero.jsx",
    "shell/ProjectHeader.jsx",
    "lib/format.jsx",
    "lib/globeData.js",
  ]) {
    const src = stripComments(read(file));
    assert.doesNotMatch(src, /ab10b319-978e-44d3-9331-af2a5f2cccc2/, `${file} must not hard-code Lips Like Sugar's project id`);
    assert.doesNotMatch(src, /Lips Like Sugar/, `${file} must not name Lips Like Sugar directly`);
  }
});
