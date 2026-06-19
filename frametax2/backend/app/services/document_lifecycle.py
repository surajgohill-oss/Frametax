"""
document_lifecycle.py

Lightweight helpers for managing SourceDocument lifecycle transitions.

Lifecycle:  DISCOVERY → PARSED → VERIFIED → SUPERSEDED

Rules:
  - Promotion is forward-only: DISCOVERY→PARSED→VERIFIED. No skipping.
  - Only VERIFIED documents can be superseded (older VERIFIED replaced by newer one).
  - PARSED documents can be superseded if a newer authoritative version replaces them.
  - DISCOVERY documents are deleted or replaced, not superseded.
  - supersede_document() sets superseded_by_id and marks tier=SUPERSEDED.
  - All transitions record who made the change via updated_at; caller passes session.

No LLM calls. All transitions are deterministic and explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

TIER_ORDER = {"DISCOVERY": 0, "PARSED": 1, "VERIFIED": 2, "SUPERSEDED": -1}


@dataclass
class PromotionReadiness:
    """Report on whether a document is ready to be promoted to the next tier."""
    document_id: str
    current_tier: str
    target_tier: str
    is_ready: bool
    blockers: list[str]
    warnings: list[str]


def get_next_tier(current_tier: str) -> Optional[str]:
    """Return the next tier in the promotion chain, or None if already at top."""
    chain = ["DISCOVERY", "PARSED", "VERIFIED"]
    try:
        idx = chain.index(current_tier)
        return chain[idx + 1] if idx + 1 < len(chain) else None
    except ValueError:
        return None


def get_promotion_readiness(
    document_id: str,
    current_tier: str,
    title: str,
    source_url: Optional[str],
    raw_text: Optional[str],
    authority_name: Optional[str],
    effective_from: Optional[str],
    linked_rule_count: int = 0,
) -> PromotionReadiness:
    """
    Evaluate whether a SourceDocument is ready to be promoted to the next tier.
    No DB writes — pure analysis for display or pre-commit validation.
    """
    target_tier = get_next_tier(current_tier)
    blockers: list[str] = []
    warnings: list[str] = []

    if target_tier is None:
        return PromotionReadiness(
            document_id=document_id,
            current_tier=current_tier,
            target_tier="(none)",
            is_ready=False,
            blockers=["Document is already at maximum tier (VERIFIED) or is SUPERSEDED"],
            warnings=[],
        )

    if target_tier == "PARSED":
        if not source_url:
            blockers.append("source_url is required before promoting to PARSED")
        if not authority_name:
            warnings.append("authority_name is missing — recommended before PARSED promotion")
        if not effective_from:
            warnings.append("effective_from date is missing")

    elif target_tier == "VERIFIED":
        if not raw_text:
            blockers.append("raw_text must be populated (document must be ingested) before VERIFIED")
        if not source_url:
            blockers.append("source_url is required for VERIFIED")
        if not effective_from:
            blockers.append("effective_from date is required for VERIFIED")
        if linked_rule_count == 0:
            warnings.append("No incentive rules linked to this document — verify linkage is complete")

    return PromotionReadiness(
        document_id=document_id,
        current_tier=current_tier,
        target_tier=target_tier,
        is_ready=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
    )


def validate_supersession(
    document_id: str,
    current_tier: str,
    replacement_id: str,
    replacement_tier: str,
) -> tuple[bool, list[str]]:
    """
    Validate that supersession of document_id by replacement_id is valid.
    Returns (ok, errors).
    """
    errors: list[str] = []

    if document_id == replacement_id:
        errors.append("A document cannot supersede itself")

    if current_tier == "SUPERSEDED":
        errors.append("Document is already SUPERSEDED")

    if current_tier == "DISCOVERY":
        errors.append("DISCOVERY documents should be deleted or updated, not superseded")

    if replacement_tier not in ("PARSED", "VERIFIED"):
        errors.append(f"Replacement document must be PARSED or VERIFIED, got {replacement_tier!r}")

    return len(errors) == 0, errors
