from __future__ import annotations

import time
import uuid

from django.http import HttpRequest, HttpResponse

from common.logging_service import bind_context, clear_context, configure_logging, get_logger


configure_logging("user")
logger = get_logger(__name__, "user")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        bind_context(request_id=request_id)
        start = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            logger.exception("unexpected_error", extra={"event": "unexpected_error"})
            clear_context()
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        clear_context()
        return response
