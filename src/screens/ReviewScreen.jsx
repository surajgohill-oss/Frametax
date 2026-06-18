import { fmt } from "../utils.js";
import { SUGGEST_COUNTRIES } from "../constants.js";
import { Eyebrow, Mono, Label, SecBtn, PrimaryBtn } from "../components/ui/index.js";

export default function ReviewScreen(props) {
  var {
    parsed, intel, fixedTot, varTot,
    pref, setPref, cInput, setCInput,
    openD, setOpenD, setPage, analyze
  } = props;

  if (!parsed) return null;
  return (
    <div className="sc fu">
      <Eyebrow>Step 2 of 4</Eyebrow>
      <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2.8rem", fontWeight:300, color:"#F0EAD6", marginBottom:".5rem" }}>{parsed.title || "Your Budget"}</h2>
      <p style={{ fontSize:".9rem", color:"#8A8070", marginBottom:"2rem", lineHeight:1.6 }}>Review parsed budget. Variable BTL costs will be rebased to local rates per destination.</p>

      <div style={{ display:"flex", gap:"2rem", padding:"1.25rem 1.5rem", border:"1px solid #2A2520", marginBottom:"2rem", background:"#0A0A0A", flexWrap:"wrap" }}>
        {[["Total Budget", fmt(parsed.totalBudget), true], ["Fixed ATL", fmt(fixedTot), false], ["Variable BTL", fmt(varTot), false], ["Departments", (parsed.departments && parsed.departments.length) || 0, false]].map(function(item) {
          return (
            <div key={item[0]} style={{ flex:1, minWidth:100 }}>
              <Label>{item[0]}</Label>
              <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.8rem", color:item[2] ? "#C9A84C" : "#F0EAD6" }}>{item[1]}</div>
            </div>
          );
        })}
      </div>

      {intel && (
        <div style={{ border:"1px solid #2A2520", marginBottom:"1.5rem", overflow:"hidden" }}>
          <div style={{ background:"#0C0C0C", padding:".75rem 1.25rem", borderBottom:"1px solid #2A2520" }}>
            <Mono color="#C9A84C" size=".7rem">Budget Intelligence Extracted</Mono>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))" }}>
            {[
              ["Budget Origin", intel.originCity, intel.originCity !== "Unknown"],
              ["Rate Base", intel.rateBase, true],
              ["Director", intel.director || "Not found", !!intel.director],
              ["Dir. Nationality", intel.directorNationality || "Will research", !!intel.directorNationality],
              ["Writer", intel.writer || "Not found", !!intel.writer],
              ["Finance", intel.hasFinance ? ("Yes " + fmt(intel.financeAmt)) : "Not in budget", intel.hasFinance],
              ["Insurance", intel.hasInsurance ? ("Yes " + fmt(intel.insuranceAmt)) : "Not in budget", intel.hasInsurance],
              ["Bond", intel.hasBond ? ("Yes " + fmt(intel.bondAmt)) : "Not in budget", intel.hasBond]
            ].map(function(item) {
              return (
                <div key={item[0]} style={{ padding:".7rem 1rem", borderRight:"1px solid #2A2520", borderBottom:"1px solid #2A2520" }}>
                  <Label>{item[0]}</Label>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".82rem", color:item[2] ? "#F0EAD6" : "#C97A1C" }}>{item[1]}</div>
                </div>
              );
            })}
          </div>
          <div style={{ padding:".75rem 1.25rem", background:"rgba(201,168,76,.04)", borderTop:"1px solid #2A2520", fontSize:".76rem", color:"#8A8070" }}>
            {"Variable BTL (" + fmt(varTot) + ") priced at "}
            <strong style={{ color:"#F0EAD6" }}>{intel.rateBase}</strong>
            {". Each destination shows the true rebased cost."}
          </div>
        </div>
      )}

      {parsed.departments && parsed.departments.map(function(dept) {
        return (
          <div key={dept.name} style={{ border:"1px solid #2A2520", marginBottom:".75rem" }}>
            <div
              onClick={function() { setOpenD(function(p) { var n = Object.assign({},p); n[dept.name] = !p[dept.name]; return n; }); }}
              style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:".9rem 1.25rem", background:"#0E0E0E", cursor:"pointer", fontSize:".82rem", fontWeight:500, letterSpacing:".06em", textTransform:"uppercase" }}>
              <span>{dept.name}</span>
              <span style={{ fontFamily:"'DM Mono',monospace", color:"#C9A84C" }}>{fmt(dept.total) + " " + (openD[dept.name] ? "^" : "v")}</span>
            </div>
            {openD[dept.name] && dept.items && dept.items.map(function(item, i) {
              return (
                <div key={i} style={{ display:"grid", gridTemplateColumns:"1fr auto auto", gap:"1rem", padding:".5rem 1.25rem", fontSize:".82rem", borderBottom:"1px solid #141414", alignItems:"center" }}>
                  <span style={{ color:"#8A8070" }}>{item.description}</span>
                  <span style={{ fontSize:".62rem", padding:".2rem .5rem", fontFamily:"'DM Mono',monospace", background:item.isFixed ? "#1A2A1A" : "#2A1A0A", color:item.isFixed ? "#5A9A5A" : "#C9801C" }}>
                    {item.isFixed ? "FIXED" : "VARIABLE"}
                  </span>
                  <span style={{ fontFamily:"'DM Mono',monospace", color:"#F0EAD6", textAlign:"right" }}>{fmt(item.amount)}</span>
                </div>
              );
            })}
          </div>
        );
      })}

      <div style={{ marginTop:"2rem", borderTop:"1px solid #2A2520", paddingTop:"1.75rem" }}>
        <Eyebrow>Preferred Countries (Optional)</Eyebrow>
        <p style={{ fontSize:".82rem", color:"#8A8070", marginBottom:"1rem", lineHeight:1.6 }}>Request specific countries - included with an honest financial verdict.</p>
        {pref.length > 0 && (
          <div style={{ display:"flex", flexWrap:"wrap", gap:".5rem", marginBottom:".75rem" }}>
            {pref.map(function(c) {
              return (
                <div key={c} onClick={function() { setPref(function(p) { return p.filter(function(x) { return x !== c; }); }); }}
                  style={{ display:"flex", alignItems:"center", gap:".4rem", background:"rgba(201,168,76,.12)", border:"1px solid rgba(201,168,76,.3)", color:"#C9A84C", fontSize:".76rem", padding:".3rem .75rem", fontFamily:"'DM Mono',monospace", cursor:"pointer" }}>
                  {c} <span style={{ opacity:.6 }}>x</span>
                </div>
              );
            })}
          </div>
        )}
        <div style={{ display:"flex", gap:".75rem", marginBottom:".75rem" }}>
          <input
            value={cInput}
            onChange={function(e) { setCInput(e.target.value); }}
            onKeyDown={function(e) {
              if (e.key === "Enter" && cInput.trim()) {
                if (!pref.includes(cInput.trim())) setPref(function(p) { return p.concat([cInput.trim()]); });
                setCInput("");
              }
            }}
            placeholder="Type a country and press Enter..."
            style={{ flex:1, background:"#0E0E0E", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".9rem", padding:".7rem 1rem", outline:"none" }}
          />
          <SecBtn onClick={function() { if (cInput.trim() && !pref.includes(cInput.trim())) { setPref(function(p) { return p.concat([cInput.trim()]); }); setCInput(""); } }}>Add +</SecBtn>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:".4rem" }}>
          {SUGGEST_COUNTRIES.filter(function(c) { return !pref.includes(c); }).map(function(c) {
            return (
              <button key={c} onClick={function() { setPref(function(p) { return p.concat([c]); }); }}
                style={{ background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontSize:".72rem", padding:".25rem .6rem", cursor:"pointer", fontFamily:"'DM Mono',monospace" }}>
                {"+ " + c}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ display:"flex", gap:"1rem", marginTop:"2rem", justifyContent:"flex-end" }}>
        <SecBtn onClick={function() { setPage("upload"); }}>Re-upload</SecBtn>
        <PrimaryBtn onClick={function() { setPage("qa"); }}>Continue</PrimaryBtn>
      </div>
    </div>
  );
}
