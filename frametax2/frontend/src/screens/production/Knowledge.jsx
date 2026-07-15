import { useMemo, useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, questionStatusLabel } from "../../lib/format";

const SCOPES = ["Production", "Jurisdiction", "Company"];
const VIEWS = ["Grey Areas", "Reference Library"];

// Every rule shown anywhere in this app already carries a real citation
// field — this aggregates the three that actually exist (register.reason
// for explicit-statute accounts, allocated_structures segment
// statutory_basis, recommendation.authority_reference) into one browsable
// library. Nothing here is a new source; it's the same citations already
// rendered in Inspector/Workspace, deduplicated and grouped.
function buildReferenceLibrary(pkg, allocatedStructures, recommendations) {
  const items = [];
  const seen = new Set();

  for (const a of pkg.register) {
    if (a.authority_basis === "explicit_statute" && a.reason && !seen.has(a.reason)) {
      seen.add(a.reason);
      items.push({ kind: "Statute", jurisdiction: null, text: a.reason, source: `Account ${a.account_code} · ${a.description}` });
    }
  }

  for (const s of allocatedStructures?.structures || []) {
    for (const seg of s.segments) {
      if (seg.statutory_basis && !seen.has(seg.statutory_basis)) {
        seen.add(seg.statutory_basis);
        items.push({ kind: "Program rule", jurisdiction: seg.jurisdiction_code, text: seg.statutory_basis, source: s.label });
      }
    }
  }

  const allRecs = [
    ...recommendations.by_category.financial, ...recommendations.by_category.structural,
    ...recommendations.by_category.creative, ...recommendations.by_category.required_input,
    ...recommendations.legal,
  ];
  for (const r of allRecs) {
    for (const ref of r.authority_reference || []) {
      if (!seen.has(ref)) {
        seen.add(ref);
        items.push({ kind: "Authority reference", jurisdiction: r.jurisdiction_codes?.[0] || null, text: ref, source: r.title });
      }
    }
  }

  return items;
}

const KIND_TIER = { "Statute": "gold", "Program rule": "blue", "Authority reference": "silver" };

export default function Knowledge() {
  const { data, error, loading } = useCineGlobe();
  const [scope, setScope] = useState("Production");
  const [view, setView] = useState("Grey Areas");
  const [selected, setSelected] = useState(null);
  const library = useMemo(() => {
    if (!data) return [];
    return buildReferenceLibrary(data.pkg, data.structures.allocated_structures, data.recommendations);
  }, [data]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal, production } = data;
  const entries = legal.grey_areas_current;
  const active = selected || entries[0];
  const activeStatus = active ? questionStatusLabel(active.status) : null;

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Knowledge</p>
        <h1 className="screen-title">The Little Utopia</h1>
      </header>

      <div className="tag-row">
        {VIEWS.map((v) => (
          <button key={v} className={`tag ${view === v ? "active" : ""}`} onClick={() => setView(v)}>{v}</button>
        ))}
      </div>

      {view === "Grey Areas" && (
        <>
          <div className="tag-row">
            {SCOPES.map((s) => (
              <button key={s} className={`tag ${scope === s ? "active" : ""}`} onClick={() => setScope(s)}>{s}</button>
            ))}
          </div>
          <p className="text-tertiary small" style={{ margin: "8px 0 20px" }}>
            {scope === "Production" && "Knowledge attached directly to The Little Utopia."}
            {scope === "Jurisdiction" && `Knowledge scoped to ${production.jurisdiction_code} — currently identical to production scope, since this is the only jurisdiction with committed knowledge.`}
            {scope === "Company" && "Knowledge visible across the whole portfolio — currently only The Little Utopia contributes."}
          </p>

          <div className="split-pane">
            <div className="row-list" style={{ width: 320, flexShrink: 0 }}>
              {entries.map((e) => {
                const s = questionStatusLabel(e.status);
                return (
                  <div key={e.item_id} className={`row-item ${active?.item_id === e.item_id ? "active" : ""}`} onClick={() => setSelected(e)}>
                    <span className={`dot ${s.tier}`} />
                    <div className="row-main">
                      <div className="row-title" style={{ fontSize: 12.5 }}>{e.resolving_evidence}</div>
                      <div className="row-sub">{s.label} · {e.jurisdiction_code}</div>
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
                  <div><dt>Confidence</dt><dd>{legal.authority_scores[active.graph_rule_id]?.confidence || "Unresolved"}</dd></div>
                  <div><dt>Business impact</dt><dd><Money value={active.amount_usd} /></dd></div>
                  <div><dt>Affected jurisdiction</dt><dd>{active.jurisdiction_code}</dd></div>
                  <div><dt>Authority</dt><dd className="mono small">{active.graph_rule_id || "AbsenceOfAuthority (not yet resolved)"}</dd></div>
                </dl>
              </div>
            )}
          </div>
        </>
      )}

      {view === "Reference Library" && (
        <section className="region">
          <p className="text-tertiary small" style={{ marginBottom: 14 }}>
            Every statute, program rule, and authority reference cited anywhere in this app, deduplicated and
            grouped — the same real citations shown in the Inspector and Workspace, not a separate source.
          </p>
          {library.length === 0 ? (
            <p className="empty-state">No citations available yet.</p>
          ) : (
            <div className="row-list">
              {library.map((item, i) => (
                <div key={i} className="row-item" style={{ cursor: "default", alignItems: "flex-start" }}>
                  <span className={`dot ${KIND_TIER[item.kind] || "silver"}`} style={{ marginTop: 5 }} />
                  <div className="row-main">
                    <div className="row-sub" style={{ marginBottom: 3 }}>
                      <span className={`badge ${KIND_TIER[item.kind] || "silver"}`}>{item.kind}</span>
                      {item.jurisdiction && <span className="mono"> {item.jurisdiction}</span>}
                      <span className="text-tertiary"> · from {item.source}</span>
                    </div>
                    <div className="row-title small" style={{ fontWeight: 400, lineHeight: 1.5 }}>{item.text}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
