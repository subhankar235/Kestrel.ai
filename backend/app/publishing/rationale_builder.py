"""Rationale builder — generates transparency rationale string explaining post selection and memory links."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import call_openai_json
from app.llm.prompts.rationale import build_rationale_prompt

logger = get_logger(__name__)


async def build_post_rationale(
    topic: dict[str, Any],
    memory_context: dict[str, Any],
    winning_draft: dict[str, Any] | None = None,
) -> str:
    """Build 'why selected / why now / memory link' transparency rationale text."""
    draft = winning_draft or {}
    behaviors = memory_context.get("behavior_results", {})
    story_info = behaviors.get("story_continuation") or topic.get("story_continuation")
    resurrection_info = behaviors.get("resurrection") or topic.get("resurrection")
    prediction_info = behaviors.get("prediction_resolution") or topic.get("prediction_resolution")
    concept_gap_info = behaviors.get("concept_gaps") or topic.get("concept_gaps")

    # Structured Memory Link Prefix
    memory_links = []
    if story_info:
        rel_id = story_info.get("related_post_id") or story_info.get("originating_post_id")
        chapter = story_info.get("next_chapter") or story_info.get("chapter", 2)
        resolved_q = story_info.get("resolved_question", "open research question")
        link_str = f"Story Continuation (Chapter {chapter}): Answers '{resolved_q}'"
        if rel_id:
            link_str += f" (related post: {rel_id})"
        memory_links.append(link_str)

    if resurrection_info:
        orig_title = resurrection_info.get("original_title") or topic.get("title")
        revisit_cond = resurrection_info.get("revisit_condition", "new evidence arrived")
        memory_links.append(
            f"Topic Resurrected: Re-evaluated previously rejected topic '{orig_title}' as condition '{revisit_cond}' was satisfied."
        )

    if prediction_info:
        rel_id = prediction_info.get("related_post_id") or prediction_info.get("originating_post_id")
        link_str = "Prediction Verdict: Evaluating outcome for expired prediction"
        if rel_id:
            link_str += f" (related post: {rel_id})"
        memory_links.append(link_str)

    if concept_gap_info:
        concepts = concept_gap_info.get("concepts", []) if isinstance(concept_gap_info, dict) else []
        c_str = " & ".join(concepts) if concepts else "connected research areas"
        memory_links.append(f"Concept Gap Synthesis: Connecting previously isolated concepts ({c_str}).")

    # Attempt LLM Rationale Generation
    try:
        system_prompt, user_prompt = build_rationale_prompt(topic, memory_context, draft)
        response = await call_openai_json(system_prompt, user_prompt)
        if isinstance(response, dict) and "rationale" in response and response["rationale"]:
            llm_rationale = str(response["rationale"]).strip()
            if memory_links:
                full_rationale = " ".join(memory_links) + " " + llm_rationale
            else:
                full_rationale = llm_rationale
            logger.info("Generated LLM rationale for published post")
            return full_rationale
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM rationale generation failed or unavailable ({exc}); using structured rationale")

    # Fallback Structured Rationale
    base_parts = ["Selected via autonomous editorial scoring and persona verification."]
    if memory_links:
        base_parts.extend(memory_links)
    else:
        topic_title = topic.get("title", "research topic")
        base_parts.append(f"Timely analysis addressing fresh research developments on '{topic_title}'.")

    final_rationale = " ".join(base_parts)
    logger.info("Composed structured rationale for published post")
    return final_rationale
