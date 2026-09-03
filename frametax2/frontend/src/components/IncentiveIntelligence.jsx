import { CompactMoney, scenarioDisplay, compactIncentiveRate, confidenceStatusLabel, confidenceStatusTone, hasAdministrativeAllocationRisk } from "../lib/format";
import { classifyStructure, selectAnchorLeadingOptimized, cardStatus, qpeOf, isBaselineStructure } from "../lib/productionOptions";

// Overview center-column, directly beneath Project Globe — the approved
// 2x2 anchor/scenario decision surface (history-based restoration,
// 2026-09-03, root authority: commit ec283e5's real "Incentive
// Intelligence 2x2 grid" — the only genuine 2-row/2-column grid this
// surface has ever used; its category semantics were Recommended/
// Alternatives/Co-Production Opportunities/Excluded, reinterpreted here
// against the canonical anchor/current-production data model
// (isBaselineStructure/is_baseline) rather than inventing a second
// concept). Selection lives in lib/productionOptions.js's
// selectAnchorLeadingOptimized (unit-tested there); this file only
// formats and renders, reusing the existing .ii-* card vocabulary
// (CardShell-style accent bar + metrics grid) unchanged in geometry.
//
// Card 1 — ANCHOR (the production's real current/base structure).
// Cards 2-3 — LEADING (the two highest-ranked alternatives, Anchor
// excluded).
// Card 4 — OPTIMIZED (the strongest legitimate optimization opportunity
// not already shown, or the canonical next-best alternative when none
// exists — never fabricated).

function OptionCard({ structure, cardIndex, baseNpc, onClick }) {
  const classification = classifyStructure(structure);
  const { title } = scenarioDisplay(structure);
  const status = cardStatus(structure, cardIndex);
  const isOpportunity = !!structure.__isOpportunity;
  // Opportunity cards (Card 4 when it represents a real disclosed
  // fund/treaty pathway, not yet-earned economics) must never format
  // their figure through compactIncentiveRate — that function only ever
  // describes a structure's OWN resolved rate_floor/rate_ceiling, and
  // applying it here would misrepresent a disclosed cap as an earned
  // rate. F#K Valentine's Day economic/semantic regression fix
  // (2026-09-03): this used to sum every disclosed fund's own
  // documented_cap_usd and show "Potential up to $X" — for a real
  // production this summed five unrelated national funds' own per-
  // project ceilings (sized for productions much larger than this one)
  // into a figure ($16.1M) that exceeded the production's entire $4.5M
  // source budget by more than 3x. A program's own cap is real and
  // disclosable but is never this project's calculated potential (item
  // 5.C/5.D) — disclose the real fund COUNT/NAMES instead, never a
  // fabricated or summed dollar figure.
  const rateLine = isOpportunity
    ? (structure.__fundCount
        ? `${structure.__fundCount} discretionary fund${structure.__fundCount === 1 ? "" : "s"} available — not a guaranteed or project-scaled figure`
        : "Potential — not yet modeled")
    : compactIncentiveRate(structure);
  const npc = structure.npc_with_adjustments_usd;
  const diff = npc != null && baseNpc != null && !isBaselineStructure(structure) ? npc - baseNpc : null;
  const clickable = !!onClick;
  const Tag = clickable ? "button" : "div";

  return (
    <Tag
      className={`ii-card ii-${classification.accent}${clickable ? " ii-clickable" : ""}`}
      onClick={onClick}
      type={clickable ? "button" : undefined}
    >
      <div className="ii-card-accent" aria-hidden="true" />
      <div className="ii-card-body">
        <div className="ii-country">
          <span className="ii-country-name">{title}</span>
        </div>
        <div className="ii-status">{status}</div>
        {rateLine && <div className="ii-structure">{rateLine}</div>}

        <div className="ii-metrics">
          <div className="ii-metric">
            <span className="ii-metric-label">Gross Budget</span>
            <span className="ii-metric-value mono">
              {structure.gross_budget_usd != null ? <CompactMoney value={structure.gross_budget_usd} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Qualified Spend</span>
            <span className="ii-metric-value mono">
              {structure.is_fully_priced ? <CompactMoney value={qpeOf(structure)} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Incentive</span>
            <span className="ii-metric-value mono">
              {structure.selected_incentive_usd != null ? <CompactMoney value={structure.selected_incentive_usd} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Net Production Cost</span>
            <span className="ii-metric-value mono">
              {npc != null ? <CompactMoney value={npc} /> : "Not priced"}
            </span>
          </div>
        </div>

        {diff != null && (
          <div className="ii-related">
            <span className="ii-related-label">Vs. current / base</span>
            <span className="ii-related-list">
              {diff > 0 ? "+" : ""}<CompactMoney value={diff} />
            </span>
          </div>
        )}

        {structure.confidence_status && (
          <div className="ii-program">
            <span className={`badge ${confidenceStatusTone(structure.confidence_status)}`}>
              {confidenceStatusLabel(structure.confidence_status)}
            </span>
          </div>
        )}

        {/* F#K item 3: real, backend-disclosed administrative/discretionary
            allocation risk (award-authority discretion, competitive/
            capacity-limited allocation, or a mandatory preapproval step).
            A structure carrying this must never present as a clean,
            unconditional deterministic winner — generic across every
            jurisdiction/program, see hasAdministrativeAllocationRisk. */}
        {hasAdministrativeAllocationRisk(structure) && (
          <div className="ii-program">
            <span className="badge amber">⚠ Discretionary / preapproval required</span>
          </div>
        )}
      </div>
    </Tag>
  );
}

export default function IncentiveIntelligence({ allocated, onSelect }) {
  const options = selectAnchorLeadingOptimized(allocated);
  const baseline = allocated?.structures?.find(isBaselineStructure);
  const baseNpc = baseline?.npc_with_adjustments_usd ?? null;

  return (
    <section className="ovx-sec ii-section">
      <div className="oh"><b>Top Structures</b><span className="n">{options.length}</span></div>
      {options.length === 0 ? (
        <p className="empty-state">No priced production structures available yet for this production.</p>
      ) : (
        <div className="ii-grid">
          {options.map((s, i) => (
            <OptionCard
              key={s.structure_id}
              structure={s}
              cardIndex={i}
              baseNpc={baseNpc}
              onClick={onSelect ? () => onSelect(s) : undefined}
            />
          ))}
        </div>
      )}
    </section>
  );
}
