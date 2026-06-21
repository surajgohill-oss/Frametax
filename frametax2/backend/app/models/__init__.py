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
)
