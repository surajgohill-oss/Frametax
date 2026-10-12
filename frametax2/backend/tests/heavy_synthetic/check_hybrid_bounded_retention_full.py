"""HEAVY synthetic check (explicit path; deliberately outside the default suite and NOT a skipped test): the UNBOUNDED hybrid production whose real search enumerates
hundreds of thousands of candidates (minutes; it exceeded 640 s here). It measures its own legacy enumeration (the same shared body as the bounded default test), so it carries
no pinned counts that could go stale.

    DATABASE_URL unset  python -m pytest tests/heavy_synthetic/check_hybrid_bounded_retention_full.py -q"""
from __future__ import annotations

import pytest

from tests.test_served_contract_bounded import assert_hybrid_bounded_retention, db, isolated_hybrid_project  # noqa: F401  (fixtures)

pytestmark = pytest.mark.asyncio


async def test_unbounded_hybrid_production_bounded_retention_matches_its_own_legacy_enumeration(db, isolated_hybrid_project, monkeypatch):
    await assert_hybrid_bounded_retention(db, isolated_hybrid_project, monkeypatch, restrict=False)
