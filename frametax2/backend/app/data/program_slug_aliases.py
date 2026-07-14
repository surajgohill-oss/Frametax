"""
program_slug_aliases.py

Canonical program-slug reconciliation between independently-built
catalogs. structure_graph_model.py (523 stacking/compatibility edges)
and the executable-jurisdiction knowledge (program_spend_rules /
program_rate_rules / jurisdiction_comparison) were populated in
different phases and, for two programs, under variant slugs for the
SAME real-world program:

  - "mt_mfc_cash_rebate"  -> "mt_mfc_rebate"
      Both name the Malta Film Commission cash rebate (the single MFC
      production rebate program; jurisdiction_comparison.MALTA's
      program_name is "Malta Film Commission Cash Rebate"). The graph
      catalog used the long form; the executable knowledge the short
      form. One program, two spellings.
  - "gr_ekome_rebate"     -> "gr_cash_rebate"
      Both name the Greek cash rebate for international productions,
      administered via EKOME (jurisdiction_comparison.GREECE:
      "Greece Cash Rebate for International Productions"). Same
      program, agency-name variant vs. generic variant.

This module is the SINGLE place that mapping lives. It never invents an
equivalence: an alias is added only when both slugs demonstrably name
the same statutory program (see the notes above). Anything not in the
map canonicalizes to itself.
"""
from __future__ import annotations

# variant slug -> canonical (executable-knowledge) slug
PROGRAM_SLUG_ALIASES: dict[str, str] = {
    "mt_mfc_cash_rebate": "mt_mfc_rebate",
    "gr_ekome_rebate": "gr_cash_rebate",
}


def canonical_slug(slug: str) -> str:
    """The canonical spelling of a program slug (itself if unaliased)."""
    return PROGRAM_SLUG_ALIASES.get(slug, slug)


def slugs_match(a: str, b: str) -> bool:
    """True when two slugs name the same program after canonicalization."""
    return canonical_slug(a) == canonical_slug(b)
