from __future__ import annotations

import random
import time
from functools import wraps
from typing import Callable, TypeVar

from ..config import get_settings

T = TypeVar("T")


def retry_provider(fn: Callable[..., T]) -> Callable[..., T]:
    """Retry a provider call with exponential backoff + jitter."""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        s = get_settings()
        last: Exception | None = None
        for attempt in range(max(1, s.provider_max_retries)):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last = exc
                if attempt + 1 >= s.provider_max_retries:
                    raise
                time.sleep(min(2 ** attempt + random.random(), 8))
        raise last  # pragma: no cover

    return wrapped
