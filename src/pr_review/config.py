"""
Centralized environment configuration.

Every module that needs an environment variable imports `settings` from
here — nothing in the codebase should call `os.getenv(...)` directly.
This keeps all required env vars discoverable in one place, and gives us
validation for free (pydantic-settings raises a clear error at startup if
something required is missing, instead of failing later with a cryptic
KeyError deep in a request).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub App / webhook
    github_webhook_secret: str
    github_app_id: str = ""
    github_private_key_path: str = ""

    # Ollama (local LLM, see AGENTS.md — provider-agnostic behind llm/)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    # Infra (used starting from the queue/DB steps)
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pr_review"


settings = Settings()  # type: ignore[call-arg]  # values come from .env at runtime