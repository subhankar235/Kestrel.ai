"""Orchestrates multi-source discovery (Exa, Tavily, RSS, GitHub) into candidate topics."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.discovery.normalizer import normalize_raw_content
from app.discovery.sources.exa_client import fetch_exa_topics
from app.discovery.sources.github_client import fetch_github_topics
from app.discovery.sources.rss_client import fetch_rss_topics
from app.discovery.sources.tavily_client import fetch_tavily_topics

logger = get_logger(__name__)


def _deduplicate_raw_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate raw discovery items based on URL and lowercased title similarity."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique_items: list[dict[str, Any]] = []

    for item in items:
        url = str(item.get("url", "")).strip().lower()
        title = str(item.get("title", "")).strip().lower()

        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)

        unique_items.append(item)

    return unique_items


async def discover_candidate_topics(domain: str) -> list[dict[str, Any]]:
    """Fan out discovery across configured sources concurrently and normalize candidate topics."""
    query = f"{domain} security research vulnerability advisory"
    logger.info(f"Starting discovery fan-out for domain '{domain}' with query: '{query}'")

    results = await asyncio.gather(
        fetch_exa_topics(query),
        fetch_tavily_topics(query),
        fetch_rss_topics(),
        fetch_github_topics(query),
        return_exceptions=True,
    )

    all_raw_items: list[dict[str, Any]] = []
    for res in results:
        if isinstance(res, list):
            all_raw_items.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Discovery source task failed: {res}")

    logger.info(
        f"Discovery fetched {len(all_raw_items)} raw items across all sources for domain '{domain}'",
        extra={"event": "discovery_raw_fetch", "domain": domain, "raw_count": len(all_raw_items)},
    )
    deduped_items = _deduplicate_raw_items(all_raw_items)
    normalized_topics = await normalize_raw_content(deduped_items)

    logger.info(
        f"Discovery batch completed for '{domain}': batch size {len(normalized_topics)} candidate topics",
        extra={
            "event": "discovery_batch",
            "domain": domain,
            "raw_count": len(all_raw_items),
            "deduped_count": len(deduped_items),
            "batch_size": len(normalized_topics),
        },
    )
    return normalized_topics

