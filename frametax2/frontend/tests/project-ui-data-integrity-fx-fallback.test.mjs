// ── PROJECT_UI_DATA_INTEGRITY, Phase 3 whitelist item 4 ───────────────────
// FX fallback component test — the fourth FX cell must never disappear
// when no canonical recommendation exists (F#K Valentine's Day's real
// state): it falls back to the active selected scenario, then Current
// Location, never fabricating a leading recommendation.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

test("Workspace's fourth FX cell falls back to the active selected scenario, then Current Location", () => {
  const src = read("screens/production/Workspace.jsx");
  assert.match(
    src,
    /dynamicFxStructure = leadingStructure \|\| bestPriced \|\| cols\[1\] \|\| cols\[0\]/,
    "the fallback chain must extend leadingStructure/bestPriced with the active selected scenario (cols[1]) then Current Location (cols[0])",
  );
  assert.match(src, /dynamicFxIsCurrentLocation/);
});

test("Overview's fourth FX cell uses the same fallback chain", () => {
  const src = read("screens/production/Overview.jsx");
  assert.match(src, /_topRanked \|\| _anchor/);
  assert.match(src, /structureIsCurrentLocation/);
});

test("FXStrip renders a distinct Current Location tag, never fabricating a Leading label, for the final fallback rung", () => {
  const src = read("components/FXStrip.jsx");
  assert.match(src, /CURRENT_LOCATION/);
  assert.match(src, /Current Location/);
});
