"""Phase 24 integration coverage for API and accept/reject persistence paths."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.editorial.judge import judge_topic_score
from app.editorial.scorer import score_candidate_topic
from app.editorial.topic_debt import log_rejected_topic
from app.models.agent import Agent
from app.models.post import Post
from app.models.topic_debt import TopicDebt
from app.publishing.publisher import publish_final_post


async def _mock_auth(token: str) -> dict[str, str]:
    return {"sub": "integration-user"}


async def _init_agent(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "Ada",
    domain: str = "AI Security",
) -> str:
    monkeypatch.setattr("app.api.deps.verify_clerk_token", _mock_auth)
    monkeypatch.setattr(
        "app.workflows.schedules.create_agent_schedule",
        AsyncMock(return_value="schedule_test"),
    )
    response = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer integration-token"},
        json={"persona": {"name": name, "domain": domain}},
    )
    assert response.status_code == 200, response.text
    return response.json()["agentId"]


@pytest.mark.asyncio
async def test_init_happy_path_and_double_init_conflict(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Init creates the agent once and rejects the second initialization."""
    agent_id = await _init_agent(client, monkeypatch)

    duplicate = await client.post(
        "/api/agent/init",
        headers={"Authorization": "Bearer integration-token"},
        json={"persona": {"name": "Another", "domain": "Robotics"}},
    )
    assert duplicate.status_code == 409
    assert agent_id.startswith("agent_")


@pytest.mark.asyncio
async def test_init_missing_auth_returns_401(client: AsyncClient) -> None:
    """The protected init route rejects requests without a bearer token."""
    response = await client.post(
        "/api/agent/init",
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_feed_empty_and_unknown_agent_cases(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new agent has an empty feed; an unknown agent returns 404."""
    agent_id = await _init_agent(client, monkeypatch)

    empty = await client.get("/api/agent/feed", params={"agentId": agent_id})
    assert empty.status_code == 200
    assert empty.json() == {"posts": []}

    unknown = await client.get("/api/agent/feed", params={"agentId": "agent_missing"})
    assert unknown.status_code == 404


@pytest.mark.asyncio
async def test_feed_happy_path_returns_published_post(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A persisted post is visible through the public feed endpoint."""
    agent_id = await _init_agent(client, monkeypatch)
    agent = (
        await db_session.execute(select(Agent).where(Agent.agent_id == agent_id))
    ).scalar_one()
    db_session.add(
        Post(
            post_id="p_integration_1",
            agent_id=agent.id,
            text="Evidence-backed security update",
            rationale="Selected after editorial review",
            sources=["https://example.com/advisory"],
        )
    )
    await db_session.commit()

    response = await client.get("/api/agent/feed", params={"agentId": agent_id})
    assert response.status_code == 200
    assert response.json()["posts"] == [
        {
            "id": "p_integration_1",
            "createdAt": response.json()["posts"][0]["createdAt"],
            "text": "Evidence-backed security update",
            "rationale": "Selected after editorial review",
            "sources": ["https://example.com/advisory"],
        }
    ]


@pytest.mark.asyncio
async def test_reject_path_persists_topic_debt_and_no_post(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A below-threshold candidate is logged as debt and never published."""
    agent_id = await _init_agent(client, monkeypatch)
    topic = {
        "title": "Unverified Security Rumor",
        "summary": "A claim without supporting evidence.",
        "sources": [],
    }
    low_scores = {
        "relevance_score": 20.0,
        "novelty_score": 20.0,
        "evidence_score": 10.0,
        "persona_fit_score": 20.0,
        "hype_penalty": 5.0,
        "repetition_penalty": 0.0,
        "reasoning": "Insufficient evidence",
    }
    with patch("app.editorial.scorer.generate_structured_output", return_value=low_scores):
        scores = await score_candidate_topic(topic, {}, {})
    accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
    assert accepted is False

    await log_rejected_topic(
        {**topic, "score": scores["total_score"]},
        reason=reason,
        agent_id=agent_id,
        db=db_session,
    )

    debt_count = await db_session.scalar(select(func.count()).select_from(TopicDebt))
    post_count = await db_session.scalar(select(func.count()).select_from(Post))
    debt = (await db_session.execute(select(TopicDebt))).scalar_one()
    assert debt_count == 1
    assert post_count == 0
    assert debt.topic_title == topic["title"]
    assert debt.status == "open"


@pytest.mark.asyncio
async def test_accept_path_persists_post_visible_in_feed(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An accepted candidate produces a post that the feed endpoint returns."""
    agent_id = await _init_agent(client, monkeypatch)
    topic = {
        "title": "Verified Model Supply-Chain Advisory",
        "summary": "Multiple independent sources confirm the finding.",
        "sources": ["https://example.com/research"],
    }
    high_scores = {
        "relevance_score": 90.0,
        "novelty_score": 85.0,
        "evidence_score": 95.0,
        "persona_fit_score": 90.0,
        "hype_penalty": 0.0,
        "repetition_penalty": 0.0,
        "reasoning": "Well-supported and timely",
    }
    with patch("app.editorial.scorer.generate_structured_output", return_value=high_scores):
        scores = await score_candidate_topic(topic, {}, {})
    accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
    assert accepted is True

    published = await publish_final_post(
        agent_id=agent_id,
        draft={
            "post_text": "A verified supply-chain advisory with concrete mitigations.",
            "sources": topic["sources"],
        },
        topic=topic,
        rationale=reason,
        db_session=db_session,
    )

    response = await client.get("/api/agent/feed", params={"agentId": agent_id})
    assert response.status_code == 200
    posts = response.json()["posts"]
    assert len(posts) == 1
    assert posts[0]["id"] == published["post_id"]
    assert posts[0]["text"] == "A verified supply-chain advisory with concrete mitigations."
    assert posts[0]["sources"] == topic["sources"]
    assert await db_session.scalar(select(func.count()).select_from(TopicDebt)) == 0
