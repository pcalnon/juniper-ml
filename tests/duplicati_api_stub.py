"""Hermetic stand-in for the Duplicati server behind the two API clients -- no socket is opened.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/yamaguchi_server_api.py``, ``util/ad-hoc/duplicati_api.py`` and the watchdog
reach the server only through ``urllib.request.urlopen``. ``FakeDuplicati.urlopen`` replaces that
one function: it routes ``(METHOD, path)`` to a canned ``(status, payload)`` and records every
request, so a test can assert the exact method, path, query, headers and JSON body -- and that
NOTHING was sent on the paths that must refuse before contacting the server.

``STUB_BASE`` is a closed loopback port, never the live server's 8300. A test that forgot to
install the stub would therefore fail with "connection refused" rather than reach a real
Duplicati -- and the credential it carries is a fixture written by the test, never a real one.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
import urllib.error
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

STUB_BASE = "http://127.0.0.1:9"
STUB_BEARER_MARKER = "stub-access-marker"
# Throwaway literal, not a credential. It carries the shell metacharacters the real secrets
# on this host do ('$', '&', '@', '#', '^'), so a value that leaks through a shell or a
# format string is still recognisable in an assertion.
FIXTURE_MARKER = "fixture-webui-Q7$&@#^-marker"

REPO_ROOT = Path(__file__).resolve().parents[1]
AD_HOC = REPO_ROOT / "util" / "ad-hoc"


def load_ad_hoc(name: str):
    """Import a ``util/ad-hoc`` module by name, the way its siblings import each other.

    The watchdog does ``import yamaguchi_server_api as api``; importing the client the same
    way here makes ``watchdog.api`` and the test's module the SAME object, so a patch on one
    is a patch on the other.
    """
    if str(AD_HOC) not in sys.path:
        sys.path.insert(0, str(AD_HOC))
    return importlib.import_module(name)


def write_credential(path: Path, text: str | bytes, mode: int = 0o600) -> Path:
    """Write a credential file with an exact mode (umask cannot widen or narrow it)."""
    data = text.encode("utf-8") if isinstance(text, str) else text
    path.write_bytes(data)
    os.chmod(path, mode)
    return path


@dataclass
class Recorded:
    """One request as the client sent it."""

    method: str
    url: str
    path: str
    query: dict
    headers: dict
    body: object


class FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        if payload is None:
            self._raw = b""
        elif isinstance(payload, bytes):
            self._raw = payload
        else:
            self._raw = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        """Never suppresses: an exception inside the ``with`` propagates, as with a real response."""


class FakeDuplicati:
    """Routes ``(METHOD, path)`` to ``(status, payload)``; unrouted requests answer 404.

    A route may instead carry a ``handler`` taking the parsed query dict and returning
    ``(status, payload)`` -- the watchdog's keyset-paged log needs one.
    """

    def __init__(self, base: str = STUB_BASE, bearer: str = STUB_BEARER_MARKER) -> None:
        self.base = base
        self.bearer = bearer
        self.routes: dict = {}
        self.requests: list[Recorded] = []
        self.route("POST", "/api/v1/auth/login", 200, {"AccessToken": bearer})

    def route(self, method: str, path: str, status: int = 200, payload: object = None, *, handler=None) -> None:
        self.routes[(method, path)] = handler if handler is not None else (status, payload)

    def urlopen(self, request, timeout=None):
        url = request.full_url
        if not url.startswith(self.base + "/"):
            raise AssertionError(f"a request left the stub's base: {url}")
        parts = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
        data = request.data
        body = json.loads(data) if data else None
        headers = {k.lower(): v for k, v in request.header_items()}
        method = request.get_method()
        self.requests.append(Recorded(method, url, parts.path, query, headers, body))
        route = self.routes.get((method, parts.path))
        if route is None:
            status, payload = 404, {"Error": f"not routed: {method} {parts.path}"}
        elif callable(route):
            status, payload = route(query)
        else:
            status, payload = route
        if status >= 400:
            raise urllib.error.HTTPError(url, status, "stub", None, io.BytesIO(json.dumps(payload).encode()))  # type: ignore[arg-type]
        return FakeResponse(status, payload)

    def paths(self) -> list[tuple[str, str]]:
        return [(r.method, r.path) for r in self.requests]

    def without_login(self) -> list[Recorded]:
        return [r for r in self.requests if r.path != "/api/v1/auth/login"]
