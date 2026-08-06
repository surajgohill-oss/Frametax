"""
ingestion_classifier.py — Phase E: pure, deterministic classification and
Project-association heuristics for discovered files. No DB access here
(callers pass in already-fetched Project/alias data) and no LLM calls —
keyword/path matching only, exactly as transparent and auditable as every
other rule in this codebase.

Both classify_file() and associate_file() return a confidence alongside
their answer. HIGH may be preselected in review; MEDIUM/LOW must not be
silently applied — the caller (the review UI) is responsible for that
distinction, not this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import NamedTuple

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".bmp"}

# (keywords, category, confidence) — checked in order, first match wins.
# Keywords are matched against the lowercased filename only (never file
# content — no OCR/parsing in this phase).
_CATEGORY_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("screenplay", "script"), "screenplay", "high"),
    (("look book", "lookbook", "look_book"), "lookbook", "high"),
    (("budget",), "budget", "high"),
    (("slide", "deck", "pitch"), "deck", "high"),
    (("schedule", "sched"), "schedule", "high"),
    (("pre-qual", "prequal", "pre_qual"), "pre_qualification", "medium"),
    (("certificate", "final incentive", "final_incentive"), "incentive_certificate", "medium"),
    (("application",), "incentive_application", "medium"),
    (("estimate",), "incentive_estimate", "medium"),
    (("cost report", "cost_report", "final cost"), "cost_report", "medium"),
    (("finance", "financing"), "finance", "medium"),
    (("cast", "talent"), "cast", "medium"),
    (("crew",), "crew", "medium"),
    (("legal", "agreement", "contract", "nda"), "legal", "medium"),
]


class ClassificationResult(NamedTuple):
    category: str
    confidence: str  # "high" | "medium" | "low"


@dataclass(frozen=True)
class AssociationResult:
    project_id: uuid.UUID | None
    confidence: str  # "high" | "medium" | "low" | "none"
    evidence: str


def classify_file(filename: str) -> ClassificationResult:
    """Category from filename + extension only. An image extension is
    always ARTWORK at HIGH confidence — every other category comes from
    keyword matching against the filename; no match falls back to OTHER
    at LOW confidence rather than guessing."""
    ext = PurePosixPath(filename).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return ClassificationResult("artwork", "high")

    lower = filename.lower()
    for keywords, category, confidence in _CATEGORY_RULES:
        if any(kw in lower for kw in keywords):
            return ClassificationResult(category, confidence)
    return ClassificationResult("other", "low")


def associate_file(
    filename: str,
    display_path: str | None,
    projects: list[tuple[uuid.UUID, str]],
    aliases: list[tuple[uuid.UUID, str]],
) -> AssociationResult:
    """Deterministic evidence, checked in the order the brief specifies:
    exact title -> alias -> containing-folder/path -> filename evidence.
    `projects` and `aliases` are (id, text) pairs the caller already
    fetched — this function never touches the DB itself."""
    lower_name = filename.lower()
    lower_path = (display_path or "").lower()
    haystack = f"{lower_path} {lower_name}"

    for project_id, title in projects:
        if title and title.lower() in haystack:
            return AssociationResult(project_id, "high", f"filename/path matches project title \"{title}\"")

    for project_id, alias in aliases:
        if alias and alias.lower() in haystack:
            return AssociationResult(project_id, "high", f"filename/path matches project alias \"{alias}\"")

    # Looser containment: strip spaces/punctuation from both sides so
    # "THE DALE" (a folder name) still matches a path segment like
    # "the-dale" or "TheDale" — still deterministic, just less literal.
    def _slug(s: str) -> str:
        return "".join(ch for ch in s.lower() if ch.isalnum())

    path_slug = _slug(lower_path)
    if path_slug:
        for project_id, title in projects:
            title_slug = _slug(title)
            if title_slug and title_slug in path_slug:
                return AssociationResult(project_id, "medium", f"containing folder loosely matches project title \"{title}\"")

    return AssociationResult(None, "none", "no matching project evidence found in filename or path")
