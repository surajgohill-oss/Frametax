"""US / Canada / Mexico scoped-inventory controls (PROJECT_OPEN_ITEM_RECOVERY F-01 .. F-06).

SYNTHETIC ONLY -- no database, no persisted generation, no real project, no evaluation. Every expectation is derived here
from text retained in the program's own citation (e.g. the dollar figures quoted verbatim by the issuing agency), from the
program-requirements record of the same program, or by explicit arithmetic over raw synthetic lines -- never from a served
or persisted engine output. A validator PASS does not close any finding: see the recovery register for dispositions."""
from __future__ import annotations

import re

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401  (populates the doctrine registry)
from app.calculators import production_normalization as pn
from app.calculators.allocation_pricing import price_segment
from app.calculators.apply_fx_rates import CanonicalFXContext
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.data.executable_jurisdiction_registry import all_doctrine_records, get_doctrine
from app.data.program_requirements import get_program_requirements


def _scoped(code: str) -> bool:
    return code == "US" or code.startswith(("US-", "CA", "MX"))


def _price(jur: str, slug: str, qpe: float, fx=None, confirmed=None):
    alloc = AccountAllocation(
        account_code="3100", description="below-the-line production spend", amount_usd=qpe, component="production",
        jurisdiction_code=jur, assignment_kind=AssignmentKind.FIXED, rationale="scope control", governing_decision="scope-control",
        line_id="ctl-1",
    )
    return price_segment(
        jurisdiction_code=jur, program_slug=slug, allocations=[alloc], spend_category_by_code={"3100": "btl_crew_labor"},
        offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=qpe * 1.4, fx_context=fx,
        confirmed_ceiling_programs=confirmed,
    )


def _fx(**over) -> CanonicalFXContext:
    rates = {c: 1.5 for c in pn.ALL_TRACKED_CURRENCIES}
    rates.update(over)
    return CanonicalFXContext(snapshot_date="2026-10-02", rates=rates, source="control", freshness_status="fresh")


def _usd_amounts(text: str) -> set[float]:
    out: set[float] = set()
    for m in re.finditer(r"\$\s?([\d,]+(?:\.\d+)?)(\s*million)?", text):
        v = float(m.group(1).replace(",", ""))
        out.add(v * 1_000_000 if m.group(2) else v)
    return out


# ── F-01 (superseded by primary authority, 2026-10-11): New Brunswick's Production Incentive is a discretionary 'maximum of' incentive ───
def test_new_brunswick_is_a_discretionary_lift_grant_with_ceilings_and_a_company_cap_not_a_flat_credit():
    # The LIFT Film & TV Production Incentive 2026/2027 guidelines (gnb.ca): Major stream "Base Grant of up to 25%" of Total NB Spend plus stackable bonuses "to a combined total of 35%"; awards
    # consider "overall demand and available funds"; Company Cap of $2M. Every tier is therefore a ceiling with an unresolved discretion condition and no guaranteed floor. (Supersedes the
    # 2017-2018 THC guidelines this control once pinned: 25% / 30% and an 800,000 feature maximum.)
    doc = get_doctrine("ca_nb_film_tax_credit")
    # Restated in NA-RECONCILIATION-18: the second 35% ceiling tier was replaced by the stackable-bonus rules under a 35% combined cap (SUBSET_COMBINED_RATE_CAPS); the base tier is the 25% Base Grant.
    assert {round(t.rate, 2) for t in doc.tiers} == {0.25}
    assert all(t.is_band_ceiling and any(c.kind == "discretionary_band" for c in t.conditions) for t in doc.tiers)
    seg = _price("CA-NB", "ca_nb_film_tax_credit", 2_000_000.0)
    # Served as POTENTIAL ONLY (NA-RECONCILIATION-12): zero guaranteed, the ceiling shown as the maximum, the award condition still unresolved.
    assert seg.executable and seg.is_band_ceiling and seg.ceiling_requires_confirmation, "a discretionary maximum is conditional potential, never guaranteed"
    # NA-RECONCILIATION-19: Total NB Spend may include up to 15% eligible deemed spend, so the unstated-fact maximum is 35% x 2,000,000 x 1.15 = 805,000 (it was 700,000 before deemed spend was modelled).
    assert seg.incentive_floor_usd == 0.0 and seg.incentive_ceiling_usd == pytest.approx(0.35 * 2_000_000.0 * 1.15)
    assert "no guaranteed floor" in " ".join(seg.notes) or "ZERO" in " ".join(seg.notes)
    from app.data.program_rate_rules import get_incentive_value_cap
    cap = get_incentive_value_cap("ca_nb_film_tax_credit")
    assert cap.cap_currency == "CAD" and cap.cap_native_amount == 2_000_000.0


def test_saskatchewan_provenance_changes_the_knowledge_axis_only_and_the_grant_is_visible_zero_guaranteed_potential():
    # Restated in NA-RECONCILIATION-19. The exact restriction that was lifted: _B1_DISCRETIONARY_RULING['ca_sk_production_grant'] = DISPLAY_ONLY_ZERO_GUARANTEED, enforced through economic_block_for_program(), kept an
    # assessed, selective grant out of the pricing kernel. The entry is removed, so the grant is priced like New Brunswick and Arkansas: potential only, a ZERO guaranteed floor, the 25% Service Production Stream base
    # plus stated-fact additions to the 40% / 35% totals. Provenance is still the knowledge axis only; the project's discretionary policy still governs inclusion.
    from app.data import authority_coverage_registry as acr
    from app.data import program_authority_provenance as pa
    assert "ca_sk_production_grant" not in acr._B1_DISCRETIONARY_RULING
    assert acr.economic_block_for_program("ca_sk_creative_saskatchewan_grant") is None
    from app.services.canonical_evaluation import _discretionary_policy_resolve, _is_discretionary_program
    for slug in ("ca_sk_creative_saskatchewan_grant", "ca_nb_film_tax_credit", "us_ar_digital_motion_picture_incentive"):
        assert _is_discretionary_program(slug), f"{slug} is gated by the existing discretionary-program policy"
    assert _discretionary_policy_resolve("ca_sk_creative_saskatchewan_grant", {}) == "include"
    assert _discretionary_policy_resolve("ca_sk_creative_saskatchewan_grant", {"discretionary_policy_default": "exclude"}) == "exclude"   # the project policy governs, not the provenance
    assert pa.authority_disposition("ca_sk_creative_saskatchewan_grant") == pa.AUTHORITY_VERIFIED_PRICEABLE
    seg = _price("CA-SK", "ca_sk_creative_saskatchewan_grant", 2_000_000.0)
    assert seg.executable and seg.incentive_floor_usd == 0.0 and seg.ceiling_requires_confirmation
    assert seg.incentive_ceiling_usd == pytest.approx(0.40 * 2_000_000.0), "25% base + Saskatchewan Stream and bonuses, clipped at the 40% total"


def test_no_scoped_tier_is_a_band_ceiling_whose_only_conditions_are_already_satisfied_type_gates():
    # F-01 / F-03 family guard: a band ceiling must keep at least one genuinely unresolved condition, otherwise the
    # segment reports a lower floor while the structure confirms the ceiling (NB) or confirms an 'up to' rate (NC).
    executable_kinds = {"production_type", "min_qpe_usd"}
    offenders = []
    for rec in all_doctrine_records():
        if not _scoped(rec.jurisdiction_code):
            continue
        for tier in rec.tiers:
            if tier.is_band_ceiling and all(c.kind in executable_kinds for c in tier.conditions):
                offenders.append((rec.program_slug, tier.tier_id))
    assert offenders == []


# ── F-02: USD thresholds were converted as if they were EUR (Connecticut, North Carolina) ─────────────────────────────
def test_us_state_thresholds_equal_the_figures_the_agency_quotes_not_a_converted_value():
    ct = get_doctrine("us_ct_film_tax_credit")
    quoted = _usd_amounts(ct.citation)
    assert {100_000.0, 500_000.0, 1_000_000.0} <= quoted
    assert sorted(t.min_qpe_usd for t in ct.tiers) == [100_000.0, 500_000.0, 1_000_000.0]
    assert ct.min_spend_usd == 100_000.0
    nc = get_doctrine("us_nc_film_entertainment_grant")
    assert 1_500_000.0 in _usd_amounts(nc.citation)
    assert nc.min_spend_usd == 1_500_000.0 and all(t.min_qpe_usd == 1_500_000.0 for t in nc.tiers)


def test_every_scoped_us_state_threshold_is_a_whole_thousand_usd():
    # Canadian thresholds are legitimately CAD-converted (e.g. Ontario OPSTC C$1m); a US-state USD figure never is.
    for rec in all_doctrine_records():
        if not rec.jurisdiction_code.startswith("US-"):
            continue
        vals = [rec.min_spend_usd, rec.annual_cap_usd] + [t.min_qpe_usd for t in rec.tiers] + [
            c.threshold_usd for t in rec.tiers for c in t.conditions]
        for v in vals:
            assert v is None or abs(v - round(v / 1000.0) * 1000.0) < 0.5, (rec.program_slug, v)


@pytest.mark.parametrize("qpe,rate", [(450_000.0, 0.10), (700_000.0, 0.15), (1_050_000.0, 0.30)])
def test_connecticut_rate_ladder_follows_the_quoted_dollar_boundaries(qpe, rate):
    seg = _price("US-CT", "us_ct_film_tax_credit", qpe)
    assert seg.executable and seg.rate_floor == pytest.approx(rate)


# ── F-03: 'up to X%' with no stated floor must be blocked the same way for NC as for MD and SC ──────────────────────
@pytest.mark.parametrize("jur,slug", [
    ("US-MD", "us_md_film_production_activity_credit"),
    ("US-SC", "us_sc_film_production_credit"),
    ("US-NC", "us_nc_film_entertainment_grant"),
])
def test_a_program_stating_only_a_rate_ceiling_does_not_price_a_confirmed_floor(jur, slug):
    seg = _price(jur, slug, 3_000_000.0)
    # NA-RECONCILIATION-12: the ceiling is served as conditional POTENTIAL with a ZERO guaranteed floor (it used to drop the segment entirely).
    rate = {"US-MD": 0.30, "US-SC": 0.30, "US-NC": 0.25}[jur]
    assert seg.executable and seg.incentive_floor_usd == 0.0 and seg.ceiling_requires_confirmation
    assert seg.incentive_ceiling_usd == pytest.approx(rate * 3_000_000.0)
    assert any("CEILING" in n for n in seg.notes), seg.notes


def test_nc_minimum_spend_still_gates_below_the_quoted_threshold():
    below = _price("US-NC", "us_nc_film_entertainment_grant", 1_400_000.0)
    assert not below.executable and not any("CEILING" in b for b in below.blockers)


# ── F-04: Rhode Island's per-project cap was never applied; Washington's annual fund was a stale secondary figure ──────
def test_rhode_island_per_project_cap_binds_and_the_annual_fund_is_reported_separately():
    doc = get_doctrine("us_ri_film_credit")
    assert 7_000_000.0 in _usd_amounts(doc.provenance.citation_detail)  # the cap is the figure the record itself cites
    big = _price("US-RI", "us_ri_film_credit", 30_000_000.0)
    assert big.incentive_floor_usd == pytest.approx(7_000_000.0)       # 30% x 30m = 9m, capped
    assert big.incentive_cap_usd == pytest.approx(7_000_000.0) and big.incentive_cap_type == "per_project_native"
    small = _price("US-RI", "us_ri_film_credit", 10_000_000.0)
    assert small.incentive_floor_usd == pytest.approx(3_000_000.0)     # below the cap: untouched, nothing invented


def test_doctrine_and_profile_annual_funds_agree_except_the_one_documented_conflict():
    documented = {"us_la_film_incentive"}  # both records argue the figure in their own notes (150m vs 125m); unresolved
    conflicts = []
    for rec in all_doctrine_records():
        if not _scoped(rec.jurisdiction_code):
            continue
        prof = get_program_requirements(rec.program_slug)
        pa = getattr(prof, "annual_program_cap_usd", None) if prof else None
        if rec.annual_cap_usd and pa and abs(rec.annual_cap_usd - pa) > 1.0:
            conflicts.append(rec.program_slug)
    assert set(conflicts) == documented
    la_doc, la_prof = get_doctrine("us_la_film_incentive"), get_program_requirements("us_la_film_incentive")
    assert "125" in la_doc.citation and "ANNUAL CAP CONFLICT" in la_prof.evidence.notes
    wa = get_doctrine("us_wa_motion_picture_competitiveness")
    assert wa.annual_cap_usd == pytest.approx(get_program_requirements(wa.program_slug).annual_program_cap_usd)


# ── F-05: Mexico -- native MXN per-project cap and minimum spend, MXN tracked, unavailable rate fails closed ─────────
def test_mxn_is_a_tracked_currency_so_a_live_refresh_fetches_it():
    assert pn._JURISDICTION_CURRENCY["MX"] == "MXN" and "MXN" in pn.ALL_TRACKED_CURRENCIES


MX_CONFIRMED = frozenset({"mx_federal_film_incentive_2026"})   # the Comite Tecnico's authorization of the full 30% for this project (producer-confirmed scenario)


def test_mexico_is_an_unconfirmed_committee_ceiling_until_the_award_is_confirmed():
    # Lineamientos (DOF 2026-03-30) lineamiento 4 III: the Comite Tecnico sets the percentage per project; 30% is only the ceiling.
    seg = _price("MX", "mx_federal_film_incentive_2026", 12_000_000.0, _fx(MXN=20.0))
    # potential only: 30% x 12,000,000 = 3.6m, clipped by the MXN 40m cap at 20 MXN/USD (2.0m); nothing guaranteed until the committee awards a percentage
    assert seg.executable and seg.is_band_ceiling and seg.ceiling_requires_confirmation and seg.incentive_floor_usd == 0.0
    assert seg.incentive_ceiling_usd == pytest.approx(2_000_000.0)


def test_mexico_cap_converts_through_the_fx_context_and_binds_a_large_credit():
    rate = 20.0  # synthetic MXN per USD
    big = _price("MX", "mx_federal_film_incentive_2026", 12_000_000.0, _fx(MXN=rate), MX_CONFIRMED)
    cap_usd = 40_000_000.0 / rate
    assert big.executable and big.incentive_cap_type == "per_project_native"
    assert big.incentive_cap_usd == pytest.approx(cap_usd)
    assert big.incentive_floor_usd == pytest.approx(cap_usd)           # 30% x 12m = 3.6m > 2.0m cap
    mid = _price("MX", "mx_federal_film_incentive_2026", 3_000_000.0, _fx(MXN=rate), MX_CONFIRMED)
    assert mid.incentive_floor_usd == pytest.approx(3_000_000.0 * 0.30) and mid.incentive_cap_applied_usd == 0.0


def test_mexico_minimum_spend_is_evaluated_natively_in_mxn():
    rate = 20.0
    below = _price("MX", "mx_federal_film_incentive_2026", 39_999_999.0 / rate, _fx(MXN=rate), MX_CONFIRMED)
    above = _price("MX", "mx_federal_film_incentive_2026", 40_000_000.0 / rate, _fx(MXN=rate), MX_CONFIRMED)
    assert not below.executable and above.executable


def test_mexico_without_an_mxn_rate_fails_closed_never_uncapped_and_never_assumed_eligible():
    ctx = CanonicalFXContext(
        snapshot_date="2026-10-02", rates={c: 1.5 for c in pn.ALL_TRACKED_CURRENCIES if c != "MXN"},
        source="control", freshness_status="fresh")
    seg = _price("MX", "mx_federal_film_incentive_2026", 12_000_000.0, ctx)
    assert not seg.executable and seg.incentive_floor_usd == 0.0 and seg.incentive_ceiling_usd == 0.0


def test_mexico_envelope_text_no_longer_contradicts_the_decree_reading():
    prof = get_program_requirements("mx_federal_film_incentive_2026")
    env = prof.additional_facts if hasattr(prof, "additional_facts") else {}
    text = repr(env) + (prof.evidence.notes if prof.evidence else "")
    assert "not an annual appropriation" not in text


# ── F-06: a stack candidate's qualifying spend must honor the production's stated-outside accounts ───────────────────
def test_stack_register_excludes_spend_the_production_states_is_incurred_elsewhere():
    from app.calculators.qualification_derivation import BudgetLine
    from app.calculators.qualification_model import QualificationState as S
    from app.services.canonical_evaluation import _price_candidate
    from app.services.canonical_project_economics import ProjectEconomicInputs

    lines = [
        BudgetLine("3100", "CAMERA DEPARTMENT", 1_000_000.0, spend_category="btl_crew_labor", line_id="L-3100"),
        BudgetLine("5000", "EDITORIAL - OUTSIDE", 100_000.0, spend_category="post_production", line_id="L-5000"),
    ]
    base = dict(
        project_id="synthetic", project_name="synthetic", jurisdiction_code="MU", production_type="feature_film",
        gross_budget_usd=1_100_000.0, leaf_account_sum_usd=1_100_000.0, budget_lines=lines,
        spend_category_by_code={"3100": "btl_crew_labor", "5000": "post_production"},
        offshore_payroll_accounts=frozenset(),
    )
    stated_outside = ProjectEconomicInputs(accounts_outside_jurisdiction=frozenset({"5000"}), **base)
    unstated = ProjectEconomicInputs(accounts_outside_jurisdiction=frozenset(), **base)

    pricing_out, register_out, _ = _price_candidate(stated_outside, "CA-ON", "on_ofttc")
    pricing_in, register_in, _ = _price_candidate(unstated, "CA-ON", "on_ofttc")
    qualifying = lambda reg: sum(a.amount_usd for a in reg if a.state == S.QUALIFIES)  # noqa: E731
    # explicit sums over the raw synthetic lines
    assert qualifying(register_in) == pytest.approx(1_100_000.0)
    assert qualifying(register_out) == pytest.approx(1_000_000.0)
    # and the stack-facing register agrees with what the priced single-program segment itself counted as QPE
    seg_out = [s for s in pricing_out.segments if getattr(s, "program_slug", None) == "on_ofttc"][0]
    assert qualifying(register_out) == pytest.approx(seg_out.qpe_usd)
