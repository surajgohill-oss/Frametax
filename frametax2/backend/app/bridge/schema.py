"""
Canonical Cross-Model Bridge schema: the provider-neutral request/response
interface, the audit package (sections A-G per spec), and the structured
review-response contract every provider's output must validate against.

Pydantic models throughout (not dataclasses, unlike most of this
codebase's domain layer) — this module's whole job is external-boundary
validation (provider JSON in, our JSON out), which is exactly what
pydantic is for; the domain calculators stay dataclass-based and
untouched.
"""
from __future__ import annotations

import enum
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str, *parts: str) -> str:
    """Deterministic-when-possible, collision-resistant ID. Package IDs
    are content-derived (see AuditPackage.compute_package_id) so the same
    inputs always produce the same package ID — a real reproducibility
    property, not cosmetic."""
    import uuid
    if parts:
        h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
        return f"{prefix}_{h}"
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ── Providers, operations, statuses ──────────────────────────────────────────

class ProviderID(str, enum.Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class OperationType(str, enum.Enum):
    # Active this tranche
    REQUIREMENTS_RESEARCH = "requirements_research"
    REQUIREMENTS_EVIDENCE_REVIEW = "requirements_evidence_review"
    QUALIFICATION_AUDIT = "qualification_audit"
    QPE_AUDIT = "qpe_audit"
    OPTIMIZER_STRUCTURE_AUDIT = "optimizer_structure_audit"
    TREATY_COPRODUCTION_AUDIT = "treaty_coproduction_audit"
    CULTURAL_TEST_AUDIT = "cultural_test_audit"
    SOURCE_CONFLICT_REVIEW = "source_conflict_review"
    IMPLEMENTATION_HANDOFF = "implementation_handoff"
    PRODUCT_ARCHITECTURE_REVIEW = "product_architecture_review"
    # Reserved, schema-compatible, NOT implemented this tranche (section 4) —
    # present only so the enum never needs an incompatible extension later.
    SCRIPT_PRODUCTION_ANALYSIS = "script_production_analysis"
    PREBUDGET_STRUCTURE_GENERATION = "prebudget_structure_generation"
    CULTURAL_TEST_OPTIMIZATION = "cultural_test_optimization"
    COMPONENT_ALLOCATION_REVIEW = "component_allocation_review"
    PRELIMINARY_BUDGET_REVIEW = "preliminary_budget_review"


RESERVED_FUTURE_OPERATIONS: frozenset[OperationType] = frozenset({
    OperationType.SCRIPT_PRODUCTION_ANALYSIS,
    OperationType.PREBUDGET_STRUCTURE_GENERATION,
    OperationType.CULTURAL_TEST_OPTIMIZATION,
    OperationType.COMPONENT_ALLOCATION_REVIEW,
    OperationType.PRELIMINARY_BUDGET_REVIEW,
})


class ConfidentialityClassification(str, enum.Enum):
    SAFE = "safe"                  # synthetic/public fixture data — no authorization needed
    INTERNAL = "internal"          # real engine output, no PII, low sensitivity
    CONFIDENTIAL = "confidential"  # real production financials/facts — requires explicit authorization


class ErrorCategory(str, enum.Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    INVALID_REQUEST = "invalid_request"
    PROVIDER_ERROR = "provider_error"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    NETWORK = "network"
    UNKNOWN = "unknown"


# ── Provider-neutral model adapter interface (section 3) ────────────────────

class ModelRequest(BaseModel):
    provider: ProviderID
    model_id: str
    operation: OperationType
    system_instruction: str
    structured_input: dict[str, Any]
    required_response_schema: dict[str, Any]
    timeout_seconds: float = 90.0
    max_retries: int = 3
    max_output_tokens: int = 8192
    allow_web_search: bool = False
    request_metadata: dict[str, Any] = Field(default_factory=dict)

    def content_hash(self) -> str:
        """For duplicate-request detection / caching (section 13) — hash
        of everything that determines the answer, not of timing/ids."""
        basis = json.dumps({
            "provider": self.provider.value, "model_id": self.model_id,
            "operation": self.operation.value, "system_instruction": self.system_instruction,
            "structured_input": self.structured_input,
            "required_response_schema": self.required_response_schema,
        }, sort_keys=True, default=str)
        return hashlib.sha256(basis.encode()).hexdigest()


class ModelResponse(BaseModel):
    provider: ProviderID
    model_id: str
    operation: OperationType
    request_metadata: dict[str, Any] = Field(default_factory=dict)
    response_text: str = ""
    parsed_response: Optional[dict[str, Any]] = None
    usage: dict[str, Any] = Field(default_factory=dict)  # input_tokens, output_tokens, etc.
    provider_request_id: Optional[str] = None
    latency_ms: Optional[float] = None
    error_category: ErrorCategory = ErrorCategory.NONE
    error_message: Optional[str] = None
    raw_response_retained: bool = False
    raw_response_hash: Optional[str] = None
    fallback_used: bool = False
    fallback_note: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)

    @property
    def ok(self) -> bool:
        return self.error_category == ErrorCategory.NONE and self.parsed_response is not None


# ── Audit package (section 6) ────────────────────────────────────────────────

class PackageInputs(BaseModel):
    budget_or_target_usd: Optional[float] = None
    script_treatment_metadata: dict[str, Any] = Field(default_factory=dict)
    schedule: dict[str, Any] = Field(default_factory=dict)
    cast_writer_director_facts: dict[str, Any] = Field(default_factory=dict)
    nationality_residency_facts: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    known_constraints: list[str] = Field(default_factory=list)
    user_overrides: dict[str, Any] = Field(default_factory=dict)
    unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class BudgetQpeLine(BaseModel):
    account_code: str
    description: str
    normalized_category: Optional[str] = None
    source_amount: float
    source_currency: str = "USD"
    component: Optional[str] = None
    jurisdiction_code: Optional[str] = None
    included_in_qpe: Optional[bool] = None
    exclusion_authority: Optional[str] = None
    qpe_usd: Optional[float] = None


class QualificationFacts(BaseModel):
    eligibility_gates: list[str] = Field(default_factory=list)
    timing_preapproval_requirements: list[str] = Field(default_factory=list)
    entity_requirements: list[str] = Field(default_factory=list)
    cultural_test_criteria: list[str] = Field(default_factory=list)
    cultural_test_points: Optional[int] = None
    minimum_spend: Optional[float] = None
    local_personnel_requirements: list[str] = Field(default_factory=list)
    treaty_coproduction_conditions: list[str] = Field(default_factory=list)
    filing_audit_requirements: list[str] = Field(default_factory=list)
    unresolved_facts: list[str] = Field(default_factory=list)
    qualification_state: Optional[str] = None


class StructureSummary(BaseModel):
    structure_id: str
    structure_type: str
    label: str
    participants: list[str]
    is_fully_priced: bool
    blockers: list[str] = Field(default_factory=list)
    ownership_shares: dict[str, float] = Field(default_factory=dict)
    treaty_slug: Optional[str] = None
    conditional_program_ids: list[str] = Field(default_factory=list)


class RejectedStructure(BaseModel):
    structure_type: str
    reason: str


class EconomicsSummary(BaseModel):
    gross_budget_usd: Optional[float] = None
    allocated_spend_usd: Optional[float] = None
    qpe_usd: Optional[float] = None
    gross_incentive_usd: Optional[float] = None
    finance_cost_usd: Optional[float] = None
    local_cost_delta_usd: Optional[float] = None
    travel_delta_usd: Optional[float] = None
    fx_delta_usd: Optional[float] = None
    net_incentive_usd: Optional[float] = None
    npc_usd: Optional[float] = None
    ranking_basis: str = "lowest_defensible_net_production_cost"


class EvidenceRecordRef(BaseModel):
    source_title: str
    source_url: Optional[str] = None
    publisher_authority: Optional[str] = None
    source_type: Optional[str] = None
    effective_date: Optional[str] = None
    retrieved_date: Optional[str] = None
    proposition_supported: str = ""
    primary_or_secondary: str = "secondary"
    stale_or_conflict_warning: Optional[str] = None


class AuditPackage(BaseModel):
    # A. Identity and reproducibility
    package_id: str
    package_schema_version: str = "1.0.0"
    production_or_scenario_id: str
    repository_commit: Optional[str] = None
    working_tree_fingerprint: Optional[str] = None
    engine_versions: dict[str, str] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=_now_iso)
    source_asset_versions: dict[str, str] = Field(default_factory=dict)
    operation: OperationType
    confidentiality: ConfidentialityClassification

    # B. Inputs
    inputs: PackageInputs = Field(default_factory=PackageInputs)

    # C. Budget / QPE trace
    budget_qpe_trace: list[BudgetQpeLine] = Field(default_factory=list)
    contingency_summary: dict[str, Any] = Field(default_factory=dict)

    # D. Qualification
    qualification: QualificationFacts = Field(default_factory=QualificationFacts)

    # E. Structures
    structures_considered: list[StructureSummary] = Field(default_factory=list)
    structures_rejected: list[RejectedStructure] = Field(default_factory=list)

    # F. Economics
    economics: EconomicsSummary = Field(default_factory=EconomicsSummary)

    # G. Evidence
    evidence: list[EvidenceRecordRef] = Field(default_factory=list)

    @staticmethod
    def compute_package_id(
        production_or_scenario_id: str, operation: OperationType,
        working_tree_fingerprint: str, generated_at_date: str,
    ) -> str:
        """Content-derived, not random — the same production+operation+
        code-state+day reproduces the same package_id."""
        return new_id(
            "pkg", production_or_scenario_id, operation.value,
            working_tree_fingerprint, generated_at_date,
        )

    def size_bytes(self) -> int:
        return len(self.model_dump_json().encode())


# ── Structured response contract (section 7) ────────────────────────────────

class FindingClassification(str, enum.Enum):
    CONFIRMED = "confirmed"
    DISAGREEMENT = "disagreement"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CALCULATION_ERROR = "calculation_error"
    RULE_INTERPRETATION_ERROR = "rule_interpretation_error"
    INPUT_MAPPING_ERROR = "input_mapping_error"
    QPE_CLASSIFICATION_ERROR = "qpe_classification_error"
    QUALIFICATION_GAP = "qualification_gap"
    STRUCTURE_OMISSION = "structure_omission"
    CULTURAL_TEST_ERROR = "cultural_test_error"
    TREATY_ERROR = "treaty_error"
    STACKING_ERROR = "stacking_error"
    STALE_SOURCE = "stale_source"
    SOURCE_CONFLICT = "source_conflict"
    NON_REPRODUCIBLE = "non_reproducible"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    finding_id: str
    jurisdiction_or_program: Optional[str] = None
    affected_rule_or_budget_line: Optional[str] = None
    classification: FindingClassification
    expected_result: Optional[str] = None
    observed_result: Optional[str] = None
    financial_impact_usd: Optional[float] = None
    severity: Severity
    rationale: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    proposed_remediation: Optional[str] = None


class OverallDisposition(str, enum.Enum):
    NO_ISSUES_FOUND = "no_issues_found"
    ISSUES_FOUND = "issues_found"
    INSUFFICIENT_EVIDENCE_TO_REVIEW = "insufficient_evidence_to_review"


class ReviewResponse(BaseModel):
    review_id: str
    package_id: str
    provider: ProviderID
    model: str
    operation: OperationType
    overall_disposition: OverallDisposition
    executive_summary: str
    findings: list[Finding] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    sources_consulted: list[EvidenceRecordRef] = Field(default_factory=list)
    usage_metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_now_iso)

    @field_validator("findings")
    @classmethod
    def _findings_have_unique_ids(cls, v: list[Finding]) -> list[Finding]:
        ids = [f.finding_id for f in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate finding_id within one ReviewResponse")
        return v


# JSON Schema handed to providers as required_response_schema — generated
# from the SAME pydantic model every response is validated against, so
# "what we asked for" and "what we validate" can never drift apart.
REVIEW_RESPONSE_JSON_SCHEMA: dict[str, Any] = ReviewResponse.model_json_schema()


# ── Requirements-research response contract (section 9) ─────────────────────
# Deliberately NOT ReviewResponse/Finding: a research operation proposes
# NEW candidate facts with sources, it does not audit an existing rule
# for correctness (Finding.expected_result/observed_result don't fit a
# "here is a fact nobody stored yet" shape). Same discipline applies:
# every proposition must cite a source; confidence is on the FACT, not
# on provider agreement.

class CandidateFact(BaseModel):
    field_name: str  # a ProgramRequirementsProfile field name, e.g. "preapproval_mandatory"
    proposed_value: Any
    source_index: int  # index into this response's source_records
    confidence: float = Field(ge=0.0, le=1.0)
    is_hard_eligibility_gate: bool = False
    notes: Optional[str] = None


class CandidateRequirementsResponse(BaseModel):
    research_id: str
    package_id: str
    provider: ProviderID
    model: str
    program_slug: str
    jurisdiction_code: str
    candidate_facts: list[CandidateFact] = Field(default_factory=list)
    source_records: list[EvidenceRecordRef] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    usage_metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_now_iso)

    @field_validator("candidate_facts")
    @classmethod
    def _sources_exist(cls, v: list[CandidateFact], info) -> list[CandidateFact]:
        # source_records isn't available via info at this stage in pydantic v2
        # field-level validation order; the real enforcement lives in
        # requirements_workflow.py's parse step, which has both fields
        # available. This validator only catches an obviously-out-of-range
        # negative index early.
        for f in v:
            if f.source_index < 0:
                raise ValueError(f"{f.field_name}: source_index must be >= 0 — every "
                                  "candidate fact must cite a source_records entry.")
        return v


CANDIDATE_REQUIREMENTS_JSON_SCHEMA: dict[str, Any] = CandidateRequirementsResponse.model_json_schema()


# ── Reconciliation (section 11) ──────────────────────────────────────────────

class AgreementKind(str, enum.Enum):
    FACTUAL_AGREEMENT = "factual_agreement"
    FACTUAL_CONFLICT = "factual_conflict"
    INTERPRETIVE_DISAGREEMENT = "interpretive_disagreement"
    MISSING_EVIDENCE = "missing_evidence"
    CALCULATION_DISAGREEMENT = "calculation_disagreement"
    DUPLICATED_FINDING = "duplicated_finding"


class Disposition(str, enum.Enum):
    CONFIRMED_DEFECT = "confirmed_defect"
    NEEDS_PRIMARY_SOURCE = "needs_primary_source"
    MODEL_DISAGREEMENT = "model_disagreement"
    EXPECTED_BEHAVIOR = "expected_behavior"
    DUPLICATE = "duplicate"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    ACCEPTED_FOR_IMPLEMENTATION = "accepted_for_implementation"


class ReconciledCluster(BaseModel):
    cluster_id: str
    package_id: str
    jurisdiction_or_program: Optional[str] = None
    member_finding_ids: list[str] = Field(default_factory=list)  # "provider:finding_id"
    agreement_kind: AgreementKind
    disposition: Optional[Disposition] = None  # None = not yet human-dispositioned
    disposition_note: Optional[str] = None
    dispositioned_by: Optional[str] = None
    dispositioned_at: Optional[str] = None
    implementation_task_id: Optional[str] = None


# ── Rule provenance (section 10) ─────────────────────────────────────────────

class ProvenanceGapClassification(str, enum.Enum):
    ENFORCED_AND_DISCLOSED = "enforced_and_disclosed"
    ENFORCED_NOT_DISCLOSED = "enforced_not_disclosed"
    DISCLOSED_NOT_ENFORCED = "disclosed_not_enforced"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class RuleProvenanceRecord(BaseModel):
    program_slug: str
    jurisdiction_code: str
    rule_field: str  # e.g. "application_timing", "preapproval", "cultural_test"
    stored_where: Optional[str] = None
    machine_enforced: bool = False
    failure_disqualifies: Optional[bool] = None
    changes_qpe: bool = False
    changes_pricing: bool = False
    warning_only: bool = False
    disclosed_in_ui: bool = False
    source_confidence: Optional[str] = None
    gap_classification: ProvenanceGapClassification


# ── Project ledger / decision register (section 5) ──────────────────────────

class LedgerStatus(str, enum.Enum):
    IMPLEMENTED = "implemented"
    ACTIVE_IN_SERVED_PIPELINE = "active_in_served_pipeline"
    STATIC_VERIFIED = "static_verified"
    RUNTIME_VERIFIED = "runtime_verified"
    REPORTED_UNVERIFIED = "reported_unverified"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"


class LedgerEntry(BaseModel):
    entry_id: str
    kind: str  # "doctrine" | "decision" | "milestone" | "defect" | "backlog_item" | "phase"
    title: str
    description: str
    status: LedgerStatus
    provenance: str  # where this fact/decision came from
    superseded_by: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)
