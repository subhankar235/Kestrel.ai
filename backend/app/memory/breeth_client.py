"""Breeth long-term associative memory HTTP client (/v1/search and /v1/episodes).

Phase 21: raises typed BreethAuthError / BreethServerError / BreethTimeoutError from
app.core.exceptions so Temporal's RetryPolicy can distinguish retryable from non-retryable
failures. The legacy BreethAPIError / BreethAuthenticationError classes are preserved as
aliases for backward-compatibility with existing code that catches them.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import (
    BreethAuthError,
    BreethClientError,
    BreethServerError,
    BreethTimeoutError,
)
from app.core.logging import get_logger, log_activity_failure
from app.schemas.memory import BreethEpisodeIn, BreethItem, BreethSearchRequest, BreethSearchResult

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Legacy aliases (backward-compat for existing catch-sites)
# ---------------------------------------------------------------------------

class BreethAPIError(Exception):
    """Exception raised for Breeth memory API HTTP or network errors."""


class BreethAuthenticationError(BreethAPIError):
    """Exception raised when Breeth API authentication fails (401/403)."""


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

async def search_memory(
    query: str,
    limit: int = 10,
    min_score: float = 0.5,
    filters: dict[str, Any] | None = None,
) -> BreethSearchResult:
    """Execute associative memory search query against Breeth API POST /v1/search.

    Raises:
        BreethAuthError: API key is invalid or revoked (401/403) — non-retryable.
        BreethServerError: Breeth returned a 5xx response — retryable.
        BreethTimeoutError: Network timeout — retryable.
        BreethClientError: Breeth returned a non-auth 4xx response — non-retryable.

    Returns a fallback empty result when BREETH_API_KEY is not set or the base URL
    contains 'example' (local dev / test mode).
    """
    settings = get_settings()
    api_key = settings.BREETH_API_KEY
    base_url = settings.BREETH_BASE_URL.rstrip("/")

    req_payload = BreethSearchRequest(
        query=query,
        limit=limit,
        min_score=min_score,
        filters=filters or {},
    )

    if not api_key or not base_url or "example" in base_url:
        logger.info(f"Breeth client running in fallback mode for query: '{query}'")
        return BreethSearchResult(results=[], query=query, total=0)

    url = f"{base_url}/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=req_payload.model_dump(), headers=headers)

            if response.status_code in (401, 403):
                exc = BreethAuthError(detail=f"Breeth auth failed: {response.text[:200]}")
                log_activity_failure(
                    logger,
                    activity="search_memory",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 500 <= response.status_code < 600:
                exc = BreethServerError(status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="search_memory",
                    error=exc,
                    retryable=True,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            if 400 <= response.status_code < 500:
                exc = BreethClientError(status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="search_memory",
                    error=exc,
                    retryable=False,
                    extra={"query": query, "status_code": response.status_code},
                )
                raise exc

            response.raise_for_status()

            data = response.json()
            items = [BreethItem(**item) for item in data.get("results", [])]
            return BreethSearchResult(
                results=items,
                query=query,
                total=data.get("total", len(items)),
            )

    except (BreethAuthError, BreethServerError, BreethClientError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = BreethTimeoutError(f"Breeth search timed out for query '{query}': {exc}")
        log_activity_failure(
            logger,
            activity="search_memory",
            error=typed,
            retryable=True,
            extra={"query": query},
        )
        raise typed from exc

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Breeth search failed: {exc}", extra={"query": query})
        raise BreethAPIError(f"Breeth memory search failed: {exc}") from exc


async def list_memory_entities(limit: int = 50) -> list[BreethItem]:
    """Read indexed graph entities exposed by Breeth's entities endpoint."""
    settings = get_settings()
    api_key = settings.BREETH_API_KEY.strip()
    base_url = settings.BREETH_BASE_URL.rstrip("/")
    if not api_key or not base_url or "example" in base_url:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/v1/entities/",
                params={"mode": "narrative"},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            payload = response.json()
            entities = payload.get("narrative", [])
            return [
                BreethItem(
                    id=str(entity.get("uuid") or entity.get("name")),
                    text=str(entity.get("summary") or entity.get("name") or ""),
                    score=float(entity.get("confidence_stored") or 0.0),
                    metadata={
                        "entity_name": entity.get("name"),
                        "degree": entity.get("degree", 0),
                        "narrative": entity.get("narrative"),
                    },
                )
                for entity in entities[:limit]
                if entity.get("name")
            ]
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Breeth entity listing failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# Write episode
# ---------------------------------------------------------------------------

async def write_episode(episode_data: BreethEpisodeIn | dict[str, Any]) -> dict[str, Any]:
    """Persist decision or published post episode payload to Breeth POST /v1/episodes.

    Raises:
        BreethAuthError: API key is invalid or revoked (401/403) — non-retryable.
        BreethServerError: Breeth returned a 5xx response — retryable.
        BreethTimeoutError: Network timeout — retryable.
        BreethClientError: Breeth returned a non-auth 4xx response — non-retryable.

    Returns a fallback result when BREETH_API_KEY is not set (local dev / test mode).
    """
    settings = get_settings()
    api_key = settings.BREETH_API_KEY
    base_url = settings.BREETH_BASE_URL.rstrip("/")

    if isinstance(episode_data, dict):
        episode_payload = BreethEpisodeIn(**episode_data)
    else:
        episode_payload = episode_data

    if not api_key or not base_url or "example" in base_url:
        logger.info(f"Breeth client recorded episode in fallback mode: {episode_payload.topic}")
        return {"status": "recorded_fallback", "topic": episode_payload.topic}

    url = f"{base_url}/v1/episodes"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    **episode_payload.model_dump(exclude_none=True),
                    "content": "\n".join(episode_payload.claims) or episode_payload.topic,
                },
                headers=headers,
            )

            if response.status_code in (401, 403):
                exc = BreethAuthError(detail=f"Breeth auth failed: {response.text[:200]}")
                log_activity_failure(
                    logger,
                    activity="write_episode",
                    error=exc,
                    retryable=False,
                    extra={"status_code": response.status_code},
                )
                raise exc

            if 500 <= response.status_code < 600:
                exc = BreethServerError(status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="write_episode",
                    error=exc,
                    retryable=True,
                    extra={"status_code": response.status_code},
                )
                raise exc

            if 400 <= response.status_code < 500:
                exc = BreethClientError(status_code=response.status_code, detail=response.text[:200])
                log_activity_failure(
                    logger,
                    activity="write_episode",
                    error=exc,
                    retryable=False,
                    extra={"status_code": response.status_code},
                )
                raise exc

            response.raise_for_status()
            return response.json()

    except (BreethAuthError, BreethServerError, BreethClientError):
        raise  # Re-raise typed exceptions unchanged

    except httpx.TimeoutException as exc:
        typed = BreethTimeoutError(f"Breeth write_episode timed out: {exc}")
        log_activity_failure(
            logger,
            activity="write_episode",
            error=typed,
            retryable=True,
        )
        raise typed from exc

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Breeth write_episode failed: {exc}")
        raise BreethAPIError(f"Breeth episode write failed: {exc}") from exc
