"""GitHub API client — monitors releases and repository activity as discovery candidates.

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

_SOURCE = "github"


async def fetch_github_topics(query: str) -> list[dict[str, Any]]:
    """Query GitHub repositories and releases for developer updates.

    Raises:
        DiscoveryAuthError: GitHub token is invalid or revoked — non-retryable.
        DiscoveryServerError: GitHub returned a 5xx response — retryable.
        DiscoveryClientError: GitHub returned a 4xx bad request — non-retryable.
        DiscoveryTimeoutError: Network timeout — retryable.
    """
    settings = get_settings()
    token = settings.GITHUB_TOKEN.strip()

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": 5,
    }
    headers = {
        "User-Agent": "Kestrel-AI-Agent",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code in (401, 403):
                exc = DiscoveryAuthError(source=_SOURCE, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_github_topics",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 500 <= response.status_code < 600:
                exc = DiscoveryServerError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_github_topics",
                    error=exc,
                    retryable=True,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 400 <= response.status_code < 500:
                exc = DiscoveryClientError(source=_SOURCE, status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="fetch_github_topics",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            response.raise_for_status()
            data = response.json()

            results = []
            for repo in data.get("items", []):
                name = repo.get("full_name") or repo.get("name", "GitHub Repository")
                desc = repo.get("description") or f"GitHub repository {name}"
                html_url = repo.get("html_url", "")

                results.append({
                    "title": f"GitHub: {name}",
                    "url": html_url,
                    "body": desc,
                    "source": _SOURCE,
                })
            return results

    except (DiscoveryAuthError, DiscoveryServerError, DiscoveryClientError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = DiscoveryTimeoutError(f"GitHub search timed out for query '{query}': {exc}")
        log_activity_failure(
            logger,
            activity="fetch_github_topics",
            error=typed,
            retryable=True,
            extra={"query": query},
        )
        raise typed from exc

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"GitHub search failed for query '{query}': {exc}")
        return []
