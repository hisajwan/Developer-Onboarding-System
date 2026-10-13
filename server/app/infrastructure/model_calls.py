"""A process-wide tally of requests sent to model providers, for evaluation runs.

Each real adapter counts one request per call it sends, failed or not (a rate-limited call still
used quota, and a fallback shows up as a second model). `snapshot()` before and after a piece of
work, then `since(before)`, gives what that work cost.
"""

import threading
from collections import Counter

_lock = threading.Lock()
_calls: Counter[str] = Counter()


def count(provider: str, model: str, kind: str) -> None:
    """`kind` is what the request did, e.g. "chat" or "embed"."""
    with _lock:
        _calls[f"{provider}:{kind}:{model}"] += 1


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_calls)


def since(before: dict[str, int]) -> dict[str, int]:
    """Calls made after `before` was taken, by key; keys with no new calls are left out."""
    now = snapshot()
    return {key: n - before.get(key, 0) for key, n in now.items() if n > before.get(key, 0)}
