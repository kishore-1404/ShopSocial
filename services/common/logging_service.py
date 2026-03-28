from __future__ import annotations

import json
import logging
import logging.handlers
import queue
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any


_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})
_listener: logging.handlers.QueueListener | None = None
_configured_services: set[str] = set()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "logger": record.name,
            "message": record.getMessage(),
        }

        context = _request_context.get()
        if context:
            payload.update(context)

        # Include common request metadata if available on record extras.
        for field in ("event", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(service_name: str, level: int = logging.INFO) -> None:
    global _listener
    if service_name in _configured_services:
        return

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers when multiple services import this in-process.
    if not any(isinstance(h, logging.handlers.QueueHandler) for h in root_logger.handlers):
        root_logger.handlers = [queue_handler]

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JsonFormatter())

    if _listener is None:
        _listener = logging.handlers.QueueListener(log_queue, stream_handler, respect_handler_level=True)
        _listener.start()

    _configured_services.add(service_name)


def get_logger(name: str, service_name: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {"service": service_name})


def bind_context(**kwargs: Any) -> None:
    current = dict(_request_context.get())
    current.update(kwargs)
    _request_context.set(current)


def clear_context() -> None:
    _request_context.set({})
