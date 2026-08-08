"""Prompt builder for editorial topic scoring against constitution thresholds and memory context."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_score_prompt(
    topic: dict[str, Any],
    memory_context: dict[str, Any],
    constitution_rules: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for editorial topic scoring."""
    system_prompt = (
        "You are an expert editorial judge for an autonomous AI creator agent. "
        "Score candidate topics strictly against constitution threshold rules and past memory context. "
        "Return valid JSON containing: 'relevance_score' (0-100), 'novelty_score' (0-100), "
        "'evidence_score' (0-100), 'hype_penalty' (0-20), 'total_score' (0-100), "
        "'accepted' (boolean), and 'reasoning' (string)."
    )

    safe_title = sanitize_untrusted_input(str(topic.get("title", "")), max_chars=200)
    safe_summary = sanitize_untrusted_input(str(topic.get("summary", "")), max_chars=1500)

    user_payload = {
        "topic": {
            "title": safe_title,
            "summary": safe_summary,
            "sources": topic.get("sources", []),
        },
        "memory_context": {
            "related_stories": memory_context.get("stories", []),
            "past_beliefs": memory_context.get("beliefs", []),
            "past_rejected_topics": memory_context.get("rejected_topics", []),
        },
        "constitution_rules": constitution_rules,
    }

    user_prompt = (
        "Evaluate and score the following candidate topic using the provided memory context and constitution rules:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
