"""Small compatibility migrations for databases created before model changes."""

from __future__ import annotations

from sqlalchemy import text

from app.db.session import engine


async def ensure_schema_compatibility() -> None:
    """Apply safe additive changes when an older deployment schema is detected."""
    if engine.dialect.name != "postgresql":
        return

    async with engine.begin() as connection:
        await connection.execute(
            text(
                "ALTER TABLE agents "
                "ADD COLUMN IF NOT EXISTS cycle_count INTEGER NOT NULL DEFAULT 0"
            )
        )
        for statement in (
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS publish_interval_minutes INTEGER NOT NULL DEFAULT 240",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS observation_period_hours INTEGER NOT NULL DEFAULT 48",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS start_mode VARCHAR(20) NOT NULL DEFAULT 'immediate'",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS start_at TIMESTAMPTZ",
        ):
            await connection.execute(text(statement))
        await connection.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS topic VARCHAR(500)"))
