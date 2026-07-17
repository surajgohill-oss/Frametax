import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LayoutDashboard } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { useProjectStatus } from "../../lib/useProjectStatus";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken } from "../../lib/format";
import { buildGlobeData, structureTier } from "../../lib/globeData";
import Globe3D from "../../components/Globe3D";
import ProductionDetails from "../../components/ProductionDetails";
import BudgetRail from "../../components/BudgetRail";

// Overview answers: WHAT is this production?
// (Workspace answers how it should be structured and optimized — optimizer
// inputs and treaty-solving controls live there, never here.)

// Maximum-size square globe frame: CSS gives the frame aspect-ratio 1/1 at
// full center-column width; Globe3D takes a fixed pixel height, so we
// measure the frame once layout settles and mount the globe at that size.
function SquareGlobe({ points, arcs, onPointClick }) {
  const frameRef = useRef(null);
  const [size, setSize] = useState(0);

  useLayoutEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    const measure = () => {
      const w = Math.round(el.getBoundingClientRect().width);
      if (w > 0) setSize((s) => (s === 0 ? w : s));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="globe-frame dark-panel" ref={frameRef}>
      {size > 0 && <Globe3D points={points} arcs={arcs} height={size} onPointClick={onPointClick} />}
    </div>
  );
}

function fmtCompact(v) {
  if (v === null || v === undefined) return null;
  return `$${(Number(v) / 1e6).toFixed(2)}M`;
}

export default function Overview() {
  const { data, error, loading, refetch } = useCineGlobe();
  const navigate = useNavigate();
  const { openInspector } = useAppState();
  const { meta } = useProjectStatus(data?.production?.production_id);

  const allocated = data?.structures?.allocated_structures;
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

  const { production, pkg, structures, people } = data;
  const best = structures.ranking.find((r) => r.is_priceable);
  const leadingLabel = best ? best.label.replace(/^Relocate /, "").replace(/ -> /g, " → ") : null;
  const setting = pkg.script?.attributes?.setting?.value;

  function handleGlobeClick(pt) {
    const list = structuresByCode.get(pt.id) || [];
    const s = list[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === pt.id);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  // Four leading structures — compact, subordinate to the globe: name,
  // structure type, NPC, leading indicator. No card-level financial detail.
  const strip = structures.ranking.slice(0, 4).map((r) => {
    const full = allocated?.structures.find((s) => s.structure_id === r.structure_id);
    return {
      id: r.structure_id,
      name: r.label.replace(/^Relocate /, "").replace(/ -> /g, " → "),
      type: full ? humanizeToken(full.structure_type) : "",
      npc: r.is_priceable ? fmtCompact(r.conservative_npc_usd) : null,
      leading: r.rank === 1 && r.is_priceable,
      tier: full ? structureTier(full, rankById) : "silver",
    };
  });

  return (
    <div className="screen ov-screen">
      <section className="overview-hero">
        <div className="overview-hero-art" aria-hidden="true" />
        <div className="overview-hero-body">
          <div style={{ display: "flex", alignItems: "flex-start" }}>
            <div>
              <p className="screen-eyebrow">Feature · {pkg.confidence} confidence</p>
              <h1 className="serif overview-title">{production.production_name}</h1>
            </div>
            <div className="overview-hero-actions">
              <button className="hero-action primary" onClick={() => navigate("/production/workspace")}>
                <LayoutDashboard size={14} strokeWidth={1.8} /> Open Workspace
              </button>
            </div>
          </div>
          {setting && <p className="overview-logline">Setting — {setting}.</p>}
          <div className="overview-stats">
            <div>
              <span className="text-tertiary small">Total production budget</span>
              <div className="mono overview-stat-value"><Money value={production.gross_budget_usd} /></div>
            </div>
            <div>
              <span className="text-tertiary small">Production stage</span>
              <div className="overview-stat-value">{meta.label}</div>
            </div>
            <div>
              <span className="text-tertiary small">Leading structure</span>
              <div className="overview-stat-value">{leadingLabel || <span className="text-tertiary">None fully priced yet</span>}</div>
            </div>
            {best && (
              <div>
                <span className="text-tertiary small">Net production cost</span>
                <div className="mono overview-stat-value"><Money value={best.conservative_npc_usd} /></div>
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="ov-grid">
        <ProductionDetails people={people} script={pkg.script} refetch={refetch} />

        <div className="ov-center">
          <SquareGlobe points={points} arcs={arcs} onPointClick={handleGlobeClick} />
          <div className="scenario-strip">
            {strip.map((s) => (
              <button className="strip-cell" key={s.id} onClick={() => navigate("/production/workspace")}>
                <span className="strip-name">
                  {s.leading && <span className="dot gold" />}
                  {s.name}
                </span>
                {s.type && <span className="strip-type">{s.type}</span>}
                <span className="strip-npc mono">{s.npc || "not yet priced"}</span>
              </button>
            ))}
          </div>
        </div>

        <BudgetRail
          production={production}
          register={pkg.register}
          onSelectAccount={(line) => openInspector("account", line)}
        />
      </div>
    </div>
  );
}
