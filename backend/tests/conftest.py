"""Shared pytest fixtures."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "local"
os.environ["SENTRY_DSN"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["OPENROUTER_MODEL"] = ""
os.environ["OPENAI_BASE_URL"] = ""
os.environ["BREETH_API_KEY"] = ""
os.environ["EXA_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""
os.environ["GITHUB_TOKEN"] = ""

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.db import base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_engine():
    engine_kwargs = {}
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    engine = create_async_engine(TEST_DATABASE_URL, **engine_kwargs)
    async with engine.begin() as conn:
        await conn.run_sync(base.Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def mock_check_db_connection(monkeypatch):
    async def _mock():
        return None

    monkeypatch.setattr("app.main.check_db_connection", _mock)


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
