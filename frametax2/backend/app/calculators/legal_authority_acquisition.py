"""
legal_authority_acquisition.py

Phase 6 (6A-6E) of CineGlobe's Legal Authority Acquisition Engine (LAAE):
the acquisition-docket, staging, verification/approval, and freshness
subsystem described in docs/LEGAL_AUTHORITY_ACQUISITION_ENGINE.md.

Position in the system (unchanged from the architecture document):

    GreyAreaItem ─┐
    JurisdictionGraph unknowns ─┼─> AcquisitionTask ─> AcquisitionDocket
    Reinvestment UNKNOWN ─┤            │
    Treaty absence/unknown ─┘          v
                                   Connector (mock in this phase)
                                        │
                                        v
                                 StagedAuthority ──(verify)──(approve)──> commit
                                        │
                                        v
                              EvidenceGraph (Rule chain OR AbsenceOfAuthority)

Hard boundaries enforced by this module:

- LAAE reads JurisdictionGraph (jurisdiction_graph.py) and never mutates
  it. It reads GreyAreaItem / reinvestment data (qualification_model.py)
  and never mutates them either. The only object this module writes to
  is an EvidenceGraph passed in by the caller, and only via
  commit_staged_authority() — the single sanctioned write path.
- Uncommitted material (anything short of AcquisitionStatus.COMMITTED)
  is never visible to calculators or optimization_engine.py. This module
  carries no import of optimization_engine.py, qpe_calculator.py, or any
  other calculator — see test_legal_authority_acquisition.py's import
  check, mirroring the same discipline levers.py established in Phase 4.
- Nothing here calls a network. ConnectorClass and BaseConnector describe
  the shape a live connector must have; MockConnector is the only
  implementation shipped in this phase, and it is fully deterministic
  (hashlib, not random/wall-clock) so repeated runs are byte-identical.
- Scenario-grade questions never auto-execute a connector.
  Commitment-grade questions may be queued, but nothing runs until a
  caller explicitly calls run_connector() — there is no scheduler here.

No LLM calls. No wall-clock dependency: every date is a caller-supplied
ISO string (YYYY-MM-DD), exactly like evidence_graph.py.
"""
from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app.calculators.evidence_graph import (
    AbsenceOfAuthority,
    AuthoritySource,
    AuthorityTier,
    Citation,
    Document,
    DocumentVersion,
    Evidence,
    EvidenceGraph,
    Rule,
)
from app.calculators.jurisdiction_graph import (
    JurisdictionGraph,
    NodeType,
    get_program_unknowns,
)
from app.calculators.qualification_model import GreyAreaItem, GreyAreaStatus

LAAE_VERSION = "1.0.0"


# ── 6A: Priority / grade / status enums ─────────────────────────────────────

class QuestionGrade(str, enum.Enum):
    """
    SCENARIO   — exploratory / hypothetical / whole-landscape questions
                 (e.g. "what does every jurisdiction in the graph not yet
                 know about itself"). Never auto-executes a connector.
    COMMITMENT — tied to a real production decision with money on the
                 table (e.g. a Little Utopia grey area). May generate
                 docket tasks that queue connector work.
    """
    SCENARIO = "scenario"
    COMMITMENT = "commitment"


class AcquisitionPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Fixed priority-score bands. A task's priority_score is unbounded above
# (it is (value * gap) / effort), so bands are expressed as lower
# thresholds, highest first.
PRIORITY_BANDS: tuple[tuple[float, AcquisitionPriority], ...] = (
    (50_000.0, AcquisitionPriority.CRITICAL),
    (10_000.0, AcquisitionPriority.HIGH),
    (1_000.0, AcquisitionPriority.MEDIUM),
    (0.0, AcquisitionPriority.LOW),
)


def priority_band(score: float) -> AcquisitionPriority:
    for threshold, band in PRIORITY_BANDS:
        if score >= threshold:
            return band
    return AcquisitionPriority.LOW


class AcquisitionStatus(str, enum.Enum):
    """The full task/staged-authority lifecycle, per architecture §6."""
    IDENTIFIED = "identified"
    QUEUED = "queued"
    CONNECTOR_SELECTED = "connector_selected"
    RETRIEVED = "retrieved"
    STAGED = "staged"
    PARSED = "parsed"
    VERIFIED = "verified"
    APPROVED = "approved"
    COMMITTED = "committed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ConnectorClass(str, enum.Enum):
    OFFICIAL_LEGISLATION = "official_legislation"
    TAX_AUTHORITY_GUIDANCE = "tax_authority_guidance"
    LEGAL_RESEARCH = "legal_research"
    TREATY_DATABASE = "treaty_database"
    ACCOUNTING_PROFESSIONAL = "accounting_professional"
    GENERAL_DISCOVERY = "general_discovery"


# Deterministic acquisition-effort baseline per connector class. These are
# system policy constants (how hard is it, in general, to acquire
# authority through this channel), not per-jurisdiction facts — analogous
# to RECOMMEND_UPSIDE_TO_COST_RATIO in levers.py. They are never treated
# as a substitute for a real value-at-stake figure.
EFFORT_BY_CONNECTOR_CLASS: dict[ConnectorClass, float] = {
    ConnectorClass.OFFICIAL_LEGISLATION: 3.0,
    ConnectorClass.TAX_AUTHORITY_GUIDANCE: 2.0,
    ConnectorClass.LEGAL_RESEARCH: 2.5,
    ConnectorClass.TREATY_DATABASE: 1.5,
    ConnectorClass.ACCOUNTING_PROFESSIONAL: 2.0,
    ConnectorClass.GENERAL_DISCOVERY: 1.0,
}
DEFAULT_ACQUISITION_EFFORT = 2.0

# Deterministic confidence-gap constants. A gap of 1.0 means "we have
# nothing"; lower values mean "we have a partial/low-confidence signal
# already". These map FactStatus / GreyAreaStatus into a single 0..1
# scale so the prioritization formula has one honest input, never an
# invented one.
CONFIDENCE_GAP_GREY_AREA_OPEN = 1.0
CONFIDENCE_GAP_FACTSTATUS_UNKNOWN = 0.6
CONFIDENCE_GAP_FACTSTATUS_ABSENT = 1.0


def compute_priority_score(
    value_at_stake_usd: Optional[float],
    confidence_gap: float,
    acquisition_effort: float,
) -> float:
    """
    (value at stake x confidence gap) / acquisition effort.

    value_at_stake_usd of None means "not knowable from existing data" —
    it is treated as 0.0 for ranking purposes rather than invented, so a
    task with unknown financial stakes sorts below (never above) any task
    with a real, known figure of the same confidence gap.
    """
    value = value_at_stake_usd if value_at_stake_usd is not None else 0.0
    effort = acquisition_effort if acquisition_effort and acquisition_effort > 0 else DEFAULT_ACQUISITION_EFFORT
    return (value * confidence_gap) / effort


# ── 6A: Task / Docket ────────────────────────────────────────────────────────

@dataclass
class AcquisitionTask:
    task_id: str
    jurisdiction_code: str
    question: str
    question_grade: QuestionGrade
    source_kind: str  # "grey_area" | "jurisdiction_unknown"
    source_ref: str   # GreyAreaItem.item_id or JurisdictionGraph node_id, for traceability
    value_at_stake_usd: Optional[float]
    confidence_gap: float
    acquisition_effort: float
    connector_class_hint: Optional[ConnectorClass] = None
    status: AcquisitionStatus = AcquisitionStatus.IDENTIFIED
    notes: str = ""

    @property
    def priority_score(self) -> float:
        return compute_priority_score(self.value_at_stake_usd, self.confidence_gap, self.acquisition_effort)

    @property
    def priority(self) -> AcquisitionPriority:
        return priority_band(self.priority_score)


@dataclass
class AcquisitionDocket:
    docket_id: str
    tasks: list[AcquisitionTask] = field(default_factory=list)

    def sorted_by_priority(self) -> list[AcquisitionTask]:
        """Deterministic: ties in priority_score break on task_id, never
        on dict/set iteration order or wall-clock insertion time."""
        return sorted(self.tasks, key=lambda t: (-t.priority_score, t.task_id))


def tasks_from_grey_areas(grey_areas: list[GreyAreaItem]) -> list[AcquisitionTask]:
    """
    One COMMITMENT-grade task per OPEN GreyAreaItem — these are real
    production decisions (Little Utopia today) with a known amount_usd
    already on the register, so value_at_stake_usd is taken directly from
    the existing figure rather than re-derived. Already-resolved grey
    areas (RESOLVED_* / RULING_REQUESTED) do not re-enter the docket.
    """
    tasks: list[AcquisitionTask] = []
    for ga in grey_areas:
        if ga.status != GreyAreaStatus.OPEN:
            continue
        connector_class = ConnectorClass.TAX_AUTHORITY_GUIDANCE
        tasks.append(AcquisitionTask(
            task_id=f"TASK-{ga.item_id}",
            jurisdiction_code=ga.jurisdiction_code,
            question=ga.resolving_evidence,
            question_grade=QuestionGrade.COMMITMENT,
            source_kind="grey_area",
            source_ref=ga.item_id,
            value_at_stake_usd=ga.amount_usd,
            confidence_gap=CONFIDENCE_GAP_GREY_AREA_OPEN,
            acquisition_effort=EFFORT_BY_CONNECTOR_CLASS[connector_class],
            connector_class_hint=connector_class,
            notes=f"authority_to_ask={ga.authority_to_ask}",
        ))
    return tasks


# kind -> connector class hint, used only to route jurisdiction-graph-
# derived unknowns to a plausible connector; not a legal determination.
_KIND_CONNECTOR_HINTS: dict[str, ConnectorClass] = {
    "treaty_availability": ConnectorClass.TREATY_DATABASE,
    "reinvestment_treatment": ConnectorClass.TAX_AUTHORITY_GUIDANCE,
}


def tasks_from_jurisdiction_graph_unknowns(graph: JurisdictionGraph) -> list[AcquisitionTask]:
    """
    One SCENARIO-grade task per UNKNOWN/ABSENT fact node reachable from
    every NationalProgram in the graph, via the existing
    get_program_unknowns() query (jurisdiction_graph.py, Phase 5B) —
    this covers requirement unknowns, restriction unknowns, absence
    nodes, reinvestment UNKNOWN, and treaty absence/unknown uniformly,
    since all five are already modeled as fact nodes with FactStatus in
    that module. No new graph traversal logic is introduced here.

    SCENARIO grade (not COMMITMENT): these are whole-landscape unknowns
    with no production attached, so they never auto-execute a connector
    per the 6D execution policy — they only enter the docket as
    candidates for future commitment-grade tasks once a production
    attaches real stakes to one of them.

    value_at_stake_usd is always None here — a bare fact node carries no
    dollar figure, and this function does not invent one.
    """
    tasks: list[AcquisitionTask] = []
    for program in sorted(graph.nodes_of_type(NodeType.NATIONAL_PROGRAM), key=lambda n: n.node_id):
        code = program.attributes.get("jurisdiction_code", "")
        for node in sorted(get_program_unknowns(graph, program.node_id), key=lambda n: n.node_id):
            kind = node.attributes.get("kind", node.node_id)
            status = node.attributes.get("status")
            gap = (
                CONFIDENCE_GAP_FACTSTATUS_ABSENT if status == "ABSENT"
                else CONFIDENCE_GAP_FACTSTATUS_UNKNOWN
            )
            connector_class = _KIND_CONNECTOR_HINTS.get(kind, ConnectorClass.OFFICIAL_LEGISLATION)
            tasks.append(AcquisitionTask(
                task_id=f"TASK-{node.node_id}",
                jurisdiction_code=code,
                question=f"What is the {kind.replace('_', ' ')} for {program.name}?",
                question_grade=QuestionGrade.SCENARIO,
                source_kind="jurisdiction_unknown",
                source_ref=node.node_id,
                value_at_stake_usd=None,
                confidence_gap=gap,
                acquisition_effort=EFFORT_BY_CONNECTOR_CLASS[connector_class],
                connector_class_hint=connector_class,
            ))
    return tasks


def build_docket(
    docket_id: str,
    grey_areas: Optional[list[GreyAreaItem]] = None,
    graph: Optional[JurisdictionGraph] = None,
) -> AcquisitionDocket:
    """Aggregates both sources into one docket. Either input may be
    omitted; an empty docket is valid."""
    tasks: list[AcquisitionTask] = []
    if grey_areas is not None:
        tasks.extend(tasks_from_grey_areas(grey_areas))
    if graph is not None:
        tasks.extend(tasks_from_jurisdiction_graph_unknowns(graph))
    return AcquisitionDocket(docket_id=docket_id, tasks=tasks)


# ── 6C: Connector abstraction ────────────────────────────────────────────────

@dataclass(frozen=True)
class ConnectorResult:
    """What a connector hands back for one task. No parsing/interpretation
    happens here — this is raw retrieval metadata plus an excerpt."""
    task_id: str
    connector_class: ConnectorClass
    source_url: Optional[str]
    title: str
    excerpt: str
    retrieved_date: str  # caller-supplied ISO date
    content_hash: str
    tier_hint: Optional[AuthorityTier] = None


def content_hash_of(text: str) -> str:
    """Deterministic integrity-hash placeholder (6E) — sha256, not a
    cryptographic commitment to anything beyond byte-for-byte content
    identity of what was actually staged."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class BaseConnector:
    """
    The shape every connector — mock or live — must implement. This
    phase ships MockConnector only. A live connector (official
    legislation portal, tax authority guidance API, legal research
    service, treaty database, professional/accounting source, or general
    discovery search) is added later by subclassing this and wiring a
    real fetch(); nothing about the docket/staging/verification pipeline
    above or below this class changes when that happens.
    """
    connector_class: ConnectorClass

    def fetch(self, task: AcquisitionTask, as_of_date: str) -> ConnectorResult:
        raise NotImplementedError


class MockConnector(BaseConnector):
    """
    Deterministic stand-in for tests and for 6D/6E wiring. Produces a
    fixed ConnectorResult for a given (task_id, as_of_date) pair every
    time — no randomness, no wall clock, no network — so two runs of the
    same docket through MockConnector are byte-identical.
    """

    def __init__(self, connector_class: ConnectorClass = ConnectorClass.GENERAL_DISCOVERY) -> None:
        self.connector_class = connector_class

    def fetch(self, task: AcquisitionTask, as_of_date: str) -> ConnectorResult:
        excerpt = (
            f"MOCK CONNECTOR — no live retrieval performed. "
            f"Placeholder for task '{task.task_id}' ({task.question})."
        )
        return ConnectorResult(
            task_id=task.task_id,
            connector_class=self.connector_class,
            source_url=f"mock://{task.jurisdiction_code.lower()}/{task.task_id}",
            title=f"Mock retrieval: {task.task_id}",
            excerpt=excerpt,
            retrieved_date=as_of_date,
            content_hash=content_hash_of(excerpt),
        )


# ── 6B: Staging / verification / approval ───────────────────────────────────

class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ApprovalClass(str, enum.Enum):
    AUTO_ELIGIBLE = "auto_eligible"        # verification alone is sufficient to commit
    REQUIRES_APPROVAL = "requires_approval"  # high-impact — needs an explicit approval step too


# Value-at-stake threshold above which a staged authority requires an
# explicit approval step in addition to verification. A system policy
# constant, not a per-jurisdiction fact.
HIGH_IMPACT_APPROVAL_THRESHOLD_USD = 50_000.0


def classify_approval(task: AcquisitionTask) -> ApprovalClass:
    value = task.value_at_stake_usd or 0.0
    if value >= HIGH_IMPACT_APPROVAL_THRESHOLD_USD:
        return ApprovalClass.REQUIRES_APPROVAL
    return ApprovalClass.AUTO_ELIGIBLE


@dataclass
class StagedAuthority:
    """
    Uncommitted material. Nothing in this dataclass is visible to
    calculators or optimization_engine.py — those modules do not import
    this one at all. Only commit_staged_authority() below can turn a
    StagedAuthority into anything the Evidence Graph (and therefore,
    eventually, a calculator's citation trail) can see.
    """
    staged_id: str
    task_id: str
    connector_result: ConnectorResult
    jurisdiction_code: str
    approval_class: ApprovalClass
    status: AcquisitionStatus = AcquisitionStatus.STAGED
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_by: Optional[str] = None
    approved_by: Optional[str] = None
    outcome: Optional[str] = None  # "authority_found" | "absence_confirmed", set at verification
    notes: str = ""


def run_connector(
    task: AcquisitionTask,
    connector: BaseConnector,
    as_of_date: str,
) -> StagedAuthority:
    """
    The single entry point that turns an AcquisitionTask into a
    StagedAuthority. Enforces the 6D execution policy structurally:

    - Refuses to run for a SCENARIO-grade task. Scenario-grade questions
      never auto-execute a connector; they may only be promoted to
      COMMITMENT-grade (by constructing a new task) once a real
      production decision attaches to them.
    - Mutates task.status through QUEUED -> RETRIEVED -> STAGED so the
      docket's own view of the task reflects what happened.

    This function must never be called from a calculator or from
    optimization_engine.py — see the import-boundary test in
    test_legal_authority_acquisition.py.
    """
    if task.question_grade != QuestionGrade.COMMITMENT:
        raise ValueError(
            f"Task '{task.task_id}' is {task.question_grade.value}-grade — "
            "connectors do not run automatically for scenario-grade questions."
        )
    if task.status not in (AcquisitionStatus.IDENTIFIED, AcquisitionStatus.QUEUED, AcquisitionStatus.CONNECTOR_SELECTED):
        raise ValueError(f"Task '{task.task_id}' is in status '{task.status.value}' — cannot run a connector now.")

    task.status = AcquisitionStatus.QUEUED
    task.status = AcquisitionStatus.CONNECTOR_SELECTED
    result = connector.fetch(task, as_of_date)
    task.status = AcquisitionStatus.RETRIEVED

    staged = StagedAuthority(
        staged_id=f"STG-{task.task_id}",
        task_id=task.task_id,
        connector_result=result,
        jurisdiction_code=task.jurisdiction_code,
        approval_class=classify_approval(task),
        status=AcquisitionStatus.STAGED,
    )
    task.status = AcquisitionStatus.STAGED
    return staged


def verify_staged_authority(
    staged: StagedAuthority,
    verified_by: str,
    outcome: str,
    notes: str = "",
) -> StagedAuthority:
    """
    Marks a StagedAuthority as human/professionally verified. outcome
    must be one of "authority_found" or "absence_confirmed" — an absence
    finding is a first-class, equally-valid outcome of verification, not
    a failure to find something.
    """
    if outcome not in ("authority_found", "absence_confirmed"):
        raise ValueError("outcome must be 'authority_found' or 'absence_confirmed'.")
    if staged.status == AcquisitionStatus.COMMITTED:
        raise ValueError(f"StagedAuthority '{staged.staged_id}' is already committed — cannot re-verify.")
    staged.verification_status = VerificationStatus.VERIFIED
    staged.status = AcquisitionStatus.VERIFIED
    staged.verified_by = verified_by
    staged.outcome = outcome
    staged.notes = notes
    return staged


def reject_staged_authority(staged: StagedAuthority, rejected_by: str, notes: str = "") -> StagedAuthority:
    staged.verification_status = VerificationStatus.REJECTED
    staged.status = AcquisitionStatus.REJECTED
    staged.verified_by = rejected_by
    staged.notes = notes
    return staged


def approve_staged_authority(staged: StagedAuthority, approved_by: str) -> StagedAuthority:
    """High-impact staged authority (ApprovalClass.REQUIRES_APPROVAL) must
    pass through here after verification and before commit."""
    if staged.verification_status != VerificationStatus.VERIFIED:
        raise ValueError(f"StagedAuthority '{staged.staged_id}' must be verified before it can be approved.")
    staged.status = AcquisitionStatus.APPROVED
    staged.approved_by = approved_by
    return staged


@dataclass(frozen=True)
class AcquisitionDecision:
    decision_id: str
    staged_id: str
    decision: str  # "commit_rule" | "commit_absence"
    committed_rule_id: Optional[str] = None
    committed_absence_id: Optional[str] = None
    notes: str = ""


def commit_staged_authority(
    staged: StagedAuthority,
    graph: EvidenceGraph,
    *,
    rule_text: Optional[str] = None,
    tier: Optional[AuthorityTier] = None,
    authority_body: Optional[str] = None,
    absence_question: Optional[str] = None,
    searched_tiers: tuple[AuthorityTier, ...] = (),
) -> AcquisitionDecision:
    """
    The ONLY sanctioned write path from LAAE into the Evidence Graph.

    Preconditions (enforced, not advisory):
    - staged.verification_status must be VERIFIED.
    - if staged.approval_class is REQUIRES_APPROVAL, staged.status must
      already be APPROVED (i.e. approve_staged_authority() was called).
    - staged.outcome must be set (by verify_staged_authority()).

    An "absence_confirmed" outcome commits an AbsenceOfAuthority node —
    this is a first-class success of the acquisition pipeline, recorded
    exactly like a found rule, not silently dropped.

    An "authority_found" outcome builds the full
    Document -> DocumentVersion -> AuthoritySource -> Citation -> Evidence
    -> Rule chain that evidence_graph.py requires before a Rule can ever
    be linked to a Recommendation (rule_is_fully_chained), using the
    caller-supplied rule_text/tier — this module never invents legal text
    or a tier; both must be supplied by whoever performed the
    verification.
    """
    if staged.verification_status != VerificationStatus.VERIFIED:
        raise ValueError(f"StagedAuthority '{staged.staged_id}' is not verified — cannot commit.")
    if staged.approval_class == ApprovalClass.REQUIRES_APPROVAL and staged.status != AcquisitionStatus.APPROVED:
        raise ValueError(f"StagedAuthority '{staged.staged_id}' requires approval before commit.")
    if staged.outcome is None:
        raise ValueError(f"StagedAuthority '{staged.staged_id}' has no recorded outcome — cannot commit.")

    if staged.outcome == "absence_confirmed":
        absence = AbsenceOfAuthority(
            absence_id=f"ABS-{staged.staged_id}",
            jurisdiction_code=staged.jurisdiction_code,
            question=absence_question or staged.connector_result.title,
            searched_tiers=searched_tiers,
            notes=staged.notes,
        )
        graph.add_absence_of_authority(absence)
        staged.status = AcquisitionStatus.COMMITTED
        return AcquisitionDecision(
            decision_id=f"DEC-{staged.staged_id}",
            staged_id=staged.staged_id,
            decision="commit_absence",
            committed_absence_id=absence.absence_id,
        )

    # outcome == "authority_found"
    if rule_text is None or tier is None:
        raise ValueError("Committing an authority_found outcome requires both rule_text and tier.")

    result = staged.connector_result
    doc = graph.add_document(Document(
        document_id=f"DOC-{staged.staged_id}",
        jurisdiction_code=staged.jurisdiction_code,
        title=result.title,
        source_url=result.source_url,
    ))
    version = graph.add_document_version(DocumentVersion(
        version_id=f"DOCV-{staged.staged_id}",
        document_id=doc.document_id,
        version_label="v1",
        retrieved_date=result.retrieved_date,
        excerpt=result.excerpt,
    ))
    source = graph.add_authority_source(AuthoritySource(
        source_id=f"SRC-{staged.staged_id}",
        jurisdiction_code=staged.jurisdiction_code,
        tier=tier,
        authority_body=authority_body or result.connector_class.value,
        title=result.title,
        document_version_id=version.version_id,
    ))
    citation = graph.add_citation(Citation(
        citation_id=f"CIT-{staged.staged_id}",
        authority_source_id=source.source_id,
        document_version_id=version.version_id,
        pinpoint="n/a",
        citation_text=result.excerpt,
    ))
    rule = graph.add_rule(Rule(
        rule_id=f"RULE-{staged.staged_id}",
        jurisdiction_code=staged.jurisdiction_code,
        description=rule_text,
    ))
    graph.add_evidence(Evidence(
        evidence_id=f"EV-{staged.staged_id}",
        rule_id=rule.rule_id,
        citation_id=citation.citation_id,
        description=staged.notes or rule_text,
    ))
    staged.status = AcquisitionStatus.COMMITTED
    return AcquisitionDecision(
        decision_id=f"DEC-{staged.staged_id}",
        staged_id=staged.staged_id,
        decision="commit_rule",
        committed_rule_id=rule.rule_id,
    )


# ── 6E: Freshness / citation lifecycle ──────────────────────────────────────

class FreshnessClass(str, enum.Enum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    UNKNOWN = "unknown"


# Fixed policy thresholds (days since retrieval), not per-jurisdiction facts.
FRESHNESS_AGING_DAYS = 180
FRESHNESS_STALE_DAYS = 365


def _days_between(earlier_iso: str, later_iso: str) -> int:
    earlier = date.fromisoformat(earlier_iso)
    later = date.fromisoformat(later_iso)
    return (later - earlier).days


def classify_freshness(retrieved_date: Optional[str], as_of_date: str) -> FreshnessClass:
    """
    Deterministic given caller-supplied dates — no wall-clock lookup, so
    a freshness classification is exactly reproducible for a given
    (retrieved_date, as_of_date) pair. retrieved_date=None (never
    retrieved / metadata missing) is UNKNOWN, distinct from STALE (we
    know when it was retrieved and it's old).
    """
    if retrieved_date is None:
        return FreshnessClass.UNKNOWN
    age_days = _days_between(retrieved_date, as_of_date)
    if age_days < 0:
        raise ValueError(f"retrieved_date '{retrieved_date}' is after as_of_date '{as_of_date}'.")
    if age_days <= FRESHNESS_AGING_DAYS:
        return FreshnessClass.FRESH
    if age_days <= FRESHNESS_STALE_DAYS:
        return FreshnessClass.AGING
    return FreshnessClass.STALE


@dataclass(frozen=True)
class ReviewQueueEntry:
    """
    A first-class "someone should look at this" record. Freshness/
    supersession checks never silently re-trust or silently discard
    already-held authority — they only ever add a ReviewQueueEntry for a
    human to act on.
    """
    entry_id: str
    reason: str  # "stale_authority" | "superseded_source"
    subject_id: str
    jurisdiction_code: str
    notes: str = ""


def detect_stale_authority(
    held_authorities: list[tuple[str, str, Optional[str]]],
    as_of_date: str,
) -> list[ReviewQueueEntry]:
    """
    held_authorities: list of (rule_id_or_source_id, jurisdiction_code,
    retrieved_date) tuples for already-committed authority — this is a
    scheduled freshness check over what LAAE already holds, per the 6D
    "scheduled freshness checks only for already-held authority" policy,
    not a check that triggers new acquisition.
    """
    entries: list[ReviewQueueEntry] = []
    for subject_id, code, retrieved_date in held_authorities:
        if classify_freshness(retrieved_date, as_of_date) == FreshnessClass.STALE:
            entries.append(ReviewQueueEntry(
                entry_id=f"REVIEW-STALE-{subject_id}",
                reason="stale_authority",
                subject_id=subject_id,
                jurisdiction_code=code,
                notes=f"Retrieved {retrieved_date}, stale as of {as_of_date}.",
            ))
    return entries


def flag_supersession_for_review(
    old_version_id: str,
    new_version: DocumentVersion,
    jurisdiction_code: str,
) -> ReviewQueueEntry:
    """
    Supersession detection hook: when a caller supersedes a
    DocumentVersion (via EvidenceGraph.supersede_document_version), this
    turns that event into a review-needed queue entry rather than a
    silent auto-carry-forward — every Rule whose evidence traced through
    the old version needs a human to confirm the new version doesn't
    change the conclusion.
    """
    return ReviewQueueEntry(
        entry_id=f"REVIEW-SUPERSEDE-{old_version_id}",
        reason="superseded_source",
        subject_id=old_version_id,
        jurisdiction_code=jurisdiction_code,
        notes=f"Superseded by '{new_version.version_id}' — verify dependent rules still hold.",
    )
