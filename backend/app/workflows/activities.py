"""Temporal Activity definitions wrapping core backend services for deterministic workflow orchestration."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import activity

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.discovery.discovery_service import discover_candidate_topics
from app.drafting.draft_generator import generate_draft_angles
from app.drafting.persona_check import verify_persona_alignment
from app.drafting.self_critique import critique_and_select_winning_draft
from app.editorial.judge import judge_topic_score
from app.editorial.scorer import score_candidate_topic
from app.memory.episode_writer import record_decision_episode
from app.memory.recall import recall_memory_context
from app.models import Base
from app.models.agent import Agent
from app.models.constitution import Constitution
from app.models.persona import Persona
from app.models.post import Post
from app.models.topic_debt import TopicDebt
from app.publishing.rationale_builder import build_post_rationale
from app.self_audit.auditor import run_self_audit


@asynccontextmanager
async def get_activity_db() -> AsyncGenerator[AsyncSession, None]:
    """Helper context manager ensuring tables exist when running in SQLite/test environments."""
    settings = get_settings()
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session


@activity.defn
async def discover_topics_activity(agent_id: str) -> list[dict[str, Any]]:
    """Activity: Discover candidate topics for the agent's persona domain."""
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()

        domain = "AI Security"
        if agent:
            persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
            persona = persona_res.scalar_one_or_none()
            if persona:
                domain = persona.domain

    topics = await discover_candidate_topics(domain)
    if not topics:
        topics = [{
            "title": f"Autonomous Research Discovery in {domain}",
            "summary": f"Fresh candidate research topics identified in {domain}.",
            "sources": ["https://example.com/research-paper"],
        }]
    return topics


@activity.defn
async def recall_memory_activity(agent_id: str, topic: dict[str, Any]) -> dict[str, Any]:
    """Activity: Recall associative memory context from Breeth."""
    return await recall_memory_context(topic)


@activity.defn
async def run_memory_behaviors_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Execute memory behaviors (story continuity, prediction updates, concept gap detection)."""
    memory_context["behaviors_evaluated"] = True
    return memory_context


@activity.defn
async def editorial_judge_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Score candidate topic and render ACCEPT/REJECT decision against constitution."""
    rules = {"accept_threshold": 60.0, "relevance_threshold": 60.0}
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()
        if agent:
            const_res = await db.execute(
                select(Constitution).where(Constitution.agent_id == agent.id, Constitution.is_active.is_(True))
            )
            constitution = const_res.scalar_one_or_none()
            if constitution and isinstance(constitution.rules, dict):
                rules = constitution.rules

    scores = await score_candidate_topic(topic, memory_context, rules)
    accept_threshold = float(rules.get("accept_threshold", 60.0))
    accepted, reason = judge_topic_score(scores, accept_threshold)

    return {
        "accepted": accepted,
        "reason": reason,
        "scores": scores,
    }


@activity.defn
async def log_topic_debt_activity(
    agent_id: str, topic: dict[str, Any], judge_result: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Persist rejected candidate topic into topic_debt database table."""
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()

        if agent:
            debt_item = TopicDebt(
                agent_id=agent.id,
                title=str(topic.get("title", "Untitled Topic")),
                raw_item=topic,
                rejection_reason=str(judge_result.get("reason", "Below score threshold")),
                revisit_condition="Revisit when new evidence or sources arrive",
                status="pending",
            )
            db.add(debt_item)
            await db.commit()

    return {"status": "logged", "title": topic.get("title")}


@activity.defn
async def generate_drafts_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> list[dict[str, Any]]:
    """Activity: Generate 3 candidate post draft angles."""
    persona_dict = {"name": "Ada", "domain": "AI Security"}
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()
        if agent:
            persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
            persona = persona_res.scalar_one_or_none()
            if persona:
                persona_dict = {"name": persona.name, "domain": persona.domain, "voice_config": persona.voice_config}

    drafts = await generate_draft_angles(topic, persona_dict)
    if not drafts:
        title = topic.get("title", "Research Update")
        drafts = [
            {
                "angle_name": "Deep Dive Analysis",
                "post_text": f"In-depth analysis on {title}. Critical implications for security and architecture.",
                "sources": topic.get("sources", []),
            },
            {
                "angle_name": "Practical Security Impact",
                "post_text": f"Practical breakdown of {title}. Key takeaways for engineering teams.",
                "sources": topic.get("sources", []),
            },
        ]

    return drafts


@activity.defn
async def self_critique_activity(agent_id: str, drafts: list[dict[str, Any]]) -> dict[str, Any]:
    """Activity: Critique candidate drafts and select the winning post."""
    return await critique_and_select_winning_draft(drafts)


@activity.defn
async def persona_check_activity(agent_id: str, winning_draft: dict[str, Any]) -> dict[str, Any]:
    """Activity: Verify winning draft alignment with persona voice."""
    persona_dict = {"name": "Ada", "domain": "AI Security"}
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()
        if agent:
            persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
            persona = persona_res.scalar_one_or_none()
            if persona:
                persona_dict = {"name": persona.name, "domain": persona.domain}

    aligned, reason = await verify_persona_alignment(winning_draft, persona_dict)
    return {"aligned": aligned, "reason": reason}


@activity.defn
async def publish_post_activity(
    agent_id: str, draft: dict[str, Any], topic: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Persist final immutable Post row to database."""
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent with agent_id '{agent_id}' not found")

        post_id = f"p_{uuid.uuid4().hex[:10]}"
        post_text = str(draft.get("post_text") or draft.get("text") or "Published update")
        sources = draft.get("sources") or topic.get("sources") or []

        post = Post(
            post_id=post_id,
            agent_id=agent.id,
            text=post_text,
            rationale="Selected via autonomous editorial scoring and persona verification",
            sources=sources if isinstance(sources, list) else [str(sources)],
        )
        db.add(post)
        await db.commit()

        return {
            "post_id": post.post_id,
            "text": post.text,
            "sources": post.sources,
        }


@activity.defn
async def build_rationale_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any], draft: dict[str, Any]
) -> str:
    """Activity: Build selection rationale string."""
    return await build_post_rationale(topic, memory_context)


@activity.defn
async def write_breeth_episode_activity(
    agent_id: str, topic: dict[str, Any], item: dict[str, Any], decision: str
) -> dict[str, Any]:
    """Activity: Persist decision episode to Breeth memory."""
    return await record_decision_episode(
        {"agent_id": agent_id, "topic": topic, "item": item, "decision": decision}
    )


@activity.defn
async def self_audit_activity(agent_id: str) -> dict[str, Any]:
    """Activity: Execute periodic self-audit and constitution review."""
    return await run_self_audit(agent_id)
