// Deterministic gradient art system for events — no external image dependencies

type GradientPair = [string, string];

const ARTIST_GRADIENTS: Record<string, GradientPair> = {
  "ariana grande":     ["#c850c0", "#4158d0"],
  "bts":               ["#667eea", "#764ba2"],
  "bts world tour":    ["#667eea", "#764ba2"],
  "fifa":              ["#1a6b3a", "#0052cc"],
  "fifa world cup":    ["#1a6b3a", "#0052cc"],
  "nfl":               ["#013369", "#d50a0a"],
  "49ers":             ["#aa0000", "#b5832c"],
  "ed sheeran":        ["#c97b2a", "#e8c34a"],
  "foo fighters":      ["#1c1c1c", "#c41230"],
  "la philharmonic":   ["#614385", "#c7903c"],
  "morgan jay":        ["#005c97", "#363795"],
  "morgan wallen":     ["#373b44", "#4286f4"],
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
  const a1 = intensity === "low" ? "44" : intensity === "medium" ? "66" : "88";
  const a2 = intensity === "low" ? "33" : intensity === "medium" ? "55" : "77";
  return [
    `radial-gradient(ellipse at 20% 60%, ${c1}${a1} 0%, transparent 55%)`,
    `radial-gradient(ellipse at 80% 35%, ${c2}${a2} 0%, transparent 50%)`,
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
