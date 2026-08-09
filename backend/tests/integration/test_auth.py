"""Phase 10 — Authentication and authorization integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_init_without_token_returns_401(client: AsyncClient) -> None:
    """Assert POST /api/agent/init without Authorization header returns 401."""
    response = await client.post(
        "/api/agent/init",
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_init_with_invalid_token_returns_401(client: AsyncClient) -> None:
    """Assert POST /api/agent/init with an invalid bearer token returns 401."""
    response = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer invalid_malformed_token"},
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_init_with_valid_token_returns_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert POST /api/agent/init with a valid token returns 200."""
    async def mock_verify(token: str) -> dict[str, str]:
        assert token == "valid_mock_token"
        return {"sub": "user_clerk_123", "email": "test@example.com"}

    monkeypatch.setattr("app.api.deps.verify_clerk_token", mock_verify)

    response = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer valid_mock_token"},
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "agentId" in data


@pytest.mark.asyncio
async def test_feed_without_token_returns_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert GET /api/agent/feed is accessible without auth (evaluator polling contract)."""
    async def mock_verify(token: str) -> dict[str, str]:
        return {"sub": "user_clerk_123"}

    monkeypatch.setattr("app.api.deps.verify_clerk_token", mock_verify)

    # 1. Create an agent via init
    init_res = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer valid_mock_token"},
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert init_res.status_code == 200
    agent_id = init_res.json()["agentId"]

    # 2. Feed query without token returns 200 {"posts": []}
    response = await client.get(f"/api/agent/feed?agentId={agent_id}")
    assert response.status_code == 200
    assert response.json() == {"posts": []}

    # 3. Feed query for unknown agentId without token returns 404
    nf_response = await client.get("/api/agent/feed?agentId=unknown_agent")
    assert nf_response.status_code == 404
