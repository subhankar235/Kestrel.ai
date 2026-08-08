"""SQLAlchemy ORM model for rejected topic debt (revisit tracking)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.agent import Agent


class TopicDebt(Base):
    """TopicDebt table — rejected topics with reasons and revisit conditions."""

    __tablename__ = "topic_debt"
    __table_args__ = (
        Index("ix_topic_debt_agent_id_status", "agent_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic_summary: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    revisit_condition: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    agent: Mapped[Agent] = relationship("Agent", back_populates="topic_debts")

    def __repr__(self) -> str:
        return f"<TopicDebt id={self.id} title={self.topic_title!r} status={self.status!r}>"
