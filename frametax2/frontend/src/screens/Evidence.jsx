import { getLegal } from "../api";
import { useBackend } from "../hooks";
import { Loading, ErrorBox, Money } from "../components/Status";

export default function Evidence() {
  const { data, error, loading } = useBackend(getLegal, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  return (
    <section>
      <h1>Evidence, Authority &amp; Legal Issues</h1>
      <p className="muted small">Source: {data.connector_source_label}</p>

      <h2>Grey Areas</h2>
      <table>
        <thead><tr><th>Item</th><th>Status</th><th>Amount at stake</th><th>Authority to ask</th></tr></thead>
        <tbody>
          {data.grey_areas_current.map((g) => (
            <tr key={g.item_id} className={g.status === "open" ? "blocking" : ""}>
              <td>{g.item_id}</td>
              <td>{g.status}</td>
              <td><Money value={g.amount_usd} /></td>
              <td>{g.authority_to_ask}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Legal Authority Acquisition Engine (docket)</h2>
      <table className="kv">
        <tbody>
          <tr><th>Questions auto-detected</th><td>{data.questions_detected}</td></tr>
          <tr><th>Auto-executed (commitment-grade)</th><td>{data.questions_auto_executed.join(", ") || "none"}</td></tr>
          <tr><th>Awaiting human verification</th><td>{data.questions_awaiting_verification.join(", ") || "none"}</td></tr>
        </tbody>
      </table>

      <h2>Authority Score</h2>
      {data.committed_rule_id ? (
        <>
          <p>Committed rule: <strong>{data.committed_rule_id}</strong></p>
          {Object.entries(data.authority_scores).map(([ruleId, score]) => (
            <table key={ruleId} className="kv">
              <tbody>
                <tr><th>Composite score</th><td>{score.composite} / 100</td></tr>
                <tr><th>Confidence</th><td>{score.confidence}</td></tr>
                <tr><th>Source strength</th><td>{score.breakdown.source_strength}</td></tr>
                <tr><th>Legal weight</th><td>{score.breakdown.legal_weight}</td></tr>
                <tr><th>Jurisdiction relevance</th><td>{score.breakdown.jurisdiction_relevance}</td></tr>
                <tr><th>Recency</th><td>{score.breakdown.recency}</td></tr>
                <tr><th>Completeness</th><td>{score.breakdown.completeness}</td></tr>
                <tr><th>Citation quality</th><td>{score.breakdown.citation_quality}</td></tr>
              </tbody>
            </table>
          ))}
        </>
      ) : (
        <p className="muted">No rule committed yet.</p>
      )}

      <h2>Evidence Trace</h2>
      {data.evidence_trace.length === 0 ? (
        <p className="muted">No evidence chain to display.</p>
      ) : (
        data.evidence_trace.map((link) => (
          <div className="card" key={link.evidence_id}>
            <p><strong>{link.authority_source_title}</strong> — {link.authority_tier} (tier {link.authority_tier_rank})</p>
            <p className="muted small">{link.document_title} · retrieved {link.retrieved_date} · {link.authority_body}</p>
            <p>{link.citation_text}</p>
          </div>
        ))
      )}

      <h2>Optimizer impact</h2>
      <table className="kv">
        <tbody>
          <tr><th>Conservative NPC before legal resolution</th><td><Money value={data.conservative_npc_before_usd} /></td></tr>
          <tr><th>Conservative NPC after legal resolution</th><td><Money value={data.conservative_npc_after_usd} /></td></tr>
        </tbody>
      </table>
    </section>
  );
}
