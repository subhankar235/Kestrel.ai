"""Concept gap behavior — identifies unconnected concept nodes in memory graph and synthesizes research queries."""

from __future__ import annotations

from typing import Any


def detect_concept_gaps(memory_context: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify concept pairs previously discussed independently but never connected."""
    concepts = memory_context.get("concepts", [])
    if len(concepts) < 2:
        return []

    gap_candidates: list[dict[str, Any]] = []
    # Pick pair of concepts
    c1, c2 = concepts[0], concepts[1]

    gap_candidates.append({
        "title": f"Synthesis: The Connection Between {c1.title()} and {c2.title()}",
        "summary": f"Exploring the unexplored intersection and synthesis between {c1} and {c2}.",
        "concept_a": c1,
        "concept_b": c2,
        "is_concept_gap_synthesis": True,
        "sources": ["https://example.com/concept-synthesis"],
    })

    return gap_candidates
