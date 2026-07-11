import { useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, questionStatusLabel } from "../../lib/format";

export default function CompanyKnowledge() {
  const { data, error, loading } = useCineGlobe();
  const [selected, setSelected] = useState(null);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal } = data;
  const entries = legal.grey_areas_current;
  const active = selected || entries[0];
  const activeStatus = active ? questionStatusLabel(active.status) : null;

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Company Knowledge</p>
        <h1 className="screen-title">Cross-production intelligence</h1>
        <p className="text-tertiary small">Only The Little Utopia contributes knowledge today — this index will span the portfolio as more productions are added.</p>
      </header>

      <div className="split-pane">
        <div className="row-list" style={{ width: 320, flexShrink: 0 }}>
          {entries.map((e) => {
            const s = questionStatusLabel(e.status);
            return (
              <div key={e.item_id} className={`row-item ${active?.item_id === e.item_id ? "active" : ""}`} onClick={() => setSelected(e)}>
                <span className={`dot ${s.tier}`} />
                <div className="row-main">
                  <div className="row-title" style={{ fontSize: 12.5 }}>{e.resolving_evidence}</div>
                  <div className="row-sub">{e.jurisdiction_code} · {s.label}</div>
                </div>
              </div>
            );
          })}
        </div>

        {active && (
          <div className="region" style={{ flex: 1 }}>
            <div className="region-title"><span>{active.authority_to_ask}</span><span className={`badge ${activeStatus.tier}`}>{activeStatus.label}</span></div>
            <dl className="kv-list">
              <div><dt>Evidence needed</dt><dd style={{ maxWidth: 380, textAlign: "right" }}>{active.resolving_evidence}</dd></div>
              <div><dt>Confidence</dt><dd>{active.status === "open" ? "Unresolved" : "Resolved"}</dd></div>
              <div><dt>Business impact</dt><dd><Money value={active.amount_usd} /></dd></div>
              <div><dt>Affected jurisdiction</dt><dd>{active.jurisdiction_code}</dd></div>
              <div><dt>Authority</dt><dd className="mono small">{active.graph_rule_id || "AbsenceOfAuthority — not yet searched to a terminus"}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
