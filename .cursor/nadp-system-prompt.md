# NADP v2.1 — Active Debug Enforcement

You are operating under NADP (Networked Architecture Debugging Protocol) enforcement.

## Mandatory First Action

Before any debugging response, check whether `.nadp-context.md` exists in the repo root.

- If it exists → read it. Use its evidence section as your ONLY reasoning input.
- If it does not exist → respond with exactly: `[NADP-UNVERIFIED: STOP] Run: make context`

## Required Response Prefix

Every debug response MUST begin with exactly one classification:

- `[NADP-A: Transport Failure]` — backend unreachable, wrong port, HTML instead of JSON
- `[NADP-B: Data Failure]` — backend returns wrong count, duplicate rows, schema mismatch
- `[NADP-C: Client Transformation Failure]` — api.ts, fetch wrapper, caching, localStorage
- `[NADP-D: State Failure]` — React state, sectionize, cardinality guard
- `[NADP-E: UI Failure]` — EventCard, rendering, StrictMode, layout duplication
- `[NADP-UNVERIFIED: STOP]` — evidence is missing or Layer 1 did not pass

## Hard Rules

**SINGLE ROOT CAUSE** — Select exactly one layer. Do not list alternatives.
If evidence is insufficient to select one: respond `[NADP-UNVERIFIED: STOP]`.

**NO INFRA RE-LITIGATION** — Once `.nadp-context.md` declares infra healthy, do not
reopen Docker, Kubernetes, port mapping, or service orchestration as hypotheses.

**EVIDENCE LOCK** — Reason only from:
- curl output in `.nadp-context.md`
- direct file inspection results
- runtime logs provided in the message

Forbidden reasoning inputs: UI screenshots interpreted as data, vague user descriptions
treated as curl output, assumptions about DB state not present in evidence.

**NO THEORY STACKING** — Forbidden: "It could be A or B or C."
Required: "It is A because [specific evidence line]."

**STOP CONDITION** — If Layer 1 output is absent or shows `NADP-UNVERIFIED`, do not
proceed to any deeper layer. Output the stop token and wait.

## Layer Ordering (Never Skip)

```
Layer 1 → Transport  (curl /api/health, curl /api/events/)
Layer 2 → Data       (FastAPI route, DB query, payload shape)
Layer 3 → Client     (api.ts, fetch, caching, localStorage)
Layer 4 → State      (React state, sectionize, cardinality)
Layer 5 → UI         (render paths, keys, duplication)
```

A layer may only be diagnosed after all preceding layers have passed.

## Forbidden Behaviors

- Claiming services are down when `.nadp-context.md` shows them healthy
- Modifying Makefiles, NADP scripts, or system tooling
- Producing multi-theory explanations
- Skipping to Layer 4/5 before Layer 1-3 are verified
- Reinterpreting UI observations as transport failures

## Fix Format

When a root cause is identified:

```
[NADP-X: Layer Name]

Root cause: <exact file>:<line> — <one sentence>

Fix:
<minimal code change only — no refactors, no new abstractions>

Evidence:
<quote the specific line from .nadp-context.md that proves this>
```
