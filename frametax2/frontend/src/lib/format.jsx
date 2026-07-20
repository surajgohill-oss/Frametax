import { JURISDICTION_COORDS } from "./jurisdictions";

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

// Formats a raw snake_case engine/module name for secondary metadata —
// e.g. "production_recommendation_engine" -> "Production recommendation".
// Pure string formatting, never invents which engines are affected.
export function humanizeToken(token) {
  const words = token.replace(/_/g, " ").replace(/\b(engine|model|discovery)\b/g, "").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

// Producer-facing incentive-program names — the frozen artifact's
// terminology contract (ui-baseline-v1) for the four executable programs.
// Presentation vocabulary only: never a rate, cap, or economic value.
// Unknown slugs fall back to plain humanization, never invented names.
const PROGRAM_NAMES = {
  mu_edb_incentive: "EDB Film Rebate",
  mt_mfc_rebate: "Malta Cash Rebate",
  ie_section_481: "Section 481",
  gr_cash_rebate: "Greece Cash Rebate",
};
export function programDisplay(slug) {
  if (!slug) return null;
  return PROGRAM_NAMES[slug] || humanizeToken(slug);
}

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
  } else if (structure.structure_type === "single_country") {
    title = jurName(primary);
  } else if (structure.structure_type === "full_relocation") {
    title = `Relocate to ${jurName(primary)}`;
  } else if (structure.structure_type === "component_relocation" && others.length) {
    title = `${jurName(primary)} + ${others.map(jurName).join(" + ")}`;
  } else {
    title = participants.length ? participants.map(jurName).join(" + ") : jurName(primary);
  }

  const segments = structure.segments || [];
  const dominant = segments.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
  const subtitle = structure.is_fully_priced && dominant?.claims_incentive && dominant?.program_slug
    ? `${programDisplay(dominant.program_slug)} · ${Math.round((dominant.rate_floor || 0) * 100)}%${dominant.is_band_ceiling ? " (up to)" : ""}`
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
