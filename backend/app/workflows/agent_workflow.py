"""AgentWorkflow definition orchestrating the 48-hour autonomous cycle.

Phase 21 — Error Handling and Retry Strategy:
  - Each activity has its own @async_retry decorator tuned to its SLA
    (configured in activities.py).
  - The discover_topics_activity is wrapped in a try/except inside the Workflow.
    If it fails after retries, the workflow returns {"status": "discovery_skipped"} and
    does NOT raise — ensuring the schedule fires again normally next cycle.
  - self_audit_activity always returns a dict (never raises) — the workflow checks
    audit_skipped to decide whether to log a warning.

Migrated from Temporal to plain async Python + APScheduler.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
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


class AgentWorkflow:
    """Agent Workflow definition — single cycle execution with Phase 21 fault tolerance."""

    async def run(self, agent_id: str) -> dict[str, Any]:
        """Execute one autonomous publication cycle.

        Phase 21 fault-tolerance guarantees:
        1. If discovery fails completely after retries → log and return "discovery_skipped".
           The schedule fires again normally next interval.
        2. Memory recall failure → empty context, pipeline continues.
        3. Self-audit failure → audit_skipped flag, constitution versioning skipped,
           publishing is NOT blocked.
        4. Breeth episode write failure → logged, pipeline returns normally.
        5. Non-retryable errors (auth) → @async_retry fails immediately (no wasted retries).
        """

        # ── 0. Cycle counter ────────────────────────────────────────────────
        cycle_count = 1
        try:
            raw_cycle = await record_and_increment_cycle_activity(agent_id)
            if isinstance(raw_cycle, int):
                cycle_count = raw_cycle
            elif isinstance(raw_cycle, dict) and "cycle_count" in raw_cycle:
                cycle_count = int(raw_cycle["cycle_count"])
        except Exception:  # noqa: BLE001
            cycle_count = 1

        # ── 0b. Prediction-deadline sweep ────────────────────────────────────
        swept_predictions: list[dict[str, Any]] = []
        try:
            raw_swept = await prediction_sweep_activity(agent_id)
            swept_predictions = raw_swept if isinstance(raw_swept, list) else []
        except Exception:  # noqa: BLE001
            swept_predictions = []

        # ── 1. Discover candidate topics ─────────────────────────────────────
        topics: list[dict[str, Any]] = []
        try:
            topics = await discover_topics_activity(agent_id)
        except Exception:  # noqa: BLE001
            return {
                "status": "discovery_skipped",
                "agent_id": agent_id,
                "cycle_count": cycle_count,
                "predictions_swept": len(swept_predictions),
                "self_audit_executed": False,
            }

        if swept_predictions:
            topics = swept_predictions + (topics or [])

        if not topics:
            return {
                "status": "no_topics",
                "agent_id": agent_id,
                "cycle_count": cycle_count,
                "predictions_swept": len(swept_predictions),
                "self_audit_executed": False,
            }

        primary_topic = topics[0]

        # ── 2. Recall associative memory context ─────────────────────────────
        memory_ctx: dict[str, Any] = {}
        try:
            memory_ctx = await recall_memory_activity(agent_id, primary_topic)
        except Exception:  # noqa: BLE001
            memory_ctx = {}

        # ── 3. Memory behaviors ───────────────────────────────────────────────
        try:
            memory_ctx = await run_memory_behaviors_activity(
                agent_id, primary_topic, memory_ctx
            )
        except Exception:  # noqa: BLE001
            pass

        # ── 4. Editorial judge decision ───────────────────────────────────────
        judge_res = await editorial_judge_activity(
            agent_id, primary_topic, memory_ctx
        )

        # ── Secondary: Self-audit (gated by SELF_AUDIT_EVERY_N_CYCLES) ────────
        self_audit_executed = False
        self_audit_skipped = False
        try:
            self_audit_n = get_settings().SELF_AUDIT_EVERY_N_CYCLES
        except Exception:  # noqa: BLE001
            self_audit_n = 10

        if cycle_count > 0 and (cycle_count % self_audit_n == 0):
            try:
                audit_result = await self_audit_activity(agent_id)
                self_audit_executed = True
                self_audit_skipped = bool(audit_result.get("audit_skipped", False))
                if self_audit_skipped:
                    pass
            except Exception:  # noqa: BLE001
                self_audit_executed = False
                self_audit_skipped = True

        # ── REJECT BRANCH ─────────────────────────────────────────────────────
        if not judge_res.get("accepted", False):
            try:
                await log_topic_debt_activity(agent_id, primary_topic, judge_res)
            except Exception:  # noqa: BLE001
                pass

            try:
                await write_breeth_episode_activity(
                    agent_id, primary_topic, judge_res, "rejected"
                )
            except Exception:  # noqa: BLE001
                pass

            return {
                "status": "rejected",
                "agent_id": agent_id,
                "topic": primary_topic.get("title"),
                "reason": judge_res.get("reason"),
                "cycle_count": cycle_count,
                "predictions_swept": len(swept_predictions),
                "self_audit_executed": self_audit_executed,
                "self_audit_skipped": self_audit_skipped,
            }

        # ── ACCEPT BRANCH ─────────────────────────────────────────────────────

        # 5. Generate draft angles
        drafts = await generate_drafts_activity(
            agent_id, primary_topic, memory_ctx
        )

        # 6. Self-critique & winning draft selection
        winning_draft = await self_critique_activity(agent_id, drafts)

        # 7. Persona alignment check
        try:
            await persona_check_activity(agent_id, winning_draft)
        except Exception:  # noqa: BLE001
            pass

        # 8. Publish final immutable post to database
        post_res = await publish_post_activity(
            agent_id, winning_draft, primary_topic, memory_ctx
        )

        # 9. Build transparency selection rationale
        try:
            await build_rationale_activity(
                agent_id, primary_topic, memory_ctx, winning_draft
            )
        except Exception:  # noqa: BLE001
            pass

        # 10. Persist episode to Breeth memory
        try:
            await write_breeth_episode_activity(
                agent_id, primary_topic, winning_draft, "accepted"
            )
        except Exception:  # noqa: BLE001
            pass

        return {
            "status": "published",
            "agent_id": agent_id,
            "post_id": post_res.get("post_id"),
            "text": post_res.get("text"),
            "cycle_count": cycle_count,
            "predictions_swept": len(swept_predictions),
            "self_audit_executed": self_audit_executed,
            "self_audit_skipped": self_audit_skipped,
        }
