// STRUCTURE-AWARE PROJECT GLOBE (2026-10-01): structural family, topology, routing, index order, grouping and
// selection identity. Live acceptance data contains two-party and multi-party hybrids, single/stack winners and
// needs-facts official co-production OPPORTUNITIES; the executable official-co-production and combined families
// have NO live instance, so they are verified with clearly-labelled focused fixtures below.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  FAMILY, FAMILY_META, NEUTRAL_ROUTE_HEX, buildStructureIndex, familyCounts, groupByFamily, identityOf, participantGlobeKeys,
  principalOf, structureArcs, structureStory, structureTopology, structuralFamilyOf,
} from "../src/lib/globeStructure.js";
import { optimizerProjection, selectSixSlots, MODE_OPTIMIZER } from "../src/lib/workspaceScenarioMode.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

// ── live-shape structures (exact fields the backend serves) ──────────────────────────────────────
const comp = (component, jurisdiction_code, allocated_usd = 1000, program_slug = "p") => ({ component, jurisdiction_code, allocated_usd, program_slug });
const single = { structure_id: "s", economic_identity: "id-s", classification: "SINGLE_JURISDICTION", participants: ["ES"], primary_jurisdiction: "ES", component_allocations: [] };
const stack = { structure_id: "k", economic_identity: "id-k", classification: "STACKED_PROGRAMS", participants: ["CA-ON"], primary_jurisdiction: "CA-ON", program_slugs: ["on_ofttc", "on_ocase"], component_allocations: [] };
const hybrid2 = { structure_id: "h2", economic_identity: "id-h2", classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "IT"], anchor_jurisdiction: "MU", primary_jurisdiction: "MU",
  component_allocations: [comp("post_vfx_package", "IT", 61568)] };
const hybridN = { structure_id: "hn", economic_identity: "id-hn", classification: "HYBRID_ANCHOR_COMPONENT", participants: ["GR", "CA-MB", "CA-NL"], anchor_jurisdiction: "MU", primary_jurisdiction: "MU",
  component_allocations: [comp("principal_production", "GR", 4302827), comp("vfx", "CA-MB", 52500), comp("post_vfx_package", "CA-NL", 9068)] };
// ── FIXTURES (no live instance): official co-production and combined co-production + component routing ─────
const copro = { structure_id: "c", economic_identity: "id-c", classification: "OFFICIAL_COPRODUCTION", treaty_slug: "uk-ca-bilateral", participants: ["GB", "CA"], primary_jurisdiction: "GB",
  coproduction_partners: [{ jurisdiction_code: "GB" }, { jurisdiction_code: "CA" }], component_allocations: [] };
const combined = { structure_id: "cb", economic_identity: "id-cb", classification: "COMBINED_COPRO_HYBRID_STACK", treaty_slug: "uk-ca-bilateral", participants: ["GB", "CA", "IE"], primary_jurisdiction: "GB",
  coproduction_partners: [{ jurisdiction_code: "GB" }, { jurisdiction_code: "CA" }], component_allocations: [comp("principal_production", "GB", 5000), comp("post_vfx_package", "IE", 800)] };

test("structural family comes from served canonical fields, never from participant count alone", () => {
  assert.equal(structuralFamilyOf(single), FAMILY.SINGLE);
  assert.equal(structuralFamilyOf(stack), FAMILY.STACK);
  assert.equal(structuralFamilyOf(hybrid2), FAMILY.HYBRID_TWO);
  assert.equal(structuralFamilyOf(hybridN), FAMILY.HYBRID_MULTI);
  assert.equal(structuralFamilyOf(copro), FAMILY.COPRO);
  assert.equal(structuralFamilyOf(combined), FAMILY.COMBINED);
  // a two-party structure that is NOT a treaty co-production is never gold
  assert.notEqual(structuralFamilyOf({ ...hybrid2, participants: ["GB", "CA"] }), FAMILY.COPRO);
  // an unclassified needs-facts treaty opportunity (live shape) is the co-production family via its treaty relationship
  assert.equal(structuralFamilyOf({ classification: "CONDITIONAL_USER_FACT_REQUIRED", treaty_slug: "uk-ca-bilateral", participants: ["GB", "CA"], coproduction_partners: [{ jurisdiction_code: "GB" }, { jurisdiction_code: "CA" }] }), FAMILY.COPRO);
});

test("family accents: ivory, blue, teal, violet, gold, gold+violet", () => {
  assert.deepEqual(
    [FAMILY.SINGLE, FAMILY.STACK, FAMILY.HYBRID_TWO, FAMILY.HYBRID_MULTI, FAMILY.COPRO, FAMILY.COMBINED].map((f) => FAMILY_META[f].hex),
    ["#e8dfc8", "#5b8def", "#2fb3a3", "#9b7be0", "#d9b24a", "#d9b24a"],
  );
  assert.equal(FAMILY_META[FAMILY.COMBINED].secondary, FAMILY_META[FAMILY.HYBRID_MULTI].hex);
});

test("route topology per family", () => {
  assert.deepEqual(structureTopology(single).edges, []);
  assert.equal(structureTopology(single).shape, "highlight");
  assert.deepEqual(structureTopology(stack).edges, []);
  assert.equal(structureTopology(stack).layered, true, "same-jurisdiction stack is layered, with no artificial arc");
  const t2 = structureTopology(hybrid2);
  assert.equal(t2.shape, "single_route"); assert.equal(t2.edges.length, 1);
  assert.deepEqual([t2.edges[0].from, t2.edges[0].to, t2.edges[0].directed], ["MU", "IT", true]);
  assert.equal(t2.edges[0].label, "POST/VFX", "concise route label: the component only, never spend or rule text");
  const tn = structureTopology(hybridN);
  assert.equal(tn.shape, "hub_and_spoke");
  assert.equal(principalOf(hybridN), "GR", "hub is the principal-production jurisdiction");
  assert.deepEqual(tn.edges.map((e) => [e.from, e.to]), [["GR", "CA-MB"], ["GR", "CA-NL"]], "spokes from one hub, not an A->B->C chain");
  const tc = structureTopology(copro);
  assert.equal(tc.shape, "peer"); assert.deepEqual(tc.edges.map((e) => [e.from, e.to, e.directed]), [["GB", "CA", false]]);
  const tb = structureTopology(combined);
  assert.equal(tb.shape, "peer_plus_branches");
  assert.deepEqual(tb.edges.map((e) => [e.kind, e.from, e.to]), [["peer", "GB", "CA"], ["component", "GB", "IE"]]);
});

test("arcs: only the displayed structure; peer relationships are solid and undirected; routes carry the component label", () => {
  assert.deepEqual(structureArcs(single), []);
  assert.deepEqual(structureArcs(stack), []);
  const a2 = structureArcs(hybrid2);
  assert.equal(a2.length, 1); assert.equal(a2[0].solid, false); assert.deepEqual(a2[0].color, [NEUTRAL_ROUTE_HEX, NEUTRAL_ROUTE_HEX], "arcs carry the category colour supplied by the caller (neutral by default), never a per-structure-type colour");
  assert.equal(a2[0].startCode, "MU"); assert.equal(a2[0].endCode, "IT");
  const an = structureArcs(hybridN);
  assert.equal(an.length, 2); assert.ok(an.every((a) => a.startCode === "GR"));
  const ac = structureArcs(copro);
  assert.equal(ac.length, 1); assert.equal(ac[0].solid, true); assert.deepEqual(structureArcs(copro, { color: "#46e0a8" })[0].color, ["#46e0a8", "#46e0a8"]);
  const ab = structureArcs(combined);
  assert.deepEqual(ab.map((a) => [a.kind, a.solid]), [["peer", true], ["component", false]]);
  assert.ok(ab.every((a) => a.color[0] === NEUTRAL_ROUTE_HEX), "every leg shares one category colour");
});

test("exact participant highlighting and principal", () => {
  assert.deepEqual(participantGlobeKeys(hybridN).sort(), ["CA-MB", "CA-NL", "GR"]);
  assert.equal(principalOf(hybrid2), "MU");
  assert.deepEqual(participantGlobeKeys(copro).sort(), ["CA", "GB"]);
});

test("jurisdiction index keeps canonical projection order (highest priority first) and counts families", () => {
  const pool = [hybrid2, hybridN, { ...hybrid2, structure_id: "h2b", economic_identity: "id-h2b" }, stack];
  const idx = buildStructureIndex(pool);
  assert.deepEqual(idx.get("MU").map((s) => s.structure_id), ["h2", "h2b"]);
  assert.deepEqual(idx.get("IT").map((s) => s.structure_id), ["h2", "h2b"]);
  assert.deepEqual(idx.get("GR").map((s) => s.structure_id), ["hn"]);
  assert.deepEqual(familyCounts(pool), { hybrid_two_party: 2, hybrid_multi_party: 1, stack: 1 });
});

test("hover story states family, principal, components, status, position and family counts", () => {
  const story = structureStory(hybridN, { position: 2, total: 5, familyCountsForJurisdiction: { hybrid_multi_party: 3, hybrid_two_party: 2 } });
  assert.equal(story.family, FAMILY.HYBRID_MULTI);
  assert.equal(story.principal, "GR");
  assert.equal(story.position, 2); assert.equal(story.total, 5);
  assert.deepEqual(story.components.map((c) => [c.component, c.jurisdiction]), [["Principal production", "GR"], ["VFX", "CA-MB"], ["Post/VFX", "CA-NL"]]);
  assert.equal(story.identity, "id-hn");
  assert.ok(story.statusLabel);
  const open = structureStory({ classification: "CONDITIONAL_USER_FACT_REQUIRED", treaty_slug: "t", participants: ["GB", "CA"], is_fully_priced: false, reason: "needs ownership split", structure_id: "o" });
  assert.equal(open.blockerText, "needs ownership split");
});

test("side panel groups by actual structural family; complexity is never a heading", () => {
  const groups = groupByFamily([hybridN, copro, single, stack, hybrid2, combined]);
  assert.deepEqual(groups.map((g) => g.family), ["single", "stack", "hybrid_two_party", "hybrid_multi_party", "official_coproduction", "combined_coproduction"]);
  assert.ok(groups.every((g) => !/practical|advanced/i.test(g.meta.label)));
});

test("stable selection identity is the economic identity (never an array index)", () => {
  assert.equal(identityOf(hybrid2), "id-h2");
  assert.equal(identityOf({ structure_id: "x" }), "x");
});

test("ProjectGlobe wires preview -> lock -> cycle with structure-only arcs, family borders and exact illumination", () => {
  const g = read("screens/production/ProjectGlobe.jsx");
  assert.match(g, /arcs=\{structureArcsForDisplay\}/);
  assert.match(g, /polygonBorders=\{structureBorders\}/);
  assert.match(g, /participantGlobeKeys\(displayStructure\)/);
  assert.match(g, /lockedIdentity/); assert.match(g, /% list\.length/, "clicking the same jurisdiction cycles");
  assert.match(g, /identityOf\(target\)/);
  const globe = read("components/Globe3D.jsx");
  assert.match(globe, /polygonBorders\?\.get\?\.\(iso\)/);
  assert.match(globe, /useEffect\(\(\) => \{\s*if \(globeRef\.current\) globeRef\.current\.arcsData\(arcs\);/, "arcs swap on their own effect so a hover preview never recreates markers");
  assert.match(globe, /d\.solid \|\| window\.matchMedia\?\.\("\(prefers-reduced-motion: reduce\)"\)\.matches \? 1 : 0\.75/, "route flow is calm under reduced motion");
  assert.match(g, /routeLabels=\{displayRoute\.labels\}/);
});

// ── curated rack contract ──────────────────────────────────────────────────────────────────────────
test("curated rack: anchor + four + one populated, unique-by-identity cards, filled with reference alternatives", () => {
  const mk = (i, rec, tier = "PRACTICAL_HYBRID") => ({
    structure_id: `s${i}`, economic_identity: `e${i}`, candidate_status: "PRICED", is_fully_priced: true,
    recommendation_status: rec, practicality_tier: tier, classification: "HYBRID_ANCHOR_COMPONENT",
    npc_with_adjustments_usd: 1000 + i, npc_verified_usd: 1000 + i,
  });
  const anchor = { structure_id: "a", economic_identity: "ea", is_baseline: true, candidate_status: "PRICED", is_fully_priced: true, npc_with_adjustments_usd: 900 };
  const evaluated = [mk(1, "EVALUATED_ALTERNATIVE"), mk(2, "EVALUATED_ALTERNATIVE"), { ...mk(3, "EVALUATED_ALTERNATIVE"), economic_identity: "e1" },
    mk(4, "EVALUATED_ALTERNATIVE", "ADVANCED_MULTI_JURISDICTION"), mk(5, "EVALUATED_ALTERNATIVE", "ADVANCED_MULTI_JURISDICTION"), mk(6, "EVALUATED_ALTERNATIVE"), mk(7, "EVALUATED_ALTERNATIVE")];
  const allocated = { structures: [anchor], evaluated_optimizer_alternatives: evaluated, recommended_optimizer_options: [], optimizer_opportunities_requiring_facts: [] };
  const r = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  const cards = r.slots;
  assert.equal(cards.length, 6, "no missing slots when enough references exist");
  assert.ok(cards.every(Boolean), "no blank cards");
  const ids = cards.map((c) => c.economic_identity);
  assert.equal(new Set(ids).size, ids.length, "no duplicated economic identity (e3 duplicates e1 and is skipped)");
  assert.ok(optimizerProjection(allocated).evaluated.length >= 6);
});
