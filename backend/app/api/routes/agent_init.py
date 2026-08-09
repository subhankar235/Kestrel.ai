"""POST /api/agent/init — callable-once agent initialization endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent import Agent
from app.models.constitution import Constitution
from app.models.persona import Persona
from app.persona.constitution import get_default_constitution_rules
from app.persona.voice import build_voice_config
from app.schemas.agent import InitRequest, InitResponse

router = APIRouter(tags=["agent"])


@router.post(
    "/init",
    response_model=InitResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialize agent instance once",
    description="Creates agent, persona, and constitution rows. Callable exactly once per deployment.",
)
async def init_agent(
    request: InitRequest,
    db: AsyncSession = Depends(get_db),
) -> InitResponse:
    """POST /api/agent/init — unauthenticated for the current local workflow."""
    # Generate a unique opaque agentId for every persona creation request.
    generated_agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    # 3. Create Agent record
    agent = Agent(
        agent_id=generated_agent_id,
        status="active",
        publish_interval_minutes=request.publishIntervalMinutes,
        observation_period_hours=request.observationPeriodHours,
        start_mode=request.startMode,
        start_at=request.startAt,
    )
    db.add(agent)
    await db.flush()

    # 4. Create Persona record
    voice_config = build_voice_config(request.persona.name, request.persona.domain)
    if request.persona.voice:
        voice_config["voice"] = request.persona.voice

    persona = Persona(
        agent_id=agent.id,
        name=request.persona.name,
        domain=request.persona.domain,
        voice_config=voice_config,
    )
    db.add(persona)

    # 5. Create initial Constitution record (v1.0)
    constitution = Constitution(
        agent_id=agent.id,
        version="1.0",
        rules=get_default_constitution_rules(),
        is_active=True,
    )
    db.add(constitution)

    await db.commit()

    # 6. Start recurring APScheduler job for autonomous agent cycle
    from app.workflows.schedules import create_agent_schedule
    await create_agent_schedule(
        generated_agent_id,
        interval_minutes=request.publishIntervalMinutes,
        start_at=request.startAt if request.startMode == "scheduled" else datetime.now(timezone.utc),
        observation_period_hours=request.observationPeriodHours,
        run_immediately=request.startMode == "immediate",
    )

    return InitResponse(agentId=generated_agent_id)
