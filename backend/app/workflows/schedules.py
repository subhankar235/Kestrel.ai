"""Temporal Schedule creation and management for recurring autonomous agent cycles."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
    ScheduleState,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.workflows.agent_workflow import AgentWorkflow

logger = get_logger(__name__)


async def _get_temporal_client() -> Client:
    """Connect and return a Temporal Client instance based on application settings."""
    settings = get_settings()
    return await Client.connect(
        settings.TEMPORAL_ADDRESS,
        namespace=settings.TEMPORAL_NAMESPACE,
    )


async def create_agent_schedule(agent_id: str, interval_minutes: int | None = None) -> str:
    """Register or update a recurring Temporal Schedule for the agent."""
    settings = get_settings()
    cycle_interval = interval_minutes or settings.PUBLISH_CYCLE_INTERVAL_MINUTES
    schedule_id = f"schedule_{agent_id}"

    try:
        client = await _get_temporal_client()

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
            state=ScheduleState(
                note=f"Primary publish cycle schedule for agent '{agent_id}' running every {cycle_interval}m"
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


async def get_agent_schedule(agent_id: str) -> dict[str, Any]:
    """Retrieve details and status of an agent's Temporal Schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        client = await _get_temporal_client()
        handle = client.get_schedule_handle(schedule_id)
        description = await handle.describe()
        return {
            "schedule_id": schedule_id,
            "agent_id": agent_id,
            "paused": description.schedule.state.paused,
            "note": description.schedule.state.note,
            "actions": description.info.num_actions,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not retrieve schedule '{schedule_id}': {exc}")
        return {
            "schedule_id": schedule_id,
            "agent_id": agent_id,
            "status": "unavailable",
            "error": str(exc),
        }


async def pause_agent_schedule(agent_id: str, note: str = "Paused by request") -> bool:
    """Pause an active agent Temporal Schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        client = await _get_temporal_client()
        handle = client.get_schedule_handle(schedule_id)
        await handle.pause(note=note)
        logger.info(f"Paused Temporal Schedule '{schedule_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to pause schedule '{schedule_id}': {exc}")
        return False


async def unpause_agent_schedule(agent_id: str, note: str = "Unpaused by request") -> bool:
    """Unpause / resume a paused agent Temporal Schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        client = await _get_temporal_client()
        handle = client.get_schedule_handle(schedule_id)
        await handle.unpause(note=note)
        logger.info(f"Unpaused Temporal Schedule '{schedule_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to unpause schedule '{schedule_id}': {exc}")
        return False


async def delete_agent_schedule(agent_id: str) -> bool:
    """Delete an agent's Temporal Schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        client = await _get_temporal_client()
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        logger.info(f"Deleted Temporal Schedule '{schedule_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to delete schedule '{schedule_id}': {exc}")
        return False


async def trigger_agent_schedule_immediately(agent_id: str) -> bool:
    """Trigger an immediate action execution on the agent's Temporal Schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        client = await _get_temporal_client()
        handle = client.get_schedule_handle(schedule_id)
        await handle.trigger()
        logger.info(f"Triggered immediate execution for schedule '{schedule_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to trigger schedule '{schedule_id}': {exc}")
        return False
