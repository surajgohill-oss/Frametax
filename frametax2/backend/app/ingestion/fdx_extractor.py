"""
fdx_extractor.py

Genuine Final Draft (.fdx) parsing. Final Draft's own file format is XML
(<FinalDraft><Content><Paragraph Type="...&quot;"><Text>...</Text></Paragraph>...),
never plain text -- a real .fdx export from Final Draft (or any compatible
screenwriting tool) always carries this markup.

Ingestion acceptance closeout (2026-09-17): confirmed live via a real API
round trip that `.fdx` had never been genuinely parsed anywhere in this
codebase -- `script_analysis_service.py`'s own FDX branch (and material_
routing.py's `_read_source_text`) read the file with `Path.read_text()`
and handed the RAW XML straight to the plain-text screenplay structural
parser (screenplay_structural_parser.py), which matches scene headings/
character cues against line-based conventions ("1 EXT. LOCATION - DAY" on
its own line) -- markup like `<Paragraph Type="Scene Heading"><Text>1
EXT. LOCATION - DAY</Text></Paragraph>` never matches those patterns, so
a real Final Draft file always produced zero scenes, exactly the same
class of defect the XLSX-decoded-as-text fix in this same closeout
replaced. The only existing FDX fixture in this repo (test_production_
package_intelligence.py) uses a `.fdx` FILENAME over plain-text CONTENT,
which is why this was never caught by any existing test.

Extracts each <Paragraph> into the ONE-LINE-PER-PARAGRAPH plain-text
convention the structural parser already expects, joining a paragraph's
own <Text> runs (Final Draft splits one paragraph's text across multiple
<Text> elements for inline style spans -- bold/italic/underline -- never
splitting a scene heading or a character cue's actual text mid-word).
Character cues are upper-cased on the way out (matching the structural
parser's own _CUE_RE expectation, and Final Draft's own on-screen
convention) even if the source XML stored mixed case.

A file that isn't valid XML (including a plain-text file some other tool
saved with a `.fdx` extension) is returned unchanged, byte-for-byte --
this is a strict upgrade, never a narrowing: the prior "read as plain
text" behavior is preserved exactly for the one case it ever worked for.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

#: Final Draft paragraph types that carry real screenplay text. Anything
#: else (e.g. a "Cast List"/"Revision" administrative section, none of
#: which appear inside <Content>) is skipped by construction since only
#: <Content>'s own direct <Paragraph> children are ever read.
_CHARACTER_TYPE = "Character"


def extract_text_from_fdx(content: str | bytes) -> str:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        # Not real XML -- either a plain-text screenplay saved with a
        # .fdx extension (the one shape the prior behavior worked for) or
        # a genuinely corrupt file. Either way, never guess: return the
        # original content unchanged, exactly the prior read-as-text
        # behavior, so a real plain-text fixture keeps working.
        return content

    content_el = root.find("Content")
    if content_el is None:
        return content

    # screenplay_structural_parser.parse_structure()'s own cue-detection
    # loop requires a Character cue's dialogue to be the VERY NEXT non-
    # blank... no -- the ADJACENT line, with no blank line between them
    # (a blank line immediately after a cue is read as "cue not followed
    # by dialogue" and skipped, matching real screenplay formatting
    # convention where a character name sits directly above their
    # dialogue). Every other paragraph boundary gets a blank line, same
    # as standard screenplay manuscript format.
    parts: list[str] = []
    prev_type: str | None = None
    for para in content_el.findall("Paragraph"):
        text = "".join(t.text or "" for t in para.iter("Text")).strip()
        if not text:
            continue
        ptype = para.get("Type")
        if ptype == _CHARACTER_TYPE:
            text = text.upper()
        if prev_type == _CHARACTER_TYPE and ptype in ("Dialogue", "Parenthetical"):
            parts.append("\n" + text)
        else:
            parts.append(("\n\n" if parts else "") + text)
        prev_type = ptype

    if not parts:
        # Valid XML, real <Content>, but nothing extractable (e.g. an
        # empty document, or a schema this parser doesn't recognize) --
        # never silently discard the source; the caller's own downstream
        # "no scenes found" handling already covers an empty screenplay
        # honestly, same as a genuinely blank plain-text file would.
        return ""

    return "".join(parts)
