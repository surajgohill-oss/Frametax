import { useEffect, useState } from "react";
import {
  FIXTURE_DISCLOSURE,
  disableFixture,
  fixtureActivationSource,
  getFixtureCounts,
  isFixtureActive,
  subscribeFixtureCounts,
} from "../lib/globeVisualFixture";

const SOURCE_LABEL = {
  env: "VITE_GLOBE_VISUAL_FIXTURE=true",
  url: "?globeFixture=1",
  latched: "latched (localStorage)",
};

// Mandatory GLOBE MODE indicator for the development visual fixture.
//
// WHY IT IS THIS LOUD. The previous badge was correct but easy to miss, and the
// fixture could silently switch itself off on any in-app navigation — so a
// screenshot could show production colours while everyone believed the fixture
// was running. The brief is explicit: there must never again be uncertainty
// about whether fixture mode is active. So this states the MODE, the mechanism
// that enabled it, the state counts, and offers a one-click exit.
//
// The approved reference render carries a persistent "GLOBE MODE — Production"
// indicator in the shell, so a visible mode readout is part of the intended
// design rather than debug furniture. Placing it properly in the shell is a
// Phase 3 layout task; this is the development-only instance of the same idea,
// deliberately kept out of the shell so no navigation is redesigned here.
//
// Renders nothing when the fixture is inactive — the default, and the only
// possible state in a production build.
export default function GlobeFixtureBadge() {
  // Counts are published by globeData when it applies the fixture, so this can
  // be mounted once at the shell and still report the live distribution.
  const [counts, setCounts] = useState(getFixtureCounts);
  useEffect(() => subscribeFixtureCounts(setCounts), []);
  if (!isFixtureActive()) return null;
  const source = fixtureActivationSource();
  return (
    <div className="globe-mode-indicator" role="status" aria-live="polite">
      <div className="gmi-head">
        <span className="gmi-dot" aria-hidden="true" />
        <b>Globe mode · Visual fixture</b>
      </div>
      <span className="gmi-note">{FIXTURE_DISCLOSURE}</span>
      {counts && (
        // Counts of semantic states ASSIGNED. Legitimately higher than the
        // number of hover markers on screen: a marker also needs a
        // JURISDICTION_COORDS entry, a polygon only needs its ISO code.
        <span className="gmi-counts">
          Recommended {counts.gold} · Optimized {counts.jade} ·
          {" "}Unlockable {counts.amber} · Additional {counts.silver}
        </span>
      )}
      {source && <span className="gmi-src">enabled via {SOURCE_LABEL[source] || source}</span>}
      {source !== "env" && (
        // Env-var activation is build-time and cannot be revoked from the page,
        // so the exit is offered only for the latched/URL routes.
        <button
          type="button"
          className="gmi-exit"
          onClick={() => { disableFixture(); window.location.reload(); }}
        >
          Switch to production data
        </button>
      )}
    </div>
  );
}
