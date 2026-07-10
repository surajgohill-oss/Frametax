// Display-only venue → city/market map (mirrors venues table; no backend call).
// Used to add the small muted "City, ST" context line on cards and headers.
const VENUE_CITY: Record<string, string> = {
  "amerant-bank-arena": "Sunrise, FL",
  "arrowhead-stadium": "Kansas City, MO",
  "att-stadium": "Arlington, TX",
  "bell-centre": "Montreal, QC",
  "bridgestone-arena": "Nashville, TN",
  "capital-one-arena": "Washington, DC",
  "cascades-amphitheater": "Ridgefield, WA",
  "climate-pledge-arena": "Seattle, WA",
  "crypto-arena": "Los Angeles, CA",
  "foxwoods-resort-casino": "Mashantucket, CT",
  "garden": "Boston, MA",
  "golden-1-center": "Sacramento, CA",
  "great-park-live": "Irvine, CA",
  "greek-theatre": "Los Angeles, CA",
  "harrahs-cherokee": "Cherokee, NC",
  "hawaii-theatre": "Honolulu, HI",
  "hollywood-bowl": "Los Angeles, CA",
  "intuit-dome": "Inglewood, CA",
  "kia-center": "Orlando, FL",
  "kia-forum": "Los Angeles, CA",
  "levis-stadium": "Santa Clara, CA",
  "lumen-field": "Seattle, WA",
  "mercedes-benz-stadium": "Atlanta, GA",
  "met-life-stadium": "East Rutherford, NJ",
  "metlife-stadium": "East Rutherford, NJ",
  "nissan-stadium": "Nashville, TN",
  "north-charleston-performing-arts-center": "North Charleston, SC",
  "north-island-credit-union-amphitheatre": "Chula Vista, CA",
  "oakland-arena": "Oakland, CA",
  "peoples-bank-arena": "Hartford, CT",
  "ppg-paints-arena": "Pittsburgh, PA",
  "rogers-arena": "Vancouver, BC",
  "schottenstein-center": "Columbus, OH",
  "scotiabank-arena": "Toronto, ON",
  "shoreline-amphitheatre": "Mountain View, CA",
  "sofi-stadium": "Inglewood, CA",
  "spectrum-center": "Charlotte, NC",
  "state-farm-arena": "Atlanta, GA",
  "state-farm-stadium": "Glendale, AZ",
  "the-castle-theatre": "Bloomington, IL",
  "t-mobile-arena": "Las Vegas, NV",
  "t-stadium": "Arlington, TX",
  "united-center": "Chicago, IL",
  "xfinity-mobile-arena": "Philadelphia, PA",
};

export function venueCity(slug?: string | null): string | null {
  if (!slug) return null;
  return VENUE_CITY[slug] ?? null;
}

/**
 * Opponent/matchup from a StubHub event URL slug (data already delivered by the
 * backend): ".../seattle-seahawks-seattle-tickets-8-15-2026/..." → "Seattle Seahawks".
 * Returns null for home games and concerts (slug resolves to the event's own name).
 */
// NFL mascot words — used to trim the trailing city from StubHub slugs like
// "new-york-giants-east-rutherford" (multi-word cities defeat drop-last-token).
const NFL_MASCOTS = new Set([
  "cardinals","falcons","ravens","bills","panthers","bears","bengals","browns",
  "cowboys","broncos","lions","packers","texans","colts","jaguars","chiefs",
  "raiders","chargers","rams","dolphins","vikings","patriots","saints","giants",
  "jets","eagles","steelers","49ers","seahawks","buccaneers","titans","commanders",
]);

export function deriveOpponent(title: string, stubhubUrl?: string | null): string | null {
  // Title already carries matchup context ("49ers at Chiefs", "X vs Y") — don't duplicate
  if (/ at | vs\.? /i.test(title)) return null;
  const m = stubhubUrl?.match(/stubhub\.com\/([a-z0-9-]+)-tickets-\d/);
  if (!m) return null;
  const tokens = m[1].split("-");
  if (tokens.length < 2) return null;
  // Prefer cutting at the last mascot word; otherwise drop the trailing city token
  let end = tokens.length - 1;
  for (let i = tokens.length - 1; i >= 0; i--) {
    if (NFL_MASCOTS.has(tokens[i])) { end = i + 1; break; }
  }
  const team = tokens.slice(0, end).map(w => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(" ");
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z]/g, "");
  if (!team || norm(team).length < 4) return null;
  if (norm(title).includes(norm(team)) || norm(team).includes(norm(title))) return null;
  return team;
}
