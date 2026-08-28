// ── Production Record served-state UI — Inspector/Sidebar Closeout Phase 1 ──
//
// Run with: npm test (node --test, same source-level convention as
// route-cutover.test.mjs — no DOM harness in this project).
//
// WHY THESE EXIST. A successfully evaluated production (real canonical
// structures/results already persisted) was still gated behind a stale
// "Go to Workspace"-shaped lifecycle transition on the Project Library card
// click, because that click routed on `leading_structure_id` — a narrower
// field that can legitimately stay unset for a mature, fully-served
// production (its baseline was simply never repointed as "leading") — not
// on the canonical served-state signal (`is_served_production`,
// `structure_count > 0`) ProjectRecord's own CTA already used correctly.
// These assertions lock in: (1) the canonical signal is what routes and
// gates, not the narrower one; (2) an evaluated production's Production
// Record exposes its evaluated-production action directly, without
// "Go to Workspace" framing; (3) an unevaluated production still gets its
// Evaluate action; (4) none of this is keyed to any specific project
// identity. See docs/architecture/CAPABILITY_LEDGER.md, "Production Record
// Served-State UI" for the live browser walkthrough these assertions cannot
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

test("UNEVALUATED: the Evaluate/Begin Evaluation action remains available and is not conditioned on served state alone", () => {
  const src = stripComments(read("screens/company/ProjectRecord.jsx"));
  assert.match(src, /runEvaluation/, "runEvaluation action must exist");
  assert.match(
    src,
    /analysis\.evaluation_begun\s*\?\s*"Re-run Evaluation"\s*:\s*"Begin Evaluation"/,
    "an unevaluated (or re-evaluatable) production must still expose Evaluate/Re-run Evaluation",
  );
});

test("EVALUATED: the legacy 'Go to Workspace' lifecycle gate is absent from the served-production CTA", () => {
  const src = stripComments(read("screens/company/ProjectRecord.jsx"));
  assert.doesNotMatch(src, /Go to Workspace/, "no 'Go to Workspace' wording anywhere in the Production Record");
  // Scoped to the isServedProduction primary-CTA branch specifically — a
  // SEPARATE, genuinely different state (evaluation began but zero
  // structures persisted yet) legitimately keeps its own "Enter Workspace"
  // wording untouched; only the served-production gate is the defect
  // (Section 11: do not blindly rename every use of "Workspace").
  const servedBranch = src.match(/isServedProduction \? \(([\s\S]*?)\) : \(/);
  assert.ok(servedBranch, "must find the isServedProduction primary-CTA branch");
  assert.doesNotMatch(servedBranch[1], /Enter Workspace/, "the served-production primary CTA must not read 'Enter Workspace'");
  assert.match(servedBranch[1], /Open Production/, "the served-production primary CTA opens the production directly");
});

test("EVALUATED: canonical production navigation/results are reachable directly from the served state, using the existing route", () => {
  const src = stripComments(read("screens/company/ProjectRecord.jsx"));
  assert.match(src, /const isServedProduction = project\.is_served_production/, "served state must be read from the canonical is_served_production field");
  // Served branch must still navigate into the existing, unmodified
  // canonical Overview route — no new module invented.
  assert.match(
    src,
    /isServedProduction \? \(\s*[\s\S]{0,300}?navigate\(`\/projects\/\$\{project\.id\}\/overview`\)/,
    "served state must open the existing canonical Overview route directly",
  );
  // Documents tab must expose the real Binder navigation once served.
  assert.match(src, /isServedProduction && \(\s*<p className="rec-note">/, "served state must expose full document management directly");
});

test("GENERIC: Project Library routing derives from canonical served state, never leading_structure_id or a project identity check", () => {
  const src = stripComments(read("screens/company/ProjectLibrary.jsx"));
  assert.match(src, /p\.is_served_production \? `\/projects\/\$\{p\.id\}\/overview`/, "routing must key off is_served_production");
  assert.doesNotMatch(src, /leading_structure_id/, "leading_structure_id must not gate Library routing (too narrow — can be unset on a mature, served production)");
  assert.doesNotMatch(src, /p\.title\s*===/, "no title-based branching");
  // No UUID literal anywhere in the routing file.
  assert.doesNotMatch(src, /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i, "no hard-coded project UUID");
});

test("GENERIC: the Project Record's served-state read is the same field name the Library grid now consumes", () => {
  const recordSrc = stripComments(read("screens/company/ProjectRecord.jsx"));
  const librarySrc = stripComments(read("screens/company/ProjectLibrary.jsx"));
  assert.match(recordSrc, /project\.is_served_production/, "ProjectRecord must read is_served_production");
  assert.match(librarySrc, /p\.is_served_production/, "ProjectLibrary must read the same is_served_production field");
});
