"""Temporal Schedule creation and management for recurring autonomous agent cycles."""

from __future__ import annotations

from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.workflows.agent_workflow import AgentWorkflow

logger = get_logger(__name__)


async def create_agent_schedule(agent_id: str, interval_minutes: int | None = None) -> str:
    """Register or update a recurring Temporal Schedule for the agent."""
    settings = get_settings()
    cycle_interval = interval_minutes or settings.PUBLISH_CYCLE_INTERVAL_MINUTES
    schedule_id = f"schedule_{agent_id}"

    try:
        client = await Client.connect(
            settings.TEMPORAL_ADDRESS,
            namespace=settings.TEMPORAL_NAMESPACE,
        )

        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                AgentWorkflow.run,
                agent_id,
                id=f"workflow_{agent_id}",
                task_queue=settings.TEMPORAL_TASK_QUEUE,
            ),
            spec=ScheduleSpec(
                intervals=[ScheduleIntervalSpec(every=timedelta(minutes=cycle_interval))]
            ),
        )

        await client.create_schedule(
            schedule_id,
            schedule,
        )
        logger.info(f"Registered Temporal Schedule '{schedule_id}' every {cycle_interval} minutes")
        return schedule_id

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"Temporal Schedule creation for agent '{agent_id}' skipped or unavailable: {exc}",
            extra={"agent_id": agent_id, "error": str(exc)},
        )
        return schedule_id
