"""Unit tests for SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Constitution, Persona, Post, TopicDebt


@pytest.mark.asyncio
async def test_agent_model_persistence(db_session: AsyncSession) -> None:
    agent = Agent(
        agent_id="test-agent-123",
        status="active",
        temporal_workflow_id="wf-12345",
    )
    db_session.add(agent)
    await db_session.commit()

    result = await db_session.execute(select(Agent).where(Agent.agent_id == "test-agent-123"))
    saved_agent = result.scalar_one_or_none()

    assert saved_agent is not None
    assert isinstance(saved_agent.id, uuid.UUID)
    assert saved_agent.status == "active"
    assert saved_agent.temporal_workflow_id == "wf-12345"


@pytest.mark.asyncio
async def test_all_models_relationships(db_session: AsyncSession) -> None:
    # Create agent
    agent = Agent(agent_id="agent-rel-1")
    db_session.add(agent)
    await db_session.flush()

    # Create persona
    persona = Persona(
        agent_id=agent.id,
        name="Ada",
        domain="AI Security",
        voice_config={"tone": "analytical", "style": "sharp"},
    )
    # Create constitution
    constitution = Constitution(
        agent_id=agent.id,
        version="1.0",
        rules={"relevance_threshold": 60.0},
        is_active=True,
    )
    # Create post 1
    post1 = Post(
        post_id="p1",
        agent_id=agent.id,
        text="AI safety initial thoughts",
        rationale="Timely analysis",
        sources=["https://example.com/source1"],
    )
    db_session.add_all([persona, constitution, post1])
    await db_session.flush()

    # Create post 2 linked to post 1
    post2 = Post(
        post_id="p2",
        agent_id=agent.id,
        text="AI safety follow up",
        rationale="Story continuation",
        sources=["https://example.com/source2"],
        related_post_id=post1.id,
        relationship="STORY_CONTINUATION",
    )
    # Create topic debt
    topic_debt = TopicDebt(
        agent_id=agent.id,
        topic_title="Low quality claim",
        topic_summary="Unverified rumors about AI model release",
        score=35.0,
        rejection_reason="Below cutoff score",
        revisit_condition="Wait for official confirmation",
        status="open",
    )
    db_session.add_all([post2, topic_debt])
    await db_session.commit()

    # Query agent with eager load / check relationships
    res = await db_session.execute(select(Agent).where(Agent.id == agent.id))
    fetched_agent = res.scalar_one()

    assert len(fetched_agent.personas) == 1
    assert fetched_agent.personas[0].name == "Ada"

    assert len(fetched_agent.constitutions) == 1
    assert fetched_agent.constitutions[0].version == "1.0"

    assert len(fetched_agent.posts) == 2
    assert len(fetched_agent.topic_debts) == 1
    assert fetched_agent.topic_debts[0].score == 35.0

    # Query post2 and check related post relationship
    res_p2 = await db_session.execute(select(Post).where(Post.post_id == "p2"))
    fetched_p2 = res_p2.scalar_one()
    assert fetched_p2.related_post_id == post1.id
    assert fetched_p2.relationship == "STORY_CONTINUATION"
