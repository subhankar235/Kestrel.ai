"""Unit and workflow tests for Phase 15 Agent Architecture and Workflows."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.persona.constitution import get_default_constitution_rules
from app.persona.voice import build_voice_config
from app.workflows.activities import (
    editorial_judge_activity,
    generate_drafts_activity,
    log_topic_debt_activity,
    publish_post_activity,
)


class TestPersonaAndConstitution:
    def test_default_constitution_rules(self) -> None:
        rules = get_default_constitution_rules()
        assert rules["relevance_threshold"] == 60.0
        assert rules["accept_threshold"] == 60.0
        assert rules["hype_penalty_max"] == 20.0

    def test_build_voice_config_security_domain(self) -> None:
        voice = build_voice_config("Ada", "AI Security")
        assert voice["name"] == "Ada"
        assert voice["domain"] == "AI Security"
        assert "security" in voice["tone"].lower()

    def test_build_voice_config_default_domain(self) -> None:
        voice = build_voice_config("Custom", "Quantum Computing")
        assert voice["name"] == "Custom"
        assert "Quantum Computing" in voice["stance"]


class TestActivities:
    @pytest.mark.asyncio
    async def test_editorial_judge_activity_accept(self, db_session: AsyncSession) -> None:
        agent = Agent(agent_id="agent_test_123", status="active")
        db_session.add(agent)
        await db_session.commit()

        topic = {"title": "AI Zero-Day Vulnerability", "summary": "Detailed security discovery"}
        memory_ctx = {"stories": [], "beliefs": []}
        result = await editorial_judge_activity("agent_test_123", topic, memory_ctx)

        assert "accepted" in result
        assert "reason" in result
        assert "scores" in result

    @pytest.mark.asyncio
    async def test_log_topic_debt_activity(self, db_session: AsyncSession) -> None:
        agent = Agent(agent_id="agent_test_456", status="active")
        db_session.add(agent)
        await db_session.commit()

        topic = {"title": "Rejected Topic"}
        judge_res = {"reason": "Low novelty score"}
        result = await log_topic_debt_activity("agent_test_456", topic, judge_res)

        assert result["status"] == "logged"
        assert result["title"] == "Rejected Topic"

    @pytest.mark.asyncio
    async def test_generate_drafts_activity(self, db_session: AsyncSession) -> None:
        agent = Agent(agent_id="agent_test_789", status="active")
        db_session.add(agent)
        await db_session.commit()

        topic = {"title": "AI Model Alignment", "sources": ["https://example.com/paper"]}
        drafts = await generate_drafts_activity("agent_test_789", topic, {})

        assert isinstance(drafts, list)
        assert len(drafts) >= 1
        assert "post_text" in drafts[0] or "text" in drafts[0]


class TestAgentWorkflowExecution:
    @pytest.mark.asyncio
    async def test_workflow_accept_path_mocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate workflow execution accept branch."""
        mock_topic = {"title": "Accepted AI Topic", "sources": ["https://example.com"]}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name or "behaviors" in func_name:
                return {"stories": []}
            if "judge" in func_name:
                return {"accepted": True, "reason": "Score 85 meets threshold"}
            if "drafts" in func_name:
                return [{"post_text": "Winning post text", "sources": ["https://example.com"]}]
            if "critique" in func_name:
                return {"post_text": "Winning post text", "sources": ["https://example.com"]}
            if "persona" in func_name:
                return {"aligned": True}
            if "publish" in func_name:
                return {"post_id": "p_test123", "text": "Winning post text"}
            if "rationale" in func_name:
                return "Selection rationale text"
            if "breeth" in func_name or "audit" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        from app.workflows.agent_workflow import AgentWorkflow
        wf = AgentWorkflow()
        result = await wf.run("agent_test_123")

        assert result["status"] == "published"
        assert result["post_id"] == "p_test123"
        assert result["text"] == "Winning post text"

    @pytest.mark.asyncio
    async def test_workflow_reject_path_mocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate workflow execution reject branch."""
        mock_topic = {"title": "Low Quality Hype Topic"}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name or "behaviors" in func_name:
                return {}
            if "judge" in func_name:
                return {"accepted": False, "reason": "Score 40 below threshold 60.0"}
            if "debt" in func_name:
                return {"status": "logged"}
            if "breeth" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        from app.workflows.agent_workflow import AgentWorkflow
        wf = AgentWorkflow()
        result = await wf.run("agent_test_123")

        assert result["status"] == "rejected"
        assert result["topic"] == "Low Quality Hype Topic"
        assert "below threshold" in result["reason"]
