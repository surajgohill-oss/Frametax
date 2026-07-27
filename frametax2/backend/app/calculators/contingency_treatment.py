"""
Final Global Discovery phase — Objective 4: first-class contingency
treatment.

CANONICAL RULE: a budgeted-but-undeployed contingency reserve is not
actual incurred qualifying expenditure. It is excluded from QPE by
default (see qualification_derivation.py's use of
AuthorityBasis.STRUCTURAL_DEFINITION for the "no program-specific
contingency rule" case). A producer may DEPLOY (allocate) part or all
of a contingency line to real destination budget lines; the deployed
amount then inherits the RECEIVING line's own eligibility, cap,
residency, location, and exclusion treatment — it is priced exactly as
if it had always been native spend in that destination category. The
undeployed remainder stays excluded.

This module is the data model + the pure expansion function. It never
decides what "qualifies" means — that remains entirely the statutory
ladder in qualification_derivation.py. All this module does is turn ONE
contingency BudgetLine into SEVERAL BudgetLines (the undeployed
remainder, still category="contingency"; one per deployment, category =
the destination) so the EXISTING, unmodified ladder logic can price each
piece on its own terms. No new account codes are introduced — deployed
and undeployed lines all keep the SAME account_code as the source
contingency line, so upstream allocation (production_allocation.py,
which assigns whole accounts to jurisdictions) is completely unaffected;
only qualification (which runs strictly after allocation) sees the
split.

Program-specific over-rides are not modeled here at all: they already
exist as ordinary SpendRule rows for spend_category="contingency" (e.g.
Mauritius's verified unconditional inclusion, Germany's verified
"excluded unless dissolved") and continue to win via the ladder's
existing step 4, unchanged. This module only supplies the NEW general
default for programs with no such explicit rule, and the deployment
splitting mechanics.

No blanket "qualify contingency" switch exists anywhere in this module
— every dollar's fate is either (a) the untouched per-program statutory
rule for category="contingency" (for the undeployed remainder), or (b)
the untouched per-program statutory rule for the producer-chosen
destination category (for each deployed amount).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field


class ContingencyState(str, enum.Enum):
    UNDEPLOYED = "undeployed"
    PARTIALLY_DEPLOYED = "partially_deployed"
    FULLY_DEPLOYED = "fully_deployed"


@dataclass(frozen=True)
class ContingencyDeployment:
    """One producer decision: move `amount_usd` of a contingency reserve
    into a real destination budget line. Immutable — the audit trail is
    the ordered tuple of these on a ContingencyAllocation, never edited
    in place; a correction is a new deployment (positive) or, if truly
    reversed, handled by the caller re-deriving the allocation from a
    trimmed deployments tuple (still fully disclosed, never silently
    overwritten)."""

    destination_account_code: str
    destination_description: str
    destination_spend_category: str
    amount_usd: float
    note: str
    deployed_by: str
    deployed_at: str  # ISO 8601 date/datetime — caller-supplied, never fabricated


@dataclass(frozen=True)
class ContingencyAllocation:
    """The full deployment record for ONE contingency budget line
    (identified by its own account_code). original_amount_usd is the
    line's real budgeted amount — never re-derived, never assumed."""

    source_account_code: str
    source_description: str
    original_amount_usd: float
    deployments: tuple[ContingencyDeployment, ...] = field(default_factory=tuple)

    @property
    def deployed_amount_usd(self) -> float:
        return round(sum(d.amount_usd for d in self.deployments), 2)

    @property
    def undeployed_amount_usd(self) -> float:
        return round(self.original_amount_usd - self.deployed_amount_usd, 2)

    @property
    def state(self) -> ContingencyState:
        deployed = self.deployed_amount_usd
        if deployed <= 0:
            return ContingencyState.UNDEPLOYED
        if self.undeployed_amount_usd <= 0.005:
            return ContingencyState.FULLY_DEPLOYED
        return ContingencyState.PARTIALLY_DEPLOYED


def add_deployment(
    allocation: ContingencyAllocation,
    deployment: ContingencyDeployment,
) -> ContingencyAllocation:
    """Return a NEW ContingencyAllocation with `deployment` appended.
    Never allows deploying more than the undeployed balance — the only
    validation this module performs; every other judgment (whether the
    destination category is eligible, capped, excluded) is left entirely
    to the statutory ladder that prices the resulting BudgetLine."""
    if deployment.amount_usd <= 0:
        raise ValueError("Deployment amount must be positive.")
    if deployment.amount_usd > allocation.undeployed_amount_usd + 0.005:
        raise ValueError(
            f"Cannot deploy ${deployment.amount_usd:,.2f} — only "
            f"${allocation.undeployed_amount_usd:,.2f} of contingency "
            f"'{allocation.source_account_code}' remains undeployed."
        )
    return ContingencyAllocation(
        source_account_code=allocation.source_account_code,
        source_description=allocation.source_description,
        original_amount_usd=allocation.original_amount_usd,
        deployments=allocation.deployments + (deployment,),
    )


def expand_contingency_lines(
    lines: list,
    allocations: dict[str, ContingencyAllocation] | None,
) -> list:
    """Expand every contingency BudgetLine that has a matching
    ContingencyAllocation into: the undeployed remainder (same
    account_code, same spend_category="contingency", reduced amount) plus
    one line per deployment (same account_code, the DESTINATION
    spend_category, the deployed amount). A contingency line with NO
    matching allocation record passes through completely unchanged — this
    is what guarantees the mechanism is inert (byte-identical output) for
    any production that has never used it, and why there is no blanket
    switch: each contingency line's treatment is opt-in, one line at a
    time, via an explicit ContingencyAllocation."""
    from app.calculators.qualification_derivation import BudgetLine

    if not allocations:
        return lines
    expanded: list = []
    for line in lines:
        alloc = allocations.get(line.account_code)
        if alloc is None or (line.spend_category or "") != "contingency":
            expanded.append(line)
            continue
        undeployed = alloc.undeployed_amount_usd
        if undeployed > 0.005:
            expanded.append(BudgetLine(
                account_code=line.account_code,
                description=f"{line.description} (undeployed reserve)",
                amount_usd=undeployed,
                spend_category="contingency",
                is_memo=False,
            ))
        for d in alloc.deployments:
            expanded.append(BudgetLine(
                account_code=line.account_code,
                description=(
                    f"{line.description} — deployed to "
                    f"{d.destination_description} ({d.note})"
                ),
                amount_usd=d.amount_usd,
                spend_category=d.destination_spend_category,
                is_memo=False,
            ))
    return expanded
