import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.infrastructure.chat_models.fake import FakeToolCallingChatModel
from app.infrastructure.chat_models.gemini import GeminiToolCallingChatModel
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


def test_an_unimplemented_provider_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="groq", _env_file=None)

    with pytest.raises(ConfigurationError, match="Chat model provider 'groq'"):
        create_chat_model(settings)
