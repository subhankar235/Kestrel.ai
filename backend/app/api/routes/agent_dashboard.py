"""GET /api/agent/dashboard — persisted agent data for the operator dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings
from app.memory.breeth_client import list_memory_entities, search_memory
from app.workflows.schedules import get_agent_schedule
from app.models.agent import Agent
from app.models.constitution import Constitution
from app.models.persona import Persona
from app.models.post import Post
from app.models.topic_debt import TopicDebt
from app.schemas.dashboard import (
    AgentSummary,
    AgentsResponse,
    DashboardCycleStatus,
    DashboardMemoryItem,
    DashboardPost,
    DashboardResponse,
    DashboardSource,
    DashboardTopicDebt,
)

router = APIRouter(tags=["agent"])


@router.get("/agents", response_model=AgentsResponse, summary="List created agents")
async def list_agents(db: AsyncSession = Depends(get_db)) -> AgentsResponse:
    """Return every created persona so the UI can preserve persona history."""
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = result.scalars().all()
    return AgentsResponse(
        agents=[
            AgentSummary(
                agentId=agent.agent_id,
                status=agent.status,
                createdAt=agent.created_at,
                name=agent.personas[0].name if agent.personas else "Unnamed agent",
                domain=agent.personas[0].domain if agent.personas else "",
                publishIntervalMinutes=agent.publish_interval_minutes,
                observationPeriodHours=agent.observation_period_hours,
            )
            for agent in agents
        ]
    )


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get persisted agent dashboard data",
)
async def get_dashboard(
    agentId: str = Query(..., description="Agent ID string returned by init endpoint"),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Return the dashboard views that currently have a Postgres source of truth."""
    agent_result = await db.execute(select(Agent).where(Agent.agent_id == agentId.strip()))
    agent = agent_result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    persona_result = await db.execute(
        select(Persona)
        .where(Persona.agent_id == agent.id)
        .order_by(Persona.created_at.desc())
        .limit(1)
    )
    persona = persona_result.scalar_one_or_none()

    constitution_result = await db.execute(
        select(Constitution)
        .where(Constitution.agent_id == agent.id, Constitution.is_active.is_(True))
        .order_by(Constitution.created_at.desc())
        .limit(1)
    )
    constitution = constitution_result.scalar_one_or_none()

    posts_result = await db.execute(
        select(Post).where(Post.agent_id == agent.id).order_by(Post.created_at.desc())
    )
    posts = posts_result.scalars().all()

    debt_result = await db.execute(
        select(TopicDebt)
        .where(TopicDebt.agent_id == agent.id)
        .order_by(TopicDebt.created_at.desc())
    )
    topic_debt = debt_result.scalars().all()

    settings = get_settings()
    persona_query = f"{persona.name} {persona.domain}" if persona else agent.agent_id
    try:
        memory_result = await search_memory(persona_query, limit=50, min_score=0.0)
    except Exception:
        # Dashboard reads must remain available when the optional Breeth service is down.
        memory_result = type("MemoryResult", (), {"results": []})()
    memory_items = memory_result.results or await list_memory_entities(limit=50)
    schedule = await get_agent_schedule(agent.agent_id)

    sources = [
        DashboardSource(name="Exa neural search", kind="Web", configured=bool(settings.EXA_API_KEY)),
        DashboardSource(name="Tavily search", kind="Web", configured=bool(settings.TAVILY_API_KEY)),
    ]

    persona_data = None
    if persona is not None:
        persona_data = {
            "name": persona.name,
            "domain": persona.domain,
            "voiceConfig": persona.voice_config,
            "createdAt": persona.created_at,
        }

    constitution_data = None
    if constitution is not None:
        constitution_data = {
            "version": constitution.version,
            "rules": constitution.rules,
            "createdAt": constitution.created_at,
        }

    return DashboardResponse(
        agentId=agent.agent_id,
        status=agent.status,
        cycleCount=agent.cycle_count,
        publishIntervalMinutes=agent.publish_interval_minutes,
        observationPeriodHours=agent.observation_period_hours,
        startMode=agent.start_mode,
        startAt=agent.start_at,
        persona=persona_data,
        constitution=constitution_data,
        posts=[
            DashboardPost(
                id=post.post_id,
                createdAt=post.created_at,
                text=post.text,
                topic=post.topic,
                rationale=post.rationale,
                sources=[str(source) for source in post.sources] if isinstance(post.sources, list) else [],
                relatedPostId=str(post.related_post_id) if post.related_post_id else None,
                relationship=post.relationship,
            )
            for post in posts
        ],
        topicDebt=[
            DashboardTopicDebt(
                id=str(item.id),
                title=item.topic_title,
                score=item.score,
                reason=item.rejection_reason,
                revisitCondition=item.revisit_condition,
                status=item.status,
                createdAt=item.created_at,
            )
            for item in topic_debt
        ],
        memory=[
            DashboardMemoryItem(
                id=item.id,
                text=item.text,
                score=item.score,
                metadata=item.metadata,
                concepts=item.concepts,
                stories=item.stories,
                openQuestions=item.open_questions,
            )
            for item in memory_items
        ],
        cycle=DashboardCycleStatus(
            scheduleId=str(schedule.get("schedule_id", f"schedule_{agent.agent_id}")),
            status=str(schedule.get("status", "active")),
            nextRunTime=schedule.get("next_run_time"),
            note=schedule.get("note"),
        ),
        sources=sources,
    )
