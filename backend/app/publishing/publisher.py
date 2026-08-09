"""Publisher — persists the final immutable post record into Postgres database."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal, engine
from app.models import Base
from app.models.agent import Agent
from app.models.post import Post

logger = get_logger(__name__)


def _extract_memory_relationship(
    topic: dict[str, Any], memory_context: dict[str, Any] | None = None
) -> tuple[uuid.UUID | None, str | None]:
    """Extract (related_post_id, relationship_type) from memory behaviors or topic metadata."""
    mem_ctx = memory_context or {}
    behaviors = mem_ctx.get("behavior_results", {})

    story_info = behaviors.get("story_continuation") or topic.get("story_continuation")
    prediction_info = behaviors.get("prediction_resolution") or topic.get("prediction_resolution")
    resurrection_info = behaviors.get("resurrection") or topic.get("resurrection")
    concept_gap_info = behaviors.get("concept_gaps") or topic.get("concept_gaps")

    related_id_uuid: uuid.UUID | None = None
    relationship_type: str | None = None

    if story_info:
        relationship_type = "STORY_CONTINUATION"
        raw_id = story_info.get("related_post_id") or story_info.get("originating_post_id")
        if isinstance(raw_id, uuid.UUID):
            related_id_uuid = raw_id

    elif prediction_info:
        relationship_type = "PREDICTION_RESOLUTION"
        raw_id = prediction_info.get("related_post_id") or prediction_info.get("originating_post_id")
        if isinstance(raw_id, uuid.UUID):
            related_id_uuid = raw_id

    elif resurrection_info:
        relationship_type = "TOPIC_RESURRECTION"

    elif concept_gap_info:
        relationship_type = "CONCEPT_GAP"

    return related_id_uuid, relationship_type


async def publish_final_post(
    agent_id: str,
    draft: dict[str, Any],
    topic: dict[str, Any],
    memory_context: dict[str, Any] | None = None,
    rationale: str | None = None,
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Write final immutable Post row to posts database table with memory relationships."""
    post_text = str(draft.get("post_text") or draft.get("text") or "Published update")
    sources = draft.get("sources") or topic.get("sources") or []
    if not isinstance(sources, list):
        sources = [str(sources)]

    final_rationale = rationale or str(draft.get("rationale") or "Selected via autonomous editorial scoring")
    related_post_id_uuid, relationship_str = _extract_memory_relationship(topic, memory_context)

    async def _execute_publish(session: AsyncSession) -> dict[str, Any]:
        agent_res = await session.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()
        if not agent:
            # Fallback for dev/test environments: auto-create Agent record
            agent = Agent(agent_id=agent_id, status="active")
            session.add(agent)
            await session.flush()

        topic_title = str(topic.get("title") or "").strip()
        if topic_title:
            duplicate_res = await session.execute(
                select(Post)
                .where(Post.agent_id == agent.id, Post.topic == topic_title)
                .order_by(Post.created_at.desc())
                .limit(1)
            )
            duplicate = duplicate_res.scalar_one_or_none()
            if duplicate is not None:
                logger.info(
                    f"Skipped duplicate topic '{topic_title}' for agent '{agent_id}'"
                )
                return {
                    "id": duplicate.post_id,
                    "post_id": duplicate.post_id,
                    "agent_id": agent_id,
                    "created_at": duplicate.created_at.isoformat(),
                    "text": duplicate.text,
                    "rationale": duplicate.rationale,
                    "sources": duplicate.sources,
                    "related_post_id": str(duplicate.related_post_id) if duplicate.related_post_id else None,
                    "relationship": duplicate.relationship,
                    "duplicate": True,
                }

        post_id_str = f"p_{uuid.uuid4().hex[:10]}"

        post = Post(
            post_id=post_id_str,
            agent_id=agent.id,
            text=post_text,
            topic=str(topic.get("title") or "") or None,
            rationale=final_rationale,
            sources=sources,
            related_post_id=related_post_id_uuid,
            relationship=relationship_str,
        )

        session.add(post)
        await session.commit()
        await session.refresh(post)

        logger.info(
            f"Successfully published Post '{post.post_id}' for agent '{agent_id}' (relationship={relationship_str})"
        )

        return {
            "id": post.post_id,
            "post_id": post.post_id,
            "agent_id": agent_id,
            "created_at": post.created_at.isoformat(),
            "text": post.text,
            "rationale": post.rationale,
            "sources": post.sources,
            "related_post_id": str(post.related_post_id) if post.related_post_id else None,
            "relationship": post.relationship,
        }

    if db_session:
        return await _execute_publish(db_session)
    else:
        async with AsyncSessionLocal() as session:
            return await _execute_publish(session)
