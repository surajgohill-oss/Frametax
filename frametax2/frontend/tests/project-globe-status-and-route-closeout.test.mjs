// Project Globe design + interaction closeout (2026-10-08): colour = jurisdiction STATUS, structure type = topology.
// Pure logic: category mapping, selected-structure routes (relocation / hybrid / multiparty) and whole-polygon picking.
import test from "node:test";
import assert from "node:assert/strict";
import { SINGLE_JURISDICTION_CATEGORY_SEMANTIC, OPTIMIZER_SEMANTIC, buildSelectedStructureRoute } from "../src/lib/globeData.js";
import { structureArcs, structureRouteLabels, structureTopology, participantGlobeKeys, NEUTRAL_ROUTE_HEX, FAMILY } from "../src/lib/globeStructure.js";
import { buildPolygonIndex, pickIsoAt, resolvePolygonTarget } from "../src/lib/globePicking.js";

test("category mapping: each served category has its own status colour; Needs Facts is amber and never 'Conditional'", () => {
  const S = SINGLE_JURISDICTION_CATEGORY_SEMANTIC;
  assert.deepEqual(Object.fromEntries(Object.entries(S).map(([k, v]) => [k, v.slot])), {
    LEADING_ALTERNATIVE: "gold", STRONG_ALTERNATIVE: "jade", REFERENCE_ALTERNATIVE: "silver", CONDITIONAL_ALTERNATIVE: "amber",
    NOT_SUITABLE_FOR_THIS_PRODUCTION: "rose", UNAVAILABLE: "red", PROGRAM_DATA_INCOMPLETE: "slate",
  });
  assert.equal(S.CONDITIONAL_ALTERNATIVE.label, "Needs facts");
  assert.equal(new Set(Object.values(S).map((v) => v.hex)).size, 7, "seven statuses, seven distinct colours");
  for (const v of Object.values(S)) assert.doesNotMatch(v.label, /conditional/i);
  assert.equal(OPTIMIZER_SEMANTIC.amber.label, "Needs Facts");
});

const comp = (component, jurisdiction_code, allocated_usd = 1000) => ({ component, jurisdiction_code, allocated_usd, program_slug: "p" });
const single = { structure_id: "s", classification: "SINGLE_JURISDICTION", participants: ["ES"], primary_jurisdiction: "ES", component_allocations: [] };
const hybrid = { structure_id: "h", classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "IT", "GB"], primary_jurisdiction: "MU",
  component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "IT"), comp("music_package", "GB")] };
const copro = { structure_id: "c", classification: "OFFICIAL_COPRODUCTION", treaty_slug: "t", participants: ["GB", "CA", "IE"], primary_jurisdiction: "GB",
  coproduction_partners: [{ jurisdiction_code: "GB" }, { jurisdiction_code: "CA" }, { jurisdiction_code: "IE" }], component_allocations: [] };

test("single jurisdiction: highlight only; a relocation draws current location -> destination", () => {
  assert.deepEqual(structureArcs(single), []);
  assert.deepEqual(structureArcs(single, { homeCode: "ES" }), [], "the current base itself is not a relocation");
  const reloc = structureArcs(single, { homeCode: "GB" });
  assert.equal(reloc.length, 1);
  assert.deepEqual([reloc[0].startCode, reloc[0].endCode, reloc[0].kind], ["GB", "ES", "relocation"]);
});

test("hybrid and multiparty: every participant is connected; component legs carry concise labels", () => {
  const arcs = structureArcs(hybrid);
  assert.deepEqual(arcs.map((a) => [a.startCode, a.endCode]), [["MU", "IT"], ["MU", "GB"]]);
  assert.deepEqual(structureRouteLabels(hybrid).map((l) => l.text), ["POST/VFX", "MUSIC"]);
  assert.deepEqual(participantGlobeKeys(hybrid).sort(), ["GB", "IT", "MU"]);
  const peers = structureArcs(copro);
  assert.equal(peers.length, 2, "every co-production participant is connected to the principal");
  assert.ok(peers.every((a) => a.solid === true && a.startCode === "GB"), "peer relationships are solid and undirected");
  assert.equal(structureTopology(copro).family, FAMILY.COPRO);
});

test("selected-structure route takes the principal's STATUS colour; switching structures replaces the route outright", () => {
  const allocated = {
    structures: [hybrid, copro],
    jurisdiction_accounting: { single_jurisdiction_contract: [{ jurisdiction_code: "MU", category: "STRONG_ALTERNATIVE" }, { jurisdiction_code: "GB", category: "LEADING_ALTERNATIVE" }] },
  };
  const a = buildSelectedStructureRoute(allocated, hybrid);
  const b = buildSelectedStructureRoute(allocated, copro);
  assert.equal(a.color, SINGLE_JURISDICTION_CATEGORY_SEMANTIC.STRONG_ALTERNATIVE.hex);
  assert.equal(b.color, SINGLE_JURISDICTION_CATEGORY_SEMANTIC.LEADING_ALTERNATIVE.hex);
  assert.deepEqual(a.arcs[0].color, [a.color, a.color]);
  assert.notDeepEqual(a.arcs.map((x) => x.endCode), b.arcs.map((x) => x.endCode));
  assert.deepEqual(buildSelectedStructureRoute(allocated, null), { arcs: [], labels: [] });
  assert.notEqual(NEUTRAL_ROUTE_HEX, a.color);
});

// Dense region: a small state sits inside a big country; the pointer must resolve the polygon under it, not the nearest marker.
const sq = (id, x0, y0, x1, y1) => ({ id, geometry: { type: "Polygon", coordinates: [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]] } });
test("polygon picking: the smallest containing polygon wins and the marker position is irrelevant", () => {
  const index = buildPolygonIndex([sq("US", 0, 0, 40, 40), sq("US-NM", 10, 10, 14, 14), sq("US-TX", 20, 10, 30, 20)], (f) => f.id);
  assert.equal(pickIsoAt(index, 12, 12), "US-NM");
  assert.equal(pickIsoAt(index, 25, 25), "US", "outside the states the country polygon answers");
  assert.equal(pickIsoAt(index, 50, 50), null);
  const pointByIso = new Map([["US-NM", { iso: "US-NM" }], ["US-TX", { iso: "US-TX" }]]);
  // the pointer is inside Texas yet right next to New Mexico's marker position: the polygon under it decides
  assert.equal(resolvePolygonTarget(index, 15, 20.5, pointByIso).iso, "US-TX");
  assert.equal(resolvePolygonTarget(index, 30, 5, pointByIso), null, "a country-only polygon with no represented record yields no hover");
});
