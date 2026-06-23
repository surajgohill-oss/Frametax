"""0048 — Seed bilateral co-production treaties.

Seeds ~25 high-priority bilateral treaties used by the treaty intelligence
layer. Covers UK, Canada, France, Australia, Germany, Ireland, and New Zealand
as majority partners. All records seeded at PARSED confidence.

Revision ID: 0048
Revises: 0047
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: Union[str, None] = "0047"
branch_labels = None
depends_on = None

# fmt: off
_TREATIES = [
    # -------------------------------------------------------------------------
    # UK bilateral treaties
    # -------------------------------------------------------------------------
    {
        "treaty_name": "UK–Canada Co-production Treaty",
        "treaty_slug": "uk-ca-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "CA",
        "year_signed": 1975,
        "effective_from": "1975-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Budget allocation must reflect each party's creative contribution. "
            "UK spend qualifies for UK tax reliefs; Canadian spend qualifies for "
            "Canadian federal and provincial incentives."
        ),
        "nationality_requirement": (
            "Key creative personnel (director, writer, lead cast) must include nationals "
            "of both treaty countries proportionate to each party's contribution."
        ),
        "creative_contribution_requirement": (
            "Each co-producer must contribute meaningful creative input including "
            "story, script, or principal creative elements."
        ),
        "cultural_test_required": False,
        "ownership_requirement": (
            "Copyright ownership shared proportional to financial contribution. "
            "Separate exploitation rights by territory permitted."
        ),
        "majority_jurisdiction_benefits": (
            "Majority UK co-producer qualifies for AVEC (up to 40%), BFI Film Fund, "
            "BBC Films, Film4. Production treated as British for all UK relief purposes."
        ),
        "minority_jurisdiction_benefits": (
            "Minority Canadian co-producer qualifies for CPTC (up to 25%), CMF, "
            "provincial credits. Treated as Canadian content for broadcasting purposes."
        ),
        "treaty_administrator_name": "British Film Commission / Telefilm Canada",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": "One of UK's oldest and most-used bilateral treaties.",
    },
    {
        "treaty_name": "UK–Australia Co-production Treaty",
        "treaty_slug": "uk-au-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "AU",
        "year_signed": 1990,
        "effective_from": "1990-07-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Each co-producer responsible for spend in their own territory. "
            "Minimum 20% of budget must be spent in each party's territory."
        ),
        "nationality_requirement": (
            "Key creative personnel from both countries. Minimum two Australian "
            "key creatives; minimum two UK key creatives."
        ),
        "creative_contribution_requirement": (
            "Both parties must make genuine creative contributions to the production."
        ),
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to financial contribution.",
        "majority_jurisdiction_benefits": (
            "UK-majority production qualifies for AVEC, BFI Fund, Film4. "
            "Treated as British for BBC/Channel 4 commissioning."
        ),
        "minority_jurisdiction_benefits": (
            "Australian co-producer qualifies for Producer Offset (40% feature / 20% TV), "
            "Screen Australia development and production funding."
        ),
        "treaty_administrator_name": "British Film Commission / Screen Australia",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "UK–France Co-production Treaty",
        "treaty_slug": "uk-fr-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "FR",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Budget allocation proportional to creative contribution. "
            "French spend qualifies for tax crédit cinéma; UK spend for AVEC."
        ),
        "nationality_requirement": (
            "Director or writer must be UK or French national. "
            "Principal cast must include nationals from both countries."
        ),
        "creative_contribution_requirement": (
            "Both parties must provide substantive creative input. "
            "Director, writer, or lead performer nationality conditions apply."
        ),
        "cultural_test_required": True,
        "ownership_requirement": "Shared copyright; separate territorial distribution rights.",
        "majority_jurisdiction_benefits": (
            "UK-majority qualifies for AVEC (20–40%), BFI Fund, Film4, BBC Films."
        ),
        "minority_jurisdiction_benefits": (
            "French co-producer qualifies for tax crédit cinéma (30%), SOFICA, "
            "CNC selective aid (COSIP), and Canal+ commissioning terms."
        ),
        "treaty_administrator_name": "British Film Commission / CNC",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": "Cultural test requirement applies to French side only.",
    },
    {
        "treaty_name": "UK–Germany Co-production Treaty",
        "treaty_slug": "uk-de-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "DE",
        "year_signed": 1975,
        "effective_from": "1975-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "German spend qualifies for DFFF and regional German funds; "
            "UK spend qualifies for AVEC."
        ),
        "nationality_requirement": (
            "Key creative personnel from both countries required. "
            "At minimum director or lead writer from each party."
        ),
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to financial contribution.",
        "majority_jurisdiction_benefits": (
            "Majority UK production qualifies for AVEC, BFI Fund."
        ),
        "minority_jurisdiction_benefits": (
            "German co-producer qualifies for DFFF (up to 20% of German qualifying spend), "
            "FFA, and Länder-level funds (FFF Bayern, Medienboard, etc.)."
        ),
        "treaty_administrator_name": "British Film Commission / FFA",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "UK–New Zealand Co-production Treaty",
        "treaty_slug": "uk-nz-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "NZ",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": (
            "Key creative personnel from both countries."
        ),
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to contribution.",
        "majority_jurisdiction_benefits": "UK-majority qualifies for AVEC.",
        "minority_jurisdiction_benefits": (
            "New Zealand co-producer qualifies for NZSPG-International (20% of NZ qualifying spend)."
        ),
        "treaty_administrator_name": "British Film Commission / NZ Film Commission",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "UK–South Africa Co-production Treaty",
        "treaty_slug": "uk-za-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "ZA",
        "year_signed": 2007,
        "effective_from": "2007-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "UK-majority qualifies for AVEC.",
        "minority_jurisdiction_benefits": (
            "South African co-producer may qualify for NFVF funding and local DTI incentives."
        ),
        "treaty_administrator_name": "British Film Commission / NFVF",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "UK–India Co-production Treaty",
        "treaty_slug": "uk-in-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "IN",
        "year_signed": 2008,
        "effective_from": "2008-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "UK-majority qualifies for AVEC.",
        "minority_jurisdiction_benefits": (
            "Indian co-producer qualifies as official co-production for certification purposes."
        ),
        "treaty_administrator_name": "British Film Commission / Films Division of India",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "UK–Ireland Co-production Treaty",
        "treaty_slug": "uk-ie-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "GB",
        "jurisdiction_b_code": "IE",
        "year_signed": 1989,
        "effective_from": "1989-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "UK spend qualifies for AVEC; Irish spend qualifies for Section 481."
        ),
        "nationality_requirement": None,
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to contribution.",
        "majority_jurisdiction_benefits": "Qualifies for AVEC; BFI, Film4 access.",
        "minority_jurisdiction_benefits": (
            "Irish co-producer qualifies for Section 481 (32% on Irish qualifying spend), "
            "Screen Ireland development and production funds."
        ),
        "treaty_administrator_name": "British Film Commission / Screen Ireland",
        "authority_url": "https://www.bfi.org.uk/supporting-uk-film/production-and-development-funding/co-production-treaties",
        "confidence_tier": "PARSED",
        "notes": "UK-Ireland proximity makes this a very common structure.",
    },
    # -------------------------------------------------------------------------
    # Canada bilateral treaties
    # -------------------------------------------------------------------------
    {
        "treaty_name": "Canada–France Co-production Treaty",
        "treaty_slug": "ca-fr-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "FR",
        "year_signed": 1983,
        "effective_from": "1983-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Canadian spend qualifies for CPTC and CMF; French spend for tax crédit cinéma."
        ),
        "nationality_requirement": (
            "Director or writer must be Canadian or French. "
            "Francophone Canadian productions benefit from Québec co-production status."
        ),
        "creative_contribution_requirement": (
            "Both parties must provide substantive creative input. "
            "QPRDP (Québec) applies where French co-producer is involved."
        ),
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright; territorial distribution rights separated.",
        "majority_jurisdiction_benefits": (
            "Canada-majority qualifies for CPTC (25%), CMF, provincial credits "
            "(OPSTC, QPRDP, BCPTC). Treated as Canadian content."
        ),
        "minority_jurisdiction_benefits": (
            "French co-producer qualifies for tax crédit cinéma (30%), CNC COSIP, SOFICA."
        ),
        "treaty_administrator_name": "Telefilm Canada / CNC",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": "Québec productions particularly benefit via QPRDP + CNC stacking.",
    },
    {
        "treaty_name": "Canada–Australia Co-production Treaty",
        "treaty_slug": "ca-au-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "AU",
        "year_signed": 1990,
        "effective_from": "1990-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to contribution.",
        "majority_jurisdiction_benefits": (
            "Canada-majority qualifies for CPTC, CMF, provincial credits."
        ),
        "minority_jurisdiction_benefits": (
            "Australian co-producer qualifies for Producer Offset (40% feature / 20% TV)."
        ),
        "treaty_administrator_name": "Telefilm Canada / Screen Australia",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Germany Co-production Treaty",
        "treaty_slug": "ca-de-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "DE",
        "year_signed": 1987,
        "effective_from": "1987-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": "German co-producer qualifies for DFFF, FFA, Länder funds.",
        "treaty_administrator_name": "Telefilm Canada / FFA",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Italy Co-production Treaty",
        "treaty_slug": "ca-it-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "IT",
        "year_signed": 1989,
        "effective_from": "1989-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": "Italian co-producer qualifies for MiC tax credit.",
        "treaty_administrator_name": "Telefilm Canada / MiC",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Spain Co-production Treaty",
        "treaty_slug": "ca-es-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "ES",
        "year_signed": 1985,
        "effective_from": "1985-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "Spanish co-producer qualifies for ICAA tax deductions and regional funds."
        ),
        "treaty_administrator_name": "Telefilm Canada / ICAA",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–South Africa Co-production Treaty",
        "treaty_slug": "ca-za-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "ZA",
        "year_signed": 1997,
        "effective_from": "1997-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": "South African co-producer may qualify for NFVF and DTI incentives.",
        "treaty_administrator_name": "Telefilm Canada / NFVF",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Ireland Co-production Treaty",
        "treaty_slug": "ca-ie-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "IE",
        "year_signed": 1989,
        "effective_from": "1989-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "Canadian spend qualifies for CPTC; Irish spend qualifies for Section 481."
        ),
        "nationality_requirement": None,
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright proportional to contribution.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "Irish co-producer qualifies for Section 481 (32% on Irish qualifying spend)."
        ),
        "treaty_administrator_name": "Telefilm Canada / Screen Ireland",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–New Zealand Co-production Treaty",
        "treaty_slug": "ca-nz-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "NZ",
        "year_signed": 1994,
        "effective_from": "1994-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "New Zealand co-producer qualifies for NZSPG-International (20% of NZ qualifying spend)."
        ),
        "treaty_administrator_name": "Telefilm Canada / NZ Film Commission",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–China Co-production Treaty",
        "treaty_slug": "ca-cn-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "CN",
        "year_signed": 1987,
        "effective_from": "1987-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "Chinese co-producer qualifies as official co-production for China quota exemption purposes."
        ),
        "treaty_administrator_name": "Telefilm Canada / NRTA",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": "Quota exemption is the primary benefit for Chinese partner.",
    },
    {
        "treaty_name": "Canada–Switzerland Co-production Treaty",
        "treaty_slug": "ca-ch-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "CH",
        "year_signed": 1988,
        "effective_from": "1988-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "Swiss co-producer qualifies for MEDIA Suisse / BAK federal support."
        ),
        "treaty_administrator_name": "Telefilm Canada / BAK",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Belgium Co-production Treaty",
        "treaty_slug": "ca-be-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "BE",
        "year_signed": 1984,
        "effective_from": "1984-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": (
            "Belgian co-producer qualifies for tax shelter (30% of qualifying spend), "
            "VAF (Flanders), Centre du Cinéma (Wallonia)."
        ),
        "treaty_administrator_name": "Telefilm Canada / Screen Flanders / Centre du Cinéma",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Canada–Mexico Co-production Treaty",
        "treaty_slug": "ca-mx-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "CA",
        "jurisdiction_b_code": "MX",
        "year_signed": 1999,
        "effective_from": "1999-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": "Canada-majority qualifies for CPTC, CMF.",
        "minority_jurisdiction_benefits": "Mexican co-producer qualifies for IMCINE support.",
        "treaty_administrator_name": "Telefilm Canada / IMCINE",
        "authority_url": "https://telefilm.ca/en/co-production",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    # -------------------------------------------------------------------------
    # Australia bilateral treaties
    # -------------------------------------------------------------------------
    {
        "treaty_name": "Australia–Germany Co-production Treaty",
        "treaty_slug": "au-de-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "DE",
        "year_signed": 2001,
        "effective_from": "2001-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "Australian-majority qualifies for Producer Offset (40% feature)."
        ),
        "minority_jurisdiction_benefits": (
            "German co-producer qualifies for DFFF, FFA, Länder funds."
        ),
        "treaty_administrator_name": "Screen Australia / FFA",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Australia–Ireland Co-production Treaty",
        "treaty_slug": "au-ie-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "IE",
        "year_signed": 2008,
        "effective_from": "2008-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "Australian-majority qualifies for Producer Offset (40% feature)."
        ),
        "minority_jurisdiction_benefits": (
            "Irish co-producer qualifies for Section 481 (32%)."
        ),
        "treaty_administrator_name": "Screen Australia / Screen Ireland",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Australia–Italy Co-production Treaty",
        "treaty_slug": "au-it-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "IT",
        "year_signed": 2009,
        "effective_from": "2009-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "Australian-majority qualifies for Producer Offset (40% feature)."
        ),
        "minority_jurisdiction_benefits": "Italian co-producer qualifies for MiC tax credit.",
        "treaty_administrator_name": "Screen Australia / MiC",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    {
        "treaty_name": "Australia–South Korea Co-production Treaty",
        "treaty_slug": "au-kr-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "AU",
        "jurisdiction_b_code": "KR",
        "year_signed": 2006,
        "effective_from": "2006-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "20.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "80.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": None,
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": False,
        "ownership_requirement": "Shared copyright.",
        "majority_jurisdiction_benefits": (
            "Australian-majority qualifies for Producer Offset (40% feature)."
        ),
        "minority_jurisdiction_benefits": "Korean co-producer qualifies for KOFIC support.",
        "treaty_administrator_name": "Screen Australia / KOFIC",
        "authority_url": "https://www.screenaustralia.gov.au/funding-and-support/co-productions",
        "confidence_tier": "PARSED",
        "notes": None,
    },
    # -------------------------------------------------------------------------
    # France bilateral treaties
    # -------------------------------------------------------------------------
    {
        "treaty_name": "France–Germany Co-production Treaty",
        "treaty_slug": "fr-de-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "FR",
        "jurisdiction_b_code": "DE",
        "year_signed": 2001,
        "effective_from": "2001-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "French spend qualifies for tax crédit cinéma; German spend for DFFF and Länder funds."
        ),
        "nationality_requirement": "Key creative personnel from both countries.",
        "creative_contribution_requirement": None,
        "cultural_test_required": True,
        "ownership_requirement": "Shared copyright; territorial rights separated.",
        "majority_jurisdiction_benefits": (
            "French-majority qualifies for tax crédit cinéma (30%), CNC COSIP, SOFICA, Canal+."
        ),
        "minority_jurisdiction_benefits": (
            "German co-producer qualifies for DFFF, FFA, Medienboard, FFF Bayern."
        ),
        "treaty_administrator_name": "CNC / FFA",
        "authority_url": "https://www.cnc.fr/professionnels/aides/international",
        "confidence_tier": "PARSED",
        "notes": "Most common continental European bilateral structure.",
    },
    {
        "treaty_name": "France–Belgium Co-production Treaty",
        "treaty_slug": "fr-be-bilateral",
        "treaty_type": "bilateral",
        "status": "active",
        "jurisdiction_a_code": "FR",
        "jurisdiction_b_code": "BE",
        "year_signed": 1965,
        "effective_from": "1965-01-01",
        "effective_until": None,
        "majority_min_contribution_pct": "30.00",
        "minority_min_contribution_pct": "20.00",
        "minority_max_contribution_pct": "70.00",
        "min_coproducer_countries": 2,
        "spend_allocation_requirement": (
            "French spend qualifies for tax crédit cinéma; Belgian spend for tax shelter."
        ),
        "nationality_requirement": None,
        "creative_contribution_requirement": None,
        "cultural_test_required": True,
        "ownership_requirement": "Shared copyright; territorial rights separated.",
        "majority_jurisdiction_benefits": (
            "French-majority qualifies for tax crédit cinéma (30%), CNC, SOFICA."
        ),
        "minority_jurisdiction_benefits": (
            "Belgian co-producer qualifies for tax shelter (30%), VAF, Centre du Cinéma."
        ),
        "treaty_administrator_name": "CNC / Centre du Cinéma de la FWB",
        "authority_url": "https://www.cnc.fr/professionnels/aides/international",
        "confidence_tier": "PARSED",
        "notes": "France-Wallonia structure is very common for francophone European co-productions.",
    },
]
# fmt: on


def upgrade() -> None:
    conn = op.get_bind()
    for t in _TREATIES:
        conn.execute(
            sa.text(
                """
                INSERT INTO co_production_treaties (
                    treaty_name, treaty_slug, treaty_type, status,
                    jurisdiction_a_code, jurisdiction_b_code,
                    year_signed, effective_from, effective_until,
                    majority_min_contribution_pct, minority_min_contribution_pct,
                    minority_max_contribution_pct, min_coproducer_countries,
                    spend_allocation_requirement, nationality_requirement,
                    creative_contribution_requirement, cultural_test_required,
                    ownership_requirement,
                    majority_jurisdiction_benefits, minority_jurisdiction_benefits,
                    treaty_administrator_name, authority_url,
                    confidence_tier, notes
                ) VALUES (
                    :treaty_name, :treaty_slug, :treaty_type, :status,
                    :jurisdiction_a_code, :jurisdiction_b_code,
                    :year_signed, :effective_from, :effective_until,
                    :majority_min_contribution_pct, :minority_min_contribution_pct,
                    :minority_max_contribution_pct, :min_coproducer_countries,
                    :spend_allocation_requirement, :nationality_requirement,
                    :creative_contribution_requirement, :cultural_test_required,
                    :ownership_requirement,
                    :majority_jurisdiction_benefits, :minority_jurisdiction_benefits,
                    :treaty_administrator_name, :authority_url,
                    :confidence_tier, :notes
                )
                ON CONFLICT (treaty_slug) DO NOTHING
                """
            ),
            t,
        )


def downgrade() -> None:
    conn = op.get_bind()
    slugs = [t["treaty_slug"] for t in _TREATIES]
    for slug in slugs:
        conn.execute(
            sa.text("DELETE FROM co_production_treaties WHERE treaty_slug = :slug"),
            {"slug": slug},
        )
