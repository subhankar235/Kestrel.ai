"""Draft generator — generates 3 distinct candidate angles per accepted topic."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import call_openai_json
from app.llm.prompts.draft import build_draft_prompt

logger = get_logger(__name__)


def _clean_fallback_summary(summary: str) -> str:
    """Keep fallback drafts readable when a source contains raw article markdown."""
    lines: list[str] = []
    for line in summary.splitlines():
        cleaned = line.strip().lstrip("#*- ")
        if not cleaned or cleaned.lower() in {"share", "key findings"}:
            continue
        if len(cleaned) < 40 and (cleaned.endswith("2026") or cleaned.startswith("August")):
            continue
        lines.append(cleaned)
    return " ".join(" ".join(lines).split())[:700]


async def generate_draft_angles(
    topic: dict[str, Any],
    persona: dict[str, Any],
    memory_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate 3 candidate post draft angles for an accepted topic.

    Angles generated:
    1. News & Key Highlights (Breaking news focus)
    2. In-Depth Technical Analysis (Core technical implications)
    3. Strategic Implications & Predictions (Forward-looking view)
    """
    memory_ctx = memory_context or {}
    title = str(topic.get("title", "Research Update"))
    summary = str(topic.get("summary", "Key findings and research insights."))
    summary = _clean_fallback_summary(summary)
    sources = topic.get("sources") or ["https://example.com/research"]
    if not isinstance(sources, list):
        sources = [str(sources)]

    persona_name = str(persona.get("name", "Ada"))
    domain = str(persona.get("domain", "AI Security"))

    system_prompt, user_prompt = build_draft_prompt(topic, persona, memory_ctx)

    try:
        response = await call_openai_json(system_prompt, user_prompt)
        if isinstance(response, dict) and "drafts" in response and isinstance(response["drafts"], list):
            drafts = response["drafts"]
            if len(drafts) >= 1:
                normalized_drafts = []
                for idx, d in enumerate(drafts):
                    if isinstance(d, dict):
                        angle_name = d.get("angle_name") or f"Angle {idx+1}"
                        post_text = d.get("post_text") or d.get("text") or summary
                        d_sources = d.get("sources") or sources
                        normalized_drafts.append({
                            "angle_name": str(angle_name),
                            "post_text": str(post_text),
                            "sources": d_sources if isinstance(d_sources, list) else [str(d_sources)],
                            "angle_type": d.get("angle_type", f"angle_{idx+1}"),
                        })
                if len(normalized_drafts) >= 1:
                    logger.info(f"LLM generated {len(normalized_drafts)} draft angles for '{title}'")
                    return normalized_drafts
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM draft generation failed or unavailable ({exc}); using fallback tournament angles")

    # Structured 3-angle fallback tournament
    fallback_drafts = [
        {
            "angle_name": "News & Key Highlights",
            "angle_type": "news",
            "post_text": (
                f"[{persona_name} Update] Fresh developments in {domain}: {title}. "
                f"Core finding: {summary} This marks a significant shift in current technical standards."
            ),
            "sources": sources,
        },
        {
            "angle_name": "In-Depth Technical Analysis",
            "angle_type": "analysis",
            "post_text": (
                f"[{persona_name} Deep Dive] Examining the architectural mechanics behind {title}. "
                f"Key breakdown: {summary} Engineering teams should evaluate these structural implications immediately."
            ),
            "sources": sources,
        },
        {
            "angle_name": "Strategic Implications & Predictions",
            "angle_type": "prediction",
            "post_text": (
                f"[{persona_name} Forward Look] Strategic projection regarding {title} in {domain}. "
                f"Impact synthesis: {summary} Expect broader adoption and defensive model updates over the coming quarter."
            ),
            "sources": sources,
        },
    ]

    logger.info(f"Generated {len(fallback_drafts)} fallback candidate draft angles for '{title}'")
    return fallback_drafts
