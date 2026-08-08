"""Temporal AgentWorkflow definition orchestrating the 48-hour autonomous cycle."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        build_rationale_activity,
        discover_topics_activity,
        editorial_judge_activity,
        generate_drafts_activity,
        log_topic_debt_activity,
        persona_check_activity,
        publish_post_activity,
        recall_memory_activity,
        run_memory_behaviors_activity,
        self_audit_activity,
        self_critique_activity,
        write_breeth_episode_activity,
    )


@workflow.defn
class AgentWorkflow:
    """Agent Workflow definition — single cycle execution (discover -> recall -> judge -> publish/reject)."""

    @workflow.run
    async def run(self, agent_id: str) -> dict[str, Any]:
        """Execute one autonomous publication cycle."""
        activity_options = {
            "start_to_close_timeout": timedelta(seconds=60),
            "retry_policy": RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        }

        # 1. Discover candidate topics
        topics = await workflow.execute_activity(
            discover_topics_activity,
            agent_id,
            **activity_options,
        )

        if not topics:
            return {"status": "no_topics", "agent_id": agent_id}

        # Evaluate candidate topic
        primary_topic = topics[0]

        # 2. Recall associative memory context
        memory_ctx = await workflow.execute_activity(
            recall_memory_activity,
            args=[agent_id, primary_topic],
            **activity_options,
        )

        # 3. Execute memory behaviors
        memory_ctx = await workflow.execute_activity(
            run_memory_behaviors_activity,
            args=[agent_id, primary_topic, memory_ctx],
            **activity_options,
        )

        # 4. Editorial judge decision
        judge_res = await workflow.execute_activity(
            editorial_judge_activity,
            args=[agent_id, primary_topic, memory_ctx],
            **activity_options,
        )

        # REJECT BRANCH
        if not judge_res.get("accepted", False):
            await workflow.execute_activity(
                log_topic_debt_activity,
                args=[agent_id, primary_topic, judge_res],
                **activity_options,
            )
            await workflow.execute_activity(
                write_breeth_episode_activity,
                args=[agent_id, primary_topic, judge_res, "rejected"],
                **activity_options,
            )
            return {
                "status": "rejected",
                "agent_id": agent_id,
                "topic": primary_topic.get("title"),
                "reason": judge_res.get("reason"),
            }

        # ACCEPT BRANCH
        # 5. Generate draft angles
        drafts = await workflow.execute_activity(
            generate_drafts_activity,
            args=[agent_id, primary_topic, memory_ctx],
            **activity_options,
        )

        # 6. Self critique & winning draft selection
        winning_draft = await workflow.execute_activity(
            self_critique_activity,
            args=[agent_id, drafts],
            **activity_options,
        )

        # 7. Persona alignment check
        await workflow.execute_activity(
            persona_check_activity,
            args=[agent_id, winning_draft],
            **activity_options,
        )

        # 8. Publish final immutable post to database
        post_res = await workflow.execute_activity(
            publish_post_activity,
            args=[agent_id, winning_draft, primary_topic],
            **activity_options,
        )

        # 9. Build transparency selection rationale
        await workflow.execute_activity(
            build_rationale_activity,
            args=[agent_id, primary_topic, memory_ctx, winning_draft],
            **activity_options,
        )

        # 10. Persist episode to Breeth memory
        await workflow.execute_activity(
            write_breeth_episode_activity,
            args=[agent_id, primary_topic, winning_draft, "accepted"],
            **activity_options,
        )

        return {
            "status": "published",
            "agent_id": agent_id,
            "post_id": post_res.get("post_id"),
            "text": post_res.get("text"),
        }
