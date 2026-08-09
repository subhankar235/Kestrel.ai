"""Unit and workflow tests for Phase 15 Agent Architecture and Workflows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


def _make_activity_mocks(mock_execute_map: dict) -> dict:
    """Create patch context managers for each activity function."""
    patches = {}
    for activity_name, return_value in mock_execute_map.items():
        if callable(return_value) and not isinstance(return_value, (dict, list)):
            patches[activity_name] = patch(
                f"app.workflows.agent_workflow.{activity_name}",
                side_effect=return_value,
            )
        else:
            patches[activity_name] = patch(
                f"app.workflows.agent_workflow.{activity_name}",
                new_callable=AsyncMock,
                return_value=return_value,
            )
    return patches


class TestAgentWorkflowExecution:
    @pytest.mark.asyncio
    async def test_workflow_accept_path_mocked(self) -> None:
        """Simulate workflow execution accept branch."""
        mock_topic = {"title": "Accepted AI Topic", "sources": ["https://example.com"]}

        with (
            patch("app.workflows.agent_workflow.record_and_increment_cycle_activity", new_callable=AsyncMock, return_value=1),
            patch("app.workflows.agent_workflow.prediction_sweep_activity", new_callable=AsyncMock, return_value=[]),
            patch("app.workflows.agent_workflow.discover_topics_activity", new_callable=AsyncMock, return_value=[mock_topic]),
            patch("app.workflows.agent_workflow.recall_memory_activity", new_callable=AsyncMock, return_value={"stories": []}),
            patch("app.workflows.agent_workflow.run_memory_behaviors_activity", new_callable=AsyncMock, return_value={"stories": []}),
            patch("app.workflows.agent_workflow.editorial_judge_activity", new_callable=AsyncMock, return_value={"accepted": True, "reason": "Score 85 meets threshold"}),
            patch("app.workflows.agent_workflow.generate_drafts_activity", new_callable=AsyncMock, return_value=[{"post_text": "Winning post text", "sources": ["https://example.com"]}]),
            patch("app.workflows.agent_workflow.self_critique_activity", new_callable=AsyncMock, return_value={"post_text": "Winning post text", "sources": ["https://example.com"]}),
            patch("app.workflows.agent_workflow.persona_check_activity", new_callable=AsyncMock, return_value={"aligned": True}),
            patch("app.workflows.agent_workflow.publish_post_activity", new_callable=AsyncMock, return_value={"post_id": "p_test123", "text": "Winning post text"}),
            patch("app.workflows.agent_workflow.build_rationale_activity", new_callable=AsyncMock, return_value="Selection rationale text"),
            patch("app.workflows.agent_workflow.write_breeth_episode_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
            patch("app.workflows.agent_workflow.self_audit_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
        ):
            from app.workflows.agent_workflow import AgentWorkflow
            wf = AgentWorkflow()
            result = await wf.run("agent_test_123")

        assert result["status"] == "published"
        assert result["post_id"] == "p_test123"
        assert result["text"] == "Winning post text"

    @pytest.mark.asyncio
    async def test_workflow_reject_path_mocked(self) -> None:
        """Simulate workflow execution reject branch."""
        mock_topic = {"title": "Low Quality Hype Topic"}

        with (
            patch("app.workflows.agent_workflow.record_and_increment_cycle_activity", new_callable=AsyncMock, return_value=1),
            patch("app.workflows.agent_workflow.prediction_sweep_activity", new_callable=AsyncMock, return_value=[]),
            patch("app.workflows.agent_workflow.discover_topics_activity", new_callable=AsyncMock, return_value=[mock_topic]),
            patch("app.workflows.agent_workflow.recall_memory_activity", new_callable=AsyncMock, return_value={}),
            patch("app.workflows.agent_workflow.run_memory_behaviors_activity", new_callable=AsyncMock, return_value={}),
            patch("app.workflows.agent_workflow.editorial_judge_activity", new_callable=AsyncMock, return_value={"accepted": False, "reason": "Score 40 below threshold 60.0"}),
            patch("app.workflows.agent_workflow.log_topic_debt_activity", new_callable=AsyncMock, return_value={"status": "logged"}),
            patch("app.workflows.agent_workflow.write_breeth_episode_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
            patch("app.workflows.agent_workflow.self_audit_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
        ):
            from app.workflows.agent_workflow import AgentWorkflow
            wf = AgentWorkflow()
            result = await wf.run("agent_test_123")

        assert result["status"] == "rejected"
        assert result["topic"] == "Low Quality Hype Topic"
        assert "below threshold" in result["reason"]
