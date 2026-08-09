"""SQLAlchemy ORM model for Agent instances (system of record)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.constitution import Constitution
    from app.models.persona import Persona
    from app.models.post import Post
    from app.models.topic_debt import TopicDebt


class Agent(Base):
    """Agent table — stores main agent entity and metadata."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    temporal_workflow_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cycle_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    publish_interval_minutes: Mapped[int] = mapped_column(Integer, default=240, nullable=False)
    observation_period_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    start_mode: Mapped[str] = mapped_column(String(20), default="immediate", nullable=False)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    personas: Mapped[list[Persona]] = relationship(
        "Persona", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )
    posts: Mapped[list[Post]] = relationship(
        "Post", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )
    constitutions: Mapped[list[Constitution]] = relationship(
        "Constitution", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )
    topic_debts: Mapped[list[TopicDebt]] = relationship(
        "TopicDebt", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} agent_id={self.agent_id!r} status={self.status!r}>"
