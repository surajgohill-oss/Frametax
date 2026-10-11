"""The isolated-record harness itself: synthetic projects roll back, and a write naming any pre-existing or anchor project is refused."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.db.session import engine
from app.models.enums import ProjectFactSourceType
from app.models.project_fact import ProjectFact
from tests.isolated_records import (
    REAL_ANCHOR_PROJECT_IDS, RealProjectWriteRefused, SYNTHETIC_TITLE_PREFIX, create_synthetic_project, isolated_session)


async def test_a_synthetic_project_is_usable_and_leaves_nothing_behind():
    async with isolated_session() as session:
        pid = await create_synthetic_project(session)
        title = (await session.execute(text("select title from projects where id = :p"), {"p": pid})).scalar_one()
        assert title.startswith(SYNTHETIC_TITLE_PREFIX)
        session.add(ProjectFact(id=uuid.uuid4(), project_id=pid, fact_key="financing_cost_usd", value="1", value_type="number",
                                source_type=ProjectFactSourceType.USER_OVERRIDE.value))
        await session.commit()                                   # savepoint release only; the outer transaction still rolls back
    async with engine.connect() as conn:
        assert (await conn.execute(text("select count(*) from projects where title like :t"), {"t": f"{SYNTHETIC_TITLE_PREFIX}%"})).scalar() == 0
        assert (await conn.execute(text("select count(*) from project_facts where project_id = :p"), {"p": pid})).scalar() == 0


@pytest.mark.parametrize("anchor", sorted(REAL_ANCHOR_PROJECT_IDS))
async def test_a_write_naming_an_anchor_production_is_refused(anchor):
    async with isolated_session() as session:
        session.add(ProjectFact(id=uuid.uuid4(), project_id=anchor, fact_key="financing_cost_usd", value="1", value_type="number",
                                source_type=ProjectFactSourceType.USER_OVERRIDE.value))
        with pytest.raises(Exception) as refused:                 # surfaces as a wrapped DBAPI error on flush
            await session.flush()
        assert "RealProjectWriteRefused" in repr(refused.value) or "refused a write" in str(refused.value)


async def test_a_write_naming_any_pre_existing_project_is_refused_and_a_read_is_not():
    async with isolated_session() as session:
        existing = (await session.execute(text("select id from projects limit 1"))).scalar()
        if existing is None:
            pytest.skip("the test database has no pre-existing project to protect")
        await session.execute(text("select * from project_facts where project_id = :p"), {"p": str(existing)})   # reads are allowed
        with pytest.raises(Exception) as refused:
            await session.execute(text("delete from project_facts where project_id = :p"), {"p": str(existing)})
        assert "refused a write" in str(refused.value)
