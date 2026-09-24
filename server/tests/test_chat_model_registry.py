import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableWithFallbacks
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.groq import GroqToolCallingChatModel
from app.infrastructure.chat_models.openrouter import OpenRouterToolCallingChatModel
from app.infrastructure.chat_models.registry import create_chat_model
from app.infrastructure.gemini.chat import GeminiChatModel


def test_default_settings_use_the_fake_chat_model() -> None:
    assert isinstance(create_chat_model(Settings(_env_file=None)), FakeToolCallingChatModel)


def test_the_fake_chat_model_satisfies_base_chat_model() -> None:
    assert isinstance(create_chat_model(Settings(_env_file=None)), BaseChatModel)


def test_gemini_is_built_with_its_fallback_model_by_default() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    model = create_chat_model(settings)

    assert isinstance(model, RunnableWithFallbacks)
    assert isinstance(model.runnable, GeminiChatModel)
    assert model.runnable.model.endswith(settings.gemini_model)
    [fallback] = model.fallbacks
    assert fallback.model.endswith(settings.gemini_fallback_model)


def test_gemini_without_a_fallback_model_is_a_plain_chat_model() -> None:
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key=SecretStr("k"),
        gemini_fallback_model=None,
        _env_file=None,
    )

    assert isinstance(create_chat_model(settings), GeminiChatModel)


def test_gemini_without_a_key_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_chat_model(settings)


@pytest.mark.parametrize(
    ("provider", "model_class", "key_field"),
    [
        ("groq", GroqToolCallingChatModel, "groq_api_key"),
        ("openrouter", OpenRouterToolCallingChatModel, "openrouter_api_key"),
    ],
)
def test_fallback_chat_models_are_built_when_their_key_is_present(
    provider: str, model_class: type, key_field: str
) -> None:
    settings = Settings(llm_provider=provider, **{key_field: SecretStr("k")}, _env_file=None)

    assert isinstance(create_chat_model(settings), model_class)


@pytest.mark.parametrize("provider", ["groq", "openrouter"])
def test_fallback_chat_models_without_a_key_are_a_configuration_error(provider: str) -> None:
    settings = Settings(llm_provider=provider, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_chat_model(settings)


@pytest.mark.parametrize(
    ("model_class", "key_field"),
    [
        (GroqToolCallingChatModel, "groq_api_key"),
        (OpenRouterToolCallingChatModel, "openrouter_api_key"),
    ],
)
def test_fallback_chat_model_generation_is_not_implemented_yet(
    model_class: type, key_field: str
) -> None:
    model = model_class.from_settings(Settings(**{key_field: SecretStr("k")}, _env_file=None))

    with pytest.raises(NotImplementedError):
        model.invoke("hello")
