"""Programs that are claimable only alongside a host credit in the same structure.

A host dependency is a calculation rule, not a producer fact: the production does not "state" it, the structure either contains the host or it does not. The dependent program's rate rule carries
a condition that needs the synthetic fact ``fact_key``; this module is the single place that derives that fact from the programs of one structure, and the pricing paths that know their structure
(the structural generator, the candidate pricing loop) add it. A path that does not know a structure never adds it, so the dependent program stays potential-only (floor zero, ceiling kept).

BC DAVE (NA-RECONCILIATION-13): Income Tax Act (BC) s.81.2(1)(a) makes the digital animation, visual effects and post-production credit for an eligible production available only to a corporation
"eligible for, and ... making an application ... for, a tax credit in relation to the production under section 80"; s.82.3(1)(a) does the same for the production services DAVE credit and the
s.82.1 credit. Sections 80 to 82 and 82.1 to 82.3 cannot both be claimed for one production (s.83.1), so the hosts are alternatives, and a structure that holds both is already refused by the pair rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StructuralPrerequisite:
    program_slug: str
    host_slugs: tuple[str, ...]
    fact_key: str
    authority: str


STRUCTURAL_PREREQUISITES: dict[str, StructuralPrerequisite] = {
    "ca_bc_dave": StructuralPrerequisite(
        program_slug="ca_bc_dave",
        host_slugs=("ca_bc_film_tv_tax_credit", "ca_bc_pstc"),
        fact_key="ca_bc_dave__structure_host_credit_present",
        authority=("Income Tax Act (BC) s.81.2(1)(a): eligible for, and applying for, the s.80 credit (domestic host, ca_bc_film_tv_tax_credit); "
                   "s.82.3(1)(a): eligible for, and applying for, the s.82.1 credit (production services host, ca_bc_pstc). s.83.1: the two host families are alternatives for one production."),
    ),
}


def _canonical(slug: str) -> str:
    from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES

    return PROGRAM_SLUG_ALIASES.get(slug, slug)


def prerequisite_for(program_slug: str) -> StructuralPrerequisite | None:
    return STRUCTURAL_PREREQUISITES.get(_canonical(program_slug))


def host_present(program_slug: str, structure_slugs: Iterable[str] | None) -> bool:
    """True when the structure contains at least one host of ``program_slug`` (False when the program has no prerequisite is never asked)."""
    pre = prerequisite_for(program_slug)
    if pre is None or not structure_slugs:
        return False
    present = {_canonical(s) for s in structure_slugs}
    return any(h in present for h in pre.host_slugs)


def structure_derived_facts(program_slug: str, structure_slugs: Iterable[str] | None) -> frozenset[str]:
    """The synthetic fact keys this structure establishes for ``program_slug`` (empty when it has no prerequisite or the host is absent)."""
    pre = prerequisite_for(program_slug)
    if pre is None or not host_present(program_slug, structure_slugs):
        return frozenset()
    return frozenset({pre.fact_key})
