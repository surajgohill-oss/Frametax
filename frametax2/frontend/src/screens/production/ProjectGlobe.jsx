import { useMemo } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildGlobeData, structureTier } from "../../lib/globeData";
import { useAppState } from "../../state/AppState";
import { Money, humanizeToken } from "../../lib/format";

// Project Globe — the production's candidate jurisdictions and treaty routes
// on the canonical globe. Same live model as the Workspace Map mode, given
// its own full section per the approved artifact nav. Marker click opens the
// jurisdiction segment / structure recommendation in the Inspector.
export default function ProjectGlobe() {
  const { data, error, loading } = useCineGlobe();
  const { openInspector, leadingStructureId, selectedJurisdiction, setSelectedJurisdiction } = useAppState();

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, structuresByCode } = useMemo(
    () => buildGlobeData(allocated, rankById, { leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, leadingStructureId, selectedJurisdiction],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  function handleClick(pt) {
    setSelectedJurisdiction(pt.id);
    const s = (structuresByCode.get(pt.id) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === pt.id);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  return (
    <div className="globe-screen">
      <div className="globe-screen-context">
        <p className="screen-eyebrow">Project Globe</p>
        <h1 className="serif" style={{ fontSize: 20 }}>Candidate jurisdictions</h1>
        <p className="text-tertiary small">
          Every jurisdiction this production has allocated spend into. Gold = top-ranked fully priced
          structure · jade = another fully priced structure · amber = allocated but blocked · silver =
          allocated, not the top-priced route.
        </p>
        <div className="sc-jurlist">
          {allocated.structures.map((s) => (
            <div className="portfolio-chip" key={s.structure_id} onClick={() => handleClick({ id: s.participants?.[0] })}>
              <span className={`dot ${structureTier(s, rankById)}`} />
              <div>
                <div className="row-title small">{s.label}</div>
                <div className="row-sub">
                  {humanizeToken(s.structure_type)} · {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : `${s.blockers.length} blocker${s.blockers.length === 1 ? "" : "s"}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="globe-screen-canvas">
        <Globe3D points={points} arcs={arcs} height={560} onPointClick={handleClick} />
        <p className="globe-caption small" style={{ borderRadius: "0 0 var(--radius-lg) var(--radius-lg)" }}>
          {arcs.length > 0
            ? "Dashed arcs mark treaty co-production routes."
            : `No treaty co-production structure is currently priced — see coverage.reachable_treaty_partners (${allocated.coverage.reachable_treaty_partners.length}) in Knowledge.`}
        </p>
      </div>
    </div>
  );
}
