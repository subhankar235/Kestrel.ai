"""Self critique — scores and ranks draft angles to select the winning candidate post."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.llm.openai_client import call_openai_json
from app.llm.prompts.critique import build_critique_prompt

logger = get_logger(__name__)


def _score_draft_heuristically(draft: dict[str, Any], persona: dict[str, Any]) -> float:
    """Heuristic fallback score for a draft angle based on length, sources, and persona match."""
    text = str(draft.get("post_text") or draft.get("text") or "")
    sources = draft.get("sources") or []
    angle_type = str(draft.get("angle_type") or draft.get("angle_name") or "")

    score = 70.0
    # Length sanity check (100 - 600 chars preferred)
    if 100 <= len(text) <= 600:
        score += 10.0

    # Sources bonus
    if isinstance(sources, list) and len(sources) > 0:
        score += 10.0

    # Preferred analysis/prediction angle bonus
    if "analysis" in angle_type.lower() or "deep dive" in angle_type.lower():
        score += 5.0

    return min(score, 100.0)


async def critique_and_select_winning_draft(
    drafts: list[dict[str, Any]],
    persona: dict[str, Any] | None = None,
    constitution_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score draft candidates, log losing draft scores for observability, and return the winning post draft."""
    if not drafts:
        return {
            "angle_name": "Default Research Update",
            "post_text": "Autonomous research synthesis update.",
            "sources": [],
            "score": 75.0,
            "critique_notes": "Default fallback draft created due to empty candidate set.",
        }

    persona_dict = persona or {"name": "Ada", "domain": "AI Security"}
    rules = constitution_rules or {"accept_threshold": 60.0}

    # Attempt LLM evaluation
    try:
        system_prompt, user_prompt = build_critique_prompt(drafts, persona_dict, rules)
        response = await call_openai_json(system_prompt, user_prompt)
        if isinstance(response, dict):
            winning_idx = response.get("winning_index")
            critique_notes = str(response.get("critique_notes", "LLM draft critique completed."))
            if isinstance(winning_idx, int) and 0 <= winning_idx < len(drafts):
                winner = dict(drafts[winning_idx])
                winner["critique_notes"] = critique_notes
                winner["score"] = float(response.get("winning_score", 88.0))

                # Log tournament scores for observability
                for i, d in enumerate(drafts):
                    angle = d.get("angle_name", f"Angle {i+1}")
                    if i == winning_idx:
                        logger.info(f"Draft Tournament Winner [idx={i}]: '{angle}' (score={winner['score']})")
                    else:
                        logger.info(f"Draft Tournament Losing Draft [idx={i}]: '{angle}' (critique='Not selected')")

                return winner
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM draft critique failed or unavailable ({exc}); using heuristic tournament scoring")

    # Fallback Heuristic Tournament
    scored_drafts = []
    for idx, d in enumerate(drafts):
        score = _score_draft_heuristically(d, persona_dict)
        scored_drafts.append((score, idx, d))

    scored_drafts.sort(key=lambda x: x[0], reverse=True)

    winner_score, winning_idx, winner_draft = scored_drafts[0]
    winner = dict(winner_draft)
    winner["score"] = winner_score
    winner["critique_notes"] = f"Selected highest heuristic score angle '{winner.get('angle_name')}'"

    # Log losing draft scores for observability
    logger.info(
        f"Draft Tournament Complete: Selected '{winner.get('angle_name')}' with score {winner_score:.1f}"
    )
    for score, idx, d in scored_drafts[1:]:
        logger.info(
            f"Draft Tournament Losing Draft [idx={idx}]: '{d.get('angle_name')}' score={score:.1f}"
        )

    return winner
