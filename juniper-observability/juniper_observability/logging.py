"""Structured-JSON logging primitives for Juniper services.

Provides:

- ``JuniperJsonFormatter`` — a ``logging.Formatter`` subclass that
  emits one JSON object per record with stable keys (``timestamp``,
  ``level``, ``logger``, ``message``, ``service``, ``request_id``, and
  optional ``exception``).
- ``configure_logging`` — installs the formatter onto the root logger
  with the requested level, replacing any existing handlers.

The ``request_id`` field is sourced from the ``request_id_var``
ContextVar populated by ``RequestIdMiddleware`` so async handlers can
emit log lines that correlate to the originating HTTP request without
threading the ID through every call.
"""

import json
import logging

from juniper_observability.middleware.request_id import request_id_var

# Default plain-text log format when ``log_format != "json"``. Mirrors
# the Python convention used by every Juniper service.
DEFAULT_LOG_FORMAT_PLAIN = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Sentinel value identifying the JSON formatter mode.
LOG_FORMAT_JSON = "json"


class JuniperJsonFormatter(logging.Formatter):
    """JSON log formatter with ``request_id`` propagation.

    Always emits the same set of top-level keys so log shippers can
    parse every Juniper service's logs without per-service rules.
    """

    def __init__(self, service: str = "juniper-service") -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service,
            "request_id": request_id_var.get(""),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def configure_logging(log_level: str, log_format: str, service_name: str = "juniper-service") -> None:
    """Configure the root logger.

    Args:
        log_level: Logging level string (``"INFO"``, ``"DEBUG"``, …).
            Unknown values fall back to ``logging.INFO``.
        log_format: ``"json"`` for structured JSON via
            :class:`JuniperJsonFormatter`; anything else for plain
            text via :data:`DEFAULT_LOG_FORMAT_PLAIN`.
        service_name: Service identity included in JSON log entries.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicate output.
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    if log_format == LOG_FORMAT_JSON:
        handler.setFormatter(JuniperJsonFormatter(service=service_name))
    else:
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT_PLAIN))

    root.addHandler(handler)
