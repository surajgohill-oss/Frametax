"""
Ingestion acceptance closeout (2026-09-17): genuine Final Draft (.fdx) XML
parsing. Reproduced live via a real API round trip (create project ->
discover -> commit -> SA-1 pipeline) that a real Final Draft-shaped .fdx
file produced zero scenes, because the raw XML markup was handed straight
to the plain-text screenplay structural parser. No DB needed -- pure
function tests, same convention as test_budget_parser_xlsx.py.
"""
from __future__ import annotations

from app.ingestion.fdx_extractor import extract_text_from_fdx

_REAL_SHAPED_FDX = """<?xml version="1.0" encoding="UTF-8"?>
<FinalDraft DocumentType="Script" Template="No" Version="1">
<Content>
<Paragraph Type="Scene Heading"><Text>1 EXT. COASTAL HIGHWAY - DAY</Text></Paragraph>
<Paragraph Type="Action"><Text>A battered pickup truck grinds along a cliff road.</Text></Paragraph>
<Paragraph Type="Character"><Text>mara</Text></Paragraph>
<Paragraph Type="Dialogue"><Text>We're losing </Text><Text AdornmentStyle="Bold">daylight</Text><Text>.</Text></Paragraph>
<Paragraph Type="Character"><Text>DRIVER</Text></Paragraph>
<Paragraph Type="Dialogue"><Text>Then stop talking and watch the road.</Text></Paragraph>
<Paragraph Type="Scene Heading"><Text>2 INT. ROADSIDE DINER - NIGHT</Text></Paragraph>
<Paragraph Type="Action"><Text>Fluorescent hum. A dog sleeps under the counter.</Text></Paragraph>
</Content>
</FinalDraft>
"""


def test_real_shaped_fdx_extracts_scene_headings_and_dialogue():
    text = extract_text_from_fdx(_REAL_SHAPED_FDX)
    assert "1 EXT. COASTAL HIGHWAY - DAY" in text
    assert "2 INT. ROADSIDE DINER - NIGHT" in text
    assert "MARA" in text  # character cue upper-cased regardless of source case
    assert "DRIVER" in text
    assert "no <Paragraph" not in text
    assert "<Text" not in text


def test_split_text_runs_within_one_paragraph_are_joined_not_separated():
    """Final Draft splits one paragraph's text across multiple <Text>
    elements for inline style spans (bold/italic/underline) -- these must
    never become separate lines or introduce spurious whitespace breaks
    mid-sentence."""
    text = extract_text_from_fdx(_REAL_SHAPED_FDX)
    assert "We're losing daylight." in text


def test_structural_parser_finds_real_scenes_from_fdx_output():
    """The actual downstream consumer: screenplay_structural_parser must
    recognize the extracted text as real scene structure, not just that
    the extractor's own output looks plausible in isolation."""
    from app.ingestion.screenplay_structural_parser import parse_structure

    text = extract_text_from_fdx(_REAL_SHAPED_FDX)
    result = parse_structure(text)
    assert len(result.scenes) == 2
    characters = {c.canonical_name for c in result.characters}
    assert "MARA" in characters
    assert "DRIVER" in characters


def test_non_xml_content_falls_back_to_original_text_unchanged():
    """A plain-text screenplay saved with a .fdx extension (the one shape
    the prior naive read-as-text behavior ever worked for, and the shape
    this repo's own existing FDX fixture uses) must keep working exactly
    as before -- never regressed by the new XML-aware path."""
    plain = "1 EXT. COASTAL HIGHWAY - DAY\n\nA battered pickup truck grinds along a cliff road."
    assert extract_text_from_fdx(plain) == plain


def test_bytes_input_is_decoded():
    text = extract_text_from_fdx(_REAL_SHAPED_FDX.encode("utf-8"))
    assert "1 EXT. COASTAL HIGHWAY - DAY" in text


def test_empty_content_element_returns_empty_string_not_raw_xml():
    empty = '<?xml version="1.0"?><FinalDraft><Content></Content></FinalDraft>'
    assert extract_text_from_fdx(empty) == ""


def test_administrative_paragraph_types_with_no_text_are_skipped():
    xml_doc = (
        '<?xml version="1.0"?><FinalDraft><Content>'
        '<Paragraph Type="Scene Heading"><Text>1 EXT. PARK - DAY</Text></Paragraph>'
        '<Paragraph Type="Action"></Paragraph>'
        "</Content></FinalDraft>"
    )
    text = extract_text_from_fdx(xml_doc)
    assert text == "1 EXT. PARK - DAY"
