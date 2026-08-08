"""Prompt builder for post selection rationale generation."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_rationale_prompt(
    topic: dict[str, Any],
    memory_context: dict[str, Any],
    winning_draft: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for rationale generation."""
    system_prompt = (
        "You are an AI agent transparency engine. "
        "Construct a clear 1-2 sentence rationale explaining why this post was chosen, "
        "how it relates to past memory or current research, and why it is published now. "
        "Return valid JSON containing 'rationale': string."
    )

    safe_title = sanitize_untrusted_input(str(topic.get("title", "")), max_chars=200)
    safe_post_text = sanitize_untrusted_input(str(winning_draft.get("post_text", "") or winning_draft.get("text", "")), max_chars=1000)

    user_payload = {
        "topic_title": safe_title,
        "winning_post_text": safe_post_text,
        "memory_context": {
            "related_stories": memory_context.get("stories", []),
            "past_beliefs": memory_context.get("beliefs", []),
        },
    }

    user_prompt = (
        "Generate a publication rationale for this post:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
