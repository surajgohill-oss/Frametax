/**
 * Entity Image System
 * Maps tracked entity names → logo URLs (ESPN CDN) and brand colors.
 * ESPN CDN logos are freely accessible without API keys.
 */

export interface EntityImageConfig {
  logo?: string;   // Team logo / artist image URL
  accent?: string; // Brand primary color override
}

// ── ESPN CDN helpers ──────────────────────────────────────────────────────────
const NFL = (abbrev: string) => `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrev}.png`;
const MLB = (abbrev: string) => `https://a.espncdn.com/i/teamlogos/mlb/500/${abbrev}.png`;
const NBA = (abbrev: string) => `https://a.espncdn.com/i/teamlogos/nba/500/${abbrev}.png`;
const NHL = (abbrev: string) => `https://a.espncdn.com/i/teamlogos/nhl/500/${abbrev}.png`;
const NCAAF = (abbrev: string) => `https://a.espncdn.com/i/teamlogos/ncaa/500/${abbrev}.png`;

// ── Entity → Image mapping ────────────────────────────────────────────────────
// Keys are lowercase entity names. Partial matching used as fallback.

export const ENTITY_IMAGES: Record<string, EntityImageConfig> = {

  // ─── NFL ────────────────────────────────────────────────────────────────────
  '49ers':            { logo: NFL('sf'),   accent: '#AA0000' },
  'san francisco 49ers': { logo: NFL('sf'), accent: '#AA0000' },
  'rams':             { logo: NFL('lar'),  accent: '#003594' },
  'la rams':          { logo: NFL('lar'),  accent: '#003594' },
  'chargers':         { logo: NFL('lac'),  accent: '#0080C6' },
  'la chargers':      { logo: NFL('lac'),  accent: '#0080C6' },
  'raiders':          { logo: NFL('lv'),   accent: '#A5ACAF' },
  'las vegas raiders':{ logo: NFL('lv'),   accent: '#A5ACAF' },
  'chiefs':           { logo: NFL('kc'),   accent: '#E31837' },
  'kansas city chiefs':{ logo: NFL('kc'),  accent: '#E31837' },
  'cowboys':          { logo: NFL('dal'),  accent: '#003594' },
  'dallas cowboys':   { logo: NFL('dal'),  accent: '#003594' },
  'eagles':           { logo: NFL('phi'),  accent: '#004C54' },
  'seahawks':         { logo: NFL('sea'),  accent: '#69BE28' },
  'broncos':          { logo: NFL('den'),  accent: '#FB4F14' },
  'steelers':         { logo: NFL('pit'),  accent: '#FFB612' },
  'patriots':         { logo: NFL('ne'),   accent: '#002244' },
  'giants':           { logo: NFL('nyg'),  accent: '#0B2265' },
  'jets':             { logo: NFL('nyj'),  accent: '#125740' },
  'bears':            { logo: NFL('chi'),  accent: '#0B162A' },
  'packers':          { logo: NFL('gb'),   accent: '#203731' },
  'vikings':          { logo: NFL('min'),  accent: '#4F2683' },
  'lions':            { logo: NFL('det'),  accent: '#0076B6' },
  'ravens':           { logo: NFL('bal'),  accent: '#241773' },
  'bengals':          { logo: NFL('cin'),  accent: '#FB4F14' },
  'browns':           { logo: NFL('cle'),  accent: '#311D00' },
  'texans':           { logo: NFL('hou'),  accent: '#03202F' },
  'colts':            { logo: NFL('ind'),  accent: '#002C5F' },
  'jaguars':          { logo: NFL('jax'),  accent: '#006778' },
  'titans':           { logo: NFL('ten'),  accent: '#0C2340' },
  'bills':            { logo: NFL('buf'),  accent: '#00338D' },
  'dolphins':         { logo: NFL('mia'),  accent: '#008E97' },
  'cardinals':        { logo: NFL('ari'),  accent: '#97233F' },
  'falcons':          { logo: NFL('atl'),  accent: '#A71930' },
  'panthers':         { logo: NFL('car'),  accent: '#0085CA' },
  'saints':           { logo: NFL('no'),   accent: '#D3BC8D' },
  'buccaneers':       { logo: NFL('tb'),   accent: '#D50A0A' },

  // ─── MLB ────────────────────────────────────────────────────────────────────
  'angels':           { logo: MLB('laa'),  accent: '#BA0021' },
  'la angels':        { logo: MLB('laa'),  accent: '#BA0021' },
  'dodgers':          { logo: MLB('lad'),  accent: '#005A9C' },
  'la dodgers':       { logo: MLB('lad'),  accent: '#005A9C' },
  'padres':           { logo: MLB('sd'),   accent: '#2F241D' },
  'giants baseball':  { logo: MLB('sf'),   accent: '#FD5A1E' },
  'sf giants':        { logo: MLB('sf'),   accent: '#FD5A1E' },
  'rangers':          { logo: MLB('tex'),  accent: '#003278' },
  'texas rangers':    { logo: MLB('tex'),  accent: '#003278' },
  'yankees':          { logo: MLB('nyy'),  accent: '#003087' },
  'red sox':          { logo: MLB('bos'),  accent: '#BD3039' },
  'cubs':             { logo: MLB('chc'),  accent: '#0E3386' },
  'white sox':        { logo: MLB('chw'),  accent: '#27251F' },
  'astros':           { logo: MLB('hou'),  accent: '#002D62' },
  'braves':           { logo: MLB('atl'),  accent: '#CE1141' },
  'mets':             { logo: MLB('nym'),  accent: '#002D72' },
  'phillies':         { logo: MLB('phi'),  accent: '#E81828' },
  'cardinals baseball': { logo: MLB('stl'), accent: '#C41E3A' },
  'brewers':          { logo: MLB('mil'),  accent: '#12284B' },
  'pirates':          { logo: MLB('pit'),  accent: '#27251F' },
  'mariners':         { logo: MLB('sea'),  accent: '#0C2C56' },
  'athletics':        { logo: MLB('oak'),  accent: '#003831' },
  'as':               { logo: MLB('oak'),  accent: '#003831' },
  'twins':            { logo: MLB('min'),  accent: '#002B5C' },
  'tigers':           { logo: MLB('det'),  accent: '#0C2340' },
  'indians':          { logo: MLB('cle'),  accent: '#00385D' },
  'guardians':        { logo: MLB('cle'),  accent: '#00385D' },
  'royals':           { logo: MLB('kc'),   accent: '#004687' },
  'orioles':          { logo: MLB('bal'),  accent: '#DF4601' },
  'blue jays':        { logo: MLB('tor'),  accent: '#134A8E' },
  'rays':             { logo: MLB('tb'),   accent: '#092C5C' },
  'marlins':          { logo: MLB('mia'),  accent: '#00A3E0' },
  'nationals':        { logo: MLB('wsh'),  accent: '#AB0003' },
  'rockies':          { logo: MLB('col'),  accent: '#33006F' },
  'diamondbacks':     { logo: MLB('ari'),  accent: '#A71930' },

  // ─── NBA ────────────────────────────────────────────────────────────────────
  'lakers':           { logo: NBA('lal'),  accent: '#552583' },
  'la lakers':        { logo: NBA('lal'),  accent: '#552583' },
  'clippers':         { logo: NBA('lac'),  accent: '#C8102E' },
  'la clippers':      { logo: NBA('lac'),  accent: '#C8102E' },
  'warriors':         { logo: NBA('gs'),   accent: '#1D428A' },
  'golden state warriors': { logo: NBA('gs'), accent: '#1D428A' },
  'celtics':          { logo: NBA('bos'),  accent: '#007A33' },
  'heat':             { logo: NBA('mia'),  accent: '#98002E' },
  'bulls':            { logo: NBA('chi'),  accent: '#CE1141' },
  'nets':             { logo: NBA('bkn'),  accent: '#000000' },
  'knicks':           { logo: NBA('ny'),   accent: '#006BB6' },
  'sixers':           { logo: NBA('phi'),  accent: '#006BB6' },
  'raptors':          { logo: NBA('tor'),  accent: '#CE1141' },
  'bucks':            { logo: NBA('mil'),  accent: '#00471B' },
  'hawks':            { logo: NBA('atl'),  accent: '#E03A3E' },
  'cavaliers':        { logo: NBA('cle'),  accent: '#860038' },
  'pistons':          { logo: NBA('det'),  accent: '#C8102E' },
  'pacers':           { logo: NBA('ind'),  accent: '#002D62' },
  'magic':            { logo: NBA('orl'),  accent: '#0077C0' },
  'hornets':          { logo: NBA('cha'),  accent: '#1D1160' },
  'grizzlies':        { logo: NBA('mem'),  accent: '#5D76A9' },
  'pelicans':         { logo: NBA('no'),   accent: '#0C2340' },
  'spurs':            { logo: NBA('sa'),   accent: '#C4CED4' },
  'mavs':             { logo: NBA('dal'),  accent: '#00538C' },
  'mavericks':        { logo: NBA('dal'),  accent: '#00538C' },
  'rockets':          { logo: NBA('hou'),  accent: '#CE1141' },
  'thunder':          { logo: NBA('okc'),  accent: '#007AC1' },
  'trail blazers':    { logo: NBA('por'),  accent: '#E03A3E' },
  'jazz':             { logo: NBA('utah'), accent: '#002B5C' },
  'nuggets':          { logo: NBA('den'),  accent: '#0E2240' },
  'timberwolves':     { logo: NBA('min'),  accent: '#0C2340' },
  'suns':             { logo: NBA('phx'),  accent: '#1D1160' },
  'sacramento kings': { logo: NBA('sac'),  accent: '#5A2D81' },

  // ─── NHL ────────────────────────────────────────────────────────────────────
  'la kings':         { logo: NHL('lak'),  accent: '#111111' },
  'ducks':            { logo: NHL('ana'),  accent: '#F47A38' },
  'mighty ducks':     { logo: NHL('ana'),  accent: '#F47A38' },
  'sharks':           { logo: NHL('sjs'),  accent: '#006D75' },
  'golden knights':   { logo: NHL('vgk'),  accent: '#B4975A' },

};

// ── Lookup with fuzzy fallback ────────────────────────────────────────────────

export function getEntityImage(entityName: string): EntityImageConfig {
  const key = entityName.toLowerCase().trim();

  // 1. Exact match
  if (ENTITY_IMAGES[key]) return ENTITY_IMAGES[key];

  // 2. Partial: entity name contains a key
  for (const [k, v] of Object.entries(ENTITY_IMAGES)) {
    if (key.includes(k)) return v;
  }

  // 3. Partial: a key contains the entity name
  for (const [k, v] of Object.entries(ENTITY_IMAGES)) {
    if (k.includes(key)) return v;
  }

  return {};
}
