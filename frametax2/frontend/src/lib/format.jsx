import { JURISDICTION_COORDS } from "./jurisdictions";

// Pure display formatting only — no business logic, no derived facts.

export function Money({ value }) {
  if (value === null || value === undefined) return <span className="text-tertiary">—</span>;
  return <span className="mono">${Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>;
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
