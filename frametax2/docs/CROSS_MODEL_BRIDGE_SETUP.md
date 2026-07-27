# Cross-Model Bridge — Setup (macOS / zsh)

Internal development infrastructure only. Not producer-facing. See
`backend/app/bridge/` for the implementation and `backend/.env.example`
for the full list of variables.

## 1. Where to create each provider key

- **Anthropic**: https://console.anthropic.com/settings/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Gemini**: https://aistudio.google.com/app/apikey

## 2. Required environment variable names

```
ANTHROPIC_API_KEY
OPENAI_API_KEY
GEMINI_API_KEY        # or GOOGLE_API_KEY as a Gemini-compatible alias
```

## 3. Local `.env` placement

Copy the template and fill in real values — never commit the result:

```bash
cd backend
cp .env.example .env
```

Then edit `backend/.env` and set the keys. `backend/.env` is already
listed in `.gitignore` (confirmed: `.env` and `*.db` are both ignored
repo-wide), so a normal `git status`/`git add` will not pick it up. The
Bridge's own SQLite file (`.bridge_data/bridge.db` by default) is also
gitignored via the `*.db` pattern.

## 4. Deployment-secret placement

Set the same three (or four, with `GOOGLE_API_KEY`) variables through
your deployment platform's secret manager (e.g. environment variables
on the host, or a managed secrets store) — never in a committed file.
`BridgeSettings` (pydantic-settings) reads from the process environment
the same way whether the value came from `.env` locally or from a
platform-injected environment variable in deployment; no code change is
needed between the two.

## 5. How to verify provider status

```bash
cd backend
source .venv/bin/activate
python -m app.bridge.cli provider-status
```

Prints `configured` / `not_configured` / `disabled` per provider —
never prints a key value, even redacted.

Or via the internal API (server must be running):

```bash
curl -s http://localhost:8010/api/v1/bridge/providers | python3 -m json.tool
```

## 6. How to run a three-provider audit

```bash
cd backend
source .venv/bin/activate

# 1. Build a real audit package from the served pipeline
python -m app.bridge.cli create-package --operation qualification_audit

# 2. Preview exactly what would be sent (dry run, no network call)
python -m app.bridge.cli preview-package <package_id>

# 3. Dispatch to every configured provider independently
python -m app.bridge.cli dispatch <package_id> --operation qualification_audit
```

Omit `--provider` to dispatch to every CONFIGURED provider; pass
`--provider anthropic --provider openai` (repeatable) to target specific
ones. A provider with no key configured is reported as
`not dispatched — not configured`, never silently skipped and never
fabricated as a successful call.

## 7. How to launch a requirements research run

```python
# python -m asyncio or a script — dispatch_research is async
from app.bridge.requirements_workflow import (
    select_missing_programs, dispatch_research, parse_candidate_response,
    compare_candidate_facts, draft_profile, accept_profile,
)
from app.bridge.schema import ProviderID

targets = select_missing_programs(limit=3)
target = targets[0]
responses = await dispatch_research(target, [
    (ProviderID.ANTHROPIC, "claude-sonnet-4-5"),
    (ProviderID.OPENAI, "gpt-5.1-mini"),
])
candidates = [c for r in responses if (c := parse_candidate_response(r, "pkg_x")) is not None]
comparisons = compare_candidate_facts(candidates)
draft = draft_profile(target, comparisons)
# accept_profile REQUIRES a real human/session identity and writes to
# the live program_requirements.py registry — review draft.fields,
# draft.conflicted_fields, and draft.hard_gates_unknown before calling it.
profile = accept_profile(draft, accepted_by="your-name-or-session-id")
```

Or list what's missing first:

```bash
python -m app.bridge.cli missing-requirements --limit 10
```

## 8. How to review usage

```bash
curl -s "http://localhost:8010/api/v1/bridge/usage?limit=50" | python3 -m json.tool
```

Every dispatched request (successful or failed) is recorded in the
`bridge_provider_responses` table with provider, model, token usage,
latency, and error category — append-only, never overwritten.

## 9. How to disable a provider

Set the corresponding flag to `false` in `backend/.env` (or the
deployment environment) and restart the backend:

```
BRIDGE_ANTHROPIC_ENABLED=false
```

`provider-status` will then report `disabled` for that provider even if
its key is still present — the key is never read for a disabled
provider.

## 10. How to rotate a key

1. Generate a new key from the provider's console (links in section 1).
2. Update `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` in
   `backend/.env` (local) or your deployment secret manager (production).
3. Restart the backend process — `BridgeSettings` is read once per
   process (cached via `get_bridge_settings()`); a running process does
   not pick up an env change without a restart.
4. Revoke the old key in the provider's console once you've confirmed
   `provider-status` shows `configured` with the new key working.

## 11. How to confirm no key was committed

Run from the repository root (one level above `frametax2/` — confirm
with `git rev-parse --show-toplevel` first if unsure):

```bash
git rev-parse --show-toplevel
git check-ignore -v frametax2/backend/.env frametax2/backend/.bridge_data/bridge.db
git status --short frametax2/backend/.env frametax2/backend/.bridge_data/
git log --all --full-history -- frametax2/backend/.env
```

`check-ignore` should print a match for both paths against
`frametax2/.gitignore`'s `.env` and `*.db` patterns (confirmed this
session: `frametax2/.gitignore:4:.env` and `frametax2/.gitignore:11:*.db`).
`git status --short` should print nothing (gitignored paths never show
as untracked/staged). `git log` should print no commits — `.env` has
never been tracked. If any of these shows something unexpected, treat
it as a real incident: rotate every key that may have been exposed
before doing anything else.
