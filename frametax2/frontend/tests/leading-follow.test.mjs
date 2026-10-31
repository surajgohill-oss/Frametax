import test from "node:test";
import assert from "node:assert/strict";
import { followServedLeading } from "../src/lib/leadingFollow.js";

test("a re-evaluation's re-pointed selection is followed while the producer has not moved it", () => {
  assert.equal(followServedLeading({ prevServed: "old-id", current: "old-id", served: "new-id" }), "new-id");
});

test("a selection the producer changed, cleared or set in this visit is never overridden", () => {
  assert.equal(followServedLeading({ prevServed: "old-id", current: "chosen-by-producer", served: "new-id" }), null);
  assert.equal(followServedLeading({ prevServed: "old-id", current: null, served: "new-id" }), null);
});

test("nothing to follow when the served id is unchanged, absent, or this is the first sighting (seeding handles that)", () => {
  assert.equal(followServedLeading({ prevServed: "same", current: "same", served: "same" }), null);
  assert.equal(followServedLeading({ prevServed: "old-id", current: "old-id", served: null }), null);
  assert.equal(followServedLeading({ prevServed: undefined, current: null, served: "first" }), null);
});

test("AppState wires the follow rule into the single seeding callback and keeps the once-per-visit seed", async () => {
  const { readFileSync } = await import("node:fs");
  const src = readFileSync(new URL("../src/state/AppState.jsx", import.meta.url), "utf8");
  assert.match(src, /followServedLeading\(\{ prevServed, current: leadingRef\.current, served: persistedId \}\)/);
  assert.match(src, /servedLeadingRef\.current\[forProjectId\] = persistedId/);
  assert.match(src, /initializedLeadingForProject\.current = forProjectId;\n\s+if \(forProjectId === projectId\) setLeadingStructureIdRaw\(persistedId\)/);
});
