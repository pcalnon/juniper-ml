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

One product rule is enforced BEFORE any canned route, because a stub that answered a request the
real server refuses is how ml#2115 merged an ``export`` that 400s on every call: 2.4.0.0's
``GET /api/v1/backup/{id}/export`` has no Bearer authorization and requires a ``token`` query
parameter holding a single-operation token for "export" (``BackupGet.cs``), which only the
Bearer-authorised ``POST /api/v1/auth/issuetoken/export`` hands out (``Auth.cs``). So, whatever route
a test installed for those paths, the stub answers as 2.4.0.0 does (``DuplicatiWebserver.cs``'s
exception mapping): a token-less export 400 with an empty body (binding fails before the handler); a
token it never issued 500, because ``ReadSingleOperationToken`` throws on a token it did not sign --
the access token included; a token it issued for ANOTHER operation 401 (``Operation != "export"``); an
issuetoken without the Bearer token an empty 401; and an issuetoken for an operation outside
``export`` / ``bugreport`` / ``websocket`` 400. The export issuetoken route is routed by default, like
login, and a test may re-route it to fail or route another operation's.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

STUB_BASE = "http://127.0.0.1:9"
STUB_BEARER_MARKER = "stub-access-marker"
# The single-operation token the default issuetoken route hands out. Distinct from the Bearer
# marker: the export route must not accept the access token in place of an operation token.
STUB_OPERATION_MARKER = "stub-export-operation-marker"
ISSUE_EXPORT_TOKEN = ("POST", "/api/v1/auth/issuetoken/export")
_ISSUE_PATH = re.compile(r"/api/v1/auth/issuetoken/([^/]+)")
_EXPORT_PATH = re.compile(r"/api/v1/backup/[^/]+/export")
_OPERATIONS = ("export", "bugreport", "websocket")  # Auth.cs: issuetoken refuses any other with 400
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
        # Per operation, every Token/token a 200 issuetoken response carried: the tokens the stub "signed".
        self.operation_tokens: dict[str, set[str]] = {}
        self.route("POST", "/api/v1/auth/login", 200, {"AccessToken": bearer})
        self.route(*ISSUE_EXPORT_TOKEN, 200, {"Token": STUB_OPERATION_MARKER})

    def route(self, method: str, path: str, status: int = 200, payload: object = None, *, handler=None) -> None:
        self.routes[(method, path)] = handler if handler is not None else (status, payload)

    def _product_refusal(self, method: str, path: str, query: dict, headers: dict):
        """The 2.4.0.0 export-flow refusals, applied before any canned route; None when none applies.

        A payload of None is an EMPTY body, as the product sends for these two 401/400 cases.
        """
        issue = _ISSUE_PATH.fullmatch(path)
        if method == "POST" and issue:
            if headers.get("authorization") != f"Bearer {self.bearer}":
                return 401, None  # .RequireAuthorization(): an empty 401 (with WWW-Authenticate)
            if issue.group(1) not in _OPERATIONS:
                return 400, {"Error": "Invalid operation", "Code": 400}  # Auth.cs: BadRequestException
        if method == "GET" and _EXPORT_PATH.fullmatch(path):
            if "token" not in query:
                return 400, None  # binding of the required [FromQuery] string token fails: an empty 400 in Production
            token = query["token"]
            if token in self.operation_tokens.get("export", set()):
                return None
            if any(token in tokens for operation, tokens in self.operation_tokens.items() if operation != "export"):
                return 401, {"Error": "Invalid operation", "Code": 401}  # BackupGet.cs: Operation != "export"
            return 500, {"Error": "An error occurred", "Code": 500}  # ReadSingleOperationToken throws: not a token it signed
        return None

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
        refusal = self._product_refusal(method, parts.path, query, headers)
        if refusal is not None:
            status, payload = refusal
        elif route is None:
            status, payload = 404, {"Error": f"not routed: {method} {parts.path}"}
        elif callable(route):
            status, payload = route(query)
        else:
            status, payload = route
        issue = _ISSUE_PATH.fullmatch(parts.path)
        if method == "POST" and issue and status == 200 and isinstance(payload, dict):
            tokens = self.operation_tokens.setdefault(issue.group(1), set())
            tokens.update(v for k, v in payload.items() if k in ("Token", "token") and isinstance(v, str) and v)
        if status >= 400:
            raw = b"" if payload is None else json.dumps(payload).encode()
            raise urllib.error.HTTPError(url, status, "stub", None, io.BytesIO(raw))  # type: ignore[arg-type]
        return FakeResponse(status, payload)

    def paths(self) -> list[tuple[str, str]]:
        return [(r.method, r.path) for r in self.requests]

    def without_login(self) -> list[Recorded]:
        return [r for r in self.requests if r.path != "/api/v1/auth/login"]
