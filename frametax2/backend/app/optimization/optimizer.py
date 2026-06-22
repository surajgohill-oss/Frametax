"""
optimizer.py — Phase E top-level optimization API.

Orchestrates the full pipeline:
  Phase 2: enumerate_structures()    → StructureCandidate list
  Phase 3: filter_structures()       → EligibleStructure list
  Phase 4: score_all_structures()    → ScoredStructure list (ranked)
  Phase 5: explain_structure()       → StructureExplanation per structure

Usage:
  from app.optimization import run_optimizer

  result = run_optimizer(
      jurisdiction_codes=["MT", "EU", "GB"],
      total_budget_usd=10_000_000,
      qualifying_spend_pct=0.70,
      production_type="feature",
  )

  for s in result.ranked_structures[:5]:
      print(f"#{s.rank}: {s.structure_id} — ${s.net_producer_benefit_usd:,.0f}")

No DB access. No AI calls. Deterministic.
"""
from __future__ import annotations

from app.data.global_inventory import ALL_PROGRAMS, GlobalProgramEntry
from app.optimization.enumerate_structures import enumerate_structures
from app.optimization.score_structures import (
    explain_structure,
    filter_structures,
    score_all_structures,
)
from app.optimization.types import OptimizationResult, ScoredStructure, StructureExplanation

OPTIMIZER_VERSION = "1.0.0"


def run_optimizer(
    jurisdiction_codes: list[str],
    total_budget_usd: float,
    qualifying_spend_pct: float = 0.65,
    production_type: str = "feature",
    max_grants_per_structure: int = 2,
    include_split_jurisdictions: bool = True,
    all_programs: list[GlobalProgramEntry] | None = None,
    top_n: int = 20,
) -> OptimizationResult:
    """
    Run the Phase E optimizer for a given set of candidate jurisdictions.

    Parameters
    ----------
    jurisdiction_codes            ISO codes of candidate filming jurisdictions
    total_budget_usd              Total production budget in USD
    qualifying_spend_pct          Fraction of budget eligible for incentives (0–1)
    production_type               'feature' | 'documentary' | 'series' | 'animation'
    max_grants_per_structure      Max grant programs per structure (default 2)
    include_split_jurisdictions   Include 2-jurisdiction split structures
    all_programs                  Override GlobalProgramEntry list (for testing)
    top_n                         Maximum ranked structures to return (default 20)

    Returns
    -------
    OptimizationResult with ranked structures and explanations
    """
    if all_programs is None:
        all_programs = ALL_PROGRAMS

    warnings: list[str] = []

    # Validate inputs
    if total_budget_usd <= 0:
        warnings.append("total_budget_usd must be > 0; defaulting to 1,000,000.")
        total_budget_usd = 1_000_000.0

    if not 0.0 < qualifying_spend_pct <= 1.0:
        warnings.append(
            f"qualifying_spend_pct {qualifying_spend_pct} out of range; defaulting to 0.65."
        )
        qualifying_spend_pct = 0.65

    # Filter inventory to production_type if applicable
    # (documentary funds only for documentary; etc.)
    filtered_programs = _filter_by_production_type(all_programs, production_type)

    # Phase 2 — Enumerate structures
    candidates = enumerate_structures(
        jurisdiction_codes=jurisdiction_codes,
        all_programs=filtered_programs,
        max_grants_per_structure=max_grants_per_structure,
        include_split_jurisdictions=include_split_jurisdictions,
    )

    if not candidates:
        warnings.append(
            f"No structures enumerated for jurisdictions: {jurisdiction_codes}. "
            "Check that jurisdiction codes match ALL_PROGRAMS entries."
        )
        return OptimizationResult(
            jurisdiction_codes=jurisdiction_codes,
            total_budget_usd=total_budget_usd,
            qualifying_spend_pct=qualifying_spend_pct,
            production_type=production_type,
            structures_enumerated=0,
            structures_eligible=0,
            structures_ineligible=0,
            ranked_structures=[],
            explanations=[],
            warnings=warnings,
            optimizer_version=OPTIMIZER_VERSION,
        )

    # Phase 3 — Filter eligible structures
    eligible, ineligible = filter_structures(candidates)

    # Phase 4 — Score and rank
    scored = score_all_structures(
        eligible_structures=eligible,
        total_budget_usd=total_budget_usd,
        qualifying_spend_pct=qualifying_spend_pct,
    )

    # Limit to top_n results
    top_structures = scored[:top_n]

    # Phase 5 — Generate explanations
    explanations: list[StructureExplanation] = []
    for s in top_structures:
        exp = explain_structure(s)
        exp.economics["total_budget_usd"] = total_budget_usd
        explanations.append(exp)

    return OptimizationResult(
        jurisdiction_codes=jurisdiction_codes,
        total_budget_usd=total_budget_usd,
        qualifying_spend_pct=qualifying_spend_pct,
        production_type=production_type,
        structures_enumerated=len(candidates),
        structures_eligible=len(eligible),
        structures_ineligible=len(ineligible),
        ranked_structures=top_structures,
        explanations=explanations,
        warnings=warnings,
        optimizer_version=OPTIMIZER_VERSION,
    )


def _filter_by_production_type(
    programs: list[GlobalProgramEntry],
    production_type: str,
) -> list[GlobalProgramEntry]:
    """
    Filter programs by production type notes/eligibility.
    Conservative: only exclude if we know a program explicitly excludes the type.
    """
    if production_type == "documentary":
        # Some funds prefer documentary; don't exclude any
        return programs

    if production_type == "feature":
        # Exclude ITVS (PBS-linked documentary fund only)
        return [
            p for p in programs
            if "itvs" not in p.program_name.lower()
            and "documentary fund" not in p.program_name.lower()
            or "feature" in p.program_name.lower()
        ]

    # For series, animation, commercial: include all (conservative)
    return programs
