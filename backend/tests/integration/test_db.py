"""Integration tests for DB connectivity, Alembic migrations, and schema creation."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import check_db_connection


@pytest.mark.asyncio
async def test_db_connectivity() -> None:
    await check_db_connection()


@pytest.mark.asyncio
async def test_schema_tables_exist(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    expected = {"agents", "personas", "posts", "constitutions", "topic_debt"}
    assert expected.issubset(tables)
