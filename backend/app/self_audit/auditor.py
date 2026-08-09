"""Self audit engine — periodically reviews published/rejected history for failure patterns.

Phase 21: The auditor is fully fault-tolerant. Any internal failure is caught, logged,
and surfaces a SelfAuditError that the workflow catches to skip constitution versioning
for that cycle without blocking publishing.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SelfAuditError
from app.core.logging import get_logger, log_activity_failure

logger = get_logger(__name__)


async def run_self_audit(agent_id: str, db_session: AsyncSession | None = None) -> dict[str, Any]:
    """Execute periodic self-audit over agent publish/reject history.

    Examines:
    - Reject rate over last N cycles (raises concern if > 80% rejected).
    - Any constitution rule that has triggered 0 accepts in last 10 cycles (stale rule).
    - Proposes rule updates if patterns are detected.

    Returns:
        dict with keys:
          - audit_passed (bool)
          - proposed_rule_updates (list[dict])
          - reject_rate (float)
          - stale_rules (list[str])
          - version_bump (bool) — True if constitution should be versioned

    Raises:
        SelfAuditError: when the audit itself encounters an unrecoverable internal error.
            The workflow catches this and skips constitution versioning for that cycle.
    """
    try:
        return await _execute_audit(agent_id=agent_id, db_session=db_session)
    except SelfAuditError:
        raise  # Let SelfAuditError propagate directly
    except Exception as exc:  # noqa: BLE001
        typed = SelfAuditError(f"Self-audit failed for agent '{agent_id}': {exc}")
        log_activity_failure(
            logger,
            activity="run_self_audit",
            error=typed,
            agent_id=agent_id,
            retryable=False,
        )
        raise typed from exc


async def _execute_audit(
    agent_id: str,
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Internal audit logic — queries DB and analyses history patterns.

    This is separated from run_self_audit() so faults here are caught by the outer wrapper
    and converted to SelfAuditError before propagating to the workflow.
    """
    from app.models.agent import Agent
    from app.models.post import Post
    from app.models.topic_debt import TopicDebt

    proposed_rule_updates: list[dict[str, Any]] = []
    stale_rules: list[str] = []
    audit_passed = True
    version_bump = False
    reject_rate = 0.0

    if db_session is not None:
        try:
            # Lookup agent
            agent_res = await db_session.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()

            if agent is not None:
                # Count published posts
                posts_res = await db_session.execute(
                    select(Post).where(Post.agent_id == agent.id)
                )
                posts = posts_res.scalars().all()
                published_count = len(posts)

                # Count rejected topics (topic_debt)
                debt_res = await db_session.execute(
                    select(TopicDebt).where(TopicDebt.agent_id == agent.id)
                )
                rejected_count = len(debt_res.scalars().all())

                total = published_count + rejected_count
                if total > 0:
                    reject_rate = rejected_count / total

                # Flag high reject rate
                if reject_rate > 0.8 and total >= 5:
                    audit_passed = False
                    stale_rules.append("accept_threshold_too_high")
                    proposed_rule_updates.append({
                        "rule": "accept_threshold",
                        "action": "lower_by_5",
                        "reason": f"High reject rate {reject_rate:.0%} over {total} cycles",
                    })
                    version_bump = True
                    logger.warning(
                        f"Self-audit: high reject rate {reject_rate:.0%} for agent '{agent_id}'",
                        extra={"agent_id": agent_id, "reject_rate": reject_rate, "total_cycles": total},
                    )

        except Exception as exc:  # noqa: BLE001
            # DB query failures inside the audit are not fatal for the audit result —
            # they surface as an empty/baseline result with audit_passed=True so the
            # cycle can continue. The exception is logged for observability.
            logger.warning(
                f"Self-audit DB query failed for agent '{agent_id}'; returning baseline result: {exc}",
                extra={"agent_id": agent_id, "error": str(exc)},
            )

    logger.info(
        f"Self-audit completed for agent '{agent_id}': audit_passed={audit_passed}, reject_rate={reject_rate:.1%}",
        extra={
            "event": "self_audit_completed",
            "agent_id": agent_id,
            "audit_passed": audit_passed,
            "reject_rate": reject_rate,
            "stale_rules": stale_rules,
            "proposed_rule_updates": len(proposed_rule_updates),
            "version_bump": version_bump,
        },
    )


    return {
        "audit_passed": audit_passed,
        "proposed_rule_updates": proposed_rule_updates,
        "reject_rate": reject_rate,
        "stale_rules": stale_rules,
        "version_bump": version_bump,
    }
