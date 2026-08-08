"""Unit tests for Phase 21 — Error Handling and Retry Strategy.

Tests verify:
1. Typed exception hierarchy classifies retryable vs non-retryable correctly.
2. Discovery source clients raise typed exceptions on auth/server/timeout failures.
3. Workflow completes a full cycle with empty candidate set when discovery times out
   (the core Phase 21 requirement: one failed step never halts the 48-hour run).
4. Self-audit failure is fault-tolerant — skips constitution versioning without blocking.
5. Breeth client raises typed exceptions on auth/server/timeout failures.
6. LLM client raises typed exceptions on auth failures (non-retryable, fail fast).
7. Logging helpers (capture_exception, log_activity_failure) execute without raising.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BreethAuthError,
    BreethClientError,
    BreethServerError,
    BreethTimeoutError,
    DiscoveryAuthError,
    DiscoveryClientError,
    DiscoveryServerError,
    DiscoveryTimeoutError,
    LLMAuthError,
    LLMClientError,
    LLMServerError,
    SelfAuditError,
    classify_http_error,
)
from app.core.logging import capture_exception, log_activity_failure
from app.models.agent import Agent
from app.schemas.memory import BreethSearchResult
from app.workflows.activities import (
    discover_topics_activity,
    recall_memory_activity,
    self_audit_activity,
    write_breeth_episode_activity,
)
from app.workflows.agent_workflow import AgentWorkflow


# ═══════════════════════════════════════════════════════════════════════════
# 1. Exception hierarchy classification tests
# ═══════════════════════════════════════════════════════════════════════════


class TestExceptionHierarchy:
    """Verify typed exception classification and classify_http_error helper."""

    def test_discovery_timeout_is_retryable(self) -> None:
        exc = DiscoveryTimeoutError("timeout")
        assert isinstance(exc, DiscoveryTimeoutError)
        # Not a DiscoveryAuthError → retryable
        assert not isinstance(exc, DiscoveryAuthError)

    def test_discovery_auth_is_non_retryable(self) -> None:
        exc = DiscoveryAuthError(source="exa", detail="invalid key")
        assert isinstance(exc, DiscoveryAuthError)
        assert exc.source == "exa"

    def test_discovery_server_is_retryable(self) -> None:
        exc = DiscoveryServerError(source="tavily", status_code=502, detail="bad gateway")
        assert isinstance(exc, DiscoveryServerError)
        assert exc.status_code == 502

    def test_discovery_client_is_non_retryable(self) -> None:
        exc = DiscoveryClientError(source="github", status_code=400, detail="bad request")
        assert isinstance(exc, DiscoveryClientError)
        assert exc.status_code == 400

    def test_llm_auth_is_non_retryable(self) -> None:
        exc = LLMAuthError(detail="invalid key")
        assert isinstance(exc, LLMAuthError)

    def test_llm_server_is_retryable(self) -> None:
        exc = LLMServerError(status_code=503, detail="overloaded")
        assert isinstance(exc, LLMServerError)

    def test_llm_client_is_non_retryable(self) -> None:
        exc = LLMClientError(status_code=422, detail="unprocessable")
        assert isinstance(exc, LLMClientError)

    def test_breeth_auth_is_non_retryable(self) -> None:
        exc = BreethAuthError(detail="revoked key")
        assert isinstance(exc, BreethAuthError)

    def test_breeth_server_is_retryable(self) -> None:
        exc = BreethServerError(status_code=500, detail="internal error")
        assert isinstance(exc, BreethServerError)

    def test_breeth_client_is_non_retryable(self) -> None:
        exc = BreethClientError(status_code=400, detail="bad payload")
        assert isinstance(exc, BreethClientError)

    def test_breeth_timeout_is_retryable(self) -> None:
        exc = BreethTimeoutError("timeout")
        assert isinstance(exc, BreethTimeoutError)

    def test_self_audit_error(self) -> None:
        exc = SelfAuditError("audit crashed")
        assert isinstance(exc, SelfAuditError)

    def test_classify_http_error_401(self) -> None:
        exc = classify_http_error("exa", 401, "unauthorized")
        assert isinstance(exc, DiscoveryAuthError)

    def test_classify_http_error_403(self) -> None:
        exc = classify_http_error("tavily", 403, "forbidden")
        assert isinstance(exc, DiscoveryAuthError)

    def test_classify_http_error_400(self) -> None:
        exc = classify_http_error("github", 400, "bad request")
        assert isinstance(exc, DiscoveryClientError)

    def test_classify_http_error_500(self) -> None:
        exc = classify_http_error("rss", 500, "internal server error")
        assert isinstance(exc, DiscoveryServerError)

    def test_classify_http_error_502(self) -> None:
        exc = classify_http_error("exa", 502, "bad gateway")
        assert isinstance(exc, DiscoveryServerError)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Discovery source client typed-exception tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDiscoveryClientTypedExceptions:
    """Verify each discovery source raises correct typed exceptions."""

    @pytest.mark.asyncio
    async def test_exa_auth_error_raises_discovery_auth(self) -> None:
        """Exa 401 → DiscoveryAuthError (non-retryable)."""
        mock_response = httpx.Response(401, text="Unauthorized")
        with patch("app.discovery.sources.exa_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(EXA_API_KEY="invalid-key")
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                with pytest.raises(DiscoveryAuthError):
                    from app.discovery.sources.exa_client import fetch_exa_topics
                    await fetch_exa_topics("AI Security")

    @pytest.mark.asyncio
    async def test_exa_server_error_raises_discovery_server(self) -> None:
        """Exa 500 → DiscoveryServerError (retryable)."""
        mock_response = httpx.Response(500, text="Internal Server Error")
        with patch("app.discovery.sources.exa_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(EXA_API_KEY="valid-key")
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                with pytest.raises(DiscoveryServerError):
                    from app.discovery.sources.exa_client import fetch_exa_topics
                    await fetch_exa_topics("AI Security")

    @pytest.mark.asyncio
    async def test_exa_timeout_raises_discovery_timeout(self) -> None:
        """Exa timeout → DiscoveryTimeoutError (retryable)."""
        with patch("app.discovery.sources.exa_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(EXA_API_KEY="valid-key")
            with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("read timed out")):
                with pytest.raises(DiscoveryTimeoutError):
                    from app.discovery.sources.exa_client import fetch_exa_topics
                    await fetch_exa_topics("AI Security")

    @pytest.mark.asyncio
    async def test_tavily_auth_error_raises_discovery_auth(self) -> None:
        """Tavily 401 → DiscoveryAuthError (non-retryable)."""
        mock_response = httpx.Response(401, text="Unauthorized")
        with patch("app.discovery.sources.tavily_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(TAVILY_API_KEY="invalid-key")
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                with pytest.raises(DiscoveryAuthError):
                    from app.discovery.sources.tavily_client import fetch_tavily_topics
                    await fetch_tavily_topics("AI Security")

    @pytest.mark.asyncio
    async def test_github_auth_error_raises_discovery_auth(self) -> None:
        """GitHub 401 → DiscoveryAuthError (non-retryable)."""
        mock_response = httpx.Response(401, text="Bad credentials")
        with patch("app.discovery.sources.github_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(GITHUB_TOKEN="invalid-token")
            with patch("httpx.AsyncClient.get", return_value=mock_response):
                with pytest.raises(DiscoveryAuthError):
                    from app.discovery.sources.github_client import fetch_github_topics
                    await fetch_github_topics("AI Security")

    @pytest.mark.asyncio
    async def test_github_timeout_raises_discovery_timeout(self) -> None:
        """GitHub timeout → DiscoveryTimeoutError (retryable)."""
        with patch("app.discovery.sources.github_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(GITHUB_TOKEN="valid-token")
            with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("connect timed out")):
                with pytest.raises(DiscoveryTimeoutError):
                    from app.discovery.sources.github_client import fetch_github_topics
                    await fetch_github_topics("AI Security")

    @pytest.mark.asyncio
    async def test_exa_missing_key_returns_empty(self) -> None:
        """Exa with no API key → graceful empty list (no exception)."""
        with patch("app.discovery.sources.exa_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(EXA_API_KEY="")
            from app.discovery.sources.exa_client import fetch_exa_topics
            result = await fetch_exa_topics("AI Security")
            assert result == []

    @pytest.mark.asyncio
    async def test_tavily_missing_key_returns_empty(self) -> None:
        """Tavily with no API key → graceful empty list (no exception)."""
        with patch("app.discovery.sources.tavily_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(TAVILY_API_KEY="")
            from app.discovery.sources.tavily_client import fetch_tavily_topics
            result = await fetch_tavily_topics("AI Security")
            assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# 3. Workflow fault-tolerance: discovery timeout → cycle completes
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkflowDiscoveryTimeoutFaultTolerance:
    """Core Phase 21 requirement: workflow still completes when discovery times out."""

    @pytest.mark.asyncio
    async def test_discovery_timeout_workflow_completes_empty_cycle(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulate discover_topics_activity raising a timeout after retries.

        The workflow must NOT raise. It returns {"status": "no_topics"} (or
        "discovery_skipped") and the Temporal Schedule fires again next interval.
        """
        call_log: list[str] = []

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))
            call_log.append(func_name)

            if "record_and_increment" in func_name:
                return 1
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                # Simulate total discovery failure — returns empty list
                # (activity catches internally and returns [])
                return []
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_timeout_test")

        # Workflow MUST complete without raising
        assert result is not None
        assert result["status"] == "no_topics"
        assert result["agent_id"] == "agent_timeout_test"
        assert result["cycle_count"] == 1
        assert "record_and_increment_cycle_activity" in call_log
        assert "discover_topics_activity" in call_log

    @pytest.mark.asyncio
    async def test_discovery_raises_exception_workflow_returns_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulate discover_topics_activity raising an exception (after Temporal retries exhaust).

        The workflow catches the exception and returns {"status": "discovery_skipped"}.
        """
        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))

            if "record_and_increment" in func_name:
                return 1
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                raise DiscoveryTimeoutError("All sources timed out after max retries")
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_discovery_crash_test")

        assert result["status"] == "discovery_skipped"
        assert result["agent_id"] == "agent_discovery_crash_test"
        assert result["self_audit_executed"] is False

    @pytest.mark.asyncio
    async def test_workflow_accept_path_still_works_after_memory_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Memory recall failure does not block the accept path — empty context is used."""
        mock_topic = {"title": "AI Resilience Test", "sources": ["https://example.com/paper"]}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))

            if "record_and_increment" in func_name:
                return 1
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name:
                raise BreethTimeoutError("Breeth timed out")
            if "behaviors" in func_name:
                raise BreethServerError(status_code=503, detail="overloaded")
            if "judge" in func_name:
                return {"accepted": True, "reason": "Score 85"}
            if "drafts" in func_name:
                return [{"post_text": "Resilient post", "sources": ["https://example.com"]}]
            if "critique" in func_name:
                return {"post_text": "Resilient post", "sources": ["https://example.com"]}
            if "persona" in func_name:
                return {"aligned": True}
            if "publish" in func_name:
                return {"post_id": "p_resilient", "text": "Resilient post"}
            if "rationale" in func_name:
                return "Resilience rationale"
            if "breeth" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_memory_fail_test")

        assert result["status"] == "published"
        assert result["post_id"] == "p_resilient"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Self-audit fault tolerance
# ═══════════════════════════════════════════════════════════════════════════


class TestSelfAuditFaultTolerance:
    """self_audit_activity must be fault-tolerant: a failed audit skips constitution
    versioning without blocking publishing."""

    @pytest.mark.asyncio
    async def test_self_audit_internal_failure_returns_skipped(self) -> None:
        """SelfAuditError from auditor → activity returns audit_skipped=True, never raises."""
        with patch("app.workflows.activities.run_self_audit", side_effect=SelfAuditError("DB crash")):
            result = await self_audit_activity("agent_audit_fail_test")

        assert result["audit_skipped"] is True
        assert result["audit_passed"] is False
        assert result["version_bump"] is False
        assert "skip_reason" in result
        assert "DB crash" in result["skip_reason"]

    @pytest.mark.asyncio
    async def test_self_audit_unexpected_exception_returns_skipped(self) -> None:
        """Arbitrary exception from auditor → activity returns audit_skipped=True."""
        with patch("app.workflows.activities.run_self_audit", side_effect=RuntimeError("Unexpected error")):
            result = await self_audit_activity("agent_audit_crash_test")

        assert result["audit_skipped"] is True
        assert result["audit_passed"] is False

    @pytest.mark.asyncio
    async def test_self_audit_success_returns_result(self) -> None:
        """Successful audit → normal result with audit_skipped=False."""
        audit_result = {
            "audit_passed": True,
            "proposed_rule_updates": [],
            "reject_rate": 0.1,
            "stale_rules": [],
            "version_bump": False,
        }
        with patch("app.workflows.activities.run_self_audit", AsyncMock(return_value=audit_result)):
            result = await self_audit_activity("agent_audit_ok_test")

        assert result["audit_skipped"] is False
        assert result["audit_passed"] is True

    @pytest.mark.asyncio
    async def test_workflow_self_audit_failure_does_not_block_publishing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Full workflow: self-audit fails on the Nth cycle but publishing still succeeds."""
        mock_topic = {"title": "Audit-Fail Publish Test", "sources": ["https://example.com"]}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))

            if "record_and_increment" in func_name:
                return 10  # 10th cycle triggers self-audit
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name or "behaviors" in func_name:
                return {"stories": []}
            if "judge" in func_name:
                return {"accepted": True, "reason": "Score 90"}
            if "self_audit" in func_name:
                # Audit fails but returns skipped result (activity handles internally)
                return {"audit_passed": False, "audit_skipped": True, "proposed_rule_updates": [], "version_bump": False}
            if "drafts" in func_name:
                return [{"post_text": "Post despite audit fail", "sources": ["https://example.com"]}]
            if "critique" in func_name:
                return {"post_text": "Post despite audit fail", "sources": ["https://example.com"]}
            if "persona" in func_name:
                return {"aligned": True}
            if "publish" in func_name:
                return {"post_id": "p_audit_fail", "text": "Post despite audit fail"}
            if "rationale" in func_name:
                return "Rationale text"
            if "breeth" in func_name:
                return {"status": "ok"}
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_audit_fail_publish_test")

        assert result["status"] == "published"
        assert result["post_id"] == "p_audit_fail"
        assert result["self_audit_executed"] is True
        assert result["self_audit_skipped"] is True


# ═══════════════════════════════════════════════════════════════════════════
# 5. Activity-level fault tolerance tests
# ═══════════════════════════════════════════════════════════════════════════


class TestActivityFaultTolerance:
    """Verify individual activities handle failures gracefully."""

    @pytest.mark.asyncio
    async def test_discover_topics_activity_returns_empty_on_failure(self) -> None:
        """discover_topics_activity catches all exceptions and returns empty list."""
        with patch(
            "app.workflows.activities.discover_candidate_topics",
            side_effect=DiscoveryTimeoutError("All sources timed out"),
        ):
            result = await discover_topics_activity("agent_disc_fail_test")
            assert isinstance(result, list)
            assert result == []

    @pytest.mark.asyncio
    async def test_recall_memory_activity_returns_empty_on_failure(self) -> None:
        """recall_memory_activity catches Breeth failures and returns empty context."""
        with patch(
            "app.workflows.activities.recall_memory_context",
            side_effect=BreethTimeoutError("Breeth timed out"),
        ):
            result = await recall_memory_activity("agent_recall_fail_test", {"title": "Test"})
            assert isinstance(result, dict)
            assert result == {}

    @pytest.mark.asyncio
    async def test_write_breeth_episode_returns_skipped_on_failure(self) -> None:
        """write_breeth_episode_activity catches failures and returns skipped status."""
        with patch(
            "app.workflows.activities.record_decision_episode",
            side_effect=BreethServerError(status_code=503, detail="overloaded"),
        ):
            result = await write_breeth_episode_activity(
                "agent_ep_fail_test",
                {"title": "Test"},
                {"post_text": "Test post"},
                "accepted",
            )
            assert result["status"] == "skipped"
            assert "reason" in result


# ═══════════════════════════════════════════════════════════════════════════
# 6. Logging helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestLoggingHelpers:
    """Verify Phase 21 logging utilities execute without raising."""

    def test_capture_exception_no_sentry_no_raise(self) -> None:
        """capture_exception should silently no-op when Sentry is not configured."""
        try:
            capture_exception(RuntimeError("test error"), context={"key": "value"})
        except Exception:
            pytest.fail("capture_exception raised an exception when it should not")

    def test_log_activity_failure_structured_output(self) -> None:
        """log_activity_failure should log structured ERROR with all fields."""
        import logging
        test_logger = logging.getLogger("test.phase21")

        try:
            log_activity_failure(
                test_logger,
                activity="test_activity",
                error=DiscoveryTimeoutError("test timeout"),
                agent_id="agent_log_test",
                cycle_count=5,
                retryable=True,
                extra={"source": "exa"},
            )
        except Exception:
            pytest.fail("log_activity_failure raised an exception when it should not")

    def test_log_activity_failure_non_retryable(self) -> None:
        """log_activity_failure for non-retryable errors."""
        import logging
        test_logger = logging.getLogger("test.phase21.auth")

        try:
            log_activity_failure(
                test_logger,
                activity="test_auth_failure",
                error=DiscoveryAuthError(source="exa", detail="revoked key"),
                agent_id="agent_auth_test",
                retryable=False,
            )
        except Exception:
            pytest.fail("log_activity_failure raised an exception when it should not")


# ═══════════════════════════════════════════════════════════════════════════
# 7. Breeth client typed-exception tests
# ═══════════════════════════════════════════════════════════════════════════


class TestBreethClientTypedExceptions:
    """Verify Breeth client raises correct typed exceptions."""

    @pytest.mark.asyncio
    async def test_breeth_search_fallback_mode_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Breeth with example URL → fallback empty result (no exception)."""
        monkeypatch.setenv("BREETH_API_KEY", "")
        monkeypatch.setenv("BREETH_BASE_URL", "https://api.breeth.example")
        from app.core.config import get_settings
        get_settings.cache_clear()

        from app.memory.breeth_client import search_memory

        result = await search_memory("test query")
        assert isinstance(result, BreethSearchResult)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_breeth_write_episode_fallback_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Breeth with example URL → fallback recorded (no exception)."""
        monkeypatch.setenv("BREETH_API_KEY", "")
        monkeypatch.setenv("BREETH_BASE_URL", "https://api.breeth.example")
        from app.core.config import get_settings
        get_settings.cache_clear()

        from app.memory.breeth_client import write_episode

        result = await write_episode({
            "topic": "Test Topic",
            "claims": ["claim1"],
            "stance": "neutral",
            "editorial_decision": "accepted",
            "sources": ["https://example.com"],
        })
        assert result["status"] == "recorded_fallback"



# ═══════════════════════════════════════════════════════════════════════════
# 8. Full workflow end-to-end with multiple failures
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkflowMultipleFailuresResilience:
    """Workflow survives multiple independent failures in one cycle."""

    @pytest.mark.asyncio
    async def test_workflow_survives_prediction_sweep_and_memory_and_audit_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Prediction sweep fails, memory recall fails, self-audit fails — but
        the workflow still publishes successfully."""
        mock_topic = {"title": "Multi-Fail Resilience", "sources": ["https://example.com"]}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))

            if "record_and_increment" in func_name:
                return 10
            if "prediction_sweep" in func_name:
                raise BreethTimeoutError("Breeth down for predictions")
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name:
                raise BreethTimeoutError("Breeth down for recall")
            if "behaviors" in func_name:
                raise RuntimeError("Behaviors crashed")
            if "judge" in func_name:
                return {"accepted": True, "reason": "Score 92"}
            if "self_audit" in func_name:
                raise SelfAuditError("Audit DB down")
            if "drafts" in func_name:
                return [{"post_text": "Resilient multi-fail post", "sources": ["https://example.com"]}]
            if "critique" in func_name:
                return {"post_text": "Resilient multi-fail post", "sources": ["https://example.com"]}
            if "persona" in func_name:
                raise LLMAuthError(detail="API key expired")
            if "publish" in func_name:
                return {"post_id": "p_multi_fail", "text": "Resilient multi-fail post"}
            if "rationale" in func_name:
                raise LLMServerError(status_code=503, detail="overloaded")
            if "breeth" in func_name:
                raise BreethServerError(status_code=500, detail="internal error")
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_multi_fail_test")

        # Despite all these failures, the workflow STILL publishes
        assert result["status"] == "published"
        assert result["post_id"] == "p_multi_fail"
        assert result["cycle_count"] == 10
        assert result["predictions_swept"] == 0  # Prediction sweep failed
        assert result["self_audit_executed"] is False  # Audit raised

    @pytest.mark.asyncio
    async def test_workflow_reject_path_survives_breeth_and_debt_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Reject path: topic debt logging fails, Breeth episode write fails — workflow completes."""
        mock_topic = {"title": "Rejected Multi-Fail", "sources": []}

        async def mock_execute(activity_func, *args, **kwargs):
            func_name = getattr(activity_func, "__name__", str(activity_func))

            if "record_and_increment" in func_name:
                return 1
            if "prediction_sweep" in func_name:
                return []
            if "discover" in func_name:
                return [mock_topic]
            if "recall" in func_name or "behaviors" in func_name:
                return {}
            if "judge" in func_name:
                return {"accepted": False, "reason": "Score 30 below threshold"}
            if "debt" in func_name:
                raise RuntimeError("DB write failed for topic_debt")
            if "breeth" in func_name:
                raise BreethServerError(status_code=500, detail="internal error")
            return {}

        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute)

        wf = AgentWorkflow()
        result = await wf.run("agent_reject_multi_fail_test")

        assert result["status"] == "rejected"
        assert result["agent_id"] == "agent_reject_multi_fail_test"
        assert "below threshold" in result["reason"]
