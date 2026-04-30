import { useState } from "react";
import { fmt } from "../utils.js";

export default function TreatyOptimizer(props) {
  var t = props.data;
  var [open, setOpen] = useState(true);
  var [activeStrat, setActiveStrat] = useState(null);
  if (!t) return null;

  function complexColor(c) {
    if (c === "low") return "#5A9A5A";
    if (c === "medium") return "#C9801C";
    return "#E07070";
  }
  function typeLabel(type) {
    var map = { treaty:"CO-PRO TREATY", stacking:"INCENTIVE STACKING", structuring:"NATIONALITY STRUCTURING", split_shoot:"SPLIT SHOOT", service_model:"SERVICE MODEL" };
    return map[type] || type.toUpperCase();
  }

  return (
    <div style={{ border:"1px solid rgba(201,168,76,.3)", marginTop:"2rem", overflow:"hidden", background:"rgba(201,168,76,.02)" }}>
      <div onClick={function() { setOpen(!open); }}
        style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"1.25rem 1.75rem", cursor:"pointer", background:"rgba(201,168,76,.05)", borderBottom: open ? "1px solid rgba(201,168,76,.2)" : "none" }}>
        <div>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.6rem", color:"#C9A84C", fontWeight:300 }}>Treaty + Incentive Optimizer</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginTop:".25rem" }}>Co-production treaties, stacking strategies, and structuring moves to maximize total incentive</div>
        </div>
        <div style={{ textAlign:"right", marginLeft:"1.5rem" }}>
          {t.maxAchievableRate && <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", color:"#C9A84C" }}>{t.maxAchievableRate}</div>}
          {t.maxAchievableAmount && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#5A9A5A" }}>{"up to " + fmt(t.maxAchievableAmount) + " combined"}</div>}
          <div style={{ color:"#8A8070", fontSize:".8rem", marginTop:".25rem" }}>{open ? "^" : "v"}</div>
        </div>
      </div>

      {open && (
        <div style={{ padding:"1.5rem 1.75rem" }}>
          {t.executiveSummary && (
            <div style={{ background:"rgba(201,168,76,.06)", border:"1px solid rgba(201,168,76,.15)", padding:"1rem 1.25rem", marginBottom:"1.5rem", fontSize:".9rem", color:"#F0EAD6", lineHeight:1.7, fontFamily:"'Jost',sans-serif" }}>
              {t.executiveSummary}
            </div>
          )}

          {t.baselineAmount !== undefined && t.maxAchievableAmount !== undefined && (
            <div style={{ display:"flex", gap:"1rem", marginBottom:"1.5rem", flexWrap:"wrap" }}>
              {[
                ["Baseline Incentive", fmt(t.baselineAmount), "#8A8070"],
                ["Maximum Achievable", fmt(t.maxAchievableAmount), "#C9A84C"],
                ["Incremental Uplift", "+" + fmt(t.incrementalUplift), "#5A9A5A"]
              ].map(function(row) {
                return (
                  <div key={row[0]} style={{ flex:1, minWidth:150, background:"#0A0A0A", padding:".85rem 1rem", border:"1px solid #2A2520" }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", letterSpacing:".12em", textTransform:"uppercase", color:"#8A8070", marginBottom:".3rem" }}>{row[0]}</div>
                    <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.6rem", color:row[2] }}>{row[1]}</div>
                  </div>
                );
              })}
            </div>
          )}

          {t.quickWins && t.quickWins.length > 0 && (
            <div style={{ marginBottom:"1.5rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#5A9A5A", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>Quick Wins</div>
              <div style={{ display:"flex", flexDirection:"column", gap:".4rem" }}>
                {t.quickWins.map(function(w, i) {
                  return (
                    <div key={i} style={{ display:"flex", gap:".75rem", alignItems:"flex-start", background:"rgba(90,154,90,.04)", border:"1px solid rgba(90,154,90,.15)", padding:".6rem 1rem", fontSize:".82rem" }}>
                      <span style={{ color:"#5A9A5A", flexShrink:0, fontFamily:"'DM Mono',monospace" }}>+</span>
                      <span style={{ color:"#F0EAD6", flex:1 }}>{w.action}</span>
                      <span style={{ color:"#5A9A5A", fontFamily:"'DM Mono',monospace", fontSize:".72rem", flexShrink:0 }}>{w.value}</span>
                      <span style={{ color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".7rem", flexShrink:0 }}>{w.timeframe}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {t.strategies && t.strategies.length > 0 && (
            <div style={{ marginBottom:"1.5rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".75rem" }}>Strategies</div>
              <div style={{ display:"flex", flexDirection:"column", gap:".5rem" }}>
                {t.strategies.map(function(s, i) {
                  var isActive = activeStrat === i;
                  return (
                    <div key={i} style={{ border:"1px solid " + (isActive ? "rgba(201,168,76,.4)" : "#2A2520"), overflow:"hidden" }}>
                      <div onClick={function() { setActiveStrat(isActive ? null : i); }}
                        style={{ display:"flex", alignItems:"center", gap:"1rem", padding:".9rem 1.1rem", cursor:"pointer", background:isActive ? "rgba(201,168,76,.05)" : "#0A0A0A" }}>
                        <div style={{ flex:1 }}>
                          <div style={{ display:"flex", gap:".5rem", alignItems:"center", flexWrap:"wrap", marginBottom:".25rem" }}>
                            <span style={{ fontFamily:"'Jost',sans-serif", fontSize:".9rem", color:"#F0EAD6", fontWeight:500 }}>{s.title}</span>
                            <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".58rem", padding:".15rem .5rem", background:"rgba(201,168,76,.1)", color:"#C9A84C", border:"1px solid rgba(201,168,76,.25)" }}>{typeLabel(s.type)}</span>
                          </div>
                          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070" }}>{s.description}</div>
                        </div>
                        <div style={{ textAlign:"right", flexShrink:0 }}>
                          {s.incentiveUplift && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".85rem", color:"#5A9A5A" }}>{s.incentiveUplift}</div>}
                          {s.estimatedValue && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#C9A84C" }}>{fmt(s.estimatedValue)}</div>}
                          <div style={{ display:"inline-block", fontFamily:"'DM Mono',monospace", fontSize:".62rem", marginTop:".25rem", padding:".15rem .45rem", background:complexColor(s.complexity) + "18", border:"1px solid " + complexColor(s.complexity) + "40", color:complexColor(s.complexity) }}>{(s.complexity || "").toUpperCase() + " COMPLEXITY"}</div>
                        </div>
                        <div style={{ color:"#8A8070", marginLeft:".5rem" }}>{isActive ? "^" : "v"}</div>
                      </div>
                      {isActive && (
                        <div style={{ padding:"1rem 1.1rem", borderTop:"1px solid #2A2520", background:"#080808" }}>
                          {s.timeToImplement && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginBottom:".6rem" }}>{"Timeline: " + s.timeToImplement}</div>}
                          {s.bestPairedWith && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#C9A84C", marginBottom:".6rem" }}>{"Best paired with: " + s.bestPairedWith}</div>}
                          {s.requirements && s.requirements.length > 0 && (
                            <div style={{ marginBottom:".6rem" }}>
                              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".65rem", color:"#C9A84C", letterSpacing:".12em", textTransform:"uppercase", marginBottom:".35rem" }}>Requirements</div>
                              {s.requirements.map(function(r, ri) {
                                return <div key={ri} style={{ fontSize:".8rem", color:"#8A8070", padding:".2rem 0", paddingLeft:"1rem", borderLeft:"1px solid #2A2520", marginBottom:".25rem" }}>{r}</div>;
                              })}
                            </div>
                          )}
                          {s.risks && s.risks.length > 0 && (
                            <div>
                              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".65rem", color:"#E07070", letterSpacing:".12em", textTransform:"uppercase", marginBottom:".35rem" }}>Risks</div>
                              {s.risks.map(function(r, ri) {
                                return <div key={ri} style={{ fontSize:".8rem", color:"#8A8070", padding:".2rem 0", paddingLeft:"1rem", borderLeft:"1px solid rgba(224,112,112,.3)", marginBottom:".25rem" }}>{r}</div>;
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {t.stackingOpportunities && t.stackingOpportunities.length > 0 && (
            <div style={{ marginBottom:"1.5rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".75rem" }}>Incentive Stacking by Country</div>
              {t.stackingOpportunities.map(function(so, i) {
                return (
                  <div key={i} style={{ border:"1px solid #2A2520", marginBottom:".5rem", overflow:"hidden" }}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:".7rem 1rem", background:"#0C0C0C" }}>
                      <div style={{ fontFamily:"'Jost',sans-serif", fontSize:".88rem", color:"#F0EAD6" }}>{so.country}</div>
                      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".8rem", color:"#C9A84C" }}>{so.combinedRate}</div>
                    </div>
                    <div style={{ padding:".5rem 1rem" }}>
                      {(so.layers || []).map(function(l, li) {
                        return (
                          <div key={li} style={{ display:"flex", justifyContent:"space-between", padding:".3rem 0", borderBottom:"1px solid #141414", fontSize:".78rem" }}>
                            <span style={{ color:"#8A8070" }}>{l.name}</span>
                            <span style={{ fontFamily:"'DM Mono',monospace", color:"#F0EAD6" }}>{l.rate}</span>
                          </div>
                        );
                      })}
                      {so.conditions && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", marginTop:".4rem", lineHeight:1.5 }}>{so.conditions}</div>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {t.treatyMap && t.treatyMap.length > 0 && (
            <div style={{ marginBottom:"1.5rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".75rem" }}>Active Treaty Map</div>
              <div style={{ display:"flex", flexDirection:"column", gap:".4rem" }}>
                {t.treatyMap.map(function(tm, i) {
                  return (
                    <div key={i} style={{ display:"flex", gap:".75rem", alignItems:"flex-start", padding:".55rem .85rem", background:"#0A0A0A", border:"1px solid #2A2520", fontSize:".8rem" }}>
                      <span style={{ color:"#C9A84C", fontFamily:"'DM Mono',monospace", flexShrink:0 }}>{tm.country1 + " + " + tm.country2}</span>
                      <span style={{ color:"#8A8070", fontSize:".7rem", flexShrink:0, fontFamily:"'DM Mono',monospace" }}>{tm.treatyType}</span>
                      <span style={{ color:"#F0EAD6", flex:1 }}>{tm.keyBenefit}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {t.warnings && t.warnings.length > 0 && (
            <div style={{ background:"rgba(224,112,112,.05)", border:"1px solid rgba(224,112,112,.2)", padding:"1rem 1.25rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#E07070", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".5rem" }}>Warnings</div>
              {t.warnings.map(function(w, i) {
                return <div key={i} style={{ fontSize:".8rem", color:"#8A8070", padding:".25rem 0", borderBottom:"1px solid rgba(224,112,112,.1)", lineHeight:1.5 }}>{w}</div>;
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
