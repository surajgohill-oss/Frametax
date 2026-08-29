// ── Production Overview Truthfulness ─────────────────────────────────────
//
// Run with: npm test (node --test, same source-level convention as
// route-cutover.test.mjs / served-production-lifecycle.test.mjs — no DOM
// harness in this project).
//
// WHY THESE EXIST. The mature Overview was silently NOT consuming real
// facts/artwork/economics already available or derivable for a production:
// (A) every project's Hero/Today thumbnail fell back to Little Utopia's own
// real photograph whenever the project had no artwork of its own, instead
// of a neutral treatment; (B) the Production Facts edit control saved
// through the legacy singleton /people endpoint, which resolves a
// DIFFERENT project's data (or none) for any project besides whichever one
// the demo engine happens to be pointed at. See
// docs/architecture/CAPABILITY_LEDGER.md, "Production Overview
// Truthfulness" for the live browser walkthrough these assertions cannot
// replace.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

// A. Project A cannot receive Project B artwork.
test("ProductionHero: a project without its own artwork never falls back to another project's real photograph", () => {
  const src = stripComments(read("components/ProductionHero.jsx"));
  // The generic fallback (showNeutralFallback) must render a plain neutral
  // element, never an <img> pointed at heroArt (Little Utopia's own file),
  // except inside the explicit, documented isLittleUtopia branch.
  assert.match(src, /showNeutralFallback[\s\S]{0,200}ph-hero-art-neutral/, "a project with no artwork must render the neutral fallback element");
  assert.match(src, /const heroSrc = isLittleUtopia \? heroArt : artworkUrl/, "heroArt must be scoped strictly to the Little Utopia branch, never a generic fallback");
});

test("Today.jsx: the Production Slate thumbnail is per-project, never Little Utopia's photo for every row", () => {
  const src = stripComments(read("screens/company/Today.jsx"));
  assert.doesNotMatch(src, /<img className="tdx-art" src=\{heroArt\}/, "no row may render heroArt unconditionally");
  assert.match(src, /<SlateArt projectId=\{p\.id\}\s*\/>/, "each row must render its own per-project artwork component");
  assert.match(src, /isLittleUtopia \? heroArt : `\$\{API_ORIGIN\}\/api\/v1\/projects\/\$\{projectId\}\/artwork`/, "SlateArt must fetch per-project artwork, falling back only for Little Utopia specifically");
});

// B. Served production facts render from canonical project/person facts.
test("Overview.jsx reads people from the canonical per-project state, not a hardcoded/company-level source", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.match(src, /const \{ production, pkg, people, economics \} = data/, "Overview must destructure people from the canonical per-project payload");
  assert.match(src, /<ProductionDetails[\s\S]{0,150}people=\{people\}/, "ProductionDetails must be rendered with the real canonical people object");
});

// C. Source-derived writer survives refresh/API roundtrip if recovered —
// proven at the persistence-seam level: the extractor is a pure function
// (already covered end-to-end by the backend test), and the frontend
// panel always displays whatever the canonical `people` prop carries,
// never a client-cached/derived value of its own.
test("ProductionDetails never invents a name — displayed value always traces to people[bucket] or the override store", () => {
  const src = stripComments(read("components/ProductionDetails.jsx"));
  assert.match(src, /const currentOf = \(role\) => \{/, "current value must be derived from the people/overrides props, not local state");
  assert.doesNotMatch(src, /"Jane Doe"|"Anthony Tambakis"|"Brantley Gutierrez"/, "no hardcoded person name anywhere in the panel");
});

// D. Unknown facts remain unknown rather than fabricated.
test("ProductionDetails renders 'Not yet named' for an empty role, never a placeholder identity", () => {
  const src = stripComments(read("components/ProductionDetails.jsx"));
  assert.match(src, /placeholder="Not yet named"/);
  assert.match(src, /cur\.name \|\| <span className="text-tertiary">Not yet named<\/span>/);
});

// E. Hero recommendation/NPC semantics use canonical eligible state.
test("ProductionHero: NPC/Recommended Structure are gated on topStructure (the same canonical eligible-ranked structure), never candidate #1 merely because candidates exist", () => {
  const src = stripComments(read("components/ProductionHero.jsx"));
  assert.match(src, /topStructure \? <Money value=\{topStructure\.npc_with_adjustments_usd\} \/> : "—"/, "NPC must come from topStructure or render truthful absence");
  assert.match(src, /No directly comparable scenario yet/, "absence must be captioned truthfully, not left ambiguous");
});
test("globeData.activeStructure only returns a structure eligible by rank #1 or the shared leading selection, never an arbitrary candidate", () => {
  const src = stripComments(read("lib/globeData.js"));
  assert.match(src, /allocated\.ranking\.find\(\(r\) => r\.rank === 1\)/, "fallback must key off the canonical rank, not array order");
});

// F. Questions Remaining uses its actual canonical definition.
test("ProjectHeader's openQuestions reads pkg.missing_inputs (the field the backend now populates), not a hardcoded/empty source", () => {
  const src = stripComments(read("shell/ProjectHeader.jsx"));
  assert.match(src, /data\?\.pkg\?\.missing_inputs\?\.length/, "openQuestions must read pkg.missing_inputs");
});

// G. Editability: the project-scoped write path exists and is used whenever
// a real project is being viewed.
test("ProductionDetails saves through the project-scoped endpoint when a projectId is available", () => {
  const src = stripComments(read("components/ProductionDetails.jsx"));
  assert.match(src, /if \(projectId\) await postProjectPeople\(projectId, answers\)/, "a project-scoped save must be used whenever projectId is known");
  assert.match(src, /else await postPeople\(answers\)/, "the legacy singleton save remains only as the no-projectId fallback");
});
test("api.js exposes a project-scoped people write, distinct from the legacy singleton one", () => {
  const src = stripComments(read("api.js"));
  assert.match(src, /export const postProjectPeople = \(projectId, answers\) =>\s*\n\s*request\(`\/projects\/\$\{projectId\}\/people`/);
});
