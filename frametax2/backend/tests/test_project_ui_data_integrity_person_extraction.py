"""
PROJECT_UI_DATA_INTEGRITY, Phase 3 whitelist item 3 -- document-person
extraction. Pure logic over synthetic page text (no DB, no real
document) -- proves the generic patterns work for ANY production, never
a hardcoded name. Real evidence against F#K Valentine's Day's own
documents (Steve Bencich, Mark Gantt) is reported separately, not pinned
here as a brittle golden-file assertion.
"""
from __future__ import annotations

from app.ingestion.document_person_extractor import extract_credits_from_pages


def test_screenplay_byline_and_deck_trailer_lines_extract_names_and_roles_generically():
    pages = [
        "SOME MOVIE\nby\nJane Smith\n2/1/2024\n",
        "Jane Smith is a celebrated writer and producer with decades of experience.\n"
        "Jane Smith - writer/producer\n"
        "John Doe is one of the industry's most versatile directors.\n"
        "John Doe - Director\n",
    ]
    credits = extract_credits_from_pages(pages)
    found = {(c.name, c.role) for c in credits}
    assert ("Jane Smith", "writer") in found
    assert ("Jane Smith", "producer") in found
    assert ("John Doe", "director") in found
    # Real evidence is retained per credit, never fabricated.
    for c in credits:
        assert c.evidence_text
        assert c.page_number is not None


def test_extracted_credits_never_carry_a_nationality_or_residency_field():
    """The extractor structurally cannot produce a nationality/residency
    fact -- it only ever reads a name and a role from real printed text.
    Missing nationality/residency is left for the existing
    canonical_production_view.py missing_inputs disclosure (a separate,
    already-wired mechanism) to surface as a real question, never
    inferred here or anywhere in this extractor."""
    pages = ["TITLE\nby\nAlex Rivera\n"]
    credits = extract_credits_from_pages(pages)
    assert credits
    for c in credits:
        assert not hasattr(c, "nationality")
        assert not hasattr(c, "residency")
        assert not hasattr(c, "primary_nationality")


def test_unrecognized_role_text_is_dropped_never_fabricated():
    pages = ["Someone Random - Caterer\n"]
    credits = extract_credits_from_pages(pages)
    assert credits == [], "a role this table doesn't recognize must never be guessed into a canonical role"
