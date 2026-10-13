"""Maps Groq SDK failures to the app's errors: rate limit -> `ModelRateLimitedError` (429, which
also triggers a configured fallback provider); anything else -> `ModelProviderError` (502).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from groq import AuthenticationError, GroqError, PermissionDeniedError, RateLimitError

from app.core.exceptions import ModelProviderError, ModelRateLimitedError

_RATE_LIMITED = "Groq's rate limit or daily quota was reached. Wait a minute and try again."


@contextmanager
def groq_errors(action: str) -> Iterator[None]:
    try:
        yield
    except GroqError as exc:
        raise _translate(exc, action) from exc


def _translate(exc: GroqError, action: str) -> Exception:
    if isinstance(exc, RateLimitError):
        return ModelRateLimitedError(_RATE_LIMITED)
    if isinstance(exc, AuthenticationError | PermissionDeniedError):
        return ModelProviderError(
            f"Groq rejected the API key while {action}. Check GROQ_API_KEY in server/.env."
        )
    text = str(exc).strip()
    detail = text.splitlines()[0][:300] if text else type(exc).__name__
    return ModelProviderError(f"Groq failed while {action}: {detail}")
