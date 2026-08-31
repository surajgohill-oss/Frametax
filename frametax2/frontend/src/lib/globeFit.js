// ── Globe camera fit: pure geometry ─────────────────────────────────────
//
// Extracted from Globe3D.jsx so it can be unit-tested without a WebGL context
// or a browser. This is the arithmetic that guarantees the Globe is never
// clipped, and it is exactly the class of thing that regressed unnoticed
// twice: a canvas can be perfectly "responsive" (buffer size tracking CSS
// size) while the sphere it renders overflows the frame, because those are two
// unrelated facts. Keeping the fit as a pure function means the no-clipping
// property is now asserted in tests rather than eyeballed in screenshots.
//
// HISTORY (do not re-tighten without re-reading this). Framing used to be a
// hardcoded `DEFAULT_CAMERA_DISTANCE = 225`, itself "pulled in from 246 so the
// globe fills more of its panel". Both values clip:
//   d=225 -> tan(asin(100/225)) / tan(25 deg) = 0.4966 / 0.4663 = 1.064
//   d=246 -> tan(asin(100/246)) / tan(25 deg) = 0.4465 / 0.4663 = 0.958
// i.e. at 225 the bare sphere is 106.4% of the available half-height, and even
// at 246 it reaches 95.8% — leaving nothing for the beacons that stand ON the
// sphere. Measured live at 1600x900 before the fix: silhouette radius 298px
// against a 280px half-height (18px clipped top and bottom) with 12 European
// markers projecting outside the canvas box entirely.

// three-globe's own globe radius. Not configurable by us.
export const GLOBE_GEOMETRY_RADIUS = 100;

// The radius that must actually stay inside the frame: the sphere PLUS the
// tallest thing standing on it. A recommendation beacon's glow shell reaches
// ~6 units above its footprint, that footprint sits at
// GOLD_BASELINE_POLYGON_ALTITUDE (0.065 -> 106.5), and the group is scaled
// 1.28x when it is the recommendation. Framing to the bare sphere is precisely
// how the recommendation marker ended up clipped against the edge.
export const GLOBE_CONTENT_RADIUS = 114;

// Breathing room, so the silhouette never grazes the edge and a polygon lifted
// by SELECTED_POLYGON_ALTITUDE near the limb still has somewhere to go.
export const FIT_MARGIN = 0.06;

export const CAMERA_FOV_DEG = 50;

/**
 * Camera distance at which `contentRadius` exactly fits the smaller of the two
 * half-extents of a `width` x `height` frame, less FIT_MARGIN.
 *
 * Pass the VISIBLE width — canvas width minus any Inspector overlay — so the
 * sphere stays whole inside the region the producer can actually see.
 *
 * Derivation: a sphere of radius R at distance d has silhouette half-angle
 * asin(R/d), which projects to tan(asin(R/d)) in half-frame units. It fits
 * vertically when that is <= tan(fovY/2), and horizontally when it is
 * <= tan(fovY/2) * aspect. Solving the binding one for d gives R / sin(theta).
 */
export function fitCameraDistance(width, height, contentRadius = GLOBE_CONTENT_RADIUS) {
  const halfV = Math.tan(((CAMERA_FOV_DEG * Math.PI) / 180) / 2);
  const aspect = width > 0 && height > 0 ? width / height : 1;
  // Vertical is limiting on a landscape panel, horizontal on a portrait one.
  const limiting = halfV * Math.min(1, aspect);
  const usable = Math.max(0.05, limiting * (1 - FIT_MARGIN));
  const sinTheta = Math.max(0.05, Math.sin(Math.atan(usable)));
  return contentRadius / sinTheta;
}

/**
 * The rendered silhouette radius of a sphere, in pixels, for a given frame and
 * camera distance. The inverse of the above, used by the tests to assert the
 * no-clipping property directly in the units a screenshot would show.
 */
export function silhouetteRadiusPx(width, height, distance, radius = GLOBE_GEOMETRY_RADIUS) {
  if (!(distance > radius)) return Infinity;
  const halfV = Math.tan(((CAMERA_FOV_DEG * Math.PI) / 180) / 2);
  const frac = Math.tan(Math.asin(radius / distance)) / halfV;
  return frac * (height / 2);
}
