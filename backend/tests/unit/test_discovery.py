"""Unit tests for discovery sources (Exa, Tavily, RSS, GitHub), normalizer, and discovery service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import Response

from app.core.config import get_settings
from app.discovery.discovery_service import _deduplicate_raw_items, discover_candidate_topics
from app.discovery.normalizer import normalize_raw_content
from app.discovery.sources.exa_client import fetch_exa_topics
from app.discovery.sources.github_client import fetch_github_topics
from app.discovery.sources.rss_client import fetch_rss_topics
from app.discovery.sources.tavily_client import fetch_tavily_topics


class TestDiscoverySources:
    @pytest.mark.asyncio
    async def test_exa_client_missing_key_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert Exa client returns empty list when API key is missing."""
        monkeypatch.setenv("EXA_API_KEY", "")
        get_settings.cache_clear()
        results = await fetch_exa_topics("AI Security")
        assert results == []


    @pytest.mark.asyncio
    async def test_exa_client_mock_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert Exa client parses response items correctly."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"title": "Exa Paper", "url": "https://exa.ai/p1", "text": "Paper abstract content"}
            ]
        }
        monkeypatch.setattr("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp))
        monkeypatch.setenv("EXA_API_KEY", "test-exa-key")
        get_settings.cache_clear()

        results = await fetch_exa_topics("AI Security")
        assert len(results) == 1
        assert results[0]["title"] == "Exa Paper"
        assert results[0]["source"] == "exa"

    @pytest.mark.asyncio
    async def test_tavily_client_mock_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert Tavily client parses search results correctly."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"title": "Tavily News", "url": "https://tavily.com/n1", "content": "Tavily news snippet"}
            ]
        }
        monkeypatch.setattr("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp))
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        get_settings.cache_clear()

        results = await fetch_tavily_topics("LLM Security")
        assert len(results) == 1
        assert results[0]["title"] == "Tavily News"
        assert results[0]["source"] == "tavily"

    @pytest.mark.asyncio
    async def test_github_client_mock_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert GitHub client parses search response correctly."""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"full_name": "owner/repo", "html_url": "https://github.com/owner/repo", "description": "LLM security scanner"}
            ]
        }
        monkeypatch.setattr("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp))

        results = await fetch_github_topics("security")
        assert len(results) == 1
        assert "owner/repo" in results[0]["title"]
        assert results[0]["source"] == "github"

    @pytest.mark.asyncio
    async def test_rss_client_mock_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assert RSS client fetches and parses feed XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
            <title>Security Feed</title>
            <item>
                <title>Zero-Day Alert</title>
                <link>https://rss.com/alert1</link>
                <description>Advisory snippet</description>
            </item>
        </channel>
        </rss>"""
        mock_resp = MagicMock(spec=Response)
        mock_resp.status_code = 200
        mock_resp.text = xml_content
        monkeypatch.setattr("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp))

        results = await fetch_rss_topics(["https://rss.com/feed.xml"])
        assert len(results) == 1
        assert results[0]["title"] == "Zero-Day Alert"
        assert results[0]["source"] == "rss"


class TestDiscoveryDeduplicationAndNormalization:
    def test_deduplicate_raw_items(self) -> None:
        items = [
            {"title": "AI Vulnerability", "url": "https://example.com/1"},
            {"title": "ai vulnerability", "url": "https://example.com/1"},  # duplicate
            {"title": "Distinct Topic", "url": "https://example.com/2"},
        ]
        deduped = _deduplicate_raw_items(items)
        assert len(deduped) == 2

    @pytest.mark.asyncio
    async def test_normalize_raw_content(self) -> None:
        raw_items = [
            {"title": "Raw Security Item", "body": "Snippet body text", "url": "https://sec.com/1", "source": "exa"}
        ]
        topics = await normalize_raw_content(raw_items)
        assert len(topics) == 1
        assert topics[0]["title"] == "Raw Security Item"
        assert topics[0]["sources"] == ["https://sec.com/1"]

    @pytest.mark.asyncio
    async def test_discover_candidate_topics(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.discovery.discovery_service.fetch_exa_topics", AsyncMock(return_value=[{"title": "Exa 1", "url": "https://exa.ai/1"}]))
        monkeypatch.setattr("app.discovery.discovery_service.fetch_tavily_topics", AsyncMock(return_value=[]))
        monkeypatch.setattr("app.discovery.discovery_service.fetch_rss_topics", AsyncMock(return_value=[]))
        monkeypatch.setattr("app.discovery.discovery_service.fetch_github_topics", AsyncMock(return_value=[]))

        topics = await discover_candidate_topics("AI Security")
        assert len(topics) == 1
        assert topics[0]["title"] == "Exa 1"
