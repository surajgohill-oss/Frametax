"""
script_parse_status.py

Script Analyzer SA-1, Part M: the deterministic script-parse status enum.

Every state here is a FACT about the project's script, not a guess. The
critical property, stated by the canonical architecture: a failed parse must
never silently fall back to estimated facts. SCRIPT_PARSE_FAILED and
SCRIPT_PARSE_BLOCKED_SCAN_ONLY are terminal for analysis until a human acts —
they do not degrade into "assume 100 pages".
"""
from __future__ import annotations

#: No screenplay document is attached to the project at all.
SCRIPT_NOT_PRESENT = "SCRIPT_NOT_PRESENT"

#: A screenplay exists but has never been through the deterministic parser.
SCRIPT_PRESENT_UNPARSED = "SCRIPT_PRESENT_UNPARSED"

#: Text extracted and structurally viable; parse can run.
SCRIPT_PARSE_READY = "SCRIPT_PARSE_READY"

#: The parser ran and raised. `parse_error` carries the reason.
SCRIPT_PARSE_FAILED = "SCRIPT_PARSE_FAILED"

#: The source is an image/scan with no extractable text layer. Blocked, not
#: guessed — SA-1 supports text-based PDF and plain text only.
SCRIPT_PARSE_BLOCKED_SCAN_ONLY = "SCRIPT_PARSE_BLOCKED_SCAN_ONLY"

#: A parse exists but a NEWER DocumentVersion is now current. The old parse
#: is retained (never overwritten); the project simply needs a re-parse
#: against the new version.
SCRIPT_PARSE_STALE_NEW_VERSION = "SCRIPT_PARSE_STALE_NEW_VERSION"

#: Current version parsed successfully; scenes/characters/elements persisted.
SCRIPT_PARSED = "SCRIPT_PARSED"

ALL_STATUSES = (
    SCRIPT_NOT_PRESENT,
    SCRIPT_PRESENT_UNPARSED,
    SCRIPT_PARSE_READY,
    SCRIPT_PARSE_FAILED,
    SCRIPT_PARSE_BLOCKED_SCAN_ONLY,
    SCRIPT_PARSE_STALE_NEW_VERSION,
    SCRIPT_PARSED,
)

#: Statuses from which downstream analysis may proceed.
ANALYSIS_READY_STATUSES = frozenset({SCRIPT_PARSED})

#: Statuses that require human action before analysis can continue.
BLOCKING_STATUSES = frozenset({
    SCRIPT_NOT_PRESENT,
    SCRIPT_PRESENT_UNPARSED,
    SCRIPT_PARSE_READY,
    SCRIPT_PARSE_FAILED,
    SCRIPT_PARSE_BLOCKED_SCAN_ONLY,
    SCRIPT_PARSE_STALE_NEW_VERSION,
})

_BLOCKER_TEXT = {
    SCRIPT_NOT_PRESENT:
        "No screenplay is attached to this project. Attach a text-based "
        "screenplay (PDF with a text layer, or plain text) to enable script analysis.",
    SCRIPT_PRESENT_UNPARSED:
        "A screenplay is attached but has not been parsed yet. Run the "
        "deterministic parse to produce scenes, characters and elements.",
    SCRIPT_PARSE_READY:
        "The screenplay is ready to parse but the parse has not been run.",
    SCRIPT_PARSE_FAILED:
        "The deterministic parse failed. No script facts are available; they "
        "are deliberately NOT estimated. See parse_error.",
    SCRIPT_PARSE_BLOCKED_SCAN_ONLY:
        "The screenplay has no extractable text layer (scan/image only). SA-1 "
        "supports text-based PDF and plain text. Supply a text-based source.",
    SCRIPT_PARSE_STALE_NEW_VERSION:
        "A newer screenplay version is current. The existing parse belongs to "
        "an older version and is retained; re-parse against the current version.",
}


def blocker_for(status: str) -> str | None:
    """Human-readable blocker, or None when the status is analysis-ready."""
    return _BLOCKER_TEXT.get(status)


def is_analysis_ready(status: str | None) -> bool:
    return status in ANALYSIS_READY_STATUSES
