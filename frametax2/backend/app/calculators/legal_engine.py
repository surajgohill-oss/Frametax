"""
legal_engine.py

Phase 8 gateway: the Legal Engine — the reusable application subsystem
that closes the loop LAAE opened.

Every piece of this loop already exists as a separately-tested engine:
grey areas and Jurisdiction Graph unknowns become AcquisitionTasks
(legal_authority_acquisition.build_docket), connectors retrieve and
stage material (run_connector / StagedAuthority), verified material
commits into the Evidence Graph (commit_staged_authority), committed
rules are scored (authority_score.score_rule), resolved grey areas
re-enter the register (qualification_model.resolve_grey_area), and the
optimizer/recommendation stack reruns on the updated state. What did
NOT exist was the subsystem that runs that loop automatically — every
prior session drove it by hand. This module is that subsystem, and only
that subsystem.

Boundaries (all inherited, none new):

- Detection is automatic and exhaustive over modeled state: every OPEN
  GreyAreaItem and every UNKNOWN/ABSENT Jurisdiction Graph fact node
  becomes a normalized LegalQuestion — no human (and no Claude session)
  has to notice a gap for it to enter the docket.
- Connector execution respects LAAE's frozen policy: COMMITMENT-grade
  tasks with a configured connector are invoked automatically;
  SCENARIO-grade tasks are surfaced but never auto-executed. Promotion
  to commitment grade requires a caller-supplied value-at-stake — the
  engine never invents stakes to justify running a connector.
- Provenance verification is automated (content-hash integrity, source
  URL presence, retrieval-date presence, connector-class consistency).
  LEGAL verification is not: verify_staged_authority's verified_by /
  outcome gate remains a human/professional step, exactly as LAAE
  designed it. This engine prepares everything up to that gate and
  resumes automatically after it — it never fabricates a verifier.
- The Evidence Graph and Authority Score are never bypassed: the only
  write path is commit_staged_authority; the only scores are
  authority_score.py's own functions over the committed chain.
- Reruns reuse build_risk_cases / discover_all_opportunities /
  compose_production_structures / generate_production_recommendations
  exactly as any direct caller would — zero new math.

Deterministic throughout: caller-supplied as_of_date, fixed orderings
(docket priority order, task_id tie-break), no wall clock, no network in
this module itself (connectors own retrieval; MockConnector is the only
implementation shipped, and live connectors register through the same
BaseConnector shape without any change here).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional

from app.calculators.authority_score import AuthorityScore, score_rule
from app.calculators.evidence_graph import AuthorityTier, EvidenceGraph
from app.calculators.jurisdiction_graph import JurisdictionGraph
from app.calculators.legal_authority_acquisition import (
    AcquisitionDocket,
    AcquisitionStatus,
    AcquisitionTask,
    BaseConnector,
    ConnectorClass,
    QuestionGrade,
    StagedAuthority,
    build_docket,
    content_hash_of,
    run_connector,
    approve_staged_authority,
    verify_staged_authority,
    commit_staged_authority,
)
from app.calculators.opportunity_discovery import discover_all_opportunities
from app.calculators.optimization_engine import OptimizationResult, build_risk_cases
from app.calculators.production_recommendation_engine import (
    RecommendationSet,
    generate_production_recommendations,
)
from app.calculators.production_structure_composer import (
    CompositionResult,
    compose_production_structures,
)
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    apply_grey_area_resolution,
    resolve_grey_area,
)

LEGAL_ENGINE_VERSION = "1.0.0"


# ── Governing authority / document-type determination ───────────────────────
# Fixed policy tables keyed by ConnectorClass — which KIND of body governs
# a question of this class and which document types can answer it. These
# describe the acquisition channel (matching EFFORT_BY_CONNECTOR_CLASS's
# role in LAAE), never a jurisdiction-specific legal fact.

GOVERNING_AUTHORITY_BY_CLASS: dict[ConnectorClass, str] = {
    ConnectorClass.OFFICIAL_LEGISLATION: "National/state legislature or official gazette",
    ConnectorClass.TAX_AUTHORITY_GUIDANCE: "Revenue authority / tax administration",
    ConnectorClass.LEGAL_RESEARCH: "Courts and legal research services",
    ConnectorClass.TREATY_DATABASE: "Foreign ministry / treaty depositary",
    ConnectorClass.ACCOUNTING_PROFESSIONAL: "Professional accounting body / Big-4 guidance",
    ConnectorClass.GENERAL_DISCOVERY: "Film commission / official program administrator",
}

REQUIRED_DOCUMENT_TYPES_BY_CLASS: dict[ConnectorClass, tuple[AuthorityTier, ...]] = {
    ConnectorClass.OFFICIAL_LEGISLATION: (
        AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.REGULATIONS,
    ),
    ConnectorClass.TAX_AUTHORITY_GUIDANCE: (
        AuthorityTier.OFFICIAL_GUIDANCE, AuthorityTier.OFFICIAL_FAQ,
        AuthorityTier.PUBLISHED_RULING, AuthorityTier.BINDING_RULING,
    ),
    ConnectorClass.LEGAL_RESEARCH: (
        AuthorityTier.PUBLISHED_RULING, AuthorityTier.LEGAL_OPINION,
    ),
    ConnectorClass.TREATY_DATABASE: (
        AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.OFFICIAL_GUIDANCE,
    ),
    ConnectorClass.ACCOUNTING_PROFESSIONAL: (
        AuthorityTier.ACCOUNTING_GUIDANCE, AuthorityTier.TAX_OPINION,
    ),
    ConnectorClass.GENERAL_DISCOVERY: (
        AuthorityTier.OFFICIAL_GUIDANCE, AuthorityTier.AGENCY_MANUAL,
        AuthorityTier.OFFICIAL_FAQ,
    ),
}


@dataclass(frozen=True)
class LegalQuestion:
    """A normalized legal question derived from an AcquisitionTask —
    the task plus the deterministic authority/document-type routing the
    connector layer needs. question_id == the underlying TASK id so the
    two docket views can never drift apart."""
    question_id: str
    jurisdiction_code: str
    question: str
    question_grade: QuestionGrade
    source_kind: str
    source_ref: str
    governing_authority: str
    required_document_types: tuple[AuthorityTier, ...]
    connector_class: ConnectorClass
    value_at_stake_usd: Optional[float]
    priority_score: float
    auto_executable: bool  # COMMITMENT grade AND a connector is configured


class ProvenanceStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True)
class ProvenanceReport:
    staged_id: str
    status: ProvenanceStatus
    checks: dict[str, bool]
    notes: str = ""


@dataclass
class AcquisitionCycleResult:
    """One automatic pass: what was detected, what ran, what is now
    staged awaiting the human verification gate, and what could not run
    (no connector configured / scenario-grade)."""
    questions: tuple[LegalQuestion, ...]
    executed_task_ids: tuple[str, ...]
    staged: dict[str, StagedAuthority]            # task_id -> staged material
    provenance: dict[str, ProvenanceReport]       # staged_id -> provenance result
    awaiting_verification: tuple[str, ...]        # staged_ids that passed provenance
    provenance_failed: tuple[str, ...]            # staged_ids that failed provenance
    not_executed: dict[str, str]                  # task_id -> reason


@dataclass
class CommitResult:
    """What commit_and_score() actually produced. resolved_grey_area is
    the NEW GreyAreaItem returned by qualification_model's pure
    resolve_grey_area() transition (the original is never mutated) —
    None when no grey area was attached or the commit was an absence."""
    committed_id: str
    score: Optional[AuthorityScore]
    resolved_grey_area: Optional[GreyAreaItem] = None


@dataclass
class RerunResult:
    """Post-commit rerun of the full downstream stack — every figure in
    here is produced by the existing engines, none by this module."""
    optimization: OptimizationResult
    composition: CompositionResult
    recommendations: RecommendationSet
    authority_scores: dict[str, AuthorityScore]   # rule_id -> score
    register_used: list[AccountQualification] = field(default_factory=list)
    grey_areas_used: list[GreyAreaItem] = field(default_factory=list)


class LegalEngine:
    """
    The reusable subsystem. Hold one per production/session: it owns an
    EvidenceGraph and a connector registry, and exposes the loop as
    discrete, resumable steps —

        detect_open_questions()      # automatic, exhaustive
        run_acquisition_cycle()      # auto-executes what policy allows
        check_provenance()           # automated integrity checks
        [human gate: record_verification()]
        commit_and_score()           # graph write + Authority Score
        rerun()                      # qualification -> optimizer -> recs

    No step fabricates what a prior step should have produced; each
    raises or reports honestly when its precondition isn't met.
    """

    def __init__(
        self,
        evidence_graph: Optional[EvidenceGraph] = None,
        connectors: Optional[dict[ConnectorClass, BaseConnector]] = None,
    ) -> None:
        self.evidence_graph = evidence_graph if evidence_graph is not None else EvidenceGraph()
        self.connectors: dict[ConnectorClass, BaseConnector] = dict(connectors or {})
        self._staged: dict[str, StagedAuthority] = {}
        self._tasks: dict[str, AcquisitionTask] = {}
        self._committed_rule_ids: list[str] = []
        self._resolved_grey_areas: dict[str, GreyAreaItem] = {}  # item_id -> resolved item

    # ── Step 1: automatic uncertainty detection ─────────────────────────

    def detect_open_questions(
        self,
        grey_areas: Optional[list[GreyAreaItem]] = None,
        graph: Optional[JurisdictionGraph] = None,
        docket_id: str = "DOCKET-LEGAL-ENGINE",
    ) -> tuple[AcquisitionDocket, tuple[LegalQuestion, ...]]:
        """Exhaustive and automatic: every OPEN grey area and every
        UNKNOWN/ABSENT graph fact becomes a task and a normalized
        LegalQuestion — reusing build_docket() unchanged, so detection
        can never diverge from LAAE's own docket construction."""
        docket = build_docket(docket_id, grey_areas=grey_areas, graph=graph)
        questions: list[LegalQuestion] = []
        for task in docket.sorted_by_priority():
            self._tasks[task.task_id] = task
            connector_class = task.connector_class_hint or ConnectorClass.GENERAL_DISCOVERY
            questions.append(LegalQuestion(
                question_id=task.task_id,
                jurisdiction_code=task.jurisdiction_code,
                question=task.question,
                question_grade=task.question_grade,
                source_kind=task.source_kind,
                source_ref=task.source_ref,
                governing_authority=GOVERNING_AUTHORITY_BY_CLASS[connector_class],
                required_document_types=REQUIRED_DOCUMENT_TYPES_BY_CLASS[connector_class],
                connector_class=connector_class,
                value_at_stake_usd=task.value_at_stake_usd,
                priority_score=task.priority_score,
                auto_executable=(
                    task.question_grade == QuestionGrade.COMMITMENT
                    and connector_class in self.connectors
                ),
            ))
        return docket, tuple(questions)

    # ── Grade promotion (caller-supplied stakes, never invented) ────────

    def promote_to_commitment(self, task_id: str, value_at_stake_usd: float, reason: str) -> AcquisitionTask:
        """A SCENARIO task becomes COMMITMENT-grade only when a real
        production attaches real stakes — per LAAE's own policy this
        constructs a new task rather than mutating the scenario one."""
        original = self._tasks.get(task_id)
        if original is None:
            raise ValueError(f"Unknown task '{task_id}'.")
        if original.question_grade == QuestionGrade.COMMITMENT:
            return original
        promoted = AcquisitionTask(
            task_id=f"{original.task_id}-COMMIT",
            jurisdiction_code=original.jurisdiction_code,
            question=original.question,
            question_grade=QuestionGrade.COMMITMENT,
            source_kind=original.source_kind,
            source_ref=original.source_ref,
            value_at_stake_usd=value_at_stake_usd,
            confidence_gap=original.confidence_gap,
            acquisition_effort=original.acquisition_effort,
            connector_class_hint=original.connector_class_hint,
            notes=f"Promoted from {original.task_id}: {reason}",
        )
        self._tasks[promoted.task_id] = promoted
        return promoted

    # ── Steps 2-3: automatic connector execution + staging ──────────────

    def run_acquisition_cycle(
        self,
        as_of_date: str,
        grey_areas: Optional[list[GreyAreaItem]] = None,
        graph: Optional[JurisdictionGraph] = None,
        max_tasks: Optional[int] = None,
    ) -> AcquisitionCycleResult:
        """One full automatic pass: detect, then execute every
        auto-executable question in priority order (bounded by max_tasks
        when given), stage results, and run provenance checks. Stops at
        the verification gate — nothing is committed here."""
        _, questions = self.detect_open_questions(grey_areas=grey_areas, graph=graph)

        executed: list[str] = []
        staged: dict[str, StagedAuthority] = {}
        provenance: dict[str, ProvenanceReport] = {}
        not_executed: dict[str, str] = {}

        for question in questions:
            if not question.auto_executable:
                if question.question_grade != QuestionGrade.COMMITMENT:
                    not_executed[question.question_id] = (
                        "scenario-grade: never auto-executed per LAAE policy; "
                        "promote_to_commitment() with real stakes to run it."
                    )
                else:
                    not_executed[question.question_id] = (
                        f"no connector configured for class '{question.connector_class.value}'."
                    )
                continue
            if max_tasks is not None and len(executed) >= max_tasks:
                not_executed[question.question_id] = "max_tasks bound reached this cycle."
                continue
            task = self._tasks[question.question_id]
            connector = self.connectors[question.connector_class]
            staged_item = run_connector(task, connector, as_of_date=as_of_date)
            self._staged[staged_item.staged_id] = staged_item
            staged[task.task_id] = staged_item
            provenance[staged_item.staged_id] = self.check_provenance(staged_item)
            executed.append(task.task_id)

        awaiting = tuple(sorted(
            sid for sid, report in provenance.items() if report.status == ProvenanceStatus.PASSED
        ))
        failed = tuple(sorted(
            sid for sid, report in provenance.items() if report.status == ProvenanceStatus.FAILED
        ))
        return AcquisitionCycleResult(
            questions=questions,
            executed_task_ids=tuple(executed),
            staged=staged,
            provenance=provenance,
            awaiting_verification=awaiting,
            provenance_failed=failed,
            not_executed=not_executed,
        )

    # ── Step 4: automated provenance verification ───────────────────────

    def check_provenance(self, staged: StagedAuthority) -> ProvenanceReport:
        """Integrity checks a machine can honestly perform: the staged
        excerpt hashes to the recorded content_hash, a source URL and
        retrieval date exist, and the connector class matches the task's
        hint. This is NOT legal verification — that gate
        (record_verification) remains human."""
        result = staged.connector_result
        task = self._tasks.get(staged.task_id)
        checks = {
            "content_hash_matches": content_hash_of(result.excerpt) == result.content_hash,
            "source_url_present": bool(result.source_url),
            "retrieved_date_present": bool(result.retrieved_date),
            "connector_class_consistent": (
                task is None or task.connector_class_hint is None
                or result.connector_class == task.connector_class_hint
            ),
        }
        passed = all(checks.values())
        return ProvenanceReport(
            staged_id=staged.staged_id,
            status=ProvenanceStatus.PASSED if passed else ProvenanceStatus.FAILED,
            checks=checks,
            notes="" if passed else "One or more provenance checks failed — do not verify or commit.",
        )

    # ── Step 5: the human gate (exposed, never fabricated) ──────────────

    def record_verification(
        self, staged_id: str, verified_by: str, outcome: str, notes: str = "",
    ) -> StagedAuthority:
        staged = self._staged.get(staged_id)
        if staged is None:
            raise ValueError(f"Unknown staged authority '{staged_id}'.")
        report = self.check_provenance(staged)
        if report.status != ProvenanceStatus.PASSED:
            raise ValueError(
                f"'{staged_id}' failed provenance checks {report.checks} — cannot verify."
            )
        return verify_staged_authority(staged, verified_by=verified_by, outcome=outcome, notes=notes)

    def record_approval(self, staged_id: str, approved_by: str) -> StagedAuthority:
        """The second human gate for high-impact material
        (ApprovalClass.REQUIRES_APPROVAL, value at stake >= LAAE's
        HIGH_IMPACT_APPROVAL_THRESHOLD_USD). Exposed, never bypassed and
        never auto-approved."""
        staged = self._staged.get(staged_id)
        if staged is None:
            raise ValueError(f"Unknown staged authority '{staged_id}'.")
        return approve_staged_authority(staged, approved_by=approved_by)

    # ── Steps 6-8: commit, score, resolve ────────────────────────────────

    def commit_and_score(
        self,
        staged_id: str,
        target_jurisdiction_code: str,
        as_of_date: str,
        *,
        rule_text: Optional[str] = None,
        tier: Optional[AuthorityTier] = None,
        authority_body: Optional[str] = None,
        absence_question: Optional[str] = None,
        searched_tiers: tuple[AuthorityTier, ...] = (),
        resolves_grey_area: Optional[GreyAreaItem] = None,
        grey_area_outcome: Optional[GreyAreaStatus] = None,
    ) -> CommitResult:
        """Commit through LAAE's single sanctioned write path, score the
        committed rule with the real Authority Score engine, and (when a
        grey area is attached) resolve it through qualification_model's
        own evidence-gated transition — the resolved item is tracked so
        rerun() applies it automatically. score is None for an absence
        commit (absence never manufactures a positive score; that IS the
        frozen rule)."""
        staged = self._staged.get(staged_id)
        if staged is None:
            raise ValueError(f"Unknown staged authority '{staged_id}'.")

        decision = commit_staged_authority(
            staged, self.evidence_graph,
            rule_text=rule_text, tier=tier, authority_body=authority_body,
            absence_question=absence_question, searched_tiers=searched_tiers,
        )

        score: Optional[AuthorityScore] = None
        resolved: Optional[GreyAreaItem] = None
        committed_id = decision.committed_rule_id or decision.committed_absence_id or ""
        if decision.committed_rule_id:
            self._committed_rule_ids.append(decision.committed_rule_id)
            score = score_rule(
                self.evidence_graph, decision.committed_rule_id,
                target_jurisdiction_code, as_of_date=as_of_date,
            )
            if resolves_grey_area is not None:
                resolved = resolve_grey_area(
                    resolves_grey_area,
                    outcome=grey_area_outcome or GreyAreaStatus.RESOLVED_INCLUDE,
                    ruling_citation=staged.connector_result.title,
                    graph=self.evidence_graph,
                    resolving_rule_id=decision.committed_rule_id,
                )
                self._resolved_grey_areas[resolved.item_id] = resolved
        return CommitResult(committed_id=committed_id, score=score, resolved_grey_area=resolved)

    def apply_resolutions(
        self,
        register: list[AccountQualification],
        grey_areas: list[GreyAreaItem],
    ) -> tuple[list[AccountQualification], list[GreyAreaItem]]:
        """Substitute every grey area this engine has resolved and
        reclassify the register through qualification_model's own
        apply_grey_area_resolution() — inputs are never mutated; new
        lists come back."""
        updated_greys = [
            self._resolved_grey_areas.get(ga.item_id, ga) for ga in grey_areas
        ]
        updated_register = register
        for item in updated_greys:
            if item.item_id in self._resolved_grey_areas:
                updated_register = apply_grey_area_resolution(updated_register, item)
        return updated_register, updated_greys

    # ── Steps 9-11: rerun qualification -> optimizer -> recommendations ──

    def rerun(
        self,
        register: list[AccountQualification],
        gross_budget_usd: float,
        rate: float,
        grey_areas: list[GreyAreaItem],
        graph: JurisdictionGraph,
        jurisdiction_code: str = "MU",
        as_of_date: Optional[str] = None,
        delay_weeks: int = 39,
        bridge_rate: float = 0.08,
    ) -> RerunResult:
        """The post-commit rerun: this engine's tracked grey-area
        resolutions are applied first (apply_resolutions — the register
        reclassification is qualification_model's own), then one
        build_risk_cases() call, one discovery pass, one composition,
        one recommendation generation — each the existing engine invoked
        exactly as any direct caller invokes it. Authority scores are
        recomputed for every rule this engine has committed."""
        register, grey_areas = self.apply_resolutions(register, grey_areas)

        optimization = build_risk_cases(
            register=register, gross_budget_usd=gross_budget_usd, rate=rate,
            structuring_paths=[], grey_areas=grey_areas,
            delay_weeks=delay_weeks, bridge_rate=bridge_rate,
            jurisdiction_code=jurisdiction_code,
        )
        collection = discover_all_opportunities(
            baseline_jurisdiction=jurisdiction_code, mu_rate=rate, graph=graph,
        )
        composition = compose_production_structures(
            collection, graph, register=register, gross_budget_usd=gross_budget_usd,
            rate=rate, grey_areas=grey_areas,
        )
        recommendations = generate_production_recommendations(
            collection, composition_result=composition, register=register,
            rate=rate, jurisdiction_code=jurisdiction_code,
        )
        scores: dict[str, AuthorityScore] = {}
        for rule_id in sorted(set(self._committed_rule_ids)):
            if self.evidence_graph.rule_is_fully_chained(rule_id):
                scores[rule_id] = score_rule(
                    self.evidence_graph, rule_id, jurisdiction_code, as_of_date=as_of_date,
                )
        return RerunResult(
            optimization=optimization,
            composition=composition,
            recommendations=recommendations,
            authority_scores=scores,
            register_used=register,
            grey_areas_used=grey_areas,
        )
