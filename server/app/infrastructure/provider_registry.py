"""Shared lookup for the provider registries: name -> builder, one error for unknown names."""

from collections.abc import Callable, Mapping
from typing import TypeVar

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
