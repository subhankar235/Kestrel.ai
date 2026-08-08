"""Prompt builder for periodic agent self-audit and constitution rule tuning."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_self_audit_prompt(
    history: list[dict[str, Any]],
    constitution: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for periodic self-audit."""
    system_prompt = (
        "You are an AI agent meta-auditor reviewing published and rejected post history. "
        "Analyze editorial performance and propose adjustments to constitution rules or thresholds if needed. "
        "Return valid JSON containing 'audit_passed': boolean, 'summary': string, "
        "and 'proposed_rule_updates': dict of updated threshold rules."
    )

    sanitized_history = []
    for item in history[:20]:  # Limit history window size
        sanitized_history.append({
            "type": item.get("type", "published"),
            "title": sanitize_untrusted_input(str(item.get("title", "")), max_chars=150),
            "score": item.get("score"),
            "decision": item.get("decision"),
        })

    user_payload = {
        "publication_history": sanitized_history,
        "current_constitution": constitution.get("rules", {}),
    }

    user_prompt = (
        "Perform a self-audit over the recent publication history:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
