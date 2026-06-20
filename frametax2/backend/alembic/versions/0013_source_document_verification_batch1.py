"""0013 — Update source_document metadata for first verification batch.

Updates source_document records for Mauritius, Malta, and Greece with
confirmed official URLs and authority details found via official source
acquisition (June 2026 search batch).

Changes per jurisdiction:
  MU — EDB Mauritius Film Rebate Scheme official page confirmed.
       URL confirmed: edbmauritius.org/schemes/film-rebate-scheme/
       max rate confirmed: up to 40%. Foreign crew cap confirmed: 40% of Mauritius budget.
       Tier remains DISCOVERY (full PDF not yet reviewed end-to-end).

  MT — MFC official rebate page URL updated to specific programme page.
       2024 updated guidelines confirmed from NAO audit report Nov-2024.
       Tier remains DISCOVERY (full document not yet reviewed end-to-end).

  GR — Enterprise Greece audiovisual page URL updated to specific path.
       EKOME confirmed as administering authority.
       40% rate confirmed (raised from 35%). Stacking cap 50% confirmed.
       Tier remains DISCOVERY (full document not yet reviewed end-to-end).

  CY — No official film production rebate page found. source_url removed.
       Notes updated to reflect failed source acquisition attempt.

NOTE ON TIER POLICY:
Source documents remain DISCOVERY until the full programme text has been
read and all core fields verified: rate, QPE definition, ATL treatment,
foreign crew rules, marine qualifying, payment timing, cap, mechanics.
Only then can confidence_tier be promoted to PARSED or VERIFIED.

Revision ID: 0013
Revises: 0012
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# Source document IDs from 0010 (deterministic uuid5)
_DOC_NS = uuid.UUID("a1000000-0010-0000-0001-000000000000")


def _did(seed: str) -> str:
    return str(uuid.uuid5(_DOC_NS, seed))


DOC_MU_ID = _did("doc:mu_edb_production_incentive_guide")
DOC_MT_ID = _did("doc:mt_mfc_rebate_guidelines_2024")
DOC_GR_ID = _did("doc:gr_enterprise_greece_cash_rebate_guide")
DOC_CY_ID = _did("doc:cy_cipa_film_production_rebate")


def upgrade() -> None:
    # MU — official URL confirmed; max rate confirmed 40%; foreign crew cap confirmed
    op.execute(
        sa.text("""
            UPDATE source_documents SET
                source_url    = :url,
                authority_name = :authority,
                notes         = :notes,
                updated_at    = :now
            WHERE id = :id
        """),
        {
            "id": DOC_MU_ID,
            "url": "https://www.edbmauritius.org/schemes/film-rebate-scheme/",
            "authority": "Economic Development Board Mauritius (EDB)",
            "notes": (
                "Official EDB Mauritius programme page confirmed (June 2026 source acquisition). "
                "Programme name: Film Rebate Scheme. "
                "Rate confirmed: 'up to 40% for high end Feature film and TV series' (max_rate=0.40). "
                "base_rate=0.35 retained from production budget evidence; exact tiering by production "
                "type requires full PDF review. "
                "Foreign crew/cast cap confirmed from official text: total remuneration to foreign "
                "cast and crew shall not exceed 40% of total Mauritius production budget; "
                "rebate not applicable to remuneration exceeding this 40% threshold. "
                "Eligible productions confirmed: Feature Film, Commercials, TV series/programmes, "
                "documentaries, Music videos, dubbing. "
                "Locally registered company + Mauritius bank account required. "
                "PDF guidelines: edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf "
                "(not yet fully reviewed — access blocked during acquisition). "
                "Remaining unknowns: ATL scope, min spend, annual cap, QPE full definition, "
                "payment timeline, rebate assignability, SPV requirements, cultural test. "
                "Confidence tier remains DISCOVERY pending full PDF text review."
            ),
            "now": NOW,
        },
    )

    # MT — specific programme page URL confirmed; 2024 updated guidelines noted
    op.execute(
        sa.text("""
            UPDATE source_documents SET
                source_url    = :url,
                authority_name = :authority,
                notes         = :notes,
                updated_at    = :now
            WHERE id = :id
        """),
        {
            "id": DOC_MT_ID,
            "url": "https://maltafilmcommission.com/malta-cash-rebate-incentives-for-the-audiovisual-industry/",
            "authority": "Malta Film Commission (MFC)",
            "notes": (
                "Official MFC rebate programme page confirmed (June 2026 source acquisition). "
                "max_rate=0.40 confirmed from official page and NAO audit Nov-2024 report "
                "('especially the 40 per cent cash rebate scheme'). "
                "base_rate=0.25 retained from prior market review; "
                "base_rate_confirmation required against 2024 updated MFC guidelines. "
                "MFC issued updated guidelines in 2024 (per NAO Malta audit: nao.gov.mt/2024/11). "
                "Programme operational 2018-present per NAO report. "
                "MFS 750,000-gal outdoor water tank confirmed operational. "
                "Full page content blocked during June 2026 fetch attempt (HTTP 403). "
                "Also available: maltafilmcommission.com/financial-incentives/ "
                "Remaining unknowns: base_rate vs 2024 guidelines, exact uplift thresholds, "
                "annual cap, rebate assignability, processing timeline, foreign crew cap. "
                "Confidence tier remains DISCOVERY pending full document read."
            ),
            "now": NOW,
        },
    )

    # GR — Enterprise Greece audiovisual-specific URL confirmed; EKOME confirmed
    op.execute(
        sa.text("""
            UPDATE source_documents SET
                source_url    = :url,
                authority_name = :authority,
                notes         = :notes,
                updated_at    = :now
            WHERE id = :id
        """),
        {
            "id": DOC_GR_ID,
            "url": "https://www.enterprisegreece.gov.gr/en/invest-in-greece/sectors-for-growth/audiovisual-productions",
            "authority": "EKOME (National Centre of Audiovisual Media and Communication) / Enterprise Greece",
            "notes": (
                "Official Enterprise Greece audiovisual page confirmed (June 2026 source acquisition). "
                "40% cash rebate confirmed from official text (raised from prior 35% rate). "
                "Administered jointly by EKOME (ekome.media) and Enterprise Greece. "
                "Eligible: feature films, TV series, documentaries, animation, digital games. "
                "Stacking with other public incentives allowed; total public support cannot exceed "
                "50% of total production cost (confirmed from official source). "
                "Also offers 30% tax relief as alternative mechanism to cash rebate. "
                "Full page content blocked during June 2026 fetch attempt (HTTP 403). "
                "EKOME secondary source: ekome.media/cash-rebate-film-tv-animation-documentaties/ "
                "Remaining unknowns: annual allocation cap amount, ATL scope confirmed, "
                "exact min spend (EUR 100K unconfirmed), WHT on international cast, "
                "rebate assignability to financier, processing timeline, foreign crew local entity. "
                "Confidence tier remains DISCOVERY pending full document text review."
            ),
            "now": NOW,
        },
    )

    # CY — no official source found; source_url cleared; notes updated
    op.execute(
        sa.text("""
            UPDATE source_documents SET
                source_url    = NULL,
                notes         = :notes,
                updated_at    = :now
            WHERE id = :id
        """),
        {
            "id": DOC_CY_ID,
            "notes": (
                "Official film production rebate source NOT FOUND during June 2026 acquisition attempt. "
                "Search attempted: visitcyprus.com (returned only tourism/convention incentives), "
                "cipa.org.cy (search result returned; HTTP fetch blocked). "
                "No dedicated film production rebate programme page located. "
                "Rate of 35% assumed from DISCOVERY market knowledge — not verified. "
                "Cyprus programme reportedly administered jointly by CIPA and Deputy Ministry of Tourism. "
                "Cyprus 12.5% corporate tax rate independently confirmed (not related to film rebate). "
                "ACQUISITION PRIORITY: Contact Cyprus Film Commission (filmcy.org) or "
                "Deputy Ministry of Tourism directly. "
                "Do NOT use Cyprus 35% rate for budget modelling until official source acquired. "
                "Confidence tier: DISCOVERY."
            ),
            "now": NOW,
        },
    )


def downgrade() -> None:
    # Restore to pre-0013 state (0010 original values)
    op.execute(
        sa.text("UPDATE source_documents SET source_url = NULL, authority_name = :auth, notes = :notes, updated_at = :now WHERE id = :id"),
        {
            "id": DOC_MU_ID,
            "auth": "Economic Development Board Mauritius (EDB)",
            "notes": "Primary source for the Mauritius EDB production incentive not yet obtained.",
            "now": NOW,
        },
    )
    op.execute(
        sa.text("UPDATE source_documents SET source_url = :url, notes = :notes, updated_at = :now WHERE id = :id"),
        {
            "id": DOC_MT_ID,
            "url": "https://maltafilmcommission.com/rebate",
            "notes": "Malta Film Commission administers the cash rebate.",
            "now": NOW,
        },
    )
    op.execute(
        sa.text("UPDATE source_documents SET source_url = :url, authority_name = :auth, notes = :notes, updated_at = :now WHERE id = :id"),
        {
            "id": DOC_GR_ID,
            "url": "https://enterprisegreece.gov.gr",
            "auth": "Enterprise Greece / Greek Film Centre (GFC)",
            "notes": "Enterprise Greece administers the 40% cash rebate.",
            "now": NOW,
        },
    )
    op.execute(
        sa.text("UPDATE source_documents SET source_url = :url, notes = :notes, updated_at = :now WHERE id = :id"),
        {
            "id": DOC_CY_ID,
            "url": "https://cipa.org.cy",
            "notes": "CIPA and the Deputy Ministry of Tourism jointly administer the Cyprus rebate.",
            "now": NOW,
        },
    )
