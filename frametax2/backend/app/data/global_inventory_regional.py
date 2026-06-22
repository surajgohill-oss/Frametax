"""
global_inventory_regional.py

Phase D — Regional/subnational fund programs.
Five new sub-national/regional programs not captured in existing waves.

All entries are DISCOVERY tier.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"

REGIONAL_PROGRAMS: list[GlobalProgramEntry] = [

    GlobalProgramEntry(
        jurisdiction_code="GB-NIR",
        jurisdiction_name="Northern Ireland (United Kingdom)",
        program_name="Northern Ireland Screen — Production Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_200_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Northern Ireland Screen — Production Fund guidelines",
        source_url="https://www.northernirelandscreen.co.uk/funding/production/",
        effective_from="1997-01-01",
        notes=(
            "Northern Ireland Screen (NIS) funds film and TV productions in Northern Ireland. "
            "Grants up to GBP 1M per project (~USD 1.2M). Regional spend obligation applies. "
            "Stacks with UK AVEC (separate national incentive). DISCOVERY tier."
        ),
        unknown_fields=["exact_grant_ceiling", "regional_spend_multiplier", "cultural_test_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE-MDM",
        jurisdiction_name="Mitteldeutschland (Germany — Saxony/Saxony-Anhalt/Thuringia)",
        program_name="Mitteldeutsche Medienförderung (MDM) — Film Production Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=2_200_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="MDM Mitteldeutsche Medienförderung — Film production support",
        source_url="https://www.mdm-online.de/",
        effective_from="1998-01-01",
        notes=(
            "MDM supports film and TV productions in central Germany (Saxony, Saxony-Anhalt, Thuringia). "
            "Investment loans up to EUR 2M per project. Regional spend obligation: 150% of loan. "
            "Stacks with DFFF federal fund. DISCOVERY tier."
        ),
        unknown_fields=["exact_loan_ceiling", "spend_multiplier", "repayment_terms"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT-APU",
        jurisdiction_name="Apulia Region (Italy)",
        program_name="Apulia Film Commission — Film Fund",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Apulia Film Commission — Funding programs",
        source_url="https://www.apuliafilmcommission.it/funding/",
        effective_from="2007-01-01",
        notes=(
            "Apulia Film Commission provides production incentives for shoots in Puglia region. "
            "Grants up to EUR 500K per project. No cultural test for international productions. "
            "Stacks with Italian national tax credit for foreign productions. DISCOVERY tier."
        ),
        unknown_fields=["exact_grant_ceiling", "minimum_local_spend", "application_rounds"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IT-PIE",
        jurisdiction_name="Piedmont Region (Italy)",
        program_name="Film Commission Torino Piemonte — Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=660_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film Commission Torino Piemonte — Production incentives",
        source_url="https://www.fctp.it/incentives/",
        effective_from="2000-01-01",
        notes=(
            "Torino Piemonte Film Commission supports productions in the Piedmont region. "
            "Grants up to EUR 600K per project. Minimum regional spend required. "
            "Stacks with Italian national tax credit. Turin has significant studio infrastructure. DISCOVERY tier."
        ),
        unknown_fields=["exact_grant_ceiling", "minimum_local_spend", "cultural_test_required"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ES-EUS",
        jurisdiction_name="Basque Country (Spain)",
        program_name="Basque Audiovisual — Eusko Jaurlaritza Film Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Basque Government — Audiovisual production support",
        source_url="https://www.kultura.ejgv.euskadi.eus/",
        effective_from="2004-01-01",
        notes=(
            "Basque Country (Euskadi) film production fund administered by Eusko Jaurlaritza. "
            "Grants up to EUR 500K for qualifying Basque productions. "
            "Basque content or language requirement. Stacks with Spanish national rebate (20%). "
            "Canary Islands rebate (50%) separate programme. DISCOVERY tier."
        ),
        unknown_fields=["exact_grant_ceiling", "basque_content_criteria", "application_deadlines"],
    ),
]
