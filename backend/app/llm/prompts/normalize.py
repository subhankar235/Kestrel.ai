"""Prompt builder for raw scraped content normalization into candidate topic schema."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_normalize_prompt(raw_item: dict[str, Any]) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for topic normalization."""
    system_prompt = (
        "You are an expert news and research content normalizer. "
        "Extract key information from raw web text and format as structured JSON containing "
        "'title', 'summary', 'source_url', 'claims', 'concepts', and 'raw_quality_score' (0-100)."
    )

    safe_title = sanitize_untrusted_input(str(raw_item.get("title", "")), max_chars=200)
    safe_body = sanitize_untrusted_input(str(raw_item.get("body", "") or raw_item.get("content", "")), max_chars=3000)
    safe_url = sanitize_untrusted_input(str(raw_item.get("url", "") or raw_item.get("source_url", "")), max_chars=500)

    user_payload = {
        "title": safe_title,
        "content": safe_body,
        "source_url": safe_url,
    }

    user_prompt = f"Normalize the following raw web discovery item into structured JSON:\n{json.dumps(user_payload, indent=2)}"

    return system_prompt, user_prompt
