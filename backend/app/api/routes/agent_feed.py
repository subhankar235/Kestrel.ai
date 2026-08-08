"""GET /api/agent/feed — unauthenticated feed endpoint polled by evaluator."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.schemas.feed import FeedResponse, PostOut

router = APIRouter(tags=["agent"])


@router.get(
    "/feed",
    response_model=FeedResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent post feed",
    description="Returns reverse-chronological list of published posts for the specified agentId. Unauthenticated.",
)
async def get_feed(
    agentId: str = Query(..., description="Agent ID string returned by init endpoint"),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    """GET /api/agent/feed?agentId=abc-123 — reverse-chronological feed lookup."""
    if not agentId or not agentId.strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query parameter 'agentId' is required",
        )

    # 1. Lookup agent by string agent_id
    result = await db.execute(select(Agent).where(Agent.agent_id == agentId.strip()))
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with agentId '{agentId}' not found",
        )

    # 2. Query posts ordered by created_at DESC
    posts_query = await db.execute(
        select(Post).where(Post.agent_id == agent.id).order_by(Post.created_at.desc())
    )
    posts_list = posts_query.scalars().all()

    # 3. Serialize to FeedResponse schema
    formatted_posts = [
        PostOut(
            id=p.post_id,
            createdAt=p.created_at,
            text=p.text,
            rationale=p.rationale,
            sources=p.sources if isinstance(p.sources, list) else [],
        )
        for p in posts_list
    ]

    return FeedResponse(posts=formatted_posts)