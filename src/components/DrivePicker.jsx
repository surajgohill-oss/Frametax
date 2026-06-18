import { useState } from "react";

export default function DrivePicker(props) {
  var { open, onClose, onSearch, onSelect, files, loading, err, target } = props;
  var [q, setQ] = useState("");
  if (!open) return null;

  function mimeIcon(mime) {
    if (!mime) return "DOC";
    if (mime.includes("pdf")) return "PDF";
    if (mime.includes("sheet") || mime.includes("excel") || mime.includes("csv")) return "XLS";
    if (mime.includes("document") || mime.includes("word")) return "DOC";
    if (mime.includes("text")) return "TXT";
    return "FILE";
  }

  return (
    <div style={{ position:"fixed", inset:0, zIndex:300, display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div onClick={onClose} style={{ position:"absolute", inset:0, background:"rgba(0,0,0,.7)", backdropFilter:"blur(4px)" }} />
      <div style={{ position:"relative", width:"min(560px,95vw)", background:"#0C0C0C", border:"1px solid #2A2520", boxShadow:"0 24px 80px rgba(0,0,0,.8)", zIndex:1, display:"flex", flexDirection:"column", maxHeight:"80vh" }}>
        <div style={{ padding:"1.25rem 1.5rem", borderBottom:"1px solid #2A2520", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <div>
            <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.4rem", color:"#F0EAD6" }}>
              {"Google Drive - Select " + (target === "budget" ? "Budget" : "Script")}
            </div>
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", marginTop:".2rem" }}>PDF, spreadsheet, Google Doc, or text file</div>
          </div>
          <button onClick={onClose} style={{ background:"transparent", border:"none", color:"#8A8070", cursor:"pointer", fontSize:"1.3rem", padding:".25rem .5rem", lineHeight:1 }}>x</button>
        </div>

        <div style={{ padding:"1rem 1.5rem", borderBottom:"1px solid #2A2520" }}>
          <div style={{ display:"flex", gap:".5rem" }}>
            <input
              value={q}
              onChange={function(e) { setQ(e.target.value); }}
              onKeyDown={function(e) { if (e.key === "Enter") onSearch(q); }}
              placeholder="Search your Drive... (e.g. budget, film, production)"
              style={{ flex:1, background:"#080808", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".9rem", padding:".65rem .9rem", outline:"none" }}
            />
            <button onClick={function() { onSearch(q); }}
              disabled={loading}
              style={{ background:"#C9A84C", color:"#080808", border:"none", fontFamily:"'Jost',sans-serif", fontSize:".8rem", fontWeight:700, padding:".65rem 1.25rem", cursor:loading?"not-allowed":"pointer", letterSpacing:".06em", textTransform:"uppercase" }}>
              {loading ? "..." : "Search"}
            </button>
          </div>
          <div style={{ display:"flex", gap:".4rem", marginTop:".6rem", flexWrap:"wrap" }}>
            {["budget", "film production", "script", "movie magic", "breakdown"].map(function(chip) {
              return (
                <button key={chip} onClick={function() { setQ(chip); onSearch(chip); }}
                  style={{ background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontSize:".7rem", padding:".2rem .55rem", cursor:"pointer", fontFamily:"'DM Mono',monospace" }}>
                  {chip}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ flex:1, overflowY:"auto", padding:"1rem 1.5rem" }}>
          {loading && (
            <div style={{ textAlign:"center", padding:"2.5rem", fontFamily:"'DM Mono',monospace", fontSize:".8rem", color:"#C9A84C", display:"flex", alignItems:"center", justifyContent:"center", gap:".75rem" }}>
              <div style={{ width:16, height:16, borderRadius:"50%", border:"2px solid #2A2520", borderTopColor:"#C9A84C", animation:"spin 1s linear infinite" }} />
              Searching Google Drive...
            </div>
          )}
          {err && (
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#E07070", background:"rgba(224,112,112,.06)", border:"1px solid rgba(224,112,112,.2)", padding:"1rem", lineHeight:1.6 }}>
              {err}
              <div style={{ marginTop:".5rem", color:"#8A8070", fontSize:".7rem" }}>Make sure your Google Drive is connected in Claude settings (Settings &gt; Connectors).</div>
            </div>
          )}
          {!loading && !err && files.length === 0 && (
            <div style={{ textAlign:"center", padding:"2.5rem", fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#8A8070", lineHeight:1.8 }}>
              Search your Drive above to find budget or script files.<br/>
              Supports PDF, Google Sheets, Google Docs, CSV, Excel.
            </div>
          )}
          {files.map(function(file, i) {
            return (
              <div key={file.id || i}
                onClick={function() { onSelect(file.id, file.name); }}
                style={{ display:"flex", alignItems:"center", gap:"1rem", padding:".85rem .9rem", border:"1px solid #2A2520", marginBottom:".5rem", cursor:"pointer", background:"#080808", transition:"border-color .15s" }}
                onMouseEnter={function(e) { e.currentTarget.style.borderColor = "#C9A84C"; }}
                onMouseLeave={function(e) { e.currentTarget.style.borderColor = "#2A2520"; }}>
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".62rem", padding:".2rem .45rem", background:"rgba(201,168,76,.1)", color:"#C9A84C", border:"1px solid rgba(201,168,76,.2)", flexShrink:0 }}>
                  {mimeIcon(file.mimeType)}
                </div>
                <div style={{ flex:1, overflow:"hidden" }}>
                  <div style={{ fontSize:".88rem", color:"#F0EAD6", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{file.name}</div>
                  {file.modifiedTime && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070", marginTop:".15rem" }}>{"Modified: " + new Date(file.modifiedTime).toLocaleDateString()}</div>}
                </div>
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", flexShrink:0 }}>Select</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
