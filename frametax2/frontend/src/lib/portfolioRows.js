// The ONE place aggregate-payload rows become resolved Company Globe rows: the live leading selection (a saved "Set as Leading"
// that is still pending or just committed, passed in so this stays a pure module) overrides the payload's own leader for that project only. Company Globe, its
// legend, the side list and the sidebar mini-globe all read these rows.
import { principalOf } from "./globeStructure.js";

export function resolvePortfolioRow(row, selection = null) {
  const structure = selection ? selection.structure : row.leading?.structure ?? null;
  return {
    project: { id: row.project_id, title: row.title, lifecycle: row.lifecycle, is_served_production: true },
    grossBudgetUsd: row.gross_budget_usd, homeCode: row.home_code, structure,
    principal: structure ? principalOf(structure) : row.baseline_jurisdiction,
    selectionKnown: selection ? !!selection.selectionKnown : true,
    userSelected: selection ? !!selection.userSelected : !!row.leading?.user_selected,
    unavailable: selection ? !!selection.unavailable : !!row.leading?.unavailable,
  };
}

export const portfolioRows = (portfolio, getSelection = () => null) =>
  (portfolio?.projects || []).map((row) => resolvePortfolioRow(row, getSelection(row.project_id)));
