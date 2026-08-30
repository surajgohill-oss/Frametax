import { JURISDICTION_COORDS } from "./jurisdictions";
import { humanizeToken, programDisplay } from "./programNames.js";

const jurName = (code) => JURISDICTION_COORDS[code]?.name || code || "—";

// Workspace Top-6/Data Truthfulness: JURISDICTION_COORDS is a GEOGRAPHIC
// pin/coordinate map for the Globe (its own file header says so — the
// "commonly-used production hub", e.g. Sydney for AU-NSW), never a
// producer-facing name registry. It was being reused as one anyway
// (jurName above), which is exactly wrong for a sub-national code — the
// real jurisdiction registry name ("Australia — New South Wales") is a
// city's state, not the city. The backend now serves that real name
// directly on a structure (jurisdiction_display_name, sourced from the
// canonical Jurisdiction table, never a frontend map) for its own
// primary_jurisdiction — prefer it there; fall back to the geo map only
// for a participant code the structure doesn't carry its own registry
// name for (a real, disclosed gap, never a fabricated label).
export function bestJurisdictionName(code, structure) {
  if (structure && code === structure.primary_jurisdiction && structure.jurisdiction_display_name) {
    return structure.jurisdiction_display_name;
  }
  return jurName(code);
}

// Pure display formatting only — no business logic, no derived facts.

export function Money({ value, bare = false }) {
  if (value === null || value === undefined) return <span className="text-tertiary">—</span>;
  const num = Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  return <span className="mono">{bare ? num : `$${num}`}</span>;
}

// Abbreviated currency for dense multi-cell displays (Today's lifecycle
// ladder) where nine full-precision figures side by side would be
// unreadable. Falls back to full precision below $1,000 — no rounding
// that would misrepresent a genuinely small figure as "$0K".
export function CompactMoney({ value }) {
  if (value === null || value === undefined) return <span className="text-tertiary">—</span>;
  const n = Number(value);
  const abs = Math.abs(n);
  let text;
  if (abs >= 1_000_000) text = `$${(n / 1_000_000).toFixed(1)}M`;
  else if (abs >= 1_000) text = `$${(n / 1_000).toFixed(0)}K`;
  else text = `$${Math.round(n).toLocaleString()}`;
  return <span className="mono">{text}</span>;
}

// Global CineGlobe display rule: when two figures that are SUPPOSED to
// represent the same real-world quantity differ only by economically
// immaterial source-document rounding noise (a few dollars on a multi-
// million-dollar budget — e.g. a leaf-account sum vs. the source document's
// own stated Grand Total), display them as equal rather than surfacing a
// dagger/footnote/explanatory paragraph a producer has no use for. This is
// presentation-only — it never touches the underlying data, never changes a
// real QPE/exclusion calculation, and never applies when the difference
// exceeds the threshold (a genuine, economically material divergence must
// still render as-is, unnormalized).
const TRIVIAL_VARIANCE_USD = 5;
export function normalizeTrivialVariance(value, reference, thresholdUsd = TRIVIAL_VARIANCE_USD) {
  if (value == null || reference == null) return value;
  return Math.abs(value - reference) <= thresholdUsd ? reference : value;
}

export function Pct({ value }) {
  if (value === null || value === undefined) return <span className="text-tertiary">—</span>;
  return <span className="mono">{(Number(value) * 100).toFixed(0)}%</span>;
}

// Final Global Discovery phase: requirements/timing fields are
// tri-state (true / false / not confirmed) far more often than the rest
// of this app's mostly-numeric surfaces — this is the one shared
// renderer so "Not stated" never gets reinvented per call site, and a
// real `false` (e.g. "no minimum spend") never collapses into the same
// dash as "unknown".
export function YesNo({ value }) {
  if (value === null || value === undefined) return <span className="text-tertiary">Not stated</span>;
  return <span>{value ? "Required" : "Not required"}</span>;
}

// Objective 5 / Objective 3's explicit instruction: a timing fact must
// never render as if it were a firmer commitment than its basis
// supports. Label text mirrors program_requirements.TimingBasis exactly.
const TIMING_BASIS_LABEL = {
  statutory_deadline: "Statutory deadline",
  official_target: "Official target",
  reported_practical: "Reported practical timing",
  estimate: "Estimate",
  unknown: "Unknown",
};

export function TimingFactValue({ fact }) {
  if (!fact) return <span className="text-tertiary">Not stated</span>;
  return (
    <span>
      {fact.value}
      <span className="text-tertiary small" style={{ marginLeft: 6 }}>
        ({TIMING_BASIS_LABEL[fact.basis] || fact.basis})
      </span>
    </span>
  );
}

// Recommendation confidence -> the globe/badge semantic tiers this
// product uses (gold/jade/silver/amber/red/charcoal). This is a display
// mapping only, over values the backend already computed.
export function confidenceTier(confidence) {
  switch (confidence) {
    case "high": return "jade";
    case "medium": return "silver";
    case "low": return "amber";
    default: return "charcoal";
  }
}

export function tierBadgeClass(tier) {
  return tier || "charcoal";
}

export function tierLabel(tier) {
  switch (tier) {
    case "gold": return "Best current recommendation";
    case "jade": return "Strong alternative";
    case "silver": return "Viable alternative";
    case "amber": return "Conditional / authority-dependent";
    case "red": return "Material blocker";
    default: return "Inactive";
  }
}

// Recommendation-confidence status (backend Phase 2). Maps the backend's
// deterministic status enum to a short producer-facing label + a tone class
// reused from the existing card palette (jade/silver/amber/charcoal). Never
// invents a status the backend didn't send.
export function confidenceStatusLabel(status) {
  switch (status) {
    case "CONFIRMED": return "Confirmed";
    case "PRICED": return "Priced · qualification not fully known";
    case "PRICED_BUT_QUALIFICATION_PENDING": return "Priced · qualification pending";
    case "CONDITIONAL": return "Conditional · mandatory gate unconfirmed";
    case "UNAVAILABLE": return "Unavailable · cannot be priced";
    case "UNKNOWN": return "Status unknown";
    default: return status || "";
  }
}

export function confidenceStatusTone(status) {
  switch (status) {
    case "CONFIRMED": return "jade";
    case "PRICED": return "silver";
    case "PRICED_BUT_QUALIFICATION_PENDING": return "amber";
    case "CONDITIONAL": return "amber";
    case "UNAVAILABLE": return "red";
    default: return "charcoal";
  }
}

// Standard geographic reference name for a jurisdiction code — same
// source data as JURISDICTION_COORDS, exposed for producer-facing labels.
export function jurisdictionName(code) {
  return JURISDICTION_COORDS[code]?.name || code;
}

// One shared flag mechanism for the whole app — standardized Unicode
// regional-indicator derivation (no asset/library dependency; the same
// technique already used ad hoc for the three FX_FLAGS in
// todayCompute.js, generalized here to any ISO2 rather than a hardcoded
// three-entry map). Sub-national jurisdictions (US-NY, CA-BC, AU-NSW, ...)
// have no flag of their own — this shows the PARENT country's flag, never
// a fabricated regional one. Unknown/empty input renders nothing (no
// placeholder flag invented for an unset nationality).
export function flagEmoji(code) {
  if (!code) return null;
  const iso2 = code.split("-")[0].toUpperCase();
  if (!/^[A-Z]{2}$/.test(iso2)) return null;
  const base = 0x1f1e6; // regional indicator "A"
  const chars = [...iso2].map((c) => base + (c.charCodeAt(0) - 65));
  return String.fromCodePoint(...chars);
}

// Turns a jurisdiction list like ["MU","BE"] into a readable structure
// name: the baseline jurisdiction plus any co-production partners.
export function structureLabel(codes = []) {
  if (codes.length === 0) return "—";
  if (codes.length === 1) return jurisdictionName(codes[0]);
  const [base, ...rest] = codes;
  return `${jurisdictionName(base)} with ${rest.map(jurisdictionName).join(" and ")} co-production`;
}

// Recommendation titles sometimes carry a raw internal token, e.g.
// "Resolve grey area: OPP-GREY-GA-INKIND-FMV". The real description field
// already restates the same fact in a full sentence ("Resolving
// 'GA-INKIND-FMV' could swing QPE on $625,000: Written EDB ruling that
// in-kind post-production FMV qualifies as QPE (Q1).") — this extracts
// the trailing human-readable clause after the last colon rather than
// inventing new copy. Falls back to the title when no such clause exists.
export function recommendationHeadline(rec) {
  // Only rewrite the title when it actually embeds a raw internal token
  // (e.g. "OPP-GREY-GA-INKIND-FMV") — most titles are already clean,
  // human-written sentences and should be left untouched.
  const hasRawToken = /\b[A-Z]{2,}(-[A-Z0-9]+){1,}\b/.test(rec.title);
  if (!hasRawToken) return rec.title;
  const desc = rec.description || "";
  const parts = desc.split(": ");
  const tail = parts[parts.length - 1];
  if (tail && tail.length > 12 && !/^[A-Z0-9-]+$/.test(tail)) return tail;
  return rec.title;
}

// Moved to programNames.js (plain .js, no JSX) so globeData.js — imported
// directly by `node --test` with no JSX transform — can use `programDisplay`
// for the Globe hover card without pulling in this file's JSX. Re-exported
// here unchanged so every existing `from "../lib/format"` caller is unaffected.
export { humanizeToken, programDisplay } from "./programNames.js";

// Canonical scenario display — the ONE place a structure's producer-facing
// title/subtitle is derived, shared by Workspace, Overview, Scenarios and
// Reports so no screen invents its own wording. Reads only real backend
// fields (primary_jurisdiction, participants, structure_type, segments) —
// never the internal engineering label, never fabricated data. The
// canonical structure_type/label/economics are untouched; this is
// presentation only.
export function scenarioDisplay(structure) {
  const participants = structure.participants || [];
  const primary = structure.primary_jurisdiction;
  const others = participants.filter((p) => p !== primary);

  let title;
  if (!primary && !participants.length) {
    title = structure.label; // defensive fallback — should not occur with real data
  } else if (structure.structure_type === "single_country" || structure.structure_type === "full_relocation") {
    // Frozen ui-baseline-v1 presentation: a single-jurisdiction card —
    // whether the baseline or a full relocation — is titled with the plain
    // jurisdiction name (prototype lanes name:"Mauritius"/"Malta"/"Ireland").
    // The structure_type is conveyed by the badge + subtitle, never by
    // prepending wording to the title. Reads canonical primary_jurisdiction.
    title = bestJurisdictionName(primary, structure);
  } else if (structure.structure_type === "component_relocation" && others.length) {
    title = `${bestJurisdictionName(primary, structure)} + ${others.map(jurName).join(" + ")}`;
  } else {
    title = participants.length
      ? participants.map((p) => bestJurisdictionName(p, structure)).join(" + ")
      : bestJurisdictionName(primary, structure);
  }

  const segments = structure.segments || [];
  const dominant = segments.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
  // Guaranteed floor rate as the headline number, with the actual modeled
  // ceiling spelled out (never just "(up to)" with no number) when a band
  // exists — matches Inspector.jsx's own rate presentation exactly. The
  // ranked NPC/incentive on this card is computed from the CEILING (the
  // canonical optimization contract: best-supported modeled, never the
  // floor), so the ceiling must be visible here, not only the floor.
  // programDisplay prefers the real canonical registry name
  // (structure.program_display_name, sourced from the backend's own
  // doctrine registry) over its small legacy hardcoded map — real for
  // any program the registry knows, never fabricated for one it doesn't.
  const subtitle = structure.is_fully_priced && dominant?.claims_incentive && dominant?.program_slug
    ? `${programDisplay(dominant.program_slug, structure.program_display_name)} · ${Math.round((dominant.rate_floor || 0) * 100)}%${dominant.is_band_ceiling ? ` (up to ${Math.round((dominant.rate_ceiling || 0) * 100)}%)` : ""}`
    : humanizeToken(structure.structure_type);

  return { title, subtitle, dominant };
}

// Workspace-only compact scenario identity — the previously approved
// compact card format ("🇲🇺 Mauritius" / "Up to 40%"), restored after the
// verbose "EDB Film Rebate · 30% (up to 40%)" program-mechanics presentation
// drifted in. Deliberately separate from scenarioDisplay above (still used
// by Overview/Scenarios/Reports, which DO want the program name) so this
// change is scoped to Workspace only. Reuses the same existing flagEmoji /
// jurisdictionName helpers — no new country/flag mapping. Detailed program
// mechanics belong in Inspector, not the primary card identity.
export function compactScenarioIdentity(structure) {
  const participants = structure.participants || [];
  const primary = structure.primary_jurisdiction;
  const codes = participants.length ? participants : (primary ? [primary] : []);
  const flags = codes.map(flagEmoji).filter(Boolean).join(" ");
  // bestJurisdictionName (never the Globe's geo-hub map alone) — see its
  // own header comment for why: a sub-national code's real registry name
  // ("Australia — New South Wales") is not its geographic hub city
  // ("Sydney"). structure.jurisdiction_display_name is the real,
  // canonical Jurisdiction-table name for structure.primary_jurisdiction.
  const jurisdictionName_ = codes.length
    ? codes.map((c) => bestJurisdictionName(c, structure)).join(" + ")
    : (structure.label || "—");

  // Workspace Top-6/Data Truthfulness: the jurisdiction name alone
  // collapses genuinely distinct programs in the same country into
  // identical-looking cards (e.g. Australia's Location Offset and PDV
  // Offset, or three different states' own PDV rebates). The real
  // program name already exists in the canonical doctrine registry
  // (structure.program_display_name) — append it whenever this
  // structure's own jurisdiction name is not already unique enough to
  // stand alone, i.e. whenever a real program name exists at all for a
  // single-program structure (a multi-program stack keeps its plain
  // jurisdiction title; its programs are enumerated in the card body).
  const singleProgram = (structure.program_slugs || []).length <= 1;
  // Falls back through programDisplay's own legacy map/humanization for
  // a program_slug the backend doctrine registry doesn't (yet) cover —
  // e.g. the original four "frozen ui-baseline-v1" programs (Little
  // Utopia/FVD's own) predate that registry. Never blank for a
  // single-program structure that has ANY program_slug at all.
  const programName = structure.program_display_name
    || (structure.program_slug ? programDisplay(structure.program_slug) : null);
  const name = singleProgram && programName
    ? `${jurisdictionName_} — ${programName}`
    : jurisdictionName_;

  // The best real modeled rate anywhere in the structure — the highest
  // rate_ceiling (falling back to rate_floor) across every incentive-
  // claiming segment, not just the biggest-QPE one. A component
  // structure's headline is its best-supported ceiling (e.g. Mauritius +
  // Saudi Arabia tops out at Saudi's real 60% modeled rate, not Mauritius's
  // smaller 40%), matching the same ceiling-not-floor convention Inspector
  // and the optimizer's own ranking already use. When the engine resolved
  // one EXACT rate (floor == ceiling — the common case for a flat
  // statutory program, not a band), the label states it plainly rather
  // than "Up to X%", which implies a range that does not exist here.
  const segments = structure.segments || [];
  const claiming = segments.filter((sg) => sg.claims_incentive);
  const floors = claiming.map((sg) => sg.rate_floor).filter((r) => r != null);
  const ceilings = claiming.map((sg) => sg.rate_ceiling ?? sg.rate_floor).filter((r) => r != null);
  const ceiling = ceilings.length ? Math.max(...ceilings) : null;
  const floor = floors.length ? Math.min(...floors) : null;
  const isExactRate = ceiling != null && floor != null && Math.round(floor * 10000) === Math.round(ceiling * 10000);
  const subtitle = ceiling != null
    ? (isExactRate ? `${Math.round(ceiling * 100)}%` : `Up to ${Math.round(ceiling * 100)}%`)
    : humanizeToken(structure.structure_type);

  return { flags, name, subtitle };
}

// Real AccountQualification.state values -> plain-language label + tier.
export function accountStateLabel(state) {
  switch (state) {
    case "qualifies": return { label: "Qualifies", tier: "jade" };
    case "structuring_opportunity": return { label: "Structuring opportunity", tier: "blue" };
    case "grey_area_requires_authority": return { label: "Needs authority decision", tier: "amber" };
    case "excluded": return { label: "Excluded from QPE", tier: "silver" };
    case "not_applicable": return { label: "Not applicable", tier: "charcoal" };
    default: return { label: state, tier: "charcoal" };
  }
}

// Grey-area / question status -> a plain-language phrase and its tier.
export function questionStatusLabel(status) {
  if (!status) return { label: "Unresolved", tier: "amber" };
  if (status === "open") return { label: "Unresolved", tier: "amber" };
  if (status.startsWith("resolved")) return { label: "Resolved", tier: "jade" };
  return { label: status.replace(/_/g, " "), tier: "silver" };
}
