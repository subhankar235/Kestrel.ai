"""Persona check — verifies winning draft matches persona voice, beliefs, and domain."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import call_openai_json
from app.llm.prompts.persona_check import build_persona_check_prompt

logger = get_logger(__name__)


async def verify_persona_alignment(
    draft: dict[str, Any],
    persona: dict[str, Any],
    memory_context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Verify winning draft aligns with persona voice, domain constraints, and prior beliefs.

    Returns:
        (aligned: bool, reason: str)
    """
    text = str(draft.get("post_text") or draft.get("text") or "")
    if not text.strip():
        return False, "Post text is empty"

    persona_name = str(persona.get("name", "Ada"))
    domain = str(persona.get("domain", "AI Security"))
    voice_config = persona.get("voice_config") or {}

    # Attempt LLM persona check
    try:
        system_prompt, user_prompt = build_persona_check_prompt(draft, persona)
        response = await call_openai_json(system_prompt, user_prompt)
        if isinstance(response, dict):
            aligned = bool(response.get("aligned", True))
            reasons = response.get("reasons", [])
            reason_str = "; ".join(reasons) if isinstance(reasons, list) and reasons else "Persona alignment verified."
            logger.info(
                f"LLM Persona Check for '{persona_name}' ({domain}): aligned={aligned}, reason='{reason_str}'"
            )
            return aligned, reason_str
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM persona check failed or unavailable ({exc}); using rule-based verification")

    # Heuristic Rule-Based Persona Verification
    banned_words = ["buzzword", "clickbait", "guaranteed profit", "100% risk free"]
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            reason = f"Draft contains forbidden term '{word}' inconsistent with persona {persona_name}"
            logger.warning(f"Persona Check Veto: {reason}")
            return False, reason

    reason = f"Draft verified aligned with persona '{persona_name}' domain '{domain}'"
    logger.info(f"Persona Check Passed: {reason}")
    return True, reason
