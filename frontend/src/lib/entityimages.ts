// Deterministic gradient art system for events — no external image dependencies

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

function djb2(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash; // force 32-bit int
  }
  return Math.abs(hash);
}

export function getEventGradient(artist: string | null | undefined, title = ""): GradientPair {
  const key = (artist ?? title).toLowerCase().trim();
  for (const [pattern, grad] of Object.entries(ARTIST_GRADIENTS)) {
    if (key.includes(pattern)) return grad;
  }
  // Also try title
  const titleKey = title.toLowerCase();
  for (const [pattern, grad] of Object.entries(ARTIST_GRADIENTS)) {
    if (titleKey.includes(pattern)) return grad;
  }
  const idx = djb2(key || titleKey) % FALLBACK_GRADIENTS.length;
  return FALLBACK_GRADIENTS[idx];
}

/** CSS background string — cinematic radial gradient, no image needed */
export function gradientBg(colors: GradientPair, intensity: "low" | "medium" | "high" = "medium"): string {
  const [c1, c2] = colors;
  // opacity hex suffixes — boosted from previous values so art reads clearly
  const a1 = intensity === "low" ? "66" : intensity === "medium" ? "99" : "cc";
  const a2 = intensity === "low" ? "55" : intensity === "medium" ? "88" : "bb";
  return [
    `radial-gradient(ellipse at 15% 65%, ${c1}${a1} 0%, transparent 60%)`,
    `radial-gradient(ellipse at 85% 30%, ${c2}${a2} 0%, transparent 55%)`,
    `radial-gradient(ellipse at 50% 50%, ${c1}22 0%, transparent 80%)`,
    "#0d1117",
  ].join(", ");
}

/** Extract grouping artist key from event title */
export function extractGroupKey(artist: string | null | undefined, title: string): string {
  if (artist) {
    // Normalize NFL variants to single "NFL" group
    if (artist.toLowerCase().startsWith("nfl") || title.toLowerCase().startsWith("nfl")) return "NFL";
    return artist;
  }
  const colonIdx = title.indexOf(":");
  if (colonIdx > 0) return title.slice(0, colonIdx).trim();
  return title;
}
