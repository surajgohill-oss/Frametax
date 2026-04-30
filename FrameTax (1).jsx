import { useState, useEffect, useRef } from "react";

var G="#C9A84C",CR="#F0EAD6",DM="#8A8070",BG="#080808",BD="#2A2520";
var CG="'Cormorant Garamond',serif",MO="'DM Mono',monospace",JO="'Jost',sans-serif";

var S={
  row:{display:"flex",alignItems:"center"},
  col:{display:"flex",flexDirection:"column"},
  sb:{display:"flex",alignItems:"center",justifyContent:"space-between"},
  center:{display:"flex",alignItems:"center",justifyContent:"center"},
  wrap:{display:"flex",flexWrap:"wrap"},
  mono:function(c,sz){return{fontFamily:MO,color:c||DM,fontSize:sz||".75rem"}},
  serif:function(sz,w){return{fontFamily:CG,fontSize:sz||"1rem",fontWeight:w||300}},
  jost:function(sz,w){return{fontFamily:JO,fontSize:sz||".9rem",fontWeight:w||400}},
  card:function(c){return{border:"1px solid "+(c||BD),marginBottom:".75rem",overflow:"hidden"}},
  pad:function(v,h){return{padding:(v||"1rem")+" "+(h||"1.5rem")}},
  box:function(bg,border){return{background:bg||"#0A0A0A",border:"1px solid "+(border||BD)}},
  badge:function(c){return{fontFamily:MO,fontSize:".62rem",padding:".15rem .45rem",background:(c||G)+"18",border:"1px solid "+(c||G)+"40",color:c||G}},
  label:{fontFamily:MO,fontSize:".68rem",letterSpacing:".12em",textTransform:"uppercase",color:DM,marginBottom:".3rem"},
  eyebrow:{fontFamily:MO,fontSize:".7rem",letterSpacing:".25em",color:G,textTransform:"uppercase"},
  upper:{textTransform:"uppercase"},
  ptr:{cursor:"pointer"},
  rel:{position:"relative"},
  abs:{position:"absolute"},
  fix:{position:"fixed"},
};

var QUESTIONS=[
  {id:"genre",label:"What genre is the film?",options:["Feature Film","TV Series","Documentary","Animation","VFX-Heavy Feature"]},
  {id:"shootDate",label:"When is planned principal photography?",isText:true,ph:"e.g. Q3 2026"},
  {id:"duration",label:"How many days of principal photography?",isText:true,ph:"e.g. 45 days"},
  {id:"union",label:"Is this a union production?",options:["Yes - SAG-AFTRA / IATSE","Yes - Local unions only","Non-union","Mixed"]},
  {id:"dirNat",label:"What nationality is the director?",isText:true,ph:"e.g. American"},
  {id:"castNat",label:"What nationality are the lead cast members?",isText:true,ph:"e.g. American, British"},
  {id:"coPro",label:"Do you have a co-production partner?",options:["Yes","No - but open to it","No - prefer single territory"]},
  {id:"localCrew",label:"What % of BTL crew could be sourced locally?",options:["Less than 25%","25-50%","50-75%","More than 75%"]},
  {id:"travel",label:"Is international travel already in the budget?",options:["Yes - fully budgeted","Partially budgeted","Not budgeted yet"]},
  {id:"finCosts",label:"Does the budget include finance costs / insurance / bond?",options:["Yes - all included","Some included","None included"]},
  {id:"subsidiary",label:"Open to registering a local production subsidiary?",options:["Yes","Possibly","No"]},
  {id:"market",label:"What is the primary release market?",options:["North America","UK / Europe","Global / Worldwide","Streaming Platform","Multiple Markets"]},
];

var COUNTRIES=["United Kingdom","Canada","Australia","New Zealand","Ireland","Germany","France","Italy","Spain","Mexico","Czech Republic","Hungary","South Africa","South Korea","Japan","UAE","Georgia","Serbia","Poland","Morocco"];
var SUGGEST_COUNTRIES=["United Kingdom","Canada","Australia","Ireland","New Zealand","South Africa","Mexico","Czech Republic","Hungary","Georgia","Spain","Italy","Morocco","UAE","Serbia","Jordan","South Korea"];
var ALL_COUNTRIES=["Afghanistan","Albania","Algeria","Argentina","Armenia","Australia","Austria","Azerbaijan","Bahrain","Bangladesh","Belgium","Bosnia","Brazil","Bulgaria","Cambodia","Canada","Chile","China","Colombia","Croatia","Cuba","Cyprus","Czech Republic","Denmark","Ecuador","Egypt","Estonia","Finland","France","Georgia","Germany","Ghana","Greece","Guatemala","Hong Kong","Hungary","Iceland","India","Indonesia","Ireland","Israel","Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kosovo","Latvia","Lebanon","Lithuania","Luxembourg","Malaysia","Malta","Mexico","Montenegro","Morocco","Netherlands","New Zealand","Nigeria","Norway","Pakistan","Panama","Peru","Philippines","Poland","Portugal","Puerto Rico","Romania","Russia","Saudi Arabia","Serbia","Singapore","Slovakia","Slovenia","South Africa","South Korea","Spain","Sri Lanka","Sweden","Switzerland","Taiwan","Thailand","Turkey","UAE","Ukraine","United Kingdom","United States","Uruguay","Uzbekistan","Vietnam","Zimbabwe"];
var CHAT_CHIPS=["What co-production structure gives the highest total credit?","How does director nationality affect qualification?","What would unlock a higher credit tier?","Currency hedging strategies?","Which destination has the most flexible cultural test?"];

async function callClaude(messages,useSearch,maxTok){
  var body={model:"claude-sonnet-4-20250514",max_tokens:maxTok||4000,messages};
  if(useSearch)body.tools=[{type:"web_search_20250305",name:"web_search"}];
  var res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  if(!res.ok)throw new Error("API "+res.status);
  var d=await res.json();
  return d.content.filter(function(b){return b.type==="text";}).map(function(b){return b.text;}).join("\n");
}

function parseJSON(raw){
  if(!raw)throw new Error("Empty");
  var s=raw.trim();
  if(s.charCodeAt(0)===96){var fn=s.indexOf("\n");if(fn>-1)s=s.slice(fn+1);var lf=s.lastIndexOf("\n");if(lf>-1&&s.slice(lf).replace(/\s/g,"").charCodeAt(0)===96)s=s.slice(0,lf);s=s.trim();}
  var om=s.match(/\{[\s\S]*\}/)||s.match(/\[[\s\S]*\]/);if(om)s=om[0];
  s=s.replace(/,(\s*[}\]])/g,"$1").replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g,"");
  return JSON.parse(autoClose(s));
}
function autoClose(s){
  var stack=[],inStr=false,esc=false;
  for(var i=0;i<s.length;i++){var c=s[i];if(esc){esc=false;continue;}if(c==="\\"&&inStr){esc=true;continue;}if(c==='"'){inStr=!inStr;continue;}if(inStr)continue;if(c==="{")stack.push("}");else if(c==="[")stack.push("]");else if(c==="}"||c==="]"){if(stack.length&&stack[stack.length-1]===c)stack.pop();}}
  return s.replace(/,\s*$/,"")+stack.reverse().join("");
}

function fmt(n){
  if(!n&&n!==0)return"-";
  var v=parseFloat(String(n).replace(/[^0-9.-]/g,""));
  if(isNaN(v))return String(n);
  if(v>=1000000)return"$"+(v/1000000).toFixed(1)+"M";
  if(v>=1000)return"$"+(v/1000).toFixed(0)+"K";
  return"$"+v.toFixed(0);
}

var CSS="@keyframes spin{to{transform:rotate(360deg)}}@keyframes fu{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}.fu{animation:fu .35s ease}.ring{width:80px;height:80px;border-radius:50%;border:2px solid #2A2520;border-top-color:#C9A84C;animation:spin 1s linear infinite}.ld{min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2rem;text-align:center;padding:2rem}.sc{max-width:900px;margin:0 auto;padding:3rem 2rem}.sc960{max-width:960px;margin:0 auto;padding:3rem 2rem}.sc680{max-width:680px;margin:0 auto;padding:3rem 2rem}";

function Btn(props){
  var bg=props.gold?props.disabled?"#3A3010":G:props.ghost?"transparent":"transparent";
  var col=props.gold?props.disabled?"#5A5040":BG:props.ghost?DM:CR;
  var border=props.gold?"none":props.ghost?"none":"1px solid "+BD;
  return <button onClick={props.onClick} disabled={props.disabled} style={Object.assign({},S.jost(".82rem",props.gold?700:400),{background:bg,color:col,border,padding:props.gold?".9rem 2.5rem":".75rem 1.75rem",cursor:props.disabled?"not-allowed":"pointer",letterSpacing:props.gold?".1em":0,textTransform:props.gold?"uppercase":"none"})}>{props.children}</button>;
}
function Mono(props){return <span style={S.mono(props.color,props.size)}>{props.children}</span>;}
function Eyebrow(props){return <div style={Object.assign({},S.eyebrow,{marginBottom:props.mb||"1rem"})}>{props.children}</div>;}
function ErrBox(props){if(!props.msg)return null;return <div style={{background:"rgba(180,40,40,.1)",border:"1px solid rgba(180,40,40,.3)",padding:"1rem 1.25rem",color:"#E07070",fontSize:".82rem",marginBottom:"1.5rem",fontFamily:MO,lineHeight:1.6}}>{props.msg}</div>;}
function Spinner(props){return <div style={{width:props.size||14,height:props.size||14,borderRadius:"50%",border:"2px solid "+BD,borderTopColor:G,animation:"spin 1s linear infinite",flexShrink:0}} />;}

function DrivePicker(props){
  var [q,setQ]=useState("");
  if(!props.open)return null;
  return(
    <div style={Object.assign({},S.fix,{inset:0,zIndex:300,display:"flex",alignItems:"center",justifyContent:"center"})}>
      <div onClick={props.onClose} style={{position:"absolute",inset:0,background:"rgba(0,0,0,.7)"}} />
      <div style={{position:"relative",width:"min(540px,95vw)",background:"#0C0C0C",border:"1px solid "+BD,zIndex:1,display:"flex",flexDirection:"column",maxHeight:"80vh"}}>
        <div style={Object.assign({},S.sb,S.pad(".85rem","1.25rem"),{borderBottom:"1px solid "+BD})}>
          <div>
            <div style={S.serif("1.3rem")}>{props.target==="budget"?"Select Budget File":"Select Script File"}</div>
            <div style={S.mono(DM,".7rem")}>Google Drive - PDF, spreadsheet, or text</div>
          </div>
          <button onClick={props.onClose} style={{background:"transparent",border:"none",color:DM,cursor:"pointer",fontSize:"1.2rem"}}>x</button>
        </div>
        <div style={Object.assign({},S.pad(".75rem","1.25rem"),{borderBottom:"1px solid "+BD})}>
          <div style={Object.assign({},S.row,{gap:".5rem"})}>
            <input value={q} onChange={function(e){setQ(e.target.value);}} onKeyDown={function(e){if(e.key==="Enter")props.onSearch(q);}} placeholder="Search Drive... (budget, film, production)" style={{flex:1,background:BG,border:"1px solid "+BD,color:CR,fontFamily:JO,fontSize:".88rem",padding:".6rem .9rem",outline:"none"}} />
            <button onClick={function(){props.onSearch(q);}} disabled={props.loading} style={{background:G,color:BG,border:"none",fontFamily:JO,fontWeight:700,fontSize:".78rem",padding:".6rem 1rem",cursor:props.loading?"not-allowed":"pointer",textTransform:"uppercase"}}>
              {props.loading?"...":"Search"}
            </button>
          </div>
          <div style={Object.assign({},S.wrap,{gap:".35rem",marginTop:".5rem"})}>
            {["budget","film production","script","movie magic"].map(function(chip){
              return <button key={chip} onClick={function(){setQ(chip);props.onSearch(chip);}} style={{background:"transparent",border:"1px solid "+BD,color:DM,fontSize:".68rem",padding:".2rem .5rem",cursor:"pointer",fontFamily:MO}}>{chip}</button>;
            })}
          </div>
        </div>
        <div style={{flex:1,overflowY:"auto",padding:"1rem 1.25rem"}}>
          {props.loading&&<div style={Object.assign({},S.center,{padding:"2rem",gap:".75rem",fontFamily:MO,color:G,fontSize:".8rem"})}><Spinner size={16} />Searching Drive...</div>}
          {props.err&&<div style={{fontFamily:MO,fontSize:".75rem",color:"#E07070",padding:"1rem",lineHeight:1.6}}>{props.err}<br/><span style={{color:DM}}>Check Settings - Connectors - Google Drive.</span></div>}
          {!props.loading&&!props.err&&props.files.length===0&&<div style={{textAlign:"center",padding:"2.5rem",fontFamily:MO,fontSize:".76rem",color:DM,lineHeight:1.8}}>Search your Drive above to find budget or script files.</div>}
          {props.files.map(function(f,i){
            return(
              <div key={f.id||i} onClick={function(){props.onSelect(f.id,f.name);}} style={{display:"flex",alignItems:"center",gap:".85rem",padding:".75rem .9rem",border:"1px solid "+BD,marginBottom:".4rem",cursor:"pointer",background:BG}}>
                <div style={S.badge()}>{f.mimeType&&f.mimeType.includes("pdf")?"PDF":f.mimeType&&f.mimeType.includes("sheet")?"XLS":"DOC"}</div>
                <div style={{flex:1,overflow:"hidden"}}>
                  <div style={{fontSize:".86rem",color:CR,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{f.name}</div>
                  {f.modifiedTime&&<div style={S.mono(DM,".67rem")}>{"Modified: "+new Date(f.modifiedTime).toLocaleDateString()}</div>}
                </div>
                <div style={S.mono(DM,".7rem")}>Select</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function HomeBaseCard(props){
  var hb=props.homeBase;
  var [open,setOpen]=useState(false);
  if(!hb)return null;
  var hasCredit=hb.estimatedCredit&&hb.estimatedCredit>0;
  return(
    <div style={Object.assign({},S.card("rgba(201,168,76,.2)"),{background:"rgba(201,168,76,.02)"})}>
      <div onClick={function(){setOpen(!open);}} style={Object.assign({},S.row,{gap:"1.25rem",padding:"1rem 1.5rem",cursor:"pointer"})}>
        <div style={Object.assign({},S.serif("1.3rem"),{color:DM,minWidth:"3rem",textAlign:"center"})}>HOME</div>
        <div style={{flex:1}}>
          <div style={Object.assign({},S.row,{gap:".5rem"})}>
            <span style={S.serif("1.4rem",300)}>{(hb.flag||"")+" "+hb.country}</span>
            <span style={S.badge(DM)}>BASELINE</span>
          </div>
          <div style={S.mono(DM,".72rem")}>{hb.incentiveProgram||"No incentive program"}</div>
        </div>
        <div style={{textAlign:"right"}}>
          <div style={S.mono(hasCredit?G:DM,"1rem")}>{hb.creditRate||"No credit"}</div>
          <div style={S.mono(CR,".72rem")}>{hb.trueNetCost?"Net: "+fmt(hb.trueNetCost):props.budget?"Net: "+fmt(props.budget):""}</div>
        </div>
        <div style={{color:DM}}>{open?"^":"v"}</div>
      </div>
      {open&&(
        <div style={{padding:"1rem 1.5rem",borderTop:"1px solid "+BD}}>
          <div style={Object.assign({},S.row,{gap:".75rem",marginBottom:".75rem"})}>
            {[["Home Budget",fmt(props.budget),CR],["Home Credit",hasCredit?fmt(hb.estimatedCredit):"None",hasCredit?G:DM],["True Net",fmt(hb.trueNetCost||props.budget),"#5A9A5A"]].map(function(r){
              return <div key={r[0]} style={Object.assign({},S.box(),{flex:1,padding:".65rem .85rem"})}><div style={S.label}>{r[0]}</div><div style={S.mono(r[2],".9rem")}>{r[1]}</div></div>;
            })}
          </div>
          {hb.notes&&<p style={{fontSize:".82rem",color:DM,lineHeight:1.6}}>{hb.notes}</p>}
          {!hasCredit&&hb.noIncentiveReason&&<div style={{padding:".75rem",background:"rgba(224,112,112,.06)",border:"1px solid rgba(224,112,112,.2)",fontFamily:MO,fontSize:".76rem",color:"#E07070",marginTop:".5rem"}}>{hb.noIncentiveReason}</div>}
        </div>
      )}
    </div>
  );
}

function TreatyOptimizer(props){
  var t=props.data;
  var [open,setOpen]=useState(true);
  var [active,setActive]=useState(null);
  if(!t)return null;
  function cplx(c){return c==="low"?"#5A9A5A":c==="medium"?"#C9801C":"#E07070";}
  function tlabel(type){return({treaty:"TREATY",stacking:"STACKING",structuring:"STRUCTURING",split_shoot:"SPLIT SHOOT",service_model:"SERVICE MODEL"})[type]||type.toUpperCase();}
  return(
    <div style={Object.assign({},S.card("rgba(201,168,76,.3)"),{background:"rgba(201,168,76,.02)",marginTop:"2rem"})}>
      <div onClick={function(){setOpen(!open);}} style={Object.assign({},S.sb,{padding:"1.25rem 1.75rem",cursor:"pointer",background:"rgba(201,168,76,.05)",borderBottom:open?"1px solid rgba(201,168,76,.2)":"none"})}>
        <div>
          <div style={Object.assign({},S.serif("1.5rem"),{color:G})}>Treaty + Incentive Optimizer</div>
          <div style={S.mono(DM,".7rem")}>Co-pro treaties, stacking, and structuring to maximize total incentive</div>
        </div>
        <div style={{textAlign:"right",marginLeft:"1.5rem"}}>
          {t.maxAchievableRate&&<div style={Object.assign({},S.serif("1.8rem"),{color:G})}>{t.maxAchievableRate}</div>}
          {t.maxAchievableAmount&&<div style={S.mono("#5A9A5A",".72rem")}>{"up to "+fmt(t.maxAchievableAmount)+" combined"}</div>}
          <div style={S.mono(DM,".75rem")}>{open?"^":"v"}</div>
        </div>
      </div>
      {open&&(
        <div style={{padding:"1.25rem 1.75rem"}}>
          {t.executiveSummary&&<div style={{background:"rgba(201,168,76,.06)",border:"1px solid rgba(201,168,76,.15)",padding:"1rem",marginBottom:"1.25rem",fontSize:".88rem",color:CR,lineHeight:1.7,fontFamily:JO}}>{t.executiveSummary}</div>}
          {t.baselineAmount!==undefined&&(
            <div style={Object.assign({},S.wrap,{gap:"1rem",marginBottom:"1.25rem"})}>
              {[["Baseline",fmt(t.baselineAmount),DM],["Max Achievable",fmt(t.maxAchievableAmount),G],["Uplift","+"+fmt(t.incrementalUplift),"#5A9A5A"]].map(function(r){
                return <div key={r[0]} style={Object.assign({},S.box(),{flex:1,minWidth:130,padding:".75rem .9rem"})}><div style={S.label}>{r[0]}</div><div style={Object.assign({},S.serif("1.5rem"),{color:r[2]})}>{r[1]}</div></div>;
              })}
            </div>
          )}
          {t.quickWins&&t.quickWins.length>0&&(
            <div style={{marginBottom:"1.25rem"}}>
              <div style={Object.assign({},S.eyebrow,{color:"#5A9A5A",marginBottom:".5rem"})}>Quick Wins</div>
              {t.quickWins.map(function(w,i){
                return <div key={i} style={Object.assign({},S.row,{gap:".75rem",background:"rgba(90,154,90,.04)",border:"1px solid rgba(90,154,90,.15)",padding:".55rem .9rem",marginBottom:".35rem",fontSize:".82rem"})}><span style={{color:"#5A9A5A"}}>+</span><span style={{flex:1,color:CR}}>{w.action}</span><span style={S.mono("#5A9A5A",".7rem")}>{w.value}</span><span style={S.mono(DM,".68rem")}>{w.timeframe}</span></div>;
              })}
            </div>
          )}
          {t.strategies&&t.strategies.length>0&&(
            <div style={{marginBottom:"1.25rem"}}>
              <div style={Object.assign({},S.eyebrow,{marginBottom:".6rem"})}>Strategies</div>
              {t.strategies.map(function(str,i){
                var isA=active===i;
                return(
                  <div key={i} style={S.card(isA?"rgba(201,168,76,.4)":undefined)}>
                    <div onClick={function(){setActive(isA?null:i);}} style={{display:"flex",alignItems:"center",gap:"1rem",padding:".85rem 1rem",cursor:"pointer",background:isA?"rgba(201,168,76,.05)":"#0A0A0A"}}>
                      <div style={{flex:1}}>
                        <div style={Object.assign({},S.row,{gap:".5rem",flexWrap:"wrap",marginBottom:".2rem"})}><span style={{fontFamily:JO,fontSize:".88rem",color:CR,fontWeight:500}}>{str.title}</span><span style={S.badge()}>{tlabel(str.type)}</span></div>
                        <div style={S.mono(DM,".7rem")}>{str.description}</div>
                      </div>
                      <div style={{textAlign:"right",flexShrink:0}}>
                        {str.incentiveUplift&&<div style={S.mono("#5A9A5A",".83rem")}>{str.incentiveUplift}</div>}
                        {str.estimatedValue&&<div style={S.mono(G,".7rem")}>{fmt(str.estimatedValue)}</div>}
                        <div style={Object.assign({},S.badge(cplx(str.complexity)),{display:"inline-block",marginTop:".25rem",fontSize:".6rem"})}>{(str.complexity||"").toUpperCase()}</div>
                      </div>
                      <div style={{color:DM,marginLeft:".25rem"}}>{isA?"^":"v"}</div>
                    </div>
                    {isA&&(
                      <div style={{padding:".85rem 1rem",borderTop:"1px solid "+BD,background:BG}}>
                        {str.timeToImplement&&<div style={S.mono(DM,".7rem")}>{"Timeline: "+str.timeToImplement}</div>}
                        {str.bestPairedWith&&<div style={Object.assign({},S.mono(G,".7rem"),{marginTop:".3rem"})}>{"Best with: "+str.bestPairedWith}</div>}
                        {str.requirements&&str.requirements.length>0&&(
                          <div style={{marginTop:".6rem"}}>
                            <div style={Object.assign({},S.eyebrow,{fontSize:".62rem",marginBottom:".3rem"})}>Requirements</div>
                            {str.requirements.map(function(r,ri){return <div key={ri} style={{fontSize:".78rem",color:DM,paddingLeft:"1rem",borderLeft:"1px solid "+BD,marginBottom:".2rem"}}>{r}</div>;})}
                          </div>
                        )}
                        {str.risks&&str.risks.length>0&&(
                          <div style={{marginTop:".6rem"}}>
                            <div style={Object.assign({},S.eyebrow,{fontSize:".62rem",color:"#E07070",marginBottom:".3rem"})}>Risks</div>
                            {str.risks.map(function(r,ri){return <div key={ri} style={{fontSize:".78rem",color:DM,paddingLeft:"1rem",borderLeft:"1px solid rgba(224,112,112,.3)",marginBottom:".2rem"}}>{r}</div>;})}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          {t.stackingOpportunities&&t.stackingOpportunities.length>0&&(
            <div style={{marginBottom:"1.25rem"}}>
              <div style={Object.assign({},S.eyebrow,{marginBottom:".6rem"})}>Incentive Stacking</div>
              {t.stackingOpportunities.map(function(so,i){
                return(
                  <div key={i} style={Object.assign({},S.card(),{marginBottom:".5rem"})}>
                    <div style={Object.assign({},S.sb,{padding:".65rem .9rem",background:"#0C0C0C"})}><span style={{fontFamily:JO,fontSize:".86rem",color:CR}}>{so.country}</span><span style={S.mono(G,".78rem")}>{so.combinedRate}</span></div>
                    <div style={{padding:".5rem .9rem"}}>
                      {(so.layers||[]).map(function(l,li){return <div key={li} style={Object.assign({},S.sb,{padding:".28rem 0",borderBottom:"1px solid #141414",fontSize:".76rem"})}><span style={{color:DM}}>{l.name}</span><span style={S.mono(CR,".75rem")}>{l.rate}</span></div>;})}
                      {so.conditions&&<div style={Object.assign({},S.mono(DM,".68rem"),{marginTop:".4rem",lineHeight:1.5})}>{so.conditions}</div>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          {t.treatyMap&&t.treatyMap.length>0&&(
            <div style={{marginBottom:"1.25rem"}}>
              <div style={Object.assign({},S.eyebrow,{marginBottom:".5rem"})}>Active Treaty Map</div>
              {t.treatyMap.map(function(tm,i){
                return <div key={i} style={Object.assign({},S.row,{gap:".75rem",padding:".5rem .85rem",background:"#0A0A0A",border:"1px solid "+BD,marginBottom:".35rem",fontSize:".78rem"})}><span style={S.mono(G,".75rem")}>{tm.country1+" + "+tm.country2}</span><span style={S.mono(DM,".68rem")}>{tm.treatyType}</span><span style={{color:CR,flex:1}}>{tm.keyBenefit}</span></div>;
              })}
            </div>
          )}
          {t.warnings&&t.warnings.length>0&&(
            <div style={{background:"rgba(224,112,112,.05)",border:"1px solid rgba(224,112,112,.2)",padding:".9rem 1.1rem"}}>
              <div style={Object.assign({},S.eyebrow,{color:"#E07070",fontSize:".65rem",marginBottom:".4rem"})}>Warnings</div>
              {t.warnings.map(function(w,i){return <div key={i} style={{fontSize:".78rem",color:DM,padding:".2rem 0",borderBottom:"1px solid rgba(224,112,112,.1)",lineHeight:1.5}}>{w}</div>;})}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function OverridePanel(props){
  var d=props.data;
  if(!d)return null;
  if(d.error)return <div style={{margin:"1rem 0",background:"rgba(224,112,112,.06)",border:"1px solid rgba(224,112,112,.2)",padding:"1rem",fontFamily:MO,fontSize:".76rem",color:"#E07070"}}>{d.error}</div>;
  return(
    <div style={{marginTop:"1rem",border:"1px solid rgba(201,168,76,.4)",background:"rgba(201,168,76,.03)",overflow:"hidden"}}>
      <div style={{background:"rgba(201,168,76,.08)",borderBottom:"1px solid rgba(201,168,76,.2)",padding:".85rem 1.25rem",display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div><div style={Object.assign({},S.eyebrow,{fontSize:".68rem"})}>Override - Assumed Full Qualification</div><div style={S.mono(DM,".68rem")}>Hypothetical scenario</div></div>
        <div style={{textAlign:"right"}}><div style={Object.assign({},S.serif("1.5rem"),{color:G})}>{d.assumedCreditRate}</div><div style={S.mono("#5A9A5A",".68rem")}>{"Credit: "+fmt(d.totalCreditOverride)}</div></div>
      </div>
      <div style={{padding:"1.1rem 1.25rem"}}>
        {d.executiveSummary&&<div style={{background:"rgba(201,168,76,.06)",border:"1px solid rgba(201,168,76,.12)",padding:".85rem",marginBottom:"1rem",fontSize:".84rem",color:CR,lineHeight:1.7,fontFamily:JO}}>{d.executiveSummary}</div>}
        <div style={Object.assign({},S.row,{gap:".6rem",marginBottom:"1rem"})}>
          {[["Override Net",fmt(d.trueNetCostOverride),"#5A9A5A"],["Override Credit",fmt(d.totalCreditOverride),G],["Extra vs Prev","+"+fmt(d.savingsVsPrevious),"#5A9A5A"]].map(function(r){
            return <div key={r[0]} style={Object.assign({},S.box(),{flex:1,padding:".65rem .75rem"})}><div style={S.label}>{r[0]}</div><div style={S.mono(r[2],".88rem")}>{r[1]}</div></div>;
          })}
        </div>
        {d.methodology&&d.methodology.length>0&&(
          <div style={{marginBottom:"1rem"}}>
            <div style={Object.assign({},S.eyebrow,{marginBottom:".5rem"})}>Calculation Methodology</div>
            <div style={{border:"1px solid "+BD,overflow:"hidden"}}>
              {d.methodology.map(function(step,i){
                return(
                  <div key={i} style={{display:"grid",gridTemplateColumns:"1.4rem 1fr auto",gap:".65rem",alignItems:"start",padding:".65rem .85rem",borderBottom:i<d.methodology.length-1?"1px solid #141414":"none",background:i%2===0?BG:"#0A0A0A"}}>
                    <div style={S.mono(G,".68rem")}>{step.step}</div>
                    <div><div style={{fontFamily:JO,fontSize:".82rem",color:CR,fontWeight:500,marginBottom:".12rem"}}>{step.label}</div><div style={S.mono(DM,".7rem")}>{step.calculation}</div>{step.notes&&<div style={S.mono("#5A5A50",".66rem")}>{step.notes}</div>}</div>
                    <div style={S.mono(CR,".85rem")}>{fmt(step.result)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        {d.structuringSteps&&d.structuringSteps.length>0&&(
          <div style={{marginBottom:"1rem"}}>
            <div style={Object.assign({},S.eyebrow,{marginBottom:".5rem"})}>How to Actually Qualify</div>
            {d.structuringSteps.map(function(st,i){
              return(
                <div key={i} style={{display:"flex",gap:".65rem",alignItems:"flex-start",padding:".55rem .85rem",border:"1px solid "+(st.critical?"rgba(201,168,76,.25)":BD),background:st.critical?"rgba(201,168,76,.04)":"#0A0A0A",marginBottom:".35rem"}}>
                  <span style={{color:st.critical?G:"#5A9A5A",fontFamily:MO,fontSize:".7rem",paddingTop:".1rem",flexShrink:0}}>{st.critical?"!":"+"}</span>
                  <div style={{flex:1}}><div style={{fontSize:".82rem",color:CR}}>{st.action}</div><div style={S.mono(DM,".68rem")}>{st.timeframe+(st.cost?" - "+st.cost:"")}</div></div>
                  {st.critical&&<span style={Object.assign({},S.badge(),{fontSize:".6rem",flexShrink:0})}>REQUIRED</span>}
                </div>
              );
            })}
          </div>
        )}
        {d.caveats&&d.caveats.length>0&&<div style={{background:"rgba(138,128,112,.05)",border:"1px solid "+BD,padding:".75rem .9rem"}}>{d.caveats.map(function(c,i){return <div key={i} style={S.mono(DM,".7rem")}>{c}</div>;})}</div>}
      </div>
    </div>
  );
}

function DestCard(props){
  var dest=props.dest,isTop=props.isTop,budget=props.budget,open=props.open,setOpen=props.setOpen;
  var overrideData=props.overrideData,overridePending=props.overridePending,onRunOverride=props.onRunOverride;
  var savings=budget&&dest.trueNetCost?fmt(budget-dest.trueNetCost):null;
  var hasFailedQuals=(dest.qualifications||[]).some(function(q){return q.status==="fail"||q.status==="partial";});
  function qColor(s){return s==="pass"||s==="likely_pass"?"#5A9A5A":s==="partial"?"#C97A1C":"#E07070";}
  function qIcon(s){return s==="pass"||s==="likely_pass"?"OK":s==="partial"?"~":"X";}
  var locColor=G;
  var lf=(dest.locationFit||"").toLowerCase();
  if(lf.match(/excell|perfect|ideal/))locColor="#5A9A5A";
  if(lf.match(/poor|cannot|not suit/))locColor="#E07070";
  return(
    <div style={S.card(isTop?G:undefined)}>
      <div onClick={function(){setOpen(!open);}} style={Object.assign({},S.row,{gap:"1.25rem",padding:"1.1rem 1.5rem",background:"#0C0C0C",cursor:"pointer"})}>
        <div style={Object.assign({},S.serif("1.7rem",600),{color:G,minWidth:"2rem",textAlign:"center"})}>{"#"+dest.rank}</div>
        <div style={{flex:1}}>
          <div style={Object.assign({},S.row,{gap:".5rem",flexWrap:"wrap"})}>
            <span style={S.serif("1.4rem",300)}>{dest.flag+" "+dest.country}</span>
            {dest.isPreferred&&<span style={S.badge()}>REQUESTED</span>}
          </div>
          <div style={S.mono(DM,".72rem")}>{dest.incentiveProgram}</div>
          {dest.locationFit&&<div style={Object.assign({},S.badge(locColor),{display:"inline-block",marginTop:".3rem",fontSize:".68rem"})}>{"Loc: "+dest.locationFit}</div>}
        </div>
        <div style={{textAlign:"right",flexShrink:0}}>
          <div style={S.mono(G,"1.05rem")}>{dest.creditRate}</div>
          {savings&&<div style={S.mono("#5A9A5A",".72rem")}>{"Save ~"+savings}</div>}
        </div>
        <div style={{color:DM,marginLeft:".5rem"}}>{open?"^":"v"}</div>
      </div>
      {open&&(
        <div style={{padding:"1.1rem 1.5rem",borderTop:"1px solid "+BD}}>
          {dest.rateAdjustmentNote&&<div style={{fontFamily:MO,fontSize:".73rem",color:G,background:"rgba(201,168,76,.05)",border:"1px solid rgba(201,168,76,.15)",padding:".55rem .9rem",marginBottom:".85rem"}}>{"Rate: "+dest.rateAdjustmentNote}</div>}
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:".65rem",marginBottom:".85rem"}}>
            {[["Local Cost",fmt(dest.localCostUSD),CR],["Tax Credit","-"+fmt(dest.estimatedCredit),G],["Travel","+"+fmt(dest.travelCost),CR],["True Net",fmt(dest.trueNetCost),"#5A9A5A"]].map(function(r){
              return <div key={r[0]} style={Object.assign({},S.box(),{padding:".65rem .75rem"})}><div style={S.label}>{r[0]}</div><div style={S.mono(r[2],".88rem")}>{r[1]}</div></div>;
            })}
          </div>
          {dest.vsSavings&&<div style={{display:"inline-block",fontFamily:MO,fontSize:".73rem",color:"#5A9A5A",background:"rgba(90,154,90,.08)",border:"1px solid rgba(90,154,90,.2)",padding:".35rem .8rem",marginBottom:".75rem"}}>{"Save "+dest.vsSavings+" ("+dest.vsPercent+") vs home"}</div>}
          {dest.exchangeRate&&<p style={Object.assign({},S.mono(DM,".72rem"),{marginBottom:".65rem"})}>{"FX: "+dest.exchangeRate+" - Risk: "+dest.currencyRisk}</p>}
          {dest.qualifications&&dest.qualifications.length>0&&(
            <div>
              <div style={Object.assign({},S.eyebrow,{fontSize:".65rem",margin:"1rem 0 .45rem"})}>Qualification Analysis</div>
              {dest.qualifications.map(function(q,i){
                return <div key={i} style={{display:"flex",gap:".65rem",fontSize:".8rem",color:DM,padding:".32rem 0",borderBottom:"1px solid #141414",lineHeight:1.5}}><span style={{color:qColor(q.status),flexShrink:0,fontFamily:MO,fontSize:".68rem"}}>{qIcon(q.status)}</span><span><strong style={{color:CR}}>{q.test}</strong>{" - "+q.detail}</span></div>;
              })}
            </div>
          )}
          <div style={Object.assign({},S.eyebrow,{fontSize:".65rem",margin:"1rem 0 .45rem"})}>Cost Eligibility</div>
          {[["Above-the-Line",dest.atLStatus],["Insurance & Bond",dest.insuranceStatus],["Finance Costs",dest.financeStatus]].map(function(r){
            return <div key={r[0]} style={{display:"flex",gap:".65rem",fontSize:".8rem",color:DM,padding:".32rem 0",borderBottom:"1px solid #141414"}}><span style={{color:G}}>*</span><span><strong style={{color:CR}}>{r[0]}</strong>{" - "+(r[1]||"Check with local film commission")}</span></div>;
          })}
          {dest.coproOpportunity&&<div style={{marginTop:".65rem",fontSize:".8rem",color:DM}}>{"Co-pro: "+dest.coproOpportunity}</div>}
          {dest.qualGap&&<div style={{background:"rgba(201,168,76,.06)",border:"1px solid rgba(201,168,76,.2)",padding:".85rem",marginTop:".85rem"}}><div style={Object.assign({},S.eyebrow,{fontSize:".65rem",marginBottom:".35rem"})}>Optimization</div><div style={{fontSize:".82rem",color:CR,lineHeight:1.6}}>{dest.qualGap}</div></div>}
          {dest.structuringTip&&<div style={{background:"rgba(90,154,90,.05)",border:"1px solid rgba(90,154,90,.2)",padding:".85rem",marginTop:".65rem"}}><div style={Object.assign({},S.eyebrow,{color:"#5A9A5A",fontSize:".65rem",marginBottom:".35rem"})}>Structuring</div><div style={{fontSize:".82rem",color:CR,lineHeight:1.6}}>{dest.structuringTip}</div></div>}
          {dest.highlights&&dest.highlights.length>0&&(
            <div>
              <div style={Object.assign({},S.eyebrow,{fontSize:".65rem",margin:"1rem 0 .45rem"})}>Highlights</div>
              {dest.highlights.map(function(h,i){return <div key={i} style={{display:"flex",gap:".65rem",fontSize:".8rem",color:DM,padding:".32rem 0",borderBottom:"1px solid #141414"}}><span style={{color:"#5A9A5A"}}>+</span><span>{h}</span></div>;})}
            </div>
          )}
          {hasFailedQuals&&(
            <div style={{marginTop:"1.1rem",borderTop:"1px solid "+BD,paddingTop:"1.1rem"}}>
              {!overrideData&&(
                <div style={Object.assign({},S.row,{gap:"1rem",flexWrap:"wrap"})}>
                  <div style={{flex:1}}><div style={S.mono("#E07070",".7rem")}>Qualifications flagged fail or partial</div><div style={Object.assign({},S.mono(DM,".67rem"),{marginTop:".2rem"})}>Run hypothetical override assuming full qualification - see full incentive and methodology.</div></div>
                  <button onClick={onRunOverride} disabled={overridePending} style={{background:overridePending?"#1A1A0A":"rgba(201,168,76,.1)",border:"1px solid rgba(201,168,76,.4)",color:overridePending?"#5A5040":G,fontFamily:MO,fontSize:".73rem",padding:".6rem 1.1rem",cursor:overridePending?"not-allowed":"pointer",whiteSpace:"nowrap"}}>
                    {overridePending?"Analyzing...":"Assume Qualification"}
                  </button>
                </div>
              )}
              {overridePending&&<div style={Object.assign({},S.center,{gap:".65rem",fontFamily:MO,fontSize:".76rem",color:G,padding:".85rem"})}><Spinner />Running override analysis...</div>}
              {overrideData&&(
                <div>
                  <div style={Object.assign({},S.sb,{marginBottom:".4rem"})}><div style={S.mono(G,".68rem")}>Override complete</div><button onClick={onRunOverride} style={{background:"transparent",border:"none",color:DM,fontFamily:MO,fontSize:".67rem",cursor:"pointer"}}>Re-run</button></div>
                  <OverridePanel data={overrideData} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SavePrompt(props){
  var [label,setLabel]=useState(props.defaultLabel||"");
  var [saved,setSaved]=useState(false);
  function doSave(){props.onSave(label);setSaved(true);setTimeout(function(){setSaved(false);},2500);}
  if(saved)return <div style={Object.assign({},S.mono("#5A9A5A",".76rem"),{textAlign:"center",padding:".75rem"})}>Saved to Library</div>;
  return(
    <div>
      <div style={Object.assign({},S.mono(DM,".7rem"),{marginBottom:".4rem"})}>Save this analysis</div>
      <input value={label} onChange={function(e){setLabel(e.target.value);}} onKeyDown={function(e){if(e.key==="Enter")doSave();}} style={{width:"100%",background:"#0A0A0A",border:"1px solid "+BD,color:CR,fontFamily:JO,fontSize:".84rem",padding:".6rem .85rem",outline:"none",marginBottom:".5rem"}} />
      <button onClick={doSave} style={{background:G,color:BG,border:"none",fontFamily:JO,fontSize:".8rem",fontWeight:700,letterSpacing:".08em",padding:".7rem 1.25rem",cursor:"pointer",width:"100%",textTransform:"uppercase"}}>Save to Library</button>
    </div>
  );
}

export default function FrameTax(){
  var fileRef=useRef(null),scriptRef=useRef(null),chatEnd=useRef(null);
  var [page,setPage]=useState("hero");
  var [budget,setBudget]=useState("");
  var [script,setScript]=useState("");
  var [sName,setSName]=useState("");
  var [locReqs,setLocReqs]=useState(null);
  var [pref,setPref]=useState([]);
  var [cInput,setCInput]=useState("");
  var [parsed,setParsed]=useState(null);
  var [intel,setIntel]=useState(null);
  var [openD,setOpenD]=useState({});
  var [qi,setQi]=useState(0);
  var [answers,setAnswers]=useState({});
  var [tIn,setTIn]=useState("");
  var [results,setResults]=useState(null);
  var [lStep,setLStep]=useState(0);
  var [cidx,setCidx]=useState(0);
  var [dragB,setDragB]=useState(false);
  var [dragS,setDragS]=useState(false);
  var [err,setErr]=useState(null);
  var [msgs,setMsgs]=useState([]);
  var [chatIn,setChatIn]=useState("");
  var [chatLd,setChatLd]=useState(false);
  var [openCards,setOpenCards]=useState({});
  var [library,setLibrary]=useState([]);
  var [showLib,setShowLib]=useState(false);
  var [libLoaded,setLibLoaded]=useState(false);
  var [overrideResults,setOverrideResults]=useState({});
  var [overridePending,setOverridePending]=useState(null);
  var [driveOpen,setDriveOpen]=useState(false);
  var [driveSearch,setDriveSearch]=useState("");
  var [driveFiles,setDriveFiles]=useState([]);
  var [driveLoading,setDriveLoading]=useState(false);
  var [driveTarget,setDriveTarget]=useState("budget");
  var [driveErr,setDriveErr]=useState(null);

  useEffect(function(){
    async function loadLib(){
      try{var r=await window.storage.get("frametax-library");if(r&&r.value)setLibrary(JSON.parse(r.value));}catch(e){}
      setLibLoaded(true);
    }
    loadLib();
  },[]);

  async function saveToLibrary(label){
    var entry={id:"ft-"+Date.now(),label:label||(parsed&&parsed.title)||"Untitled",savedAt:new Date().toLocaleDateString(),budgetText:budget,totalBudget:parsed&&parsed.totalBudget,answers,pref,results:results?{overallRecommendation:results.overallRecommendation,budgetOrigin:results.budgetOrigin,destinations:(results.destinations||[]).map(function(d){return{rank:d.rank,country:d.country,flag:d.flag,creditRate:d.creditRate,trueNetCost:d.trueNetCost,vsSavings:d.vsSavings};})}:null};
    var updated=[entry].concat(library.slice(0,19));
    setLibrary(updated);
    try{await window.storage.set("frametax-library",JSON.stringify(updated));}catch(e){}
  }

  async function deleteFromLibrary(id){
    var updated=library.filter(function(e){return e.id!==id;});
    setLibrary(updated);
    try{await window.storage.set("frametax-library",JSON.stringify(updated));}catch(e){}
  }

  function loadFromLibrary(entry){setBudget(entry.budgetText||"");setAnswers(entry.answers||{});setPref(entry.pref||[]);setShowLib(false);setPage("upload");}

  useEffect(function(){
    if(page==="qa"&&QUESTIONS[qi]&&QUESTIONS[qi].isText){
      var pre=getPreFill(QUESTIONS[qi].id);
      if(pre&&!answers[QUESTIONS[qi].id])setTIn(pre);
    }
  },[qi,page]);

  useEffect(function(){
    if(page!=="analyzing")return;
    var iv=setInterval(function(){setCidx(function(i){return(i+1)%COUNTRIES.length;});},800);
    return function(){clearInterval(iv);};
  },[page]);

  useEffect(function(){
    var el=document.createElement("script");
    el.src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
    el.onload=function(){if(window.pdfjsLib)window.pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";};
    document.head.appendChild(el);
  },[]);

  async function readPDF(file,maxPages){
    if(!maxPages)maxPages=30;
    var lib=window.pdfjsLib;
    if(!lib)throw new Error("PDF.js not ready");
    var pdf=await lib.getDocument({data:await file.arrayBuffer()}).promise;
    var txt="";
    for(var i=1;i<=Math.min(pdf.numPages,maxPages);i++){var pg=await pdf.getPage(i);var c=await pg.getTextContent();txt+=c.items.map(function(x){return x.str;}).join(" ")+"\n";}
    return txt;
  }

  async function loadBudget(file){
    if(!file)return;
    try{var txt=file.name.endsWith(".pdf")?await readPDF(file,30):await file.text();setBudget(txt.slice(0,12000));}
    catch(e){setErr("Could not read file: "+e.message);}
  }

  async function loadScript(file){
    if(!file)return;
    setSName(file.name);
    try{var txt=file.name.endsWith(".pdf")?await readPDF(file,60):await file.text();setScript(txt.slice(0,20000));}
    catch(e){setErr("Could not read script: "+e.message);}
  }

  async function searchDrive(q){
    setDriveLoading(true);setDriveErr(null);setDriveFiles([]);
    try{
      var body={model:"claude-sonnet-4-20250514",max_tokens:1000,messages:[{role:"user",content:"Search Google Drive for files matching: "+(q||"budget film production")+". List files that are PDFs spreadsheets or text documents. Return names IDs and file types."}],mcp_servers:[{type:"url",url:"https://gdrive.mcp.claude.com/mcp",name:"gdrive"}]};
      var res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      var data=await res.json();
      var files=[];
      (data.content||[]).forEach(function(block){
        if(block.type==="mcp_tool_result"){try{var t=JSON.parse((block.content&&block.content[0]&&block.content[0].text)||"{}");if(Array.isArray(t))files=t;else if(t.files)files=t.files;}catch(e){}}
        if(block.type==="text"&&files.length===0){var lines=block.text.split("\n");lines.forEach(function(line){var id=line.match(/\b([a-zA-Z0-9_-]{25,})\b/);var nm=line.match(/\*\*(.+?)\*\*/)||line.match(/^\d+\.\s+(.+?)(?:\s+-|\s+\(|$)/);if(id&&nm)files.push({id:id[1],name:nm[1].trim(),mimeType:""});});}
      });
      setDriveFiles(files);
    }catch(e){setDriveErr("Drive search failed: "+e.message);}
    finally{setDriveLoading(false);}
  }

  async function fetchDriveFile(fileId,fileName){
    setDriveLoading(true);setDriveErr(null);
    try{
      var body={model:"claude-sonnet-4-20250514",max_tokens:4000,messages:[{role:"user",content:"Fetch the full text content of Google Drive file ID: "+fileId+" (filename: "+fileName+"). Return the raw text content."}],mcp_servers:[{type:"url",url:"https://gdrive.mcp.claude.com/mcp",name:"gdrive"}]};
      var res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      var data=await res.json();
      var content="";
      (data.content||[]).forEach(function(block){if(block.type==="mcp_tool_result")content+=(block.content&&block.content[0]&&block.content[0].text)||"";if(block.type==="text"&&!content)content+=block.text;});
      if(!content.trim())throw new Error("No content returned");
      if(driveTarget==="budget")setBudget(content.slice(0,12000));
      else{setScript(content.slice(0,20000));setSName(fileName);}
      setDriveOpen(false);
    }catch(e){setDriveErr("Could not read file: "+e.message);}
    finally{setDriveLoading(false);}
  }

  async function parseBudget(){
    if(!budget.trim()){setErr("Please upload or paste your budget first.");return;}
    setErr(null);setPage("parsing");
    try{
      var prompt="Film budget analyst. Extract all line items AND production intel.\nOutput ONLY valid JSON no markdown no backticks. Start with { end with }.\nSchema: {\"title\":\"string\",\"totalBudget\":10000000,\"director\":null,\"directorNationality\":null,\"budgetOriginCity\":\"Los Angeles\",\"budgetOriginRateBase\":\"US union rates IATSE\",\"hasFinanceCosts\":true,\"financeAmount\":85000,\"hasInsurance\":true,\"insuranceAmount\":180000,\"hasCompletionBond\":true,\"completionBondAmount\":120000,\"departments\":[{\"name\":\"Above the Line\",\"total\":3200000,\"items\":[{\"description\":\"Producer Fee\",\"amount\":400000,\"isFixed\":true}]}]}\nisFixed=true for ATL talent/rights. isFixed=false for BTL crew/equipment/locations.\nBUDGET:\n"+budget;
      var raw=await callClaude([{role:"user",content:prompt}],false,4000);
      var d=parseJSON(raw);
      setIntel({director:d.director||null,directorNationality:d.directorNationality||null,writer:d.writer||null,writerNationality:d.writerNationality||null,originCity:d.budgetOriginCity||"Unknown",rateBase:d.budgetOriginRateBase||"Unknown",hasFinance:!!d.hasFinanceCosts,financeAmt:d.financeAmount||0,hasInsurance:!!d.hasInsurance,insuranceAmt:d.insuranceAmount||0,hasBond:!!d.hasCompletionBond,bondAmt:d.completionBondAmount||0,shootDays:d.shootDays||null,shootStartDate:d.shootStartDate||null});
      var first={};if(d.departments&&d.departments[0])first[d.departments[0].name]=true;
      setOpenD(first);setParsed(d);setPage("review");
    }catch(e){setErr("Parse error: "+e.message);setPage("upload");}
  }

  async function analyze(){
    setPage("analyzing");setLStep(0);setErr(null);
    var lr=locReqs;
    if(script&&!lr){
      try{
        var p2="Analyze this script. Output ONLY valid JSON no markdown no backticks. Start with { end with }.\nSchema: {\"writerName\":null,\"writerNationality\":null,\"environments\":[],\"climateNeeds\":[],\"specificLocations\":[],\"wouldNotWorkIn\":[]}\nSCRIPT:\n"+script.slice(0,15000);
        var r2=await callClaude([{role:"user",content:p2}],false,4000);
        lr=parseJSON(r2);setLocReqs(lr);
      }catch(e){lr=null;}
    }
    setLStep(1);
    var imd=null;
    try{
      var title=(parsed&&parsed.title)?parsed.title:"Untitled";
      var dirPart=(intel&&intel.director)?" directed by "+intel.director:"";
      var p3="Search IMDb for attachments to film \""+title+"\""+dirPart+".\nOutput ONLY valid JSON no markdown no backticks. Start with { end with }.\nSchema: {\"found\":false,\"directorName\":null,\"directorNationality\":null,\"castAttachments\":[]}";
      var r3=await callClaude([{role:"user",content:p3}],true,4000);
      imd=parseJSON(r3);
    }catch(e){imd=null;}
    setLStep(2);
    var ci=intel||{};
    var dirName=(imd&&imd.directorName)||ci.director||"Unknown";
    var dirNat=(imd&&imd.directorNationality)||ci.directorNationality||(answers&&answers.dirNat)||"Unknown";
    var wNat=(lr&&lr.writerNationality)||ci.writerNationality||"Unknown";
    var castParts=(imd&&imd.castAttachments&&imd.castAttachments.length>0)?imd.castAttachments.map(function(c){return c.name+"("+c.nationality+")";}):[];
    var cast=castParts.length>0?castParts.join(", "):((answers&&answers.castNat)||"Unknown");
    var origin=ci.originCity||"Los Angeles";
    var rateBase=ci.rateBase||"US union rates";
    var total=(parsed&&parsed.totalBudget)||0;
    var depts=(parsed&&parsed.departments)||[];
    var vBTL=depts.filter(function(d){return!/above|post/i.test(d.name);}).reduce(function(s,d){return s+(d.total||0);},0);
    var fATL=depts.filter(function(d){return/above/i.test(d.name);}).reduce(function(s,d){return s+(d.total||0);},0);
    var qaText=QUESTIONS.map(function(q){return q.label+": "+((answers&&answers[q.id])||"Not provided");}).join("\n");
    var prefNote=pref.length>0?"\nPREFERRED: "+pref.join(", ")+" - always include, honest verdict.":"";
    var sNote=lr?"\nSCRIPT REQS: environments: "+((lr.environments||[]).join(",")||"flexible")+", climate: "+((lr.climateNeeds||[]).join(",")||"flexible"):"";
    var finNote=ci.hasFinance?"IN budget "+fmt(ci.financeAmt):"NOT in budget";
    var insNote=ci.hasInsurance?"IN budget "+fmt(ci.insuranceAmt):"NOT in budget";
    setLStep(3);
    try{
      var prompt="World-leading film production finance expert.\n\nINTEL: Film=\""+((parsed&&parsed.title)||"Untitled")+"\" | Total="+fmt(total)+" | Origin="+origin+" | RateBase="+rateBase+"\nFixedATL="+fmt(fATL)+" (do NOT adjust) | VariableBTL="+fmt(vBTL)+" (MUST rebase to local rates)\nFinance="+finNote+" | Insurance="+insNote+"\nDirector="+dirName+" ("+dirNat+") | Writer nat.="+wNat+" | Cast="+cast+"\n\nQ&A:\n"+qaText+prefNote+sNote+"\n\nTASK 1: Analyze the HOME BASE ("+origin+"). What incentives exist in the home country? True net cost if filming at home?\nTASK 2: Analyze top 5 international filming destinations. Rebase BTL, apply live FX, calculate credits, add travel.\nOutput ONLY valid JSON no markdown no backticks. Start with { end with }.\nTop-level: homeCurrency,budgetOrigin,budgetRateBase,variableBTLBase,fixedATLBase,directorIntel{name,nationality,imdbFound},writerIntel{nationality},financeFlagged,insuranceFlagged,overallRecommendation,travelNote,currencyNote,homeBase{country,flag,incentiveProgram,creditRate,estimatedCredit,trueNetCost,notes,noIncentiveReason},destinations[].\nPer dest: rank,country,flag,incentiveProgram,creditRate,estimatedCredit,baseRateMultiplier,localCostUSD,travelCost,trueNetCost,vsSavings,vsPercent,exchangeRate,currencyRisk,rateAdjustmentNote,qualifications[]{test,status,detail},atLStatus,insuranceStatus,financeStatus,coproOpportunity,qualGap,structuringTip,locationFit,highlights[].\nMax 4 quals and 3 highlights per dest. Strings under 120 chars.";
      setLStep(4);
      var raw=await callClaude([{role:"user",content:prompt}],true,8000);
      var data=parseJSON(raw);
      if(pref.length>0&&data.destinations){data.destinations=data.destinations.map(function(d){return Object.assign({},d,{isPreferred:pref.some(function(p){return d.country.toLowerCase().includes(p.toLowerCase())||p.toLowerCase().includes(d.country.toLowerCase());})});});}
      var topDests=(data.destinations||[]).slice(0,5).map(function(d){return d.country+" ("+d.creditRate+")";}).join(", ");
      var tPrompt="Expert film finance and treaty consultant. Analyze co-production treaty strategies and incentive stacking.\nBudget origin: "+origin+" | Total: "+fmt(total)+" | Director: "+dirName+" ("+dirNat+") | Writer: "+wNat+"\nTop destinations: "+topDests+"\nOutput ONLY valid JSON no markdown no backticks. Start with { end with }.\nSchema: {\"maxAchievableRate\":\"up to 43% combined\",\"maxAchievableAmount\":5000000,\"baselineAmount\":1200000,\"incrementalUplift\":3800000,\"executiveSummary\":\"string\",\"strategies\":[{\"title\":\"string\",\"type\":\"treaty|stacking|structuring|split_shoot|service_model\",\"incentiveUplift\":\"string\",\"estimatedValue\":800000,\"complexity\":\"low|medium|high\",\"timeToImplement\":\"string\",\"description\":\"string\",\"requirements\":[],\"risks\":[],\"bestPairedWith\":\"string\"}],\"treatyMap\":[{\"country1\":\"UK\",\"country2\":\"Canada\",\"treatyType\":\"string\",\"keyBenefit\":\"string\"}],\"stackingOpportunities\":[{\"country\":\"UK\",\"layers\":[{\"name\":\"string\",\"rate\":\"string\"}],\"combinedRate\":\"string\",\"conditions\":\"string\"}],\"quickWins\":[{\"action\":\"string\",\"timeframe\":\"string\",\"value\":\"string\"}],\"warnings\":[]}";
      var tRaw=await callClaude([{role:"user",content:tPrompt}],true,5000);
      try{data.treatyOptimizer=parseJSON(tRaw);}catch(e){data.treatyOptimizer={executiveSummary:"Treaty analysis had a formatting issue. Use the follow-up chat to ask specific treaty questions.",strategies:[],warnings:[]};}
      var openInit={};if(data.destinations&&data.destinations[0])openInit[0]=true;
      setOpenCards(openInit);setResults(data);setPage("results");
    }catch(e){setErr("Analysis failed: "+e.message);setPage("qa");}
  }

  async function runOverrideAnalysis(destIndex,dest){
    var key="dest_"+destIndex;
    setOverridePending(key);
    try{
      var total=(parsed&&parsed.totalBudget)||0;
      var depts=(parsed&&parsed.departments)||[];
      var ci=intel||{};
      var failedQuals=(dest.qualifications||[]).filter(function(q){return q.status==="fail"||q.status==="partial";}).map(function(q){return q.test+": "+q.detail;}).join("; ");
      var prompt="Expert film finance accountant. SCENARIO: Assume this production FULLY QUALIFIES for all incentives in "+dest.country+" - "+dest.incentiveProgram+".\nFailed quals (assume overcome): "+(failedQuals||"none")+"\nTotal Budget: "+fmt(total)+" | Origin: "+(ci.originCity||"Los Angeles")+" | Rate base: "+(ci.rateBase||"US union rates")+"\nPrevious credit rate: "+dest.creditRate+" | Previous estimated credit: "+fmt(dest.estimatedCredit)+" | Previous net: "+fmt(dest.trueNetCost)+"\nOutput ONLY valid JSON no markdown no backticks. Start with { end with }.\nSchema: {\"assumedCreditRate\":\"25%\",\"qualifyingSpend\":8000000,\"totalCreditOverride\":2000000,\"rebasedBTL\":4500000,\"localCostTotal\":7500000,\"travelCost\":180000,\"trueNetCostOverride\":5680000,\"savingsVsHome\":2320000,\"savingsVsPrevious\":850000,\"methodology\":[{\"step\":1,\"label\":\"string\",\"calculation\":\"string\",\"result\":4464000,\"notes\":\"string\"}],\"structuringSteps\":[{\"action\":\"string\",\"timeframe\":\"string\",\"cost\":\"string\",\"critical\":true}],\"assumedQualifications\":[{\"test\":\"string\",\"howToPass\":\"string\",\"difficulty\":\"low|medium|high\"}],\"caveats\":[],\"executiveSummary\":\"string\"}";
      var raw=await callClaude([{role:"user",content:prompt}],true,5000);
      var data=parseJSON(raw);
      setOverrideResults(function(prev){var n=Object.assign({},prev);n[key]=data;return n;});
    }catch(e){setOverrideResults(function(prev){var n=Object.assign({},prev);n[key]={error:"Override analysis failed: "+e.message};return n;});}
    finally{setOverridePending(null);}
  }

  function getPreFill(qid){
    if(!intel)return "";
    if(qid==="duration")return intel.shootDays?(intel.shootDays+" days"):"";
    if(qid==="shootDate")return intel.shootStartDate||"";
    if(qid==="dirNat")return intel.directorNationality||"";
    return "";
  }

  function answerQ(val){
    var q=QUESTIONS[qi];
    setAnswers(function(prev){return Object.assign({},prev,{[q.id]:val});});
    if(qi<QUESTIONS.length-1){
      var nextQ=QUESTIONS[qi+1];
      var pre=getPreFill(nextQ.id);
      setQi(qi+1);setTIn(pre);
    } else analyze();
  }

  async function sendChat(msg){
    if(!msg||!msg.trim()||chatLd)return;
    setMsgs(function(p){return p.concat([{role:"user",text:msg}]);});
    setChatIn("");setChatLd(true);
    try{
      var destSum=(results&&results.destinations||[]).map(function(d){return d.country+" net:"+fmt(d.trueNetCost)+" credit:"+d.creditRate;}).join(" | ");
      var ctx="Film finance expert. Film: "+((parsed&&parsed.title)||"Feature")+". Budget: "+fmt(parsed&&parsed.totalBudget)+". Destinations: "+destSum;
      var hist=msgs.slice(-6).map(function(m){return{role:m.role==="user"?"user":"assistant",content:m.text};});
      var allMsgs=[{role:"user",content:ctx},{role:"assistant",content:"Context loaded."}].concat(hist).concat([{role:"user",content:msg}]);
      var reply=await callClaude(allMsgs,true,1000);
      setMsgs(function(p){return p.concat([{role:"assistant",text:reply}]);});
    }catch(e){setMsgs(function(p){return p.concat([{role:"assistant",text:"Sorry, could not process that."}]);});}
    finally{setChatLd(false);setTimeout(function(){if(chatEnd.current)chatEnd.current.scrollIntoView({behavior:"smooth"});},100);}
  }

  function reset(){setPage("hero");setParsed(null);setResults(null);setAnswers({});setQi(0);setBudget("");setScript("");setSName("");setLocReqs(null);setPref([]);setIntel(null);setMsgs([]);setErr(null);setOpenCards({});}

  var fixedTot=(parsed&&parsed.departments)?parsed.departments.reduce(function(s,d){return s+d.items.filter(function(i){return i.isFixed;}).reduce(function(ss,ii){return ss+(ii.amount||0);},0);},0):0;
  var varTot=(parsed&&parsed.departments)?parsed.departments.reduce(function(s,d){return s+d.items.filter(function(i){return!i.isFixed;}).reduce(function(ss,ii){return ss+(ii.amount||0);},0);},0):0;
  var navSteps=["upload","review","qa","results"];

  return(
    <div style={{fontFamily:JO,minHeight:"100vh",background:BG,color:CR,overflowX:"hidden"}}>
      <style>{CSS}</style>
      <div style={{position:"fixed",width:600,height:600,borderRadius:"50%",background:G,top:-200,right:-200,filter:"blur(120px)",opacity:.07,pointerEvents:"none"}} />

      <DrivePicker open={driveOpen} onClose={function(){setDriveOpen(false);setDriveErr(null);setDriveFiles([]);}} onSearch={searchDrive} onSelect={fetchDriveFile} files={driveFiles} loading={driveLoading} err={driveErr} target={driveTarget} />

      {showLib&&(
        <div style={Object.assign({},S.fix,{top:0,right:0,width:380,height:"100vh",background:"#0C0C0C",borderLeft:"1px solid "+BD,zIndex:200,display:"flex",flexDirection:"column",boxShadow:"-8px 0 32px rgba(0,0,0,.6)"})}>
          <div style={Object.assign({},S.sb,S.pad(".9rem","1.25rem"),{borderBottom:"1px solid "+BD})}>
            <div><div style={S.serif("1.3rem")}>Project Library</div><div style={S.mono(DM,".7rem")}>Saved budgets and analyses</div></div>
            <button onClick={function(){setShowLib(false);}} style={{background:"transparent",border:"none",color:DM,cursor:"pointer",fontSize:"1.2rem"}}>x</button>
          </div>
          <div style={{flex:1,overflowY:"auto",padding:".85rem"}}>
            {!libLoaded&&<div style={{textAlign:"center",padding:"2rem",fontFamily:MO,color:DM,fontSize:".76rem"}}>Loading...</div>}
            {libLoaded&&library.length===0&&<div style={{textAlign:"center",padding:"3rem 1.5rem",fontFamily:MO,fontSize:".76rem",color:DM,lineHeight:1.8}}>No saved projects yet. Run an analysis and click Save to Library.</div>}
            {libLoaded&&library.map(function(entry){
              return(
                <div key={entry.id} style={S.card()}>
                  <div style={{padding:".75rem .9rem",background:"#111"}}>
                    <div style={Object.assign({},S.sb,{marginBottom:".35rem"})}><div style={S.serif("1rem")}>{entry.label}</div><button onClick={function(){deleteFromLibrary(entry.id);}} style={{background:"transparent",border:"none",color:DM,cursor:"pointer",fontSize:".72rem",fontFamily:MO}}>delete</button></div>
                    <div style={S.mono(DM,".67rem")}>{entry.savedAt+(entry.totalBudget?"  "+fmt(entry.totalBudget):"")}</div>
                    {entry.results&&entry.results.destinations&&(
                      <div style={{margin:".5rem 0"}}>
                        {entry.results.destinations.slice(0,3).map(function(d){return <div key={d.rank} style={Object.assign({},S.sb,{padding:".25rem 0",borderBottom:"1px solid #1A1A1A",fontSize:".74rem"})}><span style={{color:CR}}>{d.flag+" "+d.country}</span><span style={S.mono(G,".72rem")}>{d.creditRate}</span></div>;})}
                      </div>
                    )}
                    <button onClick={function(){loadFromLibrary(entry);}} style={{background:"rgba(201,168,76,.1)",border:"1px solid rgba(201,168,76,.3)",color:G,fontFamily:MO,fontSize:".7rem",padding:".38rem .8rem",cursor:"pointer",width:"100%",marginTop:".5rem"}}>Load + Re-run Analysis</button>
                  </div>
                </div>
              );
            })}
          </div>
          {page==="results"&&results&&<div style={{padding:".9rem",borderTop:"1px solid "+BD}}><SavePrompt onSave={saveToLibrary} defaultLabel={(parsed&&parsed.title)||"Untitled"} /></div>}
          {page!=="results"&&budget&&<div style={{padding:".9rem",borderTop:"1px solid "+BD}}><button onClick={function(){saveToLibrary((parsed&&parsed.title)||"Budget - "+new Date().toLocaleDateString());setShowLib(false);}} style={{background:G,color:BG,border:"none",fontFamily:JO,fontSize:".8rem",fontWeight:700,padding:".7rem 1.25rem",cursor:"pointer",width:"100%",textTransform:"uppercase",letterSpacing:".08em"}}>Save Budget to Library</button></div>}
        </div>
      )}
      {showLib&&<div onClick={function(){setShowLib(false);}} style={Object.assign({},S.fix,{inset:0,zIndex:199,background:"rgba(0,0,0,.4)"})} />}

      {page!=="hero"&&(
        <nav style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"1rem 2rem",borderBottom:"1px solid "+BD,position:"sticky",top:0,background:"rgba(8,8,8,.95)",backdropFilter:"blur(10px)",zIndex:100}}>
          <span style={Object.assign({},S.serif("1.2rem"),{letterSpacing:".08em",cursor:"pointer"})} onClick={reset}>FRAME<span style={{color:G}}>TAX</span></span>
          <div style={{display:"flex",gap:4}}>
            {navSteps.map(function(s,i){var idx=navSteps.indexOf(page);return <div key={s} style={{width:40,height:3,background:i<idx?"#5A4A20":i===idx?G:BD,transition:"background .3s"}} />;} )}
          </div>
          <div style={Object.assign({},S.row,{gap:".5rem"})}>
            <button onClick={function(){setShowLib(function(v){return!v;});}} style={{background:"transparent",color:showLib?G:DM,fontFamily:MO,fontSize:".73rem",padding:".38rem .8rem",border:"1px solid "+(showLib?G:BD),cursor:"pointer"}}>{"Library"+(library.length>0?" ("+library.length+")":"")}</button>
            <button onClick={reset} style={{background:"transparent",color:DM,fontFamily:MO,fontSize:".73rem",padding:".38rem .8rem",border:"none",cursor:"pointer"}}>Start over</button>
          </div>
        </nav>
      )}

      {page==="hero"&&(
        <div style={{minHeight:"100vh",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:"3rem 2rem",textAlign:"center"}}>
          <div style={Object.assign({},S.eyebrow,{marginBottom:"2rem"})}>Film Production Finance Intelligence</div>
          <h1 style={Object.assign({},S.serif("clamp(2.8rem,7vw,5rem)",300),{lineHeight:1.05,color:CR,marginBottom:"1.5rem"})}>Where in the world<br/>should you <em style={{color:G,fontStyle:"italic"}}>film</em>?</h1>
          <p style={{maxWidth:520,fontSize:"1rem",fontWeight:300,color:DM,lineHeight:1.7,marginBottom:"3rem"}}>Upload your budget. Our AI scans 100+ global tax incentive programs, rebases BTL costs to local rates, checks IMDb for attachments, and applies live FX to find exactly where your money goes furthest.</p>
          <div style={{display:"flex",gap:"2.5rem",borderTop:"1px solid "+BD,borderBottom:"1px solid "+BD,padding:"1.5rem 2.5rem",marginBottom:"3rem",flexWrap:"wrap",justifyContent:"center"}}>
            {[["100+","Jurisdictions"],["Live","FX Rates"],["IMDb","Attachments"],["Full","Cost Rebase"]].map(function(pair){
              return <div key={pair[1]} style={{textAlign:"center"}}><div style={Object.assign({},S.serif("1.8rem",600),{color:G})}>{pair[0]}</div><div style={Object.assign({},S.mono(DM,".68rem"),{letterSpacing:".12em",textTransform:"uppercase",marginTop:".2rem"})}>{pair[1]}</div></div>;
            })}
          </div>
          <Btn gold onClick={function(){setPage("upload");}}>Upload Your Budget</Btn>
          <p style={Object.assign({},S.mono(DM,".73rem"),{marginTop:"1.5rem"})}>PDF  Movie Magic  CSV  Paste text</p>
          {library.length>0&&<button onClick={function(){setPage("upload");setShowLib(true);}} style={{marginTop:"1.5rem",background:"transparent",border:"1px solid "+BD,color:DM,fontFamily:MO,fontSize:".73rem",padding:".45rem 1.1rem",cursor:"pointer"}}>{"Open Library ("+library.length+" saved project"+(library.length!==1?"s":"")+")"}</button>}
        </div>
      )}

      {page==="upload"&&(
        <div className="sc fu">
          <Eyebrow>Step 1 of 4</Eyebrow>
          <h2 style={Object.assign({},S.serif("2.5rem",300),{color:CR,marginBottom:".5rem"})}>Upload your budget</h2>
          <p style={{fontSize:".88rem",color:DM,marginBottom:"2rem",lineHeight:1.6}}>PDF, Movie Magic, CSV, or paste text below. Optionally add your script for location analysis.</p>
          <ErrBox msg={err} />
          <div onDragOver={function(e){e.preventDefault();setDragB(true);}} onDragLeave={function(){setDragB(false);}} onDrop={function(e){e.preventDefault();setDragB(false);loadBudget(e.dataTransfer.files[0]);}} onClick={function(){if(fileRef.current)fileRef.current.click();}}
            style={{border:"1px dashed "+(dragB?G:budget?"#3A5A3A":BD),padding:"3rem 2rem",textAlign:"center",cursor:"pointer",background:budget?"rgba(90,154,90,.04)":"transparent",marginBottom:"1rem",transition:"all .3s"}}>
            <input ref={fileRef} type="file" accept=".pdf,.csv,.txt,.mbb" style={{display:"none"}} onChange={function(e){loadBudget(e.target.files[0]);}} />
            <div style={{fontSize:"2rem",marginBottom:".65rem"}}>{budget?"OK":"+"}</div>
            <div style={{color:budget?"#5A9A5A":CR,marginBottom:".3rem"}}>{budget?"Budget loaded - ready to analyze":"Drop your budget file here"}</div>
            <div style={S.mono(DM,".78rem")}>.pdf  .csv  .mbb  .txt  or click to browse</div>
          </div>
          <div style={{textAlign:"center",marginBottom:"1.25rem"}}>
            <button onClick={function(){setDriveTarget("budget");setDriveOpen(true);setDriveFiles([]);setDriveErr(null);}} style={{background:"transparent",border:"1px solid "+BD,color:DM,fontFamily:MO,fontSize:".73rem",padding:".45rem 1rem",cursor:"pointer"}}>Drive Browse Google Drive for Budget</button>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:"1rem",margin:"1.25rem 0",color:DM,fontSize:".73rem",fontFamily:MO}}>
            <div style={{flex:1,height:1,background:BD}} /><span>or paste budget text</span><div style={{flex:1,height:1,background:BD}} />
          </div>
          <textarea value={budget} onChange={function(e){setBudget(e.target.value);}} placeholder={"Paste budget text here...\n\nAbove the Line\n  Director Fee    $750,000\n\nProduction\n  DP / Camera     $280,000\n\nTotal: $10,000,000"} style={{width:"100%",background:"#0E0E0E",border:"1px solid "+BD,color:CR,fontFamily:MO,fontSize:".76rem",lineHeight:1.7,padding:"1.1rem",resize:"vertical",minHeight:150,outline:"none"}} />
          <div style={{marginTop:"1.75rem"}}>
            <Eyebrow>Optional: Script or Treatment</Eyebrow>
            <p style={{fontSize:".82rem",color:DM,marginBottom:".65rem",lineHeight:1.6}}>Scans for location requirements and writer nationality to filter destinations.</p>
            <div onDragOver={function(e){e.preventDefault();setDragS(true);}} onDragLeave={function(){setDragS(false);}} onDrop={function(e){e.preventDefault();setDragS(false);loadScript(e.dataTransfer.files[0]);}} onClick={function(){if(scriptRef.current)scriptRef.current.click();}}
              style={{border:"1px dashed "+(script?"#3A5A3A":dragS?G:"#3A3020"),padding:"1.25rem 2rem",textAlign:"center",cursor:"pointer",background:script?"rgba(90,154,90,.04)":"rgba(201,168,76,.02)",transition:"all .3s",marginBottom:".6rem"}}>
              <input ref={scriptRef} type="file" accept=".pdf,.fdx,.txt,.fountain" style={{display:"none"}} onChange={function(e){loadScript(e.target.files[0]);}} />
              {script?<div><div>OK</div><div style={{color:"#5A9A5A",marginTop:".25rem"}}>{"Script: "+sName}</div></div>:<div><div>+</div><div style={{color:CR,marginTop:".25rem"}}>Drop script here</div><div style={S.mono(DM,".7rem")}>.pdf  .fdx  .fountain  .txt</div></div>}
            </div>
            <div style={{textAlign:"center",marginBottom:".5rem"}}>
              <button onClick={function(){setDriveTarget("script");setDriveOpen(true);setDriveFiles([]);setDriveErr(null);}} style={{background:"transparent",border:"1px solid "+BD,color:DM,fontFamily:MO,fontSize:".7rem",padding:".38rem .85rem",cursor:"pointer"}}>Drive Browse Google Drive for Script</button>
            </div>
            {script&&<button onClick={function(){setScript("");setSName("");setLocReqs(null);}} style={{background:"transparent",border:"none",color:DM,fontFamily:MO,fontSize:".72rem",cursor:"pointer"}}>Remove script</button>}
          </div>
          <div style={Object.assign({},S.row,{gap:"1rem",marginTop:"2rem",justifyContent:"flex-end"})}>
            <Btn onClick={function(){setPage("hero");}}>Back</Btn>
            <Btn gold onClick={parseBudget} disabled={!budget.trim()}>{budget.trim()?"Analyze Budget":"Upload Budget First"}</Btn>
          </div>
        </div>
      )}

      {page==="parsing"&&(
        <div className="ld">
          <div className="ring" />
          <h2 style={Object.assign({},S.serif("1.8rem"),{color:CR,textAlign:"center"})}>Reading your budget</h2>
          <p style={S.mono(G,".78rem")}>Extracting line items and production intel...</p>
        </div>
      )}

      {page==="review"&&parsed&&(
        <div className="sc fu">
          <Eyebrow>Step 2 of 4</Eyebrow>
          <h2 style={Object.assign({},S.serif("2.5rem",300),{color:CR,marginBottom:".5rem"})}>{parsed.title||"Your Budget"}</h2>
          <p style={{fontSize:".88rem",color:DM,marginBottom:"2rem",lineHeight:1.6}}>Review parsed budget. Variable BTL costs will be rebased to local rates per destination.</p>
          <div style={{display:"flex",gap:"2rem",padding:"1.1rem 1.25rem",border:"1px solid "+BD,marginBottom:"2rem",background:"#0A0A0A",flexWrap:"wrap"}}>
            {[["Total Budget",fmt(parsed.totalBudget),true],["Fixed ATL",fmt(fixedTot),false],["Variable BTL",fmt(varTot),false],["Departments",(parsed.departments&&parsed.departments.length)||0,false]].map(function(item){
              return <div key={item[0]} style={{flex:1,minWidth:100}}><div style={S.label}>{item[0]}</div><div style={Object.assign({},S.serif("1.6rem"),{color:item[2]?G:CR})}>{item[1]}</div></div>;
            })}
          </div>
          {intel&&(
            <div style={Object.assign({},S.card(),{marginBottom:"1.5rem"})}>
              <div style={{background:"#0C0C0C",padding:".65rem 1.1rem",borderBottom:"1px solid "+BD}}><span style={S.mono(G,".68rem")}>Budget Intelligence Extracted</span></div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))"}}>
                {[["Budget Origin",intel.originCity,intel.originCity!=="Unknown"],["Rate Base",intel.rateBase,true],["Director",intel.director||"Not found",!!intel.director],["Dir. Nationality",intel.directorNationality||"Will research",!!intel.directorNationality],["Finance",intel.hasFinance?"Yes "+fmt(intel.financeAmt):"Not in budget",intel.hasFinance],["Insurance",intel.hasInsurance?"Yes "+fmt(intel.insuranceAmt):"Not in budget",intel.hasInsurance]].map(function(item){
                  return <div key={item[0]} style={{padding:".6rem .9rem",borderRight:"1px solid "+BD,borderBottom:"1px solid "+BD}}><div style={S.label}>{item[0]}</div><div style={S.mono(item[2]?CR:"#C97A1C",".8rem")}>{item[1]}</div></div>;
                })}
              </div>
            </div>
          )}
          {parsed.departments&&parsed.departments.map(function(dept){
            return(
              <div key={dept.name} style={Object.assign({},S.card(),{marginBottom:".65rem"})}>
                <div onClick={function(){setOpenD(function(p){var n=Object.assign({},p);n[dept.name]=!p[dept.name];return n;});}} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:".8rem 1.1rem",background:"#0E0E0E",cursor:"pointer",fontSize:".8rem",fontWeight:500,letterSpacing:".06em",textTransform:"uppercase"}}>
                  <span>{dept.name}</span><span style={S.mono(G,".8rem")}>{fmt(dept.total)+" "+(openD[dept.name]?"^":"v")}</span>
                </div>
                {openD[dept.name]&&dept.items&&dept.items.map(function(item,i){
                  return <div key={i} style={{display:"grid",gridTemplateColumns:"1fr auto auto",gap:"1rem",padding:".45rem 1.1rem",fontSize:".8rem",borderBottom:"1px solid #141414",alignItems:"center"}}><span style={{color:DM}}>{item.description}</span><span style={{fontSize:".6rem",padding:".18rem .45rem",fontFamily:MO,background:item.isFixed?"#1A2A1A":"#2A1A0A",color:item.isFixed?"#5A9A5A":"#C9801C"}}>{item.isFixed?"FIXED":"VARIABLE"}</span><span style={S.mono(CR,".8rem")}>{fmt(item.amount)}</span></div>;
                })}
              </div>
            );
          })}
          <div style={{marginTop:"1.75rem",borderTop:"1px solid "+BD,paddingTop:"1.5rem"}}>
            <Eyebrow>Preferred Countries (Optional)</Eyebrow>
            <p style={{fontSize:".82rem",color:DM,marginBottom:".85rem",lineHeight:1.6}}>Request specific countries - included with an honest financial verdict.</p>
            {pref.length>0&&<div style={Object.assign({},S.wrap,{gap:".45rem",marginBottom:".65rem"})}>{pref.map(function(c){return <div key={c} onClick={function(){setPref(function(p){return p.filter(function(x){return x!==c;});});}} style={{display:"flex",alignItems:"center",gap:".35rem",background:"rgba(201,168,76,.12)",border:"1px solid rgba(201,168,76,.3)",color:G,fontSize:".74rem",padding:".28rem .7rem",fontFamily:MO,cursor:"pointer"}}>{c} <span style={{opacity:.6}}>x</span></div>;})}</div>}
            <div style={{position:"relative",marginBottom:".65rem"}}>
              <input value={cInput} onChange={function(e){setCInput(e.target.value);}} onKeyDown={function(e){
                if(e.key==="Enter"&&cInput.trim()){
                  var exact=ALL_COUNTRIES.find(function(c){return c.toLowerCase()===cInput.trim().toLowerCase();});
                  var toAdd=exact||cInput.trim();
                  if(!pref.includes(toAdd))setPref(function(p){return p.concat([toAdd]);});
                  setCInput("");
                }
                if(e.key==="Escape")setCInput("");
              }} placeholder="Type a country name..." style={{width:"100%",background:"#0E0E0E",border:"1px solid "+BD,color:CR,fontFamily:JO,fontSize:".88rem",padding:".65rem .9rem",outline:"none"}} />
              {cInput.trim().length>=1&&(function(){
                var matches=ALL_COUNTRIES.filter(function(c){return c.toLowerCase().startsWith(cInput.toLowerCase())&&!pref.includes(c);});
                if(!matches.length)matches=ALL_COUNTRIES.filter(function(c){return c.toLowerCase().includes(cInput.toLowerCase())&&!pref.includes(c);});
                matches=matches.slice(0,7);
                if(!matches.length)return null;
                return <div style={{position:"absolute",top:"100%",left:0,right:0,background:"#111",border:"1px solid "+BD,borderTop:"none",zIndex:50,maxHeight:240,overflowY:"auto",boxShadow:"0 8px 24px rgba(0,0,0,.6)"}}>
                  {matches.map(function(c){
                    var idx=c.toLowerCase().indexOf(cInput.toLowerCase());
                    var before=c.slice(0,idx);
                    var match=c.slice(idx,idx+cInput.length);
                    var after=c.slice(idx+cInput.length);
                    return <div key={c} onClick={function(){if(!pref.includes(c))setPref(function(p){return p.concat([c]);});setCInput("");}} style={{padding:".6rem .9rem",cursor:"pointer",fontSize:".86rem",color:CR,borderBottom:"1px solid #1A1A1A",background:"#111"}}>
                      {before}<span style={{color:G,fontWeight:600}}>{match}</span>{after}
                    </div>;
                  })}
                </div>;
              })()}
            </div>
            <div style={Object.assign({},S.wrap,{gap:".35rem"})}>
              {SUGGEST_COUNTRIES.filter(function(c){return!pref.includes(c);}).map(function(c){return <button key={c} onClick={function(){setPref(function(p){return p.concat([c]);});}} style={{background:"transparent",border:"1px solid "+BD,color:DM,fontSize:".7rem",padding:".22rem .55rem",cursor:"pointer",fontFamily:MO}}>{"+ "+c}</button>;})}
            </div>
          </div>
          <div style={Object.assign({},S.row,{gap:"1rem",marginTop:"2rem",justifyContent:"flex-end"})}>
            <Btn onClick={function(){setPage("upload");}}>Re-upload</Btn>
            <Btn gold onClick={function(){setPage("qa");}}>Continue</Btn>
          </div>
        </div>
      )}

      {page==="qa"&&(
        <div className="sc680 fu">
          <Eyebrow>Step 3 of 4 - Production Details</Eyebrow>
          <div style={Object.assign({},S.row,{gap:4,marginBottom:"2.5rem"})}>
            {QUESTIONS.map(function(_,i){return <div key={i} style={{flex:1,height:3,background:i<qi?G:i===qi?CR:BD,transition:"background .3s"}} />;} )}
          </div>
          <ErrBox msg={err} />
          <div style={S.mono(G,".68rem")}>{"Question "+(qi+1)+" of "+QUESTIONS.length}</div>
          <h2 style={Object.assign({},S.serif("1.8rem",300),{lineHeight:1.3,color:CR,marginBottom:"1.75rem",marginTop:".4rem"})}>{QUESTIONS[qi].label}</h2>
          {QUESTIONS[qi].options?(
            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))",gap:".65rem",marginBottom:"1.75rem"}}>
              {QUESTIONS[qi].options.map(function(opt){
                var sel=answers[QUESTIONS[qi].id]===opt;
                return <button key={opt} onClick={function(){answerQ(opt);}} style={{padding:".85rem 1.1rem",border:"1px solid "+(sel?G:BD),background:sel?"rgba(201,168,76,.12)":"transparent",color:sel?G:CR,fontFamily:JO,fontSize:".84rem",cursor:"pointer",textAlign:"left",lineHeight:1.4}}>{opt}</button>;
              })}
            </div>
          ):(
            <div>
              <input type="text" value={tIn} placeholder={QUESTIONS[qi].ph} onChange={function(e){setTIn(e.target.value);}} onKeyDown={function(e){if(e.key==="Enter"&&tIn.trim())answerQ(tIn.trim());}} style={{width:"100%",background:"#0E0E0E",border:"1px solid "+BD,color:CR,fontFamily:JO,fontSize:"1rem",padding:".85rem 1.1rem",outline:"none",marginBottom:"1.25rem"}} />
              <div style={Object.assign({},S.row,{gap:"1rem"})}>
                <Btn onClick={function(){answerQ("Not specified");}}>Skip</Btn>
                <Btn gold onClick={function(){answerQ(tIn.trim()||"Not specified");}}>Next</Btn>
              </div>
            </div>
          )}
          {qi>0&&<button onClick={function(){setQi(qi-1);setTIn("");}} style={{background:"transparent",border:"none",color:DM,fontFamily:MO,fontSize:".73rem",cursor:"pointer",marginTop:"1rem"}}>Previous</button>}
        </div>
      )}

      {page==="analyzing"&&(
        <div className="ld">
          <div className="ring" />
          <div>
            <h2 style={Object.assign({},S.serif("1.8rem"),{color:CR,textAlign:"center"})}>Researching global incentives</h2>
            <p style={Object.assign({},S.mono(G,".78rem"),{textAlign:"center",marginTop:".5rem"})}>{"Scanning "+COUNTRIES[cidx]+"..."}</p>
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:".55rem",width:330}}>
            {["Scanning script for location requirements","Searching IMDb for cast and director","Reading budget origin and rate base","Scanning 100+ global incentive programs","Running treaty and stacking optimizer"].map(function(s,i){
              return <div key={i} style={{display:"flex",alignItems:"center",gap:".65rem",fontFamily:MO,fontSize:".78rem",color:i<lStep?G:i===lStep?CR:DM}}><div style={{width:6,height:6,borderRadius:"50%",background:"currentColor",flexShrink:0}} />{s}</div>;
            })}
          </div>
          <p style={S.mono(DM,".7rem")}>Takes 30-60 seconds. Researching live data.</p>
        </div>
      )}

      {page==="results"&&results&&(
        <div className="sc960 fu">
          <div style={{borderBottom:"1px solid "+BD,paddingBottom:"2rem",marginBottom:"2.5rem"}}>
            <Eyebrow>Analysis Complete</Eyebrow>
            <h2 style={Object.assign({},S.serif("2.5rem",300),{color:CR,marginBottom:".5rem"})}>Top Filming Destinations</h2>
            <p style={{fontSize:".88rem",color:DM,lineHeight:1.6,maxWidth:640,marginBottom:"1rem"}}>{results.overallRecommendation}</p>
            <div style={Object.assign({},S.wrap,{gap:".65rem"})}>
              {results.directorIntel&&<div style={Object.assign({},S.box(),{padding:".45rem .85rem",fontSize:".73rem",fontFamily:MO})}><span style={{color:DM}}>Director: </span><span style={{color:CR}}>{results.directorIntel.name}</span><span style={{color:G}}>{" - "+results.directorIntel.nationality}</span>{results.directorIntel.imdbFound&&<span style={{color:"#5A9A5A",marginLeft:".45rem"}}>IMDb</span>}</div>}
              {results.writerIntel&&<div style={Object.assign({},S.box(),{padding:".45rem .85rem",fontSize:".73rem",fontFamily:MO})}><span style={{color:DM}}>Writer: </span><span style={{color:G}}>{results.writerIntel.nationality}</span></div>}
              <div style={Object.assign({},S.box(),{padding:".45rem .85rem",fontSize:".73rem",fontFamily:MO})}><span style={{color:DM}}>Origin: </span><span style={{color:CR}}>{results.budgetOrigin}</span></div>
              <div style={Object.assign({},S.box(),{padding:".45rem .85rem",fontSize:".73rem",fontFamily:MO})}><span style={{color:DM}}>BTL base: </span><span style={{color:G}}>{fmt(results.variableBTLBase)}</span></div>
            </div>
            {results.currencyNote&&<p style={Object.assign({},S.mono(DM,".74rem"),{marginTop:".45rem"})}>{results.currencyNote}</p>}
            {pref.length>0&&<p style={Object.assign({},S.mono(G,".74rem"),{marginTop:".45rem"})}>{"Requested: "+pref.join(", ")}</p>}
          </div>

          {results.homeBase&&(
            <div style={{marginBottom:"1.5rem"}}>
              <div style={Object.assign({},S.mono(DM,".68rem"),{letterSpacing:".15em",textTransform:"uppercase",marginBottom:".5rem"})}>Home Base Baseline</div>
              <HomeBaseCard homeBase={results.homeBase} budget={parsed&&parsed.totalBudget} />
            </div>
          )}
          <div style={Object.assign({},S.mono(DM,".68rem"),{letterSpacing:".15em",textTransform:"uppercase",marginBottom:".5rem"})}>Top Destinations vs. Home Base</div>
          {results.destinations&&results.destinations.map(function(d,i){
            var oKey="dest_"+i;
            return <DestCard key={i} dest={d} isTop={i===0} budget={parsed&&parsed.totalBudget} open={!!openCards[i]} setOpen={function(v){setOpenCards(function(prev){var n=Object.assign({},prev);n[i]=v;return n;});}} overrideData={overrideResults[oKey]} overridePending={overridePending===oKey} onRunOverride={function(){setOpenCards(function(prev){var n=Object.assign({},prev);n[i]=true;return n;});runOverrideAnalysis(i,d);}} />;
          })}

          {results.treatyOptimizer&&<TreatyOptimizer data={results.treatyOptimizer} />}

          <div style={{marginTop:"2.5rem",border:"1px solid "+BD,overflow:"hidden"}}>
            <div style={{background:"#0C0C0C",padding:".9rem 1.5rem",borderBottom:"1px solid "+BD}}>
              <div style={S.serif("1.3rem")}>Ask a Follow-up Question</div>
              <div style={S.mono(DM,".72rem")}>Full production context loaded</div>
            </div>
            {msgs.length===0?<div style={{padding:"1.75rem",textAlign:"center",color:DM,fontSize:".8rem",fontFamily:MO}}>No questions yet. Try a suggestion below or type your own.</div>:
            <div style={{maxHeight:360,overflowY:"auto",padding:"1.1rem 1.5rem",display:"flex",flexDirection:"column",gap:".85rem"}}>
              {msgs.map(function(m,i){return <div key={i} style={{maxWidth:"85%",padding:".8rem 1rem",fontSize:".86rem",lineHeight:1.65,alignSelf:m.role==="user"?"flex-end":"flex-start",background:m.role==="user"?"rgba(201,168,76,.1)":"#0E0E0E",border:"1px solid "+(m.role==="user"?"rgba(201,168,76,.2)":BD),color:CR,whiteSpace:"pre-wrap"}}>{m.text}</div>;})}
              {chatLd&&<div style={{padding:".8rem 1rem",fontSize:".76rem",color:DM,fontFamily:MO,alignSelf:"flex-start",background:"#0E0E0E",border:"1px solid "+BD}}>Researching...</div>}
              <div ref={chatEnd} />
            </div>}
            <div style={Object.assign({},S.wrap,{gap:".4rem",padding:".65rem 1.5rem",borderTop:"1px solid "+BD,background:BG})}>
              {CHAT_CHIPS.filter(function(s){return!msgs.some(function(m){return m.text===s;});}).map(function(s){return <button key={s} onClick={function(){sendChat(s);}} style={{background:"transparent",border:"1px solid "+BD,color:DM,fontSize:".7rem",padding:".28rem .65rem",cursor:"pointer",fontFamily:MO}}>{s}</button>;})}
            </div>
            <div style={{display:"flex",borderTop:"1px solid "+BD}}>
              <input value={chatIn} onChange={function(e){setChatIn(e.target.value);}} onKeyDown={function(e){if(e.key==="Enter"&&!e.shiftKey)sendChat(chatIn);}} placeholder="Ask about co-productions, qualification gaps, rates..." disabled={chatLd} style={{flex:1,background:"#0A0A0A",border:"none",color:CR,fontFamily:JO,fontSize:".88rem",padding:".9rem 1.1rem",outline:"none"}} />
              <button onClick={function(){sendChat(chatIn);}} disabled={chatLd||!chatIn.trim()} style={{background:chatLd||!chatIn.trim()?"#3A3010":G,color:chatLd||!chatIn.trim()?"#5A5040":BG,border:"none",cursor:"pointer",padding:".9rem 1.25rem",fontFamily:JO,fontSize:".8rem",fontWeight:600,letterSpacing:".06em",textTransform:"uppercase",whiteSpace:"nowrap"}}>{chatLd?"...":"Ask"}</button>
            </div>
          </div>

          <div style={{marginTop:"2rem",padding:"1rem",border:"1px solid "+BD,fontSize:".73rem",color:DM,lineHeight:1.7,fontFamily:MO}}>DISCLAIMER: For informational and planning purposes only. Tax incentive programs change frequently. Consult a qualified entertainment attorney and/or production accountant before making financial decisions.</div>

          <div style={Object.assign({},S.center,{gap:"1rem",marginTop:"2rem",flexWrap:"wrap"})}>
            <Btn onClick={function(){setPage("qa");setQi(0);}}>Adjust Answers</Btn>
            <button onClick={function(){setShowLib(true);}} style={{background:"rgba(201,168,76,.1)",border:"1px solid rgba(201,168,76,.3)",color:G,fontFamily:JO,fontSize:".84rem",fontWeight:500,padding:".72rem 1.65rem",cursor:"pointer"}}>Save to Library</button>
            <Btn gold onClick={reset}>Analyze Another Budget</Btn>
          </div>
        </div>
      )}
    </div>
  );
}
