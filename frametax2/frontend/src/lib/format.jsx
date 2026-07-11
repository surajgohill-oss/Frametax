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
