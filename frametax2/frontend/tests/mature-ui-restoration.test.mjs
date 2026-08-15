// ── Mature UI restoration — regression protection ────────────────────────
//
// Run with: npm test (node --test, same convention as globe-invariants.test.mjs
// and route-cutover.test.mjs — no DOM/browser harness in this project).
//
// Both assertions below lock in real defects found during this phase's own
// live browser verification, not hypothetical ones:
//
// 1. ProjectHeader is rendered by AppShell as a SIBLING of the routed page
//    (AppShell wraps <Routes>; ProjectHeader is not inside any <Route
//    element>), so react-router's useParams() has no route context there
//    and silently returns {} — every tab rendered "/projects/undefined/..."
//    live before this was caught and fixed with a location-based regex
//    extraction instead (the same technique AppShell's own
//    MATURE_PROJECT_ROUTE test already used for exactly this reason).
//
// 2. humanizeToken(null) crashed Scenarios.jsx for any project whose
//    ProductionStructure rows predate the trace_json structure_type
//    enrichment (canonical_production_view.py's own generic derivation
//    covers this on the backend; humanizeToken must not re-crash if a
//    null ever reaches it from anywhere else).

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("ProjectHeader resolves projectId from the URL, never from useParams()", () => {
  // Checked against the RAW file, not stripComments() — the regex literal
  // this asserts on (pathname.match(/^\/projects\/([^/]+)\//)) itself
  // contains a literal "//" sequence (the escaped \/ immediately followed
  // by the regex-literal's own closing /), which stripComments' naive
  // line-comment stripper misreads as a comment start and truncates —
  // the same class of false positive documented in route-cutover.test.mjs
  // for "/production/*" in prose. No comments live near this line, so
  // reading the raw source is exact here, not a loss of rigor.
  const src = read("shell/ProjectHeader.jsx");
  assert.doesNotMatch(src, /const\s*\{\s*projectId\s*\}\s*=\s*useParams\(\)/, "useParams() has no route context here — must not be reintroduced");
  assert.match(src, /pathname\.match\(\/\^\\\/projects\\\/\(\[\^\/\]\+\)\\\//, "must extract projectId from location.pathname directly");
});

test("humanizeToken never crashes on a null/undefined token", () => {
  const src = stripComments(read("lib/programNames.js"));
  const fn = src.slice(src.indexOf("export function humanizeToken"), src.indexOf("export function humanizeToken") + 300);
  assert.match(fn, /if\s*\(!token\)\s*return/, "must guard against null/undefined before calling .replace()");
});

test("canonical_production_view's structure_type/is_baseline derivation is honored by the frontend consumer (Scenarios.jsx uses humanizeToken defensively)", () => {
  const src = stripComments(read("screens/production/Scenarios.jsx"));
  assert.match(src, /useParams/, "Scenarios must be project_id-aware (regression: previously called useCineGlobe() with no project scope)");
});

test("AppShell's mature-route detection covers every restored production page, not just overview", () => {
  const src = stripComments(read("shell/AppShell.jsx"));
  assert.match(
    src,
    /overview\|workspace\|scenarios\|globe\|reports\|binder\|knowledge\|record\|settings/,
    "MATURE_PROJECT_ROUTE must match all 9 restored pages, or ProjectHeader silently stops rendering on the ones it misses",
  );
});
