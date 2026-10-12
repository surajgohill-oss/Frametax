import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { libraryStageLabel, libraryStageKey, libraryFilterMatches } from "../src/lib/libraryStatus.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const evalMeta = { key: "evaluation", label: "Evaluation" };

test("Evaluation-stage projects read Evaluation only with a complete current canonical generation", () => {
  assert.equal(libraryStageLabel({ is_served_production: true }, evalMeta), "Evaluation");
  assert.equal(libraryStageLabel({ is_served_production: false }, evalMeta), "Submitted");
  assert.equal(libraryStageLabel({}, evalMeta), "Submitted");
});

test("other lifecycle stages keep their own label; the status is never title/id based", () => {
  assert.equal(libraryStageLabel({ is_served_production: false }, { key: "production", label: "Production" }), "Production");
  const src = readFileSync(join(SRC, "lib", "libraryStatus.js"), "utf8");
  assert.doesNotMatch(src, /title|\bid\b|Little Utopia|Valentine|Bad Hombres|Lips Like Sugar/i.source ? /Little Utopia|Valentine|Bad Hombres|Lips Like Sugar/ : /x/);
});

test("the Library only lists projects: no evaluation call on load", () => {
  const lib = readFileSync(join(SRC, "screens", "company", "ProjectLibrary.jsx"), "utf8");
  assert.doesNotMatch(lib, /evaluat(e|ion)\/begin|postEvaluat|beginEvaluation|\/state/);
  assert.match(lib, /libraryStageLabel\(p, meta\)/);
});

test("All Active excludes Submitted and Archived; Submitted and All filter as specified", () => {
  const evaluated = { lifecycle: "EVALUATION", is_served_production: true };
  const submitted = { lifecycle: "EVALUATION", is_served_production: false };
  const later = { lifecycle: "PRODUCTION", is_served_production: false };
  const archived = { lifecycle: "ARCHIVED" };
  assert.equal(libraryStageKey(submitted), "submitted");
  assert.deepEqual([evaluated, submitted, later, archived].map((p) => libraryFilterMatches("active", p)), [true, false, true, false]);
  assert.deepEqual([evaluated, submitted, later, archived].map((p) => libraryFilterMatches("submitted", p)), [false, true, false, false]);
  assert.ok([evaluated, submitted, later, archived].every((p) => libraryFilterMatches("all", p)));
  assert.equal(libraryFilterMatches("evaluation", submitted), false);
  assert.equal(libraryFilterMatches("evaluation", evaluated), true);
});

test("a retained but stale generation keeps the project visible and labelled stale; never evaluated stays Submitted", () => {
  const stale = { lifecycle: "EVALUATION", is_served_production: false, evaluation_freshness: "STALE", evaluation_stale_reason: "ENGINE_VERSION" };
  const never = { lifecycle: "EVALUATION", is_served_production: false, evaluation_freshness: "NONE" };
  assert.equal(libraryStageKey(stale), "evaluation");
  assert.equal(libraryStageLabel(stale, evalMeta), "Evaluation · economics stale");
  assert.equal(libraryStageLabel(never, evalMeta), "Submitted");
  assert.equal(libraryFilterMatches("active", stale), true);
  assert.equal(libraryFilterMatches("submitted", stale), false);
  assert.equal(libraryFilterMatches("active", never), false);
});

test("retained evaluation history controls the Record actions, the Library navigation and the Overview label; opening never evaluates", () => {
  const record = readFileSync(join(SRC, "screens", "company", "ProjectRecord.jsx"), "utf8");
  assert.match(record, /Open Results →/);
  assert.match(record, /Recalculate/);
  assert.match(record, /window\.confirm\(/, "recalculating is explicit and confirmed");
  // Begin Evaluation is only the genuinely unevaluated branch: it follows the stale branch
  assert.ok(record.indexOf("isStale ?") < record.indexOf("Begin Evaluation"));
  const lib = readFileSync(join(SRC, "screens", "company", "ProjectLibrary.jsx"), "utf8");
  assert.match(lib, /isEvaluated\(p\) \? `\/projects\/\$\{p\.id\}\/overview`/);
  const overview = readFileSync(join(SRC, "screens", "production", "Overview.jsx"), "utf8");
  assert.match(overview, /evaluation_freshness === "STALE"/);
  assert.doesNotMatch(lib, /beginEvaluation|runEvaluation/);
});

test("bounded optimizer lists: the hook merges further pages read only and the Workspace offers them", () => {
  const hook = readFileSync(join(SRC, "lib", "useCineGlobe.js"), "utf8");
  assert.match(hook, /getOptimizerListPage\(projectId, kind, cursor\)/);
  assert.match(hook, /!have\.has\(e\.structure_id\)/, "pages merge without duplicating an entry");
  const api = readFileSync(join(SRC, "api.js"), "utf8");
  assert.match(api, /request2\(`\$\{PROJECTS_BASE\}\/\$\{projectId\}\/evaluation\/optimizer-list\?kind=/, "the route lives under /api/v1/projects, not /cineglobe");
  const ws = readFileSync(join(SRC, "screens", "production", "Workspace.jsx"), "utf8");
  assert.match(ws, /Load more options/);
  assert.match(hook, /suppressed: "optimizer_scenarios_music_suppressed"/, "the policy-suppressed list pages through the same hook");
  const uni = readFileSync(join(SRC, "components", "JurisdictionUniverse.jsx"), "utf8");
  assert.match(uni, /optimizer_scenarios_music_suppressed_page/);
  assert.match(uni, /loadMore\("suppressed"\)/);
  const insp = readFileSync(join(SRC, "shell", "Inspector.jsx"), "utf8");
  assert.match(insp, /getJurisdictionWinner\(projectId, ref\.code\)/, "the omitted segment trace is read on demand");
  assert.match(insp, /function WinnerDetailSections/);
  assert.match(insp, /data-testid="winner-conditional-programs"/);
  assert.match(insp, /data-winner-trace-open/);
  assert.match(readFileSync(join(SRC, "lib", "globeData.js"), "utf8"), /detail_ref: structure\.detail_ref \?\? undefined/);
  assert.match(readFileSync(join(SRC, "api.js"), "utf8"), /request2\(`\$\{PROJECTS_BASE\}\/\$\{projectId\}\/evaluation\/jurisdiction-winner\//);
});
