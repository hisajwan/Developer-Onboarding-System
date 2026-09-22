import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.domain.ports import Embedder, LLMClient
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.infrastructure.embeddings.gemini import GeminiEmbedder
from app.infrastructure.embeddings.registry import create_embedder
from app.infrastructure.llm.fake import FakeLLMClient
from app.infrastructure.llm.groq import GroqLLMClient
from app.infrastructure.llm.openrouter import OpenRouterLLMClient
from app.infrastructure.llm.registry import create_llm_client


def test_default_settings_use_fakes_so_nothing_needs_a_key() -> None:
    settings = Settings(_env_file=None)

    assert isinstance(create_llm_client(settings), FakeLLMClient)
    assert isinstance(create_embedder(settings), FakeEmbedder)


def test_embedder_registry_returns_the_embedder_port() -> None:
    assert isinstance(create_embedder(Settings(_env_file=None)), Embedder)


def test_gemini_embedder_is_built_when_a_key_is_present() -> None:
    settings = Settings(embedding_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_embedder(settings), GeminiEmbedder)


def test_gemini_embedder_without_a_key_is_a_configuration_error() -> None:
    settings = Settings(embedding_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_embedder(settings)


@pytest.mark.anyio
async def test_gemini_embeddings_are_not_implemented_yet() -> None:
    embedder = GeminiEmbedder.from_settings(
        Settings(embedding_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)
    )

    with pytest.raises(NotImplementedError):
        await embedder.embed_query("hello")


def test_gemini_client_is_built_when_key_is_present() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_llm_client(settings), LLMClient)


def test_missing_api_key_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_llm_client(settings)


@pytest.mark.parametrize(
    ("provider", "client_class", "key_field"),
    [
        ("groq", GroqLLMClient, "groq_api_key"),
        ("openrouter", OpenRouterLLMClient, "openrouter_api_key"),
    ],
)
def test_fallback_llm_providers_are_built_when_their_key_is_present(
    provider: str, client_class: type, key_field: str
) -> None:
    settings = Settings(llm_provider=provider, **{key_field: SecretStr("k")}, _env_file=None)

    assert isinstance(create_llm_client(settings), client_class)


@pytest.mark.parametrize("provider", ["groq", "openrouter"])
def test_fallback_llm_providers_without_a_key_are_a_configuration_error(provider: str) -> None:
    settings = Settings(llm_provider=provider, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_llm_client(settings)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("client_class", "key_field"),
    [(GroqLLMClient, "groq_api_key"), (OpenRouterLLMClient, "openrouter_api_key")],
)
async def test_fallback_llm_generation_is_not_implemented_yet(
    client_class: type, key_field: str
) -> None:
    client = client_class.from_settings(Settings(**{key_field: SecretStr("k")}, _env_file=None))

    with pytest.raises(NotImplementedError):
        await client.generate("hello")
