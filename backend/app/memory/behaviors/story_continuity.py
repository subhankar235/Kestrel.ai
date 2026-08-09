"""Story continuity behavior — detects story chapters, links related posts, and increments chapter count."""

from __future__ import annotations

from typing import Any


def check_story_continuity(topic: dict[str, Any], memory_context: dict[str, Any]) -> dict[str, Any] | None:
    """Check if candidate topic continues an existing story thread and addresses open questions."""
    stories = memory_context.get("stories", [])
    if not stories:
        return None

    topic_title = str(topic.get("title", "")).lower()
    topic_summary = str(topic.get("summary", "")).lower()

    for story in stories:
        open_questions = story.get("open_questions", [])
        story_title = str(story.get("title", "")).lower()

        # Check if topic matches story title or answers an open question
        matches_story = any(word in topic_title or word in topic_summary for word in story_title.split() if len(word) > 4)
        answers_question = any(q.lower() in topic_summary or q.lower() in topic_title for q in open_questions)

        if matches_story or answers_question:
            current_chapter = int(story.get("chapter", 1))
            next_chapter = current_chapter + 1
            originating_post_id = story.get("originating_post_id") or f"p_story_{story.get('story_id')}"

            return {
                "is_story_continuation": True,
                "story_id": story.get("story_id"),
                "story_title": story.get("title"),
                "current_chapter": current_chapter,
                "next_chapter": next_chapter,
                "related_post_id": originating_post_id,
                "resolved_question": open_questions[0] if open_questions else "Follow-up development",
            }

    return None
