import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, activeStructure } from "../../lib/globeData";
import ProductionDetails from "../../components/ProductionDetails";
import BudgetRail from "../../components/BudgetRail";
import FXStrip from "../../components/FXStrip";

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
  const {
    inspector, openInspector, leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
  } = useAppState();
  const [globeMode, setGlobeMode] = useState("jurisdictions");
  const [hover, setHover] = useState(null);

  const allocated = data?.structures?.allocated_structures;

  // Globe data — identical derivation to ProjectGlobe.jsx and Workspace's
  // Map/Split modes. One globe engine for the whole app, never forked.
  // Same shared leadingStructureId/selectedJurisdiction as the Workspace —
  // choosing a leading structure or jurisdiction on either screen updates
  // both without a refresh.
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
  );
  const structure = allocated ? activeStructure(allocated, leadingStructureId) : null;

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, people, economics } = data;

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
    const code = pt.jurisdictionCode || pt.id;
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  return (
    <div className="screen ovxg-screen">
      {/* Approved FX / production-economics strip — beneath the header,
          above the three-column layout. Real /economics.fx_horizons data
          (spot + forward points); commentary only, never an optimizer
          input (pricing stays on current rates). */}
      <FXStrip economics={economics} />

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
            <div className="oh">
              <b>Project Globe</b>
              <div className="wsx-viewtabs" style={{ marginLeft: 10 }}>
                <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
                <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
              </div>
              <button className="act" onClick={() => navigate("/production/globe")}>Full screen →</button>
            </div>
            <div className="ovxg-globe-wrap dark-panel" style={{ position: "relative" }}>
              <Globe3D
                points={points}
                arcs={arcs}
                height={420}
                pointRadius={0.2}
                polygonColors={polygonColors}
                selectedIso={selectedIso}
                selectedLat={selectedLat}
                selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
                // The app-level floating Inspector (--inspector-width=400px)
                // can cover the right edge of the viewport, including part of
                // this panel on narrower layouts — same reframe as Project
                // Globe, so a selected country never disappears behind it.
                obscuredRightPx={inspector ? 400 : 0}
                onPointClick={handleGlobeClick}
                onPointHover={setHover}
              />
              {hover && (
                <div className="globe-tooltip">
                  <strong>{hover.jurisdictionName}</strong>
                  <div className="text-tertiary small">{hover.statusLabel}</div>
                  {hover.role && <div className="text-tertiary small">{hover.role}</div>}
                  {hover.incentiveUsd != null && <div className="small">Incentive <Money value={hover.incentiveUsd} /></div>}
                  {hover.npcUsd != null && <div className="small">NPC <Money value={hover.npcUsd} /></div>}
                </div>
              )}
            </div>
          </section>

          <div className="scenario-strip">
            {snapshot.map((s) => (
              <button
                className={`strip-cell${s.structure_id === structure?.structure_id ? " active" : ""}`}
                key={s.structure_id}
                onClick={() => {
                  // Selecting a jurisdiction snapshot IS choosing the leading
                  // structure — synchronizes Globe, Budget Rail, and Inspector
                  // immediately, then still offers the full comparison view.
                  setLeadingStructureId(s.structure_id);
                  setSelectedJurisdiction(s.primary_jurisdiction);
                }}
                onDoubleClick={() => navigate("/production/scenarios", { state: { structureId: s.structure_id } })}
              >
                <span className="strip-name">{jurName(s.primary_jurisdiction)}</span>
                <span className="strip-type">
                  Incentive {s.selected_incentive_usd ? `$${Math.round(s.selected_incentive_usd).toLocaleString()}` : "—"}
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
            structure={structure}
            economics={economics}
            onSelectAccount={(line, alloc) => openInspector("account", {
              ...line,
              crossRef: alloc ? [{
                structureId: structure.structure_id,
                structureLabel: structure.label,
                jurisdictionCode: alloc.jurisdictionCode,
                claimsIncentive: alloc.claimsIncentive,
                qpeUsd: alloc.included ? line.amount : 0,
                incentiveFloorUsd: alloc.creditContributionUsd,
              }] : [],
            })}
          />
        </div>

      </div>
    </div>
  );
}
