"""Project-level eligibility gates that no single jurisdiction segment can decide on its own.

California Film & Television Tax Credit Program 4.0 (California Film Commission, Program Guidelines dated January 1, 2026, section II.A.1, PDF
page 3; applies to allocation letters dated on or after July 1, 2025): a project is eligible only if EITHER at least 75% of the production
budget is spent in California OR at least 75% of principal-photography days are wholly in California. This is distinct from the VFX /
out-of-zone UPLIFT tests. A production shot in Manitoba with only its VFX in California fails both branches, so the California credit cannot
price on the VFX alone; the candidate stays visible with an affirmative PROJECT_ELIGIBILITY_GATE_FAILED rejection (never silently priced, hidden,
or reported as missing contracts).

Evidence discipline (Codex review of de053f69): DOLLARS DO NOT ESTABLISH SHOOTING DAYS. The spend branch is arithmetic on allocated dollars and may pass
or fail on its own terms. The principal-photography-days branch is decided only from days evidence:
  * PASS      - spend share >= 75%; or a producer-stated share of California shooting days >= 75%; or the modeled structure places ALL of its
                principal photography in the jurisdiction (an explicit modeled scenario, not an inferred ratio);
  * FAIL      - spend share < 75% AND (a producer-stated share < 75%, or the modeled structure places ALL principal photography outside the
                jurisdiction). The latter fails THAT MODELED SCENARIO (e.g. a Manitoba shoot with a California VFX slice); it is not a finding about
                an actual shoot;
  * CONDITIONAL - spend share < 75% and the days are unknown or mixed (some but not all modeled photography in the jurisdiction, or none modeled):
                the credit is a disclosed conditional planning scenario with no guaranteed value until the days are stated; neither a pass nor a failure.
Where the modeled structure carries no principal-photography accounts, its principal-production jurisdiction stands for the modeled shoot.
A producer-stated percentage (amount fact `ca_principal_photography_days_in_california_pct`, 0-100) overrides any modeled placement.
Nothing here reads a real project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

GATE_FAILED_PREFIX = "PROJECT_ELIGIBILITY_GATE_FAILED:"
GATE_CONDITIONAL_PREFIX = "PROJECT_ELIGIBILITY_GATE_CONDITIONAL:"


@dataclass(frozen=True)
class ProjectGate:
    jurisdiction_prefix: str
    spend_min: float
    photography_min: float
    photography_fact_key: str
    label: str
    source: str


PROJECT_GATES: dict[str, ProjectGate] = {
    "ca_film_30": ProjectGate(
        "US-CA", 0.75, 0.75, "ca_principal_photography_days_in_california_pct", "California Program 4.0 project eligibility",
        "California Film Commission, Program 4.0 Guidelines (Jan 1, 2026) section II.A.1: at least 75% of the production budget spent in California OR "
        "at least 75% of principal-photography days wholly in California (allocation letters dated on or after July 1, 2025)"),
}


@dataclass(frozen=True)
class GateOutcome:
    status: str                      # "PASS" | "FAIL" | "CONDITIONAL"
    spend_share: float
    photography_share: float | None  # None when the days are unknown
    photography_basis: str
    reason: str | None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"

    @property
    def conditional(self) -> bool:
        return self.status == "CONDITIONAL"


def evaluate_project_gate(program_slug: str | None, jurisdiction_code: str, rows: Iterable[tuple], primary_jurisdiction: str | None,
                          amount_facts: dict | None = None) -> GateOutcome | None:
    """rows: (jurisdiction_code, amount_usd, component_label, structural_type) for EVERY allocation of the structure. None when the program has no gate."""
    from app.data.program_slug_aliases import canonical_slug
    gate = PROJECT_GATES.get(canonical_slug(program_slug)) if program_slug else None
    if gate is None:
        return None
    rows = [(j, float(a), c, t) for j, a, c, t in rows]
    total = sum(a for _, a, _, _ in rows)
    spend_share = (sum(a for j, a, _, _ in rows if j == jurisdiction_code) / total) if total > 0 else 0.0
    eps = 1e-9
    if spend_share + eps >= gate.spend_min:
        return GateOutcome("PASS", spend_share, None, f"spend branch met ({spend_share:.1%} of the production budget)", None)
    pp_rows = [(j, a) for j, a, c, _ in rows if c == "principal_photography" and a > 0]
    stated = (amount_facts or {}).get(gate.photography_fact_key)
    status, pp_share, basis = "CONDITIONAL", None, "principal-photography days are not stated and the modeled placement is mixed or absent"
    if stated is not None and 0 <= float(stated) <= 100:
        pp_share = float(stated) / 100.0
        status = "PASS" if pp_share + eps >= gate.photography_min else "FAIL"
        basis = f"producer-stated {float(stated):.1f}% of principal-photography days wholly in {jurisdiction_code}"
    elif pp_rows:
        inside = sum(a for j, a in pp_rows if j == jurisdiction_code)
        outside = sum(a for j, a in pp_rows if j != jurisdiction_code)
        if outside <= 0:
            status, pp_share, basis = "PASS", 1.0, f"the modeled structure places ALL of its principal photography in {jurisdiction_code} (explicit modeled scenario)"
        elif inside <= 0:
            status, pp_share, basis = "FAIL", 0.0, f"the modeled structure places ALL of its principal photography outside {jurisdiction_code} (explicit modeled scenario; not an inferred dollar ratio)"
        else:
            basis = (f"the modeled principal photography is split between {jurisdiction_code} and elsewhere; dollar shares do not establish shooting days, so the "
                     "days branch is undetermined")
    elif primary_jurisdiction:
        if primary_jurisdiction == jurisdiction_code:
            status, pp_share, basis = "PASS", 1.0, f"no principal-photography accounts modeled: principal production is modeled in {jurisdiction_code}"
        else:
            status, pp_share, basis = "FAIL", 0.0, f"no principal-photography accounts modeled: principal production is modeled in {primary_jurisdiction}, outside {jurisdiction_code}"
    if status == "PASS":
        return GateOutcome("PASS", spend_share, pp_share, basis, None)
    detail = (f"{gate.label} for {jurisdiction_code}: {spend_share:.1%} of the production budget is spent there (needs {gate.spend_min:.0%}) and "
              f"the principal-photography branch (needs {gate.photography_min:.0%} of days wholly in {jurisdiction_code}) is: {basis}. {gate.source}.")
    if status == "FAIL":
        return GateOutcome("FAIL", spend_share, pp_share, basis, f"{GATE_FAILED_PREFIX} not met in this modeled scenario - {detail}")
    return GateOutcome("CONDITIONAL", spend_share, pp_share, basis,
                       f"{GATE_CONDITIONAL_PREFIX} not established - {detail} The credit is a conditional planning scenario with no guaranteed value until the days are stated.")
