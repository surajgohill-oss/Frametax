import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProjectWorkspace } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import Globe3D from "../../components/Globe3D";
import { GLOBE_SEMANTIC, STATUS_HEX, globeKey } from "../../lib/globeData";
import { JURISDICTION_COORDS } from "../../lib/jurisdictions";

// Project Workspace — the ONE project-driven evaluation/script/budget/world
// surface, generic over any project's own canonical state
// (app/services/project_workspace_view.py). Little Utopia and F#K
// Valentine's Day render through the exact same component tree here; only
// the DATA differs (Little Utopia simply has more of it — a real budget,
// a real evaluation, everything a real ingested project can have).
//
// This is deliberately NOT the richer /production/overview experience
// (BudgetRail's account-level QPE trace, ProductionDetails' people/facts
// editor, IncentiveIntelligence's per-category cards) — those consume a
// hand-built account register and economics-controls shape that only
// Little Utopia's own curated fixture carries. Building a generic
// equivalent of that is real future work, not implied by this task's own
// "no redesign, no new engine work, adapt the existing canonical
// evaluation" scope. What IS generic here is: real budget, real script
// facts, real canonical evaluation, real candidate accounting — nothing
// fabricated for a project that doesn't have the richer data yet.

const TABS = ["Overview", "Script", "Budget", "World"];

function statusLine(status) {
  switch (status) {
    case "NOT_BEGUN": return "Evaluation not begun";
    case "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION": return "Budget required before evaluation";
    case "EVALUATION_COMPLETE": return "Evaluation complete";
    default: return status || "Unknown";
  }
}

export default function ProjectWorkspace() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("Overview");

  function load() {
    setError(null);
    getProjectWorkspace(projectId).then(setData).catch((err) => setError(err.message || String(err)));
  }

  useEffect(() => {
    setData(null);
    setTab("Overview");
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  if (error) return <div className="screen"><ErrorBox message={error} /></div>;
  if (!data) return <div className="screen"><Loading /></div>;

  const { project, evaluation, budget, script } = data;

  return (
    <div className="screen rec-screen">
      <div className="rec-toprow">
        <div className="rec-crumb" onClick={() => navigate(`/company/library/${project.id}`)}>← Project Record</div>
      </div>

      <div className="rec-idband">
        <div className="rec-idmain">
          <div className="rec-title">{project.title}</div>
          <div className="rec-idrow">
            <div className="rec-idf"><span className="l2">Budget</span>
              <span className="v">{project.budget_usd != null ? <Money value={project.budget_usd} /> : "—"}</span>
            </div>
            <div className="rec-idf"><span className="l2">Base jurisdiction</span>
              <span className="v">{project.base_jurisdiction_code || "Unknown"}</span>
            </div>
            <div className="rec-idf"><span className="l2">Evaluation</span>
              <span className="v">{statusLine(evaluation.status)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="rec-tabs">
        {TABS.map((t) => (
          <button key={t} className={`rec-tab ${tab === t ? "on" : ""}`} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab evaluation={evaluation} project={project} />}
      {tab === "Script" && <ScriptTab script={script} />}
      {tab === "Budget" && <BudgetTab budget={budget} />}
      {tab === "World" && <WorldTab evaluation={evaluation} />}
    </div>
  );
}

function CandidateRow({ c }) {
  const semantic = c.ui_status === "COMPARABLE" ? GLOBE_SEMANTIC.gold
    : c.ui_status === "REVIEW_REQUIRED" ? GLOBE_SEMANTIC.amber
    : GLOBE_SEMANTIC.silver;
  return (
    <div className="stat">
      <span className="l">
        <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: 7, background: semantic.hex, marginRight: 6 }} />
        {c.label}
      </span>
      <span className="v mono">
        {c.true_net_cost_usd != null ? <Money value={c.true_net_cost_usd} /> : (c.reason ? "Needs validation" : "—")}
      </span>
    </div>
  );
}

function OverviewTab({ evaluation, project }) {
  if (evaluation.status !== "EVALUATION_COMPLETE" || !evaluation.top_result) {
    return (
      <div className="ovx-sec">
        <div className="oh"><b>Evaluation</b></div>
        <p className="text-tertiary small">
          {evaluation.status === "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"
            ? "A parsed budget is required before this project can be evaluated."
            : "Begin Evaluation from the Project Record to see results here."}
        </p>
      </div>
    );
  }
  return (
    <div className="rec-cols">
      <div className="ovx-sec">
        <div className="oh"><b>Leading structure</b></div>
        <div className="stat"><span className="l">{evaluation.top_result.label}</span>
          <span className="v mono"><Money value={evaluation.top_result.true_net_cost_usd} /></span>
        </div>
        {evaluation.top_result.total_incentive_value_usd != null && (
          <div className="stat"><span className="l">Incentive value</span>
            <span className="v mono"><Money value={evaluation.top_result.total_incentive_value_usd} /></span>
          </div>
        )}
        <p className="text-tertiary small" style={{ marginTop: 10 }}>{evaluation.mfni_limitation}</p>
      </div>
      <div className="ovx-sec">
        <div className="oh"><b>Candidate accounting</b></div>
        <div className="stat"><span className="l">Comparable (priced, own base jurisdiction)</span><span className="v mono">{evaluation.comparable_count}</span></div>
        <div className="stat"><span className="l">Review required (priced, relocation cost unmodeled)</span><span className="v mono">{evaluation.review_required_count}</span></div>
        <div className="stat"><span className="l">Unavailable (authority insufficient)</span><span className="v mono">{evaluation.unpriceable_count}</span></div>
      </div>
    </div>
  );
}

function ScriptTab({ script }) {
  if (script.status === "SCRIPT_NOT_PRESENT" || !script.filename) {
    return <div className="ovx-sec"><div className="oh"><b>Script</b></div><div className="empty-state">No screenplay ingested yet.</div></div>;
  }
  const parsed = script.status === "SCRIPT_PARSED";
  return (
    <div className="ovx-sec">
      <div className="oh"><b>{script.filename}</b></div>
      {!parsed && <p className="text-tertiary small">Status: {script.status} — structural breakdown not yet available.</p>}
      {parsed && (
        <>
          <div className="stat"><span className="l">Scenes</span><span className="v mono">{script.scene_count}</span></div>
          <div className="stat"><span className="l">Speaking characters</span><span className="v mono">{script.character_count}</span></div>
          {script.locations?.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <span className="l2" style={{ display: "block", marginBottom: 6 }}>SCRIPTED LOCATIONS ({script.locations.length})</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {script.locations.slice(0, 40).map((l) => (
                  <span key={l} className="chip">{l}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
      <p className="text-tertiary small" style={{ marginTop: 12 }}>
        Full script summary presentation is designed in a following phase — this is the existing SA-1 structural breakdown, unaltered.
      </p>
    </div>
  );
}

function BudgetTab({ budget }) {
  if (!budget.filename) {
    return <div className="ovx-sec"><div className="oh"><b>Budget</b></div><div className="empty-state">No budget document ingested yet.</div></div>;
  }
  return (
    <div className="ovx-sec">
      <div className="oh"><b>{budget.filename}</b><span className="n">{budget.line_items.length} lines</span></div>
      <div className="stat"><span className="l">Total (source-declared)</span>
        <span className="v mono">{budget.total_usd != null ? <Money value={budget.total_usd} /> : "—"}</span>
      </div>
      <div style={{ marginTop: 8, maxHeight: 420, overflowY: "auto" }}>
        {budget.line_items.map((li, i) => (
          <div className="stat" key={i}>
            <span className="l">{li.description}{li.department ? <span className="text-tertiary"> · {li.department}</span> : null}</span>
            <span className="v mono">{li.amount_usd != null ? <Money value={li.amount_usd} /> : "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function WorldTab({ evaluation }) {
  const candidates = useMemo(
    () => [...evaluation.comparable, ...evaluation.review_required, ...evaluation.unpriceable],
    [evaluation],
  );

  const { polygonColors, points } = useMemo(() => {
    const colors = new Map();
    const pts = [];
    for (const c of candidates) {
      if (!c.jurisdiction_code) continue;
      const iso = globeKey(c.jurisdiction_code);
      const semantic = c.ui_status === "COMPARABLE" ? "gold" : c.ui_status === "REVIEW_REQUIRED" ? "amber" : "silver";
      colors.set(iso, STATUS_HEX[semantic]);
      const coord = JURISDICTION_COORDS[c.jurisdiction_code];
      if (coord) {
        pts.push({
          lat: coord.lat, lng: coord.lng, id: iso, iso, name: c.jurisdiction_code,
          tier: semantic, color: STATUS_HEX[semantic],
          jurisdictionName: coord.name, statusLabel: GLOBE_SEMANTIC[semantic].label,
          npcUsd: c.true_net_cost_usd, structureLabel: c.label,
        });
      }
    }
    return { polygonColors: colors, points: pts };
  }, [candidates]);

  return (
    <div>
      <div className="ovx-sec" style={{ padding: 0, overflow: "hidden" }}>
        <div className="dark-panel" style={{ position: "relative" }}>
          <Globe3D points={points} arcs={[]} height={420} pointRadius={0.2} polygonColors={polygonColors} />
        </div>
      </div>
      <div className="rec-cols">
        <div className="ovx-sec">
          <div className="oh"><b>Comparable</b><span className="n">{evaluation.comparable.length}</span></div>
          {evaluation.comparable.length === 0
            ? <div className="empty-state">None</div>
            : evaluation.comparable.map((c) => <CandidateRow key={c.structure_id} c={c} />)}
        </div>
        <div className="ovx-sec">
          <div className="oh"><b>Review required</b><span className="n">{evaluation.review_required.length}</span></div>
          <p className="text-tertiary small" style={{ marginBottom: 8 }}>
            Priced from a real statutory rate, but relocation-specific costs (travel, in-kind) are not yet modeled generically — not shown as a confident recommendation.
          </p>
          {evaluation.review_required.slice(0, 12).map((c) => <CandidateRow key={c.structure_id} c={c} />)}
        </div>
        <div className="ovx-sec">
          <div className="oh"><b>Unavailable</b><span className="n">{evaluation.unpriceable.length}</span></div>
          <p className="text-tertiary small" style={{ marginBottom: 8 }}>
            Production-capable, but the canonical authority-coverage registry has no defensible rate to price these with. Never a validated zero benefit.
          </p>
          {evaluation.unpriceable.slice(0, 12).map((c) => <CandidateRow key={c.structure_id} c={c} />)}
        </div>
      </div>
    </div>
  );
}
