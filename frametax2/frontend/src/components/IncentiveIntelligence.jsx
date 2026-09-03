import { CompactMoney, scenarioDisplay, compactIncentiveRate, confidenceStatusLabel, confidenceStatusTone } from "../lib/format";
import { classifyStructure, selectTopFour, cardStatus, qpeOf, isBaselineStructure } from "../lib/productionOptions";

// Overview center-column, directly beneath Project Globe — the approved
// Top Four decision surface (CineGlobe Overview / Workspace final repair
// closeout, 2026-09-03): exactly four cards, one row on desktop. Card
// 1-3 are the three highest-ranked currently-modeled structures; Card 4
// is the highest-value legitimate potentially-optimized opportunity not
// already shown, or the canonical next-best modeled structure when none
// exists — selection lives in lib/productionOptions.js (unit-tested
// there); this file only formats and renders, reusing the existing
// .ii-* card vocabulary (CardShell-style accent bar + metrics grid)
// unchanged in geometry.
//
// Status line (immediately beneath the jurisdiction name) and the
// compact rate line (never a program name — see lib/format.jsx's
// compactIncentiveRate) are the two changes to the card body; nothing
// else about card width/height/padding/metrics moved.

function OptionCard({ structure, cardIndex, leadingId, baseNpc, onClick }) {
  const classification = classifyStructure(structure);
  const { title } = scenarioDisplay(structure);
  const status = cardStatus(structure, cardIndex, leadingId);
  const isOpportunity = !!structure.__isOpportunity;
  // Opportunity cards (Card 4 when it represents a real disclosed
  // fund/treaty pathway, not yet-earned economics) must never format
  // their figure through compactIncentiveRate — that function only ever
  // describes a structure's OWN resolved rate_floor/rate_ceiling, and
  // applying it here would misrepresent a disclosed cap as an earned
  // rate (item 11.D/E). Show the real disclosed cap when one exists,
  // otherwise the honest "not yet modeled" state — never a fabricated %.
  const rateLine = isOpportunity
    ? (structure.__potentialUsd ? <>Potential up to <CompactMoney value={structure.__potentialUsd} /></> : "Potential — not yet modeled")
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
      </div>
    </Tag>
  );
}

export default function IncentiveIntelligence({ allocated, leadingStructureId, onSelect }) {
  const options = selectTopFour(allocated);
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
              leadingId={leadingStructureId}
              baseNpc={baseNpc}
              onClick={onSelect ? () => onSelect(s) : undefined}
            />
          ))}
        </div>
      )}
    </section>
  );
}
