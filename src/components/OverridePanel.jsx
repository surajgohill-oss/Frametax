import { fmt } from "../utils.js";

export default function OverridePanel(props) {
  var d = props.data;
  if (!d) return null;

  if (d.error) {
    return (
      <div style={{ margin:"1rem 0", background:"rgba(224,112,112,.06)", border:"1px solid rgba(224,112,112,.2)", padding:"1rem 1.25rem", fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#E07070" }}>
        {d.error}
      </div>
    );
  }

  function diffColor(val) {
    if (!val || val === 0) return "#8A8070";
    return val > 0 ? "#5A9A5A" : "#E07070";
  }

  return (
    <div style={{ marginTop:"1rem", border:"1px solid rgba(201,168,76,.4)", background:"rgba(201,168,76,.03)", overflow:"hidden" }}>
      <div style={{ background:"rgba(201,168,76,.08)", borderBottom:"1px solid rgba(201,168,76,.2)", padding:".85rem 1.25rem", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", letterSpacing:".15em", textTransform:"uppercase", color:"#C9A84C" }}>Override Analysis - Assumed Full Qualification</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070", marginTop:".2rem" }}>Hypothetical scenario: all qualification barriers removed</div>
        </div>
        <div style={{ textAlign:"right" }}>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.6rem", color:"#C9A84C" }}>{d.assumedCreditRate}</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#5A9A5A" }}>{"Credit: " + fmt(d.totalCreditOverride)}</div>
        </div>
      </div>

      <div style={{ padding:"1.25rem" }}>
        {d.executiveSummary && (
          <div style={{ background:"rgba(201,168,76,.06)", border:"1px solid rgba(201,168,76,.12)", padding:".85rem 1rem", marginBottom:"1.25rem", fontSize:".85rem", color:"#F0EAD6", lineHeight:1.7, fontFamily:"'Jost',sans-serif" }}>
            {d.executiveSummary}
          </div>
        )}

        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:".6rem", marginBottom:"1.25rem" }}>
          {[
            ["Override Net Cost", fmt(d.trueNetCostOverride), "#5A9A5A"],
            ["Override Credit", fmt(d.totalCreditOverride), "#C9A84C"],
            ["Savings vs Home", fmt(d.savingsVsHome), "#5A9A5A"]
          ].map(function(row) {
            return (
              <div key={row[0]} style={{ background:"#080808", border:"1px solid #2A2520", padding:".75rem" }}>
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".65rem", letterSpacing:".1em", textTransform:"uppercase", color:"#8A8070", marginBottom:".3rem" }}>{row[0]}</div>
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".95rem", color:row[2] }}>{row[1]}</div>
              </div>
            );
          })}
        </div>

        {d.savingsVsPrevious !== undefined && (
          <div style={{ display:"inline-flex", alignItems:"center", gap:".5rem", fontFamily:"'DM Mono',monospace", fontSize:".76rem", background:"rgba(90,154,90,.08)", border:"1px solid rgba(90,154,90,.2)", padding:".4rem .85rem", marginBottom:"1.25rem", color:"#5A9A5A" }}>
            {"Override unlocks additional " + fmt(d.savingsVsPrevious) + " vs non-qualifying estimate"}
          </div>
        )}

        {d.methodology && d.methodology.length > 0 && (
          <div style={{ marginBottom:"1.25rem" }}>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>Calculation Methodology</div>
            <div style={{ border:"1px solid #2A2520", overflow:"hidden" }}>
              {d.methodology.map(function(step, i) {
                return (
                  <div key={i} style={{ display:"grid", gridTemplateColumns:"1.5rem 1fr auto", gap:".75rem", alignItems:"start", padding:".7rem .9rem", borderBottom: i < d.methodology.length-1 ? "1px solid #141414" : "none", background: i % 2 === 0 ? "#080808" : "#0A0A0A" }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#C9A84C", paddingTop:".1rem" }}>{step.step}</div>
                    <div>
                      <div style={{ fontFamily:"'Jost',sans-serif", fontSize:".84rem", color:"#F0EAD6", fontWeight:500, marginBottom:".15rem" }}>{step.label}</div>
                      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070" }}>{step.calculation}</div>
                      {step.notes && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#5A5A50", marginTop:".2rem", fontStyle:"italic" }}>{step.notes}</div>}
                    </div>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".88rem", color:"#F0EAD6", textAlign:"right", paddingTop:".1rem", whiteSpace:"nowrap" }}>{fmt(step.result)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {d.structuringSteps && d.structuringSteps.length > 0 && (
          <div style={{ marginBottom:"1.25rem" }}>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>How to Actually Qualify</div>
            <div style={{ display:"flex", flexDirection:"column", gap:".4rem" }}>
              {d.structuringSteps.map(function(s, i) {
                return (
                  <div key={i} style={{ display:"flex", gap:".75rem", alignItems:"flex-start", padding:".6rem .9rem", border:"1px solid " + (s.critical ? "rgba(201,168,76,.25)" : "#2A2520"), background: s.critical ? "rgba(201,168,76,.04)" : "#0A0A0A" }}>
                    <span style={{ color: s.critical ? "#C9A84C" : "#5A9A5A", fontFamily:"'DM Mono',monospace", fontSize:".7rem", flexShrink:0, paddingTop:".1rem" }}>{s.critical ? "!" : "+"}</span>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:".84rem", color:"#F0EAD6" }}>{s.action}</div>
                      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", marginTop:".2rem" }}>{s.timeframe + (s.cost ? " - " + s.cost : "")}</div>
                    </div>
                    {s.critical && <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".62rem", color:"#C9A84C", border:"1px solid rgba(201,168,76,.3)", padding:".15rem .4rem", flexShrink:0 }}>REQUIRED</span>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {d.assumedQualifications && d.assumedQualifications.length > 0 && (
          <div style={{ marginBottom:"1.25rem" }}>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>Qualification Pathways</div>
            {d.assumedQualifications.map(function(q, i) {
              var dc = q.difficulty === "low" ? "#5A9A5A" : q.difficulty === "medium" ? "#C9801C" : "#E07070";
              return (
                <div key={i} style={{ display:"flex", gap:".75rem", padding:".5rem .9rem", borderBottom:"1px solid #141414", fontSize:".82rem" }}>
                  <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".62rem", padding:".15rem .4rem", background:dc+"18", border:"1px solid "+dc+"40", color:dc, flexShrink:0, alignSelf:"flex-start", marginTop:".1rem" }}>{(q.difficulty || "").toUpperCase()}</span>
                  <div>
                    <div style={{ color:"#F0EAD6", fontWeight:500, marginBottom:".2rem" }}>{q.test}</div>
                    <div style={{ color:"#8A8070" }}>{q.howToPass}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {d.caveats && d.caveats.length > 0 && (
          <div style={{ background:"rgba(138,128,112,.05)", border:"1px solid #2A2520", padding:".75rem 1rem" }}>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070", letterSpacing:".12em", textTransform:"uppercase", marginBottom:".4rem" }}>Caveats</div>
            {d.caveats.map(function(c, i) {
              return <div key={i} style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", padding:".2rem 0", lineHeight:1.5 }}>{c}</div>;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
