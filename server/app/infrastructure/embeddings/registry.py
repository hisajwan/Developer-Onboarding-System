"""Maps EMBEDDING_PROVIDER to an adapter. Adding a provider = one adapter class + one line here."""

from collections.abc import Callable

from app.core.config import Settings
from app.domain.ports import Embedder
from app.infrastructure.embeddings.fake import FakeEmbedder
from app.infrastructure.provider_registry import build_provider

_PROVIDERS: dict[str, Callable[[Settings], Embedder]] = {
    "fake": FakeEmbedder.from_settings,
}


def create_embedder(settings: Settings) -> Embedder:
    return build_provider("Embedding", settings.embedding_provider, _PROVIDERS, settings)
