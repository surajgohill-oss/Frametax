"""NA-RECONCILIATION-25: the Manitoba evidence text. The retained Manitoba text supports only: Income Tax Act (Manitoba) s.7.5(1) excludes the Manitoba credit itself from its definition; Manitoba Film & Music TC-2
administrative guidance supports compatibility with the CPTC / PSTC and administrative non-grinding; the forward allocation against federal PSTC labour is an assumed allocation under ITA 125.5(1)(b). A quotation that a Manitoba
statute expressly excludes federal film credits from its 'government assistance' was withdrawn and must not return. Arithmetic is unchanged (controls in test_canonical_stack_bridge)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = [ROOT / "backend" / "app", ROOT / "backend" / "alembic", ROOT / "backend" / "tests", ROOT / "docs", ROOT / "handoff-cineglobe.md", ROOT / "PROJECT_RULES.md"]
WITHDRAWN = [re.compile(p, re.I) for p in (
    r"federal film credit is excluded from manitoba",
    r"excludes\s+(any\s+)?\"?any film and video",
    r"manitoba'?s own \"?government assistance\"? excludes",
    r"film and video production tax\s+credit under (this act|the manitoba)",
    r"federal credits (are|is) not assistance to the manitoba",
)]


def _files():
    for base in SCAN:
        if base.is_file():
            yield base
        else:
            for p in base.rglob("*"):
                if p.is_file() and p.suffix in {".py", ".md", ".json", ".csv", ".txt"} and "__pycache__" not in p.parts and p.name != Path(__file__).name:
                    yield p


def test_the_withdrawn_manitoba_quotation_does_not_appear_as_a_live_claim():
    offenders = []
    for p in _files():
        text = p.read_text(errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(rx.search(line) for rx in WITHDRAWN) and not re.search(r"withdr|NA-RECONCILIATION-25|no statutory exclusion", line, re.I):
                offenders.append(f"{p.relative_to(ROOT)}:{line_no}")
    assert offenders == [], f"the withdrawn Manitoba 'government assistance' quotation reappeared: {offenders}"


def test_the_supported_manitoba_classification_is_stated_in_the_executable_rule():
    src = (ROOT / "backend" / "app" / "optimization" / "stacking_rules.py").read_text()
    assert "s.7.5(1) excludes only the Manitoba credit itself" in src
    assert "administrative non-grinding" in src and "ASSUMED allocation" in src and "125.5(1)(b)" in src
    assert "whole credit" in src and "lower bound" in src


def test_the_manitoba_arithmetic_is_unchanged():
    from app.optimization.stacking_rules import STACKING_RULES_VERSION
    assert STACKING_RULES_VERSION  # the rule table still loads; the dollar figures are pinned by test_canonical_stack_bridge's Manitoba controls
