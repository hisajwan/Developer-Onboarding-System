import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.gemini import GeminiToolCallingChatModel
from app.infrastructure.chat_models.groq import GroqToolCallingChatModel
from app.infrastructure.chat_models.openrouter import OpenRouterToolCallingChatModel
from app.infrastructure.chat_models.registry import create_chat_model


def test_default_settings_use_the_fake_chat_model() -> None:
    assert isinstance(create_chat_model(Settings(_env_file=None)), FakeToolCallingChatModel)


def test_the_fake_chat_model_satisfies_base_chat_model() -> None:
    assert isinstance(create_chat_model(Settings(_env_file=None)), BaseChatModel)


def test_gemini_is_built_when_a_key_is_present() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_chat_model(settings), GeminiToolCallingChatModel)


def test_gemini_without_a_key_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_chat_model(settings)


def test_gemini_agent_generation_is_not_implemented_yet() -> None:
    model = GeminiToolCallingChatModel.from_settings(
        Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)
    )

    with pytest.raises(NotImplementedError):
        model.invoke("hello")


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
