"""Unit tests for Phase 16 Long-Term Memory and Memory Behaviors."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import Response

from app.core.config import get_settings
from app.memory.behaviors.concept_gap import detect_concept_gaps
from app.memory.behaviors.prediction_update import check_prediction_resolution
from app.memory.behaviors.story_continuity import check_story_continuity
from app.memory.behaviors.topic_resurrection import evaluate_topic_resurrection
from app.memory.breeth_client import search_memory, write_episode
from app.memory.episode_writer import record_decision_episode
from app.memory.recall import recall_memory_context
from app.publishing.rationale_builder import build_post_rationale


class TestBreethClient:
    @pytest.mark.asyncio
    async def test_search_memory_fallback_mode(self) -> None:
        """Assert Breeth search returns empty result in fallback mode when API key is missing."""
        result = await search_memory("AI Security")
        assert result.query == "AI Security"
        assert result.total == 0
        assert result.results == []

    @pytest.mark.asyncio
    async def test_search_memory_with_mocked_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert search_memory correctly parses Breeth /v1/search HTTP response."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "AI Security",
            "total": 1,
            "results": [
                {
                    "id": "m1",
                    "text": "Open story on AI jailbreaks",
                    "score": 0.85,
                    "concepts": ["jailbreak", "security"],
                    "stories": ["AI Vulnerability Series"],
                    "open_questions": ["How do guardrails prevent zero-day jailbreaks?"],
                    "metadata": {"story": {"id": "s1", "title": "AI Vulnerability Series", "chapter": 1}},
                }
            ],
        }

        mock_post = AsyncMock(return_value=mock_response)
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
        monkeypatch.setenv("BREETH_API_KEY", "test-key")
        monkeypatch.setenv("BREETH_BASE_URL", "https://api.breeth.com")
        get_settings.cache_clear()

        result = await search_memory("AI Security")
        assert result.total == 1
        assert len(result.results) == 1
        assert result.results[0].id == "m1"
        assert result.results[0].score == 0.85

    @pytest.mark.asyncio
    async def test_write_episode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert write_episode posts BreethEpisodeIn payload."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "created", "id": "ep_123"}

        mock_post = AsyncMock(return_value=mock_response)
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
        monkeypatch.setenv("BREETH_API_KEY", "test-key")
        monkeypatch.setenv("BREETH_BASE_URL", "https://api.breeth.com")
        get_settings.cache_clear()

        res = await write_episode({
            "topic": "AI Zero-Day Discovery",
            "claims": ["Vulnerability exists in LLM parser"],
            "stance": "analytical",
            "editorial_decision": "accepted",
        })
        assert res["status"] == "created"


class TestRecallEngine:
    @pytest.mark.asyncio
    async def test_recall_memory_context_builds_structured_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_search_result = MagicMock()
        mock_search_result.results = [
            MagicMock(
                id="item1",
                text="Story on LLM Guardrails",
                score=0.9,
                concepts=["guardrails", "security"],
                stories=["LLM Guardrails Series"],
                open_questions=["How to prevent prompt injection?"],
                metadata={"story": {"id": "story_1", "title": "LLM Guardrails Series", "chapter": 1, "originating_post_id": "p_orig_100"}},
            )
        ]

        async def mock_search(query: str, limit: int, min_score: float) -> MagicMock:
            return mock_search_result

        monkeypatch.setattr("app.memory.recall.search_memory", mock_search)

        ctx = await recall_memory_context({"title": "Preventing Prompt Injection"})
        assert len(ctx["stories"]) == 1
        story = ctx["stories"][0]
        assert story["story_id"] == "story_1"
        assert story["chapter"] == 1
        assert story["originating_post_id"] == "p_orig_100"
        assert "guardrails" in ctx["concepts"]


class TestMemoryBehaviors:
    def test_story_continuity_behavior(self) -> None:
        """Assert story continuity detects open story and increments chapter count."""
        topic = {
            "title": "New Prompt Injection Guardrail Technique",
            "summary": "This research answers how to prevent prompt injection in LLM guardrails.",
        }
        memory_ctx = {
            "stories": [
                {
                    "story_id": "story_100",
                    "title": "LLM Guardrails Series",
                    "chapter": 1,
                    "open_questions": ["how to prevent prompt injection"],
                    "originating_post_id": "p_first_chapter",
                }
            ]
        }

        cont = check_story_continuity(topic, memory_ctx)
        assert cont is not None
        assert cont["is_story_continuation"] is True
        assert cont["current_chapter"] == 1
        assert cont["next_chapter"] == 2
        assert cont["related_post_id"] == "p_first_chapter"

    def test_prediction_update_behavior(self) -> None:
        """Assert prediction update detects expired target date."""
        memory_ctx = {
            "predictions": [
                {
                    "prediction_id": "pred_1",
                    "text": "LLM jailbreaks will double by 2025",
                    "target_date": "2025-01-01T00:00:00Z",
                    "originating_post_id": "p_pred_orig",
                }
            ]
        }

        resolutions = check_prediction_resolution(memory_ctx)
        assert len(resolutions) == 1
        res = resolutions[0]
        assert res["is_prediction_resolution"] is True
        assert res["related_post_id"] == "p_pred_orig"
        assert "Prediction Verdict" in res["title"]

    def test_topic_resurrection_behavior(self) -> None:
        """Assert topic resurrection matches candidate against stored topic debt."""
        candidate = {
            "title": "Quantum Vulnerability Breaking RSA-2048",
            "summary": "New empirical proof-of-concept published demonstrating quantum RSA attack.",
        }
        debt_items = [
            {
                "id": "debt_1",
                "title": "Quantum Vulnerability Breaking RSA",
                "rejection_reason": "Insufficient empirical proof in 2024",
                "revisit_condition": "Revisit when empirical proof-of-concept is published",
            }
        ]

        res = evaluate_topic_resurrection(candidate, debt_items)
        assert res is not None
        assert res["resurrected"] is True
        assert res["original_topic_id"] == "debt_1"

    def test_concept_gap_behavior(self) -> None:
        """Assert concept gap behavior identifies unconnected concepts."""
        memory_ctx = {"concepts": ["adversarial-prompts", "circuit-breakers"]}
        gaps = detect_concept_gaps(memory_ctx)
        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["is_concept_gap_synthesis"] is True
        assert "Adversarial-Prompts" in gap["title"]


class TestRelatedPostRationaleVerification:
    @pytest.mark.asyncio
    async def test_rationale_includes_related_post_id(self) -> None:
        """Verification test: assert rationale includes related_post_id when continuing story."""
        topic = {
            "title": "Chapter 2: Guardrail Breakthrough",
            "story_continuation": {
                "related_post_id": "p_first_post_id",
                "next_chapter": 2,
                "resolved_question": "how to mitigate jailbreaks",
            },
        }
        memory_ctx = {}

        rationale = await build_post_rationale(topic, memory_ctx)
        assert "related post: p_first_post_id" in rationale
        assert "Chapter 2" in rationale
