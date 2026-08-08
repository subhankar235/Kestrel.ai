"""RSS feed client — parses RSS/Atom feeds for blogs, advisories, and industry updates."""

from __future__ import annotations

from typing import Any


async def fetch_rss_topics(urls: list[str]) -> list[dict[str, Any]]:
    """Parse configured RSS feed URLs for fresh articles."""
    return []
