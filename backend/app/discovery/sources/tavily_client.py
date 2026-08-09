"""Tavily search client — source cross-checking and secondary web discovery.

Phase 21: raises typed DiscoveryAuthError / DiscoveryServerError / DiscoveryTimeoutError
so Temporal's RetryPolicy can distinguish retryable from non-retryable failures.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import (
    DiscoveryAuthError,
    DiscoveryClientError,
    DiscoveryServerError,
    DiscoveryTimeoutError,
)
from app.core.logging import get_logger, log_activity_failure

logger = get_logger(__name__)

_SOURCE = "tavily"


async def fetch_tavily_topics(query: str) -> list[dict[str, Any]]:
    """Execute Tavily search query for cross-checking discovery topics.

    Raises:
        DiscoveryAuthError: API key is invalid or revoked — non-retryable.
        DiscoveryServerError: Tavily returned a 5xx response — retryable.
        DiscoveryClientError: Tavily returned a 4xx bad request — non-retryable.
        DiscoveryTimeoutError: Network timeout — retryable.

    Returns an empty list when TAVILY_API_KEY is not configured (graceful skip).
    """
    settings = get_settings()
    api_key = settings.TAVILY_API_KEY.strip()

    if not api_key:
        logger.info(f"TAVILY_API_KEY missing; skipping Tavily search for query '{query}'")
        return []

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

            if response.status_code in (401, 403):
                exc = DiscoveryAuthError(source=_SOURCE, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_tavily_topics",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 500 <= response.status_code < 600:
                exc = DiscoveryServerError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_tavily_topics",
                    error=exc,
                    retryable=True,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 400 <= response.status_code < 500:
                exc = DiscoveryClientError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_tavily_topics",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title") or "Tavily Discovery Item",
                    "url": item.get("url", ""),
                    "body": item.get("content", "") or item.get("snippet", ""),
                    "source": _SOURCE,
                })
            return results

    except (DiscoveryAuthError, DiscoveryServerError, DiscoveryClientError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = DiscoveryTimeoutError(f"Tavily search timed out for query '{query}': {exc}")
        log_activity_failure(
            logger,
            activity="fetch_tavily_topics",
            error=typed,
            retryable=True,
            extra={"query": query},
        )
        raise typed from exc

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Tavily search failed for query '{query}': {exc}")
        return []
