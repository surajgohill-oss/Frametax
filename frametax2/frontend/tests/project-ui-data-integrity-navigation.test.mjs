// ── PROJECT_UI_DATA_INTEGRITY, Phase 3 whitelist item 5 ───────────────────
// Project navigation test — every project-scoped page's back link must
// return to the Project Library, never Today, keeping its existing
// appearance (same "← " button style/position, only label + destination
// changed).

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

test("ProductionHero's back button reads Project Library, never Today", () => {
  const src = read("components/ProductionHero.jsx");
  assert.match(src, /ph-back ph-hero-back.*← Project Library/);
  assert.doesNotMatch(src, /← Today/);
});

test("ProjectHeader routes the shared back button to the Project Library, never Today", () => {
  const src = read("shell/ProjectHeader.jsx");
  assert.match(src, /navigate\("\/company\/library"\)/);
  assert.doesNotMatch(src, /navigate\("\/company\/today"\)/);
});
