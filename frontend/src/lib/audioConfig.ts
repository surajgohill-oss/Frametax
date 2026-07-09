/**
 * Audio configuration for event-specific themes.
 *
 * NFL_THEME_AUDIO_URL is a TEMPORARY CloudFront dev URL.
 * TODO: Replace with local asset at /audio/nfl-theme.mp3 once the file is
 * added to frontend/public/audio/. The production path is intentionally
 * preferred; fall back to the CDN URL only when the local file is absent.
 */

// Prefers local public asset; falls back to CloudFront dev URL when local file absent.
// To use local file: copy MP3 to frontend/public/audio/nfl-theme.mp3
export const NFL_THEME_AUDIO_URL =
  process.env.NEXT_PUBLIC_NFL_THEME_URL ??
  "/audio/nfl-theme.mp3";

export const NFL_THEME_LABEL = "NFL Theme";

/** Pattern that identifies an event as NFL-related. */
export const NFL_PATTERN = /\bnfl\b|49ers|rams|chargers|chiefs|eagles|cowboys|packers|patriots|giants|jets|bears|lions|broncos|seahawks|saints|falcons|panthers|buccaneers|cardinals|steelers|ravens|browns|bengals|texans|titans|colts|jaguars|raiders|chiefs\b/i;

export function isNflEvent(title: string, artist?: string | null): boolean {
  return NFL_PATTERN.test(title) || NFL_PATTERN.test(artist ?? "");
}
