import { useNavigate } from "react-router-dom";
import { Scale, AlertTriangle, Eye, Clapperboard, CheckCircle2, ArrowRight, Plus } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, recommendationHeadline } from "../../lib/format";

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
      <header className="screen-header" style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <p className="screen-eyebrow">Today</p>
          <h1 className="screen-title">Work queue</h1>
        </div>
        <button
          className="hero-action"
          disabled
          title="POST /api/v1/projects exists and works, but no CineGlobe screen reads from the projects table — every screen here is wired to the single cached Little Utopia demo state (little_utopia_state.py), not the database. Calling it would create an orphaned row with no visible effect, so this stays disabled until that wiring exists."
        >
          <Plus size={14} strokeWidth={1.8} /> Add production
        </button>
      </header>

      <section className="region region-cool">
        <div className="region-title"><span>Needs a decision</span><span className="count">{highValueRecs.length}</span></div>
        <div className="row-list">
          {highValueRecs.map((r) => (
            <div className="row-item" key={r.recommendation_id} onClick={() => navigate("/production/workspace")}>
              <Scale size={16} color="var(--blue)" strokeWidth={1.8} />
              <div className="row-main">
                <div className="row-title">{recommendationHeadline(r)}</div>
                <div className="row-sub">The Little Utopia · {r.requires_counsel_approval ? "counsel approval needed" : "producer approval needed"}</div>
              </div>
              <div className="row-value mono"><Money value={r.estimated_value_usd} /></div>
            </div>
          ))}
        </div>
      </section>

      <section className="region region-blocker">
        <div className="region-title"><span>Blocked</span><span className="count">{blockingQuestions.length}</span></div>
        {blockingQuestions.length === 0 ? (
          <div className="empty-row"><CheckCircle2 size={15} strokeWidth={1.8} />Nothing is blocked right now.</div>
        ) : (
          <div className="row-list">
            {blockingQuestions.map((q) => (
              <div className="row-item" key={q.identifier} onClick={() => navigate("/production/workspace")}>
                <AlertTriangle size={16} color="var(--red)" strokeWidth={1.8} />
                <div className="row-main">
                  <div className="row-title">{q.question}</div>
                  <div className="row-sub">{q.why_it_matters}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="region region-conditional">
        <div className="region-title"><span>Watching</span><span className="count">{openGreyAreas.length}</span></div>
        {openGreyAreas.length === 0 ? (
          <div className="empty-row"><CheckCircle2 size={15} strokeWidth={1.8} />Nothing open to watch.</div>
        ) : (
          <div className="row-list">
            {openGreyAreas.map((g) => (
              <div className="row-item" key={g.item_id} onClick={() => navigate("/production/knowledge")}>
                <Eye size={16} color="var(--amber)" strokeWidth={1.8} />
                <div className="row-main">
                  <div className="row-title">{g.resolving_evidence}</div>
                  <div className="row-sub">{g.authority_to_ask} · {g.jurisdiction_code} <span className="mono text-tertiary">· {g.item_id}</span></div>
                </div>
                <div className="row-value mono"><Money value={g.amount_usd} /></div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="region region-cool">
        <div className="region-title"><span>Productions needing action</span></div>
        <div className="row-list">
          <div className="row-item" onClick={() => navigate("/production/overview")}>
            <Clapperboard size={16} color="var(--blue)" strokeWidth={1.8} />
            <div className="row-main">
              <div className="row-title serif" style={{ fontSize: 14 }}>{production.production_name}</div>
              <div className="row-sub">{production.jurisdiction_code} baseline · {pkg.confidence} confidence</div>
            </div>
            <div className="row-value mono"><Money value={production.gross_budget_usd} /></div>
            <ArrowRight size={14} color="var(--text-tertiary)" />
          </div>
        </div>
      </section>
    </div>
  );
}
