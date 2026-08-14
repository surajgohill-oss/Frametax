"""
SQLAlchemy models — all imported here for Alembic autodiscovery.
"""
from app.db.base import Base  # noqa: F401

from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.document import SourceDocument  # noqa: F401
from app.models.jurisdiction import Jurisdiction  # noqa: F401
from app.models.incentive import (  # noqa: F401
    IncentiveProgram,
    IncentiveRule,
    QualifyingSpendCategory,
    ProgramUplift,
    QualificationTest,
    QualificationTestRule,
    LegalStackingRule,
)
from app.models.cost import LocalCostBenchmark, UnionFringeRule  # noqa: F401
from app.models.talent import TalentProfile, TalentQualificationAttribute  # noqa: F401
from app.models.budget import BudgetDocument, BudgetLineItem  # noqa: F401
from app.models.screenplay import (  # noqa: F401
    ScreenplayDocument,
    ScreenplayChunk,
    ExtractedScriptElement,
    Scene,
    Character,
)
from app.models.production_requirement import (  # noqa: F401
    ProductionRequirement,
    ProductionAssumption,
)
from app.models.production import ProductionStructure, StructureCalculationResult  # noqa: F401
from app.models.fx import FXRate  # noqa: F401
from app.models.ingestion import IngestionJob  # noqa: F401
from app.models.contribution import ProductionContribution  # noqa: F401
from app.models.program_intelligence import (  # noqa: F401
    ProgramAdminDetails,
    ProgramSpendTreatment,
    HistoricalProductionBenchmark,
    BenchmarkSpendItem,
    BenchmarkIngestionLog,
    FundEconomics,
)

# Project Library Phase B — persistence foundation
from app.models.project_alias import ProjectAlias  # noqa: F401
from app.models.library_document import Document, DocumentVersion, DocumentVersionSource  # noqa: F401
from app.models.project_asset import ProjectAsset  # noqa: F401
from app.models.project_fact import ProjectFact  # noqa: F401
from app.models.ingestion_candidate import IngestionCandidate  # noqa: F401
from app.models.project_activity import ProjectActivity  # noqa: F401
from app.models.project_location_requirement import ProjectLocationRequirement  # noqa: F401
from app.models.project_person import ProjectPerson  # noqa: F401
from app.models.final_production_result import FinalProductionResult  # noqa: F401
