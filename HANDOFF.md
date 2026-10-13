# HANDOFF — Concert Watchlist Tracker

**Written:** 2026-10-13, by a Claude Code web/cloud session, because the owning
Claude account is going dormant and a different Claude account will pick this
up next with zero memory of this conversation. This file is the only thing
that survives the handoff — read it before touching anything.

---

## 0. READ THIS FIRST — two unrelated apps live in one repo

The GitHub repo `surajgohill-oss/Frametax` contains **two completely
different applications** that happen to share a repo name:

1. **Concert Watchlist Tracker** — `backend/` (FastAPI) + `frontend/`
   (Next.js). A ticket-price intelligence / watchlist app for concerts and
   sports events (StubHub/TickPick/Gametime/Vivid Seats). **This is the app
   this handoff is about.**
2. **FrameTax** — the root-level `FrameTax.jsx`, `FrameTax (1).jsx`,
   `FrameTax (1).html`, governed by `SKILL.md` at repo root. A single-file
   bundled film-production tax-incentive calculator. **Unrelated. Do not
   touch unless the user explicitly asks about the film-tax app.** This
   session never modified any of those files — confirmed by grep.

If a future session (or the next Claude account) sees `SKILL.md` and starts
reading FrameTax build-discipline rules while the user is asking about ticket
prices, that's the name collision biting again. Stop and re-read this file.

---

## 1. Branch situation — read before writing any code

Two branches exist with **completely unrelated git histories** (no common
ancestor — confirmed via `git merge-base`, which returns nothing):

| | `main` | `claude/concert-watchlist-tracker-Uia95` |
|---|---|---|
| Last commit | **2026-07-10** (`3eff1bd`) | 2026-07-09 (`366ef0e`) |
| First commit | `801fb35 feat: hybrid collection...` | `021ffcf Initial commit` |
| `railway.toml` present | yes | no |
| Frontend scaffold (package.json etc.) | **missing** (same problem as the other branch) | added by this session (see §3) |
| Real marketplace logo assets | yes (`frontend/public/logos/*.png,svg`) | no (this session built local SVG marks instead — see §3) |
| Extra backend routes | `follows.py`, `collect.py`, `collection_health.py`, `reliability.py`, `artist_intelligence.py` | none of these |
| Extra frontend pages | `all-events`, `follows`, `watchlist`, `layout.tsx` | none of these |
| Local-Mac collector architecture (`LOCAL_COLLECTOR_SECRET`) | yes | no — this branch assumes server-side Playwright scraping only |

**`main` is almost certainly the real, currently-deployed app** — it's more
recent, more complete, has the Railway deploy config, and its commit
messages ("real marketplace logos," "Sold language," "sign/color
consistency") describe UI work that sounds like a parallel/later pass over
the same problems this session worked on, independently, on a disconnected
history. This is very likely the other Claude account's work, done directly
against a local clone (not a cloud sandbox), which is why it actually
reached the user's real running app while this session's work did not (see
§4).

**Recommendation for whoever picks this up: work from `main`.** Treat
`claude/concert-watchlist-tracker-Uia95` as a stale, isolated side-branch —
review it for ideas (the seller-behavior bug class in §3 is worth checking
against `main`), but **do not attempt a git merge between them** — the
unrelated histories mean git will not give you a clean merge; cherry-pick
specific file diffs by hand if anything is worth porting.

---

## 2. Environment facts learned the hard way this session

- This Claude account's sessions run in **Claude Code on the web** —
  isolated, ephemeral cloud containers. Each new session may start a **fresh
  container with no memory of previous runs** (confirmed: `uptime` showed
  "up 1 min" at the start of later turns in this same conversation, meaning
  everything not committed to git — installed deps, running servers, local
  Postgres data — was gone).
- **This session's `localhost:3000` / `localhost:8000` are never the user's
  localhost.** There is no network path from this container to the user's
  machine. Anything demoed/screenshotted from here is sandbox-only, not
  proof the user's real app reflects the change.
- **No Railway connection exists in this environment** — no Railway
  MCP server, no CLI, no credentials. This session cannot read Railway
  usage, logs, or pause/scale services. That has to happen in the Railway
  dashboard, by the user, directly.
- Git remote is reachable (via a local proxy to GitHub), so **commits and
  pushes are the only durable output** of a session here. Everything else
  (running processes, seeded databases, installed node_modules) evaporates
  between sessions.

---

## 3. What this session (`claude/concert-watchlist-tracker-Uia95`) actually did

Two commits, both on that branch, both pushed to `origin`:

**`01f4ffe` — UI Polish Phase 1:** hero price-row alignment, panel
readability (StatCard/ScoreMeter font sizes and spacing), marketplace
coverage freshness colors, Venue Intelligence overflow containment, first
pass at a `MarketplaceLogo` component.

**`366ef0e` — UI Polish Phase 2:**
- Added a full Next.js scaffold (`package.json`, `tsconfig.json`,
  `next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`) because
  this branch's checkout had **none at all** — it was `src/` only and could
  not run. (`main` has the same gap — see §1 table — so if you're working
  from `main` you'll likely hit this exact problem and need to scaffold
  there too, or find out where the real deploy pipeline gets its scaffold
  from, since Railway's `Dockerfile.railway` only builds the Python backend.)
- **Seller Behavior panel bug (real finding, worth checking on `main`
  too):** the frontend's `SellerResponse` type and the "Largest Price
  Drops/Increases" table bound fields (`old_price`, `new_price`, `score`)
  that the backend (`app/services/intelligence_engine.py`) never sends — it
  actually sends `first_price_24h`, `current_price`, `delta_pct`,
  `aggression_ratio`. This made the Was/Now columns render blank, making
  the panel look empty/broken even when the backend had real repricing
  data. Fixed on this branch. **If `main`'s Sellers tab also looks sparse,
  check for the same class of mismatch — compare the frontend type to the
  actual SQL/dict keys in `intelligence_engine.py`'s seller query.**
- Local SVG marketplace logo marks (StubHub/TickPick/Gametime/Vivid Seats)
  — note `main` already has **real logo image assets** at
  `frontend/public/logos/`, which is a better solution than what this
  branch built. Don't port this branch's SVG-mark approach into `main`;
  main's real-asset approach is already better.
- Freshness state display (fresh/green, late/amber, stale/dead/red) wired
  into the hero, event cards, and Market tab, driven by
  `backend/app/utils/freshness.py`'s existing `compute_freshness` logic.
- Pin/unpin fix — the headline "selection" was previously wired through the
  card's full-surface `<Link>`, so every click navigated away instead of
  un-selecting; added a dedicated pin button + localStorage persistence.
  **Unverified whether `main` has this same bug** — not checked this
  session.
- Zero-delta color-neutrality fixes (0% / 0 listings were rendering red or
  green instead of neutral gray) across the hero and several panels.

**Everything above was verified only in this session's own disposable cloud
sandbox**, using a local Postgres + the backend's built-in `env_mode=mock`
with hand-seeded fake events (Morgan Jay, Ed Sheeran, BTS, Dallas Cowboys).
**None of it has been confirmed against the user's real data or real
running app.** Earlier in this conversation I incorrectly implied otherwise
in a progress report before the user caught it — see the correction later
in this same thread if you have transcript access; if not, just assume
"code-complete, sandbox-verified, never user-verified" for all of §3.

---

## 4. Railway usage — reported high despite the app being untouched — UNRESOLVED

The user reported (in this conversation) that Railway usage spiked despite
not having touched the app in weeks/months, and asked for all Railway
activity to be paused. **This was never confirmed resolved** — no Railway
access exists from any session in this environment, so it could only be
diagnosed, not fixed, from here.

**Root cause, confirmed by reading the scheduler code on both branches:**
the backend starts an always-on APScheduler loop unconditionally in
`app/main.py`'s `lifespan`, independent of any user HTTP traffic. It
launches headless-Chromium (Playwright) scrapes of marketplaces on a timer:

- This branch (`Uia95`): adaptive cadence per tracked event, from every
  **15 minutes** (event <8h away) up to every 24h (event >10 days away).
- `main`: several fixed interval jobs — as frequent as **every 1 minute**,
  plus jobs every 15 min, 30 min, 1h, and 6h.

Neither branch has an environment-variable kill switch for this — it starts
automatically whenever the backend process boots, for as long as any
events remain tracked/active in the database. This is almost certainly the
cost driver: the backend has been running continuous headless-browser
automation regardless of whether the user ever opened the app.

**Action still needed, and it can only be done by the user or a session
with real Railway access:**
1. Railway dashboard → the backend service → pause the service / scale to
   0 replicas. This is the only immediate stop available.
2. Consider adding a `POLLING_ENABLED` (or similar) env-gated flag around
   `start_scheduler()` in `app/main.py`'s lifespan so the service can stay
   up (e.g., to serve read traffic) while the scraping loop is off. Not yet
   built on either branch — flagged as a good next step, not done.

**Do not assume this has been handled.** Ask the user directly before doing
anything that would restart scheduler activity (e.g., deploying, waking a
paused service, creating new tracked events).

---

## 5. Suggested first steps for whoever (human or Claude) picks this up

1. Ask the user to confirm current Railway status (paused? still running?
   usage trend since) before touching deploy-adjacent code.
2. Confirm with the user which branch is actually deployed/served at their
   real URL — don't assume `main` without asking, even though evidence
   points that way.
3. If continuing UI/bug work, do it against whichever branch is confirmed
   live, and get verification from the user's own browser/screenshots —
   a cloud session here cannot prove anything renders in the user's real
   app (see §2).
4. If picking up the seller-behavior or pin/unpin fixes, re-verify they're
   actually needed on the live branch before porting — `main` may have
   already solved them differently (§3).
5. Leave this file in place and update it before you, too, go dormant.
