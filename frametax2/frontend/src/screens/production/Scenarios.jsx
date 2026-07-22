import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken } from "../../lib/format";
import { useAppState } from "../../state/AppState";

const MAX_VISIBLE = 6;

// Scenarios — the approved artifact comparison view: the same structures as
// the Workspace rack, aligned as columns for a reading pass. Every figure is
// read verbatim from allocated_structures (Qualified spend = per-segment QPE
// summed; Incentive = total_incentive_floor_usd; NPC = npc_with_adjustments).
//
// Canonical behavior: only the MAX_VISIBLE (6) active working scenarios are
// shown as columns at once — never an unbounded/scrolling wall of every
// composed structure. Ranked (priced) structures fill the visible slots
// first; anything beyond that is reachable through the scenario selector,
// which swaps a chosen structure into the last visible slot rather than
// expanding the table.
export default function Scenarios() {
  const { data, error, loading } = useCineGlobe();
  const { openInspector } = useAppState();
  const location = useLocation();
  const openedFromNav = useRef(false);
  const [swapId, setSwapId] = useState("");

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
  const gross = production.gross_budget_usd;
  const qpe = (s) => s.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;

  // Rank order first (fully-priced structures, best NPC first), then
  // everything unranked (drafts/blocked) in the order the backend composed
  // them — a stable, meaningful ordering for "the six active scenarios."
  const ordered = [...allocated.structures].sort((a, b) => {
    const ra = rankById.get(a.structure_id)?.rank ?? Infinity;
    const rb = rankById.get(b.structure_id)?.rank ?? Infinity;
    return ra - rb;
  });
  const base = ordered.slice(0, MAX_VISIBLE);
  const overflow = ordered.slice(MAX_VISIBLE);
  const swapped = swapId ? ordered.find((s) => s.structure_id === swapId) : null;
  // The selector swaps a chosen overflow scenario into the last visible
  // slot — the visible count never exceeds MAX_VISIBLE.
  const cols = swapped ? [...base.slice(0, MAX_VISIBLE - 1), swapped] : base;

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
        {overflow.length > 0 && ` Showing the ${MAX_VISIBLE} active working scenarios.`}
      </p>
      {overflow.length > 0 && (
        <div className="sc-selector">
          <label htmlFor="sc-swap">Additional scenario</label>
          <select
            id="sc-swap"
            className="field-select"
            value={swapId}
            onChange={(e) => setSwapId(e.target.value)}
          >
            <option value="">— {base[base.length - 1]?.label} —</option>
            {overflow.map((s) => (
              <option key={s.structure_id} value={s.structure_id}>{s.label}</option>
            ))}
          </select>
        </div>
      )}
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
