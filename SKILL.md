---
name: frametax-build-discipline
description: Use this skill ANY time work touches the FrameTax film production incentive analyzer (also referenced as TaxFrame or ReelIncentive in earlier sessions) — including modifying the JSX source, rebuilding the bundle, adding features, fixing rendering issues, working with the Library/save system, the script-based location filter, the budget benchmark database, or the live incentive scan. Trigger this skill whenever the user mentions FrameTax, the film tax app, "the incentive app," budget parsing for productions, co-production treaty stacking, or asks for changes to any of: territory cards, compare mode, treaty optimizer, library/save, qualification gaps, BTL rebasing, or true net cost. This skill encodes hard-won lessons from many failed iterations — DO NOT skip it even if the change "looks small," because the rendering pipeline, JSX constraints, and feature-completeness rules are non-obvious and small deviations have repeatedly broken the entire app.
---

# FrameTax Build Discipline

This skill exists because the same classes of error keep recurring on this project. Read it fully before touching any FrameTax file. Skip nothing.

The producer using this app is making real financing decisions on real films. Sloppy output (wrong rates, broken renders, half-built features that demo well but lose data) has direct downstream cost. Defaults that are fine for prototypes are not fine here.

---

## 1. The Rendering Pipeline Is Not Negotiable

FrameTax has one stable rendering path. Every other path has been tried and has failed. Do not improvise.

**Canonical build:**
- Source: `/mnt/user-data/outputs/FrameTax.jsx` (~100KB JSX)
- Bundler: esbuild at `/home/claude/.npm-global/lib/node_modules/tsx/node_modules/esbuild/bin/esbuild`
- Command: `esbuild FrameTax.jsx --bundle --format=iife --jsx=transform --jsx-factory=React.createElement --jsx-fragment=React.Fragment --minify --outfile=FrameTax_v2.js`
- Output: ~268KB self-contained IIFE bundle, no runtime module resolution, React inlined
- Deployable: `/mnt/user-data/outputs/FrameTax.html` wraps the bundle

**Things that have repeatedly failed and must not be tried again:**
- In-browser Babel transpilation — fails on files this size
- `--external:react` — breaks at runtime, no module loader present
- Any non-IIFE format — same issue
- CDN-loaded React with module imports inside the JSX — fails to resolve

If a session is "starting fresh" and the canonical files do not exist, rebuild from this exact command. Do not propose a different bundler.

---

## 2. JSX Source Constraints (Verified by Audit Script)

The source JSX must satisfy these constraints. They are non-obvious. Violating any one of them silently breaks compilation:

- **Zero backticks** in the source. Template literals must use string concatenation. (Backticks have repeatedly collided with embedded prompt strings and broken the bundle.)
- **Zero non-ASCII characters.** No smart quotes, em dashes, ellipses, accented letters, emoji. Use ASCII equivalents. Run a `grep -P '[^\x00-\x7F]'` audit before bundling.
- **Zero SVG elements.** Use Unicode glyphs or CSS-drawn shapes. SVG has broken JSX parsing in this codebase before — root cause never fully isolated, but the rule stands.
- **Zero HTML entities** (`&amp;`, `&nbsp;`, etc.). Use the literal characters in JS strings, escape in JSX text only when required.
- **No inline IIFE patterns** like `{(function(){...})()}` inside JSX. Hoist to a named function and call it.

After every meaningful edit, run the audit:
```bash
python3 -c "
import re
with open('/mnt/user-data/outputs/FrameTax.jsx') as f: c = f.read()
issues = []
for i, line in enumerate(c.split('\n'), 1):
    if '`' in line: issues.append(f'L{i}: backtick')
    if re.search(r'[^\x00-\x7F]', line): issues.append(f'L{i}: non-ASCII')
    if '<svg' in line.lower(): issues.append(f'L{i}: SVG')
    if re.search(r'&[a-z]+;', line): issues.append(f'L{i}: HTML entity')
print('CLEAN' if not issues else '\n'.join(issues[:20]))
"
```
If the audit fails, fix before bundling. Do not bundle and hope.

---

## 3. The "Looks Built But Isn't" Failure Mode

This is the single most common error pattern on this project. Features get scoped, demoed, and forgotten without ever being fully wired. When asked to add or modify a feature, ALWAYS check the actual current state of these areas before claiming anything is done:

| Feature | Common half-built state |
|---|---|
| **Library / Save** | Saves inputs only, not the analysis snapshot. Reload re-runs AI from scratch and results drift. |
| **Script-based location exclusion** | `wouldNotWorkIn` array is extracted but only injected as a soft prompt instruction. AI ignores it ~30% of the time. Should be a deterministic pre-filter. |
| **Cultural test scoring** | LLM-narrated, not deterministic. The tests (BFI, Screen Australia, CNC, etc.) are rule-based and should be coded as functions, not described to the model. |
| **Source citations** | Schema asks for `sourceUrl`/`lastVerified` per rate, UI doesn't display them on every number. |
| **FX rates** | Model is told "use current rates" — there is no FX API wired. Numbers are guessed within a few percent. |
| **Confidence tiers** | Discussed, not built. Every number reads as equally confident. |
| **Cross-budget benchmark database** | Discussed at length, never built. Per-budget BTL rebasing exists; cross-project rate aggregation does not. |
| **Tax credit monetization (transferables at ~88¢)** | Mentioned, never built. |

**Rule:** Before saying "I'll add X" or "X already exists," grep the source. If a feature spans multiple files or the artifact storage API, verify the full path: input → state → storage → reload → render. Half-paths are the default failure mode.

---

## 4. Live Incentive Data: What's Real, What's Not

The current "live scan" step in the analysis flow runs ONE web search via the Anthropic API and asks the model to summarize current incentive data. This is better than pure training data but worse than a real data layer. Be honest about it.

**When discussing accuracy with the user:**
- Do not say "real-time data" without qualification. Say "live web search at analysis time, single pass, no source verification."
- Always flag that grants and soft money are *discretionary* and *probabilistic*. Do not promise them as if they were tax credits.
- If the user asks for a specific rate, the source URL and last verification date should be surfaced, not the rate alone.

**The intended architecture (not yet built):**
- Curated baseline JSON of ~120 programs, refreshed weekly
- Targeted live verification of top-5 destinations against official film commission sources at analysis time
- Authority hierarchy: film commission > government tax authority > Screen Daily / Variety > consultancy reports > training data

If asked to "improve real-time data," propose this architecture, do not just tweak the existing single-search prompt.

---

## 5. Browser-Side API Key Is a Known Risk

The current architecture calls the Anthropic API directly from the React client. This works in the development environment but exposes the API key. This is fine for personal use only. If the user mentions sharing, deploying, or shipping the app:

- Flag the risk explicitly. Don't bury it.
- Recommend a thin proxy (Cloudflare Worker, Vercel edge function, Lambda) that holds the key server-side.
- Estimate ~30 lines of proxy code. Do not propose rebuilding the client.

Do not silently ship a version that exposes the key to a user who said "deploy."

---

## 6. Budgets Are Real Documents — Treat Them That Way

When parsing budgets:

- **ATL vs BTL classification is contract-dependent.** Producer fees in particular can be ATL (default) or BTL (if structured as a producing services agreement with a day/weekly rate and on-the-ground presence). Do not auto-assume. When ambiguous, surface the ambiguity in the UI as an override toggle.
- **Real productions are the test cases.** Past sessions used *All My Friends Are Dead* and *Bad Hombres*. New work should be validated against actual budget files when possible, not synthetic samples.
- **Movie Magic (.mbd) and EP Budgeting** are the two formats producers actually use. PDF parsing is fragile fallback. If the user provides Excel/CSV exports from these tools, prefer those over PDFs.

---

## 7. The Producer's Mindset

The user is a film producer, not a developer. When they flag an issue, default to:

- **Ask "what specifically isn't working?"** before assuming. Sometimes the issue is a render bug, sometimes it's an accuracy bug, sometimes it's a feature that was never built. Conflating these wastes the session.
- **Show the actual numbers.** "Saved" or "Done" without showing what was saved is not useful. Echo the data.
- **Don't be agreeable.** This producer has explicitly said: "I want a partner. Not a sycophant." If a request is unwise (promising a discretionary grant as if guaranteed, exposing an API key on deploy, building a feature that overlaps with EP's existing free tool), say so directly with reasoning. The producer can override; they cannot override what they don't see.

---

## 8. When in Doubt, Audit the Conversation History

This project has a long history across multiple sessions. Before assuming a feature exists or doesn't, search the past chats:
- `conversation_search` with terms like "library save," "script exclusion," "cultural test," "FX rate," "benchmark database"
- Look for the pattern: discussed → designed → partially built → forgotten

The audit pattern is more reliable than memory. Memory in this project has a recency bias and frequently misses mid-iteration features.

---

## 9. Output Format

When delivering FrameTax work:

- The deliverable is `/mnt/user-data/outputs/FrameTax.html` (the rendered, deployable file). Always use `present_files` with this path.
- Also surface `/mnt/user-data/outputs/FrameTax.jsx` (the source) so the user can fork or hand off the codebase.
- After the bundle, run a sanity check: `print(f"HTML: {len(html):,} chars"); print("Has mount:", 'getElementById' in html); print("No require:", 'require(' not in bundle)`. If any of these fail, do not present the file — fix and rebuild.
- Do not write extensive postambles describing the work. This producer reads the deliverable directly. A two-to-four sentence summary of what changed is sufficient.

---

## 10. Things That Are Not Bugs

To avoid wasted iteration, these are intentional and should not be "fixed" without explicit user request:

- The cinematic dark/gold aesthetic. It's the chosen brand.
- The hero → upload → Q&A → analyze → results flow. Producer-tested.
- The Q&A length (~12 questions). Adding more increases drop-off.
- The IMDb attachment scan running automatically. It enriches the analysis even when the budget is clean.

---

End of skill. The point of this document is that every line in it represents a previous mistake on this project. Re-reading takes 90 seconds and avoids burning a full session on a known failure mode.
