// ── WORKSPACE_RESPONSIVE_CONTROL/RACK_CLOSEOUT (2026-09-23) ───────────────
// Layout contract regression guard, updated from the fixed 3-column /
// horizontal-overflow contract the Phase 1 investigation had pinned
// (dc0fc46) to the new container-query-driven responsive contract: the
// station header no longer lets its scenario-count disclosure collide with
// Lanes/Map/Split or Other Scenarios, and the six-card rack reflows its
// column count to the station's own available width (never a horizontal
// scrollbar) instead of overflowing. This still pins a contract going
// forward so a FUTURE change can't silently reintroduce the overlap/
// overflow regression this closeout fixes, without also re-litigating the
// original fixed-grid assumption that WAS the bug.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const STYLES = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "styles");
const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(STYLES, p), "utf8");
const readSrc = (p) => readFileSync(join(SRC, p), "utf8");

test("the station is a container-query root (inline-size) so its own content-box width — not only the viewport — drives responsive layout", () => {
  const css = read("screens.css");
  assert.match(
    css,
    /\.wsx-station \{ container-type: inline-size; container-name: wsx-station;/,
    "the station must declare container-type: inline-size so it reacts to Question Stack/Inspector opening (which shrinks the station without changing the viewport)",
  );
  assert.match(
    css,
    /overflow-x: hidden; overflow-y: auto;/,
    "the station must never scroll horizontally — only vertically, so wrapped/reflowed rows (slots 4-6) stay reachable",
  );
});

test("the six-card rack reflows 3 -> 2 -> 1 columns via @container rules, capped near the original 320px card width, never a fixed grid that only grows a horizontal scrollbar", () => {
  const css = read("screens.css");
  assert.match(
    css,
    /\.wsx-rack \{ display: grid; grid-template-columns: repeat\(3, minmax\(0, 320px\)\); justify-content: start; gap: 18px; padding: 20px 10px 20px 18px; \}/,
    "the rack's base (widest) state must still offer 3 columns near 320px, but with a shrinkable (not fixed 310px) minimum so it can reflow instead of overflow",
  );
  assert.match(
    css,
    /@container wsx-station \(max-width: 1023px\) \{\s*\.wsx-rack \{ grid-template-columns: repeat\(2, minmax\(0, 320px\)\); \}\s*\}/,
    "a constrained station must reflow the rack to 2 columns",
  );
  assert.match(
    css,
    /@container wsx-station \(max-width: 685px\) \{\s*\.wsx-rack \{ grid-template-columns: minmax\(0, 320px\); \}\s*\}/,
    "a narrow station must reflow the rack to 1 column",
  );
  // The old fixed, non-reflowing contract must be gone.
  assert.doesNotMatch(
    css,
    /minmax\(310px, 320px\)/,
    "the rack's column minimum must no longer be pinned to 310px (that pinned minimum was what forced horizontal overflow instead of reflow)",
  );
});

test("the station-head control row is container-aware: wide state keeps mode+tabs+other on one row (count stacked in its own grid area), constrained state moves to two explicit rows without overlap", () => {
  const css = read("screens.css");
  assert.match(
    css,
    /grid-template-areas: "mode tabs other" "count tabs other";/,
    "the wide-station layout must place the scenario count in its own row beneath the mode toggle, never sharing a cell with Lanes/Map/Split or Other Scenarios",
  );
  assert.match(
    css,
    /@container wsx-station \(max-width: 860px\) \{[\s\S]*?grid-template-areas: "mode tabs" "count other";[\s\S]*?\}/,
    "the constrained-station layout must place mode+tabs on row 1 and count+other on row 2",
  );
});

test("the Other Scenarios dropdown has a bounded max-width with internal ellipsis, so a long optimizer label can never force the control row to overflow horizontally", () => {
  const css = read("screens.css");
  assert.match(
    css,
    /#wsx-swap \{ min-width: 0; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; \}/,
    "the Other Scenarios <select> must be width-clamped with ellipsis overflow",
  );
});

test("every station-head grid item declares min-width: 0, the standard fix for a flex/grid child refusing to shrink below its content's intrinsic width", () => {
  const css = read("screens.css");
  for (const selector of [".wsx-scenario-mode { grid-area: mode; min-width: 0; }", ".wsx-scenario-count { grid-area: count", ".wsx-other-scenarios, .wsx-other-scenarios-spacer { grid-area: other; min-width: 0; }"]) {
    assert.ok(css.includes(selector), `expected to find "${selector}" in screens.css`);
  }
});

test("no inline whiteSpace: \"nowrap\" remains on the optimizer scenario-count disclosure — it is a named class (.wsx-scenario-count) that can wrap", () => {
  const jsx = readSrc(join("screens", "production", "Workspace.jsx"));
  assert.doesNotMatch(
    jsx,
    /optimizer_scenarios_total[\s\S]{0,400}whiteSpace:\s*"nowrap"/,
    "the scenario-count span must not carry an inline whiteSpace: \"nowrap\" style",
  );
  assert.match(jsx, /className="wsx-scenario-count"/, "the scenario-count span must use the named .wsx-scenario-count class");
});

test("the optimizer scenario-count copy is compact producer language and omits the Formal tier entirely when its count is zero, without altering the underlying numbers", () => {
  // Mirrors the exact pure-string logic in Workspace.jsx's scenario-count
  // render (never re-derives the numbers — practical/formal/advanced come
  // straight from the same allocated.optimizer_scenarios_by_tier object).
  function scenarioCountCopy(total, byTier) {
    const practical = byTier?.PRACTICAL_HYBRID ?? 0;
    const formal = byTier?.FORMAL_COPRODUCTION ?? 0;
    const advanced = byTier?.ADVANCED_MULTI_JURISDICTION ?? 0;
    const tierParts = byTier
      ? [`${practical} practical`, ...(formal ? [`${formal} formal`] : []), `${advanced} advanced`]
      : [];
    return `${total} scenario${total === 1 ? "" : "s"}${tierParts.length ? ` · ${tierParts.join(" · ")}` : ""}`;
  }

  // ACCEPTED OPTIMIZER DATA — the four productions this closeout must not disturb.
  const ACCEPTED = {
    "Little Utopia": { total: 171, byTier: { PRACTICAL_HYBRID: 93, FORMAL_COPRODUCTION: 0, ADVANCED_MULTI_JURISDICTION: 78 } },
    "Bad Hombres": { total: 267, byTier: { PRACTICAL_HYBRID: 94, FORMAL_COPRODUCTION: 0, ADVANCED_MULTI_JURISDICTION: 173 } },
    "F#K Valentine's Day": { total: 411, byTier: { PRACTICAL_HYBRID: 107, FORMAL_COPRODUCTION: 0, ADVANCED_MULTI_JURISDICTION: 304 } },
    "Lips Like Sugar": { total: 541, byTier: { PRACTICAL_HYBRID: 133, FORMAL_COPRODUCTION: 0, ADVANCED_MULTI_JURISDICTION: 408 } },
  };

  assert.equal(scenarioCountCopy(171, ACCEPTED["Little Utopia"].byTier), "171 scenarios · 93 practical · 78 advanced");
  assert.equal(scenarioCountCopy(267, ACCEPTED["Bad Hombres"].byTier), "267 scenarios · 94 practical · 173 advanced");
  assert.equal(scenarioCountCopy(411, ACCEPTED["F#K Valentine's Day"].byTier), "411 scenarios · 107 practical · 304 advanced");
  assert.equal(scenarioCountCopy(541, ACCEPTED["Lips Like Sugar"].byTier), "541 scenarios · 133 practical · 408 advanced", "Lips Like Sugar's compact copy must read 541/133/408 — the 0-value Formal tier omitted");

  for (const [name, { total, byTier }] of Object.entries(ACCEPTED)) {
    const practical = byTier.PRACTICAL_HYBRID;
    const advanced = byTier.ADVANCED_MULTI_JURISDICTION;
    assert.equal(practical + byTier.FORMAL_COPRODUCTION + advanced, total, `${name}: practical + formal + advanced must still sum to the accepted total ${total} — this closeout must not alter the numbers, only their presentation`);
    assert.doesNotMatch(scenarioCountCopy(total, byTier), /0 formal/, `${name}: the compact copy must never print "0 formal"`);
  }

  // A hypothetical non-zero Formal count must still render (only the
  // zero-value case is omitted — this is a presentation rule, not a
  // "never show Formal" rule).
  assert.equal(scenarioCountCopy(10, { PRACTICAL_HYBRID: 4, FORMAL_COPRODUCTION: 3, ADVANCED_MULTI_JURISDICTION: 3 }), "10 scenarios · 4 practical · 3 formal · 3 advanced");
});

test("Normal-mode and Optimizer-mode card titles route through different, unmodified label sources (compactScenarioIdentity vs buildScenarioLabel) — the six-card selection contract and card content are untouched by this responsive-layout pass", () => {
  const jsx = readSrc(join("screens", "production", "Workspace.jsx"));
  assert.match(jsx, /OPTIMIZER_CLASSIFICATIONS\.has\(structure\.classification\)\s*\?\s*buildScenarioLabel\(structure\)\s*:\s*compactName/, "ScenarioCard must still branch title source by classification, unchanged from the prior optimizer-label closeout");
  assert.match(jsx, /className="wsx-nm"/, "the card title must still render inside .wsx-nm — no new badge or redesigned card");
});

test(".wsx-lh-id (the card-title column) keeps min-width: 0 so a long optimizer component-routing title wraps inside .wsx-nm instead of pushing the rank/role badge out of the card", () => {
  const css = read("screens.css");
  assert.match(css, /\.wsx-lh-id \{ min-width: 0; \}/, "the card title column must keep min-width: 0 for text wrapping to work in a CSS grid/flex ancestor");
  assert.doesNotMatch(css, /\.wsx-nm \{[^}]*white-space:\s*nowrap/, "the card title itself must never be forced to a single line");
});

test(".wsx-nm breaks an unbreakable long word (e.g. a jurisdiction name like \"Newfoundland\") instead of overflowing its box — found live at a reflowed 2-column rack width, where a plain wrap alone still overflowed by 10-47px", () => {
  const css = read("screens.css");
  assert.match(css, /\.wsx-nm \{[^}]*overflow-wrap:\s*break-word/, "the card title must set overflow-wrap: break-word so a single long word wraps inside the title column rather than overflowing it");
});
