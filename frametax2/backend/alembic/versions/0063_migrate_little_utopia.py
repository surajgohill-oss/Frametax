"""0063 — Project Library Phase C: migrate The Little Utopia into persistence.

Migrates exactly ONE project — The Little Utopia — from the demo/runtime
module (app/demo/little_utopia_state.py) into the real persistent schema
built in Phase B (0062). This is a data migration only:

  - no product schema is added or changed here;
  - no optimizer/incentive-calculation code is touched;
  - no other MTS title or historical project is migrated;
  - the demo module itself is left in place as the live serving path for
    everything this migration does not take over (facts/structures/
    optimizer output keep coming from little_utopia_state.py; only
    lifecycle and leading-structure selection move their source of truth
    to this real Project row — see cineglobe.py router changes in this
    same commit).

Source files migrated (all already discovered in prior sessions — no new
Drive/Mac scan was performed for this migration):
  - screenplay: "The Little Utopia 1_30_26.pdf"
  - budget:     "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf"
  - look book:  "THE LITTLE UTOPIA LOOK BOOK .pdf"
  - deck:       "TheLittleUtopia_Slide.pptx" (two genuinely different-sized
                copies found — local Mac copy and Drive canonical copy are
                NOT assumed byte-identical; recorded as two DocumentVersions,
                lineage left unordered rather than fabricated)
  - artwork:    "utopia.png"

All five were cached under the durable storage root (~/.cineglobe/storage/
little-utopia/) before this migration ran; checksums below were computed
directly against those cached bytes.

People facts (writer/director/producers) are the real, sourced facts from
app/data/little_utopia_people.py (Wikipedia/IMDb, cross-verified against
the production's own documents) — reused verbatim, not re-derived. Lead
cast is genuinely unknown (the budget's own cover page says "CAST: tbc")
and is migrated as such, not fabricated.

Revision ID: 0063
Revises: 0062
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0063"
down_revision: Union[str, None] = "0062"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Real budget line items, reused verbatim from
# app.data.little_utopia_real_budget.LITTLE_UTOPIA_REAL_BUDGET_LINES /
# LITTLE_UTOPIA_REAL_SPEND_CATEGORY — not re-parsed, not re-derived.
# ---------------------------------------------------------------------------
_BUDGET_LINES: tuple[tuple[str, str, float, int | None, str | None], ...] = (
    ("1000", "DEVELOPMENT", 0.0, 3, "atl_writer"),
    ("1100", "SCRIPT", 5_050.0, 3, "atl_writer"),
    ("1200", "PRODUCERS UNIT", 0.0, 4, "atl_producer"),
    ("1300", "DIRECTION", 0.0, 4, "atl_director"),
    ("1400", "CAST", 136_115.0, 7, "atl_cast"),
    ("1600", "ATL TRAVEL & LIVING", 397_279.0, 10, "travel"),
    ("2000", "PRODUCTION STAFF", 321_594.0, 13, "btl_crew_labor"),
    ("2100", "EXTRA TALENT", 21_981.0, 14, "btl_crew_labor"),
    ("2200", "SET DESIGN", 65_873.0, 15, "btl_set_construction"),
    ("2300", "SET CONSTRUCTION", 107_628.0, 17, "btl_set_construction"),
    ("2400", "SET DRESSING", 154_826.0, 18, "btl_set_construction"),
    ("2500", "PROPERTIES", 68_854.0, 20, "btl_equipment_rental"),
    ("2600", "PICTURE VEHICLES AND ANIMALS", 215_218.0, 21, "btl_equipment_rental"),
    ("2700", "WARDROBE", 58_815.0, 23, "btl_equipment_rental"),
    ("2800", "MAKE-UP & HAIR", 51_809.0, 25, "btl_crew_labor"),
    ("2900", "SET OPERATIONS", 90_679.0, 27, "btl_crew_labor"),
    ("3000", "ELECTRICAL", 155_375.0, 29, "btl_equipment_rental"),
    ("3100", "CAMERA", 288_729.0, 32, "btl_equipment_rental"),
    ("3200", "PRODUCTION SOUND", 69_532.0, 33, "btl_crew_labor"),
    ("3300", "SPECIAL EFFECTS & MARINE", 99_837.0, 34, "vessel_marine"),
    ("3400", "LOCATION EXPENSE", 496_232.0, 39, "btl_location_fees"),
    ("3500", "AERIAL/DRONE UNIT", 16_215.0, 40, "btl_equipment_rental"),
    ("3600", "TRANSPORTATION", 321_899.0, 42, "btl_transportation"),
    ("3700", "STAGE & OFFICE RENTALS", 27_732.0, 43, "btl_stage_facility"),
    ("3800", "PRODUCTION LAB & MEDIA MANAGEMENT", 9_674.0, 43, "btl_equipment_rental"),
    ("3900", "BTL TRAVEL & LIVING", 438_254.0, 45, "travel"),
    ("4000", "SPECIAL SHOOT UNITS", 0.0, 46, "btl_equipment_rental"),
    ("5000", "EDITORIAL", 9_068.0, 46, "post_production"),
    ("5100", "EDITORIAL - USA", 0.0, 47, "post_production"),
    ("5200", "SOUND POST PRODUCTION", 0.0, 49, "sound"),
    ("5300", "PICTURE POST PRODUCTION", 0.0, 50, "post_production"),
    ("5400", "GRAPHICS / TITLES / STOCK FOOTAGE", 0.0, 50, "post_production"),
    ("5500", "DELIVERABLES", 0.0, 51, "post_production"),
    ("6000", "MUSIC", 0.0, 52, "music"),
    ("6100", "VFX DEPARTMENT", 52_500.0, 52, "vfx"),
    ("6500", "USA ADMIN COSTS", 0.0, 52, "legal_accounting"),
    ("7000", "ADMINISTRATIVE EXPENSES", 297_593.0, 55, "production_service_fees"),
    ("7100", "PUBLICITY", 24_348.0, 55, "btl_crew_labor"),
    ("7200", "INSURANCE", 12_374.0, 56, "insurance"),
    ("7300", "MARKETING", 0.0, 56, None),
    ("7800", "FINANCE & LEGAL", 0.0, 57, "legal_accounting"),
    ("8100", "Insurance : 1.2%", 48_181.0, None, "insurance"),
    ("8200", "Bond : 0.0%", 0.0, None, "completion_bond"),
    ("8300", "Contigency : 7.5%", 301_131.0, None, "contingency"),
)

_STORAGE_PREFIX = "little-utopia"


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Organization
    # ------------------------------------------------------------------
    org_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO organizations (id, name, slug, is_active, created_at, updated_at)
            VALUES (:id, :name, :slug, true, :now, :now)
        """),
        {"id": org_id, "name": "Mind The Story Media", "slug": "mind-the-story-media", "now": NOW},
    )

    mu_row = conn.execute(sa.text("SELECT id FROM jurisdictions WHERE code = 'MU' LIMIT 1")).fetchone()
    mu_id = str(mu_row[0]) if mu_row else None

    # ------------------------------------------------------------------
    # 2. Project (leading_structure_id filled in after the structure exists)
    # ------------------------------------------------------------------
    project_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO projects (
                id, organization_id, title, logline, genre, format,
                total_budget_usd, home_jurisdiction_id, target_shoot_year,
                notes, lifecycle, created_at, updated_at
            ) VALUES (
                :id, :org_id, :title, :logline, :genre, :format,
                :budget, :home_jur, :year,
                :notes, 'EVALUATION', :now, :now
            )
        """),
        {
            "id": project_id, "org_id": org_id, "title": "The Little Utopia",
            "logline": (
                "Newlyweds rescued at sea discover a terrifying darkness aboard a "
                "bohemian couple's sailboat — and must risk everything to survive."
            ),
            "genre": "Psychosexual Thriller", "format": "feature",
            "budget": 4_364_393.00, "home_jur": mu_id, "year": 2026,
            "notes": (
                "Migrated Phase C (2026-08-05) from app/demo/little_utopia_state.py. "
                "Lifecycle set to EVALUATION, matching the last confirmed frontend "
                "localStorage state — not inferred from optimizer/engine state."
            ),
            "now": NOW,
        },
    )

    conn.execute(
        sa.text("""
            INSERT INTO project_aliases (id, project_id, alias, source, created_at, updated_at)
            VALUES (:id, :pid, :alias, :src, :now, :now)
        """),
        {
            "id": str(uuid.uuid4()), "pid": project_id, "alias": "The Boat",
            "src": "Original novel by Clara Salaman that the screenplay is adapted from (per script title page).",
            "now": NOW,
        },
    )

    # ------------------------------------------------------------------
    # 3. Documents / DocumentVersions / DocumentVersionSources
    # ------------------------------------------------------------------
    def _doc(category: str, title: str) -> str:
        did = str(uuid.uuid4())
        conn.execute(
            sa.text("""
                INSERT INTO documents (id, project_id, category, title, created_at, updated_at)
                VALUES (:id, :pid, :cat, :title, :now, :now)
            """),
            {"id": did, "pid": project_id, "cat": category, "title": title, "now": NOW},
        )
        return did

    def _version(document_id: str, filename: str, checksum: str | None, size: int | None,
                 detected_date: str | None, label: str | None, is_current: bool) -> str:
        vid = str(uuid.uuid4())
        conn.execute(
            sa.text("""
                INSERT INTO document_versions (
                    id, document_id, original_filename, storage_path, checksum_sha256,
                    file_size, detected_date, version_label, ingested_at, is_current,
                    extraction_status, created_at, updated_at
                ) VALUES (
                    :id, :did, :fn, :sp, :cs, :sz, :dd, :lbl, :ingested, :cur, 'pending', :now, :now
                )
            """),
            {
                "id": vid, "did": document_id, "fn": filename,
                "sp": f"{_STORAGE_PREFIX}/{filename}" if checksum else None,
                "cs": checksum, "sz": size, "dd": detected_date, "lbl": label,
                "ingested": NOW, "now": NOW, "cur": is_current,
            },
        )
        return vid

    def _source(version_id: str, source_type: str, pointer: str, path: str | None = None) -> None:
        conn.execute(
            sa.text("""
                INSERT INTO document_version_sources (
                    id, document_version_id, source_type, source_pointer, source_path,
                    source_status, last_verified_at, created_at, updated_at
                ) VALUES (:id, :vid, :st, :ptr, :path, 'ok', :verified, :now, :now)
            """),
            {"id": str(uuid.uuid4()), "vid": version_id, "st": source_type,
             "ptr": pointer, "path": path, "verified": NOW, "now": NOW},
        )

    # Screenplay
    screenplay_doc = _doc("screenplay", "The Little Utopia — Screenplay")
    screenplay_ver = _version(
        screenplay_doc, "The Little Utopia 1_30_26.pdf",
        "c5213c9ced713e071a21647a4c08cec7914f18cf6bdd1432c33d4c00ff4038c0",
        1250024, "2026-01-30", "1/30/26", True,
    )
    _source(screenplay_ver, "local", "/Users/Suraj/Downloads/The Little Utopia 1_30_26.pdf",
            "/Users/Suraj/Downloads/The Little Utopia 1_30_26.pdf")
    _source(screenplay_ver, "google_drive", "1-tdhPptzjPnq0xVZxFVZoM_tprOl6koG",
            "Drive: PROJECTS/THE LITTLE UTOPIA/The Little Utopia 1_30_26.pdf (canonical)")
    _source(screenplay_ver, "google_drive", "1U4KOgGQPQMeN4pCM5lZhnHQjr7XtFo3b",
            "Drive: second 1,250,024-byte copy found during discovery (same size, not independently re-verified byte-for-byte)")

    # Budget
    budget_doc = _doc("budget", "The Little Utopia — Budget (Mauritius)")
    budget_ver = _version(
        budget_doc, "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf",
        "4b98f8236a4a6029a2da8fb6495c71c83586141ebe8ece8d0ec6dc99b1ac698c",
        736227, "2025-06-03", "v1", True,
    )
    _source(budget_ver, "local", "/Users/Suraj/Downloads/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf",
            "/Users/Suraj/Downloads/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf")
    _source(budget_ver, "google_drive", "19WvjvfRKmmSdiJ_e4zQczOYtOPNPv9px",
            "Drive: PROJECTS/THE LITTLE UTOPIA/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf (canonical)")
    _source(budget_ver, "google_drive", "1-Fhvypgj0IQYG_I9G9IU-qvq8vS8hdUg",
            "Drive: Downloads-mirror copy, same reported size (736,227 bytes)")

    # Look book (Drive-only — never existed on local disk)
    lookbook_doc = _doc("lookbook", "The Little Utopia — Look Book")
    lookbook_ver = _version(
        lookbook_doc, "THE LITTLE UTOPIA LOOK BOOK .pdf",
        "6a42245486712a01c415d96b52bd03380db5349383fd0e7b17ba4173932af7ef"[:64],
        2012263, None, None, True,
    )
    _source(lookbook_ver, "google_drive", "1uJ4xnVZQRTS7ay5OyolXSA4LxRZqH2DQ",
            "Drive: PROJECTS/THE LITTLE UTOPIA/THE LITTLE UTOPIA LOOK BOOK .pdf")

    # Deck — two genuinely different-sized copies; lineage left unordered.
    deck_doc = _doc("deck", "The Little Utopia — Slide Deck")
    deck_local_ver = _version(
        deck_doc, "TheLittleUtopia_Slide.pptx",
        "4f6d0d54d53231610064367c68498d35fe00af650eb5fc021ef67595664db29f"[:64],
        830698, None, "local Mac copy", True,
    )
    _source(deck_local_ver, "local", "/Users/Suraj/Downloads/TheLittleUtopia_Slide.pptx",
            "/Users/Suraj/Downloads/TheLittleUtopia_Slide.pptx")
    deck_drive_ver = _version(
        deck_doc, "TheLittleUtopia_Slide.pptx", None, 589045, None, "Drive canonical copy", False,
    )
    _source(deck_drive_ver, "google_drive", "1GegzIRuOghWVfBPUARbU1ZxPBHYLe1tQ",
            "Drive: PROJECTS/THE LITTLE UTOPIA/TheLittleUtopia_Slide.pptx — 589,045 bytes, "
            "NOT the same size as the local copy (830,698 bytes); not assumed identical, "
            "not downloaded/checksummed this pass — recorded as a distinct version, lineage unordered.")

    # Artwork (Drive-only, in the Drive "Downloads" mirror folder, never in
    # the canonical PROJECTS folder or on local disk)
    artwork_doc = _doc("artwork", "The Little Utopia — Key Art")
    artwork_ver = _version(
        artwork_doc, "utopia.png",
        "a6df89962c92588f65bb0bf06513a4d4b78a4a1899b97dac93cc7295066425c6"[:64],
        2374733, None, None, True,
    )
    _source(artwork_ver, "google_drive", "1p-AQvH6Odxxs_iV1QXaYU2Qyz3_Ivuy3",
            "Drive: 'Downloads' mirror folder (NOT the canonical PROJECTS folder) — only location found")

    # current_version_id back-pointers
    for doc_id, ver_id in (
        (screenplay_doc, screenplay_ver), (budget_doc, budget_ver),
        (lookbook_doc, lookbook_ver), (deck_doc, deck_local_ver), (artwork_doc, artwork_ver),
    ):
        conn.execute(
            sa.text("UPDATE documents SET current_version_id = :vid WHERE id = :did"),
            {"vid": ver_id, "did": doc_id},
        )

    # ------------------------------------------------------------------
    # 4. project_assets — master artwork
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
            INSERT INTO project_assets (
                id, project_id, kind, source_type, storage_path, checksum_sha256,
                file_size, is_master, source_document_version_id, created_at, updated_at
            ) VALUES (
                :id, :pid, 'artwork', 'discovered_image', :sp, :cs, :sz, true, :vid, :now, :now
            )
        """),
        {
            "id": str(uuid.uuid4()), "pid": project_id,
            "sp": f"{_STORAGE_PREFIX}/utopia.png",
            "cs": "a6df89962c92588f65bb0bf06513a4d4b78a4a1899b97dac93cc7295066425c6",
            "sz": 2374733, "vid": artwork_ver, "now": NOW,
        },
    )

    # ------------------------------------------------------------------
    # 5. Typed document integration — BudgetDocument + BudgetLineItem,
    #    ScreenplayDocument. Reuses the already-verified real budget data
    #    from app.data.little_utopia_real_budget — not re-parsed.
    # ------------------------------------------------------------------
    budget_document_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO budget_documents (
                id, project_id, filename, file_type, storage_path, currency_code,
                total_budget_raw, origin_city, rate_base, is_active, extraction_status,
                notes, document_version_id, created_at, updated_at
            ) VALUES (
                :id, :pid, :fn, 'pdf', :sp, 'USD', :total, 'LA', NULL, true, 'pending',
                :notes, :vid, :now, :now
            )
        """),
        {
            "id": budget_document_id, "pid": project_id,
            "fn": "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf",
            "sp": f"{_STORAGE_PREFIX}/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf",
            "total": 4_364_393.00,
            "notes": (
                "Grand Total per top sheet: $4,364,393.00. Leaf-account sum: "
                "$4,364,395.00 (a $2.00 source-document rounding variance, "
                "accepted per app.data.little_utopia_real_budget — not corrected). "
                "extraction_status='pending': line items below were migrated from "
                "already-verified data, not run through this app's generic PDF "
                "extraction pipeline against this specific file."
            ),
            "vid": budget_ver, "now": NOW,
        },
    )
    for code, desc, amount, page, spend_cat in _BUDGET_LINES:
        conn.execute(
            sa.text("""
                INSERT INTO budget_line_items (
                    id, budget_document_id, department, description, atl_btl,
                    spend_category, is_labor, is_fixed, amount_raw, amount_normalized,
                    currency_code, amount_usd, compensation_type, is_qualifying_spend_candidate,
                    source_page, review_status, created_at, updated_at
                ) VALUES (
                    :id, :bdid, :code, :desc, :atlbtl, :cat, false, false, :amt, :amt,
                    'USD', :amt, 'cash', true, :page, 'pending', :now, :now
                )
            """),
            {
                "id": str(uuid.uuid4()), "bdid": budget_document_id, "code": code,
                "desc": f"{code} {desc}",
                "atlbtl": "atl" if code in ("1000", "1100", "1200", "1300", "1400", "1600") else "btl",
                "cat": spend_cat, "amt": amount, "page": page, "now": NOW,
            },
        )

    screenplay_document_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO screenplay_documents (
                id, project_id, filename, file_type, storage_path, extraction_status,
                notes, document_version_id, created_at, updated_at
            ) VALUES (
                :id, :pid, :fn, 'pdf', :sp, 'pending', :notes, :vid, :now, :now
            )
        """),
        {
            "id": screenplay_document_id, "pid": project_id,
            "fn": "The Little Utopia 1_30_26.pdf",
            "sp": f"{_STORAGE_PREFIX}/The Little Utopia 1_30_26.pdf",
            "notes": (
                "extraction_status='pending': the current demo/runtime facts "
                "(SCRIPT_REQUIREMENTS in little_utopia_state.py) were derived from "
                "the synopsis, look book, and the screenplay's opening pages only — "
                "not a full page-by-page read, and not run through this app's "
                "generic screenplay-chunking pipeline against this specific file."
            ),
            "vid": screenplay_ver, "now": NOW,
        },
    )

    # ------------------------------------------------------------------
    # 6. ProjectFact — provenance-distinct, reusing already-verified facts
    # ------------------------------------------------------------------
    def _fact(key: str, value: str | None, value_type: str, source_type: str,
              source_version: str | None = None, source_location: str | None = None,
              confidence: float | None = None, review_status: str = "pending") -> None:
        conn.execute(
            sa.text("""
                INSERT INTO project_facts (
                    id, project_id, fact_key, value, value_type, source_type,
                    source_document_version_id, source_location, extraction_confidence,
                    review_status, created_at, updated_at
                ) VALUES (
                    :id, :pid, :key, :val, :vt, :st, :svid, :sloc, :conf, :rs, :now, :now
                )
            """),
            {
                "id": str(uuid.uuid4()), "pid": project_id, "key": key, "val": value,
                "vt": value_type, "st": source_type, "svid": source_version,
                "sloc": source_location, "conf": confidence, "rs": review_status, "now": NOW,
            },
        )

    _fact("gross_budget_usd", "4364393.00", "number", "recovered_demo_state",
          budget_ver, "Grand Total, budget top sheet, page 1", 1.0, "approved")
    _fact("jurisdiction_code", "MU", "string", "recovered_demo_state",
          budget_ver, "Budget header: 'SHOOT: Mauritius: 35 days'", 1.0, "approved")
    _fact("writer_name", "Clara Salaman", "string", "recovered_demo_state",
          screenplay_ver, "Screenplay title page; https://en.wikipedia.org/wiki/Clara_Salaman", 0.95, "approved")
    _fact("writer_nationality", "GB", "string", "recovered_demo_state",
          None, "https://en.wikipedia.org/wiki/Clara_Salaman (Wikipedia, cross-verified against script/look book/deck)", 0.9, "approved")
    _fact("director_name", "Kim Farrant", "string", "recovered_demo_state",
          lookbook_ver, "Look book; https://en.wikipedia.org/wiki/Kim_Farrant", 0.95, "approved")
    _fact("director_nationality", "AU", "string", "recovered_demo_state",
          None, "https://en.wikipedia.org/wiki/Kim_Farrant (Wikipedia/IMDb, cross-verified against script/look book/deck)", 0.9, "approved")
    _fact("producer_1_name", "Rachel Winter", "string", "recovered_demo_state",
          lookbook_ver, "Look book; https://en.wikipedia.org/wiki/Rachel_Winter", 0.95, "approved")
    _fact("producer_1_nationality", "US", "string", "recovered_demo_state",
          None, "https://en.wikipedia.org/wiki/Rachel_Winter", 0.9, "approved")
    _fact("producer_2_name", "Max Botkin", "string", "recovered_demo_state",
          lookbook_ver, "Look book; https://www.imdb.com/name/nm1363111/", 0.95, "approved")
    _fact("producer_2_nationality", "US", "string", "recovered_demo_state",
          None, "https://www.imdb.com/name/nm1363111/", 0.9, "approved")
    _fact("lead_cast_nationality", None, "string", "recovered_demo_state",
          budget_ver, "Budget cover page states 'CAST: tbc' (3 June 2025) — genuinely unannounced, not fabricated", None, "pending")

    # ------------------------------------------------------------------
    # 7. TalentProfile + ProjectPerson (reused, not duplicated)
    # ------------------------------------------------------------------
    def _person(name: str, role: str, nationality: str, source_url: str) -> None:
        talent_id = str(uuid.uuid4())
        conn.execute(
            sa.text("""
                INSERT INTO talent_profiles (
                    id, name, role, primary_nationality, notes, created_at, updated_at
                ) VALUES (:id, :name, :role, :nat, :notes, :now, :now)
                ON CONFLICT DO NOTHING
            """),
            {"id": talent_id, "name": name, "role": role, "nat": nationality,
             "notes": f"Source: {source_url}", "now": NOW},
        )
        existing = conn.execute(
            sa.text("SELECT id FROM talent_profiles WHERE name = :name LIMIT 1"), {"name": name},
        ).fetchone()
        real_talent_id = str(existing[0]) if existing else talent_id
        conn.execute(
            sa.text("""
                INSERT INTO project_people (id, project_id, talent_id, role, is_confirmed, notes, created_at, updated_at)
                VALUES (:id, :pid, :tid, :role, true, :notes, :now, :now)
            """),
            {"id": str(uuid.uuid4()), "pid": project_id, "tid": real_talent_id, "role": role,
             "notes": f"Source: {source_url}", "now": NOW},
        )

    _person("Clara Salaman", "writer", "GB", "https://en.wikipedia.org/wiki/Clara_Salaman")
    _person("Kim Farrant", "director", "AU", "https://en.wikipedia.org/wiki/Kim_Farrant")
    _person("Rachel Winter", "producer", "US", "https://en.wikipedia.org/wiki/Rachel_Winter")
    _person("Max Botkin", "producer", "US", "https://www.imdb.com/name/nm1363111/")

    # ------------------------------------------------------------------
    # 8. ProjectLocationRequirement — the 4 CONFIRMED script-derived
    #    requirements (marine, open_water_filming, period, night_work);
    #    the several NOT_EVIDENT ones are correctly absent (never known-false).
    # ------------------------------------------------------------------
    for desc, notes in (
        ("Marine / open-water setting",
         "Story opens and centers on a sailing boat sinking at sea; open-water swimming; "
         "Mediterranean setting throughout. CONFIRMED — screenplay opening pages."),
        ("Open-water filming",
         "EXT. SEA scenes; boat interior/exterior at sea; storm/sinking sequence. "
         "CONFIRMED — screenplay opening pages."),
        ("Period setting (dual timeline)",
         "Dual timeline: 1978 Cornwall (flashback) + 1985 Mediterranean (main story), "
         "'Inspired by True Events' title card. CONFIRMED — screenplay."),
        ("Night exterior work",
         "EXT. SEA. NIGHT and EXT. BEACH. NIGHT scenes in the screenplay's opening pages. "
         "CONFIRMED — screenplay."),
    ):
        conn.execute(
            sa.text("""
                INSERT INTO project_location_requirements (
                    id, project_id, description, is_flexible, source_document_version_id,
                    notes, created_at, updated_at
                ) VALUES (:id, :pid, :desc, NULL, :vid, :notes, :now, :now)
            """),
            {"id": str(uuid.uuid4()), "pid": project_id, "desc": desc,
             "vid": screenplay_ver, "notes": notes, "now": NOW},
        )

    # ------------------------------------------------------------------
    # 9. Leading structure — the currently-EFFECTIVE structure (rank #1,
    #    "ALLOC-BASELINE-MU"), since the frontend's own leadingStructureId
    #    is null-by-default (no explicit override recorded anywhere) and
    #    falls back to the optimizer's rank #1. Real economics figures
    #    below are copied from a live read of /api/v1/cineglobe/structures
    #    at migration time, not recalculated and not fabricated. No
    #    optimizer/calculation code was invoked to produce this migration.
    # ------------------------------------------------------------------
    structure_id = str(uuid.uuid4())
    conn.execute(
        sa.text("""
            INSERT INTO production_structures (
                id, project_id, name, description, status,
                jurisdiction_allocations, notes, created_at, updated_at
            ) VALUES (
                :id, :pid, :name, :desc, 'complete', :alloc, :notes, :now, :now
            )
        """),
        {
            "id": structure_id, "pid": project_id,
            "name": "ALLOC-BASELINE-MU",
            "desc": "Mauritius single-jurisdiction baseline",
            "alloc": '[{"jurisdiction_code": "MU", "shoot_pct": 1.0, "budget_pct": 1.0}]',
            "notes": (
                "Migrated as the currently-effective leading structure (optimizer "
                "rank #1 as of 2026-08-05) — no explicit user 'Set as Leading' "
                "override existed in the frontend's browser-only state at "
                "migration time (leadingStructureId was null, falling back to "
                "rank #1 per AppState.jsx's own documented behavior)."
            ),
            "now": NOW,
        },
    )
    conn.execute(
        sa.text("""
            INSERT INTO structure_calculation_results (
                id, structure_id, engine_version, total_budget_usd,
                total_incentive_value_usd, true_net_cost_usd, risk_adjusted_net_cost_usd,
                rank_by_net_cost, input_budget_document_version_id, input_fingerprint,
                input_snapshot_json, created_at, updated_at
            ) VALUES (
                :id, :sid, 'demo-runtime-2026-08-05', :budget, :incentive, :npc, :npc_cons,
                1, :bvid, :fp, :snap, :now, :now
            )
        """),
        {
            "id": str(uuid.uuid4()), "sid": structure_id,
            "budget": 4_364_393.00, "incentive": 1_742_130.80,
            "npc": 2_622_262.20, "npc_cons": 3_057_794.90,
            "bvid": budget_ver, "fp": "phasec-migration-snapshot-2026-08-05",
            "snap": (
                '{"structure_id": "ALLOC-BASELINE-MU", "rank": 1, '
                '"selected_incentive_usd": 1742130.8, "npc_verified_usd": 2622262.2, '
                '"npc_with_adjustments_usd": 2622262.2, "npc_conservative_usd": 3057794.9, '
                '"source": "live read of GET /api/v1/cineglobe/structures at migration time"}'
            ),
            "now": NOW,
        },
    )
    conn.execute(
        sa.text("UPDATE projects SET leading_structure_id = :sid WHERE id = :pid"),
        {"sid": structure_id, "pid": project_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    project_row = conn.execute(
        sa.text("SELECT id FROM projects WHERE title = 'The Little Utopia' LIMIT 1")
    ).fetchone()
    if not project_row:
        return
    pid = project_row[0]
    # ON DELETE CASCADE on project_id handles nearly everything; explicitly
    # null the leading_structure_id first to avoid an FK ordering issue,
    # then delete the project (cascades to aliases/documents/facts/people/
    # locations/structures/results), then the org (only if it has no other
    # projects — Phase C never creates a second one, so this is safe here).
    conn.execute(sa.text("UPDATE projects SET leading_structure_id = NULL WHERE id = :pid"), {"pid": pid})
    conn.execute(sa.text("DELETE FROM projects WHERE id = :pid"), {"pid": pid})
    conn.execute(
        sa.text("DELETE FROM organizations WHERE slug = 'mind-the-story-media' "
                "AND NOT EXISTS (SELECT 1 FROM projects WHERE organization_id = organizations.id)")
    )
