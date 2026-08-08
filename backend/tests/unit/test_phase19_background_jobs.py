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
        mock_client = AsyncMock()
        with patch("app.workflows.schedules._get_temporal_client", return_value=mock_client):
            schedule_id = await create_agent_schedule("agent_phase19_1", interval_minutes=60)
            assert schedule_id == "schedule_agent_phase19_1"
            assert mock_client.create_schedule.called

    @pytest.mark.asyncio
    async def test_create_agent_schedule_fallback_on_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.create_schedule.side_effect = Exception("Temporal server not reachable")
        with patch("app.workflows.schedules._get_temporal_client", return_value=mock_client):
            schedule_id = await create_agent_schedule("agent_phase19_2")
            assert schedule_id == "schedule_agent_phase19_2"

    @pytest.mark.asyncio
    async def test_get_agent_schedule(self) -> None:
        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_desc = MagicMock()
        mock_desc.schedule.state.paused = False
        mock_desc.schedule.state.note = "Test schedule"
        mock_desc.info.num_actions = 5
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_client.get_schedule_handle.return_value = mock_handle

        with patch("app.workflows.schedules._get_temporal_client", AsyncMock(return_value=mock_client)):
            res = await get_agent_schedule("agent_phase19_3")
            assert res["schedule_id"] == "schedule_agent_phase19_3"
            assert res["paused"] is False
            assert res["actions"] == 5

    @pytest.mark.asyncio
    async def test_pause_and_unpause_schedule(self) -> None:
        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_handle.pause = AsyncMock()
        mock_handle.unpause = AsyncMock()
        mock_client.get_schedule_handle.return_value = mock_handle

        with patch("app.workflows.schedules._get_temporal_client", AsyncMock(return_value=mock_client)):
            paused = await pause_agent_schedule("agent_phase19_4")
            assert paused is True

            unpaused = await unpause_agent_schedule("agent_phase19_4")
            assert unpaused is True

    @pytest.mark.asyncio
    async def test_delete_and_trigger_schedule(self) -> None:
        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_handle.trigger = AsyncMock()
        mock_handle.delete = AsyncMock()
        mock_client.get_schedule_handle.return_value = mock_handle

        with patch("app.workflows.schedules._get_temporal_client", AsyncMock(return_value=mock_client)):
            triggered = await trigger_agent_schedule_immediately("agent_phase19_5")
            assert triggered is True

            deleted = await delete_agent_schedule("agent_phase19_5")
            assert deleted is True


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
    async def test_workflow_executes_secondary_checks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_topic = {"title": "Secondary Check Topic", "sources": ["https://example.com"]}
        activities_run = []

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))
            activities_run.append(func_name)

            if "record_and_increment" in func_name:
                return 10  # 10th cycle triggers self audit
            if "prediction_sweep" in func_name:
                return [{"title": "Resolved Prediction", "is_prediction_resolution": True}]
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
                return {"post_id": "p_sec123", "text": "Winning post text"}
            if "rationale" in func_name:
                return "Selection rationale text"
            if "self_audit" in func_name:
                return {"status": "audit_complete", "version_bump": False}
            if "breeth" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_sec_test")

        assert result["status"] == "published"
        assert result["cycle_count"] == 10
        assert result["predictions_swept"] == 1
        assert result["self_audit_executed"] is True
        assert "record_and_increment_cycle_activity" in activities_run
        assert "prediction_sweep_activity" in activities_run
        assert "self_audit_activity" in activities_run

    @pytest.mark.asyncio
    async def test_workflow_skips_self_audit_on_non_nth_cycle(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_topic = {"title": "Normal Cycle Topic"}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))
            if "record_and_increment" in func_name:
                return 3  # 3rd cycle (not multiple of 10)
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name or "behaviors" in func_name:
                return {}
            if "judge" in func_name:
                return {"accepted": False, "reason": "Below score threshold"}
            if "debt" in func_name or "breeth" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_non_nth_test")

        assert result["status"] == "rejected"
        assert result["cycle_count"] == 3
        assert result["self_audit_executed"] is False
