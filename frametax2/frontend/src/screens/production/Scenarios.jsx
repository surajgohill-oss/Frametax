import { useEffect, useMemo, useRef } from "react";
import { useLocation } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken } from "../../lib/format";
import { useAppState } from "../../state/AppState";

// Scenarios — the approved artifact comparison view: the same structures as
// the Workspace rack, aligned as columns for a reading pass. Every figure is
// read verbatim from allocated_structures (Qualified spend = per-segment QPE
// summed; Incentive = total_incentive_floor_usd; NPC = npc_with_adjustments).
export default function Scenarios() {
  const { data, error, loading } = useCineGlobe();
  const { openInspector } = useAppState();
  const location = useLocation();
  const openedFromNav = useRef(false);

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);

  // Deep link from the Overview jurisdiction snapshot strip: arrive with a
  // canonical structure_id in navigation state -> open that scenario's
  // detail (the same Inspector trace a header click opens). Once only.
  useEffect(() => {
    const structureId = location.state?.structureId;
    if (!structureId || !allocated || openedFromNav.current) return;
    const s = allocated.structures.find((x) => x.structure_id === structureId);
    if (!s) return;
    openedFromNav.current = true;
    if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
    else if (s.segments?.[0]) openInspector("allocation-segment", { ...s.segments[0], structureLabel: s.label });
  }, [location.state, allocated, openInspector]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production } = data;
  const cols = allocated.structures;
  const gross = production.gross_budget_usd;
  const qpe = (s) => s.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;

  function inspect(s) {
    if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
    else if (s.segments?.[0]) openInspector("allocation-segment", { ...s.segments[0], structureLabel: s.label });
  }

  const rows = [
    ["Gross budget", () => gross, true],
    ["Qualified spend", (s) => (s.is_fully_priced ? qpe(s) : null), false],
    ["Gross incentive", (s) => (s.is_fully_priced ? s.selected_incentive_usd : null), false],
  ];

  return (
    <div className="screen sc-screen">
      <p className="sc-note">
        Alternative structures for <b>{production.production_name}</b> — the same lanes as the Workspace
        rack, aligned for a reading pass. Click any structure to trace its derivation.
      </p>
      <div className="sc-wrap">
        <table className="sc-table">
          <thead>
            <tr>
              <th />
              {cols.map((s) => {
                const rank = rankById.get(s.structure_id);
                return (
                  <th key={s.structure_id} onClick={() => inspect(s)}>
                    <span className="nm serif">{s.label}</span>
                    <span className="sub">{humanizeToken(s.structure_type)}{rank?.rank ? ` · rank ${rank.rank}` : ""}</span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, get, strong]) => (
              <tr key={label}>
                <td className="lbl">{label}</td>
                {cols.map((s) => {
                  const v = get(s);
                  return <td key={s.structure_id} className={strong ? "" : "num"}>{v == null ? "—" : <Money value={v} />}</td>;
                })}
              </tr>
            ))}
            <tr className="net">
              <td className="lbl">Net production cost</td>
              {cols.map((s) => (
                <td key={s.structure_id} onClick={() => inspect(s)} className="netv">
                  {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : <span className="text-tertiary">not priced</span>}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
