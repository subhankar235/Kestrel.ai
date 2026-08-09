"""Episode writer — constructs and writes post/decision episodes back into Breeth memory.

Phase 22: emits structured JSON log for every Breeth episode write with latency, topic,
decision type, and story/prediction metadata for full pipeline traceability.
"""

from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.memory.breeth_client import write_episode
from app.schemas.memory import BreethEpisodeIn

logger = get_logger(__name__)


async def record_decision_episode(decision_data: dict[str, Any]) -> dict[str, Any]:
    """Persist decision or published post episode payload to Breeth memory."""
    topic_data = decision_data.get("topic", {})
    item_data = decision_data.get("item", {})
    decision = str(decision_data.get("decision", "accepted"))

    topic_title = str(topic_data.get("title") or item_data.get("title") or "Research Update")
    sources = topic_data.get("sources") or item_data.get("sources") or []

    # Story information if present
    story_info = None
    has_story = False
    if item_data.get("is_story_continuation") or topic_data.get("is_story_continuation"):
        has_story = True
        story_info = {
            "id": item_data.get("story_id") or topic_data.get("story_id"),
            "chapter": item_data.get("next_chapter") or topic_data.get("next_chapter", 2),
            "title": topic_title,
        }

    # Prediction information if present
    prediction_info = None
    has_prediction = False
    if item_data.get("is_prediction") or topic_data.get("prediction"):
        has_prediction = True
        prediction_info = topic_data.get("prediction") or {"text": topic_title, "status": "active"}

    episode_payload = BreethEpisodeIn(
        topic=topic_title,
        claims=topic_data.get("claims", []),
        stance=item_data.get("stance", "neutral"),
        prediction=prediction_info,
        story=story_info,
        open_question=topic_data.get("open_question"),
        concepts=topic_data.get("concepts", []),
        sources=sources if isinstance(sources, list) else [str(sources)],
        related_posts=[str(item_data.get("post_id"))] if item_data.get("post_id") else [],
        editorial_decision=decision,
    )

    start_time = time.time()
    result = await write_episode(episode_payload)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"Breeth episode written: '{topic_title}' [{decision}] [{latency_ms:.1f}ms]",
        extra={
            "event": "breeth_episode_write",
            "topic": topic_title,
            "editorial_decision": decision,
            "latency_ms": latency_ms,
            "breeth_write_latency_ms": latency_ms,
            "has_story": has_story,
            "has_prediction": has_prediction,
            "sources_count": len(sources) if isinstance(sources, list) else 1,
            "claims_count": len(topic_data.get("claims", [])),
            "result_status": result.get("status", "unknown"),
        },
    )


    return result
