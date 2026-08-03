import { Money, flagEmoji, humanizeToken, jurisdictionName } from "../lib/format";
import { presentExclusionReason } from "../lib/globeHoverFormat";
import { GLOBE_SEMANTIC } from "../lib/globeData";

// Overview center-column, beneath Project Globe (Batch 2). Exactly four
// cards, one per canonical semantic category (Recommended / Alternatives /
// Co-Production Opportunities / Excluded) — the SAME categories, hex
// family and per-jurisdiction data (`buildCountryHoverData`) the Globe
// itself renders. This is a second VIEW of that data, never a second
// derivation of it.
//
// A representative jurisdiction is picked per category by Overview.jsx
// (see `pickRepresentatives`) and passed in here already resolved — this
// component only formats and renders. Co-Production Opportunities is
// explicitly allowed to be null: this production's real optimizer output
// has zero amber jurisdictions (confirmed live, see GLOBE_FREEZE_MANIFEST's
// Phase 3B ledger — the winning structure for every jurisdiction is the
// single-participant one, which always outranks the multi-participant
// component-relocation structure). Showing an honest "not currently
// available" state here is the CORRECT behavior for that finding, not a
// bug — the alternative (fabricating an amber card, or silently reusing
// the fixture in production) is exactly what this batch's instructions
// forbid.

const CATEGORY_ORDER = ["gold", "jade", "amber", "silver"];

function CardShell({ slot, children, onClick }) {
  const clickable = !!onClick;
  const Tag = clickable ? "button" : "div";
  return (
    <Tag
      className={`ii-card ii-${slot}${clickable ? " ii-clickable" : ""}`}
      onClick={onClick}
      type={clickable ? "button" : undefined}
    >
      <div className="ii-card-accent" aria-hidden="true" />
      <div className="ii-card-body">{children}</div>
    </Tag>
  );
}

function PopulatedCard({ entry, onClick }) {
  const meta = GLOBE_SEMANTIC[entry.status];
  const flag = flagEmoji(entry.jurisdictionCode);
  const pctOfGross =
    entry.segmentIncentiveUsd != null && entry.grossBudgetUsd
      ? `${((entry.segmentIncentiveUsd / entry.grossBudgetUsd) * 100).toFixed(1)}%`
      : null;

  return (
    <CardShell slot={entry.status} onClick={onClick}>
      <div className="ii-head">
        <span className="ii-cat-label">{meta.fullLabel}</span>
        {entry.role && <span className="ii-role">{entry.role}</span>}
      </div>
      <div className="ii-country">
        {flag && <span className="ii-flag" aria-hidden="true">{flag}</span>}
        <span className="ii-country-name">{entry.jurisdictionName}</span>
      </div>
      {entry.structureLabel && (
        <div className="ii-structure">{humanizeToken(entry.structureLabel)}</div>
      )}

      {entry.status === "silver" ? (
        <div className="ii-reason">
          {presentExclusionReason(entry.excludedReason) || "Not currently viable for this production."}
        </div>
      ) : (
        <div className="ii-metrics">
          <div className="ii-metric">
            <span className="ii-metric-label">Max Incentive</span>
            <span className="ii-metric-value">
              {entry.baseIncentive?.ratePct != null ? `Up to ${entry.baseIncentive.ratePct}%` : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Modeled Incentive</span>
            <span className="ii-metric-value mono">
              {entry.segmentIncentiveUsd != null ? <Money value={entry.segmentIncentiveUsd} /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">NPC</span>
            <span className="ii-metric-value mono">
              {entry.npcUsd != null ? <Money value={entry.npcUsd} /> : "Not priced"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Incentive / Budget</span>
            <span className="ii-metric-value">{pctOfGross || "—"}</span>
          </div>
        </div>
      )}

      {entry.status === "amber" && entry.relatedCodes?.length > 0 && (
        <div className="ii-related">
          <span className="ii-related-label">Co-producing with</span>
          <span className="ii-related-list">
            {entry.relatedCodes.map((code) => (
              <span key={code} className="ii-related-item">
                {flagEmoji(code)} {jurisdictionName(code)}
              </span>
            ))}
          </span>
        </div>
      )}

      {entry.baseIncentive?.programLabel && (
        <div className="ii-program">{entry.baseIncentive.programLabel}</div>
      )}
    </CardShell>
  );
}

function EmptyCard({ slot }) {
  const meta = GLOBE_SEMANTIC[slot];
  return (
    <CardShell slot={slot}>
      <div className="ii-head">
        <span className="ii-cat-label">{meta.fullLabel}</span>
      </div>
      <div className="ii-empty">
        Not currently available for this production.
      </div>
    </CardShell>
  );
}

export default function IncentiveIntelligence({ representatives, onSelect }) {
  return (
    <section className="ovx-sec ii-section">
      <div className="oh"><b>Incentive Intelligence</b></div>
      <div className="ii-grid">
        {CATEGORY_ORDER.map((slot) => {
          const entry = representatives[slot];
          return entry ? (
            <PopulatedCard key={slot} entry={entry} onClick={onSelect ? () => onSelect(entry) : undefined} />
          ) : (
            <EmptyCard key={slot} slot={slot} />
          );
        })}
      </div>
    </section>
  );
}
