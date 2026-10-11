"""Project-level eligibility gates that no single jurisdiction segment can decide on its own.

California Film & Television Tax Credit Program 4.0 (California Film Commission, Program Guidelines dated January 1, 2026, section II.A.1, PDF
page 3; applies to allocation letters dated on or after July 1, 2025): a project is eligible only if EITHER at least 75% of the production
budget is spent in California OR at least 75% of principal-photography days are wholly in California. This is distinct from the VFX /
out-of-zone UPLIFT tests. A production shot in Manitoba with only its VFX in California fails both branches, so the California credit cannot
price on the VFX alone; the candidate stays visible with an affirmative PROJECT_ELIGIBILITY_GATE_FAILED rejection (never silently priced, hidden,
or reported as missing contracts).

Branch reconstruction from a modeled structure (assumptions, disclosed):
  * spend share = the jurisdiction's allocated dollars / all allocated dollars of the structure;
  * principal-photography share = the share of the structure's PRINCIPAL-PHOTOGRAPHY-component dollars (the location-bound below-the-line
    production accounts) allocated to the jurisdiction, a dollar-weighted proxy for shooting days; where the structure carries no such
    lines, the share is 1.0 for the structure's principal / primary jurisdiction and 0.0 elsewhere. A producer-stated percentage of shooting
    days wholly in California (amount fact `ca_principal_photography_days_in_california_pct`, 0-100) replaces the proxy.
Nothing here reads a real project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

GATE_FAILED_PREFIX = "PROJECT_ELIGIBILITY_GATE_FAILED:"


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
    passed: bool
    spend_share: float
    photography_share: float | None
    photography_basis: str
    reason: str | None


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
    pp_rows = [(j, a) for j, a, c, _ in rows if c == "principal_photography"]
    stated = (amount_facts or {}).get(gate.photography_fact_key)
    if stated is not None and 0 <= float(stated) <= 100:
        pp_share, basis = float(stated) / 100.0, f"producer-stated {float(stated):.1f}% of principal-photography days"
    elif pp_rows and sum(a for _, a in pp_rows) > 0:
        pp_share = sum(a for j, a in pp_rows if j == jurisdiction_code) / sum(a for _, a in pp_rows)
        basis = "dollar-weighted share of the location-bound principal-photography accounts (proxy for shooting days)"
    elif primary_jurisdiction:
        pp_share = 1.0 if jurisdiction_code == primary_jurisdiction else 0.0
        basis = f"no principal-photography accounts modeled: principal production is in {primary_jurisdiction}"
    else:
        pp_share, basis = None, "principal-photography location not modeled"
    eps = 1e-9
    passed = spend_share + eps >= gate.spend_min or (pp_share is not None and pp_share + eps >= gate.photography_min)
    reason = None
    if not passed:
        reason = (f"{GATE_FAILED_PREFIX} {gate.label} not met for {jurisdiction_code}: {spend_share:.1%} of the production budget is spent there "
                  f"(needs {gate.spend_min:.0%}) and {'unknown' if pp_share is None else f'{pp_share:.1%}'} of principal photography is there "
                  f"(needs {gate.photography_min:.0%}; {basis}). Either branch suffices; neither is met, so this program's credit cannot be claimed "
                  f"on the spend routed here ({gate.source}).")
    return GateOutcome(passed, spend_share, pp_share, basis, reason)
