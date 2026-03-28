from __future__ import annotations

import os

from django.http import HttpRequest, HttpResponse, JsonResponse

from common.rate_limit import get_rate_limiter


rate_limiter = get_rate_limiter()


def _get_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _limit_for_path(path: str) -> tuple[str, int, int] | None:
    if path.startswith("/api/auth/"):
        return (
            "auth",
            _get_positive_int_env("USER_AUTH_RATE_LIMIT", 30),
            _get_positive_int_env("USER_AUTH_RATE_WINDOW_SECONDS", 60),
        )

    if path in {
        "/api/accounts/register/",
        "/api/accounts/follow/",
        "/api/accounts/unfollow/",
        "/api/accounts/like/",
        "/api/accounts/unlike/",
        "/api/accounts/comments/create/",
    }:
        return (
            "sensitive",
            _get_positive_int_env("USER_SENSITIVE_RATE_LIMIT", 60),
            _get_positive_int_env("USER_SENSITIVE_RATE_WINDOW_SECONDS", 60),
        )

    return None


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        config = _limit_for_path(request.path)
        if config is not None:
            scope, limit, window = config
            client_ip = (
                request.headers.get("X-Forwarded-For")
                or request.META.get("REMOTE_ADDR")
                or "unknown"
            )
            allowed, retry_after = rate_limiter.allow(
                f"user:{scope}:{request.path}:{client_ip}",
                limit,
                window,
            )
            if not allowed:
                response = JsonResponse(
                    {"detail": "Rate limit exceeded", "retry_after": retry_after},
                    status=429,
                )
                response["Retry-After"] = str(retry_after)
                return response

        return self.get_response(request)
