"""
Outbound-data controls (spec section 2): package allowlist, size limits,
secret-pattern detection, redaction, confidentiality gating, and a
dry-run preview showing exactly what would leave the process.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.bridge.config import BridgeSettings, get_bridge_settings
from app.bridge.schema import AuditPackage, ConfidentialityClassification

# Field names that must never appear in an outbound package — a defensive
# belt-and-suspenders check; AuditPackage's schema itself has no key/secret
# field, so this should always find nothing, and a hit here means someone
# stuffed something they shouldn't have into inputs/evidence/notes.
_SECRET_KEY_NAMES = re.compile(
    r"(api[_-]?key|secret|password|token|authorization|bearer|private[_-]?key)",
    re.IGNORECASE,
)

# Value-shape patterns for common provider key formats — catches a key
# that leaked into a free-text field even if the field name looked innocent.
#
# This package's own data legitimately contains long hyphenated slugs
# (e.g. conditional_program_ids like "COND-CH-media-desk-switzerland-
# succ-s-cin-ma-automatic-support") that can contain an incidental
# "sk-" or "ya29." substring — a real false positive found against REAL
# served data this session. Two different fixes for two different real
# key shapes:
#   - OpenAI keys are a single unbroken alnum run after "sk-" — banning
#     hyphens from the suffix class (plus \b) is sufficient, since a
#     coincidental 16+ char unbroken run inside a hyphenated slug never
#     happens by chance.
#   - Anthropic keys DO contain internal hyphens as real segment
#     separators ("sk-ant-api03-<seg1>-<seg2>"), so banning hyphens
#     would miss real keys (confirmed: it did, until this fix). Instead
#     this pattern anchors on the "-apiNN-" segment, which is specific
#     enough that a coincidental slug match is not realistic, and THEN
#     allows hyphens in the long suffix that follows.
_SECRET_VALUE_PATTERNS = [
    re.compile(r"\bsk-ant-api\d{2}-[A-Za-z0-9_-]{20,}\b"),  # Anthropic-style (checked before generic sk-)
    re.compile(r"\bsk-[A-Za-z0-9_]{16,}\b"),            # OpenAI-style
    re.compile(r"\bAIza[A-Za-z0-9_]{20,}\b"),           # Google API key style
    re.compile(r"\bya29\.[A-Za-z0-9_]{20,}\b"),         # Google OAuth token style
    re.compile(r"\bBearer\s+[A-Za-z0-9._]{16,}\b"),
]


@dataclass(frozen=True)
class RedactionFinding:
    path: str
    reason: str
    sample: str  # already-redacted, safe to log/display


@dataclass(frozen=True)
class OutboundPreview:
    package_id: str
    confidentiality: ConfidentialityClassification
    size_bytes: int
    within_size_limit: bool
    secret_findings: tuple[RedactionFinding, ...]
    requires_authorization: bool
    safe_to_send: bool
    rendered_json: str  # exactly what would be transmitted (structured_input basis)


def _redact_sample(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-2:]}"


def _scan_secrets(obj: object, path: str = "$") -> list[RedactionFinding]:
    findings: list[RedactionFinding] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_path = f"{path}.{k}"
            if isinstance(k, str) and _SECRET_KEY_NAMES.search(k):
                findings.append(RedactionFinding(
                    path=key_path, reason=f"field name '{k}' matches secret-pattern denylist",
                    sample=_redact_sample(str(v)),
                ))
            findings.extend(_scan_secrets(v, key_path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            findings.extend(_scan_secrets(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        for pattern in _SECRET_VALUE_PATTERNS:
            m = pattern.search(obj)
            if m:
                findings.append(RedactionFinding(
                    path=path, reason=f"value matches secret-shape pattern {pattern.pattern[:30]}...",
                    sample=_redact_sample(m.group(0)),
                ))
    return findings


def preview_outbound_package(
    package: AuditPackage,
    settings: BridgeSettings | None = None,
    *,
    authorized: bool = False,
) -> OutboundPreview:
    """Dry-run: exactly what would be sent, with every safety check
    already applied, and safe_to_send=False if anything is wrong —
    never a side effect, never a network call."""
    settings = settings or get_bridge_settings()
    rendered = package.model_dump_json(indent=2)
    size = len(rendered.encode())
    within_limit = size <= settings.BRIDGE_MAX_PACKAGE_BYTES

    secret_findings = tuple(_scan_secrets(package.model_dump(mode="json")))

    requires_auth = (
        package.confidentiality == ConfidentialityClassification.CONFIDENTIAL
        and settings.BRIDGE_REQUIRE_CONFIDENTIAL_AUTHORIZATION
    )
    safe = (
        within_limit
        and not secret_findings
        and (not requires_auth or authorized)
    )
    return OutboundPreview(
        package_id=package.package_id,
        confidentiality=package.confidentiality,
        size_bytes=size,
        within_size_limit=within_limit,
        secret_findings=secret_findings,
        requires_authorization=requires_auth,
        safe_to_send=safe,
        rendered_json=rendered,
    )


class OutboundTransmissionBlocked(RuntimeError):
    pass


def assert_safe_to_send(preview: OutboundPreview) -> None:
    """Gates on preview.safe_to_send — the single authoritative signal
    that already accounts for whether authorization was granted (see
    preview_outbound_package). A bug fixed this session: this function
    used to check `preview.requires_authorization` directly, which stays
    True for a CONFIDENTIAL package even after authorized=True was
    passed (it records the package's classification, not whether
    authorization is still outstanding) — that made an already-
    authorized, otherwise-clean CONFIDENTIAL package raise anyway. The
    three branches below are only for producing a specific error
    message; safe_to_send is what's actually enforced."""
    if preview.safe_to_send:
        return
    if preview.secret_findings:
        raise OutboundTransmissionBlocked(
            f"Package {preview.package_id} contains {len(preview.secret_findings)} "
            f"potential secret(s): {[f.path for f in preview.secret_findings]}"
        )
    if not preview.within_size_limit:
        raise OutboundTransmissionBlocked(
            f"Package {preview.package_id} is {preview.size_bytes} bytes, "
            "over the configured BRIDGE_MAX_PACKAGE_BYTES limit."
        )
    if preview.requires_authorization:
        raise OutboundTransmissionBlocked(
            f"Package {preview.package_id} is CONFIDENTIAL and requires explicit "
            "user authorization before its first external transmission "
            "(pass authorized=True to preview_outbound_package)."
        )
