"""Application settings — single typed source of truth for every environment variable."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_commas(value: str) -> list[str]:
    """Split a comma-separated string into a cleaned list of non-empty items."""
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Typed settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PORT: int = Field(default=8000, ge=1, le=65535)

    # --- Database (Postgres) ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kestrel"

    # --- LLM ---
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_MODEL: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    @property
    def llm_api_key(self) -> str:
        """Prefer Groq, then OpenRouter, then direct OpenAI."""
        return self.GROQ_API_KEY.strip() or self.OPENROUTER_API_KEY.strip() or self.OPENAI_API_KEY.strip()

    @property
    def llm_base_url(self) -> str | None:
        """Returns base URL for OpenRouter or custom OpenAI proxy if set."""
        if self.GROQ_API_KEY.strip():
            return self.GROQ_BASE_URL.strip()
        if self.OPENAI_BASE_URL.strip():
            return self.OPENAI_BASE_URL.strip()
        if self.OPENROUTER_API_KEY.strip() or self.OPENROUTER_MODEL.strip():
            return self.OPENROUTER_BASE_URL.strip()
        return None

    @property
    def llm_model(self) -> str:
        """Return the configured model for the active provider."""
        if self.GROQ_API_KEY.strip():
            return self.GROQ_MODEL.strip()
        if self.OPENROUTER_MODEL.strip():
            return self.OPENROUTER_MODEL.strip()
        return self.OPENAI_MODEL.strip()

    # --- Breeth memory ---
    BREETH_API_KEY: str = ""
    BREETH_BASE_URL: str = "https://api.breeth.example"

    # --- Discovery sources ---
    EXA_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    GITHUB_TOKEN: str = ""
    RSS_FEED_URLS: str = ""



    # --- Clerk auth ---
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_JWKS_URL: str = ""

    # --- Cadence & editorial thresholds ---
    PUBLISH_CYCLE_INTERVAL_MINUTES: int = Field(default=120, gt=0)
    SELF_AUDIT_EVERY_N_CYCLES: int = Field(default=10, gt=0)
    EDITORIAL_ACCEPT_THRESHOLD: float = Field(default=60.0, ge=0.0, le=100.0)

    # --- Observability ---
    SENTRY_DSN: str = ""

    # --- CORS (comma-separated) ---
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def rss_feed_urls(self) -> list[str]:
        return _split_commas(self.RSS_FEED_URLS)

    @property
    def cors_origins_list(self) -> list[str]:
        return _split_commas(self.CORS_ORIGINS)


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor; returns the same instance on every call."""
    return Settings()


SettingsDependency = Annotated[Settings, Depends(get_settings)]
