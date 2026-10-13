# HANDOFF — Concert Watchlist Tracker

**Updated:** 2026-10-13 (second pass, same day as the first version — major
new findings below). Written because the owning Claude account is going
dormant and a different Claude account will pick this up with zero memory
of this conversation. Read this before touching anything.

**Scope note:** this file is about the Concert Watchlist Tracker ONLY.

---

## 0. One repo, two unrelated products — do not cross-contaminate

The GitHub repo `surajgohill-oss/Frametax` also contains a second,
unrelated, much larger application (a film-tax-incentive / jurisdiction
optimizer, internally referred to as CineGlobe/FrameTax, with its own `ag/*`,
`codex/*`, and some `claude/*` branches, root-level `FrameTax*` files,
`frametax2/`, and `SKILL.md`). **Do not open, read, or modify any of that.**
It is not in scope here and was left completely untouched this session.
Everything below — every branch, file, and finding — is Concert Tracker
only.

---

## 1. Canonical branch: `main` — CONFIRMED, not just suspected

Earlier guidance (first version of this doc) said `main` was "almost
certainly" the real app, based on commit recency and content. **This is now
confirmed with hard evidence**, not inference: `main`'s `frontend/` source
tree matches — file-for-file (`EventCard.tsx`, `watchlist/`, `all-events/`,
`completed/`, `events/[id]/`, `lib/api.ts`, `lib/types.ts`) — the actual
file tree of the last successful **production** deployment on Vercel (see
§2). `claude/concert-watchlist-tracker-Uia95` is a stale, unrelated-history
side branch from an earlier phase of this engagement. **Work from `main`.**
Don't bother merging the two branches — they share no git ancestor, so a
real `git merge` won't work; cherry-pick by hand if anything from the side
branch is worth porting (see §5).

---

## 2. THE ACTIVE PROBLEM — Vercel production is broken, root cause confirmed

**Symptom:** every Vercel deployment triggered from `main` (or any other
branch) fails at build with:
```
NEXT_NO_VERSION: No Next.js version detected. Make sure your package.json
has "next"... check your Root Directory setting matches the directory of
your package.json file.
```
This has been failing for a long time — it's not something this session
caused.

**Root cause — two compounding issues, both confirmed:**
1. Vercel project `frontend` (`prj_ZSgKg60sZq5DiOLXvm8IdLWSxu05`, team
   `surajgohill-oss-projects`, team ID `team_Op5G1xigPzLobRGRBnaedMDW`) has
   its **Root Directory** set wrong — not pointing at `frontend/`. Repo root
   has no `package.json` on `main` at all, so any build starting from repo
   root fails immediately.
2. **`main`'s `frontend/` directory itself is missing its build scaffold** —
   no `package.json`, `tsconfig.json`, `next.config.js`, `tailwind.config.ts`,
   `postcss.config.js`. The Next.js *source code* is there and is genuinely
   well-developed; the files that make it buildable were simply never
   committed to this repo.

**How we know this for certain, not by guessing:** the Vercel project still
has one **READY, production-target** deployment live right now —
`dpl_BB5EjwbgzRTkVSrKNrqT5Lm2n1Xo`, currently aliased to
`frontend-surajgohill-oss-projects.vercel.app`. It was deployed via `vercel`
CLI directly (`source: "cli"`), not via GitHub, which is why it carries no
commit metadata and nothing in git history points to it. I pulled its stored
build output directly from Vercel's API and its scaffold files are below —
this is a byte-for-byte known-good configuration, not invented.

**Build-verified this session (local sandbox only, nothing pushed):** I
copied these exact 5 files onto a local checkout of `main`'s `frontend/`,
ran `npm install && next build`, and got a **clean build, zero errors**, all
7 routes (`/`, `/all-events`, `/completed`, `/events/[id]`, `/follows`,
`/watchlist`) compiled and statically generated successfully. This proves
`main`'s current source is not broken — it only lacks these files.

### The exact recovered scaffold (paste these into `frontend/` on `main`)

`frontend/package.json`:
```json
{
  "name": "concert-tracker-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.378.0",
    "next": "14.2.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.15.4",
    "tailwind-merge": "^2.6.1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.5.0",
    "eslint": "^8",
    "eslint-config-next": "14.2.3",
    "postcss": "^8.5.15",
    "tailwindcss": "^3.4.19",
    "typescript": "^5.9.3"
  }
}
```

`frontend/next.config.js`:
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;
```

`frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

`frontend/tailwind.config.ts`:
```ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1117",
          card: "#161b27",
          elevated: "#1e2535",
          border: "rgba(255,255,255,0.07)",
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

`frontend/postcss.config.js`:
```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### What's still needed to actually fix production

1. **Commit + push these 5 files to `main`.** Not yet done — a prior
   execution-authority instruction in this session explicitly required
   stopping for user approval before pushing anything to the production
   branch, and that approval was not given before the session moved on to
   this handoff update. **Check with the user first**, or just do it if
   they've since said yes elsewhere.
2. **Fix the Vercel Root Directory setting** to `frontend`, Framework Preset
   Next.js. **This cannot be done via the Vercel MCP connection in a cloud
   session** — `update_project` returns `403: you don't have permission to
   update the project`. Do this by hand in the Vercel dashboard: project
   `frontend` → Settings → General → Root Directory.
3. Redeploy `main` and confirm the deployment reaches `READY`.

Do both #1 and #2 — fixing only one still leaves the other failing.

---

## 3. Runtime status — could not be verified this session (not "working" or "broken", just unknown)

No Claude Code web/cloud session in this environment can reach:
- `https://backend-production-509f.up.railway.app` (Railway backend) — the
  sandbox's outbound proxy returns `403` for this host (confirmed via
  verbose curl: it's a proxy-level egress block, **not** evidence Railway
  itself is down).
- `https://frontend-surajgohill-oss-projects.vercel.app` (Vercel prod alias)
  — same proxy block.
- There is no Railway MCP/CLI connection available in this environment at
  all — confirmed by searching available tools.

So: whether the live app actually works right now, whether scheduled
polling is healthy, whether Railway usage/cost has stabilized — **all
unknown, not confirmed either way.** Don't report this as "fixed" or
"working" without checking directly (user's own browser, or a session with
real network/Railway access).

---

## 4. Railway background-scheduler cost issue — reported, root-caused, status unknown

Earlier this engagement the user reported Railway usage spiking despite not
touching the app in weeks, and asked to pause all Railway activity. Root
cause found in the backend code: `app/main.py`'s `lifespan` starts an
APScheduler loop unconditionally on boot, independent of user traffic, which
runs headless-Chromium (Playwright) marketplace scrapes as often as **every
1 minute** (other jobs at 15min/30min/1h/6h) for as long as any event stays
tracked/active in the DB. **No env-var kill switch exists for this.**

Whether the user has since paused this in the Railway dashboard is
**unknown** — never confirmed in this session. Don't assume it's handled.
A `POLLING_ENABLED` env-gated flag around `start_scheduler()` would be a
good small fix if the user wants the service to stay up for reads without
the scraping loop — not built yet.

---

## 5. Lower-priority open items (not investigated this pass, carried from earlier)

These came from work on the stale `claude/concert-watchlist-tracker-Uia95`
branch and were never checked against `main` — may or may not still apply:

- **Seller Behavior panel:** that branch had a frontend/backend field-name
  mismatch (frontend expected `old_price`/`new_price`/`score`; backend's
  `intelligence_engine.py` actually sends `first_price_24h`/`current_price`/
  `delta_pct`/`aggression_ratio`), which made the Was/Now columns render
  blank. Worth checking whether `main` has the same class of bug.
- **Pin/unpin:** that branch had a bug where the "selected headline" was
  wired through the card's full-surface `<Link>`, so every click navigated
  away instead of un-selecting. Unverified whether `main` has this too.
- `main` already has real marketplace logo image assets
  (`frontend/public/logos/`) — better than anything built on the side
  branch, no action needed there.

---

## 6. First steps for whoever picks this up next

1. **Do not assume the live app works or Railway is paused** — both
   unknown, see §3/§4.
2. If asked to fix Vercel: the fix is fully diagrammed in §2 — scaffold
   files are recovered and build-verified, just need pushing + the one
   dashboard setting change. Don't re-derive this from scratch.
3. If asked about Railway cost: point to §4, ask the user current status
   before touching anything scheduler-related.
4. Treat `main` as canonical. Don't touch `claude/concert-watchlist-tracker-Uia95`
   except to reference §5's two open findings.
5. Keep this file current — update it before you, too, go dormant.
