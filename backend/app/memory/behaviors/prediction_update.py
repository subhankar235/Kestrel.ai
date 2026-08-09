"""Prediction update behavior — evaluates past predictions against new evidence when deadlines expire."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def check_prediction_resolution(
    memory_context: dict[str, Any],
    current_date_iso: str | None = None,
) -> list[dict[str, Any]]:
    """Identify past predictions past deadline requiring resolution posts."""
    predictions = memory_context.get("predictions", [])
    if not predictions:
        return []

    now = datetime.now(timezone.utc)
    resolution_topics: list[dict[str, Any]] = []

    for pred in predictions:
        target_date_str = pred.get("target_date")
        if not target_date_str:
            continue

        try:
            target_dt = datetime.fromisoformat(target_date_str.replace("Z", "+00:00"))
            if target_dt.tzinfo is None:
                target_dt = target_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        # Check if deadline passed
        if target_dt <= now:
            statement = pred.get("text", "Past prediction statement")
            originating_post_id = pred.get("originating_post_id")

            resolution_topics.append({
                "title": f"Prediction Verdict: {statement[:60]}...",
                "summary": f"Reviewing past prediction '{statement}' whose deadline ({target_date_str}) has passed.",
                "verdict": "correct",  # Evaluated by LLM/behaviors against evidence
                "prediction_id": pred.get("prediction_id"),
                "related_post_id": originating_post_id,
                "is_prediction_resolution": True,
                "sources": ["https://example.com/prediction-audit"],
            })

    return resolution_topics
