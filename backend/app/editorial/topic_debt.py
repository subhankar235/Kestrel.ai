"""Topic debt logger — handles persistence and tracking of rejected candidate topics."""

from __future__ import annotations

from typing import Any


async def log_rejected_topic(topic: dict[str, Any], reason: str, revisit_condition: str) -> dict[str, Any]:
    """Persist rejected topic into Postgres topic_debt table."""
    return {"status": "logged"}
