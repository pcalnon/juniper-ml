#!/usr/bin/env python3
"""Edges of ``export``'s single-operation token that the happy-path suite cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_server_api.py`` pins the issuetoken-then-export flow with
``stub-export-operation-marker``, a token that contains none of ``+``, ``&`` or ``=``.
A client that concatenates ``?export-passwords=false&token=`` still passes that suite,
and the concatenated form lets a token containing ``&export-passwords=true`` flip the
flag that keeps passwords out of the guard dry-run's stdout. The same suite tries an
empty ``Token`` alone and a lowercase ``token`` alone, so it cannot see a fall-through
from an unusable PascalCase field, nor which spelling wins when both are usable. It
also fails exports that are 404 or 200-without-a-TargetURL; a 201 that still carries
a TargetURL would look like success if the status check became ``_ok`` (any 2xx).

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, ISSUE_EXPORT_TOKEN, STUB_BASE, STUB_BEARER_MARKER, FakeDuplicati, load_ad_hoc, write_credential

api = load_ad_hoc("yamaguchi_server_api")

TARGET = "file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
# Reserved characters a JWT-shaped or hostile token can carry. Concatenating this into the query
# flips export-passwords to true and splits the token; urlencode keeps one parameter of each.
TOKEN = "a+b&export-passwords=true&x=y z/%"
PASCAL = "pascal-operation-marker"
CAMEL = "camel-operation-marker"
FALLTHROUGH = "fallthrough-operation-marker"
CONFIG = {"Backup": {"ID": "7", "TargetURL": TARGET}, "Schedule": {"Repeat": "1D"}}


class _Export(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        cred = write_credential(self.dir / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
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
        self.assertNotIn(FIXTURE_MARKER, out.getvalue() + err.getvalue())
        return rc, out.getvalue(), err.getvalue()

    def test_a_reserved_character_token_cannot_flip_export_passwords(self) -> None:
        """The operation token is a query value, not a second copy of the query string."""
        self.fake.route(*ISSUE_EXPORT_TOKEN, 200, {"Token": TOKEN})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, CONFIG)
        rc, out, err = self.run_cli("export", "7")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out), CONFIG)
        download = self.fake.requests[-1]
        self.assertEqual(download.query, {"export-passwords": "false", "token": TOKEN})
        self.assertIn("%2B", download.url)
        self.assertIn("%26export-passwords%3Dtrue", download.url)
        self.assertNotIn("&export-passwords=true", download.url)
        self.assertEqual(download.headers.get("authorization"), f"Bearer {STUB_BEARER_MARKER}")
        self.assertNotIn(TOKEN, download.headers.get("authorization", ""))
        self.assertNotIn(TOKEN, out + err)

    def test_an_unusable_pascal_token_falls_through_to_lowercase(self) -> None:
        """An empty, null, numeric or object ``Token`` must not be stringified into the query."""
        bodies = (
            {"Token": "", "token": FALLTHROUGH},
            {"Token": None, "token": FALLTHROUGH},
            {"Token": 7, "token": FALLTHROUGH},
            {"Token": {"nested": "nested-operation-marker"}, "token": FALLTHROUGH},
        )
        self.fake.route("GET", "/api/v1/backup/7/export", 200, CONFIG)
        for body in bodies:
            with self.subTest(body=body):
                self.fake.requests.clear()
                self.fake.route(*ISSUE_EXPORT_TOKEN, 200, body)
                rc, out, err = self.run_cli("export", "7")
                self.assertEqual(rc, 0, err)
                self.assertEqual(self.fake.requests[-1].query["token"], FALLTHROUGH)
                self.assertNotIn("nested-operation-marker", out + err)
                self.assertNotIn(FALLTHROUGH, err)

    def test_pascal_case_wins_when_both_fields_are_usable(self) -> None:
        """2.4.0.0 writes ``Token``. A lowercase field beside it must not replace that value."""
        self.fake.route(*ISSUE_EXPORT_TOKEN, 200, {"Token": PASCAL, "token": CAMEL})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, CONFIG)
        rc, out, err = self.run_cli("export", "7")
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.fake.requests[-1].query["token"], PASCAL)
        self.assertNotIn(CAMEL, self.fake.requests[-1].url)
        self.assertNotIn(PASCAL, out + err)
        self.assertNotIn(CAMEL, out + err)

    def test_only_http_200_with_a_target_url_is_success(self) -> None:
        """A 2xx other than 200 still carrying Backup.TargetURL must not reach json.load."""
        for status in (201, 204):
            with self.subTest(status=status):
                self.fake.requests.clear()
                self.fake.route("GET", "/api/v1/backup/7/export", status, CONFIG)
                rc, out, err = self.run_cli("export", "7")
                self.assertEqual((rc, out), (1, ""))
                self.assertIn(f"export 7 failed {status}", err)
                self.assertNotIn(TARGET, out)
                self.assertNotIn("stub-export-operation-marker", err)


if __name__ == "__main__":
    unittest.main()
