"""
app.bridge — the Cross-Model Bridge.

Internal development infrastructure connecting CineGlobe's optimizer,
qualification, QPE, requirements, and treaty/co-production outputs to
independent research/audit by Anthropic, OpenAI, and Gemini. This is
NOT a producer-facing feature: no route here is wired into the served
frontend, and no disposition from this module can mutate optimizer
rules, requirements profiles, or production data automatically — every
accepted change becomes an explicit implementation task a human (or a
future targeted commit) still has to make.

Module map:
  config.py            — provider settings, model aliases (pydantic-settings)
  secrets.py            — provider status resolution, key redaction helpers
  schema.py              — canonical dataclasses: requests, packages, responses, findings
  redaction.py           — outbound content preview/redaction/confidentiality gating
  persistence.py         — dedicated local SQLite store, append-only
  package_builder.py     — deterministic AuditPackage construction from served data
  reconciliation.py      — cross-provider comparison, human-gated dispositions
  requirements_workflow.py — the Objective 9 research-to-profile workflow
  provenance.py           — per-program rule-provenance matrix
  ledger.py                — canonical project ledger + decision register
  adapters/               — one native client per provider, one shared interface
  cli.py                   — click-based internal CLI
  api.py                   — FastAPI router, mounted but NOT linked from the producer UI
"""
