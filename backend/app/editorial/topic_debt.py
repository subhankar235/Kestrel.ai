"""Topic debt logger — handles persistence and tracking of rejected candidate topics."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal
from app.models.agent import Agent
from app.models.topic_debt import TopicDebt


async def log_rejected_topic(
    topic: dict[str, Any],
    reason: str,
    revisit_condition: str | None = None,
    agent_id: str | None = None,
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """Persist rejected candidate topic into Postgres topic_debt table."""
    condition = revisit_condition or "Revisit when new empirical evidence or additional sources arrive"
    topic_title = str(topic.get("title", "Untitled Rejected Topic"))

    async def _process_logging(session: AsyncSession) -> None:
        target_agent_db_id = None
        if agent_id:
            agent_res = await session.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()
            if agent:
                target_agent_db_id = agent.id

        if not target_agent_db_id:
            agent_res = await session.execute(select(Agent))
            agent = agent_res.scalars().first()
            if agent:
                target_agent_db_id = agent.id

        if target_agent_db_id:
            debt_item = TopicDebt(
                agent_id=target_agent_db_id,
                topic_title=topic_title,
                topic_summary=str(topic.get("summary", "")),
                score=float(topic.get("score", 0.0)),
                rejection_reason=reason,
                revisit_condition=condition,
                status="open",
            )
            session.add(debt_item)
            await session.commit()

    if db is not None:
        await _process_logging(db)
    else:
        async with AsyncSessionLocal() as session:
            conn = await session.connection()
            await conn.run_sync(Base.metadata.create_all)
            await _process_logging(session)

    return {
        "status": "logged",
        "title": topic_title,
        "rejection_reason": reason,
        "revisit_condition": condition,
    }
