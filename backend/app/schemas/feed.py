"""Pydantic schemas for GET /api/agent/feed."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class PostOut(BaseModel):
    """Post payload format returned in feed endpoint."""

    id: str = Field(..., min_length=1, max_length=255, description="Post identifier string e.g. p1")
    createdAt: datetime = Field(..., description="Post creation timestamp")
    text: str = Field(..., description="Published post text")
    topic: str | None = Field(default=None, description="Topic that produced the post")
    rationale: str = Field(..., description="Selection rationale text")
    sources: list[str] = Field(default_factory=list, description="Source URLs")
    agentId: str | None = None

    @field_serializer("createdAt")
    def serialize_created_at(self, dt: datetime, _info: Any) -> str:
        """Ensure createdAt is formatted as ISO 8601 UTC with Z suffix."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FeedResponse(BaseModel):
    """Response wrapper payload for GET /api/agent/feed."""

    posts: list[PostOut] = Field(default_factory=list)
