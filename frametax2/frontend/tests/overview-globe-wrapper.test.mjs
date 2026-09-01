// ── Overview Globe Wrapper / Below-Globe Regression ────────────────────────
//
// WHY THESE EXIST. Overview.jsx passed obscuredRightPx={inspector ? 400 : 0}
// into the embedded Globe3D — a constant copied from the full Project Globe
// page, where the canvas spans nearly the full viewport width and its right
// edge genuinely sits under the fixed-position 400px Inspector panel. On
// Overview the Globe lives in the CENTER of a 3-column grid (340px | 1fr |
// 340px); the Inspector covers the RIGHT column (Budget Rail) and the
// viewport margin beyond it, never this narrower center-column canvas.
// Passing 400 anyway shrank Globe3D's internal visibleW (canvasWidth -
// obscuredRightPx) from ~550px down to ~150px the instant the Inspector
// opened, producing a drastically zoomed-out, tiny sphere. See
// docs/architecture/CAPABILITY_LEDGER.md and the live browser walkthrough
// this assertion cannot replace.
//
// This is a WRAPPER-only fix — Globe3D.jsx/globeData.js/globeFit.js/
// globeVisualFixture.js (the frozen Phase 3B engine) are untouched.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("Overview's embedded Globe never reframes for an Inspector overlay that doesn't cover its own canvas", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.doesNotMatch(
    src,
    /obscuredRightPx=\{inspector \? 400 : 0\}/,
    "the full-Project-Globe-page reframe constant (400px) must never be copied onto Overview's narrower center-column embed",
  );
  assert.match(
    src,
    /obscuredRightPx=\{0\}/,
    "Overview's Globe must pass a fixed 0 — the Inspector's fixed-right 400px panel never reaches this column's canvas",
  );
});

test("Overview.jsx does not modify the frozen Phase 3B Globe engine", () => {
  // Source-presence check only (this repo's test suite has no DOM harness):
  // confirms Overview still imports the shared engine component rather than
  // a fork, and that this file makes no camera/border/altitude edits of its
  // own — those concerns live exclusively in Globe3D.jsx/globeFit.js.
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.match(src, /import Globe3D from "\.\.\/\.\.\/components\/Globe3D";/);
  assert.doesNotMatch(src, /THREE\.|OrbitControls|fitCameraDistance|altitudeJitter/, "Overview must never reimplement engine-owned camera/border logic");
});

test("Overview's below-Globe section still renders the confirmed-current, later-approved IncentiveIntelligence grid, not the superseded 4-across strip", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.match(src, /import IncentiveIntelligence from "\.\.\/\.\.\/components\/IncentiveIntelligence";/);
  assert.match(src, /<IncentiveIntelligence\s/);
  // The old strip this component replaced (ec283e5) is gone from the tree;
  // guard against it being reintroduced under a different import path.
  assert.doesNotMatch(src, /jurisdiction-snapshot-strip|JurisdictionSnapshotStrip/i);
});

// ── Overview Globe Hover Data Parity ────────────────────────────────────
//
// WHY THIS EXISTS. Overview.jsx rendered its own truncated inline hover
// tooltip (jurisdiction / statusLabel / role only) instead of the approved
// Phase 3B hover contract (Program / Maximum Incentive / Modeled Incentive /
// NPC / Incentive-per-Gross-Budget) that ProjectGlobe.jsx already renders
// via GlobeHoverCard. GlobeHoverCard was extracted, byte-identical, into its
// own component file so BOTH screens consume ONE canonical hover-data
// contract — no second, drifted implementation in Overview.jsx.

test("Overview no longer renders the old truncated jurisdictionName/statusLabel/role-only tooltip", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.doesNotMatch(
    src,
    /hover\.statusLabel/,
    "the old local tooltip's statusLabel field must be gone — that shape never carried program/rate/NPC",
  );
  assert.doesNotMatch(
    src,
    /<div className="globe-tooltip">\s*<strong>\{hover\.jurisdictionName\}<\/strong>/,
    "Overview must not hand-roll its own hover markup — it renders GlobeHoverCard like ProjectGlobe.jsx does",
  );
});

test("Overview renders the same canonical GlobeHoverCard component ProjectGlobe.jsx uses", () => {
  const overviewSrc = stripComments(read("screens/production/Overview.jsx"));
  const projectGlobeSrc = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(overviewSrc, /import GlobeHoverCard from "\.\.\/\.\.\/components\/GlobeHoverCard";/);
  assert.match(overviewSrc, /<GlobeHoverCard hover=\{hover\} hoverRect=\{hoverRect\} canvasRef=\{canvasRef\} \/>/);
  assert.match(projectGlobeSrc, /import GlobeHoverCard from "\.\.\/\.\.\/components\/GlobeHoverCard";/);
  assert.match(projectGlobeSrc, /<GlobeHoverCard hover=\{hover\} hoverRect=\{hoverRect\} canvasRef=\{canvasRef\} \/>/);
});

test("Overview passes the two-argument (pt, rect) hover handler Globe3D calls, not a truncated single-argument setHover", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.doesNotMatch(src, /onPointHover=\{setHover\}/, "a bare setHover discards Globe3D's rect argument, which GlobeHoverCard needs to position itself");
  assert.match(src, /onPointHover=\{\(pt, rect\) => \{ setHover\(pt\); setHoverRect\(pt \? rect : null\); \}\}/);
});

test("Overview passes grossBudgetUsd into buildGlobeView, matching ProjectGlobe.jsx, so the hover card's Incentive/Gross-Budget figure isn't silently blank on Overview", () => {
  const overviewSrc = stripComments(read("screens/production/Overview.jsx"));
  const projectGlobeSrc = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(overviewSrc, /grossBudgetUsd: data\?\.production\?\.gross_budget_usd \?\? null,/);
  assert.match(projectGlobeSrc, /grossBudgetUsd: data\?\.production\?\.gross_budget_usd \?\? null,/);
});

test("GlobeHoverCard is a single extracted module, not duplicated economic-derivation logic in Overview.jsx", () => {
  const overviewSrc = stripComments(read("screens/production/Overview.jsx"));
  // The rich hover body components/format helpers must live only in
  // GlobeHoverCard.jsx — Overview.jsx must never re-derive them itself.
  assert.doesNotMatch(overviewSrc, /RecommendedOrAlternativeBody|CoProductionBody|ExcludedBody|formatFullUsd|incentivePctOfGross/);
  const hoverCardSrc = stripComments(read("components/GlobeHoverCard.jsx"));
  assert.match(hoverCardSrc, /export default function GlobeHoverCard/);
  assert.match(hoverCardSrc, /Program/);
  assert.match(hoverCardSrc, /Maximum Incentive/);
  assert.match(hoverCardSrc, /Modeled Incentive/);
  assert.match(hoverCardSrc, /NPC/);
  assert.match(hoverCardSrc, /Incentive \/ Gross Budget/);
});
