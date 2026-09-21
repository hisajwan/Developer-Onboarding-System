"""Application settings, loaded once from environment variables / `.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["gemini", "groq", "openrouter"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Onboarding Platform API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"

    # JSON list in the environment, e.g. CORS_ORIGINS=["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000"]

    llm_provider: LLMProviderName = "gemini"
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

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
