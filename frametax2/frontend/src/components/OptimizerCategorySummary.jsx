import { Money, flagEmoji } from "../lib/format";
import { buildScenarioLabel } from "../lib/scenarioLabel";
import {
  buildOptimizerCategorySummary, buildSingleJurisdictionCategorySummary,
} from "../lib/productionOptions";
import { OPTIMIZER_FAMILY_LABEL, PRACTICALITY_TIER_LABEL } from "../lib/globeData";

// GW-OI-002/003: the Featured Structures panel (IncentiveIntelligence.jsx)
// is a compact, intentionally short working set — never the complete
// optimizer/jurisdiction picture, and it never claimed to react to the
// embedded Globe's Single Jurisdiction / Optimizer toggle at all. This
// panel is the honest category/status accounting that was previously
// invisible: every canonical structural family, every practicality tier,
// and Recommended/Evaluated Alternative/Needs-More-Facts counts, sourced
// entirely from fields the backend already serves (see
// buildOptimizerCategorySummary's own header comment in
// productionOptions.js) — no new economics, nothing recomputed, no
// candidate re-ranked. A family/tier genuinely at zero for this production
// is shown as an honest "0 executable" row, never hidden and never
// fabricated with an invented candidate.
export default function OptimizerCategorySummary({ allocated, mode, onOpenComplete }) {
  if (!allocated) return null;

  if (mode !== "optimizer") {
    const sj = buildSingleJurisdictionCategorySummary(allocated);
    if (!sj) return null;
    return (
      <section className="ovx-sec ii-category-summary">
        <div className="oh">
          <b>Single Jurisdiction Coverage</b>
          <span className="n">{sj.winnerCount}</span>
          {onOpenComplete && (
            <button className="act" onClick={() => onOpenComplete({ mode: "normal" })}>
              See all {sj.winnerCount} →
            </button>
          )}
        </div>
        <div className="cat-row">
          <span className="cat-label">Jurisdiction winners</span>
          <span className="cat-count mono">{sj.winnerCount}</span>
        </div>
        <div className="cat-row">
          <span className="cat-label">Same-jurisdiction program stacks</span>
          <span className="cat-count mono">{sj.stackedProgramCount}</span>
        </div>
      </section>
    );
  }

  const summary = buildOptimizerCategorySummary(allocated);
  if (!summary) return null;

  const renderRep = (rep) => {
    if (!rep) return <span className="cat-empty">0 executable for this production</span>;
    const codes = rep.participants?.length ? rep.participants : (rep.primary_jurisdiction ? [rep.primary_jurisdiction] : []);
    const flags = codes.map(flagEmoji).filter(Boolean).join(" ");
    return (
      <span className="cat-rep">
        {flags ? `${flags} ` : ""}{buildScenarioLabel(rep)}
        {rep.npc_with_adjustments_usd != null && (
          <span className="cat-rep-npc mono"> · <Money value={rep.npc_with_adjustments_usd} bare /></span>
        )}
      </span>
    );
  };

  return (
    <section className="ovx-sec ii-category-summary">
      <div className="oh">
        <b>Optimizer Category Coverage</b>
        <span className="n">{summary.executableTotal}</span>
        {onOpenComplete && (
          <button className="act" onClick={() => onOpenComplete({ mode: "optimizer" })}>
            See all {summary.executableTotal} →
          </button>
        )}
      </div>

      <div className="cat-group">
        <div className="cat-group-title">By alternative status</div>
        <div className="cat-row"><span className="badge gold">Leading / Strong Alternative</span><span className="cat-count mono">{summary.recommendedTotal}</span></div>
        <div className="cat-row"><span className="badge silver">Reference Alternative</span><span className="cat-count mono">{summary.evaluatedTotal}</span></div>
        <div className="cat-row"><span className="badge amber">Needs More Facts</span><span className="cat-count mono">{summary.needsMoreFactsTotal}</span></div>
      </div>

      <div className="cat-group">
        <div className="cat-group-title">By structural family</div>
        {summary.families.map((f) => (
          <div className="cat-row cat-row-rep" key={f.key}>
            <div className="cat-row-head">
              <span className="cat-label">{OPTIMIZER_FAMILY_LABEL[f.key]}</span>
              <span className={`cat-count mono ${f.executableCount === 0 ? "cat-count-zero" : ""}`}>{f.executableCount} executable</span>
            </div>
            {f.executableCount > 0 && <div className="cat-rep-line">{renderRep(f.representative)}</div>}
          </div>
        ))}
      </div>

      <div className="cat-group">
        <div className="cat-group-title">By practicality tier</div>
        {summary.tiers.map((t) => (
          <div className="cat-row" key={t.key}>
            <span className="cat-label">{PRACTICALITY_TIER_LABEL[t.key]}</span>
            <span className={`cat-count mono ${t.executableCount === 0 ? "cat-count-zero" : ""}`}>{t.executableCount} executable</span>
          </div>
        ))}
      </div>
    </section>
  );
}
