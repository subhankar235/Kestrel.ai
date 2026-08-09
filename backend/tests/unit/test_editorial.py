"""Unit tests for Phase 18 editorial scorer, judge, and topic debt logger."""

from __future__ import annotations

import pytest

from app.editorial.judge import judge_topic_score
from app.editorial.scorer import score_candidate_topic
from app.editorial.topic_debt import log_rejected_topic


class TestEditorialScorerAndJudge:
    @pytest.mark.asyncio
    async def test_score_candidate_topic(self) -> None:
        topic = {
            "title": "Empirical Proof of LLM Guardrail Jailbreak",
            "summary": "Detailed research paper proving zero-day exploit.",
        }
        memory_ctx = {}
        rules = {"accept_threshold": 60.0}

        scores = await score_candidate_topic(topic, memory_ctx, rules)
        assert "total_score" in scores
        assert scores["total_score"] > 0.0

    def test_judge_topic_score_accept(self) -> None:
        scores = {"total_score": 85.0, "reasoning": "High empirical evidence"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is True
        assert "ACCEPTED" in reason

    def test_judge_topic_score_reject(self) -> None:
        scores = {"total_score": 45.0, "reasoning": "Unsubstantiated claims"}
        accepted, reason = judge_topic_score(scores, accept_threshold=60.0)
        assert accepted is False
        assert "REJECTED" in reason

    @pytest.mark.asyncio
    async def test_log_rejected_topic(self, db_session) -> None:
        topic = {"title": "Low Quality Hype Topic"}
        res = await log_rejected_topic(
            topic,
            reason="Below threshold",
            revisit_condition="Revisit on new proof",
            db=db_session,
        )
        assert res["status"] == "logged"
        assert res["title"] == "Low Quality Hype Topic"
