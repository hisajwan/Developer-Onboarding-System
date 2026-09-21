"""Application settings, loaded once from environment variables / `.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["fake", "gemini", "groq", "openrouter"]
EmbeddingProviderName = Literal["fake", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Onboarding Platform API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"

    # JSON list in the environment, e.g. CORS_ORIGINS=["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000"]

    # "fake" needs no network or keys; switch to a real provider only after the integration gate.
    llm_provider: LLMProviderName = "fake"
    embedding_provider: EmbeddingProviderName = "fake"
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    # Login gate: one user, checked on the server. Set all three in server/.env (off while unset).
    auth_username: str | None = None
    auth_password: SecretStr | None = None
    auth_secret: SecretStr | None = None  # signs the session token
    session_ttl_minutes: int = 480

    data_dir: Path = Path("data")

    @property
    def docs_dir(self) -> Path:
        return self.data_dir / "docs"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
