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
    # ── Global Data Application ────────────────────────────────────────────
    # The completed canonical corpus (GLOBAL_REMEDIATION_EXECUTABLE_DATA.json)
    # identifies programs by its OWN canonical_id, which for most records is a
    # different spelling of an existing runtime slug. Each alias below was
    # adjudicated individually against the canonical record's own
    # `canonical_program_name` + jurisdiction, under this module's standing
    # rule: an alias is added ONLY when both slugs demonstrably name the same
    # statutory program. Three canonical records that could NOT be bound this
    # way (BC FIBC, German GMPF, India NFDC) are deliberately absent and are
    # recorded as CANONICAL_DATA_HANDOFF_DEFECT in
    # authority_coverage_registry.py rather than bound to a different program.
    #
    # "Thailand BOI Film Production Incentive" — BOI in both spellings.
    "th_film_incentive": "th_boi_incentive",
    # "Fiji Audio Visual Commission Production Incentive" — the single FAVC
    # production incentive.
    "fj_film_incentive": "fj_film_rebate",
    # "FINAS Malaysia Film Rebate" — FINAS in both spellings.
    "my_film_incentive": "my_finas_rebate",
    # "Georgian National Film Centre Production Incentive" (GE, the country —
    # NOT US-GA, whose separate record is georgia_eiia).
    "ge_film_incentive": "ge_film_rebate",
    # "Refundable Tax Credit for Film Production Services" is the English name
    # of Quebec's Production Services Tax Credit.
    "proposed_canada_quebec_refundable_tax_credit_for_film_production_services":
        "ca_qc_pstc",
    # Co-Pro Conditional Pricing Data Reconnection — "nz_spgi" is
    # treaty_engine.py's own abbreviation (New Zealand Screen Production
    # Grant International) for the SAME program already canonicalized
    # under "nz_spg_international" (program_rate_rules_worldwide.py,
    # VERIFIED confidence tier, real cited 20%/25% rate; program_name
    # "New Zealand Screen Production Rebate (International)" — the
    # official government renaming, with the internal slug kept for
    # continuity per that entry's own comment). One program, two
    # spellings, same as every other entry in this table.
    "nz_spgi": "nz_spg_international",
}


def canonical_slug(slug: str) -> str:
    """The canonical spelling of a program slug (itself if unaliased)."""
    return PROGRAM_SLUG_ALIASES.get(slug, slug)


def slugs_match(a: str, b: str) -> bool:
    """True when two slugs name the same program after canonicalization."""
    return canonical_slug(a) == canonical_slug(b)
