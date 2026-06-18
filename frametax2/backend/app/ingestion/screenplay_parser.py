"""
screenplay_parser.py

Extracts structured elements from screenplay raw text.
Step 1 (deterministic): scene heading extraction, character name extraction, page chunking.
Step 2 (LLM-assisted): location identification, environment classification, writer nationality.

Step 2 is isolated and always marked is_llm_extracted=True.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ScreenplayChunk:
    chunk_index: int
    start_page: int | None
    end_page: int | None
    text: str
    token_estimate: int


@dataclass
class ExtractedElement:
    element_type: str
    value: str
    context_excerpt: str | None = None
    page_reference: int | None = None
    is_llm_extracted: bool = False
    extraction_confidence: float | None = None


@dataclass
class ScreenplayParseResult:
    filename: str
    page_count: int
    word_count: int
    chunks: list[ScreenplayChunk]
    extracted_elements: list[ExtractedElement]
    scene_headings: list[str]
    character_names: list[str]
    parse_warnings: list[str] = field(default_factory=list)


# Scene heading regex: INT./EXT. followed by location description
_SCENE_HEADING_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.?)\s+(.+?)(?:\s+-\s+.*)?$",
    re.MULTILINE | re.IGNORECASE,
)

# Character name: ALL CAPS line in dialogue context (rough heuristic)
_CHARACTER_NAME_RE = re.compile(r"^\s{15,}([A-Z][A-Z\s\.\-']{2,30})\s*$", re.MULTILINE)

# Page number markers
_PAGE_RE = re.compile(r"^\d+\.\s*$", re.MULTILINE)

CHUNK_SIZE_TOKENS = 1500
CHARS_PER_TOKEN = 4


def parse_screenplay_text(
    raw_text: str,
    filename: str,
    page_count: int | None = None,
) -> ScreenplayParseResult:
    """
    Deterministic extraction pass on screenplay raw text.
    Returns scene headings, character names, and text chunks.
    """
    word_count = len(raw_text.split())
    pc = page_count or max(1, word_count // 200)

    # Extract scene headings
    scene_headings = [m.group(0).strip() for m in _SCENE_HEADING_RE.finditer(raw_text)]

    # Extract character names (deduplicated)
    char_matches = {m.group(1).strip() for m in _CHARACTER_NAME_RE.finditer(raw_text)}
    # Filter out false positives (very short or common words)
    stop_words = {"CONTINUED", "CUT TO", "FADE IN", "FADE OUT", "SMASH CUT", "DISSOLVE TO"}
    character_names = sorted(char_matches - stop_words)

    # Chunk the screenplay for LLM context windows
    chunks = _chunk_text(raw_text, chunk_size_tokens=CHUNK_SIZE_TOKENS)

    # Extract location elements from scene headings (deterministic)
    extracted_elements: list[ExtractedElement] = []
    for heading in scene_headings:
        m = _SCENE_HEADING_RE.match(heading)
        if m:
            location = m.group(2).strip()
            extracted_elements.append(ExtractedElement(
                element_type="location",
                value=location,
                context_excerpt=heading,
                is_llm_extracted=False,
                extraction_confidence=0.9,
            ))

    return ScreenplayParseResult(
        filename=filename,
        page_count=pc,
        word_count=word_count,
        chunks=chunks,
        extracted_elements=extracted_elements,
        scene_headings=scene_headings,
        character_names=character_names,
    )


def _chunk_text(text: str, chunk_size_tokens: int = 1500) -> list[ScreenplayChunk]:
    """Split text into chunks for LLM processing."""
    chunk_size_chars = chunk_size_tokens * CHARS_PER_TOKEN
    chunks: list[ScreenplayChunk] = []
    lines = text.split("\n")
    current_chunk: list[str] = []
    current_chars = 0
    chunk_idx = 0

    for line in lines:
        current_chunk.append(line)
        current_chars += len(line) + 1
        if current_chars >= chunk_size_chars:
            chunk_text = "\n".join(current_chunk)
            chunks.append(ScreenplayChunk(
                chunk_index=chunk_idx,
                start_page=None,
                end_page=None,
                text=chunk_text,
                token_estimate=current_chars // CHARS_PER_TOKEN,
            ))
            current_chunk = []
            current_chars = 0
            chunk_idx += 1

    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        chunks.append(ScreenplayChunk(
            chunk_index=chunk_idx,
            start_page=None,
            end_page=None,
            text=chunk_text,
            token_estimate=current_chars // CHARS_PER_TOKEN,
        ))

    return chunks
