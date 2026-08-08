"""Async SQLAlchemy engine/session factory for FastAPI routes and workers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine_kwargs: dict[str, Any] = {
    "echo": False,
    "pool_pre_ping": True,
}

if "sqlite" in settings.DATABASE_URL:
    from sqlalchemy.pool import StaticPool

    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool
    engine_kwargs["pool_pre_ping"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession; closes it on request end."""
    async with SessionLocal() as session:
        yield session


async def check_db_connection() -> None:
    """Verify database connectivity at startup; raises on failure."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))