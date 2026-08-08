"""Editorial constitution rules, default threshold configurations, and rule definitions."""

from __future__ import annotations

from typing import Any


def get_default_constitution_rules() -> dict[str, Any]:
    """Return initial v1.0 editorial constitution rule thresholds."""
    return {
        "relevance_threshold": 60.0,
        "novelty_threshold": 50.0,
        "evidence_threshold": 50.0,
        "hype_penalty_max": 20.0,
    }
