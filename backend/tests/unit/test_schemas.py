"""Unit tests for Pydantic schemas in app/schemas."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.agent import InitRequest, PersonaIn
from app.schemas.feed import FeedResponse, PostOut
from app.schemas.memory import BreethEpisodeIn, BreethSearchRequest


class TestAgentSchemas:
    def test_valid_init_request_succeeds(self) -> None:
        req = InitRequest(persona=PersonaIn(name="Ada", domain="AI Security"))
        assert req.persona.name == "Ada"
        assert req.persona.domain == "AI Security"

    def test_persona_strips_whitespace(self) -> None:
        p = PersonaIn(name="  Ada  ", domain="  AI Security  ")
        assert p.name == "Ada"
        assert p.domain == "AI Security"

    def test_persona_rejects_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="", domain="AI Security")

    def test_persona_rejects_whitespace_only_domain(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="Ada", domain="   ")

    def test_persona_rejects_oversized_name(self) -> None:
        with pytest.raises(ValidationError):
            PersonaIn(name="A" * 256, domain="AI Security")


class TestFeedSchemas:
    def test_feed_response_serializes_iso_utc_with_z_suffix(self) -> None:
        dt = datetime(2026, 8, 8, 20, 30, 0, tzinfo=timezone.utc)
        post = PostOut(
            id="p1",
            createdAt=dt,
            text="Test post text",
            rationale="Test rationale",
            sources=["https://example.com"],
        )
        resp = FeedResponse(posts=[post])
        json_data = resp.model_dump_json()

        assert '"createdAt":"2026-08-08T20:30:00Z"' in json_data
        assert '"id":"p1"' in json_data

    def test_post_out_handles_naive_datetime(self) -> None:
        naive_dt = datetime(2026, 8, 8, 20, 30, 0)
        post = PostOut(
            id="p2",
            createdAt=naive_dt,
            text="Naive dt text",
            rationale="Rationale",
            sources=[],
        )
        dumped = post.model_dump(mode="json")
        assert dumped["createdAt"] == "2026-08-08T20:30:00Z"


class TestMemorySchemas:
    def test_breeth_search_request_validation(self) -> None:
        req = BreethSearchRequest(query="  AI security risks  ", limit=5, min_score=0.7)
        assert req.query == "AI security risks"
        assert req.limit == 5
        assert req.min_score == 0.7

    def test_breeth_search_request_rejects_out_of_bounds_score(self) -> None:
        with pytest.raises(ValidationError):
            BreethSearchRequest(query="valid query", min_score=1.5)

    def test_breeth_episode_in_defaults(self) -> None:
        ep = BreethEpisodeIn(topic="AI Vulnerabilities", claims=["Claim 1"])
        assert ep.topic == "AI Vulnerabilities"
        assert ep.stance == "neutral"
        assert ep.editorial_decision == "accepted"
