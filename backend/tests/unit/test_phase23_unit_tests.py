"""Phase 23 — Comprehensive Unit Tests for Pure-Logic Modules.

Tests cover every pure-logic function with real assertions against actual return values,
not just mocking. External HTTP clients (OpenAI, Breeth) are mocked at the boundary;
everything else exercises real code paths.

Coverage:
  1. scorer.py — weighted scoring math, clamping, fallback, dimension extraction
  2. judge.py — accept/reject at exact threshold boundary, above, below, zero, 100
  3. rationale_builder.py — output shape with story/resurrection/prediction/concept-gap memory links
  4. recall.py — MemoryContext classification (stories, beliefs, predictions, rejected topics, concepts)
  5. behaviors/story_continuity.py — story matching by title words and open questions
  6. behaviors/prediction_update.py — expired vs future prediction classification
  7. behaviors/topic_resurrection.py — debt title word matching for resurrection
  8. behaviors/concept_gap.py — gap synthesis pair generation
  9. self_critique.py — heuristic tournament winner selection and scoring logic
  10. drafting/draft_generator.py — fallback 3-angle generation with persona interpolation
  11. drafting/persona_check.py — banned-word veto and pass-through logic
  12. publishing/publisher.py — _extract_memory_relationship for all relationship types
  13. schemas/*.py — validators: strip, reject empty, bounds, serialization
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.drafting.persona_check import verify_persona_alignment
from app.drafting.self_critique import _score_draft_heuristically, critique_and_select_winning_draft
from app.editorial.judge import judge_topic_score
from app.editorial.scorer import score_candidate_topic
from app.memory.behaviors.concept_gap import detect_concept_gaps
from app.memory.behaviors.prediction_update import check_prediction_resolution
from app.memory.behaviors.story_continuity import check_story_continuity
from app.memory.behaviors.topic_resurrection import evaluate_topic_resurrection
from app.memory.recall import recall_memory_context
from app.publishing.publisher import _extract_memory_relationship
from app.publishing.rationale_builder import build_post_rationale
from app.schemas.agent import InitRequest, InitResponse, PersonaIn
from app.schemas.feed import FeedResponse, PostOut
from app.schemas.memory import BreethEpisodeIn, BreethItem, BreethSearchRequest, BreethSearchResult


# =============================================================================
# 1. SCORER.PY — Weighted Scoring Math
# =============================================================================

class TestScorerMath:
    """Verify score_candidate_topic computes weighted total correctly and clamps to [0, 100]."""

    @pytest.mark.asyncio
    async def test_weighted_score_calculation_with_known_values(self) -> None:
        """Formula: total = rel*0.35 + nov*0.25 + evi*0.25 + pf*0.15 - hype - rep, clamped [0,100]."""
        mock_llm_scores = {
            "relevance_score": 80.0,
            "novelty_score": 60.0,
            "evidence_score": 70.0,
            "persona_fit_score": 90.0,
            "hype_penalty": 0.0,
            "repetition_penalty": 0.0,
            "reasoning": "Strong research evidence",
        }
        # expected = 80*0.35 + 60*0.25 + 70*0.25 + 90*0.15 = 28 + 15 + 17.5 + 13.5 = 74.0
        with patch("app.editorial.scorer.generate_structured_output", return_value=mock_llm_scores):
            scores = await score_candidate_topic({"title": "Test"}, {}, {"accept_threshold": 60.0})

        assert scores["total_score"] == 74.0
        assert scores["relevance_score"] == 80.0
        assert scores["novelty_score"] == 60.0
        assert scores["evidence_score"] == 70.0
        assert scores["persona_fit_score"] == 90.0
        assert scores["hype_penalty"] == 0.0
        assert scores["repetition_penalty"] == 0.0

    @pytest.mark.asyncio
    async def test_hype_penalty_reduces_total(self) -> None:
        mock_scores = {
            "relevance_score": 100.0, "novelty_score": 100.0, "evidence_score": 100.0,
            "persona_fit_score": 100.0, "hype_penalty": 20.0, "repetition_penalty": 5.0,
            "reasoning": "Penalty test",
        }
        # expected = 100*0.35 + 100*0.25 + 100*0.25 + 100*0.15 - 20 - 5 = 100 - 25 = 75.0
        with patch("app.editorial.scorer.generate_structured_output", return_value=mock_scores):
            scores = await score_candidate_topic({"title": "Hype"}, {}, {})

        assert scores["total_score"] == 75.0

    @pytest.mark.asyncio
    async def test_total_score_clamped_to_zero_floor(self) -> None:
        mock_scores = {
            "relevance_score": 10.0, "novelty_score": 10.0, "evidence_score": 10.0,
            "persona_fit_score": 10.0, "hype_penalty": 50.0, "repetition_penalty": 50.0,
            "reasoning": "Extreme penalties",
        }
        # raw = 10*0.35 + 10*0.25 + 10*0.25 + 10*0.15 - 50 - 50 = 10 - 100 = -90 → clamped to 0
        with patch("app.editorial.scorer.generate_structured_output", return_value=mock_scores):
            scores = await score_candidate_topic({"title": "Low"}, {}, {})

        assert scores["total_score"] == 0.0

    @pytest.mark.asyncio
    async def test_total_score_clamped_to_100_ceiling(self) -> None:
        mock_scores = {
            "relevance_score": 100.0, "novelty_score": 100.0, "evidence_score": 100.0,
            "persona_fit_score": 100.0, "hype_penalty": 0.0, "repetition_penalty": 0.0,
            "reasoning": "Perfect score",
        }
        with patch("app.editorial.scorer.generate_structured_output", return_value=mock_scores):
            scores = await score_candidate_topic({"title": "Perfect"}, {}, {})

        assert scores["total_score"] == 100.0

    @pytest.mark.asyncio
    async def test_fallback_scores_used_when_llm_fails(self) -> None:
        """When LLM raises, fallback heuristic scores should still produce a valid total."""
        with patch("app.editorial.scorer.generate_structured_output", side_effect=RuntimeError("LLM down")):
            scores = await score_candidate_topic({"title": "Fallback"}, {}, {})

        assert "total_score" in scores
        assert 0.0 <= scores["total_score"] <= 100.0
        assert "reasoning" in scores

    @pytest.mark.asyncio
    async def test_scoring_returns_all_required_dimensions(self) -> None:
        with patch("app.editorial.scorer.generate_structured_output", side_effect=RuntimeError("no key")):
            scores = await score_candidate_topic({"title": "Dimensions"}, {}, {})

        required_keys = ["relevance_score", "novelty_score", "evidence_score",
                         "persona_fit_score", "hype_penalty", "repetition_penalty",
                         "total_score", "reasoning"]
        for key in required_keys:
            assert key in scores, f"Missing key: {key}"


# =============================================================================
# 2. JUDGE.PY — Accept/Reject Boundary Tests
# =============================================================================

class TestJudgeBoundary:
    """Test editorial judge at exact threshold boundary, above, below, zero, 100."""

    def test_accept_above_threshold(self) -> None:
        scores = {"total_score": 61.0, "reasoning": "Just above"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is True
        assert "ACCEPTED" in reason

    def test_reject_below_threshold(self) -> None:
        scores = {"total_score": 59.9, "reasoning": "Just below"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is False
        assert "REJECTED" in reason

    def test_accept_at_exact_threshold(self) -> None:
        scores = {"total_score": 60.0, "reasoning": "At exact boundary"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is True
        assert "ACCEPTED" in reason

    def test_reject_at_zero_score(self) -> None:
        scores = {"total_score": 0.0, "reasoning": "Zero score"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is False
        assert "0.0" in reason

    def test_accept_at_100_score(self) -> None:
        scores = {"total_score": 100.0, "reasoning": "Perfect score"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is True

    def test_accept_at_zero_threshold(self) -> None:
        """A threshold of 0 should accept everything (score >= 0)."""
        scores = {"total_score": 0.0, "reasoning": "Zero threshold"}
        accepted, reason = judge_topic_score(scores, accept_threshold=0.0)
        assert accepted is True

    def test_reject_when_threshold_is_100_and_score_is_99(self) -> None:
        scores = {"total_score": 99.9, "reasoning": "Highest bar"}
        accepted, reason = judge_topic_score(scores, accept_threshold=100.0)
        assert accepted is False

    def test_accept_when_threshold_is_100_and_score_is_100(self) -> None:
        scores = {"total_score": 100.0, "reasoning": "Perfect at max threshold"}
        accepted, reason = judge_topic_score(scores, accept_threshold=100.0)
        assert accepted is True

    def test_reason_includes_score_and_threshold(self) -> None:
        scores = {"total_score": 72.5, "reasoning": "Moderate"}
        _, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert "72.5" in reason
        assert "60.0" in reason

    def test_topic_title_passed_through(self) -> None:
        scores = {"total_score": 80.0, "reasoning": "Test"}
        _, reason = judge_topic_score(scores, accept_threshold=60.0, topic_title="My Topic")
        # reason should not crash and should contain "ACCEPTED"
        assert "ACCEPTED" in reason

    def test_missing_total_score_defaults_to_zero(self) -> None:
        scores = {"reasoning": "No total score key"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is False
        assert "0.0" in reason

    def test_missing_reasoning_defaults_to_empty(self) -> None:
        scores = {"total_score": 80.0}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is True
        assert "80.0" in reason


# =============================================================================
# 3. RATIONALE_BUILDER.PY — Output Shape
# =============================================================================

class TestRationaleBuilderOutputShape:
    """Verify rationale builder returns a non-empty string with correct structure."""

    @pytest.mark.asyncio
    async def test_fallback_rationale_includes_topic_title(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(
                topic={"title": "Zero-Day Advisory"},
                memory_context={},
                winning_draft={"post_text": "Analysis of zero-day."},
            )
        assert isinstance(rationale, str)
        assert len(rationale) > 10
        assert "Zero-Day Advisory" in rationale

    @pytest.mark.asyncio
    async def test_rationale_with_story_continuation_memory_link(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(
                topic={"title": "LLM Attack Surface"},
                memory_context={
                    "behavior_results": {
                        "story_continuation": {
                            "next_chapter": 3,
                            "resolved_question": "How do jailbreaks scale?",
                            "related_post_id": "p_abc123",
                        }
                    }
                },
                winning_draft={},
            )
        assert "Story Continuation" in rationale
        assert "Chapter 3" in rationale
        assert "How do jailbreaks scale?" in rationale
        assert "p_abc123" in rationale

    @pytest.mark.asyncio
    async def test_rationale_with_topic_resurrection_memory_link(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(
                topic={"title": "Side Channel Attack"},
                memory_context={
                    "behavior_results": {
                        "resurrection": {
                            "original_title": "Spectre Variant V3",
                            "revisit_condition": "new CVE published",
                        }
                    }
                },
            )
        assert "Topic Resurrected" in rationale
        assert "Spectre Variant V3" in rationale
        assert "new CVE published" in rationale

    @pytest.mark.asyncio
    async def test_rationale_with_prediction_resolution_memory_link(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(
                topic={"title": "Prediction Check"},
                memory_context={
                    "behavior_results": {
                        "prediction_resolution": {
                            "related_post_id": "p_pred_99",
                        }
                    }
                },
            )
        assert "Prediction Verdict" in rationale
        assert "p_pred_99" in rationale

    @pytest.mark.asyncio
    async def test_rationale_with_concept_gap_synthesis_memory_link(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(
                topic={"title": "Concept Gap"},
                memory_context={
                    "behavior_results": {
                        "concept_gaps": {
                            "concepts": ["transformer", "formal verification"],
                        }
                    }
                },
            )
        assert "Concept Gap Synthesis" in rationale
        assert "transformer" in rationale
        assert "formal verification" in rationale

    @pytest.mark.asyncio
    async def test_rationale_uses_llm_when_available(self) -> None:
        mock_response = {"rationale": "LLM-generated rationale explaining deep analysis."}
        with patch("app.publishing.rationale_builder.call_openai_json", return_value=mock_response):
            rationale = await build_post_rationale(
                topic={"title": "LLM Available"},
                memory_context={},
            )
        assert "LLM-generated rationale" in rationale

    @pytest.mark.asyncio
    async def test_rationale_always_returns_string(self) -> None:
        with patch("app.publishing.rationale_builder.call_openai_json", side_effect=RuntimeError("No LLM")):
            rationale = await build_post_rationale(topic={}, memory_context={})
        assert isinstance(rationale, str)
        assert len(rationale) > 0


# =============================================================================
# 4. RECALL.PY — MemoryContext Interpretation
# =============================================================================

class TestRecallMemoryContextInterpretation:
    """Verify recall_memory_context correctly classifies items into stories, beliefs, predictions, rejected."""

    @pytest.mark.asyncio
    async def test_classifies_story_items(self) -> None:
        story_item = BreethItem(
            id="item_1", text="LLM Attack Chapter 1", score=0.9,
            metadata={"story": {"id": "s1", "title": "LLM Attack", "chapter": 2}},
            concepts=["jailbreak"], stories=["LLM Attack"], open_questions=["What about GPT-5?"],
        )
        mock_result = BreethSearchResult(results=[story_item], query="LLM", total=1)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "LLM Attacks"})

        assert len(ctx["stories"]) == 1
        assert ctx["stories"][0]["story_id"] == "s1"
        assert ctx["stories"][0]["chapter"] == 2
        assert ctx["stories"][0]["open_questions"] == ["What about GPT-5?"]

    @pytest.mark.asyncio
    async def test_classifies_prediction_items(self) -> None:
        pred_item = BreethItem(
            id="item_2", text="GPT-5 will ship by 2027", score=0.85,
            metadata={"prediction": {"id": "pred_1", "target_date": "2027-01-01", "status": "active"}},
            concepts=["GPT"], stories=[], open_questions=[],
        )
        mock_result = BreethSearchResult(results=[pred_item], query="GPT", total=1)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "GPT-5 Release"})

        assert len(ctx["predictions"]) == 1
        assert ctx["predictions"][0]["prediction_id"] == "pred_1"
        assert ctx["predictions"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_classifies_rejected_topics(self) -> None:
        rejected_item = BreethItem(
            id="item_3", text="Crypto hype article", score=0.6,
            metadata={"editorial_decision": "rejected", "rejection_reason": "Hype content"},
            concepts=[], stories=[], open_questions=[],
        )
        mock_result = BreethSearchResult(results=[rejected_item], query="crypto", total=1)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "Crypto News"})

        assert len(ctx["rejected_topics"]) == 1
        assert ctx["rejected_topics"][0]["rejection_reason"] == "Hype content"

    @pytest.mark.asyncio
    async def test_classifies_beliefs(self) -> None:
        belief_item = BreethItem(
            id="item_4", text="AI alignment is critical for safety", score=0.88,
            metadata={}, concepts=["alignment", "safety"], stories=[], open_questions=[],
        )
        mock_result = BreethSearchResult(results=[belief_item], query="alignment", total=1)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "AI Alignment"})

        assert len(ctx["beliefs"]) == 1
        assert ctx["beliefs"][0]["statement"] == "AI alignment is critical for safety"
        assert ctx["beliefs"][0]["score"] == 0.88

    @pytest.mark.asyncio
    async def test_concepts_collected_and_sorted(self) -> None:
        item1 = BreethItem(id="i1", text="Text", score=0.5, metadata={},
                           concepts=["zzz_concept", "aaa_concept"], stories=[], open_questions=[])
        item2 = BreethItem(id="i2", text="Text2", score=0.5, metadata={},
                           concepts=["mmm_concept", "aaa_concept"], stories=[], open_questions=[])
        mock_result = BreethSearchResult(results=[item1, item2], query="test", total=2)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "Concepts"})

        assert ctx["concepts"] == ["aaa_concept", "mmm_concept", "zzz_concept"]

    @pytest.mark.asyncio
    async def test_empty_search_returns_empty_context(self) -> None:
        mock_result = BreethSearchResult(results=[], query="nothing", total=0)
        with patch("app.memory.recall.search_memory", return_value=mock_result):
            ctx = await recall_memory_context({"title": "Empty"})

        assert ctx["total_recalled"] == 0
        assert ctx["stories"] == []
        assert ctx["beliefs"] == []
        assert ctx["predictions"] == []
        assert ctx["rejected_topics"] == []
        assert ctx["concepts"] == []

    @pytest.mark.asyncio
    async def test_query_uses_title_then_summary_then_default(self) -> None:
        mock_result = BreethSearchResult(results=[], query="", total=0)
        with patch("app.memory.recall.search_memory", return_value=mock_result) as mock_search:
            await recall_memory_context({"title": "My Title"})
            assert mock_search.call_args[0][0] == "My Title"

        with patch("app.memory.recall.search_memory", return_value=mock_result) as mock_search:
            await recall_memory_context({"summary": "My Summary"})
            assert mock_search.call_args[0][0] == "My Summary"

        with patch("app.memory.recall.search_memory", return_value=mock_result) as mock_search:
            await recall_memory_context({})
            assert mock_search.call_args[0][0] == "AI Research"


# =============================================================================
# 5. BEHAVIORS — Story Continuity
# =============================================================================

class TestStoryContinuity:
    """Test check_story_continuity matching logic."""

    def test_returns_none_when_no_stories_in_memory(self) -> None:
        result = check_story_continuity(
            {"title": "Some Topic"}, {"stories": []}
        )
        assert result is None

    def test_returns_none_when_stories_key_missing(self) -> None:
        result = check_story_continuity({"title": "Topic"}, {})
        assert result is None

    def test_matches_story_by_title_word_overlap(self) -> None:
        topic = {"title": "Jailbreak Discovery in GPT-5", "summary": "New findings"}
        memory = {"stories": [{
            "story_id": "s1", "title": "GPT-5 Jailbreak Exploits",
            "chapter": 2, "open_questions": [], "originating_post_id": "p_old",
        }]}
        result = check_story_continuity(topic, memory)
        assert result is not None
        assert result["is_story_continuation"] is True
        assert result["story_id"] == "s1"
        assert result["next_chapter"] == 3
        assert result["related_post_id"] == "p_old"

    def test_matches_story_by_open_question_in_summary(self) -> None:
        topic = {"title": "Unrelated Title", "summary": "Answers how transformers scale"}
        memory = {"stories": [{
            "story_id": "s2", "title": "Short",
            "chapter": 1, "open_questions": ["how transformers scale"],
            "originating_post_id": "p_prior",
        }]}
        result = check_story_continuity(topic, memory)
        assert result is not None
        assert result["resolved_question"] == "how transformers scale"

    def test_no_match_when_words_too_short(self) -> None:
        topic = {"title": "AI is OK", "summary": "Brief update"}
        memory = {"stories": [{
            "story_id": "s3", "title": "AI is OK",
            "chapter": 1, "open_questions": [],
        }]}
        # Words "ai", "is", "ok" are all <= 4 chars, so no match
        result = check_story_continuity(topic, memory)
        assert result is None

    def test_chapter_increments_from_current(self) -> None:
        topic = {"title": "Advanced Backdoor Techniques", "summary": "details"}
        memory = {"stories": [{
            "story_id": "s4", "title": "Advanced Backdoor Evolution",
            "chapter": 5, "open_questions": [],
        }]}
        result = check_story_continuity(topic, memory)
        assert result is not None
        assert result["current_chapter"] == 5
        assert result["next_chapter"] == 6


# =============================================================================
# 6. BEHAVIORS — Prediction Update
# =============================================================================

class TestPredictionUpdate:
    """Test check_prediction_resolution classifies expired vs future predictions."""

    def test_returns_empty_when_no_predictions(self) -> None:
        result = check_prediction_resolution({"predictions": []})
        assert result == []

    def test_returns_empty_when_key_missing(self) -> None:
        result = check_prediction_resolution({})
        assert result == []

    def test_expired_prediction_generates_resolution_topic(self) -> None:
        past_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        memory = {"predictions": [{
            "prediction_id": "pred_1",
            "text": "AI will pass medical boards",
            "target_date": past_date,
            "status": "active",
            "originating_post_id": "p_100",
        }]}
        result = check_prediction_resolution(memory)
        assert len(result) == 1
        assert result[0]["is_prediction_resolution"] is True
        assert "Prediction Verdict" in result[0]["title"]
        assert result[0]["prediction_id"] == "pred_1"
        assert result[0]["related_post_id"] == "p_100"

    def test_future_prediction_is_not_resolved(self) -> None:
        future_date = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        memory = {"predictions": [{
            "prediction_id": "pred_2",
            "text": "Quantum supremacy in five years",
            "target_date": future_date,
            "status": "active",
        }]}
        result = check_prediction_resolution(memory)
        assert result == []

    def test_prediction_with_no_target_date_is_skipped(self) -> None:
        memory = {"predictions": [{
            "prediction_id": "pred_3",
            "text": "Some prediction",
            "target_date": None,
        }]}
        result = check_prediction_resolution(memory)
        assert result == []

    def test_prediction_with_invalid_date_is_skipped(self) -> None:
        memory = {"predictions": [{
            "prediction_id": "pred_4",
            "text": "Bad date format",
            "target_date": "not-a-date",
        }]}
        result = check_prediction_resolution(memory)
        assert result == []

    def test_multiple_predictions_mixed_expired_and_future(self) -> None:
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        memory = {"predictions": [
            {"prediction_id": "p1", "text": "Expired one", "target_date": past},
            {"prediction_id": "p2", "text": "Future one", "target_date": future},
            {"prediction_id": "p3", "text": "Also expired", "target_date": past},
        ]}
        result = check_prediction_resolution(memory)
        assert len(result) == 2
        ids = {r["prediction_id"] for r in result}
        assert ids == {"p1", "p3"}


# =============================================================================
# 7. BEHAVIORS — Topic Resurrection
# =============================================================================

class TestTopicResurrection:
    """Test evaluate_topic_resurrection word matching for resurrection."""

    def test_returns_none_when_debt_list_is_empty(self) -> None:
        result = evaluate_topic_resurrection({"title": "Something"}, [])
        assert result is None

    def test_resurrects_matching_topic_by_title_overlap(self) -> None:
        candidate = {"title": "Critical Firmware Vulnerability Disclosed", "summary": "New CVE data"}
        debt = [{"id": 42, "title": "Firmware Vulnerability Rejected",
                 "rejection_reason": "Insufficient evidence",
                 "revisit_condition": "Revisit when new CVE arrives"}]
        result = evaluate_topic_resurrection(candidate, debt)
        assert result is not None
        assert result["resurrected"] is True
        assert result["original_topic_id"] == 42
        assert result["rejection_reason"] == "Insufficient evidence"
        assert "Resurrected" in result["resurrection_note"]

    def test_no_resurrection_when_titles_dont_overlap(self) -> None:
        candidate = {"title": "Quantum Computing Advance", "summary": "Qubits improved"}
        debt = [{"id": 99, "title": "Cloud Security Report",
                 "rejection_reason": "Old news"}]
        result = evaluate_topic_resurrection(candidate, debt)
        assert result is None

    def test_matches_via_summary_not_just_title(self) -> None:
        candidate = {"title": "Short", "summary": "Firmware update improves protection"}
        debt = [{"id": 10, "title": "Firmware Update Analysis",
                 "rejection_reason": "Low novelty"}]
        result = evaluate_topic_resurrection(candidate, debt)
        assert result is not None
        assert result["resurrected"] is True

    def test_short_words_in_debt_title_not_matched(self) -> None:
        """Words with <=4 chars should not trigger matching."""
        candidate = {"title": "AI is hot topic now", "summary": "Details about AI"}
        debt = [{"id": 5, "title": "AI is old", "rejection_reason": "Stale"}]
        # Words: "ai" (2), "is" (2), "old" (3) — all <=4 chars
        result = evaluate_topic_resurrection(candidate, debt)
        assert result is None


# =============================================================================
# 8. BEHAVIORS — Concept Gap
# =============================================================================

class TestConceptGap:
    """Test detect_concept_gaps synthesis pair generation."""

    def test_returns_empty_when_fewer_than_2_concepts(self) -> None:
        assert detect_concept_gaps({"concepts": []}) == []
        assert detect_concept_gaps({"concepts": ["single"]}) == []

    def test_returns_gap_candidate_for_2_or_more_concepts(self) -> None:
        result = detect_concept_gaps({"concepts": ["transformer", "formal_verification", "fuzzing"]})
        assert len(result) == 1
        gap = result[0]
        assert gap["concept_a"] == "transformer"
        assert gap["concept_b"] == "formal_verification"
        assert gap["is_concept_gap_synthesis"] is True
        assert "Synthesis" in gap["title"]
        assert "Transformer" in gap["title"]
        assert "Formal_Verification" in gap["title"]

    def test_gap_candidate_has_complete_shape(self) -> None:
        result = detect_concept_gaps({"concepts": ["a_concept", "b_concept"]})
        gap = result[0]
        required_keys = {"title", "summary", "concept_a", "concept_b", "is_concept_gap_synthesis", "sources"}
        assert required_keys.issubset(gap.keys())

    def test_returns_empty_when_concepts_key_missing(self) -> None:
        assert detect_concept_gaps({}) == []


# =============================================================================
# 9. SELF_CRITIQUE.PY — Winner Selection
# =============================================================================

class TestSelfCritiqueHeuristicScoring:
    """Test _score_draft_heuristically and critique_and_select_winning_draft tournament logic."""

    def test_base_score_is_70(self) -> None:
        draft = {"post_text": "Short", "sources": [], "angle_name": "News"}
        score = _score_draft_heuristically(draft, {"name": "Ada"})
        assert score == 70.0  # No bonuses: text too short, no sources, no analysis angle

    def test_length_bonus_for_medium_text(self) -> None:
        text = "A" * 200  # 200 chars, in [100, 600] range
        draft = {"post_text": text, "sources": [], "angle_name": "News"}
        score = _score_draft_heuristically(draft, {})
        assert score == 80.0  # 70 base + 10 length

    def test_sources_bonus(self) -> None:
        draft = {"post_text": "Short", "sources": ["https://example.com"], "angle_name": "News"}
        score = _score_draft_heuristically(draft, {})
        assert score == 80.0  # 70 + 10 sources

    def test_analysis_angle_bonus(self) -> None:
        draft = {"post_text": "Short", "sources": [], "angle_name": "Deep Dive Analysis"}
        score = _score_draft_heuristically(draft, {})
        assert score == 75.0  # 70 + 5 analysis

    def test_all_bonuses_stacked(self) -> None:
        text = "A" * 300
        draft = {"post_text": text, "sources": ["src"], "angle_name": "Deep Dive Analysis"}
        score = _score_draft_heuristically(draft, {})
        assert score == 95.0  # 70 + 10(len) + 10(src) + 5(analysis)

    def test_score_capped_at_100(self) -> None:
        text = "A" * 300
        draft = {"post_text": text, "sources": ["s1", "s2"], "angle_name": "Deep Dive Analysis"}
        score = _score_draft_heuristically(draft, {})
        assert score <= 100.0

    @pytest.mark.asyncio
    async def test_tournament_selects_highest_scoring_draft(self) -> None:
        drafts = [
            {"angle_name": "News Flash", "post_text": "Short", "sources": []},
            {"angle_name": "Deep Dive Analysis", "post_text": "A" * 300, "sources": ["src1"]},
            {"angle_name": "Strategic Take", "post_text": "A" * 50, "sources": ["src1"]},
        ]
        with patch("app.drafting.self_critique.call_openai_json", side_effect=RuntimeError("No LLM")):
            winner = await critique_and_select_winning_draft(drafts)

        assert winner["angle_name"] == "Deep Dive Analysis"
        assert winner["score"] == 95.0  # 70 + 10(len) + 10(src) + 5(analysis)

    @pytest.mark.asyncio
    async def test_tournament_returns_default_when_drafts_empty(self) -> None:
        with patch("app.drafting.self_critique.call_openai_json", side_effect=RuntimeError("No LLM")):
            winner = await critique_and_select_winning_draft([])

        assert winner["angle_name"] == "Default Research Update"
        assert winner["score"] == 75.0

    @pytest.mark.asyncio
    async def test_tournament_uses_llm_when_available(self) -> None:
        drafts = [
            {"angle_name": "Draft A", "post_text": "Content A", "sources": []},
            {"angle_name": "Draft B", "post_text": "Content B", "sources": []},
        ]
        mock_response = {"winning_index": 1, "winning_score": 92.0, "critique_notes": "Draft B is superior"}
        with patch("app.drafting.self_critique.call_openai_json", return_value=mock_response):
            winner = await critique_and_select_winning_draft(drafts)

        assert winner["angle_name"] == "Draft B"
        assert winner["score"] == 92.0
        assert "superior" in winner["critique_notes"]

    @pytest.mark.asyncio
    async def test_tournament_falls_back_on_invalid_llm_index(self) -> None:
        drafts = [{"angle_name": "Only Draft", "post_text": "A" * 200, "sources": ["s"]}]
        mock_response = {"winning_index": 99, "winning_score": 50.0}  # Out of bounds
        with patch("app.drafting.self_critique.call_openai_json", return_value=mock_response):
            winner = await critique_and_select_winning_draft(drafts)

        # Falls back to heuristic since LLM index is invalid
        assert winner["angle_name"] == "Only Draft"


# =============================================================================
# 10. DRAFT_GENERATOR.PY — Fallback 3-Angle Generation
# =============================================================================

class TestDraftGenerator:
    """Test generate_draft_angles fallback produces 3 structured drafts with persona interpolation."""

    @pytest.mark.asyncio
    async def test_fallback_produces_3_angles(self) -> None:
        from app.drafting.draft_generator import generate_draft_angles

        with patch("app.drafting.draft_generator.call_openai_json", side_effect=RuntimeError("No LLM")):
            drafts = await generate_draft_angles(
                topic={"title": "Adversarial ML", "summary": "Techniques for adversarial attacks."},
                persona={"name": "Ada", "domain": "AI Security"},
            )

        assert len(drafts) == 3
        angle_names = [d["angle_name"] for d in drafts]
        assert "News & Key Highlights" in angle_names
        assert "In-Depth Technical Analysis" in angle_names
        assert "Strategic Implications & Predictions" in angle_names

    @pytest.mark.asyncio
    async def test_fallback_drafts_contain_persona_name_and_domain(self) -> None:
        from app.drafting.draft_generator import generate_draft_angles

        with patch("app.drafting.draft_generator.call_openai_json", side_effect=RuntimeError("No LLM")):
            drafts = await generate_draft_angles(
                topic={"title": "Test Topic", "summary": "Summary."},
                persona={"name": "Athena", "domain": "Cryptography"},
            )

        for d in drafts:
            assert "Athena" in d["post_text"]

    @pytest.mark.asyncio
    async def test_fallback_drafts_include_sources(self) -> None:
        from app.drafting.draft_generator import generate_draft_angles

        with patch("app.drafting.draft_generator.call_openai_json", side_effect=RuntimeError("No LLM")):
            drafts = await generate_draft_angles(
                topic={"title": "T", "summary": "S", "sources": ["https://paper.org/1"]},
                persona={"name": "Ada", "domain": "ML"},
            )

        for d in drafts:
            assert "https://paper.org/1" in d["sources"]

    @pytest.mark.asyncio
    async def test_llm_drafts_normalized_correctly(self) -> None:
        from app.drafting.draft_generator import generate_draft_angles

        llm_resp = {"drafts": [
            {"angle_name": "LLM Draft 1", "post_text": "Content 1", "sources": ["s1"]},
            {"angle_name": "LLM Draft 2", "post_text": "Content 2"},
        ]}
        with patch("app.drafting.draft_generator.call_openai_json", return_value=llm_resp):
            drafts = await generate_draft_angles(
                topic={"title": "T", "sources": ["fallback_src"]},
                persona={"name": "Ada", "domain": "AI"},
            )

        assert len(drafts) == 2
        assert drafts[0]["angle_name"] == "LLM Draft 1"
        assert drafts[0]["sources"] == ["s1"]


# =============================================================================
# 11. PERSONA_CHECK.PY — Banned-Word Veto and Pass-Through
# =============================================================================

class TestPersonaCheck:
    """Test verify_persona_alignment banned-word detection and pass-through."""

    @pytest.mark.asyncio
    async def test_empty_text_is_rejected(self) -> None:
        with patch("app.drafting.persona_check.call_openai_json", side_effect=RuntimeError("No LLM")):
            aligned, reason = await verify_persona_alignment(
                {"post_text": ""}, {"name": "Ada", "domain": "AI Security"}
            )
        assert aligned is False
        assert "empty" in reason.lower()

    @pytest.mark.asyncio
    async def test_banned_word_buzzword_rejected(self) -> None:
        with patch("app.drafting.persona_check.call_openai_json", side_effect=RuntimeError("No LLM")):
            aligned, reason = await verify_persona_alignment(
                {"post_text": "This is a buzzword filled article about AI"},
                {"name": "Ada", "domain": "AI Security"},
            )
        assert aligned is False
        assert "buzzword" in reason.lower()

    @pytest.mark.asyncio
    async def test_banned_word_clickbait_rejected(self) -> None:
        with patch("app.drafting.persona_check.call_openai_json", side_effect=RuntimeError("No LLM")):
            aligned, reason = await verify_persona_alignment(
                {"post_text": "Clickbait title about security vulnerability"},
                {"name": "Ada", "domain": "AI Security"},
            )
        assert aligned is False
        assert "clickbait" in reason.lower()

    @pytest.mark.asyncio
    async def test_banned_phrase_guaranteed_profit_rejected(self) -> None:
        with patch("app.drafting.persona_check.call_openai_json", side_effect=RuntimeError("No LLM")):
            aligned, reason = await verify_persona_alignment(
                {"post_text": "Get guaranteed profit from this security tool"},
                {"name": "Ada", "domain": "AI Security"},
            )
        assert aligned is False

    @pytest.mark.asyncio
    async def test_clean_draft_passes(self) -> None:
        with patch("app.drafting.persona_check.call_openai_json", side_effect=RuntimeError("No LLM")):
            aligned, reason = await verify_persona_alignment(
                {"post_text": "Rigorous analysis of transformer architecture vulnerabilities"},
                {"name": "Ada", "domain": "AI Security"},
            )
        assert aligned is True
        assert "Ada" in reason
        assert "AI Security" in reason

    @pytest.mark.asyncio
    async def test_llm_persona_check_used_when_available(self) -> None:
        mock_response = {"aligned": True, "reasons": ["Matches domain expertise", "Tone is professional"]}
        with patch("app.drafting.persona_check.call_openai_json", return_value=mock_response):
            aligned, reason = await verify_persona_alignment(
                {"post_text": "Technical analysis of novel attack vector"},
                {"name": "Ada", "domain": "AI Security"},
            )
        assert aligned is True
        assert "Matches domain expertise" in reason


# =============================================================================
# 12. PUBLISHER.PY — _extract_memory_relationship
# =============================================================================

class TestExtractMemoryRelationship:
    """Test _extract_memory_relationship classifies all relationship types."""

    def test_story_continuation_relationship(self) -> None:
        post_uuid = uuid.uuid4()
        topic = {}
        memory = {"behavior_results": {
            "story_continuation": {"related_post_id": post_uuid}
        }}
        related_id, rel_type = _extract_memory_relationship(topic, memory)
        assert related_id == post_uuid
        assert rel_type == "STORY_CONTINUATION"

    def test_prediction_resolution_relationship(self) -> None:
        post_uuid = uuid.uuid4()
        topic = {}
        memory = {"behavior_results": {
            "prediction_resolution": {"related_post_id": post_uuid}
        }}
        related_id, rel_type = _extract_memory_relationship(topic, memory)
        assert related_id == post_uuid
        assert rel_type == "PREDICTION_RESOLUTION"

    def test_topic_resurrection_relationship(self) -> None:
        topic = {}
        memory = {"behavior_results": {"resurrection": {"resurrected": True}}}
        related_id, rel_type = _extract_memory_relationship(topic, memory)
        assert related_id is None
        assert rel_type == "TOPIC_RESURRECTION"

    def test_concept_gap_relationship(self) -> None:
        topic = {}
        memory = {"behavior_results": {"concept_gaps": {"concepts": ["a", "b"]}}}
        related_id, rel_type = _extract_memory_relationship(topic, memory)
        assert related_id is None
        assert rel_type == "CONCEPT_GAP"

    def test_no_relationship_when_no_behaviors(self) -> None:
        related_id, rel_type = _extract_memory_relationship({}, {})
        assert related_id is None
        assert rel_type is None

    def test_story_from_topic_metadata_not_just_behaviors(self) -> None:
        post_uuid = uuid.uuid4()
        topic = {"story_continuation": {"related_post_id": post_uuid}}
        related_id, rel_type = _extract_memory_relationship(topic, {})
        assert related_id == post_uuid
        assert rel_type == "STORY_CONTINUATION"

    def test_string_related_post_id_not_cast_to_uuid(self) -> None:
        """String IDs should not be converted — only uuid.UUID instances are used."""
        topic = {}
        memory = {"behavior_results": {
            "story_continuation": {"related_post_id": "not-a-uuid"}
        }}
        related_id, rel_type = _extract_memory_relationship(topic, memory)
        assert related_id is None  # String is not a uuid.UUID instance
        assert rel_type == "STORY_CONTINUATION"


# =============================================================================
# 13. SCHEMAS — Validators and Serialization
# =============================================================================

class TestPersonaInSchema:
    """Test PersonaIn validation rules."""

    def test_valid_persona(self) -> None:
        p = PersonaIn(name="Ada", domain="AI Security")
        assert p.name == "Ada"
        assert p.domain == "AI Security"

    def test_strips_whitespace(self) -> None:
        p = PersonaIn(name="  Ada  ", domain="  AI Security  ")
        assert p.name == "Ada"
        assert p.domain == "AI Security"

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="", domain="AI Security")

    def test_rejects_whitespace_only_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="   ", domain="AI Security")

    def test_rejects_empty_domain(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="Ada", domain="")

    def test_rejects_whitespace_only_domain(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="Ada", domain="   ")

    def test_rejects_oversized_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="A" * 256, domain="AI Security")

    def test_rejects_oversized_domain(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="Ada", domain="D" * 256)

    def test_rejects_non_string_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name=123, domain="AI Security")


class TestInitRequestSchema:
    """Test InitRequest validation."""

    def test_valid_init_request(self) -> None:
        req = InitRequest(persona=PersonaIn(name="Ada", domain="AI Security"))
        assert req.persona.name == "Ada"

    def test_rejects_missing_persona(self) -> None:
        with pytest.raises(ValidationError):
            InitRequest()


class TestInitResponseSchema:
    """Test InitResponse validation."""

    def test_valid_init_response(self) -> None:
        resp = InitResponse(agentId="agent-abc-123")
        assert resp.agentId == "agent-abc-123"

    def test_rejects_empty_agent_id(self) -> None:
        with pytest.raises(ValidationError):
            InitResponse(agentId="")


class TestPostOutSchema:
    """Test PostOut serialization and validation."""

    def test_serializes_utc_datetime_with_z_suffix(self) -> None:
        dt = datetime(2026, 8, 8, 20, 30, 0, tzinfo=timezone.utc)
        post = PostOut(id="p1", createdAt=dt, text="Hello", rationale="R", sources=[])
        dumped = post.model_dump(mode="json")
        assert dumped["createdAt"] == "2026-08-08T20:30:00Z"

    def test_handles_naive_datetime_as_utc(self) -> None:
        naive_dt = datetime(2026, 1, 15, 10, 0, 0)
        post = PostOut(id="p2", createdAt=naive_dt, text="T", rationale="R", sources=[])
        dumped = post.model_dump(mode="json")
        assert dumped["createdAt"].endswith("Z")

    def test_handles_non_utc_timezone(self) -> None:
        from datetime import timedelta as td
        eastern = timezone(td(hours=-5))
        dt = datetime(2026, 8, 8, 15, 30, 0, tzinfo=eastern)
        post = PostOut(id="p3", createdAt=dt, text="T", rationale="R", sources=[])
        dumped = post.model_dump(mode="json")
        # 15:30 EST = 20:30 UTC
        assert dumped["createdAt"] == "2026-08-08T20:30:00Z"

    def test_rejects_empty_post_id(self) -> None:
        with pytest.raises(ValidationError):
            PostOut(id="", createdAt=datetime.now(timezone.utc), text="T", rationale="R", sources=[])


class TestFeedResponseSchema:
    """Test FeedResponse serialization."""

    def test_empty_feed(self) -> None:
        resp = FeedResponse(posts=[])
        assert resp.posts == []

    def test_feed_with_posts(self) -> None:
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        posts = [PostOut(id=f"p{i}", createdAt=dt, text=f"T{i}", rationale="R", sources=[]) for i in range(3)]
        resp = FeedResponse(posts=posts)
        assert len(resp.posts) == 3

    def test_feed_json_round_trip(self) -> None:
        dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        post = PostOut(id="p1", createdAt=dt, text="Post text", rationale="Because", sources=["https://example.com"])
        resp = FeedResponse(posts=[post])
        json_str = resp.model_dump_json()
        assert "p1" in json_str
        assert "2026-06-15T12:00:00Z" in json_str
        assert "https://example.com" in json_str


class TestBreethSearchRequestSchema:
    """Test BreethSearchRequest validation."""

    def test_valid_request(self) -> None:
        req = BreethSearchRequest(query="AI security risks", limit=5, min_score=0.7)
        assert req.query == "AI security risks"
        assert req.limit == 5
        assert req.min_score == 0.7

    def test_strips_query_whitespace(self) -> None:
        req = BreethSearchRequest(query="  padded query  ")
        assert req.query == "padded query"

    def test_rejects_empty_query(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="")

    def test_rejects_whitespace_only_query(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="   ")

    def test_rejects_min_score_above_1(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="valid", min_score=1.5)

    def test_rejects_min_score_below_0(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="valid", min_score=-0.1)

    def test_rejects_limit_below_1(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="valid", limit=0)

    def test_rejects_limit_above_100(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="valid", limit=101)

    def test_defaults(self) -> None:
        req = BreethSearchRequest(query="test")
        assert req.limit == 10
        assert req.min_score == 0.5
        assert req.filters == {}


class TestBreethItemSchema:
    """Test BreethItem validation."""

    def test_valid_item(self) -> None:
        item = BreethItem(id="i1", text="Memory text", score=0.85)
        assert item.score == 0.85
        assert item.concepts == []
        assert item.metadata == {}

    def test_rejects_score_above_1(self) -> None:
        with pytest.raises(ValidationError):
            BreethItem(id="i1", text="T", score=1.01)

    def test_rejects_score_below_0(self) -> None:
        with pytest.raises(ValidationError):
            BreethItem(id="i1", text="T", score=-0.01)


class TestBreethEpisodeInSchema:
    """Test BreethEpisodeIn validation."""

    def test_valid_episode(self) -> None:
        ep = BreethEpisodeIn(topic="Vulnerability Report", claims=["C1", "C2"])
        assert ep.topic == "Vulnerability Report"
        assert ep.stance == "neutral"
        assert ep.editorial_decision == "accepted"
        assert ep.prediction is None
        assert ep.story is None

    def test_strips_topic_whitespace(self) -> None:
        ep = BreethEpisodeIn(topic="  Padded Topic  ")
        assert ep.topic == "Padded Topic"

    def test_rejects_empty_topic(self) -> None:
        with pytest.raises(ValidationError):
            BreethEpisodeIn(topic="")

    def test_rejects_whitespace_only_topic(self) -> None:
        with pytest.raises(ValidationError):
            BreethEpisodeIn(topic="   ")

    def test_all_optional_fields(self) -> None:
        ep = BreethEpisodeIn(
            topic="Test",
            claims=["C1"],
            stance="positive",
            prediction={"text": "Will grow", "status": "active"},
            story={"id": "s1", "chapter": 2},
            open_question="What about scaling?",
            concepts=["llm", "safety"],
            sources=["https://paper.org"],
            related_posts=["p1", "p2"],
            editorial_decision="rejected",
        )
        assert ep.prediction == {"text": "Will grow", "status": "active"}
        assert ep.story == {"id": "s1", "chapter": 2}
        assert ep.editorial_decision == "rejected"
        assert len(ep.concepts) == 2

    def test_rejects_oversized_topic(self) -> None:
        with pytest.raises(ValidationError):
            BreethEpisodeIn(topic="T" * 501)


class TestBreethSearchResultSchema:
    """Test BreethSearchResult schema."""

    def test_empty_result(self) -> None:
        r = BreethSearchResult(results=[], query="test", total=0)
        assert r.results == []
        assert r.total == 0

    def test_result_with_items(self) -> None:
        items = [
            BreethItem(id="i1", text="T1", score=0.9),
            BreethItem(id="i2", text="T2", score=0.7),
        ]
        r = BreethSearchResult(results=items, query="query", total=2)
        assert len(r.results) == 2
        assert r.results[0].score == 0.9
