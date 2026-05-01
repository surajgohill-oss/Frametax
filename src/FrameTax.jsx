import { useState, useEffect, useRef } from "react";
import { callClaude, parseJSON, fmt, fetchFXRates } from "./utils.js";
import { QUESTIONS, COUNTRIES, FX_CURRENCIES } from "./constants.js";
import { Eyebrow, GhostBtn } from "./components/ui/index.js";
import DrivePicker from "./components/DrivePicker.jsx";
import LibraryPanel from "./components/LibraryPanel.jsx";
import HeroScreen from "./screens/HeroScreen.jsx";
import ParsingScreen from "./screens/ParsingScreen.jsx";
import AnalyzingScreen from "./screens/AnalyzingScreen.jsx";
import UploadScreen from "./screens/UploadScreen.jsx";
import QAScreen from "./screens/QAScreen.jsx";
import ReviewScreen from "./screens/ReviewScreen.jsx";
import ResultsScreen from "./screens/ResultsScreen.jsx";

export default function FrameTax() {
  var fileRef   = useRef(null);
  var scriptRef = useRef(null);
  var chatEnd   = useRef(null);

  var [page,           setPage]           = useState("hero");
  var [budget,         setBudget]         = useState("");
  var [script,         setScript]         = useState("");
  var [sName,          setSName]          = useState("");
  var [locReqs,        setLocReqs]        = useState(null);
  var [pref,           setPref]           = useState([]);
  var [cInput,         setCInput]         = useState("");
  var [parsed,         setParsed]         = useState(null);
  var [intel,          setIntel]          = useState(null);
  var [openD,          setOpenD]          = useState({});
  var [qi,             setQi]             = useState(0);
  var [answers,        setAnswers]        = useState({});
  var [tIn,            setTIn]            = useState("");
  var [results,        setResults]        = useState(null);
  var [lStep,          setLStep]          = useState(0);
  var [cidx,           setCidx]           = useState(0);
  var [dragB,          setDragB]          = useState(false);
  var [dragS,          setDragS]          = useState(false);
  var [err,            setErr]            = useState(null);
  var [msgs,           setMsgs]           = useState([]);
  var [chatIn,         setChatIn]         = useState("");
  var [chatLd,         setChatLd]         = useState(false);
  var [openCards,      setOpenCards]      = useState({});
  var [library,        setLibrary]        = useState([]);
  var [showLib,        setShowLib]        = useState(false);
  var [libLoaded,      setLibLoaded]      = useState(false);
  var [overrideResults, setOverrideResults] = useState({});
  var [overridePending, setOverridePending] = useState(null);
  var [driveOpen,      setDriveOpen]      = useState(false);
  var [driveFiles,     setDriveFiles]     = useState([]);
  var [driveLoading,   setDriveLoading]   = useState(false);
  var [driveTarget,    setDriveTarget]    = useState("budget");
  var [driveErr,       setDriveErr]       = useState(null);

  useEffect(function() {
    async function loadLib() {
      try {
        var result = await window.storage.get("frametax-library");
        if (result && result.value) setLibrary(JSON.parse(result.value));
      } catch(e) {}
      setLibLoaded(true);
    }
    loadLib();
  }, []);

  useEffect(function() {
    if (page !== "analyzing") return;
    var iv = setInterval(function() { setCidx(function(i) { return (i + 1) % COUNTRIES.length; }); }, 800);
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
    try { await window.storage.set("frametax-library", JSON.stringify(updated)); } catch(e) {}
  }

  async function deleteFromLibrary(id) {
    var updated = library.filter(function(e) { return e.id !== id; });
    setLibrary(updated);
    try { await window.storage.set("frametax-library", JSON.stringify(updated)); } catch(e) {}
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
      fxNote = "\nLIVE FX RATES (fetched " + new Date().toISOString().slice(0, 10) + ", source: open.er-api.com): " + fxLines + "\n";
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
    var origin   = ci.originCity || "Los Angeles";
    var rateBase = ci.rateBase || "US union rates";
    var total    = (parsed && parsed.totalBudget) || 0;
    var depts    = (parsed && parsed.departments) || [];

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
        treatyData = {
          executiveSummary: "Treaty analysis encountered a formatting issue. Please re-run the analysis or ask the follow-up chat for treaty recommendations.",
          strategies: [],
          warnings: ["Treaty optimizer returned invalid data - use the follow-up chat to ask specific treaty questions."]
        };
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
      var files = [];
      (data.content || []).forEach(function(block) {
        if (block.type === "mcp_tool_result") {
          try {
            var text = (block.content && block.content[0] && block.content[0].text) || "";
            var parsed2 = JSON.parse(text);
            if (Array.isArray(parsed2)) files = parsed2;
            else if (parsed2.files) files = parsed2.files;
          } catch(e) {
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
          var lines2 = block.text.split("\n");
          lines2.forEach(function(line) {
            var idMatch2 = line.match(/\b([a-zA-Z0-9_-]{25,})\b/);
            var nameMatch2 = line.match(/\*\*(.+?)\*\*/) || line.match(/^\d+\.\s+(.+?)(?:\s+-|\s+\(|$)/);
            if (idMatch2 && nameMatch2) {
              files.push({ id: idMatch2[1], name: nameMatch2[1].trim(), mimeType: "" });
            }
          });
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
        if (block.type === "text" && !content) content += block.text;
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
      var total2  = (parsed && parsed.totalBudget) || 0;
      var depts2  = (parsed && parsed.departments) || [];
      var vBTL2 = depts2.filter(function(d) { return !/above|post/i.test(d.name); })
        .reduce(function(s, d) { return s + (d.total || 0); }, 0);
      var fATL2 = depts2.filter(function(d) { return /above/i.test(d.name); })
        .reduce(function(s, d) { return s + (d.total || 0); }, 0);
      var ci2 = intel || {};

      var failedQuals = (dest.qualifications || [])
        .filter(function(q) { return q.status === "fail" || q.status === "partial"; })
        .map(function(q) { return q.test + ": " + q.detail; })
        .join("; ");

      var deptBreakdown = depts2.map(function(d) { return d.name + " $" + (d.total || 0); }).join(", ");

      var prompt = "Expert film finance accountant and production attorney.\n\n"
        + "SCENARIO: Assume this production FULLY QUALIFIES for all incentives in " + dest.country + " - " + dest.incentiveProgram + ".\n"
        + "The qualifications that previously flagged as failed or partial are: " + (failedQuals || "none noted") + "\n"
        + "Ignore those barriers for this analysis. Assume the production has structured itself to fully qualify.\n\n"
        + "BUDGET DATA:\n"
        + "Total Budget: " + fmt(total2) + "\n"
        + "Fixed ATL (not rebased): " + fmt(fATL2) + " | Variable BTL (rebased to local rates): " + fmt(vBTL2) + "\n"
        + "Rate base origin: " + (ci2.rateBase || "US union rates") + "\n"
        + "Budget origin: " + (ci2.originCity || "Los Angeles") + "\n"
        + "Departments: " + deptBreakdown + "\n"
        + "Finance costs: " + (ci2.hasFinance ? fmt(ci2.financeAmt) : "not in budget") + "\n"
        + "Insurance: " + (ci2.hasInsurance ? fmt(ci2.insuranceAmt) : "not in budget") + "\n"
        + "Completion bond: " + (ci2.hasBond ? fmt(ci2.bondAmt) : "not in budget") + "\n\n"
        + "Previous non-override results for " + dest.country + ":\n"
        + "- Credit rate: " + dest.creditRate + "\n"
        + "- Previous estimated credit: " + fmt(dest.estimatedCredit) + "\n"
        + "- Previous true net cost: " + fmt(dest.trueNetCost) + "\n"
        + "- BTL rate multiplier vs home: " + (dest.baseRateMultiplier || "unknown") + "\n\n"
        + "TASK: Produce a FULL OVERRIDE ANALYSIS assuming complete qualification.\n"
        + "Output ONLY valid JSON - no markdown, no backticks. Start with { end with }.\n"
        + "Schema: {\"assumedCreditRate\":\"e.g. 25%\",\"qualifyingSpend\":8000000,\"totalCreditOverride\":2000000,"
        + "\"rebasedBTL\":4500000,\"fixedATL\":3000000,\"localCostTotal\":7500000,\"travelCost\":180000,"
        + "\"trueNetCostOverride\":5680000,\"savingsVsHome\":2320000,\"savingsVsPrevious\":850000,"
        + "\"upliftVsPrevious\":\"Additional $850K vs non-qualifying scenario\","
        + "\"methodology\":[{\"step\":1,\"label\":\"string\",\"calculation\":\"string\",\"result\":0,\"notes\":\"string\"}],"
        + "\"structuringSteps\":[{\"action\":\"string\",\"timeframe\":\"string\",\"cost\":\"string\",\"critical\":true}],"
        + "\"assumedQualifications\":[{\"test\":\"string\",\"howToPass\":\"string\",\"difficulty\":\"low|medium|high\"}],"
        + "\"caveats\":[\"string\"],\"executiveSummary\":\"string\"}";

      var raw = await callClaude([{ role:"user", content:prompt }], true, 5000);
      var data = parseJSON(raw);
      setOverrideResults(function(prev) {
        var n = Object.assign({}, prev); n[key] = data; return n;
      });
    } catch(e) {
      setOverrideResults(function(prev) {
        var n = Object.assign({}, prev); n[key] = { error: "Override analysis failed: " + e.message }; return n;
      });
    } finally { setOverridePending(null); }
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
    ? parsed.departments.reduce(function(s, d) {
        return s + d.items.filter(function(i) { return i.isFixed; })
          .reduce(function(ss, ii) { return ss + (ii.amount || 0); }, 0);
      }, 0) : 0;
  var varTot = (parsed && parsed.departments)
    ? parsed.departments.reduce(function(s, d) {
        return s + d.items.filter(function(i) { return !i.isFixed; })
          .reduce(function(ss, ii) { return ss + (ii.amount || 0); }, 0);
      }, 0) : 0;

  var navSteps = ["upload", "review", "qa", "results"];

  return (
    <div className="fta">
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

      {showLib && (
        <LibraryPanel
          library={library}
          libLoaded={libLoaded}
          page={page}
          results={results}
          parsed={parsed}
          budget={budget}
          deleteFromLibrary={deleteFromLibrary}
          loadFromLibrary={loadFromLibrary}
          saveToLibrary={saveToLibrary}
          setShowLib={setShowLib}
        />
      )}

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
        <HeroScreen library={library} setPage={setPage} setShowLib={setShowLib} />
      )}

      {page === "upload" && (
        <UploadScreen
          budget={budget} setBudget={setBudget}
          script={script} sName={sName}
          err={err} dragB={dragB} setDragB={setDragB} dragS={dragS} setDragS={setDragS}
          fileRef={fileRef} scriptRef={scriptRef}
          setDriveTarget={setDriveTarget} setDriveOpen={setDriveOpen}
          setDriveFiles={setDriveFiles} setDriveErr={setDriveErr}
          setPage={setPage} parseBudget={parseBudget}
          loadBudget={loadBudget} loadScript={loadScript}
          setScript={setScript} setSName={setSName} setLocReqs={setLocReqs}
        />
      )}

      {page === "parsing" && <ParsingScreen />}

      {page === "review" && (
        <ReviewScreen
          parsed={parsed} intel={intel} fixedTot={fixedTot} varTot={varTot}
          pref={pref} setPref={setPref} cInput={cInput} setCInput={setCInput}
          openD={openD} setOpenD={setOpenD} setPage={setPage} analyze={analyze}
        />
      )}

      {page === "qa" && (
        <QAScreen
          qi={qi} setQi={setQi} answers={answers}
          tIn={tIn} setTIn={setTIn} err={err} answerQ={answerQ}
        />
      )}

      {page === "analyzing" && <AnalyzingScreen cidx={cidx} lStep={lStep} />}

      {page === "results" && (
        <ResultsScreen
          results={results} parsed={parsed} pref={pref}
          msgs={msgs} chatIn={chatIn} setChatIn={setChatIn} chatLd={chatLd}
          openCards={openCards} setOpenCards={setOpenCards}
          overrideResults={overrideResults} overridePending={overridePending}
          chatEnd={chatEnd} reset={reset} sendChat={sendChat}
          runOverrideAnalysis={runOverrideAnalysis}
          saveToLibrary={saveToLibrary} setShowLib={setShowLib}
          setPage={setPage} setQi={setQi}
        />
      )}
    </div>
  );
}
