"""
Phase E — pure classification/association logic tests. No DB, no
fixtures beyond plain Python values — see app/services/ingestion_classifier.py.
"""
from __future__ import annotations

import uuid

from app.services.ingestion_classifier import classify_file, associate_file


def test_classify_image_is_always_artwork_high_confidence():
    assert classify_file("utopia.png") == ("artwork", "high")
    assert classify_file("SOME_RANDOM_NAME.JPG") == ("artwork", "high")


def test_classify_keyword_matches():
    assert classify_file("The Little Utopia Budget Mauritius.pdf") == ("budget", "high")
    assert classify_file("OtherwiseEngaged_Slide.pptx") == ("deck", "high")
    assert classify_file("Production Schedule v3.xlsx") == ("schedule", "high")
    assert classify_file("Georgia Pre-Qualification Letter.pdf") == ("pre_qualification", "medium")
    assert classify_file("Incentive Estimate Letter.pdf") == ("incentive_estimate", "medium")
    assert classify_file("Final Incentive Certificate.pdf") == ("incentive_certificate", "medium")
    assert classify_file("Final Cost Report.xlsx") == ("cost_report", "medium")


def test_classify_unrecognized_is_other_low_confidence():
    result = classify_file("random_document_xyz123.docx")
    assert result.category == "other"
    assert result.confidence == "low"


def test_associate_exact_title_match_is_high_confidence():
    little_utopia_id = uuid.uuid4()
    dale_id = uuid.uuid4()
    projects = [(little_utopia_id, "The Little Utopia"), (dale_id, "The Dale")]
    result = associate_file("The Little Utopia 1_30_26.pdf", None, projects, [])
    assert result.project_id == little_utopia_id
    assert result.confidence == "high"


def test_associate_alias_match_is_high_confidence():
    project_id = uuid.uuid4()
    result = associate_file("the boat - screenplay draft.pdf", None, [(project_id, "The Little Utopia")], [(project_id, "The Boat")])
    assert result.project_id == project_id
    assert result.confidence == "high"


def test_associate_folder_path_exact_substring_is_high_confidence():
    """A folder literally named after the project title is exact-substring
    evidence, not just loose evidence — HIGH, not MEDIUM."""
    project_id = uuid.uuid4()
    projects = [(project_id, "The Dale")]
    result = associate_file("Budget.pdf", "/Users/x/PROJECTS/THE DALE/Budget.pdf", projects, [])
    assert result.project_id == project_id
    assert result.confidence == "high"


def test_associate_folder_path_loose_match_is_medium_confidence():
    """No space/punctuation between words in the folder name defeats the
    exact-substring check, so this only matches via the looser
    alphanumeric-slug comparison — MEDIUM, not HIGH."""
    project_id = uuid.uuid4()
    projects = [(project_id, "The Dale")]
    result = associate_file("Budget.pdf", "/Users/x/PROJECTS/THEDALE2026/Budget.pdf", projects, [])
    assert result.project_id == project_id
    assert result.confidence == "medium"


def test_associate_no_match_returns_none_confidence():
    result = associate_file("random_file.pdf", "/Users/x/Downloads/random_file.pdf", [(uuid.uuid4(), "The Dale")], [])
    assert result.project_id is None
    assert result.confidence == "none"


def test_associate_never_silently_high_confidence_without_evidence():
    """A file with no title/alias/path evidence must never come back HIGH
    — only exact title/alias matches are allowed that confidence tier."""
    result = associate_file("untitled.pdf", "", [(uuid.uuid4(), "Some Project")], [])
    assert result.confidence != "high"
