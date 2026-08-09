"""Pydantic schemas for Breeth memory layer (/v1/search and /v1/episodes)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class BreethSearchRequest(BaseModel):
    """Request payload for POST /v1/search."""

    query: str = Field(..., min_length=1, max_length=500, description="Memory recall query string")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of search results")
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score threshold")
    filters: dict[str, Any] = Field(default_factory=dict, description="Metadata filter parameters")

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Search query cannot be empty or whitespace-only")
        return value.strip()


class BreethItem(BaseModel):
    """Individual item returned in memory search result."""

    id: str = Field(..., description="Memory item UUID or identifier")
    text: str = Field(..., description="Text content of the episode or concept")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance similarity score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata dict")
    concepts: list[str] = Field(default_factory=list, description="Extracted concepts")
    stories: list[str] = Field(default_factory=list, description="Related story titles")
    open_questions: list[str] = Field(default_factory=list, description="Open questions")


class BreethSearchResult(BaseModel):
    """Response payload for POST /v1/search."""

    results: list[BreethItem] = Field(default_factory=list)
    query: str = Field(..., description="Original search query string")
    total: int = Field(default=0, ge=0, description="Total matching memory items")


class BreethEpisodeIn(BaseModel):
    """Payload for writing memory episode to POST /v1/episodes."""

    topic: str = Field(..., min_length=1, max_length=500, description="Topic title")
    claims: list[str] = Field(default_factory=list, description="Extracted topic claims")
    stance: str = Field(default="neutral", description="Persona stance on topic")
    prediction: Optional[dict[str, Any]] = Field(default=None, description="Prediction details if applicable")
    story: Optional[dict[str, Any]] = Field(default=None, description="Story thread details if applicable")
    open_question: Optional[str] = Field(default=None, description="Open question for future exploration")
    concepts: list[str] = Field(default_factory=list, description="Related concept tags")
    sources: list[str] = Field(default_factory=list, description="Source URLs")
    related_posts: list[str] = Field(default_factory=list, description="Related post string IDs")
    editorial_decision: str = Field(default="accepted", description="Editorial decision: accepted or rejected")

    @field_validator("topic", mode="before")
    @classmethod
    def strip_topic(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Episode topic cannot be empty or whitespace-only")
        return value.strip()
