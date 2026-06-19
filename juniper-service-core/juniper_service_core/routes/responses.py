"""Standard API response envelope for Juniper model services (WS-2 / OUT-11 T2).

The de-cascored core of cascor's ``api/models/common.py``: every generic route wraps its
payload in :class:`ResponseEnvelope` via :func:`success_response`, so all services share one
response shape::

    {"status": "success", "data": {...}, "meta": {"timestamp": ..., "version": ...}}

:func:`success_response` runs the payload through :func:`coerce_native_scalars` first, so
``numpy.int64`` / ``numpy.float64`` / 0-d ndarray scalars (which a model's ``metrics()`` or
``describe_topology()`` routinely return) become JSON-clean Python natives before
pydantic-core serializes the envelope. ``version`` defaults to the installed
``juniper-service-core`` version.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from juniper_service_core._version import __version__

__all__ = [
    "Meta",
    "ResponseEnvelope",
    "ErrorDetail",
    "ErrorResponse",
    "success_response",
    "error_response",
    "coerce_native_scalars",
]


def coerce_native_scalars(value: Any) -> Any:
    """Recursively coerce numpy scalar types to Python natives.

    pydantic-core's JSON serializer rejects ``numpy.int64`` / ``numpy.float64`` with
    ``PydanticSerializationError: Unable to serialize unknown type``. Model outputs (metrics,
    topology ``meta``, dataset arrays read back from disk) routinely surface numpy scalars, so
    this is applied at the envelope boundary -- every route's payload is JSON-clean regardless
    of whether the route author remembered to coerce per field.

    Walks dicts and lists/tuples; anything exposing a numpy-like ``.item()`` is collapsed to a
    native. Plain ``str`` / ``int`` / ``float`` / ``bool`` / ``None`` have no ``.item()`` so
    they pass through untouched.
    """
    if isinstance(value, dict):
        return {key: coerce_native_scalars(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        coerced = [coerce_native_scalars(item) for item in value]
        return type(value)(coerced) if isinstance(value, tuple) else coerced
    item = getattr(value, "item", None)
    if callable(item):
        # numpy scalars and 0-d numpy arrays expose ``.item()`` returning a Python native.
        try:
            return item()
        except (ValueError, TypeError):
            # Defensive: an object whose ``.item()`` takes args / raises falls through.
            return value
    return value


class Meta(BaseModel):
    """Response metadata: a server timestamp and the service-core version."""

    timestamp: float = Field(default_factory=time.time)
    version: str = __version__


class ResponseEnvelope(BaseModel):
    """The standard success/error response envelope."""

    status: str = "success"
    data: Any = None
    meta: Meta = Field(default_factory=Meta)


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str
    message: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    """The standard error response envelope."""

    status: str = "error"
    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)


def success_response(data: Any = None) -> dict:
    """Build a success envelope dict, coercing numpy scalars in ``data`` to JSON-clean natives."""
    return ResponseEnvelope(status="success", data=coerce_native_scalars(data)).model_dump()


def error_response(code: str, message: str, detail: str | None = None) -> dict:
    """Build an error envelope dict."""
    return ErrorResponse(error=ErrorDetail(code=code, message=message, detail=detail)).model_dump()
