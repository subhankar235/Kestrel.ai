"""Unit tests for Phase 19 — Background Jobs / Events / Webhooks."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.agent import Agent
from app.schemas.memory import BreethSearchResult
from app.workflows.activities import (
    prediction_sweep_activity,
    record_and_increment_cycle_activity,
)
from app.workflows.agent_workflow import AgentWorkflow
from app.workflows.schedules import (
    create_agent_schedule,
    delete_agent_schedule,
    get_agent_schedule,
    pause_agent_schedule,
    trigger_agent_schedule_immediately,
    unpause_agent_schedule,
)


class TestCadenceConfig:
    def test_publish_cycle_and_self_audit_config(self) -> None:
        settings = get_settings()
        assert hasattr(settings, "PUBLISH_CYCLE_INTERVAL_MINUTES")
        assert hasattr(settings, "SELF_AUDIT_EVERY_N_CYCLES")
        assert settings.PUBLISH_CYCLE_INTERVAL_MINUTES > 0
        assert settings.SELF_AUDIT_EVERY_N_CYCLES > 0


class TestScheduleManagement:
    @pytest.mark.asyncio
    async def test_create_agent_schedule_success(self) -> None:
        mock_scheduler = MagicMock()
        mock_scheduler.get_job.return_value = None
        with patch("app.workflows.schedules.get_scheduler", return_value=mock_scheduler):
            schedule_id = await create_agent_schedule("agent_phase19_1", interval_minutes=60)
            assert schedule_id == "schedule_agent_phase19_1"
            assert mock_scheduler.add_job.called

    @pytest.mark.asyncio
    async def test_create_agent_schedule_fallback_on_error(self) -> None:
        mock_scheduler = MagicMock()
        mock_scheduler.get_job.side_effect = Exception("Scheduler not available")
        with patch("app.workflows.schedules.get_scheduler", return_value=mock_scheduler):
            schedule_id = await create_agent_schedule("agent_phase19_2")
            assert schedule_id == "schedule_agent_phase19_2"

    @pytest.mark.asyncio
    async def test_get_agent_schedule(self) -> None:
        mock_scheduler = MagicMock()
        mock_job = MagicMock()
        mock_job.next_run_time = "2026-01-01 00:00:00"
        mock_job.name = "Test schedule"
        mock_scheduler.get_job.return_value = mock_job

        with patch("app.workflows.schedules.get_scheduler", return_value=mock_scheduler):
            res = await get_agent_schedule("agent_phase19_3")
            assert res["schedule_id"] == "schedule_agent_phase19_3"
            assert res["paused"] is False

    @pytest.mark.asyncio
    async def test_pause_and_unpause_schedule(self) -> None:
        mock_scheduler = MagicMock()
        with patch("app.workflows.schedules.get_scheduler", return_value=mock_scheduler):
            paused = await pause_agent_schedule("agent_phase19_4")
            assert paused is True
            assert mock_scheduler.pause_job.called

            unpaused = await unpause_agent_schedule("agent_phase19_4")
            assert unpaused is True
            assert mock_scheduler.resume_job.called

    @pytest.mark.asyncio
    async def test_delete_and_trigger_schedule(self) -> None:
        mock_scheduler = MagicMock()
        with patch("app.workflows.schedules.get_scheduler", return_value=mock_scheduler):
            deleted = await delete_agent_schedule("agent_phase19_5")
            assert deleted is True
            assert mock_scheduler.remove_job.called

        with patch("app.workflows.schedules._run_agent_cycle", new_callable=AsyncMock):
            triggered = await trigger_agent_schedule_immediately("agent_phase19_5")
            assert triggered is True


class TestSecondaryActivities:
    @pytest.mark.asyncio
    async def test_record_and_increment_cycle_activity(self, db_session: AsyncSession) -> None:
        agent = Agent(agent_id="agent_cycle_test", status="active", cycle_count=0)
        db_session.add(agent)
        await db_session.commit()

        c1 = await record_and_increment_cycle_activity("agent_cycle_test")
        assert c1 == 1

        c2 = await record_and_increment_cycle_activity("agent_cycle_test")
        assert c2 == 2

    @pytest.mark.asyncio
    async def test_prediction_sweep_activity(self) -> None:
        mock_search_res = BreethSearchResult(query="Prediction Sweep", results=[], total=0)
        with patch("app.memory.recall.search_memory", AsyncMock(return_value=mock_search_res)):
            res = await prediction_sweep_activity("agent_sweep_test")
            assert isinstance(res, list)


class TestWorkflowSecondaryCheckOrchestration:
    @pytest.mark.asyncio
    async def test_workflow_executes_secondary_checks(self) -> None:
        mock_topic = {"title": "Secondary Check Topic", "sources": ["https://example.com"]}

        with (
            patch("app.workflows.agent_workflow.record_and_increment_cycle_activity", new_callable=AsyncMock, return_value=10),
            patch("app.workflows.agent_workflow.prediction_sweep_activity", new_callable=AsyncMock, return_value=[{"title": "Resolved Prediction", "is_prediction_resolution": True}]),
            patch("app.workflows.agent_workflow.discover_topics_activity", new_callable=AsyncMock, return_value=[mock_topic]),
            patch("app.workflows.agent_workflow.recall_memory_activity", new_callable=AsyncMock, return_value={"stories": []}),
            patch("app.workflows.agent_workflow.run_memory_behaviors_activity", new_callable=AsyncMock, return_value={"stories": []}),
            patch("app.workflows.agent_workflow.editorial_judge_activity", new_callable=AsyncMock, return_value={"accepted": True, "reason": "Score 85 meets threshold"}),
            patch("app.workflows.agent_workflow.generate_drafts_activity", new_callable=AsyncMock, return_value=[{"post_text": "Winning post text", "sources": ["https://example.com"]}]),
            patch("app.workflows.agent_workflow.self_critique_activity", new_callable=AsyncMock, return_value={"post_text": "Winning post text", "sources": ["https://example.com"]}),
            patch("app.workflows.agent_workflow.persona_check_activity", new_callable=AsyncMock, return_value={"aligned": True}),
            patch("app.workflows.agent_workflow.publish_post_activity", new_callable=AsyncMock, return_value={"post_id": "p_sec123", "text": "Winning post text"}),
            patch("app.workflows.agent_workflow.build_rationale_activity", new_callable=AsyncMock, return_value="Selection rationale text"),
            patch("app.workflows.agent_workflow.write_breeth_episode_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
            patch("app.workflows.agent_workflow.self_audit_activity", new_callable=AsyncMock, return_value={"status": "audit_complete", "version_bump": False}),
        ):
            wf = AgentWorkflow()
            result = await wf.run("agent_sec_test")

        assert result["status"] == "published"
        assert result["cycle_count"] == 10
        assert result["predictions_swept"] == 1
        assert result["self_audit_executed"] is True

    @pytest.mark.asyncio
    async def test_workflow_skips_self_audit_on_non_nth_cycle(self) -> None:
        mock_topic = {"title": "Normal Cycle Topic"}

        with (
            patch("app.workflows.agent_workflow.record_and_increment_cycle_activity", new_callable=AsyncMock, return_value=3),
            patch("app.workflows.agent_workflow.prediction_sweep_activity", new_callable=AsyncMock, return_value=[]),
            patch("app.workflows.agent_workflow.discover_topics_activity", new_callable=AsyncMock, return_value=[mock_topic]),
            patch("app.workflows.agent_workflow.recall_memory_activity", new_callable=AsyncMock, return_value={}),
            patch("app.workflows.agent_workflow.run_memory_behaviors_activity", new_callable=AsyncMock, return_value={}),
            patch("app.workflows.agent_workflow.editorial_judge_activity", new_callable=AsyncMock, return_value={"accepted": False, "reason": "Below score threshold"}),
            patch("app.workflows.agent_workflow.log_topic_debt_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
            patch("app.workflows.agent_workflow.write_breeth_episode_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
            patch("app.workflows.agent_workflow.self_audit_activity", new_callable=AsyncMock, return_value={"status": "ok"}),
        ):
            wf = AgentWorkflow()
            result = await wf.run("agent_non_nth_test")

        assert result["status"] == "rejected"
        assert result["cycle_count"] == 3
        assert result["self_audit_executed"] is False
