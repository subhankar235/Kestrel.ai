"""Integration tests for Phase 12 API endpoints (/api/agent/init and /api/agent/feed)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Constitution, Persona, Post


@pytest.mark.asyncio
async def test_init_without_auth_401(client: AsyncClient) -> None:
    """Assert POST /api/agent/init without Auth returns 401."""
    res = await client.post("/api/agent/init", json={"persona": {"name": "Ada", "domain": "AI Security"}})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_init_invalid_body_400(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert POST /api/agent/init with malformed body returns 400."""
    async def mock_auth(token: str) -> dict[str, str]:
        return {"sub": "user_123"}

    monkeypatch.setattr("app.api.deps.verify_clerk_token", mock_auth)

    res = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer valid_token"},
        json={"invalid": "payload"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_init_happy_path_and_feed_flow(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test POST /api/agent/init happy path, DB creation, 409 duplicate check, and feed polling."""
    async def mock_auth(token: str) -> dict[str, str]:
        return {"sub": "user_123"}

    monkeypatch.setattr("app.api.deps.verify_clerk_token", mock_auth)

    # 1. First init call -> 200 OK
    init_res = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer valid_token"},
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert init_res.status_code == 200
    data = init_res.json()
    assert "agentId" in data
    agent_id = data["agentId"]
    assert agent_id.startswith("agent_")

    # 2. Verify records created in DB
    agent_res = await db_session.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = agent_res.scalar_one()
    assert agent.status == "active"

    persona_res = await db_session.execute(select(Persona).where(Persona.agent_id == agent.id))
    persona = persona_res.scalar_one()
    assert persona.name == "Ada"
    assert persona.domain == "AI Security"

    const_res = await db_session.execute(select(Constitution).where(Constitution.agent_id == agent.id))
    constitution = const_res.scalar_one()
    assert constitution.version == "1.0"
    assert constitution.is_active is True

    # 3. Second init call -> 409 Conflict (callable once)
    dup_res = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer valid_token"},
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert dup_res.status_code == 409

    # 4. Feed query for unknown agentId -> 404 Not Found
    nf_res = await client.get("/api/agent/feed?agentId=unknown-agent-id")
    assert nf_res.status_code == 404

    # 5. Feed query for newly created agentId -> 200 {"posts": []}
    feed_res = await client.get(f"/api/agent/feed?agentId={agent_id}")
    assert feed_res.status_code == 200
    assert feed_res.json() == {"posts": []}

    # 6. Insert a post and test feed returns it in reverse chronological order
    post = Post(
        post_id="p1",
        agent_id=agent.id,
        text="Autonomous AI security insights",
        rationale="Timely analysis on AI vulnerability discovery",
        sources=["https://example.com/sec-advisory"],
    )
    db_session.add(post)
    await db_session.commit()

    populated_feed_res = await client.get(f"/api/agent/feed?agentId={agent_id}")
    assert populated_feed_res.status_code == 200
    feed_data = populated_feed_res.json()
    assert "posts" in feed_data
    assert len(feed_data["posts"]) == 1
    p_out = feed_data["posts"][0]
    assert p_out["id"] == "p1"
    assert p_out["text"] == "Autonomous AI security insights"
    assert p_out["sources"] == ["https://example.com/sec-advisory"]
    assert "Z" in p_out["createdAt"]
