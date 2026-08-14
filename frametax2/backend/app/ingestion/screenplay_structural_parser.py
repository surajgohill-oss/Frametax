"""
screenplay_structural_parser.py

Script Analyzer SA-1, Part B: the DETERMINISTIC structural parse.

Extends (never replaces) app/ingestion/screenplay_parser.py. That module
remains the Gen-1 chunk/heading/character extractor used by existing
callers; this module produces the version-scoped canonical structure the
SA-1 entities persist: Scene, Character, dialogue linkage and the objective
SA-1 SceneElement taxonomy.

Canonical rules enforced here (SCRIPT_ANALYZER_CANONICAL_ARCHITECTURE.json):

  * No AI. Every value is a function of the source text alone.
  * Ambiguity stays UNKNOWN. A slugline this parser cannot normalise yields
    INT_EXT=UNKNOWN / DAY_NIGHT=UNKNOWN — never a guess.
  * Page eighths derive from PRESERVED PAGE LAYOUT when the source carries
    form-feeds or page markers. `word_count/200` is used ONLY when no layout
    exists at all, and is then explicitly flagged
    page_basis="APPROXIMATE_NO_LAYOUT" so nothing downstream can mistake it
    for a real page count.
  * Only EXPLICIT evidence produces an element. Presence is recorded; scale,
    quantity and complexity are NOT inferred (those are later AI phases).
  * Every element carries its source span and the exact matched text, so a
    reviewer can always see why the parser said what it said.

Determinism: identical input bytes + identical PARSER_VERSION always produce
byte-identical output, which is what makes the SA-1 idempotency guarantee
and the CanonicalProductionState fingerprint meaningful.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

PARSER_VERSION = "sa1-structural-1.0.0"

# ── normalized enums (strings, mirrored by the DB columns) ──────────────────
INT_EXT_INT = "INT"
INT_EXT_EXT = "EXT"
INT_EXT_BOTH = "INT_EXT"
INT_EXT_UNKNOWN = "UNKNOWN"

TOD_DAY = "DAY"
TOD_NIGHT = "NIGHT"
TOD_DAWN = "DAWN"
TOD_DUSK = "DUSK"
TOD_CONTINUOUS = "CONTINUOUS"
TOD_LATER = "LATER"
TOD_UNKNOWN = "UNKNOWN"

# SA-1 objective taxonomy (Part D). Deliberately does NOT include the
# AI_INTERPRETED capabilities (stunts, VFX, crowds, construction, ...).
TAX_SCENE = "SCENE"
TAX_INT_EXT = "INT_EXT"
TAX_DAY_NIGHT = "DAY_NIGHT"
TAX_SCRIPTED_LOCATION = "SCRIPTED_LOCATION"
TAX_CHARACTER = "CHARACTER"
TAX_DIALOGUE_ROLE = "DIALOGUE_ROLE"
TAX_EXPLICIT_VEHICLE = "EXPLICIT_VEHICLE"
TAX_EXPLICIT_ANIMAL = "EXPLICIT_ANIMAL"
TAX_EXPLICIT_WEAPON = "EXPLICIT_WEAPON"
TAX_EXPLICIT_MINOR = "EXPLICIT_MINOR"
TAX_EXPLICIT_PROP = "EXPLICIT_PROP"
TAX_PERIOD_REFERENCE = "PERIOD_REFERENCE"

SA1_TAXONOMY = frozenset({
    TAX_SCENE, TAX_INT_EXT, TAX_DAY_NIGHT, TAX_SCRIPTED_LOCATION,
    TAX_CHARACTER, TAX_DIALOGUE_ROLE, TAX_EXPLICIT_VEHICLE,
    TAX_EXPLICIT_ANIMAL, TAX_EXPLICIT_WEAPON, TAX_EXPLICIT_MINOR,
    TAX_EXPLICIT_PROP, TAX_PERIOD_REFERENCE,
})

EXTRACTION_DETERMINISTIC = "DETERMINISTIC_PARSE"
EVIDENCE_OBJECTIVE = "OBJECTIVE_SCRIPT_FACT"
EVIDENCE_DERIVED = "DERIVED_DETERMINISTIC"

# ── regexes ────────────────────────────────────────────────────────────────
# Scene heading. Accepts INT/EXT/INT-EXT/I-E in the common spellings, with or
# without a trailing period, optionally preceded by a scene number.
_HEADING_RE = re.compile(
    r"^[ \t]*"
    r"(?P<num>[0-9]+[A-Z]?)?[ \t.)]*"
    r"(?P<ie>INT\.?/EXT\.?|EXT\.?/INT\.?|I/E\.?|INT\.?|EXT\.?)"
    r"(?P<rest>[ \t\-–—:.].*)?$",
    re.IGNORECASE,
)

# Character cue: an indented ALL-CAPS name line immediately preceding
# dialogue. Screenplay cues are conventionally indented; we accept any
# leading whitespace but require the line to be caps-dominant and short.
_CUE_RE = re.compile(
    r"^[ \t]*(?P<name>[A-Z][A-Z0-9 .'\-]{1,38})"
    r"(?P<paren>[ \t]*\([^)]{0,40}\))?[ \t]*$"
)

# Lines that look like cues but are transitions/instructions, never characters.
_NOT_A_CHARACTER = frozenset({
    "CONTINUED", "CONT'D", "CUT TO", "CUT TO:", "FADE IN", "FADE IN:",
    "FADE OUT", "FADE OUT.", "FADE TO", "FADE TO BLACK", "SMASH CUT",
    "SMASH CUT TO", "DISSOLVE TO", "MATCH CUT", "MATCH CUT TO", "THE END",
    "INTERCUT", "INTERCUT WITH", "MONTAGE", "END MONTAGE", "TITLE",
    "TITLE CARD", "SUPER", "SUPERIMPOSE", "OMITTED", "BACK TO SCENE",
    "FLASHBACK", "END FLASHBACK", "PRELAP", "V.O.", "O.S.", "CONTINUOUS",
    "LATER", "MOMENTS LATER", "ANGLE ON", "CLOSE ON", "INSERT", "P.O.V.",
    "REVISED", "SCENE", "ACT ONE", "ACT TWO", "ACT THREE",
})

_PAREN_ONLY_RE = re.compile(r"^[ \t]*\([^)]*\)[ \t]*$")
_PAGE_MARKER_RE = re.compile(r"^[ \t]*(?P<n>\d{1,4})[ \t]*\.?[ \t]*$")

# Time-of-day tokens, longest-first so "CONTINUOUS" beats a bare "CONT".
_TOD_TOKENS: tuple[tuple[str, str], ...] = (
    ("CONTINUOUS", TOD_CONTINUOUS),
    ("MOMENTS LATER", TOD_LATER),
    ("LATER", TOD_LATER),
    ("MAGIC HOUR", TOD_DUSK),
    ("PREDAWN", TOD_DAWN),
    ("PRE-DAWN", TOD_DAWN),
    ("DAWN", TOD_DAWN),
    ("SUNRISE", TOD_DAWN),
    ("MORNING", TOD_DAY),
    ("MIDDAY", TOD_DAY),
    ("NOON", TOD_DAY),
    ("AFTERNOON", TOD_DAY),
    ("DAYBREAK", TOD_DAWN),
    ("DAY", TOD_DAY),
    ("SUNSET", TOD_DUSK),
    ("DUSK", TOD_DUSK),
    ("TWILIGHT", TOD_DUSK),
    ("EVENING", TOD_NIGHT),
    ("MIDNIGHT", TOD_NIGHT),
    ("NIGHT", TOD_NIGHT),
)

# ── explicit-evidence lexicons ─────────────────────────────────────────────
# Deliberately narrow and literal. A term is here only when its presence in
# a screenplay is unambiguous EVIDENCE of the thing. Scale is never inferred.
_VEHICLE_TERMS = (
    "car", "cars", "truck", "trucks", "van", "vans", "bus", "buses",
    "motorcycle", "motorbike", "scooter", "bicycle", "boat", "boats",
    "ship", "yacht", "ferry", "helicopter", "airplane", "aeroplane",
    "plane", "jet", "train", "tractor", "ambulance", "taxi", "jeep",
    "limousine", "limo", "sedan", "pickup", "convertible",
)
_ANIMAL_TERMS = (
    "horse", "horses", "dog", "dogs", "cat", "cats", "cow", "cows",
    "sheep", "goat", "goats", "chicken", "chickens", "bird", "birds",
    "snake", "snakes", "elephant", "camel", "donkey", "mule", "pig",
    "pigs", "rat", "rats", "monkey", "falcon", "eagle",
)
_WEAPON_TERMS = (
    "gun", "guns", "pistol", "revolver", "rifle", "shotgun", "handgun",
    "firearm", "knife", "knives", "blade", "sword", "machete", "dagger",
    "grenade", "explosive", "explosives", "bomb", "rocket launcher",
    "crossbow", "bow and arrow",
)
_MINOR_TERMS = (
    "child", "children", "kid", "kids", "boy", "girl", "toddler",
    "infant", "baby", "babies", "teenager", "teen", "schoolboy",
    "schoolgirl", "newborn",
)
_PROP_HERO_TERMS = (
    "hero prop", "picture vehicle", "practical", "prop gun", "prop knife",
)
_PERIOD_RE = re.compile(
    r"\b(?:"
    r"(?:1[0-9]|20)\d{2}s?"                      # 1920, 1920s, 2043
    r"|(?:eighteen|nineteen)\s+\w+"              # nineteen forties
    r"|period piece|present day|modern day"
    r"|victorian|edwardian|elizabethan|medieval|renaissance"
    r"|antebellum|prohibition|world war (?:i|ii|one|two)|wwi|wwii"
    r")\b",
    re.IGNORECASE,
)


# ── dataclasses ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ParsedElement:
    """One objective, evidence-backed observation inside a scene."""
    taxonomy_key: str
    normalized_value: str
    raw_evidence: str
    char_start: int
    char_end: int
    evidence_state: str = EVIDENCE_OBJECTIVE
    extraction_method: str = EXTRACTION_DETERMINISTIC
    is_interpretation: bool = False
    quantity: float | None = None
    unit: str | None = None

    @property
    def evidence_hash(self) -> str:
        return hashlib.sha256(self.raw_evidence.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class ParsedDialogue:
    character_name: str
    char_start: int
    char_end: int
    word_count: int


@dataclass
class ParsedScene:
    sequence: int
    source_scene_number: str | None
    raw_heading: str
    normalized_heading: str
    int_ext: str
    time_of_day: str
    scripted_location: str | None
    location_key: str | None
    char_start: int
    char_end: int
    page_start: int | None
    page_end: int | None
    eighths: int | None
    elements: list[ParsedElement] = field(default_factory=list)
    dialogue: list[ParsedDialogue] = field(default_factory=list)

    @property
    def scene_hash(self) -> str:
        basis = f"{self.sequence}|{self.normalized_heading}|{self.char_start}"
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]


@dataclass
class ParsedCharacter:
    canonical_name: str
    aliases: list[str]
    scene_sequences: list[int]
    dialogue_block_count: int
    dialogue_word_count: int

    @property
    def is_speaking_role(self) -> bool:
        return self.dialogue_block_count > 0


@dataclass
class StructuralParseResult:
    parser_version: str
    input_fingerprint: str
    page_basis: str            # LAYOUT_FORM_FEED | LAYOUT_PAGE_MARKER | APPROXIMATE_NO_LAYOUT
    page_count: int | None
    word_count: int
    scenes: list[ParsedScene]
    characters: list[ParsedCharacter]
    warnings: list[str] = field(default_factory=list)

    @property
    def total_eighths(self) -> int:
        return sum(s.eighths or 0 for s in self.scenes)


# ── normalisation helpers ──────────────────────────────────────────────────

def _normalize_int_ext(token: str) -> str:
    t = token.upper().replace(".", "").replace(" ", "")
    if t in ("INT/EXT", "EXT/INT", "I/E"):
        return INT_EXT_BOTH
    if t == "INT":
        return INT_EXT_INT
    if t == "EXT":
        return INT_EXT_EXT
    return INT_EXT_UNKNOWN


def _normalize_time_of_day(rest: str) -> str:
    """Read the time-of-day from the tail of a slugline. Unrecognised or
    absent -> UNKNOWN. Never guessed from context."""
    if not rest:
        return TOD_UNKNOWN
    upper = rest.upper()
    # Prefer the segment after the LAST dash, which is where TOD conventionally
    # lives ("EXT. BEACH - DAY"); fall back to scanning the whole tail.
    tail = re.split(r"[-–—]", upper)[-1].strip() if re.search(r"[-–—]", upper) else upper
    for token, value in _TOD_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", tail):
            return value
    for token, value in _TOD_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", upper):
            return value
    return TOD_UNKNOWN


def _scripted_location(rest: str) -> str | None:
    """The location portion of the slugline: everything before the TOD
    segment. Returns None when nothing usable remains."""
    if not rest:
        return None
    cleaned = rest.strip().lstrip("-–—:. \t")
    if not cleaned:
        return None
    parts = re.split(r"\s+[-–—]\s+", cleaned)
    if len(parts) > 1 and _normalize_time_of_day(parts[-1]) != TOD_UNKNOWN:
        parts = parts[:-1]
    loc = " - ".join(p.strip() for p in parts if p.strip())
    loc = re.sub(r"\s+", " ", loc).strip(" .-–—")
    return loc or None


def _location_key(location: str | None) -> str | None:
    """Canonical key for recurrence counting. Case/punctuation-insensitive."""
    if not location:
        return None
    key = re.sub(r"[^A-Z0-9 ]", " ", location.upper())
    return re.sub(r"\s+", " ", key).strip() or None


def _is_character_cue(line: str) -> str | None:
    """Return the canonical character name if `line` is a cue, else None."""
    if not line.strip():
        return None
    m = _CUE_RE.match(line)
    if not m:
        return None
    name = m.group("name").strip().rstrip(".")
    if not name or len(name) < 2:
        return None
    # Must be genuinely caps (a Title Case action line must not match).
    letters = [c for c in name if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return None
    bare = re.sub(r"\s*\((?:V\.?O\.?|O\.?S\.?|CONT'?D|OFF)\)\s*", "", name, flags=re.IGNORECASE)
    bare = bare.strip().rstrip(".")
    if bare.upper() in _NOT_A_CHARACTER:
        return None
    if _HEADING_RE.match(line):
        return None
    if re.match(r"^(INT|EXT|I/E)\b", bare, re.IGNORECASE):
        return None
    if bare.endswith(":"):
        return None
    if len(bare.split()) > 4:
        return None
    return bare or None


def _find_terms(text: str, terms: tuple[str, ...]) -> list[tuple[str, int, int]]:
    """Whole-word, case-insensitive term hits with their offsets."""
    hits: list[tuple[str, int, int]] = []
    seen: set[str] = set()
    lowered = text.lower()
    for term in terms:
        for m in re.finditer(rf"\b{re.escape(term)}\b", lowered):
            key = term
            if key in seen:
                break
            seen.add(key)
            hits.append((term, m.start(), m.end()))
            break
    return hits


# ── page layout ────────────────────────────────────────────────────────────

def _build_page_index(raw_text: str) -> tuple[str, list[int]]:
    """Return (page_basis, page_start_offsets).

    Form feeds are the strongest signal; a run of standalone ascending page
    markers is next. When neither exists we return APPROXIMATE_NO_LAYOUT and
    an empty index — callers must then treat pages as approximate.
    """
    if "\f" in raw_text:
        offsets = [0]
        for m in re.finditer("\f", raw_text):
            offsets.append(m.end())
        return "LAYOUT_FORM_FEED", offsets

    markers: list[tuple[int, int]] = []
    pos = 0
    for line in raw_text.splitlines(keepends=True):
        m = _PAGE_MARKER_RE.match(line)
        if m:
            markers.append((int(m.group("n")), pos))
        pos += len(line)
    ascending = [mk for i, mk in enumerate(markers)
                 if i == 0 or mk[0] > markers[i - 1][0]]
    if len(ascending) >= 3:
        return "LAYOUT_PAGE_MARKER", [0] + [off for _n, off in ascending]

    return "APPROXIMATE_NO_LAYOUT", []


def _page_for_offset(offset: int, page_offsets: list[int]) -> int | None:
    if not page_offsets:
        return None
    page = 1
    for i, start in enumerate(page_offsets):
        if offset >= start:
            page = i + 1
        else:
            break
    return page


# ── main entry point ───────────────────────────────────────────────────────

def parse_structure(raw_text: str) -> StructuralParseResult:
    """Deterministically parse screenplay text into the SA-1 canonical
    structure. Pure function: no I/O, no AI, no randomness."""
    warnings: list[str] = []
    fingerprint = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    word_count = len(raw_text.split())

    page_basis, page_offsets = _build_page_index(raw_text)
    if page_basis == "APPROXIMATE_NO_LAYOUT":
        warnings.append(
            "No page layout (form feeds or ascending page markers) found in the "
            "source text. Page and eighth values are APPROXIMATE and must not be "
            "treated as a real page count."
        )
        page_count = max(1, word_count // 200) if word_count else None
    else:
        page_count = len(page_offsets)

    # ── scene boundaries ───────────────────────────────────────────────
    line_spans: list[tuple[str, int, int]] = []
    pos = 0
    for line in raw_text.splitlines(keepends=True):
        line_spans.append((line.rstrip("\n\r"), pos, pos + len(line)))
        pos += len(line)

    heading_idx: list[int] = []
    for i, (line, _s, _e) in enumerate(line_spans):
        stripped = line.strip()
        if not stripped:
            continue
        m = _HEADING_RE.match(line)
        if m and m.group("ie"):
            # Require the heading to be the dominant content of its line.
            heading_idx.append(i)

    if not heading_idx:
        warnings.append("No scene headings (INT./EXT.) found — screenplay structure not recoverable.")
        return StructuralParseResult(
            parser_version=PARSER_VERSION, input_fingerprint=fingerprint,
            page_basis=page_basis, page_count=page_count, word_count=word_count,
            scenes=[], characters=[], warnings=warnings,
        )

    scenes: list[ParsedScene] = []
    for n, li in enumerate(heading_idx):
        line, l_start, _l_end = line_spans[li]
        end_line = heading_idx[n + 1] if n + 1 < len(heading_idx) else len(line_spans)
        body_end = line_spans[end_line - 1][2] if end_line > 0 else l_start

        m = _HEADING_RE.match(line)
        assert m is not None
        rest = (m.group("rest") or "")
        int_ext = _normalize_int_ext(m.group("ie"))
        tod = _normalize_time_of_day(rest)
        location = _scripted_location(rest)
        raw_heading = line.strip()
        normalized_heading = re.sub(r"\s+", " ", raw_heading.upper()).strip()

        page_start = _page_for_offset(l_start, page_offsets)
        page_end = _page_for_offset(max(l_start, body_end - 1), page_offsets)

        scenes.append(ParsedScene(
            sequence=n + 1,
            source_scene_number=(m.group("num") or None),
            raw_heading=raw_heading,
            normalized_heading=normalized_heading,
            int_ext=int_ext,
            time_of_day=tod,
            scripted_location=location,
            location_key=_location_key(location),
            char_start=l_start,
            char_end=body_end,
            page_start=page_start,
            page_end=page_end,
            eighths=None,
        ))

    # ── eighths ────────────────────────────────────────────────────────
    # A page is 8 eighths. Allocate by the scene's share of source characters
    # on its page(s) when layout exists; otherwise by share of total text.
    total_chars = max(1, len(raw_text))
    for sc in scenes:
        span = max(0, sc.char_end - sc.char_start)
        if page_basis == "APPROXIMATE_NO_LAYOUT":
            est_pages = (span / total_chars) * (page_count or 1)
        else:
            chars_per_page = total_chars / max(1, len(page_offsets))
            est_pages = span / chars_per_page
        sc.eighths = max(1, round(est_pages * 8))

    # ── characters, dialogue, elements ─────────────────────────────────
    char_map: dict[str, ParsedCharacter] = {}

    for sc in scenes:
        body = raw_text[sc.char_start:sc.char_end]

        # scene-level objective elements
        sc.elements.append(ParsedElement(
            taxonomy_key=TAX_SCENE, normalized_value=str(sc.sequence),
            raw_evidence=sc.raw_heading, char_start=sc.char_start,
            char_end=sc.char_start + len(sc.raw_heading),
        ))
        sc.elements.append(ParsedElement(
            taxonomy_key=TAX_INT_EXT, normalized_value=sc.int_ext,
            raw_evidence=sc.raw_heading, char_start=sc.char_start,
            char_end=sc.char_start + len(sc.raw_heading),
        ))
        sc.elements.append(ParsedElement(
            taxonomy_key=TAX_DAY_NIGHT, normalized_value=sc.time_of_day,
            raw_evidence=sc.raw_heading, char_start=sc.char_start,
            char_end=sc.char_start + len(sc.raw_heading),
        ))
        if sc.scripted_location:
            sc.elements.append(ParsedElement(
                taxonomy_key=TAX_SCRIPTED_LOCATION,
                normalized_value=sc.location_key or sc.scripted_location,
                raw_evidence=sc.raw_heading, char_start=sc.char_start,
                char_end=sc.char_start + len(sc.raw_heading),
            ))

        # dialogue + character cues
        cue_lines = [
            (ln, s, e) for (ln, s, e) in line_spans
            if sc.char_start <= s < sc.char_end
        ]
        for idx, (ln, s, e) in enumerate(cue_lines):
            name = _is_character_cue(ln)
            if not name:
                continue
            # A cue must be followed by non-blank, non-heading content.
            j = idx + 1
            while j < len(cue_lines) and _PAREN_ONLY_RE.match(cue_lines[j][0]):
                j += 1
            if j >= len(cue_lines):
                continue
            nxt = cue_lines[j][0]
            if not nxt.strip() or _HEADING_RE.match(nxt) or _is_character_cue(nxt):
                continue

            block_words = 0
            k = j
            while k < len(cue_lines) and cue_lines[k][0].strip() and not _HEADING_RE.match(cue_lines[k][0]):
                if _is_character_cue(cue_lines[k][0]) and k != j:
                    break
                block_words += len(cue_lines[k][0].split())
                k += 1

            sc.dialogue.append(ParsedDialogue(
                character_name=name, char_start=s, char_end=e, word_count=block_words,
            ))
            rec = char_map.get(name)
            if rec is None:
                rec = ParsedCharacter(canonical_name=name, aliases=[],
                                      scene_sequences=[], dialogue_block_count=0,
                                      dialogue_word_count=0)
                char_map[name] = rec
            if sc.sequence not in rec.scene_sequences:
                rec.scene_sequences.append(sc.sequence)
            rec.dialogue_block_count += 1
            rec.dialogue_word_count += block_words

            sc.elements.append(ParsedElement(
                taxonomy_key=TAX_CHARACTER, normalized_value=name,
                raw_evidence=ln.strip(), char_start=s, char_end=e,
            ))

        # explicit-evidence elements — presence only, never quantity
        for taxonomy, terms in (
            (TAX_EXPLICIT_VEHICLE, _VEHICLE_TERMS),
            (TAX_EXPLICIT_ANIMAL, _ANIMAL_TERMS),
            (TAX_EXPLICIT_WEAPON, _WEAPON_TERMS),
            (TAX_EXPLICIT_MINOR, _MINOR_TERMS),
            (TAX_EXPLICIT_PROP, _PROP_HERO_TERMS),
        ):
            for term, rs, re_ in _find_terms(body, terms):
                abs_s = sc.char_start + rs
                abs_e = sc.char_start + re_
                sc.elements.append(ParsedElement(
                    taxonomy_key=taxonomy, normalized_value=term.upper(),
                    raw_evidence=raw_text[max(0, abs_s - 40):abs_e + 40].strip(),
                    char_start=abs_s, char_end=abs_e,
                ))

        for m in _PERIOD_RE.finditer(body):
            abs_s = sc.char_start + m.start()
            abs_e = sc.char_start + m.end()
            sc.elements.append(ParsedElement(
                taxonomy_key=TAX_PERIOD_REFERENCE,
                normalized_value=m.group(0).upper(),
                raw_evidence=raw_text[max(0, abs_s - 40):abs_e + 40].strip(),
                char_start=abs_s, char_end=abs_e,
            ))
            break  # one period reference per scene is sufficient evidence

    # DIALOGUE_ROLE is derived, not observed — flag it as such.
    for sc in scenes:
        speakers = sorted({d.character_name for d in sc.dialogue})
        for name in speakers:
            sc.elements.append(ParsedElement(
                taxonomy_key=TAX_DIALOGUE_ROLE, normalized_value=name,
                raw_evidence=f"speaking role in scene {sc.sequence}",
                char_start=sc.char_start, char_end=sc.char_start,
                evidence_state=EVIDENCE_DERIVED,
            ))

    characters = sorted(char_map.values(), key=lambda c: c.canonical_name)
    if not characters:
        warnings.append("No character cues with dialogue were recovered.")

    return StructuralParseResult(
        parser_version=PARSER_VERSION, input_fingerprint=fingerprint,
        page_basis=page_basis, page_count=page_count, word_count=word_count,
        scenes=scenes, characters=characters, warnings=warnings,
    )
