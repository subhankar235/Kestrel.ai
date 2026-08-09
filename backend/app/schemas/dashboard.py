"""Response shapes for the read-only dashboard API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DashboardPost(BaseModel):
    id: str
    createdAt: datetime
    text: str
    topic: str | None = None
    rationale: str
    sources: list[str] = Field(default_factory=list)
    relatedPostId: str | None = None
    relationship: str | None = None


class DashboardTopicDebt(BaseModel):
    id: str
    title: str
    score: float
    reason: str
    revisitCondition: str
    status: str
    createdAt: datetime


class DashboardMemoryItem(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    concepts: list[str] = Field(default_factory=list)
    stories: list[str] = Field(default_factory=list)
    openQuestions: list[str] = Field(default_factory=list)


class DashboardSource(BaseModel):
    name: str
    kind: str
    configured: bool


class DashboardCycleStatus(BaseModel):
    scheduleId: str
    status: str
    nextRunTime: str | None = None
    note: str | None = None


class AgentSummary(BaseModel):
    agentId: str
    status: str
    createdAt: Any
    name: str
    domain: str
    publishIntervalMinutes: int
    observationPeriodHours: int


class AgentsResponse(BaseModel):
    agents: list[AgentSummary] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    agentId: str
    status: str
    cycleCount: int
    publishIntervalMinutes: int
    observationPeriodHours: int
    startMode: str
    startAt: Any | None = None
    persona: dict[str, Any] | None = None
    constitution: dict[str, Any] | None = None
    posts: list[DashboardPost] = Field(default_factory=list)
    topicDebt: list[DashboardTopicDebt] = Field(default_factory=list)
    memory: list[DashboardMemoryItem] = Field(default_factory=list)
    cycle: DashboardCycleStatus | None = None
    sources: list[DashboardSource] = Field(default_factory=list)
