"""Phase 6 — unit tests for the configuration/settings layer."""

from __future__ import annotations

from app.core.config import Settings


class TestSettings:
    def test_defaults_are_typed(self) -> None:
        settings = Settings(_env_file=None)
        assert isinstance(settings.EDITORIAL_ACCEPT_THRESHOLD, float)
        assert isinstance(settings.PORT, int)
        assert isinstance(settings.PUBLISH_CYCLE_INTERVAL_MINUTES, int)
        assert settings.OPENAI_MODEL  # non-empty default model

    def test_rss_feeds_split_on_commas(self) -> None:
        settings = Settings(
            _env_file=None,
            RSS_FEED_URLS="https://a.example/feed.xml, https://b.example/rss",
        )
        assert settings.rss_feed_urls == [
            "https://a.example/feed.xml",
            "https://b.example/rss",
        ]

    def test_rss_feeds_empty_when_absent(self) -> None:
        settings = Settings(_env_file=None, RSS_FEED_URLS="")
        assert settings.rss_feed_urls == []

    def test_cors_origins_parsed(self) -> None:
        settings = Settings(_env_file=None, CORS_ORIGINS="http://a.com, http://b.com")
        assert settings.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_production_flag(self) -> None:
        assert Settings(_env_file=None, ENVIRONMENT="production").is_production
        assert not Settings(_env_file=None, ENVIRONMENT="local").is_production

    def test_invalid_threshold_rejected(self) -> None:
        try:
            Settings(_env_file=None, EDITORIAL_ACCEPT_THRESHOLD=150.0)
        except Exception as exc:  # noqa: BLE001
            assert "EDITORIAL_ACCEPT_THRESHOLD" in str(exc)
        else:
            assert False, "expected validation error for out-of-range threshold"

    def test_invalid_type_raises_validation_error(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(_env_file=None, PORT="not_an_int")

    def test_get_settings_is_cached(self) -> None:
        from app.core.config import get_settings

        get_settings.cache_clear()
        first = get_settings()
        second = get_settings()
        assert first is second