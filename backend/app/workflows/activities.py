"""Temporal Activity definitions wrapping core backend services for deterministic workflow orchestration.

Phase 21 — Error Handling and Retry Strategy:
  - Every Activity declares an explicit RetryPolicy via activity_options in the workflow.
  - Non-retryable exception types (auth errors, bad-request errors) are declared in
    non_retry_error_types so Temporal fails fast instead of consuming all retry attempts.
  - Discovery activities gracefully return an empty candidate set on total source failure
    rather than raising — the workflow detects the empty set and skips to the next cycle.
  - self_audit_activity catches SelfAuditError internally and returns a skipped result
    so constitution versioning is never a blocker for publishing.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import activity

from app.core.config import get_settings
from app.core.exceptions import SelfAuditError
from app.core.logging import get_logger, log_activity_failure
from app.db.session import AsyncSessionLocal, engine
from app.discovery.discovery_service import discover_candidate_topics
from app.drafting.draft_generator import generate_draft_angles
from app.drafting.persona_check import verify_persona_alignment
from app.drafting.self_critique import critique_and_select_winning_draft
from app.editorial.judge import judge_topic_score
from app.editorial.scorer import score_candidate_topic
from app.memory.episode_writer import record_decision_episode
from app.memory.recall import recall_memory_context
from app.models import Base
from app.models.agent import Agent
from app.models.constitution import Constitution
from app.models.persona import Persona
from app.models.post import Post
from app.models.topic_debt import TopicDebt
from app.publishing.publisher import publish_final_post
from app.publishing.rationale_builder import build_post_rationale
from app.self_audit.auditor import run_self_audit

logger = get_logger(__name__)


@asynccontextmanager
async def get_activity_db() -> AsyncGenerator[AsyncSession, None]:
    """Helper context manager ensuring tables exist when running in SQLite/test environments."""
    settings = get_settings()
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Activity: Discover candidate topics
# ---------------------------------------------------------------------------

@activity.defn
async def discover_topics_activity(agent_id: str) -> list[dict[str, Any]]:
    """Activity: Discover candidate topics for the agent's persona domain.

    Phase 21: On total source failure (all sources raise / return empty), returns an
    empty list. The workflow detects this and skips to the next scheduled cycle.
    Per-source failures are handled inside discover_candidate_topics via asyncio.gather
    with return_exceptions=True — individual source auth errors are logged but do not
    raise from this activity.
    """
    domain = "AI Security"
    try:
        async with get_activity_db() as db:
            agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()

            if agent:
                persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
                persona = persona_res.scalar_one_or_none()
                if persona:
                    domain = persona.domain

        topics = await discover_candidate_topics(domain)
        if not topics:
            logger.info(
                f"discover_topics_activity: no topics found for domain '{domain}'; returning empty set",
                extra={"agent_id": agent_id, "domain": domain},
            )
            topics = []
        return topics

    except Exception as exc:  # noqa: BLE001
        log_activity_failure(
            logger,
            activity="discover_topics_activity",
            error=exc,
            agent_id=agent_id,
            retryable=True,
        )
        # Return empty set so the workflow can skip gracefully instead of crashing.
        return []


# ---------------------------------------------------------------------------
# Activity: Recall memory context
# ---------------------------------------------------------------------------

@activity.defn
async def recall_memory_activity(agent_id: str, topic: dict[str, Any]) -> dict[str, Any]:
    """Activity: Recall associative memory context from Breeth.

    Phase 21: Breeth failures are caught — memory recall is non-blocking.
    An empty memory context is returned on failure so the pipeline continues.
    """
    try:
        return await recall_memory_context(topic)
    except Exception as exc:  # noqa: BLE001
        log_activity_failure(
            logger,
            activity="recall_memory_activity",
            error=exc,
            agent_id=agent_id,
            retryable=True,
        )
        return {}


# ---------------------------------------------------------------------------
# Activity: Memory behaviors
# ---------------------------------------------------------------------------

@activity.defn
async def run_memory_behaviors_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Execute memory behaviors (story continuity, prediction updates, concept gap detection)."""
    from app.memory.behaviors.concept_gap import detect_concept_gaps
    from app.memory.behaviors.prediction_update import check_prediction_resolution
    from app.memory.behaviors.story_continuity import check_story_continuity
    from app.memory.behaviors.topic_resurrection import evaluate_topic_resurrection

    behaviors: dict[str, Any] = {}

    # 1. Story continuity check
    try:
        story_cont = check_story_continuity(topic, memory_context)
        if story_cont:
            behaviors["story_continuation"] = story_cont
            topic["story_continuation"] = story_cont
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"story_continuity check failed; skipping: {exc}", extra={"agent_id": agent_id})

    # 2. Prediction update check
    try:
        pred_resolutions = check_prediction_resolution(memory_context)
        if pred_resolutions:
            behaviors["prediction_resolutions"] = pred_resolutions
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"prediction_resolution check failed; skipping: {exc}", extra={"agent_id": agent_id})

    # 3. Topic resurrection check
    try:
        async with get_activity_db() as db:
            agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()
            topic_debt_items = []
            if agent:
                debt_res = await db.execute(select(TopicDebt).where(TopicDebt.agent_id == agent.id))
                topic_debt_items = [
                    {
                        "id": d.id,
                        "title": d.topic_title,
                        "rejection_reason": d.rejection_reason,
                        "revisit_condition": d.revisit_condition,
                    }
                    for d in debt_res.scalars().all()
                ]

        resurrection = evaluate_topic_resurrection(topic, topic_debt_items)
        if resurrection:
            behaviors["resurrection"] = resurrection
            topic["resurrection"] = resurrection
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"topic_resurrection check failed; skipping: {exc}", extra={"agent_id": agent_id})

    # 4. Concept gap synthesis check
    try:
        concept_gaps = detect_concept_gaps(memory_context)
        if concept_gaps:
            behaviors["concept_gaps"] = concept_gaps
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"concept_gap check failed; skipping: {exc}", extra={"agent_id": agent_id})

    memory_context["behavior_results"] = behaviors
    memory_context["behaviors_evaluated"] = True
    return memory_context


# ---------------------------------------------------------------------------
# Activity: Editorial judge
# ---------------------------------------------------------------------------

@activity.defn
async def editorial_judge_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Score candidate topic and render ACCEPT/REJECT decision against constitution."""
    rules = {"accept_threshold": 60.0, "relevance_threshold": 60.0}
    try:
        async with get_activity_db() as db:
            agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()
            if agent:
                const_res = await db.execute(
                    select(Constitution).where(Constitution.agent_id == agent.id, Constitution.is_active.is_(True))
                )
                constitution = const_res.scalar_one_or_none()
                if constitution and isinstance(constitution.rules, dict):
                    rules = constitution.rules
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"editorial_judge_activity: constitution load failed; using defaults: {exc}")

    scores = await score_candidate_topic(topic, memory_context, rules)
    accept_threshold = float(rules.get("accept_threshold", 60.0))
    accepted, reason = judge_topic_score(scores, accept_threshold, topic_title=str(topic.get("title", "Unknown")))


    return {
        "accepted": accepted,
        "reason": reason,
        "scores": scores,
    }


# ---------------------------------------------------------------------------
# Activity: Log topic debt
# ---------------------------------------------------------------------------

@activity.defn
async def log_topic_debt_activity(
    agent_id: str, topic: dict[str, Any], judge_result: dict[str, Any]
) -> dict[str, Any]:
    """Activity: Persist rejected candidate topic into topic_debt database table."""
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()

        if agent:
            debt_item = TopicDebt(
                agent_id=agent.id,
                topic_title=str(topic.get("title", "Untitled Topic")),
                topic_summary=str(topic.get("summary", "")),
                score=float(judge_result.get("scores", {}).get("total_score", 0.0)),
                rejection_reason=str(judge_result.get("reason", "Below score threshold")),
                revisit_condition="Revisit when new evidence or sources arrive",
                status="open",
            )
            db.add(debt_item)
            await db.commit()

    return {"status": "logged", "title": topic.get("title")}


# ---------------------------------------------------------------------------
# Activity: Generate draft angles
# ---------------------------------------------------------------------------

@activity.defn
async def generate_drafts_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any]
) -> list[dict[str, Any]]:
    """Activity: Generate 3 candidate post draft angles."""
    persona_dict = {"name": "Ada", "domain": "AI Security"}
    try:
        async with get_activity_db() as db:
            agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()
            if agent:
                persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
                persona = persona_res.scalar_one_or_none()
                if persona:
                    persona_dict = {"name": persona.name, "domain": persona.domain, "voice_config": persona.voice_config}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"generate_drafts_activity: persona load failed; using defaults: {exc}")

    drafts = await generate_draft_angles(topic, persona_dict)
    if not drafts:
        title = topic.get("title", "Research Update")
        drafts = [
            {
                "angle_name": "Deep Dive Analysis",
                "post_text": f"In-depth analysis on {title}. Critical implications for security and architecture.",
                "sources": topic.get("sources", []),
            },
            {
                "angle_name": "Practical Security Impact",
                "post_text": f"Practical breakdown of {title}. Key takeaways for engineering teams.",
                "sources": topic.get("sources", []),
            },
        ]

    return drafts


# ---------------------------------------------------------------------------
# Activity: Self-critique and draft selection
# ---------------------------------------------------------------------------

@activity.defn
async def self_critique_activity(agent_id: str, drafts: list[dict[str, Any]]) -> dict[str, Any]:
    """Activity: Critique candidate drafts and select the winning post."""
    return await critique_and_select_winning_draft(drafts)


# ---------------------------------------------------------------------------
# Activity: Persona alignment check
# ---------------------------------------------------------------------------

@activity.defn
async def persona_check_activity(agent_id: str, winning_draft: dict[str, Any]) -> dict[str, Any]:
    """Activity: Verify winning draft alignment with persona voice."""
    persona_dict = {"name": "Ada", "domain": "AI Security"}
    try:
        async with get_activity_db() as db:
            agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
            agent = agent_res.scalar_one_or_none()
            if agent:
                persona_res = await db.execute(select(Persona).where(Persona.agent_id == agent.id))
                persona = persona_res.scalar_one_or_none()
                if persona:
                    persona_dict = {"name": persona.name, "domain": persona.domain}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"persona_check_activity: persona load failed; using defaults: {exc}")

    aligned, reason = await verify_persona_alignment(winning_draft, persona_dict)
    return {"aligned": aligned, "reason": reason}


# ---------------------------------------------------------------------------
# Activity: Publish final post
# ---------------------------------------------------------------------------

@activity.defn
async def publish_post_activity(
    agent_id: str, draft: dict[str, Any], topic: dict[str, Any], memory_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Activity: Persist final immutable Post row to database."""
    async with get_activity_db() as db:
        return await publish_final_post(
            agent_id=agent_id,
            draft=draft,
            topic=topic,
            memory_context=memory_context,
            db_session=db,
        )


# ---------------------------------------------------------------------------
# Activity: Build rationale
# ---------------------------------------------------------------------------

@activity.defn
async def build_rationale_activity(
    agent_id: str, topic: dict[str, Any], memory_context: dict[str, Any], draft: dict[str, Any]
) -> str:
    """Activity: Build selection rationale string."""
    return await build_post_rationale(topic, memory_context, draft)


# ---------------------------------------------------------------------------
# Activity: Write Breeth episode
# ---------------------------------------------------------------------------

@activity.defn
async def write_breeth_episode_activity(
    agent_id: str, topic: dict[str, Any], item: dict[str, Any], decision: str
) -> dict[str, Any]:
    """Activity: Persist decision episode to Breeth memory."""
    try:
        return await record_decision_episode(
            {"agent_id": agent_id, "topic": topic, "item": item, "decision": decision}
        )
    except Exception as exc:  # noqa: BLE001
        log_activity_failure(
            logger,
            activity="write_breeth_episode_activity",
            error=exc,
            agent_id=agent_id,
            retryable=True,
        )
        return {"status": "skipped", "reason": str(exc)}


# ---------------------------------------------------------------------------
# Activity: Self-audit (Phase 21 — fault-tolerant)
# ---------------------------------------------------------------------------

@activity.defn
async def self_audit_activity(agent_id: str) -> dict[str, Any]:
    """Activity: Execute periodic self-audit and constitution review.

    Phase 21: SelfAuditError is caught here so the Activity always returns a result dict.
    A failed audit sets audit_skipped=True — the workflow uses this to skip constitution
    versioning without failing or blocking the publish pipeline.
    """
    try:
        async with get_activity_db() as db:
            result = await run_self_audit(agent_id=agent_id, db_session=db)

        # If audit proposes rule updates and a version bump is warranted, apply it.
        if result.get("version_bump") and result.get("proposed_rule_updates"):
            try:
                from app.self_audit.constitution_versioning import bump_constitution_version

                new_version = await bump_constitution_version(
                    agent_id=agent_id,
                    new_rules=result["proposed_rule_updates"],
                )
                result["new_constitution_version"] = new_version
                logger.info(
                    f"Constitution bumped to {new_version} after self-audit for agent '{agent_id}'",
                    extra={"agent_id": agent_id, "new_version": new_version},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"Constitution version bump skipped after audit failure: {exc}",
                    extra={"agent_id": agent_id, "error": str(exc)},
                )
                result["new_constitution_version"] = "unchanged"

        result["audit_skipped"] = False
        return result

    except SelfAuditError as exc:
        logger.warning(
            f"self_audit_activity: SelfAuditError caught — skipping constitution versioning for this cycle: {exc}",
            extra={"agent_id": agent_id, "error": str(exc)},
        )
        return {
            "audit_passed": False,
            "audit_skipped": True,
            "proposed_rule_updates": [],
            "reject_rate": 0.0,
            "stale_rules": [],
            "version_bump": False,
            "skip_reason": str(exc),
        }

    except Exception as exc:  # noqa: BLE001
        log_activity_failure(
            logger,
            activity="self_audit_activity",
            error=exc,
            agent_id=agent_id,
            retryable=False,
        )
        return {
            "audit_passed": False,
            "audit_skipped": True,
            "proposed_rule_updates": [],
            "reject_rate": 0.0,
            "stale_rules": [],
            "version_bump": False,
            "skip_reason": str(exc),
        }


# ---------------------------------------------------------------------------
# Activity: Cycle counter
# ---------------------------------------------------------------------------

@activity.defn
async def record_and_increment_cycle_activity(agent_id: str) -> int:
    """Activity: Track and increment agent cycle_count in Postgres system of record."""
    async with get_activity_db() as db:
        agent_res = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_res.scalar_one_or_none()
        if agent is None:
            agent = Agent(agent_id=agent_id, status="active", cycle_count=1)
            db.add(agent)
        else:
            agent.cycle_count = (agent.cycle_count or 0) + 1
        await db.commit()
        await db.refresh(agent)
        return agent.cycle_count


# ---------------------------------------------------------------------------
# Activity: Prediction sweep (secondary scheduled check)
# ---------------------------------------------------------------------------

@activity.defn
async def prediction_sweep_activity(agent_id: str) -> list[dict[str, Any]]:
    """Activity: Secondary scheduled check — prediction-deadline sweep (Phase 16)."""
    from app.memory.behaviors.prediction_update import check_prediction_resolution
    from app.memory.recall import recall_memory_context

    try:
        dummy_topic = {"title": "Prediction Sweep", "summary": "Scanning predictions past deadline."}
        memory_ctx = await recall_memory_context(dummy_topic)
        expired_resolutions = check_prediction_resolution(memory_ctx)
        return expired_resolutions or []
    except Exception as exc:  # noqa: BLE001
        log_activity_failure(
            logger,
            activity="prediction_sweep_activity",
            error=exc,
            agent_id=agent_id,
            retryable=True,
        )
        return []
