"""Prompt builder for draft self-critique and winning draft selection."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_critique_prompt(
    drafts: list[dict[str, Any]],
    persona: dict[str, Any],
    constitution_rules: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for draft critique and ranking."""
    system_prompt = (
        "You are an incisive editorial chief evaluating candidate post drafts. "
        "Critique each draft for clarity, persona voice match, accuracy, and engagement. "
        "Select the winning draft and return valid JSON containing 'winning_index' (integer 0-based), "
        "'critique_notes' (string), and 'winning_draft' (object with 'text', 'angle_name', 'sources')."
    )

    sanitized_drafts = []
    for idx, d in enumerate(drafts):
        sanitized_drafts.append({
            "index": idx,
            "angle_name": str(d.get("angle_name", f"Angle {idx+1}")),
            "post_text": sanitize_untrusted_input(str(d.get("post_text", "")), max_chars=1000),
            "sources": d.get("sources", []),
        })

    user_payload = {
        "candidate_drafts": sanitized_drafts,
        "persona": {
            "name": persona.get("name", "Ada"),
            "domain": persona.get("domain", "AI Security"),
        },
        "constitution_rules": constitution_rules,
    }

    user_prompt = (
        "Critique the following candidate drafts and select the winning post:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
