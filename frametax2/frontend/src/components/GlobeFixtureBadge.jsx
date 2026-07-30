import { isFixtureActive, FIXTURE_DISCLOSURE } from "../lib/globeVisualFixture";

// Mandatory on-screen disclosure for the Globe visual validation fixture.
//
// The fixture assigns HYPOTHETICAL semantic states so the renderer can be
// verified against all four of them (live optimizer output currently exercises
// only three, and its distribution is not trustworthy as a production decision
// — see globeVisualFixture.js and the capability ledger). Anything that could
// be mistaken for a real conclusion has to say so, on screen, wherever the
// Globe is shown — not only in the console and not only on one screen. Hence a
// fixed-position element mounted once at the shell level.
//
// Renders nothing at all when the fixture is inactive, which is the default and
// the only possible state in a production build unless it is explicitly enabled
// at build time.
//
// The counts panel is the permitted development-only diagnostic: it proves the
// four-state distribution at a glance during verification. It must never ship
// as production UI, which is guaranteed by the same gate as the fixture itself.
export default function GlobeFixtureBadge({ counts = null }) {
  if (!isFixtureActive()) return null;
  return (
    <div className="globe-fixture-badge" role="status" aria-live="polite">
      <b>Globe visual fixture</b>
      <span>{FIXTURE_DISCLOSURE}</span>
      {counts && (
        // "states assigned" rather than a bare tally: this counts every
        // jurisdiction the fixture assigned a state to, which is legitimately
        // MORE than the number of hover markers on screen — a marker also needs
        // a JURISDICTION_COORDS entry, while a polygon only needs its ISO code.
        <span className="globe-fixture-counts">
          states assigned — Recommended {counts.gold} · Optimized alternative {counts.jade} ·
          {" "}Unlockable {counts.amber} · Additional {counts.silver}
        </span>
      )}
    </div>
  );
}
