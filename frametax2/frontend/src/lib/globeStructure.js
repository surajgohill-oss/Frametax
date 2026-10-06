// STRUCTURE-AWARE PROJECT GLOBE (2026-10-01) -- the ONE pure module that turns an already-served canonical
// optimizer structure into (a) its structural family + accent, (b) its route topology, (c) the
// jurisdiction -> structures index (canonical projection order) and (d) the hover "story".
//
// Two INDEPENDENT visual axes (never conflated):
//   A. ACTIONABILITY  -> territory fill (owned by globeData.js / GLOBE_SEMANTIC; untouched here)
//   B. STRUCTURAL FAMILY -> border, route, icon and heading accent (this module)
//
// Family is read ONLY from served canonical fields (classification, treaty relationship, participants,
// component allocations). Official co-production is NEVER inferred from participant count; a participant
// count is used solely to split the already-classified component-hybrid family into two-party vs
// multi-party. No economics are computed here.

import { JURISDICTION_COORDS } from "./jurisdictions.js";
import { globeKey } from "./globeData.js";
import { alternativeLabel, fitSummaryText } from "./alternativeLabels.js";

export const FAMILY = {
  SINGLE: "single",
  STACK: "stack",
  HYBRID_TWO: "hybrid_two_party",
  HYBRID_MULTI: "hybrid_multi_party",
  COPRO: "official_coproduction",
  COMBINED: "combined_coproduction",
};

// Border / route / icon / heading accents. Ivory, blue, teal, violet, gold, gold+violet.
export const FAMILY_META = {
  [FAMILY.SINGLE]: { label: "Single-jurisdiction relocation", hex: "#e8dfc8", secondary: null, order: 0 },
  [FAMILY.STACK]: { label: "Same-jurisdiction program stack", hex: "#5b8def", secondary: null, order: 1 },
  [FAMILY.HYBRID_TWO]: { label: "Two-party component hybrid", hex: "#2fb3a3", secondary: null, order: 2 },
  [FAMILY.HYBRID_MULTI]: { label: "Multi-party component hybrid", hex: "#9b7be0", secondary: null, order: 3 },
  [FAMILY.COPRO]: { label: "Official co-production", hex: "#d9b24a", secondary: null, order: 4 },
  [FAMILY.COMBINED]: { label: "Co-production + component routing", hex: "#d9b24a", secondary: "#9b7be0", order: 5 },
};
export const FAMILY_ORDER = Object.keys(FAMILY_META).sort((a, b) => FAMILY_META[a].order - FAMILY_META[b].order);

const COMPONENT_LABEL = {
  principal_production: "Principal production",
  post_vfx_package: "Post/VFX",
  music_package: "Music",
  vfx: "VFX",
  post: "Post",
  music: "Music",
};
export const componentLabel = (c) => COMPONENT_LABEL[c] || String(c || "component").replace(/_/g, " ");

const uniq = (list) => [...new Set(list.filter(Boolean))];
const partnersOf = (s) => (s?.coproduction_partners || []).map((p) => p.jurisdiction_code || p.code).filter(Boolean);
const componentRows = (s) => (Array.isArray(s?.component_allocations) ? s.component_allocations : []);
const hasTreaty = (s) => !!(s?.treaty_slug || partnersOf(s).length > 0);

// Distinct jurisdictions that actually take part (served participants, else components + primary).
export function participantsOf(s) {
  const fromServed = Array.isArray(s?.participants) ? s.participants : [];
  if (fromServed.length) return uniq(fromServed);
  return uniq([s?.primary_jurisdiction, ...componentRows(s).map((c) => c.jurisdiction_code), ...partnersOf(s)]);
}

export function structuralFamilyOf(s) {
  if (!s) return FAMILY.SINGLE;
  const cls = s.classification;
  if (cls === "COMBINED_COPRO_HYBRID_STACK") return FAMILY.COMBINED;
  if (cls === "OFFICIAL_COPRODUCTION" || cls === "MULTI_PRINCIPAL_MULTILATERAL" || s.structure_type === "treaty_coproduction") {
    // A co-production that also routes components is the combined family.
    const routed = componentRows(s).some((c) => c.component && c.component !== "principal_production");
    return routed ? FAMILY.COMBINED : FAMILY.COPRO;
  }
  if (cls === "STACKED_PROGRAMS") return FAMILY.STACK;
  if (cls === "HYBRID_ANCHOR_COMPONENT") return participantsOf(s).length >= 3 ? FAMILY.HYBRID_MULTI : FAMILY.HYBRID_TWO;
  if (cls === "SINGLE_JURISDICTION") return FAMILY.SINGLE;
  // Unclassified legacy entry: derive from served relationships only (never from participant count alone
  // for co-production).
  if (hasTreaty(s)) return FAMILY.COPRO;
  const comps = componentRows(s).filter((c) => c.component && c.component !== "principal_production");
  if (comps.length) return participantsOf(s).length >= 3 ? FAMILY.HYBRID_MULTI : FAMILY.HYBRID_TWO;
  if ((s.stacked_programs?.length || s.program_slugs?.length || 0) > 1 && participantsOf(s).length <= 1) return FAMILY.STACK;
  return FAMILY.SINGLE;
}

// The anchor / principal-production jurisdiction of a structure.
export function principalOf(s) {
  const principal = componentRows(s).find((c) => c.component === "principal_production");
  return principal?.jurisdiction_code || s?.anchor_jurisdiction || s?.primary_jurisdiction || participantsOf(s)[0] || null;
}

const coordsOf = (code) => JURISDICTION_COORDS[code] || JURISDICTION_COORDS[String(code || "").split("-")[0]] || null;

// Route topology. `edges` carry the component/package and routed spend where served; `directed` is true only
// where the canonical structure establishes a direction (principal -> routed component destination).
export function structureTopology(s) {
  const family = structuralFamilyOf(s);
  const principal = principalOf(s);
  const rows = componentRows(s);
  const routed = rows.filter((c) => c.component && c.component !== "principal_production" && c.jurisdiction_code);
  const edgesToComponents = () => {
    const byDest = new Map();
    for (const r of routed) {
      if (r.jurisdiction_code === principal) continue;
      const e = byDest.get(r.jurisdiction_code) || { from: principal, to: r.jurisdiction_code, components: [], spendUsd: 0, directed: true, kind: "component" };
      e.components.push(componentLabel(r.component));
      e.spendUsd += Number(r.allocated_usd) || 0;
      byDest.set(r.jurisdiction_code, e);
    }
    return [...byDest.values()].map((e) => ({ ...e, label: `${e.components.join(" + ")}${e.spendUsd ? ` · $${Math.round(e.spendUsd).toLocaleString()}` : ""}` }));
  };
  if (family === FAMILY.SINGLE) return { family, shape: "highlight", principal, nodes: participantsOf(s), edges: [], layered: false };
  if (family === FAMILY.STACK) return { family, shape: "layered", principal, nodes: participantsOf(s), edges: [], layered: true };
  if (family === FAMILY.HYBRID_TWO) {
    return { family, shape: "single_route", principal, nodes: participantsOf(s), edges: edgesToComponents(), layered: false };
  }
  if (family === FAMILY.HYBRID_MULTI) {
    return { family, shape: "hub_and_spoke", principal, nodes: participantsOf(s), edges: edgesToComponents(), layered: false };
  }
  // Official co-production: solid peer relationship between principals (undirected -- no canonical direction).
  const principals = uniq([principal, ...partnersOf(s)]);
  const peerEdges = [];
  for (let i = 1; i < principals.length; i += 1) {
    peerEdges.push({ from: principals[0], to: principals[i], components: [], spendUsd: 0, directed: false, kind: "peer", label: "Co-production principals" });
  }
  if (family === FAMILY.COPRO) {
    return { family, shape: "peer", principal, nodes: participantsOf(s), edges: peerEdges, layered: false };
  }
  return { family, shape: "peer_plus_branches", principal, nodes: participantsOf(s), edges: [...peerEdges, ...edgesToComponents()], layered: false };
}

// three-globe arcs for ONE displayed structure (never every route at once). Colour is the family accent.
export function structureArcs(s) {
  const topo = structureTopology(s);
  const meta = FAMILY_META[topo.family];
  const arcs = [];
  for (const e of topo.edges) {
    const a = coordsOf(e.from);
    const b = coordsOf(e.to);
    if (!a || !b) continue;
    const peer = e.kind === "peer";
    arcs.push({
      startLat: a.lat, startLng: a.lng, endLat: b.lat, endLng: b.lng,
      color: peer && meta.secondary ? meta.hex : (e.kind === "component" && meta.secondary ? meta.secondary : meta.hex),
      strokeWidth: peer ? 0.7 : 0.5,
      solid: !e.directed,            // undirected / peer relationships are solid and do not animate
      altitude: peer ? 0.22 : 0.3,
      startCode: e.from, endCode: e.to, label: e.label || null, kind: e.kind, family: topo.family,
    });
  }
  return arcs;
}

// Globe keys of every participating jurisdiction (for exact highlighting).
export function participantGlobeKeys(s) {
  return uniq(participantsOf(s).map(globeKey));
}

// Ordered jurisdiction -> structures index. `pool` is already in canonical projection order; that order is
// preserved so index[0] is the highest-priority structure for the jurisdiction.
export function buildStructureIndex(pool) {
  const byKey = new Map();
  for (const s of pool || []) {
    for (const key of participantGlobeKeys(s)) {
      if (!byKey.has(key)) byKey.set(key, []);
      byKey.get(key).push(s);
    }
  }
  return byKey;
}

export function familyCounts(list) {
  const counts = {};
  for (const s of list || []) {
    const f = structuralFamilyOf(s);
    counts[f] = (counts[f] || 0) + 1;
  }
  return counts;
}

// Stable identity used for selection / locking / cycling (never an array index or structure UUID alone).
export const identityOf = (s) => s?.economic_identity || s?.structure_id || null;

// Hover "story" for a previewed structure at a hovered jurisdiction.
export function structureStory(s, { position = 1, total = 1, familyCountsForJurisdiction = null, leadingId = null } = {}) {
  if (!s) return null;
  const topo = structureTopology(s);
  const meta = FAMILY_META[topo.family];
  const rows = componentRows(s);
  return {
    identity: identityOf(s),
    structureId: s.structure_id,
    family: topo.family,
    familyLabel: meta.label,
    accent: meta.hex,
    accentSecondary: meta.secondary,
    shape: topo.shape,
    principal: topo.principal,
    components: rows.map((r) => ({
      component: componentLabel(r.component), jurisdiction: r.jurisdiction_code || null,
      program: r.program_slug || null, spendUsd: r.allocated_usd ?? null,
    })),
    participants: topo.nodes,
    routes: topo.edges.map((e) => ({ from: e.from, to: e.to, label: e.label, directed: e.directed, kind: e.kind })),
    layered: topo.layered,
    statusLabel: alternativeLabel(s, leadingId),
    fitSummary: fitSummaryText(s),
    // The specific blocker / missing facts for a structure that is not (yet) executable.
    blockerText: s.is_fully_priced ? null : (s.reason || (Array.isArray(s.blockers) && s.blockers[0]) || s.personnel_next_question || null),
    missingFacts: !s.is_fully_priced && Array.isArray(s.personnel_missing_facts) ? s.personnel_missing_facts.slice(0, 3) : [],
    position, total,
    familyCounts: familyCountsForJurisdiction,
  };
}

// Side-panel grouping by actual canonical structural family (complexity/practicality remain badges, never headings).
export function groupByFamily(list) {
  const groups = new Map(FAMILY_ORDER.map((f) => [f, []]));
  for (const s of list || []) groups.get(structuralFamilyOf(s)).push(s);
  return FAMILY_ORDER.filter((f) => groups.get(f).length).map((f) => ({ family: f, meta: FAMILY_META[f], items: groups.get(f) }));
}
