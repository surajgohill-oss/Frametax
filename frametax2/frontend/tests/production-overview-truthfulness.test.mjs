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
  assert.match(src, /const \{ production, pkg, people, economics, facts \} = data/, "Overview must destructure people from the canonical per-project payload");
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

// E. Hero recommendation/NPC semantics — SUPERSEDED (Consolidated UI/
// ingestion/permission closeout, 2026-09-03, Batch 1): the Hero no
// longer renders any per-structure recommendation/NPC at all. That
// eligible-ranked-state gating (topStructure vs a genuine rank-1 pick)
// still lives in ProjectHeader.jsx (isGenuineRecommendation) and drives
// Overview's own BudgetRail/Top Structures cards — see
// production-overview-truthfulness.test.mjs's BudgetRail test below and
// workspace-top6-truthfulness.test.mjs's ProjectHeader test.
test("ProductionHero renders no per-structure recommendation/NPC — Hero is budget-only", () => {
  const src = stripComments(read("components/ProductionHero.jsx"));
  assert.doesNotMatch(src, /topStructure/, "Hero must not read topStructure at all");
  assert.doesNotMatch(src, /npc_with_adjustments_usd/, "Hero must not render any per-structure NPC");
  assert.doesNotMatch(src, /Top Priced Candidate/);
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

// ── Bad Hombres Overview Truthfulness / Generic Ingestion Propagation ──────
//
// The Production Budget card (BudgetRail) fell back to a bare "—" for
// Credit/NPC whenever activeStructure() found neither a producer-selected
// Leading structure nor a canonical rank-1 (a real, common state:
// comparable_count:0 when a production's own base jurisdiction is
// unpriceable) — even while the Hero, right above it, already showed a
// real Modeled Net Cost for a real Top Priced candidate. Two surfaces on
// the SAME page silently describing different economic bases. See
// CAPABILITY_LEDGER.md, "Bad Hombres Overview Truthfulness" for the live
// browser walkthrough.

test("Overview's Budget card falls back to bestPricedCandidate (the SAME function the Hero uses) when no active structure exists", () => {
  // Hard Restore Frozen Project Globe: bestPricedCandidate now lives in its
  // own module (lib/bestPricedCandidate.js), not lib/globeData.js (restored
  // byte-exact to the July 30 freeze) — same function, same single source
  // every caller shares, different file.
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.match(src, /import \{ buildGlobeView, activeStructure \} from "\.\.\/\.\.\/lib\/globeData";/);
  assert.match(src, /import \{ bestPricedCandidate \} from "\.\.\/\.\.\/lib\/bestPricedCandidate";/);
  assert.match(src, /const structure = allocated \? \(activeStructure\(allocated, leadingStructureId\) \|\| bestPricedCandidate\(allocated\)\) : null;/);
});

test("BudgetRail is self-labeled (Leading/Top Priced) so it can never be read as silently contradicting the Hero", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  assert.match(src, /const stateLabel = !structure \? null : \(structureIsLeading \? "Leading" : "Top Priced"\);/);
  assert.doesNotMatch(src, /Bad Hombres|4355ae88|ab10b319|Lips Like Sugar/i, "the fix must be generic, never a per-project branch");
});
