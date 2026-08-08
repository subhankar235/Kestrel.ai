"""Prompt builder for verifying winning draft persona alignment."""

from __future__ import annotations

import json
from typing import Any

from app.llm.openai_client import sanitize_untrusted_input


def build_persona_check_prompt(
    draft: dict[str, Any],
    persona: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for persona alignment check."""
    system_prompt = (
        "You are a strict brand and persona compliance auditor. "
        "Verify whether the selected post draft adheres to the persona's specified voice, tone, and domain. "
        "Return valid JSON containing 'aligned': boolean, 'voice_match_score': float (0-100), "
        "and 'reasons': array of strings."
    )

    safe_text = sanitize_untrusted_input(str(draft.get("post_text", "") or draft.get("text", "")), max_chars=1500)

    user_payload = {
        "post_draft": safe_text,
        "persona": {
            "name": persona.get("name", "Ada"),
            "domain": persona.get("domain", "AI Security"),
            "voice_config": persona.get("voice_config", {}),
        },
    }

    user_prompt = (
        "Check persona voice and domain alignment for the following post draft:\n"
        f"{json.dumps(user_payload, indent=2)}"
    )

    return system_prompt, user_prompt
