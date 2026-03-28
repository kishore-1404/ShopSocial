from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import DefaultDict, Deque

try:
    import redis
except Exception:  # pragma: no cover - defensive fallback when redis is unavailable
    redis = None


class RateLimiter:
    def __init__(self, redis_url: str | None = None, prefix: str = "shopsocial:ratelimit") -> None:
        self._prefix = prefix
        self._lock = threading.Lock()
        self._events: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._redis_client = None

        if redis_url and redis is not None:
            self._redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        if limit <= 0:
            return False, max(window_seconds, 1)

        if self._redis_client is not None:
            return self._allow_redis(key, limit, window_seconds)

        return self._allow_memory(key, limit, window_seconds)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def _allow_memory(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                oldest = bucket[0]
                retry_after = max(int(window_seconds - (now - oldest)) + 1, 1)
                return False, retry_after

            bucket.append(now)
            return True, 0

    def _allow_redis(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        redis_key = f"{self._prefix}:{key}"
        client = self._redis_client
        if client is None:
            return self._allow_memory(key, limit, window_seconds)

        try:
            with client.pipeline() as pipe:
                pipe.incr(redis_key)
                pipe.expire(redis_key, window_seconds, nx=True)
                count, _ = pipe.execute()

            count_int = int(count)
            if count_int > limit:
                ttl = client.ttl(redis_key)
                retry_after = max(int(ttl), 1) if ttl and ttl > 0 else window_seconds
                return False, retry_after
            return True, 0
        except Exception:
            # Degrade to in-process limiting if Redis is temporarily unavailable.
            return self._allow_memory(key, limit, window_seconds)


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        use_redis = os.environ.get("RATE_LIMIT_USE_REDIS", "1") == "1"
        redis_url = os.environ.get("REDIS_URL") if use_redis else None
        _rate_limiter = RateLimiter(redis_url=redis_url)
    return _rate_limiter


def reset_rate_limiter() -> None:
    get_rate_limiter().reset()
