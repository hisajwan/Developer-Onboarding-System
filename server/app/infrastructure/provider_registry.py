"""Shared lookup for the provider registries: name -> builder, one error for unknown names."""

from collections.abc import Callable, Mapping
from typing import TypeVar

from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import ConfigurationError

T = TypeVar("T")


def build_provider(
    kind: str,
    name: str,
    providers: Mapping[str, Callable[[Settings], T]],
    settings: Settings,
) -> T:
    builder = providers.get(name)
    if builder is None:
        raise ConfigurationError(f"{kind} provider '{name}' is not implemented yet.")
    return builder(settings)


def require_api_key(secret: SecretStr | None, env_var: str) -> SecretStr:
    """A key counts as set only if it holds a real value.

    `KEY=` in `.env` (present, blank) parses to `SecretStr('')`, not `None`, so checking only
    `is None` lets a blank key through silently.
    """
    if secret is None or not secret.get_secret_value().strip():
        raise ConfigurationError(f"{env_var} is not set.")
    return secret
