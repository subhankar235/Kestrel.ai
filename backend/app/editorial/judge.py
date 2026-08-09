"""Editorial judge — accepts or rejects candidate topics against constitution thresholds.

Phase 22: emits structured JSON log for every ACCEPT/REJECT decision with full score
breakdown and reasoning text, making editorial decisions inspectable per PRD Transparency NFR.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def judge_topic_score(
    scores: dict[str, Any],
    accept_threshold: float = 60.0,
    topic_title: str | None = None,
) -> tuple[bool, str]:
    """Return ACCEPT (True) or REJECT (False) decision with clear reasoning text."""
    total_score = float(scores.get("total_score", 0.0))
    llm_reasoning = str(scores.get("reasoning", ""))
    title = topic_title or str(scores.get("topic") or "Unknown Topic")

    if total_score >= accept_threshold:
        reason = f"ACCEPTED: Total score {total_score:.1f} meets constitution threshold {accept_threshold:.1f}. {llm_reasoning}".strip()
        logger.info(
            f"Editorial decision: ACCEPT for topic '{title}'",
            extra={
                "event": "editorial_decision",
                "decision": "ACCEPT",
                "topic": title,
                "total_score": total_score,
                "accept_threshold": accept_threshold,
                "relevance_score": scores.get("relevance_score"),
                "novelty_score": scores.get("novelty_score"),
                "evidence_score": scores.get("evidence_score"),
                "persona_fit_score": scores.get("persona_fit_score"),
                "hype_penalty": scores.get("hype_penalty"),
                "repetition_penalty": scores.get("repetition_penalty"),
                "reasoning": llm_reasoning,
            },
        )
        return True, reason

    reason = f"REJECTED: Total score {total_score:.1f} is below constitution threshold {accept_threshold:.1f}. {llm_reasoning}".strip()
    logger.info(
        f"Editorial decision: REJECT for topic '{title}'",
        extra={
            "event": "editorial_decision",
            "decision": "REJECT",
            "topic": title,
            "total_score": total_score,
            "accept_threshold": accept_threshold,
            "relevance_score": scores.get("relevance_score"),
            "novelty_score": scores.get("novelty_score"),
            "evidence_score": scores.get("evidence_score"),
            "persona_fit_score": scores.get("persona_fit_score"),
            "hype_penalty": scores.get("hype_penalty"),
            "repetition_penalty": scores.get("repetition_penalty"),
            "reasoning": llm_reasoning,
        },
    )
    return False, reason

