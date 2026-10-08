#!/usr/bin/env python3
"""``duplicati_api.call`` re-authenticates once and returns errors as data.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_duplicati_web_credential.py`` already pins the shared credential file and
that a successful ``call()`` posts the password only in the login body. Every one of
those requests is HTTP 200, so the branches this client exists for are invisible there:

* a 401 is retried exactly once, and the retry carries the token from the second login;
* a second 401 stops, and a re-login that itself fails does not hit the endpoint again;
* a caller-supplied token is sent as-is until it is rejected;
* any other HTTP error is returned as truncated text, with no second login;
* an error body that cannot be read still returns the status;
* an empty success body is ``None`` and a non-JSON success body is text;
* a leading slash and a JSON payload reach exactly one endpoint;
* the retired-variable note is printed once across repeated reads;
* ``main()`` with no request exits 2 and sends nothing, and a lowercase verb is uppercased.

No server is contacted: ``urllib.request.urlopen`` is replaced by ``tests/duplicati_api_stub.py``.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import unittest.mock as mock
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

api = load_ad_hoc("yamaguchi_server_api")
dapi = load_ad_hoc("duplicati_api")

# Throwaway Bearer values a caller hands to call(); fixtures, never credentials.
CALLER_BEARER_MARKER = "caller-bearer-marker"
STALE_BEARER_MARKER = "stale-bearer-marker"


class _Client(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "web-credential"
        write_credential(self.path, f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.path)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(dapi, "BASE", STUB_BASE),
            mock.patch.object(api, "BASE", STUB_BASE),
            mock.patch.object(dapi, "_retired_reported", set[str]()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def assert_password_only_on_login(self) -> None:
        logins = [r for r in self.fake.requests if r.path == "/api/v1/auth/login"]
        self.assertGreaterEqual(len(logins), 1)
        for request in logins:
            self.assertEqual(request.body, {"Password": FIXTURE_MARKER})
        for request in self.fake.requests:
            if request.path == "/api/v1/auth/login":
                continue
            self.assertNotIn(FIXTURE_MARKER, request.url)
            self.assertNotIn(FIXTURE_MARKER, json.dumps(request.headers))
            blob = json.dumps(request.body) if request.body is not None else ""
            self.assertNotIn(FIXTURE_MARKER, blob)


class CallRetryTest(_Client):
    def test_a_401_is_retried_once_with_the_new_token(self) -> None:
        """The rejected token must not be sent again: the retry uses the second login."""
        issued = iter(("token-a", "token-b"))

        def login_handler(_query: dict) -> tuple[int, dict]:
            return 200, {"AccessToken": next(issued)}

        hits = {"n": 0}

        def api_handler(_query: dict) -> tuple[int, dict]:
            hits["n"] += 1
            if hits["n"] > 2:
                raise AssertionError("401 was retried more than once")
            if hits["n"] == 1:
                return 401, {"Error": "expired"}
            return 200, {"ProgramState": "Running"}

        self.fake.route("POST", "/api/v1/auth/login", handler=login_handler)
        self.fake.route("GET", "/api/v1/serverstate", handler=api_handler)
        self.assertEqual(dapi.call("serverstate"), (200, {"ProgramState": "Running"}))
        self.assertEqual(
            self.fake.paths(),
            [
                ("POST", "/api/v1/auth/login"),
                ("GET", "/api/v1/serverstate"),
                ("POST", "/api/v1/auth/login"),
                ("GET", "/api/v1/serverstate"),
            ],
        )
        gets = [r for r in self.fake.requests if r.path == "/api/v1/serverstate"]
        self.assertEqual(
            [r.headers["authorization"] for r in gets],
            ["Bearer token-a", "Bearer token-b"],
        )
        self.assert_password_only_on_login()

    def test_a_second_401_stops(self) -> None:
        hits = {"n": 0}

        def api_handler(_query: dict) -> tuple[int, dict]:
            hits["n"] += 1
            if hits["n"] > 2:
                raise AssertionError("401 was retried more than once")
            return 401, {"Error": "still expired"}

        self.fake.route("GET", "/api/v1/serverstate", handler=api_handler)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            dapi.call("serverstate")
        self.assertEqual(ctx.exception.code, 401)
        self.assertEqual(hits["n"], 2)
        self.assertEqual(self.fake.paths().count(("POST", "/api/v1/auth/login")), 2)
        self.assertEqual(self.fake.paths().count(("GET", "/api/v1/serverstate")), 2)

    def test_a_failed_relogin_does_not_hit_the_endpoint_again(self) -> None:
        logins = {"n": 0}

        def login_handler(_query: dict) -> tuple[int, dict]:
            logins["n"] += 1
            if logins["n"] == 1:
                return 200, {"AccessToken": "token-a"}
            return 401, {"Error": "login rejected"}

        hits = {"n": 0}

        def api_handler(_query: dict) -> tuple[int, dict]:
            hits["n"] += 1
            if hits["n"] > 1:
                raise AssertionError("the endpoint was called after a failed re-login")
            return 401, {"Error": "expired"}

        self.fake.route("POST", "/api/v1/auth/login", handler=login_handler)
        self.fake.route("GET", "/api/v1/serverstate", handler=api_handler)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            dapi.call("serverstate")
        self.assertEqual(ctx.exception.code, 401)
        self.assertEqual(logins["n"], 2)
        self.assertEqual(hits["n"], 1)
        self.assertEqual(self.fake.paths().count(("GET", "/api/v1/serverstate")), 1)

    def test_a_supplied_token_is_used_until_a_401_replaces_it(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, {"ProgramState": "Running"})
        self.assertEqual(dapi.call("serverstate", token=CALLER_BEARER_MARKER), (200, {"ProgramState": "Running"}))
        self.assertEqual(self.fake.paths(), [("GET", "/api/v1/serverstate")])
        self.assertEqual(self.fake.requests[0].headers["authorization"], f"Bearer {CALLER_BEARER_MARKER}")

        self.fake.requests.clear()

        def login_handler(_query: dict) -> tuple[int, dict]:
            return 200, {"AccessToken": "token-after-reject"}

        hits = {"n": 0}

        def api_handler(_query: dict) -> tuple[int, dict]:
            hits["n"] += 1
            if hits["n"] == 1:
                return 401, {"Error": "expired"}
            return 200, {"ok": True}

        self.fake.route("POST", "/api/v1/auth/login", handler=login_handler)
        self.fake.route("GET", "/api/v1/serverstate", handler=api_handler)
        self.assertEqual(dapi.call("serverstate", token=STALE_BEARER_MARKER), (200, {"ok": True}))
        gets = [r for r in self.fake.requests if r.path == "/api/v1/serverstate"]
        self.assertEqual(
            [r.headers["authorization"] for r in gets],
            [f"Bearer {STALE_BEARER_MARKER}", "Bearer token-after-reject"],
        )
        self.assertEqual(self.fake.paths().count(("POST", "/api/v1/auth/login")), 1)
        self.assert_password_only_on_login()

    def test_a_non_401_is_returned_truncated_without_another_login(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 503, {"Error": "E" * 1000})
        status, body = dapi.call("serverstate")
        self.assertEqual(status, 503)
        self.assertIsInstance(body, str)
        self.assertEqual(len(body), 400)
        self.assertTrue(body.startswith('{"Error": "'))
        self.assertNotIn(FIXTURE_MARKER, body)
        self.assertEqual(self.fake.paths().count(("POST", "/api/v1/auth/login")), 1)
        self.assertEqual(self.fake.paths().count(("GET", "/api/v1/serverstate")), 1)

    def test_an_unreadable_error_body_still_returns_the_status(self) -> None:
        real = self.fake.urlopen

        def urlopen(request, timeout=None):
            path = urllib.parse.urlsplit(request.full_url).path
            if path.endswith("/auth/login"):
                return real(request, timeout)

            class _Broken:
                def read(self, _n: int = -1) -> bytes:
                    raise OSError("body already consumed")

                def close(self) -> None:
                    """HTTPError closes its body on the way out; a missing close is noise, not the assertion."""

            raise urllib.error.HTTPError(request.full_url, 503, "stub", None, _Broken())

        with mock.patch("urllib.request.urlopen", urlopen):
            status, body = dapi.call("serverstate")
        self.assertEqual((status, body), (503, "<error body unavailable>"))
        self.assertEqual(self.fake.paths(), [("POST", "/api/v1/auth/login")])
        self.assertNotIn(FIXTURE_MARKER, body)

    def test_empty_and_non_json_success_bodies_stay_unparsed(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, None)
        self.assertEqual(dapi.call("serverstate"), (200, None))
        self.fake.route("GET", "/api/v1/serverstate", 200, b"<{not-json")
        self.assertEqual(dapi.call("serverstate"), (200, "<{not-json"))

    def test_a_leading_slash_and_a_payload_hit_one_endpoint(self) -> None:
        self.fake.route("POST", "/api/v1/task/7/abort", 200, {"Status": "Aborted"})
        self.assertEqual(
            dapi.call("/task/7/abort", "POST", {"reason": "operator"}),
            (200, {"Status": "Aborted"}),
        )
        sent = self.fake.without_login()
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].method, "POST")
        self.assertEqual(sent[0].path, "/api/v1/task/7/abort")
        self.assertEqual(sent[0].body, {"reason": "operator"})
        self.assertEqual(sent[0].headers.get("content-type"), "application/json")
        self.assert_password_only_on_login()


class SessionNoteAndMainTest(_Client):
    def test_a_retired_variable_is_named_once_across_repeated_reads(self) -> None:
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"DUPLICATI_PW_FILE": str(self.path), "DUPLICATI_PW_KEY": "LEGACY"}), redirect_stderr(err):
            self.assertEqual(dapi._password(), FIXTURE_MARKER)
            self.assertEqual(dapi._password(), FIXTURE_MARKER)
        text = err.getvalue()
        self.assertEqual(text.count("DUPLICATI_PW_FILE is set but no longer read"), 1)
        self.assertEqual(text.count("DUPLICATI_PW_KEY is set but no longer read"), 1)
        self.assertNotIn(FIXTURE_MARKER, text)
        self.assertEqual(self.fake.requests, [])

    def test_main_without_a_request_exits_2_and_sends_nothing(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(dapi.main(["duplicati_api.py"]), 2)
        self.assertEqual(self.fake.requests, [])
        self.assertIn("DUPLICATI_WEB_CREDENTIAL_FILE", out.getvalue())

    def test_main_uppercases_the_verb_and_prints_the_status(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, {"ProgramState": "Running"})
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(dapi.main(["duplicati_api.py", "get", "serverstate"]), 0)
        text = out.getvalue()
        self.assertIn("[200]", text)
        self.assertIn("Running", text)
        self.assertEqual(self.fake.without_login()[0].method, "GET")
        self.assert_password_only_on_login()


if __name__ == "__main__":
    unittest.main()
