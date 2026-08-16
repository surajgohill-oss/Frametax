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
  // Mature UI restoration: redirects into the restored mature Overview
  // (project_id-driven), not the earlier phase's stripped-down Workspace.
  assert.match(src, /\/projects\/\$\{.*\}\/overview/, "must redirect into the restored mature Overview route");
  // Guard against ever hard-coding Little Utopia's real UUID directly in
  // this file — the whole point is that the redirect target is resolved,
  // not fixed, so it keeps working if the served production ever changes.
  assert.doesNotMatch(src, /fa5cade5-0669-4816-bfe6-72146f8d3bae/, "must not hard-code Little Utopia's project_id");
});

test("Overview UI contract: Sidebar carries no individual project/production rows — Project Library is the one project selector", () => {
  const src = stripComments(read("shell/Sidebar.jsx"));
  assert.doesNotMatch(src, /getProjects\(/, "Sidebar must not fetch or list individual projects");
  assert.doesNotMatch(src, /cg-prodrow/, "the per-project row markup must be gone, not just hidden");
  assert.match(src, /Project Library/, "Project Library must remain the company-nav project selector");
});

test("CompanyGlobe's three navigation points target the restored mature UI", () => {
  const src = stripComments(read("screens/company/CompanyGlobe.jsx"));
  const matches = src.match(/\/projects\/\$\{production\.project_id\}\/overview/g) || [];
  assert.ok(matches.length >= 3, `expected >=3 mature-UI navigations in CompanyGlobe.jsx, found ${matches.length}`);
  assert.doesNotMatch(src, /navigate\("\/production\/overview"\)/, "no literal legacy navigate target should remain");
});

test("Today.jsx's production slate route and question link target the restored mature UI", () => {
  const src = stripComments(read("screens/company/Today.jsx"));
  assert.match(src, /route:\s*`\/projects\/\$\{production\.project_id\}\/overview`/, "slate row route must be project-driven");
  assert.match(src, /navigate\(`\/projects\/\$\{production\.project_id\}\/overview`\)/, "'View all questions' must target the restored mature UI");
  assert.doesNotMatch(src, /route:\s*"\/production\/overview"/, "no literal legacy slate route should remain");
  assert.doesNotMatch(src, /navigate\("\/production\/workspace"\)/, "no literal legacy questions link should remain");
});

test("ProjectRecord's served-production primary action opens the restored mature UI, not legacy /production/overview", () => {
  const src = stripComments(read("screens/company/ProjectRecord.jsx"));
  assert.doesNotMatch(src, /navigate\("\/production\/overview"\)/, "'Open Production' must no longer target the legacy route");
  // Both the served (Little Utopia) and non-served (FVD) paths reach the
  // SAME generic route pattern — no separate literal per project identity.
  const overviewNavCount = (src.match(/navigate\(`\/projects\/\$\{project\.id\}\/overview`\)/g) || []).length;
  assert.ok(overviewNavCount >= 1, "must navigate into /projects/{id}/overview at least once");
});

test("Overview UI contract: Project Library card click routes by the project's own leading_structure_id, never a hard-coded project", () => {
  const src = stripComments(read("screens/company/ProjectLibrary.jsx"));
  assert.match(src, /p\.leading_structure_id\s*\?\s*`\/projects\/\$\{p\.id\}\/overview`/, "a project with a mature Overview must be opened directly");
  assert.match(src, /`\/company\/library\/\$\{p\.id\}`/, "a not-yet-evaluated project must keep the existing Project Record flow");
  assert.doesNotMatch(src, /fa5cade5-0669-4816-bfe6-72146f8d3bae/, "must not hard-code Little Utopia's project_id");
});
