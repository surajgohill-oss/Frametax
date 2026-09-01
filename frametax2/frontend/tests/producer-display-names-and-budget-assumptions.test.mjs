// ── Producer Display Names + Budget Rail User Assumptions closeout ────────
//
// A. Inspector jurisdiction code resolves to human-readable name.
// B. Program slug resolves to human-readable program label.
// C. No producer-facing raw CA-MB/US-MT-style title where a canonical name
//    already exists (source-scan across every reachable Inspector surface).
// D/E/F. Finance cost saves, survives refetch, and participates in the
//    canonical evaluation fingerprint — covered on the backend in
//    test_financing_cost_assumption.py (this file has no DOM harness to
//    exercise the fetch/refetch cycle itself; it proves the wiring is
//    present and correctly shaped).
// G. Editable adjustment controls cannot be local-only.
// I. No project-title/UUID conditionals introduced.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

// ── A/B/C: Inspector display-name contract ─────────────────────────────

test("Inspector.jsx: AllocationAssignmentInspector's 'Routed to' resolves through jurisdictionName, not the raw jurisdiction_code", () => {
  const src = stripComments(read("shell/Inspector.jsx"));
  assert.doesNotMatch(
    src,
    /<dt>Routed to<\/dt><dd className="mono">\{data\.jurisdiction_code\}<\/dd>/,
    "must not render the raw jurisdiction_code (e.g. US-MT) verbatim",
  );
  assert.match(src, /<dt>Routed to<\/dt><dd>\{jurisdictionName\(data\.jurisdiction_code\)\}<\/dd>/);
});

test("Inspector.jsx: JurisdictionInspector's title resolves through jurisdictionName, not the raw code", () => {
  const src = stripComments(read("shell/Inspector.jsx"));
  assert.doesNotMatch(src, /<h3>\{data\.code\}<\/h3>/, "must not render the raw code (e.g. CA-ON) verbatim as the Inspector title");
  assert.match(src, /<h3>\{jurisdictionName\(data\.code\)\}<\/h3>/);
});

test("Inspector.jsx: AccountInspector's cross-reference rows resolve through jurisdictionName", () => {
  const src = stripComments(read("shell/Inspector.jsx"));
  assert.doesNotMatch(src, /\{c\.jurisdictionCode\}\s*\n\s*\{c\.claimsIncentive/, "cross-ref row-sub must not render the raw code");
  assert.match(src, /\{jurisdictionName\(c\.jurisdictionCode\)\}/);
});

test("Inspector.jsx: AllocationSegmentInspector (the reachable click-through Inspector) already uses jurisdictionName/programDisplay for its title/subtitle", () => {
  const src = stripComments(read("shell/Inspector.jsx"));
  assert.match(src, /<h3>\{jurisdictionName\(data\.jurisdiction_code\)\}<\/h3>/);
  assert.match(src, /\{programDisplay\(data\.program_slug\)\}/);
});

test("Inspector.jsx imports jurisdictionName/programDisplay from the one canonical format module — no second jurisdiction/program name map", () => {
  const src = stripComments(read("shell/Inspector.jsx"));
  assert.match(src, /import \{[^}]*jurisdictionName[^}]*\} from "\.\.\/lib\/format";/);
  assert.match(src, /import \{[^}]*programDisplay[^}]*\} from "\.\.\/lib\/format";/);
  // No local jurisdiction-code -> name object literal anywhere in this file.
  assert.doesNotMatch(src, /const\s+\w*JUR\w*\s*=\s*\{/i);
});

test("BudgetRail.jsx's account cross-reference (Jurisdiction allocation) resolves through jurisdictionName, not the raw code", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  assert.doesNotMatch(src, /<dd className="mono">\{alloc\.jurisdictionCode\}<\/dd>/);
  assert.match(src, /import \{ Money, jurisdictionName \} from "\.\.\/lib\/format";/);
  assert.match(src, /jurisdictionName\(alloc\.jurisdictionCode\)/);
});

test("CompanyGlobe.jsx and Settings.jsx sidebar panels resolve baseline jurisdiction through jurisdictionName", () => {
  for (const path of ["screens/company/CompanyGlobe.jsx", "screens/production/Settings.jsx"]) {
    const src = stripComments(read(path));
    assert.doesNotMatch(src, /<dd>\{production\.jurisdiction_code\}<\/dd>/, `${path} must not render the raw jurisdiction_code`);
    assert.match(src, /jurisdictionName\(production\.jurisdiction_code\)/, `${path} must resolve through jurisdictionName`);
  }
});

// ── G: no local-only editable economic inputs remain ──────────────────

test("BudgetRail.jsx: the old local-only Adjustments preview (Reinvestment/In-kind/Manual labor/Manual override inputs) is gone", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  assert.doesNotMatch(src, /Adjustments \(preview — not yet saved\)/);
  assert.doesNotMatch(src, /AdjustmentsPreview/);
  assert.doesNotMatch(src, /local preview only/);
  assert.doesNotMatch(src, /ADJUSTMENT_ROWS/);
});

test("BudgetRail.jsx: every remaining input in the active adjustment form saves through postProjectAssumptions — none are local-state-only", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  // Exactly the two producer-settable assumptions this closeout wires:
  // contingency (pre-existing) and financing cost (new). Both call the
  // same generic persistence path.
  const calls = src.match(/postProjectAssumptions\(projectId, \{[^}]*\}\)/g) || [];
  assert.equal(calls.length, 2, "expected exactly two postProjectAssumptions call sites (contingency, financing cost)");
  assert.ok(calls.some((c) => c.includes("contingency_expected_utilization_pct")));
  assert.ok(calls.some((c) => c.includes("financing_cost_usd")));
});

test("BudgetRail.jsx: In-kind is rendered read-only (no input element) since accepting it as QPE is a qualification-doctrine decision, out of this task's scope", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  const fn = /function InkindDisclosure[\s\S]*?\n}/.exec(src);
  assert.ok(fn, "InkindDisclosure not found");
  assert.doesNotMatch(fn[0], /<input/);
});

// ── Finance Costs: saves, is real, persisted, fingerprint-covered ─────

test("BudgetRail.jsx: FinanceCostLine reads its current value from the real persisted fact, never local-only default state", () => {
  const src = stripComments(read("components/BudgetRail.jsx"));
  const fn = /function FinanceCostLine[\s\S]*?\n\}\n\nexport default/.exec(src);
  assert.ok(fn, "FinanceCostLine not found");
  assert.match(fn[0], /postProjectAssumptions\(projectId, \{ financing_cost_usd: value \}\)/);
  assert.match(fn[0], /onSaved\?\.\(\)/, "must call onSaved (refetch) after a successful save, never rely on local state alone");
});

test("Overview.jsx reads financingCostUsd from facts.answers, the same real persisted-fact pattern contingencyPct already uses — not local component state", () => {
  const src = stripComments(read("screens/production/Overview.jsx"));
  assert.match(src, /const financingCostUsdRaw = facts\?\.answers\?\.financing_cost_usd;/);
  assert.match(src, /financingCostUsd=\{financingCostUsd\}/);
  assert.match(src, /onFinanceCostSaved=\{refetch\}/);
});

// ── I: generic, no project-title/UUID conditionals ─────────────────────

test("BudgetRail.jsx and Inspector.jsx introduce no project-id/title conditional branching", () => {
  for (const path of ["components/BudgetRail.jsx", "shell/Inspector.jsx"]) {
    const src = stripComments(read(path));
    assert.doesNotMatch(src, /Little Utopia|Lips Like Sugar|Bad Hombres|fa5cade5|ab10b319|4355ae88/i, `${path} must contain no per-project branch`);
  }
});
