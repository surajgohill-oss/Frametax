import { Money } from "../lib/format";

/**
 * Inline (never modal) causal chain: Budget line -> Jurisdiction rule ->
 * Evidence -> Document -> Statute/authority -> Result. Renders the real
 * committed chain when one exists (legal.evidence_trace, produced by
 * EvidenceGraph.trace_rule() via the Legal Engine); otherwise states
 * plainly that authority is still pending — never fabricates a link.
 */
export default function EconomicsTrace({ greyArea, legal }) {
  if (!greyArea) return null;
  const isCommitted = greyArea.graph_rule_id && greyArea.graph_rule_id === legal.committed_rule_id;
  const score = isCommitted ? legal.authority_scores[legal.committed_rule_id] : null;

  return (
    <div className="trace">
      <div className="trace-node">
        <span className="trace-label">Grey area</span>
        <span className="trace-value">{greyArea.item_id} · <Money value={greyArea.amount_usd} /></span>
      </div>
      <div className="trace-arrow">→</div>
      <div className="trace-node">
        <span className="trace-label">Question</span>
        <span className="trace-value small">{greyArea.authority_to_ask}</span>
      </div>
      <div className="trace-arrow">→</div>
      {isCommitted ? (
        <>
          {legal.evidence_trace.map((link) => (
            <span key={link.evidence_id} style={{ display: "contents" }}>
              <div className="trace-node">
                <span className="trace-label">{link.authority_tier.replace(/_/g, " ").toLowerCase()}</span>
                <span className="trace-value small">{link.authority_source_title}</span>
              </div>
              <div className="trace-arrow">→</div>
            </span>
          ))}
          <div className="trace-node result">
            <span className="trace-label">Result</span>
            <span className="trace-value">Resolved — Authority Score {score?.composite}/100 ({score?.confidence})</span>
          </div>
        </>
      ) : (
        <div className="trace-node pending">
          <span className="trace-label">Authority</span>
          <span className="trace-value small">Pending — LAAE task TASK-{greyArea.item_id} not yet committed to Evidence Graph</span>
        </div>
      )}
    </div>
  );
}
