import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, scenarioDisplay } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import { patchProject } from "../../api";
import { classifyStructure, isBaselineStructure } from "../../lib/productionOptions";

const MAX_VISIBLE = 6;

// Scenarios — the approved artifact comparison view: the same structures as
// the Workspace rack, aligned as columns for a reading pass. Every figure is
// read verbatim from allocated_structures (Qualified spend = per-segment QPE
// summed; Incentive = total_incentive_floor_usd; NPC = npc_with_adjustments).
//
// Scenarios UI contract (this batch): the SAME classification taxonomy
// Overview's Production Options cards use (lib/productionOptions.js) --
// Current/Base, Full Relocation, Hybrid/Component, Official Treaty
// Co-Production -- applied here as a per-column badge, and the SAME
// comparable/review split (allocated.ranking's own is_fully_priced flag,
// already the existing signal canonical_production_view.py and
// little_utopia_state.py both compute) used to keep review/unavailable
// structures out of the main comparison table entirely, in their own
// section below, rather than mixed into the same swappable column set.
//
// Canonical behavior: only the MAX_VISIBLE (6) comparable structures are
// shown as table columns at once — never an unbounded/scrolling wall.
// Ranked (comparable) structures fill the visible slots first; any
// additional COMPARABLE structures beyond that are reachable through the
// scenario selector, which swaps one into the last visible slot rather
// than expanding the table. Review/unavailable structures are never
// swapped into this table — see the Review section instead.
export default function Scenarios() {
  const { projectId } = useParams();
  const { data, error, loading } = useCineGlobe(projectId);
  const { openInspector, leadingStructureId, setLeadingStructureId } = useAppState();
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

  // Comparable vs Review/Unavailable — the SAME is_fully_priced flag on
  // the ranking entry (not the structure entry) that canonical_production_
  // view.py deliberately sets false for priced-but-not-regionally-
  // validated structures, and little_utopia_state.py's rank_allocated_
  // structures sets false for genuinely unpriced ones. Never a new
  // frontend calculation — this flag already existed and already drove
  // Overview's Top Six selection.
  const comparableOrdered = [...allocated.structures]
    .filter((s) => rankById.get(s.structure_id)?.is_fully_priced)
    .sort((a, b) => (rankById.get(a.structure_id)?.rank ?? Infinity) - (rankById.get(b.structure_id)?.rank ?? Infinity));
  const reviewOrdered = allocated.structures.filter((s) => !rankById.get(s.structure_id)?.is_fully_priced);

  const base = comparableOrdered.slice(0, MAX_VISIBLE);
  const overflow = comparableOrdered.slice(MAX_VISIBLE);
  const swapped = swapId ? comparableOrdered.find((s) => s.structure_id === swapId) : null;
  // The selector swaps a chosen COMPARABLE overflow scenario into the
  // last visible slot — the visible count never exceeds MAX_VISIBLE, and
  // a review/unavailable structure can never enter this table this way.
  const cols = swapped ? [...base.slice(0, MAX_VISIBLE - 1), swapped] : base;

  const baseline = allocated.structures.find(isBaselineStructure);
  const baseNpc = baseline?.npc_with_adjustments_usd ?? null;

  function inspect(s) {
    if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
    else if (s.segments?.[0]) openInspector("allocation-segment", { ...s.segments[0], structureLabel: s.label });
  }

  // Scenario Manager selection — synchronizes Globe / Budget Rail /
  // Overview immediately (shared AppState.leadingStructureId), no refresh.
  // Phase C write-through: also persists to the real Project row so the
  // choice survives a reload/restart. Fire-and-forget — the shared state
  // update above is what every view already reads synchronously, so a
  // slow/failed PATCH never blocks the UI; it never triggers the optimizer.
  //
  // Known, deferred gap (see the matching note in Workspace.jsx): the
  // optimizer's in-memory structures use their own string identifiers, not
  // real production_structures.id UUIDs. Only the one structure the Phase C
  // migration persisted has a real row — selecting any other 422s on the
  // UUID FK, expected until a later phase persists optimizer-generated
  // structures, not a failure.
  function selectAsLeading(s) {
    if (!s.is_fully_priced) return;
    setLeadingStructureId(s.structure_id);
    const projectId = data?.production?.project_id;
    if (projectId) {
      patchProject(projectId, { leading_structure_id: s.structure_id }).catch((err) => {
        if (String(err.message).startsWith("422")) {
          console.info(`[Scenarios] leading structure ${s.structure_id} has no persisted backend row yet (optimizer-generated, not yet migrated) — UI selection still applied`);
        } else {
          console.error("[Scenarios] failed to persist leading structure to backend:", err);
        }
      });
    }
  }

  const rows = [
    ["Gross budget", () => gross, true],
    ["Qualified spend", (s) => (s.is_fully_priced ? qpe(s) : null), false],
    ["Gross incentive", (s) => (s.is_fully_priced ? s.selected_incentive_usd : null), false],
  ];

  // FX presentation is intentionally hidden here for now (see
  // Workspace.jsx's ScenarioCard for the matching note) — the backend
  // still computes and serves fx_basis/fx_delta_usd on every priced
  // structure; a per-currency-exposed-spend adjustment view belongs in
  // the Inspector later, not a prominent row that reads as a real
  // economics adjustment when today it is exchange-rate provenance only.

  return (
    <div className="screen sc-screen">
      <p className="sc-note">
        Comparable Options for <b>{production.production_name}</b> — the same lanes as the Workspace
        rack, aligned for a reading pass. Click any structure to trace its derivation.
        {overflow.length > 0 && ` Showing the ${MAX_VISIBLE} active working scenarios.`}
        {" "}Regional production-cost normalization (MFNI) is not yet applied. Only structures whose
        regional cost is validated for direct comparison appear as columns here — the current/base
        structure needs no such adjustment by construction. Structures that are priced but not yet
        regionally validated, or not priced at all, appear in Review / Needs Validation below; their
        headline cost is not yet a fair comparison against the columns above.
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
            <option value="">— {scenarioDisplay(base[base.length - 1] || {}).title} —</option>
            {overflow.map((s) => (
              <option key={s.structure_id} value={s.structure_id}>{scenarioDisplay(s).title}</option>
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
                const { title, subtitle } = scenarioDisplay(s);
                const isLeading = s.structure_id === leadingStructureId
                  || (!leadingStructureId && rank?.rank === 1);
                const classification = classifyStructure(s);
                return (
                  <th
                    key={s.structure_id}
                    className={isLeading ? "leading" : ""}
                    onClick={() => inspect(s)}
                    onDoubleClick={() => selectAsLeading(s)}
                    title="Click to inspect · double-click to set as leading structure"
                  >
                    <span className={`badge ${classification.accent}`}>{classification.label}</span>
                    <span className="nm serif">{title}</span>
                    <span className="sub">{subtitle}{rank?.rank ? ` · rank ${rank.rank}` : ""}{isLeading ? " · leading" : ""}</span>
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
            <tr>
              <td className="lbl">Vs. current / base</td>
              {cols.map((s) => {
                const npc = s.npc_with_adjustments_usd;
                const diff = npc != null && baseNpc != null && !isBaselineStructure(s) ? npc - baseNpc : null;
                return (
                  <td key={s.structure_id} className="num">
                    {diff == null ? "—" : <>{diff > 0 ? "+" : ""}<Money value={diff} /></>}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {reviewOrdered.length > 0 && (
        <section className="region" style={{ marginTop: 20 }}>
          <div className="region-title">
            <span>Review / Needs Validation</span>
            <span className="count">{reviewOrdered.length}</span>
          </div>
          <div className="row-list">
            {reviewOrdered.map((s) => {
              const rank = rankById.get(s.structure_id);
              const { title } = scenarioDisplay(s);
              const classification = classifyStructure(s);
              const reasons = rank?.excluded_from_ranking_because || (s.blockers?.length ? s.blockers : null);
              return (
                <div key={s.structure_id} className="row-item" onClick={() => inspect(s)} style={{ cursor: "pointer" }}>
                  <span className={`dot ${classification.accent}`} />
                  <div className="row-main">
                    <div className="row-title">
                      {title} <span className={`badge ${classification.accent}`} style={{ marginLeft: 6 }}>{classification.label}</span>
                    </div>
                    <div className="row-sub">{reasons ? reasons.join(" · ") : "Not yet priced."}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
