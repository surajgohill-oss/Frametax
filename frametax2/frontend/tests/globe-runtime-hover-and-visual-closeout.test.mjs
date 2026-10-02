import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const globe = readFileSync(new URL("../src/components/Globe3D.jsx", import.meta.url), "utf8");
const projectGlobe = readFileSync(new URL("../src/screens/production/ProjectGlobe.jsx", import.meta.url), "utf8");
const workspace = readFileSync(new URL("../src/screens/production/Workspace.jsx", import.meta.url), "utf8");
const lum = (h) => { const x = h.replace("#", ""); return 0.299 * parseInt(x.slice(0, 2), 16) + 0.587 * parseInt(x.slice(2, 4), 16) + 0.114 * parseInt(x.slice(4, 6), 16); };

test("event surface: pointer listeners are on the globe mount, not on marker hit-targets", () => {
  for (const ev of ["pointermove", "pointerdown", "click", "mouseleave"]) {
    assert.match(globe, new RegExp(`mount\\.addEventListener\\("${ev}", onPolygon`), `${ev} polygon listener on mount`);
  }
  assert.match(globe, /pickRay\.setFromCamera\(ndc, camera\)/);
  assert.match(globe, /g\.toGeoCoords/);
  // polygon picking returns before consulting marker proximity; only fallback markers are skipped
  assert.match(globe, /closest\?\.\('\.globe-hit-target\[data-fallback="1"\]'\)/);
});

test("listener lifecycle: every polygon listener is removed on cleanup and re-bound with the mount effect", () => {
  for (const ev of ["pointermove", "pointerdown", "click", "mouseleave"]) {
    assert.match(globe, new RegExp(`mount\\.removeEventListener\\("${ev}", onPolygon`));
  }
  assert.match(globe, /stateRef\.current\.evalPointerHover = evalPointerHover/);
});

test("hover is re-evaluated when the camera moves under a stationary pointer", () => {
  const povIdx = globe.indexOf("povGlobe.setPointOfView(camera)");
  assert.ok(povIdx > 0);
  assert.match(globe.slice(povIdx, povIdx + 200), /evalPointerHover\?\.\(\)/);
  // stale-card guard: lastPolyIso is trusted only while it matches the rendered hover
  assert.match(globe, /iso === liveRef\.current\.lastPolyIso && \(!iso \|\| iso === liveRef\.current\.hoveredIso\)/);
  assert.match(globe, /document\.elementFromPoint\(pointer\.x, pointer\.y\)/);
});

test("Project Globe, Workspace Map and Split all mount the same Globe3D with point hover and click handlers", () => {
  for (const [name, src] of [["ProjectGlobe", projectGlobe], ["Workspace", workspace]]) {
    assert.match(src, /<Globe3D/, `${name} mounts Globe3D`);
    assert.match(src, /onPointHover=/, `${name} wires onPointHover`);
    assert.match(src, /onPointClick=/, `${name} wires onPointClick`);
  }
});

test("category tokens: brighter, ladder preserved, red is oxblood, only the Leading Alternative pulses", async () => {
  const d = await import("../src/lib/globeData.js");
  const S = d.OPTIMIZER_SEMANTIC;
  assert.deepEqual(Object.keys(S), ["gold", "jade", "silver", "amber", "red"]);
  assert.equal(S.gold.label, "Leading Alternative");
  assert.equal(S.red.label, "Unavailable");
  assert.deepEqual(Object.entries(S).filter(([, v]) => v.pulse).map(([k]) => k), ["gold"]);
  assert.deepEqual([...d.PULSE_TIERS], ["gold"]);
  const land = lum(d.GRAPHITE_HEX);
  assert.ok(lum(S.silver.hex) > land && lum(S.jade.hex) > lum(S.silver.hex) && lum(S.amber.hex) > lum(S.silver.hex));
  assert.ok(lum(S.gold.hex) - Math.max(lum(S.jade.hex), lum(S.amber.hex)) >= 25);
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(S.red.hex.slice(i, i + 2), 16));
  assert.ok(r > g * 1.6 && r > b * 1.6, "unavailable reads oxblood");
});

test("both themes: darker ocean than land with clear separation; land darker than before", () => {
  const grab = (theme, key) => new RegExp(`${theme}: \\{[\\s\\S]*?${key}: "(#[0-9a-fA-F]{6})"`).exec(globe)[1];
  for (const theme of ["day", "night"]) {
    const ocean = lum(grab(theme, "ocean"));
    const land = lum(grab(theme, "land"));
    assert.ok(land - ocean >= 40, `${theme} land clears ocean`);
  }
  assert.ok(lum(grab("day", "ocean")) < lum("#1c3350"), "day ocean deeper than prior");
  assert.ok(lum("#5d7a7e") < lum("#6c8c90"));
});

test("subtitle uses approved alternative terminology", () => {
  assert.ok(!/recommended structure for this production/i.test(projectGlobe));
  assert.match(projectGlobe, /leading alternative for this production/i);
});

test("ROOT CAUSE: the Inspector backdrop is not a pointer surface over the Globe", () => {
  const css = readFileSync(new URL("../src/styles/shell.css", import.meta.url), "utf8");
  const insp = readFileSync(new URL("../src/shell/Inspector.jsx", import.meta.url), "utf8");
  const rule = /\.inspector-backdrop \{[^}]*\}/.exec(css)[0];
  assert.match(rule, /pointer-events:\s*none/);
  assert.ok(!/inspector-backdrop"[^>]*onClick/.test(insp), "backdrop must not own a click handler");
  // outside-click close excludes the globe so globe click changes selection instead of closing
  assert.match(insp, /closest\("\.inspector, \.globe-canvas, \.globe-hit-target/);
  assert.match(insp, /document\.addEventListener\("pointerdown"/);
  assert.match(insp, /document\.removeEventListener\("pointerdown"/);
});
