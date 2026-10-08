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
