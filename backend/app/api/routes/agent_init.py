"""POST /api/agent/init — callable-once agent initialization endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auth
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
    _auth: dict[str, Any] = Depends(require_auth),
) -> InitResponse:
    """POST /api/agent/init — protected by Clerk auth, enforces callable-once."""
    # 1. Enforce callable-once per deployment
    result = await db.execute(select(Agent))
    existing_agent = result.scalar_one_or_none()
    if existing_agent is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent initialization has already been performed for this deployment",
        )

    # 2. Generate unique opaque agentId string (e.g. "abc-123")
    generated_agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    # 3. Create Agent record
    agent = Agent(
        agent_id=generated_agent_id,
        status="active",
    )
    db.add(agent)
    await db.flush()

    # 4. Create Persona record
    persona = Persona(
        agent_id=agent.id,
        name=request.persona.name,
        domain=request.persona.domain,
        voice_config=build_voice_config(request.persona.name, request.persona.domain),
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

    return InitResponse(agentId=generated_agent_id)