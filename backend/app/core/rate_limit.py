"""A minimal in-process sliding-window rate limiter for registration-flow
endpoints (register / resend-code). Deliberately single-node: state is a
plain dict in this process's memory, not Firestore or Redis. That's an
accepted scope limit, not an oversight — see docs/03-ARCHITECTURE.md's
Performance section note on this feature. It resets on every backend
restart and does not coordinate across multiple backend instances; a
production multi-instance deployment would need a shared store instead.
"""

import time
from collections import defaultdict
from threading import Lock

from app.core.errors import RateLimitError


class RateLimiter:
    def __init__(self, *, max_calls: int, window_seconds: float) -> None:
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> None:
        """Raises RateLimitError if `key` has already made `max_calls`
        within the trailing window; otherwise records this call."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            recent = [t for t in self._calls[key] if t > cutoff]
            if len(recent) >= self._max_calls:
                raise RateLimitError(
                    "Too many requests — please wait before trying again",
                    details={"retry_after_seconds": self._window_seconds},
                )
            recent.append(now)
            self._calls[key] = recent
