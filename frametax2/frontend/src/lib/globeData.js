import { JURISDICTION_COORDS } from "./jurisdictions";

export const TIER_RANK = { gold: 4, jade: 3, amber: 2, silver: 1 };

// Great-circle angular separation (degrees) between two {lat, lng} points —
// used only to size the Optimizer Overlay's auto-framing distance to the
// routing chain's real geographic spread (see buildOptimizerPathway below).
function angularSeparationDeg(a, b) {
  const toRad = Math.PI / 180;
  const lat1 = a.lat * toRad, lat2 = b.lat * toRad;
  const dLng = (b.lng - a.lng) * toRad;
  const cos = Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return Math.acos(Math.max(-1, Math.min(1, cos))) * (180 / Math.PI);
}

// Tier is derived entirely from the allocated structure's own real
// fields (allocated_structures.ranking + is_fully_priced + blockers) —
// never a client-side re-derivation of pricing. Several surfaces (card
// badges) key off this ranking tier; the Globe's country status below
// reuses the SAME tier, just remapped onto the approved production-status
// palette rather than inventing a second one.
export function structureTier(structure, rankById) {
  const rank = rankById.get(structure.structure_id);
  if (rank?.rank === 1) return "gold";
  if (structure.is_fully_priced) return "jade";
  if (structure.blockers?.length > 0) return "amber";
  return "silver";
}

// The producer's active/leading structure — the shared selection
// (AppState leadingStructureId) if set, else the optimizer's own rank #1.
export function activeStructure(allocated, leadingStructureId) {
  if (!allocated) return null;
  const byId = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  if (leadingStructureId && byId.has(leadingStructureId)) return byId.get(leadingStructureId);
  const best = allocated.ranking.find((r) => r.rank === 1);
  return best ? byId.get(best.structure_id) : null;
}

// The Globe/candidate-card shared status palette — the ONE source every
// Globe-adjacent surface reads from (GlobeLegend, Globe3D's TIER_HEX below,
// ProjectGlobe's candidate cards). Reused here as PRODUCTION STATUS, not an
// interaction state:
//   gold    = Leading Recommendation
//   jade    = Qualified / Viable
//   amber   = Conditional (treaty / partner / cultural / qualification pending)
//   silver  = Evaluated / Not Applicable
//   darkRed = No Known Incentive / Ineligible
// Brightened in the 2026-07-28 regression-lock pass — richer, more
// saturated jewel tones so active jurisdictions read as enamel/glass
// rather than chalky flat fills. Category meanings are unchanged.
export const STATUS_HEX = {
  gold: "#e8c273",
  jade: "#4bab7f",
  amber: "#e0a83f",
  silver: "#b0aca2",
  darkRed: "#a3453c",
};
export const STATUS_LABEL = {
  gold: "Leading recommendation",
  jade: "Qualified / viable",
  amber: "Conditional",
  silver: "Evaluated / not applicable",
  darkRed: "No known incentive",
};

// A jurisdiction code's country-level ISO2 — sub-national codes (US-CA,
// CA-BC, AU-NSW, ...) map to their parent country; country-level codes
// (MU, GR, ...) are already ISO2.
export function countryCode(jurisdictionCode) {
  return (jurisdictionCode || "").split("-")[0];
}

// Countries whose sub-national jurisdictions are the real production
// decision unit — a producer shoots in Georgia or British Columbia, not in
// "the United States". For these, the Globe renders admin-1 polygons
// (public/geo/admin1-us-ca.geojson) and the country-level polygon is
// suppressed entirely, so status is never averaged across 50 states.
export const SUBNATIONAL_COUNTRIES = new Set(["US", "CA"]);

// Jurisdiction codes with no admin-1 polygon of their own but a real
// country-level polygon in the world set — Natural Earth models Puerto
// Rico as its own country entity rather than a US state.
const GLOBE_KEY_OVERRIDES = { "US-PR": "PR" };

// The key a jurisdiction code renders under on the Globe: the full
// sub-national code for US/CA (matching admin-1 `iso_3166_2`), otherwise
// the parent ISO2 country code (matching world-110m `ISO_A2`).
export function globeKey(jurisdictionCode) {
  const code = jurisdictionCode || "";
  if (GLOBE_KEY_OVERRIDES[code]) return GLOBE_KEY_OVERRIDES[code];
  const parent = countryCode(code);
  if (SUBNATIONAL_COUNTRIES.has(parent) && code.includes("-")) return code;
  return parent;
}

const STATUS_RANK = { gold: 5, jade: 4, amber: 3, silver: 2, darkRed: 1 };

function roleFor(structure, code) {
  if (!structure) return null;
  if (structure.primary_jurisdiction === code) return "Primary shoot";
  if (structure.structure_type === "component_relocation") return "Routed component (post / VFX / music)";
  if (structure.structure_type === "treaty_coproduction") return "Co-production partner";
  if (structure.structure_type === "full_relocation") return "Primary shoot";
  return "Participating jurisdiction";
}

// Country-level production status + hover data, built entirely from
// allocated_structures (participation/ranking) and its discovery audit
// (examined-but-not-participating jurisdictions) — no new calculation,
// no fabricated figures. Every jurisdiction the backend has an opinion
// on (participant OR discovery-examined) gets a status; anything else
// stays unmapped (the Globe renders it as neutral/dark).
//
// Status is intentionally computed WITHOUT gating on JURISDICTION_COORDS.
// That table exists to place the secondary point/marker layer (which does
// need a lat/lng) — polygon fill only needs the ISO2 code to match against
// the loaded GeoJSON, and gating status on coordinate availability here
// silently dropped the vast majority of Dark Red (rejected) countries,
// since JURISDICTION_COORDS only has entries for the ~59 codes that also
// needed a marker. Confirmed against live data: 68 of 69 rejected
// countries (China, Russia, Brazil, India, Indonesia, ...) had no
// coordinate entry and were vanishing from the choropleth entirely — the
// precise, identifiable cause of the Globe reading as almost all Jade.
export function buildCountryStatuses(allocated, rankById) {
  const byIso = new Map(); // iso2 -> { status, hex, jurisdictionCodes:Set, best:{structure,code} }
  if (!allocated) return byIso;

  const upsert = (iso, status, jurisdictionCode, structure) => {
    const cur = byIso.get(iso);
    if (!cur || STATUS_RANK[status] > STATUS_RANK[cur.status]) {
      byIso.set(iso, {
        status, hex: STATUS_HEX[status],
        jurisdictionCodes: cur ? cur.jurisdictionCodes.add(jurisdictionCode) : new Set([jurisdictionCode]),
        best: { structure, code: jurisdictionCode },
      });
    } else {
      cur.jurisdictionCodes.add(jurisdictionCode);
    }
  };

  // 1. Every participant of every generated structure — status from the
  //    SAME structureTier the rest of the app uses (gold/jade/amber/silver).
  //    Keyed by globeKey, so US/CA sub-national jurisdictions each carry
  //    their own status rather than collapsing into one country verdict.
  for (const s of allocated.structures) {
    const tier = structureTier(s, rankById);
    for (const code of s.participants) {
      upsert(globeKey(code), tier, code, s);
    }
  }

  // 2. Discovery-examined jurisdictions with no participating structure —
  //    capability_only -> silver (evaluated, not currently applicable);
  //    rejected -> darkRed (no known incentive / ineligible). Never
  //    overrides a stronger status already set from an actual structure.
  //    (As of this data snapshot the discovery engine only ever emits
  //    "rejected" or "incentive_ready" — every "incentive_ready" record
  //    becomes a participant and is already handled in step 1, so no
  //    country currently reaches silver through this branch. That is a
  //    real gap in the backend's classification enum, not a mapping bug
  //    here — see the Globe completion report.)
  //
  //    "rejected" is NOT one uniform signal — confirmed against live data
  //    (`has_capability_data`, an existing per-examination field): 103 of
  //    124 rejected records are "no structured capability profile and no
  //    priceable incentive model" — the backend simply has no knowledge
  //    base entry for that jurisdiction at all, not a real evaluation.
  //    Painting those Dark Red reads as "we checked, it's ineligible" when
  //    the truth is "we never checked" — the exact coverage-map failure
  //    mode the Globe must avoid; it should stay selective, weighted only
  //    toward jurisdictions that matter for this production. Only the
  //    remaining 21 records (`has_capability_data: true`, rejected on a
  //    real capability mismatch against this production's own
  //    requirements, e.g. marine/open-water filming) are a genuine
  //    evaluated-and-ineligible signal, so only those reach Dark Red.
  for (const e of allocated.discovery?.examinations || []) {
    const iso = globeKey(e.jurisdiction_code);
    if (byIso.has(iso)) continue;
    if (e.classification === "capability_only") upsert(iso, "silver", e.jurisdiction_code, null);
    else if (e.classification === "rejected" && e.has_capability_data) upsert(iso, "darkRed", e.jurisdiction_code, null);
  }

  return byIso;
}

// Per-country hover payload (jurisdiction, status, estimated incentive,
// estimated NPC, primary production role) — read verbatim from the best
// (highest-status) structure touching that country. Countries with no
// participating structure (silver/darkRed from discovery only) show
// status + jurisdiction only — no incentive/NPC exists to show.
export function buildCountryHoverData(statuses, rankById) {
  const byIso = new Map();
  for (const [iso, entry] of statuses) {
    const { structure, code } = entry.best;
    byIso.set(iso, {
      isoA2: iso,
      jurisdictionCode: code,
      jurisdictionName: JURISDICTION_COORDS[code]?.name || code,
      status: entry.status,
      statusLabel: STATUS_LABEL[entry.status],
      hex: entry.hex,
      incentiveUsd: structure?.is_fully_priced ? structure.selected_incentive_usd : null,
      npcUsd: structure?.is_fully_priced ? structure.npc_with_adjustments_usd : null,
      role: roleFor(structure, code),
      structureId: structure?.structure_id ?? null,
      structureLabel: structure?.label ?? null,
    });
  }
  return byIso;
}

// Optimizer Overlay: the ACTIVE (selected/leading) structure's own
// participant chain only — never every possible relationship. Ordered
// Primary shoot -> routed/co-production participants, in the order the
// backend already returns participants. Real fields only (participants,
// primary_jurisdiction, structure_type); no fabricated intermediate
// "Post" / "VFX" split beyond what the structure_type actually encodes.
//
// Arc thickness is scaled by each leg's real qualified-spend weight
// (structure.segments[].qpe_usd, the same figure Budget Rail traces) —
// the destination jurisdiction's share of the structure's own routed
// spend. When a leg's segment isn't present in the data, its arc falls
// back to a fixed mid-width rather than inventing a weight.
export function buildOptimizerPathway(allocated, leadingStructureId) {
  const structure = activeStructure(allocated, leadingStructureId);
  if (!structure) return { points: [], arcs: [], structure: null };
  const ordered = [
    structure.primary_jurisdiction,
    ...(structure.participants || []).filter((c) => c !== structure.primary_jurisdiction),
  ].filter((c) => JURISDICTION_COORDS[c]);

  const qpeByCode = new Map((structure.segments || []).map((sg) => [sg.jurisdiction_code, sg.qpe_usd]));
  const maxQpe = Math.max(1, ...ordered.map((c) => qpeByCode.get(c) || 0));

  // The primary shoot reads Gold; every downstream routed/co-production
  // leg reads Jade — a production hierarchy, not a flat chain.
  const points = ordered.map((code, i) => {
    const status = i === 0 ? "gold" : "jade";
    return {
      lat: JURISDICTION_COORDS[code].lat, lng: JURISDICTION_COORDS[code].lng,
      tier: status, name: code, id: code, iso: globeKey(code), color: STATUS_HEX[status],
      role: roleFor(structure, code), qpeUsd: qpeByCode.get(code) ?? null,
    };
  });

  // Directional arcs: each leg's color runs origin-hue -> destination-hue
  // (three-globe renders a two-stop arcColor array as a gradient along the
  // arc), so flow direction reads without inventing arrowhead geometry.
  const arcs = [];
  for (let i = 0; i < ordered.length - 1; i++) {
    const a = JURISDICTION_COORDS[ordered[i]];
    const b = JURISDICTION_COORDS[ordered[i + 1]];
    const destQpe = qpeByCode.get(ordered[i + 1]);
    // Floor keeps a low-spend leg legible; the range above it is the real
    // allocation weight, so thickness still encodes routed spend honestly.
    // Thickened from the previous 0.3-1.1 range: in the Optimizer Overlay
    // the routing arcs ARE the production-structure story, not a thin line
    // under a second choropleth, so they need real physical weight.
    const strokeWidth = destQpe != null ? 0.55 + 1.4 * (destQpe / maxQpe) : 0.85;
    arcs.push({
      startLat: a.lat, startLng: a.lng, endLat: b.lat, endLng: b.lng,
      tier: "gold", strokeWidth,
      color: [STATUS_HEX[i === 0 ? "gold" : "jade"], STATUS_HEX.jade],
    });
  }

  // Only the active structure's own jurisdictions stay lit in the overlay —
  // this is what stops the mode reading as "the choropleth in other colors".
  const participantColors = new Map();
  for (const p of points) participantColors.set(p.iso, p.color);

  // Auto-framing target: the PRIMARY SHOOT, not the participant centroid.
  // A centroid is degenerate for the common near-antipodal routing pair
  // (Mauritius shoot -> Vancouver post are ~180° apart, so their averaged
  // direction vector collapses toward zero and the camera settles on an
  // unrelated part of the globe). The primary shoot is always well-defined
  // and is the anchor a producer reads the structure outward from.
  const focusLat = points.length ? points[0].lat : null;
  const focusLng = points.length ? points[0].lng : null;

  // Auto-framing distance: scales with how far the routing chain actually
  // spans, so a tight regional structure (e.g. Georgia -> Ireland) zooms in
  // and a globe-spanning one (Mauritius -> Vancouver) pulls back enough to
  // show the whole chain. Deliberately NOT built from a centroid (see
  // above) — it only measures the real angular spread from the primary
  // shoot to its farthest participant, which stays well-defined even for
  // near-antipodal pairs. Clamped well inside the OrbitControls zoom range
  // (150-460 in Globe3D.jsx) so the user's own zoom still has headroom
  // either side of the default.
  const focusDistance = points.length <= 1 ? 250 : (() => {
    const maxSepDeg = Math.max(...points.slice(1).map((p) => angularSeparationDeg(points[0], p)));
    const t = Math.max(0, Math.min(1, (maxSepDeg - 30) / 150));
    return Math.round(250 + t * 150);
  })();

  return { points, arcs, structure, participantColors, focusLat, focusLng, focusDistance };
}

// Single entry point for every Globe-consuming screen (Overview, Workspace
// Map/Split, ProjectGlobe) — replaces the old buildGlobeData. Returns
// everything Globe3D and its callers need: polygonColors (iso->hex) for the
// country choropleth, the secondary point/hit-target layer, the selected
// country's iso + reference coordinate (for the camera-centering tween),
// per-country hover data, and structuresByCode (unchanged consumer
// contract — click routing into the Inspector).
export function buildGlobeView(
  allocated, rankById,
  { mode = "jurisdictions", leadingStructureId = null, selectedJurisdiction = null } = {},
) {
  const empty = {
    points: [], arcs: [], polygonColors: new Map(), selectedIso: null,
    selectedLat: null, selectedLng: null, focusLat: null, focusLng: null, focusDistance: null,
    hoverByIso: new Map(), structuresByCode: new Map(),
  };
  if (!allocated) return empty;

  const statuses = buildCountryStatuses(allocated, rankById);
  const hoverByIso = buildCountryHoverData(statuses, rankById);
  const polygonColors = new Map();
  for (const [iso, entry] of statuses) polygonColors.set(iso, entry.hex);

  const structuresByCode = new Map();
  for (const s of allocated.structures) {
    for (const code of s.participants) {
      const list = structuresByCode.get(code) || [];
      list.push(s);
      structuresByCode.set(code, list);
    }
  }

  const selectedIso = selectedJurisdiction ? globeKey(selectedJurisdiction) : null;
  const selectedCoord = JURISDICTION_COORDS[selectedJurisdiction] || null;

  if (mode === "optimizer") {
    const pathway = buildOptimizerPathway(allocated, leadingStructureId);
    // Overlay isolation: ONLY the active structure's jurisdictions are
    // filled. Everything else falls back to neutral graphite, so the mode
    // reads as one production structure rather than a second choropleth.
    return {
      points: pathway.points, arcs: pathway.arcs,
      polygonColors: pathway.participantColors, selectedIso,
      selectedLat: selectedCoord?.lat ?? null, selectedLng: selectedCoord?.lng ?? null,
      // With no explicit selection, frame the active structure itself.
      focusLat: selectedCoord?.lat ?? pathway.focusLat,
      focusLng: selectedCoord?.lng ?? pathway.focusLng,
      focusDistance: pathway.focusDistance,
      hoverByIso, structuresByCode,
    };
  }

  // Real multi-jurisdiction structure relationships — broadened in the
  // 2026-07-28 regression-lock pass, then IMMEDIATELY re-bounded after live
  // verification: gating on "any ranked structure" was wrong — every one of
  // this production's ~177 generated candidates carries a rank, so that
  // filter drew dozens of arcs radiating from Mauritius to nearly every
  // country on the globe, exactly the "every possible relationship" clutter
  // the original treaty-only restriction existed to prevent.
  //
  // Correct scope: treaty structures (as before — a small, always-real,
  // always-meaningful set) PLUS the production's own currently ACTIVE/
  // LEADING structure specifically, regardless of its structure_type. This
  // is what actually fixes the reported bug ("Mauritius + Vancouver", a
  // component_relocation with no treaty_slug, disappears from Jurisdictions
  // mode even when it's the structure the producer is looking at") without
  // reintroducing clutter — at most one non-treaty relationship is ever
  // shown at a time, the same one Optimizer Overlay would show for the same
  // selection.
  const activeMultiJurisdiction = activeStructure(allocated, leadingStructureId);
  const structureArcs = [];
  const seenStructureIds = new Set();
  const pushStructureArcs = (s) => {
    if (!s || seenStructureIds.has(s.structure_id)) return;
    if (!s.participants || s.participants.length < 2) return;
    seenStructureIds.add(s.structure_id);
    const ordered = [
      s.primary_jurisdiction,
      ...s.participants.filter((c) => c !== s.primary_jurisdiction),
    ].filter((c) => JURISDICTION_COORDS[c]);
    const tier = structureTier(s, rankById);
    for (let i = 0; i < ordered.length - 1; i++) {
      const ca = JURISDICTION_COORDS[ordered[i]];
      const cb = JURISDICTION_COORDS[ordered[i + 1]];
      structureArcs.push({
        startLat: ca.lat, startLng: ca.lng, endLat: cb.lat, endLng: cb.lng,
        tier, color: STATUS_HEX[tier],
      });
    }
  };
  for (const s of allocated.structures) {
    if (s.treaty_slug && s.participants.length === 2) pushStructureArcs(s);
  }
  pushStructureArcs(activeMultiJurisdiction);

  const points = buildCountryPoints(statuses, hoverByIso, selectedIso);
  return {
    points, arcs: structureArcs, polygonColors, selectedIso,
    selectedLat: selectedCoord?.lat ?? null, selectedLng: selectedCoord?.lng ?? null,
    focusLat: selectedCoord?.lat ?? null, focusLng: selectedCoord?.lng ?? null, focusDistance: null,
    hoverByIso, structuresByCode,
  };
}

// Small, subtle interaction hit-targets — one per status-bearing country,
// positioned at its reference coordinate. Deliberately secondary in size/
// opacity: the country polygon fill is the primary visualization now: the
// points below exist ONLY to carry click/hover behavior (three-globe's
// polygon layer has no native onClick/onHover in the installed version —
// see Globe3D.jsx), not to be looked at.
export function buildCountryPoints(statuses, hoverData, selectedIso) {
  const points = [];
  for (const [iso, entry] of statuses) {
    const code = entry.best.code;
    const coord = JURISDICTION_COORDS[code];
    if (!coord) continue;
    const hover = hoverData.get(iso);
    points.push({
      lat: coord.lat, lng: coord.lng, id: iso, iso, name: hover?.jurisdictionName || code,
      tier: entry.status, color: entry.hex, selected: iso === selectedIso,
      ...hover,
    });
  }
  return points;
}
