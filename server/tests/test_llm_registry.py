import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.domain.ports import Embedder, LLMClient
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.infrastructure.embeddings.registry import create_embedder
from app.infrastructure.llm.fake import FakeLLMClient
from app.infrastructure.llm.registry import create_llm_client


def test_default_settings_use_fakes_so_nothing_needs_a_key() -> None:
    settings = Settings(_env_file=None)

    assert isinstance(create_llm_client(settings), FakeLLMClient)
    assert isinstance(create_embedder(settings), FakeEmbedder)


def test_embedder_registry_returns_the_embedder_port() -> None:
    assert isinstance(create_embedder(Settings(_env_file=None)), Embedder)


def test_unimplemented_embedding_provider_is_a_configuration_error() -> None:
    settings = Settings(embedding_provider="gemini", _env_file=None)

    with pytest.raises(ConfigurationError, match="Embedding provider 'gemini'"):
        create_embedder(settings)


def test_gemini_client_is_built_when_key_is_present() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_llm_client(settings), LLMClient)


def test_missing_api_key_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_llm_client(settings)


def test_unimplemented_provider_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="groq", _env_file=None)

    with pytest.raises(ConfigurationError, match="LLM provider 'groq'"):
        create_llm_client(settings)
