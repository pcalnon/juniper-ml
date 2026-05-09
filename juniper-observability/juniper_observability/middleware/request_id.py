"""Request-ID propagation middleware.

Injects an ``X-Request-ID`` header into every response and stores the
value in a ContextVar so async handlers and log records can correlate
to the originating HTTP request without threading the ID through every
call.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from juniper_observability.constants import HEADER_X_REQUEST_ID

# Public ContextVar; ``JuniperJsonFormatter`` reads from it to embed the
# request ID in every log record emitted during the request scope.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injects ``X-Request-ID`` into ContextVar and response header.

    If the request carries an inbound ``X-Request-ID`` header, that
    value is propagated; otherwise a fresh UUID4 is generated. The
    header is always echoed back on the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        rid = request.headers.get(HEADER_X_REQUEST_ID, str(uuid.uuid4()))
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
            response.headers[HEADER_X_REQUEST_ID] = rid
            return response
        finally:
            request_id_var.reset(token)
