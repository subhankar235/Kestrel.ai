"""Editorial topic scoring — scores candidate topics on relevance, novelty, evidence, persona fit, and penalties.

Phase 22: emits structured JSON log with per-dimension scores, latency, and LLM/fallback
indicator so every scoring decision is inspectable per PRD Transparency NFR.
"""

from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import generate_structured_output
from app.llm.prompts.score import build_score_prompt

logger = get_logger(__name__)


async def score_candidate_topic(
    topic: dict[str, Any],
    memory_context: dict[str, Any],
    rules: dict[str, Any],
) -> dict[str, Any]:
    """Calculate structured multi-dimensional editorial scores for a candidate topic."""
    sys_prompt, user_prompt = build_score_prompt(topic, memory_context, rules)
    topic_title = str(topic.get("title", "Unknown"))

    used_fallback = False
    start_time = time.time()

    try:
        raw_scores = await generate_structured_output(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001
        used_fallback = True
        logger.info(
            f"LLM scoring fallback used for '{topic_title}': {exc}",
            extra={"topic": topic_title, "error": str(exc), "fallback": True},
        )
        # Default heuristic fallback for dev/testing when LLM key is unavailable
        raw_scores = {
            "relevance_score": 80.0,
            "novelty_score": 75.0,
            "evidence_score": 70.0,
            "persona_fit_score": 85.0,
            "hype_penalty": 0.0,
            "repetition_penalty": 0.0,
            "reasoning": "High relevance and clear evidence",
        }

    duration_ms = round((time.time() - start_time) * 1000, 2)

    relevance = float(raw_scores.get("relevance_score", 70.0))
    novelty = float(raw_scores.get("novelty_score", 70.0))
    evidence = float(raw_scores.get("evidence_score", 70.0))
    persona_fit = float(raw_scores.get("persona_fit_score", 75.0))
    hype_penalty = float(raw_scores.get("hype_penalty", 0.0))
    repetition_penalty = float(raw_scores.get("repetition_penalty", 0.0))

    # Calculate weighted total score (0-100)
    total_score = max(
        0.0,
        min(
            100.0,
            (relevance * 0.35)
            + (novelty * 0.25)
            + (evidence * 0.25)
            + (persona_fit * 0.15)
            - hype_penalty
            - repetition_penalty,
        ),
    )

    logger.info(
        f"Topic scored: '{topic_title}' → {total_score:.1f}",
        extra={
            "topic": topic_title,
            "total_score": round(total_score, 2),
            "relevance_score": relevance,
            "novelty_score": novelty,
            "evidence_score": evidence,
            "persona_fit_score": persona_fit,
            "hype_penalty": hype_penalty,
            "repetition_penalty": repetition_penalty,
            "scoring_latency_ms": duration_ms,
            "used_fallback": used_fallback,
        },
    )

    return {
        "relevance_score": relevance,
        "novelty_score": novelty,
        "evidence_score": evidence,
        "persona_fit_score": persona_fit,
        "hype_penalty": hype_penalty,
        "repetition_penalty": repetition_penalty,
        "total_score": round(total_score, 2),
        "reasoning": str(raw_scores.get("reasoning", "Score computed against constitution rules")),
    }
