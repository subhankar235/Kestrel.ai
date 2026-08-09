"""APScheduler-based schedule creation and management for recurring autonomous agent cycles.

Replaces Temporal Schedules with an in-process AsyncIOScheduler.
Job state is in-memory (lost on process restart); last-run timestamps are
stored in Postgres via the Agent model's cycle_count / updated_at.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Module-level scheduler singleton ─────────────────────────────────────────
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the module-level scheduler singleton, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the scheduler if not already running (called from FastAPI lifespan)."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


def shutdown_scheduler() -> None:
    """Gracefully shutdown the scheduler (called from FastAPI lifespan)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
    _scheduler = None


async def _run_agent_cycle(agent_id: str) -> None:
    """Callback invoked by APScheduler — runs one autonomous agent cycle."""
    from app.workflows.agent_workflow import AgentWorkflow

    from app.db.session import AsyncSessionLocal
    from app.models.agent import Agent
    from app.models.cycle_run import CycleRun

    cycle_run_id = None
    started_at = datetime.now(timezone.utc)
    try:
        async with AsyncSessionLocal() as db:
            agent_result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_result.scalar_one_or_none()
            if agent is not None:
                cycle_run = CycleRun(
                    agent_id=agent.id,
                    cycle_number=(agent.cycle_count or 0) + 1,
                    started_at=started_at,
                )
                db.add(cycle_run)
                await db.commit()
                cycle_run_id = cycle_run.id
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not create cycle history for '{agent_id}': {exc}")

    logger.info(f"APScheduler firing agent cycle for '{agent_id}'")
    try:
        wf = AgentWorkflow()
        result = await wf.run(agent_id)
        logger.info(
            f"Agent cycle completed for '{agent_id}': status={result.get('status')}",
            extra={"agent_id": agent_id, "result_status": result.get("status")},
        )
        cycle_status = str(result.get("status", "completed"))
        cycle_error = None
    except BaseException as exc:  # noqa: BLE001
        result = {}
        cycle_status = "cancelled" if isinstance(exc, asyncio.CancelledError) else "failed"
        cycle_error = str(exc)
        logger.error(
            f"Agent cycle failed for '{agent_id}': {exc}",
            extra={"agent_id": agent_id, "error": str(exc)},
        )
    finally:
        if cycle_run_id is not None:
            try:
                async with AsyncSessionLocal() as db:
                    run_result = await db.execute(select(CycleRun).where(CycleRun.id == cycle_run_id))
                    cycle_run = run_result.scalar_one_or_none()
                    if cycle_run is not None:
                        cycle_run.finished_at = datetime.now(timezone.utc)
                        cycle_run.status = cycle_status
                        cycle_run.topic = result.get("topic")
                        cycle_run.published = 1 if cycle_status == "published" else 0
                        cycle_run.rejected = 1 if cycle_status == "rejected" else 0
                        cycle_run.error = cycle_error
                        cycle_run.details = result
                        await db.commit()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Could not finalize cycle history for '{agent_id}': {exc}")


async def create_agent_schedule(
    agent_id: str,
    interval_minutes: int | None = None,
    start_at: datetime | None = None,
    observation_period_hours: int | None = None,
    run_immediately: bool = False,
) -> str:
    """Register a recurring APScheduler job for the agent."""
    settings = get_settings()
    cycle_interval = interval_minutes or settings.PUBLISH_CYCLE_INTERVAL_MINUTES
    effective_start = start_at or datetime.now(timezone.utc)
    schedule_id = f"schedule_{agent_id}"

    try:
        scheduler = get_scheduler()

        # Remove existing job if present (idempotent)
        if scheduler.get_job(schedule_id):
            scheduler.remove_job(schedule_id)

        scheduler.add_job(
            _run_agent_cycle,
            trigger=IntervalTrigger(minutes=cycle_interval),
            start_date=effective_start,
            end_date=(
                effective_start
                + timedelta(hours=observation_period_hours)
                if observation_period_hours
                else None
            ),
            id=schedule_id,
            args=[agent_id],
            name=f"Agent cycle: {agent_id} (every {cycle_interval}m)",
            replace_existing=True,
        )
        if run_immediately and effective_start <= datetime.now(timezone.utc):
            asyncio.create_task(_run_agent_cycle(agent_id))
        logger.info(f"Registered APScheduler job '{schedule_id}' every {cycle_interval} minutes")
        return schedule_id

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"APScheduler job creation for agent '{agent_id}' failed: {exc}",
            extra={"agent_id": agent_id, "error": str(exc)},
        )
        return schedule_id


async def get_agent_schedule(agent_id: str) -> dict[str, Any]:
    """Retrieve details and status of an agent's scheduled job."""
    schedule_id = f"schedule_{agent_id}"
    try:
        scheduler = get_scheduler()
        job = scheduler.get_job(schedule_id)
        if job is None:
            return {
                "schedule_id": schedule_id,
                "agent_id": agent_id,
                "status": "not_found",
            }
        return {
            "schedule_id": schedule_id,
            "agent_id": agent_id,
            "paused": job.next_run_time is None,
            "note": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
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
    """Pause an active agent schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        scheduler = get_scheduler()
        scheduler.pause_job(schedule_id)
        logger.info(f"Paused schedule '{schedule_id}': {note}")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to pause schedule '{schedule_id}': {exc}")
        return False


async def unpause_agent_schedule(agent_id: str, note: str = "Unpaused by request") -> bool:
    """Resume a paused agent schedule."""
    schedule_id = f"schedule_{agent_id}"
    try:
        scheduler = get_scheduler()
        scheduler.resume_job(schedule_id)
        logger.info(f"Resumed schedule '{schedule_id}': {note}")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to resume schedule '{schedule_id}': {exc}")
        return False


async def delete_agent_schedule(agent_id: str) -> bool:
    """Delete an agent's scheduled job."""
    schedule_id = f"schedule_{agent_id}"
    try:
        scheduler = get_scheduler()
        scheduler.remove_job(schedule_id)
        logger.info(f"Deleted schedule '{schedule_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to delete schedule '{schedule_id}': {exc}")
        return False


async def trigger_agent_schedule_immediately(agent_id: str) -> bool:
    """Trigger an immediate one-shot execution of the agent cycle."""
    try:
        await _run_agent_cycle(agent_id)
        logger.info(f"Triggered immediate execution for agent '{agent_id}'")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to trigger immediate execution for agent '{agent_id}': {exc}")
        return False


async def restore_active_agent_schedules() -> int:
    """Query Postgres for active agents on server restart and ensure their jobs are scheduled."""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.agent import Agent

    restored_count = 0
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Agent).where(Agent.status == "active"))
            agents = result.scalars().all()
            for agent in agents:
                await create_agent_schedule(
                    agent.agent_id,
                    interval_minutes=agent.publish_interval_minutes,
                    start_at=agent.start_at or agent.created_at,
                    observation_period_hours=agent.observation_period_hours,
                )
                restored_count += 1
        if restored_count > 0:
            logger.info(f"Restored {restored_count} active agent schedule(s) into APScheduler")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not restore active agent schedules on boot: {exc}")
    return restored_count
