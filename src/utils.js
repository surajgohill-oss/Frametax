export async function callClaude(messages, useSearch, maxTok, apiKey) {
  if (!maxTok) maxTok = 4000;
  var body = {
    model: "claude-sonnet-4-20250514",
    max_tokens: maxTok,
    messages: messages
  };
  if (useSearch) {
    body.tools = [{ type: "web_search_20250305", name: "web_search" }];
  }
  var headers = { "Content-Type": "application/json", "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" };
  if (apiKey) headers["x-api-key"] = apiKey;
  var res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: headers,
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error("API error " + res.status);
  var data = await res.json();
  return data.content.filter(function(b) { return b.type === "text"; })
    .map(function(b) { return b.text; }).join("\n");
}

export function parseJSON(raw) {
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

export function autoCloseJSON(s) {
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
  var trimmed = s.replace(/,\s*$/, "");
  return trimmed + stack.reverse().join("");
}

export async function fetchFXRates() {
  try {
    var res = await fetch("https://open.er-api.com/v6/latest/USD");
    if (!res.ok) return null;
    var data = await res.json();
    return (data && data.rates) ? data.rates : null;
  } catch(e) { return null; }
}

export function fmt(n) {
  if (!n && n !== 0) return "-";
  var v = parseFloat(String(n).replace(/[^0-9.-]/g,""));
  if (isNaN(v)) return String(n);
  if (v >= 1000000) return "$" + (v/1000000).toFixed(1) + "M";
  if (v >= 1000)    return "$" + (v/1000).toFixed(0) + "K";
  return "$" + v.toFixed(0);
}
