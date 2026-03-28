from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from typing import Any

try:
    import redis
except Exception:  # pragma: no cover - defensive fallback when redis is unavailable
    redis = None


logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(
        self,
        redis_url: str | None = None,
        prefix: str = "shopsocial:cache",
        *,
        prefix_invalidation_debug_enabled: bool | None = None,
        prefix_invalidation_debug_sample_rate: float | None = None,
    ) -> None:
        self._prefix = prefix
        self._lock = threading.Lock()
        self._memory: dict[str, tuple[str, float]] = {}
        self._redis_client = None
        self._prefix_invalidation_debug_enabled = (
            _parse_bool_env("CACHE_PREFIX_INVALIDATION_DEBUG_ENABLED", default=True)
            if prefix_invalidation_debug_enabled is None
            else prefix_invalidation_debug_enabled
        )
        self._prefix_invalidation_debug_sample_rate = (
            _parse_sample_rate_env("CACHE_PREFIX_INVALIDATION_DEBUG_SAMPLE_RATE", default=1.0)
            if prefix_invalidation_debug_sample_rate is None
            else _clamp_sample_rate(prefix_invalidation_debug_sample_rate)
        )

        if redis_url and redis is not None:
            self._redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get_json(self, key: str) -> Any | None:
        if self._redis_client is not None:
            cached = self._get_redis(key)
            if cached is not None:
                return cached
        return self._get_memory(key)

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> bool:
        payload = json.dumps(value, default=str)

        redis_ok = False
        if self._redis_client is not None:
            redis_ok = self._set_redis(key, payload, ttl_seconds)

        # Keep memory fallback updated for local mode and Redis outage scenarios.
        self._set_memory(key, payload, ttl_seconds)
        return redis_ok or True

    def delete(self, key: str) -> None:
        if self._redis_client is not None:
            self._delete_redis(key)
        with self._lock:
            self._memory.pop(key, None)

    def delete_prefix(self, key_prefix: str) -> None:
        start = time.perf_counter()

        redis_deleted = 0
        if self._redis_client is not None:
            redis_deleted = self._delete_prefix_redis(key_prefix)

        memory_deleted = 0
        with self._lock:
            keys = [k for k in self._memory.keys() if k.startswith(key_prefix)]
            memory_deleted = len(keys)
            for key in keys:
                self._memory.pop(key, None)

        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        if self._should_emit_prefix_invalidation_debug():
            logger.debug(
                "cache_prefix_invalidation",
                extra={
                    "event": "cache_prefix_invalidation",
                    "cache_prefix": key_prefix,
                    "redis_deleted": redis_deleted,
                    "memory_deleted": memory_deleted,
                    "duration_ms": duration_ms,
                },
            )

    def clear(self) -> None:
        with self._lock:
            self._memory.clear()

    def _namespaced_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def _get_redis(self, key: str) -> Any | None:
        client = self._redis_client
        if client is None:
            return None

        try:
            payload = client.get(self._namespaced_key(key))
            return json.loads(payload) if payload else None
        except Exception:
            return None

    def _set_redis(self, key: str, payload: str, ttl_seconds: int) -> bool:
        client = self._redis_client
        if client is None:
            return False

        try:
            client.setex(self._namespaced_key(key), max(ttl_seconds, 1), payload)
            return True
        except Exception:
            return False

    def _delete_redis(self, key: str) -> None:
        client = self._redis_client
        if client is None:
            return
        try:
            client.delete(self._namespaced_key(key))
        except Exception:
            return

    def _delete_prefix_redis(self, key_prefix: str) -> int:
        client = self._redis_client
        if client is None:
            return 0
        try:
            pattern = f"{self._prefix}:{key_prefix}*"
            keys = list(client.scan_iter(match=pattern, count=100))
            if keys:
                client.delete(*keys)
            return len(keys)
        except Exception:
            return 0

    def _get_memory(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                return None

            payload, expires_at = entry
            if expires_at <= now:
                self._memory.pop(key, None)
                return None

            return json.loads(payload)

    def _set_memory(self, key: str, payload: str, ttl_seconds: int) -> None:
        expires_at = time.time() + max(ttl_seconds, 1)
        with self._lock:
            self._memory[key] = (payload, expires_at)

    def _should_emit_prefix_invalidation_debug(self) -> bool:
        if not self._prefix_invalidation_debug_enabled:
            return False
        rate = self._prefix_invalidation_debug_sample_rate
        if rate <= 0:
            return False
        if rate >= 1:
            return True
        return random.random() <= rate


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _clamp_sample_rate(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _parse_sample_rate_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return _clamp_sample_rate(default)
    try:
        return _clamp_sample_rate(float(raw))
    except (TypeError, ValueError):
        return _clamp_sample_rate(default)


_cache_client: CacheClient | None = None


def get_cache_client() -> CacheClient:
    global _cache_client
    if _cache_client is None:
        use_redis = os.environ.get("CACHE_USE_REDIS", "1") == "1"
        redis_url = os.environ.get("REDIS_URL") if use_redis else None
        _cache_client = CacheClient(redis_url=redis_url)
    return _cache_client


def reset_cache_client() -> None:
    get_cache_client().clear()
