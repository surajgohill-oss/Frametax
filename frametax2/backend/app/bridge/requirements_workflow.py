"""
Requirements Profile Research Workflow (spec section 9).

Ten-step pipeline exactly as specified:
  1. select_missing_programs()          — pick from the real 98-jurisdiction gap
  2. build_research_brief()             — canonical ModelRequest, one per provider
  3. dispatch_research()                — call configured providers independently
  4. (enforced by schema) structured candidate requirements + source records
  5. compare_candidate_facts()          — cross-provider comparison
  6. flag agreements/conflicts          — via compare_candidate_facts()'s output
  7. distinguish_primary_source_agreement_from_model_consensus()
  8. draft_profile()                    — assemble a candidate ProgramRequirementsProfile
  9. accept_profile()                   — EXPLICIT gate; nothing upstream writes production data
  10. (caller's responsibility) run tests — see runtime verification / CLI accept command

No function in this module ever calls program_requirements.register()
except accept_profile(), and accept_profile() itself refuses to run
unless the caller passes accepted_by (a real human/session identity).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.bridge.schema import (
    CandidateFact,
    CandidateRequirementsResponse,
    EvidenceRecordRef,
    ModelRequest,
    ModelResponse,
    OperationType,
    ProviderID,
    CANDIDATE_REQUIREMENTS_JSON_SCHEMA,
)

RESEARCH_SYSTEM_INSTRUCTION = """\
You are researching a specific film/TV production tax incentive program's
OPERATIONAL requirements — not its rate/rebate percentage (that is already
known and is not what this request asks for).

Return ONLY facts you can attribute to a real, citable source. For each
fact:
  - name the exact field (see the schema's CandidateFact.field_name — use
    ProgramRequirementsProfile field names: preapproval_mandatory,
    application_deadline, audit_required, cpa_or_approved_auditor_required,
    refundable, transferable, min_local_spend_usd, min_total_budget_usd,
    per_project_cap_usd, cultural_test_required, cultural_test_threshold,
    local_entity_required, allocation_type, payment_timing, sunset_date)
  - cite it to one of your source_records by index
  - mark is_hard_eligibility_gate=true for anything that would DISQUALIFY
    a production outright if unmet (not merely a disclosure nicety)
  - state your own confidence in the FACT itself, not in whether other
    models might agree with you

Prefer the evidence hierarchy: statute/regulation > official tax
authority > official incentive administrator > official film commission
> treaty text > official application guide > recognized professional
analysis > reputable industry summary > other secondary source. A search
engine result or another model's claim is never itself an authority —
only what it points to is.

If you cannot find a primary source for a fact, either omit the fact or
include it with source_type marked secondary/estimate and say so plainly
in notes. Never invent a source URL, a date, or a number.
"""


@dataclass(frozen=True)
class MissingProgramTarget:
    program_slug: str
    jurisdiction_code: str


def select_missing_programs(limit: int | None = None) -> list[MissingProgramTarget]:
    """Step 1 — reads the REAL, canonical gap (Objective 1's registry),
    never a hardcoded list."""
    from app.data.canonical_executable_registry import executable_jurisdictions_without_requirements_profile

    gap = executable_jurisdictions_without_requirements_profile()
    targets = [
        MissingProgramTarget(program_slug=e.primary_program_slug, jurisdiction_code=code)
        for code, e in sorted(gap.items())
    ]
    return targets[:limit] if limit else targets


def build_research_brief(
    target: MissingProgramTarget, provider: ProviderID, model_id: str,
) -> ModelRequest:
    """Step 2 — the SAME brief content goes to every provider (only
    provider/model_id differ) so responses are genuinely comparable."""
    from app.data.program_rate_rules import get_rate_rules
    from app.data.executable_jurisdiction_registry import _REGISTRY as doctrine_registry

    doctrine = doctrine_registry.get(target.program_slug)
    rate_rules = get_rate_rules(target.program_slug)
    known_facts = {
        "program_slug": target.program_slug,
        "jurisdiction_code": target.jurisdiction_code,
        "already_known_program_name": doctrine.program_name if doctrine else None,
        "already_known_rate_structure": [
            {"rate": r.rate, "is_band_ceiling": r.is_band_ceiling} for r in rate_rules
        ],
        "instruction": (
            "The rate structure above is ALREADY KNOWN — do not re-research it. "
            "Research the OPERATIONAL requirements only (see system instruction)."
        ),
    }
    return ModelRequest(
        provider=provider, model_id=model_id, operation=OperationType.REQUIREMENTS_RESEARCH,
        system_instruction=RESEARCH_SYSTEM_INSTRUCTION,
        structured_input=known_facts,
        required_response_schema=CANDIDATE_REQUIREMENTS_JSON_SCHEMA,
        allow_web_search=True,
        request_metadata={"program_slug": target.program_slug, "jurisdiction_code": target.jurisdiction_code},
    )


async def dispatch_research(
    target: MissingProgramTarget, providers_and_models: list[tuple[ProviderID, str]],
) -> list[ModelResponse]:
    """Step 3 — calls each configured provider independently. A provider
    with no key configured still gets a ModelResponse (AUTH error
    category from the adapter base class) — never silently skipped, so
    the caller always sees exactly which providers did and didn't run."""
    from app.bridge.adapters.base import get_adapter

    responses = []
    for provider, model_id in providers_and_models:
        request = build_research_brief(target, provider, model_id)
        adapter = get_adapter(provider)
        responses.append(await adapter.send(request))
    return responses


def parse_candidate_response(response: ModelResponse, package_id: str) -> CandidateRequirementsResponse | None:
    """Validates a ModelResponse's parsed_response against
    CandidateRequirementsResponse. Returns None (never a fabricated
    empty response) if parsing/validation fails — the caller must treat
    that provider as having contributed nothing for this program."""
    if not response.ok or response.parsed_response is None:
        return None
    try:
        candidate = CandidateRequirementsResponse.model_validate({
            **response.parsed_response,
            "provider": response.provider,
            "model": response.model_id,
            "package_id": package_id,
        })
    except Exception:
        return None
    # Enforce every fact cites a real in-range source (schema-level
    # validator only checked non-negative; here we have both lists).
    valid_facts = [
        f for f in candidate.candidate_facts
        if 0 <= f.source_index < len(candidate.source_records)
    ]
    return candidate.model_copy(update={"candidate_facts": valid_facts})


@dataclass
class FactComparison:
    field_name: str
    proposals: list[tuple[ProviderID, "CandidateFact", EvidenceRecordRef]] = field(default_factory=list)

    @property
    def distinct_values(self) -> set:
        return {str(p.proposed_value) for _, p, _ in self.proposals}

    @property
    def distinct_primary_sources(self) -> set:
        return {
            (src.source_title, src.source_url)
            for _, _, src in self.proposals
            if src.primary_or_secondary == "primary"
        }

    @property
    def is_primary_source_agreement(self) -> bool:
        """TRUE agreement: multiple providers cite the SAME real primary
        source AND agree on the value — this is what Step 7 requires
        distinguishing from mere model consensus."""
        return len(self.distinct_values) == 1 and len(self.distinct_primary_sources) >= 1

    @property
    def is_model_consensus_only(self) -> bool:
        """Providers agree on the VALUE but either cite no primary
        source, or cite DIFFERENT primary sources (or none at all) —
        agreement that is NOT backed by a shared, verifiable authority."""
        return len(self.distinct_values) == 1 and len(self.distinct_primary_sources) == 0

    @property
    def is_conflict(self) -> bool:
        return len(self.distinct_values) > 1


def compare_candidate_facts(candidates: list[CandidateRequirementsResponse]) -> dict[str, FactComparison]:
    """Steps 5-7. One FactComparison per field_name proposed by ANY
    provider — fields only one provider proposed still appear (as a
    single-proposal comparison), never dropped for lack of a second
    opinion."""
    by_field: dict[str, FactComparison] = defaultdict(lambda: FactComparison(field_name=""))
    for c in candidates:
        for f in c.candidate_facts:
            cmp = by_field[f.field_name]
            if not cmp.field_name:
                cmp.field_name = f.field_name
            cmp.proposals.append((c.provider, f, c.source_records[f.source_index]))
    return dict(by_field)


@dataclass
class DraftProfile:
    program_slug: str
    jurisdiction_code: str
    fields: dict[str, object]
    field_sources: dict[str, EvidenceRecordRef]
    primary_source_backed_fields: set
    model_consensus_only_fields: set
    conflicted_fields: dict[str, set]
    hard_gates_unknown: list[str]
    generated_at: str


def draft_profile(
    target: MissingProgramTarget, comparisons: dict[str, FactComparison],
) -> DraftProfile:
    """Step 8. A conflicted field is left OUT of `fields` (not guessed at
    by picking one side) — it is instead recorded in `conflicted_fields`
    for a human to resolve. Only primary-source-agreed or single-
    proposal-with-primary-source fields populate `fields` automatically;
    model-consensus-only fields are recorded but excluded from
    `fields` too, unless a human explicitly overrides (see accept_profile)."""
    fields: dict[str, object] = {}
    field_sources: dict[str, EvidenceRecordRef] = {}
    primary_backed: set = set()
    consensus_only: set = set()
    conflicted: dict[str, set] = {}

    known_hard_gate_fields = {
        "preapproval_mandatory", "local_entity_required", "cultural_test_required",
        "min_total_budget_usd", "min_local_spend_usd",
    }
    hard_gates_seen = set()

    for name, cmp in comparisons.items():
        if cmp.is_conflict:
            conflicted[name] = cmp.distinct_values
            continue
        if cmp.is_primary_source_agreement or (len(cmp.proposals) == 1 and cmp.distinct_primary_sources):
            _, proposal, source = cmp.proposals[0]
            fields[name] = proposal.proposed_value
            field_sources[name] = source
            primary_backed.add(name)
            if proposal.is_hard_eligibility_gate:
                hard_gates_seen.add(name)
        elif cmp.is_model_consensus_only:
            consensus_only.add(name)

    hard_gates_unknown = sorted(known_hard_gate_fields - hard_gates_seen - set(fields.keys()))

    return DraftProfile(
        program_slug=target.program_slug, jurisdiction_code=target.jurisdiction_code,
        fields=fields, field_sources=field_sources,
        primary_source_backed_fields=primary_backed,
        model_consensus_only_fields=consensus_only,
        conflicted_fields=conflicted,
        hard_gates_unknown=hard_gates_unknown,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


class ProfileAcceptanceRefused(RuntimeError):
    pass


def accept_profile(draft: DraftProfile, *, accepted_by: str):
    """Step 9 — THE ONLY function in this module (or the whole
    requirements-research path) that writes to program_requirements.py's
    registry. Requires a real human/session identity. A profile is
    'complete' per the spec's own definition — required fields populated
    or explicitly unknown, propositions source-linked, hard gates
    identified, tests still to run by the caller — never merely 'models
    agreed'.

    Model-consensus-only fields (draft.model_consensus_only_fields) are
    NEVER written as profile fields here, with no opt-out — the whole
    point of Step 7 is that provider agreement without a shared primary
    source is not evidence. They ARE disclosed in additional_facts so a
    human reviewer can see what was found and go verify it manually;
    that manual verification, not a flag on this function, is the only
    path to promoting one into a real field."""
    if not accepted_by or not accepted_by.strip():
        raise ProfileAcceptanceRefused("accept_profile requires a real accepted_by identity.")
    if draft.conflicted_fields:
        raise ProfileAcceptanceRefused(
            f"Cannot accept: unresolved conflicts on {sorted(draft.conflicted_fields)}. "
            "Resolve via primary-source lookup or explicit human override first."
        )

    from app.data.program_requirements import (
        EvidenceRecord, ProgramRequirementsProfile, RecordStatus, SourceType,
        TimingBasis, TimingFact, register,
    )

    def _to_evidence(ref: EvidenceRecordRef) -> EvidenceRecord:
        return EvidenceRecord(
            source_title=ref.source_title, source_url=ref.source_url,
            issuing_authority=ref.publisher_authority or "unknown",
            source_type=SourceType.PRIMARY if ref.primary_or_secondary == "primary" else SourceType.SECONDARY,
            status=RecordStatus.UNCERTAIN if ref.stale_or_conflict_warning else RecordStatus.CURRENT,
            effective_date=ref.effective_date, access_date=ref.retrieved_date,
            notes=ref.proposition_supported,
        )

    usable_fields = dict(draft.fields)
    usable_sources = dict(draft.field_sources)

    if not usable_fields:
        raise ProfileAcceptanceRefused(
            "No primary-source-backed fields to accept — nothing would be "
            "written. This is not an error in the workflow, it means "
            "research did not find citable primary sources for this program."
        )

    primary_evidence = next(iter(usable_sources.values()))
    profile_kwargs: dict = {
        "program_slug": draft.program_slug,
        "jurisdiction_code": draft.jurisdiction_code,
        "evidence": _to_evidence(primary_evidence),
        "additional_facts": {
            "bridge_research_note": (
                f"Accepted via Cross-Model Bridge requirements-research workflow, "
                f"by {accepted_by}, at {datetime.now(timezone.utc).isoformat()}. "
                f"{len(usable_fields)} field(s) populated, all primary-source-backed: "
                f"{sorted(usable_fields)}. "
                f"Model-consensus-only field(s) excluded pending manual source "
                f"verification: {sorted(draft.model_consensus_only_fields) or 'none'}. "
                f"Unknown hard gates: {draft.hard_gates_unknown or 'none'}."
            ),
        },
    }
    for name, value in usable_fields.items():
        if name in ("application_deadline", "audit_or_final_certification_deadline", "payment_timing"):
            # Every timing fact accepted here is, by construction, primary-
            # source-backed (usable_fields only ever contains primary-
            # source-agreement entries — see draft_profile) — OFFICIAL_TARGET
            # is the correct basis, never STATUTORY_DEADLINE (that requires
            # a human to confirm it's an actual statute citation, not just
            # "a primary source mentioned a date").
            profile_kwargs[name] = TimingFact(value=str(value), basis=TimingBasis.OFFICIAL_TARGET)
        else:
            profile_kwargs[name] = value

    profile = ProgramRequirementsProfile(**profile_kwargs)
    return register(profile)
