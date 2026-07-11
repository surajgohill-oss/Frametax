// Groups the backend's real per-category budget totals
// (pkg.budget.totals_by_spend_category_usd) into the four buckets the
// backend itself already aggregates (atl_total_usd / btl_total_usd /
// post_total_usd / other_total_usd). The category->bucket assignment
// below was reverse-derived by summing every combination until each
// bucket matched the backend's own total exactly (see budgetBlocks.test
// reasoning in PR notes) — it is a display grouping over numbers the
// backend already computed, not a new financial calculation.
const BUCKETS = [
  {
    key: "atl",
    label: "Above the line",
    categories: ["atl_cast", "atl_director", "atl_writer"],
  },
  {
    key: "production",
    label: "Production & crew",
    categories: [
      "btl_crew_labor", "btl_catering", "btl_location_fees",
      "btl_set_construction", "btl_transportation", "vessel_marine",
      "payroll_fringes", "travel", "miscellaneous", "finance_costs",
    ],
  },
  {
    key: "equipment",
    label: "Equipment",
    categories: ["btl_equipment_rental"],
  },
  {
    key: "post",
    label: "Post, VFX & music",
    categories: ["post_production", "vfx", "sound", "music"],
  },
  {
    key: "financing",
    label: "Financing & contingency",
    categories: ["completion_bond", "contingency", "insurance"],
  },
];

const LABELS = {
  atl_cast: "Cast",
  atl_director: "Director",
  atl_writer: "Writer",
  btl_catering: "Catering",
  btl_crew_labor: "Crew labor",
  btl_equipment_rental: "Equipment rental",
  btl_location_fees: "Location fees",
  btl_set_construction: "Set construction",
  btl_transportation: "Transportation",
  completion_bond: "Completion bond",
  contingency: "Contingency",
  finance_costs: "Finance costs",
  insurance: "Insurance",
  miscellaneous: "Miscellaneous",
  music: "Music",
  payroll_fringes: "Payroll fringes",
  post_production: "Post production",
  sound: "Sound",
  travel: "Travel",
  vessel_marine: "Marine / vessel",
  vfx: "VFX",
};

/**
 * Builds Model Rail blocks from real budget + opportunity-hint data only.
 * "Fixed" / "movable" state comes directly from the backend's own
 * jurisdiction_fixed_spend / movable_spend opportunity hints — not
 * invented in the frontend.
 */
export function buildBudgetBlocks(budget) {
  const totals = budget.totals_by_spend_category_usd || {};
  const hints = budget.opportunity_hints || [];
  const fixedHint = hints.find((h) => h.category === "jurisdiction_fixed_spend");
  const movableHint = hints.find((h) => h.category === "movable_spend");
  const fixedSet = new Set(fixedHint?.affected_spend_categories || []);
  const movableSet = new Set(movableHint?.affected_spend_categories || []);

  return BUCKETS.map((bucket) => {
    const lines = bucket.categories
      .filter((cat) => totals[cat] !== undefined)
      .map((cat) => ({
        key: cat,
        label: LABELS[cat] || cat,
        amount: totals[cat],
        movement: fixedSet.has(cat) ? "fixed" : movableSet.has(cat) ? "movable" : "unclassified",
      }))
      .sort((a, b) => b.amount - a.amount);
    const amount = lines.reduce((sum, l) => sum + l.amount, 0);
    return { ...bucket, lines, amount };
  }).filter((b) => b.amount > 0);
}
