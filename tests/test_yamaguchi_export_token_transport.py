#!/usr/bin/env python3
"""Export-token edges the happy-path suite and the encoding suite cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_server_api.py`` pins a failed export and a failed issuetoken when the
stub answers HTTP, and ``tests/test_yamaguchi_export_token_edges.py`` pins query encoding,
PascalCase fall-through, and a 201/204 export body. Neither raises ``URLError`` on the export
GET, so neither notices a handler that logs the request URL -- the one place the
single-operation token now travels. Neither answers issuetoken with a 3xx, so ``status >= 400``
(echo the body) versus ``status >= 300`` (echo a body that may still hold the token) is
untested on the redirect side. And neither exports a TargetURL that is only whitespace:
``str.strip()`` would turn that into the empty stdout the guard's ``[[ -n ]]`` treats as
"no URL", which skips the TargetURL comparison (STOP item 3).

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py`` except
where a test replaces it with a transport failure.
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

from tests.duplicati_api_stub import FIXTURE_MARKER, ISSUE_EXPORT_TOKEN, STUB_BASE, STUB_OPERATION_MARKER, FakeDuplicati, load_ad_hoc, write_credential

api = load_ad_hoc("yamaguchi_server_api")

TARGET = "file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
REDIRECT_TOKEN = "redirect-class-operation-marker"
ERROR_BODY = "issuetoken-refused-distinctive"
CONFIG = {"Backup": {"ID": "7", "TargetURL": TARGET}}


class _Export(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        cred = write_credential(Path(directory.name) / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        self.export_urls: list[str] = []
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(cred)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(api, "BASE", STUB_BASE),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = api.main(list(argv))
            except SystemExit as exc:
                if isinstance(exc.code, str):
                    err.write(exc.code + "\n")
                    rc = 1
                else:
                    rc = 0 if exc.code is None else exc.code
        combined = out.getvalue() + err.getvalue()
        self.assertNotIn(FIXTURE_MARKER, combined)
        return rc, out.getvalue(), err.getvalue()

    def test_a_transport_drop_after_issuetoken_does_not_print_the_url(self) -> None:
        """The export URL carries the operation token. A dropped connection must not log it.

        ``filename`` is set to that URL because ``HTTPError`` stores the request URL there, and
        a handler that prints ``filename`` (or the URL it just built) would put a one-minute
        JWT on stderr. The reason stays a bare socket error, which is what urllib reports.
        """
        cases = (
            ("URLError", lambda url: urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"), filename=url)),
            ("TimeoutError", lambda url: TimeoutError("timed out")),
            ("ConnectionError", lambda url: ConnectionError("connection aborted")),
        )
        for name, make_exc in cases:
            with self.subTest(error=name):
                self.export_urls.clear()
                self.fake.requests.clear()

                def urlopen(request, timeout=None, _make=make_exc):
                    path = urllib.parse.urlsplit(request.full_url).path
                    # issuetoken's own path ends in /export; only the backup download carries the token.
                    if "/backup/" in path and path.endswith("/export"):
                        self.export_urls.append(request.full_url)
                        raise _make(request.full_url)
                    return self.fake.urlopen(request, timeout)

                with mock.patch("urllib.request.urlopen", urlopen):
                    rc, out, err = self.run_cli("export", "7")
                self.assertEqual((rc, out), (1, ""))
                self.assertIn("cannot reach", err)
                (url,) = self.export_urls
                self.assertIn(STUB_OPERATION_MARKER, url, "the dropped request really carried the operation token")
                self.assertIn("/export?", url)
                self.assertNotIn(STUB_OPERATION_MARKER, err)
                self.assertNotIn("/export?", err)
                self.assertNotIn(url, err)
                self.assertIn(ISSUE_EXPORT_TOKEN, self.fake.paths())

    def test_a_redirect_class_issuetoken_does_not_echo_its_token(self) -> None:
        """3xx is not an error status. Its body can still hold the token, so it must not be printed.

        399 is the last status below the ``>= 400`` cut: a change to ``>= 300`` echoes it.
        """
        self.fake.route("GET", "/api/v1/backup/7/export", 200, CONFIG)
        for status in (302, 399):
            with self.subTest(status=status):
                self.fake.requests.clear()
                self.fake.route(*ISSUE_EXPORT_TOKEN, status, {"Token": REDIRECT_TOKEN})
                rc, out, err = self.run_cli("export", "7")
                self.assertEqual((rc, out), (1, ""))
                self.assertIn(f"export 7: issuetoken failed {status}", err)
                self.assertIn("no usable Token", err)
                self.assertNotIn(REDIRECT_TOKEN, err)
                self.assertNotIn(("GET", "/api/v1/backup/7/export"), self.fake.paths())

    def test_an_issuetoken_error_body_is_still_printed(self) -> None:
        """The same cut must keep a real 400 body. Swallowing it hides the refusal."""
        self.fake.route(*ISSUE_EXPORT_TOKEN, 400, {"Error": ERROR_BODY})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, CONFIG)
        rc, out, err = self.run_cli("export", "7")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn(ERROR_BODY, err)
        self.assertNotIn("no usable Token", err)
        self.assertNotIn(("GET", "/api/v1/backup/7/export"), self.fake.paths())

    def test_a_whitespace_target_url_is_still_exported(self) -> None:
        """Whitespace is non-empty to the guard's ``[[ -n ]]``. Empty stdout would skip the check.

        The operation token travels only as the query parameter: the GET has no JSON body.
        """
        for url in (" ", "\n", "\t"):
            with self.subTest(url=repr(url)):
                self.fake.requests.clear()
                payload = {"Backup": {"ID": "7", "TargetURL": url}}
                self.fake.route("GET", "/api/v1/backup/7/export", 200, payload)
                rc, out, err = self.run_cli("export", "7")
                self.assertEqual(rc, 0, err)
                self.assertEqual(json.loads(out), payload)
                download = self.fake.requests[-1]
                self.assertIsNone(download.body, "the operation token must not also be a JSON body")
                self.assertEqual(download.query["export-passwords"], "false")
                self.assertNotIn(STUB_OPERATION_MARKER, out + err)


if __name__ == "__main__":
    unittest.main()
