import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.infrastructure.provider_registry import build_provider, require_api_key


def test_an_unregistered_name_is_a_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="Widget provider 'nonexistent'"):
        build_provider("Widget", "nonexistent", {}, Settings(_env_file=None))


def test_a_registered_name_calls_its_builder_with_the_settings() -> None:
    settings = Settings(_env_file=None)
    providers = {"known": lambda s: ("built", s)}

    assert build_provider("Widget", "known", providers, settings) == ("built", settings)


def test_require_api_key_returns_a_real_value_unchanged() -> None:
    secret = SecretStr("real-key")

    assert require_api_key(secret, "SOME_KEY") is secret


def test_require_api_key_rejects_a_missing_key() -> None:
    with pytest.raises(ConfigurationError, match="SOME_KEY is not set"):
        require_api_key(None, "SOME_KEY")


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_require_api_key_rejects_a_present_but_blank_key(blank: str) -> None:
    """`KEY=` in .env parses to SecretStr(''), not None — this is the actual shape of the bug."""
    with pytest.raises(ConfigurationError, match="SOME_KEY is not set"):
        require_api_key(SecretStr(blank), "SOME_KEY")
