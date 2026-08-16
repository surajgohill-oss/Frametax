import { Money, scenarioDisplay, confidenceStatusLabel, confidenceStatusTone } from "../lib/format";
import { classifyStructure, selectTopOptions, qpeOf, isBaselineStructure } from "../lib/productionOptions";

// Overview center-column, beneath Project Globe — "which production
// structures should I seriously consider?" Overview UI contract (this
// batch): replaced the previous 4-slot per-jurisdiction representative
// grid (Recommended/Alternatives/Co-Production Opportunities/Excluded)
// with up to SIX structure-level option cards. Selection/classification
// logic lives in lib/productionOptions.js (unit-tested there); this file
// only formats and renders, reusing the existing .ii-* card vocabulary
// (CardShell-style accent bar + metrics grid) unchanged.

function OptionCard({ structure, baseNpc, onClick }) {
  const classification = classifyStructure(structure);
  const { title, subtitle } = scenarioDisplay(structure);
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
        <div className="ii-head">
          <span className="ii-cat-label">{classification.label}</span>
        </div>
        <div className="ii-country">
          <span className="ii-country-name">{title}</span>
        </div>
        {subtitle && <div className="ii-structure">{subtitle}</div>}

        <div className="ii-metrics">
          <div className="ii-metric">
            <span className="ii-metric-label">Gross Budget</span>
            <span className="ii-metric-value mono">
              {structure.gross_budget_usd != null ? <Money value={structure.gross_budget_usd} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Qualified Spend</span>
            <span className="ii-metric-value mono">
              {structure.is_fully_priced ? <Money value={qpeOf(structure)} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Incentive</span>
            <span className="ii-metric-value mono">
              {structure.selected_incentive_usd != null ? <Money value={structure.selected_incentive_usd} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Net Production Cost</span>
            <span className="ii-metric-value mono">
              {npc != null ? <Money value={npc} /> : "Not priced"}
            </span>
          </div>
        </div>

        {diff != null && (
          <div className="ii-related">
            <span className="ii-related-label">Vs. current / base</span>
            <span className="ii-related-list">
              {diff > 0 ? "+" : ""}<Money value={diff} />
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

export default function IncentiveIntelligence({ allocated, onSelect }) {
  const options = selectTopOptions(allocated);
  const baseline = allocated?.structures?.find(isBaselineStructure);
  const baseNpc = baseline?.npc_with_adjustments_usd ?? null;

  return (
    <section className="ovx-sec ii-section">
      <div className="oh"><b>Production Options</b><span className="n">{options.length}</span></div>
      {options.length === 0 ? (
        <p className="empty-state">No priced production structures available yet for this production.</p>
      ) : (
        <div className="ii-grid">
          {options.map((s) => (
            <OptionCard
              key={s.structure_id}
              structure={s}
              baseNpc={baseNpc}
              onClick={onSelect ? () => onSelect(s) : undefined}
            />
          ))}
        </div>
      )}
    </section>
  );
}
