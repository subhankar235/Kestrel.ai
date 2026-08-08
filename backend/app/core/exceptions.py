"""Typed exception hierarchy for Kestrel — distinguishes retryable from non-retryable failures.

Retryable errors (transient — Temporal should retry):
  - DiscoveryTimeoutError
  - DiscoveryServerError
  - LLMTimeoutError
  - LLMServerError
  - BreethTimeoutError
  - BreethServerError

Non-retryable errors (permanent — Temporal must NOT retry, fail fast):
  - DiscoveryAuthError
  - DiscoveryClientError
  - LLMAuthError
  - LLMClientError
  - BreethAuthError
  - BreethClientError
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class KestrelError(Exception):
    """Root exception for all application-level errors."""


# ---------------------------------------------------------------------------
# Discovery source errors
# ---------------------------------------------------------------------------


class DiscoveryError(KestrelError):
    """Base class for all discovery-source failures."""


class DiscoveryTimeoutError(DiscoveryError):
    """Retryable: network timeout talking to a discovery source (Exa, Tavily, GitHub, RSS)."""


class DiscoveryServerError(DiscoveryError):
    """Retryable: 5xx response from a discovery source."""

    def __init__(self, source: str, status_code: int, detail: str = "") -> None:
        self.source = source
        self.status_code = status_code
        super().__init__(f"{source} server error {status_code}: {detail}")


class DiscoveryClientError(DiscoveryError):
    """Non-retryable: 4xx (bad request) response from a discovery source."""

    def __init__(self, source: str, status_code: int, detail: str = "") -> None:
        self.source = source
        self.status_code = status_code
        super().__init__(f"{source} client error {status_code}: {detail}")


class DiscoveryAuthError(DiscoveryError):
    """Non-retryable: 401/403 auth failure on a discovery source — API key invalid or revoked."""

    def __init__(self, source: str, detail: str = "") -> None:
        self.source = source
        super().__init__(f"{source} auth error (401/403): {detail}")


# ---------------------------------------------------------------------------
# LLM / OpenAI errors
# ---------------------------------------------------------------------------


class LLMError(KestrelError):
    """Base class for all LLM call failures."""


class LLMTimeoutError(LLMError):
    """Retryable: LLM call timed out."""


class LLMServerError(LLMError):
    """Retryable: LLM provider returned a 5xx error."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"LLM server error {status_code}: {detail}")


class LLMClientError(LLMError):
    """Non-retryable: malformed request / unsupported model (4xx, not 401)."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"LLM client error {status_code}: {detail}")


class LLMAuthError(LLMError):
    """Non-retryable: 401 invalid API key from LLM provider."""

    def __init__(self, detail: str = "") -> None:
        super().__init__(f"LLM auth error (401): {detail}")


# ---------------------------------------------------------------------------
# Breeth memory errors
# ---------------------------------------------------------------------------


class BreethError(KestrelError):
    """Base class for all Breeth memory API failures."""


class BreethTimeoutError(BreethError):
    """Retryable: Breeth API call timed out."""


class BreethServerError(BreethError):
    """Retryable: Breeth returned a 5xx error."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"Breeth server error {status_code}: {detail}")


class BreethClientError(BreethError):
    """Non-retryable: Breeth returned a 4xx error (bad request)."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"Breeth client error {status_code}: {detail}")


class BreethAuthError(BreethError):
    """Non-retryable: 401/403 auth failure against Breeth — API key invalid or revoked."""

    def __init__(self, detail: str = "") -> None:
        super().__init__(f"Breeth auth error (401/403): {detail}")


# ---------------------------------------------------------------------------
# Self-audit errors
# ---------------------------------------------------------------------------


class SelfAuditError(KestrelError):
    """Raised when the self-audit cycle fails; caught by the workflow to skip versioning gracefully."""


# ---------------------------------------------------------------------------
# Helper: classify httpx HTTP status into typed exceptions
# ---------------------------------------------------------------------------


def classify_http_error(source: str, status_code: int, detail: str = "") -> DiscoveryError:
    """Convert an HTTP status code from a discovery source into the correct typed exception."""
    if status_code in (401, 403):
        return DiscoveryAuthError(source=source, detail=detail)
    if 400 <= status_code < 500:
        return DiscoveryClientError(source=source, status_code=status_code, detail=detail)
    if 500 <= status_code < 600:
        return DiscoveryServerError(source=source, status_code=status_code, detail=detail)
    return DiscoveryError(f"{source} unexpected HTTP {status_code}: {detail}")
