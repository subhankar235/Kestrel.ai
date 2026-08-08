"""Raw source result normalizer — turns scraped web data into structured Topic payloads."""

from __future__ import annotations

from typing import Any


async def normalize_raw_content(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize raw discovery items into structured topic dicts."""
    return []
