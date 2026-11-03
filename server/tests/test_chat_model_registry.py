import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableWithFallbacks
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.registry import create_chat_model
from app.infrastructure.gemini.chat import GeminiChatModel
from app.infrastructure.groq.chat import GroqChatModel


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


def test_groq_chat_model_is_built_when_its_key_is_present() -> None:
    settings = Settings(llm_provider="groq", groq_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_chat_model(settings), GroqChatModel)


def test_groq_chat_model_without_a_key_is_a_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        create_chat_model(Settings(llm_provider="groq", _env_file=None))


def test_groq_uses_the_configured_model() -> None:
    settings = Settings(
        llm_provider="groq", groq_api_key=SecretStr("k"), groq_model="m-1", _env_file=None
    )

    assert create_chat_model(settings).model_name == "m-1"


def test_a_fallback_provider_wraps_the_main_one() -> None:
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key=SecretStr("k"),
        groq_api_key=SecretStr("k"),
        llm_fallback_provider="groq",
        _env_file=None,
    )

    model = create_chat_model(settings)

    assert isinstance(model, RunnableWithFallbacks)
    assert isinstance(model.runnable, RunnableWithFallbacks)  # Gemini's own fallback model
    [backup] = model.fallbacks
    assert isinstance(backup, GroqChatModel)


def test_a_fallback_provider_equal_to_the_main_one_is_ignored() -> None:
    settings = Settings(llm_fallback_provider="fake", _env_file=None)

    assert isinstance(create_chat_model(settings), FakeToolCallingChatModel)
