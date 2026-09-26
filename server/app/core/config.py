"""Application settings, loaded once from environment variables / `.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["fake", "gemini", "groq", "openrouter"]
EmbeddingProviderName = Literal["fake", "gemini"]
CaptionProviderName = Literal["fake", "gemini"]


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
    caption_provider: CaptionProviderName = "fake"
    gemini_api_key: SecretStr | None = None
    # Gemini models (see https://aistudio.google.com/rate-limit). One text model does answers,
    # review judgement, tool choice and captions; the fallback (own quota) is used on rate limits.
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_model: str | None = "gemini-3.1-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    # Embedding calls are sent in groups under this many (estimated) tokens per minute.
    gemini_embedding_tokens_per_minute: int = 30_000
    gemini_timeout_seconds: float = 60.0
    gemini_max_retries: int = 1
    groq_api_key: SecretStr | None = None
    # Groq model (see https://console.groq.com/docs/rate-limits); must support tool calling.
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 60.0
    groq_max_retries: int = 1
    # Another text provider to switch to when LLM_PROVIDER's models are all rate-limited (after
    # Gemini's own fallback model). Empty disables it. Embeddings and captions never switch.
    llm_fallback_provider: LLMProviderName | None = None

    @field_validator("llm_fallback_provider", mode="before")
    @classmethod
    def _blank_means_none(cls, value: object) -> object:
        # `LLM_FALLBACK_PROVIDER=` in .env arrives as "", which should mean "no fallback".
        return None if isinstance(value, str) and not value.strip() else value

    openrouter_api_key: SecretStr | None = None

    # Login: accounts live in the users table (see scripts/create_user.py), not here. This secret
    # only signs the session token, so it alone must be set in server/.env.
    auth_secret: SecretStr | None = None
    session_ttl_minutes: int = 480

    data_dir: Path = Path("data")

    # Ingestion
    max_upload_bytes: int = 10 * 1024 * 1024
    chunk_max_tokens: int = 500
    chunk_overlap_tokens: int = 50
    # Skip images smaller than this on their shortest side (icons, avatars) and cap how many are
    # captioned per file.
    min_image_dimension_px: int = 100
    max_images_per_document: int = 20

    # Ask mode: how many chunks retrieve_and_answer feeds to the model per question.
    retrieval_top_k: int = 4

    # Code review: the Node helper that lints a snippet with ESLint (install it with `npm install`
    # in server/lint). Defaults to that folder wherever the server is started from.
    lint_dir: Path = Path(__file__).resolve().parents[2] / "lint"
    node_binary: str = "node"
    lint_timeout_seconds: float = 20.0

    @property
    def docs_dir(self) -> Path:
        return self.data_dir / "docs"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "onboarding.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
