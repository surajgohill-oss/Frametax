"""
cultural_point_tables.py

Worldwide Qualification Consumption Closeout (2026-08-19). The ONE new,
minimal, additive registry needed to connect the real cultural-test
point-table doctrine already researched into `program_requirements.py`
(Queue B, `at_fisa_plus`/`cz_film_incentive`/`fr_trip`/`no_film_incentive`/
`my_finas_rebate`/`pl_pisf_cash_rebate`/`pt_scri_pt_cash_rebate`/plus the
prior pass's `gr_cash_rebate`/`hr_cash_rebate`/`hu_hipa_rebate`/
`it_tax_credit_foreign`/`lt_film_centre_cash_rebate`/`mt_mfc_rebate`) into
the served qualification path.

Deliberately NOT a second copy of `cultural_qualification_model.py`'s
`NationalityRequirement` shape: a cultural POINT TABLE is a structurally
different rule type (weighted categories summing to a threshold, several
of which are not personnel-role facts at all -- setting, language,
production-location facts) and forcing it into the role-gate shape would
either lose real information or fabricate role rows that were never
researched. `canonical_role_qualification_bridge.py` is the ONE place
that decides, per program_slug, which registry (this one, or
`cultural_qualification_model.py`'s role registry, or the discretionary/
non-evaluated single-criterion cases) supplies the qualification data --
never both, never neither for a program with real doctrine on file.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CULTURAL_POINT_TABLES_VERSION = "1.1.0"
# 1.1.0 -- Consolidated Backend Correction (CBA-003, Codex audit
# 4db2cea): adds explicit table-level COMPLETENESS classification (a
# partially-itemised table's modeled maximum is never confused with the
# real statutory maximum, and an aggregate/approximate table is now
# quarantined from deterministic admission rather than silently treated
# as equivalent to a fully-itemised one) and per-criterion
# jurisdiction_code + expected_values for SCRIPT_FACT criteria, closing
# the false-QUALIFIES defect Codex demonstrated (fr_trip returning
# QUALIFIES from a Tokyo/US/English fact set because any() matched on
# element_type alone, with no semantic comparison to France at all).

# ── Table-level completeness classification (Part 3 / CBA-003) ─────────
#: The itemised criteria are a verified, complete representation of the
#: real official point table (every category and its exact point value
#: is on file). A partial-modeled maximum can never occur here by
#: definition -- modeled_max == total_points.
TABLE_COMPLETE = "COMPLETE"
#: The itemised criteria are a genuine SUBSET of the real official table
#: (modeled_max < total_points), but the exact size of the unmodeled
#: remainder IS known (total_points itself is a confirmed, cited
#: statutory/regulatory figure) -- safe to credit toward a CEILING
#: (never toward CONFIRMED points), per the unmodeled_headroom mechanism
#: already in canonical_role_qualification_bridge.py.
TABLE_PARTIAL_WITH_KNOWN_HEADROOM = "PARTIAL_WITH_KNOWN_HEADROOM"
#: Modeled criteria are a subset AND the real statutory maximum itself
#: is not confirmed (total_points is an estimate, not a cited figure) --
#: the size of the unmodeled remainder is genuinely unknown, not merely
#: unitemised.
TABLE_PARTIAL_WITH_UNKNOWN_HEADROOM = "PARTIAL_WITH_UNKNOWN_HEADROOM"
#: The table is built from one or more coarse, aggregate, or
#: approximated criteria (e.g. "the whole 34-point Croatian test" as a
#: single all-or-nothing row) rather than the real itemised official
#: categories -- genuinely different from a partial-but-itemised table.
#: MUST NOT be treated as safe deterministic admission evidence: these
#: tables can only ever resolve to a non-QUALIFIES state (see the
#: quarantine logic in evaluate_point_table_qualification) until the
#: real official item-level breakdown is independently confirmed.
TABLE_AUTHORITY_INCOMPLETE = "AUTHORITY_INCOMPLETE"

# ── Fact-type vocabulary (Task 4 distinction, reused not reinvented) ────
FACT_USER = "USER_FACT"           # personnel nationality/residency, ownership/control, production/work location
FACT_SCRIPT = "SCRIPT_FACT"       # story setting, subject matter, language/dialogue, source material
FACT_PRODUCTION = "PRODUCTION_FACT"  # shoot days/location, post-production/VFX location, spend split -- a
                                      # PROJECT-level fact (production plan), grouped with FACT_USER for
                                      # blocking-state purposes since both come from project data, not the script

# ── Category vocabulary (Task 3) ─────────────────────────────────────────
CATEGORY_ROLE = "ROLE"                       # a named creative/crew role's nationality/residency
CATEGORY_STORY_SETTING = "STORY_SETTING"
CATEGORY_LANGUAGE = "LANGUAGE"
CATEGORY_SUBJECT_MATTER = "SUBJECT_MATTER"
CATEGORY_PRODUCTION_ACTIVITY = "PRODUCTION_ACTIVITY"
CATEGORY_POST_VFX_ANIMATION = "POST_VFX_ANIMATION"
CATEGORY_OWNERSHIP_CONTROL = "OWNERSHIP_CONTROL"
CATEGORY_OTHER = "OTHER"

# ── Criterion "hardness" (Task 3 -- never collapse point-bearing into mandatory) ──
CRITERION_MANDATORY = "MANDATORY"       # must be satisfied or the program hard-fails regardless of points
CRITERION_POINT_BEARING = "POINT_BEARING"  # contributes points toward a threshold, never a standalone gate
CRITERION_OPTIONAL = "OPTIONAL"


@dataclass(frozen=True)
class CulturalPointCriterion:
    key: str
    category: str            # CATEGORY_*
    fact_type: str            # FACT_*
    hardness: str = CRITERION_POINT_BEARING  # CRITERION_*
    max_points: float = 0.0
    role: str | None = None   # for CATEGORY_ROLE rows: director|writer|producer|lead_cast|
                               # supporting_cast|editor|composer|dop|vfx_supervisor|post_supervisor|entity
                               # (cultural_qualification_model.py's own role vocabulary, reused not
                               # reinvented) OR a free-text descriptive role name when the researched
                               # table names a role outside that vocabulary (e.g. "costume_designer") --
                               # role_known_codes_from_project() will correctly have no data for those,
                               # which resolves honestly to a curable/available lever, never fabricated.
    jurisdiction_code: str | None = None  # None = "domestic" (this program's own jurisdiction/EEA per notes)
    description: str = ""
    #: CBA-003 fix. For FACT_SCRIPT criteria ONLY: the exact, real
    #: strings a Script Analyzer fact's value must match (case-
    #: insensitive substring) for THIS specific criterion to be
    #: satisfied -- e.g. ("france", "french", "fr") for a France
    #: setting/language criterion. Empty tuple means "not yet given an
    #: explicit match list" -- see _script_fact_matches() below, which
    #: falls back to the table's own jurisdiction's real name/language
    #: when this is empty, rather than ever matching on element_type
    #: presence alone (the exact defect Codex demonstrated: a Tokyo/US/
    #: English fact set falsely satisfying France's criteria).
    expected_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class CulturalPointTable:
    program_slug: str
    total_points: float
    threshold: float
    #: Part 3 / CBA-003 -- one of TABLE_COMPLETE/TABLE_PARTIAL_WITH_
    #: KNOWN_HEADROOM/TABLE_PARTIAL_WITH_UNKNOWN_HEADROOM/TABLE_
    #: AUTHORITY_INCOMPLETE. Never inferred silently from total_points
    #: vs. modeled criteria sum -- set explicitly per table, because
    #: "aggregate criteria happen to sum to total_points" (e.g. mt_mfc_
    #: rebate) is NOT the same real-world state as "genuinely itemised
    #: and complete" (e.g. no_film_incentive), even though both would
    #: look identical to a naive modeled_max == total_points check.
    completeness: str = TABLE_AUTHORITY_INCOMPLETE
    #: Compound minimums beyond the single aggregate threshold (e.g. Czech
    #: Republic's "min 23/46 overall AND min 4 from the Cultural block").
    #: Each entry is (category_label, min_points_from_that_category,
    #: tuple of criterion keys belonging to that category).
    sub_thresholds: tuple[tuple[str, float, tuple[str, ...]], ...] = ()
    criteria: tuple[CulturalPointCriterion, ...] = field(default_factory=tuple)
    source_note: str = ""


def _c(key, category, fact_type, max_points, role=None, jurisdiction_code=None,
       hardness=CRITERION_POINT_BEARING, description="", expected_values=()) -> CulturalPointCriterion:
    return CulturalPointCriterion(
        key=key, category=category, fact_type=fact_type, hardness=hardness,
        max_points=max_points, role=role, jurisdiction_code=jurisdiction_code,
        description=description, expected_values=expected_values,
    )


#: CBA-003 fix -- real country name(s)/adjective/language(s) for the
#: jurisdictions this module's tables cover, used ONLY to semantically
#: match a Script Analyzer fact's free-text VALUE against a criterion
#: (never to fabricate legal doctrine; this is plain, undisputed
#: geography/language fact, the same kind of fact an ISO2->name lookup
#: table would carry). Bounded to the ~15 jurisdictions with real
#: CULTURAL_POINT_TABLES entries, not a general-purpose world gazetteer.
JURISDICTION_NAME_AND_LANGUAGE: dict[str, tuple[str, ...]] = {
    "AT": ("austria", "austrian", "german", "vienna", "salzburg", "graz"),
    "CZ": ("czech", "czechia", "czech republic", "prague", "brno"),
    "FR": ("france", "french", "paris", "lyon", "marseille", "nice", "cannes"),
    "NO": ("norway", "norwegian", "oslo", "bergen", "trondheim"),
    "MY": ("malaysia", "malaysian", "malay", "kuala lumpur", "penang", "sabah"),
    "PL": ("poland", "polish", "warsaw", "krakow", "gdansk", "wroclaw"),
    "PT": ("portugal", "portuguese", "lisbon", "porto", "madeira", "azores"),
    "GR": ("greece", "greek", "athens", "thessaloniki", "crete", "santorini"),
    "HR": ("croatia", "croatian", "zagreb", "dubrovnik", "split"),
    "HU": ("hungary", "hungarian", "budapest"),
    "IT": ("italy", "italian", "rome", "milan", "venice", "turin", "naples"),
    "LT": ("lithuania", "lithuanian", "vilnius", "kaunas"),
    "MT": ("malta", "maltese", "valletta"),
    "BE": ("belgium", "belgian", "brussels", "flanders", "wallonia", "antwerp"),
    "FI": ("finland", "finnish", "helsinki"),
    "LU": ("luxembourg",),
    "DK": ("denmark", "danish", "copenhagen"),
}


def _script_fact_matches(value: str, jurisdiction_code: str | None, expected_values: tuple[str, ...]) -> bool:
    """CBA-003 fix -- the SEMANTIC comparison the pre-fix code never
    performed. A Script Analyzer fact only satisfies a criterion when its
    free-text value actually names the criterion's own jurisdiction (or
    one of the criterion's own explicit expected_values) -- element_type
    presence ALONE is never sufficient. Demonstrated defect this closes:
    Tokyo/US/English facts could satisfy fr_trip's France-specific
    criteria purely because a 'location'/'language' fact existed at all,
    with no comparison to France whatsoever."""
    v = (value or "").strip().lower()
    if not v:
        return False
    if expected_values:
        return any(ev.lower() in v for ev in expected_values)
    if jurisdiction_code:
        names = JURISDICTION_NAME_AND_LANGUAGE.get(jurisdiction_code.upper(), ())
        return any(name in v for name in names)
    # No expected_values AND no jurisdiction_code on the criterion --
    # genuinely cannot determine a match; fail closed (never silently
    # satisfied by mere presence).
    return False


# ═══════════════════════════════════════════════════════════════════════
# Populated tables -- every criterion below is drawn directly from the
# real, primary-sourced category breakdowns already recorded in each
# program's own EvidenceRecord.notes in program_requirements.py (Queue B,
# Worldwide Program Qualification Completion, 2026-08-19 and the prior
# pass it continues). No new research performed here -- this module only
# STRUCTURES doctrine that was already found, converting free-text
# category descriptions into a queryable, consumable form.
# ═══════════════════════════════════════════════════════════════════════

CULTURAL_POINT_TABLES: dict[str, CulturalPointTable] = {
    "at_fisa_plus": CulturalPointTable(
        program_slug="at_fisa_plus", total_points=80, threshold=40,
        completeness=TABLE_PARTIAL_WITH_KNOWN_HEADROOM,  # 46 official points unitemized (Codex audit 4db2cea)
        criteria=(
            _c("at_content_setting", CATEGORY_STORY_SETTING, FACT_SCRIPT, 4,
               description="Part of scenes set in Austria/EEA/Council of Europe"),
            _c("at_content_objects", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 3,
               description="Austrian/European objects filmed"),
            _c("at_content_locations", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 3,
               description="Austrian/European shooting locations used"),
            _c("at_content_character", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 3,
               description="Main character is/was Austrian/EEA/CoE"),
            _c("at_content_plot_source", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 3,
               description="Plot/underlying material is Austrian or European"),
            _c("at_prof_director", CATEGORY_ROLE, FACT_USER, 2, role="director", description="Austrian/EEA/CoE director"),
            _c("at_prof_writer", CATEGORY_ROLE, FACT_USER, 2, role="writer", description="Austrian/EEA/CoE screenwriter"),
            _c("at_prof_producer", CATEGORY_ROLE, FACT_USER, 2, role="producer", description="Austrian/EEA/CoE producer"),
            _c("at_prof_dop", CATEGORY_ROLE, FACT_USER, 2, role="dop", description="Austrian/EEA/CoE cinematographer"),
            _c("at_prof_editor", CATEGORY_ROLE, FACT_USER, 2, role="editor", description="Austrian/EEA/CoE editor"),
            _c("at_prof_composer", CATEGORY_ROLE, FACT_USER, 2, role="composer", description="Austrian/EEA/CoE composer"),
            _c("at_prod_shooting_days", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 6,
               description="Days of live-action shooting in Austria (tiered 4/5/6)"),
        ),
        sub_thresholds=(
            ("Part A Cultural Content", 4, ("at_content_setting", "at_content_objects", "at_content_locations",
                                             "at_content_character", "at_content_plot_source")),
        ),
        source_note="Official FISA+ Funding Guidelines for Service Productions 2025-2027, Annex 3.",
    ),
    "cz_film_incentive": CulturalPointTable(
        program_slug="cz_film_incentive", total_points=46, threshold=23,
        completeness=TABLE_PARTIAL_WITH_KNOWN_HEADROOM,  # 10 points unitemized (Codex audit 4db2cea)
        criteria=(
            _c("cz_story_events", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Story based on European-culture events"),
            _c("cz_story_personality", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Story based on a European-culture personality"),
            _c("cz_setting", CATEGORY_STORY_SETTING, FACT_SCRIPT, 2, description="Storyline connected with a European setting"),
            _c("cz_genre_dev", CATEGORY_OTHER, FACT_PRODUCTION, 3, description="Film contributes to development of its genre"),
            _c("cz_crew_czech", CATEGORY_ROLE, FACT_USER, 7, role="entity",
               description="Filmmakers are Czech/EEA citizens"),
            _c("cz_language", CATEGORY_LANGUAGE, FACT_SCRIPT, 4, description="Final version in an EEA language"),
            _c("cz_crew_51pct", CATEGORY_ROLE, FACT_USER, 4, role="entity",
               description=">=51% of crew are EEA citizens"),
            _c("cz_shoot_location", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 4, description="Shooting in Czech Republic"),
            _c("cz_service_providers", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 4, description="Czech service providers used"),
            _c("cz_post_production", CATEGORY_POST_VFX_ANIMATION, FACT_PRODUCTION, 4, description="Post-production in Czech Republic"),
        ),
        sub_thresholds=(
            ("Cultural criteria", 4, ("cz_story_events", "cz_story_personality", "cz_setting")),
        ),
        source_note="Official Czech Film Commission 'Production Incentives' PDF.",
    ),
    "fr_trip": CulturalPointTable(
        program_slug="fr_trip", total_points=38, threshold=18,
        completeness=TABLE_PARTIAL_WITH_KNOWN_HEADROOM,  # 1 point unitemized (Codex audit 4db2cea)
        criteria=(
            _c("fr_locations", CATEGORY_STORY_SETTING, FACT_SCRIPT, 7, description="Filming geography / locations"),
            _c("fr_characters", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 4, description="Character nationalities"),
            _c("fr_story_themes", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 5, description="Subject & story thematic elements"),
            _c("fr_language", CATEGORY_LANGUAGE, FACT_SCRIPT, 2, description="French dubbing/subtitles"),
            _c("fr_director_writer", CATEGORY_ROLE, FACT_USER, 2, role="director", description="Director/screenwriter nationality"),
            _c("fr_composer", CATEGORY_ROLE, FACT_USER, 1, role="composer"),
            _c("fr_producer", CATEGORY_ROLE, FACT_USER, 2, role="producer"),
            _c("fr_cast", CATEGORY_ROLE, FACT_USER, 2, role="lead_cast", description="Principal/secondary actors"),
            _c("fr_crew_composition", CATEGORY_ROLE, FACT_USER, 1, role="entity", description="Crew composition"),
            _c("fr_dept_heads", CATEGORY_ROLE, FACT_USER, 3, role="entity", description="Department heads"),
            _c("fr_shoot_days", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 3, description="Shooting days in France"),
            _c("fr_vfx_sfx", CATEGORY_POST_VFX_ANIMATION, FACT_PRODUCTION, 1, description="French VFX/SFX spend"),
            _c("fr_equipment", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 1, description="French equipment rental"),
            _c("fr_lab", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 1, description="French lab work"),
            _c("fr_post_production", CATEGORY_POST_VFX_ANIMATION, FACT_PRODUCTION, 2, description="French post-production"),
        ),
        sub_thresholds=(
            ("Contenu dramatique (Dramatic Content)", 7,
             ("fr_locations", "fr_characters", "fr_story_themes", "fr_language")),
        ),
        source_note="Code du cinema et de l'image animee, Art. D331-42 a D331-46 (Legifrance, official).",
    ),
    "no_film_incentive": CulturalPointTable(
        program_slug="no_film_incentive", total_points=51, threshold=20,
        completeness=TABLE_COMPLETE,  # itemized official table + sub-threshold represented (Codex audit 4db2cea)
        criteria=(
            _c("no_story_events", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Norwegian/European cultural-historical events"),
            _c("no_character", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Character from Norwegian/European culture"),
            _c("no_setting", CATEGORY_STORY_SETTING, FACT_SCRIPT, 2, description="Norwegian/European setting"),
            _c("no_source_material", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Script adapted from literature/art"),
            _c("no_contemporary_themes", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Contemporary cultural/sociological/political themes"),
            _c("no_values", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 2, description="Reflects Norwegian/European values/culture/identity"),
            _c("no_director_writer", CATEGORY_ROLE, FACT_USER, 2, role="director", description="Norwegian/European director/screenwriter/author"),
            _c("no_language", CATEGORY_LANGUAGE, FACT_SCRIPT, 2, description="Norwegian or other European language"),
            _c("no_ambitious_work", CATEGORY_OTHER, FACT_PRODUCTION, 3, description="Cinematically ambitious genre-advancing work"),
            _c("no_competence_dev", CATEGORY_OTHER, FACT_PRODUCTION, 4, description="Develops filmmaker competence"),
            _c("no_key_creatives", CATEGORY_ROLE, FACT_USER, 8, role="entity", description="Key creatives Norwegian/British/EEA (19 positions)"),
            _c("no_crew_51pct", CATEGORY_ROLE, FACT_USER, 4, role="entity", description=">=51% crew Norwegian/British/EEA"),
            _c("no_locations", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 4, description="Norwegian locations/studios"),
            _c("no_suppliers", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 4, description="Norwegian/UK/EEA suppliers"),
            _c("no_post_production", CATEGORY_POST_VFX_ANIMATION, FACT_PRODUCTION, 6, description="Norwegian/UK/EEA post-production"),
            _c("no_sustainability", CATEGORY_OTHER, FACT_PRODUCTION, 2, description="Sustainable/environmentally-friendly filming"),
        ),
        sub_thresholds=(
            ("Part 1 Cultural Test", 4,
             ("no_story_events", "no_character", "no_setting", "no_source_material",
              "no_contemporary_themes", "no_values", "no_director_writer", "no_language")),
        ),
        source_note="Lovdata (official Norwegian legal database), Forskrift om insentivordning, Vedlegg 1.",
    ),
    "my_finas_rebate": CulturalPointTable(
        program_slug="my_finas_rebate", total_points=5, threshold=None,
        completeness=TABLE_COMPLETE,  # complete optional uplift table, not a base pass/fail gate (Codex audit 4db2cea)
        criteria=(
            _c("my_location", CATEGORY_STORY_SETTING, FACT_SCRIPT, 2,
               description="Portrays Malaysia positively / as a destination"),
            _c("my_cultural_values", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 1,
               description="Displays Malaysian culture/lifestyle/customs/traditions"),
            _c("my_local_cast_crew", CATEGORY_ROLE, FACT_USER, 2, role="entity",
               description="Involvement of local cast/crew across 20 named roles"),
        ),
        source_note="Official FINAS FIMI Guidelines (Foreign Production), Appendix C -- OPTIONAL +5% uplift, "
                     "each category scored/capped independently, not a single aggregate pass/fail minimum.",
    ),
    "pl_pisf_cash_rebate": CulturalPointTable(
        program_slug="pl_pisf_cash_rebate", total_points=48, threshold=25,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # 4 12-pt allocations are acknowledged approximations (Codex audit 4db2cea)
        criteria=(
            _c("pl_heritage", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 12,
               description="Use of Polish/European cultural heritage in the film"),
            _c("pl_location", CATEGORY_STORY_SETTING, FACT_SCRIPT, 12,
               description="Location of the audiovisual production in Poland"),
            _c("pl_production_territory", CATEGORY_PRODUCTION_ACTIVITY, FACT_PRODUCTION, 12,
               description="Production of the work carried out in Poland"),
            _c("pl_polish_participation", CATEGORY_ROLE, FACT_USER, 12, role="entity",
               description="Participation of Polish artists/crews/service providers/infrastructure"),
        ),
        source_note="Ustawa z 9 listopada 2018 r. (Dz.U. 2019 poz. 50) Art. 16(4)/17(3)/21(2), + Ministry of "
                     "Culture regulation Zalacznik nr 4 (48pt/25min post-Nov-2024 amendment). Exact per-"
                     "category point split within the 48 is a disclosed residual -- the four categories above "
                     "are evenly apportioned as a documented approximation pending the regulation's own "
                     "Zalacznik nr 4 text, NOT independently confirmed at that granularity.",
    ),
    "pt_scri_pt_cash_rebate": CulturalPointTable(
        program_slug="pt_scri_pt_cash_rebate", total_points=100, threshold=45,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # only 60/40 aggregates represented (Codex audit 4db2cea)
        criteria=(
            _c("pt_cultural_value", CATEGORY_SUBJECT_MATTER, FACT_SCRIPT, 60,
               description="Parte A -- Valor Cultural (identification/nationality of authors, actors, "
                           "subject matter, Portuguese cultural content)"),
            _c("pt_creative_technical_cooperation", CATEGORY_ROLE, FACT_USER, 40, role="entity",
               description="Parte B -- Cooperacao Criativa e Tecnica (producers, technicians, "
                           "professionals hired in Portugal)"),
        ),
        source_note="Portaria n.o 276-B/2026/1, Art. 7 (via Morais Leitao's direct legal analysis). Foreign-"
                     "initiative productions with a local executive producer use a LOWER threshold: 20 total "
                     "/ 8 min from Parte A -- see additional_facts on the program_requirements.py profile. "
                     "The 60/40 Parte A/B split is the confirmed AGGREGATE structure; item-by-item points "
                     "within each part are a disclosed residual.",
    ),
    # ── Prior-pass programs: coarser real data (aggregate points/threshold
    # confirmed from primary sources, but no published category-by-category
    # breakdown was located at the time) -- represented with the honest,
    # minimum-necessary structure: a single OTHER/mixed criterion carrying
    # the full point value, fact_type=USER_FACT (personnel-heavy tests are
    # the norm for these regimes) so the qualification path can still reach
    # a real state rather than RULE_DATA_INCOMPLETE. Never a fabricated
    # category split where none was researched.
    "gr_cash_rebate": CulturalPointTable(
        program_slug="gr_cash_rebate", total_points=50, threshold=20,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # one aggregate built from secondary sources, no criteria (Codex audit 4db2cea)
        criteria=(
            _c("gr_aggregate", CATEGORY_OTHER, FACT_USER, 50, role="entity",
               description="Aggregate Greek/European cultural-content and personnel test "
                           "(category-by-category breakdown not published in sources checked)"),
        ),
        source_note="Saturation.io, fixersingreece.gr, Lexology Law 5105/2024 summary.",
    ),
    "hr_cash_rebate": CulturalPointTable(
        program_slug="hr_cash_rebate", total_points=34, threshold=12,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # category floors/allocations not executable (Codex audit 4db2cea)
        criteria=(
            _c("hr_aggregate", CATEGORY_OTHER, FACT_USER, 34, role="entity",
               description="European cultural content / creative collaboration with Croatian-European "
                           "personnel / use of Croatian production facilities (3-category floor of 4 pts "
                           "each; exact per-role point allocation not confirmed)"),
        ),
        source_note="Invest Croatia; Zagreb Film Office; Cineuropa.",
    ),
    "hu_hipa_rebate": CulturalPointTable(
        program_slug="hu_hipa_rebate", total_points=None, threshold=16,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # unknown statutory maximum, one aggregate (Codex audit 4db2cea)
        criteria=(
            _c("hu_aggregate", CATEGORY_OTHER, FACT_USER, 16, role="entity",
               description="EU-participation scoring (category breakdown not published)"),
        ),
        source_note="National Film Institute Hungary (nfi.hu).",
    ),
    "it_tax_credit_foreign": CulturalPointTable(
        program_slug="it_tax_credit_foreign", total_points=None, threshold=50,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # unknown statutory maximum, one aggregate (Codex audit 4db2cea)
        criteria=(
            _c("it_aggregate", CATEGORY_OTHER, FACT_USER, 50, role="entity",
               description="Requisiti culturali point threshold (category breakdown not published)"),
        ),
        source_note="Direzione Generale Cinema e Audiovisivo (DGCA), Ministry of Culture.",
    ),
    "lt_film_centre_cash_rebate": CulturalPointTable(
        program_slug="lt_film_centre_cash_rebate", total_points=8, threshold=2,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # 8 criteria collapsed into one all-or-nothing aggregate (Codex audit 4db2cea)
        criteria=(
            _c("lt_aggregate", CATEGORY_OTHER, FACT_USER, 8, role="entity",
               description="8 published criteria, at least 2 must be satisfied (category breakdown "
                           "not itemised in sources checked)"),
        ),
        source_note="Lithuanian Film Centre (lkc.lt).",
    ),
    "mt_mfc_rebate": CulturalPointTable(
        program_slug="mt_mfc_rebate", total_points=40, threshold=40,
        completeness=TABLE_AUTHORITY_INCOMPLETE,  # general test collapsed into one all-or-nothing aggregate (Codex audit 4db2cea)
        criteria=(
            _c("mt_aggregate", CATEGORY_OTHER, FACT_USER, 40, role="entity",
               description="General Cultural Test (minimum 40 points in aggregate; a separate, fully "
                           "itemised 'National Work' creative-input table also exists -- 15/21 feature, "
                           "8/16 documentary, 15/23 animation -- for the OPTIONAL 'Difficult Audiovisual "
                           "Work' enhanced-rate status, not the general gate)"),
        ),
        source_note="Official Malta Film Commission Cash Rebate Guidelines PDF.",
    ),
}


#: Programs whose real, confirmed cultural-qualification mechanism is
#: NOT a point table at all -- each genuinely different, each resolved
#: (not a research residual), each needing its own small, honest
#: representation rather than a fabricated point scale.
DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS: dict[str, dict] = {
    "be_tax_shelter": {
        "mechanism": "EUROPEAN_WORK_OR_OFFICIAL_COPRODUCTION_STATUS",
        "fact_type": FACT_USER,
        "description": (
            "Belgium's Tax Shelter gate is recognition as a 'European work' under Article 1(1)(n) of the "
            "EU Audiovisual Media Services Directive (2010/13/EU), OR qualification as an official "
            "co-production, granted by the Federation Wallonie-Bruxelles Centre du Cinema et de "
            "l'Audiovisuel via its own 'agrement' process -- a binary legal-status determination, not a "
            "scored point table. The fact needed is whether the CFWB has approved (or would approve) the "
            "work under this framework."
        ),
    },
    "fi_business_finland_incentive": {
        "mechanism": "NON_EVALUATED_ARTISTIC_WHOLE_DEFINITION",
        "fact_type": None,  # always resolves -- see evaluate below
        "description": (
            "Finland's Government Decree on the payment of compensation for audiovisual productions "
            "2024-2026 explicitly states the level of artistic content is NOT subject to evaluation -- a "
            "definitional eligibility category (does the work qualify as an audiovisual production of the "
            "relevant type), not a scored or discretionary test. Every qualifying-format production "
            "automatically satisfies this dimension."
        ),
    },
    "lu_filmfund_tax_shelter_rebate": {
        "mechanism": "DISCRETIONARY_COMMITTEE_ASSESSMENT",
        "fact_type": FACT_USER,
        "description": (
            "Luxembourg's AFS (Aide financiere selective) is assessed by a Film Fund Luxembourg selection "
            "committee on cultural, social and economic criteria -- a genuinely discretionary, non-"
            "formulaic determination by design, not a missing-research gap. The fact needed is whether "
            "the AFS committee has approved (or would approve) this specific project; this cannot be "
            "computed from personnel/script facts alone because the authority itself does not use a "
            "formula."
        ),
    },
    "dk_production_rebate": {
        "mechanism": "COMPETITIVE_RANKED_SCORING_NO_FIXED_THRESHOLD",
        "fact_type": FACT_USER,
        "description": (
            "Denmark's Production and Cultural Test is a 3-criterion, 300-point COMPETITIVE ranking "
            "system (Culture Test = 100 of the 300; the other two are budget size and Danish-spend "
            "share), not a fixed pass/fail threshold -- confirmed via slks.dk. Applications are ranked "
            "against other applicants in the same funding round, so no single project-fact set can "
            "determine QUALIFIES/HARD_FAIL in isolation; the exact per-criterion point template is also "
            "portal-distributed rather than published standalone (the scheme entered force 2026-01-01). "
            "The fact needed is the applicant's actual scored rank in a specific funding round, which "
            "does not exist until an application is submitted."
        ),
    },
}
