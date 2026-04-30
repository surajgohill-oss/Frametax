import { Eyebrow, ErrBox, SecBtn, PrimaryBtn, GhostBtn } from "../components/ui/index.js";

export default function UploadScreen(props) {
  var {
    budget, setBudget, script, sName,
    err, dragB, setDragB, dragS, setDragS,
    fileRef, scriptRef,
    setDriveTarget, setDriveOpen, setDriveFiles, setDriveErr,
    setPage, parseBudget, loadBudget, loadScript,
    setScript, setSName, setLocReqs
  } = props;

  return (
    <div className="sc fu">
      <Eyebrow>Step 1 of 4</Eyebrow>
      <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2.8rem", fontWeight:300, color:"#F0EAD6", marginBottom:".5rem" }}>Upload your budget</h2>
      <p style={{ fontSize:".9rem", color:"#8A8070", marginBottom:"2rem", lineHeight:1.6 }}>PDF, Movie Magic, CSV, or paste text below. Optionally add your script for location analysis.</p>
      <ErrBox msg={err} />

      <div
        onDragOver={function(e) { e.preventDefault(); setDragB(true); }}
        onDragLeave={function() { setDragB(false); }}
        onDrop={function(e) { e.preventDefault(); setDragB(false); loadBudget(e.dataTransfer.files[0]); }}
        onClick={function() { if (fileRef.current) fileRef.current.click(); }}
        style={{ border:"1px dashed " + (dragB ? "#C9A84C" : budget ? "#3A5A3A" : "#2A2520"), padding:"3rem 2rem", textAlign:"center", cursor:"pointer", background:budget ? "rgba(90,154,90,.04)" : "transparent", marginBottom:"1.5rem", transition:"all .3s" }}>
        <input ref={fileRef} type="file" accept=".pdf,.csv,.txt,.mbb" style={{ display:"none" }} onChange={function(e) { loadBudget(e.target.files[0]); }} />
        <div style={{ fontSize:"2.5rem", marginBottom:".75rem" }}>{budget ? "OK" : "+"}</div>
        <div style={{ color:budget ? "#5A9A5A" : "#F0EAD6", marginBottom:".3rem" }}>{budget ? "Budget loaded - ready to analyze" : "Drop your budget file here"}</div>
        <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".8rem", color:"#8A8070" }}>.pdf  .csv  .mbb  .txt  or click to browse</div>
      </div>

      <div style={{ display:"flex", justifyContent:"center", marginTop:".75rem" }}>
        <button
          onClick={function() { setDriveTarget("budget"); setDriveOpen(true); setDriveFiles([]); setDriveErr(null); }}
          style={{ display:"flex", alignItems:"center", gap:".5rem", background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".5rem 1.1rem", cursor:"pointer" }}>
          <span style={{ background:"linear-gradient(135deg,#4285F4,#34A853)", color:"white", fontFamily:"'DM Mono',monospace", fontSize:".6rem", fontWeight:700, padding:".1rem .35rem", borderRadius:2, letterSpacing:".05em" }}>Drive</span>
          Browse Google Drive
        </button>
      </div>

      <div style={{ display:"flex", alignItems:"center", gap:"1rem", margin:"1.5rem 0", color:"#8A8070", fontSize:".75rem", fontFamily:"'DM Mono',monospace" }}>
        <div style={{ flex:1, height:1, background:"#2A2520" }} /><span>or paste budget text</span><div style={{ flex:1, height:1, background:"#2A2520" }} />
      </div>

      <textarea
        value={budget}
        onChange={function(e) { setBudget(e.target.value); }}
        placeholder={"Paste budget text here...\n\nAbove the Line\n  Director Fee    $750,000\n\nProduction\n  DP / Camera     $280,000\n\nTotal: $10,000,000"}
        style={{ width:"100%", background:"#0E0E0E", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'DM Mono',monospace", fontSize:".78rem", lineHeight:1.7, padding:"1.25rem", resize:"vertical", minHeight:160, outline:"none" }}
      />

      <div style={{ marginTop:"2rem" }}>
        <Eyebrow>Optional: Script or Treatment</Eyebrow>
        <p style={{ fontSize:".82rem", color:"#8A8070", marginBottom:".75rem", lineHeight:1.6 }}>We will scan for location requirements and writer nationality to filter destinations.</p>
        <div
          onDragOver={function(e) { e.preventDefault(); setDragS(true); }}
          onDragLeave={function() { setDragS(false); }}
          onDrop={function(e) { e.preventDefault(); setDragS(false); loadScript(e.dataTransfer.files[0]); }}
          onClick={function() { if (scriptRef.current) scriptRef.current.click(); }}
          style={{ border:"1px dashed " + (script ? "#3A5A3A" : dragS ? "#C9A84C" : "#3A3020"), padding:"1.5rem 2rem", textAlign:"center", cursor:"pointer", background:script ? "rgba(90,154,90,.04)" : "rgba(201,168,76,.02)", transition:"all .3s" }}>
          <input ref={scriptRef} type="file" accept=".pdf,.fdx,.txt,.fountain" style={{ display:"none" }} onChange={function(e) { loadScript(e.target.files[0]); }} />
          {script
            ? <div><div style={{ fontSize:"1rem" }}>OK</div><div style={{ color:"#5A9A5A", marginTop:".3rem" }}>{"Script loaded: " + sName}</div></div>
            : <div><div style={{ fontSize:"1rem" }}>+</div><div style={{ color:"#F0EAD6", marginTop:".3rem" }}>Drop script here</div><div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginTop:".25rem" }}>.pdf  .fdx  .fountain  .txt</div></div>
          }
        </div>
        <div style={{ display:"flex", justifyContent:"center", marginTop:".6rem" }}>
          <button
            onClick={function() { setDriveTarget("script"); setDriveOpen(true); setDriveFiles([]); setDriveErr(null); }}
            style={{ display:"flex", alignItems:"center", gap:".5rem", background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".72rem", padding:".4rem .9rem", cursor:"pointer" }}>
            <span style={{ background:"linear-gradient(135deg,#4285F4,#34A853)", color:"white", fontFamily:"DM Mono,monospace", fontSize:".58rem", fontWeight:700, padding:".1rem .3rem", borderRadius:2, letterSpacing:".05em" }}>Drive</span>
            Browse Google Drive for Script
          </button>
        </div>
        {script && <GhostBtn onClick={function() { setScript(""); setSName(""); setLocReqs(null); }}>Remove script</GhostBtn>}
      </div>

      <div style={{ display:"flex", gap:"1rem", marginTop:"2rem", justifyContent:"flex-end" }}>
        <SecBtn onClick={function() { setPage("hero"); }}>Back</SecBtn>
        <PrimaryBtn onClick={parseBudget} disabled={!budget.trim()}>
          {budget.trim() ? "Analyze Budget" : "Upload Budget First"}
        </PrimaryBtn>
      </div>
      {!budget.trim() && <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#E07070", marginTop:".75rem" }}>A budget file or pasted text is required to continue.</p>}
    </div>
  );
}
