import { useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import { activeStructure } from "../../lib/globeData";
import { bestPricedCandidate } from "../../lib/bestPricedCandidate";

// Reports — the approved artifact "generated ledger" view. Reports are
// composed from the live model (no separate report store exists in this
// backend), so each card is derived from the current allocated structures
// and question queue. Export/Share are disabled until a generation engine
// is wired — nothing here is fabricated.
//
// Final non-Globe closeout, Item A (canonical scenario-selection
// consistency): this screen used to determine its "leading structure"
// with a rank==1-only lookup and NO fallback, while Overview/Workspace
// additionally fell back to the best-priced candidate whenever rank 1
// was absent (comparable_count==0 — a real, common state, e.g. Bad
// Hombres). That meant the same production state could show "No
// structure is fully priced yet" here while Overview/Workspace both
// displayed a real leading structure — a genuine scenario-truth
// disagreement, not merely a display difference. Fixed by resolving
// through the exact same activeStructure()/bestPricedCandidate() chain
// Overview and Workspace already use, including the SAME shared
// AppState leadingStructureId producer override, so all three screens
// can never disagree about which structure_id is "the" leading one for
// a given production state.
export default function Reports() {
  const { projectId } = useParams();
  const { data, error, loading } = useCineGlobe(projectId);
  const { leadingStructureId } = useAppState();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, legal, structures } = data;
  const allocated = structures.allocated_structures;
  const best = activeStructure(allocated, leadingStructureId) || bestPricedCandidate(allocated);
  const priced = allocated.structures.filter((s) => s.is_fully_priced).length;
  const blocked = allocated.structures.length - priced;
  const openGrey = legal.grey_areas_current.filter((g) => g.status === "open");
  const swing = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);
  const qpe = best?.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;

  const reports = [
    {
      name: `Net production cost — ${best ? best.label : "leading structure"}`,
      desc: "The full cost decomposition for the current leading structure, derived from the live allocation model.",
      rows: best && best.is_fully_priced
        ? [
            ["Gross budget", <Money value={production.gross_budget_usd} />],
            ["Qualified spend", <Money value={qpe} />],
            ["Gross incentive", <Money value={best.selected_incentive_usd} />],
            ["Net production cost", <Money value={best.npc_with_adjustments_usd} />],
          ]
        : [["Status", "No structure is fully priced yet"]],
    },
    {
      name: "Structure evaluation summary",
      desc: "Coverage of the candidate structures currently under evaluation for this production.",
      rows: [
        ["Structures evaluated", String(allocated.structures.length)],
        ["Fully priced", String(priced)],
        ["Blocked / partial", String(blocked)],
        ["Open questions", String(pkg.missing_inputs.length + openGrey.length)],
        ["Conditional swing", swing ? <Money value={swing} /> : "—"],
      ],
    },
  ];

  return (
    <div className="screen sc-screen">
      <p className="sc-note">
        Reports for <b>{production.production_name}</b> generate from the live model — nothing is stored
        separately, so each reflects the current state at read time.
      </p>
      {reports.map((r) => (
        <div className="rpt-card" key={r.name}>
          <h3 className="serif">{r.name}</h3>
          <div className="rpt-meta">generated from live model</div>
          <p className="rpt-desc">{r.desc}</p>
          {r.rows.map((row, i) => (
            <div className="rpt-row" key={i}><span>{row[0]}</span><b className="mono">{row[1]}</b></div>
          ))}
          <div className="rpt-acts">
            <button className="ovx-btn" disabled title="No report-generation/export engine is wired yet">Export PDF</button>
            <button className="ovx-btn" disabled title="No report-generation/export engine is wired yet">Share link</button>
          </div>
        </div>
      ))}
    </div>
  );
}
