import { useState } from "react";
import { Money } from "../lib/format";
import { postProjectAssumptions, beginEvaluation } from "../api";

// Compact Contingency Expected-Utilization control — Production Overview +
// Project Globe UI regression repair, Section 5: lives INSIDE the Budget
// Rail (never a standalone module) as a single line — reserve amount, then a
// short dropdown, matching the rest of this rail's density. Same real,
// already-implemented persistence/API this control has used since it was
// first built (POST /projects/{id}/assumptions) — this batch only moves
// where it renders, never what it does or how it's stored.
const CONTINGENCY_OPTIONS = [0, 25, 50, 75, 100];

export function ContingencyLine({ projectId, reserveUsd, currentPct, onSaved, planning }) {
  const [saving, setSaving] = useState(false);
  if (!reserveUsd) return null;

  async function choose(e) {
    const pct = e.target.value === "" ? null : Number(e.target.value);
    if (saving) return;
    setSaving(true);
    try {
      await postProjectAssumptions(projectId, { contingency_expected_utilization_pct: pct });
      // Producer Display Names + Budget Rail User Assumptions closeout:
      // GET-side reads (useCineGlobe's refetch, called via onSaved below)
      // serve the LAST PERSISTED evaluation row — they never re-run
      // pricing themselves. contingency_expected_utilization_pct is
      // already part of the evaluation cache fingerprint, so without an
      // explicit re-evaluation here the served NPC/economics would stay
      // stale after a save until some unrelated future evaluation
      // happened to run. beginEvaluation is the SAME existing, generic
      // "Begin Evaluation" entry point (idempotent per fingerprint) —
      // no new economics, no new endpoint.
      await beginEvaluation(projectId);
      onSaved?.();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="brail-block">
      <div className="brail-header brail-static brail-contingency-row" title="Expected use of contingency.">
        <span style={{ width: 13 }} />
        <span className="brail-name">Contingency</span>
        <span className="mono brail-amount">
          <Money value={reserveUsd} bare />
        </span>
        <span className="brail-contingency-use">
          <span className="text-tertiary">Use</span>
          <select
            className="brail-contingency-select"
            value={currentPct ?? ""}
            disabled={saving}
            onChange={choose}
          >
            <option value="">—</option>
            {CONTINGENCY_OPTIONS.map((pct) => (
              <option key={pct} value={pct}>{pct}%</option>
            ))}
          </select>
        </span>
      </div>
      {/* Original gross and the reserve above are never rewritten; the election only sets the PLANNED cost used for NPC
          (undeployed reserve removed once). The jurisdiction QPE rules separately qualify the deployed reserve. */}
      {planning?.state === "ELECTED" ? (
        <div className="brail-header brail-static brail-contingency-row" title={planning.note}>
          <span style={{ width: 13 }} />
          <span className="brail-name text-tertiary">Planned cost (undeployed <Money value={planning.undeployed_reserve_usd} bare /> removed)</span>
          <span className="mono brail-amount"><Money value={planning.planned_cost_usd} bare /></span>
        </div>
      ) : (
        <div className="brail-header brail-static brail-contingency-row" title={planning?.note}>
          <span style={{ width: 13 }} />
          <span className="brail-name text-tertiary">No utilization stated: planned cost = full budget</span>
        </div>
      )}
    </div>
  );
}

