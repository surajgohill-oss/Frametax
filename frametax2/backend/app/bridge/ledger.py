"""
Canonical project ledger + decision register (spec section 5).

seed_ledger() populates ONLY from established project evidence — every
entry below was verified during this engagement (test counts, runtime
checks, direct code reads), not asserted from memory. Re-running
seed_ledger() is idempotent per entry_id (a re-seed with the same
entry_id content is a no-op; a changed one is appended as a new row
with the same entry_id, and query functions return the latest row per
entry_id — append-only, never an UPDATE).
"""
from __future__ import annotations

from app.bridge.persistence import LedgerEntryRecord, get_session
from app.bridge.schema import LedgerEntry, LedgerStatus, new_id

PERMANENT_DOCTRINES: list[tuple[str, str]] = [
    ("doctrine-canonical-qpe-rule",
     "Every budget line is included in QPE unless authoritative law, regulation, or "
     "government guidance expressly excludes it."),
    ("doctrine-no-inferred-exclusions",
     "Silence, industry custom, conservatism, or engineering interpretation are not "
     "exclusions."),
    ("doctrine-finance-cost-default-zero",
     "Finance costs default to zero unless entered."),
    ("doctrine-refund-transfer-distinct",
     "Refundability and transferability are distinct and explicitly surfaced."),
    ("doctrine-local-entities-considered",
     "Local production entities are considered where legally permissible."),
    ("doctrine-ranking-lowest-npc",
     "Ranking targets lowest defensible net production cost."),
    ("doctrine-no-synthetic-risk-scores",
     "Synthetic risk scores are not ranking inputs."),
    ("doctrine-difficulty-via-disclosure",
     "Difficulty is surfaced through gates, dependencies, unknowns, and operational "
     "disclosures."),
    ("doctrine-canonical-structure-families",
     "Single-country, relocation, component, split, treaty, co-production, hybrid, "
     "majority/minority, multi-party, anchor-component, reinvestment, in-kind, "
     "grant/fund, and stacking pathways belong to the canonical product."),
    ("doctrine-suggestion-vs-accepted-vs-active",
     "App suggestions, accepted scenario changes, and the active production plan are "
     "distinct states."),
    # Established this session, already enforced in code — included because it is
    # exactly as permanent as the ten above and governs the Bridge itself.
    ("doctrine-no-automatic-rule-mutation",
     "No AI model output, consensus, or reconciliation disposition may automatically "
     "alter legal rules, requirements profiles, qualification, QPE, optimizer ranking, "
     "or production data. Every accepted change produces an explicit implementation "
     "task; only a human-identified actor (never 'system'/'auto') may accept one."),
]


def _milestone(entry_id: str, title: str, description: str, status: LedgerStatus, provenance: str) -> LedgerEntry:
    return LedgerEntry(entry_id=entry_id, kind="milestone", title=title, description=description,
                        status=status, provenance=provenance)


def _seed_entries() -> list[LedgerEntry]:
    entries: list[LedgerEntry] = []

    for entry_id, text in PERMANENT_DOCTRINES:
        entries.append(LedgerEntry(
            entry_id=entry_id, kind="doctrine", title=text[:80], description=text,
            status=LedgerStatus.ACTIVE_IN_SERVED_PIPELINE,
            provenance="Cross-Model Bridge spec, section 5 (permanent doctrines list); "
                       "already enforced in the served pipeline prior to this tranche.",
        ))

    entries += [
        _milestone(
            "milestone-canonical-executable-registry",
            "Canonical executable jurisdiction registry",
            "app/data/canonical_executable_registry.py — one authoritative accounting "
            "of the 110 executable jurisdictions, reconciling jurisdiction_comparison."
            "ALL_PROFILES with executable_jurisdiction_registry._REGISTRY (6 legacy "
            "jurisdictions MU/GR/IE/MT/ES/FR + 2 secondary program slugs surfaced). "
            "16 regression tests, 0 optimizer behavior change.",
            LedgerStatus.RUNTIME_VERIFIED,
            "Backend-completion tranche this session; verified via "
            "test_canonical_executable_registry.py (16/16 passing) and cross-checked "
            "against production_validation_harness.py's own total_executable_jurisdictions.",
        ),
        _milestone(
            "milestone-production-requirements-db",
            "Production Requirements Database",
            "app/data/program_requirements.py — structured per-program requirements "
            "profiles (application timing, preapproval, audit, refundability, "
            "transferability, caps, evidence). 17 of 110 executable programs "
            "populated as of this session's end. Served in the /structures API "
            "payload and rendered in Inspector.jsx (Task 93).",
            LedgerStatus.PARTIAL,
            "17/110 populated, verified via test_program_requirements.py; the "
            "remaining 93 are the Bridge's own primary intended workload "
            "(spec section 9).",
        ),
        _milestone(
            "milestone-contingency-treatment",
            "First-class contingency treatment",
            "app/calculators/contingency_treatment.py — undeployed contingency "
            "excluded from QPE by default (new STRUCTURAL_DEFINITION ladder step), "
            "deployed amounts inherit the destination line's own eligibility "
            "treatment. No blanket qualify-contingency switch. Mauritius baseline "
            "unaffected (explicit program-specific rule unchanged).",
            LedgerStatus.RUNTIME_VERIFIED,
            "27 tests in test_contingency_treatment.py; live-curled deploy/reset "
            "round trip verified against the served API this session.",
        ),
        _milestone(
            "milestone-structure-family-validation",
            "Structure-family validation with controlled inputs",
            "Controlled-input pricing tests across treaty_coproduction (real CA-FR "
            "treaty pair), hybrid/majority_minority/multi_party ownership-share "
            "validation, full_relocation. No discrepancies found.",
            LedgerStatus.RUNTIME_VERIFIED,
            "test_structure_family_validation.py, 6/6 passing.",
        ),
        _milestone(
            "milestone-pipeline-validation-sweep",
            "Full-sweep conditional/capability-only pipeline validation",
            "Every served structure's conditional-program entries verified to never "
            "enter NPC; every one of ~134 conditional nodes verified for catalog "
            "integrity; capability-only jurisdiction classification verified "
            "consistent with discovery metrics. No discrepancies found.",
            LedgerStatus.RUNTIME_VERIFIED,
            "test_pipeline_validation_sweep.py, 9/9 passing.",
        ),
        _milestone(
            "milestone-cyprus-stale-blocker-defect",
            "Cyprus stale-blocker defect — root-caused and fixed",
            "Root cause: a long-lived backend process (started before the CY rate-"
            "rule fix, no --reload) was serving pre-fix code on the port the "
            "frontend's .env actually targets; NOT a code defect. Fixed by killing "
            "stale processes and restarting on the correct port. Regression test "
            "added asserting no served structure ever contradicts the doctrine "
            "registry's own classification.",
            LedgerStatus.RUNTIME_VERIFIED,
            "TestServedBlockersNeverContradictTheDoctrineRegistry, 2/2 passing; "
            "confirmed live via curl against the corrected port.",
        ),
        _milestone(
            "milestone-cross-model-bridge",
            "Cross-Model Bridge (this tranche)",
            "Provider-neutral adapter interface + native Anthropic/OpenAI/Gemini "
            "adapters, canonical audit-package + structured-response schema, SQLite "
            "persistence, reconciliation layer (no auto-mutation), requirements-"
            "research workflow, rule-provenance matrix, this ledger, CLI + internal "
            "API. No provider API key is configured in this environment — live "
            "provider calls could not be completed; everything else is built and "
            "tested with mocked transport.",
            LedgerStatus.STATIC_VERIFIED,
            "This session. See final report for exact test counts and the honest "
            "disclosure of what runtime verification could and could not cover.",
        ),
    ]

    entries.append(LedgerEntry(
        entry_id="backlog-requirements-profiles",
        kind="backlog_item",
        title="93 executable jurisdictions without a structured requirements profile",
        description="Live count: call canonical_executable_registry."
                     "executable_jurisdictions_without_requirements_profile() — this "
                     "entry's number is a snapshot as of ledger seed time, not "
                     "re-verified on every read.",
        status=LedgerStatus.NOT_IMPLEMENTED,
        provenance="Established this session via the canonical registry; the Bridge's "
                   "requirements-research workflow (Objective 9) is the intended path "
                   "to closing it, gated by explicit human acceptance per profile.",
    ))

    entries.append(LedgerEntry(
        entry_id="phase-current",
        kind="phase",
        title="Current phase: backend knowledge-completion + Cross-Model Bridge",
        description="Optimizer, allocation, qualification, contingency, and canonical "
                    "registry are runtime-verified. Requirements-profile coverage "
                    "(17/110) is the open knowledge-base backlog. The Bridge is built "
                    "but has never completed a live three-provider call (no API keys "
                    "configured in this environment).",
        status=LedgerStatus.ACTIVE_IN_SERVED_PIPELINE,
        provenance="This session's own verified state at hand-off.",
    ))
    entries.append(LedgerEntry(
        entry_id="phase-next-authorized",
        kind="phase",
        title="Authorized next phase: requirements-profile batches via the Bridge",
        description="Once provider API keys are configured, use the Bridge's "
                    "requirements-research workflow to research and (with explicit "
                    "human acceptance) populate remaining profiles in small batches, "
                    "same discipline as the 5-profile batches already done manually "
                    "this session. Globe/UI work is explicitly out of scope until "
                    "this backend tranche is substantially complete, per the user's "
                    "own instruction.",
        status=LedgerStatus.DEFERRED,
        provenance="User's Cross-Model Bridge spec, 'OUT OF SCOPE' and final-report "
                   "sections.",
    ))

    return entries


def seed_ledger(session=None) -> int:
    """Idempotent per (entry_id, description) pair — re-seeding with
    unchanged content inserts nothing new. Returns the number of NEW
    rows written."""
    own_session = session is None
    session = session or get_session()
    written = 0
    try:
        for entry in _seed_entries():
            existing = (
                session.query(LedgerEntryRecord)
                .filter(LedgerEntryRecord.entry_id == entry.entry_id)
                .order_by(LedgerEntryRecord.created_at.desc())
                .first()
            )
            if existing is not None:
                import json as _json
                if _json.loads(existing.entry_json).get("description") == entry.description:
                    continue
            session.add(LedgerEntryRecord(
                row_id=new_id("ledgerrow"), entry_id=entry.entry_id, kind=entry.kind,
                title=entry.title, entry_json=entry.model_dump_json(),
            ))
            written += 1
        session.commit()
    finally:
        if own_session:
            session.close()
    return written


def current_ledger(session=None) -> list[LedgerEntry]:
    """Latest row per entry_id — SUPERSEDED history stays in the table
    (append-only) but is not returned here unless include_superseded=True
    would be added later; this session's ledger has no superseded rows yet."""
    own_session = session is None
    session = session or get_session()
    try:
        rows = session.query(LedgerEntryRecord).order_by(LedgerEntryRecord.created_at.asc()).all()
        latest_by_id: dict[str, LedgerEntryRecord] = {}
        for row in rows:
            latest_by_id[row.entry_id] = row  # later rows overwrite earlier ones
        return [LedgerEntry.model_validate_json(row.entry_json) for row in latest_by_id.values()]
    finally:
        if own_session:
            session.close()
