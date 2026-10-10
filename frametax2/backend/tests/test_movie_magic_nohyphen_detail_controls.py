"""Movie Magic detail coverage for the un-hyphenated export (PROJECT_OPEN_ITEM_RECOVERY F-07, Codex PAR-A01).

SYNTHETIC ONLY: the page text below is built here, in the row order the extraction layer produces for the
"CODE  DESCRIPTION" detail-page export, with invented amounts. Expectations are explicit sums over those rows (the
authored 'Account Total for' line is the independent parent total); no persisted generation or real budget supplies them."""
from __future__ import annotations

import pytest

from app.ingestion.budget_parser import _movie_magic_subaccounts

DETAIL_PAGE = "\n".join([
    "Acct#", "Description", "Amt", "Units", "X", "Rate", "Sub T", "Total",
    "1100  STORY, RIGHTS &...",
    "1101", "STORY RIGHTS", "1", "1", "10,000", "10,000", "Total", "$10,000",
    "1103", "WRITERS", "Writer", "Flat Fee", "1", "Flat", "1", "52,100", "52,100", "Subtotal", "$52,100", "Total", "$52,100",
    "1112", "SCRIPT RESEARCH", "1", "1", "1,000", "1,000", "Total", "$1,000",
    "1199", "Total Fringes", "Payroll", "0.94%", "52,100", "490", "WGA", "21%", "52,100", "10,941", "$11,431",
    "Account Total for 1100", "$74,531",
    "1200  PRODUCERS UNIT",
    "1201", "EXECUTIVE PRODUCER", "NAME: FEE", "1", "Flat", "1", "2000", "2000", "Total", "$2,000",
    "Account Total for 1200", "$2,000",
])

TOPSHEET_PAGE = "\n".join([
    "Acct#", "Category Description", "Total",
    "1100", "STORY, RIGHTS & CONTINUITY", "$74,531",
    "1200", "PRODUCERS UNIT", "$2,000",
])

HYPHEN_PAGE = "\n".join([
    "11-00 - STORY",
    "11-01", "STORY RIGHTS", "1", "1", "500", "500", "Total", "$500",
    "11-02", "RESEARCH", "1", "1", "250", "250", "Total", "$250",
])


def test_unhyphenated_detail_headings_capture_every_authored_child_and_the_children_conserve_the_parent():
    parents = _movie_magic_subaccounts([DETAIL_PAGE])
    children = parents["1100"]
    assert [c["account_code"] for c in children] == ["1101", "1103", "1112", "1199"]
    assert [c["amount_usd"] for c in children] == [10_000.0, 52_100.0, 1_000.0, 11_431.0]
    assert sum(c["amount_usd"] for c in children) == pytest.approx(74_531.0)   # the authored 'Account Total for 1100'


def test_a_bare_rate_or_amount_row_is_not_mistaken_for_a_child_account_code():
    # the row "2000" under parent 1200 is a rate/amount token, not a 12xx account code
    parents = _movie_magic_subaccounts([DETAIL_PAGE])
    assert [c["account_code"] for c in parents["1200"]] == ["1201"]
    assert sum(c["amount_usd"] for c in parents["1200"]) == pytest.approx(2_000.0)


def test_a_topsheet_page_with_code_and_description_on_separate_rows_creates_no_detail_parent():
    assert _movie_magic_subaccounts([TOPSHEET_PAGE]) == {}


def test_the_hyphenated_export_still_parses_unchanged():
    parents = _movie_magic_subaccounts([HYPHEN_PAGE])
    assert [(c["account_code"], c["amount_usd"]) for c in parents["11-00"]] == [("11-01", 500.0), ("11-02", 250.0)]
