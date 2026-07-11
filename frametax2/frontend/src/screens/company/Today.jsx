import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

export default function Today() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { pkg, legal, recommendations, production } = data;
  const blockingQuestions = pkg.missing_inputs.filter((m) => m.blocking);
  const openGreyAreas = legal.grey_areas_current.filter((g) => g.status === "open");
  const highValueRecs = recommendations.by_category.financial
    .filter((r) => r.estimated_value_usd)
    .sort((a, b) => (b.estimated_value_usd || 0) - (a.estimated_value_usd || 0))
    .slice(0, 3);

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Today</p>
        <h1 className="screen-title">Work queue</h1>
      </header>

      <section className="region region-accent-gold">
        <div className="region-title">Needs a decision <span className="count">{highValueRecs.length}</span></div>
        <div className="row-list">
          {highValueRecs.map((r) => (
            <div className="row-item" key={r.recommendation_id} onClick={() => navigate("/production/workspace")}>
              <span className="dot gold" />
              <div className="row-main">
                <div className="row-title">{r.title}</div>
                <div className="row-sub">The Little Utopia · {r.requires_counsel_approval ? "counsel approval" : "producer approval"}</div>
              </div>
              <div className="row-value"><Money value={r.estimated_value_usd} /></div>
            </div>
          ))}
        </div>
      </section>

      <section className="region region-accent-red">
        <div className="region-title">Blocked <span className="count">{blockingQuestions.length}</span></div>
        {blockingQuestions.length === 0 ? (
          <p className="empty-state">Nothing is blocked.</p>
        ) : (
          <div className="row-list">
            {blockingQuestions.map((q) => (
              <div className="row-item" key={q.identifier} onClick={() => navigate("/production/workspace")}>
                <span className="dot red" />
                <div className="row-main">
                  <div className="row-title">{q.question}</div>
                  <div className="row-sub">{q.why_it_matters}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="region region-accent-amber">
        <div className="region-title">Watching <span className="count">{openGreyAreas.length}</span></div>
        <div className="row-list">
          {openGreyAreas.map((g) => (
            <div className="row-item" key={g.item_id} onClick={() => navigate("/production/knowledge")}>
              <span className="dot amber" />
              <div className="row-main">
                <div className="row-title">{g.item_id}</div>
                <div className="row-sub">{g.authority_to_ask}</div>
              </div>
              <div className="row-value"><Money value={g.amount_usd} /></div>
            </div>
          ))}
        </div>
      </section>

      <section className="region region-accent-blue">
        <div className="region-title">Productions needing action</div>
        <div className="row-list">
          <div className="row-item" onClick={() => navigate("/production/overview")}>
            <span className="dot gold" />
            <div className="row-main">
              <div className="row-title serif">{production.production_name}</div>
              <div className="row-sub">{production.jurisdiction_code} baseline · {pkg.confidence} confidence</div>
            </div>
            <div className="row-value"><Money value={production.gross_budget_usd} /></div>
          </div>
        </div>
      </section>
    </div>
  );
}
