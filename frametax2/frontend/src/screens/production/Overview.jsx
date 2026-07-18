import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { useProjectStatus } from "../../lib/useProjectStatus";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken } from "../../lib/format";

// Overview — the approved artifact "identity hero + flat sheet" dashboard
// (reference/artifacts/prototype-v1-updated.html). Two-column split: the
// production's open decisions on the left, its record and optimization
// queue on the right. Every value is read verbatim from the live backend
// (useCineGlobe) — nothing is fabricated. Wiring that the artifact renders
// read-only (nationality edits) stays reachable via the Workspace Inputs
// tab, reached from the "Deal facts" row.

const JUR_NAMES = {
  MU: "Mauritius", ES: "Spain", GB: "United Kingdom", US: "United States",
  IE: "Ireland", MT: "Malta", FJ: "Fiji", GR: "Greece", IT: "Italy",
  FR: "France", DE: "Germany", AU: "Australia", NZ: "New Zealand",
  CA: "Canada", IN: "India", ZA: "South Africa", TR: "Türkiye",
};
const jurName = (code) => JUR_NAMES[code] || code || "—";
const NAT = { GB: "GB", US: "US", FR: "FR", DE: "DE", IT: "IT", ES: "ES", IE: "IE", MT: "MT", MU: "MU", FJ: "FJ", AU: "AU", NZ: "NZ", CA: "CA", IN: "IN", ZA: "ZA" };
const natOf = (arr) => {
  const n = arr?.[0]?.nationality;
  return n ? (NAT[n] || n) : "—";
};
const fmtSwing = (v) => (v ? `±$${Math.round(v).toLocaleString()}` : null);

export default function Overview() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  const { openInspector } = useAppState();
  const { meta } = useProjectStatus(data?.production?.production_id);

  const allocated = data?.structures?.allocated_structures;

  // Unified open-question list — MissingInput (Question Engine, /package)
  // plus open GreyAreaItem (Legal Engine, /legal), exactly as the Workspace
  // question stack composes them. Never fabricated.
  const questions = useMemo(() => {
    if (!data) return [];
    const mi = (data.pkg.missing_inputs || []).map((m) => ({
      id: m.identifier,
      title: m.question,
      swing: null,
      priority: m.optimizer_value,
      hot: !!m.blocking,
      meta: (m.downstream_engines || []).map(humanizeToken).join(", "),
      inspect: { kind: "question", data: m },
    }));
    const ga = (data.legal.grey_areas_current || [])
      .filter((g) => g.status === "open")
      .map((g) => ({
        id: g.item_id,
        title: g.resolving_evidence,
        swing: g.amount_usd,
        priority: "high",
        hot: true,
        meta: g.jurisdiction_code ? `${g.jurisdiction_code} · ${g.authority_to_ask || "authority ruling"}` : "authority ruling",
        inspect: { kind: "question", data: g },
      }));
    // Money-bearing questions first (they gate optimization), then the rest.
    return [...ga, ...mi];
  }, [data]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, structures, legal, people } = data;
  const ranking = structures.ranking || [];
  const best = ranking.find((r) => r.is_priceable) || null;

  const swingTotal = (legal.grey_areas_current || [])
    .filter((g) => g.status === "open")
    .reduce((s, g) => s + (g.amount_usd || 0), 0);
  const openN = questions.length;
  const blocker = questions.find((q) => q.swing) || questions.find((q) => q.hot) || null;

  // Recommended jurisdiction — the leading (top priceable) structure's
  // dominant segment by qualifying spend; falls back to the production's
  // own base jurisdiction.
  const bestStruct = allocated?.structures?.find((s) => s.structure_id === best?.structure_id);
  const dominantSeg = bestStruct?.segments?.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
  const recJur = jurName(dominantSeg?.jurisdiction_code || production.jurisdiction_code);

  const rateModeled = production.rate != null ? `${Math.round(production.rate * 100)}%` : "—";
  const rateCeiling = production.rate_resolution?.is_band_ceiling;

  const dealFacts = `dir ${natOf(people.directors)} · writer ${natOf(people.writers)} · prod ${natOf(people.producers)} · cast ${natOf(people.cast)}`;

  function openWorkspace(tab) {
    navigate("/production/workspace", tab ? { state: { tab } } : undefined);
  }

  return (
    <div className="screen ovx-screen">
      {/* Identity hero */}
      <section className="ovx-hero">
        <div className="ovx-hero-art" aria-hidden="true" />
        <div className="ovx-hero-id">
          <div className="ovx-pillrow">
            <span className="ovx-pill stage">{meta.label}</span>
            <span className="ovx-pill">{pkg.confidence} confidence</span>
            {best && <span className="ovx-pill anchor">◈ {best.label} anchor</span>}
          </div>
          <h1>{production.production_name}</h1>
          {pkg.script?.attributes?.setting?.value && (
            <div className="ovx-logline">Setting — {pkg.script.attributes.setting.value}.</div>
          )}
        </div>
        <div className="ovx-stats">
          <div className="st">
            <div className="l2">Total budget</div>
            <div className="v2"><Money value={production.gross_budget_usd} /></div>
          </div>
          <div className="st">
            <div className="l2">Recommended jurisdiction</div>
            <div className="v2">{recJur}</div>
          </div>
          <div className="st">
            <div className="l2">Net production cost</div>
            <div className="v2 gold">{best ? <Money value={best.conservative_npc_usd} /> : "—"}</div>
          </div>
          <div className="st key">
            <div className="l2">Optimization waiting</div>
            <div className="v2 gold">{swingTotal ? `$${Math.round(swingTotal).toLocaleString()}` : "—"}<small> · {openN} rulings</small></div>
          </div>
          {blocker ? (
            <div className="st block">
              <div className="l2">Biggest blocker</div>
              <div className="v2" title={blocker.title}>{fmtSwing(blocker.swing) || "priority"}<small> · {blocker.hot ? "open" : "awaiting"}</small></div>
            </div>
          ) : (
            <div className="st">
              <div className="l2">Blockers</div>
              <div className="v2" style={{ color: "var(--jade)" }}>none</div>
            </div>
          )}
        </div>
      </section>

      {/* Two-column split */}
      <div className="ovx-split">
        {/* LEFT — open decisions */}
        <div>
          <section className="ovx-sec">
            <div className="oh">
              <b>Open questions</b>
              <span className="n">{openN}{swingTotal ? ` · ±$${Math.round(swingTotal).toLocaleString()} at stake` : ""}</span>
              <button className="act" onClick={() => openWorkspace()}>Work the stack →</button>
            </div>
            {openN ? (
              <table className="ovx-qt">
                <tbody>
                  {questions.map((q, i) => (
                    <tr key={q.id} onClick={() => openInspector(q.inspect.kind, q.inspect.data)} style={{ cursor: "pointer" }}>
                      <td className="qid">Q{i + 1}</td>
                      <td className="qtitle">{q.title}</td>
                      <td className="qsw">{fmtSwing(q.swing) || <span style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-sans)", fontSize: 11 }}>{q.priority} priority</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ fontSize: 12, color: "var(--text-tertiary)", padding: "6px 0" }}>
                Nothing conditional remains — production certified.
              </div>
            )}
          </section>

          <section className="ovx-sec">
            <div className="oh">
              <b>Scenarios under evaluation</b>
              <span className="n">{ranking.length}</span>
              <button className="act" onClick={() => openWorkspace()}>Compare →</button>
            </div>
            {ranking.length ? ranking.map((r, i) => (
              <div className="ovx-sheetrow" key={r.structure_id}>
                <span><b>{r.rank ? `${["①", "②", "③", "④", "⑤"][i] || r.rank} ` : ""}{r.label}</b>{r.is_priceable ? "" : " · not yet priced"}</span>
                <span className="mono">{r.is_priceable ? <Money value={r.conservative_npc_usd} /> : "—"}</span>
              </div>
            )) : (
              <div style={{ fontSize: 12, color: "var(--text-tertiary)", padding: "6px 0" }}>
                No lanes yet — open the workspace.
              </div>
            )}
            <div className="ovx-actions">
              <button className="ovx-btn primary" onClick={() => openWorkspace()}>Open workspace</button>
              <button className="ovx-btn" onClick={() => openWorkspace("map")}>Project globe</button>
            </div>
          </section>
        </div>

        {/* RIGHT — record + optimization */}
        <div>
          <section className="ovx-sec">
            <div className="oh"><b>Production sheet</b></div>
            <div className="ovx-sheetrow"><span>Leading structure</span><span className="mono">{best ? best.label : "None priced"}</span></div>
            <div className="ovx-sheetrow"><span>Recommended rate</span><span className="mono">{rateModeled}{rateCeiling ? " (up to)" : ""}</span></div>
            <div className="ovx-sheetrow"><span>Conditional swing</span><span className="mono">{swingTotal ? `±$${Math.round(swingTotal).toLocaleString()}` : "—"}</span></div>
            <div className="ovx-sheetrow"><span>Open questions</span><span className="mono">{openN}</span></div>
            <div className="ovx-sheetrow click" onClick={() => openWorkspace("inputs")} title="Edit cast & crew nationality in Workspace → Inputs">
              <span>Deal facts</span><span className="mono">{dealFacts} <span style={{ color: "var(--blue)", fontFamily: "var(--font-sans)" }}>edit →</span></span>
            </div>
          </section>

          <section className="ovx-sec">
            <div className="oh">
              <b>Optimization queue</b>
              <button className="act" onClick={() => openWorkspace()}>Work the stack →</button>
            </div>
            {openN ? (
              <>
                <div className="ovx-optq-head">
                  <span className="amt">{swingTotal ? `$${Math.round(swingTotal).toLocaleString()}` : "—"}</span>
                  <span className="lbl">waiting to be unlocked</span>
                  <span className="sub">{openN} rulings<br />gating optimization</span>
                </div>
                {questions.map((q) => (
                  <button className={`ovx-optq-row${q.hot ? " hot" : ""}`} key={q.id} onClick={() => openInspector(q.inspect.kind, q.inspect.data)}>
                    <span className="amt">{fmtSwing(q.swing) || q.priority}</span>
                    <span className="body"><b>{q.title}</b><div className="meta">{q.meta}</div></span>
                    <span className="go">Resolve →</span>
                  </button>
                ))}
              </>
            ) : (
              <div style={{ fontSize: 12, color: "var(--text-tertiary)", padding: "6px 0" }}>
                Nothing conditional remains — every path is qualified or closed.
              </div>
            )}
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Intelligence · coming online</b></div>
            {[
              ["Reinvestment readiness — by jurisdiction", "engine pending"],
              ["Treaty opportunities", "reserved"],
              ["Currency normalization · historical FX", "reserved"],
              ["Confidence scoring · conservative / base / optimistic", "reserved"],
            ].map(([label, tag]) => (
              <div className="ovx-rsv" key={label}><span>{label}</span><span className="tag2">{tag}</span></div>
            ))}
            <div style={{ fontSize: 10.5, color: "var(--text-tertiary)", paddingTop: 7 }}>
              These panes activate when the calculation engine is wired. Layout space is reserved so nothing reflows.
            </div>
          </section>

          <section className="ovx-sec">
            <div className="oh"><b>Shortcuts</b></div>
            <div className="ovx-actions" style={{ marginTop: 2 }}>
              <button className="ovx-btn" onClick={() => navigate("/production/documents")}>Documents</button>
              <button className="ovx-btn" onClick={() => navigate("/production/knowledge")}>Knowledge</button>
              <button className="ovx-btn" onClick={() => navigate("/production/record")}>Record</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
