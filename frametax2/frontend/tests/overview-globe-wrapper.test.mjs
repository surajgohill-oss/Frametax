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
