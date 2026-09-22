// OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22) — the ONE canonical
// producer scenario label adapter every optimizer-consuming surface must
// call (Workspace cards, Workspace slot-6 dropdown, Overview's Optimized
// card, Full Project Globe's side list, Workspace Map/Split), never a
// second, independently-derived label.
//
// Lives in its own pure .js module (no JSX) — same pattern lib/
// incentiveRate.js already established (see that file's own header
// comment): "independently unit-testable with plain node — format.jsx has
// real JSX and cannot be", re-exported from format.jsx for existing
// callers. A local, minimal jurisdiction-name resolver is kept here
// (mirrors format.jsx's own bestJurisdictionName exactly) rather than
// importing it back from format.jsx, to avoid a circular import between
// the two modules — JURISDICTION_COORDS (jurisdictions.js) is the only
// shared dependency, already a pure .js module.
//
// ROOT CAUSE this replaces: compactScenarioIdentity (format.jsx) derives
// its routed-destination disambiguation from `structure.segments` — real
// for a plain component_relocation structure, but for the canonical
// producer_optimizer_scenario_canonicalization pass's own
// `optimizer_scenarios` representatives, `segments` can carry a
// NON-CLAIMING cost-tracking jurisdiction (e.g. a "United States" segment
// with claims_incentive=false, present purely to track spend physically
// incurred there — confirmed live for Little Utopia's Mauritius+Manitoba
// scenarios) alongside the real claiming participants. Merging every
// segment jurisdiction into the visible label therefore surfaced a
// jurisdiction the structure never actually claims an incentive in or
// routes a component to. `component_allocations` never carries that
// non-claiming segment — it is the routed-component ledger itself (every
// row already carries its own real `component` category and
// `jurisdiction_display_name`) — so reading it here, and ONLY it, cannot
// reintroduce that defect.
//
// This also directly fixes the FVD "dozens of duplicate Manitoba+NL+Italy
// cards" symptom: two scenarios sharing the same routed components/
// destinations but a DIFFERENT anchor jurisdiction (e.g. Greece: Post ->
// Manitoba vs Italy: Post -> Manitoba vs Trinidad and Tobago: Post ->
// Manitoba — confirmed live: 68 real, materially different FVD scenarios
// share the exact same "post->Manitoba, vfx->Newfoundland & Labrador"
// routing, differing ONLY by which real jurisdiction anchors the
// principal leg and therefore claims a different real incentive program)
// now render visibly distinct labels, since the anchor is a first-class,
// always-present part of the label — never omitted on the assumption a
// separate flag/dot element elsewhere on the card already discloses it.
// Two scenarios sharing the same participants/primary jurisdiction but
// routing a DIFFERENT category to the SAME destination (post->Manitoba vs
// music->Manitoba vs vfx->Manitoba) also render visibly distinct labels,
// since the routed component is part of the label too.
import { JURISDICTION_COORDS } from "./jurisdictions.js";
import { humanizeToken } from "./programNames.js";

const jurName = (code) => JURISDICTION_COORDS[code]?.name || code || "—";

function bestJurisdictionNameLocal(code, structure) {
  if (structure && code === structure.primary_jurisdiction && structure.jurisdiction_display_name) {
    const parts = structure.jurisdiction_display_name.split(" — ");
    return parts[parts.length - 1];
  }
  return jurName(code);
}

// A subnational code's trimmed display name (e.g. JURISDICTION_COORDS
// / jurisdiction_display_name's last " — "-delimited segment for
// "US-GA" -> "Georgia") can collide with an unrelated country's own name
// (Georgia the country, "GE") — confirmed live for FVD: both resolve to
// the bare string "Georgia", so a Georgia(country)-anchored scenario and a
// Georgia(US state)-anchored scenario, though genuinely different
// jurisdictions with different real incentive programs, rendered
// identical labels. Disambiguated by appending the ISO2 parent country
// code for any subnational jurisdiction: cheap (no extra lookup — the
// code itself already carries it), always available, and only changes
// the few genuinely ambiguous cases.
function disambiguatedJurisdictionName(code, structure, displayNameOverride) {
  const name = (displayNameOverride ? displayNameOverride.split(" — ").pop() : null)
    || bestJurisdictionNameLocal(code, structure) || code || "";
  if (code && code.includes("-")) {
    const iso2 = code.split("-")[0];
    return `${name}, ${iso2}`;
  }
  return name;
}

export function buildScenarioLabel(structure) {
  if (!structure) return "";
  const rows = structure.component_allocations || [];
  const anchorName = disambiguatedJurisdictionName(structure.primary_jurisdiction, structure)
    || structure.primary_jurisdiction || "";
  // The routed (non-principal) legs are what most often distinguish two
  // otherwise-similar-looking scenarios sharing the same anchor — but the
  // anchor itself must always lead the label (see header comment above:
  // two scenarios can share IDENTICAL routed legs and differ ONLY by
  // anchor).
  const routedLegs = rows.filter((r) => r.component && r.component !== "principal_production");
  const legLabel = (r) => {
    const dest = disambiguatedJurisdictionName(r.jurisdiction_code, structure, r.jurisdiction_display_name);
    return `${humanizeToken(r.component)} → ${dest}`;
  };
  let base;
  if (routedLegs.length) {
    base = `${anchorName}: ${routedLegs.map(legLabel).join(" · ")}`;
  } else {
    // No routed component at all (a single-leg/principal-only structure,
    // or a Single Jurisdiction winner with no component_allocations) —
    // fall back to the structure's own real jurisdiction identity, never
    // a fabricated route.
    base = anchorName || structure.label || "—";
  }
  // PRODUCER_PRACTICALITY_TIER (2026-09-22): an Advanced-tier scenario (3+
  // distinct jurisdictions, or a combined/multilateral structure) carries
  // real coordination overhead the producer must see before opening it —
  // same disclosure text every surface uses, never a second wording.
  if (structure.practicality_tier === "ADVANCED_MULTI_JURISDICTION") {
    const n = structure.participant_count ?? new Set(structure.participants || []).size;
    return `Advanced · ${n} jurisdictions · ${base}`;
  }
  return base;
}
