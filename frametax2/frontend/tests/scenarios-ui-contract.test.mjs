// ── Scenarios UI contract — regression protection ────────────────────────
//
// Run with: npm test (node --test, same convention as route-cutover.test.mjs)
//
// Source-level checks (no DOM/browser harness in this project, same
// limitation documented elsewhere) that Scenarios.jsx reuses the SAME
// classification helper Overview's Production Options cards use (never a
// second taxonomy), and that comparable structures are never mixed with
// review/unavailable ones in the same swappable column set.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("Scenarios reuses Overview's classification helper — never a second taxonomy", () => {
  const src = stripComments(read("screens/production/Scenarios.jsx"));
  assert.match(src, /from\s+["']\.\.\/\.\.\/lib\/productionOptions["']/, "must import classifyStructure/isBaselineStructure from the shared helper");
  assert.match(src, /classifyStructure\(/, "must classify each scenario using the shared helper");
});

test("Scenarios never labels a plain multi-jurisdiction split a co-production", () => {
  const src = stripComments(read("screens/production/Scenarios.jsx"));
  assert.doesNotMatch(src, /co-production/i, "no literal 'co-production' wording — classification labels come from productionOptions.js only");
});

test("Scenarios keeps comparable and review/unavailable structures in separate groups, never mixed into the same swappable columns", () => {
  const src = stripComments(read("screens/production/Scenarios.jsx"));
  assert.match(src, /comparableOrdered/, "must derive a comparable-only ordering");
  assert.match(src, /reviewOrdered/, "must derive a separate review/unavailable ordering");
  // The overflow swap-selector must be built from comparableOrdered/overflow,
  // never from the raw combined structures list.
  assert.doesNotMatch(src, /allocated\.structures\]\s*\.sort/, "must not fall back to sorting the raw combined structures list for the main table");
});

test("Scenarios shows a Vs. current/base comparison row using the shared baseline detector", () => {
  const src = stripComments(read("screens/production/Scenarios.jsx"));
  assert.match(src, /isBaselineStructure/, "must use the shared baseline detector, not a local is_baseline check");
  assert.match(src, /Vs\.\s*current\s*\/\s*base/, "must label the delta row consistently with Overview");
});
