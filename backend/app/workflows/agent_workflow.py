"""Temporal AgentWorkflow definition orchestrating the 48-hour autonomous cycle.

Phase 21 — Error Handling and Retry Strategy:
  - Each activity category has its own RetryPolicy tuned to its SLA:
      * Discovery activities: 3 attempts, 2s initial, 2.0 coefficient.
        Non-retryable: DiscoveryAuthError, DiscoveryClientError
      * LLM activities: 3 attempts, 1s initial, 2.0 coefficient.
        Non-retryable: LLMAuthError, LLMClientError
      * Memory/Breeth activities: 3 attempts, 2s initial, 1.5 coefficient.
        Non-retryable: BreethAuthError, BreethClientError
      * DB/publish activities: 3 attempts, 1s initial, 2.0 coefficient.
        Non-retryable: (none — all DB errors are transient)
  - The discover_topics_activity is wrapped in a try/except inside the Workflow.
    If it fails after retries, the workflow returns {"status": "discovery_skipped"} and
    does NOT raise — ensuring the Temporal Schedule fires again normally next cycle.
  - self_audit_activity always returns a dict (never raises) — the workflow checks
    audit_skipped to decide whether to log a warning.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.core.config import get_settings
    from app.core.exceptions import (
        BreethAuthError,
        BreethClientError,
        DiscoveryAuthError,
        DiscoveryClientError,
        LLMAuthError,
        LLMClientError,
    )
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


def _make_retry_policy(
    max_attempts: int = 3,
    initial_interval_seconds: float = 1.0,
    backoff_coefficient: float = 2.0,
    non_retry_types: list[type] | None = None,
) -> RetryPolicy:
    """Build a RetryPolicy with optional list of non-retryable exception types."""
    return RetryPolicy(
        initial_interval=timedelta(seconds=initial_interval_seconds),
        backoff_coefficient=backoff_coefficient,
        maximum_attempts=max_attempts,
        non_retryable_error_types=[t.__name__ for t in (non_retry_types or [])],
    )


# ---------------------------------------------------------------------------
# Per-category RetryPolicy presets
# ---------------------------------------------------------------------------

_DISCOVERY_RETRY = _make_retry_policy(
    max_attempts=3,
    initial_interval_seconds=2.0,
    backoff_coefficient=2.0,
    non_retry_types=[DiscoveryAuthError, DiscoveryClientError],
)

_LLM_RETRY = _make_retry_policy(
    max_attempts=3,
    initial_interval_seconds=1.0,
    backoff_coefficient=2.0,
    non_retry_types=[LLMAuthError, LLMClientError],
)

_MEMORY_RETRY = _make_retry_policy(
    max_attempts=3,
    initial_interval_seconds=2.0,
    backoff_coefficient=1.5,
    non_retry_types=[BreethAuthError, BreethClientError],
)

_DB_RETRY = _make_retry_policy(
    max_attempts=3,
    initial_interval_seconds=1.0,
    backoff_coefficient=2.0,
)

_AUDIT_RETRY = _make_retry_policy(
    max_attempts=1,  # Self-audit is optional — one attempt only; failure → skip
    initial_interval_seconds=1.0,
    backoff_coefficient=1.0,
)


def _activity_options(
    retry_policy: RetryPolicy,
    start_to_close_seconds: int = 120,
) -> dict[str, Any]:
    return {
        "start_to_close_timeout": timedelta(seconds=start_to_close_seconds),
        "retry_policy": retry_policy,
    }


@workflow.defn
class AgentWorkflow:
    """Agent Workflow definition — single cycle execution with Phase 21 fault tolerance."""

    @workflow.run
    async def run(self, agent_id: str) -> dict[str, Any]:
        """Execute one autonomous publication cycle.

        Phase 21 fault-tolerance guarantees:
        1. If discovery fails completely after retries → log and return "discovery_skipped".
           The Temporal Schedule fires again normally next interval.
        2. Memory recall failure → empty context, pipeline continues.
        3. Self-audit failure → audit_skipped flag, constitution versioning skipped,
           publishing is NOT blocked.
        4. Breeth episode write failure → logged, pipeline returns normally.
        5. Non-retryable errors (auth) → Temporal fails activity immediately (no wasted retries).
        """

        # ── 0. Cycle counter ────────────────────────────────────────────────
        cycle_count = 1
        try:
            raw_cycle = await workflow.execute_activity(
                record_and_increment_cycle_activity,
                agent_id,
                **_activity_options(_DB_RETRY),
            )
            if isinstance(raw_cycle, int):
                cycle_count = raw_cycle
            elif isinstance(raw_cycle, dict) and "cycle_count" in raw_cycle:
                cycle_count = int(raw_cycle["cycle_count"])
        except Exception:  # noqa: BLE001
            cycle_count = 1

        # ── 0b. Prediction-deadline sweep ────────────────────────────────────
        swept_predictions: list[dict[str, Any]] = []
        try:
            raw_swept = await workflow.execute_activity(
                prediction_sweep_activity,
                agent_id,
                **_activity_options(_MEMORY_RETRY),
            )
            swept_predictions = raw_swept if isinstance(raw_swept, list) else []
        except Exception:  # noqa: BLE001
            swept_predictions = []

        # ── 1. Discover candidate topics ─────────────────────────────────────
        # Wrapped in try/except: if all sources fail after retries, the workflow
        # logs and returns "discovery_skipped" WITHOUT raising — the next scheduled
        # cycle fires normally via Temporal Schedule.
        topics: list[dict[str, Any]] = []
        try:
            topics = await workflow.execute_activity(
                discover_topics_activity,
                agent_id,
                **_activity_options(_DISCOVERY_RETRY, start_to_close_seconds=90),
            )
        except Exception:  # noqa: BLE001
            # Total discovery failure after retries — skip this cycle gracefully.
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
            memory_ctx = await workflow.execute_activity(
                recall_memory_activity,
                args=[agent_id, primary_topic],
                **_activity_options(_MEMORY_RETRY),
            )
        except Exception:  # noqa: BLE001
            memory_ctx = {}

        # ── 3. Memory behaviors ───────────────────────────────────────────────
        try:
            memory_ctx = await workflow.execute_activity(
                run_memory_behaviors_activity,
                args=[agent_id, primary_topic, memory_ctx],
                **_activity_options(_MEMORY_RETRY),
            )
        except Exception:  # noqa: BLE001
            pass  # Memory behaviors are additive — failure means empty behavior results

        # ── 4. Editorial judge decision ───────────────────────────────────────
        judge_res = await workflow.execute_activity(
            editorial_judge_activity,
            args=[agent_id, primary_topic, memory_ctx],
            **_activity_options(_LLM_RETRY),
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
                audit_result = await workflow.execute_activity(
                    self_audit_activity,
                    agent_id,
                    **_activity_options(_AUDIT_RETRY),
                )
                self_audit_executed = True
                self_audit_skipped = bool(audit_result.get("audit_skipped", False))
                if self_audit_skipped:
                    # Log but do NOT block — publishing proceeds regardless.
                    pass  # audit_result already logged inside the activity
            except Exception:  # noqa: BLE001
                self_audit_executed = False
                self_audit_skipped = True

        # ── REJECT BRANCH ─────────────────────────────────────────────────────
        if not judge_res.get("accepted", False):
            try:
                await workflow.execute_activity(
                    log_topic_debt_activity,
                    args=[agent_id, primary_topic, judge_res],
                    **_activity_options(_DB_RETRY),
                )
            except Exception:  # noqa: BLE001
                pass  # Topic debt logging failure is non-fatal

            try:
                await workflow.execute_activity(
                    write_breeth_episode_activity,
                    args=[agent_id, primary_topic, judge_res, "rejected"],
                    **_activity_options(_MEMORY_RETRY),
                )
            except Exception:  # noqa: BLE001
                pass  # Breeth write failure is non-fatal

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
        drafts = await workflow.execute_activity(
            generate_drafts_activity,
            args=[agent_id, primary_topic, memory_ctx],
            **_activity_options(_LLM_RETRY),
        )

        # 6. Self-critique & winning draft selection
        winning_draft = await workflow.execute_activity(
            self_critique_activity,
            args=[agent_id, drafts],
            **_activity_options(_LLM_RETRY),
        )

        # 7. Persona alignment check
        try:
            await workflow.execute_activity(
                persona_check_activity,
                args=[agent_id, winning_draft],
                **_activity_options(_LLM_RETRY),
            )
        except Exception:  # noqa: BLE001
            pass  # Persona check failure does not block publishing

        # 8. Publish final immutable post to database
        post_res = await workflow.execute_activity(
            publish_post_activity,
            args=[agent_id, winning_draft, primary_topic, memory_ctx],
            **_activity_options(_DB_RETRY),
        )

        # 9. Build transparency selection rationale
        try:
            await workflow.execute_activity(
                build_rationale_activity,
                args=[agent_id, primary_topic, memory_ctx, winning_draft],
                **_activity_options(_LLM_RETRY),
            )
        except Exception:  # noqa: BLE001
            pass  # Rationale build failure is non-fatal

        # 10. Persist episode to Breeth memory
        try:
            await workflow.execute_activity(
                write_breeth_episode_activity,
                args=[agent_id, primary_topic, winning_draft, "accepted"],
                **_activity_options(_MEMORY_RETRY),
            )
        except Exception:  # noqa: BLE001
            pass  # Breeth write failure is non-fatal

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
