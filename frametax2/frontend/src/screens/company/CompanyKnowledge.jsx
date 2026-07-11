import { useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

export default function CompanyKnowledge() {
  const { data, error, loading } = useCineGlobe();
  const [selected, setSelected] = useState(null);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal } = data;
  const entries = legal.grey_areas_current;
  const active = selected || entries[0];

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Company Knowledge</p>
        <h1 className="screen-title">Cross-production intelligence</h1>
        <p className="text-tertiary small">Only The Little Utopia contributes knowledge today — this index will span the portfolio as more productions are added.</p>
      </header>

      <div className="split-pane">
        <div className="row-list" style={{ width: 320, flexShrink: 0 }}>
          {entries.map((e) => (
            <div key={e.item_id} className={`row-item ${active?.item_id === e.item_id ? "active" : ""}`} onClick={() => setSelected(e)}>
              <span className={`dot ${e.status === "open" ? "amber" : "jade"}`} />
              <div className="row-main">
                <div className="row-title">{e.item_id}</div>
                <div className="row-sub">{e.jurisdiction_code} · {e.status.replace("_", " ")}</div>
              </div>
            </div>
          ))}
        </div>

        {active && (
          <div className="region" style={{ flex: 1 }}>
            <div className="region-title">{active.item_id}</div>
            <dl className="kv-list">
              <div><dt>Issue</dt><dd style={{ maxWidth: 380, textAlign: "right" }}>{active.authority_to_ask}</dd></div>
              <div><dt>Evidence needed</dt><dd style={{ maxWidth: 380, textAlign: "right" }}>{active.resolving_evidence}</dd></div>
              <div><dt>Confidence</dt><dd>{active.status === "open" ? "Unresolved" : "Resolved"}</dd></div>
              <div><dt>Business impact</dt><dd><Money value={active.amount_usd} /></dd></div>
              <div><dt>Affected jurisdiction</dt><dd>{active.jurisdiction_code}</dd></div>
              <div><dt>Authority</dt><dd>{active.graph_rule_id || "AbsenceOfAuthority — not yet searched to a terminus"}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
