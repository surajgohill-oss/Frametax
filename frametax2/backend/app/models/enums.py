import enum


class ConfidenceTier(str, enum.Enum):
    VERIFIED = "VERIFIED"      # Reviewed against source document; safe for deterministic recommendation
    PARSED = "PARSED"          # Extracted from authoritative source; not yet fully reviewed
    DISCOVERY = "DISCOVERY"    # Found via search/crawl; not normalized or approved
    SUPERSEDED = "SUPERSEDED"  # Replaced by a newer source document; retained for audit trail


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    STALE = "stale"


class ProgramType(str, enum.Enum):
    TAX_CREDIT = "tax_credit"
    CASH_REBATE = "cash_rebate"
    GRANT = "grant"
    SUBSIDY = "subsidy"
    TAX_EXEMPTION = "tax_exemption"
    REGIONAL_FUND = "regional_fund"
    DISCRETIONARY_FUND = "discretionary_fund"


class CreditBasis(str, enum.Enum):
    QUALIFYING_SPEND = "qualifying_spend"
    QUALIFYING_LABOR = "qualifying_labor"
    TOTAL_BUDGET = "total_budget"
    NET_COST = "net_cost"


class RuleType(str, enum.Enum):
    MINIMUM_TOTAL_BUDGET = "minimum_total_budget"
    MINIMUM_QUALIFIED_SPEND = "minimum_qualified_spend"
    MINIMUM_JURISDICTION_SPEND_PCT = "minimum_jurisdiction_spend_pct"
    MINIMUM_SHOOTING_DAYS_PCT = "minimum_shooting_days_pct"
    REQUIRED_ENTITY_TYPE = "required_entity_type"
    MINIMUM_LOCAL_LABOR_PCT = "minimum_local_labor_pct"
    MINIMUM_CULTURAL_SCORE = "minimum_cultural_score"
    MAXIMUM_ATL_PCT = "maximum_atl_pct"
    MAXIMUM_BUDGET_FOR_UPLIFT = "maximum_budget_for_uplift"
    QUALIFYING_FILM_TEST = "qualifying_film_test"
    SPEND_CAP_PCT = "spend_cap_pct"


class FailAction(str, enum.Enum):
    DISQUALIFY = "disqualify"
    REDUCE_CREDIT = "reduce_credit"
    WARN = "warn"
    FLAG_FOR_REVIEW = "flag_for_review"


class StackingRuleType(str, enum.Enum):
    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"
    SPEND_REDUCTION = "spend_reduction"
    VALUE_CAP = "value_cap"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"


class JurisdictionLevel(str, enum.Enum):
    COUNTRY = "country"
    STATE = "state"
    PROVINCE = "province"
    REGION = "region"
    COUNTY = "county"
    CITY = "city"


class ATLBTLCategory(str, enum.Enum):
    ATL = "atl"
    BTL = "btl"
    POST = "post"
    OTHER = "other"


class SpendCategory(str, enum.Enum):
    # ATL
    ATL_DIRECTOR = "atl_director"
    ATL_WRITER = "atl_writer"
    ATL_PRODUCER = "atl_producer"
    ATL_CAST = "atl_cast"
    ATL_RIGHTS = "atl_rights"
    # BTL Labor
    BTL_CREW_LABOR = "btl_crew_labor"
    BTL_RESIDENT_LABOR = "btl_resident_labor"
    BTL_NONRESIDENT_LABOR = "btl_nonresident_labor"
    # BTL Non-labor
    BTL_EQUIPMENT_RENTAL = "btl_equipment_rental"
    BTL_STAGE_FACILITY = "btl_stage_facility"
    BTL_LOCATION_FEES = "btl_location_fees"
    BTL_SET_CONSTRUCTION = "btl_set_construction"
    BTL_TRANSPORTATION = "btl_transportation"
    BTL_CATERING = "btl_catering"
    VESSEL_MARINE = "vessel_marine"
    # Post
    POST_PRODUCTION = "post_production"
    VFX = "vfx"
    MUSIC = "music"
    SOUND = "sound"
    # Excluded / special
    FINANCE_COSTS = "finance_costs"
    INSURANCE = "insurance"
    COMPLETION_BOND = "completion_bond"
    CONTINGENCY = "contingency"
    #: A residuals reserve is NOT contingency. Contingency is an unspent
    #: allowance against production overrun; a residuals reserve is a funded
    #: obligation to guilds for future exploitation. Collapsing them
    #: overstates contingency and mis-states what is genuinely at risk.
    RESIDUALS_RESERVE = "residuals_reserve"
    PAYROLL_FRINGES = "payroll_fringes"
    # Non-cash compensation
    DEFERMENT = "deferment"
    EQUITY_PARTICIPATION = "equity_participation"
    IN_KIND = "in_kind"
    REINVESTMENT = "reinvestment"
    # Other
    TRAVEL = "travel"
    LODGING = "lodging"
    MISCELLANEOUS = "miscellaneous"


class CompensationType(str, enum.Enum):
    CASH = "cash"
    DEFERRED = "deferred"
    EQUITY = "equity"
    IN_KIND = "in_kind"
    REINVESTMENT = "reinvestment"


class ContributionType(str, enum.Enum):
    CASH = "cash"
    DEFERRED = "deferred"
    EQUITY = "equity"
    IN_KIND = "in_kind"
    SPONSORSHIP = "sponsorship"
    GOVERNMENT_SUPPORT = "government_support"
    VENDOR_FINANCING = "vendor_financing"


class DocumentType(str, enum.Enum):
    BUDGET = "budget"
    SCREENPLAY = "screenplay"
    INCENTIVE_GUIDE = "incentive_guide"
    CULTURAL_TEST = "cultural_test"
    TREATY_TEXT = "treaty_text"
    UNION_AGREEMENT = "union_agreement"
    REGULATION = "regulation"
    OTHER = "other"


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class StructureStatus(str, enum.Enum):
    DRAFT = "draft"
    CALCULATING = "calculating"
    COMPLETE = "complete"
    ERROR = "error"
    ARCHIVED = "archived"


class ProjectLifecycle(str, enum.Enum):
    """
    Canonical Project lifecycle stage — user-controlled only. The engine
    (optimizer, document completeness, incentive qualification) must never
    change this automatically. See CAPABILITY_LEDGER.md "Production Lifecycle
    Rule" — this enum is the persistent backend counterpart of the frontend's
    existing PROJECT_STATUSES (useProjectStatus.js), same five stages, same
    order, same default (EVALUATION).
    """
    EVALUATION = "EVALUATION"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class DocumentScope(str, enum.Enum):
    """Which owner a Document belongs to — exactly one is set, enforced by a CHECK constraint."""
    PROJECT = "project"
    ORGANIZATION = "organization"


class DocumentCategory(str, enum.Enum):
    SCREENPLAY = "screenplay"
    BUDGET = "budget"
    SCHEDULE = "schedule"
    DECK = "deck"
    LOOKBOOK = "lookbook"
    FINANCE = "finance"
    CAST = "cast"
    CREW = "crew"
    INCENTIVE = "incentive"
    LEGAL = "legal"
    ARTWORK = "artwork"
    OTHER = "other"
    # Phase E — historical incentive-evidence categories (the trustworthy
    # corpus a later phase compares MODELED vs PRE-QUALIFIED/ESTIMATED vs
    # APPLIED vs APPROVED vs REALIZED against; this phase only preserves
    # them with correct provenance, never acts on them).
    PRE_QUALIFICATION = "pre_qualification"
    INCENTIVE_ESTIMATE = "incentive_estimate"
    INCENTIVE_APPLICATION = "incentive_application"
    INCENTIVE_CERTIFICATE = "incentive_certificate"
    COST_REPORT = "cost_report"


class DocumentSourceType(str, enum.Enum):
    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"
    UPLOAD = "upload"
    GENERATED = "generated"
    OTHER = "other"


class DocumentSourceStatus(str, enum.Enum):
    OK = "ok"
    UNREACHABLE = "unreachable"
    DELETED_AT_SOURCE = "deleted_at_source"


class ProjectAssetKind(str, enum.Enum):
    ARTWORK = "artwork"
    OTHER = "other"


class ProjectAssetSourceType(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTED_FROM_DECK = "extracted_from_deck"
    EXTRACTED_FROM_LOOKBOOK = "extracted_from_lookbook"
    EXTRACTED_FROM_SCREENPLAY = "extracted_from_screenplay"
    DISCOVERED_IMAGE = "discovered_image"
    GENERATED = "generated"


class ProjectFactSourceType(str, enum.Enum):
    EXTRACTED = "extracted"
    USER_OVERRIDE = "user_override"
    # A fact hand-recovered/sourced during a prior migration (e.g. cross-
    # verified against Wikipedia/IMDb and the production's own documents,
    # per little_utopia_people.py) rather than produced by an automated
    # document-extraction pipeline or a user's own in-app correction.
    # Kept distinct so provenance is never misrepresented as either of the
    # other two — see Phase C "Little Utopia Persistence Migration".
    RECOVERED_DEMO_STATE = "recovered_demo_state"


class FinalResultStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    APPLIED = "applied"
    APPROVED = "approved"
    REALIZED = "realized"


class IngestionCandidateStatus(str, enum.Enum):
    """A staged candidate's lifecycle. Nothing becomes a canonical Document
    until COMMITTED — DISCOVER/CLASSIFY/ASSOCIATE only ever write to this
    staging row, never to documents/document_versions directly."""
    PENDING = "pending"
    COMMITTED = "committed"
    IGNORED = "ignored"


class MatchConfidence(str, enum.Enum):
    """Shared by both category classification and Project association —
    same three-tier vocabulary, same meaning: HIGH may be preselected in
    review; MEDIUM/LOW always require explicit user confirmation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class VersionStatus(str, enum.Enum):
    """What a candidate's checksum tells us relative to already-persisted
    DocumentVersions — never a claim about temporal ordering unless the
    evidence actually supports one."""
    NEW_DOCUMENT = "new_document"
    EXACT_DUPLICATE = "exact_duplicate"
    POSSIBLE_NEW_VERSION = "possible_new_version"
