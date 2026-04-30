import { fmt } from "../utils.js";
import SavePrompt from "./SavePrompt.jsx";

export default function LibraryPanel(props) {
  var {
    library, libLoaded, page, results, parsed, budget,
    deleteFromLibrary, loadFromLibrary, saveToLibrary, setShowLib
  } = props;

  return (
    <>
      <div style={{ position:"fixed", top:0, right:0, width:400, height:"100vh", background:"#0C0C0C", borderLeft:"1px solid #2A2520", zIndex:200, display:"flex", flexDirection:"column", boxShadow:"-8px 0 32px rgba(0,0,0,.6)" }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"1.25rem 1.5rem", borderBottom:"1px solid #2A2520" }}>
          <div>
            <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.4rem", color:"#F0EAD6" }}>Project Library</div>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", marginTop:".2rem" }}>Saved budgets and analyses</div>
          </div>
          <button onClick={function() { setShowLib(false); }} style={{ background:"transparent", border:"none", color:"#8A8070", cursor:"pointer", fontSize:"1.2rem", padding:".25rem .5rem" }}>x</button>
        </div>

        <div style={{ flex:1, overflowY:"auto", padding:"1rem" }}>
          {!libLoaded && (
            <div style={{ textAlign:"center", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".78rem", padding:"2rem" }}>Loading...</div>
          )}
          {libLoaded && library.length === 0 && (
            <div style={{ textAlign:"center", padding:"3rem 1.5rem" }}>
              <div style={{ fontSize:"2rem", marginBottom:"1rem", opacity:.4 }}>+</div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#8A8070", lineHeight:1.7 }}>
                No saved projects yet. Run an analysis and click Save to Library to store your results here.
              </div>
            </div>
          )}
          {libLoaded && library.map(function(entry) {
            return (
              <div key={entry.id} style={{ border:"1px solid #2A2520", marginBottom:".75rem", overflow:"hidden" }}>
                <div style={{ padding:".85rem 1rem", background:"#111" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:".4rem" }}>
                    <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.1rem", color:"#F0EAD6", flex:1, paddingRight:".5rem" }}>{entry.label}</div>
                    <button onClick={function() { deleteFromLibrary(entry.id); }}
                      style={{ background:"transparent", border:"none", color:"#8A8070", cursor:"pointer", fontSize:".75rem", fontFamily:"'DM Mono',monospace", flexShrink:0 }}>
                      delete
                    </button>
                  </div>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070", marginBottom:".6rem" }}>
                    {entry.savedAt + (entry.totalBudget ? "  " + fmt(entry.totalBudget) : "")}
                  </div>
                  {entry.results && entry.results.destinations && (
                    <div style={{ marginBottom:".6rem" }}>
                      {entry.results.destinations.slice(0,3).map(function(d) {
                        return (
                          <div key={d.rank} style={{ display:"flex", justifyContent:"space-between", padding:".3rem 0", borderBottom:"1px solid #1A1A1A", fontSize:".76rem" }}>
                            <span style={{ color:"#F0EAD6" }}>{d.flag + " " + d.country}</span>
                            <span style={{ fontFamily:"'DM Mono',monospace", color:"#C9A84C" }}>{d.creditRate}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {entry.results && entry.results.overallRecommendation && (
                    <div style={{ fontSize:".74rem", color:"#8A8070", lineHeight:1.5, marginBottom:".75rem" }}>
                      {entry.results.overallRecommendation.slice(0, 120) + (entry.results.overallRecommendation.length > 120 ? "..." : "")}
                    </div>
                  )}
                  <button onClick={function() { loadFromLibrary(entry); }}
                    style={{ background:"rgba(201,168,76,.1)", border:"1px solid rgba(201,168,76,.3)", color:"#C9A84C", fontFamily:"'DM Mono',monospace", fontSize:".72rem", padding:".4rem .85rem", cursor:"pointer", width:"100%" }}>
                    Load Budget + Re-run Analysis
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {page === "results" && results && (
          <div style={{ padding:"1rem", borderTop:"1px solid #2A2520" }}>
            <SavePrompt onSave={saveToLibrary} defaultLabel={(parsed && parsed.title) || "Untitled Project"} />
          </div>
        )}
        {page !== "results" && budget && (
          <div style={{ padding:"1rem", borderTop:"1px solid #2A2520" }}>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginBottom:".5rem" }}>Save current budget (no analysis yet)</div>
            <button onClick={function() { saveToLibrary((parsed && parsed.title) || "Budget - " + new Date().toLocaleDateString()); setShowLib(false); }}
              style={{ background:"#C9A84C", color:"#080808", border:"none", fontFamily:"'Jost',sans-serif", fontSize:".8rem", fontWeight:700, letterSpacing:".08em", padding:".7rem 1.25rem", cursor:"pointer", width:"100%", textTransform:"uppercase" }}>
              Save Budget to Library
            </button>
          </div>
        )}
      </div>
      <div onClick={function() { setShowLib(false); }} style={{ position:"fixed", inset:0, zIndex:199, background:"rgba(0,0,0,.4)" }} />
    </>
  );
}
