"""Declarative base for all SQLAlchemy ORM models (system of record)."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base class for every model; Alembic discovers tables via metadata."""