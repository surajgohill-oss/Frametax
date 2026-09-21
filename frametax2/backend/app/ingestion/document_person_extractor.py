"""
document_person_extractor.py

PROJECT_UI_DATA_INTEGRITY (2026-09-21) — the smallest reusable, generic
document-person extractor, wired through the existing ingestion
architecture (app/ingestion/*). Finds real credited names/roles in a
document's own extracted text using generic, project-agnostic patterns
observed across real screenplay and pitch-deck conventions — never a
hardcoded per-production name or title.

Two patterns, in order of confidence:

  1. Screenplay title-page byline — "TITLE\\nby\\nNAME" (or "written by
     NAME"), always near the start of a screenplay's own extracted text.
     Role: writer.
  2. Compact credit-trailer line — "NAME - ROLE(S)" or "NAME – ROLE(S)"
     on its own line (the convention a pitch deck's bio section uses
     after each person's paragraph, e.g. "Mark Gantt - Director",
     "Steve Bencich - writer/producer"). ROLE(S) may be slash- or
     comma-separated; each is mapped to the canonical ProjectPerson.role
     vocabulary (writer/director/producer/lead_cast/dop/editor/composer)
     via a small alias table — never a fabricated role for text this
     table doesn't recognize.

Never infers nationality, residency, or any biographical fact beyond the
name and role actually printed — that is a separate, explicitly out-of-
scope concern (see canonical_production_view.py's own missing_inputs
disclosure, which already asks the resulting question once a name with
no nationality exists).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

#: The exact ProjectPerson.role / TalentProfile.role vocabulary
#: (canonical_production_view.py's own _PEOPLE_ROLE_TO_BUCKET) — never a
#: role string outside this set is ever returned.
_ROLE_ALIASES: dict[str, str] = {
    "writer": "writer", "screenwriter": "writer", "screenplay by": "writer",
    "co-writer": "writer", "writer/producer": "writer",
    "director": "director", "co-director": "director",
    "producer": "producer", "executive producer": "producer", "producers": "producer",
    "co-producer": "producer", "line producer": "producer",
    "lead cast": "lead_cast", "cast": "lead_cast", "star": "lead_cast", "starring": "lead_cast",
    "director of photography": "dop", "dop": "dop", "cinematographer": "dop",
    "editor": "editor", "composer": "composer",
}

#: A single credit-trailer line's role segment can only be this long
#: before it's almost certainly not a role list (avoids false positives
#: on ordinary prose lines that happen to contain a hyphen).
_MAX_ROLE_SEGMENT_LEN = 40

_NAME_RE = r"[A-Z][A-Za-z.'’-]+(?: [A-Z][A-Za-z.'’-]+){1,3}"
_TRAILER_LINE_RE = re.compile(rf"^\s*({_NAME_RE})\s*[-–—]\s*([A-Za-z/, ]+?)\s*$")
_BYLINE_RE = re.compile(rf"^\s*(?:written\s+)?by\s*\n\s*({_NAME_RE})\s*$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class ExtractedPersonCredit:
    name: str
    role: str  # canonical vocabulary value
    evidence_text: str  # the exact source line/snippet matched
    page_number: int | None  # 1-indexed; None when the match isn't page-scoped


def _roles_from_segment(segment: str) -> list[str]:
    """Splits a "writer/producer" or "Writer, Director" segment into
    canonical roles, dropping any token this table doesn't recognize
    (never fabricating a role for unrecognized text)."""
    if len(segment) > _MAX_ROLE_SEGMENT_LEN:
        return []
    tokens = re.split(r"[/,]| and ", segment)
    roles: list[str] = []
    for token in tokens:
        canonical = _ROLE_ALIASES.get(token.strip().lower())
        if canonical and canonical not in roles:
            roles.append(canonical)
    return roles


def extract_credits_from_pages(pages: list[str]) -> list[ExtractedPersonCredit]:
    """`pages`: one string per page, 1-indexed page_number in the result
    (page_extractor.pdf_extractor.PDFExtractionResult.pages' own order).
    Deduplicates identical (name, role) pairs, keeping the FIRST evidence
    found (earliest page)."""
    seen: set[tuple[str, str]] = set()
    out: list[ExtractedPersonCredit] = []

    # Pattern 1: screenplay title-page byline — scoped to the first page
    # only (a screenplay's OWN title page), never scanned deeper (a mid-
    # script "by" — e.g. dialogue — must never match).
    if pages:
        m = _BYLINE_RE.search(pages[0])
        if m:
            name = m.group(1).strip()
            key = (name, "writer")
            if key not in seen:
                seen.add(key)
                out.append(ExtractedPersonCredit(
                    name=name, role="writer", evidence_text=m.group(0).strip(), page_number=1,
                ))

    # Pattern 2: compact "Name - Role(s)" credit-trailer lines, anywhere.
    for page_number, page_text in enumerate(pages, start=1):
        for line in page_text.splitlines():
            m = _TRAILER_LINE_RE.match(line)
            if not m:
                continue
            name, role_segment = m.group(1).strip(), m.group(2).strip()
            for role in _roles_from_segment(role_segment):
                key = (name, role)
                if key in seen:
                    continue
                seen.add(key)
                out.append(ExtractedPersonCredit(
                    name=name, role=role, evidence_text=line.strip(), page_number=page_number,
                ))
    return out


def extract_credits_from_text(raw_text: str) -> list[ExtractedPersonCredit]:
    """Convenience entry point for a document with no real per-page
    split on file (treats the whole text as one page)."""
    return extract_credits_from_pages([raw_text])
