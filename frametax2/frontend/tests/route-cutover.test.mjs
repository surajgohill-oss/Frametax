// ── Legacy /production/* route cutover — regression protection ──────────
//
// Run with: npm test (node --test, same convention as globe-invariants.test.mjs)
//
// WHY THESE EXIST. The generic project Workspace (ccb24eb) existed but the
// normal product navigation — sidebar, Today dashboard, Company Globe,
// Project Record's primary CTA — still pointed at the old, Little-Utopia-
// only /production/* UI. A user following ordinary navigation never saw the
// new Workspace. This batch closed every one of those entry points. These
// assertions are source-level (no browser/DOM harness in this project,
// same limitation globe-invariants.test.mjs documents) — they lock in the
// STRUCTURE of the fix (no literal "/production/..." navigate targets left
// in normal-navigation files, one wildcard redirect route, project_id
// resolved rather than hard-coded) so a future edit can't silently
// reintroduce a legacy navigate() call. They cannot replace the live
// browser walkthrough recorded in docs/validation/PROJECT_WORKSPACE_ROUTE_CUTOVER.md.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

// Same comment-stripping helper as globe-invariants.test.mjs — this file's
// own header comment above legitimately mentions "/production/" as prose,
// so literal-string assertions below must not be fooled by it.
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("App.jsx routes /production/* through one wildcard redirect, not eight legacy pages", () => {
  const src = stripComments(read("App.jsx"));
  assert.match(src, /path="\/production\/\*"/, "wildcard /production/* route must exist");
  assert.match(src, /LegacyProductionRedirect/, "wildcard route must render the redirect component");
  // The eight individual legacy routes must be gone — each would have been
  // a literal path="/production/<segment>" (not the wildcard).
  for (const segment of ["overview", "workspace", "scenarios", "globe", "reports", "binder", "knowledge", "record", "settings"]) {
    assert.doesNotMatch(
      src,
      new RegExp(`path="\\/production\\/${segment}"`),
      `no individual /production/${segment} route should remain`,
    );
  }
});

test("LegacyProductionRedirect resolves project_id from the API, never hard-codes Little Utopia's UUID", () => {
  const src = stripComments(read("shell/LegacyProductionRedirect.jsx"));
  assert.match(src, /getProduction/, "must resolve the active production via the existing API call");
  assert.match(src, /production\.project_id/, "must read project_id from the resolved response");
  assert.match(src, /\/projects\/\$\{.*\}\/workspace/, "must redirect into the generic project Workspace route");
  // Guard against ever hard-coding Little Utopia's real UUID directly in
  // this file — the whole point is that the redirect target is resolved,
  // not fixed, so it keeps working if the served production ever changes.
  assert.doesNotMatch(src, /fa5cade5-0669-4816-bfe6-72146f8d3bae/, "must not hard-code Little Utopia's project_id");
});

test("Sidebar's Productions row navigates by project_id, not a literal legacy path", () => {
  const src = stripComments(read("shell/Sidebar.jsx"));
  assert.match(src, /\/projects\/\$\{production\.project_id\}\/workspace/, "Productions row must target the generic Workspace");
});

test("CompanyGlobe's three navigation points target the generic Workspace", () => {
  const src = stripComments(read("screens/company/CompanyGlobe.jsx"));
  const matches = src.match(/\/projects\/\$\{production\.project_id\}\/workspace/g) || [];
  assert.ok(matches.length >= 3, `expected >=3 generic Workspace navigations in CompanyGlobe.jsx, found ${matches.length}`);
  assert.doesNotMatch(src, /navigate\("\/production\/overview"\)/, "no literal legacy navigate target should remain");
});

test("Today.jsx's production slate route and question link target the generic Workspace", () => {
  const src = stripComments(read("screens/company/Today.jsx"));
  assert.match(src, /route:\s*`\/projects\/\$\{production\.project_id\}\/workspace`/, "slate row route must be project-driven");
  assert.match(src, /navigate\(`\/projects\/\$\{production\.project_id\}\/workspace`\)/, "'View all questions' must target the generic Workspace");
  assert.doesNotMatch(src, /route:\s*"\/production\/overview"/, "no literal legacy slate route should remain");
  assert.doesNotMatch(src, /navigate\("\/production\/workspace"\)/, "no literal legacy questions link should remain");
});

test("ProjectRecord's served-production primary action opens the generic Workspace, not legacy /production/overview", () => {
  const src = stripComments(read("screens/company/ProjectRecord.jsx"));
  assert.doesNotMatch(src, /navigate\("\/production\/overview"\)/, "'Open Production' must no longer target the legacy route");
  // Both the served (Little Utopia) and non-served (FVD) paths reach the
  // SAME generic route pattern — no separate literal per project identity.
  const workspaceNavCount = (src.match(/navigate\(`\/projects\/\$\{project\.id\}\/workspace`\)/g) || []).length;
  assert.ok(workspaceNavCount >= 1, "must navigate into /projects/{id}/workspace at least once");
});
