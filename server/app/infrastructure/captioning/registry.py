"""Maps CAPTION_PROVIDER to an adapter. Adding a provider = one adapter class + one line here."""

from collections.abc import Callable

from app.core.config import Settings
from app.domain.ports import ImageCaptioner
from app.infrastructure.captioning.fake import FakeImageCaptioner
from app.infrastructure.captioning.gemini import GeminiImageCaptioner
from app.infrastructure.provider_registry import build_provider

_PROVIDERS: dict[str, Callable[[Settings], ImageCaptioner]] = {
    "fake": FakeImageCaptioner.from_settings,
    "gemini": GeminiImageCaptioner.from_settings,
}


def create_captioner(settings: Settings) -> ImageCaptioner:
    return build_provider("Caption", settings.caption_provider, _PROVIDERS, settings)
