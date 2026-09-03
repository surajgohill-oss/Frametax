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
// Workspace Display Regression closeout: the PRIOR fix (above) correctly
// established that same-jurisdiction structures must stay distinguishable,
// but did so by concatenating the FULL legal program_display_name into the
// primary card TITLE — exactly the verbosity regression the current
// closeout fixes. program_display_name itself is still read (never
// discarded from the served data) but the title is jurisdiction-only now;
// disambiguation moves to a compact, generically-derived secondary label.
test("compactScenarioIdentity still reads the real backend program_display_name, but never concatenates it into the primary title", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /structure\.program_display_name/, "must still read the real backend-provided program name — never discarded");
  assert.doesNotMatch(src, /const name = .*—.*programName/, "the primary title must never concatenate the program name onto the jurisdiction");
  assert.match(src, /const name = jurisdictionName_;/, "the primary title must be the jurisdiction alone");
});

test("a compact secondary program label is generically derived, never a per-program hardcoded string", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /function compactProgramLabel\(programName, jurisdictionName\)/, "must be a real function, not an inline literal map");
  // Two purely mechanical transforms only — no jurisdiction/program name
  // literal appears in the function body itself.
  assert.match(src, /startsWith\(`\$\{jurisdictionName\.toLowerCase\(\)\} `\)/, "must strip a leading jurisdiction-name prefix generically");
  assert.match(src, /replace\(\/\\s\*\\\(\[\^\)\]\*\\\)\\s\*\$\/, ""\)/, "must strip a trailing parenthetical clarifier generically");
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
// the SECONDARY label layer now (Workspace Display Regression closeout
// moved disambiguation off the primary title): two structures with the
// SAME jurisdiction but DIFFERENT program_display_name still produce
// different secondary labels/subtitles, they simply share a title.
test("two same-jurisdiction structures with different program_display_name still get distinct secondary labels", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /const compactLabel = singleProgram \? compactProgramLabel\(programName, jurisdictionName_\) : stackLabel;/);
  assert.match(src, /return \{ flags, name, subtitle, programLabel: compactLabel \};/, "programLabel must be exposed for callers that need disambiguation without the rate (e.g. a dropdown)");
});

// A/D. Workspace Display Regression: the card headline is jurisdiction-
// only; a multi-program stack (no single program name to compact) still
// gets a real, generically-derived distinguishing label by joining each
// claimed program's own compact form — never falling back to a bare,
// indistinguishable jurisdiction name when real program_display_names
// data exists to disambiguate it.
test("a multi-program stack derives its secondary label from program_display_names, never a bare indistinguishable jurisdiction name", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /structure\.program_display_names/, "must read the real backend-served array of every claimed program's name");
  assert.match(src, /const stackLabel = !singleProgram && \(structure\.program_display_names \|\| \[\]\)\.length > 1/);
  assert.match(src, /\.map\(\(n\) => compactProgramLabel\(n, jurisdictionName_\) \|\| n\)/, "each stacked program must go through the SAME compaction rule as the single-program case — no second vocabulary");
});

// B. Subnational title omits the redundant parent-country prefix — Section
// 3's rule: a composite registry name ("Australia — New South Wales")
// must render as its most specific segment alone ("New South Wales"),
// never the full "Country — Subnational" string as the card headline.
test("bestJurisdictionName's composite country-subnational form is trimmed to its most specific segment for the card title", () => {
  const src = stripComments(read("lib/format.jsx"));
  assert.match(src, /const parts = full\.split\(" — "\);/, "must split the composite registry name on its own real delimiter");
  assert.match(src, /return parts\[parts\.length - 1\];/, "must keep only the most specific (last) real segment — never a frontend-invented short name");
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
  // Hard Restore Frozen Project Globe: bestPricedCandidate was extracted
  // out of lib/globeData.js (now restored byte-exact to the July 30 freeze,
  // which predates this function) into its own small module — a current-
  // data compatibility adapter, not a behavior change. Same function, same
  // callers, different file.
  const src = stripComments(read("lib/bestPricedCandidate.js"));
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

// ── Workspace/FX Display Regression closeout ─────────────────────────────
//
// The fourth, dynamic FX slot fell back to a bogus, unresolved "—" cell
// whenever activeStructure(allocated, leadingStructureId) had no manual
// selection AND no canonical rank-1 (comparable_count: 0 — a real, common
// Lips Like Sugar state), even though a real Top Priced candidate (and
// its real, resolvable currency) existed the whole time. See
// CAPABILITY_LEDGER.md, "Workspace Display Regression Closeout" for the
// live browser walkthrough.

// E/G. Leading drives the dynamic slot when it resolves to a real
// structure — the SAME activeStructure() every other Workspace element
// (anchor lane, "Set as leading" toggle) already reads, never a second
// "who is leading" computation.
// CineGlobe Overview FX Strip + Vertical Scrolling closeout: the dynamic
// slot's structure resolution stays in Workspace.jsx (it needs
// leadingStructure/allocated, which are screen-local), but the
// LEADING/TOP PRICED label derivation moved into the shared
// components/FXStrip.jsx (Overview needs the identical derivation and
// must not carry a second copy of it).
test("the dynamic FX slot is driven by activeStructure (Leading) when it resolves, labeled LEADING", () => {
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /const dynamicFxStructure = leadingStructure \|\| bestPricedCandidate\(allocated\);/);
  assert.match(src, /const dynamicFxIsLeading = !!leadingStructure;/);
  const fxStripSrc = stripComments(read("components/FXStrip.jsx"));
  assert.match(fxStripSrc, /const dynamicLabel = structureIsLeading \? "LEADING" : \(structure \? "TOP PRICED" : null\);/);
});

// H. No Leading exists but a Top Priced candidate does — the SAME real
// economics ProjectHeader's own Hero already uses for its own "Top Priced
// Candidate" state (globeData.bestPricedCandidate), never a second,
// divergent "best" computation invented for the FX rail alone.
test("bestPricedCandidate (imported from the same module the Hero uses) drives the slot when no Leading exists", () => {
  // Hard Restore Frozen Project Globe: bestPricedCandidate now lives in its
  // own module (lib/bestPricedCandidate.js), not lib/globeData.js (restored
  // byte-exact to the July 30 freeze) — same function, same single source
  // every caller shares, different file.
  const src = stripComments(read("screens/production/Workspace.jsx"));
  assert.match(src, /import \{ buildGlobeView, structureTier, activeStructure \} from "\.\.\/\.\.\/lib\/globeData";/);
  assert.match(src, /import \{ bestPricedCandidate \} from "\.\.\/\.\.\/lib\/bestPricedCandidate";/);
});

// I. Neither a Leading selection nor a Top Priced candidate exists — the
// slot must not render at all, never a fabricated "—"/"USD / —" block.
// buildLeaderFxItems now lives in lib/todayCompute.js (CineGlobe Overview
// FX Strip + Vertical Scrolling closeout extracted it out of Workspace.jsx
// so Workspace and Overview share the one implementation).
test("buildLeaderFxItems returns nothing (no bogus dash block) when no structure is passed at all", () => {
  const src = stripComments(read("lib/todayCompute.js"));
  assert.match(src, /export function buildLeaderFxItems\(economics, structure, label\) \{\s*\n\s*if \(!structure\) return \[\];/, "must short-circuit to an empty array, never the old { code: \"—\", ... } placeholder");
  assert.doesNotMatch(src, /code: "—"/, "the fabricated unresolved-dash placeholder must be removed entirely");
});

// F/Section 9. The currency chain is fully generic: jurisdiction -> ISO2
// -> economics.jurisdiction_currency (the SAME real canonical map served
// for the fixed EUR/CAD/GBP trio) -> currency code. A subnational
// jurisdiction code (e.g. "SA-RUH") is reduced to its ISO2 country prefix
// before lookup — the same mechanism already resolves Manitoba -> CAD,
// New South Wales -> AUD, etc. through the one shared jurisdiction_currency
// map, never a per-subnational duplicate entry.
test("dynamic FX currency resolution is generic (ISO2 + shared jurisdiction_currency map), never a hardcoded per-country table", () => {
  const src = stripComments(read("lib/todayCompute.js"));
  assert.match(src, /const iso2 = jurisdiction\.split\("-"\)\[0\]\.toUpperCase\(\);/);
  assert.match(src, /const code = jurisdictionCurrency\[iso2\] \|\| iso2;/);
  assert.match(src, /const jurisdictionCurrency = economics\?\.jurisdiction_currency \|\| \{\};/, "must read the SAME real economics.jurisdiction_currency map the fixed trio uses, not a second one");
});

// J. Section 10/no hardcoded SAR: a currency the provider genuinely
// lacks renders its own real code plus a truthful unavailable state —
// never a fabricated rate, and no jurisdiction/currency is special-cased
// by name anywhere in this file.
test("a resolved currency with no snapshot entry renders its own code plus a truthful 'rate unavailable', never a fabricated rate", () => {
  const fxStripSrc = stripComments(read("components/FXStrip.jsx"));
  assert.match(fxStripSrc, /rate unavailable/);
  const computeSrc = stripComments(read("lib/todayCompute.js"));
  assert.doesNotMatch(fxStripSrc, /SAR|Saudi/, "no jurisdiction/currency may be special-cased by name in the FX strip component");
  assert.doesNotMatch(computeSrc, /SAR|Saudi/, "no jurisdiction/currency may be special-cased by name in the FX compute module");
});

test("the LEADING/TOP PRICED tag is self-contained on the resolved dynamic slot, never a detached label over an unresolved cell", () => {
  const src = stripComments(read("components/FXStrip.jsx"));
  assert.match(src, /it\.isLeader && it\.leaderLabel && <span className="wsx-fx-tag">\{it\.leaderLabel === "LEADING" \? "Leading" : "Top Priced"\}<\/span>/);
});
