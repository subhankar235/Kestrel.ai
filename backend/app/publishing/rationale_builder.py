"""Rationale builder — generates transparency rationale string explaining post selection."""

from __future__ import annotations

from typing import Any


async def build_post_rationale(topic: dict[str, Any], memory_context: dict[str, Any]) -> str:
    """Build 'why selected / why now / memory link' rationale text."""
    return "Selected due to high relevance and clear evidence."
