"""Pydantic schemas for POST /api/agent/init with input validation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PersonaIn(BaseModel):
    """Persona payload within InitRequest."""

    name: str = Field(..., min_length=1, max_length=255, description="Persona name, e.g. Ada")
    domain: str = Field(..., min_length=1, max_length=255, description="Persona domain, e.g. AI Security")
    voice: str | None = Field(default=None, max_length=1000, description="Optional persona voice")

    @field_validator("name", "domain", mode="before")
    @classmethod
    def strip_and_validate_non_empty(cls, value: str) -> str:
        """Strip whitespace and reject blank or non-string values."""
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace-only")
        return stripped


class InitRequest(BaseModel):
    """Request payload for POST /api/agent/init."""

    persona: PersonaIn
    publishIntervalMinutes: int = Field(default=240, ge=1, le=10080)
    observationPeriodHours: int = Field(default=48, ge=1, le=8760)
    startMode: Literal["immediate", "scheduled"] = "immediate"
    startAt: datetime | None = None


class InitResponse(BaseModel):
    """Response payload for POST /api/agent/init."""

    agentId: str = Field(..., min_length=1, max_length=255, description="Unique agent identifier returned to evaluator")
