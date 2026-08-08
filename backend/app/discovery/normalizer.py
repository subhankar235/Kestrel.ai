"""Raw source result normalizer — turns scraped web data into structured Topic payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import generate_structured_output
from app.llm.prompts.normalize import build_normalize_prompt

logger = get_logger(__name__)


async def normalize_raw_content(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize raw discovery items into structured topic dicts."""
    if not raw_items:
        return []

    normalized_topics: list[dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for raw in raw_items[:10]:  # Limit batch size to top 10 items
        try:
            sys_prompt, user_prompt = build_normalize_prompt(raw)

            # In dev/testing fallback without active LLM key, format directly
            try:
                parsed = await generate_structured_output(
                    prompt=user_prompt,
                    system_prompt=sys_prompt,
                    temperature=0.3,
                )
            except Exception as exc:  # noqa: BLE001
                logger.info(f"LLM normalization fallback used: {exc}")
                parsed = {
                    "title": str(raw.get("title", "Discovery Item")),
                    "summary": str(raw.get("body", "") or raw.get("title", ""))[:300],
                    "claims": ["Discovered fresh research content"],
                    "entities": [raw.get("source", "web")],
                    "sources": [raw.get("url")] if raw.get("url") else [],
                }

            source_url = raw.get("url")
            sources = parsed.get("sources") or ([source_url] if source_url else [])

            normalized_topics.append({
                "title": str(parsed.get("title") or raw.get("title", "Untitled Topic")),
                "summary": str(parsed.get("summary") or raw.get("body", "")),
                "claims": parsed.get("claims") if isinstance(parsed.get("claims"), list) else [],
                "entities": parsed.get("entities") if isinstance(parsed.get("entities"), list) else [],
                "sources": sources if isinstance(sources, list) else [str(sources)],
                "timestamp": now_iso,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to normalize discovery item '{raw.get('title')}': {exc}")

    return normalized_topics
