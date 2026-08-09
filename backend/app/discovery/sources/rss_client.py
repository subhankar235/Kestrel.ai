"""RSS feed client — parses RSS/Atom feeds for blogs, advisories, and industry updates.

Phase 21: wraps per-feed failures with DiscoveryTimeoutError / DiscoveryServerError so
the discovery_service.py aggregator can capture them via asyncio.gather(return_exceptions=True).
Each feed is processed independently — one failing feed does not block others.
"""

from __future__ import annotations

from typing import Any

import feedparser
import httpx

from app.core.config import get_settings
from app.core.exceptions import (
    DiscoveryAuthError,
    DiscoveryServerError,
    DiscoveryTimeoutError,
)
from app.core.logging import get_logger, log_activity_failure

logger = get_logger(__name__)

_SOURCE = "rss"


async def _fetch_single_feed(client: httpx.AsyncClient, feed_url: str) -> list[dict[str, Any]]:
    """Fetch and parse a single RSS feed URL. Raises typed exceptions on failure."""
    try:
        response = await client.get(feed_url)

        if response.status_code in (401, 403):
            exc = DiscoveryAuthError(source=_SOURCE, detail=f"feed={feed_url}")
            log_activity_failure(
                logger,
                activity="fetch_rss_topics",
                error=exc,
                retryable=False,
                extra={"feed_url": feed_url, "status_code": response.status_code},
            )
            raise exc

        if 500 <= response.status_code < 600:
            exc = DiscoveryServerError(source=_SOURCE, status_code=response.status_code, detail=f"feed={feed_url}")
            log_activity_failure(
                logger,
                activity="fetch_rss_topics",
                error=exc,
                retryable=True,
                extra={"feed_url": feed_url, "status_code": response.status_code},
            )
            raise exc

        response.raise_for_status()
        parsed = feedparser.parse(response.text)

        results = []
        for entry in parsed.entries[:5]:  # Top 5 items per feed
            title = entry.get("title") or "RSS Feed Article"
            link = entry.get("link") or feed_url
            summary = entry.get("summary") or entry.get("description") or ""

            results.append({
                "title": title,
                "url": link,
                "body": summary,
                "source": _SOURCE,
            })
        return results

    except (DiscoveryAuthError, DiscoveryServerError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = DiscoveryTimeoutError(f"RSS fetch timed out for '{feed_url}': {exc}")
        log_activity_failure(
            logger,
            activity="fetch_rss_topics",
            error=typed,
            retryable=True,
            extra={"feed_url": feed_url},
        )
        raise typed from exc


async def fetch_rss_topics(urls: list[str] | None = None) -> list[dict[str, Any]]:
    """Parse configured RSS feed URLs for fresh articles.

    Individual feed failures are logged and skipped — one broken feed never blocks others.
    Returns an empty list when no RSS feed URLs are configured.
    """
    settings = get_settings()
    feed_urls = urls if urls is not None else settings.rss_feed_urls

    if not feed_urls:
        logger.info("No RSS feed URLs configured; skipping RSS discovery")
        return []

    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for feed_url in feed_urls[:5]:  # Limit to top 5 feeds
            try:
                feed_items = await _fetch_single_feed(client, feed_url)
                results.extend(feed_items)
            except Exception as exc:  # noqa: BLE001
                # Per-feed failure: log and continue with remaining feeds.
                logger.warning(f"RSS fetch failed for '{feed_url}': {exc}")

    return results
