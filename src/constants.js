export var GOLD   = "#C9A84C";
export var CREAM  = "#F0EAD6";
export var DIM    = "#8A8070";
export var BG     = "#080808";
export var BORDER = "#2A2520";

export var QUESTIONS = [
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

export var COUNTRIES = [
  "United Kingdom","Canada","Australia","New Zealand","Ireland",
  "Germany","France","Italy","Spain","Mexico","Czech Republic","Hungary",
  "South Africa","South Korea","Japan","UAE","Georgia","Serbia","Poland","Morocco"
];

export var SUGGEST_COUNTRIES = [
  "United Kingdom","Canada","Australia","Ireland",
  "New Zealand","South Africa","Mexico","Czech Republic","Hungary",
  "Georgia","Spain","Italy","Morocco","UAE","Serbia","Jordan","South Korea"
];

export var CHAT_SUGGESTIONS = [
  "What co-production structure gives the highest total credit?",
  "How does the director nationality affect qualification?",
  "What would unlock a higher credit tier?",
  "Currency hedging strategies I should consider?",
  "Which destination has the most flexible cultural test?"
];
