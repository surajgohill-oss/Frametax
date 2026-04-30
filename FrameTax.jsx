import { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";

var GOLD   = "#C9A84C";
var CREAM  = "#F0EAD6";
var DIM    = "#8A8070";
var BG     = "#080808";
var BORDER = "#2A2520";

var QUESTIONS = [
  { id:"genre",       label:"What genre is the film?",
    options:["Feature Film","TV Series","Documentary","Animation","VFX-Heavy Feature"] },
  { id:"shootDate",   label:"When is planned principal photography?",
    isText:true, ph:"e.g. Q3 2026" },
  { id:"duration",    label:"How many days of principal photography?",
    isText:true, ph:"e.g. 45 days" },
  { id:"union",       label:"Is this a union production?",
    options:["Yes - SAG-AFTRA / IATSE","Yes - Local unions only","Non-union","Mixed"] },
  { id:"dirNat",      label:"What nationality is the director?",
    isText:true, ph:"e.g. American" },
  { id:"castNat",     label:"What nationality are the lead cast members?",
    isText:true, ph:"e.g. American, British" },
  { id:"coPro",       label:"Do you have a co-production partner?",
    options:["Yes","No - but open to it","No - prefer single territory"] },
  { id:"localCrew",   label:"What % of BTL crew could be sourced locally?",
    options:["Less than 25%","25-50%","50-75%","More than 75%"] },
  { id:"travel",      label:"Is international travel already in the budget?",
    options:["Yes - fully budgeted","Partially budgeted","Not budgeted yet"] },
  { id:"finCosts",    label:"Does the budget include finance costs / insurance / bond?",
    options:["Yes - all included","Some included","None included"] },
  { id:"subsidiary",  label:"Open to registering a local production subsidiary?",
    options:["Yes","Possibly","No"] },
  { id:"market",      label:"What is the primary release market?",
    options:["North America","UK / Europe","Global / Worldwide","Streaming Platform","Multiple Markets"] },
];

var COUNTRIES = ["United Kingdom","Canada","Australia","New Zealand","Ireland",
  "Germany","France","Italy","Spain","Mexico","Czech Republic","Hungary",
  "South Africa","South Korea","Japan","UAE","Georgia","Serbia","Poland","Morocco"];

var SUGGEST_COUNTRIES = ["United Kingdom","Canada","Australia","Ireland",
  "New Zealand","South Africa","Mexico","Czech Republic","Hungary",
  "Georgia","Spain","Italy","Morocco","UAE","Serbia","Jordan","South Korea"];

var CHAT_SUGGESTIONS = [
  "What co-production structure gives the highest total credit?",
  "How does the director nationality affect qualification?",
  "What would unlock a higher credit tier?",
  "Currency hedging strategies I should consider?",
  "Which destination has the most flexible cultural test?"
];

var FX_CURRENCIES = ["GBP","EUR","CAD","AUD","NZD","MXN","CZK","HUF","ZAR","KRW","JPY","AED","GEL","RSD","PLN","MAD","ILS","THB","SGD","NOK","SEK","DKK"];

async function fetchFXRates() {
  try {
    var res = await fetch("https://open.er-api.com/v6/latest/USD");
    if (!res.ok) return null;
    var data = await res.json();
    return (data && data.rates) ? data.rates : null;
  } catch(e) { return null; }
}

async function callClaude(messages, useSearch, maxTok) {
  if (!maxTok) maxTok = 4000;
  var body = {
    model: "claude-sonnet-4-20250514",
    max_tokens: maxTok,
    messages: messages
  };
  if (useSearch) {
    body.tools = [{ type: "web_search_20250305", name: "web_search" }];
  }
  var res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error("API error " + res.status);
  var data = await res.json();
  return data.content.filter(function(b) { return b.type === "text"; })
    .map(function(b) { return b.text; }).join("\n");
}

function parseJSON(raw) {
  if (!raw) throw new Error("Empty response");
  var s = raw.trim();

  // Strip code fences - check for backtick char code 96
  if (s.charCodeAt(0) === 96) {
    var firstNewline = s.indexOf("\n");
    if (firstNewline > -1) s = s.slice(firstNewline + 1);
    var lastFence = s.lastIndexOf("\n");
    if (lastFence > -1 && s.slice(lastFence).replace(/\s/g,"").charCodeAt(0) === 96) {
      s = s.slice(0, lastFence);
    }
    s = s.trim();
  }

  // Extract JSON object or array from surrounding text
  var objMatch = s.match(/\{[\s\S]*\}/);
  var arrMatch = s.match(/\[[\s\S]*\]/);
  if (objMatch) s = objMatch[0];
  else if (arrMatch) s = arrMatch[0];

  // Fix common LLM JSON mistakes:
  // 1. Trailing commas before } or ]
  s = s.replace(/,(\s*[}\]])/g, "$1");
  // 2. Remove control characters that break JSON parse
  s = s.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
  // 3. Ellipsis truncation - close any open arrays/objects
  s = autoCloseJSON(s);

  return JSON.parse(s);
}

function autoCloseJSON(s) {
  // If JSON is truncated, try to close open brackets/braces
  var stack = [];
  var inString = false;
  var escaped = false;
  for (var i = 0; i < s.length; i++) {
    var c = s[i];
    if (escaped) { escaped = false; continue; }
    if (c === "\\" && inString) { escaped = true; continue; }
    if (c === "\"") { inString = !inString; continue; }
    if (inString) continue;
    if (c === "{") stack.push("}");
    else if (c === "[") stack.push("]");
    else if (c === "}" || c === "]") {
      if (stack.length && stack[stack.length-1] === c) stack.pop();
    }
  }
  // Remove trailing comma if string ends mid-object
  var trimmed = s.replace(/,\s*$/, "");
  // Close all open brackets in reverse order
  return trimmed + stack.reverse().join("");
}

function fmt(n) {
  if (!n && n !== 0) return "-";
  var v = parseFloat(String(n).replace(/[^0-9.-]/g,""));
  if (isNaN(v)) return String(n);
  if (v >= 1000000) return "$" + (v/1000000).toFixed(1) + "M";
  if (v >= 1000)    return "$" + (v/1000).toFixed(0) + "K";
  return "$" + v.toFixed(0);
}

var CSS = "@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Mono:wght@400;500&family=Jost:wght@300;400;500;600&display=swap');"
  + "*{box-sizing:border-box;margin:0;padding:0}"
  + ".fta{font-family:'Jost',sans-serif;min-height:100vh;background:#080808;color:#F0EAD6;overflow-x:hidden}"
  + "@keyframes spin{to{transform:rotate(360deg)}}"
  + "@keyframes fu{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
  + ".fu{animation:fu .35s ease}"
  + ".ring{width:80px;height:80px;border-radius:50%;border:2px solid #2A2520;border-top-color:#C9A84C;animation:spin 1s linear infinite}"
  + ".ld{min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2rem;text-align:center;padding:2rem}"
  + ".sc{max-width:900px;margin:0 auto;padding:3rem 2rem}"
  + ".sc960{max-width:960px;margin:0 auto;padding:3rem 2rem}"
  + ".sc680{max-width:680px;margin:0 auto;padding:3rem 2rem}";

function PrimaryBtn(props) {
  return (
    <button
      onClick={props.onClick}
      disabled={props.disabled}
      style={{
        background: props.disabled ? "#3A3010" : "#C9A84C",
        color: props.disabled ? "#5A5040" : "#080808",
        fontFamily:"'Jost',sans-serif",
        fontSize:".85rem",fontWeight:700,
        letterSpacing:".1em",textTransform:"uppercase",
        padding:".9rem 2.5rem",border:"none",cursor:props.disabled?"not-allowed":"pointer"
      }}>
      {props.children}
    </button>
  );
}

function SecBtn(props) {
  return (
    <button onClick={props.onClick} style={{
      background:"transparent",color:"#F0EAD6",fontFamily:"'Jost',sans-serif",
      fontSize:".82rem",padding:".75rem 1.75rem",
      border:"1px solid #2A2520",cursor:"pointer"
    }}>
      {props.children}
    </button>
  );
}

function GhostBtn(props) {
  return (
    <button onClick={props.onClick} style={{
      background:"transparent",color:"#8A8070",fontFamily:"'DM Mono',monospace",
      fontSize:".75rem",padding:".5rem 1rem",border:"none",cursor:"pointer"
    }}>
      {props.children}
    </button>
  );
}

function Mono(props) {
  return <span style={{ fontFamily:"'DM Mono',monospace", color: props.color || "#8A8070", fontSize: props.size || ".75rem" }}>{props.children}</span>;
}

function Label(props) {
  return <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", letterSpacing:".12em", textTransform:"uppercase", color:"#8A8070", marginBottom:".3rem" }}>{props.children}</div>;
}

function ErrBox(props) {
  if (!props.msg) return null;
  return (
    <div style={{ background:"rgba(180,40,40,.1)", border:"1px solid rgba(180,40,40,.3)", padding:"1rem 1.25rem", color:"#E07070", fontSize:".82rem", marginBottom:"1.5rem", fontFamily:"'DM Mono',monospace", lineHeight:1.6 }}>
      {props.msg}
    </div>
  );
}

function Eyebrow(props) {
  return <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", letterSpacing:".25em", color:"#C9A84C", textTransform:"uppercase", marginBottom: props.mb || "1rem" }}>{props.children}</div>;
}

function DrivePicker(props) {
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
              <div style={{ marginTop:".5rem", color:"#8A8070", fontSize:".7rem" }}>Make sure your Google Drive is connected in Claude settings (Settings {'>'} Connectors).</div>
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

function HomeBaseCard(props) {
  var hb = props.homeBase;
  var budget = props.budget;
  var [open, setOpen] = useState(false);
  if (!hb) return null;
  var hasIncentive = hb.estimatedCredit && hb.estimatedCredit > 0;
  return (
    <div style={{ border:"1px solid #3A3020", marginBottom:"1rem", background:"rgba(201,168,76,.02)" }}>
      <div onClick={function() { setOpen(!open); }}
        style={{ display:"flex", alignItems:"center", gap:"1.25rem", padding:"1.25rem 1.5rem", cursor:"pointer" }}>
        <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.4rem", fontWeight:300, color:"#8A8070", minWidth:"2.2rem", textAlign:"center" }}>HOME</div>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", alignItems:"center", gap:".5rem" }}>
            <span style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.5rem", fontWeight:300, color:"#8A8070" }}>{(hb.flag || "") + " " + hb.country}</span>
            <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".6rem", background:"rgba(138,128,112,.1)", color:"#8A8070", border:"1px solid #2A2520", padding:".15rem .5rem" }}>BASELINE</span>
          </div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginTop:".2rem" }}>{hb.incentiveProgram || (hasIncentive ? "Local incentive program" : "No applicable incentive program")}</div>
        </div>
        <div style={{ textAlign:"right", flexShrink:0 }}>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:"1.1rem", color: hasIncentive ? "#C9A84C" : "#8A8070" }}>{hb.creditRate || (hasIncentive ? "-" : "No credit")}</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#F0EAD6" }}>{hb.trueNetCost ? "Net: " + fmt(hb.trueNetCost) : (budget ? "Net: " + fmt(budget) : "")}</div>
        </div>
        <div style={{ color:"#8A8070", marginLeft:".5rem" }}>{open ? "^" : "v"}</div>
      </div>
      {open && (
        <div style={{ padding:"1.25rem 1.5rem", borderTop:"1px solid #2A2520" }}>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:".75rem", marginBottom:"1rem" }}>
            {[
              ["Home Budget", fmt(budget), "#F0EAD6"],
              ["Home Credit", hasIncentive ? fmt(hb.estimatedCredit) : "None", hasIncentive ? "#C9A84C" : "#8A8070"],
              ["True Net at Home", fmt(hb.trueNetCost || budget), "#F0EAD6"]
            ].map(function(row) {
              return (
                <div key={row[0]} style={{ background:"#0A0A0A", padding:".75rem", border:"1px solid #2A2520" }}>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", letterSpacing:".12em", textTransform:"uppercase", color:"#8A8070", marginBottom:".3rem" }}>{row[0]}</div>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".9rem", color:row[2] }}>{row[1]}</div>
                </div>
              );
            })}
          </div>
          {hb.notes && <p style={{ fontSize:".82rem", color:"#8A8070", lineHeight:1.6, marginBottom:".5rem" }}>{hb.notes}</p>}
          {hb.noIncentiveReason && !hasIncentive && (
            <div style={{ background:"rgba(224,112,112,.06)", border:"1px solid rgba(224,112,112,.2)", padding:".75rem 1rem", fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#E07070" }}>
              {hb.noIncentiveReason}
            </div>
          )}
          {(hb.sourceLabel || hb.sourceUrl) && (
            <div style={{ display:"flex", flexWrap:"wrap", alignItems:"baseline", gap:".4rem", fontFamily:"'DM Mono',monospace", fontSize:".68rem", marginTop:".75rem", color:"#8A8070" }}>
              <span style={{ color: hb.confidenceTier === "verified" ? "#5A9A5A" : hb.confidenceTier === "stale" ? "#E07070" : "#C9801C", border:"1px solid " + (hb.confidenceTier === "verified" ? "#5A9A5A40" : hb.confidenceTier === "stale" ? "#E0707040" : "#C9801C40"), background: hb.confidenceTier === "verified" ? "#5A9A5A12" : hb.confidenceTier === "stale" ? "#E0707012" : "#C9801C12", padding:".1rem .4rem" }}>
                {hb.confidenceTier === "verified" ? "VERIFIED" : hb.confidenceTier === "stale" ? "STALE DATA" : "RECENT"}
              </span>
              {hb.sourceLabel && <span>{hb.sourceLabel}</span>}
              {hb.lastVerified && <span>{"as of " + hb.lastVerified}</span>}
              {hb.sourceUrl && <span style={{ color:"#C9A84C", wordBreak:"break-all" }}>{hb.sourceUrl}</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TreatyOptimizer(props) {
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

function SavePrompt(props) {
  var [label, setLabel] = useState(props.defaultLabel || "");
  var [saved, setSaved] = useState(false);
  function doSave() {
    props.onSave(label);
    setSaved(true);
    setTimeout(function() { setSaved(false); }, 2500);
  }
  if (saved) {
    return <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#5A9A5A", textAlign:"center", padding:".75rem" }}>Saved to Library</div>;
  }
  return (
    <div>
      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginBottom:".4rem" }}>Save this analysis</div>
      <input
        value={label}
        onChange={function(e) { setLabel(e.target.value); }}
        onKeyDown={function(e) { if (e.key === "Enter") doSave(); }}
        style={{ width:"100%", background:"#0A0A0A", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".85rem", padding:".6rem .85rem", outline:"none", marginBottom:".5rem" }}
      />
      <button onClick={doSave}
        style={{ background:"#C9A84C", color:"#080808", border:"none", fontFamily:"'Jost',sans-serif", fontSize:".8rem", fontWeight:700, letterSpacing:".08em", padding:".7rem 1.25rem", cursor:"pointer", width:"100%", textTransform:"uppercase" }}>
        Save to Library
      </button>
    </div>
  );
}

function OverridePanel(props) {
  var d = props.data;
  var orig = props.orig;
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

function DestCard(props) {
  var dest = props.dest;
  var isTop = props.isTop;
  var budget = props.budget;
  var savings = (budget && dest.trueNetCost) ? fmt(budget - dest.trueNetCost) : null;
  var open = props.open;
  var setOpen = props.setOpen;
  var overrideData = props.overrideData;
  var overridePending = props.overridePending;
  var onRunOverride = props.onRunOverride;

  var hasFailedQuals = (dest.qualifications || []).some(function(q) {
    return q.status === "fail" || q.status === "partial";
  });

  function qColor(s) {
    if (s === "pass" || s === "likely_pass") return "#5A9A5A";
    if (s === "partial") return "#C97A1C";
    return "#E07070";
  }
  function qIcon(s) {
    if (s === "pass" || s === "likely_pass") return "OK";
    if (s === "partial") return "~";
    return "X";
  }

  var locFit = dest.locationFit || "";
  var locColor = "#C9A84C";
  if (locFit.toLowerCase().match(/excell|perfect|ideal/)) locColor = "#5A9A5A";
  if (locFit.toLowerCase().match(/poor|cannot|not suit/)) locColor = "#E07070";

  return (
    <div style={{ border:"1px solid " + (isTop ? "#C9A84C" : "#2A2520"), marginBottom:"1rem", overflow:"hidden" }}>
      <div
        onClick={function() { setOpen(!open); }}
        style={{ display:"flex", alignItems:"center", gap:"1.25rem", padding:"1.25rem 1.5rem", background:"#0C0C0C", cursor:"pointer" }}>
        <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.8rem", fontWeight:600, color:"#C9A84C", minWidth:"2.2rem", textAlign:"center" }}>{"#" + dest.rank}</div>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", alignItems:"center", gap:".5rem", flexWrap:"wrap" }}>
            <span style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.5rem", fontWeight:300, color:"#F0EAD6" }}>{dest.flag + " " + dest.country}</span>
            {dest.isPreferred && <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".6rem", background:"rgba(201,168,76,.15)", color:"#C9A84C", border:"1px solid rgba(201,168,76,.3)", padding:".15rem .5rem" }}>REQUESTED</span>}
          </div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginTop:".2rem" }}>{dest.incentiveProgram}</div>
          {locFit && <div style={{ display:"inline-block", fontFamily:"'DM Mono',monospace", fontSize:".7rem", padding:".2rem .55rem", marginTop:".3rem", background:locColor+"18", border:"1px solid "+locColor+"40", color:locColor }}>{"Location: " + locFit}</div>}
        </div>
        <div style={{ textAlign:"right", flexShrink:0 }}>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:"1.1rem", color:"#C9A84C" }}>{dest.creditRate}</div>
          {savings && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#5A9A5A" }}>{"Save ~" + savings}</div>}
        </div>
        <div style={{ color:"#8A8070", marginLeft:".5rem" }}>{open ? "^" : "v"}</div>
      </div>

      {open && (
        <div style={{ padding:"1.25rem 1.5rem", borderTop:"1px solid #2A2520" }}>
          {dest.rateAdjustmentNote && (
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#C9A84C", background:"rgba(201,168,76,.05)", border:"1px solid rgba(201,168,76,.15)", padding:".6rem 1rem", marginBottom:"1rem" }}>
              {"Rate: " + dest.rateAdjustmentNote}
            </div>
          )}

          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:".75rem", marginBottom:"1rem" }}>
            {[
              ["Local Cost", fmt(dest.localCostUSD), "#F0EAD6"],
              ["Tax Credit", "-" + fmt(dest.estimatedCredit), "#C9A84C"],
              ["Travel", "+" + fmt(dest.travelCost), "#F0EAD6"],
              ["True Net", fmt(dest.trueNetCost), "#5A9A5A"]
            ].map(function(row) {
              return (
                <div key={row[0]} style={{ background:"#0A0A0A", padding:".75rem", border:"1px solid #2A2520" }}>
                  <Label>{row[0]}</Label>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".9rem", color:row[2] }}>{row[1]}</div>
                </div>
              );
            })}
          </div>

          {dest.vsSavings && (
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#5A9A5A", background:"rgba(90,154,90,.08)", border:"1px solid rgba(90,154,90,.2)", padding:".4rem .85rem", display:"inline-block", marginBottom:"1rem" }}>
              {"Save " + dest.vsSavings + " (" + dest.vsPercent + ") vs home budget"}
            </div>
          )}

          {dest.exchangeRate && (
            <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginBottom:".5rem" }}>
              {dest.exchangeRate + " - Currency risk: " + dest.currencyRisk}
            </p>
          )}

          {(dest.sourceLabel || dest.sourceUrl) && (
            <div style={{ display:"flex", flexWrap:"wrap", alignItems:"baseline", gap:".4rem", fontFamily:"'DM Mono',monospace", fontSize:".68rem", marginBottom:".75rem", color:"#8A8070" }}>
              <span style={{ color: dest.confidenceTier === "verified" ? "#5A9A5A" : dest.confidenceTier === "stale" ? "#E07070" : "#C9801C", border:"1px solid " + (dest.confidenceTier === "verified" ? "#5A9A5A40" : dest.confidenceTier === "stale" ? "#E0707040" : "#C9801C40"), background: dest.confidenceTier === "verified" ? "#5A9A5A12" : dest.confidenceTier === "stale" ? "#E0707012" : "#C9801C12", padding:".1rem .4rem" }}>
                {dest.confidenceTier === "verified" ? "VERIFIED" : dest.confidenceTier === "stale" ? "STALE DATA" : "RECENT"}
              </span>
              {dest.sourceLabel && <span>{dest.sourceLabel}</span>}
              {dest.lastVerified && <span>{"as of " + dest.lastVerified}</span>}
              {dest.sourceUrl && <span style={{ color:"#C9A84C", wordBreak:"break-all" }}>{dest.sourceUrl}</span>}
            </div>
          )}

          {dest.qualifications && dest.qualifications.length > 0 && (
            <div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Qualification Analysis</div>
              {dest.qualifications.map(function(q, i) {
                return (
                  <div key={i} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414", lineHeight:1.5 }}>
                    <span style={{ color:qColor(q.status), flexShrink:0, fontFamily:"'DM Mono',monospace", fontSize:".7rem" }}>{qIcon(q.status)}</span>
                    <span><strong style={{ color:"#F0EAD6" }}>{q.test}</strong>{" - " + q.detail}</span>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Cost Eligibility</div>
          {[
            ["Above-the-Line", dest.atLStatus],
            ["Insurance & Bond", dest.insuranceStatus],
            ["Finance Costs", dest.financeStatus]
          ].map(function(row) {
            return (
              <div key={row[0]} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414" }}>
                <span style={{ color:"#C9A84C", flexShrink:0, fontFamily:"'DM Mono',monospace", fontSize:".7rem" }}>*</span>
                <span><strong style={{ color:"#F0EAD6" }}>{row[0]}</strong>{" - " + (row[1] || "Check with local film commission")}</span>
              </div>
            );
          })}

          {dest.coproOpportunity && (
            <div style={{ marginTop:".75rem", fontSize:".82rem", color:"#8A8070" }}>{"Co-pro: " + dest.coproOpportunity}</div>
          )}

          {dest.qualGap && (
            <div style={{ background:"rgba(201,168,76,.06)", border:"1px solid rgba(201,168,76,.2)", padding:"1rem", marginTop:"1rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", textTransform:"uppercase", letterSpacing:".1em", marginBottom:".4rem" }}>Optimization Opportunity</div>
              <div style={{ fontSize:".83rem", color:"#F0EAD6", lineHeight:1.6 }}>{dest.qualGap}</div>
            </div>
          )}

          {dest.structuringTip && (
            <div style={{ background:"rgba(90,154,90,.05)", border:"1px solid rgba(90,154,90,.2)", padding:"1rem", marginTop:".75rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#5A9A5A", textTransform:"uppercase", letterSpacing:".1em", marginBottom:".4rem" }}>Structuring Recommendation</div>
              <div style={{ fontSize:".83rem", color:"#F0EAD6", lineHeight:1.6 }}>{dest.structuringTip}</div>
            </div>
          )}

          {dest.highlights && dest.highlights.length > 0 && (
            <div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Highlights</div>
              {dest.highlights.map(function(h, i) {
                return (
                  <div key={i} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414" }}>
                    <span style={{ color:"#5A9A5A" }}>+</span>
                    <span>{h}</span>
                  </div>
                );
              })}
            </div>
          )}

          {hasFailedQuals && (
            <div style={{ marginTop:"1.25rem", borderTop:"1px solid #2A2520", paddingTop:"1.25rem" }}>
              {!overrideData && (
                <div style={{ display:"flex", gap:"1rem", alignItems:"center", flexWrap:"wrap" }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#E07070", marginBottom:".25rem" }}>One or more qualifications flagged as fail or partial</div>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070" }}>Run a hypothetical override analysis assuming full qualification - see the full incentive, calculation methodology, and what steps are needed to actually qualify.</div>
                  </div>
                  <button
                    onClick={onRunOverride}
                    disabled={overridePending}
                    style={{ background: overridePending ? "#1A1A0A" : "rgba(201,168,76,.1)", border:"1px solid " + (overridePending ? "#3A3010" : "rgba(201,168,76,.4)"), color: overridePending ? "#5A5040" : "#C9A84C", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".65rem 1.25rem", cursor: overridePending ? "not-allowed" : "pointer", whiteSpace:"nowrap", letterSpacing:".06em" }}>
                    {overridePending ? "Analyzing..." : "Assume Qualification + Re-run"}
                  </button>
                </div>
              )}
              {overridePending && (
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#C9A84C", textAlign:"center", padding:"1rem", display:"flex", alignItems:"center", justifyContent:"center", gap:".75rem" }}>
                  <div style={{ width:14, height:14, borderRadius:"50%", border:"2px solid #2A2520", borderTopColor:"#C9A84C", animation:"spin 1s linear infinite" }} />
                  Running override analysis with full web research...
                </div>
              )}
              {overrideData && (
                <div>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:".5rem" }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#C9A84C", letterSpacing:".1em" }}>Override analysis complete</div>
                    <button onClick={onRunOverride} style={{ background:"transparent", border:"none", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".68rem", cursor:"pointer" }}>Re-run override</button>
                  </div>
                  <OverridePanel data={overrideData} orig={dest} />
                </div>
              )}
            </div>
          )}

        </div>
      )}
    </div>
  );
}

export default function FrameTax() {
  var fileRef   = useRef(null);
  var scriptRef = useRef(null);
  var chatEnd   = useRef(null);

  var [page,       setPage]       = useState("hero");
  var [budget,     setBudget]     = useState("");
  var [script,     setScript]     = useState("");
  var [sName,      setSName]      = useState("");
  var [locReqs,    setLocReqs]    = useState(null);
  var [pref,       setPref]       = useState([]);
  var [cInput,     setCInput]     = useState("");
  var [parsed,     setParsed]     = useState(null);
  var [intel,      setIntel]      = useState(null);
  var [openD,      setOpenD]      = useState({});
  var [qi,         setQi]         = useState(0);
  var [answers,    setAnswers]    = useState({});
  var [tIn,        setTIn]        = useState("");
  var [results,    setResults]    = useState(null);
  var [lStep,      setLStep]      = useState(0);
  var [cidx,       setCidx]       = useState(0);
  var [dragB,      setDragB]      = useState(false);
  var [dragS,      setDragS]      = useState(false);
  var [err,        setErr]        = useState(null);
  var [msgs,       setMsgs]       = useState([]);
  var [chatIn,     setChatIn]     = useState("");
  var [chatLd,     setChatLd]     = useState(false);
  var [openCards,  setOpenCards]  = useState({});
  var [library,    setLibrary]    = useState([]);
  var [showLib,    setShowLib]    = useState(false);
  var [libLoaded,  setLibLoaded]  = useState(false);
  var [overrideResults, setOverrideResults] = useState({});
  var [overridePending, setOverridePending] = useState(null);
  var [driveOpen,      setDriveOpen]      = useState(false);
  var [driveSearch,    setDriveSearch]    = useState("");
  var [driveFiles,     setDriveFiles]     = useState([]);
  var [driveLoading,   setDriveLoading]   = useState(false);
  var [driveTarget,    setDriveTarget]    = useState("budget"); // "budget" or "script"
  var [driveErr,       setDriveErr]       = useState(null);

  // Load library from storage on mount
  useEffect(function() {
    async function loadLib() {
      try {
        var result = await window.storage.get("frametax-library");
        if (result && result.value) {
          setLibrary(JSON.parse(result.value));
        }
      } catch(e) { /* no saved library yet */ }
      setLibLoaded(true);
    }
    loadLib();
  }, []);

  async function saveToLibrary(label) {
    var entry = {
      id: "ft-" + Date.now(),
      label: label || (parsed && parsed.title) || "Untitled Project",
      savedAt: new Date().toLocaleDateString(),
      budgetText: budget,
      totalBudget: parsed && parsed.totalBudget,
      answers: answers,
      pref: pref,
      results: results || null,
      parsed: parsed || null,
      intel: intel || null
    };
    var updated = [entry].concat(library.slice(0, 19));
    setLibrary(updated);
    try {
      await window.storage.set("frametax-library", JSON.stringify(updated));
    } catch(e) { console.error("Save failed", e); }
  }

  async function deleteFromLibrary(id) {
    var updated = library.filter(function(e) { return e.id !== id; });
    setLibrary(updated);
    try {
      await window.storage.set("frametax-library", JSON.stringify(updated));
    } catch(e) {}
  }

  function loadFromLibrary(entry) {
    setBudget(entry.budgetText || "");
    setAnswers(entry.answers || {});
    setPref(entry.pref || []);
    if (entry.parsed) setParsed(entry.parsed);
    if (entry.intel) setIntel(entry.intel);
    if (entry.results) {
      setResults(entry.results);
      setOverrideResults({});
      var openInit = {};
      if (entry.results.destinations && entry.results.destinations[0]) openInit[0] = true;
      setOpenCards(openInit);
      setShowLib(false);
      setPage("results");
    } else {
      setShowLib(false);
      setPage("upload");
    }
  }

  useEffect(function() {
    if (page !== "analyzing") return;
    var iv = setInterval(function() { setCidx(function(i) { return (i+1) % COUNTRIES.length; }); }, 800);
    return function() { clearInterval(iv); };
  }, [page]);

  useEffect(function() {
    var el = document.createElement("script");
    el.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
    el.onload = function() {
      if (window.pdfjsLib) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
      }
    };
    document.head.appendChild(el);
  }, []);

  async function readPDF(file, maxPages) {
    if (!maxPages) maxPages = 30;
    var lib = window.pdfjsLib;
    if (!lib) throw new Error("PDF.js not ready");
    var pdf = await lib.getDocument({ data: await file.arrayBuffer() }).promise;
    var txt = "";
    for (var i = 1; i <= Math.min(pdf.numPages, maxPages); i++) {
      var pg = await pdf.getPage(i);
      var content = await pg.getTextContent();
      txt += content.items.map(function(x) { return x.str; }).join(" ") + "\n";
    }
    return txt;
  }

  async function loadBudget(file) {
    if (!file) return;
    try {
      var txt = file.name.endsWith(".pdf") ? await readPDF(file, 30) : await file.text();
      setBudget(txt.slice(0, 12000));
    } catch(e) { setErr("Could not read file: " + e.message); }
  }

  async function loadScript(file) {
    if (!file) return;
    setSName(file.name);
    try {
      var txt = file.name.endsWith(".pdf") ? await readPDF(file, 60) : await file.text();
      setScript(txt.slice(0, 20000));
    } catch(e) { setErr("Could not read script: " + e.message); }
  }

  async function parseBudget() {
    if (!budget.trim()) { setErr("Please upload or paste your budget first."); return; }
    setErr(null); setPage("parsing");
    try {
      var prompt = "Film budget analyst. Extract all line items AND production intel.\n"
        + "Output ONLY valid JSON - no markdown, no backticks, no explanation. Start with { end with }.\n"
        + "Schema: {\"title\":\"string\",\"totalBudget\":10000000,\"director\":null,\"directorNationality\":null,"
        + "\"writer\":null,\"writerNationality\":null,\"budgetOriginCity\":\"Los Angeles\","
        + "\"budgetOriginRateBase\":\"US union rates IATSE\",\"hasFinanceCosts\":true,\"financeAmount\":85000,"
        + "\"hasInsurance\":true,\"insuranceAmount\":180000,\"hasCompletionBond\":true,\"completionBondAmount\":120000,"
        + "\"departments\":[{\"name\":\"Above the Line\",\"total\":3200000,\"items\":"
        + "[{\"description\":\"Producer Fee\",\"amount\":400000,\"isFixed\":true}]}]}\n"
        + "isFixed=true for ATL talent/rights. isFixed=false for BTL crew/equipment/locations.\n"
        + "BUDGET:\n" + budget;

      var raw = await callClaude([{ role:"user", content:prompt }], false, 4000);
      var d = parseJSON(raw);
      setIntel({
        director: d.director || null,
        directorNationality: d.directorNationality || null,
        writer: d.writer || null,
        writerNationality: d.writerNationality || null,
        originCity: d.budgetOriginCity || "Unknown",
        rateBase: d.budgetOriginRateBase || "Unknown",
        hasFinance: !!d.hasFinanceCosts,
        financeAmt: d.financeAmount || 0,
        hasInsurance: !!d.hasInsurance,
        insuranceAmt: d.insuranceAmount || 0,
        hasBond: !!d.hasCompletionBond,
        bondAmt: d.completionBondAmount || 0
      });
      var first = {};
      if (d.departments && d.departments[0]) first[d.departments[0].name] = true;
      setOpenD(first);
      setParsed(d);
      setPage("review");
    } catch(e) { setErr("Parse error: " + e.message); setPage("upload"); }
  }

  async function analyze() {
    setPage("analyzing"); setLStep(0); setErr(null);
    var lr = locReqs;

    if (script && !lr) {
      try {
        var p2 = "Analyze this script. Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
          + "Schema: {\"writerName\":null,\"writerNationality\":null,\"environments\":[],\"climateNeeds\":[],"
          + "\"specificLocations\":[],\"wouldNotWorkIn\":[]}\n"
          + "SCRIPT:\n" + script.slice(0, 15000);
        var r2 = await callClaude([{ role:"user", content:p2 }], false, 4000);
        lr = parseJSON(r2); setLocReqs(lr);
      } catch(e) { lr = null; }
    }
    setLStep(1);

    var imd = null;
    try {
      var title = (parsed && parsed.title) ? parsed.title : "Untitled";
      var dirPart = (intel && intel.director) ? " directed by " + intel.director : "";
      var p3 = "Search IMDb for attachments to the film \"" + title + "\"" + dirPart + ".\n"
        + "Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
        + "Schema: {\"found\":false,\"directorName\":null,\"directorNationality\":null,\"castAttachments\":[]}";
      var r3 = await callClaude([{ role:"user", content:p3 }], true, 4000);
      imd = parseJSON(r3);
    } catch(e) { imd = null; }
    setLStep(2);

    var fxRates = null;
    try { fxRates = await fetchFXRates(); } catch(e) {}
    var fxNote = "";
    if (fxRates) {
      var fxLines = FX_CURRENCIES
        .filter(function(c) { return fxRates[c]; })
        .map(function(c) { return "USD/" + c + ": " + fxRates[c]; })
        .join(", ");
      fxNote = "\nLIVE FX RATES (fetched " + new Date().toISOString().slice(0,10) + ", source: open.er-api.com): " + fxLines + "\n";
    } else {
      fxNote = "\nFX RATES: Live fetch unavailable - use best available estimate from training data.\n";
    }

    var ci = intel || {};
    var dirName = (imd && imd.directorName) || ci.director || "Unknown";
    var dirNat  = (imd && imd.directorNationality) || ci.directorNationality || (answers && answers.dirNat) || "Unknown";
    var wNat    = (lr && lr.writerNationality) || ci.writerNationality || "Unknown";
    var castParts = (imd && imd.castAttachments && imd.castAttachments.length > 0)
      ? imd.castAttachments.map(function(c) { return c.name + " (" + c.nationality + ")"; })
      : [];
    var cast = castParts.length > 0 ? castParts.join(", ") : ((answers && answers.castNat) || "Unknown");
    var origin  = ci.originCity || "Los Angeles";
    var rateBase = ci.rateBase || "US union rates";
    var total   = (parsed && parsed.totalBudget) || 0;
    var depts   = (parsed && parsed.departments) || [];

    var vBTL = depts
      .filter(function(d) { return !/above|post/i.test(d.name); })
      .reduce(function(s, d) { return s + (d.total || 0); }, 0);
    var fATL = depts
      .filter(function(d) { return /above/i.test(d.name); })
      .reduce(function(s, d) { return s + (d.total || 0); }, 0);

    var qaText = QUESTIONS
      .map(function(q) { return q.label + ": " + ((answers && answers[q.id]) || "Not provided"); })
      .join("\n");

    var prefNote = pref.length > 0
      ? "\nPREFERRED: " + pref.join(", ") + " - always include, honest verdict."
      : "";
    var sNote = lr
      ? "\nSCRIPT REQS: environments: " + ((lr.environments || []).join(",") || "flexible")
        + ", climate: " + ((lr.climateNeeds || []).join(",") || "flexible")
      : "";

    setLStep(3);
    try {
      var filmTitle = (parsed && parsed.title) ? parsed.title : "Untitled";
      var finNote = ci.hasFinance ? "IN budget " + fmt(ci.financeAmt) : "NOT in budget";
      var insNote = ci.hasInsurance ? "IN budget " + fmt(ci.insuranceAmt) : "NOT in budget";

      var prompt = "World-leading film production finance expert.\n\n"
        + fxNote
        + "INTEL: Film=\"" + filmTitle + "\" | Total=" + fmt(total)
        + " | Origin=" + origin + " | RateBase=" + rateBase + "\n"
        + "FixedATL=" + fmt(fATL) + " (do NOT adjust) | VariableBTL=" + fmt(vBTL) + " (MUST rebase to local rates)\n"
        + "Finance=" + finNote + " | Insurance=" + insNote + "\n"
        + "Director=" + dirName + " (" + dirNat + ") | Writer nat.=" + wNat + " | Cast=" + cast + "\n\n"
        + "Q&A:\n" + qaText + prefNote + sNote + "\n\n"
        + "TASK 1: Analyze the HOME BASE (where the budget is priced - " + origin + "). What incentives exist in the home country/state? What is the true net cost if filming at home?\n"
        + "TASK 2: Analyze top 5 international filming destinations. Rebase BTL, USE THE LIVE FX RATES PROVIDED ABOVE (do not estimate), calculate credits, add travel.\n"
        + "Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
        + "Top-level: homeCurrency,budgetOrigin,budgetRateBase,variableBTLBase,fixedATLBase,"
        + "directorIntel{name,nationality,imdbFound},writerIntel{nationality},"
        + "financeFlagged,insuranceFlagged,overallRecommendation,travelNote,currencyNote,"
        + "homeBase{country,flag,incentiveProgram,creditRate,estimatedCredit,trueNetCost,notes,noIncentiveReason,"
        + "sourceUrl,sourceLabel,lastVerified,confidenceTier},"
        + "destinations[].\n"
        + "Per dest: rank,country,flag,incentiveProgram,creditRate,estimatedCredit,baseRateMultiplier,"
        + "localCostUSD,travelCost,trueNetCost,vsSavings,vsPercent,exchangeRate,currencyRisk,"
        + "rateAdjustmentNote,qualifications[]{test,status,detail},atLStatus,insuranceStatus,"
        + "financeStatus,financeEligibleAmount,insuranceEligibleAmount,coproOpportunity,"
        + "qualGap,structuringTip,locationFit,highlights[],"
        + "sourceUrl,sourceLabel,lastVerified,confidenceTier.\n"
        + "sourceUrl: official film commission or government tax authority URL.\n"
        + "sourceLabel: e.g. British Film Commission, Creative Europe, Screen Australia.\n"
        + "lastVerified: ISO date the model believes this data is current to (e.g. 2025-01-01).\n"
        + "confidenceTier: verified (directly from official source) | recent (< 12 months old) | stale (> 12 months or uncertain).\n"
        + "Max 4 quals and 3 highlights per dest. Strings under 120 chars.";

      setLStep(4);
      var raw = await callClaude([{ role:"user", content:prompt }], true, 8000);
      var data = parseJSON(raw);

      // --- TREATY OPTIMIZER ---
      setLStep(4); // reuse step 4 label while this runs
      var treatyData = null;
      try {
        var topDests = (data.destinations || []).slice(0, 5).map(function(d) {
          return d.country + " (" + d.creditRate + ")";
        }).join(", ");
        var tPrompt = "Expert film finance and treaty consultant. Analyze co-production treaty strategies and incentive stacking for this production.\n"
          + "Budget origin: " + origin + " | Total: " + fmt(total) + " | Director: " + dirName + " (" + dirNat + ") | Writer nationality: " + wNat + "\n"
          + "Top destinations under consideration: " + topDests + "\n"
          + "Cast nationalities: " + cast + "\n"
          + "Q&A: " + qaText + "\n\n"
          + "Research and analyze:\n"
          + "1. Which bilateral co-production treaties between these countries could stack credits\n"
          + "2. Split-shoot strategies (e.g. VFX in one country, principal in another)\n"
          + "3. Nationality structuring (passport holder requirements, qualifying spend thresholds)\n"
          + "4. Service company vs full co-pro models\n"
          + "5. Incentive stacking (tax credits + grants + regional funds + broadcaster co-financing)\n"
          + "6. Maximum achievable total incentive % if all strategies are optimally applied\n\n"
          + "Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
          + "Schema: {\"maxAchievableRate\":\"e.g. up to 43% combined\","
          + "\"maxAchievableAmount\":5000000,"
          + "\"baselineAmount\":1200000,"
          + "\"incrementalUplift\":3800000,"
          + "\"executiveSummary\":\"2-3 sentence plain English summary\","
          + "\"strategies\":[{"
          + "\"title\":\"UK-Canada Co-Production Treaty\","
          + "\"type\":\"treaty|stacking|structuring|split_shoot|service_model\","
          + "\"incentiveUplift\":\"e.g. +8% additional credit\","
          + "\"estimatedValue\":800000,"
          + "\"complexity\":\"low|medium|high\","
          + "\"timeToImplement\":\"e.g. 6 months pre-production\","
          + "\"description\":\"clear explanation under 200 chars\","
          + "\"requirements\":[\"requirement 1\",\"requirement 2\"],"
          + "\"risks\":[\"risk 1\"],"
          + "\"bestPairedWith\":\"country name or destination rank\""
          + "}],"
          + "\"treatyMap\":[{\"country1\":\"UK\",\"country2\":\"Canada\",\"treatyType\":\"bilateral co-pro\",\"keyBenefit\":\"Access to both BFI and CMF funding\"}],"
          + "\"stackingOpportunities\":[{\"country\":\"UK\",\"layers\":[{\"name\":\"BFI Tax Relief\",\"rate\":\"25%\"},{\"name\":\"Regional Screen Scotland\",\"rate\":\"up to 15% on Scottish spend\"}],\"combinedRate\":\"up to 40%\",\"conditions\":\"Must qualify for each layer independently\"}],"
          + "\"quickWins\":[{\"action\":\"Register Scottish subsidiary\",\"timeframe\":\"3 months\",\"value\":\"Up to $280K additional\"}],"
          + "\"warnings\":[\"Do not stack X with Y - treaty prevents this\"]}";

        var tRaw = await callClaude([{ role:"user", content:tPrompt }], true, 6000);
        treatyData = parseJSON(tRaw);
      } catch(e) {
        // Try to recover partial data from the raw response
        treatyData = { executiveSummary: "Treaty analysis encountered a formatting issue. Please re-run the analysis or ask the follow-up chat for treaty recommendations.", strategies: [], warnings: ["Treaty optimizer returned invalid data - use the follow-up chat to ask specific treaty questions."] };
      }
      data.treatyOptimizer = treatyData;

      if (pref.length > 0 && data.destinations) {
        data.destinations = data.destinations.map(function(d) {
          return Object.assign({}, d, {
            isPreferred: pref.some(function(p) {
              return d.country.toLowerCase().includes(p.toLowerCase())
                  || p.toLowerCase().includes(d.country.toLowerCase());
            })
          });
        });
      }

      var openInit = {};
      if (data.destinations && data.destinations[0]) openInit[0] = true;
      setOpenCards(openInit);
      setResults(data);
      setPage("results");
    } catch(e) { setErr("Analysis failed: " + e.message); setPage("qa"); }
  }

  async function searchDrive(query) {
    setDriveLoading(true); setDriveErr(null); setDriveFiles([]);
    try {
      var body = {
        model: "claude-sonnet-4-20250514",
        max_tokens: 1000,
        messages: [{ role: "user", content: "Search Google Drive for files matching: " + (query || "budget script film production") + ". List files that are PDFs, spreadsheets, or text documents. Return their names, IDs, and file types." }],
        mcp_servers: [{ type: "url", url: "https://gdrive.mcp.claude.com/mcp", name: "gdrive" }]
      };
      var res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      var data = await res.json();
      // Extract file list from MCP tool results
      var files = [];
      (data.content || []).forEach(function(block) {
        if (block.type === "mcp_tool_result") {
          try {
            var text = (block.content && block.content[0] && block.content[0].text) || "";
            // Try to parse structured file list from result
            var parsed = JSON.parse(text);
            if (Array.isArray(parsed)) files = parsed;
            else if (parsed.files) files = parsed.files;
          } catch(e) {
            // Parse text format - look for file entries
            var lines = ((block.content && block.content[0] && block.content[0].text) || "").split("\n");
            lines.forEach(function(line) {
              var idMatch = line.match(/id[:\s]+([a-zA-Z0-9_-]{10,})/i);
              var nameMatch = line.match(/name[:\s]+"?([^"|\n]+)"?/i) || line.match(/^\d+\.\s+(.+)$/);
              if (idMatch) {
                files.push({ id: idMatch[1], name: (nameMatch && nameMatch[1].trim()) || line.trim(), mimeType: "" });
              }
            });
          }
        }
        if (block.type === "text" && files.length === 0) {
          // Fallback: parse the text response for file names/IDs
          var lines = block.text.split("\n");
          lines.forEach(function(line) {
            var idMatch = line.match(/\b([a-zA-Z0-9_-]{25,})\b/);
            var nameMatch = line.match(/\*\*(.+?)\*\*/) || line.match(/^\d+\.\s+(.+?)(?:\s+-|\s+\(|$)/);
            if (idMatch && nameMatch) {
              files.push({ id: idMatch[1], name: nameMatch[1].trim(), mimeType: "" });
            }
          });
          // If we can't parse IDs, store raw summary for display
          if (files.length === 0 && block.text.length > 20) {
            setDriveErr("Drive returned: " + block.text.slice(0, 300));
          }
        }
      });
      setDriveFiles(files);
    } catch(e) { setDriveErr("Drive search failed: " + e.message); }
    finally { setDriveLoading(false); }
  }

  async function fetchDriveFile(fileId, fileName) {
    setDriveLoading(true); setDriveErr(null);
    try {
      var body = {
        model: "claude-sonnet-4-20250514",
        max_tokens: 4000,
        messages: [{ role: "user", content: "Fetch the full text content of Google Drive file with ID: " + fileId + " (filename: " + fileName + "). Return the raw text content of the file." }],
        mcp_servers: [{ type: "url", url: "https://gdrive.mcp.claude.com/mcp", name: "gdrive" }]
      };
      var res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      var data = await res.json();
      var content = "";
      (data.content || []).forEach(function(block) {
        if (block.type === "mcp_tool_result") {
          content += (block.content && block.content[0] && block.content[0].text) || "";
        }
        if (block.type === "text" && !content) {
          content += block.text;
        }
      });
      if (!content.trim()) throw new Error("No content returned from Drive file");
      if (driveTarget === "budget") {
        setBudget(content.slice(0, 12000));
      } else {
        setScript(content.slice(0, 20000));
        setSName(fileName);
      }
      setDriveOpen(false);
    } catch(e) { setDriveErr("Could not read file: " + e.message); }
    finally { setDriveLoading(false); }
  }

  async function runOverrideAnalysis(destIndex, dest) {
    var key = "dest_" + destIndex;
    setOverridePending(key);
    try {
      var total   = (parsed && parsed.totalBudget) || 0;
      var depts   = (parsed && parsed.departments) || [];
      var vBTL = depts.filter(function(d) { return !/above|post/i.test(d.name); })
        .reduce(function(s, d) { return s + (d.total || 0); }, 0);
      var fATL = depts.filter(function(d) { return /above/i.test(d.name); })
        .reduce(function(s, d) { return s + (d.total || 0); }, 0);
      var ci = intel || {};

      var failedQuals = (dest.qualifications || [])
        .filter(function(q) { return q.status === "fail" || q.status === "partial"; })
        .map(function(q) { return q.test + ": " + q.detail; })
        .join("; ");

      var deptBreakdown = depts.map(function(d) {
        return d.name + " $" + (d.total || 0);
      }).join(", ");

      var prompt = "Expert film finance accountant and production attorney.\n\n"
        + "SCENARIO: Assume this production FULLY QUALIFIES for all incentives in " + dest.country + " - " + dest.incentiveProgram + ".\n"
        + "The qualifications that previously flagged as failed or partial are: " + (failedQuals || "none noted") + "\n"
        + "Ignore those barriers for this analysis. Assume the production has structured itself to fully qualify.\n\n"
        + "BUDGET DATA:\n"
        + "Total Budget: " + fmt(total) + "\n"
        + "Fixed ATL (not rebased): " + fmt(fATL) + " | Variable BTL (rebased to local rates): " + fmt(vBTL) + "\n"
        + "Rate base origin: " + (ci.rateBase || "US union rates") + "\n"
        + "Budget origin: " + (ci.originCity || "Los Angeles") + "\n"
        + "Departments: " + deptBreakdown + "\n"
        + "Finance costs: " + (ci.hasFinance ? fmt(ci.financeAmt) : "not in budget") + "\n"
        + "Insurance: " + (ci.hasInsurance ? fmt(ci.insuranceAmt) : "not in budget") + "\n"
        + "Completion bond: " + (ci.hasBond ? fmt(ci.bondAmt) : "not in budget") + "\n\n"
        + "Previous non-override results for " + dest.country + ":\n"
        + "- Credit rate: " + dest.creditRate + "\n"
        + "- Previous estimated credit: " + fmt(dest.estimatedCredit) + "\n"
        + "- Previous true net cost: " + fmt(dest.trueNetCost) + "\n"
        + "- BTL rate multiplier vs home: " + (dest.baseRateMultiplier || "unknown") + "\n\n"
        + "TASK: Produce a FULL OVERRIDE ANALYSIS assuming complete qualification. Show:\n"
        + "1. What steps/structures the production would need to take to actually qualify\n"
        + "2. The full incentive calculation broken down line by line\n"
        + "3. The true net cost under full qualification\n"
        + "4. How this compares to the previous (non-qualifying) estimate\n\n"
        + "Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
        + "Schema: {\n"
        + "\"assumedCreditRate\": \"e.g. 25%\",\n"
        + "\"qualifyingSpend\": 8000000,\n"
        + "\"totalCreditOverride\": 2000000,\n"
        + "\"rebasedBTL\": 4500000,\n"
        + "\"fixedATL\": 3000000,\n"
        + "\"localCostTotal\": 7500000,\n"
        + "\"travelCost\": 180000,\n"
        + "\"trueNetCostOverride\": 5680000,\n"
        + "\"savingsVsHome\": 2320000,\n"
        + "\"savingsVsPrevious\": 850000,\n"
        + "\"upliftVsPrevious\": \"Additional $850K vs non-qualifying scenario\",\n"
        + "\"methodology\": [\n"
        + "  {\"step\": 1, \"label\": \"Rebase BTL to local rates\", \"calculation\": \"$6.2M BTL x 0.72 local rate multiplier\", \"result\": 4464000, \"notes\": \"UK crew/equipment rates ~28% lower than LA\"},\n"
        + "  {\"step\": 2, \"label\": \"Identify qualifying spend\", \"calculation\": \"Local BTL + eligible ATL elements\", \"result\": 7200000, \"notes\": \"Finance costs excluded per HETV rules\"},\n"
        + "  {\"step\": 3, \"label\": \"Apply credit rate\", \"calculation\": \"$7.2M x 25% HETV credit\", \"result\": 1800000, \"notes\": \"Rate applies to first GBP 1M per episode at 25%, remainder at standard 20%\"},\n"
        + "  {\"step\": 4, \"label\": \"Add travel & shipping\", \"calculation\": \"Key crew + equipment freight\", \"result\": 180000, \"notes\": \"Estimated, not rebased\"},\n"
        + "  {\"step\": 5, \"label\": \"True net cost\", \"calculation\": \"Local cost + travel - credit\", \"result\": 5580000, \"notes\": \"\"}\n"
        + "],\n"
        + "\"structuringSteps\": [\n"
        + "  {\"action\": \"Register UK Ltd production subsidiary\", \"timeframe\": \"3 months pre-production\", \"cost\": \"~$5K legal\", \"critical\": true},\n"
        + "  {\"action\": \"Ensure 10 of 31 BFI cultural test points\", \"timeframe\": \"Script/development phase\", \"cost\": \"Minimal\", \"critical\": true}\n"
        + "],\n"
        + "\"assumedQualifications\": [\n"
        + "  {\"test\": \"Cultural test\", \"howToPass\": \"Score 10+ points via UK subject matter, director, crew\", \"difficulty\": \"low|medium|high\"}\n"
        + "],\n"
        + "\"caveats\": [\"This is a hypothetical scenario assuming full qualification\", \"Consult local attorney before proceeding\"],\n"
        + "\"executiveSummary\": \"2-3 sentence plain English summary of the override scenario\"\n"
        + "}";

      var raw = await callClaude([{ role:"user", content:prompt }], true, 5000);
      var data = parseJSON(raw);
      setOverrideResults(function(prev) {
        var n = Object.assign({}, prev);
        n[key] = data;
        return n;
      });
    } catch(e) {
      setOverrideResults(function(prev) {
        var n = Object.assign({}, prev);
        n[key] = { error: "Override analysis failed: " + e.message };
        return n;
      });
    } finally {
      setOverridePending(null);
    }
  }

  function answerQ(val) {
    var q = QUESTIONS[qi];
    setAnswers(function(prev) { return Object.assign({}, prev, { [q.id]: val }); });
    if (qi < QUESTIONS.length - 1) { setQi(qi + 1); setTIn(""); }
    else analyze();
  }

  async function sendChat(msg) {
    if (!msg || !msg.trim() || chatLd) return;
    setMsgs(function(p) { return p.concat([{ role:"user", text:msg }]); });
    setChatIn(""); setChatLd(true);
    try {
      var destSum = (results && results.destinations || [])
        .map(function(d) { return d.country + " net:" + fmt(d.trueNetCost) + " credit:" + d.creditRate; })
        .join(" | ");
      var ctx = "Film finance expert. Film: " + (parsed && parsed.title || "Feature")
        + ". Budget: " + fmt(parsed && parsed.totalBudget)
        + ". Top destinations: " + destSum;
      var hist = msgs.slice(-6).map(function(m) {
        return { role: m.role === "user" ? "user" : "assistant", content: m.text };
      });
      var allMsgs = [
        { role:"user", content:ctx },
        { role:"assistant", content:"Full context loaded. Ready for questions." }
      ].concat(hist).concat([{ role:"user", content:msg }]);
      var reply = await callClaude(allMsgs, true, 1000);
      setMsgs(function(p) { return p.concat([{ role:"assistant", text:reply }]); });
    } catch(e) {
      setMsgs(function(p) { return p.concat([{ role:"assistant", text:"Sorry, could not process that." }]); });
    } finally {
      setChatLd(false);
      setTimeout(function() { if (chatEnd.current) chatEnd.current.scrollIntoView({ behavior:"smooth" }); }, 100);
    }
  }

  function reset() {
    setPage("hero"); setParsed(null); setResults(null); setAnswers({});
    setQi(0); setBudget(""); setScript(""); setSName(""); setLocReqs(null);
    setPref([]); setIntel(null); setMsgs([]); setErr(null); setOpenCards({});
  }

  var fixedTot = (parsed && parsed.departments)
    ? parsed.departments.reduce(function(s,d) {
        return s + d.items.filter(function(i) { return i.isFixed; })
          .reduce(function(ss,ii) { return ss + (ii.amount||0); }, 0);
      }, 0) : 0;
  var varTot = (parsed && parsed.departments)
    ? parsed.departments.reduce(function(s,d) {
        return s + d.items.filter(function(i) { return !i.isFixed; })
          .reduce(function(ss,ii) { return ss + (ii.amount||0); }, 0);
      }, 0) : 0;

  var navSteps = ["upload","review","qa","results"];

  return (
    <div className="fta">
      <style>{CSS}</style>

      <div style={{ position:"fixed", width:600, height:600, borderRadius:"50%", background:"#C9A84C", top:-200, right:-200, filter:"blur(120px)", opacity:.08, pointerEvents:"none" }} />
      <div style={{ position:"fixed", width:400, height:400, borderRadius:"50%", background:"#4040C0", bottom:-100, left:-100, filter:"blur(120px)", opacity:.08, pointerEvents:"none" }} />

      {page !== "hero" && (
        <nav style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"1rem 2rem", borderBottom:"1px solid #2A2520", position:"sticky", top:0, background:"rgba(8,8,8,.95)", backdropFilter:"blur(10px)", zIndex:100 }}>
          <span style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.2rem", letterSpacing:".08em", cursor:"pointer" }} onClick={reset}>
            FRAME<span style={{ color:"#C9A84C" }}>TAX</span>
          </span>
          <div style={{ display:"flex", gap:4 }}>
            {navSteps.map(function(s, i) {
              var idx = navSteps.indexOf(page);
              return <div key={s} style={{ width:40, height:3, background: i < idx ? "#5A4A20" : i === idx ? "#C9A84C" : "#2A2520", transition:"background .3s" }} />;
            })}
          </div>
          <div style={{ display:"flex", gap:".5rem", alignItems:"center" }}>
            <button onClick={function() { setShowLib(function(v) { return !v; }); }}
              style={{ background:"transparent", color: showLib ? "#C9A84C" : "#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".4rem .85rem", border:"1px solid " + (showLib ? "#C9A84C" : "#2A2520"), cursor:"pointer", transition:"all .2s" }}>
              {"Library" + (library.length > 0 ? " (" + library.length + ")" : "")}
            </button>
            <GhostBtn onClick={reset}>Start over</GhostBtn>
          </div>
        </nav>
      )}

      {/* LIBRARY SLIDE-OUT PANEL */}
      {showLib && (
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
      )}
      {showLib && <div onClick={function() { setShowLib(false); }} style={{ position:"fixed", inset:0, zIndex:199, background:"rgba(0,0,0,.4)" }} />}

      <DrivePicker
        open={driveOpen}
        onClose={function() { setDriveOpen(false); setDriveErr(null); setDriveFiles([]); }}
        onSearch={searchDrive}
        onSelect={fetchDriveFile}
        files={driveFiles}
        loading={driveLoading}
        err={driveErr}
        target={driveTarget}
      />

      {page === "hero" && (
        <div style={{ minHeight:"100vh", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"3rem 2rem", textAlign:"center" }}>
          <Eyebrow mb="2rem">Film Production Finance Intelligence</Eyebrow>
          <h1 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"clamp(2.8rem,7vw,5.5rem)", fontWeight:300, lineHeight:1.05, color:"#F0EAD6", marginBottom:"1.5rem" }}>
            Where in the world<br/>should you{" "}
            <em style={{ color:"#C9A84C", fontStyle:"italic" }}>film</em>?
          </h1>
          <p style={{ maxWidth:520, fontSize:"1rem", fontWeight:300, color:"#8A8070", lineHeight:1.7, marginBottom:"3rem" }}>
            Upload your budget. Our AI scans 100+ global tax incentive programs, rebases BTL costs to local rates, checks IMDb for attachments, and applies live FX to find exactly where your money goes furthest.
          </p>
          <div style={{ display:"flex", gap:"2.5rem", borderTop:"1px solid #2A2520", borderBottom:"1px solid #2A2520", padding:"1.5rem 2.5rem", marginBottom:"3rem", flexWrap:"wrap", justifyContent:"center" }}>
            {[["100+","Jurisdictions"],["Live","FX Rates"],["IMDb","Attachments"],["Full","Cost Rebase"]].map(function(pair) {
              return (
                <div key={pair[1]} style={{ textAlign:"center" }}>
                  <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", fontWeight:600, color:"#C9A84C" }}>{pair[0]}</div>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", letterSpacing:".12em", textTransform:"uppercase", marginTop:".2rem" }}>{pair[1]}</div>
                </div>
              );
            })}
          </div>
          <PrimaryBtn onClick={function() { setPage("upload"); }}>Upload Your Budget</PrimaryBtn>
          <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#8A8070", marginTop:"1.5rem" }}>PDF  Movie Magic  CSV  Paste text</p>
          {library.length > 0 && (
            <button onClick={function() { setPage("upload"); setShowLib(true); }}
              style={{ marginTop:"1.5rem", background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".5rem 1.25rem", cursor:"pointer" }}>
              {"Open Library (" + library.length + " saved project" + (library.length !== 1 ? "s" : "") + ")"}
            </button>
          )}
        </div>
      )}

      {page === "upload" && (
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
      )}

      {page === "parsing" && (
        <div className="ld">
          <div className="ring" />
          <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", color:"#F0EAD6", textAlign:"center" }}>Reading your budget</h2>
          <p style={{ fontFamily:"'DM Mono',monospace", color:"#C9A84C", fontSize:".8rem", letterSpacing:".15em" }}>Extracting line items and production intel...</p>
        </div>
      )}

      {page === "review" && parsed && (
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
      )}

      {page === "qa" && (
        <div className="sc680 fu">
          <Eyebrow>Step 3 of 4 - Production Details</Eyebrow>
          <div style={{ display:"flex", gap:4, marginBottom:"2.5rem" }}>
            {QUESTIONS.map(function(_, i) {
              return <div key={i} style={{ flex:1, height:3, background:i < qi ? "#C9A84C" : i === qi ? "#F0EAD6" : "#2A2520", transition:"background .3s" }} />;
            })}
          </div>
          <ErrBox msg={err} />
          <Mono color="#C9A84C" size=".7rem">{"Question " + (qi+1) + " of " + QUESTIONS.length}</Mono>
          <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", fontWeight:300, lineHeight:1.3, color:"#F0EAD6", marginBottom:"2rem", marginTop:".5rem" }}>{QUESTIONS[qi].label}</h2>

          {QUESTIONS[qi].options ? (
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))", gap:".75rem", marginBottom:"2rem" }}>
              {QUESTIONS[qi].options.map(function(opt) {
                var sel = answers[QUESTIONS[qi].id] === opt;
                return (
                  <button key={opt} onClick={function() { answerQ(opt); }}
                    style={{ padding:".9rem 1.2rem", border:"1px solid " + (sel ? "#C9A84C" : "#2A2520"), background:sel ? "rgba(201,168,76,.12)" : "transparent", color:sel ? "#C9A84C" : "#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".85rem", cursor:"pointer", textAlign:"left", lineHeight:1.4 }}>
                    {opt}
                  </button>
                );
              })}
            </div>
          ) : (
            <div>
              <input
                type="text" value={tIn}
                placeholder={QUESTIONS[qi].ph}
                onChange={function(e) { setTIn(e.target.value); }}
                onKeyDown={function(e) { if (e.key === "Enter" && tIn.trim()) answerQ(tIn.trim()); }}
                style={{ width:"100%", background:"#0E0E0E", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:"1rem", padding:".9rem 1.2rem", outline:"none", marginBottom:"1.5rem" }}
              />
              <div style={{ display:"flex", gap:"1rem" }}>
                <SecBtn onClick={function() { answerQ("Not specified"); }}>Skip</SecBtn>
                <PrimaryBtn onClick={function() { answerQ(tIn.trim() || "Not specified"); }}>Next</PrimaryBtn>
              </div>
            </div>
          )}

          {qi > 0 && <GhostBtn onClick={function() { setQi(qi-1); setTIn(""); }}>Previous</GhostBtn>}
        </div>
      )}

      {page === "analyzing" && (
        <div className="ld">
          <div className="ring" />
          <div>
            <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", color:"#F0EAD6", textAlign:"center" }}>Researching global incentives</h2>
            <p style={{ fontFamily:"'DM Mono',monospace", color:"#C9A84C", fontSize:".8rem", textAlign:"center", marginTop:".5rem", letterSpacing:".15em" }}>{"Scanning " + COUNTRIES[cidx] + "..."}</p>
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:".6rem", width:340 }}>
            {["Scanning script for location requirements","Searching IMDb for cast & director","Reading budget origin & rate base","Scanning 100+ global incentive programs","Running treaty & stacking optimizer"].map(function(s, i) {
              return (
                <div key={i} style={{ display:"flex", alignItems:"center", gap:".75rem", fontFamily:"'DM Mono',monospace", fontSize:".8rem", color:i < lStep ? "#C9A84C" : i === lStep ? "#F0EAD6" : "#8A8070" }}>
                  <div style={{ width:6, height:6, borderRadius:"50%", background:"currentColor", flexShrink:0 }} />
                  {s}
                </div>
              );
            })}
          </div>
          <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070" }}>Takes 30-60 seconds. Researching live data.</p>
        </div>
      )}

      {page === "results" && results && (
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
      )}
    </div>
  );
}

var _root = document.getElementById("root");
if (_root) { createRoot(_root).render(React.createElement(FrameTax)); }
