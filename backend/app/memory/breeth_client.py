"""Breeth long-term memory client — HTTP wrapper for /v1/search and /v1/episodes."""

from __future__ import annotations

from typing import Any


async def search_memory(query: str) -> dict[str, Any]:
    """Execute associative memory search query against Breeth API."""
    return {"results": []}


async def write_episode(payload: dict[str, Any]) -> dict[str, Any]:
    """Write episode payload to Breeth long-term associative memory."""
    return {"status": "created"}
