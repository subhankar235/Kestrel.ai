"""Orchestrates multi-source discovery (Exa, Tavily, RSS, GitHub) into candidate topics."""

from __future__ import annotations

from typing import Any


async def discover_candidate_topics(domain: str) -> list[dict[str, Any]]:
    """Fan out discovery across configured sources and normalize candidate topics."""
    return []
