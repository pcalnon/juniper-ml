"""Tests for the generic subprocess launcher (``juniper_service_core.launcher``).

Hermetic and fast: real short-lived subprocesses for :class:`ManagedService`
lifecycle, a threaded :class:`http.server` for :func:`wait_for_health`, and a
``python -m http.server`` child for :func:`start_service`. Every test binds to an
ephemeral port (bind ``:0``) and cleans up its process plus the module-level
``_active_services`` registry so no orphans leak.
"""

from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from juniper_service_core import launcher
from juniper_service_core.launcher import ManagedService, start_service, wait_for_health


def _free_port() -> int:
    """Bind to port 0 to obtain an OS-assigned free TCP port, then release it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _HealthHandler(BaseHTTPRequestHandler):
    """Returns 200 on ``/health`` and 404 elsewhere; silences access logging."""

    def do_GET(self):  # noqa: N802 (BaseHTTPRequestHandler API)
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # noqa: A002 — silence stderr access logs
        pass


@pytest.fixture
def health_server():
    """Run a trivial HTTP health server in a background thread on a free port."""
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def active_services_guard():
    """Snapshot and restore ``_active_services`` so a test cannot leak entries."""
    saved = list(launcher._active_services)
    try:
        yield
    finally:
        for svc in list(launcher._active_services):
            try:
                svc.terminate(timeout=2)
            except Exception:
                pass
        launcher._active_services[:] = saved


def test_managed_service_is_running_true_then_false_after_terminate():
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])  # nosec B603
    svc = ManagedService("sleeper", process)
    try:
        assert svc.is_running() is True
        svc.terminate(timeout=5)
        assert svc.is_running() is False
    finally:
        if svc.is_running():
            process.kill()
            process.wait(timeout=5)


def test_wait_for_health_returns_true_when_endpoint_responds_200(health_server):
    url = f"http://127.0.0.1:{health_server}/health"
    assert asyncio.run(wait_for_health(url, timeout=2, interval=0.1)) is True


def test_wait_for_health_returns_false_when_no_server():
    url = f"http://127.0.0.1:{_free_port()}/health"
    assert asyncio.run(wait_for_health(url, timeout=1.0, interval=0.1)) is False


def test_start_service_returns_running_managed_service(active_services_guard):
    port = _free_port()
    command = f"{sys.executable} -m http.server {port} --bind 127.0.0.1"
    health_url = f"http://127.0.0.1:{port}/"

    svc = asyncio.run(
        start_service(
            "tiny-http",
            command,
            health_url,
            health_timeout=5,
        )
    )
    try:
        assert svc is not None
        assert isinstance(svc, ManagedService)
        assert svc.is_running() is True
        assert svc in launcher._active_services
    finally:
        if svc is not None:
            svc.terminate(timeout=5)
            assert svc.is_running() is False
