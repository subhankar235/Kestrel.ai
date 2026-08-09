"""Constitution versioning — applies rule changes and bumps constitution version.

Phase 21: fault-tolerant — any failure during constitution versioning is caught,
logged, and skipped for the current cycle without blocking publishing.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


async def bump_constitution_version(agent_id: str, new_rules: dict[str, Any]) -> str:
    """Create new active constitution version with updated rules.

    Queries the active constitution for the agent, deactivates it, and inserts a new
    version row with the updated rules. Returns the new version string.

    Falls back gracefully if DB writes fail — logs the error and returns the current
    version so the calling audit cycle can continue without blocking publishing.
    """
    try:
        return await _do_bump(agent_id=agent_id, new_rules=new_rules)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            f"Constitution version bump failed for agent '{agent_id}'; skipping for this cycle: {exc}",
            extra={"agent_id": agent_id, "error": str(exc)},
        )
        return "unchanged"  # Caller treats "unchanged" as a no-op


async def _do_bump(agent_id: str, new_rules: dict[str, Any]) -> str:
    """Internal implementation — queries DB and writes new constitution version."""
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.agent import Agent
    from app.models.constitution import Constitution

    async with AsyncSessionLocal() as db:
        # Find the agent
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()

        if agent is None:
            logger.warning(
                f"Constitution bump skipped: agent '{agent_id}' not found",
                extra={"agent_id": agent_id},
            )
            return "1.0"

        # Find the active constitution
        const_res = await db.execute(
            select(Constitution).where(
                Constitution.agent_id == agent.id,
                Constitution.is_active.is_(True),
            )
        )
        current = const_res.scalar_one_or_none()

        if current is None:
            logger.warning(
                f"Constitution bump skipped: no active constitution for agent '{agent_id}'",
                extra={"agent_id": agent_id},
            )
            return "1.0"

        # Parse and increment version
        try:
            parts = str(current.version).split(".")
            major = int(parts[0]) if parts else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            new_version = f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            new_version = "1.1"

        # Merge existing rules with proposed updates
        updated_rules = dict(current.rules or {})
        for proposed in new_rules if isinstance(new_rules, list) else []:
            rule_key = proposed.get("rule", "")
            action = proposed.get("action", "")
            if rule_key and action == "lower_by_5" and rule_key in updated_rules:
                updated_rules[rule_key] = max(0.0, float(updated_rules[rule_key]) - 5.0)

        # Deactivate current version
        current.is_active = False
        db.add(current)

        # Create new version
        new_const = Constitution(
            agent_id=agent.id,
            version=new_version,
            rules=updated_rules,
            is_active=True,
        )
        db.add(new_const)
        await db.commit()

        logger.info(
            f"Constitution bumped from {current.version} → {new_version} for agent '{agent_id}'",
            extra={
                "event": "constitution_version_bump",
                "agent_id": agent_id,
                "old_version": current.version,
                "new_version": new_version,
                "rules_updated": list(updated_rules.keys()),
            },
        )

        return new_version
