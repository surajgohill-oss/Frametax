"""
Canonical economic identity: the run-independent tie-breaker that replaces the
per-generation random structure uuid in every ordering, and the opaque pagination
cursor built on it. Pure -- no database.
"""
from __future__ import annotations

import pytest

from app.services.canonical_evaluation import InvalidPageCursor, decode_page_cursor, encode_page_cursor
from app.services.economic_identity import (
    candidate_status_of,
    canonical_economic_identity,
    rejection_reason_class_of,
)

def _hybrid_trace(**over):
    trace = {
        "candidate_status": "RULE_REJECTED", "structural_family": "ordinary_component_hybrid",
        "anchor_jurisdiction": "GR", "anchor_program": "gr_cash_rebate", "primary_jurisdiction": "GR",
        "program_slugs": ["gr_cash_rebate", "ca_mb_film_video_credit", "za_dtic_foreign_film"],
        "jurisdiction_codes": ["GR", "CA-MB", "ZA"], "component_types": ["vfx", "post", "music"],
        "structural_generator_structure_id": "ARCH-a4756f093a91df9a",
        "component_allocations": [
            {"component": "vfx", "jurisdiction_code": "CA-MB", "program_slug": "ca_mb_film_video_credit",
             "allocated_usd": 100.0, "line_ids": ["x"]},
            {"component": "post", "jurisdiction_code": "GR", "program_slug": "gr_cash_rebate", "allocated_usd": 5.0},
        ],
    }
    trace.update(over)
    return trace


def test_identity_is_deterministic_64_hex():
    a = canonical_economic_identity("hybrid", _hybrid_trace())
    assert a == canonical_economic_identity("hybrid", _hybrid_trace())
    assert len(a) == 64 and int(a, 16) >= 0


def test_identity_ignores_list_and_routing_order_amounts_and_reason_text():
    base = canonical_economic_identity("hybrid", _hybrid_trace())
    t = _hybrid_trace()
    t["program_slugs"] = list(reversed(t["program_slugs"]))
    t["jurisdiction_codes"] = list(reversed(t["jurisdiction_codes"]))
    t["component_types"] = list(reversed(t["component_types"]))
    t["component_allocations"] = list(reversed(t["component_allocations"]))
    for c in t["component_allocations"]:
        c["allocated_usd"] = 999.0
        c["line_ids"] = ["different"]
    t["reason"] = "completely different prose"
    t["anchor_npc_usd"] = 12345.0
    assert canonical_economic_identity("hybrid", t) == base


def test_identity_is_status_independent():
    assert canonical_economic_identity("hybrid", _hybrid_trace(candidate_status="PRICED")) == \
        canonical_economic_identity("hybrid", _hybrid_trace(candidate_status="RULE_REJECTED"))


@pytest.mark.parametrize("mutation", [
    {"anchor_jurisdiction": "AT"}, {"anchor_program": "other_program"}, {"primary_jurisdiction": "AT"},
    {"program_slug": "x"}, {"program_slugs": ["gr_cash_rebate"]}, {"jurisdiction_codes": ["GR"]},
    {"component_subset": ["vfx", "post"]}, {"component_types": ["vfx"]},
    {"structural_generator_structure_id": "ARCH-other"}, {"treaty_slug": "t"},
    {"coproduction_partners": [{"jurisdiction_code": "GB"}]}, {"structural_family": "x"},
])
def test_identity_changes_with_every_routing_dimension(mutation):
    assert canonical_economic_identity("hybrid", _hybrid_trace(**mutation)) != \
        canonical_economic_identity("hybrid", _hybrid_trace())


def test_identity_distinguishes_swapped_component_routing():
    """vfx->A + post->B is a DIFFERENT economic structure from vfx->B + post->A even though
    the jurisdiction and program SETS are identical."""
    swapped = _hybrid_trace()
    swapped["component_allocations"] = [
        {"component": "vfx", "jurisdiction_code": "GR", "program_slug": "gr_cash_rebate"},
        {"component": "post", "jurisdiction_code": "CA-MB", "program_slug": "ca_mb_film_video_credit"},
    ]
    assert canonical_economic_identity("hybrid", swapped) != canonical_economic_identity("hybrid", _hybrid_trace())


def test_identity_structure_type_matters_and_missing_trace_is_safe():
    assert canonical_economic_identity("hybrid", _hybrid_trace()) != \
        canonical_economic_identity("component_relocation", _hybrid_trace())
    assert canonical_economic_identity(None, None) == canonical_economic_identity(None, {})
    assert candidate_status_of(None) == "" and rejection_reason_class_of({}) == ""
    assert candidate_status_of({"candidate_status": "PRICED"}) == "PRICED"


def test_page_cursor_round_trips_and_rejects_anything_else():
    assert decode_page_cursor(encode_page_cursor(526155)) == 526155
    assert decode_page_cursor(encode_page_cursor(0)) == 0
    assert "=" not in encode_page_cursor(123456789)  # url-safe, unpadded
    import base64
    forged = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip("=")
    for bad in ("", "not-base64!!", "e30", "W10", forged(b'["x"]'), forged(b"[-1]"), forged(b"[true]"),
                forged(b"[1,2]"), forged(b'{"a":1}'), forged(b"[1.5]")):
        with pytest.raises(InvalidPageCursor):
            decode_page_cursor(bad)
