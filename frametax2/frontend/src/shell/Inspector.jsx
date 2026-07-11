import { X } from "lucide-react";
import { useAppState } from "../state/AppState";
import { Money, Pct, tierBadgeClass, recommendationHeadline, questionStatusLabel, humanizeToken, structureLabel } from "../lib/format";

function RecommendationInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">{data.category} recommendation</p>
      <h3>{recommendationHeadline(data)}</h3>
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
      <h3>{structureLabel(data.participating_jurisdictions)}</h3>
      <dl className="kv-list">
        <div><dt>Priceable now</dt><dd><Pct value={data.priceable_pct} /></dd></div>
        <div><dt>Open requirements</dt><dd>{data.constraints?.length || 0}</dd></div>
      </dl>
      {data.is_fully_priced && Object.keys(cases).length > 0 ? (
        <table className="inspector-table">
          <tbody>
            {["conservative", "base", "optimistic", "risk_adjusted"].filter((k) => cases[k]).map((k) => (
              <tr key={k}>
                <td style={{ textTransform: "capitalize" }}>{k.replace("_", " ")}</td>
                <td className="mono"><Money value={cases[k].net_production_cost_usd} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-tertiary small">
          Only {Math.round(data.priceable_pct * 100)}% of this structure can currently be priced. A full cost
          comparison isn't available until the open requirements below are resolved.
        </p>
      )}
      {data.constraints?.length > 0 && (() => {
        const unique = [...new Set(data.constraints.map((c) => c.description))];
        return (
          <div className="inspector-actions" style={{ flexDirection: "column", alignItems: "stretch" }}>
            {unique.slice(0, 4).map((desc) => (
              <p key={desc} className="text-secondary small" style={{ margin: "4px 0" }}>{desc}</p>
            ))}
            {unique.length > 4 && <p className="text-tertiary small">+{unique.length - 4} more requirement type(s)</p>}
          </div>
        );
      })()}
    </>
  );
}

function QuestionInspector({ data }) {
  const isGreyArea = "authority_to_ask" in data;
  const status = isGreyArea ? questionStatusLabel(data.status) : null;
  return (
    <>
      <p className="inspector-eyebrow">{isGreyArea ? "Grey area" : "Open question"}</p>
      <h3>{isGreyArea ? data.resolving_evidence : data.question}</h3>
      {isGreyArea ? (
        <dl className="kv-list">
          <div><dt>Status</dt><dd><span className={`badge ${status.tier}`}>{status.label}</span></dd></div>
          <div><dt>Amount at stake</dt><dd className="mono"><Money value={data.amount_usd} /></dd></div>
          <div><dt>Authority to ask</dt><dd>{data.authority_to_ask}</dd></div>
          {data.account_codes?.length > 0 && <div><dt>Affected accounts</dt><dd className="mono">{data.account_codes.join(", ")}</dd></div>}
        </dl>
      ) : (
        <dl className="kv-list">
          <div><dt>Why it matters</dt><dd>{data.why_it_matters}</dd></div>
          <div><dt>Decision required</dt><dd>{data.blocking ? "Yes" : "No"}</dd></div>
          <div><dt>Affects</dt><dd>{data.downstream_engines?.map(humanizeToken).join(", ")}</dd></div>
          <div><dt>Priority</dt><dd>{data.optimizer_value}</dd></div>
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
    <>
      <div className="inspector-backdrop" onClick={closeInspector} />
      <aside className="inspector">
        <button className="inspector-close" onClick={closeInspector} aria-label="Close inspector">
          <X size={16} />
        </button>
        {Renderer ? <Renderer data={inspector.data} /> : <p className="text-tertiary">No inspector view for this item.</p>}
      </aside>
    </>
  );
}
