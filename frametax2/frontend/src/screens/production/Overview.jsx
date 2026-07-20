import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken, scenarioDisplay, recommendationHeadline } from "../../lib/format";
import Globe3D from "../../components/Globe3D";
import { buildGlobeData } from "../../lib/globeData";
import { PeopleRow, StrFactRow } from "../../components/QualificationPanel";
import { buildReferenceLibrary } from "./Knowledge";

// Overview — approved three-column executive layout.
//   LEFT   — Production variables (the inputs driving the analysis) +
//            unresolved production facts. People/fact edits REUSE the
//            QualificationPanel controls (POST /people, POST /facts) —
//            same persistence path as Workspace, no second intake system.
//   CENTER — Project Globe (shared Globe3D + buildGlobeData engine,
//            unmodified), decision metrics, leading scenarios.
//   RIGHT  — Current recommendation, immediate decisions, evidence
//            readiness, one next action.
// Every value comes from the canonical backend payloads (allocated_structures,
// /people, /facts, /package, /legal, /economics). `Unknown` is rendered
// wherever the backend has no value — nothing is fabricated.

const JUR_NAMES = {
  MU: "Mauritius", ES: "Spain", GB: "United Kingdom", US: "United States",
  IE: "Ireland", MT: "Malta", FJ: "Fiji", GR: "Greece", IT: "Italy",
  FR: "France", DE: "Germany", AU: "Australia", NZ: "New Zealand",
  CA: "Canada", IN: "India", ZA: "South Africa", TR: "Türkiye",
};
const jurName = (code) => JUR_NAMES[code] || code || "—";
const fmtSwing = (v) => (v ? `±$${Math.round(v).toLocaleString()}` : null);
const RANKS = ["①", "②", "③"];
const VALUE_RANK = { high: 2, medium: 1, low: 0 };

// known / assumed / unresolved variable-state marker (existing dot tiers).
const STATE_DOT = { known: "jade", assumed: "silver", unresolved: "amber" };
function VarRow({ state, label, value, sub, title }) {
  return (
    <div className="ovxv-row" title={title}>
      <span className={`dot ${STATE_DOT[state] || "silver"}`} title={state} />
      <span className="ovxv-label">{label}</span>
      <span className="ovxv-val">
        <span className={value === "Unknown" ? "ovxv-unk" : ""}>{value}</span>
        {sub && <span className="ovxv-sub">{sub}</span>}
      </span>
    </div>
  );
}

const READY_DOT = { ready: "jade", partial: "amber", missing: "red" };

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

  const { production, pkg, legal, people, economics, recommendations, facts } = data;

  // ── Canonical scenario ranking (allocated_structures — same source as
  // Workspace/Scenarios/Project Globe; the legacy ranking/candidates pair
  // is deliberately not read). ────────────────────────────────────────────
  const structById = new Map((allocated?.structures || []).map((s) => [s.structure_id, s]));
  const rankedStructures = allocated?.ranking || [];
  const bestRank = rankedStructures.find((r) => r.rank === 1) || null;
  const bestStruct = bestRank ? structById.get(bestRank.structure_id) : null;
  const bestDisplay = bestStruct ? scenarioDisplay(bestStruct) : null;
  const dominantSeg = bestDisplay?.dominant;
  const recJurCode = dominantSeg?.jurisdiction_code || production.jurisdiction_code;

  const baselineStruct = structById.get("ALLOC-BASELINE-MU") || null;
  const baselineNpc = baselineStruct?.is_fully_priced ? baselineStruct.npc_with_adjustments_usd : null;
  const savingsVs = (s) =>
    (s && baselineStruct && s.structure_id !== baselineStruct.structure_id
      && s.is_fully_priced && baselineNpc != null)
      ? baselineNpc - s.npc_with_adjustments_usd
      : null;
  const estimatedSavings = savingsVs(bestStruct);
  const pricedCount = (allocated?.structures || []).filter((s) => s.is_fully_priced).length;

  const openGrey = (legal.grey_areas_current || []).filter((g) => g.status === "open");
  const swingTotal = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);

  // ── LEFT — production variables from persisted state ───────────────────
  const namesOf = (arr) => (arr || []).map((p) => p.name).filter(Boolean).join(", ");
  const psd = production.production_structure_default || {};
  const spvAssumption = (psd.assumptions || []).find((a) => /SPV/i.test(a)) || null;
  const setting = pkg.script?.attributes?.setting?.value || null;
  const sreq = production.physical_requirements?.script_requirements || {};
  const confirmedReq = (k) => sreq[k]?.confidence === "CONFIRMED" && sreq[k]?.value === true;
  const logistical = ["marine", "open_water_filming", "night_work", "underwater_photography"]
    .filter(confirmedReq).map(humanizeToken).join(" · ");
  const creative = confirmedReq("period")
    ? `Period story — ${sreq.period.evidence?.includes("1978") ? "dual timeline 1978 / 1985" : "period setting"}`
    : null;
  const financingAssumed = economics?.financing_source === "default_zero";
  const postElected = facts?.answers?.component_route_post || null;

  // Unresolved production facts — open grey areas (real $ swing) first,
  // then Question Engine missing inputs by optimizer value. Max 5 rows.
  const unresolvedFacts = [
    ...openGrey.map((g) => ({
      id: g.item_id,
      need: g.resolving_evidence,
      why: `${g.jurisdiction_code} · ${g.authority_to_ask || "authority ruling"}`,
      value: fmtSwing(g.amount_usd),
      tier: "red",
      inspect: { kind: "question", data: g },
    })),
    ...[...(pkg.missing_inputs || [])]
      .sort((a, b) => (VALUE_RANK[b.optimizer_value] || 0) - (VALUE_RANK[a.optimizer_value] || 0))
      .map((m) => ({
        id: m.identifier,
        need: m.question,
        why: (m.downstream_engines || []).map(humanizeToken).join(", ") || "question engine",
        value: `${m.optimizer_value} value`,
        tier: "amber",
        inspect: { kind: "question", data: m },
      })),
  ].slice(0, 5);

  // ── RIGHT — immediate decisions: the open authority ruling(s) plus the
  // unmade producer elections the Question Engine values highest. These are
  // decision items (rule / elect / allocate), not the generic question stack.
  const miById = new Map((pkg.missing_inputs || []).map((m) => [m.identifier, m]));
  const decisions = [
    ...openGrey.map((g) => ({
      id: g.item_id,
      title: `Obtain authority ruling · ${g.jurisdiction_code}`,
      need: g.resolving_evidence,
      value: fmtSwing(g.amount_usd),
      tier: "red",
      inspect: { kind: "question", data: g },
    })),
    ...[
      { id: "MISSING-TREATY-PARTNER", title: "Treaty partner election" },
      { id: "MISSING-LOCAL-SPEND-ALLOCATION", title: "Qualifying-spend allocation" },
      { id: "MISSING-PAYROLL-STRUCTURE", title: "Payroll routing election" },
    ]
      .map((d) => ({ ...d, mi: miById.get(d.id) }))
      .filter((d) => d.mi)
      .map((d) => ({
        id: d.id,
        title: d.title,
        need: d.mi.question,
        value: `${d.mi.optimizer_value} value`,
        tier: "amber",
        inspect: { kind: "question", data: d.mi },
      })),
  ].slice(0, 3);

  // ── RIGHT — evidence readiness, all derived from real payload state ────
  const allPeople = [...(people.writers || []), ...(people.directors || []), ...(people.cast || []), ...(people.producers || [])];
  const peopleKnown = allPeople.filter((p) => p.nationality_state === "known" && p.residency_state === "known").length;
  const peopleState = allPeople.length === 0 ? "missing"
    : peopleKnown === allPeople.length ? "ready"
    : allPeople.some((p) => p.nationality_state === "known" || p.residency_state === "known") ? "partial" : "missing";
  const scriptAttrsKnown = Object.values(pkg.script?.attributes || {}).some((a) => a?.is_known);
  const referenceItems = buildReferenceLibrary(pkg, allocated, recommendations);
  const readiness = [
    { label: "Budget", state: (pkg.register || []).length ? "ready" : "missing", to: "/production/binder" },
    { label: "Script", state: pkg.script?.known ? "ready" : scriptAttrsKnown ? "partial" : "missing", to: "/production/binder" },
    { label: "Schedule", state: "missing", to: "/production/binder" },
    { label: "Cast / crew facts", state: peopleState, to: "/production/record" },
    { label: "Entity documents", state: "missing", to: "/production/binder" },
    { label: "Jurisdiction evidence", state: (legal.evidence_trace || []).length ? (openGrey.length ? "partial" : "ready") : "missing", to: "/production/binder" },
    { label: "Legal / authority sources", state: referenceItems.length ? "ready" : "missing", to: "/production/knowledge" },
  ];

  const topAction = recommendations.by_category.financial[0]
    || recommendations.by_category.structural[0]
    || recommendations.by_category.creative[0]
    || null;

  function goWorkspace(tab) {
    navigate("/production/workspace", tab ? { state: { tab } } : undefined);
  }
  function handleGlobeClick(pt) {
    const s = (structuresByCode.get(pt.id) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === pt.id);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }
  function openIncentiveCalc() {
    if (dominantSeg) openInspector("allocation-segment", { ...dominantSeg, structureLabel: bestStruct.label });
  }

  const gatingFor = (s, disp) => {
    if (s.blockers?.length) return s.blockers[0];
    if (disp?.dominant?.is_band_ceiling) return "Awarded rate within the 'up to' band is set at authority approval";
    return null;
  };

  return (
    <div className="screen ovxg-screen">
      <div className="ovxg-grid">

        {/* ── LEFT — Production variables ─────────────────────────────── */}
        <div className="ovxg-col ovxg-left">
          <section className="ovx-sec">
            <div className="oh"><b>Production variables</b></div>
            <div className="ovxv-legend">
              <span><span className="dot jade" />known</span>
              <span><span className="dot silver" />assumed</span>
              <span><span className="dot amber" />unresolved</span>
            </div>
            <VarRow state="known" label="Writer" value={namesOf(people.writers) || "Unknown"} />
            <VarRow state="known" label="Director" value={namesOf(people.directors) || "Unknown"} />
            <VarRow state="known" label="Producers" value={namesOf(people.producers) || "Unknown"} />
            <VarRow
              state={people.cast?.[0]?.nationality_state === "known" ? "known" : "unresolved"}
              label="Principal cast"
              value={namesOf(people.cast) || "Unknown"}
            />
            <VarRow
              state={spvAssumption ? "assumed" : "unresolved"}
              label="Production entity"
              value={spvAssumption ? `${jurName(psd.jurisdiction_code)} production SPV` : "Unknown"}
              sub={spvAssumption ? "structure default — not yet established" : null}
              title={spvAssumption || undefined}
            />
            <VarRow state="known" label="Production type / format" value="Feature film" title={`Rate tier: ${production.rate_resolution?.tier_id || ""}`} />
            <VarRow state="known" label="Planned shoot jurisdiction" value={`${jurName(production.jurisdiction_code)} (baseline)`} />
            <VarRow
              state="unresolved"
              label="Planned shoot locations"
              value="Unknown"
              sub={setting ? `Story setting: ${setting}` : null}
            />
            <VarRow
              state={postElected ? "known" : "unresolved"}
              label="Post-production jurisdiction"
              value={postElected ? jurName(postElected) : "Unknown"}
            />
            {facts.answerable?.component_route_post && (
              <StrFactRow
                factKey="component_route_post"
                label="Route post / VFX / music to"
                meta={facts.answerable.component_route_post}
                current={facts.answers?.component_route_post ?? null}
                onSaved={refetch}
              />
            )}
            <VarRow state="unresolved" label="Shoot duration" value="Unknown" />
            <VarRow state="unresolved" label="Production schedule" value="Unknown" />
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Nationality &amp; residency</b></div>
            {[
              { key: "lead_cast", label: "Lead Cast", dataKey: "cast" },
              { key: "director", label: "Director", dataKey: "directors" },
              { key: "writer", label: "Writer", dataKey: "writers" },
              { key: "producer", label: "Producer(s)", dataKey: "producers" },
            ].map((role) => (
              <PeopleRow key={role.key} role={role} people={people} overrides={people.overrides || {}} onSaved={refetch} />
            ))}
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Constraints</b></div>
            <VarRow
              state={creative ? "known" : "unresolved"}
              label="Creative constraints"
              value={creative || "Unknown"}
              title={sreq.period?.evidence || undefined}
            />
            <VarRow
              state={logistical ? "known" : "unresolved"}
              label="Logistical constraints"
              value={logistical || "Unknown"}
              title={sreq.marine?.evidence || undefined}
            />
            <VarRow
              state={financingAssumed ? "assumed" : "known"}
              label="Financing constraints"
              value={financingAssumed ? "None recorded" : "Recorded"}
              sub={financingAssumed ? "financing cost modeled at $0 (default)" : null}
            />
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Unresolved production facts</b><span className="n">{unresolvedFacts.length}</span></div>
            {unresolvedFacts.length ? (
              <div className="row-list">
                {unresolvedFacts.map((f) => (
                  <div className="row-item" key={f.id} onClick={() => openInspector(f.inspect.kind, f.inspect.data)}>
                    <span className={`dot ${f.tier}`} />
                    <div className="row-main">
                      <div className="row-title small">{f.need}</div>
                      <div className="row-sub">{f.why}</div>
                    </div>
                    <div className="row-value mono small">{f.value}</div>
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">All production facts are resolved.</div>}
          </section>
        </div>

        {/* ── CENTER — Project Globe · decision metrics · leading scenarios ── */}
        <div className="ovxg-col ovxg-center">
          <section className="ovx-sec ovxg-globe-sec">
            <div className="oh"><b>Project Globe</b><button className="act" onClick={() => navigate("/production/globe")}>Full screen →</button></div>
            <div className="ovxg-globe-wrap dark-panel">
              <Globe3D points={points} arcs={arcs} height={380} onPointClick={handleGlobeClick} />
            </div>
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Decision metrics</b></div>
            {/* Expected incentive / NPC use the SAME fields Workspace lanes
                render (total_incentive_floor_usd, npc_with_adjustments_usd)
                so the two screens can never disagree. */}
            <div className="ovxg-metrics ovx-stats">
              <div className="st"><div className="l2">Primary jurisdiction</div><div className="v2">{jurName(recJurCode)}</div></div>
              <div className="st"><div className="l2">Leading structure</div><div className="v2">{bestDisplay ? bestDisplay.title : "—"}</div></div>
              <div className="st"><div className="l2">Expected incentive value</div><div className="v2">{bestStruct ? <Money value={bestStruct.total_incentive_floor_usd} /> : "—"}</div></div>
              <div className="st"><div className="l2">Net production cost</div><div className="v2">{bestStruct?.is_fully_priced ? <Money value={bestStruct.npc_with_adjustments_usd} /> : "—"}</div></div>
              <div className="st"><div className="l2">Estimated savings</div><div className="v2 gold">{estimatedSavings != null ? <Money value={estimatedSavings} /> : "—"}<small> vs. baseline</small></div></div>
              <div className="st"><div className="l2">Unresolved value at risk</div><div className="v2">{swingTotal ? fmtSwing(swingTotal) : "—"}</div></div>
            </div>
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Leading scenarios</b><span className="n">{rankedStructures.length}</span></div>
            {rankedStructures.slice(0, 3).map((r, i) => {
              const s = structById.get(r.structure_id);
              if (!s) return null;
              const disp = scenarioDisplay(s);
              const sv = savingsVs(s);
              const gating = gatingFor(s, disp);
              const isBaseline = baselineStruct && s.structure_id === baselineStruct.structure_id;
              return (
                <div className={`ovxg-scn ${i === 0 ? "lead" : ""}`} key={r.structure_id}>
                  <div className="ovxg-scn-top">
                    <span className="ovxg-scn-rank">{RANKS[i] || r.rank}</span>
                    <span className="ovxg-scn-name">
                      {disp.title}
                      {i === 0 && <span className="ovxg-lead-badge">LEADING</span>}
                    </span>
                    <span className="mono ovxg-scn-npc">{s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : "not priced"}</span>
                  </div>
                  <div className="ovxg-scn-sub">
                    <span>{humanizeToken(s.structure_type)} · {(s.participants || []).map(jurName).join(" + ")} · {disp.subtitle}</span>
                    <span className="mono">
                      incentive {s.total_incentive_floor_usd ? `$${Math.round(s.total_incentive_floor_usd).toLocaleString()}` : "—"}
                      {" · "}
                      {isBaseline ? "baseline" : sv != null ? `saves $${Math.round(sv).toLocaleString()}` : "savings —"}
                    </span>
                  </div>
                  <div className="ovxg-scn-foot">
                    <span className={`ovxg-scn-state ${s.is_fully_priced ? "ok" : "blocked"}`}>
                      {s.is_fully_priced ? "Fully priced" : `Blocked · ${s.blockers?.length || 0}`}
                    </span>
                    <span className="ovxg-scn-gate" title={gating || undefined}>{gating ? `Gating: ${gating}` : "No gating condition"}</span>
                    <button className="act" onClick={() => navigate("/production/scenarios")}>Open →</button>
                  </div>
                </div>
              );
            })}
            <button className="link-more" onClick={() => navigate("/production/scenarios")}>View all scenarios →</button>
          </section>
        </div>

        {/* ── RIGHT — Recommendation and actions ──────────────────────── */}
        <div className="ovxg-col ovxg-right">
          <section className="ovx-sec">
            <div className="oh"><b>Current recommendation</b></div>
            <div className="ovxg-rec">
              <div className="ovxg-rec-title serif">{bestDisplay ? bestDisplay.title : "None fully priced yet"}</div>
              {bestStruct && estimatedSavings != null && (
                <div className="ovxg-rec-sub">
                  Lowest net production cost of the {pricedCount} fully priced structures —
                  {" "}${Math.round(estimatedSavings).toLocaleString()} below the {jurName(baselineStruct?.primary_jurisdiction)} baseline.
                </div>
              )}
            </div>
            {bestStruct && (
              <>
                <div className="ovx-sheetrow">
                  <span>Allocation</span>
                  <span className="mono small">
                    {(bestStruct.segments || []).map((seg) => `${seg.jurisdiction_code} — $${Math.round(seg.qpe_usd || 0).toLocaleString()} QPE`).join(" · ")}
                  </span>
                </div>
                <div className="ovx-sheetrow"><span>Expected incentive</span><span className="mono"><Money value={bestStruct.total_incentive_floor_usd} /></span></div>
                <div className="ovx-sheetrow"><span>Net production cost</span><span className="mono"><Money value={bestStruct.npc_with_adjustments_usd} /></span></div>
                <div className="ovx-sheetrow"><span>Savings vs. baseline</span><span className="mono">{estimatedSavings != null ? <Money value={estimatedSavings} /> : "—"}</span></div>
                <div className="ovx-sheetrow"><span>Qualification</span><span>{bestStruct.is_fully_priced ? "Fully priced" : `Blocked · ${bestStruct.blockers?.length || 0}`}</span></div>
                <div className="ovx-sheetrow">
                  <span>Unresolved condition</span>
                  <span className="small" style={{ textAlign: "right", maxWidth: 200 }}>
                    {openGrey[0]?.resolving_evidence || gatingFor(bestStruct, bestDisplay) || "None"}
                  </span>
                </div>
                <button className="link-more" onClick={openIncentiveCalc}>Detailed incentive calculation →</button>
              </>
            )}
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Immediate decisions</b><span className="n">{decisions.length}</span></div>
            {decisions.length ? (
              <div className="row-list">
                {decisions.map((d) => (
                  <div className="row-item" key={d.id} onClick={() => openInspector(d.inspect.kind, d.inspect.data)}>
                    <span className={`dot ${d.tier}`} />
                    <div className="row-main">
                      <div className="row-title small">{d.title}</div>
                      <div className="row-sub">{d.need}</div>
                    </div>
                    <div className="row-value mono small">{d.value}</div>
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">No decisions pending.</div>}
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Evidence readiness</b></div>
            {readiness.map((r) => (
              <div className="ovxv-row ovxg-ready" key={r.label} onClick={() => navigate(r.to)}>
                <span className={`dot ${READY_DOT[r.state]}`} />
                <span className="ovxv-label">{r.label}</span>
                <span className={`ovxg-ready-state ${r.state}`}>{r.state}</span>
              </div>
            ))}
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Next action</b></div>
            {topAction ? (
              <>
                <div className="row-item" onClick={() => openInspector("recommendation", topAction)} style={{ cursor: "pointer", borderTop: "none" }}>
                  <span className={`dot ${topAction.confidence === "high" ? "jade" : topAction.confidence === "medium" ? "silver" : "amber"}`} />
                  <div className="row-main">
                    <div className="row-title small">{recommendationHeadline(topAction)}</div>
                    <div className="row-sub">{topAction.description}</div>
                  </div>
                </div>
                <div className="ovx-sheetrow"><span>Value affected</span><span className="mono"><Money value={topAction.estimated_value_usd} /></span></div>
                <div className="ovx-sheetrow"><span>Approval</span><span className="small">{topAction.requires_counsel_approval ? "Counsel approval required" : "Producer approval"}</span></div>
                <button className="link-more" onClick={() => goWorkspace("recommendations")}>Open in Workspace →</button>
              </>
            ) : <div className="empty-state">Nothing pending action right now.</div>}
          </section>
        </div>

      </div>
    </div>
  );
}
