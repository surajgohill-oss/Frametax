import { Money, recommendationHeadline } from "../lib/format";

// Replaces any generic "confidence score" idea with four real fields per
// opportunity: current qualification, missing requirements, potential
// incentive increase, how to qualify. Every field below is read verbatim
// from allocated_structures or recommendations — nothing here computes or
// estimates a value that the backend didn't already produce. Where the
// backend hasn't resolved a number (a blocked segment has no confirmed
// incentive yet), that gap is disclosed, not filled with a guess.

function StructureCard({ structure }) {
  const rec = structure.recommendation;
  const dependencies = rec?.dependency_group?.length ? rec.dependency_group : structure.blockers;
  return (
    <div className="field-row" style={{ flexDirection: "column", alignItems: "stretch", gap: 6, padding: "10px 2px" }}>
      <div className="row-title" style={{ fontSize: 13 }}>{structure.label}</div>
      <div className="text-tertiary small">Current qualification: <strong className="text-secondary">Blocked — not yet priced</strong></div>
      <div className="text-tertiary small">Missing requirements:</div>
      {dependencies.slice(0, 3).map((d, i) => (
        <p key={i} className="text-secondary small" style={{ margin: 0 }}>· {d}</p>
      ))}
      <div className="text-tertiary small">
        Potential incentive increase: <span className="field-unavailable">not yet quantifiable — the blocked segment contributes $0 until resolved</span>
      </div>
      {rec && <div className="text-tertiary small">How to qualify: <span className="text-secondary">{rec.action}</span></div>}
    </div>
  );
}

function RecommendationCard({ rec }) {
  return (
    <div className="field-row" style={{ flexDirection: "column", alignItems: "stretch", gap: 6, padding: "10px 2px" }}>
      <div className="row-title" style={{ fontSize: 13 }}>{recommendationHeadline(rec)}</div>
      <div className="text-tertiary small">Current qualification: <strong className="text-secondary">{rec.category} · {rec.confidence} confidence</strong></div>
      {rec.specific_actions?.length > 0 && (
        <>
          <div className="text-tertiary small">Missing requirements:</div>
          {rec.specific_actions.map((a, i) => <p key={i} className="text-secondary small" style={{ margin: 0 }}>· {a}</p>)}
        </>
      )}
      <div className="text-tertiary small">
        Potential incentive increase: <span className="mono text-secondary"><Money value={rec.estimated_value_usd} /></span>
      </div>
      <div className="text-tertiary small">How to qualify: <span className="text-secondary">{rec.description}</span></div>
    </div>
  );
}

export default function QualificationAssistant({ allocatedStructures, recommendations }) {
  const blocked = (allocatedStructures?.structures || []).filter((s) => !s.is_fully_priced).slice(0, 2);
  const valued = [
    ...recommendations.by_category.financial,
    ...recommendations.by_category.structural,
  ].filter((r) => r.estimated_value_usd).sort((a, b) => b.estimated_value_usd - a.estimated_value_usd).slice(0, 2);

  if (blocked.length === 0 && valued.length === 0) {
    return (
      <section className="region region-warm">
        <div className="region-title"><span>Qualification Assistant</span></div>
        <p className="empty-state">Every allocated structure is either fully priced or has no unresolved blockers right now.</p>
      </section>
    );
  }

  return (
    <section className="region region-warm">
      <div className="region-title"><span>Qualification Assistant</span></div>
      <div className="row-list">
        {valued.map((r) => <RecommendationCard key={r.recommendation_id} rec={r} />)}
        {blocked.map((s) => <StructureCard key={s.structure_id} structure={s} />)}
      </div>
    </section>
  );
}
