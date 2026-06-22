"""Tests for ``RequestIdMiddleware``."""

from unittest.mock import MagicMock

import pytest

from juniper_observability import RequestIdMiddleware, request_id_var


class TestRequestIdMiddleware:
    @pytest.mark.asyncio
    async def test_generates_uuid_when_no_header(self):
        import uuid

        middleware = RequestIdMiddleware(app=MagicMock())
        captured: dict = {}

        async def call_next(request):
            captured["rid"] = request_id_var.get("")
            response = MagicMock()
            response.headers = {}
            return response

        request = MagicMock()
        request.headers = {}

        response = await middleware.dispatch(request, call_next)
        # Generated value must be a valid UUID
        uuid.UUID(captured["rid"])
        # Header echoed in response
        assert response.headers["X-Request-ID"] == captured["rid"]

    @pytest.mark.asyncio
    async def test_uses_provided_header(self):
        middleware = RequestIdMiddleware(app=MagicMock())
        captured: dict = {}

        async def call_next(request):
            captured["rid"] = request_id_var.get("")
            response = MagicMock()
            response.headers = {}
            return response

        request = MagicMock()
        request.headers = {"X-Request-ID": "explicit-id-42"}

        response = await middleware.dispatch(request, call_next)
        assert captured["rid"] == "explicit-id-42"
        assert response.headers["X-Request-ID"] == "explicit-id-42"

    @pytest.mark.asyncio
    async def test_contextvar_reset_after_dispatch(self):
        """The middleware must reset the contextvar so adjacent requests don't see each other's IDs."""
        middleware = RequestIdMiddleware(app=MagicMock())

        async def call_next(_request):
            response = MagicMock()
            response.headers = {}
            return response

        # Set a known sentinel before dispatch — must be restored after.
        token = request_id_var.set("before-test")
        try:
            request = MagicMock()
            request.headers = {"X-Request-ID": "during-test"}
            await middleware.dispatch(request, call_next)
            assert request_id_var.get("") == "before-test"
        finally:
            request_id_var.reset(token)
