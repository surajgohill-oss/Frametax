import { useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

// Reports — the approved artifact "generated ledger" view. Reports are
// composed from the live model (no separate report store exists in this
// backend), so each card is derived from the current allocated structures
// and question queue. Export/Share are disabled until a generation engine
// is wired — nothing here is fabricated.
export default function Reports() {
  const { projectId } = useParams();
  const { data, error, loading } = useCineGlobe(projectId);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, legal, structures } = data;
  const allocated = structures.allocated_structures;
  const best = allocated.structures.find((s) => s.structure_id === allocated.ranking.find((r) => r.rank === 1)?.structure_id);
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
