"""Centralized AsyncOpenAI / OpenRouter client wrapper with structured JSON enforcement, exponential backoff retries, and prompt injection defense."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


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


def get_async_openai_client() -> AsyncOpenAI:
    """Instantiate AsyncOpenAI client configured for OpenAI or OpenRouter."""
    settings = get_settings()
    api_key = settings.llm_api_key or "mock-key-for-testing"
    base_url = settings.llm_base_url

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
) -> dict[str, Any]:
    """Execute LLM chat completion in structured JSON output mode with exponential backoff retries."""
    settings = get_settings()
    selected_model = model or settings.OPENAI_MODEL
    client = get_async_openai_client()

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
            logger.warning(
                f"LLM call attempt {attempt}/{max_retries} failed: {exc}",
                extra={"attempt": attempt, "error": str(exc)},
            )
            if attempt < max_retries:
                backoff_seconds = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff_seconds)

    logger.error(
        "All LLM call retries exhausted",
        extra={"max_retries": max_retries, "error": str(last_exception)},
    )
    raise RuntimeError(f"Failed to generate LLM structured output after {max_retries} retries: {last_exception}") from last_exception
