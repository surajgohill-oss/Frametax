import { useAppState } from "../state/AppState";
import { Money, Pct, tierBadgeClass } from "../lib/format";

function RecommendationInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">{data.category} recommendation</p>
      <h3>{data.title}</h3>
      <p className="text-secondary">{data.description}</p>
      <dl className="kv-list">
        <div><dt>Estimated value</dt><dd className="mono"><Money value={data.estimated_value_usd} /></dd></div>
        <div><dt>Confidence</dt><dd>{data.confidence}</dd></div>
        <div><dt>Producer approval</dt><dd>{data.requires_producer_approval ? "Required" : "Not required"}</dd></div>
        <div><dt>Counsel approval</dt><dd>{data.requires_counsel_approval ? "Required" : "Not required"}</dd></div>
        {data.creative_impact && <div><dt>Creative impact</dt><dd>{data.creative_impact}</dd></div>}
        {data.trade_off_framing && <div><dt>Trade-off</dt><dd>{data.trade_off_framing}</dd></div>}
        {data.evidence_reference?.length > 0 && (
          <div><dt>Evidence needed</dt><dd>{data.evidence_reference.join("; ")}</dd></div>
        )}
        {data.authority_reference?.length > 0 && (
          <div><dt>Authority reference</dt><dd className="mono small">{data.authority_reference.join(", ")}</dd></div>
        )}
      </dl>
    </>
  );
}

function CandidateInspector({ data }) {
  const cases = data.cases || {};
  return (
    <>
      <p className="inspector-eyebrow">Structure candidate</p>
      <h3>{data.label}</h3>
      <dl className="kv-list">
        <div><dt>Jurisdictions</dt><dd>{data.participating_jurisdictions.join(", ")}</dd></div>
        <div><dt>Priceable</dt><dd><Pct value={data.priceable_pct} /></dd></div>
        <div><dt>Fully priced</dt><dd>{String(data.is_fully_priced)}</dd></div>
      </dl>
      {Object.keys(cases).length > 0 ? (
        <table className="inspector-table">
          <tbody>
            {["conservative", "base", "optimistic", "risk_adjusted"].filter((k) => cases[k]).map((k) => (
              <tr key={k}>
                <td>{k.replace("_", " ")}</td>
                <td className="mono"><Money value={cases[k].net_production_cost_usd} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-tertiary small">Unpriced — no qualification register for this jurisdiction set.</p>
      )}
      {data.constraints?.length > 0 && (
        <p className="text-tertiary small">{data.constraints.length} open constraint(s) on this structure.</p>
      )}
    </>
  );
}

function QuestionInspector({ data }) {
  const isGreyArea = "authority_to_ask" in data;
  return (
    <>
      <p className="inspector-eyebrow">{isGreyArea ? "Grey area" : "Open question"}</p>
      <h3>{isGreyArea ? data.item_id : data.question}</h3>
      {isGreyArea ? (
        <dl className="kv-list">
          <div><dt>Status</dt><dd>{data.status}</dd></div>
          <div><dt>Amount at stake</dt><dd className="mono"><Money value={data.amount_usd} /></dd></div>
          <div><dt>Authority to ask</dt><dd>{data.authority_to_ask}</dd></div>
          <div><dt>Resolving evidence</dt><dd>{data.resolving_evidence}</dd></div>
        </dl>
      ) : (
        <dl className="kv-list">
          <div><dt>Why it matters</dt><dd>{data.why_it_matters}</dd></div>
          <div><dt>Blocking</dt><dd>{data.blocking ? "Yes" : "No"}</dd></div>
          <div><dt>Downstream engines</dt><dd>{data.downstream_engines?.join(", ")}</dd></div>
          <div><dt>Optimizer value</dt><dd>{data.optimizer_value}</dd></div>
        </dl>
      )}
      <div className="inspector-actions">
        {["Resolve", "Escalate", "Attach document", "Assign", "Convert to assumption", "Promote to grey area"].map((label) => (
          <button key={label} className="ghost-action" disabled title="Not yet wired to a backend mutation">
            {label}
          </button>
        ))}
      </div>
    </>
  );
}

function JurisdictionInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">Jurisdiction</p>
      <h3>{data.code}</h3>
      <span className={`badge ${tierBadgeClass(data.tier)}`}>{data.tierLabel}</span>
      {data.candidate && (
        <dl className="kv-list" style={{ marginTop: 12 }}>
          <div><dt>Priceable</dt><dd><Pct value={data.candidate.priceable_pct} /></dd></div>
          <div><dt>Risk-Adjusted NPC</dt><dd className="mono"><Money value={data.candidate.cases?.risk_adjusted?.net_production_cost_usd} /></dd></div>
        </dl>
      )}
    </>
  );
}

const RENDERERS = {
  recommendation: RecommendationInspector,
  candidate: CandidateInspector,
  question: QuestionInspector,
  jurisdiction: JurisdictionInspector,
};

export default function Inspector() {
  const { inspector, closeInspector } = useAppState();
  if (!inspector) return null;

  const Renderer = RENDERERS[inspector.kind];

  return (
    <aside className="inspector">
      <button className="inspector-close" onClick={closeInspector} aria-label="Close inspector">×</button>
      {Renderer ? <Renderer data={inspector.data} /> : <p className="text-tertiary">No inspector view for this item.</p>}
    </aside>
  );
}
