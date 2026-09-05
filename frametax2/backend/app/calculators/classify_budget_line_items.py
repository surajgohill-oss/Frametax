"""
classify_budget_line_items.py

Deterministic classification of budget line items into:
- ATL / BTL / POST / OTHER
- SpendCategory (btl_crew_labor, atl_director, post_production, etc.)
- is_fixed (ATL fixed fee vs. BTL variable cost)
- is_labor / is_resident_labor
- compensation_type (cash / deferred / equity / in_kind)

Rules are keyword-based with explicit priority ordering.
No LLM calls here — LLM extracts raw data; this module classifies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import NamedTuple

from app.models.enums import ATLBTLCategory, CompensationType, SpendCategory


ENGINE_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Classification rules (ordered — first match wins)
# ---------------------------------------------------------------------------

@dataclass
class ClassificationRule:
    pattern: str  # regex applied to description.lower()
    atl_btl: ATLBTLCategory
    spend_category: SpendCategory
    is_fixed: bool
    is_labor: bool
    compensation_type: CompensationType = CompensationType.CASH


_RULES: list[ClassificationRule] = [
    # --- Obligations that NAME a guild but are not that guild's fee ---
    # A residuals reserve is a funded guild obligation, NOT contingency and
    # NOT the guild's above-the-line fee. Real top sheets write it as "SAG
    # residuals accrual" / "WGA residuals", so it must be matched BEFORE the
    # ATL guild-name rules below, which would otherwise claim it as cast,
    # writer or director compensation.
    ClassificationRule(r"residual",
                       ATLBTLCategory.OTHER, SpendCategory.RESIDUALS_RESERVE, False, False),

    # --- Deferred / Equity / In-kind compensation (any ATL/BTL role) ---
    # MUST precede the Above-the-Line role rules below: a "Director
    # deferred fee" line names both a role AND a non-cash compensation
    # modifier, and the modifier must win the match so compensation_type
    # is captured correctly. This ordering pre-dates the BPI-006 fix
    # below and is now load-bearing for it: the widened \bdirectors?\b /
    # \bproducers?\b patterns would otherwise intercept "Director deferred
    # fee" / "Producer equity participation" before this block ever ran.
    ClassificationRule(r"deferred|deferral|deferment",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True,
                       CompensationType.DEFERRED),
    ClassificationRule(r"equity participation|net profit point|backend",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True,
                       CompensationType.EQUITY),
    ClassificationRule(r"in[- ]kind|reinvestment",
                       ATLBTLCategory.BTL, SpendCategory.IN_KIND, False, False,
                       CompensationType.IN_KIND),

    # --- Above-the-Line (fixed fees) ---
    # A real top sheet names ATL DEPARTMENTS ("SCRIPT", "PRODUCING",
    # "DIRECTING", "CAST"), not fee-style labels ("director fee"). The
    # fee-style spellings are kept; the department spellings are added, so
    # source account semantics classify without a per-production rule.
    #
    # Canonical Budget Parser Remediation (Codex BPI-006): the prior
    # `director( fee|...)?$` / `producer( fee)?$` patterns anchored on
    # end-of-STRING ($). classify_line_item's search_text is built as
    # description + " " + department, and every line the real film-budget
    # parser produces carries a real, non-empty department ("Above The
    # Line", "Production", ...) — so that trailing text always followed
    # "director"/"producer" and the `$` anchor could never match a real
    # parsed line (confirmed: Bad Hombres "1200 PRODUCERS UNIT", "1300
    # DIRECTOR"; F#K "1200 PRODUCERS", "1300 DIRECTOR" — all fell through
    # to MISCELLANEOUS). Fixed with \b word-boundary matching instead of
    # $ end-anchoring — matches the bare department-style word (singular
    # or plural: "DIRECTOR"/"DIRECTION", "PRODUCER"/"PRODUCERS"/"PRODUCERS
    # UNIT") wherever it appears, not only at the very end of the search
    # text. "DIRECTION" is a real top-sheet department-name variant
    # (confirmed on Bad Hombres/F#K's own real budgets) distinct from,
    # but semantically identical to, "DIRECTING".
    # Excludes several real, common roles/departments that also contain
    # the substring "director"/"direction" and must NEVER be claimed as
    # the film's own ATL director fee: "Director of Photography" (DP —
    # camera department, BTL crew labor), "Assistant Director" (1st/2nd
    # AD — BTL crew labor), and "Art Direction" (production design/art
    # department — BTL, a real regression this exclusion locks out; see
    # test_classify_budget.py's own art-direction regression test). All
    # three are matched and correctly classified by the separate
    # BTL_CREW_LABOR rule below instead.
    ClassificationRule(
        r"(?<!assistant )(?<!associate )\bdirectors?\b(?! of photography)"
        r"|director'?s fee|directorial fee|dga fee|directing"
        r"|(?<!art )(?<!set )\bdirection\b",
        ATLBTLCategory.ATL, SpendCategory.ATL_DIRECTOR, True, True),
    ClassificationRule(r"writer|screenplay|script fee|wga|(^|\s)script(\s|$)|story",
                       ATLBTLCategory.ATL, SpendCategory.ATL_WRITER, True, True),
    ClassificationRule(r"\bproducers?\b|executive producer|ep fee|producing",
                       ATLBTLCategory.ATL, SpendCategory.ATL_PRODUCER, True, True),
    ClassificationRule(r"lead cast|star( fee)?|cast( fee)?$|actor fee|talent fee|sag|(^|\s)cast(\s|$)",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True),
    ClassificationRule(r"rights|option|underlying|book right|life rights|remake",
                       ATLBTLCategory.ATL, SpendCategory.ATL_RIGHTS, True, False),

    # --- Post-production ---
    ClassificationRule(r"vfx|visual effects|cgi|animation",
                       ATLBTLCategory.POST, SpendCategory.VFX, False, False),
    ClassificationRule(r"music( score)?|composer|score|soundtrack",
                       ATLBTLCategory.POST, SpendCategory.MUSIC, False, False),
    # Canonical Budget Parser Remediation (Codex BPI-003): "PRODUCTION
    # SOUND" (recording/mic'ing on set — physically tied to the shoot,
    # BTL production spend) is matched BEFORE the generic post-sound rule
    # below, which is reserved for post-section mixing/design/ADR/foley
    # work. A bare "sound" line with no production/post qualifier is
    # further disambiguated generically by source department context in
    # classify_line_item() itself (see is_production_department below) —
    # never a keyword-only guess.
    #
    # (?<!post[ -])production sound — a real, confirmed false-positive:
    # "POST PRODUCTION SOUND" (F#K, Bad Hombres) and "POST-PRODUCTION
    # SOUND" (Lips Like Sugar, hyphenated — hence the [ -] class covering
    # both real spellings) contain the literal substring "production
    # sound" too, and MUST classify as ordinary post-section SOUND (falls
    # through to the generic sound rule below), never PRODUCTION_SOUND,
    # regardless of which numeric department bucket its own account code
    # happens to land in — the account's own explicit "POST" qualifier is
    # stronger, more specific evidence than a coarse numeric-range
    # inference (see budget_parser._dept_for_acct's own documented
    # fragility for exactly this contradiction).
    ClassificationRule(
        r"(?<!post[ -])production sound|sound (department|crew|equipment|recordist|recording)",
        ATLBTLCategory.BTL, SpendCategory.PRODUCTION_SOUND, False, False),
    ClassificationRule(r"sound( mix| design| edit|ing)?|adr|dubbing|foley",
                       ATLBTLCategory.POST, SpendCategory.SOUND, False, False),
    # "editorial", "digital intermediate", "graphics", "titles", "stock
    # footage" added (Canonical Budget Parser Remediation): real
    # regressions surfaced by removing department from search_text
    # (Codex BPI-007's own root fix) — "5000 EDITORIAL" (Little Utopia,
    # F#K), "5600 DIGITAL INTERMEDIATE" (F#K), and "5400 GRAPHICS /
    # TITLES / STOCK FOOTAGE" (Little Utopia) had only ever classified
    # post_production because their OWN department text ("Post
    # Production") leaked into keyword matching and accidentally matched
    # "post prod", not because any keyword rule recognized their real
    # content. Confirmed against the line-reconciliation audit: every one
    # of these real accounts across the four locked-corpus budgets is
    # NO_CONFIRMED_DEFECT as post_production — this restores that correct
    # classification generically, from each description's own real
    # content, per Section 13's explicit requirement to preserve
    # editorial/finishing-type distinctions as real post categories.
    ClassificationRule(
        r"post[ -]prod|editing|editorial|color|grade|deliverables|dcp|mastering"
        r"|digital intermediate|graphics|\btitles\b|stock footage",
        ATLBTLCategory.POST, SpendCategory.POST_PRODUCTION, False, False),
    # Canonical Budget Parser Remediation (Codex BPI-008): real,
    # content-driven post-flavored accounts that a numeric Movie Magic
    # account-code range alone cannot distinguish from ordinary Production
    # spend (film/lab/dailies processing, main/end title design) — matched
    # on their own real, reusable vocabulary, never a project-specific
    # description. This does not change the source account's numeric
    # department bucket (still Production-range by convention); it gives
    # the line its own real spend_category instead of defaulting to
    # MISCELLANEOUS.
    ClassificationRule(r"film\s*/?\s*lab|dailies|negative process",
                       ATLBTLCategory.POST, SpendCategory.POST_PRODUCTION, False, False),
    ClassificationRule(r"main and end titles|main title|end title|title design",
                       ATLBTLCategory.POST, SpendCategory.POST_PRODUCTION, False, False),

    # --- BTL Non-labor ---
    # Vessel/marine must precede generic equipment so "marine equipment" routes correctly
    ClassificationRule(r"vessel|yacht|charter boat|boat (hire|charter|rental)|marine (equip|gear|support|unit)|dive boat|underwater camera|speedboat|speed boat",
                       ATLBTLCategory.BTL, SpendCategory.VESSEL_MARINE, False, False),
    ClassificationRule(r"equipment( rental)?|camera rental|lighting rental|grip",
                       ATLBTLCategory.BTL, SpendCategory.BTL_EQUIPMENT_RENTAL, False, False),
    ClassificationRule(r"stage|studio rental|backlot|sound stage",
                       ATLBTLCategory.BTL, SpendCategory.BTL_STAGE_FACILITY, False, False),
    ClassificationRule(r"location fee|location permit|location rental",
                       ATLBTLCategory.BTL, SpendCategory.BTL_LOCATION_FEES, False, False),
    ClassificationRule(r"set( dressing)?|construction|art department|props",
                       ATLBTLCategory.BTL, SpendCategory.BTL_SET_CONSTRUCTION, False, False),
    ClassificationRule(r"transport|truck|vehicle rental|shuttle|van",
                       ATLBTLCategory.BTL, SpendCategory.BTL_TRANSPORTATION, False, False),
    ClassificationRule(r"cater|meals|craft service|catering",
                       ATLBTLCategory.BTL, SpendCategory.BTL_CATERING, False, False),

    # --- BTL Labor ---
    ClassificationRule(r"resident.*labor|resident.*crew|local.*hire|local.*labor",
                       ATLBTLCategory.BTL, SpendCategory.BTL_RESIDENT_LABOR, False, True),
    ClassificationRule(r"nonresident.*labor|non.?resident.*labor|out.?of.?state.*labor",
                       ATLBTLCategory.BTL, SpendCategory.BTL_NONRESIDENT_LABOR, False, True),
    ClassificationRule(r"crew|dp|cinematographer|gaffer|key grip|production design|costum|makeup|hair",
                       ATLBTLCategory.BTL, SpendCategory.BTL_CREW_LABOR, False, True),
    ClassificationRule(r"payroll|fringe|pension|health|iatse|teamster|guild",
                       ATLBTLCategory.BTL, SpendCategory.PAYROLL_FRINGES, False, True),

    # --- Travel / Lodging ---
    ClassificationRule(r"travel|airfare|flight|airfare",
                       ATLBTLCategory.BTL, SpendCategory.TRAVEL, False, False),
    ClassificationRule(r"hotel|lodging|accommodation|per diem",
                       ATLBTLCategory.BTL, SpendCategory.LODGING, False, False),

    # --- Finance / Insurance / Bond (excluded from most incentive programs) ---
    # Real film budgets name these as departments, not as "finance cost":
    # "FINANCING FEES", "BRIDGE", "BANKING FEE". The stem "financ" covers
    # finance/financing/financial; bridge and banking are named explicitly.
    # These are production FINANCING charges, never miscellaneous spend.
    # "\blend(er|ing)\b" added (Consolidated UI/ingestion/permission
    # closeout, 2026-09-03, Batch 2) -- a PROVEN gap, not a guess:
    # "LENDER FEE" is a real, plainly-labeled finance-cost synonym the
    # prior pattern did not match (confirmed: re.search against "financ|
    # interest|loan fee|bank fee|banking|bridge" returns no match for
    # "LENDER FEE"). F#K Valentine's Day's own real line ("7901 FINANCE
    # FEE : 12.5%") already matched via "financ" -- this was never an
    # F#K-specific classification failure; see BudgetRail.jsx's
    # SourceBudgetFinanceLine for the real (separate) producer-facing
    # wiring defect that made it LOOK like one.
    # WORD-BOUNDED, not a bare "lend" substring: an unbounded "lend(er|
    # ing)" would also match "Color Blending (post)" / "Blending suite
    # rental" -- "blending" contains the literal substring "lending".
    # Proven and tested (see test_classify_finance_costs.py); \b anchors
    # prevent this exact false positive while still matching LENDER/
    # LENDING/LENDER'S/etc.
    ClassificationRule(r"financ|interest|loan fee|\blend(er|ing)\b|bank fee|banking|bridge",
                       ATLBTLCategory.OTHER, SpendCategory.FINANCE_COSTS, False, False),
    ClassificationRule(r"insurance|e&o|errors.and.omissions",
                       ATLBTLCategory.OTHER, SpendCategory.INSURANCE, False, False),
    # Canonical Budget Parser Remediation (Codex BPI-004): a bare "BOND"
    # account (e.g. F#K's real "7905 BOND : 2%") did not match any prior
    # alternative — none of them covered the bare, unqualified word a real
    # top sheet commonly uses for its completion-bond line. \bbond\b
    # added, word-bounded so it can never match an unrelated word that
    # happens to contain "bond" as a substring.
    ClassificationRule(r"completion( guarantee| bond)|bond premium|bond fee|completion fee|\bbond\b",
                       ATLBTLCategory.OTHER, SpendCategory.COMPLETION_BOND, False, False),
    # Canonical Budget Parser Remediation (Codex BPI-005): legal/
    # accounting spend (e.g. Bad Hombres "LEGAL AND ACCOUNTING", Lips Like
    # Sugar "LEGAL COSTS") was previously unclassifiable — no
    # SpendCategory existed for the classifier to emit even though
    # several downstream modules already reference the "legal_accounting"
    # string (see SpendCategory.LEGAL_ACCOUNTING's own docstring). Finer
    # LEGAL vs ACCOUNTING vs FINANCE LEGAL vs PAYROLL/BUSINESS AFFAIRS
    # distinctions where the source genuinely supports them remain
    # available on each line's own preserved description text; no
    # downstream consumer currently reads a finer-grained category, so
    # introducing one here would be speculative, not a proven gap.
    ClassificationRule(r"legal|attorney|counsel|accounting",
                       ATLBTLCategory.OTHER, SpendCategory.LEGAL_ACCOUNTING, False, False),
    # Line-reconciliation audit (authoritative defect inventory): a
    # material administrative/publicity/general-office account (Little
    # Utopia "ADMINISTRATIVE EXPENSES"/"PUBLICITY", F#K "ADMINISTRATIVE
    # EXPENSES", Lips Like Sugar "GENERAL EXPENSE") previously defaulted
    # to MISCELLANEOUS and routed as ordinary principal-photography spend.
    # Distinct from LEGAL_ACCOUNTING (a professional-fee category, not an
    # office-overhead one) and from true MISCELLANEOUS (the "nothing else
    # matched" bucket) — reusable, generic vocabulary, not tied to any one
    # production's own account name.
    ClassificationRule(r"administrative expense|publicity|general expense",
                       ATLBTLCategory.OTHER, SpendCategory.GENERAL_ADMINISTRATION, False, False),
    # Little Utopia Economic Reconciliation: "conting?ency" tolerates the
    # real, common misspelling "Contigency" (missing the 'n') found in
    # Little Utopia's own real source budget PDF (account 8300) — a real,
    # generic gap independently proven by two facts: (1) the SAME account
    # is hand-classified "contingency" in app/data/little_utopia_real_
    # budget.py's own account-code-keyed map, confirming the doctrine
    # intends this exact line to be a contingency reserve; (2) the
    # category's own display name uses the correct spelling, so a typo in
    # ANY production's real budget PDF would silently defeat this rule
    # the same way. Not new doctrine — this is the SAME existing rule,
    # made robust to a real spelling variant, exactly like "conting?ency"
    # already tolerates both "contingency" and "reserve" as synonyms.
    ClassificationRule(r"contin?gency|reserve",
                       ATLBTLCategory.OTHER, SpendCategory.CONTINGENCY, False, False),
]

# Compile patterns for performance
_COMPILED: list[tuple[re.Pattern, ClassificationRule]] = [
    (re.compile(r.pattern, re.IGNORECASE), r) for r in _RULES
]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class ClassificationResult(NamedTuple):
    atl_btl: ATLBTLCategory
    spend_category: SpendCategory
    is_fixed: bool
    is_labor: bool
    compensation_type: CompensationType
    rule_matched: str | None  # the pattern that triggered this classification


def classify_line_item(description: str, department: str | None = None) -> ClassificationResult:
    """
    Deterministically classify a budget line item by description and optional department.
    Returns a ClassificationResult with the matched rule's pattern for audit trace.
    """
    # Canonical Budget Parser Remediation (Codex BPI-007): search_text
    # used to be description + " " + department, which let a line's
    # DEPARTMENT text accidentally trigger an unrelated keyword rule for
    # any generically-named line in that department section — confirmed
    # live on Lips Like Sugar's real "5900 Total Fringes" (a genuine
    # payroll_fringes line), whose department string "Post Production"
    # itself contains "post prod", matching the post_production rule
    # BEFORE the fringe rule ever got a chance, purely from department
    # leakage rather than the line's own real content. Keyword pattern
    # matching now runs on the line's own DESCRIPTION only; department
    # remains a real signal, but only through the explicit,
    # narrowly-scoped override checks below (department_atl,
    # is_production_department/is_post_department) — never as a hidden
    # extra source of arbitrary keyword matches.
    search_text = description.lower().strip()

    # SOURCE ACCOUNT SEMANTICS DECIDE ATL/BTL.
    # The budget parser already derives `department` from the source
    # document's own account-code convention (1000s = Above The Line, and so
    # on -- see budget_parser._dept_for_acct). A description-pattern table
    # cannot know that convention, so a real ATL department whose name is not
    # fee-shaped ("SCRIPT", "PRODUCING", "DIRECTING", "CAST", "ATL TRAVEL &
    # LIVING", "Total Fringes") fell through to the default BTL branch and the
    # whole above-the-line block was reported below the line. The source
    # document already stated the answer; honour it rather than re-deriving
    # it from prose.
    department_text = (department or "").lower()
    department_atl = "above the line" in department_text or department_text.strip() == "atl"
    # Canonical Budget Parser Remediation (Codex BPI-003): the SAME kind
    # of explicit, narrowly-scoped department override as department_atl
    # above, applied to disambiguate a bare "sound" account. The parser's
    # own account-code convention (budget_parser._dept_for_acct) already
    # states whether an account is source Production/BTL spend or Post
    # Production spend; a generic "sound" keyword cannot know that, so it
    # is honoured explicitly here rather than guessed from prose.
    is_post_department = "post production" in department_text
    is_production_department = (
        not is_post_department and "production" in department_text
    )

    for pattern, rule in _COMPILED:
        if pattern.search(search_text):
            spend_category = rule.spend_category
            atl_btl = rule.atl_btl
            if (
                spend_category is SpendCategory.SOUND
                and is_production_department
                # The line's OWN description explicitly saying "post" is
                # stronger, more specific evidence than the numeric
                # department bucket — confirmed live on Bad Hombres'
                # "4700 POST PRODUCTION SOUND", whose account code
                # happens to fall in the numeric Production range despite
                # its own name stating it is post-section spend (see
                # budget_parser._dept_for_acct's own documented
                # fragility). Only a TRULY bare/unqualified "sound" line
                # is reclassified here.
                and "post" not in search_text
            ):
                # A bare "sound" line (no "production"/"post"/"mix"/
                # "design"/etc. qualifier in its own description) whose
                # SOURCE account is filed under the Production department
                # is source Production/BTL spend, never post-production,
                # regardless of which keyword the description happened to
                # match.
                spend_category = SpendCategory.PRODUCTION_SOUND
                atl_btl = ATLBTLCategory.BTL
            return ClassificationResult(
                atl_btl=(
                    ATLBTLCategory.ATL
                    if department_atl and atl_btl is ATLBTLCategory.BTL
                    else atl_btl
                ),
                spend_category=spend_category,
                is_fixed=rule.is_fixed,
                is_labor=rule.is_labor,
                compensation_type=rule.compensation_type,
                rule_matched=rule.pattern,
            )

    # Default: unclassified BTL labor -- unless the source account convention
    # already placed this line above the line.
    return ClassificationResult(
        atl_btl=ATLBTLCategory.ATL if department_atl else ATLBTLCategory.BTL,
        spend_category=SpendCategory.MISCELLANEOUS,
        is_fixed=False,
        is_labor=False,
        compensation_type=CompensationType.CASH,
        rule_matched=None,
    )


def classify_atl_btl_split(
    line_items: list[dict],
) -> dict:
    """
    Classify a list of line item dicts and return summary totals.
    Each dict must have at least: description, amount_usd.
    Optional: department.

    Returns a trace-ready dict with classified items and subtotals.
    """
    classified = []
    totals = {
        "atl_total_usd": 0.0,
        "btl_total_usd": 0.0,
        "post_total_usd": 0.0,
        "other_total_usd": 0.0,
        "fixed_atl_usd": 0.0,
        "variable_btl_usd": 0.0,
        "labor_usd": 0.0,
        "non_labor_usd": 0.0,
    }

    for item in line_items:
        result = classify_line_item(
            description=item.get("description", ""),
            department=item.get("department"),
        )
        amount = float(item.get("amount_usd") or 0.0)

        classified.append({
            **item,
            "atl_btl": result.atl_btl.value,
            "spend_category": result.spend_category.value,
            "is_fixed": result.is_fixed,
            "is_labor": result.is_labor,
            "compensation_type": result.compensation_type.value,
            "classification_rule": result.rule_matched,
        })

        if result.atl_btl == ATLBTLCategory.ATL:
            totals["atl_total_usd"] += amount
            if result.is_fixed:
                totals["fixed_atl_usd"] += amount
        elif result.atl_btl == ATLBTLCategory.BTL:
            totals["btl_total_usd"] += amount
            totals["variable_btl_usd"] += amount
        elif result.atl_btl == ATLBTLCategory.POST:
            totals["post_total_usd"] += amount
        else:
            totals["other_total_usd"] += amount

        if result.is_labor:
            totals["labor_usd"] += amount
        else:
            totals["non_labor_usd"] += amount

    return {
        "engine_version": ENGINE_VERSION,
        "classified_items": classified,
        "totals": totals,
    }
