"""Editorial judge — accepts or rejects candidate topics against constitution thresholds."""

from __future__ import annotations

from typing import Any


def judge_topic_score(scores: dict[str, Any], accept_threshold: float) -> tuple[bool, str]:
    """Return ACCEPT (True) or REJECT (False) decision with reasoning."""
    total = scores.get("total_score", 0.0)
    if total >= accept_threshold:
        return True, f"Score {total} meets threshold {accept_threshold}"
    return False, f"Score {total} below threshold {accept_threshold}"
