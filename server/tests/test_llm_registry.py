import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.domain.ports import LLMClient
from app.infrastructure.llm.registry import create_llm_client


def test_gemini_client_is_built_when_key_is_present() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("k"), _env_file=None)

    assert isinstance(create_llm_client(settings), LLMClient)


def test_missing_api_key_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, _env_file=None)

    with pytest.raises(ConfigurationError):
        create_llm_client(settings)


def test_unimplemented_provider_is_a_configuration_error() -> None:
    settings = Settings(llm_provider="groq", _env_file=None)

    with pytest.raises(ConfigurationError):
        create_llm_client(settings)
