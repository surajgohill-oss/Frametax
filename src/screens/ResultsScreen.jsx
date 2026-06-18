import { fmt } from "../utils.js";
import { CHAT_SUGGESTIONS } from "../constants.js";
import { Eyebrow, SecBtn, PrimaryBtn } from "../components/ui/index.js";
import HomeBaseCard from "../components/HomeBaseCard.jsx";
import DestCard from "../components/DestCard.jsx";
import TreatyOptimizer from "../components/TreatyOptimizer.jsx";

export default function ResultsScreen(props) {
  var {
    results, parsed, pref,
    msgs, chatIn, setChatIn, chatLd,
    openCards, setOpenCards,
    overrideResults, overridePending,
    chatEnd, reset, sendChat,
    runOverrideAnalysis, saveToLibrary, setShowLib, setPage, setQi
  } = props;

  if (!results) return null;
  return (
    <div className="sc960 fu">
      <div style={{ borderBottom:"1px solid #2A2520", paddingBottom:"2rem", marginBottom:"2.5rem" }}>
        <Eyebrow>Analysis Complete</Eyebrow>
        <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2.8rem", fontWeight:300, color:"#F0EAD6", marginBottom:".5rem" }}>Top Filming Destinations</h2>
        <p style={{ fontSize:".9rem", color:"#8A8070", lineHeight:1.6, maxWidth:640, marginBottom:"1rem" }}>{results.overallRecommendation}</p>
        <div style={{ display:"flex", gap:".75rem", flexWrap:"wrap" }}>
          {results.directorIntel && (
            <div style={{ background:"#0E0E0E", border:"1px solid #2A2520", padding:".5rem .9rem", fontSize:".75rem", fontFamily:"'DM Mono',monospace" }}>
              <span style={{ color:"#8A8070" }}>Director: </span>
              <span style={{ color:"#F0EAD6" }}>{results.directorIntel.name}</span>
              <span style={{ color:"#C9A84C" }}>{" - " + results.directorIntel.nationality}</span>
              {results.directorIntel.imdbFound && <span style={{ color:"#5A9A5A", marginLeft:".5rem" }}>IMDb</span>}
            </div>
          )}
          {results.writerIntel && (
            <div style={{ background:"#0E0E0E", border:"1px solid #2A2520", padding:".5rem .9rem", fontSize:".75rem", fontFamily:"'DM Mono',monospace" }}>
              <span style={{ color:"#8A8070" }}>Writer: </span>
              <span style={{ color:"#C9A84C" }}>{results.writerIntel.nationality}</span>
            </div>
          )}
          <div style={{ background:"#0E0E0E", border:"1px solid #2A2520", padding:".5rem .9rem", fontSize:".75rem", fontFamily:"'DM Mono',monospace" }}>
            <span style={{ color:"#8A8070" }}>Origin: </span>
            <span style={{ color:"#F0EAD6" }}>{results.budgetOrigin}</span>
          </div>
          <div style={{ background:"#0E0E0E", border:"1px solid #2A2520", padding:".5rem .9rem", fontSize:".75rem", fontFamily:"'DM Mono',monospace" }}>
            <span style={{ color:"#8A8070" }}>BTL: </span>
            <span style={{ color:"#F0EAD6" }}>{fmt(results.variableBTLBase)}</span>
            <span style={{ color:"#8A8070" }}> at </span>
            <span style={{ color:"#C9A84C" }}>{results.budgetRateBase}</span>
          </div>
        </div>
        {results.currencyNote && <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".76rem", color:"#8A8070", marginTop:".5rem" }}>{results.currencyNote}</p>}
        {results.travelNote && <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".76rem", color:"#8A8070", marginTop:".3rem" }}>{results.travelNote}</p>}
        {pref.length > 0 && <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".76rem", color:"#C9A84C", marginTop:".5rem" }}>{"Requested: " + pref.join(", ")}</p>}
      </div>

      {results.homeBase && (
        <div style={{ marginBottom:"1.5rem" }}>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>Home Base Baseline</div>
          <HomeBaseCard homeBase={results.homeBase} budget={parsed && parsed.totalBudget} />
        </div>
      )}

      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", letterSpacing:".15em", textTransform:"uppercase", marginBottom:".6rem" }}>Top Destinations vs. Home Base</div>

      {results.destinations && results.destinations.map(function(d, i) {
        var oKey = "dest_" + i;
        return (
          <DestCard
            key={i}
            dest={d}
            isTop={i === 0}
            budget={parsed && parsed.totalBudget}
            open={!!openCards[i]}
            setOpen={function(v) { setOpenCards(function(prev) { var n = Object.assign({},prev); n[i] = v; return n; }); }}
            overrideData={overrideResults[oKey]}
            overridePending={overridePending === oKey}
            onRunOverride={function() { setOpenCards(function(prev) { var n = Object.assign({},prev); n[i] = true; return n; }); runOverrideAnalysis(i, d); }}
          />
        );
      })}

      {results.treatyOptimizer && (
        <TreatyOptimizer data={results.treatyOptimizer} />
      )}

      <div style={{ marginTop:"3rem", padding:"1.25rem", border:"1px solid #2A2520", fontSize:".75rem", color:"#8A8070", lineHeight:1.7, fontFamily:"'DM Mono',monospace" }}>
        DISCLAIMER: For informational and planning purposes only. Tax incentive programs change frequently. Consult a qualified entertainment attorney and/or production accountant before making financial decisions.
      </div>

      <div style={{ marginTop:"2.5rem", border:"1px solid #2A2520", overflow:"hidden" }}>
        <div style={{ background:"#0C0C0C", padding:"1rem 1.5rem", borderBottom:"1px solid #2A2520" }}>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.4rem", color:"#F0EAD6" }}>Ask a Follow-up Question</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#8A8070", marginTop:".2rem" }}>Full production context loaded</div>
        </div>

        {msgs.length === 0
          ? <div style={{ padding:"2rem 1.5rem", textAlign:"center", color:"#8A8070", fontSize:".82rem", fontFamily:"'DM Mono',monospace" }}>No questions yet. Try a suggestion below or type your own.</div>
          : <div style={{ maxHeight:400, overflowY:"auto", padding:"1.25rem 1.5rem", display:"flex", flexDirection:"column", gap:"1rem" }}>
              {msgs.map(function(m, i) {
                return (
                  <div key={i} style={{ maxWidth:"85%", padding:".85rem 1.1rem", fontSize:".88rem", lineHeight:1.65, alignSelf:m.role==="user"?"flex-end":"flex-start", background:m.role==="user"?"rgba(201,168,76,.1)":"#0E0E0E", border:"1px solid "+(m.role==="user"?"rgba(201,168,76,.2)":"#2A2520"), color:"#F0EAD6", whiteSpace:"pre-wrap" }}>
                    {m.text}
                  </div>
                );
              })}
              {chatLd && <div style={{ padding:".85rem 1.1rem", fontSize:".78rem", color:"#8A8070", fontFamily:"'DM Mono',monospace", alignSelf:"flex-start", background:"#0E0E0E", border:"1px solid #2A2520" }}>Researching...</div>}
              <div ref={chatEnd} />
            </div>
        }

        <div style={{ display:"flex", flexWrap:"wrap", gap:".5rem", padding:".75rem 1.5rem", borderTop:"1px solid #2A2520", background:"#080808" }}>
          {CHAT_SUGGESTIONS.filter(function(s) { return !msgs.some(function(m) { return m.text === s; }); }).map(function(s) {
            return (
              <button key={s} onClick={function() { sendChat(s); }}
                style={{ background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontSize:".72rem", padding:".3rem .75rem", cursor:"pointer", fontFamily:"'DM Mono',monospace" }}>
                {s}
              </button>
            );
          })}
        </div>

        <div style={{ display:"flex", borderTop:"1px solid #2A2520" }}>
          <input
            value={chatIn}
            onChange={function(e) { setChatIn(e.target.value); }}
            onKeyDown={function(e) { if (e.key === "Enter" && !e.shiftKey) sendChat(chatIn); }}
            placeholder="Ask about co-productions, qualification gaps, rates..."
            disabled={chatLd}
            style={{ flex:1, background:"#0A0A0A", border:"none", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".9rem", padding:"1rem 1.25rem", outline:"none" }}
          />
          <button
            onClick={function() { sendChat(chatIn); }}
            disabled={chatLd || !chatIn.trim()}
            style={{ background:chatLd||!chatIn.trim()?"#3A3010":"#C9A84C", color:chatLd||!chatIn.trim()?"#5A5040":"#080808", border:"none", cursor:"pointer", padding:"1rem 1.5rem", fontFamily:"'Jost',sans-serif", fontSize:".82rem", fontWeight:600, letterSpacing:".06em", textTransform:"uppercase", whiteSpace:"nowrap" }}>
            {chatLd ? "..." : "Ask"}
          </button>
        </div>
      </div>

      <div style={{ display:"flex", gap:"1rem", marginTop:"2rem", justifyContent:"center", flexWrap:"wrap" }}>
        <SecBtn onClick={function() { setPage("qa"); setQi(0); }}>Adjust Answers</SecBtn>
        <button onClick={function() { setShowLib(true); }}
          style={{ background:"rgba(201,168,76,.1)", border:"1px solid rgba(201,168,76,.3)", color:"#C9A84C", fontFamily:"'Jost',sans-serif", fontSize:".85rem", fontWeight:500, padding:".75rem 1.75rem", cursor:"pointer" }}>
          Save to Library
        </button>
        <PrimaryBtn onClick={reset}>Analyze Another Budget</PrimaryBtn>
      </div>
    </div>
  );
}
