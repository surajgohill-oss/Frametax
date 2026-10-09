"""Company Globe aggregate contract (app/services/portfolio_globe_view.py). Pure; no database."""
from app.services.portfolio_globe_view import (
    SNAPSHOT_SCHEMA, build_snapshot, compact_structure, resolve_leader, snapshot_is_current,
)


def _view():
    s = lambda sid, **kw: {"structure_id": sid, "primary_jurisdiction": "MU", "participants": ["MU", "ZA"],
                           "classification": "HYBRID_ANCHOR_COMPONENT", "label": sid, "huge": "x" * 5000,
                           "component_allocations": [{"component": "post_vfx_package", "jurisdiction_code": "ZA", "allocated_usd": 1.0, "noise": 1}],
                           "coproduction_partners": [{"code": "RO"}], **kw}
    return {
        "production": {"jurisdiction_code": "MU", "gross_budget_usd": 4.0},
        "structures": {"allocated_structures": {
            "structures": [s("base", is_baseline=True, primary_jurisdiction="MU", participants=["MU"]), s("cond"), s("other")],
            "canonical_selected_structure_id": None,
            "optimizer_candidates": [s("multi", participants=["MU", "ZA", "KE"]), s("other")],
            "leading_conditional_structure": {"structure_id": "cond"},
            "jurisdiction_accounting": {"home_jurisdiction": "MU"},
        }},
    }


def test_snapshot_is_compact_and_keyed_by_generation():
    snap = build_snapshot(_view(), engine_version="e1", fingerprint="f1")
    assert snap["schema"] == SNAPSHOT_SCHEMA and snap["home_code"] == "MU"
    assert all("huge" not in s for s in snap["structures"])
    assert snap["structures"][1]["component_allocations"] == [{"component": "post_vfx_package", "jurisdiction_code": "ZA", "allocated_usd": 1.0}]
    assert snap["structures"][1]["coproduction_partners"] == [{"jurisdiction_code": "RO"}]
    assert snapshot_is_current(snap, engine_version="e1", fingerprint="f1")
    assert not snapshot_is_current(snap, engine_version="e1", fingerprint="f2")
    assert not snapshot_is_current(snap, engine_version="e2", fingerprint="f1")
    assert not snapshot_is_current(None, engine_version="e1", fingerprint="f1")


def test_snapshot_includes_optimizer_pool_candidates_a_producer_can_select():
    snap = build_snapshot(_view(), engine_version="e1", fingerprint="f1")
    ids = [s["structure_id"] for s in snap["structures"]]
    assert ids == ["base", "cond", "other", "multi"], "ranked page first, pool extras after, no duplicates"
    assert resolve_leader(snap, user_structure_id="multi", user_selected=True)[0]["participants"] == ["MU", "ZA", "KE"]


def test_leader_is_the_explicit_choice_else_the_anchor_never_a_canonical_or_conditional_substitute():
    snap = build_snapshot(_view(), engine_version="e1", fingerprint="f1")
    assert resolve_leader(snap, user_structure_id="other", user_selected=True)[1] == "user"
    # no explicit choice -> the anchor (structure None), even though a leading-conditional structure is served
    assert snap["conditional_structure_id"] == "cond"
    assert resolve_leader(snap, user_structure_id=None, user_selected=False) == (None, "baseline")
    snap["canonical_structure_id"] = "other"
    assert resolve_leader(snap, user_structure_id=None, user_selected=False) == (None, "baseline"), "canonical selection is not substituted"
    # a choice that is no longer in the generation returns to the anchor (disclosed as unavailable by the caller)
    assert resolve_leader(snap, user_structure_id="gone", user_selected=True) == (None, "baseline")
    # clearing the choice returns to the anchor
    assert resolve_leader(snap, user_structure_id="other", user_selected=False) == (None, "baseline")


def test_compact_structure_never_invents_fields():
    assert compact_structure({"structure_id": "x"})["participants"] is None
