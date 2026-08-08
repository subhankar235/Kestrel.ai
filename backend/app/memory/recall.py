"""Recall engine — runs memory search and constructs MemoryContext before editorial judgment.

Phase 22: emits structured JSON log for every Breeth search call with latency, result count,
and classified memory items (stories/beliefs/predictions/concepts) for full pipeline
traceability per PRD Transparency NFR.
"""

from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.memory.breeth_client import search_memory

logger = get_logger(__name__)


async def recall_memory_context(topic: dict[str, Any]) -> dict[str, Any]:
    """Search Breeth memory and assemble structured MemoryContext for editorial scoring and behaviors."""
    query = str(topic.get("title") or topic.get("summary") or "AI Research")

    start_time = time.time()
    search_result = await search_memory(query, limit=10, min_score=0.4)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    stories: list[dict[str, Any]] = []
    beliefs: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    rejected_topics: list[dict[str, Any]] = []
    concepts: set[str] = set()

    for item in search_result.results:
        metadata = item.metadata or {}
        concepts.update(item.concepts)

        # Classify item metadata
        if metadata.get("story") or item.stories:
            story_info = metadata.get("story") if isinstance(metadata.get("story"), dict) else {}
            stories.append({
                "story_id": story_info.get("id") or f"story_{item.id}",
                "title": story_info.get("title") or item.text,
                "chapter": int(story_info.get("chapter", 1)),
                "open_questions": item.open_questions or story_info.get("open_questions", []),
                "originating_post_id": story_info.get("originating_post_id") or metadata.get("related_post_id"),
            })

        if metadata.get("prediction"):
            pred_info = metadata.get("prediction") if isinstance(metadata.get("prediction"), dict) else {}
            predictions.append({
                "prediction_id": pred_info.get("id") or f"pred_{item.id}",
                "text": item.text,
                "target_date": pred_info.get("target_date"),
                "status": pred_info.get("status", "active"),
                "originating_post_id": metadata.get("related_post_id"),
            })

        if metadata.get("editorial_decision") == "rejected":
            rejected_topics.append({
                "title": item.text,
                "rejection_reason": metadata.get("rejection_reason", "Low relevance"),
                "revisit_condition": metadata.get("revisit_condition", "Revisit on new evidence"),
            })
        elif item.text:
            beliefs.append({"statement": item.text, "score": item.score})

    sorted_concepts = sorted(list(concepts))

    logger.info(
        f"Breeth memory search completed for '{query}' [{latency_ms:.1f}ms]",
        extra={
            "event": "breeth_search",
            "query": query,
            "latency_ms": latency_ms,
            "breeth_latency_ms": latency_ms,
            "result_count": len(search_result.results),
            "total_recalled": len(search_result.results),
            "stories_count": len(stories),
            "beliefs_count": len(beliefs),
            "predictions_count": len(predictions),
            "rejected_topics_count": len(rejected_topics),
            "concepts_count": len(sorted_concepts),
        },
    )


    return {
        "query": query,
        "stories": stories,
        "beliefs": beliefs,
        "predictions": predictions,
        "rejected_topics": rejected_topics,
        "concepts": sorted_concepts,
        "total_recalled": len(search_result.results),
    }
