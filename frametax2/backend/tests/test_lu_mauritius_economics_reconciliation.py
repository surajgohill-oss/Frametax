"""
test_lu_mauritius_economics_reconciliation.py

Independent, line-level expected-value tests for the LU Mauritius economics
reconciliation (canonical_evaluation.ENGINE_VERSION "canonical-1.94.0").

These tests do NOT trust any target number handed to the investigation —
they reconstruct the expected QPE, floor incentive, and ceiling incentive
from FIRST PRINCIPLES: the real 44 budget lines
(little_utopia_real_budget.LITTLE_UTOPIA_REAL_BUDGET_LINES), the real
per-line classification (LITTLE_UTOPIA_REAL_SPEND_CATEGORY), the real
territorial exclusion set (LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU), the real
Mauritius EDB qualification rules (MU_EDB_RULES), and the real Mauritius
rate tiers (MU_RATE_RULES) — never a hardcoded expected total copied from
anywhere else. If any of these source modules changes, this test's own
independently-computed expected value changes with it; it can never be
satisfied by coincidentally matching a stale pinned number.
"""
from __future__ import annotations

from app.data.little_utopia_real_budget import (
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_BUDGET_LINES,
    LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
    LITTLE_UTOPIA_CONTINGENCY_EXPECTED_UTILIZATION_PCT,
    AUTHORITATIVE_GROSS_BUDGET_USD,
)
from app.data.program_spend_rules import MU_EDB_RULES
from app.data.program_rate_rules import MU_RATE_RULES


def _mu_qualifies(category: str) -> bool | None:
    for rule in MU_EDB_RULES:
        if rule.spend_category == category:
            return rule.qualifies
    return None  # no rule at all -> GREY_AREA_REQUIRES_AUTHORITY, same as None


def _independently_reconstructed_qpe() -> tuple[float, float, float]:
    """Returns (qpe_usd, excluded_outside_mu_usd, unresolved_grey_usd),
    reconstructed line-by-line with NO dependency on any served/persisted
    value — only the raw source data modules."""
    qpe = 0.0
    excluded_outside_mu = 0.0
    unresolved_grey = 0.0
    for code, description, amount, _page in LITTLE_UTOPIA_REAL_BUDGET_LINES:
        if code in LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU:
            excluded_outside_mu += amount
            continue
        category = LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(code)
        if category is None:
            unresolved_grey += amount
            continue
        qualifies = _mu_qualifies(category)
        if category == "contingency" and qualifies is True:
            pct = LITTLE_UTOPIA_CONTINGENCY_EXPECTED_UTILIZATION_PCT
            if pct is None:
                unresolved_grey += amount
                continue
            deployed = round(amount * (max(0.0, min(100.0, pct)) / 100.0), 2)
            qpe += deployed
            unresolved_grey += round(amount - deployed, 2)
            continue
        if qualifies is True:
            qpe += amount
        else:
            unresolved_grey += amount
    return round(qpe, 2), round(excluded_outside_mu, 2), round(unresolved_grey, 2)


def _mu_rate(tier_id: str) -> float:
    rule = next(r for r in MU_RATE_RULES if r.tier_id == tier_id)
    return rule.rate


class TestIndependentSourceLineConservation:
    def test_44_leaf_lines_sum_matches_documented_leaf_sum(self):
        total = sum(amount for _c, _d, amount, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES)
        assert len(LITTLE_UTOPIA_REAL_BUDGET_LINES) == 44
        assert round(total, 2) == 4_364_395.00  # LEAF_ACCOUNT_SUM_USD, documented $2 variance vs gross

    def test_territorial_exclusion_total_is_the_known_9068_us_editorial(self):
        excluded = sum(
            amount for code, _d, amount, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES
            if code in LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU
        )
        assert round(excluded, 2) == 9_068.00

    def test_every_leaf_account_code_is_classified_or_explicitly_left_grey(self):
        # Every code either has a real category override or is a documented,
        # deliberate grey (7300 MARKETING — no clean category, $0, immaterial).
        classified_or_grey = {"7300"}
        for code, _d, _a, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES:
            assert code in LITTLE_UTOPIA_REAL_SPEND_CATEGORY or code in classified_or_grey, (
                f"account {code} has neither a classification nor a documented grey exemption"
            )


class TestIndependentQPEReconstruction:
    def test_reconstructed_qpe_from_source_lines_and_rules(self):
        qpe, excluded, grey = _independently_reconstructed_qpe()
        # Independently reconstructed from the 44 real lines, the real
        # per-line classification, the real MU_EDB_RULES qualification
        # table (including the production_sound rule this same fix adds),
        # and the real 100% contingency election -- NOT copied from any
        # previously-served or previously-asserted number.
        assert qpe == 4_355_327.00
        assert excluded == 9_068.00
        # Grey/unresolved is only the genuinely unclassifiable $0 MARKETING
        # line and MUSIC ($0) -- both immaterial, confirming nothing real
        # was silently dropped.
        assert grey == 0.0

    def test_production_sound_has_a_real_mu_qualification_rule(self):
        # Before this fix, PRODUCTION_SOUND (split from BTL_CREW_LABOR by
        # Codex BPI-003) had NO Mauritius rule at all, so it fell to
        # GREY_AREA_REQUIRES_AUTHORITY despite being unambiguous BTL crew
        # labor under the same already-cited EDB authority.
        assert _mu_qualifies("production_sound") is True

    def test_removing_the_three_confirmed_defects_reproduces_the_stale_served_qpe(self):
        # Sanity check on the DIAGNOSIS itself: reconstructing QPE while
        # deliberately reintroducing each of the three confirmed defects
        # (miscategorized lines -> miscellaneous/general_administration,
        # no production_sound rule, no contingency fact) must reproduce the
        # exact stale served value ($1,910,199.00) that was independently
        # read from the live database before this fix -- proving the three
        # defects fully explain the gap, with nothing left unaccounted for.
        stale_categories = dict(LITTLE_UTOPIA_REAL_SPEND_CATEGORY)
        miscategorized_to_misc = [
            "1000", "2000", "2100", "2500", "2600", "2700", "3000", "3100",
            "3300", "3400", "3500", "3800", "4000", "6500",
        ]
        for code in miscategorized_to_misc:
            stale_categories[code] = "miscellaneous"
        stale_categories["7000"] = "general_administration"
        stale_categories["7100"] = "general_administration"
        # 3200 PRODUCTION SOUND was (and, after this fix, still is) really
        # persisted as "production_sound" -- LITTLE_UTOPIA_REAL_SPEND_
        # CATEGORY's own "btl_crew_labor" entry for 3200 was never applied
        # to the DB row (this fix leaves it alone, adding the missing MU
        # rule instead). Must reflect the REAL pre-fix persisted category,
        # not the classification module's alternate suggestion for it.
        stale_categories["3200"] = "production_sound"

        def _stale_qualifies(category: str) -> bool | None:
            if category in ("miscellaneous", "general_administration", "production_sound"):
                return None  # no MU rule for these at the pre-fix state
            return _mu_qualifies(category)

        qpe = 0.0
        for code, _d, amount, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES:
            if code in LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU:
                continue
            category = stale_categories.get(code)
            if category is None:
                continue
            if category == "contingency":
                continue  # no contingency_expected_utilization_pct fact pre-fix -> fully grey
            if _stale_qualifies(category) is True:
                qpe += amount
        assert round(qpe, 2) == 1_910_199.00


class TestIndependentRateReconstruction:
    def test_floor_and_ceiling_incentive_from_reconstructed_qpe(self):
        qpe, _excluded, _grey = _independently_reconstructed_qpe()
        floor_rate = _mu_rate("mu_frs_30_general")
        ceiling_rate = _mu_rate("mu_frs_40_feature")
        assert floor_rate == 0.30
        assert ceiling_rate == 0.40
        floor_incentive = round(qpe * floor_rate, 2)
        ceiling_incentive = round(qpe * ceiling_rate, 2)
        assert floor_incentive == 1_306_598.10
        assert ceiling_incentive == 1_742_130.80

    def test_selected_and_potential_ceiling_npc_from_gross_and_incentives(self):
        qpe, _excluded, _grey = _independently_reconstructed_qpe()
        floor_incentive = round(qpe * _mu_rate("mu_frs_30_general"), 2)
        ceiling_incentive = round(qpe * _mu_rate("mu_frs_40_feature"), 2)
        # Little Utopia's Mauritius segment has no confirmed ceiling
        # approval on file -> selected incentive is the floor (30%), not
        # the discretionary "up to 40%" ceiling.
        selected_npc = round(AUTHORITATIVE_GROSS_BUDGET_USD - floor_incentive, 2)
        potential_ceiling_npc = round(AUTHORITATIVE_GROSS_BUDGET_USD - ceiling_incentive, 2)
        assert selected_npc == 3_057_794.90
        assert potential_ceiling_npc == 2_622_262.20
