"""Standalone Temporal Worker process entrypoint polling TEMPORAL_TASK_QUEUE.

Phase 22: Sentry is initialized in the worker process independently of FastAPI so unhandled
exceptions from Activities are captured in Sentry tagged with the correct environment.
"""

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import get_settings
from app.core.logging import get_logger, init_sentry

from app.workflows.activities import (

    build_rationale_activity,
    discover_topics_activity,
    editorial_judge_activity,
    generate_drafts_activity,
    log_topic_debt_activity,
    persona_check_activity,
    prediction_sweep_activity,
    publish_post_activity,
    recall_memory_activity,
    record_and_increment_cycle_activity,
    run_memory_behaviors_activity,
    self_audit_activity,
    self_critique_activity,
    write_breeth_episode_activity,
)
from app.workflows.agent_workflow import AgentWorkflow

logger = get_logger(__name__)

ALL_ACTIVITIES = [
    discover_topics_activity,
    recall_memory_activity,
    run_memory_behaviors_activity,
    editorial_judge_activity,
    log_topic_debt_activity,
    generate_drafts_activity,
    self_critique_activity,
    persona_check_activity,
    publish_post_activity,
    build_rationale_activity,
    write_breeth_episode_activity,
    self_audit_activity,
    record_and_increment_cycle_activity,
    prediction_sweep_activity,
]


def _init_sentry() -> None:
    """Initialize Sentry for the Temporal worker process (separate from FastAPI)."""
    init_sentry("temporal-worker")



async def run_worker() -> None:
    """Connect to Temporal and run worker polling the configured task queue."""
    settings = get_settings()

    # Initialize Sentry for the worker process
    _init_sentry()

    logger.info(
        f"Connecting Temporal worker to {settings.TEMPORAL_ADDRESS} (queue: {settings.TEMPORAL_TASK_QUEUE})",
        extra={
            "temporal_address": settings.TEMPORAL_ADDRESS,
            "temporal_namespace": settings.TEMPORAL_NAMESPACE,
            "task_queue": settings.TEMPORAL_TASK_QUEUE,
        },
    )

    client = await Client.connect(
        settings.TEMPORAL_ADDRESS,
        namespace=settings.TEMPORAL_NAMESPACE,
    )

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[AgentWorkflow],
        activities=ALL_ACTIVITIES,
    )

    logger.info(
        "Temporal worker listening for tasks...",
        extra={
            "workflow_count": 1,
            "activity_count": len(ALL_ACTIVITIES),
        },
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
