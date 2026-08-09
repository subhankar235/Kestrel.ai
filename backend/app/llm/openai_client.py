"""Centralized AsyncOpenAI / OpenRouter client wrapper with structured JSON enforcement,
exponential backoff retries, and prompt injection defense.

Phase 21: raises typed LLMAuthError / LLMServerError / LLMTimeoutError instead of bare
RuntimeError so Temporal's RetryPolicy can distinguish retryable from non-retryable failures.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import LLMAuthError, LLMClientError, LLMServerError, LLMTimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)

ProviderConfig = tuple[str, str, str | None, str]


def sanitize_untrusted_input(text: str, max_chars: int = 4000) -> str:
    """Sanitize and truncate raw web/feed text to prevent prompt injection attacks.

    1. Truncates text to max_chars.
    2. Neutralizes prompt delimiter breakouts (e.g. triple backticks).
    3. Strips unprintable control characters.
    """
    if not text:
        return ""

    # Truncate
    truncated = text[:max_chars]

    # Neutralize markdown fenced code block injection
    safe_text = truncated.replace("```", "'''")

    # Strip control characters (keep tab, newline, carriage return)
    safe_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", safe_text)

    return safe_text.strip()


def _provider_configs(settings: Any) -> list[ProviderConfig]:
    """Return configured providers in fallback order."""
    providers: list[ProviderConfig] = []
    if settings.OPENROUTER_API_KEY.strip():
        providers.append(("openrouter", settings.OPENROUTER_API_KEY.strip(), settings.OPENROUTER_BASE_URL.strip(), settings.OPENROUTER_MODEL.strip() or "openrouter/free"))
    if settings.GEMINI_API_KEY.strip():
        providers.append(("gemini", settings.GEMINI_API_KEY.strip(), settings.GEMINI_BASE_URL.strip(), settings.GEMINI_MODEL.strip()))
    if settings.GROQ_API_KEY.strip():
        providers.append(("groq", settings.GROQ_API_KEY.strip(), settings.GROQ_BASE_URL.strip(), settings.GROQ_MODEL.strip()))
    return providers or [("mock", "mock-key-for-testing", None, settings.OPENAI_MODEL.strip())]


def get_async_openai_client(provider: ProviderConfig | None = None) -> AsyncOpenAI:
    """Instantiate an OpenAI-compatible client for the selected provider."""
    settings = get_settings()
    selected = provider or _provider_configs(settings)[0]
    _, api_key, base_url, _ = selected

    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )


async def generate_structured_output(
    prompt: str,
    system_prompt: str = "You are a structured AI assistant. Always output valid, parseable JSON.",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    max_retries: int = 3,
    _provider_index: int = 0,
) -> dict[str, Any]:
    """Execute LLM chat completion in structured JSON output mode with exponential backoff retries.

    Raises:
        LLMAuthError: API key is invalid or revoked (401) — non-retryable.
        LLMClientError: Bad request / unsupported model (4xx, not 401) — non-retryable.
        LLMServerError: Provider returned a 5xx error — retryable.
        LLMTimeoutError: Request timed out — retryable.
        RuntimeError: All retries exhausted for retryable errors.
    """
    settings = get_settings()
    providers = _provider_configs(settings)
    provider = providers[min(_provider_index, len(providers) - 1)]
    provider_name, _, _, provider_model = provider
    selected_model = model or provider_model
    client = get_async_openai_client(provider)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    last_exception: Exception | None = None
    start_time = time.time()

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Executing LLM request",
                extra={
                    "attempt": attempt,
                    "provider": provider_name,
                    "model": selected_model,
                    "prompt_length": len(prompt),
                },
            )

            response = await client.chat.completions.create(
                model=selected_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=max_tokens,
            )

            duration_ms = round((time.time() - start_time) * 1000, 2)
            content = response.choices[0].message.content or "{}"
            usage = response.usage

            logger.info(
                "LLM call completed",
                extra={
                    "model": selected_model,
                    "duration_ms": duration_ms,
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
                },
            )

            parsed_json = json.loads(content)
            return parsed_json

        except Exception as exc:  # noqa: BLE001
            last_exception = exc
            exc_str = str(exc)

            # Classify the error type from the exception message / type
            if _is_auth_error(exc):
                typed = LLMAuthError(detail=exc_str[:300])
                logger.error(
                    f"LLM auth error (non-retryable): {exc}",
                    extra={"attempt": attempt, "error": exc_str},
                )
                if _provider_index + 1 < len(providers):
                    break
                raise typed from exc

            if _is_client_error(exc):
                status = _extract_status_code(exc)
                typed_client = LLMClientError(status_code=status, detail=exc_str[:300])
                logger.error(
                    f"LLM client error (non-retryable): {exc}",
                    extra={"attempt": attempt, "error": exc_str},
                )
                if _provider_index + 1 < len(providers):
                    break
                raise typed_client from exc

            if _is_server_error(exc):
                status = _extract_status_code(exc)
                # Server errors are retryable
                logger.warning(
                    f"LLM server error attempt {attempt}/{max_retries}: {exc}",
                    extra={"attempt": attempt, "error": exc_str},
                )
                if attempt < max_retries:
                    backoff_seconds = 0.5 * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff_seconds)
                    continue
                raise LLMServerError(status_code=status, detail=exc_str[:300]) from exc

            # Generic / unknown errors — log and retry with backoff
            logger.warning(
                f"LLM call attempt {attempt}/{max_retries} failed: {exc}",
                extra={"attempt": attempt, "error": exc_str},
            )
            if attempt < max_retries:
                backoff_seconds = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff_seconds)

    if _provider_index + 1 < len(providers):
        next_provider = providers[_provider_index + 1][0]
        logger.warning(
            f"LLM provider {provider_name} exhausted; falling back to {next_provider}"
        )
        return await generate_structured_output(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            _provider_index=_provider_index + 1,
        )

    logger.error(
        "All LLM call retries exhausted",
        extra={"max_retries": max_retries, "error": str(last_exception)},
    )
    raise RuntimeError(f"Failed to generate LLM structured output after {max_retries} retries: {last_exception}") from last_exception


# ---------------------------------------------------------------------------
# Helpers: error classification from openai SDK exceptions
# ---------------------------------------------------------------------------


def _extract_status_code(exc: Exception) -> int:
    """Extract HTTP status code from an openai SDK error, defaulting to 0."""
    return getattr(exc, "status_code", 0) or 0


def _is_auth_error(exc: Exception) -> bool:
    """Return True if the exception represents a 401 auth failure."""
    status = _extract_status_code(exc)
    if status == 401:
        return True
    # Fallback: check string representation for common auth error markers
    exc_str = str(exc).lower()
    return "invalid_api_key" in exc_str or "incorrect api key" in exc_str


def _is_client_error(exc: Exception) -> bool:
    """Return True if the exception represents a non-auth 4xx client error."""
    status = _extract_status_code(exc)
    return 400 <= status < 500 and status != 401


def _is_server_error(exc: Exception) -> bool:
    """Return True if the exception represents a 5xx server error."""
    status = _extract_status_code(exc)
    return 500 <= status < 600


# ---------------------------------------------------------------------------
# Convenience alias used by drafting / publishing modules
# ---------------------------------------------------------------------------


async def call_openai_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Execute LLM chat completion with system and user prompts returning parsed JSON dict."""
    return await generate_structured_output(prompt=user_prompt, system_prompt=system_prompt)
