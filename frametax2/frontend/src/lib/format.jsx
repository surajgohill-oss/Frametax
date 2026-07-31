import { JURISDICTION_COORDS } from "./jurisdictions";
import { humanizeToken, programDisplay } from "./programNames.js";

const jurName = (code) => JURISDICTION_COORDS[code]?.name || code || "—";

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
    title = jurName(primary);
  } else if (structure.structure_type === "component_relocation" && others.length) {
    title = `${jurName(primary)} + ${others.map(jurName).join(" + ")}`;
  } else {
    title = participants.length ? participants.map(jurName).join(" + ") : jurName(primary);
  }

  const segments = structure.segments || [];
  const dominant = segments.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
  // Guaranteed floor rate as the headline number, with the actual modeled
  // ceiling spelled out (never just "(up to)" with no number) when a band
  // exists — matches Inspector.jsx's own rate presentation exactly. The
  // ranked NPC/incentive on this card is computed from the CEILING (the
  // canonical optimization contract: best-supported modeled, never the
  // floor), so the ceiling must be visible here, not only the floor.
  const subtitle = structure.is_fully_priced && dominant?.claims_incentive && dominant?.program_slug
    ? `${programDisplay(dominant.program_slug)} · ${Math.round((dominant.rate_floor || 0) * 100)}%${dominant.is_band_ceiling ? ` (up to ${Math.round((dominant.rate_ceiling || 0) * 100)}%)` : ""}`
    : humanizeToken(structure.structure_type);

  return { title, subtitle, dominant };
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
