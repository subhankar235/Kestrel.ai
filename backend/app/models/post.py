"""SQLAlchemy ORM model for published posts (immutable record)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.agent import Agent


class Post(Base):
    """Post table — system of record for generated posts returned by feed endpoint."""

    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_agent_id_created_at_desc", "agent_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    related_post_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="SET NULL"),
        nullable=True,
    )
    relationship: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    agent: Mapped[Agent] = orm_relationship("Agent", back_populates="posts")
    related_post: Mapped[Optional[Post]] = orm_relationship(
        "Post", remote_side=[id], backref="child_posts", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} post_id={self.post_id!r} agent_id={self.agent_id}>"
