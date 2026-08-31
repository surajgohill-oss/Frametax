import { useState } from "react";
import { Money } from "../lib/format";
import { postProjectAssumptions } from "../api";

// Production Page Integrity — Generic Contingency Expected-Utilization
// Control.
//
// Restores the producer-facing counterpart to a fact
// (contingency_expected_utilization_pct) that has always been read by the
// backend (canonical_project_economics.build_project_economic_inputs ->
// qualification_derivation.derive_qualification_register) but never had a
// UI to set it — see CAPABILITY_LEDGER.md, "Production Page Integrity
// Closeout". Generic across every project: no project id or title is ever
// read here. Absent a value, the reserve is a real GREY_AREA_REQUIRES_
// AUTHORITY state (never silently defaulted to 0% or 100% — see
// qualification_derivation.py's own existing, unchanged doctrine).
//
// Reserve $ amount is read from the SAME generic budget-composition data
// BudgetComposition.jsx uses (pkg.budget.totals_by_spend_category_usd.
// contingency) — never a second contingency-detection implementation.
const OPTIONS = [0, 25, 50, 75, 100];

export default function ContingencyControl({ projectId, budget, currentPct, onSaved }) {
  const reserveUsd = budget?.totals_by_spend_category_usd?.contingency ?? 0;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // reserve of $0 means this project's budget has no contingency line at
  // all — nothing to elect a utilization percentage over.
  if (!reserveUsd) return null;

  async function choose(pct) {
    if (saving) return;
    setSaving(true);
    setError(null);
    try {
      await postProjectAssumptions(projectId, { contingency_expected_utilization_pct: pct });
      onSaved?.();
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="brail-panel ccx-panel">
      <div className="pd-section-label">Contingency</div>

      <div className="brail-headline">
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Contingency reserve</span>
          <span className="mono brail-headline-v"><Money value={reserveUsd} /></span>
        </div>
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Expected utilization</span>
          <span className="mono brail-headline-v">{currentPct == null ? "Not set" : `${currentPct}%`}</span>
        </div>
      </div>

      <div className="ccx-options">
        {OPTIONS.map((pct) => (
          <button
            key={pct}
            className={`ccx-opt ${currentPct === pct ? "active" : ""}`}
            disabled={saving}
            onClick={() => choose(pct)}
          >
            {pct}%
          </button>
        ))}
      </div>

      <p className="text-tertiary small" style={{ marginTop: 10 }}>
        Expected percentage of the budgeted contingency likely to be deployed. This does not mean the entire
        utilized amount automatically qualifies for incentives — qualification remains program/jurisdiction
        dependent.
      </p>
      {currentPct == null && (
        <p className="text-tertiary small" style={{ marginTop: 4 }}>
          No election yet — the reserve is treated as a genuinely unresolved amount, never assumed at either 0%
          or 100%.
        </p>
      )}
      {error && <p className="small" style={{ marginTop: 6, color: "var(--red, #b3261e)" }}>{error}</p>}
    </section>
  );
}
