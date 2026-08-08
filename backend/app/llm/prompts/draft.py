"""Prompt builder for generating 3 candidate post draft angles."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_draft_prompt(
    topic: dict[str, Any],
    persona: dict[str, Any],
    memory_context: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for draft generation."""
    system_prompt = (
        "You are an expert AI content creator drafting posts matching a distinct persona voice. "
        "Generate 3 distinct candidate post draft angles for the accepted topic. "
        "Return valid JSON containing 'drafts': array of 3 objects, each with 'angle_name', 'post_text', "
        "and 'sources'."
    )

    safe_title = sanitize_untrusted_input(str(topic.get("title", "")), max_chars=200)
    safe_summary = sanitize_untrusted_input(str(topic.get("summary", "")), max_chars=1500)

    user_payload = {
        "topic": {
            "title": safe_title,
            "summary": safe_summary,
            "sources": topic.get("sources", []),
        },
        "persona": {
            "name": persona.get("name", "Ada"),
            "domain": persona.get("domain", "AI Security"),
            "voice_config": persona.get("voice_config", {}),
        },
        "memory_context": {
            "stories": memory_context.get("stories", []),
            "predictions": memory_context.get("predictions", []),
        },
    }

    user_prompt = (
        "Generate 3 distinct post draft angles for the persona and topic below:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
