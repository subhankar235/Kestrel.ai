"""Unit and integration tests for Phase 20 — Business Logic (Drafting, Persona Check, Publishing)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.drafting.draft_generator import generate_draft_angles
from app.drafting.persona_check import verify_persona_alignment
from app.drafting.self_critique import critique_and_select_winning_draft
from app.main import app
from app.models.agent import Agent
from app.models.persona import Persona
from app.models.post import Post
from app.publishing.publisher import publish_final_post
from app.publishing.rationale_builder import build_post_rationale


class TestDraftGenerator:
    @pytest.mark.asyncio
    async def test_generate_draft_angles_fallback(self) -> None:
        topic = {"title": "AI Zero-Day Security", "summary": "Vulnerability identified in LLM parsers."}
        persona = {"name": "Ada", "domain": "AI Security"}

        with patch("app.drafting.draft_generator.call_openai_json", side_effect=Exception("API Key Missing")):
            drafts = await generate_draft_angles(topic, persona)
            assert isinstance(drafts, list)
            assert len(drafts) == 3
            angles = [d["angle_name"] for d in drafts]
            assert "News & Key Highlights" in angles
            assert "In-Depth Technical Analysis" in angles
            assert "Strategic Implications & Predictions" in angles
            for d in drafts:
                assert "post_text" in d
                assert "sources" in d


class TestSelfCritique:
    @pytest.mark.asyncio
    async def test_critique_and_select_winning_draft(self) -> None:
        drafts = [
            {"angle_name": "News Angle", "angle_type": "news", "post_text": "Short news post", "sources": ["https://news.com"]},
            {"angle_name": "Deep Dive Angle", "angle_type": "analysis", "post_text": "In-depth technical breakdown of architectural vulnerabilities in machine learning frameworks.", "sources": ["https://paper.com"]},
            {"angle_name": "Prediction Angle", "angle_type": "prediction", "post_text": "Future forecast", "sources": []},
        ]

        with patch("app.drafting.self_critique.call_openai_json", side_effect=Exception("LLM Disabled")):
            winner = await critique_and_select_winning_draft(drafts)
            assert winner["angle_name"] == "Deep Dive Angle"
            assert "score" in winner
            assert winner["score"] > 70.0


class TestPersonaCheck:
    @pytest.mark.asyncio
    async def test_verify_persona_alignment_success(self) -> None:
        draft = {"post_text": "In-depth security analysis of LLM prompt injection vectors."}
        persona = {"name": "Ada", "domain": "AI Security"}

        with patch("app.drafting.persona_check.call_openai_json", side_effect=Exception("LLM Disabled")):
            aligned, reason = await verify_persona_alignment(draft, persona)
            assert aligned is True
            assert "Ada" in reason

    @pytest.mark.asyncio
    async def test_verify_persona_alignment_veto(self) -> None:
        draft = {"post_text": "Buy this clickbait stock now guaranteed profit!"}
        persona = {"name": "Ada", "domain": "AI Security"}

        with patch("app.drafting.persona_check.call_openai_json", side_effect=Exception("LLM Disabled")):
            aligned, reason = await verify_persona_alignment(draft, persona)
            assert aligned is False
            assert "forbidden term" in reason


class TestRationaleBuilder:
    @pytest.mark.asyncio
    async def test_build_post_rationale_with_memory_link(self) -> None:
        topic = {"title": "AI Model Vulnerability"}
        memory_ctx = {
            "behavior_results": {
                "story_continuation": {
                    "related_post_id": "p_orig123",
                    "next_chapter": 2,
                    "resolved_question": "How to patch zero-day model weights?",
                }
            }
        }
        draft = {"post_text": "Detailed security post."}

        rationale = await build_post_rationale(topic, memory_ctx, draft)
        assert isinstance(rationale, str)
        assert "Story Continuation (Chapter 2)" in rationale
        assert "p_orig123" in rationale


class TestPublisher:
    @pytest.mark.asyncio
    async def test_publish_final_post_database_persistence(self, db_session: AsyncSession) -> None:
        agent_id = "agent_pub_test_100"
        agent = Agent(agent_id=agent_id, status="active")
        db_session.add(agent)
        await db_session.commit()

        orig_post = Post(
            post_id="p_orig_999",
            agent_id=agent.id,
            text="Original story chapter 1 post text.",
            rationale="Initial story chapter",
            sources=["https://example.com/ch1"],
        )
        db_session.add(orig_post)
        await db_session.commit()

        topic = {"title": "Chapter 2 Research"}
        draft = {
            "post_text": "Follow-up chapter 2 security analysis post.",
            "sources": ["https://example.com/ch2"],
        }
        memory_ctx = {
            "behavior_results": {
                "story_continuation": {
                    "related_post_id": orig_post.id,
                    "next_chapter": 2,
                    "resolved_question": "What is the mitigation?",
                }
            }
        }

        published = await publish_final_post(
            agent_id=agent_id,
            draft=draft,
            topic=topic,
            memory_context=memory_ctx,
            rationale="Story Continuation (Chapter 2): Answers question",
            db_session=db_session,
        )

        assert published["id"].startswith("p_")
        assert published["agent_id"] == agent_id
        assert published["text"] == draft["post_text"]
        assert published["sources"] == draft["sources"]
        assert published["related_post_id"] == str(orig_post.id)
        assert published["relationship"] == "STORY_CONTINUATION"

        # Verify DB retrieval
        db_post = (await db_session.execute(select(Post).where(Post.post_id == published["id"]))).scalar_one_or_none()
        assert db_post is not None
        assert db_post.text == draft["post_text"]


class TestEndToEndAcceptPathFeedIntegration:
    @pytest.mark.asyncio
    async def test_accept_path_feed_integration(self, client: AsyncClient, db_session: AsyncSession) -> None:
        agent_id = "agent_feed_accept_200"
        agent = Agent(agent_id=agent_id, status="active")
        db_session.add(agent)
        await db_session.commit()

        persona = Persona(agent_id=agent.id, name="Ada", domain="AI Security", voice_config={"tone": "analytical"})
        db_session.add(persona)
        await db_session.commit()

        topic = {"title": "AI Model Robustness", "summary": "Breakthrough in adversarial defense.", "sources": ["https://arxiv.org/abs/2000.0000"]}
        drafts = await generate_draft_angles(topic, {"name": "Ada", "domain": "AI Security"})
        winner = await critique_and_select_winning_draft(drafts)
        aligned, _ = await verify_persona_alignment(winner, {"name": "Ada", "domain": "AI Security"})
        assert aligned is True

        rationale = await build_post_rationale(topic, {}, winner)
        pub_res = await publish_final_post(
            agent_id=agent_id,
            draft=winner,
            topic=topic,
            rationale=rationale,
            db_session=db_session,
        )

        # Call GET /api/agent/feed?agentId=agent_feed_accept_200 via test client fixture
        resp = await client.get(f"/api/agent/feed?agentId={agent_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "posts" in data
        assert len(data["posts"]) >= 1
        first_post = data["posts"][0]
        assert first_post["id"] == pub_res["id"]
        assert first_post["text"] == winner["post_text"]
        assert first_post["rationale"] == rationale
        assert first_post["sources"] == pub_res["sources"]
        assert "createdAt" in first_post

