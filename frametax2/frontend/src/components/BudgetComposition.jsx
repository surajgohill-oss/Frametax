import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Money } from "../lib/format";
import { humanizeToken } from "../lib/programNames.js";

// Production Page Integrity — Overview Budget Breakdown.
//
// This is the project's REAL, imported budget composition — every canonical
// SpendCategory the classifier already assigns to each BudgetLineItem
// (app/models/enums.py, applied by classify_budget_line_items.py), summed
// straight from pkg.budget.totals_by_spend_category_usd /
// pkg.budget.line_items. It is deliberately populated for EVERY project,
// including one whose own base jurisdiction isn't priced yet (Lips Like
// Sugar, Bad Hombres) — unlike BudgetRail's account blocks, this panel never
// depends on pkg.register (a jurisdiction-pricing-derived source that is
// empty exactly when a production's own home jurisdiction can't be priced).
//
// Deliberately DISTINCT from BudgetRail ("Modeled Economics" — Credit / NPC
// / Finance Costs / Adjustments, all a function of the ACTIVE STRUCTURE):
// this panel shows only what the imported document itself says, with no
// jurisdiction, structure, or incentive-program dependency at all. No new
// taxonomy is introduced — SpendCategory is the one canonical grouping the
// codebase already assigns to every line, reused here unchanged.
//
// SUM OF DISPLAYED CATEGORIES = production.gross_budget_usd (the document's
// own declared grand total) for every real budget seen so far; the rare
// case where a document's OWN stated total doesn't equal the sum of its own
// extracted leaf lines is production.budget_reconciliation's job to surface
// (a real gap in the source document, e.g. a total-only figure never broken
// into its own leaf line) — never silently redistributed here to force a
// match.
function categoryLabel(cat) {
  const words = humanizeToken(cat || "miscellaneous");
  return words.replace(/^Atl\b/, "ATL").replace(/^Btl\b/, "BTL");
}

function CategoryBlock({ category, amount, lines, onSelectLine }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="brail-block">
      <button className="brail-header" onClick={() => setOpen((o) => !o)}>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        <span className="brail-name">{categoryLabel(category)}</span>
        <span className="brail-amount mono"><Money value={amount} /></span>
      </button>
      {open && (
        <div className="brail-lines">
          {lines.map((line) => (
            <button
              key={line.line_id}
              className="brail-line"
              onClick={() => onSelectLine?.(line)}
            >
              {/* line.description already carries its own leading account
                  code verbatim from the source document (e.g. "1100
                  SCRIPT") — never re-prepend line.account_code here, or
                  every row doubles it ("1100 1100 SCRIPT"). */}
              <span className="brail-line-name">{line.description}</span>
              <span className="mono"><Money value={line.amount_usd} /></span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function BudgetComposition({ production, budget, onSelectLine }) {
  const lineItems = budget?.line_items || [];
  const totalsByCategory = budget?.totals_by_spend_category_usd || {};

  const categories = useMemo(() => {
    const linesByCategory = new Map();
    for (const line of lineItems) {
      const cat = line.spend_category || "miscellaneous";
      if (!linesByCategory.has(cat)) linesByCategory.set(cat, []);
      linesByCategory.get(cat).push(line);
    }
    return Object.entries(totalsByCategory)
      .map(([category, amount]) => ({
        category,
        amount,
        lines: (linesByCategory.get(category) || []).sort((a, b) => (b.amount_usd || 0) - (a.amount_usd || 0)),
      }))
      .sort((a, b) => b.amount - a.amount);
    // budget is the stable prop identity (a fresh object per fetch, not per
    // render) — depending on it directly instead of the two derived
    // locals avoids an exhaustive-deps warning without losing correctness.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [budget]);

  const categorySum = useMemo(
    () => Math.round(categories.reduce((sum, c) => sum + (c.amount || 0), 0) * 100) / 100,
    [categories],
  );

  const recon = production?.budget_reconciliation;

  // No budget imported for this project yet, or no leaf lines extracted —
  // never render an empty/misleading breakdown.
  if (lineItems.length === 0) return null;

  return (
    <section className="brail-panel bcomp-panel">
      <div className="pd-section-label">Budget composition</div>

      <div className="brail-headline">
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Total budget</span>
          <span className="mono brail-headline-v"><Money value={production?.gross_budget_usd} /></span>
        </div>
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Categories</span>
          <span className="mono brail-headline-v">{categories.length}</span>
        </div>
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Leaf lines</span>
          <span className="mono brail-headline-v">{lineItems.length}</span>
        </div>
      </div>

      {categories.map((c) => (
        <CategoryBlock key={c.category} category={c.category} amount={c.amount} lines={c.lines} onSelectLine={onSelectLine} />
      ))}

      <div className="brail-total">
        <span>Sum of displayed categories</span>
        <span className="mono brail-total-value"><Money value={categorySum} /></span>
      </div>

      {recon?.note && (
        <p className="text-tertiary small" style={{ marginTop: 10 }}>{recon.note}</p>
      )}
    </section>
  );
}
