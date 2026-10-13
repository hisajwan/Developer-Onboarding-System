"""Maps Gemini SDK failures to the app's errors: rate limit or quota -> `ModelRateLimitedError`
(429, which also triggers the fallback model); anything else -> `ModelProviderError` (502).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from google.api_core.exceptions import (
    GoogleAPIError,
    PermissionDenied,
    ResourceExhausted,
    Unauthenticated,
)
from langchain_google_genai._common import GoogleGenerativeAIError

from app.core.exceptions import ModelProviderError, ModelRateLimitedError

_RATE_LIMITED = "Gemini's rate limit or daily quota was reached. Wait a minute and try again."


@contextmanager
def gemini_errors(action: str) -> Iterator[None]:
    try:
        yield
    except (GoogleAPIError, GoogleGenerativeAIError) as exc:
        raise _translate(exc, action) from exc


def _translate(exc: Exception, action: str) -> Exception:
    cause = exc.__cause__ if isinstance(exc, GoogleGenerativeAIError) else exc
    text = str(exc)
    if isinstance(cause, ResourceExhausted) or "429" in text or "RESOURCE_EXHAUSTED" in text:
        return ModelRateLimitedError(_RATE_LIMITED)
    if isinstance(cause, Unauthenticated | PermissionDenied) or "API key" in text:
        return ModelProviderError(
            f"Gemini rejected the API key while {action}. Check GEMINI_API_KEY in server/.env."
        )
    return ModelProviderError(f"Gemini failed while {action}: {_first_line(cause or exc)}")


def _first_line(exc: BaseException) -> str:
    text = str(exc).strip()
    return text.splitlines()[0][:300] if text else type(exc).__name__
