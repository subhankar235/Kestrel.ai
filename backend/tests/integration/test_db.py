"""Integration tests for DB connectivity, Alembic migrations, and schema creation."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import check_db_connection


@pytest.mark.asyncio
async def test_db_connectivity() -> None:
    await check_db_connection()


@pytest.mark.asyncio
async def test_schema_tables_exist(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as conn:
        # Check SQLite or Postgres tables exist
        res = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = {row[0] for row in res.fetchall()}
        expected = {"agents", "personas", "posts", "constitutions", "topic_debt"}
        assert expected.issubset(tables)
