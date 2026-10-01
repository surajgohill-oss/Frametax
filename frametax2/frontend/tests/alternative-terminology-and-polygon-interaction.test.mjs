// ALTERNATIVE_TERMINOLOGY + JURISDICTION_POLYGON_INTERACTION (2026-10-01).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { ALT, alternativeLabel } from "../src/lib/alternativeLabels.js";
import { buildPolygonIndex, pickIsoAt, polygonIsoSet, markerNeedsFallback, resolvePolygonTarget } from "../src/lib/globePicking.js";
import { optimizerProjection } from "../src/lib/workspaceScenarioMode.js";
import { buildGlobeView, OPTIMIZER_SEMANTIC } from "../src/lib/globeData.js";
import { JURISDICTION_COORDS } from "../src/lib/jurisdictions.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const readSrc = (rel) => readFileSync(path.join(here, "..", "src", rel), "utf8");
const readGeo = (name) => JSON.parse(readFileSync(path.join(here, "..", "public", "geo", name), "utf8"));

function s(id, o = {}) {
  return {
    structure_id: id, participants: ["GR", "IT"], primary_jurisdiction: "GR", is_fully_priced: true,
    recommendation_status: "EVALUATED_ALTERNATIVE", savings_vs_current_usd: 50_000, npc_with_adjustments_usd: 1_000_000,
    classification: "HYBRID_ANCHOR_COMPONENT", practicality_tier: "PRACTICAL_HYBRID", ...o,
  };
}

test("label mapping covers every canonical status exactly as specified", () => {
  assert.equal(alternativeLabel(s("a", { recommendation_status: "RECOMMENDED", is_recommended: true }), "a"), "LEADING ALTERNATIVE");
  assert.equal(alternativeLabel(s("b", { recommendation_status: "RECOMMENDED", is_recommended: true }), "a"), "STRONG ALTERNATIVE");
  assert.equal(alternativeLabel(s("c", { savings_vs_current_usd: 40_000 })), "COST-SAVING REFERENCE");
  assert.equal(alternativeLabel(s("d", { recommendation_status: "COSTS_MORE", savings_vs_current_usd: -10_000 })), "REFERENCE ALTERNATIVE");
  assert.equal(alternativeLabel(s("e", { recommendation_status: "NEUTRAL", savings_vs_current_usd: 0 })), "REFERENCE ALTERNATIVE");
  assert.equal(alternativeLabel(s("f", { recommendation_status: "BASELINE_UNRESOLVED", savings_vs_current_usd: null })), "REFERENCE ALTERNATIVE");
  assert.equal(alternativeLabel({ candidate_status: "CO_PRO_OPPORTUNITY" }), "NEEDS MORE FACTS");
  for (const st of ["RULE_REJECTED", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "FEASIBILITY_REVIEW_REQUIRED", "QUALIFICATION_HARD_FAIL"]) {
    assert.equal(alternativeLabel({ candidate_status: st }), "UNAVAILABLE", st);
  }
  assert.deepEqual(Object.values(ALT).length, 6);
});

test("zero qualified alternatives: nobody is Leading or Strong, every executable option stays visible as a reference", () => {
  const rows = [
    s("p1", { savings_vs_current_usd: 90_000 }), // positive but below the hurdle
    s("p2", { recommendation_status: "COSTS_MORE", savings_vs_current_usd: -5_000 }),
    s("p3", { recommendation_status: "NEUTRAL", savings_vs_current_usd: 0 }),
  ];
  const a = { recommended_optimizer_options: [], evaluated_optimizer_alternatives: rows, optimizer_executable_total: 3 };
  const p = optimizerProjection(a);
  assert.equal(p.recommended.length, 0);
  const leadingId = p.recommended[0]?.structure_id ?? null;
  assert.equal(leadingId, null);
  const labels = p.evaluated.map((x) => alternativeLabel(x, leadingId));
  assert.ok(labels.every((l) => l !== ALT.LEADING && l !== ALT.STRONG));
  assert.equal(p.evaluated.length, 3, "worse-than-anchor and below-hurdle options are never hidden");
  assert.equal(labels.filter((l) => l === ALT.COST_SAVING).length, 1, "positive-but-below-hurdle -> cost-saving reference");
});

test("better-than-anchor alone never makes an option Leading or Strong; only the canonical status does", () => {
  const big = s("big", { savings_vs_current_usd: 5_000_000 }); // far better than anchor, NOT canonical RECOMMENDED
  assert.equal(alternativeLabel(big, "someone-else"), ALT.COST_SAVING);
  assert.notEqual(alternativeLabel(big, "big"), ALT.LEADING);
});

test("user-facing surfaces no longer say 'Recommended' for optimizer alternatives", () => {
  assert.equal(OPTIMIZER_SEMANTIC.gold.label, "Leading Alternative");
  assert.equal(OPTIMIZER_SEMANTIC.jade.label, "Strong Alternative");
  assert.equal(OPTIMIZER_SEMANTIC.silver.label, "Reference Alternative");
  assert.equal(OPTIMIZER_SEMANTIC.red.label, "Unavailable");
  const globe = readSrc("screens/production/ProjectGlobe.jsx");
  assert.match(globe, /heading: "Leading \/ Strong Alternatives"/);
  assert.match(globe, /heading: "Reference Alternatives"/);
  const ws = readSrc("screens/production/Workspace.jsx");
  assert.match(ws, /alternativeLabel\(structure, optimizerLeadingId\)/);
  assert.match(ws, /optgroup label=\{workspaceMode === MODE_OPTIMIZER \? "Leading \/ Strong Alternatives"/);
  assert.match(readSrc("components/OptimizerCategorySummary.jsx"), /Leading \/ Strong Alternative/);
  assert.match(readSrc("shell/Inspector.jsx"), /Alternative status/);
  // chips on the Globe list carry the label too
  assert.match(globe, /alternativeLabel\(s, optimizerProj\?\.recommended\?\.\[0\]\?\.structure_id \?\? null\)/);
});

// ── polygon interaction ──────────────────────────────────────────────────
const FIX = { FRA: "FR", NOR: "NO" };
function isoOfFeature(f) {
  const sub = f?.properties?.iso_3166_2;
  if (sub) return sub;
  const raw = f?.properties?.ISO_A2;
  if (raw && raw !== "-99") return raw;
  return FIX[f?.properties?.ADM0_A3] || raw;
}
function loadIndex() {
  const world = readGeo("world-110m.geojson");
  const admin1 = readGeo("admin1-us-ca.geojson");
  const countries = world.features.filter((f) => !["US", "CA"].includes(isoOfFeature(f)));
  return buildPolygonIndex([...countries, ...admin1.features], isoOfFeature);
}
// An interior sample point of a feature: scan its bbox for a contained point farthest from `avoid`.
function interiorPoint(index, iso, avoid) {
  const e = index.find((x) => x.iso === iso);
  let best = null, bestD = -1;
  const { minX, minY, maxX, maxY } = e.bbox;
  const stepX = (maxX - minX) / 24 || 0.01, stepY = (maxY - minY) / 24 || 0.01;
  for (let x = minX + stepX / 2; x < maxX; x += stepX) for (let y = minY + stepY / 2; y < maxY; y += stepY) {
    if (pickIsoAt([e], y, x) !== iso) continue;
    const d = avoid ? Math.hypot(x - avoid.lng, y - avoid.lat) : 0;
    if (d > bestD) { bestD = d; best = { lat: y, lng: x, d }; }
  }
  return best;
}

test("polygon resolution: a point anywhere inside a represented jurisdiction (away from its marker) resolves to that exact jurisdiction", () => {
  const index = loadIndex();
  const isos = polygonIsoSet(index);
  let checked = 0;
  for (const iso of ["CA-SK", "CA-MB", "CA-ON", "CA-BC", "US-TX", "US-GA", "MN", "GE", "FR", "DE", "KZ", "IN", "PE", "GR"]) {
    assert.ok(isos.has(iso), `${iso} has polygon geometry`);
    const marker = JURISDICTION_COORDS[iso];
    const p = interiorPoint(index, iso, marker);
    assert.ok(p, iso);
    assert.equal(pickIsoAt(index, p.lat, p.lng), iso, `${iso} interior point (${p.lat.toFixed(1)}, ${p.lng.toFixed(1)}), ${p.d.toFixed(1)} deg from its marker`);
    if (p.d > 1) checked++;
  }
  assert.ok(checked >= 10, "interior points were genuinely away from the coordinate marker");
});

test("state/province polygons are distinct from national ones: no national US/CA polygon, Texas is US-TX, Georgia (GE) is not US-GA", () => {
  const index = loadIndex();
  const isos = polygonIsoSet(index);
  assert.equal(isos.has("US"), false);
  assert.equal(isos.has("CA"), false);
  assert.ok(isos.has("US-TX") && isos.has("US-GA") && isos.has("GE"));
  const tx = interiorPoint(index, "US-TX", null);
  assert.equal(pickIsoAt(index, tx.lat, tx.lng), "US-TX");
  const ge = interiorPoint(index, "GE", null);
  assert.equal(pickIsoAt(index, ge.lat, ge.lng), "GE");
  const sk = interiorPoint(index, "CA-SK", null);
  assert.equal(pickIsoAt(index, sk.lat, sk.lng), "CA-SK", "Saskatchewan is independently interactive");
  assert.equal(pickIsoAt(index, 0, -30), null, "open ocean resolves to nothing");
});

test("marker fallback applies only where polygon geometry is unavailable", () => {
  const isos = polygonIsoSet(loadIndex());
  const fallback = (iso) => markerNeedsFallback({ iso }, isos);
  for (const iso of ["CA", "AU-NSW", "AU-QLD", "AU-SA", "MU", "SG", "MT"]) assert.equal(fallback(iso), true, `${iso} keeps its marker as the pointer target`);
  for (const iso of ["CA-SK", "CA-MB", "US-TX", "MN", "GE", "FR"]) assert.equal(fallback(iso), false, `${iso} is polygon-interactive`);
  assert.equal(markerNeedsFallback({ iso: "FR" }, null), true, "no polygons loaded yet -> markers remain usable");
});

test("polygon target is keyed to the canonical jurisdiction record and not influenced by marker proximity", () => {
  const index = loadIndex();
  const mk = (iso) => ({ iso, jurisdictionCode: iso, jurisdictionName: JURISDICTION_COORDS[iso]?.name });
  const pointByIso = new Map(["CA-SK", "CA-MB", "US-TX"].map((i) => [i, mk(i)]));
  // a point inside Saskatchewan but numerically closest (marker-wise) to Manitoba's marker still resolves to Saskatchewan
  const skEdge = interiorPoint(index, "CA-SK", JURISDICTION_COORDS["CA-MB"]);
  assert.equal(resolvePolygonTarget(index, skEdge.lat, skEdge.lng, pointByIso).iso, "CA-SK");
  assert.equal(resolvePolygonTarget(index, skEdge.lat, skEdge.lng, new Map()), null, "an unrepresented jurisdiction yields no hover");
});

test("Globe3D wires central polygon picking and keeps keyboard/fallback behaviour", () => {
  const src = readSrc("components/Globe3D.jsx");
  assert.match(src, /resolvePolygonTarget\(idx, lat, lng/);
  assert.match(src, /g\.toGeoCoords\(/);
  assert.match(src, /mount\.addEventListener\("pointermove", onPolygonMove\)/);
  assert.match(src, /mount\.addEventListener\("click", onPolygonClick\)/);
  assert.match(src, /el\.dataset\.fallback = fallback \? "1" : "0"/);
  assert.match(src, /el\.style\.pointerEvents = fallback \? "auto" : "none"/);
  assert.match(src, /isVisible && el\.dataset\.fallback === "1" \? "auto" : "none"/);
  assert.match(src, /el\.setAttribute\("tabindex", "0"\)/, "markers stay keyboard-focusable");
  assert.match(src, /el\.addEventListener\("focus"/);
  assert.doesNotMatch(src, /const size = 40/, "no oversized marker hit-boxes simulating jurisdiction geometry");
});

test("end to end data path: a built Optimizer view exposes a hover record for every polygon-backed jurisdiction", () => {
  const a = {
    recommended_optimizer_options: [], optimizer_executable_total: 1,
    evaluated_optimizer_alternatives: [s("e1", { participants: ["CA-MB", "US-TX", "MN"], primary_jurisdiction: "CA-MB" })],
    optimizer_opportunities_requiring_facts: [], rejection_universe: { by_disposition: {}, first_page: { results: [] } },
  };
  const v = buildGlobeView(a, new Map(), { mode: "optimizer" });
  const isos = polygonIsoSet(loadIndex());
  for (const p of v.points) {
    if (!isos.has(p.iso)) continue;
    assert.ok(v.hoverByIso.get(p.iso).jurisdictionName, `hover record for ${p.iso}`);
    assert.equal(p.tier, "silver");
  }
});
