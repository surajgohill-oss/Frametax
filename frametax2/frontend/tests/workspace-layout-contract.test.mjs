// ── WORKSPACE_VISUAL_REGRESSION_CORRECTION (2026-09-22) ───────────────────
// Layout contract regression guard — the Phase 1 investigation confirmed
// zero CSS changes between the pre-scenario-mode-wiring commit (dc0fc46)
// and the current implementation (`git diff dc0fc46 HEAD --
// screens.css` is empty): the six-card rack's grid, card dimensions, and
// wrap-to-second-row behavior were never touched. This test pins that
// contract going forward so a FUTURE change can't silently reintroduce
// a real layout regression without a visible test failure.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const STYLES = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "styles");
const read = (p) => readFileSync(join(STYLES, p), "utf8");

test("the six-card rack grid keeps its established 3-column, fixed-width, wrap-to-next-row contract", () => {
  const css = read("screens.css");
  assert.match(
    css,
    /\.wsx-rack \{ display: grid; grid-template-columns: repeat\(3, minmax\(310px, 320px\)\); justify-content: start; gap: 18px; padding: 20px 10px 20px 18px; \}/,
    "the rack must stay a fixed 3-column grid (310-320px cards) that wraps extra cards to a second row -- never a redesign to fewer/enlarged columns",
  );
});

test("the station container keeps its own scroll contract, never clipping wrapped rows", () => {
  const css = read("screens.css");
  assert.match(css, /\.wsx-station \{ overflow: auto;/, "the station must remain independently scrollable so wrapped rows (slots 4-6) stay reachable");
});
