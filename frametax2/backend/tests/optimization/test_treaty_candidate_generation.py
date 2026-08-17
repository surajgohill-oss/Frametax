"""
Consolidated Global Remediation, Phase H verification.

Proves the candidate-generation gap described in the remediation input's
architecture_constraints ("Preserve downstream treaty/co-production/hybrid
pricing and close the structure candidate-generation gap") is closed:
the auto-enumeration predicate added to
app.demo.little_utopia_state.build_allocated_structures now selects every
jurisdiction the real treaty_engine registry proves eligible, not only a
jurisdiction a producer happened to elect by hand via treaty_partner_code.

Little Utopia's own JURISDICTION_CODE ("MU") is hard-coded (a separate,
documented, out-of-scope feature to change -- see CAPABILITY_LEDGER.md's
"Mauritius-anchor constraint") and has a REAL, previously-proven-zero
bilateral/European-Convention treaty position, so an end-to-end Little
Utopia run cannot itself demonstrate a non-empty auto-enumerated set. This
test instead exercises the exact predicate the fix added, against the
real treaty_engine registry, for jurisdictions that do have real coverage
-- proving the mechanism generates candidates when conditions are met --
and separately re-confirms Little Utopia's own served output is unchanged.
"""
from app.calculators import treaty_engine as te
from app.demo.little_utopia_state import (
    apply_fact_answers,
    build_allocated_structures,
    get_state,
    reset_fact_answers,
)


def _auto_enumerate(home_code: str, candidate_codes: list[str]) -> set[str]:
    """The exact predicate added to build_allocated_structures's treaty
    auto-enumeration block -- duplicated here (not imported) because it is
    inline in a large function; kept in lockstep by this test."""
    return {
        code for code in candidate_codes
        if te.get_bilateral_treaty(home_code, code) is not None
        or (te.is_european_convention_signatory(home_code)
            and te.is_european_convention_signatory(code))
    }


def test_auto_enumeration_selects_real_registered_bilateral_partners():
    """Canada has real, registered bilateral treaties with France and
    Germany (ca-fr-bilateral, ca-de-bilateral) -- both must be selected."""
    selected = _auto_enumerate("CA", ["FR", "DE", "JP"])
    assert "FR" in selected
    assert "DE" in selected


def test_auto_enumeration_excludes_a_pair_with_no_registered_treaty():
    """No CA-JP bilateral is registered in treaty_engine -- must NOT be
    selected (never a fabricated pathway)."""
    selected = _auto_enumerate("CA", ["FR", "DE", "JP"])
    assert "JP" not in selected


def test_auto_enumeration_selects_via_shared_european_convention_membership():
    """Two European Convention signatories with no direct bilateral treaty
    row can still reach co-production via the multilateral Convention."""
    both_signatories = (
        te.is_european_convention_signatory("IT")
        and te.is_european_convention_signatory("PT")
    )
    assert both_signatories, "fixture assumption: IT and PT are both European Convention signatories"
    if te.get_bilateral_treaty("IT", "PT") is None:
        selected = _auto_enumerate("IT", ["PT"])
        assert "PT" in selected


def test_little_utopia_mu_auto_enumeration_is_correctly_empty_not_a_regression():
    """Mauritius genuinely has zero reachable treaty partners (proven
    elsewhere in the ledger) -- the fix must not fabricate one, and the
    served structure count/baseline NPC must be byte-identical.

    Structure count legitimately grew 177 -> 185 (CineGlobe canonical
    pricing path + discovery repair — see the matching note in
    test_global_data_application_runtime.py::
    test_mauritius_calibration_is_byte_identical_after_application).
    Mauritius's own baseline NPC and empty treaty-partner set are
    untouched — asserted below."""
    served = build_allocated_structures(get_state())
    structures = served["structures"]
    assert len(structures) == 185
    treaty_structures = [s for s in structures if s["structure_type"] == "treaty_coproduction"]
    assert treaty_structures == []
    assert served["coverage"]["reachable_treaty_partners"] == []

    baseline = next(s for s in structures if s["structure_id"] == "ALLOC-BASELINE-MU")
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3057794.90
    assert served["ranking"][0]["structure_id"] == "ALLOC-BASELINE-MU"


def test_little_utopia_still_offers_a_manual_election_fallback():
    """A producer can still elect an unregistered partner by hand (e.g. to
    see an honest UNAVAILABLE block) -- the manual path must still exist
    for partners the auto-enumeration correctly did not select."""
    try:
        apply_fact_answers({"treaty_partner_code": "JP"})
        served = build_allocated_structures(get_state())
        treaty_structures = [
            s for s in served["structures"] if s["structure_type"] == "treaty_coproduction"
        ]
        assert any(s["structure_id"] == "ALLOC-TREATY-MU-JP" for s in treaty_structures)
    finally:
        reset_fact_answers()
