"""0043 — Seed fund_economics for 23 existing grant/fund programs.

Phase D / Phase 1: Populates the fund_economics table for all existing
grant, co-production fund, development fund, and discretionary fund programs
with available intelligence.

Revision ID: 0043
Revises: 0042
"""
from __future__ import annotations

import uuid
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0043"
down_revision: Union[str, None] = "0042"
branch_labels = None
depends_on = None


def _uid(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"frametax.fund_econ.{key}")


# ---------------------------------------------------------------------------
# Fund economics data keyed by program slug.
# Fields: (is_repayable, repayment_terms, is_recoupable, recoupment_terms,
#          has_equity_participation, equity_participation_notes,
#          has_matching_requirement, matching_notes,
#          has_territorial_spend_requirement, territorial_spend_notes,
#          eligible_formats, typical_max_award_usd,
#          award_range_notes, is_competitive,
#          stackable_with_incentives, stackability_notes,
#          confidence_tier, notes)
# ---------------------------------------------------------------------------
_FUND_DATA: dict[str, dict] = {
    "eu_eurimages": {
        "is_repayable": True,
        "repayment_terms": (
            "Repayable advance from first receipts of co-production. Recouped pro-rata "
            "alongside other co-producers. No recoupment if project fails commercially."
        ),
        "is_recoupable": True,
        "recoupment_terms": "Eurimages recoups from theatrical/sales receipts pari passu.",
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": (
            "Minimum 3 co-producing countries required (2 for documentary). "
            "Each country must have a qualifying co-producer."
        ),
        "has_territorial_spend_requirement": False,
        "territorial_spend_notes": None,
        "eligible_formats": "feature,documentary,animation",
        "typical_max_award_usd": 1_650_000,
        "award_range_notes": "EUR 1.5M ceiling per project (USD equivalent at ~1.10). Typical awards EUR 300K–1.5M.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "Eurimages does not reduce national tax credit bases in member states. "
            "Stacks with UK AVEC, IE Section 481, FR TRIP, DE DFFF, etc. "
            "Each country's incentive applies to its own eligible spend."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Council of Europe fund operating since 1988. 44 member states.",
    },

    "eu_media_fund": {
        "is_repayable": True,
        "repayment_terms": (
            "Development loans are repayable if project goes into production. "
            "Selective distribution support is partly repayable from receipts."
        ),
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": (
            "Project must be European; producers must be established in MEDIA-eligible countries. "
            "Cross-border co-production and distribution mandatory for higher funding tiers."
        ),
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": (
            "Production must contribute to European cultural identity and "
            "primary spend must occur in MEDIA-eligible countries."
        ),
        "eligible_formats": "feature,documentary,animation,series,game",
        "typical_max_award_usd": 2_750_000,
        "award_range_notes": "EUR 2.5M ceiling for large co-productions. Typical development: EUR 50–150K.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "Creative Europe MEDIA support does not constitute state aid reducing national "
            "incentive bases. Stacks with national credits of member states."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Creative Europe MEDIA 2021-2027. EUR 1.07B total budget for 7-year cycle.",
    },

    "nordic_ftvf": {
        "is_repayable": True,
        "repayment_terms": (
            "Repayable from net receipts. Repayment obligation ceases if project "
            "does not recoup production costs."
        ),
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": (
            "Co-production between at least two Nordic/Baltic countries required. "
            "Each must have an established broadcaster or production company attached."
        ),
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Minimum Nordic spend required. Majority of creative key personnel must be Nordic.",
        "eligible_formats": "feature,documentary,series",
        "typical_max_award_usd": 1_650_000,
        "award_range_notes": "SEK 8-15M per project (USD 750K–1.5M at current rates).",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "Stacks with Nordic national incentives (NO 25%, FI 25%, DK 22%, SE 25%). "
            "Does not reduce national qualifying spend bases."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Nordisk Film & TV Fond. Covers DK, FI, IS, NO, SE + Baltic states.",
    },

    "ca_cmf": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": (
            "Broadcaster licence fee required as co-financing commitment. "
            "Convergent stream requires Canadian broadcaster attach."
        ),
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Spend must be on Canadian content for Canadian broadcasters. CRTC-certified Canadian content.",
        "eligible_formats": "series,documentary,animation",
        "typical_max_award_usd": 7_500_000,
        "award_range_notes": "Up to CAD $10M for flagship drama. Typical: CAD $1-4M for 1-hour drama series.",
        "is_competitive": True,
        "stackable_with_incentives": False,
        "stackability_notes": (
            "CMF is government assistance. Under ITA §125.4 and CRA T4283, "
            "CMF grants must be deducted from qualified labour expenditure (QLE) "
            "before computing CPTC. Reduces CPTC qualifying basis."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Canada Media Fund (CMF). CAD $400M+ annual budget. Broadcaster-driven convergent stream.",
    },

    "ca_telefilm_dev": {
        "is_repayable": True,
        "repayment_terms": (
            "Telefilm advances are equity investments repayable from first receipts. "
            "Recouped at 1:1 before producers' share. Co-investment model."
        ),
        "is_recoupable": True,
        "recoupment_terms": "Telefilm recoups its investment from gross receipts as equity co-investor.",
        "has_equity_participation": True,
        "equity_participation_notes": (
            "Telefilm takes equity position proportional to its investment. "
            "Backend participation from global sales."
        ),
        "has_matching_requirement": True,
        "matching_notes": "Must demonstrate co-financing from private sector (distributors, broadcasters, private equity).",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Canadian content; majority Canadian key creative.",
        "eligible_formats": "feature",
        "typical_max_award_usd": 3_750_000,
        "award_range_notes": "Up to CAD $5M equity. Typical: CAD $1-3M for mid-budget English-language features.",
        "is_competitive": True,
        "stackable_with_incentives": False,
        "stackability_notes": (
            "Telefilm equity constitutes government assistance under ITA §125.4. "
            "Reduces CPTC QCLE base via T4283 government assistance deduction."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Telefilm Canada — Canada Feature Film Fund (CFFF). Equity co-investment model.",
    },

    "gb_bfi_production": {
        "is_repayable": True,
        "repayment_terms": (
            "BFI Film Fund typically invests as an equity co-investor. "
            "Investment repayable from recoupment waterfall after production costs."
        ),
        "is_recoupable": True,
        "recoupment_terms": "BFI recoups equity share from gross receipts proportionally to investment.",
        "has_equity_participation": True,
        "equity_participation_notes": "BFI takes equity share in IP and participates in backend receipts.",
        "has_matching_requirement": True,
        "matching_notes": "Must demonstrate co-financing. BFI rarely finances more than 50% of budget.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Must pass BFI Cultural Test (UK cultural content test).",
        "eligible_formats": "feature,documentary",
        "typical_max_award_usd": 2_530_000,
        "award_range_notes": "Up to GBP 2M per project (USD 2.5M). Typical: GBP 300K–1.5M.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "BFI equity investment does not reduce UK AVEC qualifying spend basis. "
            "AVEC applies to UK-qualifying expenditure net of credits but BFI investment "
            "is not deducted from the AVEC qualifying spend — it is co-financing."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "BFI Film Fund — Lottery-funded. Supports ambitious British films.",
    },

    "fr_cnc_production": {
        "is_repayable": True,
        "repayment_terms": (
            "Avance sur recettes is a repayable advance from first receipts. "
            "Repayment triggered once film achieves commercial break-even."
        ),
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "French producer must hold majority rights. Co-financing from distributor or broadcaster expected.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Film must be French cultural content. Majority French creative personnel.",
        "eligible_formats": "feature,documentary",
        "typical_max_award_usd": 1_430_000,
        "award_range_notes": "Up to EUR 1.2M for first-film aid. Typical selective aid: EUR 150K–800K.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "CNC avance does not reduce TRIP (French tax rebate for international) qualifying basis "
            "for foreign productions. For French domestic productions, interaction with SOFICA "
            "investment must be analysed case-by-case."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "CNC Avances sur Recettes — France's main selective production aid. Two annual selection rounds.",
    },

    "au_screen_production": {
        "is_repayable": True,
        "repayment_terms": (
            "Screen Australia equity investment is repayable from first receipts. "
            "Recouped at cost before producer share."
        ),
        "is_recoupable": True,
        "recoupment_terms": "Screen Australia recoups equity from gross receipts proportionally.",
        "has_equity_participation": True,
        "equity_participation_notes": "Screen Australia holds equity in IP and participates in global sales receipts.",
        "has_matching_requirement": True,
        "matching_notes": "Must demonstrate strong co-financing from private or international sources.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Australian content. Key Australian creative elements required.",
        "eligible_formats": "feature,documentary,animation,series",
        "typical_max_award_usd": 2_200_000,
        "award_range_notes": "Up to AUD $3M+ for major productions. Typical: AUD $500K–2M.",
        "is_competitive": True,
        "stackable_with_incentives": False,
        "stackability_notes": (
            "Screen Australia equity is government assistance. Under Australian Location Offset "
            "and Producer Offset rules, government financial assistance reduces qualifying "
            "Australian production expenditure (QAPE) — the base for both offsets."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Screen Australia — National screen agency. Producer Offset separate from this fund.",
    },

    "nl_hbf": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": False,
        "territorial_spend_notes": None,
        "eligible_formats": "feature,documentary,short",
        "typical_max_award_usd": 110_000,
        "award_range_notes": "EUR 50–100K per project (USD 55K–110K). Small grants for Global South filmmakers.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Non-repayable grants. No interaction with national tax incentives expected.",
        "confidence_tier": "DISCOVERY",
        "notes": "Hubert Bals Fund (IFFR) — Dutch Institute for developing-world filmmakers.",
    },

    "qa_dfi_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": False,
        "territorial_spend_notes": None,
        "eligible_formats": "feature,documentary,short",
        "typical_max_award_usd": 400_000,
        "award_range_notes": "Up to QAR 1.5M (~USD $400K). Two annual cycles (spring/fall).",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Non-repayable grant. No known interaction with production incentives in other countries.",
        "confidence_tier": "DISCOVERY",
        "notes": "Doha Film Institute — Grants for Arab and international filmmakers. Separate from QFC incentive.",
    },

    "us_sundance_doc": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": False,
        "territorial_spend_notes": None,
        "eligible_formats": "documentary",
        "typical_max_award_usd": 300_000,
        "award_range_notes": "Grants USD $25K–$300K per project. Multiple rounds annually.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Non-repayable private foundation grant. No interaction with state/federal tax credits.",
        "confidence_tier": "DISCOVERY",
        "notes": "Sundance Institute Documentary Fund — non-governmental, private foundation.",
    },

    "za_dac_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "South African content requirement. South African key creative personnel.",
        "eligible_formats": "feature,documentary,animation",
        "typical_max_award_usd": 250_000,
        "award_range_notes": "ZAR 3-4M grants (~USD $160K–220K at current rates). NFVF allocation varies annually.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Stacks with NFVF Foreign Film Incentive for qualifying international co-productions.",
        "confidence_tier": "DISCOVERY",
        "notes": "NFVF South Africa — Dept of Arts and Culture fund. Separate from Section 12O foreign incentive.",
    },

    "nohfc_production_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Spend must occur in Northern Ontario (defined geographic region).",
        "eligible_formats": "feature,documentary,series,short",
        "typical_max_award_usd": 375_000,
        "award_range_notes": "Up to CAD $500K (~USD $375K). Discretionary; amount varies by project.",
        "is_competitive": True,
        "stackable_with_incentives": False,
        "stackability_notes": (
            "NOHFC grants are government assistance. Must be deducted from OFTTC and "
            "CPTC qualifying labour bases before computing credits."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "Northern Ontario Heritage Fund Corporation — production fund for Northern Ontario shoots.",
    },

    "ibermedia_programme": {
        "is_repayable": True,
        "repayment_terms": "Ibermedia loans are repayable from first exploitation receipts.",
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "Minimum two Ibero-American co-producing countries required.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Production must involve Latin American / Iberian creative elements.",
        "eligible_formats": "feature,documentary,series",
        "typical_max_award_usd": 400_000,
        "award_range_notes": "USD $200K–$500K per project. Annual fund EUR 5M+ from member contributions.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": (
            "Stacks with national incentives of member states (BR, MX, AR, CO, PE, CL, etc.) "
            "and EU MEDIA for Spanish/Portuguese productions."
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "IBERMEDIA Programme — Ibero-American co-production fund. 20+ member states.",
    },

    "de_fff_bayern": {
        "is_repayable": True,
        "repayment_terms": "FFF Bayern loans are repayable from exploitation receipts (investment loans).",
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "Private co-financing required. FFF rarely funds more than 50% of budget.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Significant spend in Bavaria required (regional spend obligation typically 150% of grant).",
        "eligible_formats": "feature,documentary,series,animation",
        "typical_max_award_usd": 2_200_000,
        "award_range_notes": "Up to EUR 2M investment loans. Grants up to EUR 300K for specific categories.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Stacks with DFFF (German Federal Film Fund) and national incentives. FFF investment reduces DFFF qualifying basis if considered government assistance.",
        "confidence_tier": "DISCOVERY",
        "notes": "FilmFernsehFonds Bayern — Bavarian regional film fund. Regional spend obligation applies.",
    },

    "de_nrw_filmstiftung": {
        "is_repayable": True,
        "repayment_terms": "NRW Filmstiftung investment loans are repayable from receipts.",
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "Co-financing required. Significant NRW regional spend must be demonstrated.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Regional spend obligation: 150% of subsidy must be spent in NRW.",
        "eligible_formats": "feature,documentary,series,animation,game",
        "typical_max_award_usd": 2_200_000,
        "award_range_notes": "Up to EUR 2M. Germany's largest regional film fund by volume.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Stacks with DFFF federal incentive. Combined applications common. Interaction with EU MEDIA also common.",
        "confidence_tier": "DISCOVERY",
        "notes": "Film und Medienstiftung NRW — North Rhine-Westphalia regional fund. Germany's largest.",
    },

    "hk_film_dev_fund": {
        "is_repayable": True,
        "repayment_terms": "HK FDF loans are repayable from box office receipts after production cost recoupment.",
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "Majority HK creative elements required. Must demonstrate market viability.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Must be a Hong Kong film (HKSAR definition). Majority HK key creatives.",
        "eligible_formats": "feature",
        "typical_max_award_usd": 640_000,
        "award_range_notes": "Up to HKD 5M (~USD $640K) per project.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "No known interaction with international tax incentive programmes.",
        "confidence_tier": "DISCOVERY",
        "notes": "Hong Kong Film Development Fund (FDF) — Create Hong Kong administered.",
    },

    "in_nfdc_coproduction": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "International co-producer from treaty country required.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "India must be the primary territory or significant creative contributor.",
        "eligible_formats": "feature,documentary",
        "typical_max_award_usd": 75_000,
        "award_range_notes": "INR 5-10M (~USD $60K–120K). Limited annual budget for co-production development.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Development fund only. No known stacking restrictions with Indian state incentives.",
        "confidence_tier": "DISCOVERY",
        "notes": "NFDC International Co-production Development Fund — early-stage only.",
    },

    "sg_imda_film_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "Singapore producer must hold majority rights. Co-financing from distributor encouraged.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Project must be Singapore-rooted with significant Singapore creative elements.",
        "eligible_formats": "feature,documentary,animation",
        "typical_max_award_usd": 1_500_000,
        "award_range_notes": "Up to SGD 2M (~USD $1.5M) for feature productions.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Grant does not affect tax incentive treatment under EDB/IRAS schemes.",
        "confidence_tier": "DISCOVERY",
        "notes": "IMDA Singapore — Infocomm Media Development Authority feature film production grant.",
    },

    "tw_taicca_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "International co-production partner from TAICCA partner country required.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Taiwan creative elements required. Project must benefit Taiwan content ecosystem.",
        "eligible_formats": "feature,documentary,animation,series",
        "typical_max_award_usd": 750_000,
        "award_range_notes": "TWD 20M (~USD $650K) approximate maximum.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "No known restriction on stacking with co-producer country national incentives.",
        "confidence_tier": "DISCOVERY",
        "notes": "TAICCA — Taiwan Creative Content Agency. International co-production fund.",
    },

    "film_i_vast": {
        "is_repayable": True,
        "repayment_terms": "Film i Väst investment is an equity loan repayable from first receipts.",
        "is_recoupable": True,
        "recoupment_terms": "Recoups from exploitation receipts proportionally to investment.",
        "has_equity_participation": True,
        "equity_participation_notes": "Takes equity position with backend participation from global sales.",
        "has_matching_requirement": True,
        "matching_notes": "Significant regional spend in Västra Götaland (Sweden) required. Co-financing from broadcaster/distributor.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Spend multiplier: 150% of investment must be spent in Västra Götaland region.",
        "eligible_formats": "feature,documentary,series,animation",
        "typical_max_award_usd": 2_200_000,
        "award_range_notes": "SEK 20M (~USD $2M) per project. One of Europe's largest regional funds.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Stacks with Swedish national incentive and Eurimages. Film i Väst commonly appears in Eurimages co-productions.",
        "confidence_tier": "DISCOVERY",
        "notes": "Film i Väst — Swedish regional co-production fund (Västra Götaland). Major European co-producer.",
    },

    "acpfilms_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": True,
        "matching_notes": "ACP country producer must be majority rights holder. EU minority co-producer required.",
        "has_territorial_spend_requirement": True,
        "territorial_spend_notes": "Majority of production spend must occur in ACP countries.",
        "eligible_formats": "feature,documentary,animation",
        "typical_max_award_usd": 600_000,
        "award_range_notes": "EUR 200K–500K per project (USD $220K–550K).",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Stacks with national incentives in ACP countries and EU MEDIA.",
        "confidence_tier": "DISCOVERY",
        "notes": "ACP Films — EU-ACP Cultural Film Fund for African, Caribbean, Pacific filmmakers.",
    },

    "us_itvs_fund": {
        "is_repayable": False,
        "repayment_terms": None,
        "is_recoupable": False,
        "recoupment_terms": None,
        "has_equity_participation": False,
        "equity_participation_notes": None,
        "has_matching_requirement": False,
        "matching_notes": None,
        "has_territorial_spend_requirement": False,
        "territorial_spend_notes": None,
        "eligible_formats": "documentary",
        "typical_max_award_usd": 250_000,
        "award_range_notes": "USD $50K–$250K per project. Broadcast-linked documentary support.",
        "is_competitive": True,
        "stackable_with_incentives": True,
        "stackability_notes": "Non-governmental private fund. No interaction with tax credits.",
        "confidence_tier": "DISCOVERY",
        "notes": "ITVS International Documentary Fund — linked to PBS/CPB public broadcast distribution.",
    },
}


def upgrade() -> None:
    conn = op.get_bind()

    rows = []
    for slug, data in _FUND_DATA.items():
        result = conn.execute(
            sa.text("SELECT id FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if result is None:
            continue  # programme not yet seeded; skip gracefully
        program_id = result[0]
        rows.append({
            "id": _uid(slug),
            "program_id": program_id,
            **data,
        })

    if rows:
        conn.execute(
            sa.text("""
                INSERT INTO fund_economics (
                    id, program_id,
                    is_repayable, repayment_terms,
                    is_recoupable, recoupment_terms,
                    has_equity_participation, equity_participation_notes,
                    has_matching_requirement, matching_notes,
                    has_territorial_spend_requirement, territorial_spend_notes,
                    eligible_formats, typical_max_award_usd,
                    award_range_notes, is_competitive,
                    stackable_with_incentives, stackability_notes,
                    confidence_tier, notes
                ) VALUES (
                    :id, :program_id,
                    :is_repayable, :repayment_terms,
                    :is_recoupable, :recoupment_terms,
                    :has_equity_participation, :equity_participation_notes,
                    :has_matching_requirement, :matching_notes,
                    :has_territorial_spend_requirement, :territorial_spend_notes,
                    :eligible_formats, :typical_max_award_usd,
                    :award_range_notes, :is_competitive,
                    :stackable_with_incentives, :stackability_notes,
                    :confidence_tier, :notes
                )
                ON CONFLICT (id) DO NOTHING
            """),
            rows,
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug in _FUND_DATA:
        result = conn.execute(
            sa.text("SELECT id FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if result is None:
            continue
        conn.execute(
            sa.text("DELETE FROM fund_economics WHERE program_id = :pid"),
            {"pid": result[0]},
        )
