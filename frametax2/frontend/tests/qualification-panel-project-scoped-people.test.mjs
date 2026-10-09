import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

test("Workspace Inputs people saves go to the viewed project, never the singleton demo engine", () => {
  const panel = read("components/QualificationPanel.jsx");
  assert.match(panel, /if \(projectId\) \{\s*await postProjectPeople\(projectId,/);
  assert.match(panel, /else \{\s*await postPeople\(/, "legacy write only without a project");
  assert.match(read("screens/production/Workspace.jsx"), /<QualificationPanel [^>]*projectId=\{projectId\}/);
});
