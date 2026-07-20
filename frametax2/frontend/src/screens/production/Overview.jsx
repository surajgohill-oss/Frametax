import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import Globe3D from "../../components/Globe3D";
import { buildGlobeData } from "../../lib/globeData";
import ProductionDetails from "../../components/ProductionDetails";
import BudgetRail from "../../components/BudgetRail";

// Overview — approved closeout structure (restored from the approved-design
// migration, commit 9644759):
//   LEFT   — Production Facts (ProductionDetails: the Overview view of the
//            same Production Record the Workspace Inspector edits — POST
//            /people, role-level nationality; no duplicate input model)
//            + script-derived Production Requirements.
//   CENTER — Project Globe (the production Globe3D engine, unmodified,
//            graphite/obsidian direction) + the compact jurisdiction
//            snapshot strip: exactly four cards, each only jurisdiction /
//            incentive / net production cost; selecting one opens the
//            detailed scenario view.
//   RIGHT  — Budget Rail (BudgetRail: collapsed-by-default traceability
//            view over the canonical pkg.register; each line opens the
//            account Inspector, which carries the real qualified /
//            partially-qualified / excluded state from the QPE engine —
//            nothing recalculated here).

const JUR_NAMES = {
  MU: "Mauritius", GR: "Greece", IE: "Ireland", MT: "Malta",
  GB: "United Kingdom", US: "United States", ES: "Spain", FJ: "Fiji",
  IT: "Italy", FR: "France", DE: "Germany", AU: "Australia",
  NZ: "New Zealand", CA: "Canada", IN: "India", ZA: "South Africa",
};
const jurName = (code) => JUR_NAMES[code] || code || "—";

export default function Overview() {
  const { data, error, loading, refetch } = useCineGlobe();
  const navigate = useNavigate();
  const { openInspector } = useAppState();

  const allocated = data?.structures?.allocated_structures;

  // Globe data — identical derivation to ProjectGlobe.jsx and Workspace's
  // Map/Split modes. One globe engine for the whole app, never forked.
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, structuresByCode } = useMemo(
    () => buildGlobeData(allocated, rankById),
    [allocated, rankById],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, people } = data;

  // Jurisdiction snapshot strip — the four whole-production jurisdiction
  // options (single-country baseline + full relocations), in optimizer rank
  // order. Values are the same canonical fields the Workspace lanes render
  // (total_incentive_floor_usd / npc_with_adjustments_usd).
  const structById = new Map((allocated?.structures || []).map((s) => [s.structure_id, s]));
  const snapshot = (allocated?.ranking || [])
    .map((r) => structById.get(r.structure_id))
    .filter((s) => s && (s.structure_type === "single_country" || s.structure_type === "full_relocation"))
    .slice(0, 4);

  function handleGlobeClick(pt) {
    const s = (structuresByCode.get(pt.id) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === pt.id);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  return (
    <div className="screen ovxg-screen">
      <div className="ovxg-grid">

        {/* ── LEFT — Production Facts + Production Requirements ─────────── */}
        <div className="ovxg-col">
          <ProductionDetails
            people={people}
            requirements={production.physical_requirements}
            refetch={refetch}
          />
        </div>

        {/* ── CENTER — Project Globe + jurisdiction snapshot strip ──────── */}
        <div className="ovxg-col">
          <section className="ovx-sec ovxg-globe-sec">
            <div className="oh"><b>Project Globe</b><button className="act" onClick={() => navigate("/production/globe")}>Full screen →</button></div>
            <div className="ovxg-globe-wrap dark-panel">
              <Globe3D points={points} arcs={arcs} height={420} onPointClick={handleGlobeClick} />
            </div>
          </section>

          <div className="scenario-strip">
            {snapshot.map((s) => (
              <button
                className="strip-cell"
                key={s.structure_id}
                onClick={() => navigate("/production/scenarios", { state: { structureId: s.structure_id } })}
              >
                <span className="strip-name">{jurName(s.primary_jurisdiction)}</span>
                <span className="strip-type">
                  Incentive {s.total_incentive_floor_usd ? `$${Math.round(s.total_incentive_floor_usd).toLocaleString()}` : "—"}
                </span>
                <span className="strip-npc mono">
                  {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : "not priced"}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* ── RIGHT — Budget Rail (traceability over the canonical register) ── */}
        <div className="ovxg-col">
          <BudgetRail
            production={production}
            register={pkg.register}
            onSelectAccount={(line) => openInspector("account", line)}
          />
        </div>

      </div>
    </div>
  );
}
