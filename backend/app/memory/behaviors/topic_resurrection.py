"""Topic resurrection behavior — re-evaluates rejected topic debt when new evidence arrives."""

from __future__ import annotations

from typing import Any


def evaluate_topic_resurrection(
    candidate_topic: dict[str, Any],
    topic_debt_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Evaluate whether new topic evidence satisfies stored revisit conditions from past rejections."""
    if not topic_debt_items:
        return None

    cand_title = str(candidate_topic.get("title", "")).lower()
    cand_summary = str(candidate_topic.get("summary", "")).lower()

    for debt in topic_debt_items:
        debt_title = str(debt.get("title", "")).lower()
        revisit_condition = debt.get("revisit_condition", "Revisit on new evidence")

        # Check title similarity
        title_words = [w for w in debt_title.split() if len(w) > 4]
        matches = any(w in cand_title or w in cand_summary for w in title_words)

        if matches:
            return {
                "resurrected": True,
                "original_topic_id": debt.get("id"),
                "original_title": debt.get("title"),
                "rejection_reason": debt.get("rejection_reason", "Previously below threshold"),
                "revisit_condition": revisit_condition,
                "resurrection_note": f"Resurrected previously rejected topic '{debt.get('title')}' as new evidence arrived.",
            }

    return None
