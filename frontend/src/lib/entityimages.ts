// Gradient art + static image system for events

type GradientPair = [string, string];

const ARTIST_GRADIENTS: Record<string, GradientPair> = {
  "ariana grande":     ["#e040fb", "#3d5afe"],
  "bts":               ["#7c4dff", "#448aff"],
  "bts world tour":    ["#7c4dff", "#448aff"],
  "kid cudi":          ["#00e5ff", "#d500f9"],
  "fifa":              ["#00c853", "#0091ea"],
  "fifa world cup":    ["#00c853", "#0091ea"],
  "nfl":               ["#002244", "#d50a0a"],
  "49ers":             ["#aa0000", "#b5832c"],
  "ed sheeran":        ["#ff6d00", "#ffea00"],
  "foo fighters":      ["#b71c1c", "#212121"],
  "la philharmonic":   ["#6a1b9a", "#e65100"],
  "morgan jay":        ["#0288d1", "#283593"],
  "morgan wallen":     ["#37474f", "#1565c0"],
};

const FALLBACK_GRADIENTS: GradientPair[] = [
  ["#0f2027", "#2c5364"],
  ["#200122", "#6f0000"],
  ["#1d2671", "#c33764"],
  ["#134e5e", "#71b280"],
  ["#373b44", "#4286f4"],
  ["#0b486b", "#f56217"],
  ["#1a1a2e", "#533483"],
  ["#2d1b69", "#11998e"],
];

/**
 * Static artist image map — Songkick CDN (verified 200 OK).
 * Each entry: [match pattern, image URL]
 * Used as a fallback when no backend image_url is available.
 */
const STATIC_ART: [RegExp, string][] = [
  [/ariana grande/i,  "https://images.sk-static.com/images/media/profile_images/artists/5466476/huge_avatar"],
  [/bts\b/i,          "https://images.sk-static.com/images/media/profile_images/artists/8521933/huge_avatar"],
  [/kid cudi/i,       "https://images.sk-static.com/images/media/profile_images/artists/3017714/huge_avatar"],
  [/ed sheeran/i,     "https://images.sk-static.com/images/media/profile_images/artists/137952/huge_avatar"],
  [/foo fighters/i,   "https://images.sk-static.com/images/media/profile_images/artists/485568/huge_avatar"],
  [/morgan jay/i,     "https://images.sk-static.com/images/media/profile_images/artists/8789617/huge_avatar"],
];

function djb2(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return Math.abs(hash);
}

export function getEventGradient(artist: string | null | undefined, title = ""): GradientPair {
  const key = (artist ?? title).toLowerCase().trim();
  for (const [pattern, grad] of Object.entries(ARTIST_GRADIENTS)) {
    if (key.includes(pattern)) return grad;
  }
  const titleKey = title.toLowerCase();
  for (const [pattern, grad] of Object.entries(ARTIST_GRADIENTS)) {
    if (titleKey.includes(pattern)) return grad;
  }
  const idx = djb2(key || titleKey) % FALLBACK_GRADIENTS.length;
  return FALLBACK_GRADIENTS[idx];
}

/**
 * Return a static artist image URL for an event, or null if none is mapped.
 * Matches against artist field first, then event title.
 */
export function getStaticArtUrl(artist: string | null | undefined, title = ""): string | null {
  const haystack = (artist ?? title).toLowerCase();
  for (const [re, url] of STATIC_ART) {
    if (re.test(haystack)) return url;
  }
  const titleLower = title.toLowerCase();
  for (const [re, url] of STATIC_ART) {
    if (re.test(titleLower)) return url;
  }
  return null;
}

/**
 * Full artwork URL fallback chain:
 *   1. event.image_url (backend field, if ever populated)
 *   2. event.poster_url (backend field, if ever populated)
 *   3. static curated image (Songkick CDN)
 *   4. null → caller falls back to gradient
 */
export function getEventArtworkUrl(
  artist: string | null | undefined,
  title: string,
  imageUrl?: string | null,
  posterUrl?: string | null,
): string | null {
  return imageUrl || posterUrl || getStaticArtUrl(artist, title) || null;
}

/** CSS background string — artist-identity gradient, readable on dark cards */
export function gradientBg(colors: GradientPair, intensity: "low" | "medium" | "high" = "medium"): string {
  const [c1, c2] = colors;
  const a1 = intensity === "low" ? "30" : intensity === "medium" ? "55" : "77";
  const a2 = intensity === "low" ? "28" : intensity === "medium" ? "44" : "66";
  return [
    `radial-gradient(ellipse at 15% 65%, ${c1}${a1} 0%, transparent 60%)`,
    `radial-gradient(ellipse at 85% 30%, ${c2}${a2} 0%, transparent 55%)`,
    "#0d1117",
  ].join(", ");
}

/** Extract grouping artist key from event title */
export function extractGroupKey(artist: string | null | undefined, title: string): string {
  if (artist) {
    if (artist.toLowerCase().startsWith("nfl") || title.toLowerCase().startsWith("nfl")) return "NFL";
    return artist;
  }
  const colonIdx = title.indexOf(":");
  if (colonIdx > 0) return title.slice(0, colonIdx).trim();
  return title;
}
