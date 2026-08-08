"""Exa API client — semantic and live web search discovery source.

Phase 21: raises typed DiscoveryAuthError / DiscoveryServerError / DiscoveryTimeoutError
instead of bare exceptions so Temporal's RetryPolicy can distinguish retryable from
non-retryable failures.
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

_SOURCE = "exa"


async def fetch_exa_topics(query: str) -> list[dict[str, Any]]:
    """Execute Exa web search query for topic candidates.

    Raises:
        DiscoveryAuthError: API key is invalid or revoked (401/403) — non-retryable.
        DiscoveryServerError: Exa returned a 5xx response — retryable.
        DiscoveryClientError: Exa returned a 4xx (bad request) — non-retryable.
        DiscoveryTimeoutError: Network timeout — retryable.

    Returns an empty list when EXA_API_KEY is not configured (graceful skip).
    """
    settings = get_settings()
    api_key = settings.EXA_API_KEY.strip()

    if not api_key:
        logger.info(f"EXA_API_KEY missing; skipping Exa search for query '{query}'")
        return []

    url = "https://api.exa.ai/search"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "useAutoprompt": True,
        "numResults": 5,
        "contents": {"text": True},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in (401, 403):
                exc = DiscoveryAuthError(source=_SOURCE, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_exa_topics",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 500 <= response.status_code < 600:
                exc = DiscoveryServerError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_exa_topics",
                    error=exc,
                    retryable=True,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 400 <= response.status_code < 500:
                exc = DiscoveryClientError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_exa_topics",
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
                    "title": item.get("title") or "Exa Discovery Item",
                    "url": item.get("url", ""),
                    "body": item.get("text", "") or item.get("snippet", ""),
                    "source": _SOURCE,
                })
            return results

    except (DiscoveryAuthError, DiscoveryServerError, DiscoveryClientError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = DiscoveryTimeoutError(f"Exa search timed out for query '{query}': {exc}")
        log_activity_failure(
            logger,
            activity="fetch_exa_topics",
            error=typed,
            retryable=True,
            extra={"query": query},
        )
        raise typed from exc

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Exa search failed for query '{query}': {exc}")
        return []
