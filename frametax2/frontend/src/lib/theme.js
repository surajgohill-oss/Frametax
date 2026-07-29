// CineGlobe day/night theme.
//
// PHASE-1 FINDING (2026-07-28): there was no theme system to "restore". The
// header control was shipped `disabled`, titled "Theme — no dark token set
// exists in this app yet"; no theme state existed anywhere in state/; and
// tokens.css scoped its --dark-* block to "globe canvases and their
// immediate chrome ONLY. Never applied to the application shell or content
// screens." So the failure chain had no broken link — the control was an
// honest placeholder. This module is that missing owner, built on the
// EXISTING token architecture rather than as a parallel system.
//
// The state lives on document.documentElement as `data-theme`, because the
// whole design system is already CSS custom properties: flipping one
// attribute re-resolves every token at once, with no React re-render and,
// critically, no remount of the Globe's WebGL context (a required
// acceptance condition — Project Globe must survive a theme switch).

const STORAGE_KEY = "cineglobe:theme";
export const THEMES = ["day", "night"];
const DEFAULT_THEME = "day";

const listeners = new Set();

function normalise(value) {
  return THEMES.includes(value) ? value : DEFAULT_THEME;
}

// Read persisted preference. Deliberately localStorage, not a server/account
// setting: the brief allows preserving the choice but explicitly forbids
// inventing account-level persistence, and a theme that resets on every
// refresh reads as broken.
export function readStoredTheme() {
  try {
    return normalise(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    // Private mode / storage disabled — fall back to the default rather than
    // breaking the shell.
    return DEFAULT_THEME;
  }
}

export function getTheme() {
  const attr = document.documentElement.getAttribute("data-theme");
  return normalise(attr);
}

export function setTheme(next) {
  const theme = normalise(next);
  document.documentElement.setAttribute("data-theme", theme);
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Non-fatal: the attribute is already applied, so the session still works.
  }
  listeners.forEach((fn) => {
    try { fn(theme); } catch { /* a bad subscriber must not break the rest */ }
  });
  return theme;
}

export function toggleTheme() {
  return setTheme(getTheme() === "night" ? "day" : "night");
}

// Subscribe to theme changes. Used by non-React consumers — specifically the
// Globe's WebGL scene, which must recolour its materials in place instead of
// being torn down and rebuilt.
export function subscribeTheme(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// Applied once at boot, before first paint, so the shell never flashes the
// day palette on a night-mode reload.
export function initTheme() {
  document.documentElement.setAttribute("data-theme", readStoredTheme());
}
