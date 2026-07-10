import { useState } from "react";
import { getRecommendations } from "../api";
import { useBackend } from "../hooks";
import { Loading, ErrorBox, Money } from "../components/Status";

const TABS = [
  { key: "financial", label: "Financial" },
  { key: "structural", label: "Structural" },
  { key: "creative", label: "Creative" },
  { key: "legal", label: "Legal" },
];

function RecTable({ recs }) {
  if (recs.length === 0) return <p className="muted">None in this category.</p>;
  return (
    <table>
      <thead>
        <tr><th>Title</th><th>Value</th><th>Confidence</th><th>Producer approval</th><th>Counsel approval</th></tr>
      </thead>
      <tbody>
        {recs.map((r) => (
          <tr key={r.recommendation_id}>
            <td>{r.title}<div className="muted small">{r.description}</div></td>
            <td><Money value={r.estimated_value_usd} /></td>
            <td>{r.confidence}</td>
            <td>{r.requires_producer_approval ? "required" : "—"}</td>
            <td>{r.requires_counsel_approval ? "required" : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Recommendations() {
  const { data, error, loading } = useBackend(getRecommendations, []);
  const [tab, setTab] = useState("financial");

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  const recsForTab = tab === "legal" ? data.legal : data.by_category[tab];

  return (
    <section>
      <h1>Recommendations ({data.total})</h1>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={t.key === tab ? "active" : ""}
            onClick={() => setTab(t.key)}
          >
            {t.label} ({t.key === "legal" ? data.legal.length : data.by_category[t.key].length})
          </button>
        ))}
      </nav>
      <RecTable recs={recsForTab} />
    </section>
  );
}
