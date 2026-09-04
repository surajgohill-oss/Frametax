import { JURISDICTION_COORDS } from "./jurisdictions.js";
import { fixtureSlotFor, fixtureRelatedFor, isFixtureActive, noteFixtureCounts } from "./globeVisualFixture.js";
// Reused, not re-derived: the SAME program-name + rate presentation
// scenarioDisplay() already uses for structure cards across Overview,
// Workspace and Scenarios (see format.jsx) — so a hovered jurisdiction's
// "base incentive" line can never disagree with what its own card shows.
import { programDisplay } from "./programNames.js";

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

// A structure's semantic state, derived entirely from the allocated
// structure's own real fields (allocated_structures.ranking +
// is_fully_priced + blockers) — never a client-side re-derivation of
// pricing. Several surfaces (card badges) key off these slot names; the
// Globe's country state below reuses the SAME derivation rather than
// inventing a second one, so a jurisdiction can never read as Recommended
// on the Globe and as something else on its card.
//
// Reading of each branch under the semantic system (see GLOBE_SEMANTIC):
//   rank 1          -> Recommended            (the one best structure)
//   fully priced    -> Optimized alternative  (real, economically viable)
//   has blockers    -> Unlockable opportunity (beneficial but conditional)
//   otherwise       -> Additional             (touched, not actionable yet)
export function structureTier(structure, rankById) {
  const rank = rankById.get(structure.structure_id);
  if (rank?.rank === 1) return "gold";
  if (structure.is_fully_priced) return "jade";
  if (structure.blockers?.length > 0) return "amber";
  return "silver";
}

// The producer's active/leading structure — the shared selection
// (AppState leadingStructureId) if set, else the ONE canonical
// scenario-selection source the backend computes and serves explicitly
// (allocated.canonical_selected_structure_id — see canonical_production_
// view.py, Final non-Globe closeout Item A). Every non-Globe surface
// (Overview, Workspace, Reports) calls this same function so none of
// them can independently determine a different "project truth" when no
// producer override is active — the rank==1-only line ranking.find(...)
// used to fall back to here still runs, but ONLY as a defensive guard
// for a served payload that predates the canonical field, never as a
// second authoritative computation.
export function activeStructure(allocated, leadingStructureId) {
  if (!allocated) return null;
  const byId = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  if (leadingStructureId && byId.has(leadingStructureId)) return byId.get(leadingStructureId);
  if (allocated.canonical_selected_structure_id && byId.has(allocated.canonical_selected_structure_id)) {
    return byId.get(allocated.canonical_selected_structure_id);
  }
  // Defensive-only fallback (see comment above) — mirrors the exact same
  // rank==1 rule the server itself applies when computing the canonical
  // field, so this can never disagree with it even if it ever fires.
  const best = allocated.ranking.find((r) => r.rank === 1);
  return best ? byId.get(best.structure_id) : null;
}

// ── The Globe's semantic system (Phase 2 closeout) ──────────────────────
// EXACTLY FOUR production-decision states. This object is the canonical
// source: every Globe-adjacent surface (choropleth fill, beacons, hover
// card, structure cards) reads from here, and none may introduce a fifth.
//
// These states describe what a producer should DO about a jurisdiction, not
// what the engine knows about it. The previous model shipped five
// DATABASE-STATE categories — "Qualified / viable", "Evaluated / not
// applicable", "No known incentive" — which described the discovery
// engine's own bookkeeping. A producer cannot act on "evaluated", and
// "No known incentive" actively misled: per the discovery audit, 103 of 124
// rejected records mean "no knowledge-base entry exists", not "we checked
// and it is ineligible", so painting them as a verdict asserted a
// conclusion the backend never reached.
//
//   recommended  Gold   The single best production structure. Soft pulse.
//   alternative  Green  An economically beneficial alternative. No pulse.
//   unlockable   Amber  Beneficial but currently blocked — clearly conditional.
//   additional   Slate  Everything else this production touches. Low emphasis.
//
// `pulse` is authoritative: ONLY the recommendation pulses (see Globe3D's
// ring layer). An alternative that pulsed would read as a second
// recommendation, which is the one thing this system exists to prevent.
//
// The slot keys (gold/jade/amber/silver) are retained deliberately — the
// app-wide tier vocabulary OUTSIDE the Globe (ScenarioCard badges,
// format.js's tierBadgeClass) keys off exactly these names, and renaming
// them would churn surfaces this pass is explicitly scoped out of. What
// changed is the SEMANTICS and the wording attached to them.
// ── THE EMPHASIS LADDER (measured, not eyeballed) ───────────────────────
// The four states must increase in emphasis monotonically. Perceived
// luminance (0.299R + 0.587G + 0.114B) is the check, and the ladder below is
// the contract:
//
//   untouched land  #78828f  129   (GRAPHITE_HEX — the base, no state)
//   Additional      #8c96a4  149   desaturated slate, low emphasis
//   Optimized alt.  #55d698  168   saturated green
//   Unlockable      #eaa93c  176   saturated amber
//   Recommended     #f7dc9b  221   brightest thing on the Globe
//
// FIXED HERE — the ladder was INVERTED and it is the measurable cause of the
// "Globe is mostly grey" report. Additional was #a9b2c0 at luminance **177**,
// i.e. BRIGHTER than both Optimized alternative (137) and Unlockable (161).
// The lowest-emphasis state was the second-most-prominent thing on screen, and
// because Additional is the residual bucket (61 of 86 jurisdictions), the
// Globe rendered as a field of light grey with the actionable states sitting
// *beneath* it. No amount of material or lighting work could have fixed that;
// it is an ordering error in the palette itself.
//
// Optimized alternative and Unlockable are deliberately close in luminance
// (168 / 176) — they are PEER states, and they separate by hue (green vs
// amber), not by weight. Only Recommended is allowed to dominate.
//
// Saturation and contrast follow the approved reference render: the actionable
// states carry real colour, the neutrals are genuinely desaturated. This is
// hierarchy work, not final material tuning — materials, lighting, ocean and
// atmosphere remain Phase 3.
// PHASE 3A FINAL RECONCILIATION: jade/amber hue+saturation reconciled against
// the approved reference render (sampled directly, not estimated) — richer,
// more saturated "mineral/enamel" material colour, luminance held within the
// already-verified ladder (see the monotonicity test below; both moved from
// ~117 to ~117, i.e. same rank, just more pigment). gold/silver untouched:
// the render has no analog for either (its "leading recommendation" swatch is
// green, its neutrals are a legacy six-state grey/violet) — the render governs
// material richness and colour, not a hue swap for states it doesn't map to.
// PHASE 3A FINAL MICRO-PASS: four explicit material identities given directly
// (not sampled), each re-solved in HSL and luminance-checked against the raw-
// byte luminance the monotonicity test itself uses (NOT three.js's colour-
// managed THREE.Color().r/.g/.b, which is a LINEAR value and gave a false
// pass in an earlier draft of this pass) — "warm champagne-gold" / "richer
// jade, not pale mint" / "restrained amber-copper" / "quiet blue-grey slate,
// distinct from neutral land" (GRAPHITE_HEX, lum 131).
// Ladder after this pass: land 131 < silver 145 < jade 151 < amber 153 < gold 212
// (recommended leads the peer pair by 59, comfortably over the required 25).
// PHASE 3A FINAL CLOSEOUT: labels reconciled a third time to the production's
// actual executive terminology, given directly rather than guessed —
// "Recommended" (unchanged) / "Alternatives" (was "Optimized") /
// "Co-Production Opportunities" (was "Opportunity") / "Excluded" (was
// "Baseline"). `fullLabel` carries the long form for hover/detail surfaces
// where "Co-Production Opportunities" fits; `label` is the compact-legend
// form ("Co-Pro Opportunities") used only where horizontal space is scarce.
// Same four slots, same hex, same `state` keys, same logic — a wording pass
// only, per this batch's explicit "do not change semantic logic" instruction.
export const GLOBE_SEMANTIC = {
  gold: { state: "recommended", label: "Recommended", fullLabel: "Recommended", hex: "#e6d3a8", pulse: true },
  jade: { state: "alternative", label: "Alternatives", fullLabel: "Alternatives", hex: "#4cbd97", pulse: false },
  amber: { state: "unlockable", label: "Co-Pro Opportunities", fullLabel: "Co-Production Opportunities", hex: "#d48a49", pulse: false },
  // Desaturated slate — deliberately the DIMMEST of the four, sitting just
  // above untouched land. Never a warm/taupe grey: those reintroduce the muddy
  // cast the neutral light rig exists to prevent (see Globe3D lighting).
  silver: { state: "additional", label: "Excluded", fullLabel: "Excluded", hex: "#8494a4", pulse: false },
};

// Derived, never hand-maintained. Existing consumers (Globe3D's TIER_HEX,
// ProjectGlobe's structure cards, CompanyGlobe) import these two.
export const STATUS_HEX = Object.fromEntries(
  Object.entries(GLOBE_SEMANTIC).map(([k, v]) => [k, v.hex]),
);
export const STATUS_LABEL = Object.fromEntries(
  Object.entries(GLOBE_SEMANTIC).map(([k, v]) => [k, v.label]),
);
// Long form for hover/detail surfaces (e.g. "Co-Production Opportunities"
// rather than the legend's compact "Co-Pro Opportunities"). Three of the
// four slots are identical to STATUS_LABEL; only `amber` differs.
export const STATUS_FULL_LABEL = Object.fromEntries(
  Object.entries(GLOBE_SEMANTIC).map(([k, v]) => [k, v.fullLabel]),
);
// Which states pulse. Globe3D reads this rather than hardcoding "gold".
export const PULSE_TIERS = new Set(
  Object.entries(GLOBE_SEMANTIC).filter(([, v]) => v.pulse).map(([k]) => k),
);

// Untouched landmass — jurisdictions this production has no opinion about.
// It carries no semantic state (it is the absence of one), so it has no entry
// above, but it IS part of the same canonical palette and must be declared
// exactly once. Globe3D.jsx imports THIS constant rather than re-declaring it.
//
// PHASE 3A: hue moved from neutral-cool grey (#78828f) to teal-slate
// (#6c8c90), LUMINANCE HELD at the same ladder position (~129 -> ~131,
// effectively unchanged). This is the reconciliation-plan-approved response to
// "numerically brighter is not accepted as fixed" — the Phase 2 pass raised
// luminance only, which stopped land reading as void but left it a flat
// neutral-cool grey rather than the approved render's teal-slate character.
// Hue is the axis that changes now; luminance is deliberately NOT re-touched
// here, because the ladder ordering (land < Additional < Optimized/Unlockable
// < Recommended) is already correct and re-verified by `npm test` — moving hue
// at fixed luminance is what keeps that test green while fixing the actual
// complaint. Roughness/emissive/material-response changes that make this hue
// read with real tonal variation (not just a flat swap) live in Globe3D.jsx's
// `getCapMaterial` frosted branch, not here.
//
// Still strictly a TEAL-slate, never a warm/taupe one: warm neutrals here
// reintroduce the muddy cast the neutral light rig exists to prevent.
export const GRAPHITE_HEX = "#6c8c90";

// Development-only: rewrite a status map to the visual fixture's assignments.
// Lives HERE rather than in globeVisualFixture.js because this module is the
// sole owner of what a semantic state looks like — the fixture only supplies
// slot names, so it can never introduce a colour or a fifth state. Mutates in
// place because this map is the single upstream of every Globe surface.
function applyFixtureStates(statuses) {
  const counts = { gold: 0, jade: 0, amber: 0, silver: 0 };
  // Keyed by the map's globe key, not the winning structure's jurisdiction
  // code — the key is stable, the representative code depends on upsert order.
  for (const [iso, entry] of statuses) {
    const slot = fixtureSlotFor(iso);
    const semantic = GLOBE_SEMANTIC[slot] ? slot : "silver";
    entry.status = semantic;
    entry.hex = GLOBE_SEMANTIC[semantic].hex;
    counts[semantic] += 1;
    // Hypothetical Co-Production relationship, dev-only. Attached to the
    // entry rather than passed separately so it travels the SAME path the
    // real `structure.participants` relationship does, and so it can only
    // ever exist on a map that applyFixtureStates has already rewritten —
    // i.e. it is structurally impossible for it to reach production
    // rendering. See fixtureRelatedFor's own comment for why the real data
    // cannot exercise this state at all.
    const rel = fixtureRelatedFor(iso);
    if (rel) entry.fixtureRelated = rel;
  }
  noteFixtureCounts(counts);
  return statuses;
}

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

// Exported (Phase 3B Batch 2) so the category-diff engine's consumer can
// tell an IMPROVING transition (silver -> amber, amber -> jade, etc., the
// "unlock pulse" case) from a downgrade, using the SAME rank the status
// upsert itself already resolves by — never a second, parallel ordering.
export const STATUS_RANK = { gold: 4, jade: 3, amber: 2, silver: 1 };

function roleFor(structure, code) {
  if (!structure) return null;
  if (structure.primary_jurisdiction === code) return "Primary shoot";
  if (structure.structure_type === "component_relocation") return "Routed component (post / VFX / music)";
  if (structure.structure_type === "treaty_coproduction") return "Co-production partner";
  if (structure.structure_type === "full_relocation") return "Primary shoot";
  return "Participating jurisdiction";
}

// Country-level semantic state + hover data, built entirely from
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

  // `meta` carries presentation-only extras that aren't part of the
  // status/ranking decision itself — currently just the discovery
  // examination's own real `reason` string for Excluded jurisdictions (see
  // branch 2 below), so hover can state WHY without a second, invented
  // explanation.
  const upsert = (iso, status, jurisdictionCode, structure, meta = null) => {
    const cur = byIso.get(iso);
    if (!cur || STATUS_RANK[status] > STATUS_RANK[cur.status]) {
      byIso.set(iso, {
        status, hex: STATUS_HEX[status],
        jurisdictionCodes: cur ? cur.jurisdictionCodes.add(jurisdictionCode) : new Set([jurisdictionCode]),
        best: { structure, code: jurisdictionCode },
        meta,
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
  //    all fold into "Additional" (silver). Never overrides a stronger
  //    state already set from an actual structure.
  //
  //    PHASE 2 CLOSEOUT: this branch previously split into two states —
  //    capability_only -> silver ("evaluated / not applicable") and
  //    rejected+has_capability_data -> darkRed ("no known incentive"). Both
  //    were database states, and darkRed was the worse offender: it
  //    asserted a verdict ("we checked, it's ineligible") on a Globe whose
  //    job is to communicate production decisions. A producer cannot act on
  //    either one; neither is a recommendation, an alternative, or an
  //    unlockable opportunity. They are Additional, at low emphasis.
  //
  //    Note this is a semantic fold, not a loss of selectivity. The
  //    `has_capability_data` gate is RETAINED: 103 of 124 rejected records
  //    mean "no knowledge-base entry exists for this jurisdiction at all",
  //    not "evaluated and ineligible", and those must still stay off the
  //    Globe entirely — painting them any colour turns the instrument into
  //    a coverage map. Only the 21 records rejected on a real capability
  //    mismatch against this production's own requirements (e.g.
  //    marine/open-water filming) are something this production actually
  //    touched, so only those reach Additional.
  for (const e of allocated.discovery?.examinations || []) {
    const iso = globeKey(e.jurisdiction_code);
    if (byIso.has(iso)) continue;
    const touched =
      e.classification === "capability_only" ||
      (e.classification === "rejected" && e.has_capability_data);
    // e.reason is the backend's own real, already-generated sentence
    // (production_discovery.py) — carried through so Excluded's hover can
    // state the actual reason instead of a generic placeholder.
    if (touched) upsert(iso, "silver", e.jurisdiction_code, null, { reason: e.reason || null });
  }

  return byIso;
}

// Per-country hover payload — read verbatim from the best (highest-state)
// structure touching that country. Countries with no participating
// structure (Excluded, from discovery only) carry state + jurisdiction
// only, because no structure exists to read figures from.
//
// PHASE 3A FINAL CLOSEOUT — INSPECTOR BOUNDARY UPDATED (explicit,
// user-directed reversal of the Phase 2 closeout rule below): hover is now
// required to show "a lightweight economic summary" — base incentive
// structure, its rate, and estimated NPC — so `incentiveUsd`/`npcUsd` may
// now be RENDERED by the Globe hover card, not merely carried for an
// Inspector preview. Nothing here is a second calculation: every figure
// below is read verbatim from the same `structure`/`segments` fields the
// Inspector and every structure card already read (see AllocationSegment
// Inspector in Inspector.jsx and scenarioDisplay in format.jsx). What
// remains off-limits is long source notes, the qualification trace,
// account-level detail and any other Inspector-only content — those still
// require opening the Inspector.
//
// PHASE 3B BATCH 1: `baseIncentive` now carries the MODELED rate
// (`rate_ceiling`, confirmed from allocation_pricing.py source to be the
// field literally populated from `rr.modeled_rate` — the rate that actually
// funds `incentive_ceiling_usd`/`selected_incentive_usd`/
// `npc_with_adjustments_usd`), not the guaranteed floor — see
// globeHoverFormat.js's `modeledRateInfo` for the full reasoning. Also adds
// the per-jurisdiction segment incentive (`segmentIncentiveUsd`, at the
// modeled rate, for "% of gross budget"), the structure's own gross budget,
// and — for Co-Production Opportunities — the structure's real participant
// list as `relatedCodes` (raw codes; the caller resolves display names, kept
// out of this pure-data module).
//
// `grossBudgetUsd` param: the PRODUCTION's own gross budget, used only as
// the fallback when a structure has none of its own — same
// `structure.gross_budget_usd ?? productionGross` chain Workspace.jsx's
// ScenarioCard already uses (see format.jsx-era comment there); never a
// second, independently-derived figure.
export function buildCountryHoverData(statuses, grossBudgetUsd = null) {
  const byIso = new Map();
  for (const [iso, entry] of statuses) {
    const { structure, code } = entry.best;
    // Base incentive structure + rate, read from the SAME segment field
    // names Inspector.jsx's AllocationSegmentInspector renders (program_slug,
    // rate_floor, rate_ceiling, is_band_ceiling, claims_incentive) — no
    // second derivation. Only the segment for THIS jurisdiction's own code,
    // not the structure's dominant segment (that's scenarioDisplay's job on
    // the card, a different question: "what defines this whole structure").
    const seg = structure?.segments?.find((sg) => sg.jurisdiction_code === code);
    const baseIncentive = seg?.claims_incentive && seg.program_slug
      ? {
          programLabel: programDisplay(seg.program_slug),
          ratePct: seg.rate_ceiling != null ? Math.round(seg.rate_ceiling * 100) : null,
          floorPct: seg.rate_floor != null ? Math.round(seg.rate_floor * 100) : null,
          isBandCeiling: !!seg.is_band_ceiling,
        }
      : null;
    byIso.set(iso, {
      isoA2: iso,
      jurisdictionCode: code,
      jurisdictionName: JURISDICTION_COORDS[code]?.name || code,
      status: entry.status,
      statusLabel: STATUS_LABEL[entry.status],
      // Long form for the hover card ("Co-Production Opportunities"); the
      // legend keeps the compact STATUS_LABEL ("Co-Pro Opportunities").
      fullStatusLabel: STATUS_FULL_LABEL[entry.status],
      semanticState: GLOBE_SEMANTIC[entry.status]?.state ?? null,
      hex: entry.hex,
      incentiveUsd: structure?.is_fully_priced ? structure.selected_incentive_usd : null,
      npcUsd: structure?.is_fully_priced ? structure.npc_with_adjustments_usd : null,
      // This jurisdiction's OWN segment incentive (at the modeled rate) —
      // distinct from `incentiveUsd` above, which is the whole structure's
      // total across every segment. Real for any segment with a resolved
      // rate, independent of `is_fully_priced` (a segment can resolve a rate
      // while a DIFFERENT segment in the same structure blocks the whole
      // structure from being fully priced).
      segmentIncentiveUsd: seg?.claims_incentive ? seg.incentive_ceiling_usd ?? null : null,
      grossBudgetUsd: structure?.gross_budget_usd ?? grossBudgetUsd ?? null,
      baseIncentive,
      // Real backend text (production_discovery.py's own reason string) —
      // only ever set for Excluded jurisdictions sourced from a discovery
      // examination (see buildCountryStatuses branch 2). Never fabricated;
      // absent when the engine hasn't actually classified a reason.
      excludedReason: entry.meta?.reason ?? null,
      // Co-Production Opportunities only: the structure's own real
      // participants (this hover's code excluded) — see globeHoverFormat.js
      // for why this is the one real "related jurisdiction" relationship
      // this data model has, and the report for what's still missing.
      // `entry.fixtureRelated` is set ONLY by applyFixtureStates (dev-only,
      // see globeVisualFixture.js) and is absent on every real-data path, so
      // the `??` below resolves to the real participants in production. It
      // exists because the real relationship is unreachable for this
      // production — measured, not assumed: the winning structure for every
      // jurisdiction is the single-participant ALLOC-RELOC-* one, so this
      // array is empty for all 86, and the illumination it drives has never
      // fired at runtime.
      relatedCodes:
        entry.fixtureRelated?.related ??
        structure?.participants?.filter((c) => c !== code) ??
        [],
      // PHASE 3B BATCH 2: the structure's own real `primary_jurisdiction` —
      // used ONLY to let hover illumination make the primary related
      // jurisdiction read slightly stronger than the rest, per the batch's
      // explicit "only when such ranking is supported by real data, never
      // invent a preferred partner" instruction. Real field, not a computed
      // preference.
      primaryJurisdictionCode:
        entry.fixtureRelated?.primary ?? structure?.primary_jurisdiction ?? null,
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

  // The primary shoot reads Recommended; every downstream routed/
  // co-production leg reads Optimized alternative — a production hierarchy,
  // not a flat chain. No new state is introduced for overlay mode.
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
  { mode = "jurisdictions", leadingStructureId = null, selectedJurisdiction = null, grossBudgetUsd = null } = {},
) {
  const empty = {
    points: [], arcs: [], polygonColors: new Map(), selectedIso: null,
    selectedLat: null, selectedLng: null, focusLat: null, focusLng: null, focusDistance: null,
    hoverByIso: new Map(), structuresByCode: new Map(),
    stateCounts: { gold: 0, jade: 0, amber: 0, silver: 0 }, categoryByIso: new Map(),
  };
  if (!allocated) return empty;

  const statuses = buildCountryStatuses(allocated, rankById);
  // Development-only visual fixture. THE single injection point for the whole
  // Globe: polygon fill, beacons, ring/pulse eligibility, hover labels and the
  // structure-card dots all derive from this one map, so rewriting it here
  // keeps every surface consistent without a second rendering path. Disabled
  // by default and inert in production builds — see globeVisualFixture.js.
  // Presentation only: nothing here touches the backend response, the
  // optimizer, or any persisted record.
  if (isFixtureActive()) applyFixtureStates(statuses);
  const hoverByIso = buildCountryHoverData(statuses, grossBudgetUsd);
  // Phase 3B Batch 1: the category-diff engine's input — plain iso->status
  // ("gold"/"jade"/"amber"/"silver") map, cheap to derive here since
  // `statuses` already carries it. No animation, no rendering — see
  // lib/globeCategoryDiff.js for what consumes this.
  const categoryByIso = new Map();
  for (const [iso, entry] of statuses) categoryByIso.set(iso, entry.status);
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

  // Per-state tally of what is actually on the Globe. Exposed so the dev
  // fixture badge and the regression checks can assert the distribution
  // (notably "exactly one Recommended") against the rendered truth rather than
  // against a hardcoded expectation.
  const stateCounts = { gold: 0, jade: 0, amber: 0, silver: 0 };
  for (const [, entry] of statuses) {
    if (stateCounts[entry.status] != null) stateCounts[entry.status] += 1;
  }

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
      hoverByIso, structuresByCode, stateCounts, categoryByIso,
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
    hoverByIso, structuresByCode, stateCounts, categoryByIso,
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
